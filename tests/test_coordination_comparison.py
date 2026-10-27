import json
import os
import shutil
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


RECIPE_REPAIR = '''import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('action')
parser.add_argument('--state', type=Path, required=True)
parser.add_argument('--evidence', type=Path, required=True)
parser.add_argument('--key', required=True)
parser.add_argument('--amount', type=int)
args = parser.parse_args()
marker = args.state / ('.recipe-' + args.key + '.json')
def cli(*parts):
    return subprocess.check_output([sys.executable, '-B', 'ledger.py', '--state', str(args.state), *parts], text=True)
if args.action == 'run':
    created = not args.state.exists()
    cli('init')
    cli('seed')
    marker.write_text(json.dumps({'created': created}))
    cli('post', args.key, str(args.amount))
    record = json.loads(cli('read', args.key))
    assert record == {'key': args.key, 'account': 'demo', 'amount': args.amount}
    args.evidence.write_text(json.dumps(record))
else:
    created = json.loads(marker.read_text())['created']
    if created:
        shutil.rmtree(args.state)
    else:
        path = args.state / 'ledger.json'
        data = json.loads(path.read_text())
        del data['entries'][args.key]
        path.write_text(json.dumps(data))
        marker.unlink()
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

    def test_natural_artifact_controls(self):
        with tempfile.TemporaryDirectory() as temporary:
            for case in ('natural-import', 'natural-total'):
                with self.subTest(case=case):
                    workspace = Path(temporary) / case
                    before = cases.prepare_case(case, workspace)
                    with self.assertRaises(AssertionError):
                        cases.probe(case, workspace)
                    repairs = ({'json_input.py': JSON_REPAIR, 'csv_input.py': CSV_REPAIR, 'report.py': CLI_REPAIR}
                               if case == 'natural-import' else
                               {'app.py': 'def total(values):\n    return sum(v for v in values if v is not None)\n'})
                    for name, content in repairs.items():
                        (workspace / name).write_text(content)
                    cases.probe(case, workspace)
                    (workspace / 'test_regression.py').write_text('pass\n')
                    self.assertTrue(cases.scope_preserved(case, workspace, before))
                    if case == 'natural-total':
                        for broken in ('return 0', 'return sum(abs(v) for v in values if v is not None)',
                                       'return sum(values)'):
                            (workspace / 'app.py').write_text('def total(values):\n    ' + broken + '\n')
                            with self.assertRaises(AssertionError):
                                cases.probe(case, workspace)
                    (workspace / 'data/archive.json').write_text('[]')
                    self.assertFalse(cases.scope_preserved(case, workspace, before))

    def test_source_entrypoint_runner_routes_natural_cases(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'auth.json').write_text('{}')
            def trial(case, variant, destination, *args, **kwargs):
                destination.mkdir()
                (destination / 'final.txt').write_text('done')
                return dict(artifact=dict(passed=True, scope_preserved=True), exit_code=0,
                            timed_out=False, preferences_unchanged=True, bundle_unchanged=True,
                            sessions=[dict(parent_id=None, completed=True)])
            for entrypoint in ('fix', 'tdd', 'pancake'):
                with patch.dict(os.environ, CODEX_HOME=str(root)), \
                     patch.object(runner, 'source_identity', return_value={}), \
                     patch.object(runner, 'identity', return_value={}), \
                     patch.object(runner.subprocess, 'check_output', return_value='cli'), \
                     patch.object(runner, 'run_trial', side_effect=trial) as launch, \
                     patch('sys.argv', ['coordination_compare', '--source', str(root / 'source'),
                         '--entrypoint', entrypoint, '--output', str(root / entrypoint),
                         '--cases', 'natural-import', 'natural-total']):
                    runner.main()
                self.assertEqual([call.args[0] for call in launch.call_args_list],
                                 ['natural-import', 'natural-total'])
                for call in launch.call_args_list:
                    adapter = call.kwargs['case_adapter']
                    self.assertEqual(adapter.entrypoint, f'skills/{entrypoint}/SKILL.md')
                    self.assertTrue(adapter.allow_implementers)
                    self.assertNotIn('delegat', adapter.request)
                manifest = json.loads((root / entrypoint / 'manifest.json').read_text())
                self.assertEqual(manifest['entrypoint'], entrypoint)

    def test_trusted_recipe_controls_reject_false_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            mutations = [
                RECIPE_REPAIR,
                RECIPE_REPAIR.replace("    cli('init')\n    cli('seed')\n", ''),
                RECIPE_REPAIR.replace("    cli('post', args.key, str(args.amount))\n    record = json.loads(cli('read', args.key))", "    record = {'key': args.key, 'account': 'demo', 'amount': args.amount}"),
                RECIPE_REPAIR.replace('shutil.rmtree(args.state)', 'shutil.rmtree(args.state.parent)'),
                'try:\n    exec(' + repr(RECIPE_REPAIR) + ')\nexcept Exception:\n    pass\n',
            ]
            for index, recipe in enumerate(mutations):
                with self.subTest(index=index):
                    workspace = root / str(index)
                    cases.prepare_case('fresh-recipe', workspace)
                    (workspace / 'recipe.py').write_text(recipe)
                    if index == 0:
                        cases.probe_recipe(workspace)
                    else:
                        with self.assertRaises((AssertionError, OSError)):
                            cases.probe_recipe(workspace)

    def test_recipe_may_refuse_to_overwrite_retained_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / 'project'
            cases.prepare_case('fresh-recipe', workspace)
            recipe = RECIPE_REPAIR.replace("if args.action == 'run':",
                                          "if args.action == 'run':\n    assert not args.evidence.exists()")
            (workspace / 'recipe.py').write_text(recipe)
            cases.probe_recipe(workspace)
            self.assertTrue((workspace / 'fresh-receipt.json').is_file())
            self.assertTrue((workspace / 'preexisting-receipt.json').is_file())

    @unittest.skipUnless(os.environ.get('PANCAKE_SANDBOX_SMOKE') == '1' and shutil.which('codex'),
                         'Opt in with PANCAKE_SANDBOX_SMOKE=1 on a supported Codex sandbox host')
    def test_recipe_sandbox_smoke(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / 'project'
            before = cases.prepare_case('fresh-recipe', workspace)
            profile = root / 'profile'
            profile.mkdir()
            (workspace / 'recipe.py').write_text(RECIPE_REPAIR)
            (workspace / 'recipe.md').write_text('Run and cleanup commands use recipe.py.')
            result = cases.assess_case('fresh-recipe', workspace, before, profile)
            self.assertTrue(result['passed'], result)
            self.assertTrue(result['scope_preserved'])
            self.assertEqual(set(result['retained_receipts']), {'fresh', 'preexisting'})
            self.assertEqual((workspace / 'demo/ledger.json').read_text(), cases.RECIPE_FILES['demo/ledger.json'])

    def test_generated_recipe_requires_isolated_sandbox(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / 'project'
            before = cases.prepare_case('fresh-recipe', workspace)
            (workspace / 'recipe.py').write_text(RECIPE_REPAIR)
            (workspace / 'recipe.md').write_text('Run and cleanup commands use recipe.py.')
            with patch.object(cases.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'failure')) as run:
                result = cases.assess_case('fresh-recipe', workspace, before, root / 'profile')
            self.assertFalse(result['passed'])
            command = run.call_args.args[0]
            self.assertEqual(command[:4], ['codex', 'sandbox', '--permission-profile', ':workspace'])
            self.assertIn('sandbox_workspace_write.exclude_tmpdir_env_var=true', command)
            self.assertIn('sandbox_workspace_write.exclude_slash_tmp=true', command)
            self.assertNotEqual(Path(command[command.index('--cd') + 1]), workspace)

    def test_returned_artifact_current_and_stale_controls(self):
        with tempfile.TemporaryDirectory() as temporary:
            for case in cases.LATE_FILES:
                with self.subTest(case=case):
                    workspace = Path(temporary) / case
                    before = cases.prepare_case(case, workspace)
                    report = json.loads((workspace / 'returned/report.json').read_text())
                    self.assertTrue(report['synthetic'])
                    self.assertEqual(report['base_sha256'], cases.hashlib.sha256((workspace / 'returned/base.py').read_bytes()).hexdigest())
                    self.assertEqual(report['artifact_sha256'], cases.hashlib.sha256((workspace / 'returned/ledger.py').read_bytes()).hexdigest())
                    with self.assertRaises(AssertionError):
                        cases.probe(case, workspace)
                    (workspace / 'ledger.py').write_text(cases.LATE_ARTIFACT)
                    if case == 'late-stale':
                        with self.assertRaises(AssertionError):
                            cases.probe(case, workspace)
                        (workspace / 'ledger.py').write_text(cases.LATE_CURRENT.replace('abs(value)', 'value'))
                    cases.probe(case, workspace)
                    self.assertTrue(cases.scope_preserved(case, workspace, before))
                    correct = (workspace / 'ledger.py').read_text()
                    (workspace / 'ledger.py').write_text(correct.replace('sum(', 'float(sum(').replace(')}', '))}'))
                    with self.assertRaises(AssertionError):
                        cases.probe(case, workspace)
                    (workspace / 'ledger.py').write_text(correct)
                    (workspace / 'returned/report.json').write_text('{}')
                    self.assertFalse(cases.scope_preserved(case, workspace, before))

    def test_repeated_migration_artifact_controls(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / 'project'
            before = cases.prepare_case('repeated-migration', workspace)
            with self.assertRaises(AssertionError):
                cases.probe('repeated-migration', workspace)
            repaired = {}
            for name in cases.EXPORTERS:
                filename = name + '.py'
                original = cases.MIGRATION_FILES[filename]
                repaired[filename] = original.replace('"total": total', '"amount": total').replace(
                    'def read(record):', 'def read(record):\n    if "amount" in record:\n        return record["amount"]')
            repaired['combine.py'] = cases.COMBINE.replace('"total": sum(row["total"]', '"amount": sum(row["amount"]')
            for name, content in repaired.items():
                (workspace / name).write_text(content)
            cases.probe('repeated-migration', workspace)
            self.assertTrue(cases.scope_preserved('repeated-migration', workspace, before))
            mutants = [
                ('sales.py', repaired['sales.py'].replace('emit(total)', 'emit(amount)').replace('"amount": total', '"amount": amount')),
                ('refunds.py', repaired['refunds.py'].replace('record["refund"]["total"]', 'record["total"]')),
                ('fees.py', cases.MIGRATION_FILES['fees.py']),
                ('combine.py', cases.COMBINE),
                ('sales.py', repaired['sales.py'].replace('"amount": total', '"amount": float(total)')),
                ('sales.py', repaired['sales.py'].replace('return record["amount"]', 'return float(record["amount"])')),
                ('sales.py', repaired['sales.py'].replace('"amount": total', '"amount": total or False')),
                ('combine.py', repaired['combine.py'].replace('sum(row["amount"] for row in exports)',
                                                            'float(sum(row["amount"] for row in exports))')),
                ('combine.py', repaired['combine.py'].replace('def combine(records):',
                     'def combine(records):\n    if any(not rows for rows in records.values()):\n        raise ValueError("empty list")')),
            ]
            for name, content in mutants:
                (workspace / name).write_text(content)
                with self.assertRaises(AssertionError):
                    cases.probe('repeated-migration', workspace)
                (workspace / name).write_text(repaired[name])
            (workspace / 'data/archive.json').write_text('{}')
            self.assertFalse(cases.scope_preserved('repeated-migration', workspace, before))

    def test_runner_rejects_partial_or_mixed_modes(self):
        invalid = [[], ['--source', '/a'], ['--baseline', '/a'],
                   ['--baseline', '/a', '--candidate', '/b', '--source', '/c'],
                   ['--source', '/a', '--poteto-source', '/b', '--candidate', '/c']]
        for options in invalid:
            with self.subTest(options=options), \
                 patch('sys.argv', ['coordination_compare', '--output', '/unused', *options]), \
                 patch('sys.stderr'), patch.object(runner, 'run_trial') as launch:
                with self.assertRaises(SystemExit):
                    runner.main()
                launch.assert_not_called()

    def test_paired_runner_uses_each_frozen_pancake_bundle(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'auth.json').write_text('{}')
            def trial(case, variant, destination, *args, **kwargs):
                destination.mkdir()
                (destination / 'final.txt').write_text('done')
                return dict(artifact=dict(passed=True, scope_preserved=True), exit_code=0,
                            timed_out=False, preferences_unchanged=True, bundle_unchanged=True,
                            sessions=[dict(parent_id=None, completed=True)])
            with patch.dict(os.environ, CODEX_HOME=str(root)), \
                 patch.object(runner, 'source_identity', return_value={}), \
                 patch.object(runner, 'poteto_inventory') as inventory, \
                 patch.object(runner, 'identity', return_value={}), \
                 patch.object(runner.subprocess, 'check_output', return_value='test-cli'), \
                 patch.object(runner, 'run_trial', side_effect=trial) as launch, \
                 patch('sys.argv', ['coordination_compare', '--baseline', str(root / 'base'),
                                   '--candidate', str(root / 'candidate'), '--output', str(root / 'output'),
                                   '--cases', 'repeated-migration', 'direct-total']):
                runner.main()
            self.assertEqual(launch.call_count, 4)
            inventory.assert_not_called()
            self.assertEqual([call.args[1] for call in launch.call_args_list], ['pancake'] * 4)
            self.assertEqual([call.kwargs['source'] for call in launch.call_args_list],
                             [(root / name).resolve() for name in ('base', 'candidate', 'candidate', 'base')])
            self.assertEqual([row['variant'] for row in json.loads((root / 'output/results.json').read_text())],
                             ['baseline', 'candidate', 'candidate', 'baseline'])

    def test_added_tests_require_case_authorization(self):
        with tempfile.TemporaryDirectory() as temporary:
            for case in cases.CASES:
                workspace = Path(temporary) / case
                before = cases.prepare_case(case, workspace)
                (workspace / 'test_extra.py').write_text('pass\n')
                self.assertEqual(cases.scope_preserved(case, workspace, before), case in ('integrated-import', 'repeated-migration', 'natural-import', 'natural-total'))

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
                        results = json.loads((root / 'output/results.json').read_text())
                        self.assertEqual([row['entrypoint'] for row in results],
                                         ['skills/pancake/SKILL.md', 'skills/poteto-mode/SKILL.md',
                                          'skills/poteto-mode/SKILL.md', 'skills/pancake/SKILL.md'])
