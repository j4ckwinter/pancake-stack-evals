import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from behavioral import acceptance_cases as cases, acceptance_compare as runner
from behavioral.compare import trial_plan


def api(domain, outcome):
    namespace = {}
    exec(cases.ORIGINALS[domain] if outcome == 'original' else cases.revised(domain, outcome), namespace)
    return namespace[domain]


class AcceptanceTests(unittest.TestCase):
    def test_simultaneous_moves_through_real_api(self):
        for outcome in ('original', 'bug', 'clean'):
            operation = api('reschedule', outcome)
            current = {'A': 1, 'B': 2, 'C': 3}
            for moves, expected in (({'A': 2, 'B': 1}, {'A': 2, 'B': 1, 'C': 3}),
                                    ({'A': 2, 'B': 3, 'C': 1}, {'A': 2, 'B': 3, 'C': 1})):
                saved = dict(moves)
                if outcome == 'bug':
                    with self.assertRaisesRegex(ValueError, 'occupied target'):
                        operation(current, moves)
                else:
                    self.assertEqual(operation(current, moves), expected)
                self.assertEqual(current, {'A': 1, 'B': 2, 'C': 3})
                self.assertEqual(moves, saved)
            self.assertEqual(operation(current, {'A': 1}), {'A': 1, 'B': 2, 'C': 3})
            self.assertIsNot(operation(current, {}), current)
            for moves in ({'A': 3, 'B': 4}, {'A': 4, 'B': 4}, {'Z': 0}, {'A': True}, {'A': -1}, {'A': 6}):
                with self.assertRaises(ValueError):
                    operation(current, moves)
                self.assertEqual(current, {'A': 1, 'B': 2, 'C': 3})
            for invalid in ({'A': True}, {'A': 6}, {'A': 1, 'B': 1}):
                with self.assertRaises(ValueError):
                    operation(invalid, {})

    def test_net_funding_through_real_api(self):
        for outcome in ('original', 'bug', 'clean'):
            operation = api('checkout', outcome)
            for amounts, expected in (((1000, 400, 600), {'charged': 600, 'remaining': 0}),
                                       ((1000, 1000, 0), {'charged': 0, 'remaining': 0})):
                if outcome == 'bug':
                    with self.assertRaisesRegex(ValueError, 'insufficient wallet'):
                        operation(*amounts)
                else:
                    self.assertEqual(operation(*amounts), expected)
            self.assertEqual(operation(1000, 400, 1200), {'charged': 600, 'remaining': 600})
            for amounts in ((1000, 400, 599), (1000, 1001, 0), (True, 0, 1),
                            (1000, True, 1000), (1000, 0, True), (0, 0, 0),
                            (1000, -1, 1000), (1000, 0, -1)):
                with self.assertRaises(ValueError):
                    operation(*amounts)

    def test_visible_suites_pass_and_preservation_is_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            for case, adapter in cases.CASES.items():
                workspace = Path(temporary) / case
                before = adapter.preparation(case, workspace)
                result = subprocess.run([sys.executable, '-B', '-m', 'unittest'], cwd=workspace,
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                assessment = adapter.assessment(case, workspace, before, workspace)
                self.assertIsNone(assessment['passed'])
                self.assertTrue(assessment['scope_preserved'])
                self.assertEqual(adapter.entrypoint, 'skills/check/SKILL.md')
                self.assertFalse(adapter.allow_reviewers)
                self.assertNotIn(cases.judgment(case).get('expected_issue') or 'expected_issue',
                                 adapter.request)
                (workspace / 'extra.txt').write_text('changed')
                self.assertFalse(adapter.assessment(case, workspace, before, workspace)['scope_preserved'])

    def test_treatments_require_only_paragraph_removal(self):
        with tempfile.TemporaryDirectory() as temporary:
            roots = {name: Path(temporary) / name for name in ('current', 'without')}
            for root in roots.values():
                (root / 'skills/check').mkdir(parents=True)
                (root / 'snapshot-origin.json').write_text('{}')
            current = roots['current'] / 'skills/check/SKILL.md'
            without = roots['without'] / 'skills/check/SKILL.md'
            current.write_text('Header\n\nWhen acceptance rules change, exercise them.\n\nEnd\n')
            without.write_text('Header\n\nEnd\n')
            captured = runner.validate_treatments(roots)
            self.assertEqual(set(captured), {'current', 'without'})
            without.write_text('Header\n\nDifferent\n')
            with self.assertRaisesRegex(ValueError, 'remove only'):
                runner.validate_treatments(roots)
            without.write_text('Header\n\nEnd\n')
            (roots['without'] / 'extra').write_text('drift')
            with self.assertRaisesRegex(ValueError, 'differ only'):
                runner.validate_treatments(roots)

    def test_driver_bounded_trials_and_manual_outcomes(self):
        plan = trial_plan(tuple(cases.CASES), ('current', 'without'), 1)
        self.assertEqual(len(plan), 8)
        self.assertEqual(len(set((case, variant) for case, _, variant in plan)), 8)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'auth.json').write_text('{}')
            def trial(case, variant, destination, *args, **kwargs):
                self.assertEqual(args[3], 37)
                self.assertIs(kwargs['case_adapter'], cases.CASES[case])
                destination.mkdir()
                (destination / 'final.txt').write_text('review')
                return dict(artifact={'passed': None, 'scope_preserved': True}, exit_code=0,
                            timed_out=False, preferences_unchanged=True, bundle_unchanged=True,
                            sessions=[{'parent_id': None, 'completed': True}])
            with patch.dict(os.environ, CODEX_HOME=str(root)), \
                 patch.object(runner, 'validate_treatments', return_value={'current': {}, 'without': {}}), \
                 patch.object(runner, 'source_identity', return_value={}), \
                 patch.object(runner, 'identity', return_value={}), \
                 patch.object(runner.subprocess, 'check_output', return_value='test-cli'), \
                 patch.object(runner, 'run_trial', side_effect=trial), \
                 patch('sys.argv', ['acceptance_compare', '--current', str(root / 'current'),
                                    '--without', str(root / 'without'), '--output', str(root / 'output'),
                                    '--timeout', '37']):
                runner.main()
            results = json.loads((root / 'output/results.json').read_text())
            self.assertEqual(len(results), 8)
            for result in results:
                self.assertTrue(result['execution_valid'])
                self.assertTrue(result['scope_preserved'])
                self.assertIsNone(result['artifact']['passed'])
                self.assertEqual(result['manual_judgment']['outcome_status'], 'pending')
