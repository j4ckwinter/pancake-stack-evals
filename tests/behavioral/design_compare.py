"""Explicit bounded comparison of frozen source bundles; never run by unit tests."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from behavioral import design, historical_review
from behavioral.compare import EVALUATOR, ROOT, run_trial, trial_plan, write_json
from behavioral.support import snapshot
from run_checks import identity


def source_identity(root):
    return {'files': snapshot(root), 'origin': json.loads((root / 'snapshot-origin.json').read_text())}


def trial_valid(result):
    roots = [s for s in result.get('sessions', []) if s['parent_id'] is None]
    return (result.get('inputs_unchanged') is True and result.get('exit_code') == 0
            and result.get('timed_out') is False
            and result.get('final_response_present') is True
            and result.get('artifact', {}).get('passed') is True
            and result.get('preferences_unchanged') is True
            and bool(roots) and all(s.get('completed') is True for s in roots))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--candidate-only', action='store_true', help='separate targeted follow-up, not a paired comparison')
    parser.add_argument('--entrypoint', choices=('design', 'parallel-work'), default='design')
    parser.add_argument('--cases', nargs='+', choices=tuple(design.REQUESTS) + tuple(historical_review.CASES), default=list(design.REQUESTS))
    args = parser.parse_args()
    if not 1 <= args.timeout <= 600:
        parser.error('timeout must be 1–600 seconds')
    roots = {'baseline': args.baseline.resolve(), 'candidate': args.candidate.resolve()}
    output = args.output.resolve()
    if any(output.is_relative_to(root) for root in (*roots.values(), ROOT, EVALUATOR)):
        parser.error('output must be outside all input repositories')
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if not auth.is_file():
        parser.error('Codex file authentication cache required')
    inputs = {key: source_identity(root) for key, root in roots.items()}
    evaluator = identity(EVALUATOR)
    plan = trial_plan(args.cases, ('candidate',) if args.candidate_only else ('baseline', 'candidate'), 1)
    output.mkdir(mode=0o700)
    write_json(output / 'manifest.json', {'sources': inputs, 'evaluator': evaluator, 'plan': plan,
        'model_override': None, 'effort_override': None, 'timeout': args.timeout,
        'ordinary_timeout': min(args.timeout, 180), 'entrypoint': args.entrypoint,
        'cli': subprocess.check_output(['codex', '--version'], text=True).strip(),
        'historical_fixture': historical_review.provenance() if any(c in historical_review.CASES for c in args.cases) else None})
    def unchanged():
        return identity(EVALUATOR) == evaluator and all(source_identity(root) == inputs[key] for key, root in roots.items())
    results = []
    for index, (case, repeat, variant) in enumerate(plan, 1):
        if not unchanged():
            raise SystemExit('Inputs changed; stopped before next launch')
        destination = output / f'run-{index:02d}'
        print(f'Starting {index}/{len(plan)}: {case} {variant}', flush=True)
        suite = 'historical-review' if case in historical_review.CASES else 'design'
        result = run_trial(case, 'pancake', destination, auth, None, None, args.timeout if case == 'independent' else min(args.timeout, 180),
                           suite=suite, source=roots[variant], design_entrypoint=args.entrypoint)
        final = destination / 'final.txt'
        result.update(variant=variant, repetition=repeat, inputs_unchanged=unchanged(),
                      final_response_present=final.is_file() and bool(final.read_text().strip()))
        write_json(destination / 'result.json', result)
        if suite == 'design':
            write_json(destination / 'judge.json', design.judge_packet(case, destination, result))
        results.append(result)
        write_json(output / 'results.json', results)
        print(f'Finished {index}: preserved={result["artifact"]["passed"]} seconds={result["elapsed_seconds"]}', flush=True)
        if not trial_valid(result):
            raise SystemExit('Invalid trial (inputs, execution, preservation or root completion); inspect retained records')


if __name__ == '__main__':
    main()
