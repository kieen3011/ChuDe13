# CONTRIBUTING — Quy định cộng tác

Tài liệu này quy định quy trình làm việc, quản lý mã nguồn và phối hợp phát triển dành cho các thành viên dự án **ChuDe13 — Group Expense Manager**.

Mục tiêu là đảm bảo các thành viên có thể phát triển độc lập từng module, hạn chế xung đột mã nguồn và tích hợp các chức năng thành một sản phẩm thống nhất.

---

## 1. Nguyên tắc làm việc

Tất cả thành viên cần tuân thủ các nguyên tắc sau:

1. Mỗi thành viên sử dụng tài khoản GitHub cá nhân để tham gia dự án.
2. Không phát triển trực tiếp trên branch `main`.
3. Mỗi thành viên làm việc trên branch riêng hoặc branch được phân công cho từng nhiệm vụ.
4. Không tự ý sửa, xóa hoặc ghi đè code do thành viên khác phụ trách khi chưa trao đổi.
5. Mọi thay đổi cần được kiểm tra, commit và push lên GitHub.
6. Muốn tích hợp code vào `main`, thành viên phải tạo Pull Request (PR).
7. Team Leader chịu trách nhiệm review, kiểm thử và quyết định merge Pull Request.
8. Không đưa mật khẩu, API key, thông tin xác thực, dữ liệu cá nhân hoặc database chứa dữ liệu thật lên GitHub.
9. Khi thay đổi ảnh hưởng đến module khác, cần thông báo cho thành viên phụ trách module liên quan.
10. Ưu tiên tính ổn định, khả năng bảo trì và tính tương thích của toàn bộ hệ thống.

---

## 2. Phân công thành viên và branch

| Thành viên | Vai trò | Branch đề xuất |
|---|---|---|
| Kiên | Team Leader / Core Logic | `feature/core-logic` |
| Lợi | Backend CRUD / Net Balance | `feature/backend-crud` |
| Lương | GUI / UI-UX | `feature/gui` |
| Lộc | VietQR / Export / Testing | `feature/qr-export-testing` |
| Thục | Documentation / Report / Presentation | `docs/report-presentation` |

Các branch trên là tên đề xuất ban đầu. Team Leader có trách nhiệm thống nhất tên branch và phạm vi công việc trước khi triển khai.

### Quy tắc đặt tên branch

Khuyến khích sử dụng các tiền tố:

| Prefix | Mục đích | Ví dụ |
|---|---|---|
| `feature/` | Phát triển chức năng mới | `feature/member-management` |
| `fix/` | Sửa lỗi | `fix/expense-rounding` |
| `test/` | Bổ sung hoặc sửa kiểm thử | `test/settlement-workflow` |
| `docs/` | Cập nhật tài liệu | `docs/update-readme` |
| `refactor/` | Tái cấu trúc mã nguồn | `refactor/expense-service` |

Nếu một thành viên thực hiện nhiều nhiệm vụ khác nhau, nên tạo branch riêng cho từng nhiệm vụ thay vì đưa tất cả thay đổi vào một branch dài hạn.

---

## 3. Quy trình bắt đầu làm việc

### Bước 1: Clone repository

Nếu chưa có source code trên máy:

```bash
git clone https://github.com/kieen3011/ChuDe13.git
cd ChuDe13
```

### Bước 2: Kiểm tra trạng thái repository

```bash
git status
```

Đảm bảo các thay đổi cục bộ đã được lưu hoặc xử lý trước khi chuyển branch.

### Bước 3: Cập nhật branch main

```bash
git switch main
git pull origin main
```

### Bước 4: Tạo branch riêng

Ví dụ thành viên Lợi phát triển chức năng Backend CRUD:

```bash
git switch -c feature/backend-crud
```

Nếu branch đã tồn tại trên GitHub:

```bash
git fetch origin
git switch --track origin/feature/backend-crud
```

Không tạo branch mới nếu branch tương ứng đã tồn tại và đang được sử dụng.

### Bước 5: Kiểm tra branch đang làm việc

```bash
git branch
```

Branch có dấu `*` là branch hiện tại.

---

## 4. Quy trình lưu và đẩy code

Sau khi hoàn thành một phần công việc, thành viên thực hiện các bước sau.

### Bước 1: Kiểm tra thay đổi

```bash
git status
```

Xem nội dung thay đổi:

```bash
git diff
```

### Bước 2: Chạy kiểm thử

Chạy các bài kiểm thử phù hợp với chức năng vừa thay đổi:

```bash
python -m unittest discover -s tests -v
```

Nếu thay đổi chỉ liên quan đến một module, có thể chạy bộ kiểm thử tương ứng trước.

### Bước 3: Đưa file cần thiết vào staging

Không nên sử dụng `git add .` một cách tùy tiện.

Ưu tiên thêm chính xác các file đã thay đổi:

```bash
git add src/expense_split.py
```

Hoặc:

```bash
git add tests/test_expense_split.py
```

