import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from behavioral import context_recovery as context
from behavioral.compare import run_trial, trial_plan
from behavioral.support import snapshot


def assessment():
    return {'run_id': 'one', 'case': 'stale-handoff', 'process': {}, 'unsupported_claims': 0,
            'facts': {fact: {'status': 'supported', 'response_evidence': ['Quoted candidate statement'],
                             'source_evidence': [source]} for fact, source in context.FACTS.items()}}


class ContextRecoveryTests(unittest.TestCase):
    def test_current_evidence_overrides_stale_handoff_and_git_reads_preserve_every_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepared = {}
            revisions = []
            for case in context.CASES:
                work = root / case
                before = context.prepare_case(case, work)
                def git(*args):
                    return subprocess.check_output(['git', *args], cwd=work, text=True,
                        env=dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1'))
                head = git('rev-parse', 'HEAD').strip()
                prior = git('rev-parse', 'HEAD^').strip()
                revisions.append((head, prior))
                self.assertIn(prior, (work / 'checks.txt').read_text())
                self.assertNotIn(head, (work / 'checks.txt').read_text())
                self.assertIn('rename', git('show', 'HEAD:docs/decision.md'))
                self.assertIn('-def create_invoice(total):', git('diff', '--', 'producer.py'))
                self.assertIn('+def create_invoice(amount):', git('diff', '--', 'producer.py'))
                self.assertEqual(git('status', '--porcelain').splitlines(),
                    [' M notes.txt', ' M producer.py', ' M test_producer.py', '?? HANDOFF.md'])
                self.assertEqual(git('remote', '-v'), '')
                self.assertEqual(snapshot(work), before)
                self.assertIn('.git/index', before)
                prepared[case] = {name: digest for name, digest in before.items()
                                  if not name.startswith('.git/') and name != 'HANDOFF.md'}
            self.assertEqual(revisions[0], revisions[1])
            self.assertEqual(prepared['stale-handoff'], prepared['fresh-handoff'])

    def test_inherited_git_overrides_cannot_mutate_an_external_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            external = root / 'external'
            external.mkdir()
            environment = context.git_environment(os.environ)
            subprocess.run(['git', 'init', '--quiet', '--template=', str(external)],
                           env=environment, check=True)
            (external / 'precious.txt').write_text('untouched user work')
            subprocess.run(['git', '-C', str(external), 'add', '.'], env=environment, check=True)
            before = snapshot(external)
            with patch.dict(os.environ, GIT_DIR=str(external / '.git'),
                            GIT_WORK_TREE=str(external), GIT_INDEX_FILE=str(external / '.git/index'),
                            GIT_OBJECT_DIRECTORY=str(external / '.git/objects')):
                context.prepare_case('stale-handoff', root / 'workspace')
            self.assertEqual(snapshot(external), before)
            log = subprocess.check_output(['git', '-C', str(root / 'workspace'), 'log', '--format=%s'],
                                          text=True, env=environment)
            self.assertEqual(log.splitlines(), ['Accept compatible migration and record prior check',
                                               'Initial invoice contract'])

    def test_fact_ledger_counts_supported_missing_and_contradicted_separately(self):
        judged = assessment()
        judged['facts']['dirty-implementation']['status'] = 'contradicted'
        judged['facts']['stale-verification'].update(status='missed', response_evidence=[])
        judged['unsupported_claims'] = 1
        self.assertEqual(context.score('stale-handoff', judged), {
            'expected_facts': 5, 'supported_facts': 3, 'missed_facts': 1,
            'contradicted_facts': 1, 'unsupported_claims': 1})
        invalid = []
        item = assessment(); del item['facts']['next-step']; invalid.append(item)
        item = assessment(); item['facts']['unknown'] = item['facts']['next-step']; invalid.append(item)
        item = assessment(); item['facts']['next-step']['response_evidence'] = []; invalid.append(item)
        item = assessment(); item['facts']['next-step']['source_evidence'] = []; invalid.append(item)
        item = assessment(); item['facts']['next-step']['status'] = 'guess'; invalid.append(item)
        item = assessment(); item['unsupported_claims'] = True; invalid.append(item)
        for item in invalid:
            with self.subTest(item=item), self.assertRaises(ValueError):
                context.score('stale-handoff', item)

    def test_failed_execution_and_preservation_are_not_semantic_success(self):
        record = {'run_id': 'one', 'case': 'stale-handoff', 'variant': 'baseline', 'exit_code': 1,
                  'timed_out': False, 'sessions': [], 'artifact': {'passed': False},
                  'preferences_unchanged': True, 'usage_complete': False}
        outcome = context.summarize([record], [assessment()])['baseline']
        self.assertEqual(outcome['execution_failures'], 1)
        self.assertEqual(outcome['supported_facts'], 5)
        self.assertEqual(outcome['cost'], {})
        self.assertEqual(outcome['process']['workspace_unchanged'], {'passed': 0, 'failed': 1, 'unavailable': 0})
        for judgments in ([], [dict(assessment(), run_id='wrong')], [dict(assessment(), case='fresh-handoff')]):
            with self.assertRaises(ValueError):
                context.summarize([record], judgments)
        with self.assertRaises(ValueError):
            context.summarize([record, record], [assessment(), assessment()])

    def test_runner_is_read_only_bounded_and_retains_git_without_credentials(self):
        real_popen = subprocess.Popen
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            auth = root / 'auth.json'; auth.write_text('private test credential')
            for suite, case in [('context-recovery', 'stale-handoff'), ('historical-review', 'migration-clean')]:
                for variant in ('baseline', 'pancake'):
                    output = root / f'{suite}-{variant}'
                    with self.subTest(suite=suite, variant=variant), patch('behavioral.compare.subprocess.Popen') as launch:
                        process = launch.return_value
                        process.returncode = 0; process.poll.return_value = 0
                        launch.side_effect = lambda command, **kwargs: (real_popen(command, **kwargs)
                            if command[0] == 'git' else process)
                        with patch.dict(os.environ, GIT_DIR=str(root / 'outside.git'),
                                        GIT_INDEX_FILE=str(root / 'outside.index')):
                            result = run_trial(case, variant, output, auth, 'gpt-6.1-sol', 'medium', 300, suite)
                        command = launch.call_args.args[0]
                        self.assertEqual(command[command.index('--sandbox') + 1], 'read-only')
                        self.assertEqual(command[command.index('--disable') + 1], 'multi_agent')
                        self.assertNotIn('--enable', command)
                        self.assertEqual(process.communicate.call_args.kwargs['timeout'], 300)
                        prompt = (output / 'prompt.txt').read_text()
                        self.assertIn('Do not delegate', prompt)
                        self.assertNotIn(case, prompt)
                        self.assertEqual('Use the Recap skill' in prompt, suite == 'context-recovery' and variant == 'pancake')
                        self.assertEqual('Use the Pancake skill' in prompt, suite == 'historical-review' and variant == 'pancake')
                        self.assertEqual(snapshot(output / 'workspace'), json.loads((output / 'before.json').read_text()))
                        self.assertTrue(result['artifact']['passed'])
                        self.assertFalse(Path(result['candidate_root']).exists())
                        self.assertEqual(auth.read_text(), 'private test credential')
                        self.assertFalse((output / 'auth.json').exists())
                        if suite == 'context-recovery':
                            environment = launch.call_args.kwargs['env']
                            self.assertNotIn('GIT_DIR', environment)
                            self.assertNotIn('GIT_INDEX_FILE', environment)
                            self.assertEqual(environment['GIT_OPTIONAL_LOCKS'], '0')
                            self.assertEqual(environment['GIT_CONFIG_GLOBAL'], os.devnull)
                            self.assertTrue((output / 'workspace/.git/index').is_file())

    def test_launch_failure_removes_temporary_profile_and_leaves_original_auth(self):
        real_popen = subprocess.Popen
        real_mkdtemp = tempfile.mkdtemp
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            auth = root / 'auth.json'
            auth.write_text('private test credential')
            for suite, case in [('context-recovery', 'fresh-handoff'), ('historical-review', 'migration-faulty')]:
                created = []
                def create(**kwargs):
                    path = real_mkdtemp(**kwargs)
                    created.append(Path(path))
                    return path
                def launch(command, **kwargs):
                    if command[0] == 'git':
                        return real_popen(command, **kwargs)
                    raise OSError('candidate launch unavailable')
                with patch('behavioral.compare.tempfile.mkdtemp', side_effect=create), \
                        patch('behavioral.compare.subprocess.Popen', side_effect=launch):
                    with self.assertRaisesRegex(OSError, 'candidate launch unavailable'):
                        run_trial(case, 'baseline', root / suite, auth, 'model', 'medium', 300, suite)
                self.assertEqual(len(created), 1)
                self.assertFalse(created[0].exists())
                self.assertEqual(auth.read_text(), 'private test credential')
                self.assertIn('--disable', json.loads((root / suite / 'invocation.json').read_text()))

    def test_protocol_has_eight_counterbalanced_runs_per_suite(self):
        from behavioral.historical_review import CASES
        for cases in (CASES, context.CASES):
            plan = trial_plan(tuple(cases), ('baseline', 'pancake'), 2)
            self.assertEqual(len(plan), 8)
            for case in cases:
                first = [arm for name, repeat, arm in plan if name == case and repeat == 1]
                second = [arm for name, repeat, arm in plan if name == case and repeat == 2]
                self.assertEqual(first, second[::-1])
                self.assertEqual(set(first), {'baseline', 'pancake'})
