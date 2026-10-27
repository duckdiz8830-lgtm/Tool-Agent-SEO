# CHANGELOG-VER49.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER48.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 4.9 CLAUDE — Vá tận gốc trùng SKU + FAQ droppable — 28/07/2026

### 1. Vá TẬN GỐC lỗi trùng SKU (không còn phòng thủ mò)

Xác nhận bằng tài liệu chính thức WooCommerce REST API v3: tham số
`status` mặc định là **`publish`**. Hàm tra SKU trước khi tạo sản phẩm
trước đây KHÔNG chỉ định `status` — nghĩa là chỉ tìm trong sản phẩm đã
publish, bỏ sót hoàn toàn sản phẩm ở trạng thái **draft** (chính trạng
thái MỌI sản phẩm tool này tạo ra, vì luôn ép cứng draft) — tự tool tạo
bài xong không tìm lại được chính bài mình vừa tạo.

`tim_san_pham_woo_theo_sku()`/`tim_san_pham_woo_theo_slug()` giờ mặc định
gửi `status='any'` (bao trùm draft/publish/pending/private).

**Trường hợp còn lại — sản phẩm trong THÙNG RÁC:** Thịnh gửi ảnh chụp thật
xác nhận: sản phẩm trùng SKU đang ở `post_status=trash`. Theo đúng ngữ
nghĩa WordPress lõi, `status='any'` KHÔNG bao gồm `trash` — hành vi này
không phải do tool chọn, là quy ước gốc của WordPress. Thêm bước kiểm tra
riêng `status='trash'` khi vẫn không tìm thấy sau `status='any'`: nếu tìm
ra, **báo lỗi rõ ràng nói đúng vấn đề** (SKU bị giữ bởi sản phẩm trong
thùng rác, ID cụ thể, cần vào WordPress Admin xoá vĩnh viễn) — **KHÔNG tự
động khôi phục hay xoá vĩnh viễn** dữ liệu, đây là quyết định của Thịnh.

### 2. FAQ trở thành "field có thể bỏ" thay vì chặn cả bài

Bằng chứng thật: lỗi FAQ dài bất thường xảy ra ở **2 model hoàn toàn khác
nhau** (gemini-3.6-flash và gemini-3.1-flash-lite) — xác nhận đây không
phải lỗi riêng 1 model, sửa prompt cũng không đủ mạnh. Đổi chiến lược:

`goi_ai_co_du_phong()` — nếu TOÀN BỘ vi phạm Hard Block chỉ nằm trong
`faq[...]` (không đụng field cốt lõi nào), tự động bỏ mảng FAQ và coi là
THÀNH CÔNG ngay (không cần đổi cặp key/model). Bài vẫn đăng đầy đủ mọi
phần khác — chỉ thiếu khối FAQ (vốn là phần phụ theo thiết kế outline).

**Có test đối chứng bắt buộc:** nếu vi phạm CÓ dính tới field cốt lõi
(không chỉ FAQ), tuyệt đối KHÔNG được tự ý bỏ qua — vẫn xử lý như lỗi
thật, vẫn thử đổi cặp key/model như trước.

### File sửa

`autopost.py` (thêm `status='any'`/`trang_thai` param), `ai_wp_adapter.py`
(phát hiện trash + báo rõ; FAQ droppable trong `goi_ai_co_du_phong`),
`giao-dien.py` (log khi FAQ bị bỏ, tiêu đề "VER 4.9 Claude"),
`test_v47.py` (cập nhật kịch bản DP-3 dùng lỗi field cốt lõi thay vì FAQ,
vì FAQ giờ tự phục hồi không cần đổi model).

### File mới

`test_v49.py` (9 test: status=any mặc định đúng, phát hiện trash báo rõ
không tự sửa dữ liệu, FAQ-droppable giữ nguyên nội dung khác, đối chứng
không tự ý bỏ qua khi lỗi ở field cốt lõi).

### Không làm

- Không tự động xử lý sản phẩm trong thùng rác WooCommerce — quyết định
  của Thịnh, tool chỉ báo rõ vấn đề.
- Chưa giải quyết được HTTP 503 "high demand" từ Google — lỗi tạm thời
  phía server Google, ngoài khả năng kiểm soát của code.
