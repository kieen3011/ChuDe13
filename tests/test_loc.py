import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
import pandas as pd

# Thêm thư mục gốc dự án vào sys.path để import được từ src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.loc_features import (
    MOCK_DATA,
    tao_ma_vietqr,
    xuat_bao_cao_csv,
    xuat_bao_cao_excel,
)


class TestHeThongVaNgoaiLe(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # --- KỊCH BẢN 1: TẠO MÃ VIETQR ---
    def test_vietqr_hoat_dong_chuan(self):
        qr_path = os.path.join(self.temp_dir, "qr_test.png")
        img = tao_ma_vietqr("VCB", "1012345678", 1100000, "Thục trả tiền Kiên", qr_path)
        self.assertTrue(os.path.exists(qr_path))
        self.assertGreater(img.size[0], 100)

    def test_vietqr_corner_cases_khong_crash(self):
        # 1. Số tiền âm hoặc bằng 0 -> Phải báo ValueError rõ ràng
        with self.assertRaises(ValueError):
            tao_ma_vietqr("VCB", "1012345678", -10000)
        with self.assertRaises(ValueError):
            tao_ma_vietqr("VCB", "1012345678", 0)

        # 2. Mã ngân hàng sai hoặc bỏ trống số tài khoản
        with self.assertRaises(ValueError):
            tao_ma_vietqr("BANK_KHONG_TON_TAI", "1012345678", 50000)
        with self.assertRaises(ValueError):
            tao_ma_vietqr("VCB", "", 50000)

        # 3. Nội dung chuyển khoản có ký tự đặc biệt & tiếng Việt dài > 50 ký tự
        img = tao_ma_vietqr(
            "MB",
            "0912345678",
            250000,
            "Đặng Thanh Lộc chuyển tiền ăn lẩu gà @Đà Lạt 2026!!! Rất dài...",
        )
        self.assertIsNotNone(img)

    # --- KỊCH BẢN 2: XUẤT BÁO CÁO CSV & EXCEL ---
    def test_xuat_bao_cao_day_du_du_lieu(self):
        exp_csv, set_csv = xuat_bao_cao_csv(
            MOCK_DATA["expenses"], MOCK_DATA["settlements"], self.temp_dir
        )
        xlsx_path = os.path.join(self.temp_dir, "report.xlsx")
        xuat_bao_cao_excel(MOCK_DATA["expenses"], MOCK_DATA["settlements"], xlsx_path)

        self.assertTrue(os.path.exists(exp_csv))
        self.assertTrue(os.path.exists(set_csv))
        self.assertTrue(os.path.exists(xlsx_path))

        # Đọc lại file Excel kiểm tra đủ 2 sheet và đúng số dòng
        excel_file = pd.ExcelFile(xlsx_path)
        self.assertEqual(excel_file.sheet_names, ["Lich_Su_Chi_Tieu", "Danh_Sach_No"])
        self.assertEqual(len(excel_file.parse("Lich_Su_Chi_Tieu")), 5)
        self.assertEqual(len(excel_file.parse("Danh_Sach_No")), 3)

    def test_xuat_bao_cao_corner_case_du_lieu_rong(self):
        # Nhóm mới tạo chưa có khoản chi nào vẫn xuất file bình thường, không crash
        exp_csv, set_csv = xuat_bao_cao_csv([], [], self.temp_dir)
        xlsx_path = os.path.join(self.temp_dir, "empty.xlsx")
        xuat_bao_cao_excel([], [], xlsx_path)

        self.assertTrue(os.path.exists(exp_csv))
        self.assertTrue(os.path.exists(xlsx_path))

    # --- KỊCH BẢN 3: ĐỐI SOÁT SỐ LIỆU MOCK DATA DEMO ---
    def test_mock_data_can_doi_ke_toan(self):
        tong_chi = sum(item["amount"] for item in MOCK_DATA["expenses"])
        self.assertEqual(tong_chi, 6500000)

        tong_hoan_tra = sum(item["amount"] for item in MOCK_DATA["settlements"])
        self.assertEqual(tong_hoan_tra, 2100000)


if __name__ == "__main__":
    unittest.main(verbosity=2)