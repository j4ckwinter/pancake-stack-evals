import json
import os
from dataclasses import replace
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from behavioral import coordination_cases as cases, coordination_compare as runner
from behavioral.compare import run_trial, poteto_inventory
from behavioral.workflow_cases import Case
from target import source_root

JSON_REPAIR = '''import json

def load(text):
    rows = json.loads(text)
    if isinstance(rows, dict):
        rows = rows['transactions']
    if not isinstance(rows, list):
        raise ValueError('rows must be a list')
    result = []
    for row in rows:
        if not isinstance(row, dict) or type(row.get('amount')) is not int:
            raise ValueError('invalid amount')
        account = row.get('account', 'general')
        if not isinstance(account, str):
            raise ValueError('invalid account')
        result.append({'account': account.strip() or 'general', 'amount': row['amount']})
    return result
'''
CSV_REPAIR = '''import csv
import io
import re

def load(text):
    reader = csv.DictReader(io.StringIO(text), strict=True)
    if not {'account', 'amount'} <= set(reader.fieldnames or []):
        raise ValueError('missing columns')
    result = []
    for row in reader:
        value = (row['amount'] or '').strip()
        if not re.fullmatch(r'[+-]?[0-9]+', value):
            raise ValueError('invalid amount')
        result.append({'account': (row['account'] or '').strip() or 'general', 'amount': int(value)})
    return result
'''
CLI_REPAIR = '''import argparse
import json
import sys
import json_input
import csv_input

parser = argparse.ArgumentParser()
parser.add_argument('--format', choices=['json', 'csv'], default='json')
args = parser.parse_args()
try:
    rows = (json_input if args.format == 'json' else csv_input).load(sys.stdin.read())
    accounts = {}
    for row in rows:
        accounts[row['account']] = accounts.get(row['account'], 0) + row['amount']
    print(json.dumps({'total': sum(accounts.values()), 'by_account': accounts}))
except (ValueError, KeyError, TypeError, csv_input.csv.Error) as error:
    print(str(error), file=sys.stderr)
    sys.exit(2)
'''


