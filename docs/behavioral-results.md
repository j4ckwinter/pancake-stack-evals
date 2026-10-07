# Workflow trials on 3 October 2026

For the repeated baseline comparison on 7 October, see [baseline comparison](baseline-comparison.md). The historical trials below remain unchanged.

These trials used the repository-source skills based on `602da98` with the changes prepared for `0.16.4`. Each task ran in a fresh agent context against its own temporary project and preference profile. The agents inherited the parent model. This was independent task execution with no provider diversity. The coordinating assessor knew the case and source variant, so assessment was not blinded.

The fixtures are derived from the seven historical trial families. They do not reproduce the original historical environments. The candidate tasks received natural requests and source skill paths, without private acceptance probes or expected corrections. All filesystem access remained unrestricted. The setup reduces accidental clues but cannot establish that assessor files were inaccessible.

## Observed outcomes

| Task | Checked outcome | Remaining evidence limit |
| --- | --- | --- |
| Delivery explanation | Correct rates, threshold, rejected inputs, and source locations. Trusted artifact checks passed and files were unchanged. | The candidate correctly described its work as static inspection. Parent execution proves fixture behavior, not candidate execution. |
| Empty-input fix | The final command returned count and average zero for empty input, preserved nonempty results, and passed project tests. The original nonempty assertion survived alongside an added regression test. | The final reply named the divide-by-zero cause and passing checks but did not include a failing-before result. Parent fixture tests reproduce the baseline failure; that does not establish that the candidate reproduced it before editing. |
| Carrier verification | The response reported missing token and missing client separately and declined integration readiness. Local rates and both failure states passed trusted artifact checks. Files were unchanged. | No live carrier service, credentials, or production policy were exercised. |
| Preference fallback | The response distinguished unavailable requested model and effort from retained host settings. Invoice checks passed. Project and isolated profile were unchanged. | Exact host model and effort were not exposed. Fixture resolution does not prove model-selection behavior. |
| Exporter review | The response identified the renamed field breaking the consumer, despite a passing exporter test. Trusted checks reproduced that mismatch. Files were unchanged. | External billing compatibility remained inaccessible. |
| Prose rewrite | The reply preserved the colleague's attribution, exact command and count, missing token, uncertain cause, and proposed rollback awaiting approval. It removed unsupported praise. Source files were unchanged. | Meaning was assessed directly by the coordinator. Artifact checks alone cannot judge prose quality. |
| Live-record migration | New payloads and consumer used `amount`; archived `total` records, archive reader, and unrelated note were preserved. Trusted checks and updated project tests passed. | The candidate reported direct review despite independent review being available. No completed independent review was established. |

