import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from behavioral import review
from behavioral.compare import main, run_trial
from behavioral.review_comparison import CASES, prepare_review, summarize


class ReviewComparisonTests(unittest.TestCase):
    def test_fixtures_pass_local_tests_and_independent_contract_probes(self):
        probes = {
            "config": (
                "from jobs import select_jobs; "
                "assert select_jobs(['queued'], {'limit': 0}) == []"
            ),
            "lifetime": (
                "from report import render_report; "
                "assert render_report('rows.txt') == 'alpha,beta'"
            ),
        }
        controls = {
            "config": (
                "from jobs import select_jobs; "
                "assert select_jobs(list(range(30)), {'limit': None}) == list(range(20)); "
                "assert select_jobs(['a', 'b'], {'limit': 1}) == ['a']"
            ),
            "lifetime": (
                "from reader import parse_rows; from io import StringIO; "
                "assert list(parse_rows(StringIO(' one \\n\\ntwo\\n'))) == ['one', 'two']"
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            for case in CASES:
                with self.subTest(case=case):
                    workspace = Path(directory) / case
                    prepare_review(case, workspace)
                    family = case.split('-')[0]
                    local = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover'],
                                           cwd=workspace, capture_output=True, text=True, timeout=10)
                    self.assertEqual(local.returncode, 0, local.stderr)
                    (workspace / 'rows.txt').write_text(' alpha \n\nbeta\n')
                    probe = subprocess.run([sys.executable, '-B', '-c', probes[family]],
                                           cwd=workspace, capture_output=True, text=True, timeout=10)
                    self.assertEqual(probe.returncode == 0, case.endswith('-clean'), probe.stderr)
                    control = subprocess.run([sys.executable, '-B', '-c', controls[family]],
                                             cwd=workspace, capture_output=True, text=True, timeout=10)
                    self.assertEqual(control.returncode, 0, control.stderr)
                    if case == 'lifetime-clean':
                        lifecycle = r"""
from unittest.mock import patch
from io import StringIO
from reader import read_rows
stream = StringIO(' first\nsecond\n')
with patch('builtins.open', return_value=stream):
    rows = read_rows('ignored')
    assert list(rows) == ['first', 'second']
assert stream.closed
"""
                        completed = subprocess.run([sys.executable, '-B', '-c', lifecycle],
                                                   cwd=workspace, capture_output=True, text=True, timeout=10)
                        self.assertEqual(completed.returncode, 0, completed.stderr)
                    source_name = 'settings.py' if family == 'config' else 'reader.py'
                    self.assertIn('--- a/' + source_name, (workspace / 'change.diff').read_text())
                    self.assertNotIn(case, ''.join(p.read_text() for p in workspace.iterdir()))
        self.assertEqual(set(review.CASES), {'keyword', 'consumer', 'archive', 'clean'})

    def records(self):
        result = dict(run_id='run-01', case='config-bug', variant='baseline', exit_code=0,
                      timed_out=False, sessions=[{'completed': True}], artifact={'passed': True},
                      preferences_unchanged=True, usage_complete=True,
                      usage_all_sessions={'total_tokens': 100}, elapsed_seconds=2,
                      tool_calls_all_sessions=3, command_actions_all_sessions=1)
        assessment = dict(run_id='run-01', case='config-bug', detected=['zero-limit'],
                          false_findings=0, process={'contract_reads': True},
                          unnecessary_work={'status': 'assessed', 'items': []})
        return result, assessment

    def test_summary_separates_work_correctness_and_cost_with_unknowns(self):
        result, assessment = self.records()
        item = dict(id='work-1', category='redundant_verification',
                    evidence=['raw-sessions/session.jsonl:18-26'],
                    reason='Repeated the unchanged passing check without resolving a new question.')
        assessment['unnecessary_work']['items'] = [item]
        failed = dict(result, run_id='run-02', exit_code=1, timed_out=True, usage_complete=False)
        unknown = dict(assessment, run_id='run-02', detected=[],
                       unnecessary_work={'status': 'unavailable', 'reason': 'Worker transcript missing.'})
        summary = summarize([result, failed], [assessment, unknown])['baseline']
        self.assertEqual(summary['miss_rate'], 0.5)
        self.assertEqual(summary['execution_failures'], 1)
        self.assertEqual(summary['cost']['elapsed_seconds']['n'], 1)
        self.assertEqual(summary['unnecessary_work'], {
            'assessed_runs': 1, 'unavailable_runs': 1, 'runs_with_items': 1, 'items': 1,
            'categories': {'unrelated_investigation': 0, 'redundant_verification': 1,
                           'unnecessary_delegation': 0, 'scope_expansion': 0}})
        clean = dict(result, case='config-clean')
        clean_assessment = dict(assessment, case='config-clean', detected=[], false_findings=1)
        self.assertEqual(summarize([clean], [clean_assessment])['baseline']['clean_false_positive_rate'], 1)
        unknown_only = summarize([failed], [unknown])['baseline']['unnecessary_work']
        self.assertIsNone(unknown_only['items'])
        self.assertIsNone(unknown_only['categories'])

    def test_invalid_or_missing_work_records_fail(self):
        result, assessment = self.records()
        item = dict(id='one', category='scope_expansion', evidence=['events.jsonl:4'], reason='Unrequested rewrite.')
        invalid = [None, {}, {'status': 'other'}, {'status': 'unavailable', 'reason': ''},
                   {'status': 'unavailable', 'reason': 'Missing', 'items': []},
                   {'status': 'assessed', 'items': [item, item]},
                   {'status': 'assessed', 'items': [dict(item, category='extra_tokens')]},
                   {'status': 'assessed', 'items': [dict(item, evidence=[])]},
                   {'status': 'assessed', 'items': [dict(item, evidence=[' '])]},
                   {'status': 'assessed', 'items': [dict(item, reason='')]},
                   {'status': 'assessed', 'items': [dict(item, id=[])]}]
        for work in invalid:
            with self.subTest(work=work), self.assertRaises(ValueError):
                summarize([result], [dict(assessment, unnecessary_work=work)])
        del assessment['unnecessary_work']
        with self.assertRaises(ValueError):
            summarize([result], [assessment])
        with self.assertRaises(ValueError):
            summarize([result], [])

    def test_three_arms_share_read_only_scope_and_isolate_bundles(self):
        from test_comparison import ComparisonTests
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'skills'
            ComparisonTests().make_poteto(source)
            auth = root / 'auth'
            auth.write_text('fake credential')
            prompts, snapshots = [], []
            for variant in ('baseline', 'pancake', 'poteto'):
                run = root / variant
                run.mkdir()
                def candidate(prompt, **kwargs):
                    prompts.append(prompt.split('\nUse the ')[0])
                    self.assertIn('Do not edit files', prompt)
                    self.assertIn('Independent read-only review', prompt)
                    self.assertNotIn('implementation delegates', prompt)
                    self.assertNotIn('config-clean', prompt)
                    self.assertNotIn('zero-limit', prompt)
                    self.assertFalse((run / 'workspace/review_comparison.py').exists())
                    self.assertFalse((run / 'profile/skills').exists())
                    if variant == 'baseline':
                        self.assertFalse((run / 'bundle').exists())
                    elif variant == 'pancake':
                        self.assertIn('skills/pancake/SKILL.md', prompt)
                        self.assertTrue((run / 'bundle/skills/pancake/SKILL.md').is_file())
                        self.assertFalse((run / 'bundle/skills/poteto-mode').exists())
                    else:
                        self.assertIn('skills/poteto-mode/SKILL.md', prompt)
                        self.assertEqual({p.name for p in (run / 'bundle/skills').iterdir()},
                                         {'poteto-mode', 'helper'})
                with patch('behavioral.compare.tempfile.mkdtemp', return_value=str(run)), \
                        patch('behavioral.compare.subprocess.Popen') as launch:
                    process = launch.return_value
                    process.communicate.side_effect = candidate
                    process.returncode = process.poll.return_value = 0
                    result = run_trial('config-clean', variant, root / (variant + '-evidence'),
                                       auth, 'model', 'medium', 10, 'review-comparison', source)
                command = launch.call_args.args[0]
                self.assertEqual(command[command.index('--sandbox') + 1], 'read-only')
                self.assertIn('agents.max_threads=2', command)
                self.assertTrue(result['artifact']['passed'])
                self.assertEqual(result['changed_files'], [])
                self.assertEqual(result['added_files'], [])
                self.assertIn('completed_workers', result)
                snapshots.append(result['after'])
                self.assertFalse(run.exists())
            self.assertEqual(len(set(prompts)), 1)
            self.assertEqual(snapshots[0], snapshots[1])
            self.assertEqual(snapshots[1], snapshots[2])
            self.assertEqual(auth.read_text(), 'fake credential')

    def test_cli_selects_all_review_cases_and_stops_on_changed_inputs(self):
        from test_comparison import ComparisonTests
        for change in ('none', 'before', 'after'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / 'skills'
                ComparisonTests().make_poteto(source)
                (root / 'auth.json').write_text('fake credential')
                output = root / 'evidence'
                identity_calls = []

                def captured_identity(path):
                    identity_calls.append(path)
                    changed = (change == 'before' and len(identity_calls) >= 3 or
                               change == 'after' and len(identity_calls) >= 5)
                    return {'revision': 'changed' if changed else 'initial'}

                def candidate(case, variant, destination, *args):
                    destination.mkdir()
                    return dict(run_id=destination.name, case=case, variant=variant,
                                artifact={'passed': True}, elapsed_seconds=1,
                                exit_code=0, sessions=[{'completed': True}])

                argv = ['compare.py', '--suite', 'review-comparison', '--poteto-source', str(source),
                        '--output', str(output), '--model', 'model', '--repetitions', '1']
                with patch('sys.argv', argv), patch.dict('os.environ', CODEX_HOME=str(root)), \
                        patch('behavioral.compare.identity', side_effect=captured_identity), \
                        patch('behavioral.compare.subprocess.check_output', return_value='test-cli'), \
                        patch('behavioral.compare.run_trial', side_effect=candidate) as run, \
                        patch('builtins.print'):
                    if change == 'none':
                        main()
                    else:
                        with self.assertRaisesRegex(SystemExit, 'inputs changed'):
                            main()
                manifest = json.loads((output / 'manifest.json').read_text())
                self.assertEqual(len(manifest['plan']), 12)
                self.assertEqual({row[0] for row in manifest['plan']},
                                 {'config-bug', 'config-clean', 'lifetime-bug', 'lifetime-clean'})
                self.assertEqual({row[2] for row in manifest['plan']}, {'baseline', 'pancake', 'poteto'})
                self.assertEqual(run.call_count, {'none': 12, 'before': 0, 'after': 1}[change])
                if change != 'before':
                    results = json.loads((output / 'results.json').read_text())
                    self.assertEqual(results[-1]['inputs_unchanged'], change == 'none')

    def test_read_only_trial_timeout_retains_evidence_and_cleans_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / 'project'
            run.mkdir()
            auth = root / 'auth'
            auth.write_text('fake credential')
            with patch('behavioral.compare.tempfile.mkdtemp', return_value=str(run)), \
                    patch('behavioral.compare.subprocess.Popen') as launch, \
                    patch('behavioral.compare.os.killpg'):
                process = launch.return_value
                process.communicate.side_effect = [subprocess.TimeoutExpired('codex', 1), None]
                process.returncode = process.poll.return_value = -9
                result = run_trial('lifetime-clean', 'baseline', root / 'evidence', auth,
                                   'model', None, 1, 'review-comparison')
            self.assertTrue(result['timed_out'])
            self.assertEqual(result['exit_code'], -9)
            self.assertTrue((root / 'evidence/result.json').is_file())
            self.assertFalse(run.exists())
            self.assertEqual(auth.read_text(), 'fake credential')


if __name__ == '__main__':
    unittest.main()
