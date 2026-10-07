import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from target import LEGACY

ROOT = LEGACY
HELPER = ROOT / "skills/setup/scripts/preferences.py"
EXAMPLE = json.loads((ROOT / "config/preferences.example.json").read_text())


class PreferencesTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "nested/config.json"

    def run_cli(self, command, payload=None, *args):
        return subprocess.run(
            [sys.executable, str(HELPER), "--config", str(self.path), command, *args],
            input=payload, text=True, capture_output=True,
        )

    def test_missing_show_and_resolution_do_not_write(self):
        result = self.run_cli("show")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), EXAMPLE)
        result = self.run_cli("resolve")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "implementation": {"model": None, "reasoningEffort": None},
            "review": {"model": None, "reasoningEffort": None},
            "research": {"model": None, "reasoningEffort": None},
        })
        self.assertFalse(self.path.parent.exists())

    def test_save_round_trip_and_repeat(self):
        config = copy.deepcopy(EXAMPLE)
        config["defaults"]["model"] = "host-model"
        for _ in range(2):
            result = self.run_cli("save", json.dumps(config))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), config)
            self.assertEqual(json.loads(self.path.read_text()), config)
        self.assertEqual(json.loads(self.run_cli("show").stdout), config)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_mixed_inheritance(self):
        config = copy.deepcopy(EXAMPLE)
        config["defaults"]["reasoningEffort"] = "high"
        config["roles"]["review"]["model"] = "review-model"
        config["roles"]["research"]["reasoningEffort"] = "medium"
        self.assertEqual(self.run_cli("save", json.dumps(config)).returncode, 0)
        result = self.run_cli("resolve", None, "--host-model", "parent-model",
                              "--host-reasoning-effort", "low")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "implementation": {"model": "parent-model", "reasoningEffort": "low"},
            "review": {"model": "review-model", "reasoningEffort": "low"},
            "research": {"model": "parent-model", "reasoningEffort": "low"},
        })
        self.assertEqual(self.run_cli("save", json.dumps(EXAMPLE)).returncode, 0)
        result = self.run_cli("resolve", None, "--host-model", "parent-model",
                              "--host-reasoning-effort", "low")
        self.assertEqual(json.loads(result.stdout), {
            role: {"model": "parent-model", "reasoningEffort": "low"}
            for role in ("implementation", "review", "research")
        })

    def test_legacy_efforts_are_inactive_and_preserved_across_schemas(self):
        notice = ("preferences: Saved reasoning-effort values remain stored but are inactive. "
                  "Delegates inherit host effort unless the task explicitly requests an effort.\n")
        for version in (1, 2, 3):
            config = copy.deepcopy(EXAMPLE)
            config["schemaVersion"] = version
            config["defaults"] = {"model": "default-model", "reasoningEffort": "high"}
            config["roles"]["research"]["reasoningEffort"] = "low"
            if version >= 2:
                config["challengeReviewers"] = [
                    {"model": "duplicate-model", "reasoningEffort": "high"},
                    {"model": "duplicate-model", "reasoningEffort": "low"}]
            if version == 3:
                config["implementationReviewers"] = [
                    {"model": None, "reasoningEffort": "unsupported-legacy-effort"}]
            self.assertEqual(self.run_cli("save", json.dumps(config)).returncode, 0)
            original = self.path.read_bytes()
            for command in ("resolve", "resolve-challenge", "resolve-implementation-review"):
                with self.subTest(version=version, command=command):
                    result = self.run_cli(command, None, "--host-reasoning-effort", "medium")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stderr, notice)
                    if command == "resolve":
                        expected = {role: {"model": "default-model", "reasoningEffort": "medium"}
                                    for role in ("implementation", "review", "research")}
                    elif command == "resolve-challenge" and version >= 2:
                        expected = [{"model": "duplicate-model", "reasoningEffort": "medium"},
                                    {"model": "duplicate-model", "reasoningEffort": "medium"}]
                    else:
                        expected = [{"model": "default-model", "reasoningEffort": "medium"}]
                    self.assertEqual(json.loads(result.stdout), expected)
                    self.assertEqual(self.path.read_bytes(), original)
            config["roles"]["review"]["model"] = "changed-model"
            result = self.run_cli("save", json.dumps(config))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(self.run_cli("show").stdout), config)
            self.assertEqual(json.loads(self.run_cli("resolve").stdout)["review"],
                             {"model": "changed-model", "reasoningEffort": None})

    def test_panel_only_effort_disclosure_and_all_null_silence(self):
        config = copy.deepcopy(EXAMPLE)
        config.update(schemaVersion=3, challengeReviewers=[], implementationReviewers=[
            {"model": "reviewer", "reasoningEffort": "high"}])
        self.assertEqual(self.run_cli("save", json.dumps(config)).returncode, 0)
        result = self.run_cli("resolve-implementation-review")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [{"model": "reviewer", "reasoningEffort": None}])
        self.assertIn("remain stored but are inactive", result.stderr)
        config["implementationReviewers"][0]["reasoningEffort"] = None
        self.assertEqual(self.run_cli("save", json.dumps(config)).returncode, 0)
        result = self.run_cli("resolve-implementation-review")
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), [{"model": "reviewer", "reasoningEffort": None}])

    def test_invalid_inputs_preserve_existing_file(self):
        self.assertEqual(self.run_cli("save", json.dumps(EXAMPLE)).returncode, 0)
        original = self.path.read_bytes()
        invalid = ["{", "[]", '{"schemaVersion":1,"schemaVersion":1}']
        for version in (True, 2, "1", 1.0):
            config = copy.deepcopy(EXAMPLE)
            config["schemaVersion"] = version
            invalid.append(json.dumps(config))
        for location in ((), ("defaults",), ("roles",), ("roles", "review")):
            for mutation in ("extra", "missing"):
                config = copy.deepcopy(EXAMPLE)
                target = config
                for key in location:
                    target = target[key]
                if mutation == "extra":
                    target["extra"] = None
                else:
                    del target[next(iter(target))]
                invalid.append(json.dumps(config))
        for value in ("", " ", " model", "model ", False, 3, [], {}):
            config = copy.deepcopy(EXAMPLE)
            config["defaults"]["model"] = value
            invalid.append(json.dumps(config))
        for payload in invalid:
            with self.subTest(payload=payload):
                result = self.run_cli("save", payload)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(self.path.read_bytes(), original)

    def test_corrupt_or_future_existing_file_is_not_overwritten(self):
        self.path.parent.mkdir()
        future = copy.deepcopy(EXAMPLE)
        future["schemaVersion"] = 4
        for payload in ("{", json.dumps(future)):
            self.path.write_text(payload)
            for command in ("show", "save"):
                result = self.run_cli(command, json.dumps(EXAMPLE))
                self.assertEqual(result.returncode, 2)
                self.assertEqual(self.path.read_text(), payload)

    def test_challenge_missing_and_legacy_resolution_are_read_only(self):
        result = self.run_cli("resolve-challenge", None, "--host-model", "parent-model",
                              "--host-reasoning-effort", "low")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [{"model": "parent-model", "reasoningEffort": "low"}])
        self.assertFalse(self.path.parent.exists())
        self.assertEqual(self.run_cli("save", json.dumps(EXAMPLE)).returncode, 0)
        original = self.path.read_bytes()
        self.assertEqual(json.loads(self.run_cli("resolve-challenge").stdout),
                         [{"model": None, "reasoningEffort": None}])
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(json.loads(self.run_cli("show").stdout), EXAMPLE)

    def test_panel_round_trip_inheritance_and_empty_fallback(self):
        config = copy.deepcopy(EXAMPLE)
        config["schemaVersion"] = 2
        config["defaults"]["reasoningEffort"] = "high"
        config["roles"]["review"]["model"] = "review-model"
        config["challengeReviewers"] = [
            {"model": "first-model", "reasoningEffort": None},
            {"model": None, "reasoningEffort": "medium"},
        ]
        self.assertEqual(self.run_cli("save", json.dumps(config)).returncode, 0)
        self.assertEqual(json.loads(self.run_cli("show").stdout), config)
        original = self.path.read_bytes()
        result = self.run_cli("resolve-challenge", None, "--host-model", "parent-model",
                              "--host-reasoning-effort", "low")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [
            {"model": "first-model", "reasoningEffort": "low"},
            {"model": "review-model", "reasoningEffort": "low"},
        ])
        roles = json.loads(self.run_cli("resolve").stdout)
        self.assertEqual(set(roles), {"implementation", "review", "research"})
        self.assertEqual(roles["review"], {"model": "review-model", "reasoningEffort": None})
        self.assertEqual(self.path.read_bytes(), original)
        config["challengeReviewers"] = []
        self.assertEqual(self.run_cli("save", json.dumps(config)).returncode, 0)
        self.assertEqual(json.loads(self.run_cli("resolve-challenge").stdout),
                         [{"model": "review-model", "reasoningEffort": None}])
        config["defaults"] = {"model": None, "reasoningEffort": None}
        config["roles"]["review"]["model"] = None
        config["challengeReviewers"] = [{"model": None, "reasoningEffort": None}]
        self.assertEqual(self.run_cli("save", json.dumps(config)).returncode, 0)
        result = self.run_cli("resolve-challenge", None, "--host-model", "parent-model",
                              "--host-reasoning-effort", "low")
        self.assertEqual(json.loads(result.stdout), [{"model": "parent-model", "reasoningEffort": "low"}])

    def test_malformed_panels_preserve_saved_panel(self):
        config = copy.deepcopy(EXAMPLE)
        config.update(schemaVersion=2, challengeReviewers=[])
        self.assertEqual(self.run_cli("save", json.dumps(config)).returncode, 0)
        original = self.path.read_bytes()
        for panel in (None, {}, "model", [None], [{}], [{"model": "x"}],
                      [{"model": " x", "reasoningEffort": None}],
                      [{"model": None, "reasoningEffort": False}],
                      [{"model": None, "reasoningEffort": None, "extra": None}]):
            with self.subTest(panel=panel):
                invalid = copy.deepcopy(config)
                invalid["challengeReviewers"] = panel
                result = self.run_cli("save", json.dumps(invalid))
                self.assertEqual(result.returncode, 2)
                self.assertEqual(self.path.read_bytes(), original)
        for payload in ('{"schemaVersion":2,"defaults":{},"roles":{},"challengeReviewers":[],"challengeReviewers":[]}',):
            self.assertEqual(self.run_cli("save", payload).returncode, 2)
            self.assertEqual(self.path.read_bytes(), original)
        self.path.write_text(json.dumps(dict(config, challengeReviewers=[{}])))
        malformed = self.path.read_bytes()
        for command in ("show", "resolve-challenge", "save"):
            result = self.run_cli(command, json.dumps(EXAMPLE))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(self.path.read_bytes(), malformed)

    def test_implementation_review_legacy_and_missing_fallback_do_not_write(self):
        result = self.run_cli("resolve-implementation-review", None,
                              "--host-model", "parent-model", "--host-reasoning-effort", "low")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout),
                         [{"model": "parent-model", "reasoningEffort": "low"}])
        self.assertFalse(self.path.parent.exists())
        for version in (1, 2):
            config = copy.deepcopy(EXAMPLE)
            config["roles"]["review"] = {"model": "review-model", "reasoningEffort": "high"}
            if version == 2:
                config.update(schemaVersion=2, challengeReviewers=[
                    {"model": "challenge-model", "reasoningEffort": "medium"}])
            self.assertEqual(self.run_cli("save", json.dumps(config)).returncode, 0)
            original = self.path.read_bytes()
            result = self.run_cli("resolve-implementation-review")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout),
                             [{"model": "review-model", "reasoningEffort": None}])
            self.assertEqual(json.loads(self.run_cli("show").stdout), config)
            self.assertEqual(self.path.read_bytes(), original)

    def test_implementation_panel_resolution_preserves_challenge_and_roles(self):
        config = copy.deepcopy(EXAMPLE)
        config.update(schemaVersion=3,
                      challengeReviewers=[{"model": "challenge-model", "reasoningEffort": "low"}],
                      implementationReviewers=[
                          {"model": "first-model", "reasoningEffort": None},
                          {"model": None, "reasoningEffort": "medium"}])
        config["defaults"]["reasoningEffort"] = "high"
        config["roles"]["review"]["model"] = "review-model"
        result = self.run_cli("save", json.dumps(config))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.run_cli("show").stdout), config)
        original = self.path.read_bytes()
        result = self.run_cli("resolve-implementation-review", None,
                              "--host-model", "parent-model", "--host-reasoning-effort", "low")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [
            {"model": "first-model", "reasoningEffort": "low"},
            {"model": "review-model", "reasoningEffort": "low"}])
        self.assertEqual(json.loads(self.run_cli("resolve-challenge").stdout),
                         [{"model": "challenge-model", "reasoningEffort": None}])
        self.assertEqual(json.loads(self.run_cli("resolve").stdout), {
            "implementation": {"model": None, "reasoningEffort": None},
            "review": {"model": "review-model", "reasoningEffort": None},
            "research": {"model": None, "reasoningEffort": None}})
        self.assertEqual(self.path.read_bytes(), original)
        config["implementationReviewers"] = []
        self.assertEqual(self.run_cli("save", json.dumps(config)).returncode, 0)
        self.assertEqual(json.loads(self.run_cli("resolve-implementation-review").stdout),
                         [{"model": "review-model", "reasoningEffort": None}])
        self.assertEqual(json.loads(self.run_cli("show").stdout), config)
        config["roles"]["review"] = {"model": None, "reasoningEffort": None}
        config["defaults"] = {"model": None, "reasoningEffort": None}
        config["implementationReviewers"] = [{"model": None, "reasoningEffort": None}]
        self.assertEqual(self.run_cli("save", json.dumps(config)).returncode, 0)
        result = self.run_cli("resolve-implementation-review", None,
                              "--host-model", "parent-model", "--host-reasoning-effort", "low")
        self.assertEqual(json.loads(result.stdout),
                         [{"model": "parent-model", "reasoningEffort": "low"}])

    def test_schema_three_invalid_inputs_preserve_existing_preferences(self):
        config = copy.deepcopy(EXAMPLE)
        config.update(schemaVersion=3, challengeReviewers=[], implementationReviewers=[])
        self.assertEqual(self.run_cli("save", json.dumps(config)).returncode, 0)
        original = self.path.read_bytes()
        invalid = []
        for panel in (None, {}, "model", [None], [{}], [{"model": "x"}],
                      [{"model": " x", "reasoningEffort": None}],
                      [{"model": None, "reasoningEffort": False}],
                      [{"model": None, "reasoningEffort": None, "extra": None}]):
            choice = copy.deepcopy(config)
            choice["implementationReviewers"] = panel
            invalid.append(json.dumps(choice))
        for key in ("implementationReviewers", "challengeReviewers"):
            choice = copy.deepcopy(config)
            del choice[key]
            invalid.append(json.dumps(choice))
        for version in (1, 2):
            invalid.append(json.dumps(dict(config, schemaVersion=version)))
        invalid.append(json.dumps(config)[:-1] + ', "implementationReviewers": []}')
        for payload in invalid:
            with self.subTest(payload=payload):
                result = self.run_cli("save", payload)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertEqual(self.path.read_bytes(), original)
        self.path.write_text(json.dumps(dict(config, implementationReviewers=[{}])))
        malformed = self.path.read_bytes()
        for command in ("show", "resolve", "resolve-challenge", "resolve-implementation-review", "save"):
            result = self.run_cli(command, json.dumps(EXAMPLE))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(self.path.read_bytes(), malformed)

    def test_filesystem_error_has_no_traceback(self):
        self.path.parent.write_text("parent is a file")
        result = self.run_cli("save", json.dumps(EXAMPLE))
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(self.path.parent.read_text(), "parent is a file")


class HostPreferencesTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.env = dict(os.environ, HOME=str(self.root / "home"),
                        CODEX_HOME=str(self.root / "codex"),
                        CLAUDE_CONFIG_DIR=str(self.root / "claude"))

    def invoke(self, *args, payload=None):
        return subprocess.run([sys.executable, str(HELPER), *args],
                              input=payload, text=True, capture_output=True, env=self.env)

    def profile(self, host):
        return self.root / host / "pancake-stack/config.json"

    def test_profiles_coexist_without_cross_reads_or_writes(self):
        codex = copy.deepcopy(EXAMPLE)
        claude = copy.deepcopy(EXAMPLE)
        codex["defaults"]["model"] = "codex-choice"
        claude["defaults"]["model"] = "claude-choice"
        self.assertEqual(self.invoke("save", payload=json.dumps(codex)).returncode, 0)
        before = self.profile("codex").read_bytes()
        self.assertEqual(self.invoke("--host", "claude", "save", payload=json.dumps(claude)).returncode, 0)
        self.assertEqual(self.profile("codex").read_bytes(), before)
        self.assertEqual(json.loads(self.invoke("show").stdout), codex)
        self.assertEqual(json.loads(self.invoke("--host", "claude", "show").stdout), claude)
        self.profile("claude").unlink()
        self.assertEqual(json.loads(self.invoke("--host", "claude", "show").stdout), EXAMPLE)
        self.assertEqual(self.invoke("--host", "claude", "save", payload=json.dumps(claude)).returncode, 0)
        self.profile("codex").write_text("broken codex")
        self.assertEqual(json.loads(self.invoke("--host", "claude", "show").stdout), claude)
        self.assertEqual(self.invoke("--host", "claude", "save", payload=json.dumps(claude)).returncode, 0)
        self.assertEqual(self.profile("codex").read_text(), "broken codex")
        self.profile("claude").write_text("broken claude")
        self.profile("codex").write_text(json.dumps(codex))
        self.assertEqual(json.loads(self.invoke("show").stdout), codex)
        result = self.invoke("--host", "claude", "save", payload=json.dumps(claude))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.profile("claude").read_text(), "broken claude")

    def test_legacy_effort_resolution_is_isolated_on_both_hosts(self):
        for host in ("codex", "claude"):
            config = copy.deepcopy(EXAMPLE)
            config["defaults"] = {"model": host + "-model", "reasoningEffort": "high"}
            result = self.invoke("--host", host, "save", payload=json.dumps(config))
            self.assertEqual(result.returncode, 0, result.stderr)
        originals = {host: self.profile(host).read_bytes() for host in ("codex", "claude")}
        for host in ("codex", "claude"):
            for command in ("resolve", "resolve-challenge", "resolve-implementation-review"):
                result = self.invoke("--host", host, command, "--host-reasoning-effort", "low")
                self.assertEqual(result.returncode, 0, result.stderr)
                choice = {"model": host + "-model", "reasoningEffort": "low"}
                expected = ({role: choice for role in ("implementation", "review", "research")}
                            if command == "resolve" else [choice])
                self.assertEqual(json.loads(result.stdout), expected)
                self.assertIn("remain stored but are inactive", result.stderr)
                self.assertEqual({name: self.profile(name).read_bytes()
                                  for name in ("codex", "claude")}, originals)

    def test_config_override_precedes_both_host_paths(self):
        explicit = self.root / "explicit.json"
        for host in ("codex", "claude"):
            result = self.invoke("--host", host, "--config", str(explicit), "save", payload=json.dumps(EXAMPLE))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(explicit.read_text()), EXAMPLE)
            self.assertFalse(self.profile(host).exists())

    def test_missing_profiles_are_read_only_and_do_not_fall_back(self):
        for host in ("codex", "claude"):
            for command in ("show", "resolve", "resolve-challenge", "resolve-implementation-review"):
                result = self.invoke("--host", host, command)
                self.assertEqual(result.returncode, 0, result.stderr)
                if command == "show":
                    self.assertEqual(json.loads(result.stdout), EXAMPLE)
        self.assertFalse((self.root / "codex").exists())
        self.assertFalse((self.root / "claude").exists())
        self.assertFalse((self.root / "home/.codex").exists())
        self.assertFalse((self.root / "home/.claude").exists())

    def test_fallback_directories_and_invalid_host(self):
        self.env.pop("CODEX_HOME")
        self.env.pop("CLAUDE_CONFIG_DIR")
        for host, directory in (("codex", ".codex"), ("claude", ".claude")):
            result = self.invoke("--host", host, "save", payload=json.dumps(EXAMPLE))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((self.root / "home" / directory / "pancake-stack/config.json").read_text()), EXAMPLE)
        before = {str(path): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        result = self.invoke("--host", "unknown", "save", payload=json.dumps(EXAMPLE))
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice", result.stderr)
        self.assertEqual({str(path): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
