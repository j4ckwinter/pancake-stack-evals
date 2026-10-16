# Bounded Design extraction pilot

`tests/behavioral/design_compare.py` reuses the existing isolated comparison runner.
Supply two frozen source directories, each containing `snapshot-origin.json` with
its original revision and dirty-state identity. Every input file is hashed; input
drift stops the batch. Source snapshots and raw results stay private outside both
repositories. This is a source-guidance trial, not installed-host validation.

The five natural requests cover an ordinary optional interface, input validation,
persisted-record migration, retry/shared ownership, and explicitly requested
independent competing designs. Candidate workspaces contain only small relevant
Python modules and, for migration, a stored record. Candidate prompts contain no
rubric, expected architecture, comparison labels or assessment results. Private
`design.RUBRIC` and per-run `judge.json` packets guide later human or independent
assessment. Neutral run paths conceal arm labels, though source guidance can reveal
identity. Filesystem separation is not a security boundary.

Run only with live usage authorized and after freezing inputs:

```sh
PANCAKE_STACK_SOURCE=../pancake-stack python3 -B tests/behavioral/design_compare.py \
  --baseline /private/tmp/frozen-before --candidate /private/tmp/frozen-after \
  --output /private/tmp/new-design-results --timeout 300
```

One trial per case and arm means ten sequential runs, at most 34 minutes of
candidate execution (180 seconds for ordinary cases, 300 for independent designs). Order alternates by case. There are no model or effort
overrides: isolated Codex CLI defaults apply, and actual session selections are
recorded. They do not necessarily equal the parent host's selections. Four threads
permit the explicit two-proposal and separate-judge task. Worker prompts request inherited settings. The runner does not install plugins,
change global configuration, or copy personal history.
Authentication is copied privately and removed even on launch failure or timeout.

Review actual successful source/project reads and paired tool outputs, completed
linked workers, proposals and final responses. Fresh-context calls and host
acceptance establish observed isolation; encrypted briefs or missing internals
remain unavailable. Inspect judge ordering and actual comparison content. Do not
infer adherence from the final response alone. Record unsupported claims and
unnecessary work with evidence. A longer response or higher cost is not inherently
unnecessary. Preserve each failed or unavailable criterion. Report elapsed time,
all-session token usage, usage gaps, actual settings and unchanged project files
separately from quality. Proposed runtime checks are not executed behavior.

For the existing legitimate-structural-variant regression and calibrated clean
control, add `--cases migration-faulty migration-clean`. This reuses the pinned
historical fixture and its existing trusted tests, with Pancake review entrypoints
and delegation disabled in both arms. Apply `historical_review.CASES` and the
existing reviewer mechanism rubric: detect rejection of valid shared modules and
behavior-preserving facade/docs changes, count unsupported clean-control findings,
and keep calibration distinct from historical evidence. These are review outcomes,
not additional Design outcomes.

One sample per case and arm is a bounded smoke comparison, not a causal or general
effectiveness estimate. Keep raw records private; publish only inspected sanitized
findings and exact hashes. Do not describe a favorable cost sample as a proven gain.

A separate final-source routing check can use `--candidate-only --cases independent
--entrypoint parallel-work`. Its manifest identifies it separately; do not pool it
with the paired Design comparison. Continuation requires unchanged inputs and
workspace, unchanged preferences, no timeout, zero exit status, a nonempty final response and a completed
root session. Invalid trials remain in results and stop the batch.
