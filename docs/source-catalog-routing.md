# Source-catalog routing probe

All six route-selection trials completed with unchanged inputs, workspaces, bundles, and isolated preferences. Each returned the complete expected guidance text before selecting its route. A separate judge found all six final routes relevant and all six authorization statements correct. The strict reading-scope criterion passed five cases: PR status also read the full PR-drafting skill before rejecting that route. No underlying task or alternative workflow was executed.

The agent was explicitly asked to inspect a supplied source catalog and select guidance for a natural-language request. It was not given a named skill entry point. The runner passed the bundle's `skills` directory through the existing Case adapter. These observations concern source-guided selection, not automatic triggers, installed-host discovery, picker behavior, or workflow execution.

| Request | Expected guidance | Complete returned content | Execution valid |
| --- | --- | --- | --- |
| Diagnose memory growth | Pancake forensics | Yes | Yes |
| Measure a schema cache | Pancake experiments | Yes | Yes |
| Check outstanding PR feedback | Pancake PR maintenance | Yes | Yes |
| Match a reference interface | Pancake visual parity | Yes | Yes |
| Explain cancellation flow | How | Yes | Yes |
| Draft PR wording | PR | Yes | Yes |

The two controls distinguish execution-flow explanation from diagnosis and PR drafting from maintenance. The experiment read Verify as supporting guidance. The visual request read implementation, verification, and change-review guidance. The PR-status request inspected and rejected the PR drafting route. Catalog enumeration and searches were not penalized. The extra full PR-drafting read failed the judge's strict minimal-guidance interpretation. Across four criteria per case, that interpretation yielded 23/24 passes; interpreting the fourth criterion solely as unnecessary workflow execution yielded 24/24. Preserve this distinction rather than treating an extra read as execution.

The candidate was Pancake Stack revision `fc470cfa58d25c8eb3b5e23a7f3d8cc51694b308` with uncommitted picker-description, README, and recipe changes. The evaluator was clean at `3e199e4e9d82e213a1e3a1dba6496a2f4e0ebc7c`. The [sanitized evidence](evidence/source-catalog-routing-2026-10-21.json) retains exact file hashes, original run IDs, input state, relative guidance paths, source hashes, and complete-read judgments, timing, and usage. Raw transcripts and the complete judge packet remain private.

No model or effort override was supplied. Each case had a 180-second limit, a read-only workspace, disabled delegation, and an isolated profile. All six roots were distinct and completed. Completed command outputs showed only local catalog listing, search, and reads, plus one working-directory query. No task execution or external access was observed. The recorded scope audit does not establish exhaustive filesystem access.

A [retained one-off runner](evidence/source-catalog-routing-2026-10-21.py) uses the existing `run_trial` and Case adapter. Run only with live-trial authorization:

```sh
python3 -B docs/evidence/source-catalog-routing-2026-10-21.py --source /path/to/pancake-stack --evaluator /path/to/pancake-stack-evals --output /private/new-routing-records
```

Both inputs must be Git checkouts. The runner records revisions and working-tree hashes before launching, checks them around each trial, and stops on invalid execution, changed inputs, mutated scope, missing completion, or empty output. The output directory must be new and outside both repositories. Assess routing relevance and scope from actual returned content and final answers; preservation alone does not establish correct routing.

This was one presentation of each request, with no baseline. The subjects could search all source guidance, beyond metadata normally exposed by a host. README and recipes were not included in the trial bundle, and no picker-metadata read was observed. The results do not demonstrate that the documentation or picker-description change improved discovery. No plugin was installed, global settings were unchanged, and Claude was not exercised.
