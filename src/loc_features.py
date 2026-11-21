import copy
import csv
import re
import unicodedata
from pathlib import Path
from typing import Optional
import pandas as pd
import qrcode

# Chỉ sử dụng 5 ngân hàng theo danh sách tài khoản của nhóm (chuẩn BIN NAPAS)
BANK_BINS = {
    "TCB": "970407",          # Techcombank
    "TECHCOMBANK": "970407",
    "ACB": "970416",          # ACB
    "TPB": "970423",          # TPBank
    "TPBANK": "970423",
    "MB": "970422",           # MBBank
    "TIMO": "963388",         # Timo by BVBank
}


# ==============================================================================
# 1. TẠO MÃ VIETQR CHUẨN NGÂN HÀNG & THANH TOÁN LẦN LƯỢT TỪNG NGƯỜI
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
    """Sinh 1 ảnh mã VietQR chuẩn ngân hàng (NAPAS 247) kèm số tiền & nội dung."""
    if not bank_code or not str(bank_code).strip():
        raise ValueError("Mã ngân hàng không được để trống.")
    if not account_no or not str(account_no).strip():
        raise ValueError("Số tài khoản không được để trống.")
    if amount is None or amount <= 0:
        raise ValueError("Số tiền thanh toán phải lớn hơn 0.")

    # Chuẩn hóa tên ngân hàng (ví dụ: 'tp bank' -> 'TPBANK')
    normalized_bank = re.sub(r"\s+", "", str(bank_code).strip().upper())
    bin_code = BANK_BINS.get(normalized_bank, normalized_bank)
    if not (bin_code.isdigit() and len(bin_code) == 6):
        raise ValueError(f"Mã ngân hàng không hợp lệ: {bank_code}")

    clean_acc = re.sub(r"\s+", "", str(account_no))
    if not clean_acc.isalnum():
        raise ValueError("Số tài khoản chỉ được chứa chữ và số.")

    clean_amt = str(int(round(amount)))
    clean_note = _chuan_hoa_noi_dung(note)

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


