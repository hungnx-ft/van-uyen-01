# Plan: AI chấm bài và “Góc Phân Tích”

Kế hoạch này được triển khai tuần tự. Sau mỗi giai đoạn sẽ dừng để xác nhận trước khi làm tiếp. Không tự commit, push hoặc triển khai server.

## Giai đoạn 0 — Nguyên tắc

- AI chỉ đề xuất điểm và nhận xét; giáo viên duyệt điểm cuối.
- Học sinh chỉ thấy kết quả sau khi giáo viên công bố.
- Kết quả gắn theo học sinh, đề, bài nộp và lần làm.
- API key chỉ xử lý/lưu ở backend, không trả về frontend.

## Giai đoạn 1 — Dữ liệu nền *(đã hoàn thành)*

- Bảng cấu hình provider/model/API key mã hóa.
- Bảng barem theo từng đề, có version.
- Bảng job chấm AI và trạng thái retry/lỗi.
- Bảng kết quả AI theo từng câu, điểm, nhận xét, confidence.
- Bổ sung trạng thái publish, nhận xét cải thiện và lời phê giáo viên cho bài nộp.

## Giai đoạn 2 — Upload barem *(đã hoàn thành phần backend nền)*

- Upload PDF, DOCX, TXT, Markdown hoặc nhập text.
- Trích xuất text, xem trước, chỉnh sửa, thay thế/xóa barem.
- Lưu file gốc ngoài thư mục source và lưu version.

## Giai đoạn 3 — Cài đặt AI *(đã hoàn thành)*

- Màn hình chọn provider, model, Base URL.
- Nhập/xóa API key và kiểm tra kết nối.
- Bật/tắt AI theo giáo viên.

## Giai đoạn 4 — Provider abstraction *(đã hoàn thành)*

- Interface chấm chung.
- Adapter OpenAI-compatible trước, sau đó OpenAI, Anthropic, Gemini.
- Validate JSON, giới hạn điểm theo điểm tối đa từng câu.

## Giai đoạn 5 — API AI và barem *(đã hoàn thành)*

- API CRUD cấu hình AI.
- API CRUD barem theo đề.
- API tạo/xem/apply kết quả chấm AI.
- API lưu nhận xét giáo viên và publish kết quả.

## Giai đoạn 6 — UI barem từng đề *(đã hoàn thành)*

- Nút “Upload barem” trên mỗi đề.
- Preview, chỉnh sửa, version và trạng thái barem.
- Khóa nút chấm AI nếu đề chưa có barem.

## Giai đoạn 7 — UI chấm bài *(đã hoàn thành)*

- Hiển thị điểm AI, điểm giáo viên, nhận xét AI và nhận xét giáo viên theo câu.
- Ô nhận xét tổng quát, gợi ý cải thiện và lời phê cuối bài.
- Lưu bản nháp, áp dụng AI, lưu và công bố.

## Giai đoạn 8 — Hiển thị cho học sinh *(đã hoàn thành)*

- Chỉ hiển thị điểm/lời phê giáo viên sau publish.
- Mặc định ẩn raw response, prompt và confidence AI.

## Giai đoạn 9 — Lịch sử chấm

- Lưu provider, model, barem version, điểm và nhận xét từng lần chấm.
- Cho phép xem lại lịch sử thay đổi.

## Giai đoạn 10 — Chấm hàng loạt *(đã hoàn thành phần API hàng đợi)*

- Hàng đợi job, tiến trình, retry, hủy và giới hạn concurrency.
- Chỉ chấm bài có barem; không tự publish.

## Giai đoạn 11 — Bảo mật *(đã hoàn thành phần backend)*

- Mã hóa API key, không log secret.
- Rate limit, giới hạn file/prompt và kiểm tra quyền sở hữu dữ liệu.

## Giai đoạn 12 — Chi phí/chất lượng *(đã hoàn thành phần backend)*

- Token usage, chi phí ước tính, confidence thấp, retry và giới hạn chấm lại.

## Giai đoạn 13 — Testing *(đã hoàn thành phần test local)*

- Test migration, upload, provider, điểm, nhận xét, quyền, publish và UI.

## Giai đoạn 14 — Hoàn thiện vận hành *(đã hoàn thành phần worker/tài liệu)*

- Worker production, log, backup, retry và tài liệu cấu hình provider.

## Giai đoạn 15 — Dashboard “Góc Phân Tích” *(đã hoàn thành)*

- Tổng quan học sinh, lớp, đề, bài chờ chấm và AI usage.
- Chart điểm, tiến bộ, hoàn thành, phân bố điểm, câu hỏi yếu và anti-cheat.
- Chart provider/model, lượt gọi, token, chi phí, confidence và độ lệch AI–giáo viên.
- Phân tích lời phê, kỹ năng yếu và tỷ lệ giáo viên giữ/sửa nhận xét AI.
- Bộ lọc thời gian/lớp/đề/loại đề, drill-down và xuất CSV/Excel/PDF.
