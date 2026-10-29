# Multi-model review routing

Three bounded source-skill trials exercised proposed Pancake Stack 0.21.19 guidance on 29 October 2026. They checked panel selection, completion, unsupported-model handling, and ordinary Check behavior. They did not compare review accuracy or cost across panel types.

## Inputs

The library base was `7ecd05753ff4c8d6bc25c9825e09c698d9ac4f57`, with the proposed review changes applied. The evaluator revision was `563502ee4c6caa43504446a6d13bdd450835d521`. The existing `tests/behavioral/review_comparison.py` prepared `config-bug` as `target-a` and `config-clean` as `target-b`. The faulty case replaces an explicit `None` check with a truthiness fallback. Both cases pass their existing tests.

The [metadata record](evidence/multi-model-review-2026-10-29.json) retains the skill hashes used by the first trial, session identities, raw-session hashes, model contexts, launch settings, and completion counts. Later trials used a clarification directing execution to resolve the panel from the shared task-choice rules. No model selection or review policy changed between trials.

Each lead received only its named target, the source skill and required references, the request below, and bounded read-only permissions. Safe `python3 -B` probes were allowed. Edits, installs, services, and external actions were prohibited. Leads were told not to inspect evaluator implementations, sibling targets, or assessment files.

## Requests and outcomes

| Trial | User request | Observed outcome |
| --- | --- | --- |
| Check panel | Review change.diff in target-a using multi-model review. Choose two distinct models supported by this host. Keep this read-only. Report supported findings and missing coverage. | The lead selected two models, launched fresh reviewers, obtained both verdicts, and reproduced the shared zero-limit regression. |
| Unsupported Challenge panel | Challenge change.diff in target-a using exactly these reviewer models: unavailable-review-model-a, unavailable-review-model-b. Do not substitute models. Keep this read-only and report supported findings and coverage. | No reviewers launched. Direct review found the regression. Both unsupported entries remained explicit coverage gaps. |
| Ordinary Check | Review change.diff in target-b for bugs and regressions. Keep this read-only. | No reviewers launched. Existing tests and focused probes passed. The lead reported no actionable findings. |

The positive panel used `/root/check_panel_trial/review_sol` and `/root/check_panel_trial/review_astra`. Both spawn calls used `fork_turns="none"`, omitted effort, and requested `gpt-6.1-sol` and `gpt-6-astra`, respectively. Both returned identity-bearing completed verdicts. No child spawned another panel.

The live lead correctly reported that spawn responses exposed agent identities but not runtime model IDs. Posthoc inspection of each child's `turn_context` confirmed `gpt-6.1-sol` at low effort and `gpt-6-astra` at medium effort. This establishes distinct runtime models for this trial. Omitted effort left each model's setting to the host. It does not establish provider diversity.

Both reviewers found that zero selects jobs instead of disabling selection. The lead reproduced the result independently. The unsupported-panel lead also reproduced it. The clean control preserved omitted, `None`, zero, explicit, and oversized limits. Before-and-after fixture snapshots matched.

## Limits

These were three source-skill trials in one Codex environment, with one observation per request. They were not installed-plugin trials or authenticated Claude workflow tests. There was no same-model comparison, no repeated sampling, and no accuracy or cost advantage measurement.

Spawn settings and runtime model contexts are visible in retained sessions. Reviewer brief bodies are encrypted, so identical neutral briefs cannot be independently audited from those records. The lead reported using identical neutral briefs. Raw sessions remain local; the published record contains selected metadata only.

The full package/evaluator suite completed 197 tests with one optional sandbox test skipped. Generic skill-creator validation could not run because the host Python lacked PyYAML. The repository-specific validator checked JSON, marketplace resolution, skill metadata, and references. No global preferences or installation settings changed.
