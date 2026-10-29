
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import validate_orders, reconcile


class TestDataReconciliation(unittest.TestCase):

    def test_valid_orders(self):
        rows = [
            {"order_id": "ORD001", "amount": "500"},
            {"order_id": "ORD002", "amount": "300"}
        ]

        valid, rejected = validate_orders(rows, "test.csv")

        self.assertEqual(len(valid), 2)
        self.assertEqual(len(rejected), 0)

    def test_missing_order_id(self):
        rows = [
            {"order_id": "", "amount": "150"}
        ]

        valid, rejected = validate_orders(rows, "test.csv")

        self.assertEqual(len(valid), 0)
        self.assertEqual(rejected[0]["reject_reason"], "missing_order_id")

    def test_invalid_amount(self):
        rows = [
            {"order_id": "ORD005", "amount": "abc"}
        ]

        valid, rejected = validate_orders(rows, "test.csv")

        self.assertEqual(len(valid), 0)
        self.assertEqual(rejected[0]["reject_reason"], "invalid_amount")

    def test_duplicate_order_id(self):
        rows = [
            {"order_id": "ORD006", "amount": "250"},
            {"order_id": "ORD006", "amount": "250"}
        ]

        valid, rejected = validate_orders(rows, "test.csv")

        self.assertEqual(len(valid), 1)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["reject_reason"], "duplicate_order_id")

    def test_amount_mismatch(self):
        source = [{"order_id": "ORD001", "amount": "500"}]
        target = [{"order_id": "ORD001", "amount": "600"}]

        result = reconcile(source, target)

        self.assertEqual(result["amount_mismatches"], 1)
        self.assertEqual(result["matched_records"], 0)

    def test_missing_target_record(self):
        source = [{"order_id": "ORD001", "amount": "500"}]
        target = []

        result = reconcile(source, target)

        self.assertEqual(result["missing_from_target"], 1)
    
    def test_missing_source_record(self):
        source = []
        target = [{"order_id": "ORD002", "amount": "300"}]

        result = reconcile(source, target)

        self.assertEqual(result["missing_from_source"], 1)


    def test_matching_records(self):
        source = [{"order_id": "ORD001", "amount": "500"}]
        target = [{"order_id": "ORD001", "amount": "500"}]

        result = reconcile(source, target)

        self.assertEqual(result["matched_records"], 1)
        self.assertEqual(result["amount_mismatches"], 0)

    def test_empty_input(self):
        valid, rejected = validate_orders([], "test.csv")

        self.assertEqual(valid, [])
        self.assertEqual(rejected, [])

    def test_missing_amount(self):
        rows = [
            {"order_id": "ORD007", "amount": ""}
        ]

        valid, rejected = validate_orders(rows, "test.csv")

        self.assertEqual(len(valid), 0)
        self.assertEqual(rejected[0]["reject_reason"], "missing_amount")

    def test_whitespace_order_id(self):
        rows = [
            {"order_id": "   ", "amount": "150"}
        ]

        valid, rejected = validate_orders(rows, "test.csv")

        self.assertEqual(len(valid), 0)
        self.assertEqual(rejected[0]["reject_reason"], "missing_order_id")

    def test_negative_amount(self):
        rows = [
            {"order_id": "ORD008", "amount": "-100"}
        ]

        valid, rejected = validate_orders(rows, "test.csv")

        self.assertEqual(len(valid), 0)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["reject_reason"], "invalid_amount")

    def test_complete_successful_reconciliation(self):
        source = [
            {"order_id": "ORD001", "amount": "500"},
            {"order_id": "ORD002", "amount": "300"}
        ]
        target = [
            {"order_id": "ORD001", "amount": "500"},
            {"order_id": "ORD002", "amount": "300"}
        ]

        result = reconcile(source, target)

        self.assertEqual(result["matched_records"], 2)
        self.assertEqual(result["amount_mismatches"], 0)
        self.assertEqual(result["missing_from_source"], 0)
        self.assertEqual(result["missing_from_target"], 0)
    
    def test_aggregate_difference_from_amount_mismatch(self):
        source = [
            {"order_id": "ORD001", "amount": "500"},
            {"order_id": "ORD002", "amount": "300"}
        ]
        target = [
            {"order_id": "ORD001", "amount": "550"},
            {"order_id": "ORD002", "amount": "300"}
        ]

        result = reconcile(source, target)

        source_total = sum(int(row["amount"]) for row in source)
        target_total = sum(int(row["amount"]) for row in target)

        self.assertEqual(target_total - source_total, 50)
        self.assertEqual(result["amount_mismatches"], 1)
    
    def test_null_amount(self):
        rows = [
            {"order_id": "ORD009", "amount": None}
        ]

        valid, rejected = validate_orders(rows, "test.csv")

        self.assertEqual(len(valid), 0)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["reject_reason"], "missing_amount")
    
    def test_malformed_amount_with_extra_characters(self):
        rows = [
            {"order_id": "ORD010", "amount": "12abc"}
        ]

        valid, rejected = validate_orders(rows, "test.csv")

        self.assertEqual(len(valid), 0)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["reject_reason"], "invalid_amount")


    



if __name__ == "__main__":
    unittest.main()
