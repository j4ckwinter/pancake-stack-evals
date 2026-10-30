# Verify exact string persistence

Run from the directory containing `store.py` and `verify.py`:

```sh
TMPDIR=/tmp python3 -B verify.py
```

Requires Python 3 and writable temporary storage; validated with Python 3.9.6.
There are no third-party dependencies or services. The harness uses the same
Python executable for subprocesses, with `-B` to avoid bytecode writes.

| Supported entry point | Action and expected result | Observed status |
| --- | --- | --- |
| `save(path, value)` | Save each value, then call `load(path)` in a fresh process; exact equality | Passed |
| `python3 -B store.py PATH VALUE` | Invoke the CLI for each value; require exit 0, then read through `load(path)` in a fresh process; exact equality | Passed |
| `load(path)` | Read persisted strings in a new interpreter after each supported writer | Passed |

Both writer tests use a filename containing spaces and six literal values:
`receipt`, `replacement`, an empty string, leading/trailing spaces and a tab,
a multiline string, and Unicode with quotes and a backslash. Reusing the path
also checks overwriting previous content. Expected values come from the test
inputs, not the store's serialization logic.

Success prints both test names, `Ran 2 tests`, and `OK`, with exit status 0.
Each test covers six values; a failure names its input and reports the unequal
strings. Subprocess failure or a five-second timeout also fails verification.
To retain evidence, redirect stdout and stderr to a task-owned log outside
the disposable storage; preserve the command's exit status.

The harness creates temporary directories and removes them on normal success
and Python exception unwinding, including assertion failures. It starts no
services; subprocesses are bounded. Forced termination may leave temporary
storage: remove only directories confirmed to belong to that run.

## Detection evidence

On 2026-10-30, the original store passed both tests. A disposable copy changed
only `{'value': value}` in `save` to `{'value': value.strip()}`. Running the same
harness there exited 1 with two assertion failures, one for each writer:
`'padded' != '  padded\t '`. Other values remained valid. The broken copy was
removed and the original store passed again. This proves detection of that
representative data-corruption case, not all possible defects.

## Limits

The README's supported string persistence contract is the scope. Missing or
malformed files, invalid CLI arguments, non-string values, filesystem permission
errors, concurrency, atomicity, and crash durability have no documented outcome
here and are not covered. The CLI check invokes the current Python interpreter;
it does not verify installation, shell aliases, or alternate Python versions.
