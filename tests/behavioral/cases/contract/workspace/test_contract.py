import unittest
from producer import create_invoice
from consumer import read_total
from archive import read_total as read_archive


class ContractTests(unittest.TestCase):
    def test_round_trip(self):
        self.assertEqual(read_total(create_invoice(19.5)), 19.5)

    def test_archive(self):
        self.assertEqual(read_archive({"version": 1, "invoice": {"total": 19.5}}), 19.5)