class CoordinationTests(unittest.TestCase):
    def test_case_permissions_and_compatibility(self):
        old = Case('request', 'entry', False)
        self.assertFalse(old.allow_implementers)
        self.assertEqual(old.max_threads, 2)
        for cap in (True, False, 1, 5, 2.0, '4', None):
            with self.assertRaises(ValueError):
                replace(old, max_threads=cap)
        with self.assertRaises(ValueError):
            replace(old, read_only=True, allow_implementers=True)

    def test_artifact_controls(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / 'project'
            before = cases.prepare_case('integrated-import', workspace)
            with self.assertRaises(AssertionError):
                cases.probe('integrated-import', workspace)
            repairs = {'json_input.py': JSON_REPAIR, 'csv_input.py': CSV_REPAIR, 'report.py': CLI_REPAIR}
            for name, content in repairs.items():
                (workspace / name).write_text(content)
            cases.probe('integrated-import', workspace)
            self.assertTrue(cases.scope_preserved('integrated-import', workspace, before))
            for name, broken in [('csv_input.py', cases.FILES['csv_input.py']),
                                 ('csv_input.py', CSV_REPAIR.replace(', strict=True', '')),
                                 ('json_input.py', JSON_REPAIR.replace("row['amount']", "abs(row['amount'])")),
                                 ('report.py', CLI_REPAIR.replace('sys.exit(2)', 'sys.exit(0)'))]:
                (workspace / name).write_text(broken)
                with self.assertRaises(AssertionError):
                    cases.probe('integrated-import', workspace)
                (workspace / name).write_text(repairs[name])
            (workspace / 'data/archive.json').write_text('[]')
            self.assertFalse(cases.scope_preserved('integrated-import', workspace, before))

    def test_added_tests_require_case_authorization(self):
        with tempfile.TemporaryDirectory() as temporary:
            for case in cases.CASES:
                workspace = Path(temporary) / case
                before = cases.prepare_case(case, workspace)
                (workspace / 'test_extra.py').write_text('pass\n')
                self.assertEqual(cases.scope_preserved(case, workspace, before), case == 'integrated-import')

    def test_poteto_adapter_preserves_inputs_and_permissions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skills = root / 'skills'
            entry = skills / 'poteto-mode/SKILL.md'
            entry.parent.mkdir(parents=True)
            entry.write_text('[Port](../poteto-mode/references/codex-port.md)\n')
            (entry.parent / 'references').mkdir()
            (entry.parent / 'references/codex-port.md').write_text('inherit model and effort')
            inventory = poteto_inventory(skills)
            auth = root / 'auth.json'
            auth.write_text('{}')
            for mutate in (False, True):
                observed = {}
                def launch(command, **kwargs):
                    observed['command'] = command
                    if mutate:
                        profile = Path(kwargs['env']['CODEX_HOME'])
                        (profile.parent / 'bundle/skills/poteto-mode/SKILL.md').write_text('changed')
                    return SimpleNamespace(returncode=0, communicate=lambda *a, **kw: None, poll=lambda: 0)
                adapter = replace(cases.CASES['integrated-import'], assessment=lambda *a: dict(passed=True, scope_preserved=True))
                with patch('behavioral.compare.subprocess.Popen', side_effect=launch):
                    result = run_trial('integrated-import', 'poteto', root / str(mutate), auth, None, None, 10,
                                       source=source_root(), poteto_source=skills, expected_poteto=inventory, case_adapter=adapter)
                command = observed['command']
                self.assertIn('agents.max_threads=4', command)
                self.assertIn('--enable', command)
                self.assertNotIn('-m', command)
                self.assertFalse(any('model_reasoning_effort' in x for x in command))
                prompt = (root / str(mutate) / 'prompt.txt').read_text()
                self.assertIn('skills/poteto-mode/SKILL.md', prompt)
                self.assertNotIn('skills/pancake/SKILL.md', prompt)
                self.assertIn('exclusive write scope', prompt)
                self.assertIn('must not delegate further', prompt)
                self.assertEqual(result['artifact']['scope_preserved'], not mutate)
            self.assertEqual(poteto_inventory(skills), inventory)
            with self.assertRaisesRegex(ValueError, 'input changed'):
                run_trial('integrated-import', 'poteto', root / 'bad', auth, None, None, 10,
                          poteto_source=skills, expected_poteto={}, case_adapter=adapter)

    def test_assessor_sandboxes_generated_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / 'project'
            before = cases.prepare_case('direct-total', workspace)
            with patch.object(cases.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'failure')) as run:
                result = cases.assess_case('direct-total', workspace, before, Path(temporary))
            self.assertFalse(result['passed'])
            self.assertTrue(result['scope_preserved'])
            self.assertEqual(run.call_args.args[0][:4], ['codex', 'sandbox', '--permission-profile', ':read-only'])

    def test_runner_stops_invalid_execution_not_behavior_failure(self):
        for fault in (None, 'scope', 'bundle', 'timeout', 'root', 'final', 'drift'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / 'auth.json').write_text('{}')
                def trial(case, variant, destination, *args, **kwargs):
                    destination.mkdir()
                    (destination / 'final.txt').write_text('' if fault == 'final' else 'done')
                    return dict(artifact=dict(passed=False, scope_preserved=fault not in ('scope', 'bundle')),
                                exit_code=0, timed_out=fault == 'timeout', preferences_unchanged=True, bundle_unchanged=fault != 'bundle',
                                sessions=[dict(parent_id=None, completed=fault != 'root')])
                with patch.dict(os.environ, CODEX_HOME=str(root)), \
                     patch.object(runner, 'source_identity', side_effect=[{}, {}, {'changed': True}] if fault == 'drift' else None, return_value={}), \
                     patch.object(runner, 'poteto_inventory', return_value={}), \
                     patch.object(runner, 'identity', return_value={}), \
                     patch.object(runner.subprocess, 'check_output', return_value='test-cli'), \
                     patch.object(runner, 'run_trial', side_effect=trial) as launch, \
                     patch('sys.argv', ['coordination_compare', '--source', str(root / 'source'),
                                       '--poteto-source', str(root / 'poteto'), '--output', str(root / 'output')]):
                    if fault:
                        with self.assertRaisesRegex(SystemExit, 'Invalid trial'):
                            runner.main()
                        self.assertEqual(launch.call_count, 1)
                    else:
                        runner.main()
                        self.assertEqual(launch.call_count, 4)
