import json
from pathlib import Path
import tempfile
import unittest
from behavioral.traces import summarize_session, completed_workers


class TrialTraceTests(unittest.TestCase):
    def read(self, events):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'trace.jsonl'
            path.write_text('\n'.join(json.dumps(event) for event in events))
            return summarize_session(path)

    def test_custom_tool_records_preserve_execution_evidence(self):
        output = [{"type": "input_text", "text": '{"exit_code": 1, "output": "TypeError"}'}]
        result = self.read([
            {"type": "response_item", "payload": {"type": "custom_tool_call", "call_id": "check",
                "name": "exec", "input": "text(await tools.exec_command({cmd: 'python3 probe.py'}))"}},
            {"type": "response_item", "payload": {"type": "custom_tool_call_output",
                "call_id": "check", "output": output}},
        ])
        self.assertEqual(result["calls"][0]["id"], "check")
        self.assertIn("python3 probe.py", result["calls"][0]["arguments"]["input"])
        self.assertEqual(result["outputs"], [{"id": "check", "output": output}])

    def test_completed_worker_requires_identity_verdict_and_completion(self):
        worker = self.read([
            {'type': 'session_meta', 'payload': {'id': 'child', 'parent_thread_id': 'root', 'source': {'subagent': {'thread_spawn': {'agent_path': '/root/review'}}}}},
            {'type': 'turn_context', 'payload': {'model': 'actual-model', 'effort': 'low'}},
            {'type': 'response_item', 'payload': {'type': 'message', 'role': 'assistant', 'phase': 'final_answer', 'content': [{'text': 'No findings.'}]}},
            {'type': 'event_msg', 'payload': {'type': 'task_complete'}}])
        self.assertEqual(completed_workers([worker], 'root'), [worker])
        self.assertEqual(worker['selections'], [{'model': 'actual-model', 'effort': 'low'}])
        for field, value in [('completed', False), ('verdicts', []), ('parent_id', 'other'), ('id', None), ('agent_path', None)]:
            self.assertEqual(completed_workers([dict(worker, **{field: value})], 'root'), [])

    def test_wait_or_lead_claim_does_not_establish_worker(self):
        lead = self.read([
            {'type': 'session_meta', 'payload': {'id': 'root'}},
            {'type': 'response_item', 'payload': {'type': 'function_call_output', 'call_id': 'wait', 'output': 'Wait completed.'}},
            {'type': 'response_item', 'payload': {'type': 'message', 'role': 'assistant', 'phase': 'final_answer', 'content': [{'text': 'Reviewer completed.'}]}},
            {'type': 'event_msg', 'payload': {'type': 'task_complete'}}])
        self.assertEqual(completed_workers([lead], 'root'), [])

    def test_requested_model_is_not_observed_selection(self):
        session = self.read([{'type': 'response_item', 'payload': {'type': 'function_call', 'name': 'spawn_agent', 'call_id': 'spawn', 'arguments': json.dumps({'model': 'requested', 'message': 'opaque task'})}}])
        self.assertEqual(session['selections'], [])
        self.assertEqual(session['calls'][0]['arguments'], {'model': 'requested'})

    def test_new_turn_invalidates_old_verdict(self):
        session = self.read([
            {'type': 'response_item', 'payload': {'type': 'message', 'role': 'assistant', 'phase': 'final_answer', 'content': [{'text': 'Old verdict'}]}},
            {'type': 'event_msg', 'payload': {'type': 'task_complete'}},
            {'type': 'event_msg', 'payload': {'type': 'task_started'}}])
        self.assertFalse(session['completed'])
        self.assertEqual(session['verdicts'], [])

    def test_fork_history_does_not_replace_worker_identity_or_settings(self):
        session = self.read([
            {'type': 'session_meta', 'payload': {'id': 'child', 'parent_thread_id': 'root', 'source': {'subagent': {'thread_spawn': {'agent_path': '/root/review'}}}}},
            {'type': 'session_meta', 'payload': {'id': 'root', 'source': 'exec'}},
            {'type': 'turn_context', 'payload': {'model': 'parent-model'}},
            {'type': 'event_msg', 'payload': {'type': 'task_started'}},
            {'type': 'turn_context', 'payload': {'model': 'worker-model', 'effort': 'low'}}])
        self.assertEqual(session['id'], 'child')
        self.assertEqual(session['parent_id'], 'root')
        self.assertEqual(session['selections'], [{'model': 'worker-model', 'effort': 'low'}])

    def test_inherited_completion_before_worker_creation_is_ignored(self):
        session = self.read([
            {'type': 'session_meta', 'payload': {'id': 'child', 'parent_thread_id': 'root', 'timestamp': '2026-10-07T12:00:00Z', 'source': {'subagent': {'thread_spawn': {'agent_path': '/root/review'}}}}},
            {'type': 'response_item', 'timestamp': '2026-10-07T11:59:00Z', 'payload': {'type': 'message', 'role': 'assistant', 'phase': 'final_answer', 'content': [{'text': 'Parent verdict'}]}},
            {'type': 'event_msg', 'timestamp': '2026-10-07T11:59:01Z', 'payload': {'type': 'task_complete'}}])
        self.assertEqual(completed_workers([session], 'root'), [])


