# VĂN UYỂN — Frontend

Source Nuxt 4 + Vue 3 + TypeScript chuyển từ `../index.html`. Giữ phong cách giao diện, responsive, dữ liệu LocalStorage và các nghiệp vụ đang có. File HTML gốc không bị thay đổi.

## Chạy local

Yêu cầu Node.js 22 trở lên (đã kiểm tra với Node.js 24), npm.

```sh
cd frontend
npm ci
npm run dev
```

Để chạy với backend FastAPI thật, đặt URL API trước khi khởi động:

```sh
NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1 npm run dev
```

Khi không đặt biến này, ứng dụng giữ chế độ LocalStorage tương thích bản HTML để phát triển giao diện offline.

Mở địa chỉ localhost được Nuxt in ra. Production:

```sh
npm run build
npm run preview
```

Ứng dụng chạy SPA (`ssr: false`). `npm run generate` xuất bản static; hosting cần fallback mọi đường dẫn về `index.html` để refresh các route con.

## Tổ chức source

- `app/pages/`: trang chủ, đăng nhập, đăng ký, kiến thức, luyện tập, thi thử, học tập, quản lý.
- `app/components/`: layout/menu, modal/toast, bài giảng, editor/thẻ đề, workspace, câu hỏi/chấm điểm và quản lý lớp.
- `app/composables/`: state dùng chung bằng Nuxt `useState`, tài khoản, LocalStorage, timer, workspace và anti-cheat.
- `app/repositories/`: hợp đồng lưu dữ liệu và implementation LocalStorage.
- `app/types/`: kiểu dữ liệu tương thích các bản ghi cũ.
- `app/utils/`: quy tắc đề, điểm, thời gian và lớp đọc/ghi storage.
- `app/data/theory.ts`: nội dung kiến thức mẫu lấy từ bản HTML.
- `app/assets/css/main.css`: CSS gốc và điều chỉnh cho Vue/mobile.

Component sử dụng props/events, `v-model`, `v-for` và reactive state. Không chạy lại script HTML cũ, không gắn hàm global hay inline `onclick`. `v-html` chỉ dùng cho nội dung bài giảng sau khi làm sạch bằng DOMPurify.

## Chức năng

- Giáo viên/học sinh đăng nhập; học sinh tự đăng ký; đổi mật khẩu.
- Kiến thức hai tầng, đọc/đăng/xóa bài, ảnh/PDF/link/HTML.
- Soạn/sửa/xóa và giao đề theo lớp.
- Đọc hiểu: 5 câu/4 điểm/25 phút; viết đoạn: 1 bài/2 điểm/35 phút; viết bài: 1 bài/5 điểm/60 phút.
- Thi thử: 7 câu/10 điểm/120 phút; hết giờ tự nộp. Luyện tập hết giờ cảnh báo và tiếp tục.
- Tự chấm, chấm từng câu, nhận xét, lịch sử, xếp hạng, làm lại và in/lưu PDF bằng trình duyệt.
- Tạo lớp, chuyển lớp, reset mật khẩu và xóa học sinh.
- Thông báo đề được giao và số bài chưa làm.

## Dữ liệu local và tài khoản

Các bảng vẫn dùng khóa `vu_users`, `vu_classes`, `vu_theory_articles`, `vu_practice_exams`, `vu_mock_exams`, `vu_results`, `vu_assignments`. Phiên đăng nhập dùng `vu_current_user` trong SessionStorage. Khi cùng origin và cùng profile, ứng dụng đọc dữ liệu cũ trực tiếp.

**HTML mở bằng `file://` và Nuxt trên localhost là hai vùng lưu trữ khác nhau.** Dữ liệu không tự chuyển giữa chúng. Đợt này chưa xây giao diện nhập/xuất toàn bộ dữ liệu hoặc nối backend.

Tài khoản giáo viên mẫu giống bản HTML, được khai báo trong `app/repositories/localDatabase.ts` và chỉ thêm khi bảng `vu_users` chưa tồn tại. Bảng rỗng có chủ đích không bị seed lại. Mật khẩu đã đổi không bị ghi đè khi reload.

