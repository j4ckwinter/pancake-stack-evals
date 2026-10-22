"""Synthetic public acceptance paths; expectations never enter trial workspaces."""
import difflib
from pathlib import Path

from .support import snapshot
from .workflow_cases import Case

REQUEST = ('Review change.diff against the current project for actionable problems. '
           'Inspect relevant contracts and report findings with evidence. Do not edit files.')

RESCHEDULE = '''def reschedule(current: dict[str, int], moves: dict[str, int]) -> dict[str, int]:
    if any(type(slot) is not int or not 0 <= slot <= 5 for slot in current.values()):
        raise ValueError("invalid current slot")
    if len(set(current.values())) != len(current):
        raise ValueError("duplicate current slot")
    for booking, target in moves.items():
        if booking not in current or type(target) is not int or not 0 <= target <= 5:
            raise ValueError("invalid move")
    final = dict(current)
    final.update(moves)
    if len(set(final.values())) != len(final):
        raise ValueError("duplicate final slot")
    return final
'''
CHECKOUT = '''def checkout(gross: int, voucher: int, wallet: int) -> dict[str, int]:
    if any(type(value) is not int for value in (gross, voucher, wallet)):
        raise ValueError("amounts must be integers")
    if gross <= 0 or voucher < 0 or wallet < 0 or voucher > gross:
        raise ValueError("invalid amount")
    net = gross - voucher
    remaining = wallet - net
    if remaining < 0:
        raise ValueError("insufficient wallet")
    return {"charged": net, "remaining": remaining}
'''
ORIGINALS = {'reschedule': RESCHEDULE, 'checkout': CHECKOUT}
CONTRACTS = {
    'reschedule': '''reschedule(current: dict[str, int], moves: dict[str, int]) -> dict[str, int]

Callers supply dictionaries with string booking IDs. These are caller preconditions.
Current slots must be unique exact integers from 0 to 5.
Moves map existing booking IDs to exact integer slots from 0 to 5.
Apply all moves simultaneously. Swaps and cycles are permitted when final slots
are unique. Reject invalid current slots, unknown IDs, invalid move slots, or
duplicate final slots with ValueError. Return a new mapping and preserve both inputs.
Run python3 -B -m unittest.
''',
    'checkout': '''checkout(gross: int, voucher: int, wallet: int) -> dict[str, int]

All amounts are exact integer cents. Gross must be positive. Voucher and wallet
must be nonnegative, and voucher cannot exceed gross. Apply the voucher before
charging the wallet. Require wallet >= gross - voucher. Return a receipt with
charged equal to gross - voucher and remaining equal to wallet - charged.
Reject invalid amounts and insufficient wallet with ValueError.
Run python3 -B -m unittest.
''',
}
VISIBLE_TESTS = {
    'reschedule': '''import unittest
from app import reschedule

class BookingTests(unittest.TestCase):
    def test_vacant(self):
        self.assertEqual(reschedule({'A': 1, 'B': 2}, {'A': 3}), {'A': 3, 'B': 2})
    def test_occupied(self):
        with self.assertRaises(ValueError):
            reschedule({'A': 1, 'B': 2}, {'A': 2})
    def test_invalid(self):
        for moves in ({'Z': 3}, {'A': 6}, {'A': True}):
            with self.assertRaises(ValueError):
                reschedule({'A': 1}, moves)
''',
    'checkout': '''import unittest
from app import checkout

class CheckoutTests(unittest.TestCase):
    def test_discount(self):
        self.assertEqual(checkout(1000, 400, 1200), {'charged': 600, 'remaining': 600})
    def test_insufficient(self):
        with self.assertRaises(ValueError):
            checkout(1000, 0, 999)
    def test_invalid(self):
        for voucher in (-1, 1001, True):
            with self.assertRaises(ValueError):
                checkout(1000, voucher, 1200)
''',
}


def revised(domain, outcome):
    if outcome not in ('bug', 'clean'):
        raise ValueError('unknown outcome')
    original = ORIGINALS[domain]
    if domain == 'reschedule':
        condition = 'other != booking' if outcome == 'bug' else 'other != booking and other not in moves'
        gate = ('    for booking, target in moves.items():\n'
                '        for other, occupied in current.items():\n'
                f'            if {condition} and occupied == target:\n'
                '                raise ValueError("occupied target")\n')
        return original.replace('    final = dict(current)\n', gate + '    final = dict(current)\n')
    bound = 'gross' if outcome == 'bug' else 'net'
    return original.replace('    remaining = wallet - net\n',
                            f'    if wallet < {bound}:\n'
                            '        raise ValueError("insufficient wallet")\n'
                            '    remaining = wallet - net\n')


def prepare_case(case, destination):
    domain, outcome = case.rsplit('-', 1)
    changed = revised(domain, outcome)
    destination = Path(destination)
    destination.mkdir()
    files = {'app.py': changed, 'README.md': CONTRACTS[domain],
             'test_app.py': VISIBLE_TESTS[domain], 'change.diff': ''.join(difflib.unified_diff(
                 ORIGINALS[domain].splitlines(True), changed.splitlines(True),
                 fromfile='a/app.py', tofile='b/app.py'))}
    for name, content in files.items():
        (destination / name).write_text(content)
    return snapshot(destination)


def assess_case(case, workspace, before, profile):
    return {'passed': None, 'scope_preserved': snapshot(workspace) == before,
            'status': 'pending manual response judgment'}


CASES = {f'{domain}-{outcome}': Case(REQUEST, 'skills/check/SKILL.md', True,
                                   prepare_case, assess_case)
         for domain in ORIGINALS for outcome in ('bug', 'clean')}


def judgment(case):
    domain, outcome = case.rsplit('-', 1)
    issue = {'reschedule': 'Occupancy preflight rejects valid simultaneous swaps and cycles.',
             'checkout': 'Gross affordability preflight rejects wallets that fund the net charge.'}
    return {'expected_issue': issue[domain] if outcome == 'bug' else None,
            'outcome_status': 'pending', 'false_positive_status': 'pending',
            'execution_evidence_status': 'pending',
            'criteria': ['Cite response and inspected code for defect detection or unsupported findings.',
                         'Distinguish actual API execution from static trace and verification limits.',
                         'Grade outcomes separately from input and artifact preservation.']}
