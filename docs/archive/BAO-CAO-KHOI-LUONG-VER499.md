# BAO-CAO-KHOI-LUONG-VER499.md

| # | Hạng mục | Nội dung |
|---|---|---|
| 1 | Phiên bản | Ver 4.9.9 Claude |
| 2 | Ngày | 29/07/2026 |
| 3 | Nguồn gốc | Review SEO độc lập (Gemini, qua Thịnh chuyển lại) trên 2 bài đã đăng thật (KPK160CU, KPK180CU) — phát hiện trùng lặp ~85% giữa SKU cùng dòng |
| 4 | Nội dung chính | CSS inline (không cần thao tác tay); bỏ prefix "lotech-" (không để dấu vết tool); Delta Context (tier/chênh lệch/tải ước tính) tính bằng code, đưa vào prompt AI chống trùng lặp; boilerplate rút gọn dưới 40 từ; Title/H1 SKU-first không ngày tháng; khối "Về thương hiệu" data thật |
| 5 | Phản biện đề xuất Gemini | Bỏ "ép AI nhặt từ khoá theo quota" (đúng dấu hiệu Google phạt), bỏ số "30-40% tăng công suất AF" và "10-15% tiết kiệm chi phí" (bịa, không nguồn) — thay bằng rule mềm không quota + chỉ giữ khái niệm không giữ số |
| 6 | Rủi ro kỹ thuật đã tự kiểm chứng | Delta Context phải được Hard Block chấp nhận (số tính sẵn) nhưng vẫn chặn số AI tự bịa thêm — verify bằng test thật (V3-07/V3-08), không chỉ suy luận |
| 7 | File sửa | `render_phase2.py`, `profiles.py`, `prompts_phase2.py`, `giao-dien.py`, `test_round2_integration.py`, `test_v497_patch.py`, `test_v498_patch.py` |
| 8 | File mới | `test_v499_patch.py`, `CHANGELOG-VER499.md`, `TEST-REPORT-VER499.md`, `BAO-CAO-KHOI-LUONG-VER499.md` |
| 9 | Test | 31 test mới (100% PASS) + 208 test trước đó (10 test ở 3 file cập nhật theo hành vi mới có chủ đích, không nới lỏng) = 239/239 |
| 10 | Chưa làm | Pillar page dầu/khô (chưa có URL thật để wire link); cơ chế Hard Block fail nhảy sản phẩm tiếp theo (chờ xác nhận riêng); Rank Math SEO Title/Description riêng (cần xác nhận meta key thật); style inline chưa verify 100% qua WordPress thật |
| 11 | Việc chỉ Thịnh làm được | Xác nhận style inline hiển thị đúng trên site thật; đọc thử bài mới có so sánh SKU anh em; kiểm tra Title mới trên WordPress; quyết định viết Pillar page |
