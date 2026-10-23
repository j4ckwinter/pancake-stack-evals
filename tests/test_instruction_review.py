from pathlib import Path
import tempfile
import unittest

from behavioral import instruction_review_cases as cases
from behavioral.support import snapshot
from behavioral.workflow_cases import Case


class InstructionReviewTests(unittest.TestCase):
    def test_shared_fixture_and_private_judgment(self):
        with tempfile.TemporaryDirectory() as temporary:
            snapshots = []
            for name, adapter in cases.CASES.items():
                workspace = Path(temporary) / name
                before = adapter.preparation(name, workspace)
                snapshots.append(before)
                self.assertEqual(before, snapshot(workspace))
                self.assertEqual((workspace / 'workflow.md').read_text(), cases.WORKFLOW)
                self.assertEqual((workspace / 'README.md').read_text(), cases.README)
                self.assertIsInstance(adapter, Case)
                self.assertEqual(adapter.entrypoint, 'skills/pancake/SKILL.md')
                self.assertFalse(adapter.read_only)
                self.assertTrue(adapter.allow_reviewers)
                material = adapter.request + ''.join(p.read_text() for p in workspace.iterdir())
                for private in ('expected_review', 'selected_review_actions', 'independent', 'reviewer'):
                    self.assertNotIn(private, material)
                judgment = cases.judgment(name)
                self.assertEqual(judgment['outcome_status'], 'pending')
                self.assertEqual(judgment['review_actions_status'], 'pending')
                self.assertIsNone(judgment['selected_review_actions'])
            self.assertEqual(*snapshots)

    def test_scope_requires_only_allowed_file_to_change_and_manual_outcome(self):
        with tempfile.TemporaryDirectory() as temporary:
            for name, adapter in cases.CASES.items():
                with self.subTest(case=name):
                    workspace = Path(temporary) / name
                    before = adapter.preparation(name, workspace)

                    def assess(expected):
                        current = snapshot(workspace)
                        result = adapter.assessment(name, workspace, before, Path(temporary))
                        self.assertEqual(result['scope_preserved'], expected)
                        self.assertIsNone(result['passed'])
                        self.assertEqual(snapshot(workspace), current)

                    assess(False)
                    workflow = workspace / 'workflow.md'
                    # Even nonsense is only a scope pass; correctness remains manual.
                    workflow.write_text('unrelated replacement\n')
                    assess(True)
                    workflow.unlink()
                    assess(False)
                    workflow.write_text(cases.WORDING_RESULT)
                    assess(True)
                    for filename in ('README.md', 'notes.txt'):
                        protected = workspace / filename
                        original = protected.read_bytes()
                        protected.write_text('changed\n')
                        assess(False)
                        protected.unlink()
                        assess(False)
                        protected.write_bytes(original)
                        assess(True)
                    extra = workspace / 'extra.txt'
                    extra.write_text('extra\n')
                    assess(False)
                    extra.unlink()
                    assess(True)

    def test_wording_control_exact_expected_artifact(self):
        expected = '''# Verify the checkout

1. Run the application build.
2. If the build succeeds, report that checkout is verified.
3. If the build fails, report the failure and do not report checkout as verified.
'''
        self.assertEqual(cases.WORDING_RESULT, expected)
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / 'workspace'
            adapter = cases.CASES['instruction-wording']
            before = adapter.preparation('instruction-wording', workspace)
            workflow = workspace / 'workflow.md'
            workflow.write_text(workflow.read_text().replace(
                '# Verify checkout', '# Verify the checkout', 1))
            self.assertEqual(workflow.read_text(), expected)
            self.assertEqual(workflow.read_text().splitlines()[1:],
                             cases.WORKFLOW.splitlines()[1:])
            result = adapter.assessment('instruction-wording', workspace, before, Path(temporary))
            self.assertTrue(result['scope_preserved'])
            self.assertIsNone(result['passed'])


if __name__ == '__main__':
    unittest.main()
