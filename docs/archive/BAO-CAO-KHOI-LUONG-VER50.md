# BAO-CAO-KHOI-LUONG-VER50.md

| # | Hạng mục | Nội dung |
|---|---|---|
| 1 | Phiên bản | Ver 5.0 Claude |
| 2 | Ngày | 30/07/2026 |
| 3 | Nguồn gốc | Log lỗi production thật (batch 50 sản phẩm, bị dừng ở sản phẩm #6 do "Bài bị cắt vì vượt giới hạn token") + 6 góp ý UX từ ảnh chụp site thật |
| 4 | Bug thật đã vá | Gemini 3.x "suy nghĩ ngầm" không giới hạn, ăn chung ngân sách `maxOutputTokens` với câu trả lời JSON → cắt bài giữa chừng. Vá bằng `thinkingConfig.thinkingBudget=6000` + nâng `maxOutputTokens` 24000→48000 |
| 5 | UX đã sửa | Title bỏ mã hàng + thêm "Báo Giá"; CTA nổi bật hơn (không animation — giới hạn kỹ thuật thật của inline style); bảng so sánh công suất có link khi SKU đã đăng; placeholder chèn ảnh; "Đặc điểm" chia nhiều đoạn thay vì 1 khối; xem trước dạng trang HTML thật qua trình duyệt |
| 6 | Quyết định điều chỉnh (không phải hồi quy) | Title bỏ mã hàng (Ver 4.9.9 từng thêm theo khuyến nghị SEO tổng quát) và "Đặc điểm" chia đoạn (Ver 4.9.9 từng gộp 1 khối) — cả 2 điều chỉnh lại sau khi Thịnh xem thật trên site, có ghi chú rõ lý do trong code |
| 7 | File sửa | `ai_wp_adapter.py`, `render_phase2.py`, `db_phase2.py`, `prompts_phase2.py`, `giao-dien.py`, `test_v498_patch.py`, `test_v499_patch.py` |
| 8 | File mới | `test_v50_patch.py`, `CHANGELOG-VER50.md`, `TEST-REPORT-VER50.md`, `BAO-CAO-KHOI-LUONG-VER50.md` |
| 9 | Test | 22 test mới (100% PASS) + 240 test trước đó (2 test cập nhật theo hành vi mới có chủ đích) = 262/262 |
| 10 | Chưa làm | Chưa verify thinkingBudget=6000 là mức tối ưu (cần chạy thật để biết); animation CTA (giới hạn kỹ thuật, đã thống nhất bỏ); thông số kỹ thuật máy biến áp còn mỏng (ngoài phạm vi code); pillar page dầu/khô; cơ chế Hard Block fail nhảy sản phẩm tiếp theo |
| 11 | Việc chỉ Thịnh làm được | **Ưu tiên cao nhất: chạy lại batch thật, xác nhận lỗi MAX_TOKENS đã giảm/hết** — đây là bug chặn tiến độ đăng bài, cần xác nhận trước khi làm gì khác. Sau đó: xem trang mới, test nút mở trình duyệt, bắt đầu chèn ảnh thật |
