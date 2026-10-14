import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from behavioral import historical_review as history
from behavioral import review
from behavioral.support import snapshot
from test_comparison_fixtures import fix_contract, READER


class HistoricalReviewTests(unittest.TestCase):
    def test_immutable_snapshot_and_counterfactual_scope(self):
        record = history.provenance()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            faulty = history.prepare_case('migration-faulty', root / 'faulty')
            clean = history.prepare_case('migration-clean', root / 'clean')
            self.assertEqual({k: v for k, v in faulty.items() if k != 'change.diff'}, record['files'])
            self.assertEqual({name for name in faulty if faulty[name] != clean[name]},
                             {'tests/behavioral/support.py', 'change.diff'})
            for case in ('faulty', 'clean'):
                diff = (root / case / 'change.diff').read_text()
                self.assertIn('"contract": Scenario', diff)
                self.assertIn('tests/behavioral/cases/contract/request.txt', diff)
                self.assertNotIn('valid-migration-rejected', diff)
            self.assertNotIn('test_contract_accepts_shared_modules',
                            (root / 'clean/tests/test_comparison_fixtures.py').read_text())
            fixture = root / 'tampered'
            import shutil
            shutil.copytree(history.FIXTURE, fixture)
            with patch.object(history, 'FIXTURE', fixture):
                (fixture / 'repaired-support.py.txt').write_text('tampered')
                with self.assertRaisesRegex(ValueError, 'artifact mismatch'):
                    history.prepare_case('migration-clean', root / 'rejected')
                self.assertFalse((root / 'rejected').exists())
                (fixture / 'provenance.json').write_text('{}')
                with self.assertRaisesRegex(ValueError, 'provenance mismatch'):
                    history.provenance()

    def test_real_assessor_accepts_valid_migration_only_after_production_repair(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for case in history.CASES:
                with self.subTest(case=case):
                    repository = root / case
                    history.prepare_case(case, repository)
                    work = root / (case + '-implementation')
                    import shutil
                    shutil.copytree(repository / 'tests/behavioral/cases/contract/workspace', work)
                    before = snapshot(work)
                    fix_contract(work)
                    (work / 'lib').mkdir()
                    shared = READER.replace('def read_total(payload):', 'def read_total(payload, versions):').replace('VERSIONS', 'versions')
                    (work / 'lib/invoice.py').write_text(shared)
                    for name, versions in [('consumer.py', '(2,)'), ('archive.py', '(1, 2)')]:
                        (work / name).write_text('from lib.invoice import read_total as read_invoice\n'
                            f'def read_total(payload):\n    return read_invoice(payload, {versions})\n')
                    billing = (work / 'billing.py').read_text()
                    readme = (work / 'README.md').read_text()
                    (work / 'billing.py').write_text('from producer import create_invoice\n'
                        'def invoice_for_order(total):\n    return create_invoice(total)\n')
                    (work / 'README.md').write_text(readme + '\nReaders share invoice validation.\n')
                    script = ('import sys,json; sys.path.insert(0, ' + repr(str(repository / 'tests')) + '); '
                              'from behavioral.support import assess; '
                              'work,before=json.load(sys.stdin); print(assess("contract",work,before))')
                    def assess():
                        return subprocess.run([sys.executable, '-I', '-B', '-c', script],
                            input=json.dumps([str(work), before]), text=True, capture_output=True, timeout=30,
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
                    result = assess()
                    if case == 'migration-faulty':
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('protected file changed: README.md', result.stderr)
                        (work / 'README.md').write_text(readme)
                        result = assess()
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('protected file changed: billing.py', result.stderr)
                        (work / 'billing.py').write_text(billing)
                        result = assess()
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('unrelated file added: lib/invoice.py', result.stderr)
                    else:
                        self.assertEqual((result.returncode, result.stdout), (0, 'artifact checks passed\n'), result.stderr)
                        for name in ('notes.txt', 'archive.json'):
                            original = (work / name).read_bytes()
                            (work / name).write_text('unrelated mutation')
                            result = assess()
                            self.assertNotEqual(result.returncode, 0)
                            self.assertIn(f'protected file changed: {name}', result.stderr)
                            (work / name).write_bytes(original)
                        (work / 'unrelated.json').write_text('{}')
                        result = assess()
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('outside automatic assessment scope', result.stderr)

    def test_current_assessor_rejects_independent_contract_regressions(self):
        self.assert_contract_regressions_rejected(current=True)

    def test_calibrated_control_rejects_independent_contract_regressions(self):
        self.assert_contract_regressions_rejected(current=False)

    def assert_contract_regressions_rejected(self, current):
        import shutil
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = Path(__file__).resolve().parents[1] if current else root / 'repository'
            if not current:
                history.prepare_case('migration-clean', repository)
            work = root / 'implementation'
            shutil.copytree(repository / 'tests/behavioral/cases/contract/workspace', work)
            before = snapshot(work)
            fix_contract(work)
            script = ('import sys,json; sys.path.insert(0, ' + repr(str(repository / 'tests')) + '); '
                      'from behavioral.support import assess; '
                      'work,before=json.load(sys.stdin); print(assess("contract",work,before))')
            def assess():
                return subprocess.run([sys.executable, '-I', '-B', '-c', script],
                    input=json.dumps([str(work), before]), text=True, capture_output=True, timeout=30)
            self.assertEqual(assess().returncode, 0)
            # Each mutant accepts just one prohibited v1 payload; all other
            # behavior delegates to the compliant reader.
            bad_records = [
                {'version': 1, 'invoice': {'total': True}},
                {'version': 1, 'invoice': {'total': '1'}},
                {'version': 1, 'invoice': {'total': 1, 'extra': 1}},
                {'version': 1, 'invoice': {'total': 1}, 'extra': 1},
                {'version': 1, 'invoice': None},
                {'version': 1.0, 'invoice': {'total': 1}},
                {'version': 2.0, 'invoice': {'amount': 1}},
            ]
            original = (work / 'archive.py').read_text()
            for payload in bad_records:
                with self.subTest(payload=payload):
                    mutant = original.replace('def read_total(', 'def strict_read(')
                    mutant += ('\ndef read_total(payload):\n'
                               f'    if repr(payload) == {repr(repr(payload))}: return 1\n'
                               '    return strict_read(payload)\n')
                    (work / 'archive.py').write_text(mutant)
                    result = assess()
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('malformed record accepted', result.stderr)
            (work / 'archive.py').write_text(original)
            # Each reader/version mutant accepts False only, keeping True and
            # all other malformed values strict. Boolean equality with zero
            # must not hide the missing invalid-input probe.
            for filename, version, field in [('archive.py', 1, 'total'),
                                             ('archive.py', 2, 'amount'),
                                             ('consumer.py', 2, 'amount')]:
                with self.subTest(reader=filename, version=version, value=False):
                    source = (work / filename).read_text()
                    mutant = source.replace('def read_total(', 'def strict_read(')
                    mutant += ('\ndef read_total(payload):\n'
                               '    if (isinstance(payload, dict)\n'
                               f'            and payload.get("version") == {version}\n'
                               '            and isinstance(payload.get("invoice"), dict)\n'
                               f'            and payload["invoice"].get({field!r}) is False):\n'
                               '        return 0\n'
                               '    return strict_read(payload)\n')
                    try:
                        (work / filename).write_text(mutant)
                        result = assess()
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('malformed record accepted', result.stderr)
                    finally:
                        (work / filename).write_text(source)
            producer = (work / 'producer.py').read_text()
            # Preserve the existing 19.5 round-trip test while breaking other
            # values already exercised by trusted checks.
            (work / 'producer.py').write_text(producer.replace(
                '"version": 2', '"version": (2 if total == 19.5 else 2.0)'))
            with self.subTest(defect="float producer version"):
                self.assertNotEqual(assess().returncode, 0)
            (work / 'producer.py').write_text(producer)
            tests = (work / 'test_contract.py').read_text()
            (work / 'test_contract.py').write_text('')
            result = assess()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('no regression tests discovered', result.stderr)
            # Skipped subtests are counted separately from executed methods.
            # They must not invalidate the two retained passing tests.
            (work / 'test_contract.py').write_text(tests +
                '\nclass ExtraTests(unittest.TestCase):\n'
                '    def test_skipped_subtests(self):\n'
                '        for value in range(3):\n'
                '            with self.subTest(value=value):\n'
                '                self.skipTest("optional")\n')
            self.assertEqual(assess().returncode, 0)

    def test_calibration_artifacts_are_pinned_and_patch_is_exact(self):
        import shutil
        history.calibration()
        metadata = history.provenance()
        original = json.loads((history.FIXTURE / 'provenance.json').read_text())
        self.assertEqual(metadata['historical_clean_control'], original['clean_control'])
        self.assertIn('calibrated-support.py.txt', metadata['clean_control'])
        self.assertEqual(metadata['calibration']['manifest_sha256'], history.CALIBRATION_SHA256)
        self.assertIsNone(metadata['calibration']['historical_revision'])
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / 'fixture'
            shutil.copytree(history.FIXTURE, fixture)
            with patch.object(history, 'FIXTURE', fixture):
                for name in ('calibration.json', 'calibration.diff', 'calibrated-support.py.txt'):
                    original = (fixture / name).read_bytes()
                    (fixture / name).write_text('tampered')
                    with self.assertRaisesRegex(ValueError, 'calibration'):
                        history.prepare_case('migration-clean', Path(temporary) / 'rejected')
                    self.assertFalse((Path(temporary) / 'rejected').exists())
                    (fixture / name).write_bytes(original)

    def test_adjudication_counts_mechanisms_and_clean_false_positives(self):
        self.assertEqual(review.score('migration-faulty', ['valid-migration-rejected'] * 2, 0, cases=history.CASES),
            {'expected_defects': 1, 'detected_defects': 1, 'missed_defects': 0, 'false_findings': 0, 'clean_control': False})
        self.assertEqual(review.score('migration-clean', [], 1, cases=history.CASES)['false_findings'], 1)
        with self.assertRaises(ValueError):
            review.score('migration-clean', ['valid-migration-rejected'], 0, cases=history.CASES)
