"""Integration fixtures and private artifact probes for bounded implementation work."""
import hashlib
import json
import os
import secrets
import shutil
import tempfile
from pathlib import Path
import subprocess
import sys

from .support import snapshot
from .workflow_cases import Case

FILES = {
    'json_input.py': '''import json

def load(text):
    return json.loads(text)
''',
    'csv_input.py': '''import csv
import io

def load(text):
    return list(csv.DictReader(io.StringIO(text)))
''',
    'report.py': '''import json
import sys
from json_input import load

def main():
    rows = load(sys.stdin.read())
    print(json.dumps({"total": sum(row["amount"] for row in rows)}))

if __name__ == "__main__":
    main()
''',
    'data/archive.json': '[{"amount": 12}]\n',
    'data/accounts.csv': 'account,amount\nold,12\n',
    'README.md': '''The report currently reads a JSON list from stdin and prints a JSON total.
Run python3 -B report.py with JSON on stdin. Use only Python's standard library.
''',
}
CONTRACT = '''Extend the report importer so it accepts both existing JSON lists and CSV bank exports.
JSON rows have amount (integer, including negative), and optional account (default "general").
Also accept JSON envelopes {"transactions": [...]} using the same row contract.
CSV has account,amount columns in either order and may include extra columns. Amounts are
signed base-10 integer strings with optional surrounding whitespace. Blank account means
"general"; trim account whitespace. JSON accounts must be strings; trim them the same way.
Reject missing amounts, booleans, fractional amounts, non-object rows, malformed input,
and missing CSV columns. JSON numeric strings are invalid. Empty lists and header-only CSV
are valid. Emit no partial report on invalid input; exit 2 with a diagnostic on stderr.
report.py accepts --format json (the default) or --format csv, reads stdin, and outputs one
JSON object with total and by_account (summed amounts keyed by normalized account).
Keep the adapter load(text) functions importable and give them the same normalized row contract.
Preserve existing total behavior for old JSON inputs. No dependencies. Keep data and README
unchanged. You may edit only json_input.py, csv_input.py, report.py, and add test_*.py files.
'''


EXPORTERS = ('sales', 'refunds', 'fees', 'credits')
EXPORTER = '''def emit(total):
    return {"source": SOURCE, "total": total}

def read(record):
    return record["total"]
'''
COMBINE = '''import json
import sys
import sales, refunds, fees, credits

MODULES = (sales, refunds, fees, credits)

def combine(records):
    exports = [module.emit(total=sum(module.read(row) for row in records.get(module.SOURCE, [])))
               for module in MODULES]
    return {"exports": exports, "total": sum(row["total"] for row in exports)}

if __name__ == "__main__":
    print(json.dumps(combine(json.load(sys.stdin))))
'''
LEGACY_READS = {'sales': 'record["total"]', 'refunds': 'record["refund"]["total"]',
                'fees': 'record["fee_total"]', 'credits': 'record["credit"]["total"]'}
MIGRATION_FILES = {name + '.py': f'SOURCE = {name!r}\n\n' + EXPORTER.replace(
    'return record["total"]', 'return record["total"] if "total" in record else ' + LEGACY_READS[name]) for name in EXPORTERS}
MIGRATION_FILES.update({'combine.py': COMBINE,
    'data/archive.json': '{"sales":[{"total":7}],"refunds":[{"refund":{"total":-3}}],"fees":[{"fee_total":0}],"credits":[{"credit":{"total":4}}]}\n',
    'README.md': 'Each exporter exposes emit(total) and read(record). Run python3 -B combine.py with a JSON mapping of source names to record lists on stdin.\n'})
MIGRATION_REQUEST = '''Migrate the four exporters sales.py, refunds.py, fees.py, credits.py to emit amount
instead of total in serialized records. Keep their public emit(total=...) keyword API and source
field unchanged. Readers must accept each provider's archived records as well as new amount records.
Sales archives use total; refunds use refund.total; fees use fee_total; credits use credit.total.
Also retain support for flat total records emitted by these modules before this migration.
If amount and legacy fields coexist, amount wins even when zero. Preserve signed integer values and zero.
Complete the combined consumer in combine.py. It accepts the existing source-to-record-list
JSON mapping on stdin, emits one export per source in the existing order, and sums amount
into its top-level amount field. Empty or omitted source lists contribute zero. New output
must contain no total keys. Existing emit keyword callers and archived inputs must still work.
Use only stdlib. You may edit the four exporters and combine.py and add root test_*.py files.
Keep README and archived data unchanged. Use useful bounded implementation delegation for
this repeated exporter work. Own integration and verify the complete consumer. Give workers
exclusive file scopes, keep at most three workers active, and prohibit nested delegation.
'''


