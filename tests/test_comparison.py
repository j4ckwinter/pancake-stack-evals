import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from behavioral.compare import collect_sessions, poteto_inventory, run_trial, trial_plan


class ComparisonTests(unittest.TestCase):
    def make_poteto(self, root):
        for name in ("poteto-mode", "helper"):
            directory = root / name
            directory.mkdir(parents=True)
            (directory / "SKILL.md").write_text(
                "Read [port](../poteto-mode/references/codex-port.md).")
        references = root / "poteto-mode/references"
        references.mkdir()
        (references / "codex-port.md").write_text("Codex adaptation")
        (references / "origin.json").write_text('{"commit": "test"}')
        (root / "unrelated").mkdir()
        (root / "unrelated/SKILL.md").write_text("Unrelated skill")
        (root / "pstack-models.json").write_text("private preferences")

    def test_poteto_inventory_selects_full_bundles_and_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "entrypoint|contain"):
                poteto_inventory(root)
            self.make_poteto(root)
            inventory = poteto_inventory(root)
            self.assertEqual(inventory["skills"], ["helper", "poteto-mode"])
            self.assertEqual(len(inventory["files"]), 4)
            self.assertEqual(inventory["origin"], {"commit": "test"})
            self.assertEqual(inventory["unresolved_relative_links"], [])
            (root / "helper/escape").symlink_to(root / "pstack-models.json")
            with self.assertRaisesRegex(ValueError, "symlink"):
                poteto_inventory(root)

    def test_three_arm_rotation_balances_each_case_over_three_repeats(self):
        variants = ("baseline", "pancake", "poteto")
        plan = trial_plan(("label", "contract"), variants, 3, rotate=True)
        self.assertEqual(len(plan), 18)
        for case in ("label", "contract"):
            orders = [[variant for item, repeat, variant in plan if item == case and repeat == n]
                      for n in (1, 2, 3)]
            for position in range(3):
                self.assertEqual({order[position] for order in orders}, set(variants))
        self.assertEqual(trial_plan(("x",), variants[:2], 2),
                         [("x", 1, "baseline"), ("x", 1, "pancake"),
                          ("x", 2, "pancake"), ("x", 2, "baseline")])

    def test_comparison_arms_share_scope_and_copy_only_selected_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "skills"
            self.make_poteto(source)
            auth = root / "auth"
            auth.write_text("fake credential")
            prompts = []
            commands = []
            for variant in ("baseline", "pancake", "poteto"):
                run = root / variant
                run.mkdir()
                def candidate(prompt, **kwargs):
                    prompts.append(prompt.split("\nUse the ")[0])
                    self.assertNotIn("comparison", prompt)
                    self.assertIn("read saved preferences", prompt)
                    self.assertIn("Scoped implementation delegates", prompt)
                    self.assertFalse((run / "profile/skills").exists())
                    self.assertFalse((run / "workspace/support.py").exists())
                    if variant == "poteto":
                        self.assertEqual(set(p.name for p in (run / "bundle/skills").iterdir()),
                                         {"poteto-mode", "helper"})
                        self.assertFalse((run / "bundle/skills/pstack-models.json").exists())
                with patch("behavioral.compare.tempfile.mkdtemp", return_value=str(run)), \
                        patch("behavioral.compare.subprocess.Popen") as launch, \
                        patch("behavioral.compare.assess_candidate", return_value={"passed": False}):
                    process = launch.return_value
                    process.communicate.side_effect = candidate
                    process.returncode = 0
                    process.poll.return_value = 0
                    result = run_trial("label", variant, root / (variant + "-evidence"),
                                       auth, "model", "medium", 10, "comparison", source)
                commands.append(launch.call_args.args[0])
                self.assertIn("completed_workers", result)
                self.assertNotIn("completed_reviewers", result)
                self.assertFalse(run.exists())
            self.assertEqual(len(set(prompts)), 1)
            for command in commands:
                self.assertIn("agents.max_threads=2", command)
                self.assertEqual(command[command.index("--sandbox") + 1], "workspace-write")
            self.assertEqual(auth.read_text(), "fake credential")

    def test_timeout_removes_profile_credentials_and_retains_result(self):
        import subprocess
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "project"
            run.mkdir()
            auth = root / "auth"
            auth.write_text("fake credential")
            destination = root / "evidence"
            with patch("behavioral.compare.tempfile.mkdtemp", return_value=str(run)), \
                    patch("behavioral.compare.subprocess.Popen") as launch, \
                    patch("behavioral.compare.os.killpg") as kill, \
                    patch("behavioral.compare.assess_candidate", return_value={"passed": False}):
                process = launch.return_value
                process.communicate.side_effect = [subprocess.TimeoutExpired("codex", 1), None]
                process.returncode = -9
                process.poll.return_value = -9
                result = run_trial("label", "baseline", destination, auth,
                                   "model", "medium", 1, "comparison")
            self.assertTrue(result["timed_out"])
            kill.assert_called_once()
            self.assertFalse(run.exists())
            self.assertTrue((destination / "result.json").is_file())
            self.assertEqual(auth.read_text(), "fake credential")

    def test_repository_review_shares_scope_and_pins_poteto_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "skills"
            self.make_poteto(source)
            expected = poteto_inventory(source)
            auth = root / "auth"
            auth.write_text("fake credential")
            prompts = []
            for variant in ("baseline", "pancake", "poteto"):
                run = root / variant
                run.mkdir()

                def candidate(prompt, **kwargs):
                    prompts.append(prompt.split("\nUse the ")[0])
                    self.assertIn("Do not delegate", prompt)
                    self.assertIn("read or change preferences", prompt)
                    self.assertTrue((run / "workspace/change.diff").is_file())
                    self.assertFalse((run / "profile/skills").exists())
                    if variant == "poteto":
                        self.assertIn("Use the Poteto skill", prompt)
                        self.assertNotIn("Use the Pancake skill", prompt)
                        self.assertEqual(poteto_inventory(run / "bundle/skills"), expected)
                    elif variant == "baseline":
                        self.assertFalse((run / "bundle").exists())

                with patch("behavioral.compare.tempfile.mkdtemp", return_value=str(run)), \
                        patch("behavioral.compare.subprocess.Popen") as launch:
                    process = launch.return_value
                    process.communicate.side_effect = candidate
                    process.returncode = 0
                    process.poll.return_value = 0
                    result = run_trial("identity-clean", variant, root / (variant + "-records"),
                                       auth, None, None, 10, "repository-review", source,
                                       expected if variant == "poteto" else None)
                command = launch.call_args.args[0]
                self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
                self.assertEqual(command[command.index("--disable") + 1], "multi_agent")
                self.assertNotIn("--enable", command)
                self.assertTrue(result["artifact"]["passed"])
                self.assertTrue(result["preferences_unchanged"])
                self.assertFalse(run.exists())
            self.assertEqual(len(set(prompts)), 1)
            (source / "helper/SKILL.md").write_text("Changed")
            with self.assertRaisesRegex(ValueError, "changed since manifest"):
                run_trial("identity-clean", "poteto", root / "changed", auth,
                          None, None, 10, "repository-review", source, expected)
            self.assertFalse((root / "changed").exists())

    def test_changed_poteto_input_is_rejected_before_preparation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "skills"
            self.make_poteto(source)
            expected = poteto_inventory(source)
            (source / "helper/SKILL.md").write_text(
                (source / "helper/SKILL.md").read_text() + " Changed.")
            with self.assertRaisesRegex(ValueError, "changed since manifest"):
                run_trial("label", "poteto", root / "output", root / "auth",
                          "model", None, 1, "comparison", source, expected)
            self.assertFalse((root / "output").exists())

    def test_preparation_and_retention_errors_clean_temporary_projects(self):
        import shutil
        for stage in ("preparation", "retention"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                run = root / "project"
                run.mkdir()
                auth = root / "auth"
                auth.write_text("fake credential")
                original_copy = shutil.copytree
                def copy(source, destination, *args, **kwargs):
                    if stage == "preparation" or Path(destination).name == "raw-sessions":
                        raise OSError("injected copy failure")
                    return original_copy(source, destination, *args, **kwargs)
                def candidate(*args, **kwargs):
                    (run / "profile/sessions").mkdir()
                with patch("behavioral.compare.tempfile.mkdtemp", return_value=str(run)), \
                        patch("behavioral.compare.shutil.copytree", side_effect=copy), \
                        patch("behavioral.compare.subprocess.Popen") as launch, \
                        patch("behavioral.compare.assess_candidate", return_value={"passed": False}):
                    process = launch.return_value
                    process.communicate.side_effect = candidate
                    process.returncode = 0
                    process.poll.return_value = 0
                    with self.assertRaisesRegex(OSError, "injected"):
                        run_trial("label", "baseline", root / "output", auth,
                                  "model", None, 1, "comparison")
                self.assertFalse(run.exists())
                self.assertEqual(auth.read_text(), "fake credential")

    def test_worker_usage_excludes_inherited_events(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory)
            sessions = profile / "sessions"
            sessions.mkdir()
            path = sessions / "worker.jsonl"
            events = [
                {"type": "session_meta", "payload": {
                    "id": "worker", "timestamp": "2026-10-07T12:00:00Z"}},
                {"timestamp": "2026-10-07T11:59:00Z", "type": "event_msg",
                 "payload": {"type": "token_count", "info": {
                     "total_token_usage": {"total_tokens": 1000}}}},
                {"timestamp": "2026-10-07T11:59:00Z", "type": "response_item",
                 "payload": {"type": "function_call", "name": "exec_command", "arguments": "{}"}},
                {"timestamp": "2026-10-07T11:59:00Z", "type": "event_msg",
                 "payload": {"type": "item_completed", "item": {"type": "CommandExecution"}}},
            ]
            path.write_text("\n".join(map(json.dumps, events)))
            result = collect_sessions(profile)[0]
            self.assertIsNone(result["usage"])
            self.assertEqual(result["tool_calls"], 0)
            self.assertEqual(result["command_actions"], 0)
            events.extend([
                {"timestamp": "2026-10-07T12:01:00Z", "type": "event_msg",
                 "payload": {"type": "token_count", "info": {
                     "total_token_usage": {"total_tokens": 50}}}},
                {"timestamp": "2026-10-07T12:01:00Z", "type": "response_item",
                 "payload": {"type": "custom_tool_call", "name": "apply_patch"}},
                {"timestamp": "2026-10-07T12:01:00Z", "type": "event_msg",
                 "payload": {"type": "item_completed", "item": {"type": "CommandExecution"}}},
            ])
            path.write_text("\n".join(map(json.dumps, events)))
            result = collect_sessions(profile)[0]
            self.assertEqual(result["usage"], {"total_tokens": 50})
            self.assertEqual(result["tool_calls"], 1)
            self.assertEqual(result["command_actions"], 1)

    def test_review_runner_uses_read_only_bundle_without_exposing_truth(self):
        from behavioral.review import consolidate
        from behavioral.compare import ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            auth = root / "source-auth"
            auth.write_text("fake test credential")
            for index, variant in enumerate(("baseline", "consolidated")):
                run = root / f"project-{index}"
                run.mkdir()
                def candidate(*args, **kwargs):
                    source = (ROOT / "skills/check/SKILL.md").read_text()
                    expected = consolidate(source) if variant == "consolidated" else source
                    self.assertEqual((run / "bundle/skills/check/SKILL.md").read_text(), expected)
                    prompt = args[0]
                    self.assertNotIn("keyword-api", prompt)
                    self.assertNotIn(variant, prompt)
                    self.assertFalse((run / "workspace/review.py").exists())
                destination = root / (variant + "-evidence")
                with patch("behavioral.compare.tempfile.mkdtemp", return_value=str(run)), \
                        patch("behavioral.compare.subprocess.Popen") as launch:
                    process = launch.return_value
                    process.communicate.side_effect = candidate
                    process.returncode = 0
                    process.poll.return_value = 0
                    result = run_trial("keyword", variant, destination, auth, "model", None, 10, "review")
                command = launch.call_args.args[0]
                self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
                self.assertFalse(any("model_reasoning_effort=" in arg for arg in command))
                self.assertEqual(result["run_id"], destination.name)
                self.assertTrue(result["artifact"]["passed"])
                self.assertFalse(run.exists())

    def test_rejected_symlink_keeps_result_and_removes_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "candidate"
            run.mkdir()
            auth = root / "source-auth"
            auth.write_text("fake test credential")
            destination = root / "evidence"

            def candidate(*args, **kwargs):
                (run / "workspace/shortcut").symlink_to(root / "outside")

            with patch("behavioral.compare.tempfile.mkdtemp", return_value=str(run)), \
                    patch("behavioral.compare.subprocess.Popen") as launch, \
                    patch("behavioral.compare.assess_candidate", return_value={"passed": False}):
                process = launch.return_value
                process.communicate.side_effect = candidate
                process.returncode = 0
                process.poll.return_value = 0
                result = run_trial("exporter", "baseline", destination, auth, "model", "medium", 10)
            self.assertFalse(result["artifact"]["passed"])
            self.assertIn("snapshot_error", result["after"])
            self.assertTrue((destination / "result.json").is_file())
            self.assertTrue((destination / "workspace/shortcut").is_symlink())
            self.assertFalse(run.exists())
            self.assertEqual(auth.read_text(), "fake test credential")


if __name__ == "__main__":
    unittest.main()
