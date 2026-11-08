
import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

import settlement_service


class TestNetBalance(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(
            Path(self.temp_dir.name) / "test.db"
        )

        settlement_service.DATABASE_PATH = self.db_path

        connection = sqlite3.connect(self.db_path)

        connection.executescript("""
            CREATE TABLE group_members (
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (group_id, user_id)
            );

            CREATE TABLE expenses (
                expense_id INTEGER PRIMARY KEY,
                group_id INTEGER NOT NULL,
                payer_user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL
            );

            CREATE TABLE expense_details (
                detail_id INTEGER PRIMARY KEY,
                expense_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                owed_amount INTEGER NOT NULL
            );
        """)

        connection.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_normal_calculation(self):
        connection = sqlite3.connect(self.db_path)

        connection.executemany(
            "INSERT INTO group_members VALUES (?, ?)",
            [(1, 1), (1, 2), (1, 3)]
        )

        connection.executemany(
            "INSERT INTO expenses VALUES (?, ?, ?, ?)",
            [
                (1, 1, 1, 100000),
                (2, 1, 2, 50000)
            ]
        )

        connection.executemany(
            "INSERT INTO expense_details VALUES (?, ?, ?, ?)",
            [
                (1, 1, 1, 30000),
                (2, 1, 2, 30000),
                (3, 1, 3, 40000),
                (4, 2, 1, 20000),
                (5, 2, 2, 10000),
                (6, 2, 3, 20000)
            ]
        )

        connection.commit()
        connection.close()

        results = settlement_service.calculate_net_balances(1)

        self.assertEqual(
            results,
            [
                {
                    "user_id": 1,
                    "total_paid": 100000,
                    "total_owed": 50000,
                    "net_balance": 50000
                },
                {
                    "user_id": 2,
                    "total_paid": 50000,
                    "total_owed": 40000,
                    "net_balance": 10000
                },
                {
                    "user_id": 3,
                    "total_paid": 0,
                    "total_owed": 60000,
                    "net_balance": -60000
                }
            ]
        )

    def test_group_without_expenses(self):
        connection = sqlite3.connect(self.db_path)

        connection.executemany(
            "INSERT INTO group_members VALUES (?, ?)",
            [(2, 1), (2, 2)]
        )

        connection.commit()
        connection.close()

        results = settlement_service.calculate_net_balances(2)

        self.assertEqual(
            [member["net_balance"] for member in results],
            [0, 0]
        )

    def test_group_without_members(self):
        with self.assertRaises(ValueError):
            settlement_service.calculate_net_balances(999)

    def test_unbalanced_expense_data(self):
        connection = sqlite3.connect(self.db_path)

        connection.execute(
            "INSERT INTO group_members VALUES (?, ?)",
            (3, 1)
        )

        connection.execute(
            "INSERT INTO expenses VALUES (?, ?, ?, ?)",
            (1, 3, 1, 100000)
        )

        connection.execute(
            "INSERT INTO expense_details VALUES (?, ?, ?, ?)",
            (1, 1, 1, 90000)
        )

        connection.commit()
        connection.close()

        with self.assertRaises(ValueError):
            settlement_service.calculate_net_balances(3)


if __name__ == "__main__":
    unittest.main()

