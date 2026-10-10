# Backend VĂN UYỂN

FastAPI + SQLAlchemy + PostgreSQL: auth, phân quyền, lớp/học sinh, bài giảng, đề, bài nộp, giao đề, chấm bài và chấm bằng AI. Frontend Nuxt trong `frontend/` gọi API này khi đặt `NUXT_PUBLIC_API_BASE`. Tổng quan dự án xem `README.md` ở thư mục gốc.

## Chạy với Docker

```sh
cp .env.example .env
docker compose up --build
```

Compose chờ PostgreSQL sẵn sàng, chạy `alembic upgrade head`, rồi mở API ở `http://localhost:8000`. Swagger: `/docs`, OpenAPI: `/api/v1/openapi.json`.

Chạy Python trực tiếp: dùng Python 3.12, virtualenv, `pip install -r requirements.txt`, PostgreSQL; thiết lập `DATABASE_URL`, chạy `alembic upgrade head` rồi `uvicorn app.main:app --reload`.

Production phải đặt `ENVIRONMENT=production`, secret riêng tối thiểu 32 ký tự và CORS origin frontend cụ thể. Secret mẫu bị từ chối trong production. Ví dụ sinh secret: `python -c 'import secrets; print(secrets.token_urlsafe(48))'`. Không commit `.env`.

Nên đặt thêm `AI_KEY_ENCRYPTION_KEY` (khóa Fernet) để mã hóa API key AI tách khỏi `SECRET_KEY`: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. API key đã lưu trước đó vẫn giải mã được; giáo viên lưu lại key một lần để chuyển sang khóa mới.

## Database đang có từ bản cũ

- Database trống: `alembic upgrade head` tạo toàn bộ schema.
- Database cũ do `create_all` tạo: sao lưu và đối chiếu schema với migration `0001_legacy_schema.py` trước. Chỉ khi khớp baseline, chạy `alembic stamp 0001` rồi `alembic upgrade head`.
- Không stamp mù lên database khác schema. Không dùng `create_all` để nâng cấp schema nữa.
- Migration `0002` giữ ID, mật khẩu băm và quan hệ lớp hiện có; tên hiển thị cũ mặc định lấy username, trạng thái mặc định active.
- Migration `0003` bổ sung quản lý lớp và membership học sinh.
- Migration `0004` bổ sung metadata xuất bản cho bài giảng/đề, đáp án và điểm bài nộp, cùng bảng giao đề theo lớp. Migration tự chuẩn hóa section cũ ngoài phạm vi và loại bản ghi điểm trùng trước khi thêm constraint.
- JWT cũ không có `sid`/issuer/audience không còn dùng được; người dùng đăng nhập lại.

## Tạo giáo viên đầu tiên

Không còn endpoint HTTP công khai tạo giáo viên. Sau migration, chạy:

```sh
docker compose exec backend python -m app.cli.seed_teacher \
  --username teacher@example.com --full-name 'Hà Thanh Hằng' \
  --school-name 'THCS Yên Phong'
```

CLI hỏi mật khẩu bằng `getpass`; automation có thể truyền biến `SEED_TEACHER_PASSWORD`. Không có mật khẩu hardcode, không reset/ghi đè tài khoản đã tồn tại. Tên đăng nhập phân biệt hoa/thường, chỉ cho phép chữ/số và `_.@+-`, dài 3–100 ký tự. Mật khẩu mới từ 8 ký tự, tối đa 72 byte UTF-8 để tránh bcrypt âm thầm cắt mật khẩu. `bcrypt==4.0.1` được pin để tương thích Passlib 1.7.4 của dự án.

## API tài khoản

| Method | Endpoint | Request / hành vi |
|---|---|---|
| POST | `/api/v1/auth/register` | JSON `username`, `password`, `full_name`, `school_name` tùy chọn; trả 201 |
| POST | `/api/v1/auth/login` | Form `username`, `password`; trả access + refresh token |
| POST | `/api/v1/auth/refresh` | JSON `refresh_token`; thay refresh token sau mỗi lần thành công |
| GET | `/api/v1/auth/me` | Bearer access token; trả profile, không trả password/hash |
| PUT | `/api/v1/auth/password` | Bearer + JSON `current_password`, `new_password`; thu hồi tất cả phiên, trả 204 |
| POST | `/api/v1/auth/logout` | Bearer; thu hồi phiên hiện tại, trả 204 |

