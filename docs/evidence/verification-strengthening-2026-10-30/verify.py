"""Check exact persistence through both supported writers and a fresh reader."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from store import save

ROOT = Path(__file__).resolve().parent
VALUES = ("receipt", "replacement", "", "  padded\t ", "line one\nline two", 'café 雪 "quoted" \\')


def run_python(*args):
    return subprocess.run(
        [sys.executable, "-B", *map(str, args)],
        cwd=ROOT, capture_output=True, text=True, timeout=5, check=True,
    )


def read_fresh(path):
    result = run_python(
        "-c",
        "import json, sys; from store import load; print(json.dumps(load(sys.argv[1])))",
        path,
    )
    return json.loads(result.stdout)


class PersistenceChecks(unittest.TestCase):
    def check_writer(self, writer):
        with tempfile.TemporaryDirectory(prefix="store-verify-") as temp:
            path = Path(temp) / "record with spaces.json"
            for value in VALUES:
                with self.subTest(value=value):
                    writer(path, value)
                    self.assertEqual(read_fresh(path), value)

    def test_save_api(self):
        self.check_writer(save)

    def test_save_cli(self):
        self.check_writer(lambda path, value: run_python(ROOT / "store.py", path, value))


if __name__ == "__main__":
    unittest.main(verbosity=2)
