# Triển khai VĂN UYỂN lên Linux + Nginx (không Docker)

Tài liệu này triển khai phiên bản hiện tại của dự án gồm:

- Frontend Nuxt 4/Vue 3 được build thành static SPA và phục vụ trực tiếp bởi Nginx.
- Backend FastAPI chạy bằng Uvicorn dưới `systemd` tại `127.0.0.1:8000`.
- PostgreSQL cài trực tiếp trên máy chủ.
- Địa chỉ public: `https://hungnguyenxuan.info/vanuyen/`.
- API public: `https://hungnguyenxuan.info/vanuyen/api/v1`.

Các lệnh bên dưới dành cho Ubuntu/Debian và cần tài khoản có quyền `sudo`. Nếu server dùng AlmaLinux/Rocky Linux, thay `apt` bằng `dnf`; phần cấu hình ứng dụng, systemd và Nginx giữ nguyên.

> Không ghi đè toàn bộ virtual host đang chạy của `hungnguyenxuan.info`. Phần Nginx bên dưới được thiết kế để chèn thêm vào `server { ... }` hiện hữu, nhờ đó website đang chạy ở `/` không bị ảnh hưởng.

## 1. Kiến trúc sau khi triển khai

```text
Trình duyệt
   |
   | HTTPS :443
   v
Nginx (hungnguyenxuan.info)
   |-- /vanuyen/          -> /var/www/vanuyen (frontend static)
   `-- /vanuyen/api/...   -> 127.0.0.1:8000/api/... (FastAPI)
                                  |
                                  `-> PostgreSQL localhost:5432
```

Chỉ cổng 80/443 mở ra Internet. Không mở cổng 3000, 8000 hoặc 5432.

## 2. Chuẩn bị DNS và kiểm tra server

Tại nơi quản lý DNS, tạo hoặc kiểm tra bản ghi:

```text
Type: A
Name: @
Value: IP_PUBLIC_CUA_SERVER
```

Nếu dùng Cloudflare, có thể tạm để `DNS only` lúc cấp chứng chỉ lần đầu. Kiểm tra DNS đã trỏ đúng:

```bash
getent hosts hungnguyenxuan.info
curl -I http://hungnguyenxuan.info
```

Cập nhật hệ thống và cài các gói cần thiết:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl ca-certificates build-essential \
  python3 python3-venv python3-dev libpq-dev \
  postgresql postgresql-contrib nginx
```

Kiểm tra service:

```bash
sudo systemctl enable --now postgresql nginx
sudo systemctl status postgresql nginx --no-pager
```

## 3. Cài Node.js 22 để build frontend

Nuxt trong dự án yêu cầu Node.js 22 trở lên. Cài NodeSource Node.js 22:

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version
```

Node chỉ dùng khi build frontend; production không cần chạy một Node server thường trực.

## 4. Tạo user chạy ứng dụng và tải source

Tạo system user không có quyền đăng nhập:

```bash
sudo useradd --system --create-home --home-dir /opt/van-uyen \
  --shell /usr/sbin/nologin vanuyen
```

Clone đúng repository và branch đang chứa frontend/backend mới:

```bash
sudo -u vanuyen git clone --branch feature/new_frontend \
  https://github.com/thanh-hang-204/van-uyen.git /opt/van-uyen/app
cd /opt/van-uyen/app
git rev-parse --short HEAD
```

Nếu code production đã được merge sang branch khác, thay `feature/new_frontend` bằng tên branch/tag cần triển khai. Không triển khai file `index.html` cũ ở thư mục gốc.

## 5. Tạo PostgreSQL database

Sinh mật khẩu database dạng URL-safe (chỉ chữ và số để không phải URL-encode trong `DATABASE_URL`):

```bash
openssl rand -hex 24
```

Lưu kết quả vào trình quản lý mật khẩu, rồi mở PostgreSQL shell:

```bash
sudo -u postgres psql
```

Thực hiện, thay `MAT_KHAU_DB_VUA_TAO` bằng giá trị thật:

