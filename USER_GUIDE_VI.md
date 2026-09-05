# VĂN UYỂN — Hướng dẫn sử dụng

Tài liệu này hướng dẫn giáo viên và học sinh sử dụng hệ thống VĂN UYỂN từ lúc mở ứng dụng, quản lý lớp, soạn bài, giao bài, làm bài, chấm bài đến xử lý các tình huống thường gặp.

## 1. Tổng quan hệ thống

VĂN UYỂN có hai vai trò:

- **Giáo viên:** quản lý lớp và học sinh, đăng bài kiến thức, tạo đề luyện tập/thi thử, giao đề, xem bài nộp và chấm bài.
- **Học sinh:** đọc kiến thức, làm bài luyện tập, thi thử, xem lịch sử và kết quả, đổi mật khẩu.

Hệ thống có hai chế độ dữ liệu:

1. **Chế độ backend:** tài khoản và dữ liệu được lưu trong PostgreSQL, phù hợp khi chạy thật nhiều người dùng.
2. **Chế độ LocalStorage:** dữ liệu nằm trong trình duyệt, phù hợp xem giao diện hoặc chạy offline. Dữ liệu trên máy này không tự đồng bộ sang máy khác.

Khi chạy bằng Docker, hệ thống mặc định dùng backend.

## 2. Mở hệ thống

### 2.1. Chạy bằng Docker

Từ thư mục dự án:

```sh
cp .env.example .env
docker compose up --build
```

Mở:

- Frontend: <http://localhost:3000>
- Backend health: <http://localhost:8000/health/live>

Để dừng hệ thống:

```sh
docker compose down
```

### 2.2. Chạy frontend riêng

```sh
cd frontend
npm ci
npm run dev
```

Muốn frontend gọi backend thật:

```sh
NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1 npm run dev
```

Nếu không đặt biến này, frontend dùng LocalStorage.

## 3. Đăng nhập và tài khoản

### 3.1. Giáo viên

Tài khoản giáo viên backend được tạo bởi quản trị viên bằng lệnh seed:

```sh
docker compose exec backend python -m app.cli.seed_teacher \
  --username teacher@example.com \
  --full-name "Tên giáo viên" \
  --school-name "Tên trường"
```

Lệnh sẽ hỏi mật khẩu. Có thể truyền trước khi chạy:

```sh
SEED_TEACHER_PASSWORD='MatKhauAnToan' docker compose exec backend \
  python -m app.cli.seed_teacher \
  --username teacher@example.com \
  --full-name "Tên giáo viên"
```

Tài khoản demo LocalStorage:

- Tên đăng nhập: `hathanhhangc2yenphong@bacninh.edu.vn`
- Mật khẩu: `Thanhhang97@`

Trong backend, tài khoản đã tồn tại sẽ không bị ghi đè.

### 3.2. Học sinh

Học sinh có hai cách được tạo:

- Giáo viên tạo tài khoản và gán vào một lớp.
- Học sinh tự đăng ký tài khoản tự do ở màn hình **Đăng ký tài khoản tự do**.

Tài khoản tự đăng ký không thuộc lớp nào. Học sinh tự do vẫn có thể đọc nội dung và làm các đề mở, nhưng không nhận được đề giao theo lớp cho đến khi giáo viên tạo/gán tài khoản vào lớp.

### 3.3. Đăng xuất và đổi mật khẩu

- Bấm tên tài khoản ở góc giao diện để mở menu tài khoản.
- Chọn **Đăng xuất** khi dùng xong, đặc biệt trên máy dùng chung.
- Chọn **Đổi Mật Khẩu**, nhập mật khẩu cũ và mật khẩu mới.
- Mật khẩu backend phải dài tối thiểu 8 ký tự và tối đa 72 byte UTF-8.

Khi đổi hoặc đặt lại mật khẩu ở backend, các phiên đăng nhập cũ của tài khoản đó bị thu hồi.

## 4. Các khu vực chính

Sau khi đăng nhập, menu bên trái gồm:

- **Trang chủ:** màn hình tổng quan.
- **Góc kiến thức:** bài giảng và tài liệu Ngữ văn.
- **Góc luyện tập:** đề luyện tập theo dạng bài.
- **Góc thi thử:** đề thi thử có thời gian giới hạn.
- **Góc học tập:** lịch sử và các đề được giao dành cho học sinh.
- **Góc quản lý:** chỉ giáo viên nhìn thấy.

