from datetime import datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterable

from .validation import ValidationError, parse_date_Flexible


def _get_field(item: Any, key: str, default: Any = None) -> Any:
    """Lấy giá trị trường từ dict hoặc object một cách an toàn."""
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


def filter_expenses_by_date(
    expenses: Iterable[Any],
    start_date: Any = None,
    end_date: Any = None,
    date_field: str = "date",
) -> list[Any]:
    """
    Lọc danh sách hóa đơn theo ngày cụ thể hoặc khoảng [start_date, end_date].
    - Nếu chỉ truyền start_date và end_date=None: lọc đúng ngày đó.
    - Nếu truyền cả start_date và end_date: lọc trong khoảng ngày (bao gồm 2 đầu mút).
    """
    start_dt: datetime | None = None
    end_dt: datetime | None = None

    if start_date is not None:
        d_start = parse_date_Flexible(start_date, "Ngày bắt đầu")
        start_dt = datetime.combine(d_start.date(), time.min)

    if end_date is not None:
        d_end = parse_date_Flexible(end_date, "Ngày kết thúc")
        end_dt = datetime.combine(d_end.date(), time.max)
    elif start_dt is not None:
        end_dt = datetime.combine(start_dt.date(), time.max)

    if start_dt and end_dt and start_dt > end_dt:
        raise ValidationError("Ngày bắt đầu không được lớn hơn ngày kết thúc.")

    result: list[Any] = []
    for exp in expenses:
        raw_date = _get_field(exp, date_field)
        if raw_date is None:
            continue
        try:
            exp_dt = parse_date_Flexible(raw_date, date_field)
        except ValidationError:
            continue

        if start_dt and exp_dt < start_dt:
            continue
        if end_dt and exp_dt > end_dt:
            continue
        result.append(exp)

    return result


def filter_expenses_by_payer(
    expenses: Iterable[Any],
    payer_query: Any,
    payer_id_field: str = "payer_id",
    payer_name_field: str = "payer_name",
) -> list[Any]:
    """
    Lọc hóa đơn theo người trả tiền (khớp theo ID chính xác hoặc tên người trả không phân biệt hoa thường).
    """
    if payer_query is None or (isinstance(payer_query, str) and not payer_query.strip()):
        return list(expenses)

    query_str = str(payer_query).strip().lower()
    result: list[Any] = []

    for exp in expenses:
        pid = _get_field(exp, payer_id_field)
        pname = _get_field(exp, payer_name_field)

        matched_id = pid is not None and str(pid).strip().lower() == query_str
        matched_name = pname is not None and query_str in str(pname).strip().lower()

        if matched_id or matched_name:
            result.append(exp)

    return result


def search_expenses_by_title(
    expenses: Iterable[Any],
    keyword: str | None,
    title_field: str = "title",
    note_field: str = "note",
    search_in_note: bool = False,
) -> list[Any]:
    """
    Tìm kiếm hóa đơn theo tên khoản chi (không phân biệt hoa thường, hỗ trợ tiếng Việt có dấu).
    Có thể bật search_in_note=True để tìm cả trong ghi chú nếu cần.
    """
    if not keyword or not keyword.strip():
        return list(expenses)

    kw = " ".join(keyword.strip().lower().split())
    result: list[Any] = []

    for exp in expenses:
        title = str(_get_field(exp, title_field, "") or "").lower()
        if kw in title:
            result.append(exp)
            continue

        if search_in_note:
            note = str(_get_field(exp, note_field, "") or "").lower()
            if kw in note:
                result.append(exp)

    return result


def sort_expenses(
    expenses: Iterable[Any],
    sort_by: str = "date",
    descending: bool = True,
) -> list[Any]:
    """Sắp xếp danh sách hóa đơn theo 'date', 'amount', hoặc 'title'."""
    items = list(expenses)
    key_map: dict[str, Callable[[Any], Any]] = {
        "date": lambda x: parse_date_Flexible(_get_field(x, "date", "1970-01-01"), "date"),
        "amount": lambda x: _to_decimal(_get_field(x, "amount", 0)),
        "title": lambda x: str(_get_field(x, "title", "") or "").lower(),
    }
    key_fn = key_map.get(sort_by, key_map["date"])
    return sorted(items, key=key_fn, reverse=descending)


def get_transaction_history(
    expenses: Iterable[Any],
    keyword: str | None = None,
    payer: Any = None,
    start_date: Any = None,
    end_date: Any = None,
    sort_by: str = "date",
    descending: bool = True,
) -> list[Any]:
    """
    Hàm lọc đa tiêu chí kết hợp cho màn hình Lịch sử giao dịch trên UI:
    lọc theo ngày + lọc theo người trả + tìm kiếm theo tên + sắp xếp.
    """
    filtered = list(expenses)
    filtered = filter_expenses_by_date(filtered, start_date=start_date, end_date=end_date)
    filtered = filter_expenses_by_payer(filtered, payer_query=payer)
    filtered = search_expenses_by_title(filtered, keyword=keyword)
    return sort_expenses(filtered, sort_by=sort_by, descending=descending)