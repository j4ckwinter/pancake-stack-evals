import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from behavioral.compare import main, run_trial, trial_plan
from behavioral.repository_review import (
    ARCHIVE_SHA256, CASES, PROBES, REVISION, extract_snapshot,
    prepare_review, prepare_snapshot, provenance,
)
from behavioral.support import snapshot


class RepositoryReviewTests(unittest.TestCase):
    def test_snapshot_integrity_and_complete_context(self):
        record = provenance()
        self.assertEqual(record['revision'], REVISION)
        self.assertEqual(record['archive_sha256'], ARCHIVE_SHA256)
        self.assertEqual(len(record['files']), 122)
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / 'project'
            self.assertEqual(prepare_snapshot(workspace), record['files'])
            for name in ('AGENTS.md', 'README.md', 'tests/behavioral/compare.py',
                         'tests/test_identity.py', 'tests/test_trial_traces.py'):
                self.assertIn(name, record['files'])
            self.assertNotIn('tests/behavioral/repository_review.py', record['files'])
            self.assertNotIn('fixtures/repository-review/provenance.json', record['files'])

    def test_snapshot_rejects_dangerous_entries_and_tampered_content(self):
        def archive(name, kind=tarfile.REGTYPE):
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode='w') as output:
                entry = tarfile.TarInfo(name)
                entry.type = kind
                entry.linkname = '/tmp/target'
                entry.size = 1 if kind == tarfile.REGTYPE else 0
                output.addfile(entry, io.BytesIO(b'x') if entry.size else None)
            return gzip.compress(stream.getvalue(), mtime=0)
        digest = hashlib.sha256(b'x').hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            for name, kind in [('../escape', tarfile.REGTYPE), ('/absolute', tarfile.REGTYPE),
                               ('link', tarfile.SYMTYPE), ('hardlink', tarfile.LNKTYPE),
                               ('pipe', tarfile.FIFOTYPE), ('.git/config', tarfile.REGTYPE),
                               ('a/../escape', tarfile.REGTYPE)]:
                with self.subTest(name=name):
                    destination = Path(temporary) / 'project'
                    with self.assertRaises(ValueError):
                        extract_snapshot(destination, archive(name, kind), {name: digest})
                    self.assertFalse(destination.exists())
            with self.assertRaisesRegex(ValueError, 'hashes'):
                extract_snapshot(Path(temporary) / 'project', archive('file'), {'file': 'wrong'})

    def test_original_and_cases_pass_existing_tests_and_separate_hidden_probes(self):
        with tempfile.TemporaryDirectory() as temporary:
            for case in ('original', *CASES):
                with self.subTest(case=case):
                    workspace = Path(temporary) / case
                    before = prepare_snapshot(workspace) if case == 'original' else prepare_review(case, workspace)
                    for family in PROBES:
                        filename = 'test_identity.py' if family == 'identity' else 'test_trial_traces.py'
                        local = subprocess.run(
                            [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', filename, '-v'],
                            cwd=workspace, capture_output=True, text=True, timeout=30)
                        self.assertEqual(local.returncode, 0, local.stderr)
                        self.assertNotIn('Ran 0 tests', local.stderr)
                        script = "import sys; sys.path[:0] = ['.', 'tests']\n" + PROBES[family]
                        probe = subprocess.run([sys.executable, '-I', '-B', '-c', script],
                                               cwd=workspace, capture_output=True, text=True, timeout=30)
                        faulty = case == family + '-faulty'
                        self.assertEqual(probe.returncode != 0, faulty, probe.stderr)
                        if faulty:
                            self.assertIn('AssertionError:', probe.stderr)
                            self.assertNotIn('ImportError', probe.stderr)
                    self.assertEqual(snapshot(workspace), before)
                    if case != 'original':
                        original = provenance()['files']
                        changed = {name for name in original if original[name] != before[name]}
                        self.assertEqual(changed, {'run_checks.py'} if case.startswith('identity')
                                         else {'tests/behavioral/traces.py'})
                        self.assertEqual(before.keys() - original.keys(), {'change.diff'})
                        self.assertNotIn(case, (workspace / 'change.diff').read_text())

    def test_plan_is_sixteen_trials_with_each_case_counterbalanced(self):
        plan = trial_plan(tuple(CASES), ('baseline', 'pancake'), 2)
        self.assertEqual(len(plan), 16)
        for case in CASES:
            first = [variant for name, repetition, variant in plan if name == case and repetition == 1]
            second = [variant for name, repetition, variant in plan if name == case and repetition == 2]
            self.assertEqual(first, second[::-1])
            self.assertEqual(set(first), {'baseline', 'pancake'})

    def test_runner_uses_readonly_no_delegation_and_preserves_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            auth = root / 'auth.json'
            auth.write_text('fake auth')
            for variant in ('baseline', 'pancake'):
                with self.subTest(variant=variant), patch('behavioral.compare.subprocess.Popen') as launch:
                    process = launch.return_value
                    process.returncode = 0
                    process.poll.return_value = 0
                    result = run_trial('identity-clean', variant, root / variant, auth,
                                       'model', 'medium', 300, 'repository-review')
                    command = launch.call_args.args[0]
                    self.assertEqual(command[command.index('--sandbox') + 1], 'read-only')
                    self.assertEqual(command[command.index('--disable') + 1], 'multi_agent')
                    self.assertNotIn('--enable', command)
                    prompt = (root / variant / 'prompt.txt').read_text()
                    self.assertIn('Do not delegate', prompt)
                    self.assertEqual('Use the Pancake skill' in prompt, variant == 'pancake')
                    self.assertNotIn('identity-clean', prompt)
                    self.assertTrue(result['artifact']['passed'])
                    self.assertEqual(result['snapshot'], provenance())
                    self.assertFalse(Path(result['candidate_root']).exists())
                    self.assertEqual(auth.read_text(), 'fake auth')

    def test_main_stops_when_inputs_change_and_records_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / 'profile'
            profile.mkdir()
            (profile / 'auth.json').write_text('fake auth')
            calls = []
            def observed(path):
                calls.append(path)
                return {'revision': 'changed' if len(calls) >= 3 else 'fixed'}
            args = ['compare.py', '--suite', 'repository-review', '--model', 'model',
                    '--repetitions', '2', '--output', str(root / 'results')]
            with patch.dict(os.environ, CODEX_HOME=str(profile)), patch.object(sys, 'argv', args), \
                    patch('behavioral.compare.identity', side_effect=observed), \
                    patch('behavioral.compare.subprocess.check_output', return_value='codex test'), \
                    patch('behavioral.compare.run_trial') as trial:
                with self.assertRaisesRegex(SystemExit, 'inputs changed'):
                    main()
                trial.assert_not_called()
            manifest = json.loads((root / 'results/manifest.json').read_text())
            self.assertEqual(manifest['snapshot'], provenance())
            self.assertEqual(len(manifest['plan']), 16)

    def test_main_records_input_change_during_trial_and_stops(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / 'profile'
            profile.mkdir()
            (profile / 'auth.json').write_text('fake auth')
            calls = []
            def observed(path):
                calls.append(path)
                return {'revision': 'changed' if len(calls) >= 5 else 'fixed'}
            def candidate(case, variant, destination, *args):
                destination.mkdir()
                return dict(run_id=destination.name, case=case, variant=variant,
                            artifact={'passed': True}, elapsed_seconds=1, exit_code=0,
                            sessions=[{'completed': True}])
            args = ['compare.py', '--suite', 'repository-review', '--model', 'model',
                    '--repetitions', '2', '--output', str(root / 'results')]
            with patch.dict(os.environ, CODEX_HOME=str(profile)), patch.object(sys, 'argv', args), \
                    patch('behavioral.compare.identity', side_effect=observed), \
                    patch('behavioral.compare.subprocess.check_output', return_value='codex test'), \
                    patch('behavioral.compare.run_trial', side_effect=candidate) as trial:
                with self.assertRaisesRegex(SystemExit, 'inputs changed during'):
                    main()
                self.assertEqual(trial.call_count, 1)
            result = json.loads((root / 'results/run-01/result.json').read_text())
            self.assertFalse(result['inputs_unchanged'])
