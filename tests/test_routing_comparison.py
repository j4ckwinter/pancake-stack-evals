import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

from behavioral import routing_cases as cases, routing_compare as runner
from behavioral.compare import run_trial, skill_catalog, trial_plan
from behavioral.context_recovery import git_environment
from behavioral.workflow_cases import Case
from target import source_root


class RoutingComparisonTests(unittest.TestCase):
    def test_discovery_modes_supply_only_their_intended_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            auth = root / 'auth.json'
            auth.write_text('{}')
            for mode in ('explicit', 'catalog', 'none'):
                observed = {}
                def launch(command, **kwargs):
                    project = Path(kwargs['env']['CODEX_HOME']).parent
                    observed['bundle'] = (project / 'bundle').exists()
                    observed['catalog'] = skill_catalog(project / 'bundle') if observed['bundle'] else []
                    return SimpleNamespace(returncode=0, communicate=lambda *args, **kwargs: None, poll=lambda: 0)
                adapter = replace(cases.CASES['trace'].adapter(mode), entrypoint='skills/how/SKILL.md')
                with patch('behavioral.compare.subprocess.Popen', side_effect=launch):
                    result = run_trial('trace', mode, root / mode, auth, None, None, 10,
                                       source=source_root(), case_adapter=adapter)
                prompt = (root / mode / 'prompt.txt').read_text()
                self.assertTrue(prompt.startswith(adapter.request))
                self.assertEqual(observed['bundle'], mode != 'none')
                self.assertTrue(result['bundle_unchanged'])
                self.assertEqual('Use the workflow at' in prompt, mode == 'explicit')
                self.assertEqual('Available skills' in prompt, mode == 'catalog')
                if mode == 'none':
                    self.assertNotIn('bundle', prompt)
                    self.assertNotIn('SKILL.md', prompt)
                if mode == 'catalog':
                    for item in observed['catalog']:
                        self.assertIn(f"{item['name']}: {item['description']} (file: {item['path']})", prompt)
                    self.assertNotIn('expected_route', prompt)
                self.assertIsNone(result['artifact']['passed'])
                self.assertTrue(result['artifact']['scope_preserved'])
        self.assertEqual(Case('task', 'path', True).discovery, 'explicit')
        with self.assertRaisesRegex(ValueError, 'discovery'):
            Case('task', 'path', True, discovery='forced')

    def test_catalog_matches_actual_frontmatter(self):
        source = source_root()
        catalog = skill_catalog(source)
        self.assertEqual(len(catalog), 19)
        for item in catalog:
            text = Path(item['path']).read_text().split('---')[1]
            self.assertIn('\nname: ' + item['name'] + '\n', text)
            self.assertIn('\ndescription: ' + item['description'] + '\n', text)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, 'complete'):
                skill_catalog(Path(temporary))

    def test_fixtures_keep_judgments_private_and_history_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            histories = []
            for name, item in cases.CASES.items():
                workspace = root / name
                before = item.adapter('catalog').preparation(name, workspace)
                for path in workspace.rglob('*'):
                    if path.is_file() and '.git' not in path.parts:
                        self.assertNotIn('expected_route', path.read_text())
                self.assertNotIn('expected_route', item.request)
                if item.setup == 'history':
                    history = subprocess.check_output(['git', 'log', '--format=%H'], cwd=workspace,
                                                      env=git_environment(os.environ), text=True)
                    histories.append(history)
                if item.setup != 'records':
                    self.assertTrue(cases.assess_case(name, workspace, before, root)['scope_preserved'])
                    (workspace / 'unrelated.txt').write_text('edit')
                    self.assertFalse(cases.assess_case(name, workspace, before, root)['scope_preserved'])
            self.assertEqual(len(histories), 2)
            self.assertEqual(histories[0], histories[1])
            self.assertEqual(len(histories[0].splitlines()), 2)
            snapshot = (root / 'status/pr-snapshot.txt').read_text()
            self.assertIn('unit FAILURE', snapshot)
            self.assertIn('CONFLICTING', snapshot)

    def test_pairs_and_driver_record_outcomes_separately(self):
        plan = trial_plan(list(cases.CASES), ('catalog', 'none'), 1)
        self.assertEqual(len(plan), 16)
        self.assertEqual([variant for _, _, variant in plan[:4]], ['catalog', 'none', 'none', 'catalog'])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'auth.json').write_text('{}')
            def trial(case, variant, destination, *args, **kwargs):
                destination.mkdir()
                (destination / 'final.txt').write_text('response')
                return dict(artifact={'passed': False, 'scope_preserved': True}, exit_code=0,
                            timed_out=False, preferences_unchanged=True, bundle_unchanged=True,
                            sessions=[{'parent_id': None, 'completed': True}])
            with patch.dict(os.environ, CODEX_HOME=str(root)), \
                 patch.object(runner, 'source_identity', return_value={}), \
                 patch.object(runner, 'identity', return_value={}), \
                 patch.object(runner, 'skill_catalog', return_value=[]), \
                 patch.object(runner.subprocess, 'check_output', return_value='test-cli'), \
                 patch.object(runner, 'run_trial', side_effect=trial), \
                 patch('sys.argv', ['routing_compare', '--source', str(root / 'source'),
                                    '--output', str(root / 'output'), '--cases', 'repair']):
                runner.main()
            records = json.loads((root / 'output/results.json').read_text())
            self.assertEqual(len(records), 2)
            for record in records:
                self.assertTrue(record['execution_valid'])
                self.assertFalse(record['artifact']['passed'])
                self.assertEqual(record['manual_judgment']['routing_status'], 'pending')
