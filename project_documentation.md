# MÔ TẢ DỰ ÁN VĂN UYỂN

**Tên dự án:** VĂN UYỂN - Nơi chữ nghĩa nở hoa  
**Loại dự án:** Ứng dụng Web Học tập / Quản lý kiểm tra đánh giá (E-Learning platform)  
**Kiến trúc công nghệ:** Single-Page Application (SPA) hoàn toàn tĩnh (Serverless). Chạy bằng HTML, CSS (Vanilla) và JavaScript thuần trong 1 file duy nhất (`index.html`). Toàn bộ cơ sở dữ liệu được lưu tại bộ nhớ trình duyệt (`LocalStorage`).

---

## 1. MỤC TIÊU DỰ ÁN
VĂN UYỂN là một nền tảng "sổ tay văn học" điện tử kết hợp tính năng kiểm tra đánh giá trực tuyến. Dự án được thiết kế với giao diện thẩm mỹ mang phong cách "khu vườn văn chương" (hoa lá, màu sắc tươi sáng) dành riêng cho môn Ngữ văn. 
Dự án nhằm giúp:
- **Học sinh:** Tra cứu kiến thức, lý thuyết, luyện đề và thi thử với trải nghiệm tập trung (chống gian lận).
- **Giáo viên:** Dễ dàng soạn bài giảng, tạo hệ thống đề thi, quản lý lớp học và chấm điểm một cách tập trung mà không cần hệ thống máy chủ phức tạp.

---

## 2. PHÂN QUYỀN NGƯỜI DÙNG (ROLES)

Ứng dụng chia làm hai vai trò chính:
- **🎒 Học sinh:** Truy cập được Góc Kiến thức, Góc Luyện tập, Góc Thi thử và Cài đặt.
- **👩‍🏫 Giáo viên:** Ngoài các quyền của học sinh, Giáo viên có thêm đặc quyền truy cập **Góc Soạn đề** và **Góc Quản lý** lớp học/chấm điểm. Giáo viên đăng nhập qua việc nhập đúng mật mã được thiết lập sẵn.

---

## 3. CÁC TÍNH NĂNG CHÍNH (MODULES)

### 3.1. Góc Kiến Thức (Lý thuyết)
- **Hệ thống danh mục 2 tầng:** 
  - Đọc hiểu (Đọc hiểu Thơ, Đọc hiểu Truyện, Văn bản thông tin, Văn bản nghị luận)
  - Viết đoạn văn (Nghị luận xã hội, Nghị luận văn học)
  - Viết bài văn (Nghị luận xã hội, Nghị luận văn học)
- **Đa phương tiện:** Giáo viên có thể tải lên bài giảng dưới nhiều định dạng: Văn bản thuần (Text/HTML), Hình ảnh (tự động chuyển sang base64 lưu cục bộ), File PDF, hoặc dán Đường dẫn Link (tài liệu Google Drive/Docs).

### 3.2. Góc Luyện Tập
- Nơi học sinh làm các bài kiểm tra ngắn.
- **Cấu trúc đề:** Mỗi đề gồm đúng 5 câu hỏi thành phần (Tổng 4.0 điểm).
- **Tự chấm điểm:** Sau khi nộp bài, hệ thống hiển thị một giao diện đặc biệt gồm 4 cột: Bài làm của học sinh, Đáp án chuẩn của giáo viên, Khung tự chấm (học sinh tự đánh giá điểm của mình) và Khung chờ giáo viên chấm.

### 3.3. Góc Thi Thử
- Chế độ làm bài nghiêm túc với cấu trúc đề mô phỏng chuẩn kỳ thi thật.
- **Cấu trúc đề (Tổng 10.0 điểm):**
  - **Phần I. Đọc hiểu (4.0 điểm):** 5 câu hỏi nhỏ.
  - **Phần II. Viết (6.0 điểm):** 2 câu hỏi (Viết đoạn NLXH 2đ và Viết bài NLVH 4đ).
