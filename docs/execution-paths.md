# Execution path improvements, 25 October 2026

The first two bounded comparisons support shorter implementation instructions and a selective independent-design default. They do not establish general quality or speed gains. Each source change was evaluated separately before the next change.

## Implementation compression

Both source variants completed the small refactor and invoice migration. Literal artifact probes passed. A separate assessor checked neutral artifacts, recorded baseline/final commands, and completed reviewer identities. Both migrations preserved the documented API and archive contracts. The compressed variant reviewer executed Decimal/Fraction probes. The unchanged variant reviewer caught an intermediate Decimal rejection, which was fixed before a completed rereview. Explicit executed NaN coverage was unavailable for that unchanged run. Each had one completed independent reviewer. The small refactors used no reviewers.

| Task | Guidance | Complete returned guidance words | Seconds |
|---|---|---:|---:|
| Small refactor | Unchanged | 3,899 | 24.468 |
| Small refactor | Compressed | 3,596 | 24.932 |
| Invoice migration | Compressed | 5,083 | 88.198 |
| Invoice migration | Unchanged | 5,255 | 112.699 |

The implementation reference shrank from 970 to 667 words. Complete returned guidance includes other references and repeated worker reads, so its difference need not equal the edited-file difference. Counts measure returned text, not attention or tokens. These single observations are not latency estimates.

## Consequential design defaults

Both interface designs remained direct and preserved existing caller semantics. Both queue proposals passed independent semantic assessment. The new default launched two fresh proposal workers and a later separate judge. The judge reconciled materially different enqueue-identity and retry contracts. The unchanged default produced a direct proposal.

| Task | Guidance | Complete returned guidance words | Seconds | Completed workers |
|---|---|---:|---:|---:|
| Interface | Prior default | 852 | 25.545 | 0 |
| Interface | Selective competition | 885 | 28.517 | 0 |
| Queue retry | Selective competition | 6,579 | 123.594 | 3 |
| Queue retry | Prior default | 1,359 | 69.284 | 0 |

The new default exercised the intended behavior and retained the small-task control. It costs more reading and elapsed time in this sample. Both semantic designs passed, so this is not evidence that independent competition generally improves designs. Worker briefs are encrypted in the retained records. Fresh-context flags, linked completed outputs and sequencing are observable; equal briefing is unavailable.

The frozen design bundle predates a recipes wording correction. Only skills and docs/configuration.md enter candidate bundles, so that later documentation correction does not change trial instructions. One package check overlapped the recipe correction and is excluded despite passing tests. Its stable replacement passed all 180 checks with both inputs unchanged.

## Conditional comparison-reference extraction

The extraction was rejected. It navigated correctly and preserved the assessed tasks, but did not demonstrate ordinary-path simplification sufficient to justify another reference.

| Task | Guidance | Complete returned guidance words | Seconds | Completed workers |
|---|---|---:|---:|---:|
| Partitioned repository trace | Existing reference | 5,111 | 92.145 | 1 |
| Partitioned repository trace | Extracted reference | 5,665 | 105.770 | 1 |
| Explicit independent comparison | Extracted reference | 12,877 | 224.945 | 3 |
| Explicit independent comparison | Existing reference | 15,270 | 223.237 | 3 |

The ordinary candidate did not return the extracted comparison reference. It returned the shortened parallel-work reference twice, saving 370 words on that file, but loaded and repeated other guides. Its complete observed path increased by 554 words. The explicit comparison followed the new reference and returned fewer total words. Summed observations across both cases decreased from 20,381 to 18,542 words. This mixed sample does not establish a causal reading reduction.

Independent assessment passed all four task, semantic, scope and process outcomes. The explicit candidates independently converged on their primary recommendations while considering alternate architectures. Their agreement is not evidence of diverse primary recommendations. Exact briefing remains unavailable. One judge misread an explicit retry_policy argument in an example as a default; the final conservative policy remained sound. The exact rejected patch is retained for reproduction.

The accepted source for the final repository review is clean commit 42cd642. It contains implementation compression and the selective consequential-design default. It does not contain the extracted comparison reference.

## Repository review against pinned Poteto

All eight substantive review verdicts passed independent assessment. Each arm detected both seeded regressions and reported no false actionable findings on the two clean controls.

| Case | Pancake | Poteto |
|---|---|---|
| Identity, clean extraction | No actionable findings | No actionable findings |
| Identity, faulty extraction | Symlink-order regression detected | Symlink-order regression detected |
| Trace reset, clean extraction | No actionable findings | No actionable findings |
| Trace reset, faulty extraction | Stale prior-turn evidence detected | Stale prior-turn evidence detected |

