import difflib
from pathlib import Path

from . import review
from .support import snapshot

CASES = {
    "config-bug": ("zero-limit",),
    "config-clean": (),
    "lifetime-bug": ("closed-stream",),
    "lifetime-clean": (),
}
REQUEST = review.REQUEST
WORK_CATEGORIES = (
    "unrelated_investigation", "redundant_verification",
    "unnecessary_delegation", "scope_expansion",
)


def prepare_review(case, destination):
    CASES[case]
    destination = Path(destination)
    destination.mkdir(parents=True)
    if case.startswith("config-"):
        original = {
            "README.md": (
                "# Batch selection\n\n"
                "select_jobs(jobs, options) returns at most options['limit'] jobs. "
                "The limit is a nonnegative integer or None. An omitted or None limit "
                "uses 20. Zero disables selection and must return no jobs.\n"
            ),
            "settings.py": (
                "DEFAULT_LIMIT = 20\n\n\n"
                "def resolve_limit(options):\n"
                "    limit = options.get('limit')\n"
                "    if limit is None:\n"
                "        return DEFAULT_LIMIT\n"
                "    return limit\n"
            ),
            "jobs.py": (
                "from settings import resolve_limit\n\n\n"
                "def select_jobs(jobs, options):\n"
                "    return jobs[:resolve_limit(options)]\n"
            ),
            "test_jobs.py": (
                "import unittest\nfrom jobs import select_jobs\n\n\n"
                "class JobTests(unittest.TestCase):\n"
                "    def test_explicit_limit(self):\n"
                "        self.assertEqual(select_jobs(['a', 'b', 'c'], {'limit': 2}), ['a', 'b'])\n\n"
                "    def test_default(self):\n"
                "        self.assertEqual(select_jobs(list(range(30)), {}), list(range(20)))\n"
            ),
        }
        expression = ("options.get('limit') or DEFAULT_LIMIT" if case == "config-bug" else
                      "DEFAULT_LIMIT if options.get('limit') is None else options['limit']")
        changed = {"settings.py": "DEFAULT_LIMIT = 20\n\n\ndef resolve_limit(options):\n"
                                  f"    return {expression}\n"}
    else:
        original = {
            "README.md": (
                "# Report rows\n\n"
                "read_rows(path) returns an iterable of stripped, nonblank UTF-8 lines. "
                "Callers may consume it after the function returns. Empty files yield no rows. "
                "The stream must close when iteration finishes. render_report(path) returns "
                "the rows joined by commas.\n"
            ),
            "reader.py": (
                "def parse_rows(stream):\n"
                "    return (line.strip() for line in stream if line.strip())\n\n\n"
                "def read_rows(path):\n"
                "    with open(path, encoding='utf-8') as stream:\n"
                "        return list(parse_rows(stream))\n"
            ),
            "report.py": (
                "from reader import read_rows\n\n\n"
                "def render_report(path):\n"
                "    rows = read_rows(path)\n"
                "    return ','.join(rows)\n"
            ),
            "test_reader.py": (
                "import io\nimport unittest\nfrom reader import parse_rows\n\n\n"
                "class ReaderTests(unittest.TestCase):\n"
                "    def test_rows(self):\n"
                "        self.assertEqual(list(parse_rows(io.StringIO(' a \\n\\nb\\n'))), ['a', 'b'])\n\n"
                "    def test_empty(self):\n"
                "        self.assertEqual(list(parse_rows(io.StringIO(''))), [])\n"
            ),
        }
        operation = "return parse_rows(stream)" if case == "lifetime-bug" else "yield from parse_rows(stream)"
        changed = {"reader.py": original["reader.py"].replace("return list(parse_rows(stream))", operation)}
    for name, content in original.items():
        (destination / name).write_text(changed.get(name, content))
    diff = "".join("".join(difflib.unified_diff(
        original[name].splitlines(keepends=True), content.splitlines(keepends=True),
        fromfile=f"a/{name}", tofile=f"b/{name}")) for name, content in sorted(changed.items()))
    (destination / "change.diff").write_text(diff)
    return snapshot(destination)


def validate_work(assessment):
    """Validate evidence-bearing judgments without inferring waste from cost."""
    work = assessment.get("unnecessary_work")
    if not isinstance(work, dict):
        raise ValueError("unnecessary_work assessment is required")
    if work.get("status") == "unavailable":
        if set(work) != {"status", "reason"} or not isinstance(work["reason"], str) or not work["reason"].strip():
            raise ValueError("unavailable work requires a reason and no item count")
        return work
    if work.get("status") != "assessed" or set(work) != {"status", "items"} or not isinstance(work["items"], list):
        raise ValueError("work must be assessed with items or unavailable with a reason")
    seen = set()
    for item in work["items"]:
        if (not isinstance(item, dict) or set(item) != {"id", "category", "evidence", "reason"}
                or any(not isinstance(item[key], str) or not item[key].strip() for key in ("id", "category", "reason"))
                or item["id"] in seen or item["category"] not in WORK_CATEGORIES
                or not isinstance(item["evidence"], list) or not item["evidence"]
                or any(not isinstance(ref, str) or not ref.strip() for ref in item["evidence"])):
            raise ValueError("work items require unique IDs, known categories, reasons, and evidence references")
        seen.add(item["id"])
    return work


def summarize(results, assessments):
    """Summarize selected runs; select matching pairs first for per-case results."""
    groups = review.summarize(results, assessments, cases=CASES)
    for group in groups.values():
        group["unnecessary_work"] = {
            "assessed_runs": 0, "unavailable_runs": 0, "runs_with_items": 0,
            "items": 0, "categories": {category: 0 for category in WORK_CATEGORIES},
        }
    for result, assessment in zip(results, assessments):
        work = validate_work(assessment)
        counts = groups[result["variant"]]["unnecessary_work"]
        if work["status"] == "unavailable":
            counts["unavailable_runs"] += 1
            continue
        counts["assessed_runs"] += 1
        counts["runs_with_items"] += bool(work["items"])
        counts["items"] += len(work["items"])
        for item in work["items"]:
            counts["categories"][item["category"]] += 1
    for group in groups.values():
        counts = group["unnecessary_work"]
        if not counts["assessed_runs"]:
            counts["items"] = counts["runs_with_items"] = counts["categories"] = None
    return groups
