#!/usr/bin/env python3
"""Store Pancake Stack preferences without modifying host settings."""

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

ROLES = ("implementation", "review", "research")
FIELDS = ("model", "reasoningEffort")
HOST_PATHS = {"codex": ("CODEX_HOME", ".codex"), "claude": ("CLAUDE_CONFIG_DIR", ".claude")}
PANELS = {"challengeReviewers": 2, "implementationReviewers": 3}
PANEL_COMMANDS = {
    "resolve-challenge": "challengeReviewers",
    "resolve-implementation-review": "implementationReviewers",
}


def empty_config():
    return {
        "schemaVersion": 1,
        "defaults": dict.fromkeys(FIELDS),
        "roles": {role: dict.fromkeys(FIELDS) for role in ROLES},
    }


def exact_keys(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{label} must contain exactly {', '.join(keys)}")


def validate(config):
    if not isinstance(config, dict):
        raise ValueError("preferences must be an object")
    version = config.get("schemaVersion")
    if type(version) is not int or version not in (1, 2, 3):
        raise ValueError("schemaVersion must be the integer 1, 2, or 3")
    keys = ("schemaVersion", "defaults", "roles")
    panels = tuple(name for name, minimum in PANELS.items() if version >= minimum)
    keys += panels
    exact_keys(config, keys, "preferences")
    exact_keys(config["roles"], ROLES, "roles")
    choices = [("defaults", config["defaults"])]
    choices.extend((role, config["roles"][role]) for role in ROLES)
    for panel in panels:
        reviewers = config[panel]
        if not isinstance(reviewers, list):
            raise ValueError(f"{panel} must be a list")
        choices.extend((f"{panel}[{index}]", choice)
                       for index, choice in enumerate(reviewers))
    for label, choice in choices:
        exact_keys(choice, FIELDS, label)
        for field, value in choice.items():
            if value is not None and (
                not isinstance(value, str) or not value.strip() or value != value.strip()
            ):
                raise ValueError(f"{label}.{field} must be null or a nonempty trimmed string")
    return config


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key}")
        result[key] = value
    return result


def parse(text):
    try:
        return validate(json.loads(text, object_pairs_hook=unique_object))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON at line {error.lineno}, column {error.colno}") from error


def read_config(path):
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return empty_config()
    return parse(content)


def save_config(path, config):
    read_config(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as output:
            temporary = Path(output.name)
            output.write(json.dumps(config, indent=2) + "\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def resolve(config, host_model, host_effort):
    return {
        role: {
            "model": config["roles"][role]["model"] or config["defaults"]["model"] or host_model,
            "reasoningEffort": host_effort,
        }
        for role in ROLES
    }


def resolve_panel(config, panel, host_model, host_effort):
    review = resolve(config, host_model, host_effort)["review"]
    reviewers = config.get(panel) or [dict.fromkeys(FIELDS)]
    return [
        {"model": choice["model"] or review["model"], "reasoningEffort": host_effort}
        for choice in reviewers
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=HOST_PATHS, default="codex",
                        help="select isolated Codex or Claude Code preferences")
    parser.add_argument("--config", type=Path, help="override the preference file path")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("show")
    commands.add_parser("save", help="validate and save the complete JSON object from stdin")
    for command in ("resolve", *PANEL_COMMANDS):
        resolver = commands.add_parser(command)
        resolver.add_argument("--host-model")
        resolver.add_argument("--host-reasoning-effort")
    args = parser.parse_args()
    try:
        variable, directory = HOST_PATHS[args.host]
        host_home = Path(os.environ.get(variable) or Path.home() / directory)
        path = args.config if args.config is not None else host_home / "pancake-stack/config.json"
        if args.command == "save":
            result = parse(sys.stdin.read())
            save_config(path, result)
        else:
            result = read_config(path)
            if args.command == "resolve" or args.command in PANEL_COMMANDS:
                host = empty_config()
                host["defaults"] = {
                    "model": args.host_model,
                    "reasoningEffort": args.host_reasoning_effort,
                }
                validate(host)
                choices = [result["defaults"], *result["roles"].values()]
                for panel in PANELS:
                    choices.extend(result.get(panel, []))
                if any(choice["reasoningEffort"] is not None for choice in choices):
                    print("preferences: Saved reasoning-effort values remain stored but are inactive. "
                          "Delegates inherit host effort unless the task explicitly requests an effort.",
                          file=sys.stderr)
                if args.command == "resolve":
                    result = resolve(result, args.host_model, args.host_reasoning_effort)
                else:
                    result = resolve_panel(result, PANEL_COMMANDS[args.command],
                                           args.host_model, args.host_reasoning_effort)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, UnicodeError) as error:
        print(f"preferences: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
