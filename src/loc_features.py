import csv
import re
import unicodedata
from pathlib import Path
from typing import Optional
import pandas as pd
import qrcode

# Mã BIN ngân hàng chuẩn NAPAS
BANK_BINS = {
    "VCB": "970436",   # Vietcombank
    "MB": "970422",    # MBBank
    "TCB": "970407",   # Techcombank
    "BIDV": "970418",  # BIDV
    "VTB": "970415",   # VietinBank
    "ACB": "970416",   # ACB
    "VPB": "970432",   # VPBank
}


# ==============================================================================
# 1. TÍNH NĂNG TẠO MÃ VIETQR CHUẨN NGÂN HÀNG (SỬ DỤNG THƯ VIỆN QRCODE)
# ==============================================================================
def _chuan_hoa_noi_dung(text: str) -> str:
    """Chuyển tiếng Việt có dấu thành không dấu, bỏ ký tự đặc biệt cho nội dung CK."""
    text = text.replace("đ", "d").replace("Đ", "D")
    no_accent = "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )
    return re.sub(r"[^a-zA-Z0-9\s]", "", no_accent).strip()[:50]


def _tinh_crc16(data: str) -> str:
    """Tính mã kiểm tra CRC-16/CCITT-FALSE theo chuẩn EMVCo VietQR."""
    crc = 0xFFFF
    for byte in data.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if (crc & 0x8000) else (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def tao_ma_vietqr(
    bank_code: str,
    account_no: str,
    amount: float,
    note: str = "Thanh toan no nhom",
    save_path: Optional[str] = None,
):
    """
    Tự động sinh mã QR chuyển khoản chuẩn ngân hàng (NAPAS 247) kèm số tiền & nội dung.
    Trả về đối tượng ảnh PIL để gắn trực tiếp lên giao diện.
    """
    if not bank_code or not str(bank_code).strip():
        raise ValueError("Mã ngân hàng không được để trống.")
    if not account_no or not str(account_no).strip():
        raise ValueError("Số tài khoản không được để trống.")
    if amount is None or amount <= 0:
        raise ValueError("Số tiền thanh toán phải lớn hơn 0.")

    bin_code = BANK_BINS.get(bank_code.strip().upper(), bank_code.strip())
    if not (bin_code.isdigit() and len(bin_code) == 6):
        raise ValueError(f"Mã ngân hàng không hợp lệ: {bank_code}")

    clean_acc = re.sub(r"\s+", "", str(account_no))
    if not clean_acc.isalnum():
        raise ValueError("Số tài khoản chỉ được chứa chữ và số.")

    clean_amt = str(int(round(amount)))
    clean_note = _chuan_hoa_noi_dung(note)

    # Đóng gói chuỗi dữ liệu EMVCo VietQR
    tlv = lambda tag, val: f"{tag}{len(val):02d}{val}"
    merchant_info = (
        tlv("00", "A000000727")
        + tlv("01", tlv("00", bin_code) + tlv("01", clean_acc))
        + tlv("02", "QRIBFTTA")
    )
    raw_payload = (
        tlv("00", "01")
        + tlv("01", "12")
        + tlv("38", merchant_info)
        + tlv("53", "704")
        + tlv("54", clean_amt)
        + tlv("58", "VN")
        + (tlv("62", tlv("08", clean_note)) if clean_note else "")
        + "6304"
    )
    payload = raw_payload + _tinh_crc16(raw_payload)

    qr_img = qrcode.make(payload).convert("RGB")
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        qr_img.save(save_path)
    return qr_img


# ==============================================================================
# 2. MODULE XUẤT BÁO CÁO LỊCH SỬ CHI TIÊU & DANH SÁCH NỢ (CSV / EXCEL)
# ==============================================================================
def xuat_bao_cao_csv(
    expenses: list,
    settlements: list,
    output_dir: str = "exports",
) -> tuple:
    """Xuất lịch sử chi tiêu và danh sách nợ ra 2 file CSV (dùng thư viện csv)."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    exp_path = f"{output_dir}/lich_su_chi_tieu.csv"
    set_path = f"{output_dir}/danh_sach_no.csv"

    exp_headers = ["date", "title", "payer", "amount", "split_type", "participants"]
    with open(exp_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=exp_headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(expenses)

    set_headers = ["from_user", "to_user", "bank", "account", "amount", "status"]
    with open(set_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=set_headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(settlements)

    return exp_path, set_path


def xuat_bao_cao_excel(
    expenses: list,
    settlements: list,
    filepath: str = "exports/bao_cao_chi_tieu.xlsx",
) -> str:
    """Xuất báo cáo tổng hợp gồm 2 sheet ra file Excel (.xlsx) bằng pandas."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    df_exp = pd.DataFrame(
        expenses,
        columns=["date", "title", "payer", "amount", "split_type", "participants"],
    )
    df_exp.columns = ["Ngày", "Khoản Chi", "Người Trả", "Số Tiền (VND)", "Kiểu Chia", "Người Tham Gia"]

    df_set = pd.DataFrame(
        settlements,
        columns=["from_user", "to_user", "bank", "account", "amount", "status"],
    )
    df_set.columns = ["Người Trả Nợ", "Người Nhận", "Ngân Hàng", "Số Tài Khoản", "Số Tiền (VND)", "Trạng Thái"]

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df_exp.to_excel(writer, sheet_name="Lich_Su_Chi_Tieu", index=False)
        df_set.to_excel(writer, sheet_name="Danh_Sach_No", index=False)

        for sheet in writer.sheets.values():
            for col in sheet.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                sheet.column_dimensions[col[0].column_letter].width = max(max_len + 4, 15)

    return filepath


