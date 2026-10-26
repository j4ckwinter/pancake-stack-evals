# Coordination and reproducibility gaps, 26 October 2026

## Delegated implementation

Four source-guidance trials exercised a delegated importer change and a small direct edit. Both Pancake and a task-local Codex adaptation of pstack 0.15.32 passed the predeclared artifact probes and preserved protected files. The importer probes call the composed CLI and adapter interfaces, including signed values, empty input, old payloads, account normalization, invalid input, and malformed CSV quoting. Positive repaired artifacts and deliberately broken variants establish that the probes discriminate these failures.

| Task | Guidance | Artifact probes | Completed children | Seconds |
|---|---|---|---:|---:|
| Importer | Pancake | Pass | 3 | 142.467 |
| Importer | Adapted pstack | Pass | 2 | 161.823 |
| Small edit | Adapted pstack | Pass | 0 | 81.766 |
| Small edit | Pancake | Pass | 0 | 47.777 |

The task requested bounded implementation delegation for independent adapters. These runs establish behavior under that explicit request, not automatic task decomposition. The small control explicitly prohibited delegation. The runs used inherited CLI defaults with no model or effort override. Session records identify gpt-6.1-sol. Root effort was unreported; child records report low effort. This does not establish inheritance from the outer IDE conversation or model diversity.

The upstream input is `cursor/plugins` revision `99b609a72323b70204eab407c622f436e858e112`, package version 0.15.32. The [adaptation receipt](evidence/coordination-launches/adapt-upstream.py.txt) inserts a Codex compatibility reference into each skill and supplies host mappings and agent templates. Workflow bodies remain upstream content. The bundle contains 58 skills and 167 files. Nine help-document links outside the skill tree and one literal template URL remain unresolved. These paths are not part of the tested feature workflow. Optional external tools and native Cursor execution were not exercised.

The [unit record](evidence/coordination-unit1-2026-10-26.json) retains exact input hashes, observed sessions, artifact results, and package-check identity. Raw records remain private under `/tmp/pancake-gaps-oct26/unit1`. Credentials were removed by the runner. Each trial used a fresh temporary profile and workspace with a 300-second limit. The evaluator and both source bundles remained unchanged throughout the batch.

Independent code review caught two oracle gaps before model trials. The direct task incorrectly permitted added tests, and the CSV probe omitted malformed quoting. Both were corrected and received regression coverage. All 186 package and evaluator tests passed before the batch. Package checks did not overlap the model runs.

These are single observations per case and arm, not general superiority or latency estimates. The validity of duplicate names among irrelevant extra CSV columns was not specified precisely. The two importer artifacts differ there, so that difference remains an unscored residual concern rather than a posthoc success criterion. Process assessment uses actual tool calls and outputs. Encrypted assignment messages prevent a complete briefing audit. Claude verification and plugin installation remain excluded.

Independent evidence assessment confirmed substantive exclusive worker edits, lead integration and combined checks in both importer runs. Pancake also completed an independent review with code inspection and executed checks. Both direct controls used no workers. The unit record retains the assessment and its action references. Blinding was partial because guidance identities remained visible.

## Representative-unit pilot

The conditional pilot paragraph was rejected. Both migration arms launched the two exporter-pair workers before any representative implementation or verification. Both later passed the final artifact probes and completed independent review. The raw timestamps establish launch-before-implementation ordering. Encrypted briefing content leaves shared-brief corrections unobservable.

| Task | Guidance | Artifact probes | Pilot before expansion | Seconds |
|---|---|---|---|---:|
| Repeated migration | Unchanged | Pass | Absent | 105.793 |
| Repeated migration | Pilot paragraph | Pass | Absent | 114.103 |
| Small direct edit | Pilot paragraph | Pass | Not applicable | 38.509 |
| Small direct edit | Unchanged | Pass | Not applicable | 32.178 |

The migration covers four provider-specific archived formats, flat legacy records, new amount records, zero-valued precedence, keyword API compatibility, exact integer types, and the composed CLI. The direct controls prohibit delegation and both stayed direct. Independent review corrected numeric-equality false passes and missing explicit empty-list coverage before the live trials. All 189 package and evaluator tests then passed with unchanged inputs.

Only the pilot paragraph differs between the frozen skill trees. This four-module, fully specified migration may fall under the candidate's small or established transformation exception. Its absence of observed separation does not establish that representative pilots are generally ineffective. It supplies no behavioral reason to retain the addition here. The [candidate patch](evidence/coordination-pilot-candidate.patch) and [unit record](evidence/coordination-unit2-2026-10-26.json) preserve the experiment and independent assessment. Raw records remain private under `/tmp/pancake-gaps-oct26/unit2`. No subjects were rerun to obtain a preferred outcome.

## Fresh-state verification recipe

The proposed fresh-state and stand-in paragraphs were rejected. Both guidance arms read the existing recipe reference and produced runnable recipes with initialization, seeding, real CLI posting and read-back, retained evidence, and ownership-aware cleanup. Corrected sandbox replay passed for both saved artifacts from empty and preexisting state. Both also returned failure when posting or reading failed while health remained green. This supplies coverage for existing guidance rather than evidence that the addition is needed.

| Guidance | Corrected artifact replay | Seconds |
|---|---|---:|
| Unchanged | Pass | 118.638 |
| Fresh-state paragraph | Pass | 138.902 |

The original evaluator incorrectly reused one receipt path across two independent state scenarios while requiring the first receipt to survive cleanup. Both recipes reasonably refused to overwrite it. The user contract did not require overwriting evidence. Independent assessment identified the oracle error. The corrected fixture uses separate receipts and adds a positive control that refuses occupied evidence paths. The original model runs and failed assessment records remain unchanged; only the saved artifacts were replayed under the corrected oracle. The unit record retains both outcomes and both evaluator identities.

Independent assessment confirmed exact documented command execution in the unchanged run. The candidate executed the same run/cleanup interface through temporary-path subprocess checks; its literal documentation block was not separately replayed. Documentation examples match the working interfaces in both artifacts. The executable replay does not establish arbitrary shell-prose reproducibility. Stand-in setup behavior was not exercised, so no benefit from that clause is claimed.

The [candidate patch](evidence/coordination-recipe-candidate.patch) and [unit record](evidence/coordination-unit3-2026-10-26.json) retain the comparison, oracle correction, independent assessments, and input hashes. Raw records remain private under `/tmp/pancake-gaps-oct26/unit3`. Portable fixture controls use trusted literal programs; live artifacts always execute in a disposable writable sandbox. The real sandbox smoke is explicitly opt-in, so Python-only CI does not require an installed Codex CLI.

All 193 package and evaluator checks completed successfully, with the opt-in sandbox smoke skipped in the standard run. The smoke passed separately. Both inputs remained unchanged.
