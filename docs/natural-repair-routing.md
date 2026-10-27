# Natural repair routing, 27 October 2026

The conditional parallel-work links proposed for Fix and TDD were rejected. Both changed entrypoints returned the complete reference for the importer repair, but neither used implementation delegates. All baseline and changed runs produced correct artifacts. This sample supplies no demonstrated benefit that justifies the added reading requirement.

The evaluator now supports natural repair requests through Fix, TDD, and Pancake. The importer request describes broken CSV imports, JSON envelopes, and account totals, then specifies the required contract and regression coverage. The small control asks `total` to ignore `None` while preserving signed sums and empty input. Both permit scoped implementation workers without requesting them. The selected skill determines the workflow, including TDD ordering. This removes the explicit delegation request and prohibition used in the earlier [coordination trials](coordination-gaps.md).

| Guidance | Case | Artifact and scope | Implementation children | Completed review children | Complete lead parallel-work returns |
| --- | --- | --- | ---: | ---: | ---: |
| Baseline Fix | Importer | Pass | 0 | 1 | 0 |
| Baseline TDD | Importer | Pass | 0 | 1 | 0 |
| Baseline Pancake | Importer | Pass | 0 | 1 | 0 |
| Changed Fix | Importer | Pass | 0 | 1 | 1 |
| Changed TDD | Importer | Pass | 0 | 1 | 1 |
| Baseline Fix | Small control | Pass | 0 | 0 | 0 |
| Baseline TDD | Small control | Pass | 0 | 0 | 0 |
| Baseline Pancake | Small control | Pass | 0 | 0 | 0 |
| Changed Fix | Small control | Pass | 0 | 0 | 0 |
| Changed TDD | Small control | Pass | 0 | 0 | 0 |

The unchanged Pancake importer also remained direct. These observations do not establish a missing delegation default in Fix or TDD. A worker count alone would not establish better implementation, and these small fixtures do not settle which larger tasks benefit from decomposition.

The artifact oracle reuses the existing composed CLI and adapter probes. It covers signed amounts, empty inputs, old payloads, account normalization, malformed input, atomic failure, and preserved data. Existing importer mutation controls discriminate broken adapters and CLI behavior. New small-control checks accept a repaired implementation and reject unchanged, constant-zero, and absolute-value sums. New runner regressions exercise all three entrypoints. Independent harness review corrected effective-entrypoint reporting for the existing Poteto arm before model execution. Sixteen focused checks passed with one existing opt-in sandbox smoke skipped.

A fresh assessor reviewed six baseline artifacts and ordered visible actions under shuffled labels. It supported all artifact results, observed failing regressions before production edits, and found completed independent review for every importer. Only reviewers ran as children. Some initial failure output was truncated, but visible failures still established the ordering. A missing irrelevant trailing CSV column remained an ambiguity outside the scored contract. The artifact oracle supplies scope preservation separately from the transcript audit.

A separate fresh assessor supported all four changed-run artifacts, scope results, failing-regression ordering, and completed importer reviews. It found no child implementation. Changed TDD rejected duplicate irrelevant CSV headers, while changed Fix accepted them. As in the earlier coordination trials, this remains an unspecified and unscored residual concern. The pass criteria were not changed after execution. The changed Fix lead resumed its reviewer after adjusting handling of duplicate irrelevant CSV headers. The retained child trace covers the final follow-up inspection and executed suite, but does not retain every action from its initial review. Lead messages and final child completion remain visible. The evidence does not infer missing review actions from the final verdict.

Complete-reference counts use the existing exact Markdown body matcher against returned tool output. Filename mentions and partial bodies do not count. The changed importer leads each received the complete parallel-work reference once. Neither small control received it. This establishes targeted delivery, not attention or useful application.

All ten trials used frozen source bundles, fresh isolated profiles, inherited CLI defaults, and a 300-second limit. All completed within the bound with final responses and unchanged inputs, bundles, and preferences. Observed models were `gpt-6.1-sol`; lead effort was unreported and reviewer effort was `low`. Package checks did not overlap live trials. An initial preflight failed before model execution because a raw worktree lacked `snapshot-origin.json`. The runner then used frozen skills and documentation with recorded origin metadata. That attempt is retained.

The [normalized evidence](evidence/natural-repair-routing-2026-10-27.json) records source and evaluator revisions, dirty-state hashes, outcomes, and complete-reference counts. The [rejected patch](evidence/natural-routing-candidate.patch) preserves the exact proposal. All attempts, raw sessions, action linkage, and assessor packets remain private. Guidance bodies and identities were removed from assessment packets where possible, but structure and behavior can still reveal treatment. Assignment ciphertext limits the briefing audit. These are single observations per entrypoint and case, with baseline batches followed by changed batches. No latency, model-diversity, installation, Claude parity, or general superiority claim follows.
