# CHANGELOG-VER45.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER42.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 4.5 — Checklist báo giá + Sản phẩm liên quan — 26/07/2026

Gộp 2 hạng mục theo lộ trình rút gọn đã thống nhất (bỏ số 4.3/4.4 trung
gian, nhảy thẳng "4.5" theo yêu cầu tiết kiệm token) — không đụng Quality
Gate (dời xuống sau, chấm điểm cần có đủ nội dung để chấm) và Tài liệu kỹ
thuật (chờ dữ liệu catalogue thật, bàn riêng).

### Block 5 — Checklist yêu cầu báo giá

Rule tĩnh theo `profile_id`, KHÔNG phải AI viết, KHÔNG phụ thuộc dữ liệu
record — câu hỏi cố định áp dụng cho mọi sản phẩm cùng nhóm hàng
(`render_phase2.khoi_checklist_bao_gia()`, bảng `CHECKLIST_BAO_GIA`).
Profile chưa khai báo → block không hiện, an toàn.

### Block 6 — Sản phẩm liên quan

**Nguyên tắc quan trọng nhất (đúng chuẩn High-end Content đã chốt): CHỈ
link tới sản phẩm ĐÃ ĐĂNG THẬT** (`bai_viet_phase2.trang_thai='da_dang'`
và có `wp_url`) — tuyệt đối không bịa link tới sản phẩm chưa tồn tại trên
web.

Kiến trúc: `db_phase2.tim_san_pham_lien_quan()` tự truy vấn DB (cùng
`profile_id`, ưu tiên cùng cấp điện áp rồi cùng thương hiệu, loại chính
record đang xét), trả list `[{'ten', 'url'}]`.
`render_phase2.khoi_san_pham_lien_quan()` CHỈ dựng HTML từ danh sách đã
có sẵn — **không tự query DB** (giữ `render_phase2.py` không phụ thuộc DB,
đúng kiến trúc hiện có, dễ test độc lập như `bang_thong_so`/`khoi_cta`).

`dung_bai_html()` thêm tham số `san_pham_lien_quan=None` (mặc định
không truyền = không hiện block, 100% backward compatible).

### Nối vào cả 2 luồng đăng thật

- Ver 3.7 (batch theo record, tab 4): thêm `DB.tim_san_pham_lien_quan()`
  trước khi dựng bài.
- Ver 3.9 (Article Jobs, tab 7): tương tự.
- "Chạy thử" (Mock preview, tab 3): **không nối** — giữ nguyên, ngoài
  phạm vi yêu cầu (chỉ preview nhanh, không phải luồng đăng thật).

### File sửa

- `render_phase2.py` — thêm `khoi_checklist_bao_gia()`,
  `khoi_san_pham_lien_quan()`, nối vào `dung_bai_html()` giữa nội dung AI
  và FAQ.
- `db_phase2.py` — thêm `tim_san_pham_lien_quan()`.
- `giao-dien.py` — nối `DB.tim_san_pham_lien_quan()` vào 2 luồng đăng
  thật (Ver 3.7 batch + Ver 3.9 Article Jobs), chỉ đổi tiêu đề app.

### File mới

- `test_v45_checklist_lien_quan.py` — 16 test: checklist theo profile,
  HTML builder phòng thủ (item thiếu ten/url bị bỏ qua), DB query đúng —
  chỉ trả sản phẩm đã đăng thật, đúng profile, không trả chính nó, ưu tiên
  đúng thứ tự (cấp điện áp + thương hiệu), end-to-end qua `dung_bai_html()`.

### Không làm (đúng scope đã chốt)

- Quality Gate chấm điểm — để sau, cần có đủ nội dung (checklist + liên
  quan đã có ở bản này) mới chấm có ý nghĩa.
- Block Tài liệu kỹ thuật — chờ dữ liệu catalogue thật, bàn riêng vụ Excel.
- Không nối vào "Chạy thử" (Mock preview) — ngoài phạm vi yêu cầu.
