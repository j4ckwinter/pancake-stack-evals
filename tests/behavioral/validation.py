"""Test-only validation pilot; hidden assessment is never supplied to candidates."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from .support import CASES, snapshot

GUIDANCE = ("For rejection checks, keep unrelated inputs valid so another validation "
            "rule cannot explain the failure. Use a valid neighboring case and vary "
            "the dimension under test.")
ANCHOR = "Check that the observation can distinguish the intended behavior from the relevant failure."
GUARD = '    if type(version) is not int:\n        raise ValueError("version must be an integer")\n'


def revise_verify(text):
    if text.count(ANCHOR) != 1 or GUIDANCE in text:
        raise ValueError("Verify treatment anchor changed or treatment already present")
    return text.replace(ANCHOR, ANCHOR + " " + GUIDANCE)


def treatment_hashes(source):
    source = Path(source)
    baseline = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted((source / "skills").rglob("*")) if p.is_file()}
    baseline["docs/configuration.md"] = hashlib.sha256((source / "docs/configuration.md").read_bytes()).hexdigest()
    revised = dict(baseline)
    revised["skills/verify/SKILL.md"] = hashlib.sha256(
        revise_verify((source / "skills/verify/SKILL.md").read_text()).encode()).hexdigest()
    return {"baseline": baseline, "revised": revised}


def prepare_validation(destination):
    shutil.copytree(CASES / "validation/workspace", destination)
    return snapshot(destination)


RUN_TESTS = r'''
import contextlib, io, json, sys, types, unittest
from pathlib import Path
source = json.load(sys.stdin)
module = types.ModuleType('reader')
module.__file__ = str(Path('reader.py').resolve())
exec(compile(source, module.__file__, 'exec'), module.__dict__)
sys.modules['reader'] = module
sys.path.insert(0, '.')
valid = [({'version': 1, 'invoice': {'total': 12}}, 12),
         ({'version': 2, 'invoice': {'amount': 12}}, 12)]
assert all(module.read_total(payload) == expected for payload, expected in valid)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    suite = unittest.defaultTestLoader.discover('.', pattern='test_reader.py')
    def test_ids(tests):
        return [identifier for test in tests for identifier in
                (test_ids(test) if isinstance(test, unittest.TestSuite) else [test.id()])]
    identifiers = test_ids(suite)
    result = unittest.TestResult()
    suite.run(result)
print(json.dumps({'test_ids': identifiers, 'tests_run': result.testsRun,
                  'failures': [{'test': t.id(), 'traceback': trace} for t, trace in result.failures],
                  'errors': [{'test': t.id(), 'traceback': trace} for t, trace in result.errors],
                  'skipped': len(result.skipped),
                  'expected_failures': len(result.expectedFailures),
                  'unexpected_successes': len(result.unexpectedSuccesses)}))
'''


def run_tests(workspace, source):
    result = subprocess.run([sys.executable, "-I", "-B", "-c", RUN_TESTS],
                            cwd=workspace, input=json.dumps(source), text=True,
                            capture_output=True, timeout=10)
    if result.returncode:
        return {"tests_run": 0, "failures": [], "errors": [result.stderr], "process_failed": True}
    return json.loads(result.stdout)


def assess_validation(workspace, before):
    workspace = Path(workspace)
    current = snapshot(workspace)
    assert current.keys() == before.keys(), "candidate added or deleted files"
    assert all(current[name] == digest for name, digest in before.items()
               if name != "test_reader.py"), "protected file changed"
    source = (workspace / "reader.py").read_text()
    assert source.count(GUARD) == 1, "mutant anchor changed"
    control = run_tests(workspace, source)
    control_passed = (control["tests_run"] > 0 and not control["failures"] and not control["errors"]
                      and not control.get("unexpected_successes") and not control.get("skipped")
                      and not control.get("expected_failures"))
    mutants = {}
    for name, implementation in mutant_sources(source).items():
        mutant = run_tests(workspace, implementation)
        mutant["killed"] = (
            mutant["tests_run"] == control["tests_run"]
            and mutant.get("test_ids") == control.get("test_ids")
            and not mutant["errors"] and not mutant.get("skipped")
            and not mutant.get("expected_failures") and not mutant.get("unexpected_successes")
            and any("ValueError not raised" in f["traceback"] for f in mutant["failures"]))
        mutants[name] = mutant
    mutants_killed = all(mutant["killed"] for mutant in mutants.values())
    assert snapshot(workspace) == current, "assessment changed workspace"
    return {"passed": control_passed and mutants_killed, "scope_preserved": True,
            "control_passed": control_passed, "mutants_killed": mutants_killed,
            "control": control, "mutants": mutants}


def mutant_sources(source):
    assert source.count(GUARD) == 1, "mutant anchor changed"
    return {kind: source.replace(GUARD, GUARD.replace(
                "type(version) is not int", f"type(version) not in (int, {kind})"))
            for kind in ("bool", "float")}