These cases use a complete archived repository with actual modules, callers, tests and documentation. The changes are seeded refactors, not historical production incidents. Both arms ran read-only without delegation. This compares bounded review behavior and cannot establish orchestration strengths, implementation efficacy, or general superiority.

The Poteto input is the installed Codex adaptation of upstream pstack 0.15.5 at `2eb7ed4613cfc8f098dfe464a23680ea44d84c5e`. It contains 47 selected skills and 220 files. Its only unresolved relative link is the literal `url` placeholder in `why/references/synthesizer-prompt.md`. No current-upstream equivalence or installed-host claim is made.

One initial neutral packet omitted nested commands from the CLI event projection. Canonical raw session actions proved that the candidate had read the caller and existing tests. Its first heredoc failed under the read-only sandbox; its later `python3 -B -c` check completed 2,801 in-memory event sequences. The provisional reporting concern was removed after this evidence review. Full filesystem integration remained unavailable or omitted where disclosed. CLI event projections alone are not exhaustive execution evidence.

## Method and limits

Candidates ran in isolated Codex profiles with bounded execution and private raw records. Authentication was removed and temporary candidate directories were cleaned. No model or effort override was requested. Recorded selections identify gpt-6.1-sol; effort is unreported. Workers were instructed to inherit their candidate conversation settings. This is not proof of inheritance from the outer IDE conversation.

Each comparison has one repetition per case and arm. Independent assessors received neutral labels, actual artifacts, final outputs, completed worker records and command excerpts with guidance bodies removed. Source terminology and response style can disclose workflow details, so blinding is partial. These are independent same-host assessments, not provider-diverse judgments. Claude verification is excluded.


Package checks overlapped some candidate runs. Machine load was not controlled. Elapsed times are descriptive observations, not speed gains, regressions, or causal latency estimates. Full-repository fixtures retain their original evaluation/test terminology; strict terminology blinding is not claimed.

The independent source reviews passed the compressed sequence, corrected four-file design change, extraction text/link integrity, and repository-review runner extension. Static acceptance of the extraction did not override its inconclusive reading evidence. The first package run passed 179 checks. The added runner isolation regression brings the subsequent stable runs to 180. The unstable design check remains recorded and excluded. Installation and Claude verification are separate and were not performed.

## Records and reproduction

The [evidence record](evidence/execution-paths-2026-10-25.json) retains exact source and evaluator identities, dirty-tree hashes, settings, source-review verdicts, package checks, normalized final responses, independent judgments and per-run measurements. The [decision trail](evidence/execution-paths-decisions-2026-10-25.tsv) records acceptance, rejection and preparation. It does not establish publication. The [rejected extraction patch](evidence/execution-paths-cookoff-candidate.patch) applies to the accepted design revision.

The complete 67-file skill trees used by the compression and design candidates match commits `6b4f154` and `42cd642` byte-for-byte. Frozen inputs retained the exact precommit dirty identities. Snapshot preparation copied `skills` and `docs` and recorded `run_checks.identity` in `snapshot-origin.json`. Trial bundles copy skills and only `docs/configuration.md`.

The exact coordinator launch receipts are retained as nonexecutable text for [compression](evidence/execution-paths-launches/unit1.py.txt), [design defaults](evidence/execution-paths-launches/unit2.py.txt), [conditional extraction](evidence/execution-paths-launches/unit3.py.txt), and [repository review](evidence/execution-paths-launches/repository.py.txt). They call the existing `run_trial`, identity guards and complete-guidance assessor. Adapt their local absolute paths and provide new private output directories before an explicitly authorized rerun. The recorded plans and all input hashes are in the evidence manifest. These receipts are not a new supported runner interface. A rerun requires retained matching source and adapted Poteto inputs. Public source revisions alone do not reconstruct the private adapted bundle or raw sessions. No complete public reproducibility claim is made.

Compression used a 300-second limit per candidate. Design used 180 seconds for the interface and 300 for retry. Extraction used 180 seconds for the partitioned trace and 300 for explicit competition. Repository review used 300 seconds per candidate and reversed arm order between cases. Inputs remained unchanged throughout each batch. No automatic retries were used. Private raw records remain under `/tmp/pancake-unit1-oct25`, `/tmp/pancake-unit2-oct25`, `/tmp/pancake-unit3-oct25` and `/tmp/pancake-repository-oct25`; copied authentication was removed.
