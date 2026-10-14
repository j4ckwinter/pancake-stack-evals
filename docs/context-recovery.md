# Context recovery comparison, 14 October 2026

Baseline and Pancake each recovered **20/20 required facts**, with no unsupported claims across four runs per arm. Both reached the scoring ceiling; this batch demonstrates no quality benefit from the Recap treatment.

Two cases share a small invoice repository with two deterministic commits and uncommitted producer, test and unrelated note changes. Only the handoff differs: one accurately describes the work; one incorrectly claims compatibility, green tests and publication. Each response was assessed for the accepted `total=` API and preserved archives, the dirty incompatible parameter, stale verification, unconfirmed publication, and compatibility repair followed by current verification. All eight responses preserved those distinctions.

| Arm | Supported facts | Unsupported claims | Median seconds | Median total tokens |
| --- | ---: | ---: | ---: | ---: |
| baseline | 20/20 | 0 | 32.367 | 61,174 |
| pancake | 20/20 | 0 | 35.594 | 64,526 |

Runtime/token medians describe this batch only. They are not causal estimates of speed, efficiency or monetary cost. Full per-run elapsed time, token/cache usage, tool and command counts, completion state, requested and actual model settings, normalized responses and complete assessments are in [the evidence](evidence/context-recovery-2026-10-14.json).

All runs used Codex CLI 0.160.0 with actual `gpt-6.1-sol` at `medium` effort. There were two repetitions per case and arm, with arm order alternated. Candidates inspected repository files and Git state: no application/test execution or delegation occurred. Workspace and preference preservation checks passed for every run. Inspection-based predictions were distinguished from executed checks, and missing publication receipts were treated as uncertainty.

The assessor first reviewed neutral labels A–H with responses, command observations and fixture state. Treatment/model prompts and label mapping were withheld until the completed assessment was saved. This is partial blinding: prose, handoff content and omitted-guidance counts could provide clues. One assessor supplied the semantic judgments without independent replication.

Source package revision: `1f888f972c2d3a726eba2bf8cf978df038fcc2ee` (clean). Evaluator revision: `13e1151009adab40a7fe2c70d986186cb1e118ca` (clean). The evidence preserves all recorded file hashes, both arm prompts, fixture content, public neutral-label mapping and every assessment. Its summary was generated using `tests.behavioral.context_recovery.summarize`, with process evidence separated from the boolean process map. Ordered run identity/case joins and response quotations were validated.

Baseline received the common catch-up request and scope restrictions. Pancake received the same prompt plus an explicit instruction to use the supplied Recap skill and applicable references. This tests recap recovery in two closely related synthetic cases on one host/model, not implementation, installation, publication or general long-term context recovery. More difficult cases and independent repetitions are needed to measure an improvement above this ceiling. Cache reuse and unmeasured service variation also limit interpretation of timing and token differences.

Temporary paths are normalized to `<project>`. Account metadata, session identifiers and raw rollouts are excluded. Assessment source pointers retain neutral labels; the JSON explains their mapping and reproduces the fixture content needed to interpret them.
