from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Sequence


class ValidationError(ValueError):
    """Ngoại lệ dùng chung cho lỗi dữ liệu đầu vào không hợp lệ."""


def parse_positive_amount(amount: Any, field_name: str = "Số tiền") -> Decimal:
    """
    Chuyển đổi và kiểm tra số tiền phải là số hợp lệ và lớn hơn 0.
    Trả về kiểu Decimal để tránh sai số dấu phẩy động khi tính tiền.
    """
    if isinstance(amount, bool) or amount is None:
        raise ValidationError(f"{field_name} không hợp lệ.")

    try:
        dec_amount = Decimal(str(amount).strip().replace(",", ""))
    except (InvalidOperation, AttributeError):
        raise ValidationError(f"{field_name} phải là một giá trị số hợp lệ.")

    if dec_amount.is_nan() or dec_amount.is_infinite():
        raise ValidationError(f"{field_name} không hợp lệ.")

    if dec_amount <= Decimal("0"):
        raise ValidationError(f"{field_name} phải lớn hơn 0.")

    return dec_amount


def validate_non_empty_name(
    name: Any,
    field_name: str = "Tên",
    min_length: int = 1,
    max_length: int = 120,
) -> str:
    """Kiểm tra chuỗi tên/mô tả không rỗng và nằm trong giới hạn độ dài."""
    if not isinstance(name, str):
        raise ValidationError(f"{field_name} phải là chuỗi ký tự.")

    cleaned = " ".join(name.strip().split())
    if len(cleaned) < min_length:
        raise ValidationError(f"{field_name} không được để trống.")
    if len(cleaned) > max_length:
        raise ValidationError(f"{field_name} không được vượt quá {max_length} ký tự.")

    return cleaned


def validate_percentages(
    percentages: Sequence[Any],
    tolerance: Decimal = Decimal("0.01"),
) -> list[Decimal]:
    """
    Kiểm tra danh sách tỷ lệ phần trăm chia hóa đơn:
    - Không rỗng
    - Mỗi tỷ lệ >= 0 và <= 100
    - Tổng tỷ lệ bằng 100% (cho phép sai số nhỏ theo tolerance nếu có làm tròn)
    """
    if not percentages:
        raise ValidationError("Danh sách tỷ lệ chia không được để trống.")

    parsed: list[Decimal] = []
    for idx, pct in enumerate(percentages, start=1):
        if isinstance(pct, bool) or pct is None:
            raise ValidationError(f"Tỷ lệ phần trăm ở vị trí thứ {idx} không hợp lệ.")
        try:
            val = Decimal(str(pct).strip())
        except (InvalidOperation, AttributeError):
            raise ValidationError(f"Tỷ lệ phần trăm ở vị trí thứ {idx} phải là số.")

        if val < Decimal("0") or val > Decimal("100"):
            raise ValidationError(
                f"Tỷ lệ phần trăm ở vị trí thứ {idx} ({val}%) phải nằm trong khoảng 0% - 100%."
            )
        parsed.append(val)

    total = sum(parsed, Decimal("0"))
    target = Decimal("100")
    if abs(total - target) > tolerance:
        raise ValidationError(
            f"Tổng tỷ lệ chia hiện tại là {total}%, phải bằng đúng 100%."
        )

    return parsed


def validate_fixed_shares(
    shares: Sequence[Any],
    total_amount: Any,
    tolerance: Decimal = Decimal("1"),
) -> list[Decimal]:
    """
    Kiểm tra chia theo số tiền cố định từng người chịu chi:
    - Mỗi phần >= 0
    - Tổng các phần khớp với tổng hóa đơn
    """
    expected_total = parse_positive_amount(total_amount, "Tổng hóa đơn")
    if not shares:
        raise ValidationError("Danh sách số tiền chia không được để trống.")

    parsed: list[Decimal] = []
    for idx, s in enumerate(shares, start=1):
        if isinstance(s, bool) or s is None:
            raise ValidationError(f"Khoản chia ở vị trí thứ {idx} không hợp lệ.")
        try:
            val = Decimal(str(s).strip().replace(",", ""))
        except (InvalidOperation, AttributeError):
            raise ValidationError(f"Khoản chia ở vị trí thứ {idx} phải là số.")

        if val < Decimal("0"):
            raise ValidationError(f"Khoản chia ở vị trí thứ {idx} không được âm.")
        parsed.append(val)

    actual_sum = sum(parsed, Decimal("0"))
    if abs(actual_sum - expected_total) > tolerance:
        raise ValidationError(
            f"Tổng tiền chia ({actual_sum}) chưa khớp với tổng hóa đơn ({expected_total})."
        )

    return parsed


