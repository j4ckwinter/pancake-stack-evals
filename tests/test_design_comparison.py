import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from behavioral import design
from behavioral.compare import run_trial
from behavioral.support import snapshot
from target import source_root


class DesignComparisonTests(unittest.TestCase):
    def test_candidate_material_excludes_assessor_and_treatment(self):
        with tempfile.TemporaryDirectory() as temporary:
            for case, request in design.REQUESTS.items():
                workspace = Path(temporary) / case
                before = design.prepare_case(case, workspace)
                self.assertEqual(before, snapshot(workspace))
                self.assertTrue(before)
                material = request + ''.join(p.read_text() for p in workspace.iterdir())
                for secret in ('RUBRIC', 'baseline', 'candidate', 'judge_packet', 'passed, failed'):
                    self.assertNotIn(secret, material)
                self.assertNotEqual(set(before), {'README.md'})

    def test_runner_default_model_read_only_and_credential_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            auth = root / 'auth.json'
            auth.write_text('{"fake": true}')
            destination = root / 'run'
            observed = {}
            def reject_launch(command, **kwargs):
                observed['command'] = command
                observed['profile'] = Path(kwargs['env']['CODEX_HOME'])
                self.assertTrue((observed['profile'] / 'auth.json').is_file())
                raise RuntimeError('simulated launch failure')
            with patch('behavioral.compare.subprocess.Popen', side_effect=reject_launch):
                with self.assertRaisesRegex(RuntimeError, 'simulated launch failure'):
                    run_trial('independent', 'pancake', destination, auth, None, None, 10,
                              suite='design', source=source_root())
            command = observed['command']
            self.assertNotIn('-m', command)
            self.assertFalse(any('model_reasoning_effort' in arg for arg in command))
            self.assertEqual(command[command.index('--sandbox') + 1], 'read-only')
            self.assertIn('agents.max_threads=4', command)
            self.assertFalse(observed['profile'].exists())
            self.assertEqual(auth.read_text(), '{"fake": true}')
            prompt = (destination / 'prompt.txt').read_text()
            self.assertIn('/skills/design/SKILL.md', prompt)
            self.assertNotIn('RUBRIC', prompt)
            self.assertNotIn('baseline', prompt)


    def test_invalid_completion_or_preservation_stops_continuation(self):
        from behavioral.design_compare import trial_valid
        good = dict(inputs_unchanged=True, exit_code=0, timed_out=False,
                    artifact={'passed': True}, preferences_unchanged=True, final_response_present=True,
                    sessions=[{'parent_id': None, 'completed': True}])
        self.assertTrue(trial_valid(good))
        for key, bad in [('inputs_unchanged', False), ('exit_code', 1),
                         ('timed_out', True), ('final_response_present', False), ('artifact', {'passed': False}),
                         ('preferences_unchanged', False), ('sessions', []),
                         ('sessions', [{'parent_id': 'root', 'completed': True}]),
                         ('sessions', [{'parent_id': None, 'completed': False}])]:
            with self.subTest(key=key, value=bad):
                self.assertFalse(trial_valid(dict(good, **{key: bad})))

    def test_parallel_entrypoint_starts_at_shared_routing_reference(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            auth = root / 'auth.json'
            auth.write_text('{}')
            with patch('behavioral.compare.subprocess.Popen', side_effect=RuntimeError('stop')):
                with self.assertRaisesRegex(RuntimeError, 'stop'):
                    run_trial('independent', 'pancake', root / 'run', auth, None, None, 10,
                              suite='design', source=source_root(), design_entrypoint='parallel-work')
            prompt = (root / 'run/prompt.txt').read_text()
            self.assertIn('/skills/pancake/references/parallel-work.md', prompt)
            self.assertNotIn('/skills/design/SKILL.md', prompt)


    def test_main_stops_after_invalid_trial_and_records_empty_final(self):
        from behavioral import design_compare as runner
        import os
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'auth.json').write_text('{}')
            for failure in ('artifact', 'final'):
                output = root / failure
                def fake_trial(case, variant, destination, *args, **kwargs):
                    destination.mkdir()
                    if failure != 'final':
                        (destination / 'final.txt').write_text('proposal')
                    return dict(run_id=destination.name, artifact={'passed': failure != 'artifact'},
                        elapsed_seconds=1, exit_code=0, timed_out=False, preferences_unchanged=True,
                        sessions=[{'parent_id': None, 'completed': True}])
                with patch.dict(os.environ, CODEX_HOME=str(root)), \
                     patch.object(runner, 'source_identity', return_value={'files': {}}), \
                     patch.object(runner, 'identity', return_value={'revision': 'fixed'}), \
                     patch.object(runner.subprocess, 'check_output', return_value='test-cli'), \
                     patch.object(runner, 'run_trial', side_effect=fake_trial) as launch, \
                     patch('sys.argv', ['design_compare', '--baseline', str(root / 'base'),
                           '--candidate', str(root / 'candidate'), '--output', str(output),
                           '--cases', 'interface']):
                    with self.assertRaisesRegex(SystemExit, 'Invalid trial'):
                        runner.main()
                    self.assertEqual(launch.call_count, 1)
                records = json.loads((output / 'results.json').read_text())
                self.assertEqual(len(records), 1)
                self.assertEqual(records[0]['final_response_present'], failure != 'final')

    def test_main_detects_input_drift_before_launch(self):
        from behavioral import design_compare as runner
        import os
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'auth.json').write_text('{}')
            for changed in ('source', 'evaluator'):
                source_values = [{'files': {}}, {'files': {}}, {'files': {'changed': 'hash'}}]
                evaluator_values = [{'revision': 'before'}, {'revision': 'after'}]
                with patch.dict(os.environ, CODEX_HOME=str(root)), \
                     patch.object(runner, 'source_identity', side_effect=source_values if changed == 'source' else None, return_value={'files': {}}), \
                     patch.object(runner, 'identity', side_effect=evaluator_values if changed == 'evaluator' else None, return_value={'revision': 'fixed'}), \
                     patch.object(runner.subprocess, 'check_output', return_value='test-cli'), \
                     patch.object(runner, 'run_trial') as launch, \
                     patch('sys.argv', ['design_compare', '--baseline', str(root / 'base'),
                           '--candidate', str(root / 'candidate'), '--output', str(root / changed)]):
                    with self.assertRaisesRegex(SystemExit, 'Inputs changed'):
                        runner.main()
                    launch.assert_not_called()