Ở chế độ local, mật khẩu và đáp án nằm trong trình duyệt, phân quyền frontend không thay thế xác thực server. Khi bật `NUXT_PUBLIC_API_BASE`, đăng nhập/đăng ký, refresh token, đổi mật khẩu, đăng xuất, tạo lớp, đăng bài, tạo đề, giao đề, nộp bài, tải lịch sử, anti-cheat và chấm bài gọi backend FastAPI; access/refresh token chỉ lưu trong SessionStorage. API hiện chưa có endpoint sửa/xóa bài và đề nên giao diện sẽ báo rõ thao tác này chưa được hỗ trợ ở backend. Font Google và Font Awesome dùng URL giống bản HTML.

Bài làm mới lưu snapshot đề để có thể xem lại sau khi đề được sửa/xóa. Bài cũ không có snapshot cần còn đề gốc. Bài luyện tập được lưu khi nộp trước bước tự chấm; đóng cửa sổ tự chấm không làm mất bài đã nộp. Bài đang nhập chưa nộp chưa có autosave; đóng workspace sẽ hỏi xác nhận.

Một số lỗi cũ đã xử lý trong quá trình chuyển: ID mẫu trùng, reset mật khẩu giáo viên khi tải trang, lọc sai nhóm sau lưu đề, thiếu số lần làm, timer và listener không được dọn.

## Giai đoạn 2: dữ liệu và state

- Kiểm tra cấu trúc từng bảng và dữ liệu lồng nhau khi đọc/ghi: vai trò, loại đề, định dạng tài liệu, câu hỏi, đáp án, điểm hữu hạn không âm và ID không trùng trong mỗi bảng.
- Giữ các khóa `vu_*` và ID cũ. Bổ sung mặc định cho trường hiển thị tùy chọn; suy ra số lần làm từ thời điểm nộp nếu bản HTML chưa lưu. Việc đọc không viết đè dữ liệu cũ.
- Ghi `vu_schema_version=1` khi khởi tạo thành công. Dữ liệu chưa có phiên bản vẫn được đọc; phiên bản chưa hỗ trợ bị chặn để tránh ghi đè.
- Seed bài mẫu với UUID và chỉ khi bảng chưa tồn tại. Nếu khởi tạo lỗi giữa chừng, các khóa vừa tạo được hoàn tác; state chỉ được công bố sau khi ghi thành công.
- Form và state được tách bản sao khi lưu. Lỗi quota/permission hoặc validation không cập nhật state như thể đã lưu.
- Session chỉ lưu ID; vai trò, mật khẩu và lớp luôn lấy từ state người dùng hiện tại. Session HTML cũ được rút gọn; session lỗi hoặc tài khoản đã xóa được loại bỏ. Điều hướng chờ dữ liệu và session khởi tạo xong.
- Thay đổi dữ liệu ở tab khác cùng origin cập nhật qua sự kiện `storage`; chuyển lớp/reset mật khẩu/xóa tài khoản được phản ánh ở tab đang đăng nhập. Đây không phải cơ chế khóa hay giải quyết xung đột khi nhiều tab cùng ghi.
- Dữ liệu hỏng hiện thông báo có vị trí lỗi, nút tải bản sao nguyên trạng và nút thử lại. Không tự xóa bảng hỏng hay tự sửa ID trùng. File tải xuống giữ chuỗi gốc của từng khóa, kể cả JSON hỏng, để phục vụ khôi phục thủ công.

Giai đoạn 3 hiện đã đặt nền API client và auth backend; các repository nội dung/lớp/đề sẽ được chuyển tiếp theo từng màn hình. Không hỗ trợ import/export bảng tính. Chưa có công cụ chuyển dữ liệu tự động giữa origin `file://` và localhost. Các liên kết lịch sử tới đề/lớp đã xóa được giữ khi chạy local; validation không áp dụng ràng buộc khóa ngoại của một server database.

## Kiểm tra

```sh
npm run typecheck
npm test
npm run format:check
npm run build
```

E2E dùng một profile tạm riêng, không sửa dữ liệu trình duyệt đang dùng. Chạy dev server trước, rồi:

```sh
npx playwright install chromium
npm run test:e2e
```

Có thể dùng Chrome đã cài trên macOS:

```sh
PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm run test:e2e
```

Đặt `TEST_BASE_URL` nếu chạy server ở địa chỉ khác `http://127.0.0.1:3000`.

## Chạy toàn bộ stack bằng Docker

Từ thư mục gốc:

```sh
docker compose up --build
```

Frontend chạy tại `http://localhost:3000` và gọi backend tại `http://localhost:8000/api/v1`. Có thể ghi đè `NUXT_PUBLIC_API_BASE` trong file `.env` khi triển khai ở host khác.