Đăng ký tự do luôn tạo Student, `class_id=null`, `is_active=true`. Các field role/class/status bị từ chối thay vì nhận từ client.

Đăng nhập bị giới hạn 20 lần/phút mỗi IP và 10 lần/5 phút mỗi username (trả 429 kèm `Retry-After`); các endpoint `/api/v1/ai/` giới hạn 60 request/phút mỗi IP. Bộ đếm nằm trong bộ nhớ từng process. Sau reverse proxy, chạy uvicorn với `--proxy-headers --forwarded-allow-ips=<IP proxy>` để lấy đúng IP người dùng.

Ví dụ kết quả login:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

Access token có thời hạn mặc định 30 phút, luôn kiểm tra trạng thái user và phiên trong DB. Refresh token có thời hạn tuyệt đối mặc định 7 ngày tính từ lần login, không kéo dài khi refresh. DB chỉ lưu SHA-256 của refresh token. Refresh đồng thời cùng một token chỉ có một request thành công; token đã dùng trả 401, không thu hồi phiên thay thế. Frontend cần gom refresh thành một request chung và cập nhật token trước khi gửi request kế tiếp. Logout không ảnh hưởng phiên trên thiết bị khác; đổi/reset mật khẩu thu hồi tất cả phiên. Tài khoản inactive không login, refresh hoặc gọi API được.

Giai đoạn này API dùng Bearer và JSON token, không tự ghi cookie. Khi nối frontend cần chốt nơi lưu token; không tiếp tục coi role trong LocalStorage là quyền truy cập server.

## Quyền trên API hiện có

- Teacher chỉ list lớp của mình; tạo học sinh vào lớp mình sở hữu.
- `POST /users/students`: yêu cầu `username`, `password`, `full_name`, `class_id`; `school_name` tùy chọn, role nếu gửi chỉ được là `Student`.
- Học sinh tự đăng ký (chưa có lớp) hiện với mọi Teacher để xem và thêm vào lớp. Reset mật khẩu, sửa thông tin, khóa và xóa chỉ áp dụng cho Student đang thuộc lớp của Teacher; không áp dụng cho giáo viên, học sinh tự do hoặc lớp người khác.
- Chuyển lớp chỉ được giữa hai lớp thuộc cùng Teacher, hoặc từ trạng thái chưa có lớp vào lớp của Teacher.
- Teacher xem thư viện đề/bài giảng mình tạo. Học sinh thuộc lớp xem nội dung của giáo viên lớp đó. Học sinh tự do xem thư viện chung.
- Danh sách đề trả về cho Student luôn có `answer_key` rỗng. Đáp án chỉ đi kèm từng câu trả lời trong bài nộp của chính học sinh: đề luyện tập trả ngay khi nộp; đề thi thử chỉ trả sau khi giáo viên công bố kết quả.
- Học sinh chỉ thấy lịch sử bản thân; chỉ ghi anti-cheat cho bài của mình.
- Teacher chỉ chấm đề của mình; với học sinh thuộc lớp, lớp đó cũng phải thuộc Teacher. Không chấm được bằng ID câu trả lời của một bài khác.
- Tài nguyên ngoài quyền trả 404 để không tiết lộ sự tồn tại.

## Nội dung và giao đề

Đề Practice/Mock nhận `target_group`, `passage`, `genre`, `is_published`; câu hỏi nhận `answer_key`. Bài giảng nhận `main_category`, `sub_category`, `description`, `icon`, `is_published`. Bài nộp nhận lượt làm, thời điểm nộp, điểm tự chấm, điểm giáo viên và nhận xét; mỗi câu trả lời chỉ có một bản ghi điểm.

