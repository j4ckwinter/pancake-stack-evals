# Repository review source

`source.tar.gz` contains the complete Git archive of evaluator commit
`d81ad93f3195d5164a305b79e504c44e16001b51`. `provenance.json` records its origin,
compressed archive SHA-256, and SHA-256 for each of its 122 regular files.
Tests and trials use these vendored bytes. They require neither old Git objects
nor network access, including in shallow CI checkouts.

The archive was produced from the named commit with `git archive --format=tar`,
then compressed with Python `gzip.compress(archive_bytes, mtime=0)`. File contents
and paths are preserved. The extractor checks the archive hash, rejects links
and unsafe paths, and checks every file hash before creating the workspace.

The evaluator applies one seeded refactor to each extracted copy. Clean and
faulty changes affect either symlink handling in `run_checks.py` or turn reset in
`tests/behavioral/traces.py`. These are new mutations of real repository code,
not claims about historical bugs. Case identities, probes, provenance metadata,
and expected findings stay outside the candidate workspace. Original names and
evaluation terminology remain in the archived source, so blinding is partial.