Trên điện thoại, bấm **Mở menu** để hiện thanh điều hướng.

## 5. Hướng dẫn cho giáo viên

### 5.1. Tạo lớp học

1. Vào **Góc quản lý**.
2. Trong khung **Tạo lớp học**, nhập tên lớp.
3. Nhập năm học nếu trường sử dụng trường này.
4. Bấm nút tạo lớp.
5. Kiểm tra lớp đã xuất hiện trong bộ lọc danh sách học sinh.

Giáo viên chỉ nhìn thấy và quản lý các lớp do mình tạo.

### 5.2. Tạo tài khoản học sinh

1. Trong **Góc quản lý**, mở khung **Thêm học sinh**.
2. Nhập tên đăng nhập.
3. Nhập mật khẩu ban đầu.
4. Nhập họ tên đầy đủ.
5. Chọn lớp.
6. Nhập trường nếu cần.
7. Bấm nút tạo tài khoản.

Tên đăng nhập phải là duy nhất. Nên bàn giao mật khẩu ban đầu cho học sinh qua kênh riêng và yêu cầu học sinh đổi mật khẩu sau lần đăng nhập đầu tiên.

### 5.3. Quản lý học sinh

Trong bảng **Danh sách học sinh**, có thể:

- Lọc theo lớp.
- **Chuyển lớp:** chọn lớp đích rồi lưu. Giáo viên phải sở hữu cả lớp hiện tại và lớp đích.
- **Đặt lại mật khẩu:** nhập mật khẩu mới cho học sinh.
- **Khóa tài khoản:** học sinh không thể đăng nhập khi bị khóa.
- **Mở khóa tài khoản:** cho phép đăng nhập lại.
- **Xem bài làm:** xem lịch sử, mở bài và chấm bài.
- **Xóa tài khoản:** xóa tài khoản và các bài làm liên quan sau khi xác nhận.

Các thao tác chuyển lớp, đặt lại mật khẩu, khóa/mở khóa và xóa chỉ áp dụng trong phạm vi học sinh thuộc lớp do giáo viên quản lý.

### 5.4. Đăng bài kiến thức

1. Vào **Góc kiến thức**.
2. Chọn nhóm lớn và nhóm nhỏ ở hai hàng phân loại.
3. Bấm **＋ Đăng bài viết**.
4. Nhập tiêu đề.
5. Chọn định dạng/nội dung và nhập phần nội dung.
6. Nhập mô tả, biểu tượng và phân loại nếu cần.
7. Bấm lưu.

Với bài đã đăng, giáo viên có thể mở menu trên thẻ bài để **Sửa bài** hoặc **Xóa bài**. Nội dung HTML hiển thị trong trình đọc được làm sạch trước khi hiển thị.

### 5.5. Tạo đề luyện tập

1. Vào **Góc luyện tập**.
2. Chọn dạng bài phù hợp: đọc hiểu, viết đoạn, viết bài hoặc nhóm tương ứng.
3. Bấm **＋ Thêm đề mới**.
4. Nhập tên đề.
5. Chọn thể loại và loại bài luyện tập.
6. Nhập ngữ liệu hoặc đề bài.
7. Nhập câu hỏi và đáp án/hướng dẫn chấm cho từng câu.
8. Bấm **Lưu Đề**.

Khi đổi loại bài sau khi đã nhập câu hỏi, hệ thống hỏi xác nhận vì câu hỏi và đáp án sẽ được tạo lại.

### 5.6. Tạo đề thi thử

1. Vào **Góc thi thử**.
2. Bấm **＋ Thêm đề mới**.
3. Nhập tên đề và ngữ liệu đọc hiểu.
4. Nhập đủ 7 câu hỏi.
5. Nhập đáp án chuẩn/hướng dẫn chấm cho từng câu.
6. Bấm **Lưu Đề**.

Đề thi thử có thời lượng 120 phút. Khi hết giờ, bài được tự động nộp.

### 5.7. Sửa hoặc xóa đề

1. Trên thẻ đề, bấm nút **⋯ Thao tác đề**.
2. Chọn **Sửa đề** hoặc **Xóa đề**.
3. Khi xóa, xác nhận trong hộp thoại.

