# ChuDe13 — Group Expense Manager

**Ứng dụng quản lý chi tiêu nhóm và chia sẻ hóa đơn**, được phát triển bằng Python và SQLite.

<p align="center">
  <strong>Python · SQLite · Git · GitHub</strong>
</p>

## 1. Giới thiệu dự án

**Group Expense Manager** là ứng dụng hỗ trợ các thành viên trong một nhóm quản lý chi tiêu chung, chia sẻ hóa đơn và theo dõi các khoản thanh toán giữa các thành viên.

Ứng dụng hướng đến việc giải quyết những vấn đề thường gặp khi nhiều người cùng chi trả cho một hoạt động, chẳng hạn như du lịch, ăn uống hoặc sinh hoạt tập thể.

Các mục tiêu chính:

- Quản lý nhóm và danh sách thành viên.
- Ghi nhận các khoản chi tiêu và người thanh toán.
- Chia hóa đơn theo nhiều phương thức.
- Tính toán số dư của từng thành viên.
- Tối ưu hóa các giao dịch hoàn tiền giữa các thành viên.
- Hỗ trợ theo dõi lịch sử và thống kê chi tiêu.

Đây là dự án bài tập lớn thuộc môn **Thiết kế Python — Chủ đề 13: Quản lý chi tiêu nhóm (Chia hóa đơn)**.

## 2. Công nghệ sử dụng

| Công nghệ | Vai trò |
|---|---|
| Python 3.13 | Ngôn ngữ lập trình chính |
| SQLite | Hệ quản trị cơ sở dữ liệu |
| `sqlite3` | Thư viện kết nối và thao tác với SQLite |
| Git | Quản lý phiên bản mã nguồn |
| GitHub | Lưu trữ mã nguồn và cộng tác nhóm |
| `unittest` | Kiểm thử các chức năng của ứng dụng |

Các thư viện giao diện và tích hợp bổ sung sẽ được lựa chọn, xác minh và cập nhật khi triển khai các module tương ứng.

## 3. Chức năng dự kiến

| Nhóm chức năng | Mô tả |
|---|---|
| Quản lý nhóm | Tạo và quản lý các nhóm chi tiêu |
| Quản lý thành viên | Thêm, sửa và xóa thành viên |
| Quản lý hóa đơn | Ghi nhận khoản chi, người thanh toán và nội dung chi tiêu |
| Chia hóa đơn | Chia đều, chia theo tỷ lệ phần trăm hoặc số tiền cố định |
| Tính toán số dư | Xác định số tiền mỗi thành viên cần trả hoặc được nhận |
| Tối ưu hóa nợ | Đề xuất các giao dịch hoàn tiền nhằm giảm số lượng giao dịch |
| Lịch sử giao dịch | Tra cứu và lọc các khoản chi tiêu |
| Thống kê | Tổng hợp tình hình chi tiêu của nhóm |
| VietQR | Hỗ trợ tạo mã QR chuyển khoản |
| Xuất báo cáo | Xuất dữ liệu chi tiêu và thanh toán ra CSV hoặc Excel |

**Lưu ý:** Bảng trên mô tả phạm vi chức năng mục tiêu của dự án, không đồng nghĩa tất cả chức năng đã hoàn thành.

## 4. Cấu trúc dự án

```text
GroupExpenseManager/
│
├── database/
│   └── group_expense.db
│
├── docs/
│   ├── architecture.md
│   ├── database_design.md
│   ├── data_dictionary.md
│   │
│   ├── gui_ux/
│   │   ├── user_flow/
│   │   ├── wireframes/
│   │   ├── screenshots/
│   │   ├── design_guidelines.md
│   │   └── README.md
│   │
│   ├── diagrams/
│   │   └── README.md
│   │
│   └── reports/
│       └── README.md
│
├── src/
│   ├── create_tables.py
│   ├── expense_service.py
│   ├── expense_split.py
│   ├── settlement_service.py
│   ├── main.py
│   │
│   ├── gui/
│   │   └── README.md
│   │
│   ├── integrations/
│   │   └── vietqr/
│   │       └── README.md
│   │
│   └── exports/
│       └── README.md
│
├── tests/
│   ├── test_expense_split.py
│   ├── test_expense_service.py
│   ├── test_settlement_workflow.py
│   │
│   ├── gui/
│   └── integrations/
│
├── assets/
│   ├── images/
│   ├── icons/
│   └── screenshots/
│
├── README.md
├── CONTRIBUTING.md
├── requirements.txt
└── .gitignore
```

