"""Explicit live comparison runner; never called by unittest discovery.

Uses the existing Codex file authentication cache in temporary private profiles.
Raw records may contain account metadata; keep output private, not in Git.
"""
import argparse
import hashlib
from datetime import datetime
import json
import os
import re
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


COMPARISON_CASES = ("label", "contract")


def skill_catalog(bundle):
    catalog = []
    for path in sorted((Path(bundle) / 'skills').glob('*/SKILL.md')):
        lines = path.read_text().splitlines()
        if not lines or lines[0] != '---' or '---' not in lines[1:]:
            raise ValueError(f'missing frontmatter: {path}')
        fields = dict(line.split(': ', 1) for line in lines[1:lines.index('---', 1)])
        if set(fields) != {'name', 'description'} or fields['name'] != path.parent.name:
            raise ValueError(f'invalid catalog metadata: {path}')
        catalog.append(dict(fields, path=str(path)))
    if len(catalog) != 19:
        raise ValueError('routing suite requires the complete 19-skill catalog')
    return catalog



def poteto_inventory(source):
    """Select the installed Codex adaptation without copying user configuration."""
    source = Path(source).resolve()
    entrypoint = source / "poteto-mode/SKILL.md"
    if not entrypoint.is_file():
        raise ValueError("poteto source must contain poteto-mode/SKILL.md")
    selected = []
    hashes = {}
    for directory in sorted(source.iterdir()):
        skill = directory / "SKILL.md"
        if not skill.is_file():
            continue
        if directory.is_symlink() or skill.is_symlink():
            raise ValueError(f"skill symlink is unsupported: {directory}")
        if "poteto-mode/references/codex-port.md" not in skill.read_text():
            continue
        selected.append(directory.name)
        for path in sorted(directory.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"skill symlink is unsupported: {path}")
            if path.is_file():
                hashes[str(path.relative_to(source))] = hashlib.sha256(path.read_bytes()).hexdigest()
    if "poteto-mode" not in selected:
        raise ValueError("poteto entrypoint lacks the Codex compatibility marker")
    if not (source / "poteto-mode/references/codex-port.md").is_file():
        raise ValueError("poteto Codex compatibility guidance is missing")
    missing = []
    for name in hashes:
        if not name.endswith(".md"):
            continue
        path = source / name
        for reference in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            reference = reference.split("#", 1)[0]
            if not reference or "://" in reference or reference.startswith(("/", "#")):
                continue
            target = (path.parent / reference).resolve()
            if (not target.is_relative_to(source) or
                    (str(target.relative_to(source)) not in hashes and not any(
                        item.startswith(str(target.relative_to(source)) + "/") for item in hashes))):
                missing.append({"file": name, "reference": reference})
    origin = source / "poteto-mode/references/origin.json"
    return {"skills": selected, "files": hashes, "unresolved_relative_links": missing,
            "origin": json.loads(origin.read_text()) if origin.is_file() else None}


