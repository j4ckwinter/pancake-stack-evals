import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from behavioral.support import CASES, SCENARIOS, assess, prepare, snapshot


class BehavioralFixtureTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_preparation_copies_only_project_and_isolates_runs(self):
        before = prepare("delivery", self.root / "project")
        prepare("delivery", self.root / "other")
        self.assertEqual(set(before), {"app.py", "notes.txt"})
        (self.root / "project/notes.txt").write_text("changed")
        self.assertEqual(snapshot(self.root / "other"), before)
        self.assertEqual(snapshot(CASES / "delivery/workspace"), before)
        with self.assertRaises(FileExistsError):
            prepare("delivery", self.root / "project")

    def test_read_only_artifact_checks_exercise_baselines(self):
        for case in ("delivery", "checkout", "invoice", "exporter", "update"):
            with self.subTest(case=case):
                workspace = self.root / case
                before = prepare(case, workspace)
                self.assertEqual(assess(case, workspace, before), "artifact checks passed")

    def test_summary_baseline_crashes_through_command(self):
        workspace = self.root / "project"
        before = prepare("summary", workspace)
        result = subprocess.run([sys.executable, "-B", "app.py"], cwd=workspace,
                                input="[]", text=True, capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ZeroDivisionError", result.stderr)
        with self.assertRaises(AssertionError):
            assess("summary", workspace, before)

    def test_summary_checks_accept_fix_and_reject_constant_result(self):
        workspace = self.root / "project"
        before = prepare("summary", workspace)
        source = workspace / "app.py"
        source.write_text(source.read_text().replace(
            "sum(values) / len(values)", "sum(values) / len(values) if values else 0"))
        self.assertEqual(assess("summary", workspace, before), "artifact checks passed")
        source.write_text("import json\nprint(json.dumps({'count': 0, 'average': 0}))\n")
        with self.assertRaises(AssertionError):
            assess("summary", workspace, before)

    def test_review_fixture_has_passing_exporter_and_broken_consumer(self):
        workspace = self.root / "project"
        prepare("exporter", workspace)
        result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover"],
                                cwd=workspace, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([sys.executable, "-B", "-c",
                                 "from app import export_invoice; from consumer import read_total; "
                                 "print(read_total(export_invoice(19.5)))"],
                                cwd=workspace, text=True, capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("KeyError: 'total'", result.stderr)

    def test_records_checks_require_new_live_contract_and_old_archive(self):
        workspace = self.root / "project"
        before = prepare("records", workspace)
        with self.assertRaises(AssertionError):
            assess("records", workspace, before)
        (workspace / "producer.py").write_text("def create_invoice(total):\n    return {'amount': total}\n")
        (workspace / "consumer.py").write_text("def read_total(payload):\n    return payload['amount']\n")
        tests = workspace / "test_records.py"
        tests.write_text(tests.read_text().replace('{"total": 19.5}', '{"amount": 19.5}'))
        self.assertEqual(assess("records", workspace, before), "artifact checks passed")
        (workspace / "consumer.py").write_text("def read_total(payload):\n    return payload['total']\n")
        with self.assertRaises(AssertionError):
            assess("records", workspace, before)

    def test_records_rejects_parameter_rename_despite_passing_local_tests(self):
        workspace = self.root / "project"
        before = prepare("records", workspace)
        (workspace / "producer.py").write_text("def create_invoice(amount):\n    return {'amount': amount}\n")
        (workspace / "consumer.py").write_text("def read_total(payload):\n    return payload['amount']\n")
        tests = workspace / "test_records.py"
        tests.write_text(tests.read_text().replace('{"total": 19.5}', '{"amount": 19.5}'))
        result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover"],
                                cwd=workspace, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        with self.assertRaisesRegex(AssertionError, "unexpected keyword argument 'total'"):
            assess("records", workspace, before)
        (workspace / "producer.py").write_text("def create_invoice(total):\n    return {'amount': total}\n")
        self.assertEqual(assess("records", workspace, before), "artifact checks passed")
        (workspace / "billing.py").write_text("# caller removed\n")
        with self.assertRaisesRegex(AssertionError, "protected file changed: billing.py"):
            assess("records", workspace, before)

    def test_protected_changes_are_rejected_for_every_case(self):
        for case in SCENARIOS:
            with self.subTest(case=case):
                workspace = self.root / case
                before = prepare(case, workspace)
                (workspace / "notes.txt").write_text("unrelated edit")
                with self.assertRaises(AssertionError):
                    assess(case, workspace, before)

    def test_read_only_additions_and_deletions_are_rejected(self):
        workspace = self.root / "project"
        before = prepare("invoice", workspace)
        extra = workspace / "unexpected.txt"
        extra.write_text("extra")
        with self.assertRaises(AssertionError):
            assess("invoice", workspace, before)
        extra.unlink()
        (workspace / "notes.txt").unlink()
        with self.assertRaises(AssertionError):
            assess("invoice", workspace, before)

    def test_correction_additions_are_limited_to_regression_files(self):
        workspace = self.root / "project"
        before = prepare("summary", workspace)
        source = workspace / "app.py"
        source.write_text(source.read_text().replace(
            "sum(values) / len(values)", "sum(values) / len(values) if values else 0"))
        (workspace / "test_regression.py").write_text(
            "import unittest\nfrom app import summarize\n"
            "class Regression(unittest.TestCase):\n"
            "    def test_empty(self):\n"
            "        self.assertEqual(summarize([]), {'count': 0, 'average': 0})\n")
        self.assertEqual(assess("summary", workspace, before), "artifact checks passed")
        (workspace / "unrelated.txt").write_text("outside requested scope")
        with self.assertRaisesRegex(AssertionError, "unrelated file added"):
            assess("summary", workspace, before)

    def test_symlinks_cannot_hide_mutations(self):
        workspace = self.root / "project"
        prepare("invoice", workspace)
        (workspace / "shortcut").symlink_to(self.root / "outside")
        with self.assertRaises(ValueError):
            snapshot(workspace)

    def test_preference_trial_uses_real_helper_and_temporary_storage(self):
        from target import LEGACY
        helper = LEGACY / "skills/setup/scripts/preferences.py"
        config = self.root / "profile/pancake-stack/config.json"
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({
            "schemaVersion": 1,
            "defaults": {"model": None, "reasoningEffort": None},
            "roles": {
                "implementation": {"model": None, "reasoningEffort": None},
                "review": {"model": None, "reasoningEffort": None},
                "research": {"model": "unavailable-research-model",
                             "reasoningEffort": "unavailable-effort"},
            },
        }))
        before = config.read_bytes()
        result = subprocess.run([sys.executable, str(helper), "--config", str(config), "resolve"],
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "implementation": {"model": None, "reasoningEffort": None},
            "review": {"model": None, "reasoningEffort": None},
            "research": {"model": "unavailable-research-model",
                         "reasoningEffort": None},
        })
        self.assertEqual(config.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
