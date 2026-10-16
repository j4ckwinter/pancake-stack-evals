"""Private Design pilot fixtures and rubric. Never copy this module to candidates."""
from pathlib import Path
from .support import snapshot

REQUESTS = {
    'interface': 'Propose a small change so callers can request the first N report rows without changing existing callers. Explain the interface and checks; do not implement it.',
    'boundary': 'Design validation for the report limit: accept nonnegative integers, reject booleans and fractional numbers, and keep omission meaning all rows. Explain the behavior and useful checks; do not implement it.',
    'migration': 'Propose a migration from total to amount in newly emitted invoice records. Keep the existing Python API usable and old stored records readable. Explain the change and verification; do not implement it.',
    'retry': 'Design reliable job claiming for multiple local producer and consumer processes. A consumer can crash before or after doing the job. Explain ownership, retries, and checks; do not implement it.',
    'independent': 'Have two independent agents propose competing designs for reliable job claiming across multiple local producer and consumer processes, then have a separate agent compare their proposals. I prefer JSON if practical, but that is a preference rather than a requirement. Consumers can crash before or after doing a job. Recommend an approach; do not implement it.',
}
FILES = {
    'interface': {'report.py': 'def rows(records):\n    return list(records)\n',
                  'app.py': 'from report import rows\n\ndef display(records):\n    return rows(records)\n'},
    'boundary': {'report.py': 'def rows(records, limit=None):\n    return list(records) if limit is None else list(records)[:limit]\n'},
    'migration': {'producer.py': 'def create_invoice(total):\n    return {"total": total}\n',
                  'consumer.py': 'def read_total(record):\n    return record["total"]\n',
                  'billing.py': 'from producer import create_invoice\n\ndef bill(total):\n    return create_invoice(total=total)\n',
                  'archive.json': '[{"total": 19.5}]\n'},
    'retry': {'queue.py': 'import json\nfrom pathlib import Path\n\ndef enqueue(path, job):\n    target = Path(path)\n    jobs = json.loads(target.read_text()) if target.exists() else []\n    jobs.append(job)\n    target.write_text(json.dumps(jobs))\n\ndef take(path):\n    target = Path(path)\n    jobs = json.loads(target.read_text())\n    job = jobs.pop(0)\n    target.write_text(json.dumps(jobs))\n    return job\n'},
}
FILES['independent'] = FILES['retry']

# Criteria describe observable quality; they are not an imposed architecture.
RUBRIC = {
    'interface': ['Preserves existing calls and result semantics.', 'Defines bounded retrieval without unnecessary architecture.', 'Identifies useful old/new-call checks.'],
    'boundary': ['Rejects bool despite int subclassing, fractional values and negative limits.', 'Preserves omitted and zero behavior.', 'Varies rejected dimensions independently with valid neighboring inputs.'],
    'migration': ['Preserves create_invoice(total=...).', 'Traces emitted and stored records to their readers.', 'Covers a feasible transition and archive compatibility checks.'],
    'retry': ['Addresses atomic claim across processes and persistent ownership.', 'Addresses failure before/after effects, duplicate execution and recovery.', 'Defines contention/crash checks and does not promise impossible exactly-once effects.'],
    'independent': ['Two completed independent proposals and a later separate comparison have linked session evidence.', 'Fresh-context launches are observed; unavailable briefs remain explicitly unavailable.', 'Judge compares proposals against constraints and meaningful tradeoffs without treating preference as mandatory.', 'Final recommendation handles concurrency, durability, retries and duplicate effects.'],
}


def prepare_case(case, destination):
    destination = Path(destination)
    destination.mkdir()
    for name, content in FILES[case].items():
        (destination / name).write_text(content)
    return snapshot(destination)


def judge_packet(case, destination, record):
    """An assessor-only packet, deliberately separate from the candidate prompt."""
    return {'case': case, 'criteria': RUBRIC[case],
            'candidate_output': str(destination / 'final.txt'),
            'sessions': str(destination / 'sessions.json'),
            'raw_sessions': str(destination / 'raw-sessions'),
            'preserved': record['artifact']['passed'],
            'instructions': 'Mark every criterion passed, failed, or unavailable with evidence. Inspect actual successful source reads, project reads and completed tool outputs. Cost alone does not prove wasted work. Proposals are not implemented runtime behavior. Report unsupported claims and unnecessary work separately; never use word count as quality.'}
