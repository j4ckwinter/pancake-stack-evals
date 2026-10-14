# Codex checkout installation and refresh

On 14 October 2026, Codex CLI 0.160.0 installed Pancake Stack 0.21.6 from a local Git checkout, refreshed it to 0.21.7 after `git pull --ff-only`, and accepted a repeated install at 0.21.7. At every stage, the cached `plugin.json` and all skill resources matched the source hashes. The final plugin list reported 0.21.7 installed and enabled.

The trial cloned the public repository, placed a tracking branch at tag `v0.21.6`, registered the checkout once, and invoked `codex plugin add pancake-stack@pancake-stack --json`. Pulling the tracking branch advanced it to the public `main` revision for 0.21.7. Repeating the add command installed that version into its versioned cache. The documented verification block was then executed verbatim and read version 0.21.7 from the cached manifest.

All Codex commands used a new temporary `CODEX_HOME`. No default profile was selected and no existing installation was changed. This was an explicit installation experiment, separate from repository checks. It did not run a live model workflow or inspect a visible app picker. It tests a local checkout source, not the Git-marketplace upgrade route or every host/version combination.

[The evidence](evidence/codex-refresh-2026-10-14.json) retains commands, exit codes, outputs, exact source revisions, installed versions and source/cache hashes. Temporary paths are normalized to `<trial>`. The [library recipe](https://github.com/j4ckwinter/pancake-stack/blob/main/docs/codex-installation.md) provides the tested acquisition, refresh and version-check commands.
