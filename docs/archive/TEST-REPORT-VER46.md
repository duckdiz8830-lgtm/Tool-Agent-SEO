# TEST-REPORT-VER46.md

## Kết quả tổng

**326/326 PASS, 0 FAIL** (306 cũ không đổi + 13 patch 4.5.1 + 20 mới Ver 4.6, cộng 2 file test cũ được cập nhật fixture/assertion cho khớp thay đổi có chủ đích).

Đã verify portable từ `/tmp/v46_check` (thư mục đổi tên đúng `Lotech-Autopost-Ver4.6-Claude`).

Chạy y hệt cách các bản trước, thêm `test_v451_patch.py` và `test_v46.py` vào bộ lệnh.

## Chi tiết `test_v451_patch.py` (13 test — 5 điểm GPT review)

| Test | Kịch bản | Kết quả |
|---|---|---|
| P0-1..4 | Article Jobs (SUCCESS) là nguồn hợp lệ; job PENDING không tính; canonical ưu tiên bai_viet_phase2 khi có ở cả 2 nguồn | PASS |
| P1-SITE-1/2 | Record đăng 2 site khác nhau -> chỉ trả URL đúng site đang đăng | PASS |
| P1-DIEM-1, P1-CT-1, P1-SORT-1 | Ứng viên điểm 0 bị loại; service không lẫn vào product; sort ổn định khi bằng điểm | PASS |
| CTA-ANCHOR-1/2 | Nút "Yêu cầu báo giá" có đích `id="lien-he-bao-gia"` thật | PASS |
| HERO-DEDUP-1/2 | Mã hàng/thương hiệu chỉ xuất hiện đúng 1 lần trong Hero | PASS |

## Chi tiết `test_v46.py` (20 test)

| Nhóm | Test | Kết quả |
|---|---|---|
| CFG (cấu hình site) | Mặc định 'post', lưu 'woo_product' đúng, giá trị lạ tự về 'post' an toàn | PASS |
| WOO (đăng WooCommerce) | Tạo mới đúng endpoint `/wc/v3/products`, ép draft/simple, không set giá, SKU đúng | PASS |
| WOO (idempotent) | SKU đã có -> PUT đúng ID, không đẻ trùng | PASS |
| WOO (không retry mù) | POST timeout + kiểm SKU lại cũng lỗi mạng -> dừng hẳn, chỉ thử tạo mới đúng 1 lần | PASS |
| REQ (field bắt buộc) | JSON hợp lệ nhưng thiếu field -> FAILED; đủ field -> vẫn OK bình thường | PASS |
| FAQ (chất lượng văn bản) | Ký tự lặp, từ lặp, độ dài bất thường bị chặn; văn bản bình thường không bị chặn nhầm | PASS |
| TOKEN | maxOutputTokens = 16000 | PASS |

## Chưa test được

- Đăng thật lên WooCommerce (`maybienapvn.vn`) — sandbox không có mạng ra ngoài. Việc CHỈ Thịnh làm được: cấu hình site chọn "Sản phẩm (WooCommerce)", chạy 1-2 sản phẩm thật, xác nhận Draft xuất hiện đúng ở mục Sản phẩm (không phải Bài viết) trên WordPress Admin.
- Tỷ lệ Gemini thành công thật sau khi tăng token + field-thiếu-là-FAILED — cần Thịnh chạy batch thật để so sánh với 0/10 ban đầu.
