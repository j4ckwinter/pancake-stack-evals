import unittest
from reader import read_total


class ReaderTests(unittest.TestCase):
    def test_supported_versions(self):
        self.assertEqual(read_total({"version": 1, "invoice": {"total": 12}}), 12)
        self.assertEqual(read_total({"version": 2, "invoice": {"amount": 12}}), 12)

    def test_boolean_version(self):
        with self.assertRaises(ValueError):
            read_total({"version": True, "invoice": {"amount": 12}})
