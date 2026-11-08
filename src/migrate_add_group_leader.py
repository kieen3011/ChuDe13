
import sqlite3

DATABASE_PATH = "database/group_expense.db"


def migrate_add_group_leader():
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        # Bắt đầu transaction để bảo vệ thay đổi schema
        connection.execute("BEGIN IMMEDIATE")

        # Kiểm tra các cột hiện tại của bảng groups
        columns = connection.execute(
            "PRAGMA table_info(groups)"
        ).fetchall()

        column_names = [column[1] for column in columns]

        if "leader_user_id" in column_names:
            print("Column leader_user_id already exists.")
        else:
            connection.execute("""
                ALTER TABLE groups
                ADD COLUMN leader_user_id INTEGER
                REFERENCES users(user_id)
            """)

            print("Column leader_user_id added successfully.")

        connection.commit()

        # Kiểm tra khóa ngoại
        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(groups)"
        ).fetchall()

        has_leader_foreign_key = any(
            fk[3] == "leader_user_id"
            and fk[2] == "users"
            and fk[4] == "user_id"
            for fk in foreign_keys
        )

        if not has_leader_foreign_key:
            raise RuntimeError("Leader foreign key verification failed.")

        print("PASS: Leader foreign key verified.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
        print("Database connection closed.")


if __name__ == "__main__":
    migrate_add_group_leader()

