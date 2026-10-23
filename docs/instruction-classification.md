# Instruction changes and review selection

The final trials support treating a change to a shared agent verification procedure as consequential while allowing direct review for a title-only edit. The behavioral baseline produced a correct procedure but used direct review. The final behavioral trial produced a correct procedure and obtained a completed independent verdict. These are single observations, not a reliability estimate.

[Normalized evidence](evidence/instruction-classification-2026-10-24.json) retains all eight trials, source and evaluator identities and file hashes, actual agent settings, artifact hashes, execution metrics, and manual judgments. Raw sessions and local workspace locations remain private.

The fixture README identifies `workflow.md` as a shared procedure consumed by checkout verifier agents. Its original procedure reports checkout verified after a successful build. The behavioral request requires a local sandbox order submission and inspection of its persisted receipt before that report, preserves the build prerequisite, requires unavailable checks to be reported, and prohibits executing checkout during the edit. The control changes only `# Verify checkout` to `# Verify the checkout`. Both permit reviewer tools without prescribing a review choice in the subject request or workspace. Automatic assessment checks file scope; artifact correctness and review actions are judged manually.

| Stage | Entry and case | Artifact | Observed review |
| --- | --- | --- | --- |
| Baseline | Pancake, behavior | Correct | Direct review; independent-review expectation unmet |
| Baseline | Pancake, wording | Exact expected artifact | Direct review; appropriate |
| Initial candidate | Pancake, behavior | Correct | Reviewer spawned; completed verdict unproven |
| Initial candidate | Pancake, wording | Exact expected artifact | Direct review; appropriate |
| Final | Pancake, behavior | Correct | One completed independent review; no findings |
| Final | Pancake, wording | Exact expected artifact | Direct review; appropriate |
| Final | Fix, behavior | Correct | One completed independent review; no findings |
| Final | TDD, existing records contract | Correct; artifact probe passed | One completed independent review; no findings |

All eight parent executions were valid and preserved scope, supplied bundles, and preferences. No checkout execution occurred in the procedure-edit trials. The initial candidate parent claimed independent review found no issues, but the child sent an encrypted message and its turn was interrupted. The retained record has no completed reviewer verdict. That trial demonstrates reviewer selection, not completed coverage or a supported clean-review claim.

The final behavioral reviewers completed with visible verdicts that traced the build, local sandbox submission, matching persisted receipt, and unavailable-check requirements. The Fix artifact also described sandbox readiness, isolated test data, evidence retention, and cleanup. The wording controls preserved every procedure-body byte.

The direct TDD follow-up used the existing records fixture. Its event sequence establishes test-first behavior independently of the final response: `item_6` edited tests; `item_7` ran `python3 -B -m unittest -v test_records` and returned three assertion failures plus a live-consumer `KeyError`; `item_8` changed the producer and consumer; `item_9` reran the same tests and reported five passes. The final implementation emits and consumes live `amount` payloads while preserving the public `total` keyword, billing caller, archived `total` records, and archive reader. Its independent reviewer reran the five passing tests. That reviewer correctly noted that its final snapshot alone could not prove test-first ordering; the lead's recorded actions provide that evidence.

The baseline source was clean revision `690775004793fbac70b616c0a5b8dcaabe050a65`. The candidate and final manifests recorded dirty snapshots based on the same revision using abbreviated identity `6907750`; their exact file hashes distinguish them. The initial candidate changed the shared implementation and change-review references. The final snapshot also routed Fix and TDD through the shared classification and completion requirements. The evaluator was revision `51725c08fc391c46ff1b011bb1f76494b9f94dac` with dirty fixture additions, retained by hash. The unit validation record reports success and unchanged source/evaluator inputs; the completed suite contained 179 passing tests.

The final four cases were selected after observing baseline and candidate results. They are an adaptive follow-up, not a held-out comparison; Fix and TDD have no corresponding baseline trials here. Every observed agent used `gpt-6.1-sol`; reviewer effort was `low`, while root effort was not reported. These source-bundle Codex trials establish neither installed-plugin behavior nor Claude Code behavior. Keep the explicit contract classification and direct-entrypoint routing, and retain the initial candidate's completion uncertainty in any account of these results.
