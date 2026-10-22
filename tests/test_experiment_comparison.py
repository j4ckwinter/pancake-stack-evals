import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from behavioral import experiment_cases as cases, experiment_compare as runner
from behavioral.compare import trial_plan


def namespace(text):
    result = {}
    exec(text, result)
    return result


class ExperimentTests(unittest.TestCase):
    def test_performance_baseline_consumes_same_work(self):
        api = namespace(cases.IMPORTER)
        rows = namespace(cases.fixture_files('performance')['workload.py'])['rows']
        expected = api['current'](rows)
        lazy = api['proposed'](rows)
        self.assertIs(iter(lazy), lazy)
        self.assertEqual(len(expected), 18000)
        self.assertEqual(len(rows) - len(expected), 2000)
        self.assertEqual(list(lazy), expected)
        self.assertEqual(list(lazy), [])
        # Construction performs no hashing, exposing the supplied benchmark's flaw.
        with patch.object(api['hashlib'], 'sha256', side_effect=RuntimeError('work began')):
            lazy = api['proposed'](['row'])
            with self.assertRaisesRegex(RuntimeError, 'work began'):
                next(lazy)

    def test_prototype_distinguishes_atomic_failure(self):
        api = namespace(cases.STRATEGIES)
        inputs = json.loads(cases.fixture_files('prototype')['inputs.json'])
        for name in ('incremental', 'staged'):
            state = dict(inputs['initial'])
            self.assertEqual(api[name](state, inputs['success']), {'a': 1, 'b': 3})
            state = dict(inputs['initial'])
            with self.assertRaises(ValueError):
                api[name](state, inputs['failure'])
            self.assertEqual(state, {'a': 1, 'b': 3} if name == 'incremental' else {'a': 1})

    def test_evaluation_artifacts_disagree_with_claims(self):
        files = cases.fixture_files('skill-evaluation')
        self.assertEqual(namespace(files['sample-a/app.py'])['total']([-2, None, 1]), 3)
        self.assertEqual(namespace(files['sample-b/app.py'])['total']([-2, None, 1]), -1)
        self.assertNotEqual(files['sample-a/notes.txt'], files['baseline/notes.txt'])
        self.assertEqual(files['sample-b/notes.txt'], files['baseline/notes.txt'])
        self.assertIn('synthetic', files['README.md'])

    def test_scratch_scope_preserves_existing_files_and_separates_outcomes(self):
        with tempfile.TemporaryDirectory() as temporary:
            for case, adapter in cases.CASES.items():
                workspace = Path(temporary) / case
                before = adapter.preparation(case, workspace)
                self.assertFalse(adapter.read_only)
                self.assertFalse(adapter.allow_reviewers)
                self.assertEqual(adapter.entrypoint, 'skills/pancake/SKILL.md')
                (workspace / 'scratch/run').mkdir()
                (workspace / 'scratch/run/result.json').write_text('{}')
                result = adapter.assessment(case, workspace, before, workspace)
                self.assertTrue(result['scope_preserved'])
                self.assertIsNone(result['passed'])
                (workspace / 'scratch/keep.txt').write_text('destroyed')
                self.assertFalse(adapter.assessment(case, workspace, before, workspace)['scope_preserved'])
                (workspace / 'scratch/keep.txt').write_text(cases.fixture_files(case)['scratch/keep.txt'])
                (workspace / 'outside.txt').write_text('outside')
                self.assertFalse(adapter.assessment(case, workspace, before, workspace)['scope_preserved'])
                (workspace / 'outside.txt').unlink()
                (workspace / 'scratch/run/link').symlink_to(workspace / 'scratch/keep.txt')
                with self.assertRaises(ValueError):
                    adapter.assessment(case, workspace, before, workspace)

    def test_exact_extraction_and_unrelated_drift_rejection(self):
        original = ('# Shared\n\nKeep baseline.\n\n## Choose the experiment\n\n'
                    '### Performance\n\nMeasure completed work.\n\n'
                    '### Prototype\n\nObserve actual state.\n\n'
                    '### Skill evaluation\n\nInspect artifacts.\n\n'
                    '## Decide and clean up\n\nPreserve unrelated files.\n')
        with tempfile.TemporaryDirectory() as temporary:
            roots = {name: Path(temporary) / name for name in ('current', 'selective')}
            for root in roots.values():
                (root / runner.REFERENCE).parent.mkdir(parents=True)
                (root / 'snapshot-origin.json').write_text('{}')
            (roots['current'] / runner.REFERENCE).write_text(original)
            for name, content in runner.selective_files(original).items():
                (roots['selective'] / name).write_text(content)
            self.assertEqual(set(runner.validate_treatments(roots)), set(roots))
            selected = roots['selective'] / runner.REFERENCE
            selected.write_text(selected.read_text().replace('Keep baseline.', 'Omit baseline.'))
            with self.assertRaisesRegex(ValueError, 'preserve all'):
                runner.validate_treatments(roots)
            selected.write_text(runner.selective_files(original)[runner.REFERENCE])
            (roots['selective'] / 'extra.txt').write_text('drift')
            with self.assertRaisesRegex(ValueError, 'differ only'):
                runner.validate_treatments(roots)

    def test_bounded_driver_preserves_pending_manual_outcomes(self):
        self.assertEqual(len(trial_plan(tuple(cases.CASES), ('current', 'selective'), 1)), 6)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'auth.json').write_text('{}')
            def trial(case, variant, destination, *args, **kwargs):
                self.assertEqual(args[3], 37)
                self.assertIs(kwargs['case_adapter'], cases.CASES[case])
                destination.mkdir()
                (destination / 'final.txt').write_text('observations')
                return dict(artifact={'passed': None, 'scope_preserved': True}, exit_code=0,
                            timed_out=False, preferences_unchanged=True, bundle_unchanged=True,
                            sessions=[{'parent_id': None, 'completed': True}])
            with patch.dict(os.environ, CODEX_HOME=str(root)), \
                 patch.object(runner, 'validate_treatments', return_value={'current': {}, 'selective': {}}), \
                 patch.object(runner, 'source_identity', return_value={}), \
                 patch.object(runner, 'identity', return_value={}), \
                 patch.object(runner.subprocess, 'check_output', return_value='test-cli'), \
                 patch.object(runner, 'run_trial', side_effect=trial), \
                 patch('sys.argv', ['experiment_compare', '--current', str(root / 'current'),
                                    '--selective', str(root / 'selective'), '--output', str(root / 'output'),
                                    '--timeout', '37']):
                runner.main()
            results = json.loads((root / 'output/results.json').read_text())
            self.assertEqual(len(results), 6)
            for result in results:
                self.assertTrue(result['execution_valid'])
                self.assertTrue(result['scope_preserved'])
                self.assertIsNone(result['artifact']['passed'])
                self.assertEqual(result['manual_judgment']['outcome_status'], 'pending')
