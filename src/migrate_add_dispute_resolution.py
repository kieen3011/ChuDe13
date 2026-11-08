
import sqlite3
from pathlib import Path

DATABASE_PATH = (
    Path(__file__).resolve().parents[1]
    / "database"
    / "group_expense.db"
)


def migrate():
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        with connection:
            columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(settlements)"
                ).fetchall()
            }

            if "sender_resolved_at" not in columns:
                connection.execute("""
                    ALTER TABLE settlements
                    ADD COLUMN sender_resolved_at TEXT
                """)

            if "receiver_resolved_at" not in columns:
                connection.execute("""
                    ALTER TABLE settlements
                    ADD COLUMN receiver_resolved_at TEXT
                """)

        print("PASS: Dispute resolution migration completed.")

    finally:
        connection.close()


if __name__ == "__main__":
    migrate()

