## 5. Cấu trúc dự án

```text
ChuDe13/
├── database/                   # Cơ sở dữ liệu SQLite cục bộ
│
├── docs/                       # Tài liệu dự án
│   ├── architecture.md         # Kiến trúc tổng thể
│   ├── database_design.md      # Thiết kế cơ sở dữ liệu
│   ├── data_dictionary.md      # Từ điển dữ liệu
│   ├── gui_ux/                 # Tài liệu thiết kế giao diện
│   ├── diagrams/               # Sơ đồ hệ thống
│   └── reports/                # Báo cáo dự án
│
├── src/                        # Mã nguồn ứng dụng
│   ├── create_tables.py        # Khởi tạo cấu trúc database
│   ├── expense_service.py      # Xử lý nghiệp vụ chi tiêu
│   ├── expense_split.py        # Thuật toán chia hóa đơn
│   ├── settlement_service.py   # Xử lý quyết toán
│   ├── main.py                 # Điểm khởi chạy ứng dụng
│   ├── gui/                    # Giao diện người dùng
│   ├── integrations/           # Tích hợp dịch vụ bên ngoài
│   │   └── vietqr/
│   └── exports/                # Chức năng xuất dữ liệu
│
├── tests/                      # Bộ kiểm thử
│   ├── test_expense_split.py
│   ├── test_expense_service.py
│   ├── test_settlement_workflow.py
│   ├── gui/
│   └── integrations/
│
├── assets/                     # Tài nguyên giao diện
│   ├── images/
│   ├── icons/
│   └── screenshots/
│
├── README.md                   # Giới thiệu dự án
├── CONTRIBUTING.md             # Quy định đóng góp
├── requirements.txt            # Danh sách thư viện
└── .gitignore                  # Quy tắc loại trừ file Git
```

### Mô tả thư mục

| Thư mục | Chức năng |
|---|---|
| `database/` | Lưu trữ cơ sở dữ liệu SQLite cục bộ |
| `docs/` | Lưu tài liệu thiết kế, kiến trúc và báo cáo |
| `src/` | Chứa mã nguồn và các module chức năng |
| `tests/` | Chứa các chương trình kiểm thử |
| `assets/` | Lưu hình ảnh, icon và tài nguyên giao diện |