def trial_plan(cases, variants, repetitions, rotate=False):
    plan = []
    for repeat in range(repetitions):
        for index, case in enumerate(cases):
            offset = (repeat + index) % len(variants)
            ordered = (variants[offset:] + variants[:offset] if rotate else
                       variants if (repeat + index) % 2 == 0 else variants[::-1])
            plan.extend((case, repeat + 1, variant) for variant in ordered)
    return plan


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
    if case == "validation":
        script = (
            f"import sys, json; sys.path.insert(0, {str(EVALUATOR / 'tests')!r}); "
            "from behavioral.validation import assess_validation; "
            "case, workspace, before = json.load(sys.stdin); "
            "print(json.dumps(assess_validation(workspace, before)))"
        )
    result = subprocess.run(
        ["codex", "sandbox", "--permission-profile", ":read-only", "--cd", str(workspace),
         "--", sys.executable, "-I", "-B", "-c", script],
        input=json.dumps([case, str(workspace), before]), text=True, capture_output=True,
        timeout=45, env=dict(os.environ, CODEX_HOME=str(profile),
                             CLAUDE_CONFIG_DIR=str(profile / "claude")),
    )
    if case == "validation" and result.returncode == 0:
        assessment = json.loads(result.stdout)
        return dict(assessment, exit_code=result.returncode, stderr=result.stderr)
    return {"passed": result.returncode == 0 and result.stdout == "artifact checks passed\n",
            "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def run_trial(case, variant, destination, auth, model, effort, timeout, suite="workflow", poteto_source=None, expected_poteto=None, source=None, design_entrypoint="design", case_adapter=None):
    if case_adapter is not None and (suite != "workflow" or design_entrypoint != "design"
                                     or poteto_source is not None or expected_poteto is not None):
        raise ValueError("case adapter requires workflow suite")
    if design_entrypoint not in ("design", "parallel-work"):
        raise ValueError("invalid Design entrypoint")
    source = Path(source) if source is not None else ROOT
    read_only_review = suite in ("design", "review", "review-comparison", "repository-review", "historical-review", "context-recovery")
    if case_adapter is not None:
        read_only_review = case_adapter.read_only
    three_arm = suite in ("comparison", "review-comparison")
    if suite == "design":
        from behavioral.design import REQUESTS, prepare_case
        REQUEST, prepare_review = REQUESTS[case], prepare_case
    if suite == "review-comparison":
        if __package__:
            from .review_comparison import CASES as review_cases, REQUEST, prepare_review
        else:
            from behavioral.review_comparison import CASES as review_cases, REQUEST, prepare_review
        if variant not in ("baseline", "pancake", "poteto") or case not in review_cases:
            raise ValueError("invalid review-comparison case or variant")
    if suite == "review":
        if __package__:
            from .review import REQUEST, consolidate, prepare_review
        else:
            sys.path.insert(0, str(EVALUATOR / "tests"))
            from behavioral.review import REQUEST, consolidate, prepare_review
    if suite == "repository-review":
        from behavioral.repository_review import CASES as review_cases, REQUEST, prepare_review, provenance
        if variant not in ("baseline", "pancake") or case not in review_cases:
            raise ValueError("invalid repository-review case or variant")
    if suite in ("historical-review", "context-recovery"):
        from behavioral import historical_review, context_recovery
        scenario = historical_review if suite == "historical-review" else context_recovery
        REQUEST, prepare_review, provenance = scenario.REQUEST, scenario.prepare_case, scenario.provenance
        if variant not in ("baseline", "pancake") or case not in scenario.CASES:
            raise ValueError("invalid case or variant")
    inventory = poteto_inventory(poteto_source) if variant == "poteto" else None
    if expected_poteto is not None and inventory != expected_poteto:
        raise ValueError("poteto input changed since manifest capture")
    destination.mkdir(mode=0o700)
    # Candidate paths carry neither the scenario nor its treatment label.
    run = Path(tempfile.mkdtemp(prefix="project-"))
    try:
        profile = run / "profile"
        profile.mkdir(mode=0o700)
        workspace = run / "workspace"
        if case_adapter is not None:
            before = case_adapter.preparation(case, workspace)
        elif suite == "validation":
            from behavioral.validation import prepare_validation, revise_verify, treatment_hashes
            before = prepare_validation(workspace)
        else:
            before = prepare_review(case, workspace) if read_only_review else prepare(case, workspace)
        bundle = run / "bundle"
        if (case_adapter.discovery != "none" if case_adapter is not None else
                variant == "pancake" or suite in ("review", "validation")):
            shutil.copytree(source / "skills", bundle / "skills")
            (bundle / "docs").mkdir()
            shutil.copy2(source / "docs/configuration.md", bundle / "docs/configuration.md")
        if suite == "validation":
            if variant == "revised":
                verify = bundle / "skills/verify/SKILL.md"
                verify.write_text(revise_verify(verify.read_text()))
            if snapshot(bundle) != treatment_hashes(ROOT)[variant]:
                raise ValueError("validation bundle differs from source treatment")
        if variant == "poteto":
            for name in inventory["skills"]:
                shutil.copytree(Path(poteto_source) / name, bundle / "skills" / name)
            if poteto_inventory(bundle / "skills") != inventory:
                raise ValueError("poteto copied bundle differs from captured input")
        if suite == "review" and variant == "consolidated":
            check = bundle / "skills/check/SKILL.md"
            check.write_text(consolidate(check.read_text()))
        if case_adapter is not None and case_adapter.discovery != "none":
            copied = snapshot(bundle)
            expected = {f"skills/{k}": v for k, v in snapshot(source / "skills").items()}
            expected["docs/configuration.md"] = hashlib.sha256((source / "docs/configuration.md").read_bytes()).hexdigest()
            if copied != expected:
                raise ValueError("copied bundle differs from source")
        request = (case_adapter.request if case_adapter is not None else
                   REQUEST if read_only_review else (CASES / case / "request.txt").read_text().strip())
        prompt = request + (
            "\n\nWork only in the current project. Preserve unrelated files. "
            "Independent read-only review is permitted when useful; reviewers must inherit "
            "this conversation's model and effort and must not delegate further. "
            "Do not commit, install dependencies, use external services, or inspect unrelated "
            "projects or user history. Keep any preference reads within the isolated "
            "CODEX_HOME profile."
        )
        if three_arm:
            prompt = request + (
                "\n\nWork only in the current project and supplied skill bundle. Preserve unrelated files. " +
                ("Independent read-only review is permitted when useful. " if read_only_review else
                 "Scoped implementation delegates and independent read-only reviewers are permitted when useful. ") +
                "All workers must inherit this conversation's model and effort and must not delegate further. "
                "Do not commit, install dependencies, use external services, read saved preferences, change "
                "preferences, or inspect unrelated projects or user history. Resolve sibling skill references "
                "inside the supplied bundle, never from global skill directories."
            )
        if variant == "poteto":
            prompt += f"\nUse the Poteto skill at {bundle / 'skills/poteto-mode/SKILL.md'} and its applicable references."
        if variant == "pancake":
            prompt += f"\nUse the Pancake skill at {bundle / 'skills/pancake/SKILL.md'} and its applicable references."
        if suite == "review":
            prompt = request + (
                f"\nUse the Check skill at {bundle / 'skills/check/SKILL.md'}. "
                "Work only in this project and the supplied skill bundle. Do not delegate, "
                "commit, install dependencies, use external services, change preferences, "
                "or inspect unrelated projects or user history."
            )
        if suite in ("repository-review", "historical-review", "context-recovery"):
            prompt = request + (
                "\nWork only in this project and the supplied skill bundle. Do not delegate, "
                "commit, install dependencies, use external services, read or change preferences, "
                "or inspect unrelated projects or user history. Resolve sibling skills within the bundle."
            )
            if variant == "pancake":
                skill = "recap" if suite == "context-recovery" else "pancake"
                prompt += f"\nUse the {skill.title()} skill at {bundle / 'skills' / skill / 'SKILL.md'} and its applicable references."
        if suite == "validation":
            prompt = request + (
                f"\nUse the TDD skill at {bundle / 'skills/tdd/SKILL.md'} and its applicable references. "
                "Work only in this project and the supplied skill bundle. Do not delegate, "
                "commit, install dependencies, use external services, read or change preferences, "
                "or inspect unrelated projects or user history. Resolve sibling skills within the bundle."
            )
        if suite == "design":
            entrypoint = bundle / ("skills/design/SKILL.md" if design_entrypoint == "design" else "skills/pancake/references/parallel-work.md")
            prompt = REQUEST + (
                f"\nUse the workflow at {entrypoint} and applicable references. "
                "Work only in this project and supplied bundle. Do not edit files, install anything, "
                "use external services, read or change saved preferences, or inspect unrelated projects "
                "or user history. Independent read-only delegates are permitted when useful; they "
                "must inherit the current model and effort and cannot delegate further. "
                "Resolve sibling skills within the supplied bundle."
            )
        if case_adapter is not None:
            discovery = case_adapter.discovery
            prompt = request
            if discovery == "explicit":
                prompt += f"\nUse the workflow at {bundle / case_adapter.entrypoint} and applicable references. "
            elif discovery == "catalog":
                prompt += "\nAvailable skills may be used when applicable to the task.\n"
                prompt += "\n".join(f"- {item['name']}: {item['description']} (file: {item['path']})"
                                    for item in skill_catalog(bundle))
            prompt += (
                ("\nWork only in this project. " if discovery == "none" else
                 ("\n" if discovery == "catalog" else "") + "Work only in this project and supplied bundle. ") +
                ("Independent read-only reviewers are permitted when useful; they must inherit "
                 "the current model and effort and must not delegate further. Do not commit, install "
                 if case_adapter.allow_reviewers else "Do not delegate, commit, install ") +
                "dependencies, use external services, read or change preferences, or inspect unrelated "
                "projects or user history."
            )
            if discovery != "explicit":
                prompt += " Do not read global skill directories."
            if discovery != "none":
                prompt += " Resolve sibling skills within the supplied bundle."
        command = [
            "codex", "exec", "--ignore-user-config", "--ignore-rules", "--json",
            "--enable", "multi_agent", "-c", "agents.max_threads=2",
            "-c", 'cli_auth_credentials_store="file"',
            *(["-m", model] if model else []),
            *(["-c", f"model_reasoning_effort={json.dumps(effort)}"] if effort else []),
            "--sandbox", "read-only" if read_only_review else "workspace-write", "--skip-git-repo-check",
            "--cd", str(workspace), "--output-last-message", str(destination / "final.txt"), "-",
        ]
        if suite == "design":
            command[command.index("agents.max_threads=2")] = "agents.max_threads=4"
        if (case_adapter is not None and not case_adapter.allow_reviewers) or suite in ("repository-review", "historical-review", "context-recovery"):
            index = command.index("--enable")
            command[index:index + 4] = ["--disable", "multi_agent"]
        write_json(destination / "invocation.json", command)
        write_json(destination / "before.json", before)
        (destination / "prompt.txt").write_text(prompt)
        result = {"run_id": destination.name, "suite": suite, "case": case, "variant": variant, "candidate_root": str(run),
                  "requested_model": model, "requested_effort": effort}
        if suite in ("repository-review", "historical-review", "context-recovery"):
            result["snapshot"] = provenance()
        process = None
        try:
            shutil.copy2(auth, profile / "auth.json")
            (profile / "auth.json").chmod(0o600)
            started = time.monotonic()
            environment = dict(os.environ, CODEX_HOME=str(profile), PYTHONDONTWRITEBYTECODE="1")
            if suite == "context-recovery" or (case_adapter is not None and case_adapter.discovery != "explicit"):
                from behavioral.context_recovery import git_environment
                environment = git_environment(environment)
            with (destination / "events.jsonl").open("w") as out, (destination / "stderr.txt").open("w") as err:
                process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                           text=True, start_new_session=True,
                                           env=environment)
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
                result["artifact"] = (case_adapter.assessment(case, workspace, before, profile) if case_adapter is not None else
                                      {"passed": snapshot(workspace) == before} if read_only_review
                                      else assess_candidate(case, workspace, before, profile))
            except (AssertionError, ValueError, OSError, subprocess.SubprocessError) as error:
                result["artifact"] = {"passed": False, "detail": str(error)}
            if case_adapter is not None:
                try:
                    result["bundle_unchanged"] = (not bundle.exists() if case_adapter.discovery == "none"
                                                  else snapshot(bundle) == copied)
                except (ValueError, OSError):
                    result["bundle_unchanged"] = False
                result["artifact"]["scope_preserved"] = (
                    result["artifact"].get("scope_preserved", False) and result["bundle_unchanged"])
            result["preferences_unchanged"] = not (profile / "pancake-stack").exists() and not (profile / "pstack-models.json").exists() and not (profile / "config.toml").exists()
            try:
                result["after"] = snapshot(workspace)
            except (ValueError, OSError) as error:
                result["after"] = {"snapshot_error": str(error)}
            if three_arm and "snapshot_error" not in result["after"]:
                result["changed_files"] = sorted(name for name in before
                                                 if result["after"].get(name) != before[name])
                result["added_files"] = sorted(result["after"].keys() - before.keys())
                final = destination / "final.txt"
                result["final_response_chars"] = len(final.read_text()) if final.exists() else None
            sessions = collect_sessions(profile)
            write_json(destination / "sessions.json", sessions)
            parents = [s for s in sessions if s["parent_id"] is None]
            result["sessions"] = [{k: s[k] for k in ("id", "parent_id", "agent_path", "selections", "completed", "usage")}
                                  for s in sessions]
            result["completed_workers" if three_arm else "completed_reviewers"] = [s["id"] for p in parents for s in completed_workers(sessions, p["id"])]
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
    finally:
        shutil.rmtree(run)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new private directory outside the repository")
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", help="omit to inherit CLI default")
    parser.add_argument("--suite", choices=("workflow", "review", "comparison", "review-comparison", "validation", "repository-review", "historical-review", "context-recovery"), default="workflow")
    parser.add_argument("--poteto-source", type=Path, help="installed Codex-adapted sibling skill root")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=300, help="seconds per candidate")
    args = parser.parse_args()
    if args.repetitions < 1 or args.timeout < 1:
        parser.error("repetitions and timeout must be positive")
    poteto = None
    three_arm = args.suite in ("comparison", "review-comparison")
    if three_arm:
        if args.poteto_source is None:
            parser.error(f"{args.suite} requires --poteto-source")
        try:
            poteto = poteto_inventory(args.poteto_source)
        except (OSError, ValueError) as error:
            parser.error(str(error))
    elif args.poteto_source is not None:
        parser.error("--poteto-source is only valid for comparison or review-comparison")
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
    if args.suite == "review-comparison":
        from behavioral.review_comparison import CASES as review_cases
    if args.suite == "repository-review":
        from behavioral.repository_review import CASES as review_cases, provenance
    if args.suite in ("historical-review", "context-recovery"):
        from behavioral import historical_review, context_recovery
        scenario = historical_review if args.suite == "historical-review" else context_recovery
        review_cases, provenance = scenario.CASES, scenario.provenance
    cases = (("validation",) if args.suite == "validation" else tuple(review_cases) if args.suite in ("review", "review-comparison", "repository-review", "historical-review", "context-recovery") else
             COMPARISON_CASES if args.suite == "comparison" else CASES_TO_RUN)
    variants = (("baseline", "revised") if args.suite == "validation" else ("baseline", "consolidated") if args.suite == "review" else
                ("baseline", "pancake", "poteto") if three_arm else
                ("baseline", "pancake"))
    plan = trial_plan(cases, variants, args.repetitions, three_arm)
    source_identity, evaluator_identity = identity(ROOT), identity(EVALUATOR)
    treatments = None
    if args.suite == "validation":
        from behavioral.validation import treatment_hashes
        treatments = treatment_hashes(ROOT)
    write_json(output / "manifest.json", {
        "source": source_identity,
        "evaluator": evaluator_identity,
        "cli_version": subprocess.check_output(["codex", "--version"], text=True).strip(),
        "model": args.model, "effort": args.effort, "timeout_seconds": args.timeout,
        "suite": args.suite, "poteto": poteto, "treatments": treatments,
        "snapshot": provenance() if args.suite in ("repository-review", "historical-review", "context-recovery") else None,
        "plan": plan,
    })
    results = []
    for index, (case, repeat, variant) in enumerate(plan, 1):
        if (identity(ROOT) != source_identity or identity(EVALUATOR) != evaluator_identity
                or (three_arm and poteto_inventory(args.poteto_source) != poteto)):
            raise SystemExit("Comparison inputs changed since manifest capture; batch stopped.")
        print(f"Starting {index}/{len(plan)}: {case} {variant} repetition {repeat}", flush=True)
        result = run_trial(case, variant, output / f"run-{index:02d}", auth,
                           args.model, args.effort, args.timeout, args.suite, args.poteto_source,
                           poteto if variant == "poteto" else None)
        result["inputs_unchanged"] = (
            identity(ROOT) == source_identity and identity(EVALUATOR) == evaluator_identity
            and (not three_arm or poteto_inventory(args.poteto_source) == poteto))
        write_json(output / f"run-{index:02d}" / "result.json", result)
        result["repetition"] = repeat
        results.append(result)
        write_json(output / "results.json", results)
        print(f"Finished {index}: artifact={result['artifact']['passed']} elapsed={result['elapsed_seconds']}s", flush=True)
        if not result.get("inputs_unchanged", True):
            raise SystemExit("Comparison inputs changed during execution; inspect records before continuing.")
        if result["exit_code"] != 0 or not result["sessions"]:
            raise SystemExit("Candidate execution failed; inspect retained records before continuing.")


if __name__ == "__main__":
    main()
