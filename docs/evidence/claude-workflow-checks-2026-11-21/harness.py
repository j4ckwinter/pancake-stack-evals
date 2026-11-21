import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

EVALS = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(EVALS))
from tests.behavioral import repository_review, review_comparison, support  # noqa: E402

RAW = Path(os.environ["PSTACK_RAW"])
BUNDLES = Path(os.environ["TMPDIR"]) / "pstack-bundles"
TRIALS = Path(os.environ["TMPDIR"]) / "pstack-trials"
PROJECTS = Path.home() / ".claude/projects"
SETTINGS = json.dumps({"sandbox": {"enabled": True, "autoAllowBashIfSandboxed": True, "allowUnsandboxedCommands": False}})


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def commit_all(cwd, message="Initial import"):
    git(cwd, "init", "-q")
    git(cwd, "add", "-A")
    git(cwd, "-c", "user.name=Dev", "-c", "user.email=dev@example.invalid", "commit", "-qm", message)


def prepare_repository(destination):
    repository_review.prepare_snapshot(destination)
    commit_all(destination)


def prepare_repository_case(case):
    def build(destination):
        repository_review.prepare_review(case, destination)
        commit_all(destination)
    return build


def prepare_config(case):
    def build(destination):
        review_comparison.prepare_review(case, destination)
        commit_all(destination)
    return build


def prepare_config_plain(destination):
    review_comparison.prepare_review("config-clean", destination)
    (Path(destination) / "change.diff").unlink()
    commit_all(destination)


def prepare_handoff(destination):
    prepare_config_plain(destination)
    d = Path(destination)
    (d / "jobs.py").write_text(
        "from settings import resolve_limit\n\n\n"
        "def select_jobs(jobs, options):\n"
        "    offset = options.get('offset', 0)\n"
        "    return jobs[offset:offset + resolve_limit(options)]\n")
    (d / "test_paging.py").write_text(
        "import unittest\nfrom jobs import select_jobs\n\n\n"
        "class PagingTests(unittest.TestCase):\n"
        "    def test_offset(self):\n"
        "        self.assertEqual(select_jobs(list(range(10)), {'limit': 2, 'offset': 4}), [4, 5])\n")


def prepare_summary(destination):
    support.prepare("summary", destination)
    commit_all(destination)


def state(workspace):
    w = Path(workspace)
    return {
        "files": support.snapshot(w) if w.exists() else {},
        "head": git(w, "rev-parse", "HEAD").strip(),
        "status": git(w, "status", "--porcelain", "--untracked-files=all"),
        "staged": git(w, "diff", "--cached", "--name-status"),
    }


def drop_git(files):
    return {k: v for k, v in files.items() if not k.startswith(".git/")}


def session_files(cwd, session_id):
    import re
    folder = PROJECTS / re.sub(r"[^A-Za-z0-9]", "-", str(Path(cwd).resolve()))
    main = folder / f"{session_id}.jsonl"
    return (main, folder / session_id) if main.exists() else (None, None)


def run(trial):
    run_id = trial["id"]
    out = RAW / run_id
    if (out / "result.json").exists():
        return json.loads((out / "summary.json").read_text())
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    root = Path(tempfile.mkdtemp(prefix="trial-", dir=TRIALS))
    workspace = root / "proj"
    trial["prepare"](workspace)
    before = state(workspace)
    command = ["claude", "-p", trial["prompt"], "--model", trial["model"],
               "--setting-sources", "project", "--strict-mcp-config",
               "--plugin-dir", str(BUNDLES / trial["bundle"]),
               "--settings", SETTINGS, "--permission-mode", "acceptEdits",
               "--disallowedTools", "WebFetch", "WebSearch",
               "--allowedTools", f"Read(/{BUNDLES}/**)", f"Read(//private{BUNDLES}/**)", "Bash",
               "--output-format", "json", "--max-budget-usd", "10"]
    started = time.time()
    try:
        completed = subprocess.run(command, cwd=workspace, capture_output=True, text=True, timeout=trial.get("timeout", 1200))
        stdout, stderr, code = completed.stdout, completed.stderr, completed.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code = (error.stdout or b"").decode() if isinstance(error.stdout, bytes) else (error.stdout or ""), "timeout", "timeout"
    elapsed = time.time() - started
    (out / "stdout.json").write_text(stdout)
    (out / "stderr.txt").write_text(stderr)
    after = state(workspace)
    try:
        result = json.loads(stdout)
    except json.JSONDecodeError:
        result = {"result": None, "session_id": None}
    main, sub = session_files(workspace, result.get("session_id")) if result.get("session_id") else (None, None)
    if main:
        shutil.copy(main, out / "session.jsonl")
        if sub and sub.exists():
            shutil.copytree(sub, out / "session", dirs_exist_ok=True)
    shutil.copytree(workspace, out / "workspace", ignore=shutil.ignore_patterns(".git"), dirs_exist_ok=True)
    changed = sorted(k for k in set(drop_git(before["files"])) | set(drop_git(after["files"]))
                     if before["files"].get(k) != after["files"].get(k))
    summary = {
        "id": run_id, "family": trial["family"], "arm": trial["arm"], "case": trial.get("case"),
        "model": trial["model"], "bundle": trial["bundle"], "exit": code, "elapsed_s": round(elapsed, 1),
        "cost_usd": result.get("total_cost_usd"), "turns": result.get("num_turns"),
        "is_error": result.get("is_error"), "session_id": result.get("session_id"),
        "changed_files": changed, "head_changed": before["head"] != after["head"],
        "status_before": before["status"], "status_after": after["status"],
        "staged_after": after["staged"], "workspace": str(workspace),
        "final": result.get("result"),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    (out / "result.json").write_text(json.dumps(result, indent=1))
    return summary


def run_all(trials, workers=4):
    TRIALS.mkdir(exist_ok=True)
    RAW.mkdir(exist_ok=True)
    with ThreadPoolExecutor(workers) as pool:
        for s in pool.map(run, trials):
            print(json.dumps({k: s[k] for k in ("id", "exit", "elapsed_s", "cost_usd", "changed_files", "head_changed")}), flush=True)
