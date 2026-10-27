# BAO-CAO-KHOI-LUONG-VER496.md

| # | Hạng mục | Nội dung |
|---|---|---|
| 1 | Phiên bản | Ver 4.9.6 Claude |
| 2 | Ngày | 29/07/2026 |
| 3 | Nguồn gốc | Ảnh chụp production thật từ Thịnh (maybienapvn.vn, SKU MBT3P250A2608) — không phải bug tự tìm |
| 4 | Bug thật đã vá | Schema JSON-LD lộ ra thành chữ trên trang (WordPress kses xoá thẻ `<script>`, giữ text bên trong) |
| 5 | Yêu cầu đã xử lý | Bỏ khối checklist báo giá (giảm lead); content "hướng dẫn lựa chọn" bớt công thức cứng; slug thêm từ khoá SEO |
| 6 | An toàn ngược tự phát hiện | Đổi công thức slug có thể phá URL bài đã đăng thật khi update — đã vá riêng, không resend slug cho bài đã có wp_id |
| 7 | Việc đã thử rồi bỏ (không đoán mù) | Thêm `offers` vào Schema — phát hiện phá quyết định cũ có test khẳng định, KHÔNG áp dụng, giữ nguyên |
| 8 | File sửa | `render_phase2.py`, `prompts_phase2.py`, `ai_wp_adapter.py`, `giao-dien.py`, `test_gate2.py` (cập nhật D1 có giải thích) |
| 9 | File mới | `test_v496_patch.py`, `CHANGELOG-VER496.md`, `TEST-REPORT-VER496.md`, `BAO-CAO-KHOI-LUONG-VER496.md` |
| 10 | Test | 14 test mới (100% PASS) + 155 test trước đó chạy lại xác nhận không hồi quy = 169/169 |
| 11 | Chưa làm | Wire schema vào Rank Math (cần Thịnh xác nhận tên meta key thật); rà 15 sản phẩm đã đăng có bị trùng do đổi slug; RM6/SM6 (71 SKU) |
| 12 | Việc chỉ Thịnh làm được | Xác nhận đường đưa Schema lên site (unfiltered_html hoặc Rank Math meta), kiểm tra sản phẩm cũ không bị trùng, đọc thử content mới, xem slug mới trên trình duyệt thật |