### Mô tả các thư mục chính

| Thư mục | Chức năng |
|---|---|
| `database/` | Lưu trữ cơ sở dữ liệu SQLite cục bộ |
| `docs/` | Tài liệu kiến trúc, thiết kế và báo cáo dự án |
| `src/` | Chứa mã nguồn chính của ứng dụng |
| `tests/` | Chứa các bộ kiểm thử |
| `assets/` | Lưu trữ hình ảnh, biểu tượng và tài nguyên giao diện |

**Lưu ý:** Cấu trúc trên là cấu trúc tổ chức dự án mục tiêu. Các thư mục và module sẽ được bổ sung theo tiến độ triển khai thực tế.

## 5. Yêu cầu môi trường

- Python 3.13.
- Git.
- Visual Studio Code hoặc IDE Python tương đương.

SQLite được tích hợp thông qua thư viện `sqlite3` có sẵn trong Python, không cần cài đặt hệ quản trị cơ sở dữ liệu riêng.

## 6. Cài đặt dự án

### Bước 1: Clone repository

```bash
git clone https://github.com/kieen3011/ChuDe13.git
```

### Bước 2: Di chuyển vào thư mục dự án

```bash
cd ChuDe13
```

### Bước 3: Kiểm tra phiên bản Python

```bash
python --version
```

### Bước 4: Cài đặt các thư viện cần thiết

```bash
pip install -r requirements.txt
```

**Lưu ý:** Quy trình khởi tạo cơ sở dữ liệu và chạy ứng dụng chính thức sẽ được cập nhật sau khi nhóm xác minh đầy đủ các bước thiết lập.

## 7. Kiểm thử

Dự án sử dụng thư viện `unittest` để kiểm thử các chức năng.

Chạy toàn bộ bộ kiểm thử bằng lệnh:

```bash
python -m unittest discover -s tests -v
```

Kết quả kiểm thử cần được kiểm tra trước khi tích hợp thay đổi vào nhánh chính.

## 8. Phân công nhiệm vụ nhóm

Dự án được thực hiện bởi 5 thành viên. Mỗi thành viên đều trực tiếp tham gia phát triển sản phẩm kỹ thuật theo nhiệm vụ được phân công.

| Thành viên | Vai trò | Nhiệm vụ chính |
|---|---|---|
| **Kiên** | Team Leader & Core Logic Lead | Thiết kế CSDL SQLite, thuật toán tối ưu hóa nợ, xử lý chia tiền theo tỷ lệ và số tiền cố định, quản lý Git và tích hợp code |
| **Lợi** | Backend Developer | Phát triển CRUD nhóm, thành viên, hóa đơn; tính toán số dư và xử lý làm tròn tiền |
| **Lương** | UI/UX Developer | Xây dựng giao diện, Dashboard, biểu mẫu nhập hóa đơn và màn hình kết quả; tích hợp UI với Backend |
| **Lộc** | Feature & Data Developer | Phát triển VietQR, xuất báo cáo CSV/Excel, tạo dữ liệu mẫu và kiểm thử các tính năng mở rộng |
| **Thục** | Module Developer & Documentation Lead | Phát triển Validation, lịch sử giao dịch, tìm kiếm, thống kê; biên soạn báo cáo Word và thuyết minh khi demo |

### Phân công tài liệu và báo cáo

