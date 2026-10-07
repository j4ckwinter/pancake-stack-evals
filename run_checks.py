"""Validate an explicit Pancake Stack checkout without installing it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def identity(root):
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    paths = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root).split(b"\0")
    hashes = {}
    for value in paths:
        if not value:
            continue
        name = os.fsdecode(value)
        path = root / name
        content = os.fsencode(os.readlink(path)) if path.is_symlink() else path.read_bytes() if path.is_file() else None
        hashes[name] = hashlib.sha256(content).hexdigest() if content is not None else None
    return {"revision": revision, "dirty": bool(subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, text=True)),
        "file_hashes": hashes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="optional JSON record outside the source checkout")
    args = parser.parse_args()
    source = args.source.resolve()
    evaluator = Path(__file__).resolve().parent
    if not (source / "plugin.json").is_file():
        parser.error("--source must contain plugin.json")
    if args.output and any(args.output.resolve().is_relative_to(root) for root in (source, evaluator)):
        parser.error("--output must be outside both checkouts")
    before = identity(source)
    evaluator_before = identity(evaluator)
    result = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=evaluator, env=dict(os.environ, PANCAKE_STACK_SOURCE=str(source),
                               PYTHONDONTWRITEBYTECODE="1"),
    )
    unchanged = before == identity(source)
    evaluator_unchanged = evaluator_before == identity(evaluator)
    record = {"source": before, "evaluator": evaluator_before,
              "source_unchanged": unchanged, "evaluator_unchanged": evaluator_unchanged,
              "exit_code": result.returncode,
              "passed": result.returncode == 0 and unchanged and evaluator_unchanged}
    serialized = json.dumps(record, indent=2) + "\n"
    if args.output:
        args.output.write_text(serialized)
    print(json.dumps({key: value for key, value in record.items()
                      if key not in ("source", "evaluator")}, indent=2))
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