The migration result prompted a narrower completion requirement in [implementation guidance](https://github.com/j4ckwinter/pancake-stack/blob/795dc890ee0b0acf24e743d82362c4a92e4202e1/skills/pancake/references/implementation.md). A fresh follow-up used that revised source and passed both data contracts, but again reported direct review. The wording change therefore has no demonstrated adherence improvement. This process gap remains an observable failure criterion for future trials. Adding further instructions without evidence about routing or execution would not establish a fix.

The candidate outputs and parent artifact checks support the observations above. Full candidate tool transcripts were not audited, so workflow reads, reproduction ordering, and other process claims remain unverified unless independently established. Host completion status and final replies establish that the listed candidate tasks completed; they do not prove every claimed tool action.

## Measurement-validity trial

A separate fresh task assessed a benchmark for summing the squares of 100000 integer rows. The apparently fast implementation returned an unconsumed generator. The candidate rejected adopting it from the original timing and measured complete eager and consumed-lazy operations instead.

Its retained measurement artifact contains 40 alternating pairs after five warmup pairs on Python 3.9.6. It records 80 successful measured sums and zero failures, with input construction outside timing. Median durations were about 2.379 ms and 2.387 ms. The corresponding ranges were 2.245 to 2.496 ms and 2.252 to 2.545 ms. The observed difference was smaller than the variation, so the response made no speedup claim.

Parent inspection confirmed the sample counts and independently called both implementations. The eager result and consumed generator both produced `333328333350000`. The raw measurement artifact supports the reported local observations. It does not prove that the guidance caused the response, identify a production bottleneck, or establish end-to-end performance.

## Repository verification

The fixture-support tests exercise baseline failures, literal outputs, incomplete corrections, protected-file mutations, read-only additions and deletions, isolated preference resolution, symlink rejection, and correction-file scope. Independent review found that the first assessor accepted arbitrary new files during correction tasks. The corrected assessor limits additions to top-level regression-test files, with a test that accepts a real regression check and rejects an unrelated addition.

An independent read-only reviewer reran all eleven focused checks and found no remaining actionable issues in that correction or the revised completion wording. This review covers the repository change. It does not supply the independent review missing from the migration candidates' own workflows.

Use the [evaluation procedure](behavioral-evaluation.md) to repeat these scenarios. Installed discovery, host shortcuts, global configuration, and marketplace registration remain separate checks documented in [the installation record](installation-verification.md).


## Focused tool-record follow-up

Two additional trials used the unchanged `437490f` skill snapshot, version `0.16.4`, on `codex-cli 0.160.0`. Each used a fresh temporary workspace and profile, ignored user configuration and rules, and enabled the CLI's multi-agent feature with a two-thread limit. The prompt explicitly permitted independent read-only review. The exact model and reasoning effort were not exposed in the retained events or stderr; null resolved preferences do not identify either. Feature configuration and prompt wording alone do not prove the candidate's available tool inventory. The coordinator inspected tool records and was not blinded. No guidance variant or causal comparison was tested.

Both processes exited zero and both trusted artifact assessments passed. The [summary evidence](evidence/summary-2026-10-03.json) and [migration evidence](evidence/records-2026-10-03.json) retain event order, commands, outputs, final replies, invocation, source hashes, and final project files. Temporary paths are replaced with `$TRIAL_ROOT`; returned skill bodies are replaced with their paths and hashes. Output hashes and raw JSONL hashes refer to the original local records. The raw files remain in the run's local temporary storage. No credentials are retained in either profile or repository evidence.

| Criterion | Tool evidence | Assessment |
| --- | --- | --- |
| Summary source reads | Completed `item_1`, `item_3`, and `item_6` returned Pancake, implementation, values, sift, check, and verify guidance. | Reads observed; comprehension and adherence cannot be inferred. |
| Summary reproduction order | `item_6` exited 1 with `ZeroDivisionError`, before the first recorded edit, `item_8`. `item_9` subsequently passed two tests and both CLI inputs. | Failing-before and passing-after behavior observed. |
| Summary final report | Final `item_10` names the correction and passing checks but omits the prior failure and cause. | Reporting criterion failed despite correct artifacts and observed reproduction. |
| Migration source reads | Completed `item_1`, `item_2`, and `item_3` returned implementation and review guidance alongside the live and archive code. | Reads observed; this run does not support missing guidance reads as the explanation. |
| Migration contracts | `item_5` edits producer, live consumer, and tests; `item_6` passes live and archive tests. Trusted assessment separately confirms both contracts and protected files. | Artifact criterion passed. |
| Migration review | Final `item_7` says affected callers and contracts were reviewed. The trace has no delegation or completed reviewer event. | Independent review remains unverified; the required workflow criterion is not established. Reading the check skill is not independent review. |

Shell batches deserve separate inspection: summary `item_5` has a zero final exit status despite a `git status` failure in a workspace without Git. That output does not establish a successful Git inspection. The command records do establish that the requested source content was returned. Neither trial demonstrates a general adherence improvement, and no stronger wording was added to implementation guidance on the basis of these runs.

The [accepted safeguards](safeguards.md) distinguish verified package validation and artifact boundaries from these unresolved workflow requirements.


## Completion workflow correction in 0.16.6

The implementation sequence now retains defect evidence and identifies consequential review needs during grounding. Review has its own phase. The final completion step uses the retained observations to report the cause and before-and-after result, plus the actual independent-review verdict or a concrete capability or permission limit. Standalone fix uses the same explicit defect-reporting shape. These are judgment-based workflow changes, not mechanical enforcement.

A fresh summary task ran on the same CLI version and invocation shape as the earlier focused task. The [new summary record](evidence/workflow-summary-2026-10-03.json) shows `item_6` reproducing the original CLI failure, `item_8` failing the newly added regression before the correction, and `item_10` passing both tests and CLI inputs. Its final reply identifies division by zero and says the regression failed before the fix and now passes. Source reads returned the revised implementation guidance. Trusted artifact assessment passed.

A fresh migration task used the current collaboration host, where delegation is observable. The [migration record](evidence/workflow-records-2026-10-03.json) retains the host's completed candidate and separate child-reviewer statuses. The reviewer reported no findings and independently passing live and archive tests. The final reply reports that verdict. The host status was inspected after candidate completion; it does not preserve the exact completion timestamps. Trusted artifact assessment passed and confirmed protected files were unchanged. Nested command transcripts were not retained, so individual reviewer command actions and source reads remain reported rather than directly traced.

The migration host differs from the earlier CLI run, and neither task used a randomized baseline or provider-diverse panel. The observed successes support these individual workflows; they do not prove causation, universal adherence, or working delegation in the previous CLI environment. The earlier failures remain in this document and their evidence files.


Standalone Fix also ran a fresh summary task on the CLI. Its [record](evidence/workflow-fix-2026-10-03.json) shows the original error in `item_4`, the added command-level regression failing in `item_6`, and passing tests and CLI inputs in `item_9`. The original error shares a shell batch with a succeeding nonempty command, so the batch exits zero despite the earlier traceback. The final reply names division by zero and the failing-before/passing-after regression. Trusted artifact assessment passed.

Independent review of the migration evidence caught imprecise reporting. The final reply says the two tests include zero-value checks, but their saved assertions use only `19.5`. In a read-only audit, the candidate clarified that zero was covered by a separate inline command and supplied its reported command and output. The evidence retains both the original reply and that correction. The inline execution remains self-reported because its original tool transcript was not retained. Later trusted assessment verifies zero behavior but does not prove that earlier candidate action.


## TDD skill in 0.17.0

The requested `tdd` skill was exercised on three fresh summary projects. The [retained evidence](evidence/tdd-2026-10-03.json) distinguishes the initial draft from the final source after independent review clarified test-only and already-working behavior.

The initial CLI task added its regression in `item_3`, ran it in `item_4` and observed `ZeroDivisionError`, then changed production code in `item_6`. Both tests passed in `item_7`; trusted artifact assessment separately passed. Its final reply accurately reports failing-before and passing-after evidence. Completed command records establish the ordering; this is one synthetic task, not proof of general effectiveness.

A separate test-only request added a command-level empty-input regression and left production code and the unrelated note unchanged. Parent execution reproduced its expected failure while preserving the existing nonempty assertion. Review identified that the initial prose could confuse already-passing coverage with a required behavioral failure. The final skill now has an explicit test-only branch and does not require manufacturing a failure.

A third fresh task used the final skill to add command coverage for `[6, 10]`, expecting count two and average eight. Parent execution confirmed both tests pass, the new assertion exercises the real command, and production code and the unrelated note remain unchanged. These test-only tasks inherited parent settings; their original tool transcripts were not retained. Parent checks establish the saved artifacts and behavior, not candidate execution ordering. Installed discovery, impractical-service fallback, general effectiveness, and provider-diverse comparison remain unverified.


## Challenge panel follow-up on 5 October 2026

Version 0.17.2 adds an optional Challenge reviewer panel. A fresh repository-source Pancake task supplied `gpt-6.1-sol` and `gpt-6-sol`, both with medium reasoning, against the exporter fixture. The lead reported both supported selections accepted and both independent reviews completed after bounded thread-limit retries. Parent host status observed reviewer execution and the second completed verdict. Both reviews identified the local consumer break and left inaccessible external billing compatibility unresolved. Parent artifact assessment passed, confirmed the sample project unchanged, and confirmed no isolated preference file was written. The [retained record](evidence/challenge-panel-2026-10-05.json) distinguishes direct observations from lead-reported model acceptance. This covers one task-supplied panel, not provider diversity, runtime model attestation, installed discovery, or the complete saved-panel setup flow.


## Installed Challenge panel on 5 October 2026

Fresh CLI sessions exercised version 0.17.2 from the installed cache. Setup discovered the host catalog and saved a two-reviewer panel in isolated storage. A separate Challenge session consumed that saved panel without task-supplied model choices. Retained spawn results and completed child `turn_context` records show host selection of `gpt-6.1-sol` and `gpt-6-sol`, both at medium effort. Missing, empty, and reported unsupported reviewer-choice runs used direct review and disclosed the absence of independent reviewers. Trusted fixture assessment passed and confirmed the sample project unchanged.

The [installation record](installation-verification.md) and [retained host evidence](evidence/installed-panel-2026-10-05.json) distinguish these observations from remote-runtime attestation, provider diversity, visible VS Code picker behavior, and unverified rejected-spawn or unavailable-delegation fallback. Real user preferences were not changed.


## Implementation panels and competing Design in 0.18

The [retained workflow evidence](evidence/roadmap-workflows-2026-10-05.json) covers fresh installed CLI sessions on 5 October 2026. Setup in 0.18.1 upgraded isolated schema 2 preferences to schema 3, saved two implementation reviewers, and preserved defaults, roles, and the Challenge panel.

The first migration artifact passed, but the workflow failed its completed-panel criterion. The lead reported both reviewers complete while one retained reviewer turn was interrupted without a verdict. The [failed-trial record](evidence/implementation-panel-incomplete-2026-10-05.json) preserves that discrepancy. Version 0.18.2 requires a separately identified completed verdict for each selected panel entry and rejects a generic wait result as proof of completion.

A fresh 0.18.2 migration then passed both artifact and panel checks. Retained child sessions completed on host-selected `gpt-6.1-sol` and `gpt-6-sol`, both at medium effort, and each returned no actionable findings. Trusted fixture assessment confirmed the new live `amount` contract, legacy archive readability, and protected files. The updated live test asserts exact payload shape and consumption for `19.5` and zero. A separate punctuation change with the same saved panel completed without child sessions and returned the expected greeting, confirming proportional review in that case.

The installed Design trial completed two independent candidate sessions, then a separate fresh-context judge. Candidates used the two requested model IDs at medium effort; the judge used `gpt-6.1-sol` at medium effort. Both candidates preserved the existing live/archive boundary and differed in callable API migration. The judge compared concrete compatibility, ownership, recovery, migration, and verification criteria against the baseline. The lead disclosed architectural convergence rather than claiming distinct architecture coverage. Project hashes remained unchanged and both baseline tests passed. This verifies design orchestration, not implementation of either proposal.

Host records establish selected models and reasoning efforts, not independent remote-runtime attestation. All observed models use one provider. Fresh judge context, ordering, and neutral proposal IDs are observable; full identity blinding is not independently established because local delegation message bodies are encrypted. Unavailable judges, partial candidates, and unsupported implementation selections remain unexercised cases.

Onboarding now includes a read-only first task, optional setup, separate review panels, and explicit independent Design examples. Existing substantial-work, decision-trail, handoff, and PR-maintenance guidance covers this run. No assigned PR or cross-session coordination requirement justified a new watcher or registry, so those conditional helpers remain deferred. No push, PR action, scheduler, or real user preference write occurred.

## Delegation fallback follow-up on 6 October 2026

Fresh installed 0.18.2 tasks on `codex-cli 0.160.0` exercised the previously missing rejected-selection and incomplete-exploration paths. Each used an isolated project and temporary `CODEX_HOME`. A separate runtime probe rejected the deliberately invalid negative-fixture model with HTTP 400 before the workflow trials. It was never presented as a supported model choice.

The [fallback evidence](evidence/delegation-fallbacks-2026-10-06.json) retains requests, completed commands, rejected spawn results, child contexts and verdicts, parent artifact checks, and file snapshots.

| Scenario | Observed outcome |
| --- | --- |
| Rejected implementation reviewer | The host rejected the requested pair. Pancake made no substitution, performed direct review, and disclosed the missing independent review. Trusted checks confirmed the live `amount` contract and unchanged readable `total` archives. |
| Rejected Challenge reviewer | The host rejected the requested pair. Challenge disclosed direct review and the missing perspective, reproduced the local consumer break, and left external billing compatibility unresolved. The project remained unchanged. |
| Partial Design exploration | One author was rejected and one completed. A separate judge completed after the proposal. The lead explicitly reported incomplete exploration and made no substitution. Project hashes and baseline tests were unchanged. |
| Unavailable Design judge | Two authors completed before the requested judge was rejected. The lead disclosed the absent independent verdict and proposed a design without claiming it was implemented. Project hashes and baseline tests were unchanged. |
| Delegation outside task permissions | A nonempty saved Challenge panel did not run when the task prohibited independent agents. Direct review disclosed the permission limit. The project and saved panel remained unchanged; the coordinator restored its temporary profile afterward. |

An initial one-thread diagnostic still completed a reviewer. An initial `gpt-5.6-terra` request also completed instead of exercising unavailability. Both diagnostics had a malformed runtime plugin override and read installed instructions by path. They remain inconclusive for their intended unavailable-capability criteria and do not establish automatic skill loading. The corrected tasks loaded the installation-generated temporary profile configuration. The [Setup loading correction](installation-verification.md) retains the underlying verifier correction.

These outcomes cover the named scenarios only. A host with genuinely absent collaboration tools remains unexercised. Permission limits and rejected selections do not prove that missing-tool behavior. All completed agents use one provider; host-selected contexts do not independently attest the remote inference runtime. No actual user preference file, global configuration, publication, or external message changed.


## Deferred preference lookup trials on 7 October 2026

Four fresh Codex CLI tasks exercised the uncommitted source change that defers saved preference lookup. Each used a separate temporary project and preference profile with a two-entry inherited implementation-review panel. The current source skill tree was copied once before execution. No plugin installation or user preference change was performed. Temporary authentication copies were removed after each process. The [evidence record](evidence/preference-timing-2026-10-07.json) retains the source diff and hashes, requests, completed tool events, final replies, and artifact assessments.

| Scenario | Observed result | Assessment |
| --- | --- | --- |
| Direct delivery explanation | Correct explanation, unchanged project, no preference helper command. | Startup lookup avoided in this case. |
| Delegated delivery investigation | Resolution occurred during delegate preparation after source inspection. An invalid `resolve research` attempt failed, then help inspection and plain `resolve` succeeded. | Conditional resolution observed; independent delegate completion is not established by retained events. |
| Migration with saved panel | `show` completed before the first edit; panel resolution followed that edit. The resolved panel contained two entries. The candidate reported a delegation thread-context failure and disclosed incomplete review. | Review-time discovery failed. Independent panel review remained incomplete. |
| Migration with explicit reviewer pair | No saved preference helper command, despite a two-entry saved panel. The candidate reported one completed reviewer using the explicit model and effort. | Saved-lookup bypass passed; actual reviewer selection and completed verdict remain unverified. |

All four trusted artifact assessments passed, and isolated preference objects remained unchanged. The CLI wait events contain empty receiver identities and agent states; final claims do not establish independent review. These are single synthetic runs with an unblinded assessor, no randomized baseline, and no Claude Code or installed-plugin coverage. They support the observed lookup behavior but do not establish general adherence. The premature panel read and recovered helper syntax error remain recorded; the skill instructions were not changed during these verification trials.


## Preference follow-up and observation repair on 7 October 2026

A fresh Codex CLI delegation probe retained trial-owned session records instead of relying on the summary JSONL stream. The records identified the child thread, its parent and task path, reported model and effort, its own final answer, and completion. The new read-only trace assessor consumes explicit trial paths. Six regression tests cover missing identities, lead-only claims, generic waits, requested versus observed settings, stale verdicts, and inherited fork history. Session metadata is read from the first owner record; inherited records predating worker creation are excluded. A completed child still needs association with the requested panel entry and reviewed project; the retained spawn calls, workspace metadata, and verdicts provide that evidence here.

The [follow-up evidence](evidence/preference-followup-2026-10-07.json) preserves thirteen task runs across source snapshots, plus the observation probe. Source hashes identify each snapshot. All thirteen trusted artifact assessments passed and all isolated preference files remained byte-for-byte unchanged. Authentication copies were removed. The original failed trials remain above.

| Behavior | Follow-up observation |
| --- | --- |
| Direct prose and local fix | Both completed without preference lookup. The fix retained failing-before and passing-after evidence. |
| Saved delegated role | Plain `resolve` succeeded; a linked investigator completed with the saved `gpt-6.1-sol` and low effort. |
| Saved implementation panel | Initial rerun skipped review entirely despite reading implementation guidance. After making shared payload and persisted-data contracts explicit review triggers, two fresh migrations each read preferences after editing and completed two identified reviewers with the saved settings. |
| Complete task override | No saved lookup; one identified reviewer completed with the explicit model and low effort despite a two-entry saved panel. |
| Partial task override | Requests saying “inherit its reasoning effort” repeatedly skipped saved resolution. With effort omitted from the request and medium saved for review, a final fresh trial ran `resolve`, spawned a fresh reviewer with medium effort, and retained its completed verdict. That changed request disambiguates the case; it does not prove the wording changes alone caused success or settle every use of “inherit”. |
| Saved Challenge panel | Two identified reviewers completed with saved settings and reported the producer-to-consumer regression. |
| Unsupported panel entry | The valid reviewer completed; the unsupported model remained explicitly uncovered, with no substitution. |
| Unavailable selection controls | `--disable multi_agent` did not remove the exposed collaboration tools. That run supplies saved Challenge panel evidence, not evidence about unavailable controls. This branch remains untested on a genuinely restricted host. |

The independent change review found one blanket timing prohibition that would have blocked legitimate pre-implementation delegates. It was narrowed to implementation-review panel discovery, and the reviewer confirmed the correction. Package, source-resolution, skill, preference, fixture, and trace tests passed (53 tests). These focused runs were unblinded, use Codex source skills, and do not establish installed behavior, Claude parity, or universal adherence. Explicit inheritance wording and hosts without selection controls remain limits. No further instructions were added merely to turn those limits into a passing claim.

## Reviewer detection and narrow consolidation, 7 October 2026

The records migration fixture now protects an established `billing.invoice_for_order()` caller using `create_invoice(total=...)`. Its request explicitly preserves that public API. Trusted probes exercise both positional and keyword calls, the unchanged billing caller, the new live payload, and old archived records. A regression test proves that renaming the parameter is rejected even when the candidate's local tests pass.

The [reviewer comparison evidence](evidence/reviewer-comparison-2026-10-07.json) records 16 fresh read-only Codex CLI 0.160.0 reviews using `gpt-6.1-sol`: three single-defect migrations and a clean migration, two repetitions each, with baseline and consolidated Check instructions. Ordering was counterbalanced and execution sequential. No effort override was supplied; session records report null effort, so actual effort is unknown. Each faulty fixture passes its local tests but fails exactly one independent contract probe.

The candidate consolidates only three adjacent contract-tracing paragraphs, reducing Check from 4,697 to 4,356 UTF-8 bytes. It adds no compatibility rule and preserves the surrounding process instructions. A fresh independent assessor reviewed neutral packets with treatment identities and instruction bodies withheld. The lead then mapped its judgments to the variants. Weakened test assertions were deduplicated with their associated contract failure.

| Observation | Current baseline | Consolidated variant |
| --- | --- | --- |
| Completed reviews | 8/8 | 8/8 |
| Detected seeded defects | 6/6 | 6/6 |
| Missed defects | 0/6 | 0/6 |
| False actionable findings, all runs | 0 | 0 |
| Clean controls with false findings | 0/2 | 0/2 |
| Diff/caller inspection, contract execution, grounded verdict | 8/8 each | 8/8 each |
| Workspace and preferences preserved | 8/8 | 8/8 |
| Elapsed seconds, median [min–max] | 28.519 [24.122–35.187] | 29.206 [24.742–30.101] |
| Input tokens, median [min–max] | 80,509 [79,901–82,251] | 80,630 [63,463–82,012] |
| Cached input tokens, median [min–max] | 71,168 [67,968–73,856] | 70,592 [54,016–74,880] |
| Output tokens, median [min–max] | 596 [494–701] | 598 [528–694] |
| Total tokens, median [min–max] | 81,060 [80,493–82,952] | 81,251 [64,062–82,699] |
| Recorded top-level tool calls, median [min–max] | 4 [4–4] | 4 [3–4] |
| Emitted command-action events, median [min–max] | 5.5 [4–7] | 6 [4–7] |

Every cost row has eight completed observations per variant; there were no execution failures or missing usage records. Tokens measure usage, not money. Command-action events omit some executed commands on this host, so their counts cannot measure all shell activity. Paired raw custom tool calls and outputs established the missing executions. Initial assessor packets omitted these records and incorrectly suggested process failures; the assessor corrected those judgments after receiving the complete evidence. The trace parser now retains custom tool inputs and outputs, with a regression test.

Keep the production baseline. This small pilot found no loss of the measured review behavior, but it did not demonstrate lower overhead: medians were similar and ranges overlapped. Accuracy saturated on four closely related fixtures; these observations do not establish general defect detection, production savings, or implementation-panel behavior. No shipped skill instructions, preferences, installation, or marketplace registration changed. The raw records remain private at `/tmp/pstack-review-20261007-pilot`; the linked evidence retains sanitized verdicts, execution excerpts, instruction diff, source hashes, scores, and cost samples.