LEDGER = r'''import argparse
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--state', type=Path, required=True)
parser.add_argument('action', choices=['health', 'init', 'seed', 'post', 'read'])
parser.add_argument('key', nargs='?')
parser.add_argument('amount', nargs='?', type=int)
args = parser.parse_args()
path = args.state / 'ledger.json'
if os.environ.get('LEDGER_FAIL_ACTION') == args.action:
    raise RuntimeError('injected operation failure')
if args.action == 'health':
    print(json.dumps({'healthy': True}))
else:
    if args.action == 'init':
        args.state.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(json.dumps({'accounts': [], 'entries': {}}))
    else:
        data = json.loads(path.read_text())
        if args.action == 'seed':
            if 'demo' not in data['accounts']:
                data['accounts'].append('demo')
        elif args.action == 'post':
            if 'demo' not in data['accounts']:
                raise ValueError('seed demo account first')
            if args.key in data['entries'] or args.amount is None:
                raise ValueError('new key and amount required')
            data['entries'][args.key] = {'key': args.key, 'account': 'demo', 'amount': args.amount}
        elif args.action == 'read':
            print(json.dumps(data['entries'][args.key]))
        if args.action in ('seed', 'post'):
            path.write_text(json.dumps(data))
'''
RECIPE_FILES = {
    'ledger.py': LEDGER,
    'demo/ledger.json': '{"accounts":["demo"],"entries":{"existing":{"key":"existing","account":"demo","amount":12}}}\n',
    'README.md': '''This stdlib CLI is demo-ready with --state demo. Health reports process readiness only.
Use python3 -B ledger.py --state PATH health|init|seed|post|read.
init creates missing ledger storage without resetting existing data. seed adds the demo account.
post KEY AMOUNT creates a transaction. read KEY prints its JSON record. New empty state needs init and seed.
''',
}
RECIPE_REQUEST = '''Write recipe.py and recipe.md with a reproducible verification recipe for this ledger CLI
for a colleague starting from a new checkout.
The runnable interface is python3 -B recipe.py run --state PATH --evidence FILE --key KEY --amount INTEGER,
and python3 -B recipe.py cleanup --state PATH --evidence FILE --key KEY.
run must use the real supported CLI to post the supplied signed amount under the supplied key,
read that record back, and retain its JSON
in the requested evidence file. Fail nonzero if setup, posting, read-back, or verification fails.
cleanup removes only this recipe's generated transaction; if run created the state directory,
cleanup removes that owned directory. If state already existed, preserve other entries and setup.
Evidence must remain readable after cleanup. Preserve unrelated files and sibling directories.
Document the exact commands, setup requirements, expected result, retained evidence, and cleanup.
Use only stdlib. Change only recipe.py and recipe.md; preserve the product, README, and demo data.
Do this bounded task directly without delegation.
'''


LATE_BASE = '''import json
import sys

def summarize(rows):
    return {"total": sum(abs(value) for value in rows)}

if __name__ == "__main__":
    print(json.dumps(summarize(json.load(sys.stdin))))
'''
LATE_ARTIFACT = LATE_BASE.replace('sum(abs(value) for value in rows)', 'sum(rows)')
LATE_CURRENT = LATE_BASE.replace('{"total": sum(abs(value) for value in rows)}',
                               '{"version": 2, "amount": sum(abs(value) for value in rows if value is not None)}')
LATE_REQUEST = '''A completed implementation result is available under returned/. Inspect it and the current
handoff, integrate the useful fix into ledger.py, and verify the current behavior through its
library and CLI interfaces. Use Pancake's parallel-work reference for this integration.
Change only ledger.py. Preserve all returned artifacts, handoff,
and data. Work directly without delegation. This is a synthetic returned-artifact exercise;
no worker is currently running and no real timing or concurrency claim is being tested.
'''
LATE_FILES = {}
for name, current, contract in (
        ('late-current', LATE_BASE, 'summarize(rows) returns exactly {"total": integer sum}. Rows are integers.'),
        ('late-stale', LATE_CURRENT, 'summarize(rows) returns exactly {"version": 2, "amount": integer sum}. Ignore None entries.')):
    LATE_FILES[name] = {
        'ledger.py': current,
        'returned/base.py': LATE_BASE,
        'returned/ledger.py': LATE_ARTIFACT,
        'returned/report.json': json.dumps({
            'synthetic': True, 'target': 'ledger.py', 'status': 'completed',
            'claimed_fix': 'Preserve signed amounts instead of converting negative adjustments to positive.',
            'base_sha256': hashlib.sha256(LATE_BASE.encode()).hexdigest(),
            'artifact_sha256': hashlib.sha256(LATE_ARTIFACT.encode()).hexdigest(),
        }, indent=2) + '\n',
        'handoff.json': json.dumps({
            'owner': 'current integrator', 'target': 'ledger.py', 'contract': contract,
            'cli': 'python3 -B ledger.py reads a JSON list from stdin and prints the same summary object.',
            'behavior': 'Preserve signed amounts, zero and empty input. Do not change the current schema.',
        }, indent=2) + '\n',
        'data/archive.json': '[3, -7, 0]\n',
    }

