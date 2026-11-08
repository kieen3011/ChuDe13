
import sqlite3
from settlement_service import create_settlement

DATABASE_PATH = "database/group_expense.db"

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()

try:
    cursor.execute("PRAGMA foreign_keys = ON")

    # 1. Lấy hai người dùng hiện có
    cursor.execute("""
        SELECT user_id
        FROM users
        ORDER BY user_id
        LIMIT 2
    """)

    test_users = cursor.fetchall()

    if len(test_users) < 2:
        raise RuntimeError("Cần ít nhất 2 users để kiểm thử.")

    from_user_id = test_users[0][0]
    to_user_id = test_users[1][0]

    # 2. Tìm nhóm kiểm thử đã tồn tại
    test_group_name = "TEST_SETTLEMENT_GROUP"

    cursor.execute("""
        SELECT group_id
        FROM groups
        WHERE group_name = ?
        LIMIT 1
    """, (test_group_name,))

    result = cursor.fetchone()

    # Nếu chưa có thì tạo nhóm
    if result is None:
        cursor.execute("""
            INSERT INTO groups (group_name)
            VALUES (?)
        """, (test_group_name,))

        group_id = cursor.lastrowid
    else:
        group_id = result[0]

    # 3. Thêm hai người vào nhóm
    cursor.executemany("""
        INSERT OR IGNORE INTO group_members (
            user_id,
            group_id
        )
        VALUES (?, ?)
    """, [
        (from_user_id, group_id),
        (to_user_id, group_id)
    ])

    connection.commit()

    print("PASS: Test group prepared")
    print("Group ID:", group_id)
    print("From User ID:", from_user_id)
    print("To User ID:", to_user_id)

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()


# ==========================================
# TEST CREATE SETTLEMENT
# ==========================================

try:
    settlement_id = create_settlement(
        group_id=group_id,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        amount=200000
    )

    print("\nPASS: Settlement created")
    print("Settlement ID:", settlement_id)

except Exception as error:
    print("\nFAIL:", error)


# ==========================================
# VERIFY DATABASE
# ==========================================

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()

cursor.execute("""
    SELECT *
    FROM settlements
    ORDER BY settlement_id DESC
    LIMIT 1
""")

print("\n--- Latest Settlement ---")
print(cursor.fetchone())

cursor.execute("""
    SELECT *
    FROM settlement_history
    ORDER BY history_id DESC
    LIMIT 1
""")

print("\n--- Latest Settlement History ---")
print(cursor.fetchone())

# ==========================================
# KIỂM THỬ ATOMICITY - TRANSACTION ROLLBACK
# ==========================================

import sqlite3

connection = sqlite3.connect("database/group_expense.db")
cursor = connection.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

# Đếm settlement trước kiểm thử
cursor.execute("SELECT COUNT(*) FROM settlements")
before_count = cursor.fetchone()[0]

try:
    with connection:

        # Thao tác 1: Tạo settlement hợp lệ
        cursor.execute("""
            INSERT INTO settlements (
                group_id,
                from_user_id,
                to_user_id,
                amount,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            28, 1, 2, 100000,
            "PENDING",
            "2026-11-08"
        ))

        test_settlement_id = cursor.lastrowid

        print("Settlement inserted temporarily.")

        # Thao tác 2: Cố tình tạo lỗi Foreign Key
        cursor.execute("""
            INSERT INTO settlement_history (
                settlement_id,
                old_status,
                new_status,
                changed_by_user_id,
                changed_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            test_settlement_id,
            None,
            "PENDING",
            999999,
            "2026-11-08"
        ))

except sqlite3.IntegrityError as error:
    print("PASS: History insertion rejected:", error)


# Kiểm tra số lượng sau rollback
cursor.execute("SELECT COUNT(*) FROM settlements")
after_count = cursor.fetchone()[0]

if before_count == after_count:
    print("PASS: Settlement insertion rolled back")
else:
    print("FAIL: Settlement record was not rolled back")


# Kiểm tra số lượng history
cursor.execute("SELECT COUNT(*) FROM settlement_history")
print("History records:", cursor.fetchone()[0])

connection.close()

connection.close()

