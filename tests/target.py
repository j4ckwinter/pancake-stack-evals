"""Explicit source checkout and retained legacy helper locations."""
import os
from pathlib import Path

EVALUATOR = Path(__file__).resolve().parents[1]
LEGACY = EVALUATOR / "fixtures/legacy-0.19.3"

def source_root():
    value = os.environ.get("PANCAKE_STACK_SOURCE")
    if not value:
        raise RuntimeError("Set PANCAKE_STACK_SOURCE to the Pancake Stack checkout under test")
    root = Path(value).resolve()
    if not (root / "plugin.json").is_file():
        raise RuntimeError("PANCAKE_STACK_SOURCE must contain plugin.json")
    return root
