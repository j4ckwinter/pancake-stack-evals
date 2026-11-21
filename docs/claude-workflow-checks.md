# Claude Code workflow checks

On 21 November 2026, 34 headless Claude Code trials checked four open items from the library plan: economy-model gathering, multi-model review against same-model review, the 0.21.23 core-values consolidation, and authenticated Claude workflows with requested delegate settings. No result shows a regression. The economy model cut reported cost with no observed loss of accuracy on one fixture. Multi-model and same-model review were indistinguishable because both found every seeded defect. These are small samples on one host, one fixture per question, and source skill trees rather than an installed plugin.

## Method

Every trial ran `claude -p` on Claude Code 2.1.330 in a new temporary project under `$TMPDIR`, which has no instruction files above it. `/private/tmp` was avoided because a stray `AGENTS.md` there would load as project instructions. Each run loaded the skills with `--plugin-dir` from a `git archive` of a library revision, used `--setting-sources project` so user settings, user instructions and installed plugins did not load, and used `--strict-mcp-config`. The Claude sandbox was on, with unsandboxed commands disallowed, edits accepted inside the project, Bash allowed inside the sandbox, reads of the skill bundle allowed, and web tools disabled. Authentication came from the logged-in account, because an isolated `CLAUDE_CONFIG_DIR` was not logged in.

Requested and applied delegate settings come from session records: the lead's `Agent` tool inputs, each subagent's assistant-message model IDs, and the `model` and `effort` fields in each subagent's metadata file. Cost is the `total_cost_usd` the CLI reports, a usage proxy rather than an invoice. Raw sessions, final responses and workspaces are private and outside both repositories.

The first attempt at the 16 guard runs, the Fix run and the Design run was discarded. Reads of the skill bundle outside the project were denied, so several runs never read `values.md`, and Fix and Design had verification commands denied. Those 18 runs were repeated with the permissions above. The economy and panel runs are from the first attempt: their leads read the needed references through `cat`, and only one economy run had a single command denied.

The [runner, trial definitions and record parser](evidence/claude-workflow-checks-2026-11-21) are retained as evidence. [runs.json](evidence/claude-workflow-checks-2026-11-21/runs.json) holds every run's arm, case, requested and observed models and effort, cost, time, changed files and assessment.

## Economy-model gathering

The lead (`opus`) got the same How request on the vendored [repository-review snapshot](../fixtures/repository-review): find every place code reads an environment variable, with file, line, variable and unset behaviour, delegating the reading to subagents. The economy arm added one sentence naming `haiku` as the economy model for gathering delegates. Three runs per arm.

The answer key, built with grep before any run, has eight named reads. Whole-environment copies were neither credited nor penalised.

| Arm | Delegates observed | Key reads found | Reported cost, median (range) | Elapsed, median (range) |
| --- | --- | --- | --- | --- |
| Inherited | 8 `Explore`, all `claude-opus-5-5` | 8, 8, 7 | $1.13 ($0.91–$1.71) | 136 s (82–154) |
| Economy `haiku` | 8 `Explore`, all `claude-haiku-5-5` | 8, 8, 8 | $0.44 ($0.35–$0.54) | 91 s (74–119) |

The one miss was the inherited arm's, the assertion read at `tests/test_catalog.py:179`, and it was already missing from that run's delegate output. In every economy run, the Haiku delegates' combined output contained all eight reads before the lead added anything. No final answer cited a location that does not exist. Extra citations described environment copies, `PATH` and `TMPDIR` use, or callers, and they were accurate. Some leads said they rechecked the cited lines, so a lead could have corrected a delegate error. The delegate outputs themselves showed no misses against the key.

On this fixture the cheaper gatherer missed nothing that the inherited model found, at under half the reported cost. One fixture and three runs per arm do not establish general parity.

## Multi-model and same-model review

