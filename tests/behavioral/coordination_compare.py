"""Explicit paired workflow trials using frozen inputs. Never run by test discovery."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from behavioral.compare import EVALUATOR, ROOT, run_trial, trial_plan, write_json, poteto_inventory
from behavioral.design_compare import source_identity, trial_valid
from behavioral.coordination_cases import CASES, judgment
from run_checks import identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--poteto-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--repetitions', type=int, default=1)
    parser.add_argument('--cases', nargs='+', choices=tuple(CASES), default=list(CASES))
    args = parser.parse_args()
    if not 1 <= args.timeout <= 600 or not 1 <= args.repetitions <= 3:
        parser.error('timeout must be 1 to 600 seconds and repetitions 1 to 3')
    if len(args.cases) != len(set(args.cases)):
        parser.error('duplicate cases are not supported')
    roots = {'pancake': args.source.resolve(), 'poteto': args.poteto_source.resolve()}
    output = args.output.resolve()
    if any(output.is_relative_to(root) for root in (*roots.values(), ROOT, EVALUATOR)):
        parser.error('output must be outside all input repositories')
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if not auth.is_file():
        parser.error('Codex file authentication cache required')
    inputs = {'pancake': source_identity(roots['pancake']), 'poteto': poteto_inventory(roots['poteto'])}
    evaluator = identity(EVALUATOR)
    plan = trial_plan(args.cases, ('pancake', 'poteto'), args.repetitions)
    output.mkdir(mode=0o700)
    write_json(output / 'manifest.json', dict(sources=inputs, evaluator=evaluator, plan=plan,
        model_override=None, effort_override=None, timeout=args.timeout,
        cli=subprocess.check_output(['codex', '--version'], text=True).strip()))
    def unchanged():
        return (identity(EVALUATOR) == evaluator and source_identity(roots['pancake']) == inputs['pancake']
                and poteto_inventory(roots['poteto']) == inputs['poteto'])
    results = []
    for index, (case, repeat, variant) in enumerate(plan, 1):
        if not unchanged():
            raise SystemExit('Inputs changed; stopped before next launch')
        destination = output / f'run-{index:02d}'
        print(f'Starting {index}/{len(plan)}: {case} {variant}', flush=True)
        result = run_trial(case, variant, destination, auth, None, None, args.timeout,
                           source=roots['pancake'], case_adapter=CASES[case],
                           poteto_source=roots['poteto'] if variant == 'poteto' else None,
                           expected_poteto=inputs['poteto'] if variant == 'poteto' else None)
        final = destination / 'final.txt'
        result.update(variant=variant, repetition=repeat, pair_id=f'{case}-{repeat}',
                      inputs_unchanged=unchanged(),
                      final_response_present=final.is_file() and bool(final.read_text().strip()))
        execution = dict(result, artifact={'passed': result['artifact'].get('scope_preserved', False)})
        result['execution_valid'] = trial_valid(execution) and result.get('bundle_unchanged') is True
        write_json(destination / 'result.json', result)
        write_json(destination / 'judgment.json', judgment(case))
        results.append(result)
        write_json(output / 'results.json', results)
        print(f'Finished {index}/{len(plan)}: {case} {variant} artifact={result["artifact"]["passed"]}', flush=True)
        if not result['execution_valid']:
            raise SystemExit('Invalid trial execution or scope; inspect retained records')


if __name__ == '__main__':
    main()
