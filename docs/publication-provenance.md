# Evidence publication provenance

Before publication, five local commits were rewritten to follow the public evidence allowlist in [workflow comparison](workflow-comparison.md). Public records retain trial revisions, relative file hashes, selected reads, timing, token counts, and aggregate judgments. Full prompts, transcripts, private paths, session identities, and detailed audit packets remain in private storage.

The recorded trial revisions below identify the actual executions. They were not silently replaced with publication revisions. The original local commits are not published or expected to resolve on GitHub. Their equivalents change only report/evidence publication; comparison of every pair confirmed identical `tests/`, `fixtures/`, and `run_checks.py` contents. Trial input file hashes remain the authority for the original dirty or clean snapshots.

| Original local evaluator revision | Published equivalent | Harness and fixtures |
| --- | --- | --- |
| `08d6e9241a79603ecbad157ad8c876b53ce9682d` | `51b4957ccca45d81d2f6d8156a3042504f8f7679` | Identical |
| `edf9f0e2a1c5eac3bc5b1bd9e08308a09444edce` | `d9e1c8c7c6b71a7c7e3e825f0eda4e3a39c668a8` | Identical |
| `5535a0a2b5df61a2f06258a6d73bdd87a7e378c8` | `3e280e2eb873c70167f08164d1f34cb755b63739` | Identical |
| `6fe0e1b709c5f13f10c80450d523d4a3eeb7bd7d` | `17b6913a7f3e9b7c5793bfc75160c29d92535651` | Identical |
| `3e199e4e9d82e213a1e3a1dba6496a2f4e0ebc7c` | `263b37d672f5b9223bcd59468764b4861a6af207` | Identical |

The first historical trials used `afb9203cf33dec23f200e4985f0b39b933522a4e`, which predates this rewrite and remains unchanged. The final package check uses the published evaluator lineage and the final library files. Publication summaries cannot independently reproduce private reviewer-identity or command-order audits. Those limitations remain explicit in each report.
