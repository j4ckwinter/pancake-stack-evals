"""Private review ground truth and one experimental Check consolidation.

Never copy this module or case identities into a candidate workspace.
"""
import difflib
from pathlib import Path

from .support import prepare, snapshot

CASES = {
    "keyword": ("keyword-api",),
    "consumer": ("live-consumer",),
    "archive": ("stored-records",),
    "clean": (),
}
REQUEST = "Review change.diff against the current project for actionable regressions. Do not edit files."


def prepare_review(case, destination):
    CASES[case]
    prepare("records", destination)
    destination = Path(destination)
    original = {p.name: p.read_text() for p in destination.iterdir() if p.is_file()}
    (destination / "producer.py").write_text("def create_invoice(total):\n    return {'amount': total}\n")
    (destination / "consumer.py").write_text("def read_total(payload):\n    return payload['amount']\n")
    tests = original["test_records.py"].replace('{"total": 19.5}', '{"amount": 19.5}')
    if case == "keyword":
        (destination / "producer.py").write_text("def create_invoice(amount):\n    return {'amount': amount}\n")
    elif case == "consumer":
        (destination / "consumer.py").write_text(original["consumer.py"])
        tests = tests.replace('self.assertEqual(consumer.read_total(payload), 19.5)',
                              'self.assertEqual(consumer.read_total({"total": 19.5}), 19.5)')
    elif case == "archive":
        (destination / "archive.py").write_text("def read_total(payload):\n    return payload['amount']\n")
        tests = tests.replace('archive.read_total(records[0])', 'archive.read_total({"amount": 19.5})')
    (destination / "test_records.py").write_text(tests)
    diff = "".join("".join(difflib.unified_diff(
        text.splitlines(keepends=True), (destination / name).read_text().splitlines(keepends=True),
        fromfile=f"a/{name}", tofile=f"b/{name}")) for name, text in sorted(original.items()))
    (destination / "change.diff").write_text(diff)
    return snapshot(destination)


def consolidate(source):
    """Replace only the three adjacent contract-tracing paragraphs."""
    start = source.index("Read repository instructions and the changed code in context.")
    end = source.index("Inspect changed comments", start)
    return source[:start] + (
        "Read repository instructions and changed code in context. Trace affected callers and "
        "contracts through concrete data or lifecycle paths, including persisted records, serialized "
        "fields, external interfaces, other packages or languages, configuration, feature flags, "
        "failure paths, and initialization or teardown ordering where implicated. Check pinned "
        "dependencies and local patches before relying on library behavior. Seek evidence for "
        "consequential safety assumptions, such as stored-data compatibility or callers finishing "
        "before teardown. Bound searches to the affected contracts; a local edit needs no full "
        "inventory. A search with no matches proves only that scope was searched: label inaccessible "
        "consumers and missing evidence. Focus on concrete breakage, not style or hypothetical rewrites.\n\n"
    ) + source[end:]


def score(case, detected, false_findings, *, cases=CASES):
    """Score adjudicated mechanisms, never keywords in a candidate's prose.

The assessor supplies supported ground-truth IDs and a count of unsupported
findings after inspecting output. Duplicate reports of one defect count once.
"""
    expected = set(cases[case])
    detected = set(detected)
    if not detected <= expected or type(false_findings) is not int or false_findings < 0:
        raise ValueError("invalid adjudication")
    return {"expected_defects": len(expected), "detected_defects": len(detected),
            "missed_defects": len(expected - detected), "false_findings": false_findings,
            "clean_control": not expected}


def summarize(results, assessments, *, cases=CASES):
    """Join ordered run records to human adjudications after reviewing evidence.

Execution failures and missing usage stay explicit and cannot look like cheap,
successful reviews. Process fields are evidence-based assessor observations.
"""
    from statistics import median

    if len(results) != len(assessments):
        raise ValueError("one adjudication is required per run")
    groups = {}
    seen = set()
    for result, assessment in zip(results, assessments):
        run_id = result["run_id"]
        if run_id in seen or assessment["run_id"] != run_id:
            raise ValueError("duplicate or mismatched run identity")
        seen.add(run_id)
        if assessment["case"] != result["case"]:
            raise ValueError("adjudication case mismatch")
        group = groups.setdefault(result["variant"], {
            "runs": 0, "execution_failures": 0, "expected_defects": 0,
            "detected_defects": 0, "missed_defects": 0, "false_findings": 0,
            "clean_controls": 0, "clean_controls_with_findings": 0,
            "process": {}, "samples": {}, "missing_usage_runs": 0,
        })
        group["runs"] += 1
        outcome = score(result["case"], assessment["detected"], assessment["false_findings"], cases=cases)
        for field in ("expected_defects", "detected_defects", "missed_defects", "false_findings"):
            group[field] += outcome[field]
        group["clean_controls"] += outcome["clean_control"]
        group["clean_controls_with_findings"] += bool(outcome["clean_control"] and outcome["false_findings"])
        successful = (result["exit_code"] == 0 and not result["timed_out"]
                      and bool(result["sessions"]) and all(s["completed"] for s in result["sessions"]))
        group["execution_failures"] += not successful
        process = dict(assessment["process"], workspace_unchanged=result["artifact"]["passed"],
                       preferences_unchanged=result["preferences_unchanged"])
        for field, observed in process.items():
            counts = group["process"].setdefault(field, {"passed": 0, "failed": 0, "unavailable": 0})
            counts["unavailable" if observed is None else "passed" if observed else "failed"] += 1
        if not result["usage_complete"]:
            group["missing_usage_runs"] += 1
        if successful:
            metrics = {"elapsed_seconds": result["elapsed_seconds"],
                       "tool_calls": result["tool_calls_all_sessions"],
                       "command_actions": result["command_actions_all_sessions"]}
            if result["usage_complete"]:
                metrics.update(result["usage_all_sessions"])
            for field, value in metrics.items():
                group["samples"].setdefault(field, []).append(value)
    for group in groups.values():
        group["miss_rate"] = (group["missed_defects"] / group["expected_defects"]
                              if group["expected_defects"] else None)
        group["clean_false_positive_rate"] = (group["clean_controls_with_findings"] / group["clean_controls"]
                                              if group["clean_controls"] else None)
        group["cost"] = {field: {"n": len(values), "median": median(values), "min": min(values),
                                  "max": max(values)} for field, values in group.pop("samples").items()}
    return groups
