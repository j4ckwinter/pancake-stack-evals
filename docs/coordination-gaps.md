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
