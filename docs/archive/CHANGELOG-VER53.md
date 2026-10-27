# CHANGELOG-VER53.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER52.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 5.3 CLAUDE — Giai đoạn 1 của Đề xuất toàn diện — 30/07/2026

Thực thi trọn "Giai đoạn 1" trong `DE-XUAT-TOAN-DIEN-LOTECH-AUTOPOST.md`
(7 hạng mục code ngay, không chờ dữ liệu/quyết định gì thêm từ Thịnh).

### B5 — Nút "Cập nhật lại bài đã đăng" (ưu tiên cao nhất)

Trước đây bài có `wp_id` (đã đăng) bị bỏ qua **vĩnh viễn** ở mọi bản sau —
đây chính là lý do Thịnh từng hiểu lầm "fix không chạy" (case KPK250CU,
thực ra bài chưa từng được sinh lại). Thêm checkbox "Cho phép cập nhật lại
bài ĐÃ ĐĂNG" (mặc định TẮT — an toàn ngược, không đổi hành vi cũ nếu không
bật). Bật lên: vòng lặp batch KHÔNG skip bài đã đăng nữa, sinh nội dung
mới rồi gọi `dang_woo_that()`/`dang_wp_that()` như bình thường — **2 hàm
này ĐÃ tự tra `wp_id`/SKU cũ để làm UPDATE (PUT) thay vì tạo bài mới**
(đọc code xác nhận kỹ trước khi làm, không cần sửa gì ở tầng đó).

