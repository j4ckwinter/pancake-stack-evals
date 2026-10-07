# Claude Code support

Pancake Stack 0.19.0 packages the same 19 workflows for Codex and Claude Code. The hosts share `skills/`, including the core values, implementation sequence, independent review requirements, test-first cycle, and verification rules. The native Claude manifests are in `.claude-plugin/`. The portable manifest and Codex marketplace remain available.

## Use Pancake in Claude Code

From the repository root, load the plugin for one session:

```sh
claude --plugin-dir .
```

Start with a read-only task:

> /pancake-stack:how Explain how this project starts and where its main behavior lives. Keep this read-only and cite the implementation.

Use `/pancake-stack:pancake` for implementation, `/pancake-stack:design` for a proposal, and `/pancake-stack:setup` for optional saved preferences. Other workflow names match the [skill list](https://github.com/j4ckwinter/pancake-stack/blob/795dc890ee0b0acf24e743d82362c4a92e4202e1/README.md). Replace the Codex `$` prefix in [prompt recipes](recipes.md) with `/`.

The local marketplace flow uses Claude Code's native shell commands:

```sh
claude plugin marketplace add .
claude plugin install pancake-stack@pancake-stack
```

This local flow passed in a temporary Claude configuration directory on 6 October 2026. Git-backed distribution remains a separate host check. This local source does not publish the changes or make them available from remote main.

## Configure the active host

Setup discovers model choices before asking you to select a model. It does not offer saved effort choices. The Claude adapter asks the local CLI for initialization metadata without a user message or model turn. It preserves the returned aliases and effort choices. Empty effort metadata remains undiscovered. Discovery failure falls back to observable active-host metadata or your picker. CLI metadata does not prove account access or that a worker applies a setting.

The preference object keeps schemas 1, 2, and 3 unchanged. Roles and both reviewer panels inherit models through their defaults. Effort inherits from the host unless explicitly requested for a task. Existing saved effort remains stored but inactive, and resolution discloses nonnull legacy effort once on stderr. Reads do not migrate or rewrite files. Setup preserves existing effort and unrelated choices when editing models. New entries use `null` effort. Claude Code uses `$CLAUDE_CONFIG_DIR/pancake-stack/config.json`, defaulting to `~/.claude/pancake-stack/config.json`. Codex uses its existing separate location. Models are opaque host requests; Pancake does not translate GPT names into Claude names or read another provider's file as a fallback.

To inspect Claude preferences from the repository:

```sh
python3 skills/setup/scripts/preferences.py --host claude show
```

The flag precedes every preference subcommand. Explicit `--config` overrides either default path. Saving model choices configures future delegates and reviewer panels. Direct work uses current host settings without a preference lookup; saved panels are discovered at review time. Saving preferences leaves the current chat and global host settings unchanged. See the [configuration contract](configuration.md).

## Delegate with the same review requirements

Challenge and consequential implementation review retain separate optional panels. Each selected entry needs its own identified, completed verdict. Competing Design retains independent authors and a separate judge. Missing or unsupported selections remain coverage gaps. Small local changes keep proportional direct review.

Claude Code's Agent interface differs from Codex collaboration. The workflow uses the actual exposed selection controls and reports requested versus observed model and effort separately. Catalog support alone cannot establish per-worker application. If the host substitutes a model or cannot apply an explicit effort, that difference must be disclosed. The shared workflow rules do not promise identical model output or unexposed capabilities.

## Verification scope

On 6 October 2026, Claude Code 2.1.291 validated both native manifests with `--strict`, installed the local marketplace package in an isolated profile, and initialized a session that listed all 19 unique namespaced skills from the shared tree. Its model metadata was read without authentication or a model turn. Repository tests exercise both manifests, shared metadata, source resolution, isolated host preferences, and discovery failure handling.

The existing Codex installation flow also installed 0.19.0 in a fresh temporary profile. An authenticated installed How task returned a correct source-cited explanation and disclosed static-only inspection. Parent artifact checks passed and confirmed file preservation. See the [host evidence](evidence/claude-support-2026-10-06.json).

Authenticated How, Fix, Check, Setup conversation flow, reviewer panels, and competing Design remain pending because this environment has no Claude authentication. Structural checks and skill discovery do not establish those behaviors. Applied per-worker effort and model selection remain separate gates. Codex's existing discovery and preference tests continue to run.

The [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference) defines native packaging. [Claude environment variables](https://code.claude.com/docs/en/env-vars) define `CLAUDE_CONFIG_DIR`. [Subagent guidance](https://code.claude.com/docs/en/sub-agents) describes model and effort selection. Runtime verification uses the installed host rather than assuming current documentation applies to every older client.
