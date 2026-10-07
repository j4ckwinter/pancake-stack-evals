import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("run_checks", Path(__file__).resolve().parents[1] / "run_checks.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class IdentityTests(unittest.TestCase):
    def test_untracked_inputs_change_identity_and_deletions_remain_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
            git("init")
            (root / "tracked.md").write_text("original")
            git("add", ".")
            git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "Fixture")
            clean = runner.identity(root)
            self.assertFalse(clean["dirty"])
            (root / "request.txt").write_text("first request")
            first = runner.identity(root)
            self.assertTrue(first["dirty"])
            self.assertIn("request.txt", first["file_hashes"])
            (root / "request.txt").write_text("second request")
            second = runner.identity(root)
            self.assertEqual(first["revision"], second["revision"])
            self.assertNotEqual(first["file_hashes"]["request.txt"], second["file_hashes"]["request.txt"])
            (root / "tracked.md").unlink()
            self.assertIsNone(runner.identity(root)["file_hashes"]["tracked.md"])
