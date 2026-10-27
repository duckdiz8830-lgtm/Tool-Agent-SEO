# CHANGELOG-VER37.md

Từ v2.5: mỗi ZIP kèm đủ tài liệu — `SPEC.md` (giữ nguyên, không đổi kiến
trúc), file này (= CHANGELOG), `KNOWN-ISSUES.md`, `TEST-REPORT-VER37.md`,
`BAO-CAO-KHOI-LUONG-VER37.md`. Theo dõi tiến độ tổng thể xem tracker Excel.

---

## LOTECH AUTOPOST VER 3.7 — Real Batch Publish MVP — 26/07/2026

Mở khoá đăng WordPress THẬT cho **nhiều sản phẩm/lần** (trước đây chỉ xử lý
đúng 1 record active). Sửa trực tiếp trên code Ver 3.6, không tạo codebase
song song, không đổi schema DB.

### Đã làm

| # | Hạng mục | Trước | Sau | Trạng thái |
|---|---|---|---|---|
| 1 | Đăng Draft thật | Chỉ 1 record active/lần | Toàn bộ record `selected=1`, chạy tuần tự | DONE |
| 2 | Bỏ qua record đã xong | Không có — luôn gọi lại Gemini/WP | Kiểm `trang_thai='da_dang'` + có `wp_id` trước khi gọi API — bỏ qua nếu đã xong | DONE |
| 3 | Lỗi 1 record không chết batch | N/A (chưa có batch thật) | try/tiếp tục vòng lặp, ghi `trang_thai='loi'` + lý do, sang record kế | DONE |
| 4 | Dừng an toàn giữa batch | Nút Dừng bị khoá cứng ở luồng Real (`state='disabled'`) | Bật lại `nut_v3_dung`, tái dùng CHÍNH Event `v3_dung_lai` đã có từ Mock batch — kiểm ở đầu mỗi record | DONE |
| 5 | Hiển thị tiến độ | Chỉ 4 bước cố định (1/4→4/4) | `đã chạy/tổng`, `thành công`, `lỗi` theo từng record thật | DONE |
| 6 | Retry lỗi mạng/429/5xx | — | **Không viết mới** — `goi_ai_that()` và `dang_wp_that()` đã tự retry (3 lần, backoff, phân biệt lỗi tạm thời vs lỗi dữ liệu) từ Ver 3.4. Xác nhận lại còn đúng khi gọi trong vòng lặp. | ĐÃ CÓ SẴN, không cần code thêm |
| 7 | Chống đẻ `slug-2` | — | **Không viết mới** — `dang_wp_that()` đã tra `wp_id` lưu sẵn rồi tra `slug` qua `autopost.tim_bai_theo_slug()` trước khi tạo bài, từ Ver 3.4/3.5. | ĐÃ CÓ SẴN |
| 8 | Trạng thái RUNNING treo khi crash | — | **Không cần** — thiết kế hiện tại không bao giờ ghi trạng thái "đang chạy" vào DB; record đang xử lý dở vẫn ở `chua_sinh` (= PENDING), tự nhiên an toàn khi app đóng đột ngột giữa batch. | KHÔNG CẦN SỬA (đã đúng sẵn) |

### Cắt khỏi Work Order gốc (và lý do)

- **Retry tự động phân loại lỗi (mục 7-8 Work Order)**: không viết logic mới — 2 hàm adapter đã tự làm việc này từ Ver 3.4, viết lại là trùng lặp.
- Không đổi tên hàng loạt, không đổi schema `bai_viet_phase2` — dùng nguyên cột `trang_thai`/`loi`/`wp_id`/`wp_url`/`thoi_luong_giay` đã có.

### File đã sửa

- `giao-dien.py` — thay `_v3_dang_draft_that()` (1 record) bằng bản chọn-nhiều-record; thêm `_v3_viec_dang_draft_that_hang_loat()` và `_v3_cap_nhat_tien_do_that()`; xoá `_v3_viec_dang_draft_that()`/`_v3_ket_thuc_dang_that()` cũ (không còn ai gọi).
- `test_v34_that_ui.py` — thu hẹp lại selection về đúng 1 record trước khi test luồng Real (Ver 3.7 đổi hành vi sang chọn-nhiều), sửa assertion REAL-1 theo nhãn tiến độ mới (không còn popup `messagebox.showinfo`).

### File mới

- `test_v37_batch_real.py` — 8 test riêng cho Ver 3.7 (T1–T4b, xem TEST-REPORT-VER37.md).

### Known issues còn lại

- Chưa xác nhận network THẬT (Gemini/WordPress thật) — mọi test ở đây dùng mock. Việc CHỈ Thịnh làm được: chạy batch thật N=5 → N=20.
