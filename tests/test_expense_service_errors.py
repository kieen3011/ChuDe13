
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from expense_service import create_expense_with_split, DATABASE_PATH


GROUP_ID = 28
PAYER_USER_ID = 1


def assert_expense_not_saved(description):
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        result = connection.execute("""
            SELECT COUNT(*)
            FROM expenses
            WHERE group_id = ? AND description = ?
        """, (GROUP_ID, description)).fetchone()

        if result[0] != 0:
            raise AssertionError(
                f"Failed transaction left an expense: {description}"
            )

    finally:
        connection.close()


def test_invalid_group():
    description = "ERROR_TEST_INVALID_GROUP"

    try:
        create_expense_with_split(
            group_id=999999,
            payer_user_id=PAYER_USER_ID,
            description=description,
            total_amount=100000,
            split_type="EQUAL",
        )
    except ValueError:
        assert_expense_not_saved(description)
        print("PASS: Invalid group validation")
    else:
        raise AssertionError("Expected ValueError for invalid group")


def test_payer_not_in_group():
    description = "ERROR_TEST_INVALID_PAYER"

    try:
        create_expense_with_split(
            group_id=GROUP_ID,
            payer_user_id=999999,
            description=description,
            total_amount=100000,
            split_type="EQUAL",
        )
    except ValueError:
        assert_expense_not_saved(description)
        print("PASS: Payer membership validation")
    else:
        raise AssertionError("Expected ValueError for invalid payer")


def test_invalid_percentage():
    description = "ERROR_TEST_INVALID_PERCENTAGE"

    try:
        create_expense_with_split(
            group_id=GROUP_ID,
            payer_user_id=PAYER_USER_ID,
            description=description,
            total_amount=100000,
            split_type="PERCENTAGE",
            percentages=[60, 30],
        )
    except ValueError:
        assert_expense_not_saved(description)
        print("PASS: Invalid percentage validation")
    else:
        raise AssertionError("Expected ValueError for invalid percentage")


def test_invalid_fixed_amounts():
    description = "ERROR_TEST_INVALID_FIXED"

    try:
        create_expense_with_split(
            group_id=GROUP_ID,
            payer_user_id=PAYER_USER_ID,
            description=description,
            total_amount=100000,
            split_type="FIXED",
            fixed_amounts=[40000, 50000],
        )
    except ValueError:
        assert_expense_not_saved(description)
        print("PASS: Fixed amount total validation")
    else:
        raise AssertionError("Expected ValueError for invalid fixed amounts")


def test_transaction_rollback():
    description = "ERROR_TEST_TRANSACTION_ROLLBACK"
    trigger_name = "test_force_expense_detail_failure"

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        existing = connection.execute("""
            SELECT COUNT(*)
            FROM expenses
            WHERE group_id = ? AND description = ?
        """, (GROUP_ID, description)).fetchone()[0]

        if existing:
            raise ValueError("Rollback test data already exists")

        # Tạo trigger để cố ý làm lỗi khi lưu
        # expense_details của user_id = 2.
        connection.execute(f"""
            CREATE TRIGGER {trigger_name}
            BEFORE INSERT ON expense_details
            WHEN NEW.user_id = 2
            BEGIN
                SELECT RAISE(ABORT, 'Forced test failure');
            END;
        """)

        connection.commit()

    finally:
        connection.close()

    try:
        create_expense_with_split(
            group_id=GROUP_ID,
            payer_user_id=PAYER_USER_ID,
            description=description,
            total_amount=100000,
            split_type="EQUAL",
        )

    except sqlite3.IntegrityError:
        assert_expense_not_saved(description)
        print("PASS: Transaction rollback")

    else:
        raise AssertionError(
            "Expected IntegrityError during expense detail insertion"
        )

    finally:
        # Xóa trigger kiểm thử, không xóa dữ liệu nghiệp vụ.
        connection = sqlite3.connect(DATABASE_PATH)

        try:
            connection.execute(
                f"DROP TRIGGER IF EXISTS {trigger_name}"
            )
            connection.commit()
        finally:
            connection.close()
if __name__ == "__main__":
    test_invalid_group()
    test_payer_not_in_group()
    test_invalid_percentage()
    test_invalid_fixed_amounts()
    test_transaction_rollback()

    print("\nALL EXPENSE SERVICE ERROR TESTS PASSED")
