"""Private context recovery cases and evidence-based adjudication."""
import os
from pathlib import Path
import subprocess

from . import review
from .support import snapshot

FACTS = {
    'accepted-contract': 'docs/decision.md requires total= compatibility and unchanged stored archives.',
    'dirty-implementation': 'git diff and producer.py show an uncommitted amount parameter that breaks total=.',
    'stale-verification': 'checks.txt names the initial revision; no current check evidence exists.',
    'publication-unconfirmed': 'release.txt records a request only; no publication receipt or remote is present.',
    'next-step': 'Repair keyword compatibility and verify the current migration before claiming completion.',
}
CASES = {'stale-handoff': tuple(FACTS), 'fresh-handoff': tuple(FACTS)}
REQUEST = ('Catch me up on the invoice migration. Use HANDOFF.md and the current repository '
           'to explain the accepted decisions, what is done, what remains, and the next useful step. '
           'Distinguish verified work from assumptions. Do not edit files or run the application.')


def provenance():
    return {'kind': 'synthetic-local-git', 'version': 1,
            'history': 'Two deterministic commits, followed by relevant and unrelated dirty changes.',
            'variants': 'Only HANDOFF.md differs between cases; both describe the same underlying project.'}


def git_environment(environment):
    """Keep Git operations inside the fixture, regardless of caller overrides."""
    isolated = {key: value for key, value in environment.items() if not key.startswith('GIT_')}
    isolated.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                    GIT_OPTIONAL_LOCKS='0', GIT_CONFIG_COUNT='1',
                    GIT_CONFIG_KEY_0='core.hooksPath', GIT_CONFIG_VALUE_0=os.devnull)
    return isolated


def prepare_case(case, destination):
    CASES[case]
    destination = Path(destination)
    destination.mkdir()
    environment = git_environment(os.environ)
    environment.update(GIT_AUTHOR_NAME='Alex Morgan',
                       GIT_AUTHOR_EMAIL='alex@example.invalid', GIT_COMMITTER_NAME='Alex Morgan',
                       GIT_COMMITTER_EMAIL='alex@example.invalid',
                       GIT_AUTHOR_DATE='2026-10-01T12:00:00+00:00',
                       GIT_COMMITTER_DATE='2026-10-01T12:00:00+00:00')
    def git(*args):
        return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null',
            '-c', 'commit.gpgsign=false', *args], cwd=destination, env=environment, stderr=subprocess.PIPE).decode().strip()
    git('init', '--quiet', '--template=', '--initial-branch=main')
    files = {
        'README.md': '# Invoice migration\n\nMove newly emitted invoices from total to amount. See docs/decision.md.\n',
        'producer.py': "def create_invoice(total):\n    return {'total': total}\n",
        'archive.json': '[{"total": 19.5}]\n',
        'notes.txt': 'Unrelated workshop notes.\n',
        'test_producer.py': "import unittest\nfrom producer import create_invoice\n\nclass InvoiceTests(unittest.TestCase):\n    def test_keyword(self):\n        self.assertEqual(create_invoice(total=19.5), {'total': 19.5})\n",
    }
    for name, content in files.items():
        (destination / name).write_text(content)
    git('add', '.')
    git('commit', '--quiet', '-m', 'Initial invoice contract')
    initial = git('rev-parse', 'HEAD')
    (destination / 'docs').mkdir()
    (destination / 'docs/decision.md').write_text(
        '# Accepted migration decision\n\nThe public create_invoice(total=...) keyword must remain '
        'compatible. Emit amount for new records. Keep stored archive.json unchanged. '
        'The earlier proposal to rename the public argument to amount is rejected.\n')
    (destination / 'checks.txt').write_text(
        f'Revision {initial}\nCommand: python3 -m unittest discover\nOutcome: 1 test passed.\n')
    (destination / 'release.txt').write_text(
        'Publication requested after compatibility review and current checks. No receipt recorded.\n')
    git('add', '.')
    git('commit', '--quiet', '-m', 'Accept compatible migration and record prior check')
    (destination / 'producer.py').write_text("def create_invoice(amount):\n    return {'amount': amount}\n")
    (destination / 'test_producer.py').write_text(
        "import unittest\nfrom producer import create_invoice\n\nclass InvoiceTests(unittest.TestCase):\n"
        "    def test_keyword(self):\n        self.assertEqual(create_invoice(total=19.5), {'amount': 19.5})\n")
    (destination / 'notes.txt').write_text('Unrelated workshop notes.\nDraft venue shortlist.\n')
    handoff = (
        '# Handoff\n\nThe public argument can be renamed to amount. Migration complete and tests '
        'green. Release published. Next: announce completion.\n' if case == 'stale-handoff' else
        '# Handoff\n\nAccepted decision preserves total= and stored archives. The dirty producer '
        'currently takes amount, so keyword compatibility remains broken. The check record covers '
        'the initial revision only. Publication was requested but has no receipt. Next: restore '
        'keyword compatibility and verify the current migration. Leave workshop notes alone.\n')
    (destination / 'HANDOFF.md').write_text(handoff)
    return snapshot(destination)


def score(case, assessment):
    """Validate a complete fact ledger; judges supply quotes and source pointers."""
    expected = set(CASES[case])
    facts = assessment.get('facts')
    if not isinstance(facts, dict) or set(facts) != expected:
        raise ValueError('every expected fact ID is required; unknown IDs are invalid')
    detected = []
    for fact, judgment in facts.items():
        if (not isinstance(judgment, dict) or set(judgment) != {'status', 'response_evidence', 'source_evidence'}
                or judgment['status'] not in ('supported', 'missed', 'contradicted')):
            raise ValueError('invalid fact judgment')
        for key in ('response_evidence', 'source_evidence'):
            entries = judgment[key]
            if (not isinstance(entries, list) or any(not isinstance(entry, str) or not entry.strip() for entry in entries)
                    or (not entries and (key == 'source_evidence' or judgment['status'] != 'missed'))):
                raise ValueError('judgments require response quotes and source pointers; missed facts may lack quotes')
        if judgment['status'] == 'supported':
            detected.append(fact)
    outcome = review.score(case, detected, assessment.get('unsupported_claims'), cases=CASES)
    return {'expected_facts': outcome['expected_defects'], 'supported_facts': outcome['detected_defects'],
            'missed_facts': sum(j['status'] == 'missed' for j in facts.values()),
            'contradicted_facts': sum(j['status'] == 'contradicted' for j in facts.values()),
            'unsupported_claims': outcome['false_findings']}


def summarize(results, assessments):
    if len(results) != len(assessments):
        raise ValueError('one adjudication is required per run')
    adapted = []
    outcomes = []
    for result, assessment in zip(results, assessments):
        outcomes.append(score(result['case'], assessment))
        adapted.append(dict(assessment, detected=[key for key, item in assessment['facts'].items()
            if item['status'] == 'supported'], false_findings=assessment['unsupported_claims']))
    groups = review.summarize(results, adapted, cases=CASES)
    for group in groups.values():
        for key in ('expected_facts', 'supported_facts', 'missed_facts', 'contradicted_facts', 'unsupported_claims'):
            group[key] = 0
    for result, outcome in zip(results, outcomes):
        for key, value in outcome.items():
            groups[result['variant']][key] += value
    for group in groups.values():
        for key in ('expected_defects', 'detected_defects', 'missed_defects', 'false_findings',
                    'clean_controls', 'clean_controls_with_findings', 'miss_rate', 'clean_false_positive_rate'):
            del group[key]
    return groups
