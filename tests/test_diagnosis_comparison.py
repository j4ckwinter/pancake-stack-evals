import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from behavioral import coordination_cases as cases


class DiagnosisControls(unittest.TestCase):
    def test_quote_oracle_accepts_partitioned_cache_and_rejects_shortcuts(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / 'quotes'
            before = cases.prepare_case('account-quotes', workspace)
            existing = subprocess.run([sys.executable, '-B', '-m', 'unittest'], cwd=workspace,
                                      text=True, capture_output=True, timeout=5)
            self.assertEqual(existing.returncode, 0, existing.stderr)
            observed = subprocess.run([sys.executable, '-B', 'quote_cli.py'], cwd=workspace,
                input='{"account":"north","sku":"Widget"}\n{"account":"south","sku":"Widget"}\n',
                text=True, capture_output=True, timeout=5)
            self.assertEqual(observed.returncode, 0, observed.stderr)
            self.assertEqual([json.loads(line) for line in observed.stdout.splitlines()],
                             [{'amount': 120}, {'amount': 120}])
            original = (workspace / 'quotes.py').read_text()
            repaired = original.replace('key = sku', 'key = (account.strip().casefold(), sku)')
            mutations = [original, repaired.replace('if key in self.cache:', 'if False:'),
                         repaired.replace('casefold(), sku)', 'casefold(), sku.casefold())'),
                         repaired.replace('return self.cache[key]', 'return abs(self.cache[key])'),
                         repaired.replace('account.strip().casefold()', 'account'),
                         repaired.replace('key = (', 'if account == "missing": account = "north"\n        key = ('),
                         repaired.replace('class QuoteService:', 'class QuoteService:\n    cache = {}').replace(
                             'self.cache = {}', 'self.cache = self.__class__.cache')]
            for content in mutations:
                (workspace / 'quotes.py').write_text(content)
                with self.assertRaises(AssertionError):
                    cases.probe('account-quotes', workspace)
            (workspace / 'quotes.py').write_text(repaired)
            cases.probe('account-quotes', workspace)
            (workspace / 'test_quotes.py').write_text('pass\n')
            self.assertTrue(cases.scope_preserved('account-quotes', workspace, before))
            (workspace / 'data/catalog.json').write_text('{}\n')
            self.assertFalse(cases.scope_preserved('account-quotes', workspace, before))
            with self.assertRaises(AssertionError):
                cases.probe('account-quotes', workspace)
