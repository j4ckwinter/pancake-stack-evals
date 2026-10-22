# Measured gap pass

This pass kept the 19 existing skills and worked through the gaps in independently checked units. The user authorized implementation, commits, publication, and release. Claude workflow verification and plugin installation were excluded.

| Unit | Decision | Evidence |
| --- | --- | --- |
| Contributor check command | Invoke the evaluator through Python. The documented direct invocation failed with permission denied. | Corrected AGENTS.md; 136 checks passed with unchanged inputs before commit. |
| Natural task routing | Retain current descriptions. Both catalog-assisted and no-catalog runs completed the eight core tasks. | [Sixteen routing trials](metadata-routing.md). |
| Acceptance review coverage | Add two unrelated defect domains and their clean controls; retain existing Check wording. | [Eight acceptance trials](acceptance-paths.md), all outcomes passed. No demonstrated treatment advantage. |
| Experiment references | Retain three conditional branches after exact instruction relocation; all six outcomes passed and complete guidance reads fell in each pair. | [Six extraction trials](experiment-references.md). |

The initial routing report recorded one failed outcome and a second reporting caveat. Its assessment packet first dropped mixed guidance/task reads, then missed nested tool calls absent from CLI command events. Raw session calls and matched results proved the disputed executions. The same extraction error also affected two acceptance judgments. No subjects were rerun. Corrected judgments are 16/16 routing and 8/8 acceptance passes. An accidentally retained flattened output briefly revealed guidance to the assessors before removal. Both reports disclose partial blinding.

The evaluator now has regression coverage for nested calls, failed results, repeated results, prior turns, and session-local output matching. Raw call text proves an attempt; matched outputs and later wait results establish execution. File order does not establish chronology across sessions.

Checks rejected two local verification attempts because documentation changed during execution, although all tests passed. Stable reruns superseded those attempts. These input guards were not bypassed. Independent same-model code and evidence reviews completed for each unit; no model-diversity claim is made.

Trial manifests record the original clean archived library revision. Treatment files are derived from that archive and separately hashed in full; an origin's clean flag does not assert that a modified treatment equals the original revision. Raw records and authentication data are not published. Normalized evidence retains hashes, observations, and limitations.

Publication preserves the sequential implementation commits and pins the final published evaluator in the library. No global settings, preferences, marketplace registration, or plugin installation changed.
