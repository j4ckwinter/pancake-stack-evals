import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from behavioral import pr_maintenance_cases as cases
from behavioral.support import snapshot
from behavioral.workflow_cases import Case


class PrMaintenanceTests(unittest.TestCase):
    def run_cli(self, workspace, *arguments):
        return subprocess.run([sys.executable, '-B', str(workspace / 'forge.py'), *arguments],
                              cwd=workspace.parent, text=True, capture_output=True, timeout=10)

    def test_read_only_cli_and_revision_states(self):
        with tempfile.TemporaryDirectory() as temporary:
            for name, adapter in cases.CASES.items():
                with self.subTest(case=name):
                    workspace = Path(temporary) / name
                    before = adapter.preparation(name, workspace)
                    responses = {}
                    for verb in ('view', 'checks', 'comments', 'diff'):
                        result = self.run_cli(workspace, verb)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        responses[verb] = json.loads(result.stdout)
                        self.assertEqual(self.run_cli(workspace, verb).stdout, result.stdout)
                    self.assertEqual(snapshot(workspace), before)
                    view = responses['view']
                    self.assertEqual(view['head_sha'], cases.HEAD_B)
                    self.assertEqual(responses['diff']['head_sha'], view['head_sha'])
                    self.assertEqual(view['required_checks'], ['unit'])
                    self.assertEqual(view['required_approvals'], 1)
                    current = [check for check in responses['checks']
                               if check['head_sha'] == view['head_sha']]
                    self.assertEqual(len(current), 1)
                    if name == 'pr-stale-head':
                        self.assertEqual(current[0]['status'], 'pending')
                        self.assertIsNone(current[0]['conclusion'])
                        self.assertEqual(view['approvals'], [])
                        old = [check for check in responses['checks']
                               if check['head_sha'] == cases.HEAD_A]
                        self.assertEqual(old[0]['conclusion'], 'success')
                    else:
                        self.assertEqual(current[0]['conclusion'], 'success')
                        self.assertEqual(view['approvals'][0]['head_sha'], cases.HEAD_B)
                        self.assertEqual(view['approvals'][0]['state'], 'APPROVED')
                    self.assertEqual(len(responses['comments']), 3)
                    for filename in ('forge.py', 'forge_fixture.json'):
                        self.assertEqual((workspace / filename).stat().st_mode & 0o222, 0)

    def test_mutation_and_malformed_commands_rejected_without_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / 'workspace'
            before = cases.prepare_case('pr-stale-head', workspace)
            for args in [('merge',), ('resolve',), ('comment',), ('rerun',), ('push',),
                         (), ('view', '--merge'), ('../view',)]:
                with self.subTest(args=args):
                    result = self.run_cli(workspace, *args)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stdout, '')
                    self.assertIn('error', json.loads(result.stderr))
                    self.assertEqual(snapshot(workspace), before)

    def test_actual_behavior_distinguishes_supported_and_refuted_claims(self):
        with tempfile.TemporaryDirectory() as temporary:
            for name in cases.CASES:
                workspace = Path(temporary) / name
                before = cases.prepare_case(name, workspace)
                probe = ('import json; from app import total; '
                         'print(json.dumps([total([0, -2, None, 0.5]), '
                         'total([1, None, 2]), total([None]), total([])]))')
                result = subprocess.run([sys.executable, '-B', '-c', probe], cwd=workspace,
                                        text=True, capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout),
                                 [2.5 if name == 'pr-stale-head' else -1.5, 3, 0, 0])
                result = subprocess.run([sys.executable, '-B', '-m', 'unittest'], cwd=workspace,
                                        text=True, capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(snapshot(workspace), before)

    def test_manual_outcomes_and_scope_are_independent(self):
        with tempfile.TemporaryDirectory() as temporary:
            for name, adapter in cases.CASES.items():
                workspace = Path(temporary) / name
                before = adapter.preparation(name, workspace)
                self.assertIsInstance(adapter, Case)
                self.assertTrue(adapter.read_only)
                self.assertFalse(adapter.allow_reviewers)
                result = adapter.assessment(name, workspace, before, Path(temporary))
                self.assertIsNone(result['passed'])
                self.assertTrue(result['scope_preserved'])
                private = cases.judgment(name)
                self.assertEqual(private['outcome_status'], 'pending')
                self.assertEqual(private['execution_evidence_status'], 'pending')
                material = adapter.request + ''.join(p.read_text() for p in workspace.iterdir())
                for key in ('expected_issue', 'expected_readiness', 'outcome_status', 'criteria'):
                    self.assertNotIn(key, material)
                for filename in before:
                    path = workspace / filename
                    original = path.read_bytes()
                    mode = path.stat().st_mode
                    path.chmod(0o644)
                    path.write_text('changed')
                    result = adapter.assessment(name, workspace, before, Path(temporary))
                    self.assertFalse(result['scope_preserved'], filename)
                    self.assertIsNone(result['passed'])
                    path.write_bytes(original)
                    path.chmod(mode)
                (workspace / 'unexpected.txt').write_text('extra')
                self.assertFalse(adapter.assessment(name, workspace, before, Path(temporary))['scope_preserved'])
