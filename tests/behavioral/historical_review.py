"""Private historical regression fixture; never supply this module to candidates."""
import difflib
import hashlib
import json
from pathlib import Path

from .repository_review import extract_snapshot
from .support import snapshot

FIXTURE = Path(__file__).resolve().parents[2] / 'fixtures/historical-review'
PROVENANCE_SHA256 = '0fa8fb385620873dfa146bc25844e29b984b0b6d71624450b86e0f2557135235'
CASES = {'migration-faulty': ('valid-migration-rejected',), 'migration-clean': ()}
REQUEST = ('Review change.diff against the current repository for actionable regressions. '
           'The diff is an extraction of the assessor and contract scenario changes; the '
           'complete repository context is available. Inspect relevant callers and contracts. Do not edit files.')


def provenance():
    raw = (FIXTURE / 'provenance.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROVENANCE_SHA256:
        raise ValueError('historical provenance mismatch')
    record = json.loads(raw)
    for name, digest in dict(record['artifacts'], **{'source.tar.gz': record['archive_sha256']}).items():
        if hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'historical artifact mismatch: {name}')
    return record


def prepare_case(case, destination):
    CASES[case]
    record = provenance()
    destination = Path(destination)
    extract_snapshot(destination, (FIXTURE / 'source.tar.gz').read_bytes(), record['files'])
    diff = (FIXTURE / 'introducing.diff').read_text()
    if case == 'migration-clean':
        relative = 'tests/behavioral/support.py'
        repaired = (FIXTURE / 'repaired-support.py.txt').read_text()
        (destination / relative).write_text(repaired)
        prefix, _ = diff.split('diff --git a/tests/behavioral/support.py', 1)
        base = (FIXTURE / 'base-support.py.txt').read_text()
        diff = prefix + ''.join(difflib.unified_diff(base.splitlines(keepends=True),
            repaired.splitlines(keepends=True), fromfile=f'a/{relative}', tofile=f'b/{relative}'))
    (destination / 'change.diff').write_text(diff)
    return snapshot(destination)
