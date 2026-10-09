from pathlib import Path
import tempfile
import unittest

from behavioral.support import assess, prepare


PRODUCER = 'def create_invoice(total):\n    return {"version": 2, "invoice": {"amount": total}}\n'
READER = """def read_total(payload):
    if not isinstance(payload, dict) or set(payload) != {'version', 'invoice'}:
        raise ValueError('invalid envelope')
    version = payload['version']
    if type(version) is not int or version not in VERSIONS:
        raise ValueError('invalid version')
    field = 'total' if version == 1 else 'amount'
    invoice = payload['invoice']
    if not isinstance(invoice, dict) or set(invoice) != {field}:
        raise ValueError('invalid invoice')
    amount = invoice[field]
    if type(amount) not in (int, float) or amount < 0:
        raise ValueError('invalid amount')
    return amount
"""


def fix_contract(workspace):
    (workspace / 'producer.py').write_text(PRODUCER)
    (workspace / 'consumer.py').write_text(READER.replace('VERSIONS', '(2,)'))
    (workspace / 'archive.py').write_text(READER.replace('VERSIONS', '(1, 2)'))


class ComparisonFixtureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_label_requires_exact_fix_without_other_changes(self):
        workspace = self.root / 'workspace'
        before = prepare('label', workspace)
        with self.assertRaises(AssertionError):
            assess('label', workspace, before)
        source = workspace / 'cli.py'
        source.write_text(source.read_text().replace('Availble', 'Available'))
        self.assertEqual(assess('label', workspace, before), 'artifact checks passed')
        fixed = source.read_bytes()
        source.write_bytes(fixed.replace(b'\n', b'\r\n'))
        with self.assertRaises(AssertionError):
            assess('label', workspace, before)
        source.write_bytes(fixed)
        source.write_text(source.read_text() + '\n')
        with self.assertRaises(AssertionError):
            assess('label', workspace, before)
        source.write_text(source.read_text()[:-1])
        (workspace / 'test_added.py').write_text('')
        with self.assertRaises(AssertionError):
            assess('label', workspace, before)

    def test_contract_baseline_fails_and_complete_fix_passes(self):
        workspace = self.root / 'workspace'
        before = prepare('contract', workspace)
        with self.assertRaises(AssertionError):
            assess('contract', workspace, before)
        fix_contract(workspace)
        self.assertEqual(assess('contract', workspace, before), 'artifact checks passed')

    def test_contract_accepts_shared_modules_but_preserves_unrelated_files(self):
        workspace = self.root / 'workspace'
        before = prepare('contract', workspace)
        fix_contract(workspace)
        library = workspace / 'lib'
        library.mkdir()
        shared = READER.replace('def read_total(payload):', 'def read_total(payload, versions):').replace('VERSIONS', 'versions')
        (library / 'invoice.py').write_text(shared)
        for filename, versions in [('consumer.py', '(2,)'), ('archive.py', '(1, 2)')]:
            (workspace / filename).write_text(
                'from lib.invoice import read_total as read_invoice\n\n'
                f'def read_total(payload):\n    return read_invoice(payload, {versions})\n')
        (workspace / 'billing.py').write_text(
            'from producer import create_invoice\n\n'
            'def invoice_for_order(total):\n    return create_invoice(total)\n')
        (workspace / 'README.md').write_text((workspace / 'README.md').read_text() + '\nBoth readers share invoice validation.\n')
        self.assertEqual(assess('contract', workspace, before), 'artifact checks passed')
        notes = workspace / 'notes.txt'
        saved = notes.read_bytes()
        notes.write_text('unrelated edit')
        with self.assertRaisesRegex(AssertionError, 'protected file changed'):
            assess('contract', workspace, before)
        notes.write_bytes(saved)
        (workspace / 'unrelated.json').write_text('{}')
        with self.assertRaisesRegex(AssertionError, 'outside automatic assessment scope'):
            assess('contract', workspace, before)

        legacy = self.root / 'legacy'
        legacy_before = prepare('summary', legacy)
        (legacy / 'helper.py').write_text('')
        with self.assertRaisesRegex(AssertionError, 'unrelated file added'):
            assess('summary', legacy, legacy_before)

    def test_contract_rejects_independently_incomplete_migrations(self):
        mutations = {
            'keyword': ('producer.py', PRODUCER.replace('total', 'amount')),
            'consumer': ('consumer.py', "def read_total(payload):\n    return payload['invoice']['total']\n"),
            'archive': ('archive.py', READER.replace('VERSIONS', '(2,)')),
            'zero': ('consumer.py', READER.replace('VERSIONS', '(2,)').replace('return amount', 'return amount or 1')),
            'conflicts': ('consumer.py', READER.replace('VERSIONS', '(2,)').replace("set(invoice) != {field}", "field not in invoice")),
            'unknown_version': ('archive.py', READER.replace('VERSIONS', '(1, 2, 3)')),
            'negative': ('consumer.py', READER.replace('VERSIONS', '(2,)').replace(' or amount < 0', '')),
            'archive_rewrite': ('archive.json', '[]\n'),
            'facade': ('billing.py', 'def invoice_for_order(total):\n    return {}\n'),
        }
        for name, (filename, contents) in mutations.items():
            with self.subTest(name=name):
                workspace = self.root / name
                before = prepare('contract', workspace)
                fix_contract(workspace)
                (workspace / filename).write_text(contents)
                with self.assertRaises(AssertionError):
                    assess('contract', workspace, before)


if __name__ == '__main__':
    unittest.main()
