# VĂN UYỂN — Nơi chữ nghĩa nở hoa

Nền tảng học tập và kiểm tra môn Ngữ văn: học sinh đọc kiến thức, luyện đề, thi thử; giáo viên quản lý lớp, soạn đề, giao bài, chấm bài (có hỗ trợ chấm bằng AI) và theo dõi kết quả.

**Production:** https://nguvancohang.com (API: `https://nguvancohang.com/api/v1`). Server deploy từ branch `main`, xem [`DEPLOY_SERVER_VI.md`](DEPLOY_SERVER_VI.md).

## Kiến trúc

```text
Trình duyệt ──► Frontend Nuxt 4 / Vue 3 (SPA, thư mục frontend/)
                    │  REST + Bearer token
                    ▼
               Backend FastAPI (thư mục app/) ──► PostgreSQL 15
                    ▲
               AI worker (python -m app.worker) ──► API OpenAI / OpenAI-compatible
```

| Thành phần | Công nghệ | Ghi chú |
|---|---|---|
| Frontend | Nuxt 4, Vue 3, TypeScript | SPA (`ssr: false`). Có chế độ LocalStorage khi không cấu hình backend |
| Backend | FastAPI, SQLAlchemy 2, Alembic | JWT access token + refresh token xoay vòng, phân quyền Teacher/Student |
| Database | PostgreSQL 15 | Schema chỉ thay đổi qua migration Alembic |
| AI worker | Python, httpx | Lấy job từ hàng đợi trong DB, chấm theo barem, giáo viên duyệt trước khi áp dụng |

`index.html` ở thư mục gốc là bản HTML/LocalStorage đời đầu, chỉ giữ để tham khảo. Mô tả của bản đó nằm trong `project_documentation.md`.

## Tính năng chính

**Học sinh**
- Góc Kiến thức: bài giảng phân loại 2 tầng (Đọc hiểu, Viết đoạn văn, Viết bài văn), dạng văn bản, ảnh, PDF hoặc link.
- Góc Luyện tập: làm bài, xem đáp án ngay sau khi nộp để tự chấm.
- Góc Thi thử: đề theo cấu trúc thi thật, hết giờ tự nộp. Đáp án và điểm chỉ hiện khi giáo viên công bố kết quả.
- Xem lịch sử bài làm, điểm, lời phê và xếp hạng; đổi mật khẩu.
- Chống gian lận khi làm bài: chặn copy/chuột phải, đếm số lần rời tab.

**Giáo viên**
- Quản lý lớp (tạo, lưu trữ, khôi phục) và học sinh (tạo lẻ hoặc nhập hàng loạt từ Excel, chuyển lớp, khóa, đặt lại mật khẩu).
- Học sinh tự đăng ký hiện với mọi giáo viên để xếp lớp; chỉ khi đã vào lớp của giáo viên đó mới được đặt lại mật khẩu, sửa, khóa hoặc xóa.
- Soạn, sửa, xóa đề luyện tập và thi thử; số câu mỗi phần tùy chỉnh. Đề đã có bài nộp chỉ sửa được nội dung câu hỏi, không thêm/bớt câu.
- Giao đề cho lớp, chấm từng câu, viết lời phê và công bố kết quả.
- Chấm bằng AI: tải barem (PDF, DOCX, TXT, Markdown), chấm từng bài hoặc hàng loạt, xem lịch sử, áp dụng điểm AI sau khi duyệt.
- Góc Phân tích: thống kê kết quả, chi phí và độ lệch giữa điểm AI và điểm giáo viên.

## Chạy nhanh bằng Docker

```sh
cp .env.example .env
docker compose up --build
```

