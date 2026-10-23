import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from behavioral.reading_paths import build_report


class ReadingPathTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.first = '# First\n\nRead the actual implementation.\n'
        self.second = '# Second\n\nVerify the observable result.\n'
        (self.source / 'first.md').write_text(self.first)
        (self.source / 'second.md').write_text(self.second)

    def session(self, outputs, name='session', command='cat first.md second.md'):
        path = self.root / f'{name}.jsonl'
        events = [{'type': 'session_meta', 'payload': {'id': name}},
            {'type': 'response_item', 'payload': {'type': 'custom_tool_call',
                'call_id': 'read', 'name': 'functions.exec', 'input': command}}]
        events.extend({'type': 'response_item', 'payload': {'type': 'custom_tool_call_output',
            'call_id': 'read', 'output': output}} for output in outputs)
        path.write_text('\n'.join(json.dumps(event) for event in events))
        return path

    def test_complete_bodies_and_repeated_returns_have_separate_volumes(self):
        path = self.session([self.first + self.second, self.first, self.first + self.first])
        report = build_report(self.source, [path])
        self.assertEqual(report['totals'], dict(unique_files=2, complete_returns=5,
            unique_words=12, repeated_words=18, total_words=30))
        self.assertEqual(report['files']['first.md']['complete_returns'], 4)
        self.assertEqual([item['count'] for item in report['files']['first.md']['occurrences']], [1, 1, 2])
        self.assertEqual(report['source']['markdown_sha256']['first.md'],
            hashlib.sha256(self.first.encode()).hexdigest())
        self.assertEqual(report['sessions'][0]['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_mentions_partial_and_truncated_bodies_do_not_establish_reads(self):
        path = self.session(['Read first.md and second.md', '# First\n\nRead the actual',
            '# Second\n\n[output truncated]', self.first], command=self.second)
        report = build_report(self.source, [path])
        self.assertEqual(report['totals'], dict(unique_files=1, complete_returns=1,
            unique_words=6, repeated_words=0, total_words=6))
        self.assertEqual(report['files']['second.md']['complete_returns'], 0)
        self.assertEqual([item['reason'] for item in report['unmeasured']],
                         ['no_complete_source_body'] * 3)

    def test_nested_exec_results_decode_once_and_preserve_repeated_events(self):
        envelope = json.dumps({'exit_code': 0, 'output': self.first})
        blocks = [{'type': 'input_text', 'text': envelope},
                  {'type': 'text', 'text': json.dumps({'content': [{'type': 'text', 'text': self.second}]})},
                  {'type': 'image', 'data': self.second}]
        path = self.session([blocks, {'output': self.first}, envelope + '\n' + envelope])
        report = build_report(self.source, [path])
        self.assertEqual(report['totals'], dict(unique_files=2, complete_returns=5,
            unique_words=12, repeated_words=18, total_words=30))

    def test_partial_chunks_are_not_joined_into_invented_complete_return(self):
        path = self.session([self.first[:15], self.first[15:], self.second])
        report = build_report(self.source, [path])
        self.assertEqual(report['files']['first.md']['complete_returns'], 0)
        self.assertEqual(report['files']['second.md']['complete_returns'], 1)
        self.assertEqual(len(report['unmeasured']), 2)

    def test_multiple_sessions_count_independently_and_duplicate_paths_rejected(self):
        first = self.session([self.first])
        second = self.session([self.first], name='worker')
        report = build_report(self.source, [second, first])
        self.assertEqual(report['totals']['repeated_words'], 6)
        self.assertEqual([item['session_id'] for item in report['files']['first.md']['occurrences']],
                         ['session', 'worker'])
        with self.assertRaisesRegex(ValueError, 'distinct paths'):
            build_report(self.source, [first, first])

    def test_identical_source_bodies_are_ambiguous_not_double_counted(self):
        (self.source / 'copy.md').write_text(self.first)
        report = build_report(self.source, [self.session([self.first + self.second])])
        self.assertEqual(report['totals']['complete_returns'], 1)
        self.assertEqual(report['unmeasured'][0]['reason'], 'identical_source_bodies')
        self.assertEqual(report['unmeasured'][0]['candidates'], ['copy.md', 'first.md'])

    def test_cli_writes_private_report_and_rejects_input_destinations(self):
        session = self.session([self.first])
        output = self.root / 'report.json'
        script = Path(__file__).parent / 'behavioral' / 'reading_paths.py'
        command = [sys.executable, '-B', str(script), '--source', str(self.source),
                   '--sessions', str(session), '--output']
        result = subprocess.run(command + [str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(output.read_text())['totals']['total_words'], 6)
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        for forbidden in (self.source / 'report.json', script.parent / 'report.json', session):
            result = subprocess.run(command + [str(forbidden)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
        result = subprocess.run(command + [str(output)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
