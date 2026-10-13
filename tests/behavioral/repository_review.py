"""Repository-derived review cases and private probes, never candidate context."""
import difflib
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile

from .support import snapshot

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures/repository-review"
REVISION = "d81ad93f3195d5164a305b79e504c44e16001b51"
ARCHIVE_SHA256 = "1e6d0ae6aa4380347e9c8e409c037a95dba355af9eac005a8bb9efb5444df075"
CASES = {
    "identity-clean": (),
    "identity-faulty": ("symlink-identity",),
    "traces-clean": (),
    "traces-faulty": ("prior-turn-evidence",),
}
REQUEST = "Review change.diff against the current repository for actionable regressions. Inspect relevant callers and tests where useful. Do not edit files."


def provenance():
    value = json.loads((FIXTURE / "provenance.json").read_text())
    archive = (FIXTURE / "source.tar.gz").read_bytes()
    if (value["revision"] != REVISION or value["archive_sha256"] != ARCHIVE_SHA256
            or hashlib.sha256(archive).hexdigest() != ARCHIVE_SHA256):
        raise ValueError("repository snapshot provenance mismatch")
    return value


def extract_snapshot(destination, archive, expected):
    """Validate all entries and hashes before writing only regular files."""
    files = {}
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as source:
        for member in source.getmembers():
            name = member.name
            path = PurePosixPath(name)
            if (path.is_absolute() or not path.parts or ".." in path.parts
                    or ".git" in path.parts or "\\" in name or str(path) != name.rstrip("/")
                    or name in seen or not (member.isdir() or member.isfile())):
                raise ValueError(f"unsafe snapshot entry: {name}")
            seen.add(name)
            if member.isfile():
                files[name] = (source.extractfile(member).read(), member.mode)
    actual = {name: hashlib.sha256(data).hexdigest() for name, (data, _) in files.items()}
    if actual != expected:
        raise ValueError("repository snapshot file hashes differ")
    destination = Path(destination)
    destination.mkdir()
    for name, (data, mode) in files.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o755 if mode & 0o111 else 0o644)


def prepare_snapshot(destination):
    record = provenance()
    extract_snapshot(destination, (FIXTURE / "source.tar.gz").read_bytes(), record["files"])
    return snapshot(destination)


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("repository mutation anchor changed")
    return text.replace(old, new, 1)


def prepare_review(case, destination):
    CASES[case]
    prepare_snapshot(destination)
    destination = Path(destination)
    family = case.split("-")[0]
    relative = "run_checks.py" if family == "identity" else "tests/behavioral/traces.py"
    path = destination / relative
    before = path.read_text()
    if family == "identity":
        helper = ('def file_content(path):\n'
                  '    if path.is_symlink():\n'
                  '        return os.fsencode(os.readlink(path))\n'
                  '    if path.is_file():\n'
                  '        return path.read_bytes()\n'
                  '    return None\n\n\n')
        if case == "identity-faulty":
            helper = ('def file_content(path):\n'
                      '    if path.is_file():\n'
                      '        return path.read_bytes()\n'
                      '    if path.is_symlink():\n'
                      '        return os.fsencode(os.readlink(path))\n'
                      '    return None\n\n\n')
        after = replace_once(before, "def identity(root):", helper + "def identity(root):")
        after = replace_once(after,
            "content = os.fsencode(os.readlink(path)) if path.is_symlink() else path.read_bytes() if path.is_file() else None",
            "content = file_content(path)")
    else:
        reset = ('            result["completed"] = False\n'
                 '            result["verdicts"] = []\n'
                 '            result["selections"] = []\n'
                 '            result["calls"] = []\n'
                 '            result["outputs"] = []\n')
        body = reset.replace("            ", "    ")
        if case == "traces-faulty":
            body = body.replace('    result["calls"] = []\n', '').replace('    result["outputs"] = []\n', '')
        after = replace_once(before, "def summarize_session(path):",
                             "def reset_turn(result):\n" + body + "\n\ndef summarize_session(path):")
        after = replace_once(after, reset, "            reset_turn(result)\n")
    path.write_text(after)
    diff = "".join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                       fromfile=f"a/{relative}", tofile=f"b/{relative}"))
    (destination / "change.diff").write_text(diff)
    return snapshot(destination)


PROBES = {
    "identity": r'''
import tempfile
import subprocess
from pathlib import Path
from run_checks import identity
with tempfile.TemporaryDirectory() as directory:
    storage = Path(directory)
    root = storage / 'checkout'
    root.mkdir()
    def git(*args):
        subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
    git('init')
    first, second = storage / 'first', storage / 'second'
    first.write_text('same bytes')
    second.write_text('same bytes')
    link = root / 'input'
    link.symlink_to(first)
    git('add', '.')
    git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'Fixture')
    before = identity(root)
    first.write_text('external edit')
    assert identity(root) == before, 'external referent contents changed checkout identity'
    first.write_text('same bytes')
    link.unlink()
    link.symlink_to(second)
    assert identity(root)['file_hashes']['input'] != before['file_hashes']['input'], 'retargeted symlink lost from identity'
''',
    "traces": r'''
import json
import tempfile
from pathlib import Path
from behavioral.traces import summarize_session
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / 'session.jsonl'
    events = [{'type': 'session_meta', 'payload': {'id': 'worker'}}]
    for name, output in [('old', 'failure'), ('new', 'success')]:
        events.extend([
            {'type': 'event_msg', 'payload': {'type': 'task_started'}},
            {'type': 'turn_context', 'payload': {'model': name, 'effort': 'medium'}},
            {'type': 'response_item', 'payload': {'type': 'function_call', 'call_id': name, 'name': 'exec_command', 'arguments': json.dumps({'command': name})}},
            {'type': 'response_item', 'payload': {'type': 'function_call_output', 'call_id': name, 'output': output}},
            {'type': 'response_item', 'payload': {'type': 'message', 'phase': 'final_answer', 'role': 'assistant', 'content': [{'text': name}]}},
            {'type': 'event_msg', 'payload': {'type': 'task_complete'}}])
    path.write_text('\n'.join(map(json.dumps, events)))
    result = summarize_session(path)
    assert result['completed'] and result['verdicts'] == ['new']
    assert result['selections'] == [{'model': 'new', 'effort': 'medium'}]
    assert result['calls'] == [{'id': 'new', 'name': 'exec_command', 'arguments': {'command': 'new'}}], 'prior-turn calls retained'
    assert result['outputs'] == [{'id': 'new', 'output': 'success'}], 'prior-turn outputs retained'
''',
}
