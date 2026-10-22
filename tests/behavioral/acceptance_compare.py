"""Eight bounded Check trials against two frozen source treatments."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from behavioral.acceptance_cases import CASES, judgment
from behavioral.compare import EVALUATOR, ROOT, run_trial, trial_plan, write_json
from behavioral.design_compare import source_identity, trial_valid
from run_checks import identity


def validate_treatments(roots):
    inputs = {name: source_identity(root) for name, root in roots.items()}
    current, without = (inputs[name]['files'] for name in ('current', 'without'))
    differences = {name for name in current.keys() | without.keys()
                   if current.get(name) != without.get(name)} - {'snapshot-origin.json'}
    if differences != {'skills/check/SKILL.md'}:
        raise ValueError('treatments must differ only in Check and snapshot provenance')
    check = (roots['current'] / 'skills/check/SKILL.md').read_text()
    paragraphs = [part for part in check.split('\n\n') if part.startswith('When acceptance rules change,')]
    if len(paragraphs) != 1 or check.replace(paragraphs[0] + '\n\n', '', 1) != (
            roots['without'] / 'skills/check/SKILL.md').read_text():
        raise ValueError('without treatment must remove only the acceptance paragraph')
    return inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', type=Path, required=True)
    parser.add_argument('--without', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=240)
    parser.add_argument('--cases', nargs='+', choices=tuple(CASES), default=list(CASES))
    args = parser.parse_args()
    if not 1 <= args.timeout <= 600 or len(args.cases) != len(set(args.cases)):
        parser.error('timeout must be 1 to 600 seconds and cases must be unique')
    roots = {'current': args.current.resolve(), 'without': args.without.resolve()}
    output = args.output.resolve()
    if any(output.is_relative_to(root) for root in (*roots.values(), ROOT, EVALUATOR)):
        parser.error('output must be outside input repositories')
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if not auth.is_file():
        parser.error('Codex file authentication cache required')
    inputs, evaluator = validate_treatments(roots), identity(EVALUATOR)
    plan = trial_plan(args.cases, ('current', 'without'), 1)
    output.mkdir(mode=0o700)
    write_json(output / 'manifest.json', dict(sources=inputs, evaluator=evaluator, plan=plan,
        timeout=args.timeout, model_override=None, effort_override=None,
        cli=subprocess.check_output(['codex', '--version'], text=True).strip()))
    def unchanged():
        return identity(EVALUATOR) == evaluator and all(
            source_identity(root) == inputs[name] for name, root in roots.items())
    results = []
    for index, (case, repeat, variant) in enumerate(plan, 1):
        if not unchanged():
            raise SystemExit('Inputs changed; stopped before next launch')
        destination = output / f'run-{index:02d}'
        print(f'Starting {index}/{len(plan)}: {case} {variant}', flush=True)
        result = run_trial(case, variant, destination, auth, None, None, args.timeout,
                           source=roots[variant], case_adapter=CASES[case])
        final = destination / 'final.txt'
        result.update(pair_id=case, repetition=repeat, inputs_unchanged=unchanged(),
                      final_response_present=final.is_file() and bool(final.read_text().strip()))
        result['execution_valid'] = trial_valid(dict(result, artifact={'passed': True}))
        result['scope_preserved'] = result['artifact']['scope_preserved'] and result['bundle_unchanged']
        result['manual_judgment'] = judgment(case)
        write_json(destination / 'result.json', result)
        results.append(result)
        write_json(output / 'results.json', results)
        if not result['execution_valid'] or not result['scope_preserved']:
            raise SystemExit('Invalid execution or scope; inspect private records')


if __name__ == '__main__':
    main()
