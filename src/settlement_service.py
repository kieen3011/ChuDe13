import sqlite3
import heapq
from datetime import datetime


DATABASE_PATH = "database/group_expense.db"


def _validate_positive_integer(value, field_name):
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
    ):
        raise ValueError(
            f"{field_name} must be a positive integer."
        )


def _get_current_time():
    return datetime.now().astimezone().isoformat(
        timespec="seconds"
    )


def _record_settlement_history(
    cursor,
    settlement_id,
    old_status,
    new_status,
    changed_by_user_id,
    changed_at,
    note
):
    cursor.execute("""
        INSERT INTO settlement_history (
            settlement_id,
            old_status,
            new_status,
            changed_by_user_id,
            changed_at,
            note
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        settlement_id,
        old_status,
        new_status,
        changed_by_user_id,
        changed_at,
        note
    ))


def _get_settlement_for_update(cursor, settlement_id):
    cursor.execute("""
        SELECT
            settlement_id,
            group_id,
            from_user_id,
            to_user_id,
            amount,
            status,
            sender_confirmed_at,
            receiver_confirmed_at,
            sender_resolved_at,
            receiver_resolved_at
        FROM settlements
        WHERE settlement_id = ?
    """, (settlement_id,))

    settlement = cursor.fetchone()

    if settlement is None:
        raise ValueError("Settlement does not exist.")

    return settlement


def _validate_participant(settlement, user_id):
    sender_id = settlement[2]
    receiver_id = settlement[3]

    if user_id not in (sender_id, receiver_id):
        raise ValueError(
            "User is not a participant of this settlement."
        )


def create_settlement(group_id, from_user_id, to_user_id, amount):

    _validate_positive_integer(group_id, "Group ID")
    _validate_positive_integer(from_user_id, "Sender ID")
    _validate_positive_integer(to_user_id, "Receiver ID")
    _validate_positive_integer(amount, "Amount")

    if from_user_id == to_user_id:
        raise ValueError(
            "Sender and receiver cannot be the same person."
        )

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT COUNT(DISTINCT user_id)
                FROM group_members
                WHERE group_id = ?
                AND user_id IN (?, ?)
            """, (group_id, from_user_id, to_user_id))

            member_count = cursor.fetchone()[0]

            if member_count != 2:
                raise ValueError(
                    "Sender and receiver must belong to this group."
                )

            current_time = _get_current_time()

            cursor.execute("""
                INSERT INTO settlements (
                    group_id,
                    from_user_id,
                    to_user_id,
                    amount,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, 'PENDING', ?)
            """, (
                group_id,
                from_user_id,
                to_user_id,
                amount,
                current_time
            ))

            settlement_id = cursor.lastrowid

            _record_settlement_history(
                cursor,
                settlement_id,
                None,
                "PENDING",
                from_user_id,
                current_time,
                "Initial settlement creation"
            )

        return settlement_id

    finally:
        connection.close()

def confirm_settlement(settlement_id, user_id):

    _validate_positive_integer(settlement_id, "Settlement ID")
    _validate_positive_integer(user_id, "User ID")

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            cursor = connection.cursor()

            settlement = _get_settlement_for_update(
                cursor, settlement_id
            )

            _validate_participant(settlement, user_id)

            status = settlement[5]

            if status != "PENDING":
                raise ValueError(
                    "Only PENDING settlements can be confirmed."
                )

            sender_id = settlement[2]
            sender_confirmed_at = settlement[6]
            receiver_confirmed_at = settlement[7]

            current_time = _get_current_time()

            if user_id == sender_id:
                if sender_confirmed_at is not None:
                    raise ValueError(
                        "Sender has already confirmed."
                    )

                cursor.execute("""
                    UPDATE settlements
                    SET sender_confirmed_at = ?
                    WHERE settlement_id = ?
                """, (current_time, settlement_id))

                sender_confirmed_at = current_time
                note = "Sender confirmed settlement."

            else:
                if receiver_confirmed_at is not None:
                    raise ValueError(
                        "Receiver has already confirmed."
                    )

                cursor.execute("""
                    UPDATE settlements
                    SET receiver_confirmed_at = ?
                    WHERE settlement_id = ?
                """, (current_time, settlement_id))

                receiver_confirmed_at = current_time
                note = "Receiver confirmed settlement."

            new_status = (
                "CONFIRMED"
                if sender_confirmed_at is not None
                and receiver_confirmed_at is not None
                else "PENDING"
            )

            cursor.execute("""
                UPDATE settlements
                SET status = ?
                WHERE settlement_id = ?
            """, (new_status, settlement_id))

            _record_settlement_history(
                cursor,
                settlement_id,
                status,
                new_status,
                user_id,
                current_time,
                note
            )

        return new_status

    finally:
        connection.close()

