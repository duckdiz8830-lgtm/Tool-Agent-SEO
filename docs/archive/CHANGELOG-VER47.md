# CHANGELOG-VER47.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER46.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 4.7 CLAUDE — Auto fallback key/model + Chuẩn hoá MASTER có nút + FAQ length — 26/07/2026

Bối cảnh: log thật cho thấy máy biến áp thỉnh thoảng bị 2 lỗi — Gemini cắt
bài vì vượt token, hoặc tự sinh FAQ rác (1 câu hỏi dài 8162 ký tự, lặp kiểu
"a? a? a? a?..." — dấu hiệu model tự lặp/degenerate, không phải Hard Block
chặn nhầm). Cáp điện chạy 20 bài mượt không sao — nghi vấn hàng đầu là
model cụ thể (gemini-3.6-flash) không ổn định ở 1 số trường hợp, chưa chắc
do outline hay do "từ khoá nặng" (không có dấu hiệu `finishReason=SAFETY`
trong log, chỉ có `MAX_TOKENS`).

### Cơ chế tự động thử key/model dự phòng (`goi_ai_co_du_phong`)

Không sửa được tận gốc việc Gemini tự lặp (đây là lỗi tầng model, không
phải bug code), nhưng vá được **khả năng phục hồi**: khi 1 record gặp lỗi
— cắt token HOẶC Hard Block chặn nội dung rác — tự động thử lại **ngay
trong cùng lượt chạy** với cặp API key/model tiếp theo trong danh sách dự
phòng, không phải đợi chạy lại cả batch.

Thứ tự thử: **đổi model trước** (giữ nguyên key chính — rẻ, hợp lý khi lỗi
là model bất ổn), rồi **mới đổi key** (hợp lý khi lỗi là hết quota trong
ngày của key chính). 2 nguyên nhân khác nhau, không gộp chung 1 danh sách.

- `cauhinh.py`: `doc_gemini()` trả thêm `api_key_du_phong`/`model_du_phong`
  (list), `luu_gemini_du_phong()` lưu — không đụng field cũ, tương thích
  ngược 100%.
- `ai_wp_adapter.goi_ai_that()`: thêm tham số `api_key=None` (không truyền
  = đọc từ env như cũ, không đổi hành vi cũ) để lớp dự phòng gọi được
  nhiều key khác nhau mà không phải đổi biến môi trường giữa chừng (nguy
  hiểm khi nhiều luồng chạy).
- `ai_wp_adapter.goi_ai_co_du_phong()`: hàm mới, thử lần lượt (api_key,
  model), gộp CẢ bước gọi Gemini lẫn Hard Block vào 1 lượt thử — vì cả 2
  loại lỗi (cắt token, sinh rác) đều là dấu hiệu model bất ổn, đáng thử
  đổi cặp key/model như nhau.
- Nối vào cả 2 luồng đăng thật (Ver 3.7 batch + Ver 3.9 Article Jobs).
- UI: 2 ô nhập nhiều dòng (model dự phòng, API key dự phòng) trong tab
  Cấu hình, nút "Lưu dự phòng" riêng.

### Giới hạn độ dài câu hỏi FAQ trong prompt

Trước đây chỉ giới hạn độ dài CÂU TRẢ LỜI ("30-60 từ"), không giới hạn
CÂU HỎI — model không có điểm dừng rõ ràng. Thêm "mỗi câu hỏi DƯỚI 15 từ".
**Lưu ý trung thực:** đây là giảm nhẹ rủi ro (cho model 1 tín hiệu dừng rõ
hơn), KHÔNG phải fix triệt để — nếu model đang thật sự lặp vô hạn (degenerate),
dặn dò trong prompt không chắc chặn được, vì lúc đó model không còn "nghe
lời" nữa. Cơ chế tự động thử key/model dự phòng ở trên mới là lớp bảo vệ
chính.

### Tăng maxOutputTokens

16000 → 24000.

### Nút "Chuẩn hoá MASTER" trong UI

Tab "2. Nhập dữ liệu" — gọi THẲNG `chuan_hoa_master.chuan_hoa()` (không
viết lại logic, 1 nguồn code dùng chung cho cả dòng lệnh lẫn nút bấm).
Luồng: chọn thư mục `du_lieu_goc` → chọn nơi lưu file ra → chạy → hiện
tóm tắt + nhắc soát cột "Trạng Thái Kiểm Duyệt"/"Nghi Ngờ Phân Loại
Sai"/"Trùng Mã/Tên" trong Excel trước khi tự chọn "Chọn file MASTER..."
để nhập bản đã soát — KHÔNG tự động áp dụng, người dùng vẫn là người
duyệt cuối cùng.

### Vá banner cũ

Header trong app vẫn ghi "LOTECH AUTOPOST · VER 3" từ Ver 3.6 tới giờ (chỉ
tiêu đề cửa sổ được cập nhật qua các bản, banner tĩnh bị bỏ sót) — sửa
đúng "VER 4.7 Claude".

### File sửa

`ai_wp_adapter.py`, `giao-dien.py`, `cauhinh.py`, `prompts_phase2.py`,
`test_v37_batch_real.py`/`test_v37_1_patch.py`/`test_v39_article_jobs.py`
(cập nhật fixture mock nhận thêm `timeout`/`api_key`), `test_v46.py`
(cập nhật assertion token 16000→24000).

### File mới

`test_v47.py` (13 test — cấu hình dự phòng, 2 kịch bản fallback thật:
model cắt token và model sinh rác đều được cứu bằng đổi model, hết sạch
danh sách vẫn báo lỗi rõ ràng, prompt FAQ có giới hạn câu hỏi, token tăng,
module chuẩn hoá sẵn sàng cho GUI gọi).

### Không làm

- Không sửa được tận gốc việc Gemini tự lặp/degenerate — đây là hành vi
  model, ngoài khả năng kiểm soát bằng code. Cơ chế dự phòng là giảm
  thiểu, không phải triệt để.
- Chưa xác định được CHẮC CHẮN vì sao chỉ máy biến áp bị (nghi vấn hàng
  đầu là model, chưa loại trừ hẳn khả năng khác) — cần Thịnh xác nhận
  model dùng lúc chạy cáp điện mượt có phải cùng `gemini-3.6-flash`
  không, mới kết luận chắc được.
