
import sys
import unittest

sys.path.insert(0, "src")

from settlement_service import simplify_debts


class TestDebtSimplification(unittest.TestCase):

    def test_normal_case(self):
        """Kiểm tra trường hợp có nhiều người nợ và người được nhận."""

        net_balances = [
            {"user_id": 1, "net_balance": 500000},
            {"user_id": 2, "net_balance": 300000},
            {"user_id": 3, "net_balance": -400000},
            {"user_id": 4, "net_balance": -400000}
        ]

        transactions = simplify_debts(net_balances)
        
        # Verify each member's settlement amount
        for member in net_balances:
            user_id = member["user_id"]
            balance = member["net_balance"]

            if balance > 0:
                received = sum(
                    t["amount"]
                    for t in transactions
                    if t["to_user_id"] == user_id
                )
                self.assertEqual(received, balance)

            elif balance < 0:
                paid = sum(
                    t["amount"]
                    for t in transactions
                    if t["from_user_id"] == user_id
                )
                self.assertEqual(paid, abs(balance))

        # Verify transaction validity
        for transaction in transactions:
            self.assertNotEqual(
                transaction["from_user_id"],
                transaction["to_user_id"]
            )
            self.assertIs(type(transaction["amount"]), int)
            self.assertGreater(transaction["amount"], 0)

        self.assertEqual(len(transactions), 3)

        total_transferred = sum(
            transaction["amount"]
            for transaction in transactions
        )

        self.assertEqual(total_transferred, 800000)

    def test_empty_list(self):
        """Danh sách rỗng phải trả về danh sách giao dịch rỗng."""

        result = simplify_debts([])

        self.assertEqual(result, [])

    def test_all_balances_zero(self):
        """Không ai nợ hoặc được nhận tiền."""

        net_balances = [
            {"user_id": 1, "net_balance": 0},
            {"user_id": 2, "net_balance": 0}
        ]

        result = simplify_debts(net_balances)

        self.assertEqual(result, [])
    def test_unbalanced_net_balances(self):
            """Tổng Net Balance khác 0 phải bị từ chối."""
    
            net_balances = [
                {"user_id": 1, "net_balance": 500000},
                {"user_id": 2, "net_balance": -300000}
            ]
    
            with self.assertRaises(ValueError):
                simplify_debts(net_balances)
    def test_non_integer_balances(self):
        """Net Balance không được là float hoặc bool."""

        invalid_cases = [
            [
                {"user_id": 1, "net_balance": 100.5},
                {"user_id": 2, "net_balance": -100.5}
            ],
            [
                {"user_id": 1, "net_balance": True},
                {"user_id": 2, "net_balance": -1}
            ]
        ]

        for net_balances in invalid_cases:
            with self.subTest(net_balances=net_balances):
                with self.assertRaises(ValueError):
                    simplify_debts(net_balances)
    def test_duplicate_user_ids(self):
        """Không cho phép user_id bị trùng."""

        net_balances = [
            {"user_id": 1, "net_balance": 500000},
            {"user_id": 1, "net_balance": -500000}
        ]

        with self.assertRaises(ValueError):
            simplify_debts(net_balances)
    def test_invalid_user_ids(self):
        """User ID phải là số nguyên dương."""

        invalid_ids = [0, -1, 1.5, True, "1"]

        for invalid_id in invalid_ids:
            with self.subTest(user_id=invalid_id):
                net_balances = [
                    {"user_id": invalid_id, "net_balance": 100000},
                    {"user_id": 2, "net_balance": -100000}
                ]

                with self.assertRaises(ValueError):
                    simplify_debts(net_balances)
    def test_invalid_input_structure(self):
        """Kiểm tra dữ liệu đầu vào sai cấu trúc."""

        invalid_cases = [
            None,
            "invalid",
            123,
            [{"user_id": 1}],
            [{"net_balance": 100000}],
            [123]
        ]

        for invalid_data in invalid_cases:
            with self.subTest(data=invalid_data):
                with self.assertRaises(ValueError):
                    simplify_debts(invalid_data)
if __name__ == "__main__":
    unittest.main(verbosity=2)

   