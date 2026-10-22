"""Explicit bounded source-metadata routing trials, not native installed discovery."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from behavioral.compare import EVALUATOR, ROOT, run_trial, skill_catalog, trial_plan, write_json
from behavioral.design_compare import source_identity, trial_valid
from behavioral.routing_cases import CASES, judgment
from run_checks import identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=240)
    parser.add_argument('--cases', nargs='+', choices=tuple(CASES), default=list(CASES))
    args = parser.parse_args()
    if not 1 <= args.timeout <= 600 or len(args.cases) != len(set(args.cases)):
        parser.error('timeout must be 1 to 600 seconds and cases must be unique')
    source, output = args.source.resolve(), args.output.resolve()
    if any(output.is_relative_to(root) for root in (source, ROOT, EVALUATOR)):
        parser.error('output must be outside input repositories')
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if not auth.is_file():
        parser.error('Codex file authentication cache required')
    frozen, evaluator = source_identity(source), identity(EVALUATOR)
    catalog = skill_catalog(source)
    plan = trial_plan(args.cases, ('catalog', 'none'), 1)
    output.mkdir(mode=0o700)
    write_json(output / 'manifest.json', dict(source=frozen, evaluator=evaluator, plan=plan,
        discovery='source metadata, not native installed discovery', catalog=catalog,
        timeout=args.timeout, model_override=None, effort_override=None,
        cli=subprocess.check_output(['codex', '--version'], text=True).strip()))
    def unchanged():
        return source_identity(source) == frozen and identity(EVALUATOR) == evaluator
    results = []
    for index, (case, repeat, variant) in enumerate(plan, 1):
        if not unchanged():
            raise SystemExit('Inputs changed; stopped before next launch')
        destination = output / f'run-{index:02d}'
        print(f'Starting {index}/{len(plan)}: {case} {variant}', flush=True)
        result = run_trial(case, variant, destination, auth, None, None, args.timeout,
                           source=source, case_adapter=CASES[case].adapter(variant))
        final = destination / 'final.txt'
        result.update(pair_id=case, repetition=repeat, inputs_unchanged=unchanged(),
                      final_response_present=final.is_file() and bool(final.read_text().strip()))
        execution = dict(result, artifact={'passed': True})
        result['execution_valid'] = trial_valid(execution)
        result['scope_preserved'] = result['artifact']['scope_preserved'] and result['bundle_unchanged']
        result['manual_judgment'] = judgment(case)
        write_json(destination / 'result.json', result)
        results.append(result)
        write_json(output / 'results.json', results)
        if not result['execution_valid'] or not result['scope_preserved']:
            raise SystemExit('Invalid execution or scope; inspect private records')


if __name__ == '__main__':
    main()