Thành viên Thục phụ trách tổng hợp báo cáo Word, bao gồm:

- Giới thiệu và mục tiêu dự án.
- Phân tích yêu cầu và nghiệp vụ.
- Thiết kế cơ sở dữ liệu.
- Giải thích thuật toán xử lý và chia hóa đơn.
- Hướng dẫn sử dụng phần mềm.
- Hình ảnh minh họa các chức năng đã triển khai.

Các thành viên còn lại có trách nhiệm cung cấp hình ảnh giao diện, kết quả kiểm thử và mô tả chức năng thuộc phần việc của mình.

## 9. Lộ trình triển khai

Dự án dự kiến được triển khai trong 4 tuần.

| Thời gian | Công việc trọng tâm | Thành viên phụ trách |
|---|---|---|
| **Tuần 1** | Phân tích nghiệp vụ, chốt thiết kế CSDL, phác thảo Wireframe và lập đề cương báo cáo | Cả 5 thành viên |
| **Tuần 2** | Phát triển Backend CRUD, thuật toán tối ưu hóa nợ, Validation, lọc dữ liệu và giao diện cơ bản | Kiên, Lợi, Lương, Thục |
| **Tuần 3** | Tích hợp giao diện với Backend, phát triển VietQR, xuất CSV, tạo dữ liệu mẫu và bắt đầu hoàn thiện báo cáo | Kiên, Lương, Lộc, Thục |
| **Tuần 4** | Kiểm thử tổng thể, sửa lỗi, hoàn thiện báo cáo Word và chuẩn bị kịch bản demo | Cả 5 thành viên |

## 10. Quy tắc cộng tác

Để đảm bảo quá trình phát triển thống nhất và hạn chế xung đột mã nguồn, nhóm áp dụng các quy tắc sau:

### 10.1. Quy tắc Git và GitHub

- Mỗi thành viên làm việc trên branch riêng.
- Không tự ý commit trực tiếp lên branch `main`.
- Commit cần có nội dung mô tả rõ ràng.
- Tạo Pull Request để đề xuất tích hợp code.
- Team Leader chịu trách nhiệm review và kiểm thử trước khi merge vào nhánh chính.

### 10.2. Quy tắc tích hợp

- Các module cần tuân thủ cấu trúc và giao diện kết nối đã thống nhất.
- Thành viên cần thông báo khi thay đổi hàm, tham số hoặc cấu trúc dữ liệu có ảnh hưởng đến module khác.
- Không tự ý ghi đè code của thành viên khác.
- Các thay đổi cần được kiểm thử trước khi tích hợp.

### 10.3. Quy tắc báo cáo

- Sau khi hoàn thành chức năng, thành viên gửi ảnh chụp màn hình và mô tả ngắn cho thành viên Thục.
- Hình ảnh đưa vào báo cáo cần phản ánh đúng phiên bản phần mềm đã triển khai.
- Các chức năng chưa hoàn thiện phải được ghi nhận đúng trạng thái.

### 10.4. Deadline nội bộ

Nhóm đặt mục tiêu hoàn thành phần lập trình trước ngày bảo vệ ít nhất 3 ngày để có thời gian kiểm thử chéo, sửa lỗi và hoàn thiện báo cáo.

## 11. Trạng thái dự án

Dự án đang trong quá trình phát triển và tích hợp các module.

Các chức năng sẽ được cập nhật theo tiến độ thực tế. Những nội dung chưa triển khai hoặc chưa vượt qua kiểm thử sẽ không được xem là đã hoàn thành.

---

## 12. Thông tin repository

**Repository:** [ChuDe13 — Group Expense Manager](https://github.com/kieen3011/ChuDe13)

**Môn học:** Thiết kế Python

**Chủ đề:** 13 — Quản lý chi tiêu nhóm (Chia hóa đơn)

**Ngôn ngữ:** Python

**Cơ sở dữ liệu:** SQLite

**Nhóm phát triển:** 5 thành viên
