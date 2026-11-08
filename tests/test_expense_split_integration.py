
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from expense_split import calculate_equal_split

DATABASE_PATH = PROJECT_ROOT / "database" / "group_expense.db"

GROUP_ID = 28
PAYER_USER_ID = 1
DESCRIPTION = "TEST_EQUAL_SPLIT"
TOTAL_AMOUNT = 100003


def test_equal_split_integration():
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            cursor = connection.cursor()

            # 1. Lấy thông tin nhóm
            group = cursor.execute("""
                SELECT group_name, leader_user_id
                FROM groups
                WHERE group_id = ?
            """, (GROUP_ID,)).fetchone()

            if group is None:
                raise ValueError("Group does not exist")

            group_name, leader_user_id = group

            if leader_user_id is None:
                raise ValueError("Group leader has not been assigned")

            # 2. Lấy danh sách thành viên
            members = cursor.execute("""
                SELECT user_id
                FROM group_members
                WHERE group_id = ?
                ORDER BY user_id
            """, (GROUP_ID,)).fetchall()

            user_ids = [row[0] for row in members]

            if not user_ids:
                raise ValueError("Group has no members")

            if leader_user_id not in user_ids:
                raise ValueError("Leader is not a group member")

            if PAYER_USER_ID not in user_ids:
                raise ValueError("Payer is not a group member")

            # Tránh tạo hóa đơn thử nghiệm trùng lặp
            existing = cursor.execute("""
                SELECT expense_id
                FROM expenses
                WHERE group_id = ? AND description = ?
            """, (GROUP_ID, DESCRIPTION)).fetchone()

            if existing is not None:
                raise ValueError("Test expense already exists")

            # 3. Gọi thuật toán Equal Split
            leader_index = user_ids.index(leader_user_id)

            shares = calculate_equal_split(
                TOTAL_AMOUNT,
                user_ids,
                leader_index
            )

            if sum(shares) != TOTAL_AMOUNT:
                raise ValueError("Allocation total is incorrect")

            # 4. Lưu hóa đơn
            cursor.execute("""
                INSERT INTO expenses (
                    group_id,
                    payer_user_id,
                    description,
                    amount
                )
                VALUES (?, ?, ?, ?)
            """, (
                GROUP_ID,
                PAYER_USER_ID,
                DESCRIPTION,
                TOTAL_AMOUNT
            ))

            expense_id = cursor.lastrowid

            # 5. Lưu từng khoản phải chịu
            expense_details = [
                (expense_id, user_id, owed_amount)
                for user_id, owed_amount in zip(user_ids, shares)
            ]

            cursor.executemany("""
                INSERT INTO expense_details (
                    expense_id,
                    user_id,
                    owed_amount
                )
                VALUES (?, ?, ?)
            """, expense_details)

            # 6. Xác minh dữ liệu đã lưu
            saved_details = cursor.execute("""
                SELECT user_id, owed_amount
                FROM expense_details
                WHERE expense_id = ?
                ORDER BY user_id
            """, (expense_id,)).fetchall()

            saved_total = sum(row[1] for row in saved_details)

            if saved_total != TOTAL_AMOUNT:
                raise ValueError("Saved allocation total is incorrect")

        print("PASS: Expense created")
        print("Expense ID:", expense_id)
        print("Group:", group_name)
        print("Leader user ID:", leader_user_id)
        print("Saved details:", saved_details)
        print("Total allocated:", saved_total)
        print("PASS: SQLite Expense Split Integration")

    finally:
        connection.close()


if __name__ == "__main__":
    test_equal_split_integration()
