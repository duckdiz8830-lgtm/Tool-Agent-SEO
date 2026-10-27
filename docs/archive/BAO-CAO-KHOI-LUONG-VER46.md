# BAO-CAO-KHOI-LUONG-VER46.md

| # | Trường | Nội dung |
|---|---|---|
| 1 | Thời gian | 1 phiên làm việc dài, gồm 2 lượt chat (bị ngắt giữa 4.5.1, tiếp tục sang 4.6) |
| 2 | File sửa | 9 — `ai_wp_adapter.py`, `giao-dien.py`, `cauhinh.py`, `autopost.py`, `render_phase2.py`, `db_phase2.py`, `test_v37_1_patch.py`, `test_v39_article_jobs.py`, `test_v42_hero_cta.py` |
| 3 | File mới | 2 — `test_v451_patch.py`, `test_v46.py` |
| 4 | Dòng diff (tích luỹ từ Ver 3.6) | `ai_wp_adapter.py`: 363; `giao-dien.py`: 881; `cauhinh.py`: 38; `autopost.py`: 40; `render_phase2.py`: 294; `db_phase2.py`: 228; test mới: 200 + 136 |
| 5 | Test mới | 13 (4.5.1) + 20 (4.6) = 33 |
| 6 | Tổng test | 326/326 PASS, 0 FAIL |
| 7 | Hoàn thành | 5 điểm GPT review Ver 4.5.1; WooCommerce làm luồng đăng chính theo site; field-thiếu-là-FAILED; validator FAQ rác; tăng token 8192→16000; đổi tên "4.6 Claude" |
| 8 | Chưa làm | Quality Gate, Block Tài liệu kỹ thuật, xoay vòng nhiều API key (Thịnh nói để sau) |
| 9 | Không test được | Đăng thật lên WooCommerce; tỷ lệ Gemini thành công thật sau khi vá |
| 10 | Việc Thịnh làm | (a) Cấu hình site `maybienapvn.vn` chọn "Sản phẩm (WooCommerce)" ở tab Cấu hình. (b) Chạy thật 1-2 sản phẩm, xác nhận ra đúng mục Sản phẩm WooCommerce (không phải Bài viết). (c) Chạy batch thật so sánh tỷ lệ thành công với 0/10 trước đó. |
| 11 | Rủi ro | Thấp cho phần logic (test kỹ, có test âm chống retry mù/đăng trùng, học đúng bài học từ vụ vá WordPress). Rủi ro thật: chưa test được WooCommerce trên site thật — cấu trúc payload (`name`/`description`/`short_description`) dựa trên tài liệu REST API chuẩn của WooCommerce, chưa xác nhận tương thích 100% với theme Flatsome cụ thể mà Thịnh dùng. |
| 12 | Rủi ro pháp lý/bảo mật | Không có. |
| 13 | ZIP | `Lotech-Autopost-Ver4.6-Claude.zip` |

## Sự cố quy trình (ghi lại minh bạch)

Trong lúc chèn `dang_woo_that()`, str_replace vô tình xoá mất dòng khai
báo `def kiem_tra_ket_noi_wp():`, làm mất hẳn 1 hàm khỏi module. Phát hiện
ngay ở bước chạy `test_that_mocked.py` đầu tiên sau khi sửa (không dồn
đến cuối mới test) — vá trong vài phút. Đây là bằng chứng cụ thể cho việc
tại sao quy trình "test ngay sau mỗi bước, không dồn cuối" là bắt buộc,
không phải thủ tục hình thức.

Check field-thiếu-bắt-buộc và FAQ-chất-lượng mới cũng làm lộ ra 2 file
test cũ dùng dữ liệu giả quá ngắn (`'T'`, `'M'`) làm placeholder — sửa lại
fixture dùng độ dài thực tế, không nới lỏng validator mới để né test cũ.
