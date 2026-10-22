# Natural requests with a skill catalog

All eight catalog-assisted tasks selected applicable guidance and completed their core task. Seven selected the expected primary skill. The captured PR-status task used Recap and correctly avoided PR drafting. The no-catalog controls also completed the core tasks, but one PR draft claimed an unobserved test execution. These observations support the current descriptions for these requests, not a general quality advantage or installed-host discovery claim.

The [runner](../tests/behavioral/routing_compare.py) gives subjects natural requests and either the complete source name/description/path catalog or no catalog. It does not ask subjects to select a route. The no-catalog arm receives no copied skill bundle. Existing explicit-entrypoint trials retain their prior prompt. [Case definitions](../tests/behavioral/routing_cases.py) keep expected routes and assessment criteria outside subject workspaces.

| Request | Catalog guidance observed | Core result in both arms |
| --- | --- | --- |
| Explain execution | How | Correct None and negative-value behavior |
| Explain rationale | Why | Local history supports compatibility decision |
| Repair invoice fields | Fix | Live amount records and archived total records work |
| Use test-first development | TDD | Meaningful failure before production edits, then five passing checks |
| Review a diff | Check | Signed-value regression identified |
| Challenge an assumption | Challenge | Concrete negative-value counterexamples |
| Draft a PR | PR | Describes actual changes and outstanding compatibility fix |
| Interpret captured PR status | Recap | Reports recorded blockers without claiming current remote status |

Both repair arms passed the independent artifact oracle. A fresh assessor reviewed task outputs, resulting files, and actions under neutral labels. Fifteen of sixteen overall outcome judgments passed, and all sixteen scope judgments passed. The failing no-catalog draft claimed that unittest ran and produced a specific error, although its actions only inspected files and the diff. Its core description was correct. The catalog Challenge run executed counterexamples, including the existing test input, but overstated this as running the existing test. That reporting flaw remains recorded separately from its correct substantive finding.

Actual returned skill contents establish the primary reads. Supporting-file reads can be truncated, so this is not a claim that every referenced instruction was fully loaded or followed. Both test-first records show test changes, relevant assertion failures or a consumer KeyError, production changes, and passing checks in that order. No subject contacted a remote service or changed protected project files. Requested delegation was disabled throughout these trials.

## Reproduce the comparison

Create a frozen source directory with `snapshot-origin.json`, as required by [the existing source comparison protocol](design-comparison.md). Run from the evaluator checkout with a Codex file authentication cache available:

```sh
PANCAKE_STACK_SOURCE=/path/to/pancake-stack python3 -B tests/behavioral/routing_compare.py --source /path/to/frozen-source --output /private/new-routing-records
```

The runner uses private profiles, removes copied credentials, bounds each trial at 240 seconds, freezes source and evaluator identities, and stops after invalid execution or scope mutation. Artifact failure remains distinct from execution validity. Raw records stay private. Review retained task actions and responses before assigning outcome, routing, or scope success.

The recorded run used a paired trace preflight, then three concurrent groups for the other seven pairs. Each group counterbalanced presentation order. Both preflight contexts exposed the same four built-in system skills and no host-injected Pancake skills. The catalog was supplied as task context. This does not test automatic host triggers, plugin installation, or a visible picker. Claude was not exercised.

All sixteen trials completed. No model or effort override was supplied; sessions reported gpt-6.1-sol with null effort. One observation per task and arm cannot establish repeatability or superiority. Concurrent execution makes elapsed times descriptive, not a performance comparison. The history fixture includes a handoff summary; actual Git-history evidence was still required and observed.

The initial assessment packet omitted commands that combined guidance reads and task inspection. Task actions were restored with guidance masked before the final judgment, clearing three evidence caveats. This corrected the packet, not the subject runs. Blinding is partial because outputs can reveal workflow choices. The [normalized evidence](evidence/metadata-routing-2026-10-22.json) retains exact input hashes, run judgments, complete entry-read observations, output hashes, and this limitation. The 140 package and evaluator checks passed with both inputs unchanged before the live run.

Retain the current skill descriptions. The trial adds observable routing and execution evidence; it does not justify more picker entries or additional workflow wording.