- Học sinh nộp bài và trạng thái sẽ là "Đang chờ chấm".

### 3.4. Góc Soạn Đề (Dành cho Giáo viên)
- Giao diện cho phép giáo viên nhập tiêu đề, đối tượng (Ôn thi vào 10/Thi HSG), ngữ liệu, và chi tiết từng câu hỏi/đáp án.
- Tự động thay đổi số lượng form nhập liệu tương ứng với loại đề (5 câu cho Luyện tập, 7 câu phân phần cho Thi thử).
- Tích hợp tính năng **Sửa/Xóa** đề ngay ngoài giao diện thẻ bài.

### 3.5. Góc Quản Lý & Chấm Bài (Dành cho Giáo viên)
- **Quản lý Lớp học:** Giáo viên tạo lớp học mới, dán danh sách tên học sinh. Hệ thống sẽ tự động tạo tài khoản và mật khẩu ngẫu nhiên cho từng em.
- **Tính năng trích xuất:** Tải xuống file danh sách tài khoản (`.txt`) để gửi cho lớp.
- **Chấm điểm:** Giáo viên xem danh sách các bài đã nộp, vào giao diện chấm điểm nhập điểm cho từng câu và để lại "Lời phê".
- Hệ thống hỗ trợ chuyển lớp, đặt lại mật khẩu cho học sinh nếu quên.

### 3.6. Góc Cài Đặt & Tiện Ích
- **Sao lưu/Phục hồi:** Export toàn bộ `LocalStorage` ra file JSON, và Import file JSON vào để phục hồi (do đặc thù không dùng Server).
- **Đổi Giao diện:** Chọn các theme thẩm mỹ khác nhau (Trắng, Xanh nhạt, Tím, Vàng).
- **Hệ thống Anti-cheat:** Khi làm bài thi, ngăn chặn học sinh bôi đen/copy-paste, cảnh báo và đếm số lần chuyển tab (rời khỏi trang web), tắt phím tắt chuột phải và F12.

---

## 4. CẤU TRÚC LƯU TRỮ DỮ LIỆU (DATABASE SCHEMA)
Do sử dụng `LocalStorage`, các "Bảng" dữ liệu được biểu diễn dưới dạng mảng JSON lưu trên trình duyệt:

1. `users`: Chứa thông tin đăng nhập, họ tên, role, id lớp học.
2. `classes`: Lưu thông tin các lớp (Tên lớp, năm học).
3. `theory_articles`: Lưu các bài giảng (tiêu đề, phân loại, nội dung văn bản/ảnh/base64/pdf).
4. `practice_exams`: Dữ liệu đề luyện tập (5 câu hỏi).
5. `mock_exams`: Dữ liệu đề thi thử (7 câu hỏi chia Phần I, Phần II).
6. `results`: Lưu kết quả làm bài của học sinh (đáp án, điểm tự chấm, điểm giáo viên chấm, thời gian làm bài).

---

## 5. HƯỚNG PHÁT TRIỂN / MỞ RỘNG (Tương lai)
- Xây dựng Backend thực thụ (NodeJS/Firebase) để đồng bộ hoá dữ liệu giữa các máy tính (hiện tại giáo viên và học sinh đang bị giới hạn thao tác trên cùng một máy, hoặc phải dùng tính năng Import/Export JSON để gửi qua lại).
- Nâng cấp bộ đếm giờ thi và nộp bài tự động khi hết giờ.
- Bổ sung biểu đồ thống kê kết quả học tập cho Góc Quản lý.

> [!NOTE]
> File mã nguồn hiện đang được lưu tại đường dẫn: `~/Desktop/so-tay-van-hoc/index.html`. Bạn có thể sao chép file này đi bất cứ đâu, mở bằng Chrome/Edge/Safari là web sẽ hoạt động ngay lập tức.
