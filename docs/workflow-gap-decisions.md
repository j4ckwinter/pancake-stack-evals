# Workflow gap decisions

The October 23–24 pass implemented four scoped improvements after comparing Pancake Stack with pstack. The user authorized separate commits and release. All runtime evidence belongs in this repository; the library remains declarative.

| Unit | Decision | Evidence and limits |
| --- | --- | --- |
| Reading paths | Centralize delegation coordination without adding another skill. | [Reading paths](reading-paths.md) records four valid trials. An earlier input-unstable trial and check were excluded. Full returned guidance decreased by 149 words per selected task; this is not a token or efficacy claim. |
| Measurement retention | Use exclusive per-batch storage in the evaluator fixture. | [Sample retention](sample-retention.md) records two 80-sample batches and a rejected overwrite. A later serialization correction has focused tests, not a rerun of the live trial. |
| PR maintenance | Keep current skill wording and add execution coverage. | [PR maintenance](pr-maintenance-execution.md) records actual local adapter commands, a stale-head defect case, and a clean control. No live forge was tested. |
| Instruction classification | Load classification before editing and explicitly cover agent authorization, delegation, and verification changes. | [Instruction classification](instruction-classification.md) separates correct artifacts from review completion and retains the initial candidate's ambiguous reviewer evidence. |

Minimize Reader Load shaped the delegation deletion. Model the Domain shaped the recorder's explicit batch lifecycle. Encode Lessons in Structure kept retention and execution checks in the evaluator rather than adding skill prose. Prove It Works required real artifacts and recorded reviewer verdicts. Sequence Work into Verifiable Units kept the changes in separate commits.

Independent reviewers inherited host model settings. They were separate review contexts, not a diverse-model panel. GitHub CLI was used because Origin was unavailable. The release plan uses merge commits to preserve the user's requested per-unit history. No plugin installation, global preference writes, new skills, or authenticated Claude workflow trials were included. Raw sessions and credentials are not published.

An early release-review check overlapped evidence-document writes. Its 179 tests passed, but the evaluator identity changed, so that run is excluded from stable release validation. The final library check runs against the published evaluator revision.