# ==============================================================================
# 3. DỮ LIỆU MẪU DEMO (CHUYẾN DU LỊCH ĐÀ LẠT 3N2Đ CỦA NHÓM 5 NGƯỜI)
# ==============================================================================
MOCK_DATA = {
    "group_name": "Du lịch Đà Lạt 3 ngày 2 đêm",
    "members": [
        {"name": "Kiên", "bank": "VCB", "account": "1012345678"},
        {"name": "Lợi", "bank": "MB", "account": "0912345678"},
        {"name": "Lương", "bank": "TCB", "account": "19034567890123"},
        {"name": "Lộc", "bank": "ACB", "account": "88997766"},
        {"name": "Thục", "bank": "BIDV", "account": "31410001234567"},
    ],
    "expenses": [
        {
            "date": "2026-11-15",
            "title": "Thuê Homestay 2 đêm",
            "payer": "Kiên",
            "amount": 2500000,
            "split_type": "Chia đều",
            "participants": "Kiên, Lợi, Lương, Lộc, Thục (500k/người)",
        },
        {
            "date": "2026-11-15",
            "title": "Vé xe khách khứ hồi",
            "payer": "Lợi",
            "amount": 2000000,
            "split_type": "Chia đều",
            "participants": "Kiên, Lợi, Lương, Lộc, Thục (400k/người)",
        },
        {
            "date": "2026-11-15",
            "title": "Ăn tối lẩu gà & nướng BBQ",
            "payer": "Lương",
            "amount": 1200000,
            "split_type": "Số tiền cố định",
            "participants": "Kiên, Lương, Lộc, Thục (300k/người)",
        },
        {
            "date": "2026-11-16",
            "title": "Cafe săn mây & vé đồi chè",
            "payer": "Lộc",
            "amount": 500000,
            "split_type": "Phần trăm",
            "participants": "Kiên, Lợi, Lương, Lộc, Thục (20%/người)",
        },
        {
            "date": "2026-11-17",
            "title": "Ăn vặt chợ đêm Đà Lạt",
            "payer": "Thục",
            "amount": 300000,
            "split_type": "Chia đều nhóm nhỏ",
            "participants": "Kiên, Lộc, Thục (100k/người)",
        },
    ],
    "settlements": [
        {
            "from_user": "Thục",
            "to_user": "Kiên",
            "bank": "VCB",
            "account": "1012345678",
            "amount": 1100000,
            "status": "Chưa thanh toán",
        },
        {
            "from_user": "Lộc",
            "to_user": "Lợi",
            "bank": "MB",
            "account": "0912345678",
            "amount": 900000,
            "status": "Chưa thanh toán",
        },
        {
            "from_user": "Lương",
            "to_user": "Lợi",
            "bank": "MB",
            "account": "0912345678",
            "amount": 100000,
            "status": "Chưa thanh toán",
        },
    ],
}


if __name__ == "__main__":
    tao_ma_vietqr("MB", "0912345678", 900000, "Loc tra tien Loi", "exports/demo_vietqr.png")
    xuat_bao_cao_csv(MOCK_DATA["expenses"], MOCK_DATA["settlements"], "exports")
    xuat_bao_cao_excel(MOCK_DATA["expenses"], MOCK_DATA["settlements"], "exports/bao_cao_chi_tieu.xlsx")
    print("Da tao xong anh VietQR + file CSV + file Excel trong thu muc exports/!")