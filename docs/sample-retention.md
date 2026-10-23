# Preserve successive measurement batches

The evaluator now supplies a collision-safe recorder for a separate retention task. Each batch owns a newly created directory. Metadata and sample files use exclusive creation; each sample is serialized before writing and flushed before returning. Normal completion records the sample count. Exceptions or process termination preserve the flushed prefix without a completion marker.

The historical three experiment cases and six-trial comparison remain unchanged. `RETENTION_CASE` adds a protected copy of the recorder and explicitly asks for two batches. Its assessment reports retention separately from manual performance judgment. It rejects malformed or unterminated records, duplicate/nonfinite JSON values, missing metadata, incorrect completion counts, and scope changes. This is a fixture facility in the evaluator, not a plugin executable or universal skill requirement.

## Verification

A fresh isolated source-skill trial completed two batches of 80 samples each. Both timed complete imports and checked every output against independently constructed expected hashes. The result correctly declined a supported speedup. The lead inspected the generated measurement code and all 160 records. Repeating the actual generated command against batch-01 raised FileExistsError and preserved every workspace file byte-for-byte.

All 171 package and regression checks passed with unchanged inputs before the final serializer correction. Independent review found an ambiguous-key consistency issue: Python could serialize integer and string keys to duplicate JSON names. The recorder now rejects that output before writing. Seventeen focused recorder and historical-experiment tests passed after the correction, including a killed writer, collision preservation, nested duplicate keys, cycles, invalid completion markers, and preservation of protected fixture files. The live trial predates this narrow validation correction; it used ordinary string keys.

Run the focused checks from the evaluator checkout:

```sh
PANCAKE_STACK_SOURCE=/path/to/pancake-stack PYTHONPATH=tests python3 -B -m unittest test_sample_store test_experiment_comparison
```

The opt-in live adapter is `behavioral.experiment_cases.RETENTION_CASE`, using the existing `run_trial` with a frozen source bundle, private isolated profile, a 240-second bound, and no model or effort override. [Normalized evidence](evidence/sample-retention-2026-10-23.json) retains source identities, artifact hashes, retention counts, and the collision check. Raw sessions and samples remain private.

## Limits

This prevents accidental overwrite through the supported recorder. A candidate can bypass it or deliberately alter writable artifacts. Flush does not promise durability through machine or storage failure. This single explicitly instructed run does not establish spontaneous recorder use, generalized retention, installed behavior, model diversity, or a performance improvement. The earlier lost-sample report remains unchanged.
