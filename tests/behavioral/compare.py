"""Explicit live comparison runner; never called by unittest discovery.

Uses the existing Codex file authentication cache in temporary private profiles.
Raw records may contain account metadata; keep output private, not in Git.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

if __package__:
    from .support import CASES, prepare, snapshot
    from .traces import completed_workers, summarize_session
else:
    from support import CASES, prepare, snapshot
    from traces import completed_workers, summarize_session

EVALUATOR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(EVALUATOR / "tests"))
from target import source_root
sys.path.insert(0, str(EVALUATOR))
from run_checks import identity
ROOT = source_root()
CASES_TO_RUN = ("summary", "records", "exporter")


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def collect_sessions(profile):
    sessions = []
    for path in sorted((profile / "sessions").rglob("*.jsonl")):
        session = summarize_session(path)
        usage = None
        created_at = None
        tool_calls = 0
        command_actions = 0
        for line in path.read_text().splitlines():
            event = json.loads(line)
            payload = event.get("payload", {})
            if event.get("type") == "session_meta" and created_at is None:
                if payload.get("timestamp"):
                    created_at = datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
            timestamp = event.get("timestamp")
            if created_at and timestamp and datetime.fromisoformat(timestamp.replace("Z", "+00:00")) < created_at:
                continue
            if event.get("type") == "response_item" and payload.get("type") in ("function_call", "custom_tool_call"):
                tool_calls += 1
            if (event.get("type") == "event_msg" and payload.get("type") == "item_completed"
                    and payload.get("item", {}).get("type") == "CommandExecution"):
                command_actions += 1
            if event.get("type") == "event_msg" and payload.get("type") == "token_count":
                info = payload.get("info")
                if info:
                    usage = info.get("total_token_usage")
        session["usage"] = usage
        session["tool_calls"] = tool_calls
        session["command_actions"] = command_actions
        sessions.append(session)
    return sessions


def assess_candidate(case, workspace, before, profile):
    """Run generated application/tests in the CLI's read-only sandbox."""
    script = (
        f"import sys, json; sys.path.insert(0, {str(EVALUATOR / 'tests')!r}); "
        "from behavioral.support import assess; "
        "case, workspace, before = json.load(sys.stdin); "
        "print(assess(case, workspace, before))"
    )
    result = subprocess.run(
        ["codex", "sandbox", "--permission-profile", ":read-only", "--cd", str(workspace),
         "--", sys.executable, "-I", "-B", "-c", script],
        input=json.dumps([case, str(workspace), before]), text=True, capture_output=True,
        timeout=45, env=dict(os.environ, CODEX_HOME=str(profile),
                             CLAUDE_CONFIG_DIR=str(profile / "claude")),
    )
    return {"passed": result.returncode == 0 and result.stdout == "artifact checks passed\n",
            "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def run_trial(case, variant, destination, auth, model, effort, timeout, suite="workflow"):
    if suite == "review":
        if __package__:
            from .review import REQUEST, consolidate, prepare_review
        else:
            sys.path.insert(0, str(EVALUATOR / "tests"))
            from behavioral.review import REQUEST, consolidate, prepare_review
    destination.mkdir(mode=0o700)
    # Candidate paths carry neither the scenario nor its treatment label.
    run = Path(tempfile.mkdtemp(prefix="project-"))
    profile = run / "profile"
    profile.mkdir(mode=0o700)
    workspace = run / "workspace"
    before = prepare_review(case, workspace) if suite == "review" else prepare(case, workspace)
    bundle = run / "bundle"
    if variant == "pancake" or suite == "review":
        shutil.copytree(ROOT / "skills", bundle / "skills")
        shutil.copytree(ROOT / "docs", bundle / "docs")
    if suite == "review" and variant == "consolidated":
        check = bundle / "skills/check/SKILL.md"
        check.write_text(consolidate(check.read_text()))
    request = REQUEST if suite == "review" else (CASES / case / "request.txt").read_text().strip()
    prompt = request + (
        "\n\nWork only in the current project. Preserve unrelated files. "
        "Independent read-only review is permitted when useful; reviewers must inherit "
        "this conversation's model and effort and must not delegate further. "
        "Do not commit, install dependencies, use external services, or inspect unrelated "
        "projects or user history. Keep any preference reads within the isolated "
        "CODEX_HOME profile."
    )
    if variant == "pancake":
        prompt += f"\nUse the Pancake skill at {bundle / 'skills/pancake/SKILL.md'} and its applicable references."
    if suite == "review":
        prompt = request + (
            f"\nUse the Check skill at {bundle / 'skills/check/SKILL.md'}. "
            "Work only in this project and the supplied skill bundle. Do not delegate, "
            "commit, install dependencies, use external services, change preferences, "
            "or inspect unrelated projects or user history."
        )
    command = [
        "codex", "exec", "--ignore-user-config", "--ignore-rules", "--json",
        "--enable", "multi_agent", "-c", "agents.max_threads=2",
        "-c", 'cli_auth_credentials_store="file"', "-m", model,
        *(["-c", f"model_reasoning_effort={json.dumps(effort)}"] if effort else []),
        "--sandbox", "read-only" if suite == "review" else "workspace-write", "--skip-git-repo-check",
        "--cd", str(workspace), "--output-last-message", str(destination / "final.txt"), "-",
    ]
    write_json(destination / "invocation.json", command)
    write_json(destination / "before.json", before)
    (destination / "prompt.txt").write_text(prompt)
    result = {"run_id": destination.name, "suite": suite, "case": case, "variant": variant, "candidate_root": str(run),
              "requested_model": model, "requested_effort": effort}
    process = None
    try:
        shutil.copy2(auth, profile / "auth.json")
        (profile / "auth.json").chmod(0o600)
        started = time.monotonic()
        with (destination / "events.jsonl").open("w") as out, (destination / "stderr.txt").open("w") as err:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                       text=True, start_new_session=True,
                                       env=dict(os.environ, CODEX_HOME=str(profile), PYTHONDONTWRITEBYTECODE="1"))
            try:
                process.communicate(prompt, timeout=timeout)
                result["timed_out"] = False
            except subprocess.TimeoutExpired:
                result["timed_out"] = True
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate()
        result["elapsed_seconds"] = round(time.monotonic() - started, 3)
        result["exit_code"] = process.returncode
        (profile / "auth.json").unlink(missing_ok=True)
        try:
            result["artifact"] = ({"passed": snapshot(workspace) == before} if suite == "review"
                                  else assess_candidate(case, workspace, before, profile))
        except (AssertionError, ValueError, OSError, subprocess.SubprocessError) as error:
            result["artifact"] = {"passed": False, "detail": str(error)}
        result["preferences_unchanged"] = not (profile / "pancake-stack").exists()
        try:
            result["after"] = snapshot(workspace)
        except (ValueError, OSError) as error:
            result["after"] = {"snapshot_error": str(error)}
        sessions = collect_sessions(profile)
        write_json(destination / "sessions.json", sessions)
        parents = [s for s in sessions if s["parent_id"] is None]
        result["sessions"] = [{k: s[k] for k in ("id", "parent_id", "agent_path", "selections", "completed", "usage")}
                              for s in sessions]
        result["completed_reviewers"] = [s["id"] for p in parents for s in completed_workers(sessions, p["id"])]
        result["usage_all_sessions"] = {
            field: sum(s["usage"].get(field, 0) for s in sessions if s["usage"])
            for field in ("input_tokens", "cached_input_tokens", "output_tokens", "total_tokens")
        }
        result["usage_complete"] = bool(sessions) and all(s["usage"] for s in sessions)
        result["tool_calls_all_sessions"] = sum(s["tool_calls"] for s in sessions)
        result["command_actions_all_sessions"] = sum(s["command_actions"] for s in sessions)
        shutil.copytree(workspace, destination / "workspace", symlinks=True)
        write_json(destination / "result.json", result)
        return result
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        (profile / "auth.json").unlink(missing_ok=True)
        # Retain trial-owned session records for auditing, excluding credentials.
        if (profile / "sessions").exists():
            shutil.copytree(profile / "sessions", destination / "raw-sessions")
        shutil.rmtree(run)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new private directory outside the repository")
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", help="omit to inherit CLI default")
    parser.add_argument("--suite", choices=("workflow", "review"), default="workflow")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=300, help="seconds per candidate")
    args = parser.parse_args()
    if args.repetitions < 1 or args.timeout < 1:
        parser.error("repetitions and timeout must be positive")
    output = args.output.resolve()
    if output.is_relative_to(ROOT) or output.is_relative_to(EVALUATOR):
        parser.error("raw trial output must be outside the repository")
    auth = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "auth.json"
    if not auth.is_file():
        parser.error("a Codex file authentication cache is required")
    output.mkdir(mode=0o700)
    if args.suite == "review":
        if __package__:
            from .review import CASES as review_cases
        else:
            sys.path.insert(0, str(EVALUATOR / "tests"))
            from behavioral.review import CASES as review_cases
    cases = tuple(review_cases) if args.suite == "review" else CASES_TO_RUN
    variants = ("baseline", "consolidated") if args.suite == "review" else ("baseline", "pancake")
    plan = [(case, repeat + 1, variant) for repeat in range(args.repetitions)
            for index, case in enumerate(cases)
            for variant in (variants if (repeat + index) % 2 == 0 else variants[::-1])]
    write_json(output / "manifest.json", {
        "source": identity(ROOT),
        "evaluator": identity(EVALUATOR),
        "cli_version": subprocess.check_output(["codex", "--version"], text=True).strip(),
        "model": args.model, "effort": args.effort, "timeout_seconds": args.timeout,
        "suite": args.suite,
        "plan": plan,
    })
    results = []
    for index, (case, repeat, variant) in enumerate(plan, 1):
        print(f"Starting {index}/{len(plan)}: {case} {variant} repetition {repeat}", flush=True)
        result = run_trial(case, variant, output / f"run-{index:02d}", auth,
                           args.model, args.effort, args.timeout, args.suite)
        result["repetition"] = repeat
        results.append(result)
        write_json(output / "results.json", results)
        print(f"Finished {index}: artifact={result['artifact']['passed']} elapsed={result['elapsed_seconds']}s", flush=True)
        if result["exit_code"] != 0 or not result["sessions"]:
            raise SystemExit("Candidate execution failed; inspect retained records before continuing.")


if __name__ == "__main__":
    main()