class SessionActionTests(unittest.TestCase):
    def extract(self, sessions):
        from behavioral.traces import session_actions
        with tempfile.TemporaryDirectory() as temporary:
            paths = []
            for index, events in enumerate(sessions):
                path = Path(temporary) / f'{index}.jsonl'
                path.write_text('\n'.join(json.dumps(event) for event in events))
                paths.append(path)
            return session_actions(paths)

    def item(self, kind, call_id, **fields):
        return {'type': 'response_item', 'payload': dict(type=kind, call_id=call_id, **fields)}

    def test_nested_exec_and_failed_probe_survive_turns_and_match_by_id(self):
        nested = "text(await tools.exec_command({cmd: 'python3 -c probe'}))"
        failed = [{"type": "input_text", "text": '{"exit_code": 1, "output": "ValueError"}'}]
        actions = self.extract([[
            self.item('custom_tool_call', 'probe', name='functions.exec', input=nested),
            self.item('function_call', 'read', name='exec_command', arguments='{"cmd":"cat app.py"}'),
            self.item('function_call_output', 'read', output='def checkout(): pass'),
            self.item('custom_tool_call_output', 'probe', output=failed),
            {'type': 'event_msg', 'payload': {'type': 'task_started'}},
            self.item('function_call', 'pending', name='exec_command', arguments='{"cmd":"python3 test.py"}'),
        ]])
        self.assertEqual([action['call_id'] for action in actions], ['probe', 'read', 'pending'])
        self.assertEqual(actions[0]['command'], nested)
        self.assertEqual(actions[0]['outputs'], [failed])
        self.assertEqual(actions[0]['output'], '{"exit_code": 1, "output": "ValueError"}')
        self.assertEqual(actions[1]['output'], 'def checkout(): pass')
        self.assertEqual(actions[2]['outputs'], [])

    def test_outputs_remain_separate_per_session_and_keep_repeated_events(self):
        sessions = []
        for session_id, output in [('first', 'one'), ('second', 'two')]:
            sessions.append([
                {'type': 'session_meta', 'payload': {'id': session_id}},
                self.item('custom_tool_call', 'same', name='functions.exec', input='text(1)'),
                self.item('custom_tool_call_output', 'same', output=output),
                self.item('custom_tool_call_output', 'same', output='continued'),
                self.item('custom_tool_call_output', 'orphan', output='unmatched result'),
            ])
        actions = self.extract(sessions)
        self.assertEqual(actions[0]['output'], 'one\ncontinued')
        self.assertEqual(actions[2]['output'], 'two\ncontinued')
        self.assertEqual(actions[0]['session_id'], 'first')
        self.assertEqual(actions[2]['session_id'], 'second')
        self.assertTrue(actions[1]['unmatched_output'])
        self.assertEqual(actions[1]['output'], 'unmatched result')

    def test_text_flattening_excludes_nontext_without_discarding_raw_evidence(self):
        blocks = [{'type': 'image', 'data': 'binary-secret', 'text': 'not text'},
                  {'type': 'text', 'text': 'hello'}, {'type': 'input_text', 'text': 'world'},
                  {'type': 'text', 'text': {'unexpected': 'shape'}},
                  {'arbitrary': 'metadata'}, {'type': 'output_text', 'text': 'done'}]
        action = self.extract([[
            self.item('custom_tool_call', 'mixed', name='functions.exec', input='image(result)'),
            self.item('custom_tool_call_output', 'mixed', output=blocks),
        ]])[0]
        self.assertEqual(action['output'], 'hello\nworld\ndone')
        self.assertEqual(action['outputs'], [blocks])