```sql
CREATE USER vanuyen_app WITH PASSWORD 'MAT_KHAU_DB_VUA_TAO';
CREATE DATABASE vanuyen_db OWNER vanuyen_app ENCODING 'UTF8';
\q
```

Kiểm tra kết nối (lệnh sẽ hỏi mật khẩu):

```bash
psql -h 127.0.0.1 -U vanuyen_app -d vanuyen_db -c 'SELECT 1;'
```

PostgreSQL mặc định chỉ cần lắng nghe local. Không sửa `listen_addresses` thành `*` và không mở port 5432 trên firewall.

## 6. Cấu hình backend

Repository có sẵn bộ wheel offline dành riêng cho **Linux x86_64 + CPython 3.12**. Cách này không tải package từ PyPI trên server.

Tạo virtual environment, kiểm tra archive và cài dependency offline:

```bash
cd /opt/van-uyen/app
sudo -u vanuyen python3 -m venv .venv
cd vendor
sha256sum -c SHA256SUMS
sudo -u vanuyen tar -xzf python-wheels-linux-x86_64-py312.tar.gz \
  -C /opt/van-uyen/app/vendor
cd /opt/van-uyen/app
sudo -u vanuyen .venv/bin/pip install \
  --no-index \
  --find-links vendor/vanuyen-wheelhouse \
  -r requirements.txt
sudo -u vanuyen .venv/bin/pip check
```

Kết quả checksum phải là `OK`. Không dùng archive này nếu server là ARM hoặc Python khác 3.12.

Sinh secret riêng cho token:

```bash
openssl rand -hex 48
```

Tạo file cấu hình bằng editor:

```bash
sudo install -o root -g vanuyen -m 640 /dev/null /opt/van-uyen/app/.env
sudo nano /opt/van-uyen/app/.env
```

Nội dung (thay hai giá trị bí mật):

```dotenv
ENVIRONMENT=production
SECRET_KEY=SECRET_NGAU_NHIEN_VUA_TAO
DATABASE_URL=postgresql://vanuyen_app:MAT_KHAU_DB_VUA_TAO@127.0.0.1:5432/vanuyen_db
CORS_ORIGINS=["https://hungnguyenxuan.info"]
UPLOAD_DIR=/opt/van-uyen/data/uploads
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Lưu ý: CORS dùng **origin**, vì vậy không thêm `/vanuyen` vào `CORS_ORIGINS`. Không commit `.env` lên Git và không dùng secret mẫu trong source.

Tạo thư mục dữ liệu, chạy migration:

```bash
sudo install -d -o vanuyen -g vanuyen -m 750 /opt/van-uyen/data/uploads
cd /opt/van-uyen/app
sudo -u vanuyen .venv/bin/alembic upgrade head
sudo -u vanuyen .venv/bin/alembic current
```

## 7. Tạo tài khoản giáo viên đầu tiên

Chạy CLI có sẵn của dự án. Lệnh sẽ hỏi mật khẩu và không hiển thị mật khẩu ra màn hình:

```bash
cd /opt/van-uyen/app
sudo -u vanuyen .venv/bin/python -m app.cli.seed_teacher \
  --username giaovien \
  --full-name "Giáo viên Văn Uyển" \
  --school-name "Tên trường"
```

Mật khẩu phải dài từ 8 đến 72 byte UTF-8. CLI không ghi đè tài khoản đã tồn tại.

## 8. Tạo service systemd cho FastAPI

Tạo file:

```bash
sudo nano /etc/systemd/system/vanuyen-api.service
```

Nội dung:

```ini
[Unit]
Description=Van Uyen FastAPI backend
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=vanuyen
Group=vanuyen
WorkingDirectory=/opt/van-uyen/app
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/van-uyen/app/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Kích hoạt và kiểm tra:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now vanuyen-api
sudo systemctl status vanuyen-api --no-pager
curl -fsS http://127.0.0.1:8000/health/live
curl -fsS http://127.0.0.1:8000/health/ready
```

Kết quả `/health/ready` phải chứa `"database":"ok"`. Xem log khi có lỗi:

```bash
sudo journalctl -u vanuyen-api -n 100 --no-pager
```

## 9. Build frontend cho subpath `/vanuyen`

Hai biến sau bắt buộc được đặt **ngay lúc build**:

- `NUXT_APP_BASE_URL=/vanuyen/`: asset và Vue Router dùng đúng subpath.
- `NUXT_PUBLIC_API_BASE=/vanuyen/api/v1`: frontend gọi API qua cùng domain/Nginx.

Build và phát hành:

```bash
cd /opt/van-uyen/app/frontend
sudo -u vanuyen npm ci
sudo -u vanuyen env \
  NUXT_APP_BASE_URL=/vanuyen/ \
  NUXT_PUBLIC_API_BASE=/vanuyen/api/v1 \
  npm run generate

