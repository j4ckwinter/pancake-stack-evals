import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

from behavioral import workflow_cases as cases, workflow_compare as runner
from behavioral.compare import run_trial
from behavioral.support import snapshot
from target import source_root


class WorkflowComparisonTests(unittest.TestCase):
    def test_trial_rejects_changed_supplied_bundle(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            auth = root / 'auth.json'
            auth.write_text('{}')
            adapter = replace(cases.CASES['ordinary-clean'],
                assessment=lambda *args: {'passed': True, 'scope_preserved': True})
            for mutate in (False, True):
                def launch(command, **kwargs):
                    profile = Path(kwargs['env']['CODEX_HOME'])
                    if mutate:
                        (profile.parent / 'bundle/skills/check/SKILL.md').write_text('replacement')
                    return SimpleNamespace(returncode=0, communicate=lambda *args, **kwargs: None,
                                           poll=lambda: 0)
                with patch('behavioral.compare.subprocess.Popen', side_effect=launch):
                    result = run_trial('ordinary-clean', 'pancake', root / str(mutate), auth,
                                       None, None, 10, source=source_root(), case_adapter=adapter)
                self.assertEqual(result['bundle_unchanged'], not mutate)
                self.assertEqual(result['artifact']['scope_preserved'], not mutate)

    def test_equivalent_refactor_and_edge_regression(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / 'project'
            before = cases.prepare_case('small-refactor', workspace)
            (workspace / 'app.py').write_text('def total(values):\n    return sum(v for v in values if v is not None)\n')
            cases.assess_refactor(workspace, before)
            (workspace / 'app.py').write_text('def total(values):\n    return sum(abs(v) for v in values if v is not None)\n')
            with self.assertRaises(AssertionError):
                cases.assess_refactor(workspace, before)
            (workspace / 'README.md').write_text('changed')
            with self.assertRaisesRegex(AssertionError, 'unrelated'):
                cases.assess_refactor(workspace, before)

    def test_review_fixtures_and_private_criteria(self):
        with tempfile.TemporaryDirectory() as temporary:
            for case, adapter in cases.CASES.items():
                workspace = Path(temporary) / case
                before = adapter.preparation(case, workspace)
                material = adapter.request + ''.join(p.read_text() for p in workspace.iterdir())
                for private in ('expected_issue', 'manual_checks', 'baseline', 'candidate', 'judgment'):
                    self.assertNotIn(private, material)
                if case == 'small-refactor':
                    continue
                self.assertTrue(adapter.assessment(case, workspace, before, Path(temporary))['passed'])
                result = subprocess.run([sys.executable, '-B', '-c', cases.PROBE], cwd=workspace,
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode == 0, case not in ('ordinary-bug', 'comment-bug', 'suppression-bug'))
                if case.startswith('comment-'):
                    comment = (workspace / 'app.py').read_text().splitlines()[0]
                    self.assertIn('preserve negative adjustments', comment)
                (workspace / 'app.py').write_text('changed')
                self.assertFalse(adapter.assessment(case, workspace, before, Path(temporary))['passed'])

    def test_adapter_cli_and_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            auth = root / 'auth.json'
            auth.write_text('{"fake": true}')
            for case in ('small-refactor', 'ordinary-clean'):
                observed = {}
                def reject(command, **kwargs):
                    observed.update(command=command, profile=Path(kwargs['env']['CODEX_HOME']))
                    self.assertTrue((observed['profile'] / 'auth.json').exists())
                    raise RuntimeError('simulated failure')
                with patch('behavioral.compare.subprocess.Popen', side_effect=reject):
                    with self.assertRaisesRegex(RuntimeError, 'simulated failure'):
                        run_trial(case, 'pancake', root / case, auth, None, None, 10,
                                  source=source_root(), case_adapter=cases.CASES[case])
                command = observed['command']
                self.assertNotIn('-m', command)
                self.assertFalse(any('model_reasoning_effort' in arg for arg in command))
                self.assertEqual(command[command.index('--disable') + 1], 'multi_agent')
                self.assertEqual(command[command.index('--sandbox') + 1],
                                 'workspace-write' if case == 'small-refactor' else 'read-only')
                self.assertFalse(observed['profile'].exists())
                prompt = (root / case / 'prompt.txt').read_text()
                self.assertIn(cases.CASES[case].entrypoint, prompt)
            self.assertEqual(auth.read_text(), '{"fake": true}')
            with self.assertRaisesRegex(ValueError, 'adapter requires'):
                run_trial('small-refactor', 'pancake', root / 'invalid', auth, None, None, 10,
                          suite='design', case_adapter=cases.CASES['small-refactor'])

    def test_assessor_uses_sandbox(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / 'workspace'
            before = cases.prepare_case('small-refactor', workspace)
            with patch.object(cases.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'failed')) as run:
                result = cases.assess_case('small-refactor', workspace, before, Path(temporary))
            self.assertFalse(result['passed'])
            self.assertTrue(result['scope_preserved'])
            self.assertEqual(run.call_args.args[0][:4], ['codex', 'sandbox', '--permission-profile', ':read-only'])

    def test_driver_pairs_failures_and_aborts_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'auth.json').write_text('{}')
            for drift in (False, True):
                output = root / str(drift)
                def fake_trial(case, variant, destination, *args, **kwargs):
                    destination.mkdir()
                    (destination / 'final.txt').write_text('done')
                    return dict(artifact={'passed': False, 'scope_preserved': True},
                                exit_code=0, timed_out=False, preferences_unchanged=True,
                                sessions=[{'parent_id': None, 'completed': True}])
                values = [{'files': {}}, {'files': {}}, {'files': {'changed': 'x'}}] if drift else None
                with patch.dict(os.environ, CODEX_HOME=str(root)), \
                     patch.object(runner, 'source_identity', side_effect=values, return_value={'files': {}}), \
                     patch.object(runner, 'identity', return_value={'revision': 'fixed'}), \
                     patch.object(runner.subprocess, 'check_output', return_value='test-cli'), \
                     patch.object(runner, 'run_trial', side_effect=fake_trial) as launch, \
                     patch('sys.argv', ['workflow_compare', '--baseline', str(root / 'base'),
                           '--candidate', str(root / 'candidate'), '--output', str(output),
                           '--cases', 'small-refactor']):
                    if drift:
                        with self.assertRaisesRegex(SystemExit, 'Inputs changed'):
                            runner.main()
                        launch.assert_not_called()
                    else:
                        runner.main()
                        self.assertEqual(launch.call_count, 2)
                        records = json.loads((output / 'results.json').read_text())
                        self.assertEqual([r['variant'] for r in records], ['baseline', 'candidate'])
                        self.assertTrue(all(r['execution_valid'] and not r['artifact']['passed'] for r in records))
