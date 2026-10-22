"""Read only explicitly supplied trial session records; never discover user history."""
import json
from datetime import datetime


def summarize_session(path, *, all_actions=False):
    result = {"id": None, "parent_id": None, "agent_path": None, "workspace": None,
              "selections": [], "calls": [], "outputs": [],
              "verdicts": [], "completed": False}
    created_at = None
    for line in path.read_text().splitlines():
        event = json.loads(line)
        payload = event.get("payload", {})
        kind = event.get("type")
        timestamp = event.get("timestamp")
        if created_at and timestamp and datetime.fromisoformat(timestamp.replace("Z", "+00:00")) < created_at:
            continue
        if kind == "session_meta" and result["id"] is None:
            if payload.get("timestamp"):
                created_at = datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
            result["id"] = payload.get("id")
            result["parent_id"] = payload.get("parent_thread_id")
            result["workspace"] = payload.get("cwd")
            source = payload.get("source")
            if isinstance(source, dict):
                spawn = source.get("subagent", {}).get("thread_spawn", {})
                result["agent_path"] = spawn.get("agent_path")
        elif kind == "turn_context":
            result["selections"].append({"model": payload.get("model"),
                                         "effort": payload.get("effort")})
        elif kind == "response_item":
            if payload.get("type") == "function_call":
                args = json.loads(payload.get("arguments", "{}"))
                # Task text can be encrypted and is unnecessary to establish selection.
                args.pop("message", None)
                result["calls"].append({"id": payload.get("call_id"),
                                         "name": payload.get("name"),
                                         "arguments": args})
            elif payload.get("type") == "custom_tool_call":
                result["calls"].append({"id": payload.get("call_id"),
                                         "name": payload.get("name"),
                                         "arguments": {"input": payload.get("input")}})
            elif payload.get("type") in ("function_call_output", "custom_tool_call_output"):
                result["outputs"].append({"id": payload.get("call_id"),
                                           "output": payload.get("output")})
            elif payload.get("type") == "message" and payload.get("phase") == "final_answer" and payload.get("role") == "assistant":
                result["verdicts"].append("".join(part.get("text", "") for part in payload.get("content", [])))
        elif kind == "event_msg" and payload.get("type") == "task_started":
            result["completed"] = False
            result["verdicts"] = []
            result["selections"] = []
            if not all_actions:
                result["calls"] = []
                result["outputs"] = []
        elif kind == "event_msg" and payload.get("type") == "task_complete":
            result["completed"] = True
    return result


def completed_workers(sessions, parent_id):
    """Require a linked worker, a completed turn, and its own nonempty verdict."""
    return [session for session in sessions
            if session["parent_id"] == parent_id and session["id"]
            and session["agent_path"] and session["completed"]
            and any(session["verdicts"])]


def output_text(value):
    """Expose text blocks without evaluating nested JSON or including binary payloads."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(text for item in value if (text := output_text(item)))
    if isinstance(value, dict) and value.get("type") in ("text", "input_text", "output_text"):
        text = value.get("text")
        return text if isinstance(text, str) else ""
    return ""


def session_actions(paths):
    """Canonical call evidence from explicitly supplied raw session paths, including failures.

    Nested exec JavaScript stays intact. Outputs match by call ID within a session;
    multiple output events and calls without outputs remain visible. No CLI event
    stream or guessed nested-command parser is used.
    """
    actions = []
    for path in sorted(paths):
        session = summarize_session(path, all_actions=True)
        outputs = {}
        for item in session["outputs"]:
            outputs.setdefault(item["id"], []).append(item["output"])
        seen = set()
        for call in session["calls"]:
            call_id = call["id"]
            matched = outputs.get(call_id, []) if call_id is not None else []
            seen.add(call_id)
            args = call["arguments"]
            command = next((args[key] for key in ("input", "cmd", "command")
                            if isinstance(args.get(key), str)), json.dumps(args))
            actions.append(dict(session_id=session["id"], call_id=call_id,
                                name=call["name"], arguments=args, command=command,
                                outputs=matched, output=output_text(matched)))
        for call_id, unmatched in outputs.items():
            if call_id is None or call_id not in seen:
                actions.append(dict(session_id=session["id"], call_id=call_id,
                                    name=None, arguments=None, command=None,
                                    outputs=unmatched, output=output_text(unmatched),
                                    unmatched_output=True))
    return actions
