# CHANGELOG-VER46.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER45.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 4.6 CLAUDE — WooCommerce + Field-thiếu-là-FAILED + FAQ Quality + Token — 26/07/2026

Đặt tên "4.6 Claude" (file ZIP, tên thư mục, tiêu đề app) để phân biệt rõ
với nhánh "4.5.1 Ultra" do GPT tự code song song trong lúc gián đoạn —
kiến trúc KHÔNG kế thừa từ nhánh đó, code lại từ đầu trên nền 4.5.1 đã vá.

### Phần 1 — Hoàn thành Ver 4.5.1 (bị ngắt giữa chừng, làm nốt trước khi thêm gì mới)

5 điểm GPT review độc lập — xem chi tiết đầy đủ trong `CHANGELOG-VER45.md`
mục "cần vá": Article Jobs làm nguồn hợp lệ cho sản phẩm liên quan (P0),
lọc đúng theo site (P1), bỏ ứng viên điểm 0 + bắt buộc cùng content_type
(P1), vá anchor CTA chết `#lien-he-bao-gia` (P1), Hero hết lặp mã
hàng/thương hiệu (P2). Test: `test_v451_patch.py`, 13/13 PASS.

### Phần 2 — WooCommerce trở thành luồng đăng CHÍNH cho sản phẩm (theo từng site)

**Bối cảnh:** Lotech chuyển sang dùng Flatsome + WooCommerce cho giao diện
sản phẩm (UI/UX tốt hơn tự code), site đầu tiên: `maybienapvn.vn`. Chỉ đổi
NƠI đăng bài — không có price/cart/checkout (đã ẩn trên site), giữ nguyên
mô hình "Liên hệ báo giá".

- **Cấu hình theo từng site** (`cauhinh.py`): thêm `che_do_dang` ('post'
  mặc định hoặc 'woo_product'), dropdown mới trong tab "1. Cấu hình". Site
  cũ không set gì vẫn mặc định 'post' — không đổi hành vi 1 site nào đang
  chạy WordPress thường.
- **`dang_woo_that()`** (`ai_wp_adapter.py`) — bản WooCommerce của
  `dang_wp_that()`, copy nguyên kỷ luật chống đăng trùng học được từ Ver
  3.7.1 (không retry mù khi timeout mơ hồ — dò lại trước khi thử lại).
  Endpoint `/wc/v3/products`, auth Application Password y hệt WordPress
  (không cần Consumer Key/Secret riêng — chỉ cần tài khoản có quyền
  `manage_woocommerce`). Ép cứng `status=draft`, `type=simple`, KHÔNG set
  `regular_price`/`sale_price`.
- **Idempotent theo SKU** (`autopost.tim_san_pham_woo_theo_sku`) — SKU
  (mã hàng) đáng tin hơn slug vì duy nhất theo thiết kế MASTER; dự phòng
  theo slug nếu record không có mã hàng.
- **Nối vào vòng lặp đăng thật** (tab 4, Ver 3.7): branch theo
  `wc['che_do_dang']` — site nào chọn WooCommerce thì gọi `dang_woo_that`,
  site khác gọi `dang_wp_that` y hệt trước giờ. Article Jobs (tab 7)
  **KHÔNG đụng** — giữ nguyên `/wp/v2/posts`, để dành dùng cho từ
  khoá/blog sau này theo đúng định hướng nhân sự mới.

### Phần 3 — JSON hợp lệ nhưng thiếu field bắt buộc = FAILED

Trước đây Gemini trả JSON parse được nhưng THIẾU field (VD thiếu hẳn
`dac_diem_html`) vẫn được coi là thành công — bài ra mỏng hơn, không ai
biết. Giờ kiểm đủ field bắt buộc theo đúng schema đã gửi Gemini
(`responseSchema`), thiếu field nào là FAILED thẳng, không âm thầm đăng
bài cụt.

### Phần 4 — Validator chặn chuỗi rác/lặp trong FAQ (và mọi field văn xuôi khác)

`kiem_tra_chat_luong_text()` — kiểm CHẤT LƯỢNG văn bản (khác Hard Block
chống-bịa-số): ký tự lặp liên tiếp ≥10 lần, từ lặp liên tục ≥5 lần, độ dài
bất thường (áp dụng cho meta_title/meta_description/faq.q/faq.a — field
văn xuôi dài như `dac_diem_html` chỉ kiểm lặp, không giới hạn độ dài cố
định). Gộp chung vào `kiem_tra_bia_toan_bo()` — 1 điểm kiểm duy nhất, không
cần sửa gì thêm ở nơi gọi.

### Phần 5 — Tăng maxOutputTokens

8192 → 16000. Có `responseSchema` ép cấu trúc từ Ver 4.1 nên tăng trần
không làm bài lan man hơn, chỉ thêm đệm an toàn chống cắt giữa chừng.

### Sự cố trong lúc code (tự phát hiện, tự vá, ghi lại để minh bạch)

Lúc chèn `dang_woo_that()` vào file, lỡ tay xoá mất dòng khai báo
`def kiem_tra_ket_noi_wp():` — phát hiện ngay qua `test_that_mocked.py`
báo `AttributeError`, vá lại trong vòng vài phút trước khi tiếp tục. Không
phát hiện được nếu không chạy test ngay sau mỗi bước — đúng lý do vì sao
quy trình "test sau từng bước, không dồn cuối" quan trọng.

Check field-thiếu/FAQ-rác mới cũng làm vỡ 2 fixture test cũ dùng placeholder
quá ngắn (`'meta_title': 'T'`, `'meta_description': 'M'`) — đã sửa fixture
dùng độ dài thực tế thay vì nới lỏng validator.

### File sửa

`ai_wp_adapter.py`, `giao-dien.py`, `cauhinh.py`, `autopost.py`,
`render_phase2.py`, `db_phase2.py` (patch 4.5.1), `test_v37_1_patch.py`,
`test_v39_article_jobs.py`, `test_v42_hero_cta.py` (cập nhật fixture/assertion).

### File mới

`test_v451_patch.py` (13 test), `test_v46.py` (20 test: cấu hình
che_do_dang, WooCommerce tạo mới/idempotent/không-retry-mù, field-thiếu,
FAQ rác, token).

### Không làm (đúng scope đã chốt)

- Article Jobs — không đụng, giữ nguyên cho từ khoá/blog sau này.
- Quality Gate chấm điểm, Block Tài liệu kỹ thuật — vẫn để dành.
- Không xây tính năng xoay vòng nhiều API key — Thịnh nói để sau.
- Không đọc/kế thừa code nhánh "4.5.1 Ultra" (GPT tự làm) — kiến trúc độc lập.
