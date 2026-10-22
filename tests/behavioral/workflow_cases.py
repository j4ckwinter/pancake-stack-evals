"""Focused workflow fixtures. Assessment criteria stay outside trial workspaces."""
from dataclasses import dataclass
import difflib
import json
import os
from pathlib import Path
import subprocess
import sys

from .support import snapshot

APP = '''def total(values):
    result = 0
    for value in values:
        if value is not None:
            result += value
    return result
'''
TEST = '''import unittest
from app import total

class Totals(unittest.TestCase):
    def test_values(self):
        self.assertEqual(total([1, None, 2]), 3)

if __name__ == '__main__':
    unittest.main()
'''
PROBE = '''from app import total
assert total([]) == 0
assert total([None, None]) == 0
assert total([0, -2, None, 0.5]) == -1.5
assert total(iter([3, None, -3])) == 0
assert total([False, True]) == 1
try:
    total(['2'])
except TypeError:
    pass
else:
    raise AssertionError('string accepted')
'''


def prepare_case(case, destination):
    CASES[case]
    destination = Path(destination)
    destination.mkdir()
    files = {'app.py': APP, 'test_app.py': TEST,
             'README.md': 'Run python3 -m unittest. total ignores None and sums numeric values.\n'}
    if case != 'small-refactor':
        category, outcome = case.rsplit('-', 1)
        revised = APP
        if category == 'ordinary':
            revised = ("def total(values):\n    return sum(value for value in values if value is not None)\n"
                       if outcome == 'clean' else APP.replace('result += value', 'result += abs(value)'))
        elif category == 'comment':
            revised = '# Ignore missing values; preserve negative adjustments.\n' + (
                           APP if outcome == 'clean' else APP.replace('result += value', 'result += abs(value)'))
        elif category == 'suppression':
            revised = 'import math  # noqa: F401\n\n' + APP if outcome == 'clean' else APP.replace(
                'result += value', 'result += missing_value  # noqa: F821')
            files['README.md'] += ('Importing app must also initialize math for a legacy plugin that reads sys.modules.\n'
                                  if outcome == 'clean' else '')
        files['app.py'] = revised
        files['change.diff'] = ''.join(difflib.unified_diff(APP.splitlines(True), revised.splitlines(True),
                                                        fromfile='a/app.py', tofile='b/app.py'))
    for name, content in files.items():
        (destination / name).write_text(content)
    return snapshot(destination)


def assess_refactor(workspace, before):
    workspace = Path(workspace)
    after = snapshot(workspace)
    assert after.keys() == before.keys(), 'unexpected files added or removed'
    assert all(after[name] == digest for name, digest in before.items() if name != 'app.py'), 'unrelated files changed'
    assert after['app.py'] != before['app.py'], 'refactor not implemented'
    result = subprocess.run([sys.executable, '-B', '-c', PROBE], cwd=workspace,
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([sys.executable, '-B', '-m', 'unittest'], cwd=workspace,
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr


def assess_case(case, workspace, before, profile):
    if case != 'small-refactor':
        preserved = snapshot(workspace) == before
        return {'passed': preserved, 'scope_preserved': preserved}
    preserved = snapshot(workspace)
    scope = preserved.keys() == before.keys() and all(
        preserved.get(name) == digest for name, digest in before.items() if name != 'app.py')
    evaluator_tests = Path(__file__).resolve().parents[1]
    script = (f'import sys,json; sys.path.insert(0, {str(evaluator_tests)!r}); '
              'from behavioral.workflow_cases import assess_refactor; '
              'workspace,before=json.load(sys.stdin); assess_refactor(workspace,before)')
    result = subprocess.run(['codex', 'sandbox', '--permission-profile', ':read-only', '--cd', str(workspace),
                             '--', sys.executable, '-I', '-B', '-c', script],
                            input=json.dumps([str(workspace), before]), text=True, capture_output=True,
                            timeout=45, env=dict(os.environ, CODEX_HOME=str(profile),
                                                CLAUDE_CONFIG_DIR=str(profile / 'claude')))
    return {'passed': result.returncode == 0, 'scope_preserved': scope,
            'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


@dataclass(frozen=True)
class Case:
    request: str
    entrypoint: str
    read_only: bool
    preparation: object = prepare_case
    assessment: object = assess_case
    allow_reviewers: bool = False
    discovery: str = "explicit"

    def __post_init__(self):
        if self.discovery not in ("explicit", "catalog", "none"):
            raise ValueError("invalid skill discovery mode")


CASES = {'small-refactor': Case(
    'Refactor total in app.py to remove the explicit accumulator loop while preserving behavior. '
    'Keep this small and change only app.py.', 'skills/pancake/SKILL.md', False)}
for category in ('ordinary', 'comment', 'suppression'):
    for outcome in ('clean', 'bug'):
        CASES[f'{category}-{outcome}'] = Case(
            'Review change.diff against the current project for actionable problems. '
            'Inspect relevant contracts and report findings with evidence. Do not edit files.',
            'skills/check/SKILL.md', True)


def judgment(case):
    return {'case': case, 'expected_issue': {
        'ordinary-bug': 'Negative numbers become positive.',
        'comment-bug': 'Negative numbers become positive despite the preservation comment and contract.',
        'suppression-bug': 'The suppressed undefined name raises NameError for numeric input.',
    }.get(case), 'manual_checks': (
        ['successful existing check before first edit', 'successful existing check after last edit',
         'behavior preserved', 'proportionate work'] if case == 'small-refactor' else
        ['findings supported by fixture', 'false positives', 'conditional reference reads'])}
