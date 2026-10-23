"""Fixture recorder for separate, collision-safe experiment batches.

Use ``with BatchRecorder(new_directory, metadata) as batch: batch.record(sample)``.
Metadata and samples are JSON objects. Each successful record is flushed before
returning. A normal exit writes complete.json with the recorded sample count;
an interrupted batch retains its prefix without claiming completion. Flush does
not guarantee survival of machine or storage failure. Never reuse a directory.
"""
import json
from pathlib import Path


def _serialize(value):
    if not isinstance(value, dict):
        raise TypeError('metadata and samples must be JSON objects')
    def unique_keys(pairs):
        keys = [key for key, _ in pairs]
        if len(keys) != len(set(keys)):
            raise ValueError('ambiguous serialized JSON object keys')
        return dict(pairs)

    serialized = json.dumps(value, allow_nan=False)
    json.loads(serialized, object_pairs_hook=unique_keys)
    return serialized + '\n'


class BatchRecorder:
    def __init__(self, directory, metadata):
        self.directory = Path(directory)
        self._metadata = _serialize(metadata)
        self._stream = None
        self._entered = False
        self._count = 0

    def __enter__(self):
        if self._entered:
            raise RuntimeError('recorder already entered')
        self._entered = True
        self.directory.mkdir(parents=True, exist_ok=False)
        with (self.directory / 'metadata.json').open('x', encoding='utf-8') as stream:
            stream.write(self._metadata)
        self._stream = (self.directory / 'samples.jsonl').open('x', encoding='utf-8')
        return self

    def record(self, sample):
        if self._stream is None or self._stream.closed:
            raise RuntimeError('recorder is not open')
        serialized = _serialize(sample)
        self._stream.write(serialized)
        self._stream.flush()
        self._count += 1

    def __exit__(self, exc_type, exc_value, traceback):
        self._stream.close()
        if exc_type is None:
            with (self.directory / 'complete.json').open('x', encoding='utf-8') as stream:
                stream.write(json.dumps({'count': self._count}) + '\n')
        return False
