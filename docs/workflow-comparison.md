# Focused workflow comparisons

`tests/behavioral/workflow_compare.py` compares two frozen source directories. Each must contain the skills, `docs/configuration.md`, and `snapshot-origin.json` recording the source revision and dirty state. The manifest records file hashes, evaluator identity, CLI version and trial order. Input changes stop the batch. The runner copies and verifies each skill bundle.

Run only after live-trial authorization. For example, from this repository:

```sh
python3 tests/behavioral/workflow_compare.py --baseline /private/baseline --candidate /private/candidate --output /private/trial-records
```

The output directory must be new and outside all inputs. Trials use temporary private profiles, inherited CLI model defaults, disabled delegation, and a 180-second default timeout. Limits are 600 seconds per trial and three repetitions. Authentication is copied for execution and removed before sessions are retained. No plugin is installed and no global settings are changed.

`small-refactor` asks for a small behavior-preserving implementation change. Its fixed assessor checks numeric edge cases, the existing test, an actual implementation change, and preservation of unrelated files. Assessment runs in the CLI read-only sandbox. Ordinary, comment, and suppression reviews each have a clean and a problematic fixture. Review workspaces must remain unchanged. Private judgment packets describe expected findings; automated preservation is not a review-quality verdict.

Both source variants run every selected case in alternating order. Behavioral failure remains recorded and does not suppress the counterpart. Invalid execution, missing completion, changed inputs, or scope mutation stops the batch.

Audit raw session calls and their completed outputs manually. For refactoring, establish a successful existing check before the first edit and after the last edit. For reference usage, record successful content reads with relative bundle paths and any line ranges. A command mentioning a path, a failed command, or a filename listing is not a successful content read. Keep ambiguous shell commands marked unknown. The records do not establish exhaustive filesystem access.

Raw prompts, workspaces, sessions and outputs remain private. Publish only explicitly selected case and variant identifiers, source/evaluator hashes and revisions, aggregate quality judgments, relative successful read paths and ranges, timings, and token counts. Exclude transcripts, absolute paths, session/account identifiers and credentials. Describe manual uncertainty and incomplete pairs. Unit checks use isolated fixtures and mocked CLI launch; they do not establish live model behavior.
