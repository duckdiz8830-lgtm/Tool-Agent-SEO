# TEST-REPORT-VER47.md

## Kết quả tổng

**331/331 PASS, 0 FAIL** (318 cũ không đổi + 13 mới, cộng 4 file test cũ
được cập nhật fixture/assertion cho khớp thay đổi có chủ đích, không phải
nới lỏng để né lỗi).

Đã verify portable từ `/tmp/v47_check` (thư mục đổi tên đúng
`Lotech-Autopost-Ver4.7-Claude`).

## Chi tiết `test_v47.py` (13 test)

| Test | Kịch bản | Kết quả |
|---|---|---|
| CFG-1..4 | Lưu/đọc lại đúng model + API key dự phòng; rỗng an toàn; tách chuỗi đúng | PASS |
| DP-1 | Thành công ngay cặp đầu, không cần dự phòng | PASS |
| **DP-2** | **Đúng kịch bản thật của Thịnh:** model chính bị MAX_TOKENS -> tự chuyển model dự phòng, cứu được | PASS |
| **DP-3** | **Đúng kịch bản thật:** model chính sinh FAQ rác (Hard Block chặn) -> tự chuyển model dự phòng, cứu được | PASS |
| DP-4 | Hết sạch danh sách dự phòng vẫn lỗi -> trả lỗi cuối cùng rõ ràng, không giấu | PASS |
| DP-5 | Danh sách rỗng -> lỗi rõ ràng, không crash | PASS |
| KEY-1 | Truyền `api_key` trực tiếp vào `goi_ai_that()` -> dùng đúng key đó, không đọc env | PASS |
| FAQ-PROMPT-1 | Prompt user có giới hạn độ dài câu hỏi FAQ (trước chỉ có câu trả lời) | PASS |
| TOKEN-1 | maxOutputTokens = 24000 | PASS |
| CHM-WIRE-1 | Module `chuan_hoa_master` sẵn sàng cho nút GUI gọi (không viết lại logic) | PASS |

## File test cũ cập nhật (không phải lỗi, đổi chữ ký hàm nội bộ)

`test_v37_batch_real.py`, `test_v37_1_patch.py`, `test_v39_article_jobs.py`
— các hàm giả lập AI thêm `**_kwargs` để nhận `timeout`/`api_key` mà
`goi_ai_co_du_phong()` giờ truyền qua `goi_ai_that()`. `test_v46.py` — cập
nhật assertion token 16000→24000 (Ver 4.7 tăng thêm từ mức Ver 4.6).

## Chưa test được

- Cơ chế dự phòng chạy thật với model/key thật — sandbox không có mạng ra ngoài.
- Chưa xác định được chắc chắn nguyên nhân gốc máy biến áp hay lỗi (nghi vấn model, chưa loại trừ hẳn khả năng khác).