| Dịch vụ | Địa chỉ |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/v1 (Swagger: http://localhost:8000/docs) |
| PostgreSQL | `127.0.0.1:5432`, chỉ mở trên máy local |

Backend tự chạy `alembic upgrade head` khi khởi động. Tạo tài khoản giáo viên đầu tiên (không có endpoint công khai tạo giáo viên):

```sh
docker compose exec backend python -m app.cli.seed_teacher \
  --username giaovien --full-name "Giáo viên Văn Uyển" --school-name "Tên trường"
```

Học sinh có thể tự đăng ký tại trang `/register`, hoặc do giáo viên tạo trong Góc Quản lý.

## Phát triển không dùng Docker

Backend (Python 3.12, cần PostgreSQL đang chạy):

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # sửa DATABASE_URL nếu cần
alembic upgrade head
uvicorn app.main:app --reload
python -m app.worker          # chỉ khi cần chấm AI
```

Frontend (Node.js 22+):

```sh
cd frontend
npm ci
NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1 npm run dev
```

Bỏ `NUXT_PUBLIC_API_BASE` để chạy chế độ LocalStorage (không cần backend; dữ liệu và mật khẩu nằm trong trình duyệt, chỉ dùng để xem giao diện).

## Cấu hình

Biến môi trường của backend (xem `.env.example`):

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `ENVIRONMENT` | `development` | `production` bật các kiểm tra bắt buộc bên dưới |
| `SECRET_KEY` | giá trị mẫu | Ký JWT. Production bắt buộc giá trị riêng, tối thiểu 32 ký tự |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/van_uyen_db` | Kết nối PostgreSQL |
| `CORS_ORIGINS` | `["http://localhost:3000","http://127.0.0.1:3000"]` | Origin frontend, không chấp nhận `*` |
| `AI_KEY_ENCRYPTION_KEY` | trống | Khóa Fernet mã hóa API key AI, tách khỏi `SECRET_KEY` |
| `UPLOAD_DIR` | `uploads` | Nơi lưu file barem |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | `30` / `7` | Thời hạn token |

Frontend chỉ cần `NUXT_PUBLIC_API_BASE` (URL API mà trình duyệt gọi tới).

Tạo giá trị bí mật:

```sh
python -c "import secrets; print(secrets.token_urlsafe(48))"                               # SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # AI_KEY_ENCRYPTION_KEY
```

Sau khi đặt `AI_KEY_ENCRYPTION_KEY`, giáo viên lưu lại API key một lần trong Cài đặt AI. Từ đó có thể đổi `SECRET_KEY` mà không mất API key đã lưu.

## Chấm bài bằng AI

1. Giáo viên vào Cài đặt AI, chọn **OpenAI** hoặc **OpenAI-compatible**, nhập model, API key, Base URL (nếu có) và bật tính năng.
2. Tải barem cho từng đề.
3. Trong màn chấm bài, tạo job chấm AI. Worker lấy job, gọi provider và lưu kết quả.
4. Giáo viên xem kết quả, bấm áp dụng điểm, sửa nếu cần rồi công bố cho học sinh.

Worker thử lại tối đa 3 lần mỗi job. Job bị kẹt ở trạng thái đang xử lý hơn 10 phút (worker bị dừng giữa chừng) được tự đưa lại hàng đợi. Ở production, Base URL phải là HTTPS và trỏ tới địa chỉ public.

## Bảo mật

- Học sinh không nhận được đáp án qua danh sách đề; đáp án chỉ đi kèm bài nộp của chính học sinh (luyện tập: ngay sau khi nộp; thi thử: sau khi công bố kết quả).
- Đăng nhập bị giới hạn 20 lần/phút mỗi IP và 10 lần/5 phút mỗi tài khoản; API AI giới hạn 60 request/phút mỗi IP. Bộ đếm nằm trong từng process.
- Khi chạy sau reverse proxy, uvicorn phải chạy với `--proxy-headers --forwarded-allow-ips=<IP proxy>` để nhận đúng IP người dùng. Nếu không, mọi người dùng dùng chung một bộ đếm theo IP.
- Refresh token chỉ lưu dạng hash; đổi hoặc đặt lại mật khẩu thu hồi mọi phiên. Token phía trình duyệt nằm trong SessionStorage.

## Kiểm tra

```sh
# Backend: PostgreSQL riêng trong Docker, mỗi test một schema, chạy migration thật
docker compose -f docker-compose.test.yml run --rm --build tests
docker compose -f docker-compose.test.yml down -v

# Frontend
cd frontend
npm test
npm run typecheck
```

Chi tiết E2E (Playwright) xem `frontend/README.md`.

## Cấu trúc thư mục

```text
app/            Backend FastAPI: api/, services/, repositories/, models/, schemas/, worker.py
migrations/     Migration Alembic
frontend/       Frontend Nuxt: app/pages, app/components, app/composables
vendor/         Bộ wheel offline cho server Linux x86_64 + Python 3.12
index.html      Bản HTML/LocalStorage đời đầu (tham khảo)
```

## Tài liệu khác

| File | Nội dung |
|---|---|
| `app/README.md` | Chi tiết backend: API, phân quyền, transaction, migration |
| `frontend/README.md` | Chi tiết frontend: tổ chức source, chế độ LocalStorage, E2E |
| `DEPLOY_SERVER_VI.md` | Triển khai lên Linux + Nginx + systemd (không Docker) |
| `USER_GUIDE_VI.md` | Hướng dẫn sử dụng cho giáo viên và học sinh |
| `PLAN_AI_GOC_PHAN_TICH_VI.md` | Kế hoạch tính năng chấm AI và Góc Phân tích |
| `project_documentation.md` | Mô tả bản HTML/LocalStorage đời đầu |
