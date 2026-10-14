# Pancake Stack evaluations

This repository owns package checks, behavioral fixtures, live trial tools, and historical evidence for Pancake Stack. It was cloned from source commit `795dc890ee0b0acf24e743d82362c4a92e4202e1`, preserving the original Git history. It is hosted at [j4ckwinter/pancake-stack-evals](https://github.com/j4ckwinter/pancake-stack-evals).

## Run checks

Use Python 3.12, matching the library CI environment. From this repository, supply the library checkout explicitly:

```sh
python3 -B run_checks.py --source ../pancake-stack --output /tmp/pancake-checks.json
```

The runner checks the current working tree. Its JSON record identifies the library and evaluator commits, dirty state, and file hashes, including nonignored untracked files. It also verifies that the checks did not change either tree. A dirty-tree result is not a verdict on the commit alone. Tests use temporary storage and do not install the plugin or change global preferences.

The `fixtures/legacy-0.19.3` helpers preserve tests of retired functionality. Their passing results describe those historical helpers, not current library capabilities.

## Live evaluations

Live runs require explicit authorization and a supported authenticated Codex CLI. Set `PANCAKE_STACK_SOURCE` to the absolute library checkout before invoking `tests/behavioral/compare.py`. Keep raw output outside both repositories. The runner records both revisions, dirty state, and source hashes. It never runs during unit-test discovery.

The [evaluation procedure](docs/behavioral-evaluation.md), [trial results](docs/behavioral-results.md), and [baseline comparison](docs/baseline-comparison.md) retain historical methods and outcomes. Documentation copied from the library describes the versions named in those records; old repository-relative commands may require the explicit source setting above. Existing evidence has not been relabeled as verification of the simplified library.

## Current evidence

The [three-arm pilot](docs/three-arm-comparison.md) compares baseline, Pancake, and the local Codex port of Poteto on two bounded tasks. The [installed reviewer trials](docs/reviewer-consolidation.md) exercise the consolidated rules in version 0.21.3. Each report records scope and limitations; neither establishes general success rates.

The [three-arm review pilot](docs/review-comparison.md) adds configuration and resource-lifetime defects with matched clean controls. All 12 runs completed, with no missed seeded defects or unsupported actionable findings. Unnecessary work is adjudicated separately from cost. The one-repetition pilot does not establish general quality or repeatability.

The [repository review pilot](docs/repository-review.md) covers repository-derived identity and trace defects. The [validation controls](docs/validation-controls.md) separate successful verification from missing or failed evidence. The [historical review and context recovery protocol](docs/historical-context-coverage.md) declares paired historical-regression and stale/fresh-handoff suites without claiming trial outcomes.

## Automation

The library's [package workflow](https://github.com/j4ckwinter/pancake-stack/blob/main/.github/workflows/checks.yml) checks out a pinned published evaluator alongside the target library. The current check count is reported by `run_checks.py`. Publish evaluator changes before advancing the library's pin; do not pin a commit GitHub cannot fetch.

Hosted checks [passed at library revision `1405ff6`](https://github.com/j4ckwinter/pancake-stack/actions/runs/37963572728) with the older 70-check evaluator. Consult the workflow's pin and [Actions results](https://github.com/j4ckwinter/pancake-stack/actions) for later coverage. The runner records both repository identities and checks for mutations. Live model trials and plugin installation remain separate authorized operations.
