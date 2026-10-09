import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from target import LEGACY

HELPER = LEGACY / "skills/setup/scripts/catalog.py"


class CatalogTests(unittest.TestCase):
    def run_catalog(self, mode):
        with tempfile.TemporaryDirectory() as directory:
            server = Path(directory) / "codex"
            server.write_text(f"#!{sys.executable}\n" + '''
import json, os, sys, time
mode = ''' + repr(mode) + '''
initialized = False
for line in sys.stdin:
    message = json.loads(line)
    method = message['method']
    if method == 'initialized':
        initialized = True
        continue
    identifier = message['id']
    if method == 'initialize':
        result = {}
    elif method == 'model/list':
        assert initialized
        assert message['params']['includeHidden'] is False
        if mode == 'timeout':
            time.sleep(10)
        if mode == 'closed':
            break
        if mode.startswith('error'):
            error = {'code': -1}
            if mode == 'error_message':
                error['message'] = 'Sign in to Codex before listing models'
            elif mode == 'error_invalid':
                error['message'] = {'detail': 'unexpected'}
            elif mode == 'error_empty':
                error['message'] = '  '
            elif mode == 'error_shape':
                error = 'unexpected'
            print(json.dumps({'id': identifier, 'error': error}), flush=True)
            continue
        if mode == 'malformed':
            result = {'data': [{'model': 'test-model', 'supportedReasoningEfforts': [{}]}]}
        elif mode == 'empty':
            result = {'data': []}
        else:
            cursor = message['params']['cursor']
            result = {'data': [{'model': 'first' if cursor is None else 'second',
                'supportedReasoningEfforts': [{'reasoningEffort': 'high'}]}],
                'nextCursor': 'page2' if cursor is None or mode == 'cycle' else None}
    print(json.dumps({'method': 'notification'}), flush=True)
    print(json.dumps({'id': identifier, 'result': result}), flush=True)
''')
            server.chmod(0o700)
            result = subprocess.run(
                [sys.executable, str(HELPER), "--codex", str(server), "--timeout", "3"],
                text=True, capture_output=True, timeout=8,
            )
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ["codex"])
            return result

    def test_catalog_pagination_and_notifications(self):
        result = self.run_catalog("success")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"models": [
            {"model": "first", "reasoningEfforts": ["high"]},
            {"model": "second", "reasoningEfforts": ["high"]},
        ]})

    def test_failures_have_no_partial_catalog(self):
        for mode in ("error", "malformed", "empty", "closed", "timeout", "cycle"):
            with self.subTest(mode=mode):
                result = self.run_catalog(mode)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertIn("catalog:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_server_error_message_is_preserved(self):
        result = self.run_catalog("error_message")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr,
            "catalog: Codex rejected model/list: Sign in to Codex before listing models\n")

    def test_invalid_server_error_messages_use_safe_fallback(self):
        for mode in ("error", "error_invalid", "error_empty", "error_shape"):
            with self.subTest(mode=mode):
                result = self.run_catalog(mode)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "catalog: Codex rejected model/list\n")

    def test_missing_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(HELPER), "--codex", str(Path(directory) / "missing")],
                text=True, capture_output=True, timeout=6,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("catalog:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class ClaudeCatalogTests(unittest.TestCase):
    def run_catalog(self, mode):
        with tempfile.TemporaryDirectory() as directory:
            server = Path(directory) / "claude"
            record = Path(directory) / "record.json"
            server.write_text(f"#!{sys.executable}\n" + '''
import json, os, sys, time
mode = ''' + repr(mode) + '''
record = ''' + repr(str(record)) + '''
message = json.loads(sys.stdin.readline())
with open(record, 'w') as output:
    json.dump({'args': sys.argv[1:], 'message': message, 'pid': os.getpid(),
               'claudecode': os.environ.get('CLAUDECODE'),
               'config_dir': os.environ.get('CLAUDE_CONFIG_DIR')}, output)
identifier = message['request_id']
if mode == 'nested' and 'CLAUDECODE' in os.environ:
    sys.exit(1)
if mode == 'timeout':
    time.sleep(10)
if mode == 'closed':
    sys.exit(0)
rows = [{'value': 'picker-alias', 'resolvedModel': 'underlying-id',
         'supportedEffortLevels': ['medium', 'high']},
        {'value': 'unknown-effort', 'supportsEffort': True}]
if mode == 'empty':
    rows = []
if mode == 'invalid_rows':
    rows = {}
if mode == 'invalid_model':
    rows = [{'value': None}]
if mode == 'invalid_effort':
    rows = [{'value': 'model', 'supportedEffortLevels': [None]}]
if mode == 'invalid_efforts':
    rows = [{'value': 'model', 'supportedEffortLevels': 'high'}]
response = {'subtype': 'success', 'request_id': identifier, 'response': {'models': rows}}
if mode == 'error':
    response = {'subtype': 'error', 'request_id': identifier, 'error': 'metadata unavailable'}
if mode == 'invalid_result':
    response['response'] = []
if mode == 'invalid_response':
    response = []
print(json.dumps({'type': 'control_response', 'response': {'request_id': 'unrelated'}}), flush=True)
print(json.dumps({'type': 'notification'}), flush=True)
print(json.dumps({'type': 'control_response', 'response': response}), flush=True)
for line in sys.stdin:
    with open(record, 'a') as output:
        output.write('UNEXPECTED USER TURN')
''')
            server.chmod(0o700)
            result = subprocess.run(
                [sys.executable, str(HELPER), "--host", "claude", "--claude", str(server), "--timeout", "3"],
                capture_output=True, text=True, timeout=8,
            )
            self.assertTrue(record.is_file(), f"fake Claude did not initialize: {result.stderr}")
            recorded = json.loads(record.read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(recorded["pid"], 0)
            return result, recorded

    def test_nested_session_marker_is_removed_only_from_child(self):
        with patch.dict(os.environ, {'CLAUDECODE': '1', 'CLAUDE_CONFIG_DIR': '/test/claude-config'}):
            result, record = self.run_catalog('nested')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIsNone(record['claudecode'])
            self.assertEqual(record['config_dir'], '/test/claude-config')
            self.assertEqual(os.environ['CLAUDECODE'], '1')
            self.assertEqual(len(json.loads(result.stdout)['models']), 2)

    def test_initialize_only_and_observed_choices(self):
        result, record = self.run_catalog("success")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"models": [
            {"model": "picker-alias", "reasoningEfforts": ["medium", "high"]},
            {"model": "unknown-effort", "reasoningEfforts": []},
        ]})
        self.assertEqual(record['message'], {
            'type': 'control_request', 'request_id': 'pancake-model-catalog',
            'request': {'subtype': 'initialize'},
        })
        self.assertEqual(record['args'], [
            '-p', '--input-format', 'stream-json', '--output-format', 'stream-json',
            '--verbose', '--no-session-persistence', '--setting-sources', 'user',
            '--settings', '{"disableAllHooks":true}', '--strict-mcp-config',
            '--mcp-config', '{"mcpServers":{}}', '--tools', '',
        ])

    def test_failure_boundaries_do_not_return_partial_choices(self):
        for mode in ('empty', 'invalid_rows', 'invalid_model', 'invalid_effort',
                     'invalid_efforts', 'invalid_result', 'invalid_response', 'error', 'closed', 'timeout'):
            with self.subTest(mode=mode):
                result, _ = self.run_catalog(mode)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, '')
                self.assertIn('catalog:', result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                if mode == 'error':
                    self.assertIn('metadata unavailable', result.stderr)


if __name__ == "__main__":
    unittest.main()
