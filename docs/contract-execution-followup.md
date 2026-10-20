# Contract execution follow-up, 20 October 2026

Concrete contract guidance detected the selected valid-migration rejection in one paired observation and one separate follow-up. Current Check missed it in the paired observation. This supports a narrow Check change, not a claim of general review superiority.

| Observation | Current Check | Candidate Check |
| --- | --- | --- |
| Faulty fixture, paired | Target missed | Target detected by static trace |
| Calibrated fixture, paired | Reported unrestricted Python and Markdown additions | Reported rejection of a relevant JSON regression fixture |
| Faulty fixture, adaptive follow-up | Not run | Target detected with a mocked snapshot |

The candidate adds 63 words asking reviewers to construct a valid consumer operation from the documented contract and exercise the complete acceptance path. When execution is unavailable, it asks for a concrete trace through each gate and an explicit verification limit. The [normalized evidence](evidence/contract-execution-2026-10-20.json) publishes frozen hashes, relative guidance reads, aggregate judgments, and limits. Exact prompts, commands, responses, and probe outputs remain private.

Both candidate faulty runs identified a valid shared validation module rejected before behavioral checks. The first used static inspection. The follow-up called the real `assess()` entrypoint with a mocked snapshot. Both also identified missing malformed-v1 coverage and disclosed their verification limits. Neither ran a complete migration on disk. Target detection is assessed separately from successful execution and artifact preservation.

## Control findings and independent checks

The candidate control finding exposes a remaining automatic-assessment limit. A relevant JSON fixture used by a regression test is rejected because the calibrated gate permits only Python and Markdown additions. A separate on-disk reproduction first passed a valid migration through the calibrated assessor. Adding that fixture and its regression test left three tests passing, but the full assessor rejected the fixture before its behavioral probe. This corroborates the reported rejection, not candidate execution of the full migration.

The current-Check control reported the opposite boundary, unrestricted Python and Markdown additions. The independent reviewer confirmed a mismatch between the gate and the documented addition restriction. Restoring a narrow whitelist could reintroduce the selected valid-migration rejection. This finding needs semantic scope review, not automatic rejection of all new helpers.

The calibrated control is not universally clean. Clean specificity is unavailable. Its immutable artifact and historical provenance were not changed. Six existing historical regressions passed, including valid shared-module acceptance after repair and rejection of independent malformed-contract cases.

An independent reviewer assessed shuffled outputs A through D against their matching sources and probe records without the treatment mapping or candidate instruction. The reviewer confirmed the target detection, target miss, and supported control findings. This was partial blinding because responses can reveal procedural clues. The same independent reviewer assessed the adaptive repeat separately after the first four judgments.

## Method and decision

The initial batch ran faulty current, faulty candidate, calibrated candidate, and calibrated current, in that order. One adaptive candidate-only faulty repetition followed the first four observations and remains separately identified. Each run had a 240-second limit, ignored user configuration and rules, used an isolated profile, disabled delegation, and supplied no model or effort override. Codex CLI 0.160.0 recorded `gpt-6.1-sol` with null effort. This does not establish model inheritance from the parent conversation.

The existing `Case` adapter and `compare.run_trial` ran the unchanged historical request against frozen source copies. All five runs completed, returned the full supplied Check text in command output, and preserved project snapshots, copied bundles, and checked preference paths. Frozen input hashes and the evaluator identity remained unchanged during trials. Raw sessions remain private. No new evaluation runner was added.

Promote the exact tested instruction as a bounded improvement in contract review. Keep the residual automatic-assessment limits visible. This batch does not establish reliable detection across other repositories, a general false-positive rate, or a requirement to write files during read-only reviews.
