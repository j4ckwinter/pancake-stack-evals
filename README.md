# Pancake Stack evaluations

This local repository owns package checks, behavioral fixtures, live trial tools, and historical evidence for Pancake Stack. It was cloned from source commit `795dc890ee0b0acf24e743d82362c4a92e4202e1`, preserving the original Git history. No remote is configured.

## Run checks

Use Python 3.12, matching the former CI environment. From this repository, supply the library checkout explicitly:

```sh
python3 -B run_checks.py --source ../pancake-stack --output /tmp/pancake-checks.json
```

The runner checks the current working tree. Its JSON record identifies the library and evaluator commits, dirty state, and file hashes, including nonignored untracked files. It also verifies that the checks did not change either tree. A dirty-tree result is not a verdict on the commit alone. Tests use temporary storage and do not install the plugin or change global preferences.

The `fixtures/legacy-0.19.3` helpers preserve tests of retired functionality. Their passing results describe those historical helpers, not current library capabilities.

## Live evaluations

Live runs require explicit authorization and a supported authenticated Codex CLI. Set `PANCAKE_STACK_SOURCE` to the absolute library checkout before invoking `tests/behavioral/compare.py`. Keep raw output outside both repositories. The runner records both revisions, dirty state, and source hashes. It never runs during unit-test discovery.

The [evaluation procedure](docs/behavioral-evaluation.md), [trial results](docs/behavioral-results.md), and [baseline comparison](docs/baseline-comparison.md) retain historical methods and outcomes. Documentation copied from the library describes the versions named in those records; old repository-relative commands may require the explicit source setting above. Existing evidence has not been relabeled as verification of the simplified library.

## Automation

GitHub cannot fetch this local-only repository. The library's old in-repository test workflow must be removed when its tests move. Once a remote is authorized, its workflow can check out a pinned evaluator commit alongside the library and run the command above. Private repository access requires separately configured credentials. Do not add a workflow pointing to a nonexistent remote.
