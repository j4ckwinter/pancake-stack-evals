"""Natural requests and private outcome criteria for source-metadata discovery."""
from dataclasses import dataclass

from . import context_recovery, workflow_cases
from .entrypoint_compare import assess_records, entrypoints
from .support import prepare, snapshot
from .workflow_cases import Case



def prepare_case(case, workspace):
    setup = CASES[case].setup
    if setup == 'records':
        return prepare('records', workspace)
    if setup == 'history':
        return context_recovery.prepare_case('fresh-handoff', workspace)
    before = workflow_cases.prepare_case('ordinary-bug', workspace)
    if setup == 'status':
        (workspace / 'pr-snapshot.txt').write_text(
            'Captured 2026-10-01T12:00:00Z. PR #17, head abc123.\n'
            'State OPEN. Mergeability CONFLICTING. Required checks: unit FAILURE, lint SUCCESS.\n'
            'Review: CHANGES_REQUESTED. Unresolved thread: preserve negative adjustments.\n'
            'No later status is available in this snapshot.\n')
        before = snapshot(workspace)
    return before


def assess_case(case, workspace, before, profile):
    if CASES[case].setup == 'records':
        return assess_records('records', workspace, before, profile)
    preserved = snapshot(workspace) == before
    return {'passed': None, 'scope_preserved': preserved, 'status': 'pending manual response judgment'}


@dataclass(frozen=True)
class RoutingCase:
    request: str
    setup: str
    expected_route: str
    expected_outcomes: tuple

    def adapter(self, discovery):
        return Case(self.request, '', self.setup != 'records', prepare_case, assess_case,
                    discovery=discovery)


repair = entrypoints()[0][2].request
CASES = {
    'trace': RoutingCase(
        'Explain how total handles missing and negative values. Trace the implementation and cite '
        'the relevant lines. Do not edit files.', 'review', 'how',
        ('Explains None filtering and abs converting negative values to positive.', 'Cites app.py.')),
    'rationale': RoutingCase(
        'Why was the public total keyword kept during the invoice migration? Use repository '
        'history to explain the decision and distinguish it from the current implementation. Do not edit files.',
        'history', 'why', ('Uses git history and docs/decision.md.',
        'Explains compatibility decision and current amount keyword contradiction.')),
    'repair': RoutingCase(repair, 'records', 'fix', ('Repairs both new and archived contracts.',)),
    'test-first': RoutingCase(repair + ' Use test-first development for this change.', 'records', 'tdd',
        ('Shows a relevant failing test before production edits, then passing checks.',)),
    'diff-review': RoutingCase(
        'Review change.diff for actionable bugs and regressions. Cite evidence and do not edit files.',
        'review', 'check', ('Reports negative adjustments becoming positive with app.py evidence.',)),
    'assumptions': RoutingCase(
        'Stress-test the assumption that taking absolute values in total is a safe simplification. '
        'Challenge the approach against the existing contract, with concrete counterexamples. Do not edit files.',
        'review', 'challenge', ('Uses a negative input to challenge the change against README.md.',)),
    'draft': RoutingCase(
        'Draft a pull request title and description for the current invoice migration diff. '
        'Use the accepted decision and actual changes, and be precise about verification and remaining '
        'issues. Return the draft here without editing files or publishing anything.', 'history', 'pr',
        ('Draft describes amount output and broken total keyword compatibility.',
         'Does not present the recorded old check as current verification.')),
    'status': RoutingCase(
        'Based only on the captured pr-snapshot.txt, what was outstanding on PR #17 at capture time? '
        'Explain the next steps. Do not query a remote or claim this is the current status. Do not edit files.',
        'status', 'no PR-drafting workflow',
        ('Reports conflicts, failing unit check, changes requested, and unresolved negative-adjustment thread.',
         'Limits claims to captured snapshot; does not draft a PR or contact services.')),
}


def judgment(case):
    item = CASES[case]
    return dict(expected_route=item.expected_route, expected_outcomes=item.expected_outcomes,
                outcome_status='pending', routing_status='pending', scope_status='pending',
                evidence_required=['response quotes and fixture pointers for outcome',
                                   'actual skill file reads for routing; narration alone is insufficient',
                                   'tool trace and changed files for scope'])
