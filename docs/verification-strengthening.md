# Verification strengthening

Five bounded fresh-context source-skill trials exercised proposed Pancake Stack 0.21.20 guidance on 30 October 2026. They covered harness sensitivity, entry-point coverage, regression attribution, model drift, and existing-fix comparison. These are single observations, not a comparison with the prior skills or evidence of general improvement.

## Inputs and isolation

The library base was `d0a5d76b8cdbdf9d3fcff4327ebb1c8d505af9f0`, with the proposed guidance applied. The evaluator base was `bd752da43b956cb5baf024b126ca1a42d5e1b179`. The [metadata](evidence/verification-strengthening-2026-10-30/metadata.json) records source hashes, agent identities, and outcomes. Source skill files remained unchanged throughout the trials. Release metadata and documentation changed separately.

The [fixture preparer](../fixtures/verification-strengthening/prepare.py) creates five isolated targets from source, with local Git baselines where needed. Run it with `python3 -B fixtures/verification-strengthening/prepare.py /tmp/CHOOSE-AN-UNUSED-DIRECTORY`. It creates that directory and local fixture commits, does not install dependencies, and never starts agents. Commit IDs vary with creation time; resolve each target's actual revisions before replaying a request. Target E duplicates D for a separate report.

Each agent started with `fork_turns="none"` and inherited settings. Each received only its target, the source Check or Verify skill path, and the request below. They could read required skill references and use bounded local Python checks. They could not inspect sibling fixtures, the evaluator, parent history, or other agents. Delegation, network, installs, services, global settings, and commits were prohibited. Only the harness task could edit its two output files and use disposable broken copies; the existing-fix tasks could use isolated temporary source copies. No model diversity or installed-plugin behavior is claimed.

## Requests and observations

| Target | Request | Observed result |
| --- | --- | --- |
| A | Improve the store verification harness and write a reusable recipe covering supported entry points. Preserve product code and README; isolated copies permitted. | Replaced an existence-only check with exact persistence assertions through API and CLI writers and fresh-process reads. Documented coverage. Detected deliberate whitespace corruption in both writers and reran the valid artifact successfully. |
| B | Review `change.diff` for bugs and regressions, read-only. | Reported the introduced zero-limit regression and explicitly separated an existing division-by-zero defect from findings against the diff. |
| C | Audit whether the existing model still verifies the delivery worker contract. Run local checks; edit neither model nor product. | Found that the passing model combines two implementation steps atomically. Executed all six bounded worker schedules; four violated the at-most-one-delivery contract. Replayed a concrete violating schedule. |
| D | Verify whether the supplied fix commit resolves the reported zero-label issue. Compare before and after without changing the fix. | Compared exact parent and patched sources with identical inputs. Zero failed before and passed after; all six patched cases passed. Limited the claim to the exposed library function. |
| E | Verify whether the same fix commit resolves a report that `label(None)` displays incorrectly. Compare before and after without changing the fix. | Found both revisions already return the documented value for None. Reported that fix claim as inconclusive, while distinguishing the observed zero correction. |

The retained [harness](evidence/verification-strengthening-2026-10-30/verify.py), [recipe](evidence/verification-strengthening-2026-10-30/VERIFY.md), [negative-control output](evidence/verification-strengthening-2026-10-30/negative-control.txt), and [restored valid output](evidence/verification-strengthening-2026-10-30/valid-after-control.txt) preserve the generated artifact and its evidence. The harness trial initially used macOS's default temporary directory outside the assigned `/tmp` boundary. The agent reported this deviation, removed those copies, moved retained evidence, and used `TMPDIR=/tmp` for final runs. Behavioral success does not erase that scope deviation.

The [selected returned verdicts](evidence/verification-strengthening-2026-10-30/returned-verdicts.json) preserve B–E reports. Their historical tool execution and cleanup are agent-reported, not independently auditable from those reports. The lead independently replayed the harness, attribution cases, worker schedules, and label comparisons and checked that tracked files in the read-only targets remained unchanged; the [replay record](evidence/verification-strengthening-2026-10-30/lead-replay.json) retains those later observations. The original weak harness accepted whitespace corruption while the generated harness rejected it. Product files in A remained unchanged. Fresh-agent reports alone are not treated as proof of every unobserved tool action; this record does not retain complete raw session transcripts.

The local package/evaluator suite completed 197 tests with one opt-in sandbox check skipped. Both input trees remained unchanged during the successful run. Generic skill-creator validation was unavailable because the host Python lacked PyYAML; repository-specific metadata and reference validation passed.

## Review and limits

An independent fresh-context implementation reviewer found a stale Claude marketplace version. It was corrected to match both 0.21.20 manifests and the reviewer confirmed resolution, with no other actionable instruction findings. This static verdict does not establish behavioral efficacy.

No prior-skill control arm, repeated sampling, installed-host trial, authenticated Claude workflow, external model checker, or unbounded formal proof was exercised. The formal case uses an existing small Python model and real worker execution. The harness negative control covers whitespace corruption only. These observations support bounded workflow operation and preserve material gaps.

Instruction overhead was assessed by whitespace-separated entry-file word counts: Verify increased from 706 to 783 words; Check from 595 to 663. The three new detailed references are conditional. These are file-size observations, not measured total reading, latency, or token savings. No speculative router restructuring was adopted.
