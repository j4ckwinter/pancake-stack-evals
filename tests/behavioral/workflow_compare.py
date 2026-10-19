"""Explicit paired workflow trials using frozen inputs. Never run by test discovery."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from behavioral.compare import EVALUATOR, ROOT, run_trial, trial_plan, write_json
from behavioral.design_compare import source_identity, trial_valid
from behavioral.workflow_cases import CASES, judgment
from run_checks import identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('--repetitions', type=int, default=1)
    parser.add_argument('--cases', nargs='+', choices=tuple(CASES), default=list(CASES))
    args = parser.parse_args()
    if not 1 <= args.timeout <= 600 or not 1 <= args.repetitions <= 3:
        parser.error('timeout must be 1 to 600 seconds and repetitions 1 to 3')
    if len(args.cases) != len(set(args.cases)):
        parser.error('duplicate cases are not supported')
    roots = {'baseline': args.baseline.resolve(), 'candidate': args.candidate.resolve()}
    output = args.output.resolve()
    if any(output.is_relative_to(root) for root in (*roots.values(), ROOT, EVALUATOR)):
        parser.error('output must be outside all input repositories')
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if not auth.is_file():
        parser.error('Codex file authentication cache required')
    inputs = {key: source_identity(root) for key, root in roots.items()}
    evaluator = identity(EVALUATOR)
    plan = trial_plan(args.cases, ('baseline', 'candidate'), args.repetitions)
    output.mkdir(mode=0o700)
    write_json(output / 'manifest.json', dict(sources=inputs, evaluator=evaluator, plan=plan,
        model_override=None, effort_override=None, timeout=args.timeout,
        cli=subprocess.check_output(['codex', '--version'], text=True).strip()))
    def unchanged():
        return identity(EVALUATOR) == evaluator and all(source_identity(root) == inputs[key] for key, root in roots.items())
    results = []
    for index, (case, repeat, variant) in enumerate(plan, 1):
        if not unchanged():
            raise SystemExit('Inputs changed; stopped before next launch')
        destination = output / f'run-{index:02d}'
        result = run_trial(case, 'pancake', destination, auth, None, None, args.timeout,
                           source=roots[variant], case_adapter=CASES[case])
        final = destination / 'final.txt'
        result.update(variant=variant, repetition=repeat, pair_id=f'{case}-{repeat}',
                      inputs_unchanged=unchanged(),
                      final_response_present=final.is_file() and bool(final.read_text().strip()))
        execution = dict(result, artifact={'passed': result['artifact'].get('scope_preserved', False)})
        result['execution_valid'] = trial_valid(execution)
        write_json(destination / 'result.json', result)
        write_json(destination / 'judgment.json', judgment(case))
        results.append(result)
        write_json(output / 'results.json', results)
        print(f'Finished {index}/{len(plan)}: {case} {variant} artifact={result["artifact"]["passed"]}', flush=True)
        if not result['execution_valid']:
            raise SystemExit('Invalid trial execution or scope; inspect retained records')


if __name__ == '__main__':
    main()