Kiểm tra lại những file sắp commit:

```bash
git status
git diff --cached
```

### Bước 4: Commit thay đổi

```bash
git commit -m "feat: add member management"
```

Commit message cần mô tả chính xác nội dung thay đổi.

### Bước 5: Push branch lên GitHub

```bash
git push -u origin feature/backend-crud
```

Thay tên branch bằng branch thực tế đang sử dụng.

Đối với những lần push tiếp theo:

```bash
git push
```

---

## 5. Quy trình Pull Request

Sau khi hoàn thành công việc và push branch lên GitHub, thành viên tạo Pull Request để đề xuất tích hợp code vào branch `main`.

### Các bước tạo Pull Request

1. Truy cập repository: https://github.com/kieen3011/ChuDe13
2. Mở mục **Pull requests**.
3. Chọn **New pull request**.
4. Chọn branch đích và branch nguồn:
   - Base: `main`
   - Compare: branch của thành viên.
5. Viết tiêu đề và mô tả Pull Request.
6. Kiểm tra danh sách file thay đổi.
7. Chọn **Create pull request**.
8. Chờ Team Leader review.

### Nội dung Pull Request cần có

Mỗi Pull Request nên trình bày:

- **Mục đích:** Lý do thực hiện thay đổi.
- **Nội dung:** Những chức năng hoặc file đã được thay đổi.
- **Kiểm thử:** Các bài kiểm thử đã thực hiện và kết quả.
- **Ảnh minh họa:** Bổ sung nếu có thay đổi giao diện.
- **Ảnh hưởng:** Các module khác có bị ảnh hưởng hay không.

### Điều kiện để được merge

Pull Request chỉ nên được merge khi:

1. Nội dung thay đổi đúng với nhiệm vụ được giao.
2. Không chứa file database, mật khẩu hoặc thông tin nhạy cảm.
3. Code không gây ảnh hưởng ngoài phạm vi được phép.
4. Các bài kiểm thử liên quan đã được thực hiện.
5. Không còn merge conflict chưa được xử lý.
6. Team Leader đã review và chấp thuận.

Không tự ý merge Pull Request vào `main` khi chưa được Team Leader cho phép.

---

## 6. Quy tắc đặt tên commit

Nhóm sử dụng quy ước commit message theo dạng:

```text
<prefix>: <mô tả ngắn gọn>
```

| Prefix | Ý nghĩa | Ví dụ |
|---|---|---|
| `feat` | Thêm chức năng | `feat: add member CRUD` |
| `fix` | Sửa lỗi | `fix: correct expense split` |
| `test` | Thêm hoặc sửa kiểm thử | `test: add settlement tests` |
| `docs` | Cập nhật tài liệu | `docs: update database design` |
| `refactor` | Tái cấu trúc code | `refactor: improve expense service` |
| `style` | Điều chỉnh định dạng code | `style: format Python modules` |
| `chore` | Công việc bảo trì | `chore: update requirements` |

### Ví dụ commit hợp lệ

```bash
git commit -m "feat: implement percentage split"
```

```bash
git commit -m "fix: handle rounding remainder"
```

```bash
git commit -m "test: add invalid input cases"
```

Commit message cần ngắn gọn, rõ nghĩa và phản ánh đúng nội dung đã thay đổi.

---

## 7. Quy tắc xử lý xung đột mã nguồn

Merge conflict có thể xảy ra khi nhiều thành viên cùng chỉnh sửa một file hoặc khi branch cá nhân chưa được cập nhật theo `main`.

Khi gặp xung đột, thực hiện theo quy trình:

1. Xác định branch và file đang xảy ra xung đột.
2. Kiểm tra nội dung thay đổi của các bên.
3. Trao đổi với thành viên phụ trách file liên quan.
4. Thống nhất phần code cần giữ lại hoặc kết hợp.
5. Giải quyết conflict và kiểm tra lại nội dung.
6. Chạy các bài kiểm thử liên quan.
7. Commit kết quả giải quyết conflict và tiếp tục quy trình Pull Request.

Không tự ý xóa toàn bộ nội dung của một bên để giải quyết conflict.

Nếu chưa hiểu nguyên nhân hoặc không chắc chắn cách xử lý, cần dừng lại và nhờ Team Leader hỗ trợ.

---

## 8. Quy định đối với cơ sở dữ liệu

Cơ sở dữ liệu là thành phần quan trọng của hệ thống. Mọi thay đổi liên quan đến database cần được kiểm soát.

### Nguyên tắc chung

- Không commit database SQLite chứa dữ liệu thử nghiệm hoặc dữ liệu thật lên GitHub.
- Không tự ý xóa database hoặc chạy lệnh xóa bảng.
- Không tự ý thay đổi schema khi chưa trao đổi với người phụ trách database.
- Không ghi đè database của thành viên khác.
- Không đưa dữ liệu cá nhân hoặc thông tin nhạy cảm vào dữ liệu mẫu công khai.