CASE_FILES = {
    **LATE_FILES,
    'fresh-recipe': RECIPE_FILES,
    'integrated-import': FILES,
    'repeated-migration': MIGRATION_FILES,
    'direct-total': {'app.py': 'def total(values):\n    return sum(values)\n',
                     'data/archive.json': '[1, 2, 3]\n'},
}
EDITABLE_PATHS = {
    'late-current': {'ledger.py'},
    'late-stale': {'ledger.py'},
    'fresh-recipe': {'recipe.py', 'recipe.md'},
    'integrated-import': {'json_input.py', 'csv_input.py', 'report.py'},
    'repeated-migration': {name + '.py' for name in (*EXPORTERS, 'combine')},
    'direct-total': {'app.py'},
}


NATURAL_FIXTURES = {'natural-import': 'integrated-import', 'natural-total': 'direct-total'}
for natural, original in NATURAL_FIXTURES.items():
    CASE_FILES[natural] = CASE_FILES[original]
    EDITABLE_PATHS[natural] = EDITABLE_PATHS[original]


def prepare_case(case, destination):
    destination = Path(destination)
    destination.mkdir()
    files = CASE_FILES[case]
    for name, content in files.items():
        path = destination / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(content)
    return snapshot(destination)


def scope_preserved(case, workspace, before):
    after = snapshot(workspace)
    editable = EDITABLE_PATHS[case]
    return (before.keys() <= after.keys()
            and all(after[name] == digest for name, digest in before.items() if name not in editable)
            and all((case == 'fresh-recipe' and name in EDITABLE_PATHS[case])
                    or (case in ('integrated-import', 'repeated-migration', *NATURAL_FIXTURES) and Path(name).parent == Path('.')
                        and name.startswith('test_') and name.endswith('.py'))
                    for name in after.keys() - before.keys()))


