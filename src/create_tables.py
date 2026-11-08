
import sqlite3


# ==========================================
# CONFIGURATION
# ==========================================

DATABASE_PATH = "database/group_expense.db"

# Chỉ bật khi cần tạo dữ liệu mẫu để phát triển.
SEED_SAMPLE_DATA = True


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()

try:
    # Bật kiểm tra Foreign Key
    cursor.execute("PRAGMA foreign_keys = ON")

    # ======================================
    # 1. USERS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL
        )
    """)

    # ======================================
    # 2. GROUPS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL,
            leader_user_id INTEGER,

            FOREIGN KEY (leader_user_id)
                REFERENCES users(user_id)
        )
    """)

    # ======================================
    # 3. GROUP_MEMBERS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            group_member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id),

            FOREIGN KEY (group_id)
                REFERENCES groups(group_id),

            UNIQUE (user_id, group_id)
        )
    """)

    # ======================================
    # 4. EXPENSES
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            payer_user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount INTEGER NOT NULL CHECK (amount > 0),

            FOREIGN KEY (group_id)
                REFERENCES groups(group_id),

            FOREIGN KEY (payer_user_id)
                REFERENCES users(user_id)
        )
    """)

    # ======================================
    # 5. EXPENSE_DETAILS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expense_details (
            detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            owed_amount INTEGER NOT NULL CHECK (owed_amount >= 0),

            FOREIGN KEY (expense_id)
                REFERENCES expenses(expense_id),

            FOREIGN KEY (user_id)
                REFERENCES users(user_id),

            UNIQUE (expense_id, user_id)
        )
    """)

    # ======================================
    # 6. SETTLEMENTS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlements (
            settlement_id INTEGER PRIMARY KEY AUTOINCREMENT,

            group_id INTEGER NOT NULL,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,

            amount INTEGER NOT NULL CHECK (amount > 0),

            status TEXT NOT NULL
                CHECK (
                    status IN (
                        'PENDING',
                        'DISPUTED',
                        'CONFIRMED'
                    )
                ),

            sender_confirmed_at TEXT,
            receiver_confirmed_at TEXT,

            created_at TEXT NOT NULL,

            CHECK (from_user_id != to_user_id),

            FOREIGN KEY (group_id)
                REFERENCES groups(group_id),

            FOREIGN KEY (from_user_id)
                REFERENCES users(user_id),

            FOREIGN KEY (to_user_id)
                REFERENCES users(user_id)
        )
    """)

    # ======================================
    # 7. SETTLEMENT_HISTORY
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlement_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,

            settlement_id INTEGER NOT NULL,

            old_status TEXT
                CHECK (
                    old_status IS NULL
                    OR old_status IN (
                        'PENDING',
                        'DISPUTED',
                        'CONFIRMED'
                    )
                ),

            new_status TEXT NOT NULL
                CHECK (
                    new_status IN (
                        'PENDING',
                        'DISPUTED',
                        'CONFIRMED'
                    )
                ),

            changed_by_user_id INTEGER NOT NULL,

            changed_at TEXT NOT NULL,

            note TEXT,

            FOREIGN KEY (settlement_id)
                REFERENCES settlements(settlement_id),

            FOREIGN KEY (changed_by_user_id)
                REFERENCES users(user_id)
        )
    """)

    # ======================================
    # SEED SAMPLE DATA
    # ======================================

    if SEED_SAMPLE_DATA:

        sample_users = [
            ("An",),
            ("Bình",),
            ("Chi",)
        ]

        for user in sample_users:
            cursor.execute("""
                INSERT INTO users (full_name)
                SELECT ?
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM users
                    WHERE full_name = ?
                )
            """, (user[0], user[0]))

    # ======================================
    # COMMIT
    # ======================================

    connection.commit()

    print("Database initialized successfully!")

except sqlite3.Error as error:

    connection.rollback()
    print("Database initialization failed:", error)

finally:

    connection.close()
    print("Database connection closed.")