Đề đã có bài được giao hoặc đã có bài nộp có thể bị từ chối xóa để bảo toàn dữ liệu lịch sử. Khi đó cần giữ đề hoặc xử lý dữ liệu theo quy trình quản trị riêng.

### 5.8. Giao đề cho lớp

1. Mở menu **⋯ Thao tác đề** trên đề cần giao.
2. Chọn **Giao đề**.
3. Chọn lớp.
4. Bấm **Giao Đề ✅**.

Nếu chưa có lớp, hệ thống yêu cầu tạo lớp trước. Học sinh thuộc lớp sẽ nhìn thấy đề trong thông báo và **Góc học tập**.

### 5.9. Xem và chấm bài

Có hai cách mở bài:

- Trong thẻ đề, khi có bài chờ chấm, bấm **Chấm ngay**.
- Vào **Góc quản lý**, chọn học sinh rồi mở lịch sử bài làm.

Trong màn hình bài làm:

1. Đọc đáp án của học sinh.
2. Chấm từng câu theo thang điểm của đề.
3. Nhập nhận xét nếu cần.
4. Lưu kết quả.

Bài đã nộp được giữ snapshot của đề tại thời điểm làm bài, giúp xem lại ngay cả khi đề gốc được sửa sau đó.

### 5.10. Theo dõi chống gian lận

Trong lúc học sinh làm bài, hệ thống theo dõi một số sự kiện như chuyển tab/rời trang. Giáo viên xem các thông tin này cùng bài nộp nếu backend đã bật chức năng anti-cheat.

Các sự kiện này là dữ liệu hỗ trợ đánh giá; giáo viên vẫn cần xem toàn bộ bài và bối cảnh trước khi kết luận.

## 6. Hướng dẫn cho học sinh

### 6.1. Đăng nhập hoặc đăng ký

1. Mở trang đăng nhập.
2. Nhập tên đăng nhập và mật khẩu.
3. Bấm **Đăng nhập hệ thống**.

Nếu chưa có tài khoản, bấm **Đăng ký tài khoản tự do**, nhập tên đăng nhập, mật khẩu, họ tên rồi bấm **Tạo tài khoản**.

Sau khi đăng ký thành công, hệ thống tự đăng nhập và đưa tới trang chính.

### 6.2. Đọc kiến thức

1. Vào **Góc kiến thức**.
2. Chọn nhóm lớn và nhóm nhỏ.
3. Bấm vào thẻ bài muốn đọc.
4. Đọc nội dung trong cửa sổ trình đọc.
5. Bấm **Đóng** để quay lại danh sách.

### 6.3. Làm bài luyện tập

1. Vào **Góc luyện tập**.
2. Chọn dạng bài.
3. Bấm **Làm bài ngay →**.
4. Đọc ngữ liệu và nhập câu trả lời.
5. Theo dõi đồng hồ nếu đề có giới hạn thời gian.
6. Nộp bài theo hướng dẫn.
7. Thực hiện bước tự chấm nếu đề yêu cầu.

Đề luyện tập có thể cho phép tiếp tục khi hết giờ tùy loại bài. Đóng cửa sổ khi chưa nộp sẽ hỏi xác nhận; nội dung chưa nộp không được đảm bảo lưu tự động.

### 6.4. Thi thử

1. Vào **Góc thi thử**.
2. Chọn đề.
3. Bấm **Thi Ngay ⚑**.
4. Nhập đủ 7 câu trả lời.
5. Không đóng cửa sổ hoặc chuyển sang tab khác nếu không cần thiết.
6. Bài tự nộp khi hết 120 phút hoặc nộp theo nút trong màn hình làm bài.

Nếu trình duyệt phát hiện chuyển tab/rời trang, sự kiện có thể được ghi lại để giáo viên xem.

### 6.5. Xem bài đã làm

Có thể xem lịch sử theo hai cách:

- Trên thẻ đề, mở mục **Lịch sử làm bài**.
- Vào **Góc học tập** để xem các bài đã giao, trạng thái và kết quả.

Trạng thái thường gặp:

- **Đang chờ chấm:** đã nộp nhưng giáo viên chưa chấm.
- **Đã chấm:** đã có điểm/nhận xét.
- Có thể làm lại đề nếu giáo viên cho phép hoặc giao diện hiển thị nút làm lại.

### 6.6. Đổi mật khẩu

