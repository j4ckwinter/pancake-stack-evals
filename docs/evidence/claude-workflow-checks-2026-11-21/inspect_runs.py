import json
import os
import sys
from collections import Counter
from pathlib import Path

RAW = Path(os.environ["PSTACK_RAW"])


def records(path):
    for line in path.read_text().splitlines():
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def usage_and_models(path):
    models, tokens = Counter(), Counter()
    seen = set()
    for r in records(path):
        if r.get("type") != "assistant":
            continue
        m = r.get("message", {})
        if m.get("model"):
            models[m["model"]] += 1
        mid = m.get("id")
        if mid in seen:
            continue
        seen.add(mid)
        for k, v in (m.get("usage") or {}).items():
            if isinstance(v, int):
                tokens[k] += v
    return dict(models), dict(tokens)


def launches(path):
    out = []
    for r in records(path):
        if r.get("type") != "assistant":
            continue
        for c in r.get("message", {}).get("content", []) or []:
            if c.get("type") == "tool_use" and c.get("name") in ("Agent", "Task"):
                i = c.get("input", {})
                out.append({k: i.get(k) for k in ("subagent_type", "model", "effort", "description")})
    return out


def bash_commands(path):
    out = []
    for r in records(path):
        if r.get("type") != "assistant":
            continue
        for c in r.get("message", {}).get("content", []) or []:
            if c.get("type") == "tool_use" and c.get("name") in ("Bash", "Edit", "Write"):
                i = c.get("input", {})
                out.append((c["name"], (i.get("command") or i.get("file_path") or "")[:160]))
    return out


def inspect(run_dir):
    s = json.loads((run_dir / "summary.json").read_text())
    main = run_dir / "session.jsonl"
    info = {"id": s["id"], "elapsed_s": s["elapsed_s"], "cost_usd": s["cost_usd"],
            "changed": s["changed_files"], "head_changed": s["head_changed"]}
    if main.exists():
        info["lead_models"], info["lead_tokens"] = usage_and_models(main)
        info["launches"] = launches(main)
    subs = []
    for f in sorted((run_dir / "session").rglob("*.jsonl")) if (run_dir / "session").exists() else []:
        meta = f.with_suffix(".meta.json")
        models, tokens = usage_and_models(f)
        subs.append({"file": f.name, "models": models, "tokens": tokens,
                     "meta": json.loads(meta.read_text()) if meta.exists() else None})
    info["subagents"] = subs
    return info


if __name__ == "__main__":
    prefix = sys.argv[1] if len(sys.argv) > 1 else ""
    for d in sorted(RAW.iterdir()):
        if d.name.startswith(prefix) and (d / "summary.json").exists():
            print(json.dumps(inspect(d), indent=None, default=str))
