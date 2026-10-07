# Configuration contract

[The example](https://github.com/j4ckwinter/pancake-stack/blob/795dc890ee0b0acf24e743d82362c4a92e4202e1/config/preferences.example.json) has `schemaVersion` equal to the integer `1`. `defaults` contains `model` and `reasoningEffort`. `roles` contains `implementation`, `review`, and `research`, each with the same two fields. All fields are required. Extra fields, duplicate JSON keys, and unsupported schema versions are rejected.

A role model of `null` inherits the default model. A default model of `null` inherits the supplied host model. An unavailable host model remains `null` in resolved output. Saved `reasoningEffort` values remain valid storage fields but do not affect resolution or delegation. Resolved effort is the supplied `--host-reasoning-effort` value or `null`.

An explicit `model` or `reasoningEffort` is a nonempty trimmed string. The preference helper validates the structure, not account availability or model and effort compatibility. Setup first runs the bundled catalog helper for the active host. Codex uses its local app server; Claude Code uses CLI initialization metadata. If discovery fails, Setup uses accessible host metadata or the user's host picker. Setup offers model choices only. Delegate effort inherits from the host unless explicitly requested for the task.

An explicit task effort is transient and does not enforce a numeric token budget. Saving preferences does not change the parent conversation's model or global host configuration. Direct work uses current host settings without a saved preference lookup. Saved roles are resolved when preparing delegates with supported model selection. Challenge and consequential implementation review read saved panels at review time because panel size also determines reviewer count. An explicit task model bypasses the saved lookup and inherits host effort unless the task requests effort separately. An omitted or `null` task model can use the saved role model. Setup and explicit preference inspection can run the helper directly.

User storage is `$CODEX_HOME/pancake-stack/config.json`. When `CODEX_HOME` is unset or empty, the path is `~/.codex/pancake-stack/config.json`. Project overrides are deferred. The helper's `--config` flag selects an explicit file path for isolated checks or a user-requested location.

With `--host claude` before the subcommand, storage is `$CLAUDE_CONFIG_DIR/pancake-stack/config.json`, defaulting to `~/.claude/pancake-stack/config.json`. Unqualified commands retain the Codex default. Host selection is not a saved field and does not change schema 1, 2, or 3. The helper never reads the other host as a fallback or translates model names. Explicit `--config` takes precedence for both hosts. See [Claude Code support](claude.md).

`show` returns the complete configuration. A missing file returns the all-null object without creating directories. `save` accepts the complete JSON object on stdin and atomically replaces the preference file. It refuses to overwrite a malformed or unsupported existing configuration. Repeated saves converge to the same content. Concurrent setup sessions use the last completed save, so finish one setup session before starting another.

`resolve` returns effective preferences by role with the existing `model` and `reasoningEffort` output keys. Optional `--host-model` and `--host-reasoning-effort` arguments provide observable host values. The returned effort is informational. Delegation leaves effort unset unless explicitly requested for the task. Resolve reads without writing or applying preferences. Validation and filesystem failures print an error to stderr and exit with code `2`.

Schemas 1, 2, and 3 remain supported without automatic migration. Reads leave files unchanged. Setup preserves legacy effort and unrelated choices when editing model selections. New entries use `null` effort. Each resolution command prints one disclosure to stderr when any nonnull saved effort is present, explaining that the value remains stored but no longer controls delegation.

See [Set up Pancake Stack](setup.md) for invocation and helper usage.

## Optional Challenge reviewer panel

Schema 1 stays supported with its existing fields and output shape. Schema 2 adds the required `challengeReviewers` list. Each entry contains exactly `model` and `reasoningEffort`, with the same nullable trimmed string rules. A reviewer model inherits through the review role, defaults, then the supplied host model. Effort comes only from the supplied host value or remains `null`. An empty list returns one effective review pair. `resolve` still returns only the three existing roles.

[The panel example](https://github.com/j4ckwinter/pancake-stack/blob/795dc890ee0b0acf24e743d82362c4a92e4202e1/config/challenge-panel.example.json) contains two all-null entries to demonstrate the shape. These resolve to the same settings and do not demonstrate model diversity. Select distinct model IDs supported by your active host to request diversity. Duplicate model choices remain valid independent perspectives. Resolution preserves each entry and the panel count.

`resolve-challenge` returns a list of effective reviewer pairs. It accepts the same optional host arguments as `resolve` and never writes or applies preferences. Missing storage returns one inherited review pair without creating directories. Schema 1 and an empty Challenge panel in schema 2 or 3 use the same fallback.

Selecting a saved Challenge panel on schema 1 explicitly opts into schema 2. Setup preserves schema 3 when already present, and Challenge reads its own panel from either schema 2 or 3. Older installed helpers reject unsupported schemas. Update the installed plugin before opting in; ordinary setup preserves the loaded version and panels without automatic migration. Clearing the Challenge list retains the loaded version and restores the single review fallback.

Only Challenge consumes the panel. Task-supplied reviewer choices replace it for that task without persistence. With delegation available, Challenge launches one reviewer per selected entry, queues host limits, and awaits verdicts. Unsupported or failed choices remain uncovered and must be reported. Model IDs and explicit task efforts must be supported by the actual delegation host, not merely the catalog server. Distinct completed model IDs establish model diversity; they do not by themselves establish provider diversity.

## Optional consequential implementation reviewer panel

Schema 3 retains the exact defaults, roles, and Challenge panel fields and adds the required `implementationReviewers` list. Each entry contains exactly `model` and `reasoningEffort`. Nullable models inherit through review, defaults, then the supplied host model. Effort comes only from the supplied host value or remains `null`. Schema 1 and 2 remain supported without migration. `resolve` and `resolve-challenge` keep their existing output shapes.

[The implementation panel example](https://github.com/j4ckwinter/pancake-stack/blob/795dc890ee0b0acf24e743d82362c4a92e4202e1/config/implementation-panel.example.json) uses two all-null entries. They resolve to the same settings and request independent reviews without demonstrating model diversity. Duplicate entries remain separate reviewers. Choose distinct models supported by the actual delegation host to request diversity.

`resolve-implementation-review` returns effective implementation reviewer pairs without writing or applying preferences. Missing storage, schema 1 or 2, and an empty schema 3 list return one inherited review pair. Reading missing storage does not create directories. Challenge and implementation panels resolve independently.

Explicit implementation panel setup opts into schema 3. Older helpers reject that version. Update the installed plugin before opting in. Setup preserves defaults, roles, and existing Challenge choices, adding an empty Challenge list when upgrading schema 1. Ordinary setup preserves the loaded version and both panels. Clearing the implementation list retains schema 3.

Only consequential implementation review consumes this panel. Small local changes keep proportional direct review. With working, permitted delegation, consequential work launches one independent read-only reviewer per selected entry, or the existing single reviewer when the panel is absent or empty. Task choices replace the implementation panel for that task without persistence. All reviewers receive the same neutral snapshot and brief. Their completed evidence informs the lead's verdict rather than a vote. Requested and actual model settings must be distinguished, and unsupported or failed entries remain explicit coverage gaps. Different completed actual model IDs establish model diversity, not necessarily provider diversity.
