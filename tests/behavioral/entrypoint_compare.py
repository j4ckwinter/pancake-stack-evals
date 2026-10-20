"""Explicit paired direct/Pancake repair trials; private output, no model overrides."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from behavioral.compare import EVALUATOR, ROOT, assess_candidate, run_trial, write_json
from behavioral.design_compare import source_identity, trial_valid
from behavioral.support import SCENARIOS, prepare, snapshot
from behavioral.workflow_cases import Case
from run_checks import identity


def assess_records(case, workspace, before, profile):
    result = assess_candidate('records', workspace, before, profile)
    current = snapshot(workspace)
    mutable = SCENARIOS['records'].mutable
    preserved = (all(current.get(name) == digest for name, digest in before.items()
                     if name not in mutable) and all(name in current for name in mutable)
                 and all(len(Path(name).parts) == 1 and name.startswith('test_')
                         and name.endswith('.py') for name in current.keys() - before.keys()))
    return dict(result, scope_preserved=preserved)


def entrypoints():
    request = ('New invoice payloads need to use amount, but the producer and live consumer '
               'still use total. Fix this mismatch while keeping archived total records readable '
               'and preserving create_invoice(total=...) and the established billing caller. '
               'Update the relevant checks and verify both contracts.')
    return [(pair, name, Case(request + suffix, f'skills/{name}/SKILL.md', False,
                             prepare, assess_records, allow_reviewers=True))
            for pair, direct, suffix in [('repair', 'fix', ''),
                ('test-first-repair', 'tdd', ' Use test-first development for this change.')]
            for name in (direct, 'pancake')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=240)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 600:
        parser.error('timeout must be 1 to 600 seconds')
    source, output = args.source.resolve(), args.output.resolve()
    if any(output.is_relative_to(root) for root in (source, ROOT, EVALUATOR)):
        parser.error('output must be outside input repositories')
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if not auth.is_file():
        parser.error('Codex file authentication cache required')
    frozen, evaluator = source_identity(source), identity(EVALUATOR)
    output.mkdir(mode=0o700)
    write_json(output / 'manifest.json', dict(source=frozen, evaluator=evaluator,
        timeout=args.timeout, model_override=None, effort_override=None,
        cli=subprocess.check_output(['codex', '--version'], text=True).strip(),
        plan=[(pair, name) for pair, name, _ in entrypoints()]))
    def unchanged():
        return source_identity(source) == frozen and identity(EVALUATOR) == evaluator
    results = []
    for index, (pair, name, adapter) in enumerate(entrypoints(), 1):
        if not unchanged():
            raise SystemExit('Inputs changed; stopped before next launch')
        print(f'Starting {index}/4: {pair} {name}', flush=True)
        destination = output / f'run-{index:02d}'
        result = run_trial('records', 'pancake', destination, auth, None, None,
                           args.timeout, source=source, case_adapter=adapter)
        final = destination / 'final.txt'
        result.update(pair=pair, entrypoint=name, inputs_unchanged=unchanged(),
                      final_response_present=final.is_file() and bool(final.read_text().strip()))
        execution = dict(result, artifact={'passed': result['artifact'].get('scope_preserved', False)})
        result['execution_valid'] = trial_valid(execution) and result['bundle_unchanged']
        write_json(destination / 'result.json', result)
        results.append(result)
        write_json(output / 'results.json', results)
        print(f'Finished {index}/4: artifact={result["artifact"]["passed"]} '
              f'reviewers={len(result["completed_reviewers"])} elapsed={result["elapsed_seconds"]}', flush=True)
        if not result['execution_valid']:
            raise SystemExit('Invalid execution; inspect private records')


if __name__ == '__main__':
    main()