| Method | Endpoint | Quyền / hành vi |
|---|---|---|
| POST | `/api/v1/assignments/` | Teacher tạo giao đề cho lớp mình sở hữu; chỉ nhận đúng một `practice_exam_id` hoặc `mock_exam_id` thuộc teacher |
| GET | `/api/v1/assignments/` | Teacher xem giao đề của mình; Student xem giao đề theo lớp, mới nhất trước |
| POST | `/api/v1/submissions/` | Student nộp bài và các câu trả lời |
| GET | `/api/v1/submissions/my-submissions` | Student xem lịch sử bài làm của mình |
| GET | `/api/v1/submissions/teacher-submissions` | Teacher xem bài nộp thuộc đề của mình để chấm |
| POST | `/api/v1/submissions/{submission_id}/grade` | Teacher lưu điểm từng câu, tổng điểm và nhận xét |
| POST | `/api/v1/anti-cheat/event` | Student ghi nhận lần chuyển tab của bài đã nộp |

Backend không cung cấp import/export bảng tính; học sinh được tạo và quản lý qua API JSON.

## Chấm bằng AI

Provider hỗ trợ: `openai` và `openai-compatible` (Chat Completions). Giáo viên cấu hình ở `PUT /api/v1/ai/settings`, tải barem ở `POST /api/v1/exams/{practice|mock}/{exam_id}/rubric`, rồi tạo job ở `POST /api/v1/ai/submissions/{submission_id}/jobs` (hoặc `/ai/submissions/bulk-jobs`). Kết quả chỉ được chép vào bài nộp khi giáo viên gọi `POST /api/v1/ai/jobs/{job_id}/apply`.

Worker `python -m app.worker` (hoặc `--once` cho cron) lấy job `pending`, ghép câu trả lời với câu hỏi theo ID và gọi provider. Mỗi job thử tối đa 3 lần; `retry` đặt lại số lần thử. Job `processing` quá 10 phút được coi là worker đã chết và đưa lại hàng đợi. Job bị hủy trong lúc chấm thì kết quả về sau bị bỏ. Ở production, Base URL phải là HTTPS và phân giải ra địa chỉ public.

Điểm chấm tay và điểm AI không được vượt điểm tối đa của câu; tổng điểm AI không vượt điểm tối đa của đề. Đề đã có bài nộp chỉ sửa được nội dung, điểm và đáp án của các câu hiện có; thêm/bớt câu trả 409 để không làm mất liên kết với bài đã nộp. Upload hiện được đổi sang tên do server sinh và giới hạn 5 MB để không thể ghi đè đường dẫn do client cung cấp; kiểm tra nội dung file và API đọc/tải tài liệu thuộc module kiến thức.

## Transaction và lỗi

Mỗi request dùng một transaction; repository chỉ `flush()`, dependency `get_db()` commit khi thành công và rollback khi lỗi. Các service được gọi ngoài HTTP phải nằm trong `SessionLocal.begin()` hoặc transaction do caller quản lý.

Lỗi trả cùng envelope:

```json
{"error":{"code":"validation_error","message":"Request validation failed","details":[{"field":"body.password","message":"...","type":"..."}]}}
```

401: phiên/credential không hợp lệ; 403: sai role; 404: không tồn tại/ngoài quyền; 409: xung đột dữ liệu; 422: request không hợp lệ; 503: database không sẵn sàng. Response lỗi validation không echo input hoặc token/mật khẩu.

`/health/live` kiểm tra process. `/health/ready` kiểm tra kết nối DB, không trả lỗi kết nối chi tiết.

## Test riêng với PostgreSQL

```sh
docker compose -p van-uyen-stage2-test -f docker-compose.test.yml \
  up --build --abort-on-container-exit --exit-code-from tests
docker compose -p van-uyen-stage2-test -f docker-compose.test.yml down
```

Bộ test dùng Python 3.12, PostgreSQL 15 trong project Docker riêng, database nằm trong tmpfs, không map cổng host và không mount dữ liệu ứng dụng. Mỗi test có schema ngẫu nhiên và chạy migration thật. Chạy trực tiếp bằng `pip install -r requirements-dev.txt` rồi `TEST_DATABASE_URL=... pytest`; tên database phải chứa `test`.

Phạm vi: registration/validation/trùng username; hashing; JWT giả/hết hạn; refresh rotation và đồng thời; logout; đổi/reset mật khẩu thu hồi phiên; inactive account; seed CLI; quyền lớp/học sinh/bài làm; rollback; CORS/health; migration mới và nâng cấp/downgrade dữ liệu cũ.
