# Three-arm review comparison, 12 October 2026

All twelve bounded runs completed. Each arm detected both seeded defects and reported no unsupported actionable finding on its two clean controls. The independent assessor found no unnecessary-work episode that met the predeclared rubric. This small sample does not establish general review quality or a minimum-work claim.

## Method

The new `review-comparison` suite pairs a zero-valued configuration contract and deferred file consumption with correct changes to the same code. All four projects pass their local tests. Independent evaluator probes establish the two defects and check the clean controls. The historical Check-wording experiment remains unchanged.

One repetition ran sequentially across baseline, source Pancake, and the local Codex adaptation of Poteto. Every arm received the same organic read-only request, delegation permission, model, effort, and 240-second limit. Arm order rotated across cases, but one repetition does not balance positions within a case. Baseline received no skill bundle. Pancake and Poteto started at their workflow entrypoints.

The [evidence record](evidence/review-comparison-2026-10-12.json) retains exact source and evaluator revisions, dirty states, input hashes, Poteto inventory, prompts and invocations, observed settings, per-run results, adjudications, and sanitized inspection packets. Source was `5653457`, evaluator was `f3a3049`, and both were clean. All candidate parent and worker records reported `gpt-6.1-sol` with medium effort on Codex CLI 0.160.0. Every run preserved its workspace and reported unchanged inputs. All temporary profiles and credential copies were removed. Raw records remain private at `/tmp/pancake-release-20261012/review-pilot`.

A separate assessor requested as `gpt-5.6-sol` inspected neutral-labeled final outputs and command/result excerpts against the predeclared rubric. Treatment identities were withheld until adjudication finished. Guidance names and private paths were normalized, and long guidance-read bodies were omitted. Prose and worker topology could still reveal treatment. The lead read all final outputs and corroborated omitted diff-read results against the full retained records. This is partial blinding, not complete blinding.

## Outcomes

Each arm has four observations, including two defect cases and two clean controls. Tokens sum parent and worker input, including cached input, plus output. They measure usage, not money. Full ranges and individual results remain in the evidence.

| Guidance | Completed | Defects detected | False findings | Noisy clean controls | Unnecessary-work episodes | Median seconds | Median total tokens | Completed workers per run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 4/4 | 2/2 | 0 | 0/2 | 0 | 38.3 | 83,328 | 0, 0, 0, 0 |
| pancake | 4/4 | 2/2 | 0 | 0/2 | 0 | 39.8 | 86,680 | 0, 0, 0, 0 |
| poteto | 4/4 | 2/2 | 0 | 0/2 | 0 | 87.9 | 394,398 | 1, 1, 1, 1 |

Poteto completed one review worker in each run. Baseline and Pancake stayed direct. The assessor did not count those workers as unnecessary delegation. Completed worker verdicts are observable, but encrypted briefs and missing explicit context-isolation arguments do not establish neutral independent review. Several runs repaired failed heredoc commands before completing their checks. Those retries resolved failed execution, so the rubric did not count them as redundant verification. The retained inspection packets show the failed and successful operations.

## Decision and limits

Keep the current workflow instructions. This pilot broadens coverage beyond invoice migrations and exercises false-positive and unnecessary-work accounting, but accuracy still saturates on simple cases. Pancake and baseline had similar observed median times; this is not a repeatability or equivalence estimate. Poteto used more time and tokens without improving measured detection in these cases. Neither result establishes general superiority.

Reviewer mechanics are already shared, and Design references already load conditionally. Further text extraction or delegation rules need demonstrated benefit. A prior Check compression did not reduce measured overhead. The next useful evaluation should use representative repository changes and repeated, balanced runs, not add instructions solely to reduce word count.

Authenticated Claude workflows remain deferred. No installation trial, visible picker behavior, provider diversity, or production savings is claimed. Reproduce this procedure through [the behavioral evaluation guide](behavioral-evaluation.md#three-arm-review-comparison).
