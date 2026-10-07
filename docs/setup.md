# Set up Pancake Stack

Start a new chat after installing the package. Invoke `$pancake-stack:setup` in Codex or `/pancake-stack:setup` in Claude Code. Setup asks for a model and accepts model choices already supplied in your request. Role customization is optional. Leave a model unset to inherit its default, then the host model. Effort inherits from the host unless a task explicitly requests it. Setup does not save effort choices.

Installed CLI trials verified saving and reading preferences at explicit temporary paths and at the default path inside an isolated `CODEX_HOME`. The user has confirmed that setup loads in VS Code. Completing its visible VS Code selection flow remains unverified. See the [installation record](installation-verification.md).

Setup queries the active host's model metadata before asking you to choose. Codex uses its local app server; Claude Code uses initialization metadata without sending a model turn. If discovery fails, setup reports the reason and falls back to accessible host metadata or your host picker. A remote or overridden host can have different choices. Setup saves your choices without changing the current conversation or global host settings.

Saved model choices apply to delegates and reviewer panels. Direct work stays on your current host settings without running the preference helper. Roles are resolved when preparing delegates that can use them; saved panels are read at review time, including when model selection is unavailable. An explicit task model replaces the corresponding saved choice without a saved lookup. A task can request effort for that invocation only.

## Run the preference helper

Inspect the local model catalog without writing preferences:

```sh
python3 skills/setup/scripts/catalog.py
```

For Claude Code, use `python3 skills/setup/scripts/catalog.py --host claude`. `--claude <executable-path>` selects an observable executable outside PATH. The returned choices describe CLI metadata, not proof of account access or delegated settings. Missing effort metadata remains undiscovered.

The Codex adapter uses the [app server protocol](https://learn.chatgpt.com/docs/app-server) and follows catalog pagination. Both adapters stop discovery after 15 seconds. `--codex` selects an explicit Codex executable path. Discovery failures exit with code `2`.

Use Python 3.8 or later. From the repository root, inspect preferences with:

```sh
python3 skills/setup/scripts/preferences.py show
```

In Claude Code, add `--host claude` before every preference subcommand. The same save and resolution commands apply, using Claude-owned storage. The configuration and inheritance rules are shared; no preferences move between hosts automatically.

Schemas 1, 2, and 3 remain readable without migration. Reads leave existing files unchanged. Setup preserves stored effort and unrelated choices when editing models, and uses `null` effort for new entries. Legacy effort remains stored but no longer controls delegates. Resolution prints one disclosure to stderr when it encounters nonnull saved effort.

Save a complete preference object through stdin. This command writes user preferences:

```sh
python3 skills/setup/scripts/preferences.py save < config/preferences.example.json
```

Resolve preferences against observable host values:

```sh
python3 skills/setup/scripts/preferences.py resolve --host-model MODEL_ID --host-reasoning-effort EFFORT
```

Replace the placeholders with values from your host. Resolve does not apply the result. Its effort field reports the supplied host value or `null`. Leave delegate effort unset unless the task explicitly requests an override. See the [configuration contract](configuration.md) for inheritance and validation rules.

## Verify without changing user preferences

Run the automated helper and fixture-support tests from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

The preference tests pass explicit temporary paths to every helper invocation. Catalog tests use a temporary fake app server to check pagination, notifications, timeouts, malformed responses, and unavailable executables. The tests do not install a plugin or write to user preference storage.

Use the [behavioral evaluation procedure](behavioral-evaluation.md) to exercise workflows on the fixtures under `tests/behavioral`. Automated fixture checks do not establish how an agent follows a skill or how the host invokes it. Keep those claims tied to workflow trials and the [installation record](installation-verification.md).

## Configure Challenge reviewers

Ask `$pancake-stack:setup` to configure a Challenge reviewer panel. Setup uses the discovered catalog, accepts already supplied choices, and guides one reviewer at a time. Ordinary setup does not ask about or change the panel. Existing panels survive default and role edits.

Saving a Challenge panel on schema 1 explicitly opts into schema 2, which older installed helpers cannot read. Setup preserves schema 3 when already present. Clearing the list restores the existing review fallback while retaining the loaded schema. The [panel example](https://github.com/j4ckwinter/pancake-stack/blob/795dc890ee0b0acf24e743d82362c4a92e4202e1/config/challenge-panel.example.json) demonstrates two inherited entries, not distinct model choices. Replace those fields through setup with supported choices before expecting model diversity.

Inspect effective reviewer requests without changing preferences:

```sh
python3 skills/setup/scripts/preferences.py resolve-challenge --host-model MODEL_ID --host-reasoning-effort EFFORT
```

Replace the placeholders with observable host values. The result does not prove that delegated model selection works. Challenge reports requested settings, actual selections, and unavailable perspectives when it runs.

## Configure consequential implementation reviewers

Ask `$pancake-stack:setup` to configure a consequential implementation reviewer panel. Setup accepts supplied choices or guides one reviewer at a time using the discovered catalog. It preserves default and role choices and the Challenge panel. Ordinary setup does not ask about this panel.

Saving an implementation panel explicitly opts into schema 3, which older installed helpers cannot read. Clearing it retains schema 3 and restores the single independent reviewer for consequential work. The [implementation example](https://github.com/j4ckwinter/pancake-stack/blob/795dc890ee0b0acf24e743d82362c4a92e4202e1/config/implementation-panel.example.json) illustrates two inherited entries. Select distinct supported models to request model diversity. Local, low-impact changes keep direct review.

Inspect effective implementation reviewer requests without changing preferences:

```sh
python3 skills/setup/scripts/preferences.py resolve-implementation-review --host-model MODEL_ID --host-reasoning-effort EFFORT
```

Replace the placeholders with observable host values. These are resolved preferences, not proof of applied model settings. The implementation workflow reports completed independent reviews, actual settings, and unavailable perspectives.