1. Bấm tên tài khoản.
2. Chọn phần đổi mật khẩu.
3. Nhập mật khẩu cũ.
4. Nhập mật khẩu mới.
5. Bấm **Đổi Mật Khẩu**.

Nếu giáo viên đặt lại mật khẩu, dùng mật khẩu mới được cung cấp để đăng nhập rồi đổi lại ngay.

## 7. Lỗi thường gặp và cách xử lý

### Không đăng nhập được

- Kiểm tra đúng tên đăng nhập và mật khẩu.
- Kiểm tra tài khoản có bị giáo viên khóa không.
- Nếu chạy backend, kiểm tra container `backend` và `postgres` đang healthy.
- Nếu phiên hết hạn, đăng nhập lại.

### Không thấy lớp hoặc đề được giao

- Học sinh phải thuộc đúng lớp được giao.
- Giáo viên kiểm tra đề đã giao đúng lớp chưa.
- Làm mới trang sau khi giáo viên giao đề.
- Nếu dùng LocalStorage, dữ liệu chỉ có trên đúng trình duyệt/profile đã tạo dữ liệu.

### Không lưu được bài hoặc đề

- Kiểm tra đã nhập đủ trường bắt buộc.
- Kiểm tra đề có đúng số câu và tổng điểm theo loại bài không.
- Kiểm tra backend còn hoạt động.
- Không mở nhiều thao tác lưu cùng lúc.

### Backend không khởi động

```sh
docker compose ps
docker compose logs backend
docker compose logs postgres
```

Nếu database chưa sẵn sàng, chờ PostgreSQL healthy rồi khởi động lại backend.

### Lỗi dữ liệu trình duyệt

Nếu hệ thống báo dữ liệu hỏng:

1. Không xóa LocalStorage ngay.
2. Bấm **Tải bản sao dữ liệu gốc** để giữ lại dữ liệu.
3. Thử **Thử lại**.
4. Nếu vẫn lỗi, gửi file sao lưu cho người quản trị.

Không tự sửa JSON trong LocalStorage nếu chưa có bản sao.

### Không thấy nút quản lý

Nút **Góc quản lý** chỉ hiển thị với tài khoản có vai trò giáo viên. Học sinh cần đăng xuất và đăng nhập lại bằng đúng tài khoản giáo viên nếu đang dùng nhầm tài khoản.

## 8. Lưu ý bảo mật và vận hành

- Không dùng mật khẩu demo trong môi trường thật.
- Đặt `SECRET_KEY` riêng, dài ít nhất 32 ký tự khi chạy production.
- Không commit file `.env` hoặc mật khẩu vào Git.
- Dùng HTTPS khi triển khai qua Internet.
- Sao lưu PostgreSQL định kỳ.
- Không chia sẻ access token, refresh token hoặc file sao lưu dữ liệu cho người không có quyền.
- Khi dùng máy tính chung, luôn đăng xuất và đóng trình duyệt.
- Tài khoản bị khóa không thể đăng nhập hoặc làm mới phiên backend.

## 9. Checklist nhanh cho giáo viên

- [ ] Đăng nhập đúng tài khoản giáo viên.
- [ ] Tạo lớp và kiểm tra năm học.
- [ ] Tạo tài khoản học sinh, bàn giao mật khẩu riêng.
- [ ] Đăng bài kiến thức cần thiết.
- [ ] Tạo đề và kiểm tra câu hỏi/đáp án.
- [ ] Giao đề đúng lớp.
- [ ] Theo dõi bài chờ chấm.
- [ ] Chấm bài và nhập nhận xét.
- [ ] Khóa tài khoản khi cần.
- [ ] Đăng xuất sau khi sử dụng.

## 10. Checklist nhanh cho học sinh

- [ ] Đăng nhập hoặc đăng ký tài khoản.
- [ ] Đổi mật khẩu sau lần đăng nhập đầu tiên.
- [ ] Đọc hướng dẫn và kiến thức trước khi làm bài.
- [ ] Kiểm tra thời gian trước khi bắt đầu.
- [ ] Không rời trang khi đang thi thử.
- [ ] Nộp bài trước khi đóng cửa sổ.
- [ ] Kiểm tra trạng thái bài trong Góc học tập.
- [ ] Đăng xuất trên thiết bị dùng chung.
