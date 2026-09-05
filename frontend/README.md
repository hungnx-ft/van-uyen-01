# VĂN UYỂN — Frontend

Source Nuxt 4 + Vue 3 + TypeScript chuyển từ `../index.html`. Giữ phong cách giao diện, responsive, dữ liệu LocalStorage và các nghiệp vụ đang có. File HTML gốc không bị thay đổi.

## Chạy local

Yêu cầu Node.js 22 trở lên (đã kiểm tra với Node.js 24), npm.

```sh
cd frontend
npm ci
npm run dev
```

Mở địa chỉ localhost được Nuxt in ra. Production:

```sh
npm run build
npm run preview
```

Ứng dụng chạy SPA (`ssr: false`). `npm run generate` xuất bản static; hosting cần fallback mọi đường dẫn về `index.html` để refresh các route con.

## Tổ chức source

- `app/pages/`: trang chủ, đăng nhập, đăng ký, kiến thức, luyện tập, thi thử, học tập, quản lý.
- `app/components/`: layout/menu, modal/toast, bài giảng, editor/thẻ đề, workspace, câu hỏi/chấm điểm, lớp học/Excel.
- `app/composables/`: state dùng chung bằng Nuxt `useState`, tài khoản, LocalStorage, timer, workspace, anti-cheat, Excel.
- `app/types/`: kiểu dữ liệu tương thích các bản ghi cũ.
- `app/utils/`: quy tắc đề, điểm, thời gian và lớp đọc/ghi storage.
- `app/data/theory.ts`: nội dung kiến thức mẫu lấy từ bản HTML.
- `app/assets/css/main.css`: CSS gốc và điều chỉnh cho Vue/mobile.

Component sử dụng props/events, `v-model`, `v-for` và reactive state. Không chạy lại script HTML cũ, không gắn hàm global hay inline `onclick`. `v-html` chỉ dùng cho nội dung bài giảng sau khi làm sạch bằng DOMPurify. Excel được tải bằng dynamic import.

## Chức năng

- Giáo viên/học sinh đăng nhập; học sinh tự đăng ký; đổi mật khẩu.
- Kiến thức hai tầng, đọc/đăng/xóa bài, ảnh/PDF/link/HTML.
- Soạn/sửa/xóa và giao đề theo lớp.
- Đọc hiểu: 5 câu/4 điểm/25 phút; viết đoạn: 1 bài/2 điểm/35 phút; viết bài: 1 bài/5 điểm/60 phút.
- Thi thử: 7 câu/10 điểm/120 phút; hết giờ tự nộp. Luyện tập hết giờ cảnh báo và tiếp tục.
- Tự chấm, chấm từng câu, nhận xét, lịch sử, xếp hạng, làm lại và in/lưu PDF bằng trình duyệt.
- Tạo lớp, nhập học sinh từ cột đầu tiên file Excel, xuất tài khoản, chuyển lớp, reset mật khẩu, xóa học sinh.
- Thông báo đề được giao và số bài chưa làm.

## Dữ liệu local và tài khoản

Các bảng vẫn dùng khóa `vu_users`, `vu_classes`, `vu_theory_articles`, `vu_practice_exams`, `vu_mock_exams`, `vu_results`, `vu_assignments`. Phiên đăng nhập dùng `vu_current_user` trong SessionStorage. Khi cùng origin và cùng profile, ứng dụng đọc dữ liệu cũ trực tiếp.

**HTML mở bằng `file://` và Nuxt trên localhost là hai vùng lưu trữ khác nhau.** Dữ liệu không tự chuyển giữa chúng. Đợt này chưa xây giao diện nhập/xuất toàn bộ dữ liệu hoặc nối backend.

Tài khoản giáo viên mẫu giống bản HTML, được khai báo trong `app/composables/useDatabase.ts` và chỉ thêm khi chưa có giáo viên. Mật khẩu đã đổi không bị ghi đè khi reload. Học sinh nhập Excel dùng mật khẩu khởi tạo `demo@123` như bản cũ.

Đây vẫn là chế độ local: mật khẩu và đáp án nằm trong trình duyệt, phân quyền frontend không thay thế xác thực server. Chưa gọi backend FastAPI. Font Google và Font Awesome dùng URL giống bản HTML.

Bài làm mới lưu snapshot đề để có thể xem lại sau khi đề được sửa/xóa. Bài cũ không có snapshot cần còn đề gốc. Bài luyện tập được lưu khi nộp trước bước tự chấm; đóng cửa sổ tự chấm không làm mất bài đã nộp. Bài đang nhập chưa nộp chưa có autosave; đóng workspace sẽ hỏi xác nhận.

Một số lỗi cũ đã xử lý trong quá trình chuyển: ID mẫu trùng, reset mật khẩu giáo viên khi tải trang, lọc sai nhóm sau lưu đề, thiếu số lần làm, timer và listener không được dọn.

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
