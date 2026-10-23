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


RETENTION_REQUEST = (
    'Measure whether the proposed importer improves this local workload. Inspect '
    'and correct the supplied benchmark in scratch/run, checking matching outputs '
    'and measuring completed work. Run two separate measurement batches using '
    'the supplied sample_store.BatchRecorder(directory, metadata) context manager '
    'with a new directory under scratch/run for each batch. Record each raw '
    'measurement as a JSON object immediately after measuring it; include method, '
    'units and workload context in metadata. Retain both batches and report their '
    'locations, counts and performance conclusions with limitations. Preserve all '
    'supplied files, including sample_store.py, and unrelated scratch notes.'
)


def prepare_retention_case(case, destination):
    prepare_case('performance', destination)
    recorder = Path(destination) / 'sample_store.py'
    recorder.write_text(Path(__file__).with_name('sample_store.py').read_text())
    return snapshot(destination)


def _json_object(text):
    def invalid_constant(value):
        raise ValueError('nonfinite JSON value: ' + value)

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result

    value = json.loads(text, parse_constant=invalid_constant,
                       object_pairs_hook=unique_object)
    # JSON numbers such as 1e999 also overflow to nonfinite floats in Python.
    json.dumps(value, allow_nan=False)
    if not isinstance(value, dict):
        raise ValueError('expected JSON object')
    return value


def assess_retention_case(case, workspace, before, profile):
    result = assess_case('performance', workspace, before, profile)
    root = Path(workspace) / 'scratch/run'
    directories = sorted({path.parent for name in ('metadata.json', 'samples.jsonl', 'complete.json')
                          for path in root.rglob(name)})
    batches = []
    for directory in directories:
        batch = {'directory': str(directory.relative_to(workspace)),
                 'sample_count': 0, 'complete': False, 'errors': []}
        try:
            _json_object((directory / 'metadata.json').read_text())
            with (directory / 'samples.jsonl').open() as stream:
                for line in stream:
                    if not line.endswith('\n'):
                        raise ValueError('unterminated sample record')
                    _json_object(line)
                    batch['sample_count'] += 1
            completion = directory / 'complete.json'
            if completion.exists():
                marker = _json_object(completion.read_text())
                count = marker.get('count')
                if type(count) is not int or count != batch['sample_count']:
                    raise ValueError('completion count does not match samples')
                batch['complete'] = True
        except (OSError, UnicodeError, ValueError) as error:
            batch['errors'].append(str(error))
        batches.append(batch)
    result.update(batch_records=batches,
                  retained_sample_count=sum(batch['sample_count'] for batch in batches),
                  completed_batch_count=sum(batch['complete'] for batch in batches),
                  incomplete_batch_count=sum(not batch['complete'] for batch in batches),
                  sample_retention_valid=(result['scope_preserved'] and len(batches) >= 2
                      and all(batch['complete'] and batch['sample_count'] > 0
                              and not batch['errors'] for batch in batches)))
    return result


RETENTION_CASE = Case(RETENTION_REQUEST, 'skills/pancake/SKILL.md', False,
                      prepare_retention_case, assess_retention_case)
