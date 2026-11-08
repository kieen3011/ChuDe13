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
ChuDe13/
├── database/
│   └── (SQLite database - không đưa lên GitHub)
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   └── database_design.md
├── src/
│   ├── create_tables.py
│   ├── expense_service.py
│   ├── expense_split.py
│   ├── main.py
│   ├── migrate_add_dispute_resolution.py
│   ├── migrate_add_group_leader.py
│   └── settlement_service.py
├── tests/
│   ├── database_test.py
│   ├── test_debt_simplification.py
│   ├── test_expense_service.py
│   ├── test_expense_service_errors.py
│   ├── test_expense_split.py
│   ├── test_expense_split_integration.py
│   ├── test_net_balance.py
│   └── test_settlement_workflow.py
├── .gitignore
├── CONTRIBUTING.md
└── README.md
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