def dispute_settlement(settlement_id, user_id, note):

    _validate_positive_integer(settlement_id, "Settlement ID")
    _validate_positive_integer(user_id, "User ID")

    if not isinstance(note, str) or not note.strip():
        raise ValueError("Dispute note cannot be empty.")

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            cursor = connection.cursor()

            settlement = _get_settlement_for_update(
                cursor, settlement_id
            )

            _validate_participant(settlement, user_id)

            status = settlement[5]

            if status != "PENDING":
                raise ValueError(
                    "Only PENDING settlements can be disputed."
                )

            current_time = _get_current_time()

            cursor.execute("""
                UPDATE settlements
                SET
                    status = 'DISPUTED',
                    sender_resolved_at = NULL,
                    receiver_resolved_at = NULL
                WHERE settlement_id = ?
            """, (settlement_id,))

            _record_settlement_history(
                cursor,
                settlement_id,
                "PENDING",
                "DISPUTED",
                user_id,
                current_time,
                f"Dispute raised: {note.strip()}"
            )

        return "DISPUTED"

    finally:
        connection.close()

def confirm_dispute_resolution(
    settlement_id,
    user_id,
    resolution_note
):

    _validate_positive_integer(settlement_id, "Settlement ID")
    _validate_positive_integer(user_id, "User ID")

    if (
        not isinstance(resolution_note, str)
        or not resolution_note.strip()
    ):
        raise ValueError(
            "Resolution note cannot be empty."
        )

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            cursor = connection.cursor()

            settlement = _get_settlement_for_update(
                cursor, settlement_id
            )

            _validate_participant(settlement, user_id)

            status = settlement[5]

            if status != "DISPUTED":
                raise ValueError(
                    "Settlement must be DISPUTED."
                )

            sender_id = settlement[2]
            sender_resolved_at = settlement[8]
            receiver_resolved_at = settlement[9]

            current_time = _get_current_time()

            if user_id == sender_id:
                if sender_resolved_at is not None:
                    raise ValueError(
                        "Sender has already confirmed resolution."
                    )

                cursor.execute("""
                    UPDATE settlements
                    SET sender_resolved_at = ?
                    WHERE settlement_id = ?
                """, (current_time, settlement_id))

                sender_resolved_at = current_time
                note = (
                    "Sender agreed to dispute resolution: "
                    + resolution_note.strip()
                )

            else:
                if receiver_resolved_at is not None:
                    raise ValueError(
                        "Receiver has already confirmed resolution."
                    )

                cursor.execute("""
                    UPDATE settlements
                    SET receiver_resolved_at = ?
                    WHERE settlement_id = ?
                """, (current_time, settlement_id))

                receiver_resolved_at = current_time
                note = (
                    "Receiver agreed to dispute resolution: "
                    + resolution_note.strip()
                )

            both_resolved = (
                sender_resolved_at is not None
                and receiver_resolved_at is not None
            )

            if both_resolved:
                cursor.execute("""
                    UPDATE settlements
                    SET
                        status = 'PENDING',
                        sender_confirmed_at = NULL,
                        receiver_confirmed_at = NULL,
                        sender_resolved_at = NULL,
                        receiver_resolved_at = NULL
                    WHERE settlement_id = ?
                """, (settlement_id,))

                new_status = "PENDING"

                note = (
                    "Both parties agreed to resolve the dispute. "
                    "Settlement returned to PENDING. "
                    + resolution_note.strip()
                )

            else:
                new_status = "DISPUTED"

            _record_settlement_history(
                cursor,
                settlement_id,
                "DISPUTED",
                new_status,
                user_id,
                current_time,
                note
            )

        return new_status

    finally:
        connection.close()

