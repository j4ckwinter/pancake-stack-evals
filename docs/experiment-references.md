# Selective experiment references

Retain the selective reference split. All six task outcomes passed in the paired comparison, protected files were preserved, and the split returned less complete guidance in each pair. Shared framing, baseline, decision, and cleanup rules remain together. Performance, prototype, and skill-evaluation instructions move verbatim into three conditional references. No skill or picker entry is added.

The shared reference falls from 1,044 to 427 whitespace-separated words. The complete split contains 1,070 words, including its navigation text. The decision rests on observed reading paths, not entry length alone.

| Task | Original complete guidance words | Selective complete guidance words | Outcome in both arms |
| --- | --- | --- | --- |
| Performance | 2,893 | 2,610 | Corrected lazy-work timing, checked completed work, repeated measurements, no unsupported speedup |
| Prototype | 2,893 | 2,378 | Exercised both approaches on successful and failing batches; identified atomicity violation |
| Skill evaluation | 3,714 | 2,056 | Checked supplied artifacts, detected incorrect code and scope violation, limited the conclusion |

Counts include every complete returned skill or reference, supporting guidance, and repeated returns. They are derived from raw session tool outputs matched against exact source text, not command intentions or CLI event summaries. All six runs returned shared experiment guidance; selective runs also returned the applicable branch. No guidance-output truncation was observed. This measures supplied guidance words, not total context, tokens, execution speed, or model quality.

The original skill-evaluation run additionally read Check and Verify, totaling 1,248 words. That incidental difference accounts for most of its reading reduction; this single pair cannot establish that the split caused those reads to disappear. The direct branch reductions are 283 performance words, 515 prototype words, and 410 skill-evaluation words. The extra navigation step was exercised successfully in all three selective runs.

The [cases](../tests/behavioral/experiment_cases.py) use a lazy importer benchmark, two duplicate-handling prototypes, and explicitly synthetic workflow artifacts. Ordinary requests do not reveal hidden expected outcomes. Subjects may add evidence only under `scratch/run`; existing files, including unrelated scratch notes, are protected. The guard excludes bytecode caches and empty directories, so preservation is not proof of zero filesystem side effects. No subjects were launched by the skill-evaluation candidates.

The [runner](../tests/behavioral/experiment_compare.py) validates the exact extraction and unchanged source/evaluator identities. Run from the evaluator checkout with Codex file authentication available:

```sh
PANCAKE_STACK_SOURCE=/path/to/pancake-stack python3 -B tests/behavioral/experiment_compare.py --current /path/to/frozen-current --selective /path/to/frozen-selective --output /private/new-experiment-records
```

Six sequential trials completed within 240-second bounds, with order counterbalanced across cases and no model or effort override. Sessions reported gpt-6.1-sol with null effort. Independent same-model assessment used neutral packets with guidance bodies masked; outputs can still disclose workflow choices, so blinding is partial. The [normalized evidence](evidence/experiment-references-2026-10-22.json) retains exact inputs, per-run reads, outcomes, hashes, and limits. Raw records remain private.

One selective performance candidate overwrote its first batch of raw samples when repeating its measurements. The tool record retains the first summary, and the second batch retains raw samples. The assessor treated that as a nonblocking evidence limitation, not complete sample retention.

Six fixture/runner tests passed before these trials. Independent code review passed before launch. One observation per mode and variant supports this bounded extraction decision, not repeatability or broad efficacy. Installation, native discovery, and Claude workflows were not exercised.
