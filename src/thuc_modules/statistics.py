from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable


def _get_field(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _to_decimal(val: Any) -> Decimal:
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val or "0"))
    except InvalidOperation:
        return Decimal("0")


def calculate_total_group_expense(
    expenses: Iterable[Any],
    amount_field: str = "amount",
) -> Decimal:
    """Tính tổng chi tiêu của cả nhóm."""
    total = Decimal("0")
    for exp in expenses:
        total += _to_decimal(_get_field(exp, amount_field, 0))
    return total


def get_extreme_expenses(
    expenses: Iterable[Any],
    amount_field: str = "amount",
) -> dict[str, Any]:
    """
    Tìm khoản chi lớn nhất (max) và khoản chi nhỏ nhất (min).
    Nếu danh sách rỗng, trả về None cho cả hai.
    """
    expense_list = list(expenses)
    if not expense_list:
        return {
            "max_expense": None,
            "min_expense": None,
        }

    max_exp = max(expense_list, key=lambda x: _to_decimal(_get_field(x, amount_field, 0)))
    min_exp = min(expense_list, key=lambda x: _to_decimal(_get_field(x, amount_field, 0)))

    return {
        "max_expense": max_exp,
        "min_expense": min_exp,
    }


def get_top_spender(
    expenses: Iterable[Any],
    amount_field: str = "amount",
    payer_id_field: str = "payer_id",
    payer_name_field: str = "payer_name",
) -> dict[str, Any] | None:
    """
    Xác định người chi (thanh toán hóa đơn) nhiều nhất cho nhóm.
    Trả về thông tin người chi nhiều nhất và tổng tiền đã chi, hoặc None nếu chưa có giao dịch.
    """
    spending_by_person: dict[Any, dict[str, Any]] = {}

    for exp in expenses:
        pid = _get_field(exp, payer_id_field)
        pname = _get_field(exp, payer_name_field)
        key = pid if pid is not None else pname
        if key is None:
            continue

        amt = _to_decimal(_get_field(exp, amount_field, 0))
        if key not in spending_by_person:
            spending_by_person[key] = {
                "payer_id": pid,
                "payer_name": pname or str(pid),
                "total_paid": Decimal("0"),
                "expense_count": 0,
            }

        spending_by_person[key]["total_paid"] += amt
        spending_by_person[key]["expense_count"] += 1

    if not spending_by_person:
        return None

    return max(spending_by_person.values(), key=lambda entry: entry["total_paid"])


def get_group_expense_summary(expenses: Iterable[Any]) -> dict[str, Any]:
    """
    Tổng hợp toàn bộ thống kê cơ bản cho màn hình Thống kê & Báo cáo Word:
    - Tổng chi tiêu nhóm
    - Số lượng khoản chi
    - Trung bình mỗi khoản chi
    - Khoản chi lớn nhất / nhỏ nhất
    - Người chi nhiều nhất
    - Bảng tổng chi theo từng người trả
    """
    expense_list = list(expenses)
    total_amount = calculate_total_group_expense(expense_list)
    count = len(expense_list)
    extremes = get_extreme_expenses(expense_list)
    top_spender = get_top_spender(expense_list)

    avg_amount = (
        (total_amount / Decimal(count)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        if count > 0
        else Decimal("0")
    )

    per_payer: dict[Any, dict[str, Any]] = {}
    for exp in expense_list:
        pid = _get_field(exp, "payer_id")
        pname = _get_field(exp, "payer_name") or str(pid)
        key = pid if pid is not None else pname
        amt = _to_decimal(_get_field(exp, "amount", 0))
        if key not in per_payer:
            per_payer[key] = {"payer_id": pid, "payer_name": pname, "total_paid": Decimal("0")}
        per_payer[key]["total_paid"] += amt

    sorted_payers = sorted(
        per_payer.values(), key=lambda x: x["total_paid"], reverse=True
    )

    return {
        "total_amount": total_amount,
        "expense_count": count,
        "average_amount": avg_amount,
        "max_expense": extremes["max_expense"],
        "min_expense": extremes["min_expense"],
        "top_spender": top_spender,
        "spending_breakdown": sorted_payers,
    }