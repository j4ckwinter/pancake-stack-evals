# Historical migration assessor regression

`source.tar.gz` is the complete tree at introducing commit `c2b044ea3eb460519942f58af4926d6fda04bfe2`. `provenance.json` pins its parent, archive digest, and every extracted file. The private scenario module pins the provenance file's digest and checks each auxiliary artifact before extraction.

`introducing.diff` is the actual Git diff from the parent, restricted to `tests/behavioral/support.py` and the contract scenario directory. This extraction focuses the review on the affected assessor and task contract. The full contemporaneous repository remains available to the candidate.

`base-support.py.txt` comes from the introducing commit's parent. `repaired-support.py.txt` comes from fixing commit `e3a04e80210c87315c1d30cec324b352f3a4f11a`. The clean control now replaces that production file with `calibrated-support.py.txt` in the introducing tree and recomputes its displayed diff against the same parent. It is a counterfactual control, not a historical revision. No fixing-commit tests, documentation, or answer-bearing evidence enter the candidate tree.

The private regression test executes the historical `support.assess` against a valid migration using a shared source module and compatible billing/documentation updates. The faulty assessor rejects it before checking behavior. The repaired assessor accepts it and still rejects modified notes, modified stored archives, and unrelated JSON additions. These fixture checks establish discrimination for this mechanism, not model performance.

## Supplemental calibration

The original `repaired-support.py.txt` remains byte-for-byte historical evidence. `calibrated-support.py.txt` is derived from it by the exact supplemental `calibration.diff`; `calibration.json` pins both artifacts and their historical base. The scenario module pins this separate manifest and verifies the patch relationship before preparing the clean case. This calibration is not a historical revision. The faulty case remains the exact introducing snapshot.

Independent local reproductions identified three additional gaps in the original repaired control: malformed v1 archives could pass, producer float version values could satisfy equality without passing through readers, and deleting all tests produced successful zero-test discovery. The calibrated control checks the malformed-record matrix for both versions, checks actual producer/facade types and round trips, and rejects empty test suites. Nonempty discovery alone cannot prove arbitrary replacement tests are meaningful or prevent all tests being skipped; this calibration addresses the demonstrated deletion failure without prescribing test names or implementation structure.

Deterministic checks exercise these failures, acceptance of the valid shared-module migration, and protection of unrelated files. They establish fixture behavior only. The [historical report](../../docs/historical-review.md) records an earlier calibrated follow-up; the [19 October follow-up](../../docs/historical-review-followup.md) records fresh reviews after the Boolean correction. Each batch retains its original input identity. Supported additional findings must not be counted as false findings merely because they were absent from the expected-mechanism list.

The same validation corrections also apply to the current evaluator’s `tests/behavioral/support.py`. Shared deterministic probes exercise both the current assessor and the calibrated historical assessor; the immutable historical artifacts and faulty snapshot are unchanged.
