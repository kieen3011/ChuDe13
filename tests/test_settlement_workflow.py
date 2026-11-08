
import sqlite3
import sys
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

import settlement_service as service


class TestSettlementWorkflow(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        self.database_path = (
            Path(self.temp_dir.name) / "test_settlement.db"
        )

        self.database_patch = patch.object(
            service,
            "DATABASE_PATH",
            str(self.database_path)
        )

        self.database_patch.start()

        connection = sqlite3.connect(self.database_path)

        connection.execute("PRAGMA foreign_keys = ON")

        connection.executescript("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL
            );

            CREATE TABLE groups (
                group_id INTEGER PRIMARY KEY,
                group_name TEXT NOT NULL
            );

            CREATE TABLE group_members (
                group_member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                UNIQUE(user_id, group_id),
                FOREIGN KEY (user_id)
                    REFERENCES users(user_id),
                FOREIGN KEY (group_id)
                    REFERENCES groups(group_id)
            );

            CREATE TABLE settlements (
                settlement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL CHECK (amount > 0),
                status TEXT NOT NULL CHECK (
                    status IN ('PENDING', 'DISPUTED', 'CONFIRMED')
                ),
                sender_confirmed_at TEXT,
                receiver_confirmed_at TEXT,
                created_at TEXT NOT NULL,
                sender_resolved_at TEXT,
                receiver_resolved_at TEXT,
                CHECK (from_user_id != to_user_id),
                FOREIGN KEY (group_id)
                    REFERENCES groups(group_id),
                FOREIGN KEY (from_user_id)
                    REFERENCES users(user_id),
                FOREIGN KEY (to_user_id)
                    REFERENCES users(user_id)
            );

            CREATE TABLE settlement_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                settlement_id INTEGER NOT NULL,
                old_status TEXT,
                new_status TEXT NOT NULL,
                changed_by_user_id INTEGER NOT NULL,
                changed_at TEXT NOT NULL,
                note TEXT,
                FOREIGN KEY (settlement_id)
                    REFERENCES settlements(settlement_id),
                FOREIGN KEY (changed_by_user_id)
                    REFERENCES users(user_id)
            );

            INSERT INTO users VALUES (1, 'An');
            INSERT INTO users VALUES (2, 'Binh');
            INSERT INTO users VALUES (3, 'Chi');

            INSERT INTO groups VALUES (1, 'Test Group');

            INSERT INTO group_members (user_id, group_id)
            VALUES (1, 1);

            INSERT INTO group_members (user_id, group_id)
            VALUES (2, 1);
        """)

        connection.commit()
        connection.close()

    def tearDown(self):
        self.database_patch.stop()
        self.temp_dir.cleanup()

    def create_test_settlement(self):
        return service.create_settlement(
            group_id=1,
            from_user_id=1,
            to_user_id=2,
            amount=100000
        )

    def get_status(self, settlement_id):
        details = service.get_settlement_details(
            settlement_id
        )
        return details["status"]

    def test_create_settlement(self):
        settlement_id = self.create_test_settlement()

        details = service.get_settlement_details(
            settlement_id
        )

        self.assertEqual(details["status"], "PENDING")
        self.assertEqual(details["amount"], 100000)
        self.assertEqual(details["from_user_id"], 1)
        self.assertEqual(details["to_user_id"], 2)
        self.assertEqual(len(details["history"]), 1)

        self.assertIsNone(
            details["history"][0]["old_status"]
        )

        self.assertEqual(
            details["history"][0]["new_status"],
            "PENDING"
        )

    def test_both_parties_confirm(self):
        settlement_id = self.create_test_settlement()

        result1 = service.confirm_settlement(
            settlement_id, 1
        )

        self.assertEqual(result1, "PENDING")

        result2 = service.confirm_settlement(
            settlement_id, 2
        )

        self.assertEqual(result2, "CONFIRMED")

        details = service.get_settlement_details(
            settlement_id
        )

        self.assertIsNotNone(
            details["sender_confirmed_at"]
        )

        self.assertIsNotNone(
            details["receiver_confirmed_at"]
        )

    def test_duplicate_sender_confirmation(self):
        settlement_id = self.create_test_settlement()

        service.confirm_settlement(settlement_id, 1)

        with self.assertRaises(ValueError):
            service.confirm_settlement(settlement_id, 1)

    def test_duplicate_receiver_confirmation(self):
        settlement_id = self.create_test_settlement()

        service.confirm_settlement(settlement_id, 2)

        with self.assertRaises(ValueError):
            service.confirm_settlement(settlement_id, 2)

    def test_non_participant_cannot_confirm(self):
        settlement_id = self.create_test_settlement()

        with self.assertRaises(ValueError):
            service.confirm_settlement(settlement_id, 3)

    def test_dispute_and_resolution_cycle(self):
        settlement_id = self.create_test_settlement()

        # PENDING -> DISPUTED
        result = service.dispute_settlement(
            settlement_id,
            1,
            "Amount is incorrect."
        )

        self.assertEqual(result, "DISPUTED")

        # Only sender agrees to resolve.
        result = service.confirm_dispute_resolution(
            settlement_id,
            1,
            "We have discussed the issue."
        )

        self.assertEqual(result, "DISPUTED")

        details = service.get_settlement_details(
            settlement_id
        )

        self.assertIsNotNone(
            details["sender_resolved_at"]
        )

        self.assertIsNone(
            details["receiver_resolved_at"]
        )

        # Same participant cannot resolve twice.
        with self.assertRaises(ValueError):
            service.confirm_dispute_resolution(
                settlement_id,
                1,
                "Duplicate resolution."
            )

        # Receiver agrees: DISPUTED -> PENDING
        result = service.confirm_dispute_resolution(
            settlement_id,
            2,
            "I agree to resolve the issue."
        )

        self.assertEqual(result, "PENDING")

        details = service.get_settlement_details(
            settlement_id
        )

        # Old payment confirmations must be cleared.
        self.assertIsNone(details["sender_confirmed_at"])
        self.assertIsNone(details["receiver_confirmed_at"])

        # Resolution confirmation fields are reset.
        self.assertIsNone(details["sender_resolved_at"])
        self.assertIsNone(details["receiver_resolved_at"])

        # Both parties must confirm payment again.
        self.assertEqual(
            service.confirm_settlement(settlement_id, 1),
            "PENDING"
        )

        self.assertEqual(
            service.confirm_settlement(settlement_id, 2),
            "CONFIRMED"
        )

        # Verify complete history.
        details = service.get_settlement_details(
            settlement_id
        )

        history_statuses = [
            item["new_status"]
            for item in details["history"]
        ]

        self.assertEqual(
            history_statuses,
            [
                "PENDING",
                "DISPUTED",
                "DISPUTED",
                "PENDING",
                "PENDING",
                "CONFIRMED"
            ]
        )

    def test_non_participant_cannot_dispute(self):
        settlement_id = self.create_test_settlement()

        with self.assertRaises(ValueError):
            service.dispute_settlement(
                settlement_id,
                3,
                "Unauthorized dispute."
            )

    def test_cannot_confirm_disputed_settlement(self):
        settlement_id = self.create_test_settlement()

        service.dispute_settlement(
            settlement_id,
            1,
            "Disagreement."
        )

        with self.assertRaises(ValueError):
            service.confirm_settlement(settlement_id, 1)

    def test_cannot_dispute_confirmed_settlement(self):
        settlement_id = self.create_test_settlement()

        service.confirm_settlement(settlement_id, 1)
        service.confirm_settlement(settlement_id, 2)

        with self.assertRaises(ValueError):
            service.dispute_settlement(
                settlement_id,
                1,
                "Late dispute."
            )

    def test_empty_dispute_note(self):
        settlement_id = self.create_test_settlement()

        with self.assertRaises(ValueError):
            service.dispute_settlement(
                settlement_id,
                1,
                "   "
            )

    def test_empty_resolution_note(self):
        settlement_id = self.create_test_settlement()

        service.dispute_settlement(
            settlement_id,
            1,
            "Disagreement."
        )

        with self.assertRaises(ValueError):
            service.confirm_dispute_resolution(
                settlement_id,
                1,
                "   "
            )

    def test_non_participant_cannot_resolve_dispute(self):
        settlement_id = self.create_test_settlement()

        service.dispute_settlement(
            settlement_id,
            1,
            "Disagreement."
        )

        with self.assertRaises(ValueError):
            service.confirm_dispute_resolution(
                settlement_id,
                3,
                "Unauthorized resolution."
            )

    def test_nonexistent_settlement(self):
        with self.assertRaises(ValueError):
            service.get_settlement_details(999)

        with self.assertRaises(ValueError):
            service.confirm_settlement(999, 1)

    def test_invalid_settlement_amount(self):
        with self.assertRaises(ValueError):
            service.create_settlement(
                1, 1, 2, 0
            )

        with self.assertRaises(ValueError):
            service.create_settlement(
                1, 1, 2, -100
            )

        with self.assertRaises(ValueError):
            service.create_settlement(
                1, 1, 2, 100.5
            )

    def test_sender_and_receiver_cannot_be_same(self):
        with self.assertRaises(ValueError):
            service.create_settlement(
                1, 1, 1, 100000
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
