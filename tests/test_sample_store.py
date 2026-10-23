import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from behavioral import experiment_cases as cases
from behavioral.sample_store import BatchRecorder


class SampleStoreTests(unittest.TestCase):
    def test_two_batches_preserve_order_metadata_and_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ('first', 'second'):
                with BatchRecorder(root / name, {'method': 'completed work', 'units': 's'}) as batch:
                    for value in (0.2, 0.1):
                        batch.record({'elapsed': value})
                        self.assertIn(str(value), (root / name / 'samples.jsonl').read_text())
                self.assertEqual(json.loads((root / name / 'metadata.json').read_text()),
                                 {'method': 'completed work', 'units': 's'})
                self.assertEqual([json.loads(line) for line in (root / name / 'samples.jsonl').read_text().splitlines()],
                                 [{'elapsed': 0.2}, {'elapsed': 0.1}])
                self.assertEqual(json.loads((root / name / 'complete.json').read_text()), {'count': 2})

    def test_collision_never_changes_existing_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'batch'
            with BatchRecorder(directory, {'original': True}) as batch:
                batch.record({'value': 1})
            original = {path.name: path.read_bytes() for path in directory.iterdir()}
            with self.assertRaises(FileExistsError):
                with BatchRecorder(directory, {'replacement': True}):
                    self.fail('collision accepted')
            self.assertEqual({path.name: path.read_bytes() for path in directory.iterdir()}, original)

    def test_exception_and_invalid_sample_keep_only_written_prefix(self):
        for failure in ('exception', 'serialization', 'nan', 'infinity', 'not-object'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary) / 'batch'
                with self.assertRaises((RuntimeError, TypeError, ValueError)):
                    with BatchRecorder(directory, {}) as batch:
                        batch.record({'value': 1})
                        if failure == 'exception':
                            raise RuntimeError('interrupted')
                        batch.record({'value': {'serialization': object(), 'nan': float('nan'),
                                               'infinity': float('inf')}.get(failure)}
                                     if failure != 'not-object' else [])
                self.assertEqual((directory / 'samples.jsonl').read_text(), '{"value": 1}\n')
                self.assertFalse((directory / 'complete.json').exists())
                with self.assertRaises(RuntimeError):
                    batch.record({'value': 2})

    def test_ambiguous_keys_and_cycles_preserve_written_prefix(self):
        ambiguous = {1: 'first', '1': 'second'}
        cyclic = {}
        cyclic['self'] = cyclic
        for sample in (ambiguous, {'nested': [ambiguous]}, cyclic):
            with self.subTest(sample=sample), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary) / 'batch'
                with self.assertRaises(ValueError):
                    with BatchRecorder(directory, {}) as batch:
                        batch.record({'value': 1})
                        batch.record(sample)
                self.assertEqual((directory / 'samples.jsonl').read_text(), '{"value": 1}\n')
                self.assertFalse((directory / 'complete.json').exists())

    def test_rejects_unopened_closed_and_reentered_recorder(self):
        with tempfile.TemporaryDirectory() as temporary:
            recorder = BatchRecorder(Path(temporary) / 'batch', {})
            with self.assertRaises(RuntimeError):
                recorder.record({})
            with recorder:
                recorder.record({})
            with self.assertRaises(RuntimeError):
                recorder.record({})
            with self.assertRaises(RuntimeError):
                with recorder:
                    pass

    def test_invalid_metadata_creates_no_directory(self):
        for metadata in ([], {'value': float('nan')}, {'value': object()},
                         {'nested': {1: 'first', '1': 'second'}}):
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary) / 'batch'
                with self.assertRaises((TypeError, ValueError)):
                    with BatchRecorder(directory, metadata):
                        pass
                self.assertFalse(directory.exists())

    def test_killed_process_retains_flushed_sample_without_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'batch'
            source = Path(cases.__file__).with_name('sample_store.py')
            script = ('import sys, time\n'
                      'sys.path.insert(0, sys.argv[1])\n'
                      'from sample_store import BatchRecorder\n'
                      'with BatchRecorder(sys.argv[2], {"method": "kill test"}) as batch:\n'
                      '    batch.record({"value": 1})\n'
                      '    print("flushed", flush=True)\n'
                      '    time.sleep(30)\n')
            process = subprocess.Popen([sys.executable, '-B', '-c', script,
                                        str(source.parent), str(directory)], stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True)
            try:
                import selectors
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout, selectors.EVENT_READ)
                    self.assertTrue(selector.select(timeout=5), 'writer never became ready')
                self.assertEqual(process.stdout.readline(), 'flushed\n')
                process.kill()
                process.communicate(timeout=5)
            finally:
                if process.poll() is None:
                    process.kill()
                process.communicate(timeout=5)
            self.assertEqual((directory / 'samples.jsonl').read_text(), '{"value": 1}\n')
            self.assertFalse((directory / 'complete.json').exists())

    def workspace(self, root):
        workspace = root / 'workspace'
        before = cases.RETENTION_CASE.preparation('sample-retention', workspace)
        for name in ('first', 'second'):
            with BatchRecorder(workspace / 'scratch/run' / name, {'units': 's'}) as batch:
                batch.record({'elapsed': 0.1})
                batch.record({'elapsed': 0.2})
        return workspace, before

    def assess(self, workspace, before):
        return cases.RETENTION_CASE.assessment('sample-retention', workspace, before, workspace)

    def test_assessment_counts_batches_without_deciding_performance(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace, before = self.workspace(Path(temporary))
            result = self.assess(workspace, before)
            self.assertTrue(result['sample_retention_valid'])
            self.assertEqual(result['retained_sample_count'], 4)
            self.assertEqual(result['completed_batch_count'], 2)
            self.assertEqual(result['incomplete_batch_count'], 0)
            self.assertIsNone(result['passed'])
            (workspace / 'sample_store.py').write_text('changed')
            result = self.assess(workspace, before)
            self.assertFalse(result['scope_preserved'])
            self.assertFalse(result['sample_retention_valid'])

    def test_assessment_rejects_corruption_and_reports_retained_prefix(self):
        corruptions = [('metadata.json', '[]'), ('metadata.json', '{"x":NaN}'),
                       ('metadata.json', '{"x":1e999}'), ('metadata.json', '{"x":1,"x":2}'),
                       ('samples.jsonl', '{"elapsed": 1}\ninvalid\n'),
                       ('samples.jsonl', '{"elapsed": 1}'), ('samples.jsonl', '[]\n'),
                       ('samples.jsonl', '{"elapsed": Infinity}\n'),
                       ('complete.json', '{"count": 1}'), ('complete.json', '{"count": true}'),
                       ('complete.json', 'broken')]
        for name, content in corruptions:
            with self.subTest(name=name, content=content), tempfile.TemporaryDirectory() as temporary:
                workspace, before = self.workspace(Path(temporary))
                (workspace / 'scratch/run/first' / name).write_text(content)
                result = self.assess(workspace, before)
                self.assertFalse(result['sample_retention_valid'])
                self.assertTrue(result['batch_records'][0]['errors'])

    def test_incomplete_and_missing_batches_are_not_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / 'workspace'
            before = cases.RETENTION_CASE.preparation('sample-retention', workspace)
            self.assertFalse(self.assess(workspace, before)['sample_retention_valid'])
            with self.assertRaises(RuntimeError):
                with BatchRecorder(workspace / 'scratch/run/interrupted', {}) as batch:
                    batch.record({'elapsed': 0.1})
                    raise RuntimeError('stop')
            result = self.assess(workspace, before)
            self.assertEqual(result['retained_sample_count'], 1)
            self.assertEqual(result['completed_batch_count'], 0)
            self.assertEqual(result['incomplete_batch_count'], 1)
            self.assertFalse(result['sample_retention_valid'])

    def test_historical_suite_unchanged(self):
        self.assertEqual(set(cases.CASES), {'performance', 'prototype', 'skill-evaluation'})
        self.assertNotIn('sample_store.py', cases.fixture_files('performance'))
