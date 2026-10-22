"""Six bounded experiment trials against two frozen source treatments."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from behavioral.experiment_cases import CASES, judgment
from behavioral.compare import EVALUATOR, ROOT, run_trial, trial_plan, write_json
from behavioral.design_compare import source_identity, trial_valid
from run_checks import identity


BRANCHES = (('Performance', 'performance'), ('Prototype', 'prototype'),
            ('Skill evaluation', 'skill-evaluation'))
REFERENCE = 'skills/pancake/references/experiments.md'


def selective_files(original):
    """Exact relocation: retain shared text and every branch instruction verbatim."""
    revised = original
    files = {}
    for title, slug in BRANCHES:
        start = original.index('### ' + title + '\n\n')
        boundaries = [pos for marker in ('\n### ', '\n## ') if
                      (pos := original.find(marker, start + 4)) >= 0]
        end = min(boundaries) + 1 if boundaries else len(original)
        section = original[start:end]
        name = f'experiments-{slug}.md'
        files['skills/pancake/references/' + name] = section.replace('### ', '# ', 1)
        replacement = (f'### {title}\n\nRead [{title.lower()} guidance]({name}) '
                       'for this experiment.\n\n')
        revised = revised.replace(section, replacement, 1)
    files[REFERENCE] = revised
    return files


def validate_treatments(roots):
    inputs = {name: source_identity(root) for name, root in roots.items()}
    current, selective = (inputs[name]['files'] for name in ('current', 'selective'))
    expected = selective_files((roots['current'] / REFERENCE).read_text())
    differences = {name for name in current.keys() | selective.keys()
                   if current.get(name) != selective.get(name)} - {'snapshot-origin.json'}
    if differences != set(expected):
        raise ValueError('treatments must differ only in experiment reference extraction')
    if any((roots['selective'] / name).read_text() != content for name, content in expected.items()):
        raise ValueError('selective treatment must preserve all shared and branch guidance exactly')
    if any(name in current for name in expected if name != REFERENCE):
        raise ValueError('extracted branch paths must be new')
    return inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', type=Path, required=True)
    parser.add_argument('--selective', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=240)
    parser.add_argument('--cases', nargs='+', choices=tuple(CASES), default=list(CASES))
    args = parser.parse_args()
    if not 1 <= args.timeout <= 600 or len(args.cases) != len(set(args.cases)):
        parser.error('timeout must be 1 to 600 seconds and cases must be unique')
    roots = {'current': args.current.resolve(), 'selective': args.selective.resolve()}
    output = args.output.resolve()
    if any(output.is_relative_to(root) for root in (*roots.values(), ROOT, EVALUATOR)):
        parser.error('output must be outside input repositories')
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if not auth.is_file():
        parser.error('Codex file authentication cache required')
    inputs, evaluator = validate_treatments(roots), identity(EVALUATOR)
    plan = trial_plan(args.cases, ('current', 'selective'), 1)
    output.mkdir(mode=0o700)
    write_json(output / 'manifest.json', dict(sources=inputs, evaluator=evaluator, plan=plan,
        timeout=args.timeout, model_override=None, effort_override=None,
        comparison_limits='Three cases, one trial per treatment; no general efficacy claim. Outcome and full returned guidance exposure require manual judgment.',
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
        result['execution_valid'] = (trial_valid(dict(result, artifact={'passed': True}))
            and not any(session.get('parent_id') is not None for session in result.get('sessions', [])))
        result['scope_preserved'] = result['artifact']['scope_preserved'] and result['bundle_unchanged']
        result['manual_judgment'] = judgment(case)
        write_json(destination / 'result.json', result)
        results.append(result)
        write_json(output / 'results.json', results)
        if not result['execution_valid'] or not result['scope_preserved']:
            raise SystemExit('Invalid execution or scope; inspect private records')


if __name__ == '__main__':
    main()