def validate_participants(
    payer_id: Any,
    participant_ids: Iterable[Any],
    group_member_ids: Iterable[Any] | None = None,
) -> tuple[Any, list[Any]]:
    """
    Kiểm tra người trả tiền và danh sách người chịu chi:
    - Có người trả tiền
    - Danh sách người chịu chi không rỗng và không trùng lặp
    - Nếu có danh sách thành viên nhóm, kiểm tra tất cả đều thuộc nhóm
    """
    if payer_id is None or (isinstance(payer_id, str) and not payer_id.strip()):
        raise ValidationError("Vui lòng chọn người thanh toán hóa đơn.")

    unique_participants: list[Any] = []
    seen = set()
    for pid in participant_ids:
        if pid is None or (isinstance(pid, str) and not pid.strip()):
            raise ValidationError("Danh sách người chịu chi chứa thành viên không hợp lệ.")
        if pid not in seen:
            seen.add(pid)
            unique_participants.append(pid)

    if not unique_participants:
        raise ValidationError("Phải có ít nhất 1 người tham gia chia chi phí.")

    if group_member_ids is not None:
        allowed = set(group_member_ids)
        if payer_id not in allowed:
            raise ValidationError("Người thanh toán không thuộc nhóm hiện tại.")
        invalid_members = [pid for pid in unique_participants if pid not in allowed]
        if invalid_members:
            raise ValidationError(
                f"Các thành viên sau không thuộc nhóm: {invalid_members}"
            )

    return payer_id, unique_participants


def parse_date_Flexible(date_value: Any, field_name: str = "Ngày") -> datetime:
    """Chuyển đổi chuỗi ngày (YYYY-MM-DD hoặc DD/MM/YYYY) hoặc datetime/date thành datetime."""
    if isinstance(date_value, datetime):
        return date_value

    if hasattr(date_value, "year") and hasattr(date_value, "month") and hasattr(date_value, "day"):
        return datetime(date_value.year, date_value.month, date_value.day)

    if not isinstance(date_value, str) or not date_value.strip():
        raise ValidationError(f"{field_name} không được để trống.")

    raw = date_value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    raise ValidationError(
        f"{field_name} ('{raw}') không đúng định dạng (hỗ trợ YYYY-MM-DD hoặc DD/MM/YYYY)."
    )


def validate_expense_input(
    title: Any,
    amount: Any,
    payer_id: Any,
    participant_ids: Iterable[Any],
    expense_date: Any = None,
    split_mode: str = "equal",
    percentages: Sequence[Any] | None = None,
    fixed_shares: Sequence[Any] | None = None,
    group_member_ids: Iterable[Any] | None = None,
) -> dict[str, Any]:
    """
    Hàm tổng hợp kiểm tra toàn bộ dữ liệu một khoản chi trước khi lưu vào CSDL/gọi Backend.
    Trả về dict dữ liệu đã chuẩn hóa nếu hợp lệ, hoặc ném ValidationError nếu sai.
    """
    clean_title = validate_non_empty_name(title, field_name="Tên khoản chi")
    clean_amount = parse_positive_amount(amount, field_name="Số tiền hóa đơn")
    clean_payer, clean_participants = validate_participants(
        payer_id, participant_ids, group_member_ids
    )

    clean_date = (
        parse_date_Flexible(expense_date, field_name="Ngày chi tiêu")
        if expense_date is not None
        else datetime.now()
    )

    mode = (split_mode or "equal").strip().lower()
    normalized_shares: dict[Any, Decimal] = {}

    if mode == "equal":
        count = Decimal(len(clean_participants))
        base_share = (clean_amount / count).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        for pid in clean_participants:
            normalized_shares[pid] = base_share

    elif mode in ("percent", "percentage"):
        if percentages is None or len(percentages) != len(clean_participants):
            raise ValidationError(
                "Số lượng tỷ lệ phần trăm phải khớp với số người chịu chi."
            )
        pcts = validate_percentages(percentages)
        for pid, pct in zip(clean_participants, pcts):
            share = (clean_amount * pct / Decimal("100")).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
            normalized_shares[pid] = share

    elif mode in ("exact", "fixed"):
        if fixed_shares is None or len(fixed_shares) != len(clean_participants):
            raise ValidationError(
                "Số lượng khoản chia cố định phải khớp với số người chịu chi."
            )
        shares = validate_fixed_shares(fixed_shares, clean_amount)
        for pid, sh in zip(clean_participants, shares):
            normalized_shares[pid] = sh.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    else:
        raise ValidationError(
            f"Chế độ chia tiền '{split_mode}' không hỗ trợ (chỉ nhận 'equal', 'percent', 'exact')."
        )

    return {
        "title": clean_title,
        "amount": clean_amount,
        "payer_id": clean_payer,
        "participant_ids": clean_participants,
        "date": clean_date,
        "split_mode": mode,
        "shares": normalized_shares,
    }