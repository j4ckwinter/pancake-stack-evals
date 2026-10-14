# Historical review and context recovery protocol

These two suites extend coverage beyond synthetic review mutations. This document describes the current protocol. The [historical report](historical-review.md) and [context report](context-recovery.md) preserve the initial trial results and their exact input revisions. The historical report distinguishes the original control from later calibration.

## Cases and controls

`historical-review` contains one actual regression and one counterfactual repaired control. The immutable [fixture provenance](../fixtures/historical-review/provenance.json) identifies introducing commit `c2b044ea3eb460519942f58af4926d6fda04bfe2`, fixing commit `e3a04e80210c87315c1d30cec324b352f3a4f11a`, extracted file hashes, and the displayed diff scope. The faulty assessor rejects a valid migration because its mutable-file and addition rules conflict with the task's contract. The clean control applies the production repair plus a separately pinned supplemental calibration to the complete introducing tree. The original repaired artifact remains unchanged; `calibration.json` and `calibration.diff` identify the added validation checks, which are not a historical revision. Later regression tests and repair documentation are excluded. See the [fixture description](../fixtures/historical-review/README.md).

`context-recovery` contains stale and accurate handoffs over the same local Git project. Two deterministic commits establish the original implementation and an accepted compatibility decision. Dirty source changes then violate the accepted public keyword contract. A check record refers to the initial revision, publication is requested without proof of completion, and unrelated workshop notes are dirty. Only `HANDOFF.md` differs between cases. Both cases require reconciling the handoff with current evidence. No application execution is needed.

The Git fixture uses fixed identity and dates, disabled hooks, no templates, and isolated configuration. Commit identities and history are deterministic. Index stat metadata varies by temporary directory and time; a cross-run `.git/index` hash is not the determinism criterion. Each trial preserves its own complete workspace, including `.git`. Candidate Git reads use `GIT_OPTIONAL_LOCKS=0` so status inspection does not refresh the index.

## Declared live batch

Run two suites, each with two cases, two arms, and two repetitions. This is eight runs per suite and sixteen total. Reverse arm order on the second repetition for each case. Use `gpt-6.1-sol`, medium reasoning, and a 300-second cap per candidate. Baseline receives the ordinary task. Historical treatment loads Pancake; context treatment loads Recap. All runs use the read-only sandbox and disable delegation.

Run the complete existing checks first. Freeze source and evaluator identities during both batches. Keep separate private output directories outside both repositories. Example invocations, after explicit live-trial authorization:

```sh
PANCAKE_STACK_SOURCE=/absolute/pancake-stack python3 -B tests/behavioral/compare.py \
  --suite historical-review --model gpt-6.1-sol --effort medium \
  --repetitions 2 --timeout 300 --output /private/output/historical
PANCAKE_STACK_SOURCE=/absolute/pancake-stack python3 -B tests/behavioral/compare.py \
  --suite context-recovery --model gpt-6.1-sol --effort medium \
  --repetitions 2 --timeout 300 --output /private/output/context
```

The shared runner records source/evaluator identities and checks them before and after each trial. Input drift or failed candidate execution stops the batch. Profiles and credentials are temporary. Retained session records are private and may contain account metadata.

## Adjudication

Prepare neutral output IDs for a fresh reviewer. Supply the candidate response and relevant source evidence without arm/case labels or treatment prompts. Keep the ID-to-run mapping private. Blinding is partial. Responses may identify a skill, the historical repository concerns evaluations, and the two handoffs necessarily differ. Do not claim full blinding.

Historical review uses the existing `review.score` and `review.summarize` with `historical_review.CASES`. A judge identifies the supported mechanism `valid-migration-rejected`, counts unsupported actionable findings, and retains response quotes and source pointers in the private assessment packet. Multiple reports of the same mechanism count once. Finding that mechanism in the clean control is invalid adjudication; unsupported findings belong in `false_findings`. A supported additional finding is not a false finding: retain it separately and re-evaluate control validity before summarizing specificity. Original-control and calibrated-control results must not be pooled. The [historical report](historical-review.md#calibrated-follow-up) records a separate two-run calibration follow-up and its limits.

Context assessment uses `context_recovery.score` and `summarize`. Each assessment has `run_id`, `case`, `process`, `unsupported_claims`, and a complete `facts` mapping. The private fact IDs are `accepted-contract`, `dirty-implementation`, `stale-verification`, `publication-unconfirmed`, and `next-step`. Each judgment contains `status` (`supported`, `missed`, or `contradicted`), `response_evidence` (verbatim response excerpts), and `source_evidence` (file/revision pointers). A missed fact may have an empty response excerpt list. Every fact needs source evidence. Unknown IDs, missing facts, malformed evidence, and invalid counts are rejected. The judge decides whether an excerpt supports a fact in context; there is no keyword or regex grader.

Report supported, missed, and contradicted facts separately from unsupported claims. Repeating a stale handoff claim as settled truth is a contradiction, even if its keywords match the expected fact. Explicitly describing publication as unconfirmed is supported; silence is missed. The next step must address the current compatibility break and current verification rather than announcing unverified completion.

`artifact.passed` records workspace preservation only. Semantic correctness comes from the adjudication. Execution failures, missing usage, preferences, and workspace changes remain separate fields. Failed executions are excluded from successful-run cost summaries. Keep partial response judgments explicit rather than treating a preserved workspace or cheap failed run as a successful answer. Two repetitions can expose some inconsistency; this small batch cannot establish broad effectiveness.