Dialog xác nhận hiện cảnh báo rõ khi bật chế độ này ("sẽ bị GHI ĐÈ nội
dung mới"). Log ghi rõ `[CẬP NHẬT LẠI]` để phân biệt với đăng mới.

### B6 — Hard Block chặn → thất bại ngay, không đốt hết cặp dự phòng

Trước đây: Hard Block chặn nội dung cốt lõi (không phải lỗi mạng) vẫn
`continue` sang cặp key/model tiếp theo — tốn quota vô ích khi đổi model
không chắc sửa được (bản chất thường do data mỏng khiến AI phải "chế"
thêm, không phải lỗi ngẫu nhiên của 1 model). Giờ: Hard Block chặn cốt
lõi → **`return` thất bại ngay lập tức** cho sản phẩm này, KHÔNG thử thêm
cặp nào khác — dành quota cho sản phẩm MỚI trong cùng batch, hiệu quả hơn
cố mãi 1 sản phẩm cứng đầu. Sản phẩm lỗi không mất, batch sau (mai, quota
reset) tự thử lại (chỉ bỏ qua bài `da_dang`, không bỏ qua bài `loi`).

**Phân biệt rõ với lỗi 429/mạng** — nhánh đó VẪN thử tiếp như cũ (đã test
riêng xác nhận không lẫn 2 loại lỗi). Test bằng mock xác nhận: Hard Block
→ đúng 1 lần gọi AI; lỗi mạng → vẫn đủ 3 lần thử như thiết kế cũ.

### C6 — Khối "Về lõi Silic/Amorphous"

Mở rộng độ sâu content theo yêu cầu Thịnh (đối chiếu bài mẫu Gemini —
phần giải thích lõi Silic của họ dùng được vì là kiến thức ngành chung).
CODE viết cứng, KHÔNG có số % nào (tránh lặp lỗi "CAPEX giảm 30-40%" đã
bị chặn ở bài Gemini trước — không có 1 số % chung đúng cho mọi thiết kế
máy thật). Chỉ hiện khi nhận diện được loại lõi từ Tên hàng, rỗng cho
outline vỏ (vỏ không có lõi) và khi không rõ loại (không đoán).

### C7 — Khối "Bảo trì & lắp đặt"

Tách riêng khỏi `khoi_chung_may_bien_ap()` (đã rút gọn còn 1 câu từ Ver
4.9.9 để chống Boilerplate SEO — KHÔNG nhét lại nội dung dài vào đó).
Nội dung là thực hành bảo trì CHUNG của ngành (dầu: kiểm tra dầu cách
điện, rãnh thu dầu sự cố; khô: vệ sinh bụi, thông gió) — KHÔNG phải cam
kết bảo hành/chính sách riêng Lotech (cái đó cần Thịnh xác nhận chính
sách thật trước, xem đề xuất mục C13, CHƯA làm ở bản này).

### C8 — Bullet points + in đậm từ khoá

Thêm QUY_TAC_CHUNG rule #12: khi 1 mục có từ 3 ý trở lên, ưu tiên
`<ul><li>` thay vì đoạn văn dài liền mạch; in đậm 1-3 cụm từ khoá/thông số
quan trọng mỗi đoạn. Chỉ sửa PROMPT — không đổi dữ liệu. `<strong>`/`<ul>`/
`<li>` đã có sẵn trong `ALLOWED_TAGS` (sanitize_html), không cần sửa
whitelist.

### C9 — "Sản phẩm liên quan" dạng grid

Đổi từ `<ul><li>` (list gạch đầu dòng thô, Thịnh nhận xét "chắp vá") sang
CSS Grid — mỗi sản phẩm 1 thẻ viền bo góc, tự xuống dòng theo độ rộng màn
hình, dễ quét mắt hơn.

### C10 — Nút "Tải Catalogue/Datasheet (PDF)"

Thêm field `catalogue_pdf_url` — **OPTIONAL** ở `cot_import` của **cả 4
profile** (đã cẩn thận thêm `cot_bat_buoc` tường minh cho `cap_dien` và
`may_bien_ap_do_luong` — 2 profile này TRƯỚC ĐÓ dựa vào hành vi mặc định
"None = mọi cột trong cot_import đều bắt buộc"; nếu chỉ thêm field mới mà
không khai báo `cot_bat_buoc`, MASTER hiện tại sẽ VỠ IMPORT vì thiếu cột
mới — đã tránh đúng lỗi này, học từ sự cố tương tự ở Ver 4.9.5).

`khoi_nut_catalogue()` chỉ hiện nút khi field có giá trị thật — MASTER
hiện **chưa có cột này**, nên nút ẩn cho MỌI sản phẩm tới khi Thịnh có
file PDF thật và điền link vào MASTER (không suy đoán/tạo link giả).

### File sửa

`giao-dien.py` (checkbox + logic bỏ skip, đổi tiêu đề bản),
`ai_wp_adapter.py` (Hard Block fail-fast), `render_phase2.py` (3 hàm mới:
`khoi_ve_loi`, `khoi_bao_tri_lap_dat`, `khoi_nut_catalogue`; sửa
`khoi_san_pham_lien_quan` sang grid; wire cả 3 vào `dung_bai_html`),
`profiles.py` (field `catalogue_pdf_url` optional cho 4 profile),
`prompts_phase2.py` (rule 12), `tests/test_v47.py` +
`tests/test_v51_patch.py` (cập nhật theo hành vi mới có chủ đích, có giải
thích rõ lý do), `validators.py` (xem mục vá hồi quy dưới đây).

### VÁ THÊM — hồi quy thật do Ver 5.2 gây ra, tự phát hiện lúc chạy full regression trước khi đóng gói bản này

`validators.py::validate_may_bien_ap()` (bộ sửa bug kVA/kV — Cấp Điện Áp
bị copy nhầm bằng Công Suất) chỉ gate theo `outline_id ==
'outline_may_bien_ap'`. Ver 5.2 tách "Vỏ mạ kẽm..." ra outline RIÊNG
(`outline_vo_may_bien_ap`, đúng — vỏ không phải máy biến áp thật) nhưng
KHÔNG cập nhật lại gate này — hậu quả: ~24 dòng vỏ đang bị bug kVA/kV
**thôi không được fix nữa** kể từ Ver 5.2 (giảm từ 165 dòng bug/164 tự sửa
xuống còn 141/140, lệch đúng 24 — khớp số dòng vỏ).

Phát hiện qua `test_phase2_full.py::Test 10` báo lệch số khi chạy ĐỦ
30 file test trước khi đóng gói — **không phải do review ngoài phát hiện,
tự bắt được nhờ kỷ luật full regression đã lập từ Ver 5.1**. Vá: mở rộng
gate thành `outline_id in ('outline_may_bien_ap', 'outline_vo_may_bien_ap')`.
Lỗi này KHÔNG ảnh hưởng nội dung hiển thị thật (đã chủ động loại
`cap_dien_ap` khỏi `cot_ai`/`cot_bang` của outline vỏ từ Ver 5.2, field
buggy này chưa từng được hiện ra) — nhưng vẫn vá đúng ở tầng dữ liệu, tránh
để lại nợ kỹ thuật cho các tính năng dùng field này sau này.

Đã chạy lại ĐỦ 30 file test sau khi vá, đếm chính xác số dòng `[FAIL]`
(không dựa vào dòng tổng kết cuối — cách cũ suýt khiến lỗi này lọt qua vì
đọc nhầm dòng tổng kết của 1 file khác) — xác nhận **0 FAIL thật** trên
toàn bộ.

### File mới

`tests/test_v53_patch.py` (30 test: B5/B6 bằng mock thật xác nhận đúng số
lần gọi AI, C6-C10 đủ điều kiện hiện/ẩn đúng, wiring thật vào
`dung_bai_html`).

### Không làm (Giai đoạn 2-3, chờ input Thịnh — xem đề xuất)

- Gate CONFIRMED/CAN_KIEM (A1) — cần thiết kế UI riêng, việc quan trọng
  nhất còn lại trước khi scale.
- Schema sống (B7) — chờ tên meta key Rank Math thật.
- Box "Cam kết & Chứng nhận" (C13) — chờ Thịnh xác nhận có chính sách bảo
  hành/CO-CQ CHUNG hay không.
- Nội dung PDF/ảnh thật (C10 nội dung, C11) — chỉ Thịnh làm được.
