# pancake stack evals

i like what [pancake stack](https://github.com/j4ckwinter/pancake-stack) does for my workflow. i also want to know whether the instructions actually help.

this is where i test that. the checks, comparisons, misses, and inconclusive results live here.

## run the checks

use Python 3.12, matching the library's CI environment. from this repo, point the runner at your pancake stack checkout:

```sh
python3 -B run_checks.py --source ../pancake-stack --output /tmp/pancake-checks.json
```

the checks use temporary storage. they don't install the plugin or change global preferences.

the JSON result records both repos' commits, uncommitted changes, and file hashes, including nonignored untracked files. it also checks that neither tree changed during the run. if your checkout has uncommitted changes, the result covers those too.

CI uses a pinned evaluator. to reproduce that exact setup, follow the library's [verification recipe](https://github.com/j4ckwinter/pancake-stack/blob/main/docs/verification.md#run-the-checks). publish evaluator changes before advancing that pin.

## see what happened

each report keeps its methods, results, and limits together.

| report | what it looks at |
| --- | --- |
| [historical review](docs/historical-review.md) | a real regression, missed findings, and problems uncovered in the evaluator itself. |
| [context recovery](docs/context-recovery.md) | whether an agent can reconcile stale or accurate handoffs with the current repo. |
| [repository review](docs/repository-review.md) and [three-arm review](docs/review-comparison.md) | seeded defects and clean controls, with time and token use recorded separately from correctness. |
| [three-arm comparison](docs/three-arm-comparison.md) | baseline, Pancake, and the local Codex port of Poteto on two bounded tasks. |
| [validation controls](docs/validation-controls.md) | whether generated verification catches the intended failures. |
| [installed reviewer trials](docs/reviewer-consolidation.md) | default and requested reviewers in installed version 0.21.3. |
| [Design isolation](docs/design-isolation.md) | fresh candidate and judge contexts, with limits on inspecting their briefs. |
| [Codex refresh](docs/codex-refresh.md) | updating a local-checkout installation and checking its cached version and resources. |

## run a comparison

live trials need explicit authorization and a supported, authenticated Codex CLI. set `PANCAKE_STACK_SOURCE` to your library checkout's absolute path before using `tests/behavioral/compare.py`. use isolated profiles and bounded runs. keep raw output private and outside both repos.

start with the [evaluation procedure](docs/behavioral-evaluation.md) or the [historical review and context recovery protocol](docs/historical-context-coverage.md). live trials don't run as part of the package checks. plugin installation is a separate authorized action too.

## what this proves

passing checks tell us about the files and behavior they exercised. a small trial on one host and model doesn't establish a general success rate. a result tied to an older version stays tied to that version.

the helpers in `fixtures/legacy-0.19.3` test retired functionality. their passing results don't establish current plugin capabilities.

the [decision trail](docs/gap-pass.md) explains the latest corrections and unresolved limits. [earlier trial results](docs/behavioral-results.md), the [baseline comparison](docs/baseline-comparison.md), and the [library split record](docs/library-split.md) retain the older evidence and project history. commands in historical reports may need the explicit source setting described above.
