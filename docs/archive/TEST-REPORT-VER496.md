# TEST-REPORT-VER496.md

## Ver 4.9.6 Claude — 29/07/2026

### Test mới: `test_v496_patch.py` — 14/14 PASS

| Nhóm | Test | Kết quả |
|---|---|---|
| Schema | HTML không còn "application/ld+json" (S1-01) | PASS |
| Schema | HTML không còn "@context" lộ ra chữ (S1-02) | PASS |
| Schema | dung_bai_html() trả key 'schema' dict đúng nội dung Product (S1-03) | PASS |
| Checklist | Khối "Thông tin cần cung cấp để nhận báo giá" đã bỏ (S2-01) | PASS |
| Content | QUY_TAC_CHUNG không còn ép câu công thức cứng (S3-01) | PASS |
| Content | QUY_TAC_CHUNG có cấm rõ công thức "gửi bản vẽ" (S3-02) | PASS |
| Slug | Có từ khoá sản phẩm, không chỉ mã hàng suông (S4-01) | PASS |
| Slug | Vẫn chứa mã hàng — giữ duy nhất tuyệt đối (S4-02) | PASS |
| Slug | Vẫn suffix theo mẫu chuan/ngan_gon (S4-03) | PASS |
| Slug | Không crash khi thiếu ten_goc (S4-04) | PASS |
| An toàn ngược | dang_woo_that() chỉ gửi slug khi tạo mới (S5-01) | PASS |
| An toàn ngược | dang_wp_that() chỉ gửi slug khi tạo mới (S5-02) | PASS |
| An toàn ngược | goi (Woo) không khởi tạo sẵn key slug (S5-03) | PASS |
| An toàn ngược | goi (WP Post) không khởi tạo sẵn key slug (S5-04) | PASS |

### Full regression toàn bộ test cũ (bao gồm test_v495_patch.py) — sau khi sửa test_gate2.py::D1

| File | Kết quả |
|---|---|
| test_gate2.py | 23/23 PASS (D1 đã cập nhật theo hành vi mới, có giải thích) |
| test_phase2_full.py | 12/12 PASS |
| test_round2_integration.py | 34/34 PASS |
| test_v451_patch.py | 13/13 PASS |
| test_v46.py | 20/20 PASS |
| test_v47.py | 13/13 PASS |
| test_v48.py | 10/10 PASS |
| test_v49.py | 9/9 PASS |
| test_v495_patch.py | 21/21 PASS |

**Tổng cộng: 155/155 PASS (test trước Ver 4.9.6) + 14/14 PASS (test mới) = 169/169.**

### Thay đổi hành vi test — minh bạch, không âm thầm nới lỏng

`test_gate2.py::D1` trước đây kiểm tra schema JSON-LD NẰM TRONG `html` trả
về. Đây chính là hành vi GÂY RA BUG THẬT (mục 1 CHANGELOG-VER496.md) — giữ
nguyên test cũ nghĩa là giữ nguyên bug. Đã sửa test để khớp hành vi ĐÚNG
(schema trả riêng qua key `schema`, không lộ ra `html`), có comment giải
thích rõ lý do và trỏ về ảnh chụp bug thật, không xoá âm thầm.

### Việc chỉ Thịnh làm được

1. **Xác nhận cách thật để đưa Schema lên site** — 2 hướng khả dĩ: (a) cấp
   quyền `unfiltered_html` cho tài khoản Application Password đang dùng
   (nếu WordPress cho phép), hoặc (b) dùng custom field Rank Math (đã cài
   sẵn) — cần Thịnh xác nhận tên meta key thật của Rank Math (vào Rank Math
   → Schema Generator xem field lưu ở đâu) rồi báo lại để code tiếp, không
   đoán mù.
2. **Kiểm tra 15 sản phẩm đã đăng trước Ver 4.9.6** — xác nhận không có
   sản phẩm nào bị tạo trùng do đổi slug (đặc biệt nếu site nào dùng luồng
   WordPress Post thường thay vì WooCommerce — xem mục 5 CHANGELOG).
3. **Đọc thử vài bài mới sinh** — xác nhận "Hướng dẫn lựa chọn" đọc tự
   nhiên hơn, không còn công thức "gửi bản vẽ" lặp lại.
4. **Kiểm tra slug mới trên trình duyệt thật** — URL dài hơn trước (có từ
   khoá), xác nhận không vượt giới hạn hiển thị xấu trên site.
