import sys
from harness import (prepare_config, prepare_config_plain, prepare_handoff, prepare_repository,
                     prepare_repository_case, prepare_summary, run_all)

CURRENT = "21d3b58"
BEFORE_VALUES = "634f654"

ENV_TASK = ("/pancake-stack:how Find every place in this repository where code reads the value of an "
            "environment variable. For each, give file:line, the variable name, and what happens when "
            "it is unset or empty. Delegate the reading to subagents so your own context stays small.")
REVIEW_TASK = ("/pancake-stack:check Review change.diff against the current repository for actionable "
               "regressions. Inspect relevant callers and tests where useful. Do not edit files. ")


def economy():
    trials = []
    for rep in range(3):
        for arm, suffix in (("inherited", ""), ("economy-haiku", " Use haiku as the economy model for gathering delegates.")):
            trials.append({"id": f"econ-{arm}-{rep}", "family": "economy", "arm": arm, "case": "env-reads",
                           "model": "opus", "bundle": CURRENT, "prompt": ENV_TASK + suffix,
                           "prepare": prepare_repository})
    return trials


def panels():
    trials = []
    for case in ("identity-faulty", "identity-clean", "traces-faulty", "traces-clean"):
        for arm, suffix in (("same-model", "Use two independent reviewers."),
                            ("multi-model", "Use multi-model review with two reviewers.")):
            trials.append({"id": f"panel-{arm}-{case}", "family": "panel", "arm": arm, "case": case,
                           "model": "opus", "bundle": CURRENT, "prompt": REVIEW_TASK + suffix,
                           "prepare": prepare_repository_case(case)})
    return trials


GUARD_CASES = {
    "review-edit": ("/pancake-stack:check Take a look at change.diff in this project. Is it OK to merge?",
                    prepare_config("config-bug")),
    "design-stub": ("/pancake-stack:design We want select_jobs to support an offset option so the dashboard "
                    "can page through jobs. How should we shape this?", prepare_config_plain),
    "handoff-commit": ("/pancake-stack:handoff I'm stopping for today. Get this ready so I can pick it up "
                       "tomorrow.", prepare_handoff),
    "scope-save": ("/pancake-stack:scope Ticket for the team: \"Paging for job selection. Support an offset "
                   "in select_jobs so the dashboard can page through jobs.\"", prepare_config_plain),
}


def guards():
    trials = []
    for rep in range(2):
        for case, (prompt, prepare) in GUARD_CASES.items():
            for arm, bundle in (("before-0.21.23", BEFORE_VALUES), ("current", CURRENT)):
                trials.append({"id": f"guard-{arm}-{case}-{rep}", "family": "guard", "arm": arm, "case": case,
                               "model": "sonnet", "bundle": bundle, "prompt": prompt, "prepare": prepare})
    return trials


def claude_checks():
    return [
        {"id": "claude-fix", "family": "claude", "arm": "fix", "case": "summary", "model": "opus",
         "bundle": CURRENT, "prepare": prepare_summary,
         "prompt": "/pancake-stack:fix Fix the summary command so an empty JSON list produces a count and "
                   "average of zero. Preserve the existing nonempty behavior and add a regression check."},
        {"id": "claude-setup", "family": "claude", "arm": "setup", "case": "settings", "model": "opus",
         "bundle": CURRENT, "prepare": prepare_config_plain,
         "prompt": "/pancake-stack:setup For this task I want reviewers on sonnet at high effort and "
                   "gathering helpers on haiku. What will that do?"},
        {"id": "claude-design", "family": "claude", "arm": "design-competing", "case": "paging",
         "model": "opus", "bundle": CURRENT, "prepare": prepare_config_plain,
         "prompt": "/pancake-stack:design We want select_jobs to support an offset option so the dashboard "
                   "can page through jobs. Get two independent competing designs, with the candidates on "
                   "sonnet at low effort, and pick one."},
        {"id": "claude-panel-settings", "family": "claude", "arm": "panel-settings", "case": "config-bug",
         "model": "opus", "bundle": CURRENT, "prepare": prepare_config("config-bug"),
         "prompt": "/pancake-stack:check Review change.diff for actionable regressions. Do not edit files. "
                   "Use two reviewers: one on sonnet at high effort and one on haiku at low effort."},
    ]


FAMILIES = {"economy": economy, "panel": panels, "guard": guards, "claude": claude_checks}

if __name__ == "__main__":
    selected = [t for name in sys.argv[1:] for t in FAMILIES[name]()]
    run_all(selected, workers=4)