### Khi cần thay đổi cấu trúc database

Thành viên cần:

1. Trao đổi với người phụ trách database.
2. Mô tả các bảng, trường hoặc quan hệ cần thay đổi.
3. Đánh giá ảnh hưởng đến các module đang sử dụng database.
4. Cập nhật tài liệu thiết kế cơ sở dữ liệu.
5. Chuẩn bị phương án cập nhật schema an toàn.
6. Kiểm thử trên database riêng trước khi tích hợp.

Không thực hiện thay đổi trực tiếp trên database dùng chung nếu chưa có sự thống nhất của nhóm.

---

## 9. Quy tắc phối hợp giữa các module

Do dự án được phát triển bởi nhiều thành viên, các module cần thống nhất cách giao tiếp và trao đổi dữ liệu.

### Nguyên tắc phối hợp

- Thống nhất tên hàm, tham số và kiểu dữ liệu trước khi tích hợp.
- Không tự ý thay đổi giao diện hàm đang được module khác sử dụng.
- Thông báo trước khi thay đổi cấu trúc database hoặc dữ liệu trả về.
- Ưu tiên tái sử dụng các hàm nghiệp vụ thay vì viết lại logic trùng lặp.
- Kiểm thử chức năng độc lập trước khi tích hợp với module khác.

### Phân công phối hợp

| Module | Người phụ trách chính | Thành viên phối hợp |
|---|---|---|
| Core Logic và Database | Kiên | Lợi |
| Backend CRUD và Net Balance | Lợi | Kiên, Thục |
| GUI / UI-UX | Lương | Kiên, Lợi, Thục |
| VietQR và Export | Lộc | Kiên, Lợi |
| Validation, History và Statistics | Thục | Lợi, Lương |
| Tích hợp và kiểm thử tổng thể | Kiên | Cả 5 thành viên |

---

## 10. Trách nhiệm Team Leader

Team Leader chịu trách nhiệm điều phối và kiểm soát quá trình tích hợp mã nguồn.

Các nhiệm vụ chính:

- Phân công và theo dõi tiến độ công việc.
- Thống nhất cấu trúc dự án và quy ước lập trình.
- Kiểm tra khả năng tương thích giữa các module.
- Review Pull Request.
- Kiểm tra kết quả kiểm thử trước khi merge.
- Quản lý branch `main`.
- Điều phối xử lý merge conflict.
- Theo dõi các thay đổi ảnh hưởng đến cơ sở dữ liệu.
- Đảm bảo mã nguồn tích hợp không làm hỏng các chức năng đã có.

Việc merge cần dựa trên kết quả review và kiểm thử, không chỉ dựa trên việc thành viên đã hoàn thành nhiệm vụ.

---

## 11. Quy định bảo mật và bảo vệ dữ liệu

Tất cả thành viên phải tuân thủ các quy định sau:

1. Không commit mật khẩu, API key hoặc token truy cập.
2. Không đưa file `.env` chứa thông tin nhạy cảm lên GitHub.
3. Không đưa database có dữ liệu cá nhân hoặc dữ liệu thật lên repository.
4. Không tự ý chia sẻ thông tin truy cập repository cho người không thuộc nhóm.
5. Kiểm tra file trước khi commit và push.
6. Nếu phát hiện thông tin nhạy cảm đã bị push, cần thông báo ngay cho Team Leader để xử lý.

Các file và thư mục không cần thiết cần được khai báo trong `.gitignore`.

---

## 12. Checklist trước khi tạo Pull Request

Mỗi thành viên nên kiểm tra các nội dung sau trước khi gửi PR:

- [ ] Đang làm việc trên đúng branch.
- [ ] Code nằm trong phạm vi nhiệm vụ được giao.
- [ ] Không sửa hoặc ghi đè code của thành viên khác ngoài phạm vi thống nhất.
- [ ] Đã kiểm tra `git status` và `git diff`.
- [ ] Đã kiểm tra các file được đưa vào commit.
- [ ] Đã chạy các bài kiểm thử liên quan.
- [ ] Không đưa database hoặc thông tin nhạy cảm lên GitHub.
- [ ] Commit message rõ ràng.
- [ ] Đã push branch lên GitHub.
- [ ] Pull Request có mô tả đầy đủ.

---

## 13. Nguyên tắc chung

**Không ưu tiên tốc độ hơn tính ổn định và tính đúng đắn của hệ thống.**

Mọi thành viên cần chủ động trao đổi, tuân thủ phạm vi công việc và đảm bảo code có thể đọc, kiểm thử, bảo trì và tích hợp với các module còn lại.

Mọi thay đổi quan trọng liên quan đến kiến trúc, database hoặc giao diện kết nối giữa các module cần được thống nhất trước khi triển khai.

---

**Project:** ChuDe13 — Group Expense Manager  
**Repository:** https://github.com/kieen3011/ChuDe13  
**Team size:** 5 members  
**Language:** Python  
**Database:** SQLite
