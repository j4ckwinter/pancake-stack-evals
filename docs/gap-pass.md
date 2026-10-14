# Gap pass, 14 October 2026

This pass addressed candidate isolation, evaluator input guards, historical and handoff coverage, and a reproducible Codex refresh route. The library changes stay declarative. Tests, fixtures and evidence remain in this repository. Claude authenticated workflow verification was excluded from the task.

| Decision | Evidence and outcome |
| --- | --- |
| Reuse shared fresh-context rules for Design candidates and the judge. | [One live Design trial](design-isolation.md) observed fresh launches and completed verdicts. Encrypted brief text limits the neutrality audit. |
| Apply input-identity guards to every comparison suite. | Workflow and review drift cases failed before the fix. Regression tests now cover all eight suites, including drift before and during a trial. |
| Add historical and stale/fresh handoff cases through the existing runner. | [Historical review](historical-review.md) retains missed targets and valid off-target findings. [Recovery](context-recovery.md) reached the scoring ceiling for both arms. Neither establishes a quality advantage. |
| Preserve an invalid control's original results and calibrate separately. | Real reproductions confirmed malformed archives, producer/reader incompatibility, and zero-test acceptance. The follow-up found the omitted `False` case. Current checks reject those cases; no live result is relabeled after correction. |
| Remove a proposed skipped-test counter check. | Independent review reproduced a valid suite rejected because method and subtest counts differ. A retained acceptance regression covers that case. |
| Keep the allowance for shared Python helpers and documentation. | Filename restrictions would risk restoring the historical rejection defect. Semantic relevance remains a review responsibility. |
| Document the tested local-checkout update route. | [Codex refresh](codex-refresh.md) verified 0.21.6 to 0.21.7 plus a repeated install in a temporary profile. The two versions have identical skill contents; this proves version refresh and resource identity, not replacement of changed skill text. |

## Verification and independent review

The final implementation passed 121 package and evaluator tests with source and evaluator files unchanged during the run. Package checks cover JSON parsing, marketplace resolution, all 19 skills, and local documentation links. These checks are separate from model trials and installation experiments.

Fresh reviewers checked candidate isolation, the input guard fix, scenario implementation, control calibration and the installation recipe. Review found and corrected an inherited `GIT_INDEX_FILE` escape and the skipped-subtest false rejection. Semantic assessors received neutral response labels before the arm mapping. Their partial blinding and lack of replicated response assessment remain explicit in the reports.

The task used Poteto mode. Prove It Works led to real host trials and before/after regressions. Build the Lever put rerunnable checks in the evaluator. Model the Domain kept cases and adjudicated fact IDs explicit. Laziness Protocol reused the existing runner and shared context rules. Test Behavior, Not Implementation used independent invalid implementations and valid acceptance controls. Sequence Verifiable Units kept changes in ordered commits. The reports preserve the unsuccessful measurements as well as the fixes.

Publication preserves those commits so the exact source and evaluator revisions in evidence remain reachable. Repository CI pins an evaluator commit; a local verification recipe must resolve that same pin rather than silently testing a newer default branch. Installation and release remain explicit delivery actions outside package checks.
