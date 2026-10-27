"""Explicit paired workflow trials using frozen inputs. Never run by test discovery."""
import argparse
from dataclasses import replace
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
    parser.add_argument('--source', type=Path)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--poteto-source', type=Path)
    parser.add_argument('--entrypoint', choices=('fix', 'tdd', 'pancake'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--repetitions', type=int, default=1)
    parser.add_argument('--cases', nargs='+', choices=tuple(CASES), default=['integrated-import', 'direct-total'])
    args = parser.parse_args()
    if not 1 <= args.timeout <= 600 or not 1 <= args.repetitions <= 3:
        parser.error('timeout must be 1 to 600 seconds and repetitions 1 to 3')
    if len(args.cases) != len(set(args.cases)):
        parser.error('duplicate cases are not supported')
    paired = args.baseline is not None or args.candidate is not None
    if paired:
        if args.baseline is None or args.candidate is None or args.source is not None or args.poteto_source is not None:
            parser.error('use --baseline and --candidate together, without comparison sources')
        roots = {'baseline': args.baseline.resolve(), 'candidate': args.candidate.resolve()}
    elif args.source is not None and args.poteto_source is None and args.entrypoint:
        roots = {'pancake': args.source.resolve()}
    else:
        if args.entrypoint:
            parser.error('--entrypoint requires a single source or baseline/candidate pair')
        if args.source is None or args.poteto_source is None:
            parser.error('use --source and --poteto-source together')
        roots = {'pancake': args.source.resolve(), 'poteto': args.poteto_source.resolve()}
    output = args.output.resolve()
    if any(output.is_relative_to(root) for root in (*roots.values(), ROOT, EVALUATOR)):
        parser.error('output must be outside all input repositories')
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if not auth.is_file():
        parser.error('Codex file authentication cache required')
    def capture_inputs():
        return {key: poteto_inventory(root) if key == 'poteto' else source_identity(root)
                for key, root in roots.items()}
    inputs = capture_inputs()
    evaluator = identity(EVALUATOR)
    plan = trial_plan(args.cases, tuple(roots), args.repetitions)
    output.mkdir(mode=0o700)
    write_json(output / 'manifest.json', dict(sources=inputs, evaluator=evaluator, plan=plan,
        model_override=None, effort_override=None, timeout=args.timeout, entrypoint=args.entrypoint,
        cli=subprocess.check_output(['codex', '--version'], text=True).strip()))
    def unchanged():
        return identity(EVALUATOR) == evaluator and capture_inputs() == inputs
    results = []
    for index, (case, repeat, variant) in enumerate(plan, 1):
        if not unchanged():
            raise SystemExit('Inputs changed; stopped before next launch')
        destination = output / f'run-{index:02d}'
        print(f'Starting {index}/{len(plan)}: {case} {variant}', flush=True)
        adapter = CASES[case]
        if args.entrypoint:
            adapter = replace(adapter, entrypoint=f'skills/{args.entrypoint}/SKILL.md')
        result = run_trial(case, 'pancake' if paired else variant, destination, auth, None, None, args.timeout,
                           source=roots[variant] if paired else roots['pancake'], case_adapter=adapter,
                           poteto_source=roots['poteto'] if variant == 'poteto' else None,
                           expected_poteto=inputs['poteto'] if variant == 'poteto' else None)
        final = destination / 'final.txt'
        result.update(variant=variant, entrypoint='skills/poteto-mode/SKILL.md' if variant == 'poteto' else adapter.entrypoint, repetition=repeat, pair_id=f'{case}-{repeat}',
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
