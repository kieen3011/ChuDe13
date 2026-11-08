# ChuDe13 — Group Expense Manager

**Ứng dụng quản lý chi tiêu nhóm và chia sẻ hóa đơn**, được phát triển bằng Python và SQLite.

## 1. Giới thiệu

Group Expense Manager hướng đến việc hỗ trợ các thành viên trong một nhóm quản lý khoản chi chung, theo dõi số tiền mỗi người đã thanh toán và xác định số tiền cần thanh toán giữa các thành viên.

Đây là dự án học tập và phát triển theo nhóm.

## 2. Công nghệ sử dụng

| Công nghệ | Vai trò |
|---|---|
| Python | Ngôn ngữ lập trình chính |
| SQLite | Hệ quản trị cơ sở dữ liệu |
| sqlite3 | Thư viện kết nối SQLite trong Python |
| Git & GitHub | Quản lý mã nguồn và cộng tác nhóm |

## 3. Cấu trúc dự án

```text

GroupExpenseManager/
│
├── database/                       # DATABASE
│   └── group_expense.db            # SQLite database (không push lên GitHub)
│
├── docs/                           # TÀI LIỆU KỸ THUẬT VÀ DỰ ÁN
│   ├── architecture.md             # Kiến trúc tổng thể, cách các module kết nối
│   ├── database_design.md          # Thiết kế database, bảng và quan hệ
│   ├── data_dictionary.md          # Giải thích các trường dữ liệu
│   │
│   ├── gui_ux/                     # TÀI LIỆU THIẾT KẾ GIAO DIỆN
│   │   ├── user_flow/              # Luồng thao tác của người dùng
│   │   ├── wireframes/             # Bản phác thảo bố cục giao diện
│   │   ├── screenshots/            # Ảnh giao diện đã triển khai
│   │   ├── design_guidelines.md    # Màu sắc, font, nút, quy chuẩn UI
│   │   └── README.md               # Hướng dẫn và trạng thái GUI/UX
│   │
│   ├── diagrams/                   # SƠ ĐỒ HỆ THỐNG
│   │   └── README.md               # ERD, DFD, UML và mô tả sơ đồ
│   │
│   └── reports/                    # BÁO CÁO VÀ THUYẾT TRÌNH
│       └── README.md               # Hướng dẫn lưu báo cáo, slide
│
├── src/                            # MÃ NGUỒN ỨNG DỤNG
│   ├── create_tables.py            # Tạo cấu trúc các bảng database
│   ├── expense_service.py          # Xử lý nghiệp vụ khoản chi
│   ├── expense_split.py             # Logic chia khoản chi
│   ├── settlement_service.py       # Tính toán và xử lý quyết toán
│   ├── main.py                     # Điểm khởi chạy ứng dụng
│   │
│   ├── gui/                        # GIAO DIỆN NGƯỜI DÙNG
│   │   └── README.md               # Hướng dẫn cấu trúc và kết nối GUI
│   │
│   ├── integrations/               # TÍCH HỢP DỊCH VỤ BÊN NGOÀI
│   │   └── vietqr/
│   │       └── README.md           # Hướng dẫn tích hợp VietQR
│   │
│   └── exports/                    # XUẤT DỮ LIỆU
│       └── README.md               # Hướng dẫn xuất CSV và Excel
│
├── tests/                          # KIỂM THỬ
│   ├── test_expense_split.py       # Test logic chia khoản chi
│   ├── test_expense_service.py     # Test nghiệp vụ khoản chi
│   ├── test_settlement_workflow.py # Test quy trình quyết toán
│   │
│   ├── gui/                        # Test giao diện
│   └── integrations/               # Test VietQR và xuất dữ liệu
│
├── assets/                         # TÀI NGUYÊN GIAO DIỆN
│   ├── images/                     # Hình ảnh sử dụng trong ứng dụng
│   ├── icons/                      # Icon và biểu tượng
│   └── screenshots/                # Ảnh minh họa sản phẩm
│
├── README.md                       # Giới thiệu và hướng dẫn sử dụng dự án
├── CONTRIBUTING.md                 # Quy định đóng góp và làm việc nhóm
├── requirements.txt                # Danh sách thư viện Python cần cài
└── .gitignore                      # Những file Git không được theo dõi

```

## 4. Yêu cầu môi trường

- Python 3.13 (phiên bản đã sử dụng trong quá trình phát triển).
- Git.
- Visual Studio Code hoặc IDE Python tương đương.

SQLite được hỗ trợ thông qua thư viện `sqlite3` có sẵn trong Python.

## 5. Cài đặt dự án

Clone repository:

```bash
git clone https://github.com/kieen3011/ChuDe13.git
```

Di chuyển vào thư mục dự án:

```bash
cd ChuDe13
```

Kiểm tra Python:

```bash
python --version
```

**Lưu ý:** Cách khởi tạo cơ sở dữ liệu và chạy ứng dụng sẽ được bổ sung sau khi nhóm xác minh quy trình chạy chính thức.

## 6. Kiểm thử

Chạy bộ kiểm thử unittest:

```bash
python -m unittest discover -s tests -v
```

Kết quả kiểm thử cần được kiểm tra trước khi tích hợp thay đổi vào nhánh chính.

## 7. Quy tắc cộng tác

- Mỗi thành viên làm việc trên branch riêng.
- Không tự ý commit trực tiếp lên `main`.
- Commit cần có nội dung mô tả rõ thay đổi.
- Tạo Pull Request để đề xuất tích hợp code.
- Team Leader review và kiểm thử trước khi merge.

Chi tiết xem tại [CONTRIBUTING.md](CONTRIBUTING.md).

## 8. Nhóm phát triển

| Thành viên | Phụ trách |
|---|---|
| Kiên | Team Leader / Core Logic |
| Lợi | Backend CRUD / Net Balance |
| Lương | GUI / UI-UX |
| Lộc | VietQR / Export / Testing |
| Thục | Documentation / Report / Presentation |

## 9. Trạng thái dự án

Dự án đang trong quá trình phát triển và tích hợp các phần việc của nhóm.

---

**Repository:** https://github.com/kieen3011/ChuDe13