sudo install -d -o root -g www-data -m 755 /var/www/vanuyen
sudo cp -a .output/public/. /var/www/vanuyen/
sudo chown -R root:www-data /var/www/vanuyen
sudo find /var/www/vanuyen -type d -exec chmod 755 {} \;
sudo find /var/www/vanuyen -type f -exec chmod 644 {} \;
```

Kiểm tra nhanh giá trị đã được nhúng vào bundle:

```bash
grep -R "/vanuyen/api/v1" /var/www/vanuyen/_nuxt | head
test -f /var/www/vanuyen/index.html && echo "Frontend build OK"
```

Không dùng `npm run dev` hoặc `npm run preview` trong production.

## 10. Cấu hình Nginx

Tìm virtual host đang phục vụ domain:

```bash
sudo nginx -T | grep -n "server_name.*hungnguyenxuan.info"
```

Mở file tương ứng trong `/etc/nginx/sites-available/`. Chèn các `location` sau **bên trong cả server HTTPS đang có** (hoặc server HTTP trước khi cài SSL):

```nginx
# Chuẩn hóa URL để relative path luôn đúng.
location = /vanuyen {
    return 301 /vanuyen/;
}

# API phải đặt trước location frontend.
location ^~ /vanuyen/api/ {
    proxy_pass http://127.0.0.1:8000/api/;
    proxy_http_version 1.1;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    client_max_body_size 6m;
    proxy_connect_timeout 10s;
    proxy_read_timeout 120s;
}

# Frontend SPA. Fallback index.html giúp refresh /login, /study... không bị 404.
location /vanuyen/ {
    root /var/www;
    try_files $uri $uri/ /vanuyen/index.html;
}

