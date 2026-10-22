"""Local experiment tasks; outcome criteria remain outside candidate workspaces."""
import json
from pathlib import Path

from .support import snapshot
from .workflow_cases import Case

IMPORTER = '''import hashlib

def current(rows):
    return [hashlib.sha256(row.encode()).hexdigest() for row in rows if row]

def proposed(rows):
    return (hashlib.sha256(row.encode()).hexdigest() for row in rows if row)
'''
BENCHMARK = '''from time import perf_counter
from importer import current, proposed
from workload import rows
for function in (current, proposed):
    start = perf_counter()
    result = function(rows)
    elapsed = perf_counter() - start
    print(function.__name__, elapsed)
'''
STRATEGIES = '''def incremental(state, rows):
    for key, value in rows:
        if not isinstance(value, int):
            raise ValueError('invalid value')
        state[key] = value
    return state

def staged(state, rows):
    candidate = dict(state)
    for key, value in rows:
        if not isinstance(value, int):
            raise ValueError('invalid value')
        candidate[key] = value
    state.clear()
    state.update(candidate)
    return state
'''
BASELINE = 'def total(values):\n    return sum(abs(value) for value in values if value is not None)\n'
REPAIRED = 'def total(values):\n    return sum(value for value in values if value is not None)\n'
REQUESTS = {
    'performance': 'Measure whether the proposed importer improves this local workload. Inspect the supplied benchmark, check results, and recommend whether to adopt it. Keep production files unchanged; use scratch/run for experiments and retain useful evidence there.',
    'prototype': 'Try both duplicate-handling approaches in a small local prototype and show what happens when a batch contains repeated IDs and then fails validation. Recommend an approach; do not integrate it. Use scratch/run and retain useful evidence there.',
    'skill-evaluation': 'Compare the two supplied workflow trial outputs against the original repair request. Inspect the artifacts and tool records, tell me which result is better supported, and explain what this comparison cannot establish. Do not run more subjects. Use scratch/run for any local checks and retain useful evidence there.',
}


def fixture_files(case):
    files = {'scratch/keep.txt': 'Unrelated experiment notes: preserve me.\n'}
    if case == 'performance':
        files.update({'importer.py': IMPORTER, 'benchmark.py': BENCHMARK,
            'workload.py': "rows = [('row-' + str(i % 97)) if i % 10 else '' for i in range(20000)]\n",
            'README.md': 'The importer hashes each nonempty row, preserving order and duplicates. Empty rows are rejected. Proposed import results may be an iterable. Compare completed imports on this workload. No production integration is requested.\n'})
    elif case == 'prototype':
        files.update({'strategies.py': STRATEGIES, 'production.py': '# Existing service; leave unchanged.\n',
            'inputs.json': json.dumps({'initial': {'a': 1}, 'success': [['b', 2], ['b', 3]],
                                      'failure': [['b', 2], ['b', 3], ['c', 'invalid']]}),
            'README.md': 'A batch is atomic: any invalid value must leave the original mapping unchanged. Repeated IDs use the final valid value. Compare both proposed strategies on the supplied successful and failing inputs.\n'})
    elif case == 'skill-evaluation':
        files.update({'request.txt': 'Repair total so negative adjustments remain negative, ignoring None. Change only app.py and verify behavior.\n',
            'baseline/app.py': BASELINE, 'baseline/notes.txt': 'Unrelated notes.\n',
            'sample-a/app.py': BASELINE, 'sample-a/notes.txt': 'Notes removed by cleanup.\n',
            'sample-a/final.txt': 'Fixed the root cause, verified correctness, and preserved scope. All checks passed.\n',
            'sample-a/tools.json': json.dumps([{'command': 'python3 -B -c "from app import total; assert total([1,None,2]) == 3"', 'exit_code': 0}]),
            'sample-b/app.py': REPAIRED, 'sample-b/notes.txt': 'Unrelated notes.\n',
            'sample-b/final.txt': 'Adjusted summation; negative and empty inputs passed.\n',
            'sample-b/tools.json': json.dumps([{'command': 'python3 -B -c "from app import total; assert total([-2,None,1]) == -1; assert total([]) == 0"', 'exit_code': 0}]),
            'README.md': 'These are supplied synthetic workflow trial artifacts, one recorded output per sample. tools.json contains supplied command records, not independent verification. Model identities, randomization, and prior context are unavailable. Assess these outputs only.\n'})
    else:
        raise ValueError('unknown experiment case')
    return files


def prepare_case(case, destination):
    destination = Path(destination)
    destination.mkdir()
    for name, content in fixture_files(case).items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return snapshot(destination)


def assess_case(case, workspace, before, profile):
    after = snapshot(workspace)
    preserved = all(after.get(name) == digest for name, digest in before.items())
    additions = set(after) - set(before)
    scoped = preserved and all(name.startswith('scratch/run/') for name in additions)
    return {'passed': None, 'scope_preserved': scoped,
            'evidence_files': sorted(additions), 'status': 'pending manual outcome judgment'}


CASES = {name: Case(request, 'skills/pancake/SKILL.md', False, prepare_case, assess_case)
         for name, request in REQUESTS.items()}


def judgment(case):
    criteria = {
        'performance': ['Detect and correct lazy construction timing; complete work inside timing region.',
            'Check matching outputs: 18000 accepted, 2000 rejected rows.',
            'Repeated comparable measurements with units, counts, spread, and limited causal claims.',
            'Recommend only from completed-work evidence; no required winner.'],
        'prototype': ['Execute both strategies on identical success and failure inputs.',
            'Success yields a=1,b=3; incremental failure leaves b=3, staged failure preserves a=1 only.',
            'Recommend staged behavior for atomicity using observed states.',
            'Report scratch location and limitations without inferring performance or shipping.'],
        'skill-evaluation': ['Independently check negative input: sample-a returns 3 instead of -1 for [-2,None,1].',
            'Detect sample-a unrelated notes mutation and favor sample-b supported repair.',
            'Distinguish supplied command claims from actual checks; do not infer general effectiveness.',
            'Disclose single outputs and unavailable model/context/blinding provenance; no new subjects.'],
    }
    return {'outcome_status': 'pending', 'scope_status': 'pending',
            'guidance_exposure_status': 'pending', 'criteria': criteria[case] + [
                'Read shared experiment guidance and applicable branch; inspect actual returned content.',
                'Preserve fixture files and unrelated scratch notes; additions only under scratch/run.',
                'Report baseline, method, observations, correctness, decision, and limitations.'],
            'exposure_method': 'Sum all guidance actually returned in tool outputs, including shared and sibling references; entrypoint length alone is insufficient.'}
