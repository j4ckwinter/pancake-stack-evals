"""Measure complete guidance returned in explicitly supplied private session records.

Counts are observed text volume, not tokens or proof that the model used guidance.
Partial bodies, filename mentions, and unsupported output shapes are unmeasured.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

if __package__:
    from .traces import output_text, session_actions
else:
    from traces import output_text, session_actions

EVALUATOR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(EVALUATOR))
from run_checks import identity


def returned_texts(value):
    """Decode text and known output envelopes without counting their encoded copies."""
    if isinstance(value, list):
        for item in value:
            yield from returned_texts(item)
    elif isinstance(value, dict):
        if value.get('type') in ('text', 'input_text', 'output_text'):
            yield from returned_texts(output_text(value))
        else:
            for key in ('output', 'content'):
                if key in value:
                    yield from returned_texts(value[key])
                    break
    elif isinstance(value, str) and value:
        try:
            decoded = json.loads(value)
        except (ValueError, RecursionError):
            decoded = None
        if isinstance(decoded, (dict, list)):
            yield from returned_texts(decoded)
        else:
            lines = value.splitlines()
            # Exec can print one JSON result envelope per line.
            if len(lines) > 1 and all(line.startswith('{') and line.endswith('}') for line in lines):
                try:
                    envelopes = [json.loads(line) for line in lines]
                except ValueError:
                    envelopes = None
                if envelopes is not None:
                    yield from returned_texts(envelopes)
                    return
            yield value


def build_report(source, sessions):
    """Match frozen Markdown bodies to returned output; never inspect call arguments."""
    source = Path(source).resolve()
    paths = [Path(path).resolve() for path in sessions]
    if not source.is_dir() or not paths or len(paths) != len(set(paths)):
        raise ValueError('source must be a directory and sessions must be nonempty distinct paths')
    files, bodies = {}, {}
    for path in sorted(source.rglob('*.md')):
        if '.git' in path.relative_to(source).parts:
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(source):
            raise ValueError(f'guidance symlink is unsupported: {path}')
        raw = path.read_bytes()
        body = raw.decode('utf-8').replace('\r\n', '\n').strip()
        name = path.relative_to(source).as_posix()
        files[name] = dict(sha256=hashlib.sha256(raw).hexdigest(), words=len(body.split()),
                           occurrences=[], complete_returns=0)
        if body:
            bodies.setdefault(body, []).append(name)
    if not files:
        raise ValueError('source must contain Markdown guidance')
    unmeasured = []
    for action_index, action in enumerate(session_actions(paths)):
        for output_index, output in enumerate(action['outputs']):
            texts = list(returned_texts(output))
            location = dict(session_id=action['session_id'], call_id=action['call_id'],
                            action_index=action_index, output_index=output_index)
            if not texts:
                unmeasured.append(dict(location, reason='unsupported_or_empty_output'))
            for text_index, text in enumerate(texts):
                text = text.replace('\r\n', '\n')
                matched = False
                for body, names in bodies.items():
                    count = text.count(body)
                    if not count:
                        continue
                    matched = True
                    if len(names) > 1:
                        unmeasured.append(dict(location, text_index=text_index,
                            reason='identical_source_bodies', candidates=names, complete_returns=count))
                        continue
                    item = files[names[0]]
                    item['complete_returns'] += count
                    item['occurrences'].append(dict(location, text_index=text_index, count=count))
                if not matched:
                    unmeasured.append(dict(location, text_index=text_index,
                        reason='no_complete_source_body',
                        coverage='partial_truncated_mentions_or_unrelated_text_unmeasured'))
    unique_words = sum(item['words'] for item in files.values() if item['complete_returns'])
    total_words = sum(item['words'] * item['complete_returns'] for item in files.values())
    source_info = dict(path=str(source), markdown_sha256={name: item['sha256'] for name, item in files.items()})
    if (source / '.git').exists():
        source_info['checkout'] = identity(source)
    origin = source / 'snapshot-origin.json'
    if origin.is_file():
        source_info['snapshot_origin'] = json.loads(origin.read_text())
    return dict(schema_version=1, measurement='exact_complete_markdown_body_returns',
        limitations=['Counts returned text, not model attention or token usage.',
                      'Partial, truncated, reformatted and unsupported output content is unmeasured.',
                      'Surrounding whitespace and CRLF are normalized; filenames never establish reads.',
                      'Identical source bodies cannot be attributed to individual paths.',
                      'A body embedded verbatim in another source body also matches; totals may overlap.'],
        source=source_info, evaluator=identity(EVALUATOR),
        sessions=[dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths],
        files=files, totals=dict(unique_files=sum(bool(item['complete_returns']) for item in files.values()),
            complete_returns=sum(item['complete_returns'] for item in files.values()),
            unique_words=unique_words, repeated_words=total_words - unique_words,
            total_words=total_words), unmeasured=unmeasured)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--sessions', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if any(output.is_relative_to(root) for root in (args.source.resolve(), EVALUATOR)):
        parser.error('--output must be outside source and evaluator repositories')
    if output in [path.resolve() for path in args.sessions]:
        parser.error('--output must not replace a session input')
    report = build_report(args.source, args.sessions)
    with output.open('x', encoding='utf-8') as stream:
        output.chmod(0o600)
        json.dump(report, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
