# Initial diagnosis, 27 October 2026

The retained Fix edit moves the existing distinguishing-observation instruction from repeated failed corrections to the first diagnosis step. The new condition applies when more than one cause is plausible. This comparison found successful diagnosis and repair with both versions. It does not demonstrate a diagnostic advantage from the relocation. The edit is retained as a sequencing clarification, not as a measured performance improvement. It relocates an existing instruction with near-zero length growth. This differs from the rejected natural-routing links, which added a required reference read without demonstrated benefit.

The fixture uses a long-lived JSON-lines quote CLI, an importable `QuoteService`, and a file-backed `Catalog`. Account selection, account normalization, and cache behavior are plausible sources of incorrect prices. In the original implementation, the cache key contains only the SKU. Looking up north's Widget and then south's Widget returns 120 twice. Restarting the service returns the correct price for each account. The existing two tests pass because they exercise fresh accounts and one repeated lookup.

The natural request reports the wrong prices and asks for a repair that preserves the documented contracts. Account names ignore surrounding whitespace and case. SKU spelling remains exact. Successful warm lookups avoid repeated catalog reads. Unknown quotes raise errors without returning or storing another account's price. Each service owns its own cache. The request does not prescribe a cause or diagnostic process. A small `None`-filtering sum repair provides the clear-cause control.

| Guidance | Case | Artifact and scope | Completed review children | Complete lead Fix returns |
| --- | --- | --- | ---: | ---: |
| Baseline | Account quotes | Pass | 1 | 1 |
| Relocated instruction | Account quotes | Pass | 1 | 1 |
| Relocated instruction | Small control | Pass | 0 | 1 |
| Baseline | Small control | Pass | 0 | 1 |

Both quote leads inspected the service, catalog, CLI, and contract before patching production code. Both reproduced the incorrect CLI output, added regression coverage, changed the key to normalized account plus exact SKU, and verified the repaired CLI. Their independent reviewers inspected the contracts and executed the suites. The baseline suite had eight tests; the changed-guidance suite had seven. The artifact oracle separately passed both. These similar trajectories do not establish that either workflow consciously enumerated every alternative.

A fresh assessor supported all four outcomes. In both quote runs, prepatch inspection showed that the catalog selects a normalized account and exact SKU, the CLI passes both fields, and cache hits bypass lookup using only the SKU. This distinguished cache ownership from account selection and normalization. Both runs reproduced 120, 120, then showed behavioral regression failures before production edits and 120, 80 afterward. Both completed independent review. The small controls remained direct.

The assessor used the packet without fresh execution. Scope-oracle results were consistent with visible writes, but the baseline reviewer lacked an original diff. The changed run had narrower coverage for cold invalid arguments and malformed CLI inputs. Unicode account aliases were not explicitly exercised. These were coverage limits, not demonstrated defects.

The evaluator reuses the existing Case adapter, sandboxed artifact checks, and paired runner. Positive controls accept a partitioned cache. Negative controls reject the original bug, disabled caching, case-folded SKUs, absolute-value amounts, unnormalized account keys, default-account fallbacks, shared caches, and changed catalog data. The fixture check independently observes the original incorrect CLI output while its original tests pass. Independent review approved the fixture and source diff. Before live execution, all 197 package and evaluator checks passed with one opt-in sandbox smoke skipped and unchanged inputs.

The four sequential runs used fresh isolated profiles, frozen bundles, inherited CLI defaults, and a 300-second bound. All finished with final responses and unchanged inputs, bundles, and preferences. Each lead received the complete applicable Fix body once. Observed models were `gpt-6.1-sol`; lead effort was unreported and reviewer effort was `low`. Package checks did not overlap model execution.

The [normalized evidence](evidence/initial-diagnosis-2026-10-27.json) records revisions, dirty-state hashes, source differences, outcomes, and complete-body returns. The [candidate patch](evidence/initial-diagnosis-candidate.patch) preserves the exact relocation. Baseline skill hashes are shared with the [natural repair evidence](evidence/natural-repair-routing-2026-10-27.json). Raw sessions and assessment packets remain private. Partial blinding and encrypted assignment messages limit the process audit. This cache-key defect is easy to identify from source, so the comparison does not establish improvement on harder ambiguous diagnoses. No latency, host installation, Claude parity, or general superiority claim follows.