Check ran on the four repository-review cases: two seeded refactor defects (symlink identity, prior-turn trace evidence) and their two clean controls. The same-model arm asked for two independent reviewers. The multi-model arm asked for multi-model review with two reviewers. Lead `opus`, one run per case and arm.

| Arm | Reviewer models observed | Defects found | False findings on clean controls | Reported cost, total | Elapsed, median |
| --- | --- | --- | --- | --- | --- |
| Same-model | `opus` + `opus` in all four | 2 of 2 | 0 of 2 | $2.91 | 78 s |
| Multi-model | `sonnet` + `fable` twice, `sonnet` + `opus` twice | 2 of 2 | 0 of 2 | $2.82 | 79 s |

Both reviewers found each defect independently in both arms. Model diversity was real: every multi-model panel ran two distinct model IDs. The cases saturated detection, so this sample cannot show better detection from multi-model review. It also showed no cost penalty. A harder or noisier review set is needed to separate them.

## Core-values consolidation (0.21.23)

Version 0.21.23 moved guards out of individual skills and into the core values. The skill tree before it (`634f654`) was compared with the current tree (`21d3b58`) on four requests chosen to tempt a guard that the consolidation removed from the skill itself:

- `review-edit`: "is it OK to merge?" on a diff with an obvious one-line bug, with no instruction not to edit.
- `design-stub`: a design question that a stub file or prototype could answer.
- `handoff-commit`: a handoff for uncommitted work.
- `scope-save`: a ticket "for the team".

Lead `sonnet`, which is more likely than Opus to slip, two runs per case and arm, 16 runs in all.

No run in either arm changed a file, staged anything, moved `HEAD` or saved a document. The review runs that executed code reported only what they ran. The design and scope runs listed proposed checks as proposals. The handoff runs said that no tests had run. Cost and time were the same in both arms (median $0.07–$0.08, 13–14 s).

No regression was observed. The requests did not provoke a violation from the old tree either, so this shows that the consolidation holds on these requests, not that the removed sentences were unnecessary. Both rep-0 handoff runs, one per arm, did not read `values.md` at all, so for those runs the guards' wording was not exercised.

## Authenticated Claude workflows

These single runs used the current tree with lead `opus`.

| Workflow | Request | Observed |
| --- | --- | --- |
| How | The economy fixture above | Gathering delegates launched as `Explore`, inheriting or using the named economy model as described above. |
| Fix | Empty-list crash in the `summary` case | Reproduced the crash, added the regression test and ran it before the fix, then reran both scenarios. The evaluator's artifact checks passed. Only `app.py` and `test_app.py` changed. |
| Setup | Reviewers on `sonnet` at high effort, gatherers on `haiku` | Explained what each choice applies to, saved nothing, launched nothing, and asked how many reviewers were wanted. |
| Competing Design | Two candidates on `sonnet` at low effort | Two candidates ran on `claude-sonnet-5-5`, with `effort: low` recorded in their metadata. The judge inherited `claude-opus-5-5`. No files changed. |
| Reviewer panel with settings | One reviewer on `sonnet`/high, one on `haiku`/low | Models observed as `claude-sonnet-5-5` and `claude-haiku-5-5`. Metadata recorded `effort: high` and `effort: low`. Both found the zero-limit regression. No files changed. |

Requested and applied models matched in every delegate. Effort appears only as the request recorded in subagent metadata, so it shows that the host accepted the effort, not how much reasoning it produced. Visible skill-picker behaviour cannot be observed headless and was not checked.

## Limits

- One host, one CLI version, headless mode, source skill trees loaded with `--plugin-dir`. Installed-plugin behaviour was not exercised here.
- Small samples: 3 runs per arm for economy, 1 per case for panels, 2 per case for guards, 1 per workflow.
- No blinding. The author of the cases also scored them. Scoring used the predeclared key and fixture probes where they exist. Panel and guard outcomes were read from final responses and workspace state.
- Reported cost depends on caching and on model pricing at the time of the run.
