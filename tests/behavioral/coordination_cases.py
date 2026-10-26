"""Integration fixtures and private artifact probes for bounded implementation work."""
import json
import os
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


def prepare_case(case, destination):
    destination = Path(destination)
    destination.mkdir()
    files = FILES if case == 'integrated-import' else {'app.py': 'def total(values):\n    return sum(values)\n',
                                                     'data/archive.json': '[1, 2, 3]\n'}
    for name, content in files.items():
        path = destination / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(content)
    return snapshot(destination)


def scope_preserved(case, workspace, before):
    after = snapshot(workspace)
    editable = {'json_input.py', 'csv_input.py', 'report.py'} if case == 'integrated-import' else {'app.py'}
    return (before.keys() <= after.keys()
            and all(after[name] == digest for name, digest in before.items() if name not in editable)
            and all(case == 'integrated-import' and Path(name).parent == Path('.')
                    and name.startswith('test_') and name.endswith('.py')
                    for name in after.keys() - before.keys()))


def probe(case, workspace):
    workspace = Path(workspace)
    if case == 'direct-total':
        script = 'from app import total; assert total([])==0; assert total([1,None,-3,0])==-2; assert total([None])==0'
        result = subprocess.run([sys.executable, '-B', '-c', script], cwd=workspace, capture_output=True, text=True, timeout=5)
        assert result.returncode == 0, result.stderr
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


def assess_case(case, workspace, before, profile):
    scope = scope_preserved(case, workspace, before)
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
    return dict(case=case, manual_checks=['exclusive worker write scopes', 'useful implementation by workers',
        'integration ownership', 'checks against combined artifact', 'no abandoned workers', 'proportionate coordination'],
        warning='Worker completion alone does not establish implementation or integration quality.')