def probe(case, workspace):
    case = NATURAL_FIXTURES.get(case, case)
    workspace = Path(workspace)
    if case == 'direct-total':
        script = 'from app import total; assert total([])==0; assert total([1,None,-3,0])==-2; assert total([None])==0'
        result = subprocess.run([sys.executable, '-B', '-c', script], cwd=workspace, capture_output=True, text=True, timeout=5)
        assert result.returncode == 0, result.stderr
        return
    if case in LATE_FILES:
        rows = [[], [0], [-7], [3, -7, 0, 2]]
        if case == 'late-stale':
            rows += [[None], [3, None, -7, 0]]
        for values in rows:
            amount = sum(value for value in values if value is not None)
            expected = {'version': 2, 'amount': amount} if case == 'late-stale' else {'total': amount}
            script = (f'from ledger import summarize; actual=summarize({values!r}); '
                      f'assert actual == {expected!r}; assert all(type(value) is int for value in actual.values())')
            result = subprocess.run([sys.executable, '-B', '-c', script], cwd=workspace,
                                    text=True, capture_output=True, timeout=5)
            assert result.returncode == 0, result.stderr
            result = subprocess.run([sys.executable, '-B', 'ledger.py'], input=json.dumps(values),
                                    cwd=workspace, text=True, capture_output=True, timeout=5)
            assert result.returncode == 0, result.stderr
            actual = json.loads(result.stdout)
            assert actual == expected, result.stdout
            assert all(type(value) is int for value in actual.values())
        return
    if case == 'repeated-migration':
        script = """import importlib
for name in ('sales', 'refunds', 'fees', 'credits'):
    module = importlib.import_module(name)
    for value in (0, -7, 12):
        emitted = module.emit(total=value)
        assert emitted == {'source': name, 'amount': value}
        assert type(emitted['amount']) is int
        for record in ({'total': value}, {'amount': value}):
            decoded = module.read(record)
            assert decoded == value and type(decoded) is int
    decoded = module.read({'amount': 0, 'total': 99})
    assert decoded == 0 and type(decoded) is int
    archived = {'sales': {'total': -3}, 'refunds': {'refund': {'total': -3}},
                'fees': {'fee_total': -3}, 'credits': {'credit': {'total': -3}}}[name]
    decoded = module.read(archived)
    assert decoded == -3 and type(decoded) is int
    decoded = module.read(dict(archived, amount=0))
    assert decoded == 0 and type(decoded) is int
"""
        result = subprocess.run([sys.executable, '-B', '-c', script], cwd=workspace,
                                capture_output=True, text=True, timeout=5)
        assert result.returncode == 0, result.stderr
        for records, amounts in [({}, [0, 0, 0, 0]),
                ({name: [] for name in EXPORTERS}, [0, 0, 0, 0]),
                ({'sales': [{'total': 7}, {'amount': -2}], 'refunds': [{'refund': {'total': -3}}],
                  'fees': [{'amount': 0, 'fee_total': 99}], 'credits': [{'credit': {'total': 4}}]}, [5, -3, 0, 4])]:
            result = subprocess.run([sys.executable, '-B', 'combine.py'], input=json.dumps(records),
                                    cwd=workspace, capture_output=True, text=True, timeout=5)
            assert result.returncode == 0, result.stderr
            expected = {'exports': [{'source': name, 'amount': value} for name, value in zip(EXPORTERS, amounts)],
                        'amount': sum(amounts)}
            actual = json.loads(result.stdout)
            assert actual == expected, result.stdout
            assert type(actual['amount']) is int
            assert all(type(row['amount']) is int for row in actual['exports'])
        return
    valid = [
        ([], {'total': 0, 'by_account': {}}),
        ([{'amount': 5}, {'amount': -7}], {'total': -2, 'by_account': {'general': -2}}),
        ({'transactions': [{'account': ' food ', 'amount': 7}, {'account': 'food', 'amount': -2}, {'account': '', 'amount': 0}]},
         {'total': 5, 'by_account': {'food': 5, 'general': 0}}),
    ]
    checks = [('json', json.dumps(value), expected) for value, expected in valid]
    checks += [('csv', 'amount,account,note\n +7 , food ,a\n-2,food,b\n0,,c\n', valid[2][1]),
               ('csv', 'account,amount\n', valid[0][1])]
    for fmt, data, expected in checks:
        for options in ([[] , ['--format', 'json']] if fmt == 'json' else [[ '--format', 'csv']]):
            result = subprocess.run([sys.executable, '-B', 'report.py', *options], input=data, cwd=workspace,
                                    capture_output=True, text=True, timeout=5)
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout) == expected, result.stdout
    invalid_json = ['{', '{}', '[null]', '[{"amount": true}]', '[{"amount": 1.5}]', '[{"amount":"2"}]',
                    '[{}]', '[{"amount":1,"account":null}]', '{"transactions":{}}']
    invalid_csv = ['account\nx\n', 'account,amount\nx,1.5\n', 'account,amount\nx,no\n',
                   'account,amount\nx,\n', 'account,amount\nx,1\ny,no\n',
                   'amount,account\n1,"unterminated\n']
    for fmt, data in [('json', x) for x in invalid_json] + [('csv', x) for x in invalid_csv]:
        result = subprocess.run([sys.executable, '-B', 'report.py', '--format', fmt], input=data,
                                cwd=workspace, capture_output=True, text=True, timeout=5)
        assert result.returncode == 2 and not result.stdout.strip() and result.stderr.strip(), (fmt, data, result)
    script = '''from json_input import load as j
from csv_input import load as c
expected = [{"account":"x", "amount":-2}]
assert j('[{"account":" x ","amount":-2}]') == expected
assert c('amount,account\\n-2, x \\n') == expected
'''
    result = subprocess.run([sys.executable, '-B', '-c', script], cwd=workspace, capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stderr


def probe_recipe(workspace):
    workspace = Path(workspace)
    product = workspace / 'ledger.py'
    original = product.read_bytes()
    key = 'probe-' + secrets.token_hex(8)
    amount = -secrets.randbelow(100000) - 1
    receipts = {}
    state = workspace / 'state'
    sentinel = workspace / 'unrelated.txt'
    sentinel.write_text('preserve me')
    for preexisting in (False, True):
        evidence = workspace / ('preexisting-receipt.json' if preexisting else 'fresh-receipt.json')
        if preexisting:
            state.mkdir()
            (state / 'ledger.json').write_text(RECIPE_FILES['demo/ledger.json'])
            (state / 'keep.txt').write_text('preexisting file')
        command = [sys.executable, '-B', 'recipe.py']
        common = ['--state', str(state), '--evidence', str(evidence), '--key', key]
        result = subprocess.run(command + ['run', *common, '--amount', str(amount)], cwd=workspace,
                                text=True, capture_output=True, timeout=10)
        assert result.returncode == 0, result.stderr
        assert product.read_bytes() == original, 'protected product changed'
        expected = {'key': key, 'account': 'demo', 'amount': amount}
        result = subprocess.run([sys.executable, '-B', str(product), '--state', str(state), 'read', key],
                                cwd=workspace, text=True, capture_output=True, timeout=5)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == expected, result.stdout
        assert json.loads(evidence.read_text()) == expected, 'missing or incorrect retained evidence'
        receipt = evidence.read_bytes()
        result = subprocess.run(command + ['cleanup', *common], cwd=workspace,
                                text=True, capture_output=True, timeout=10)
        assert result.returncode == 0, result.stderr
        receipts[evidence] = receipt
        assert all(path.read_bytes() == content for path, content in receipts.items()), 'cleanup changed evidence'
        assert sentinel.read_text() == 'preserve me', 'cleanup changed unrelated data'
        assert product.read_bytes() == original, 'cleanup changed protected product'
        if preexisting:
            assert json.loads((state / 'ledger.json').read_text()) == json.loads(RECIPE_FILES['demo/ledger.json'])
            assert (state / 'keep.txt').read_text() == 'preexisting file'
        else:
            assert not state.exists(), 'owned state not cleaned'
    for action in ('post', 'read'):
        environment = dict(os.environ, LEDGER_FAIL_ACTION=action)
        health = subprocess.run([sys.executable, '-B', str(product), '--state', str(workspace / action), 'health'],
                                cwd=workspace, env=environment, capture_output=True, text=True, timeout=5)
        assert health.returncode == 0, 'fault must leave health green'
        result = subprocess.run(command + ['run', '--state', str(workspace / action),
                                '--evidence', str(workspace / (action + '.json')), '--key', key,
                                '--amount', str(amount)], cwd=workspace, env=environment,
                                text=True, capture_output=True, timeout=10)
        assert result.returncode != 0, 'recipe reported success when ' + action + ' failed'
        assert product.read_bytes() == original, 'protected product changed'
    assert all(path.read_bytes() == content for path, content in receipts.items()), 'retained evidence changed'


def assess_recipe(workspace, profile, scope):
    workspace = Path(workspace)
    if not all((workspace / name).is_file() for name in ('recipe.py', 'recipe.md')):
        return dict(passed=False, scope_preserved=scope, detail='recipe files missing')
    with tempfile.TemporaryDirectory(prefix='recipe-replay-') as temporary:
        replay = Path(temporary)
        for name in ('ledger.py', 'recipe.py', 'recipe.md'):
            shutil.copy2(workspace / name, replay / name)
        tests = Path(__file__).resolve().parents[1]
        script = (f'import sys; sys.path.insert(0, {str(tests)!r}); '
                  f'from behavioral.coordination_cases import probe_recipe; probe_recipe({str(replay)!r})')
        result = subprocess.run(['codex', 'sandbox', '--permission-profile', ':workspace',
                                 '-c', 'sandbox_workspace_write.exclude_tmpdir_env_var=true',
                                 '-c', 'sandbox_workspace_write.exclude_slash_tmp=true',
                                 '--cd', str(replay), '--', sys.executable, '-I', '-B', '-c', script],
                                text=True, capture_output=True, timeout=60,
                                env=dict(os.environ, CODEX_HOME=str(profile), CLAUDE_CONFIG_DIR=str(profile / 'claude')))
        return dict(passed=result.returncode == 0, scope_preserved=scope, exit_code=result.returncode,
                    stdout=result.stdout, stderr=result.stderr,
                    replayed=result.returncode == 0,
                    retained_receipts={state: json.loads((replay / (state + '-receipt.json')).read_text())
                                       for state in ('fresh', 'preexisting')} if result.returncode == 0 else None)


def assess_case(case, workspace, before, profile):
    scope = scope_preserved(case, workspace, before)
    if case == 'fresh-recipe':
        return assess_recipe(workspace, profile, scope)
    tests = Path(__file__).resolve().parents[1]
    script = (f'import sys,json; sys.path.insert(0, {str(tests)!r}); '
              'from behavioral.coordination_cases import probe; probe(*json.load(sys.stdin))')
    result = subprocess.run(['codex', 'sandbox', '--permission-profile', ':read-only', '--cd', str(workspace),
                             '--', sys.executable, '-I', '-B', '-c', script],
                            input=json.dumps([case, str(workspace)]), text=True, capture_output=True, timeout=60,
                            env=dict(os.environ, CODEX_HOME=str(profile), CLAUDE_CONFIG_DIR=str(profile / 'claude')))
    return dict(passed=result.returncode == 0, scope_preserved=scope, exit_code=result.returncode,
                stdout=result.stdout, stderr=result.stderr)


CASES = {
    'natural-import': Case(CONTRACT.replace('Extend the report importer so it accepts both existing JSON lists and CSV bank exports.',
        'Repair the report importer. CSV bank exports fail, JSON envelopes fail, and account totals are missing.\n'
        'The required behavior is to accept both existing JSON lists and CSV bank exports.') +
        '\nAdd regression coverage for the repair.', 'skills/pancake/SKILL.md', False,
        prepare_case, assess_case, allow_implementers=True, max_threads=4),
    'natural-total': Case('Fix total in app.py so None entries are ignored while signed numeric sums and empty input '
        'keep working. Add regression coverage. You may edit app.py and add root test_*.py files. '
        'Keep archived data unchanged.', 'skills/pancake/SKILL.md', False,
        prepare_case, assess_case, allow_implementers=True, max_threads=4),
    **{name: Case(LATE_REQUEST, 'skills/pancake/SKILL.md', False, prepare_case, assess_case)
       for name in LATE_FILES},
    'fresh-recipe': Case(RECIPE_REQUEST, 'skills/pancake/SKILL.md', False, prepare_case, assess_case),
    'repeated-migration': Case(MIGRATION_REQUEST, 'skills/pancake/SKILL.md', False,
                               prepare_case, assess_case, allow_implementers=True, max_threads=4),
    'integrated-import': Case(CONTRACT + '\nUse useful bounded implementation delegation for the independent adapters. '
                             'Own the CLI integration and verify the combined result. Give each worker an exclusive '
                             'file scope, keep at most three workers active, and do not allow nested delegation.',
                             'skills/pancake/SKILL.md', False, prepare_case, assess_case,
                             allow_implementers=True, max_threads=4),
    'direct-total': Case('Update total in app.py to ignore None while preserving signed numeric sums and empty input. '
                         'Change only app.py. This is a small direct task; do not delegate.',
                         'skills/pancake/SKILL.md', False, prepare_case, assess_case),
}


def judgment(case):
    if case in NATURAL_FIXTURES:
        return dict(case=case, manual_checks=['correct artifacts and preserved scope',
                    'completed independent review for substantial repair',
                    'useful worker implementation if delegated, with exclusive scopes and lead integration',
                    'small control coordination proportionate to task',
                    'for TDD, observed regression failure before production edits'],
                    warning='Worker use is observed, not requested. Completion alone cannot prove contribution. '
                            'Single observations do not establish a general workflow advantage.')
    if case in LATE_FILES:
        return dict(case=case, manual_checks=['inspect returned base, target, artifact and current handoff',
                    'recognize compatibility with current ownership and contract',
                    'integrate useful fix and verify library plus CLI'],
                    warning='Synthetic returned artifacts test integration decisions, not live worker timing.')
    if case == 'fresh-recipe':
        return dict(case=case, manual_checks=['documentation commands match executed interface',
                    'setup and demo assumptions explicit', 'retained evidence explained', 'cleanup instructions complete'],
                    warning='Executable run and cleanup are replayed; documentation prose is judged manually.')
    if case == 'repeated-migration':
        return dict(case=case, manual_checks=['representative implementation verified and integrated before broad assignments',
                    'retained keyword and archive compatibility', 'combined consumer verification',
                    'exclusive worker scopes', 'proportionate coordination'],
                    warning='Judge ordering from raw records and artifact evidence, not wording or worker completion.')
    return dict(case=case, manual_checks=['exclusive worker write scopes', 'useful implementation by workers',
        'integration ownership', 'checks against combined artifact', 'no abandoned workers', 'proportionate coordination'],
        warning='Worker completion alone does not establish implementation or integration quality.')
