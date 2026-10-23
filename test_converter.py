"""
Test suite for Bukku Accounting Converter
Validates parsing accuracy, mathematical consistency, and template generation.
"""

import unittest
import os
from pathlib import Path
from converter import BukkuStatementConverter

BUKKU_FOLDER = Path(r"G:\My Drive\RPWP HEALTHCARE MASTER FOLDER\HEARING CENTRE\ACCOUNTING\BUKKU")

class TestBukkuConverter(unittest.TestCase):
    def setUp(self):
        self.converter = BukkuStatementConverter(fill_empty_description=True, ref_style="standard")
        self.test_output_dir = Path(__file__).parent / "test_output"
        self.test_output_dir.mkdir(exist_ok=True)

    def test_august_2026_bank_islam(self):
        aug_file = BUKKU_FOLDER / "Ogos 2026 transaction_history.csv"
        self.assertTrue(aug_file.exists(), f"August file not found: {aug_file}")

        res = self.converter.parse_file(aug_file)
        summary = res.to_summary_dict()

        # Check bank identity and account
        self.assertEqual(res.bank_name, "Bank Islam (Malaysia)")
        self.assertEqual(res.account_no, "12029010086201")

        # Check dates
        self.assertEqual(res.from_date, "01/08/2026")
        self.assertEqual(res.to_date, "31/08/2026")

        # Check transactions count
        self.assertEqual(len(res.transactions), 43)

        # Check exact totals matching Bank Islam's footer
        self.assertAlmostEqual(res.total_spent, 20967.04, places=2)
        self.assertAlmostEqual(res.total_received, 58108.93, places=2)
        self.assertEqual(res.closing_balance, "89069.17")
        self.assertEqual(summary["verification_status"], "PASS")

        # Check date format without timestamp (Y-m-d)
        self.assertEqual(res.transactions[0]["date"], "2026-08-03")
        self.assertNotIn(":", res.transactions[0]["date"])

        # Check DMY mode without timestamp
        converter_dmy = BukkuStatementConverter(date_format="dmy")
        res_dmy = converter_dmy.parse_file(aug_file)
        self.assertEqual(res_dmy.transactions[0]["date"], "03/08/2026")
        self.assertNotIn(":", res_dmy.transactions[0]["date"])

        # Test CSV export
        csv_out = self.test_output_dir / "test_bukku_august_2026.csv"
        self.converter.export_bukku_csv(res, csv_out)
        self.assertTrue(csv_out.exists())

        # Test XLSX export
        xlsx_out = self.test_output_dir / "test_bukku_august_2026.xlsx"
        self.converter.export_bukku_xlsx(res, xlsx_out)
        self.assertTrue(xlsx_out.exists())

    def test_september_2026_bank_islam(self):
        sep_file = BUKKU_FOLDER / "September 2026 transaction_history.csv"
        self.assertTrue(sep_file.exists(), f"September file not found: {sep_file}")

        res = self.converter.parse_file(sep_file)
        summary = res.to_summary_dict()

        self.assertEqual(res.bank_name, "Bank Islam (Malaysia)")
        self.assertEqual(res.account_no, "12029010086201")
        self.assertEqual(res.from_date, "01/09/2026")
        self.assertEqual(res.to_date, "30/09/2026")
        self.assertEqual(len(res.transactions), 29)
        self.assertAlmostEqual(res.total_spent, 29481.70, places=2)
        self.assertAlmostEqual(res.total_received, 48988.40, places=2)
        self.assertEqual(res.closing_balance, "108575.87")
        self.assertEqual(summary["verification_status"], "PASS")

        csv_out = self.test_output_dir / "test_bukku_september_2026.csv"
        self.converter.export_bukku_csv(res, csv_out)
        self.assertTrue(csv_out.exists())

    def test_type_b_raw_bank_islam(self):
        raw_file = BUKKU_FOLDER / "transaction_history (1).csv"
        self.assertTrue(raw_file.exists(), f"Raw file not found: {raw_file}")

        res = self.converter.parse_file(raw_file)
        self.assertEqual(res.account_no, "12029010086201")
        self.assertGreater(len(res.transactions), 0)
        self.assertTrue(res.closing_balance)

if __name__ == "__main__":
    unittest.main()
