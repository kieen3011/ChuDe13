
import sqlite3
from pathlib import Path

from expense_split import (
    calculate_equal_split,
    calculate_percentage_split,
    calculate_fixed_split,
)


# Đường dẫn database luôn được xác định theo vị trí project.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "group_expense.db"


def create_expense_with_split(
    group_id,
    payer_user_id,
    description,
    total_amount,
    split_type,
    percentages=None,
    fixed_amounts=None,
):
    """
    Tạo một khoản chi và lưu phần tiền mỗi thành viên phải chịu.

    split_type:
        "EQUAL"       - Chia đều
        "PERCENTAGE"  - Chia theo phần trăm
        "FIXED"       - Chia theo số tiền cố định

    Returns:
        expense_id của khoản chi vừa tạo.
    """

    # ======================================
    # 1. VALIDATE INPUT
    # ======================================

    if not isinstance(total_amount, int) or isinstance(total_amount, bool):
        raise ValueError("Total amount must be an integer")

    if total_amount <= 0:
        raise ValueError("Total amount must be greater than zero")

    if not isinstance(description, str) or not description.strip():
        raise ValueError("Description cannot be empty")

    split_type = split_type.strip().upper()

    if split_type not in ("EQUAL", "PERCENTAGE", "FIXED"):
        raise ValueError("Invalid split type")

    # ======================================
    # 2. VALIDATE SPLIT PARAMETERS
    # ======================================

    if split_type == "PERCENTAGE":
        if percentages is None:
            raise ValueError("Percentages are required")

        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            for value in percentages
        ):
            raise ValueError("Percentages must be non-negative integers")

        if sum(percentages) != 100:
            raise ValueError("Total percentage must equal 100")

    if split_type == "FIXED":
        if fixed_amounts is None:
            raise ValueError("Fixed amounts are required")

    # ======================================
    # 3. CONNECT TO DATABASE
    # ======================================

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            cursor = connection.cursor()

            # ==================================
            # 4. GET GROUP AND LEADER
            # ==================================

            group = cursor.execute("""
                SELECT leader_user_id
                FROM groups
                WHERE group_id = ?
            """, (group_id,)).fetchone()

            if group is None:
                raise ValueError("Group does not exist")

            leader_user_id = group[0]

            # ==================================
            # 5. GET GROUP MEMBERS
            # ==================================

            rows = cursor.execute("""
                SELECT user_id
                FROM group_members
                WHERE group_id = ?
                ORDER BY user_id
            """, (group_id,)).fetchall()

            user_ids = [row[0] for row in rows]

            if not user_ids:
                raise ValueError("Group has no members")

            if payer_user_id not in user_ids:
                raise ValueError("Payer must be a group member")

            # ==================================
            # 6. CALCULATE SPLIT
            # ==================================

            if split_type == "EQUAL":

                if leader_user_id is None:
                    raise ValueError("Group leader has not been assigned")

                if leader_user_id not in user_ids:
                    raise ValueError("Leader is not a group member")

                leader_index = user_ids.index(leader_user_id)

                shares = calculate_equal_split(
                    total_amount,
                    user_ids,
                    leader_index,
                )

            elif split_type == "PERCENTAGE":

                if leader_user_id is None:
                    raise ValueError("Group leader has not been assigned")

                if leader_user_id not in user_ids:
                    raise ValueError("Leader is not a group member")

                if len(percentages) != len(user_ids):
                    raise ValueError(
                        "Member count and percentage count must match"
                    )

                leader_index = user_ids.index(leader_user_id)

                shares = calculate_percentage_split(
                    total_amount,
                    user_ids,
                    percentages,
                    leader_index,
                )

            else:  # FIXED

                if len(fixed_amounts) != len(user_ids):
                    raise ValueError(
                        "Member count and fixed amount count must match"
                    )

                shares = calculate_fixed_split(
                    total_amount,
                    user_ids,
                    fixed_amounts,
                )

            # ==================================
            # 7. VERIFY ALLOCATION
            # ==================================

            if len(shares) != len(user_ids):
                raise ValueError("Allocation count is incorrect")

            if sum(shares) != total_amount:
                raise ValueError("Allocation total is incorrect")

            # ==================================
            # 8. INSERT EXPENSE
            # ==================================

            cursor.execute("""
                INSERT INTO expenses (
                    group_id,
                    payer_user_id,
                    description,
                    amount
                )
                VALUES (?, ?, ?, ?)
            """, (
                group_id,
                payer_user_id,
                description.strip(),
                total_amount,
            ))

            expense_id = cursor.lastrowid

            # ==================================
            # 9. INSERT EXPENSE DETAILS
            # ==================================

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

        # Transaction đã commit thành công.
        return expense_id

    finally:
        connection.close()