def get_settlement_details(settlement_id):

    _validate_positive_integer(settlement_id, "Settlement ID")

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                settlement_id,
                group_id,
                from_user_id,
                to_user_id,
                amount,
                status,
                sender_confirmed_at,
                receiver_confirmed_at,
                sender_resolved_at,
                receiver_resolved_at,
                created_at
            FROM settlements
            WHERE settlement_id = ?
        """, (settlement_id,))

        row = cursor.fetchone()

        if row is None:
            raise ValueError("Settlement does not exist.")

        settlement = {
            "settlement_id": row[0],
            "group_id": row[1],
            "from_user_id": row[2],
            "to_user_id": row[3],
            "amount": row[4],
            "status": row[5],
            "sender_confirmed_at": row[6],
            "receiver_confirmed_at": row[7],
            "sender_resolved_at": row[8],
            "receiver_resolved_at": row[9],
            "created_at": row[10]
        }

        cursor.execute("""
            SELECT
                old_status,
                new_status,
                changed_by_user_id,
                changed_at,
                note
            FROM settlement_history
            WHERE settlement_id = ?
            ORDER BY history_id
        """, (settlement_id,))

        settlement["history"] = [
            {
                "old_status": item[0],
                "new_status": item[1],
                "changed_by_user_id": item[2],
                "changed_at": item[3],
                "note": item[4]
            }
            for item in cursor.fetchall()
        ]

        return settlement

    finally:
        connection.close()



def calculate_net_balances(group_id):
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.cursor()

        query = """
            WITH paid AS (
                SELECT
                    group_id,
                    payer_user_id AS user_id,
                    SUM(amount) AS total_paid
                FROM expenses
                WHERE group_id = ?
                GROUP BY group_id, payer_user_id
            ),
            owed AS (
                SELECT
                    e.group_id,
                    ed.user_id,
                    SUM(ed.owed_amount) AS total_owed
                FROM expenses AS e
                JOIN expense_details AS ed
                    ON ed.expense_id = e.expense_id
                WHERE e.group_id = ?
                GROUP BY e.group_id, ed.user_id
            )
            SELECT
                gm.user_id,
                COALESCE(paid.total_paid, 0) AS total_paid,
                COALESCE(owed.total_owed, 0) AS total_owed,
                COALESCE(paid.total_paid, 0)
                    - COALESCE(owed.total_owed, 0) AS net_balance
            FROM group_members AS gm
            LEFT JOIN paid
                ON paid.group_id = gm.group_id
                AND paid.user_id = gm.user_id
            LEFT JOIN owed
                ON owed.group_id = gm.group_id
                AND owed.user_id = gm.user_id
            WHERE gm.group_id = ?
            ORDER BY gm.user_id
        """

        cursor.execute(query, (group_id, group_id, group_id))
        rows = cursor.fetchall()

        if not rows:
            raise ValueError(
                "Group does not exist or has no members."
            )

        results = []

        for row in rows:
            user_id, total_paid, total_owed, net_balance = row

            results.append({
                "user_id": user_id,
                "total_paid": total_paid,
                "total_owed": total_owed,
                "net_balance": net_balance
            })

        # Kiểm tra tổng Net Balance của nhóm
        total_net_balance = sum(
            member["net_balance"] for member in results
        )

        if total_net_balance != 0:
            raise ValueError(
                "Data integrity error: total Net Balance "
                "of the group must equal zero."
            )

        return results

    finally:
        connection.close()
def simplify_debts(net_balances):
        # Validate input structure
    if not isinstance(net_balances, list):
        raise ValueError(
            "Net balances must be a list."
        )

    for member in net_balances:
        if not isinstance(member, dict):
            raise ValueError(
                "Each member must be a dictionary."
            )

        if "user_id" not in member or "net_balance" not in member:
            raise ValueError(
                "Each member must contain user_id and net_balance."
            )
        # Validate Net Balance data types
    for member in net_balances:
        balance = member["net_balance"]

        if not isinstance(balance, int) or isinstance(balance, bool):
            raise ValueError(
                "Net Balance must be an integer."
            )
    # Validate user IDs
    for member in net_balances:
        user_id = member["user_id"]

        if (
            not isinstance(user_id, int)
            or isinstance(user_id, bool)
            or user_id <= 0
        ):
            raise ValueError(
                "User ID must be a positive integer."
            )
    # Validate unique user IDs
    user_ids = [
        member["user_id"]
        for member in net_balances
    ]

    if len(user_ids) != len(set(user_ids)):
        raise ValueError(
            "Duplicate user IDs are not allowed."
        )
    # Validate total Net Balance
    total_balance = sum(
        member["net_balance"]
        for member in net_balances
    )

    if total_balance != 0:
        raise ValueError(
            "Total Net Balance must equal zero."
        )

    creditors = []
    debtors = []
    # Separate Creditors and Debtors
    for member in net_balances:
        user_id = member["user_id"]
        balance = member["net_balance"]

        if balance > 0:
            heapq.heappush(
                creditors,
                (-balance, user_id)
            )

        elif balance < 0:
            heapq.heappush(
                debtors,
                (balance, user_id)
            )

    transactions = []

    # Match Debtors with Creditors
    while creditors and debtors:
        negative_credit, creditor_id = heapq.heappop(
            creditors
        )

        debt_balance, debtor_id = heapq.heappop(
            debtors
        )

        credit_amount = -negative_credit
        debt_amount = -debt_balance

        transfer_amount = min(
            credit_amount,
            debt_amount
        )

        transactions.append({
            "from_user_id": debtor_id,
            "to_user_id": creditor_id,
            "amount": transfer_amount
        })

        # Update remaining balances
        remaining_credit = (
            credit_amount - transfer_amount
        )

        remaining_debt = (
            debt_amount - transfer_amount
        )

        if remaining_credit > 0:
            heapq.heappush(
                creditors,
                (-remaining_credit, creditor_id)
            )

        if remaining_debt > 0:
            heapq.heappush(
                debtors,
                (-remaining_debt, debtor_id)
            )

    return transactions
