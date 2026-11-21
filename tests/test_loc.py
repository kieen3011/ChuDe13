import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.loc_features import (
    MOCK_DATA,
    PhienThanhToanTungNguoi,
    tao_ma_vietqr,
    tao_qr_cho_tung_nguoi,
    xuat_bao_cao_csv,
    xuat_bao_cao_excel,
)


class TestHeThongVaNgoaiLe(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # --- KỊCH BẢN 1: KIỂM TRA ĐỦ 5 TÀI KHOẢN NGÂN HÀNG CỦA NHÓM ---
    def test_tao_qr_ca_5_tai_khoan_ngan_hang(self):
        danh_sach_tai_khoan = [
            ("TCB", "2725102007"),
            ("ACB", "40673317"),
            ("TPB", "71139791234"),
            ("MB", "0767120559"),
            ("TIMO", "9021369617471"),
        ]
        for idx, (bank, acc) in enumerate(danh_sach_tai_khoan, start=1):
            qr_path = os.path.join(self.temp_dir, f"qr_{idx}_{bank}.png")
            img = tao_ma_vietqr(bank, acc, 100000 * idx, f"Test chuyen tien {bank}", qr_path)
            self.assertTrue(os.path.exists(qr_path))
            self.assertGreater(img.size[0], 100)

    # --- KỊCH BẢN 2: TẠO MÃ VIETQR LẦN LƯỢT TỪNG NGƯỜI ---
    def test_tao_qr_cho_tat_ca_moi_nguoi(self):
        qr_dir = os.path.join(self.temp_dir, "qr_list")
        danh_sach_qr = tao_qr_cho_tung_nguoi(MOCK_DATA["settlements"], qr_dir)

        self.assertEqual(len(danh_sach_qr), 3)
        for item in danh_sach_qr:
            self.assertTrue(os.path.exists(item["qr_path"]))
            self.assertGreater(item["qr_image"].size[0], 100)

    def test_luong_thanh_toan_tuan_tu_tung_nguoi(self):
        qr_dir = os.path.join(self.temp_dir, "qr_seq")
        phien = PhienThanhToanTungNguoi(MOCK_DATA["settlements"], qr_dir)

        # Người 1: Lộc chuyển cho Lợi (ACB - 40673317)
        gd1 = phien.lay_giao_dich_hien_tai()
        self.assertEqual(gd1["thu_tu"], "1/3")
        self.assertEqual(gd1["from_user"], "Lộc")
        self.assertEqual(gd1["to_user"], "Lợi")
        self.assertEqual(gd1["account"], "40673317")

        # Xong người 1 -> Tự động chuyển sang Người 2: Thục chuyển cho Kiên (TCB - 2725102007)
        gd2 = phien.xac_nhan_va_sang_nguoi_tiep_theo()
        self.assertEqual(gd2["thu_tu"], "2/3")
        self.assertEqual(gd2["from_user"], "Thục")
        self.assertEqual(gd2["to_user"], "Kiên")
        self.assertEqual(gd2["account"], "2725102007")

        # Xong người 2 -> Tự động chuyển sang Người 3: Lương chuyển cho Lợi (ACB - 40673317)
        gd3 = phien.xac_nhan_va_sang_nguoi_tiep_theo()
        self.assertEqual(gd3["thu_tu"], "3/3")
        self.assertEqual(gd3["from_user"], "Lương")

        # Xong người 3 -> Hết danh sách
        gd4 = phien.xac_nhan_va_sang_nguoi_tiep_theo()
        self.assertIsNone(gd4)
        self.assertTrue(phien.da_hoan_tat_tat_ca())

    def test_vietqr_corner_cases_khong_crash(self):
        with self.assertRaises(ValueError):
            tao_ma_vietqr("TCB", "2725102007", -10000)
        with self.assertRaises(ValueError):
            tao_ma_vietqr("TCB", "2725102007", 0)
        with self.assertRaises(ValueError):
            tao_ma_vietqr("BANK_KHONG_DUNG", "2725102007", 50000)
        with self.assertRaises(ValueError):
            tao_ma_vietqr("TCB", "", 50000)

        phien_rong = PhienThanhToanTungNguoi([], self.temp_dir)
        self.assertTrue(phien_rong.da_hoan_tat_tat_ca())
        self.assertIsNone(phien_rong.lay_giao_dich_hien_tai())

    # --- KỊCH BẢN 3: XUẤT BÁO CÁO CSV & EXCEL ---
    def test_xuat_bao_cao_day_du_du_lieu(self):
        exp_csv, set_csv = xuat_bao_cao_csv(
            MOCK_DATA["expenses"], MOCK_DATA["settlements"], self.temp_dir
        )
        xlsx_path = os.path.join(self.temp_dir, "report.xlsx")
        xuat_bao_cao_excel(MOCK_DATA["expenses"], MOCK_DATA["settlements"], xlsx_path)

        self.assertTrue(os.path.exists(exp_csv))
        self.assertTrue(os.path.exists(set_csv))
        self.assertTrue(os.path.exists(xlsx_path))

        excel_file = pd.ExcelFile(xlsx_path)
        self.assertEqual(excel_file.sheet_names, ["Lich_Su_Chi_Tieu", "Danh_Sach_No"])

    # --- KỊCH BẢN 4: ĐỐI SOÁT SỐ LIỆU MOCK DATA ---
    def test_mock_data_can_doi_ke_toan(self):
        self.assertEqual(sum(i["amount"] for i in MOCK_DATA["expenses"]), 6500000)
        self.assertEqual(sum(i["amount"] for i in MOCK_DATA["settlements"]), 2100000)


if __name__ == "__main__":
    unittest.main(verbosity=2)