
import sys
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from expense_service import create_expense_with_split, DATABASE_PATH


GROUP_ID = 28
PAYER_USER_ID = 1


def verify_expense(expense_id, expected_amount):
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        expense = connection.execute("""
            SELECT amount
            FROM expenses
            WHERE expense_id = ?
        """, (expense_id,)).fetchone()

        details = connection.execute("""
            SELECT user_id, owed_amount
            FROM expense_details
            WHERE expense_id = ?
            ORDER BY user_id
        """, (expense_id,)).fetchall()

        if expense is None:
            raise AssertionError("Expense was not saved")

        if sum(row[1] for row in details) != expected_amount:
            raise AssertionError("Saved allocation total is incorrect")

        if expense[0] != expected_amount:
            raise AssertionError("Expense amount is incorrect")

        if len(details) != 2:
            raise AssertionError("Expected exactly two allocation rows")

        print("Expense ID:", expense_id)
        print("Saved details:", details)
        print("Total allocated:", sum(row[1] for row in details))

    finally:
        connection.close()


def run_test(description, split_type, amount, **kwargs):
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        existing = connection.execute("""
            SELECT expense_id
            FROM expenses
            WHERE group_id = ? AND description = ?
        """, (GROUP_ID, description)).fetchone()

        if existing is not None:
            raise ValueError(
                f"Test data already exists: {description}. "
                "Do not rerun this test with the same description."
            )

    finally:
        connection.close()

    expense_id = create_expense_with_split(
        group_id=GROUP_ID,
        payer_user_id=PAYER_USER_ID,
        description=description,
        total_amount=amount,
        split_type=split_type,
        **kwargs,
    )

    verify_expense(expense_id, amount)


def test_equal_split():
    run_test(
        description="SERVICE_TEST_EQUAL",
        split_type="EQUAL",
        amount=100003,
    )
    print("PASS: Equal Split Service")


def test_percentage_split():
    run_test(
        description="SERVICE_TEST_PERCENTAGE",
        split_type="PERCENTAGE",
        amount=100003,
        percentages=[50, 50],
    )
    print("PASS: Percentage Split Service")


def test_fixed_split():
    run_test(
        description="SERVICE_TEST_FIXED",
        split_type="FIXED",
        amount=100000,
        fixed_amounts=[40000, 60000],
    )
    print("PASS: Fixed Split Service")


if __name__ == "__main__":
    test_equal_split()
    test_percentage_split()
    test_fixed_split()

    print("\nALL EXPENSE SERVICE TESTS PASSED")

