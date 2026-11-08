# CONTRIBUTING — Quy định cộng tác

Tài liệu này quy định quy trình làm việc với Git và GitHub dành cho các thành viên dự án ChuDe13 — Group Expense Manager.

## 1. Nguyên tắc làm việc

1. Mỗi thành viên sử dụng tài khoản GitHub cá nhân.
2. Mỗi thành viên làm việc trên branch riêng, không phát triển trực tiếp trên `main`.
3. Không tự ý sửa hoặc xóa phần code do thành viên khác phụ trách nếu chưa trao đổi.
4. Mọi thay đổi cần được commit và push lên GitHub.
5. Muốn tích hợp code vào `main`, thành viên phải tạo Pull Request (PR).
6. Team Leader chịu trách nhiệm review, kiểm thử và quyết định merge.
7. Không đưa dữ liệu cá nhân, mật khẩu, API key hoặc file database thật lên GitHub.

## 2. Phân công branch

| Thành viên | Nhiệm vụ | Branch đề xuất |
|---|---|---|
| Kiên | Team Leader / Core Logic | `feature/core-logic` |
| Lợi | Backend CRUD / Net Balance | `feature/backend-crud` |
| Lương | GUI / UI-UX | `feature/gui` |
| Lộc | VietQR / Export / Testing | `feature/qr-export-testing` |
| Thục | Documentation / Report / Presentation | `docs/report-presentation` |

Các branch trên là tên đề xuất. Thành viên có thể tạo branch khi bắt đầu nhiệm vụ được giao.

## 3. Quy trình bắt đầu làm việc

### Bước 1: Clone repository

```bash
git clone https://github.com/kieen3011/ChuDe13.git
cd ChuDe13
```

### Bước 2: Cập nhật main

```bash
git switch main
git pull origin main
```

### Bước 3: Tạo branch riêng

Ví dụ thành viên Lợi:

```bash
git switch -c feature/backend-crud
```

Không tạo branch mới nếu branch tương ứng đã tồn tại trên máy.

## 4. Quy trình lưu và đẩy code

Sau khi hoàn thành một phần công việc:

### Kiểm tra thay đổi

```bash
git status
git diff
```

### Chạy kiểm thử phù hợp

```bash
python -m unittest discover -s tests -v
```

### Commit thay đổi

```bash
git add .
git commit -m "Describe your changes"
```

### Push branch lên GitHub

```bash
git push -u origin feature/backend-crud
```

Thay tên branch bằng branch của thành viên đang làm việc.

## 5. Quy trình Pull Request

Sau khi push branch:

1. Mở repository trên GitHub.
2. Chọn **Pull requests**.
3. Chọn **New pull request**.
4. Chọn:
   - Base: `main`
   - Compare: branch của thành viên.
5. Viết mô tả nội dung đã thay đổi.
6. Tạo Pull Request.
7. Chờ Team Leader review.

Không tự merge Pull Request vào `main` nếu chưa được Team Leader cho phép.

## 6. Quy tắc đặt tên commit

Ưu tiên các tiền tố sau:

| Prefix | Ý nghĩa | Ví dụ |
|---|---|---|
| `feat` | Thêm chức năng | `feat: add member CRUD` |
| `fix` | Sửa lỗi | `fix: correct expense split` |
| `test` | Thêm hoặc sửa kiểm thử | `test: add settlement tests` |
| `docs` | Cập nhật tài liệu | `docs: update database design` |
| `refactor` | Tái cấu trúc code | `refactor: improve expense service` |

Commit message cần ngắn gọn, mô tả đúng thay đổi.

## 7. Quy tắc xử lý xung đột

Nếu Git thông báo merge conflict:

1. Không xóa hoặc ghi đè code một cách tùy tiện.
2. Xác định file đang bị xung đột.
3. Trao đổi với thành viên phụ trách file đó.
4. Giải quyết xung đột và kiểm tra lại code.
5. Chạy các bài kiểm thử liên quan trước khi tiếp tục.

Nếu chưa hiểu cách giải quyết, hãy dừng lại và nhờ Team Leader hỗ trợ.

## 8. Quy tắc đối với database

- Không commit database SQLite chứa dữ liệu thử nghiệm hoặc dữ liệu thật.
- Không tự ý xóa database hoặc chạy lệnh xóa bảng.
- Không tự ý thay đổi schema mà chưa trao đổi với người phụ trách database.
- Mọi thay đổi cấu trúc database cần được cập nhật trong tài liệu thiết kế và migration tương ứng.

## 9. Trách nhiệm Team Leader

Team Leader chịu trách nhiệm:

- Phân chia và theo dõi nhiệm vụ.
- Review Pull Request.
- Kiểm tra tính tương thích giữa các module.
- Chạy kiểm thử trước khi merge.
- Quản lý nhánh `main`.
- Giải quyết xung đột khi tích hợp.

## 10. Nguyên tắc chung

**Không ưu tiên tốc độ hơn tính ổn định.**

Mọi thành viên cần đảm bảo code có thể đọc, kiểm tra và tích hợp được với phần còn lại của dự án.
