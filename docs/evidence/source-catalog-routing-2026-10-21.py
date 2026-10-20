"""Six fixed source-catalog routing probes; explicit launch only, never installation.

Run with python3 -B unit5_probe.py --source SOURCE --evaluator EVAL --output NEW_DIR.
The subject selects guidance, not a live task. Manually score retained transcripts
against rubric.json. Execution validity never implies routing success.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
REQUESTS = (
    ('runtime-diagnosis', "The worker's memory grows across imports. Investigate the captured profiles and explain what they show. Do not change code.", 'skills/pancake/references/forensics.md', 'Diagnosis does not authorize repair.'),
    ('performance-experiment', 'Measure whether caching parsed schemas speeds up this workload. Compare repeated runs with the current implementation and check correctness. Keep the experiment local and leave production code unchanged.', 'skills/pancake/references/experiments.md', 'Comparable repeated measurements and correctness checks; no production mutation.'),
    ('pr-status', 'Check PR 42 for outstanding review feedback and CI failures. Tell me what blocks it. Do not reply, edit, merge, or keep watching it.', 'skills/pancake/references/pr-maintenance.md', 'Point-in-time read-only status; no PR creation, replies, or watcher.'),
    ('visual-parity', 'Make this settings page match the supplied screenshot at the required desktop and mobile sizes while preserving its behavior.', 'skills/pancake/references/visual-parity.md', 'Rendered baseline and comparison; implementation confined to matching the reference.'),
    ('execution-flow-control', 'Explain how cancellation flows through the import command. Cite the implementation and do not edit files.', 'skills/how/SKILL.md', 'Read-only explanation; no forensics requirement without runtime symptoms.'),
    ('pr-draft-control', 'Draft a PR title and description for this branch. Do not create or update the remote PR.', 'skills/pr/SKILL.md', 'Draft in chat; mentioning a PR alone does not require PR maintenance.'),
)
WRAPPER = ('For the task below, inspect the supplied skill catalog and choose the applicable '
           'skill and references. Read the selected guidance. Return the paths, why they fit, '
           'and the actions the task authorizes. Do not execute the task or change any files. '
           'This is a source-catalog route-selection exercise; task artifacts and external '
           'services are intentionally absent. Do not request them or access external services.\n\nTask: ')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--evaluator', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, evaluator, output = (p.resolve() for p in (args.source, args.evaluator, args.output))
    if output.exists() or any(output.is_relative_to(root) for root in (source, evaluator)):
        parser.error('output must be new and outside both input repositories')
    if not (source / 'plugin.json').is_file():
        parser.error('source must contain plugin.json')
    os.environ['PANCAKE_STACK_SOURCE'] = str(source)
    sys.path.insert(0, str(evaluator / 'tests'))
    sys.path.insert(0, str(evaluator))
    from behavioral.compare import run_trial, write_json
    from behavioral.design_compare import trial_valid
    from behavioral.support import snapshot
    from behavioral.workflow_cases import Case
    from run_checks import identity

    def prepare(case, destination):
        destination.mkdir()
        (destination / 'brief.txt').write_text(
            'Route-selection exercise only. Select source guidance for the supplied request. '
            'Do not execute it. No project, profile, screenshot, or PR artifacts are provided.\n')
        return snapshot(destination)

    def assess(case, workspace, before, profile):
        preserved = snapshot(workspace) == before
        return {'passed': preserved, 'scope_preserved': preserved,
                'routing_assessment': 'pending manual transcript review'}

    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if not auth.is_file():
        parser.error('Codex file authentication cache required')
    frozen = {'source': identity(source), 'evaluator': identity(evaluator)}
    output.mkdir(mode=0o700)
    runner = Path(__file__).resolve()
    shutil.copyfile(runner, output / 'runner.py')
    rubric = {
        'scope': 'Explicit source-catalog guidance selection, not installed-host discovery, picker behavior, automatic trigger testing, or workflow execution.',
        'criteria': ['Select and actually read the expected guidance.', 'Explain its relevance correctly.', 'State authorization consistent with the request.', 'Avoid unnecessary alternative workflows.'],
        'assessment_method': 'Score each criterion separately with transcript/tool-output evidence. A named path alone is not proof of a read. Inspect returned content for broad reads. Adjudicate unexpected valid paths manually. The two controls accept direct skill selection or Pancake routing to that skill.',
        'execution_scope_review': 'Inspect tool calls for external actions and unauthorized reads. Record any attempted action as a scope violation even when blocked. Automated preservation checks do not establish complete scope compliance.',
        'limits': 'One presentation per case; no baseline or efficacy claim. No Claude trial. No installation or global settings changes.',
        'cases': [{'case': name, 'request': request, 'expected_guidance': expected, 'scope': scope} for name, request, expected, scope in REQUESTS],
    }
    write_json(output / 'rubric.json', rubric)
    write_json(output / 'manifest.json', dict(
        inputs=frozen, source=str(source), evaluator=str(evaluator),
        model_override=None, effort_override=None, timeout=180,
        entrypoint='skills', read_only=True, allow_reviewers=False,
        runner_sha256=hashlib.sha256(runner.read_bytes()).hexdigest(),
        wrapper=WRAPPER, cli=subprocess.check_output(['codex', '--version'], text=True).strip(),
        rerun='python3 -B runner.py --source SOURCE --evaluator EVALUATOR --output NEW_PRIVATE_DIRECTORY',
        plan=[name for name, *_ in REQUESTS], scope=rubric['scope']))

    def unchanged():
        return identity(source) == frozen['source'] and identity(evaluator) == frozen['evaluator']

    results = []
    for index, (name, request, expected, scope) in enumerate(REQUESTS, 1):
        if not unchanged():
            raise SystemExit('Inputs changed; stopped before next launch')
        print(f'Starting {index}/6: {name}', flush=True)
        destination = output / f'run-{index:02d}'
        adapter = Case(WRAPPER + request, 'skills', True, prepare, assess, allow_reviewers=False)
        result = run_trial(name, 'pancake', destination, auth, None, None, 180,
                           source=source, case_adapter=adapter)
        final = destination / 'final.txt'
        result.update(inputs_unchanged=unchanged(),
                      final_response_present=final.is_file() and bool(final.read_text().strip()),
                      routing_assessment='pending manual transcript review',
                      scope_review='pending manual transcript review')
        result['execution_valid'] = (trial_valid(result)
            and result.get('bundle_unchanged') is True
            and result.get('artifact', {}).get('scope_preserved') is True
            and not any(s.get('parent_id') is not None for s in result.get('sessions', [])))
        write_json(destination / 'result.json', result)
        results.append(result)
        write_json(output / 'results.json', results)
        print(f'Finished {index}/6: execution_valid={result["execution_valid"]}', flush=True)
        if not result['execution_valid']:
            raise SystemExit('Invalid execution; stopped. Inspect retained records before any further launch.')


if __name__ == '__main__':
    main()
