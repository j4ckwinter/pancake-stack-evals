from pathlib import Path
import tempfile
import unittest

from behavioral.validation import assess_validation, prepare_validation, revise_verify, GUARD, run_tests, mutant_sources


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name) / 'project'
        self.before = prepare_validation(self.workspace)

    def test_weak_suite_survives_mutant(self):
        result = assess_validation(self.workspace, self.before)
        self.assertTrue(result['control_passed'])
        self.assertFalse(result['mutants_killed'])
        self.assertFalse(result['passed'])

    def test_focused_suite_kills_mutant(self):
        test = self.workspace / 'test_reader.py'
        test.write_text(test.read_text() + '''
    def test_version_types(self):
        for version, field in [(True, 'total'), (1.0, 'total'), (2.0, 'amount')]:
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    read_total({'version': version, 'invoice': {field: 12}})
''')
        result = assess_validation(self.workspace, self.before)
        self.assertTrue(result['passed'], result)
        for mutant in result['mutants'].values():
            self.assertEqual(result['control']['test_ids'], mutant['test_ids'])
            self.assertEqual(mutant['errors'], [])
            self.assertTrue(mutant['killed'])

    def test_control_and_mutant_accept_valid_neighbors(self):
        source = (self.workspace / 'reader.py').read_text()
        for implementation in (source, *mutant_sources(source).values()):
            result = run_tests(self.workspace, implementation)
            self.assertEqual(result['errors'], [])
            self.assertEqual(result['failures'], [])
            self.assertEqual(result['tests_run'], 2)

    def test_errors_are_not_mutant_detection(self):
        (self.workspace / 'test_reader.py').write_text('raise RuntimeError("broken import")\n')
        result = assess_validation(self.workspace, self.before)
        self.assertFalse(result['passed'])
        self.assertFalse(result['mutants_killed'])

    def test_no_tests_is_not_success(self):
        (self.workspace / 'test_reader.py').write_text('')
        self.assertFalse(assess_validation(self.workspace, self.before)['passed'])

    def test_scope_preserves_production(self):
        (self.workspace / 'reader.py').write_text('')
        with self.assertRaisesRegex(AssertionError, 'protected'):
            assess_validation(self.workspace, self.before)

    def test_scope_rejects_additions(self):
        (self.workspace / 'extra.py').write_text('')
        with self.assertRaisesRegex(AssertionError, 'added or deleted'):
            assess_validation(self.workspace, self.before)

    def test_treatment_requires_one_anchor(self):
        from behavioral.validation import ANCHOR
        revised = revise_verify('before ' + ANCHOR + ' after')
        self.assertTrue(revised.startswith('before ' + ANCHOR))
        self.assertTrue(revised.endswith(' after'))
        for invalid in ('absent', ANCHOR * 2, revised):
            with self.assertRaises(ValueError):
                revise_verify(invalid)

    def test_skipped_coverage_is_not_success(self):
        test = self.workspace / 'test_reader.py'
        test.write_text(test.read_text().replace('    def test_boolean_version',
                                               '    @unittest.skip("not exercised")\n    def test_boolean_version'))
        self.assertFalse(assess_validation(self.workspace, self.before)['control_passed'])

    def test_treatment_hashes_change_only_verify(self):
        from behavioral.validation import ANCHOR, treatment_hashes
        source = Path(self.temp.name) / 'source'
        (source / 'skills/verify').mkdir(parents=True)
        (source / 'docs').mkdir()
        (source / 'skills/verify/SKILL.md').write_text(ANCHOR)
        (source / 'docs/configuration.md').write_text('configuration')
        hashes = treatment_hashes(source)
        self.assertNotEqual(hashes['baseline']['skills/verify/SKILL.md'],
                            hashes['revised']['skills/verify/SKILL.md'])
        self.assertEqual(hashes['baseline']['docs/configuration.md'],
                         hashes['revised']['docs/configuration.md'])
        self.assertEqual((source / 'skills/verify/SKILL.md').read_text(), ANCHOR)

    def test_single_type_coverage_is_insufficient(self):
        test = self.workspace / 'test_reader.py'
        original = test.read_text()
        for kind, version, field in [('bool', 'True', 'total'), ('float', '2.0', 'amount')]:
            with self.subTest(kind=kind):
                test.write_text(original + f"\n    def test_one_type(self):\n        with self.assertRaises(ValueError):\n            read_total({{'version': {version}, 'invoice': {{'{field}': 12}}}})\n")
                result = assess_validation(self.workspace, self.before)
                self.assertTrue(result['control_passed'])
                self.assertFalse(result['passed'])
                self.assertTrue(result['mutants'][kind]['killed'])
                other = 'float' if kind == 'bool' else 'bool'
                self.assertFalse(result['mutants'][other]['killed'])