def tao_qr_cho_tung_nguoi(
    settlements: list,
    output_dir: str = "exports/qr_thanh_toan",
) -> list:
    """
    Sinh riêng từng mã VietQR cho TẤT CẢ các giao dịch trả nợ trong danh sách.
    Mỗi giao dịch có thêm 'qr_image' (ảnh PIL) và 'qr_path' (đường dẫn file PNG).
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    ket_qua = []

    for idx, item in enumerate(settlements, start=1):
        giao_dich = copy.deepcopy(item)
        nguoi_tra = giao_dich["from_user"]
        nguoi_nhan = giao_dich["to_user"]
        so_tien = giao_dich["amount"]
        noi_dung = f"{nguoi_tra} chuyen tien cho {nguoi_nhan}"

        ten_file = f"{idx:02d}_{_chuan_hoa_noi_dung(nguoi_tra)}_chuyen_{_chuan_hoa_noi_dung(nguoi_nhan)}.png".replace(" ", "_")
        duong_dan = f"{output_dir}/{ten_file}"

        qr_img = tao_ma_vietqr(
            bank_code=giao_dich["bank"],
            account_no=giao_dich["account"],
            amount=so_tien,
            note=noi_dung,
            save_path=duong_dan,
        )
        giao_dich["note"] = _chuan_hoa_noi_dung(noi_dung)
        giao_dich["qr_image"] = qr_img
        giao_dich["qr_path"] = duong_dan
        ket_qua.append(giao_dich)

    return ket_qua


class PhienThanhToanTungNguoi:
    """
    Quản lý luồng quét QR lần lượt từng người:
    Người 1 quét QR -> Bấm xác nhận xong -> Tự động chuyển sang QR của Người 2 -> ...
    """

    def __init__(self, settlements: list, output_dir: str = "exports/qr_thanh_toan"):
        self.danh_sach = tao_qr_cho_tung_nguoi(settlements, output_dir=output_dir)
        self.chi_so_hien_tai = 0
        self._bo_qua_nguoi_da_tra()

    def _bo_qua_nguoi_da_tra(self):
        while (
            self.chi_so_hien_tai < len(self.danh_sach)
            and self.danh_sach[self.chi_so_hien_tai].get("status") == "Đã thanh toán"
        ):
            self.chi_so_hien_tai += 1

    def lay_giao_dich_hien_tai(self) -> Optional[dict]:
        """Lấy thông tin + ảnh QR của người đang cần chuyển tiền hiện tại."""
        if self.chi_so_hien_tai >= len(self.danh_sach):
            return None
        gd = self.danh_sach[self.chi_so_hien_tai]
        return {
            "thu_tu": f"{self.chi_so_hien_tai + 1}/{len(self.danh_sach)}",
            **gd,
        }

    def xac_nhan_va_sang_nguoi_tiep_theo(self) -> Optional[dict]:
        """Đánh dấu người hiện tại đã chuyển xong và trả về QR của người tiếp theo."""
        if self.chi_so_hien_tai < len(self.danh_sach):
            self.danh_sach[self.chi_so_hien_tai]["status"] = "Đã thanh toán"
            self.chi_so_hien_tai += 1
            self._bo_qua_nguoi_da_tra()
        return self.lay_giao_dich_hien_tai()

    def da_hoan_tat_tat_ca(self) -> bool:
        """Trả về True khi tất cả mọi người trong nhóm đã chuyển tiền xong."""
        return self.chi_so_hien_tai >= len(self.danh_sach)


# ==============================================================================
# 2. MODULE XUẤT BÁO CÁO LỊCH SỬ CHI TIÊU & DANH SÁCH NỢ (CSV / EXCEL)
# ==============================================================================
def xuat_bao_cao_csv(
    expenses: list,
    settlements: list,
    output_dir: str = "exports",
) -> tuple:
    """Xuất lịch sử chi tiêu và danh sách nợ ra 2 file CSV."""
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
# 3. DỮ LIỆU MẪU DEMO (CHUYẾN DU LỊCH ĐÀ LẠT 3N2Đ - DÙNG ĐÚNG 5 TÀI KHOẢN)
# ==============================================================================
MOCK_DATA = {
    "group_name": "Du lịch Đà Lạt 3 ngày 2 đêm",
    "members": [
        {"name": "Kiên", "bank": "TCB", "account": "2725102007"},
        {"name": "Lợi", "bank": "ACB", "account": "40673317"},
        {"name": "Lương", "bank": "TPB", "account": "71139791234"},
        {"name": "Lộc", "bank": "MB", "account": "0767120559"},
        {"name": "Thục", "bank": "TIMO", "account": "9021369617471"},
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
            "from_user": "Lộc",
            "to_user": "Lợi",
            "bank": "ACB",
            "account": "40673317",
            "amount": 900000,
            "status": "Chưa thanh toán",
        },
        {
            "from_user": "Thục",
            "to_user": "Kiên",
            "bank": "TCB",
            "account": "2725102007",
            "amount": 1100000,
            "status": "Chưa thanh toán",
        },
        {
            "from_user": "Lương",
            "to_user": "Lợi",
            "bank": "ACB",
            "account": "40673317",
            "amount": 100000,
            "status": "Chưa thanh toán",
        },
    ],
}


if __name__ == "__main__":
    phien_qr = PhienThanhToanTungNguoi(MOCK_DATA["settlements"], output_dir="exports/qr_thanh_toan")

    print("=== BAT DAU PHIEN THANH TOAN VIETQR TUNG NGUOI ===")
    gd_hien_tai = phien_qr.lay_giao_dich_hien_tai()
    while gd_hien_tai is not None:
        print(
            f"[{gd_hien_tai['thu_tu']}] {gd_hien_tai['from_user']} -> {gd_hien_tai['to_user']} "
            f"({gd_hien_tai['bank']} - {gd_hien_tai['account']}) "
            f"| So tien: {gd_hien_tai['amount']:,} VND "
            f"| Anh QR: {gd_hien_tai['qr_path']}"
        )
        gd_hien_tai = phien_qr.xac_nhan_va_sang_nguoi_tiep_theo()

    print("=== DA HOAN TAT THANH TOAN CHO TAT CA MOI NGUOI! ===")
    xuat_bao_cao_csv(MOCK_DATA["expenses"], phien_qr.danh_sach, "exports")
    xuat_bao_cao_excel(MOCK_DATA["expenses"], phien_qr.danh_sach, "exports/bao_cao_chi_tieu.xlsx")
    print("Da xuat bao cao CSV va Excel trong thu muc exports/!")