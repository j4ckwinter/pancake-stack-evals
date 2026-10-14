from contextlib import ExitStack
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from behavioral import compare


class InputGuardTests(unittest.TestCase):
    suites = ("workflow", "review", "comparison", "review-comparison",
              "validation", "repository-review", "historical-review", "context-recovery")

    def exercise(self, suite, changed=None, timing=None):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            repositories = {}
            for name in ("source", "evaluator"):
                repositories[name] = root / name
                subprocess.run(
                    ["git", "clone", "--shared", "--no-checkout", str(compare.EVALUATOR),
                     str(repositories[name])], check=True, capture_output=True)
                (repositories[name] / "input.txt").write_text("original")
            auth = root / "auth.json"
            auth.write_text("test credential")
            poteto = root / "poteto"
            skill = poteto / "poteto-mode/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("Read ../poteto-mode/references/codex-port.md")
            references = skill.parent / "references"
            references.mkdir()
            (references / "codex-port.md").write_text("Codex adaptation")
            output = root / "output"
            command = ["compare", "--suite", suite, "--model", "test",
                       "--repetitions", "1", "--output", str(output)]
            if suite in ("comparison", "review-comparison"):
                command += ["--poteto-source", str(poteto)]
            original_write = compare.write_json
            original_check_output = subprocess.check_output

            def change():
                path = skill if changed == "poteto" else repositories[changed] / "input.txt"
                path.write_text(path.read_text() + " changed")

            def write(path, value):
                original_write(path, value)
                if timing == "before" and path.name == "manifest.json":
                    change()

            def check_output(command, **kwargs):
                if command == ["codex", "--version"]:
                    return "test-cli\n"
                return original_check_output(command, **kwargs)

            def trial(case, variant, destination, *args):
                destination.mkdir()
                result = {"case": case, "variant": variant, "artifact": {"passed": True},
                          "elapsed_seconds": 1, "exit_code": 0, "sessions": ["retained-session"]}
                (destination / "candidate.txt").write_text("retained candidate evidence")
                original_write(destination / "result.json", result)
                if timing == "during":
                    change()
                return result

            stack.enter_context(patch.object(compare, "ROOT", repositories["source"]))
            stack.enter_context(patch.object(compare, "EVALUATOR", repositories["evaluator"]))
            stack.enter_context(patch.object(compare, "run_trial", side_effect=trial))
            stack.enter_context(patch.object(compare, "write_json", side_effect=write))
            stack.enter_context(patch.object(subprocess, "check_output", side_effect=check_output))
            stack.enter_context(patch("behavioral.validation.treatment_hashes", return_value={}))
            stack.enter_context(patch("behavioral.repository_review.provenance", return_value={}))
            stack.enter_context(patch.dict(os.environ, {"CODEX_HOME": str(root)}))
            stack.enter_context(patch.object(sys, "argv", command))
            if timing:
                message = "since manifest capture" if timing == "before" else "during execution"
                with self.assertRaisesRegex(SystemExit, message):
                    compare.main()
            else:
                compare.main()
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(manifest["suite"], suite)
            self.assertIn("input.txt", manifest["source"]["file_hashes"])
            self.assertIn("input.txt", manifest["evaluator"]["file_hashes"])
            if timing == "before":
                self.assertEqual(sorted(p.name for p in output.iterdir()), ["manifest.json"])
                return
            results = json.loads((output / "results.json").read_text())
            expected_plan = manifest["plan"][:1] if timing == "during" else manifest["plan"]
            expected = [
                {"case": case, "variant": variant, "artifact": {"passed": True},
                 "elapsed_seconds": 1, "exit_code": 0, "sessions": ["retained-session"],
                 "inputs_unchanged": timing is None, "repetition": repeat}
                for case, repeat, variant in expected_plan
            ]
            self.assertEqual(results, expected)
            self.assertEqual(sorted(p.name for p in output.glob("run-*")),
                             [f"run-{n:02d}" for n in range(1, len(expected) + 1)])
            for index, result in enumerate(expected, 1):
                run = output / f"run-{index:02d}"
                self.assertEqual((run / "candidate.txt").read_text(), "retained candidate evidence")
                self.assertEqual(json.loads((run / "result.json").read_text()),
                                 {key: value for key, value in result.items() if key != "repetition"})

    def test_changed_repository_stops_before_first_trial(self):
        for suite in self.suites:
            for changed in ("source", "evaluator"):
                with self.subTest(suite=suite, changed=changed):
                    self.exercise(suite, changed, "before")

    def test_changed_repository_preserves_trial_and_stops_batch(self):
        for suite in self.suites:
            for changed in ("source", "evaluator"):
                with self.subTest(suite=suite, changed=changed):
                    self.exercise(suite, changed, "during")

    def test_unchanged_inputs_complete_batch(self):
        for suite in self.suites:
            with self.subTest(suite=suite):
                self.exercise(suite)

    def test_poteto_changes_still_stop_comparison_batches(self):
        for suite in ("comparison", "review-comparison"):
            for timing in ("before", "during"):
                with self.subTest(suite=suite, timing=timing):
                    self.exercise(suite, "poteto", timing)
