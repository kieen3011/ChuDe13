from decimal import Decimal

from .history_filter import (
    filter_expenses_by_date,
    filter_expenses_by_payer,
    get_transaction_history,
    search_expenses_by_title,
)
from .statistics import (
    calculate_total_group_expense,
    get_extreme_expenses,
    get_group_expense_summary,
    get_top_spender,
)
from .validation import ValidationError, validate_expense_input

SAMPLE_EXPENSES = [
    {
        "id": 1,
        "title": "Ăn sáng bánh mì chảo",
        "amount": Decimal("180000"),
        "payer_id": "u1",
        "payer_name": "Kiên",
        "date": "2026-11-10",
    },
    {
        "id": 2,
        "title": "Vé vào cổng khu du lịch",
        "amount": Decimal("600000"),
        "payer_id": "u2",
        "payer_name": "Lợi",
        "date": "2026-11-10",
    },
    {
        "id": 3,
        "title": "Ăn trưa hải sản nhóm",
        "amount": Decimal("1250000"),
        "payer_id": "u3",
        "payer_name": "Lương",
        "date": "2026-11-11",
    },
    {
        "id": 4,
        "title": "Cà phê & nước suối",
        "amount": Decimal("145000"),
        "payer_id": "u3",
        "payer_name": "Lương",
        "date": "2026-11-11",
    },
    {
        "id": 5,
        "title": "Thuê xe di chuyển",
        "amount": Decimal("850000"),
        "payer_id": "u4",
        "payer_name": "Lộc",
        "date": "2026-11-12",
    },
]


def run_demo() -> None:
    print("=== 1. TEST VALIDATION ===")
    valid_data = validate_expense_input(
        title="  Ăn tối lẩu gà lá é  ",
        amount="500000",
        payer_id="u1",
        participant_ids=["u1", "u2", "u3", "u4", "u5"],
        expense_date="2026-11-12",
        split_mode="equal",
        group_member_ids=["u1", "u2", "u3", "u4", "u5"],
    )
    print("Hợp lệ:", valid_data["title"], "| Tiền:", valid_data["amount"], "| Chia:", valid_data["shares"])

    for bad_case, kwargs in [
        ("Tên rỗng", dict(title="   ", amount=100000, payer_id="u1", participant_ids=["u1", "u2"])),
        ("Tiền <= 0", dict(title="Buffet", amount=-50000, payer_id="u1", participant_ids=["u1", "u2"])),
        (
            "Tổng % != 100",
            dict(
                title="Khách sạn",
                amount=1000000,
                payer_id="u1",
                participant_ids=["u1", "u2"],
                split_mode="percent",
                percentages=[40, 40],
            ),
        ),
    ]:
        try:
            validate_expense_input(**kwargs)
        except ValidationError as exc:
            print(f"Bắt đúng lỗi [{bad_case}]: {exc}")

    print("\n=== 2. TEST LỊCH SỬ & LỌC ===")
    print("Tìm 'ăn':", [x["title"] for x in search_expenses_by_title(SAMPLE_EXPENSES, "ăn")])
    print("Người trả 'Lương':", [x["title"] for x in filter_expenses_by_payer(SAMPLE_EXPENSES, "Lương")])
    print("Ngày 2026-11-11:", [x["title"] for x in filter_expenses_by_date(SAMPLE_EXPENSES, "2026-11-11")])
    combo = get_transaction_history(
        SAMPLE_EXPENSES,
        start_date="2026-11-10",
        end_date="2026-11-11",
        sort_by="amount",
        descending=True,
    )
    print("Khoảng 10-11/11 (giảm dần theo tiền):", [(x["title"], str(x["amount"])) for x in combo])

    print("\n=== 3. TEST THỐNG KÊ ===")
    print("Tổng chi nhóm:", calculate_total_group_expense(SAMPLE_EXPENSES))
    extremes = get_extreme_expenses(SAMPLE_EXPENSES)
    print("Khoản chi lớn nhất:", extremes["max_expense"]["title"], extremes["max_expense"]["amount"])
    print("Khoản chi nhỏ nhất:", extremes["min_expense"]["title"], extremes["min_expense"]["amount"])
    top = get_top_spender(SAMPLE_EXPENSES)
    print("Người chi nhiều nhất:", top["payer_name"], top["total_paid"])
    summary = get_group_expense_summary(SAMPLE_EXPENSES)
    print("Trung bình mỗi khoản:", summary["average_amount"])


if __name__ == "__main__":
    run_demo()