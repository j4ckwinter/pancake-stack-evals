# Repository review pilot, 13 October 2026

Both baseline and Pancake detected all four seeded-defect presentations per arm and produced no false findings on four clean controls per arm. All 16 trials completed. Pancake used more recorded tokens and time at the median in this sample; these results establish neither superiority nor general review performance.

| Outcome | Baseline | Pancake |
|---|---:|---:|
| Completed trials | 8/8 | 8/8 |
| Seeded defects detected | 4/4 | 4/4 |
| Clean controls with false findings | 0/4 | 0/4 |
| False findings across all trials | 0 | 0 |
| Execution failures | 0 | 0 |
| Median elapsed seconds | 49.851 | 69.252 |
| Median total tokens | 124,361 | 156,112 |
| Median cached input tokens | 104,512 | 137,728 |
| Median output tokens | 992.5 | 1,428.5 |
| Median tool calls | 5.5 | 6 |
| Median command actions | 4.5 | 8 |

Token counts include cached input and are usage measurements, not dollar costs. All trials have recorded usage. Each median is computed independently, so component medians need not add to the total-token median.

## Design and provenance

The [declared protocol](behavioral-evaluation.md#repository-review-pilot) used two real evaluator modules from frozen commit `d81ad93f3195d5164a305b79e504c44e16001b51`. Each module had a behavior-preserving helper extraction and a seeded faulty extraction. These are mutations of real repository code, not historical bug fixes. The archive contains all 122 committed files, including callers, tests, and documentation. Its compressed SHA-256 is `1e6d0ae6aa4380347e9c8e409c037a95dba355af9eac005a8bb9efb5444df075`; extraction validates the archive and individual file hashes.

The faulty identity refactor checks `is_file()` before `is_symlink()`, following the link and hashing referent bytes. Retargeting an already-dirty or untracked link between equal-content files can escape the identity guard. The faulty trace refactor omits clearing `calls` and `outputs` at a new turn, retaining earlier evidence alongside the latest verdict and settings. The clean counterparts preserve the original behavior.

Four cases, two arms, and two repetitions produced 16 trials. Arm order reversed per case on the second repetition. Both arms used `gpt-6.1-sol`, medium effort, Codex CLI `0.160.0`, a 300-second limit, isolated profiles, read-only workspaces, and disabled delegation. Pancake additionally received its skill bundle. The source checkout was clean at `b7704ec2f6e61c87da3178c194b166500f9e3fb5`; the evaluator checkout was clean at `5755ba815573754b083ddb49fce36cc09c30ae3f`.

Source and evaluator identities remained unchanged throughout the batch. All workspace checks passed, no preference files were created, and temporary candidate profiles were removed after record collection. Raw traces remain private outside Git; copied authentication files were removed with temporary profiles.

## Verification and independent assessment

Before live execution, all 104 evaluator/source checks passed. The original snapshot and all four mutations passed the existing focused identity and trace tests. Independent private filesystem probes passed the original and clean changes, and rejected only the matching faulty changes. This establishes the seeded mechanisms separately from candidate review performance.

Candidate checks ran under a read-only sandbox. Fourteen candidates completed a Python check using mocks, in-memory trace readers, or branch-equivalence probes; two clean identity reviews relied on inspection. The trace checks adapted the seven existing tests to an in-memory reader and, for faulty cases, added reproductions. They do not establish full filesystem integration coverage or a full-suite candidate run.

There were 15 Python command attempts and 14 successful Python executions. Packet E (`run-08`) first attempted a heredoc that the sandbox blocked. Its shell still returned zero because a later source-listing command succeeded. A subsequent `python3 -c` attempt successfully ran seven tests and reproduced the defect. The evidence retains both attempts rather than counting the wrapper exit status as successful Python execution. Other checks emitted macOS temporary-cache warnings but reached their recorded Python assertions or test results.

The independent assessor was requested as `gpt-5.6-sol`; no runtime model-selection evidence is retained, so this is not an observed-model claim. It received neutral labels A–P, the changed source and diffs, original repository context, final responses, and recorded Python commands and outputs. It received neither the treatment map nor requested model or guidance-reading commands. It judged every finding by mechanism and consequence: all eight faulty presentations were detected, all eight clean presentations correctly received no actionable findings, and verification claims matched the retained checks. Some caller-inspection claims lacked separate evidence in the neutral packets; the assessor treated that as a coverage limit.

Blinding was partial: original repository names and evaluation terminology remained visible, and final prose could disclose aspects of the workflow. The label map was joined to the independent assessments afterward. Aggregates use `behavioral.review.summarize` with `behavioral.repository_review.CASES`, keeping execution failures and usage separate from defect scores.

The [sanitized evidence](evidence/repository-review-2026-10-13.json) retains manifest file hashes, run results, normalized prompts and invocations, final responses, Python attempts and outputs, label mapping, per-output assessments, and computed aggregates. Raw-file SHA-256 values refer to original bytes before path normalization. Credentials, account metadata, and raw session records are excluded.

## Limits

This is a ceiling result on two seeded mechanisms in one repository with two repetitions per arm. Repeated presentations are not independent defects. It does not establish broader review efficacy, historical-bug detection, installation parity, or a causal explanation for the observed usage difference. Full repository context makes the task less synthetic than an isolated snippet, but the changes and ground truth were still constructed for this pilot.