# Asset có hash có thể cache lâu.
location ^~ /vanuyen/_nuxt/ {
    root /var/www;
    access_log off;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

Không đặt `location /vanuyen/` bên trong một `location` khác. Nếu cấu hình cũ có regex/location bắt mọi request, kiểm tra `nginx -T` để chắc chắn các block trên được ưu tiên.

Kiểm tra rồi reload an toàn:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Kiểm tra HTTP/local routing:

```bash
curl -I http://hungnguyenxuan.info/vanuyen/
curl -fsS http://hungnguyenxuan.info/vanuyen/api/v1/openapi.json | head -c 100
```

## 11. Cấp HTTPS bằng Let's Encrypt

Nếu `hungnguyenxuan.info` đã có HTTPS hợp lệ thì bỏ qua phần cài chứng chỉ, nhưng vẫn phải thêm các location vào block `listen 443 ssl`.

Nếu chưa có:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d hungnguyenxuan.info
sudo certbot renew --dry-run
```

Sau đó xác minh:

```bash
curl -I https://hungnguyenxuan.info/vanuyen/
curl -fsS https://hungnguyenxuan.info/vanuyen/api/v1/openapi.json | head -c 100
systemctl list-timers | grep certbot
```

Mở trình duyệt tại `https://hungnguyenxuan.info/vanuyen/`, đăng nhập giáo viên và thử tạo lớp/tài khoản học sinh.

## 12. Firewall tối thiểu

Nếu server dùng UFW:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

Hãy chắc chắn SSH đã được allow trước khi bật UFW. Không allow `8000/tcp` hay `5432/tcp`.

## 13. Quy trình cập nhật phiên bản

Trước khi cập nhật, backup database theo mục 14. Sau đó:

```bash
cd /opt/van-uyen/app
sudo -u vanuyen git fetch origin
sudo -u vanuyen git pull --ff-only origin feature/new_frontend

sudo -u vanuyen .venv/bin/pip install \
  --no-index \
  --find-links vendor/vanuyen-wheelhouse \
  -r requirements.txt
sudo -u vanuyen .venv/bin/alembic upgrade head

cd /opt/van-uyen/app/frontend
sudo -u vanuyen npm ci
sudo -u vanuyen env \
  NUXT_APP_BASE_URL=/vanuyen/ \
  NUXT_PUBLIC_API_BASE=/vanuyen/api/v1 \
  npm run generate

sudo cp -a .output/public/. /var/www/vanuyen/
sudo chown -R root:www-data /var/www/vanuyen
sudo systemctl restart vanuyen-api
sudo nginx -t
sudo systemctl reload nginx
```

Kiểm tra sau deploy:

```bash
curl -fsS http://127.0.0.1:8000/health/ready
curl -fsS https://hungnguyenxuan.info/vanuyen/api/v1/openapi.json >/dev/null
curl -fsS https://hungnguyenxuan.info/vanuyen/ >/dev/null
sudo systemctl --no-pager --full status vanuyen-api
```

Nếu đổi branch production, thay tên branch ở cả bước clone và update.

## 14. Backup và khôi phục

### Backup thủ công

```bash
sudo install -d -o postgres -g postgres -m 700 /var/backups/vanuyen
sudo -u postgres pg_dump -Fc vanuyen_db \
  -f /var/backups/vanuyen/vanuyen_db_$(date +%F_%H%M).dump
sudo tar -czf /var/backups/vanuyen/uploads_$(date +%F_%H%M).tar.gz \
  -C /opt/van-uyen/data uploads
```

Nên sao chép backup sang một máy hoặc object storage khác. Backup nằm cùng server không bảo vệ được khi ổ đĩa hỏng.

### Khôi phục database

Thao tác restore ghi đè dữ liệu hiện tại, chỉ thực hiện trong thời gian bảo trì và sau khi đã tạo thêm một backup:

```bash
sudo systemctl stop vanuyen-api
sudo -u postgres dropdb --if-exists vanuyen_db
sudo -u postgres createdb --owner=vanuyen_app vanuyen_db
sudo -u postgres pg_restore --no-owner --role=vanuyen_app \
  --dbname=vanuyen_db /var/backups/vanuyen/TEN_FILE.dump
sudo systemctl start vanuyen-api
curl -fsS http://127.0.0.1:8000/health/ready
```

Khôi phục uploads nếu ứng dụng có sử dụng endpoint upload:

```bash
sudo tar -xzf /var/backups/vanuyen/TEN_FILE_UPLOADS.tar.gz -C /opt/van-uyen/data
sudo chown -R vanuyen:vanuyen /opt/van-uyen/data/uploads
```

## 15. Theo dõi và xử lý lỗi

Các lệnh chẩn đoán thường dùng:

```bash
sudo journalctl -u vanuyen-api -f
sudo tail -n 100 /var/log/nginx/error.log
sudo tail -n 100 /var/log/nginx/access.log
sudo systemctl status vanuyen-api postgresql nginx --no-pager
sudo -u postgres psql -d vanuyen_db -c 'SELECT now();'
```

### Trang trắng hoặc asset `_nuxt` bị 404

- Xem source HTML/Network và kiểm tra asset bắt đầu bằng `/vanuyen/_nuxt/`.
- Build lại với `NUXT_APP_BASE_URL=/vanuyen/`.
- Kiểm tra file tồn tại dưới `/var/www/vanuyen/_nuxt/`.
- Chạy `sudo nginx -t` và xem cấu hình thực tế bằng `sudo nginx -T`.

### Frontend báo “Backend API chưa được cấu hình”

Biến API chưa được nhúng lúc build. Build lại với:

```bash
NUXT_APP_BASE_URL=/vanuyen/ \
NUXT_PUBLIC_API_BASE=/vanuyen/api/v1 \
npm run generate
```

Sau đó copy lại `.output/public` và hard refresh trình duyệt.

### API trả 502 Bad Gateway

```bash
sudo systemctl status vanuyen-api --no-pager
curl -v http://127.0.0.1:8000/health/ready
sudo journalctl -u vanuyen-api -n 100 --no-pager
```

Thường do `.env` sai, PostgreSQL chưa chạy, migration chưa chạy hoặc port 8000 đã bị chiếm.

### API public trả 404 nhưng API local hoạt động

Kiểm tra chính xác cặp cấu hình:

```nginx
location ^~ /vanuyen/api/ {
    proxy_pass http://127.0.0.1:8000/api/;
}
```

Dấu `/` cuối của cả `location` và `proxy_pass` là có chủ đích: Nginx đổi `/vanuyen/api/v1/...` thành `/api/v1/...` trước khi gửi FastAPI.

### Service báo lỗi SECRET_KEY

Ở `ENVIRONMENT=production`, ứng dụng từ chối secret mặc định hoặc secret ngắn hơn 32 ký tự. Sinh secret mới bằng `openssl rand -hex 48`, cập nhật `.env`, rồi:

```bash
sudo systemctl restart vanuyen-api
```

### Đăng nhập được nhưng request bị CORS

Giá trị đúng là:

```dotenv
CORS_ORIGINS=["https://hungnguyenxuan.info"]
```

Không thêm dấu `/` cuối và không thêm `/vanuyen` vì origin chỉ gồm scheme + hostname + port.

## 16. Checklist nghiệm thu

- [ ] DNS của `hungnguyenxuan.info` trỏ đúng IP server.
- [ ] `https://hungnguyenxuan.info/vanuyen/` trả HTTP 200.
- [ ] Refresh trực tiếp `/vanuyen/login`, `/vanuyen/study` không bị Nginx 404.
- [ ] Asset tải từ `/vanuyen/_nuxt/`, không phải `/_nuxt/`.
- [ ] `/vanuyen/api/v1/openapi.json` trả JSON.
- [ ] `/health/ready` local báo database `ok`.
- [ ] Đăng nhập giáo viên thành công.
- [ ] Tạo lớp, học sinh, đề, giao đề, nộp bài và chấm bài hoạt động.
- [ ] Port 8000 và 5432 không public.
- [ ] Chứng chỉ HTTPS tự gia hạn thành công.
- [ ] Có backup PostgreSQL ngoài server và đã thử quy trình restore.

## 17. Worker chấm AI (khi bật tính năng)

Worker đọc các job `pending`, gọi provider đã cấu hình, lưu kết quả và tự retry tối đa 3 lần. Tạo service riêng:

```ini
[Unit]
Description=Van Uyen AI grading worker
After=network.target postgresql.service vanuyen-api.service
Requires=postgresql.service

[Service]
User=vanuyen
Group=vanuyen
WorkingDirectory=/opt/van-uyen/app
ExecStart=/opt/van-uyen/app/.venv/bin/python -m app.worker
Restart=always
RestartSec=5
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Lưu tại `/etc/systemd/system/vanuyen-ai-worker.service`, sau đó:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now vanuyen-ai-worker
sudo journalctl -u vanuyen-ai-worker -f
```

Worker không tự publish kết quả. Giáo viên vẫn phải xem, áp dụng điểm và công bố feedback.

## 18. Lưu ý của phiên bản hiện tại

- `README.md` ở root mô tả bản LocalStorage/HTML cũ và không phản ánh đầy đủ stack production hiện tại; dùng tài liệu này cho triển khai server.
- Font Google và Font Awesome đang được tải từ CDN, nên giao diện cần Internet phía trình duyệt để hiển thị đúng font/icon.
- Backend có thư mục upload và giới hạn file 5 MB, nhưng luồng frontend hiện chủ yếu lưu nội dung/ảnh/PDF trong trường dữ liệu API. Vẫn nên backup cả PostgreSQL lẫn `/opt/van-uyen/data/uploads`.
- Đừng dùng SQLite thay PostgreSQL: migration và cấu hình production của repository này đã được xây dựng cho PostgreSQL.
