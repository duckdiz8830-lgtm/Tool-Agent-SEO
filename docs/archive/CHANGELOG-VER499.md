# CHANGELOG-VER499.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER498.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 4.9.9 CLAUDE — Chống trùng lặp SEO (Delta Context) + CSS inline + Title SKU-first — 29/07/2026

### Bối cảnh

Thịnh đăng thật 2 bài (KPK160CU, KPK180CU), đưa cho Gemini review SEO độc
lập. Kết luận: cấu trúc kỹ thuật tốt nhưng nội dung trùng lặp ~85% giữa
các SKU cùng dòng (chỉ đổi số công suất/mã hàng) + khối "về máy biến áp
nói chung" chép y nguyên 100% → rủi ro thật: Google Helpful Content System
đánh giá thấp Site-wide Quality khi nhiều URL có tỷ lệ text lặp lại cao,
dù mỗi trang riêng lẻ không cạnh tranh từ khoá với nhau (khách B2B search
đúng mã hàng, không phải từ khoá chung). Đã bàn kỹ với Thịnh, có phản biện
2 đề xuất của Gemini bị đánh giá là rủi ro bịa số (xem mục 3, 7).

### 1. CSS chuyển sang INLINE — không phụ thuộc thao tác tay

Thịnh không rành CSS, không muốn phải dán file CSS vào Theme. Toàn bộ khối
code-dựng (Hero, bảng thông số, CTA, bảng so sánh, khối chung, khối
thương hiệu, sản phẩm liên quan) chuyển từ `class="..."` sang
`style="..."` ngay trên từng thẻ — tool tự lo hết, không cần Thịnh làm gì.
Bảng style tập trung ở `ST = {...}` đầu `render_phase2.py`, dễ đổi màu
sau này (sửa 1 chỗ, áp dụng mọi hàm).

**Rủi ro cần Thịnh xác nhận qua thực tế:** WordPress lọc nội dung
(`wp_kses`) khi lưu qua REST API — thuộc tính `style` KHÔNG bị chặn hoàn
toàn như thẻ `<script>`/`<style>`, nhưng WordPress giới hạn property CSS
được phép qua filter `safe_style_css` (background/color/border/padding/
margin/font*/display... thường được phép; property hiếm/mới có thể bị
lọc tuỳ phiên bản WP). Chưa kiểm chứng 100% trên site thật — nếu style bị
mất 1 phần, layout xấu đi nhưng KHÔNG lộ chữ như bug script cũ (khác hẳn
mức độ nghiêm trọng).

### 2. Bỏ hẳn prefix "lotech-" — không để lại dấu vết tool/domain

Thịnh lo ngại dùng tool cho site khác sẽ để lại "chữ ký" nhận diện được.
Vì đã chuyển CSS sang inline (mục 1), class không còn cần thiết để "móc"
CSS ngoài vào nữa — bỏ HẲN mọi class `lotech-*`/`btn-*`/`specs-table`.
CHỈ giữ `id="lien-he-bao-gia"` (chức năng thật — đích neo nút "Yêu cầu báo
giá", không phải thẩm mỹ, tên tiếng Việt thường, không lộ tool nào).

### 3. Delta Context — chống trùng lặp giữa SKU cùng dòng

Theo đề xuất Gemini (đã phản biện, giữ phần dùng số thật, bỏ phần bịa số
— xem mục 7): tính bằng CODE (không để AI tự tính, tránh Hard Block chặn
nhầm số AI tự suy ra + tránh AI tự bịa):

- `tier_cong_suat` — phân khúc nhỏ (<250kVA) / trung (250-1000kVA) / lớn
  (>1000kVA).
- `sku_lien_ke_nho`/`sku_lien_ke_lon` — mã SKU liền kề gần nhất trong
  cùng dòng (từ `db_phase2.tim_san_pham_cung_dong`, đã có từ Ver 4.9.8).
- `chenh_lech_nho`/`chenh_lech_lon` — chênh lệch kVA + % so với mã liền
  kề, tính bằng phép chia đơn giản trên số thật.
- `tai_uoc_tinh` — ước tính dải tải kW, LUÔN kèm chú thích
  "(ước tính, giả định cosφ=0.8)" — KHÔNG được phép hiện như số đo thật.

Toàn bộ field trên đăng ký vào `PROFILES['may_bien_ap_do_luong']['cot_ai']`
VÀ `OUTLINES['outline_may_bien_ap']['cot_ai']` (profiles.py) — bắt buộc để
Hard Block (`_kho_cua_dong`/`_kho_mo_rong_cua_dong`, render_phase2.py)
nhận các số này là "có nguồn thật", không chặn nhầm.

**Test xác nhận cơ chế an toàn (quan trọng nhất bản này):** Hard Block
CHẤP NHẬN khi AI viết lại đúng số trong delta context, nhưng VẪN CHẶN nếu
AI tự thêm số % không có trong delta context (VD "tiết kiệm 15% chi phí")
— xem `test_v499_patch.py::V3-07`/`V3-08`.

Row được gộp delta context TRƯỚC khi gọi AI (không phải sau) — sửa cả 3
điểm gọi AI trong `giao-dien.py` (batch record, batch job, preview) để
tính `cung_dong`/delta context trước `goi_ai_co_du_phong()`/`goi_ai_mock()`
thay vì sau như Ver 4.9.8 (lúc đó chỉ dùng cho bảng hiển thị, chưa đưa vào
prompt AI).

Guidance prompt (`prompts_phase2.py::OUTLINE_NOI_DUNG['outline_may_bien_ap']`)
yêu cầu AI PHẢI dùng delta context để giải thích lý do chọn mức công suất
này thay vì mã liền kề — đúng khuyến nghị Gemini, nhưng bổ sung rào chắn:
cấm AI tự đưa số tiết kiệm chi phí (%, VNĐ) vì Lotech không công khai giá.

### 4. Boilerplate rút gọn — chống Site-wide Quality thấp

Khối "về máy biến áp [dầu/khô] nói chung" trước đây ~150 từ, chép y
nguyên 100% giữa mọi SKU cùng loại. Rút còn 1 CÂU NGẮN (~28 từ, test xác
nhận dưới 40 từ) nêu đúng nguyên lý làm mát + tiêu chuẩn áp dụng, vẫn phân
biệt rạch ròi dầu/khô. Pillar page riêng (kiến thức đầy đủ, theo đề xuất
Gemini) CHƯA được viết — xem mục "Chưa làm".

### 5. Title/H1 SKU-first — CODE dựng, không phụ thuộc AI

Trước đây title lấy từ `ai_data['meta_title']` (AI tự do, không đảm bảo
đúng định dạng mỗi lần). Giờ với `outline_may_bien_ap`, dùng
`dung_tieu_de(row)` — công thức cố định: `Máy biến áp [Dầu/Khô]
[Thương hiệu] [Công suất]kVA [Mã hàng] ([Đặc tính lõi nếu nhận diện
được])`. KHÔNG có ngày/tháng (Thịnh xác nhận bỏ — gắn cứng ngày sẽ cũ dần,
tool chưa có cơ chế tự làm mới định kỳ). Outline khác GIỮ NGUYÊN hành vi
cũ (AI's meta_title) — chưa mở rộng công thức này ra ngoài phạm vi đã
duyệt.

### 6. Khối "Về thương hiệu" — data catalogue THẬT, không bịa

`THONG_TIN_THUONG_HIEU` — chỉ 2 brand đã có catalogue/hồ sơ năng lực THẬT
đọc qua trước đó (MBT, THIBIDI — nhà máy, ISO, dây chuyền sản xuất, năm
hợp tác công nghệ). Brand khác (KP/Hàn Quốc và mọi brand chưa có nguồn) —
`khoi_ve_thuong_hieu()` trả rỗng, KHÔNG suy đoán/bịa thông tin công ty.

### 7. Đã CÂN NHẮC rồi KHÔNG làm — phản biện đề xuất Gemini

- **"Ép AI nhặt ≥2 từ trong danh sách từ vựng theo tier" (Semantic
  Keywords/LSI)** — Google đã công khai phủ nhận LSI keywords là cách họ
  đánh giá nội dung; ép quota từ khoá là dấu hiệu "viết cho máy đọc" mà
  chính Helpful Content System nhắm tới hạ điểm. Thay bằng rule 11
  (QUY_TAC_CHUNG, prompts_phase2.py) — gợi ý MỀM dùng từ đồng nghĩa tự
  nhiên khi phù hợp, KHÔNG bắt buộc.
- **"Tăng công suất đỉnh (AF) lên tới 30-40%"** — con số Gemini tự đặt ra,
  không có nguồn nào xác nhận cho brand/dòng nào đang bán. Chỉ giữ khái
  niệm AN/AF (thật, có trong kiến thức ngành), bỏ hẳn con số %.
- **"Tiết kiệm 10-15% chi phí so với mua mã lớn hơn"** — bịa hoàn toàn,
  `gia_list` là field cấm tuyệt đối, AI chưa từng thấy giá. Đã chặn rõ
  trong guidance prompt.
- **"Gộp trang, chọn biến thể bằng JS" (variable product)** — đổi hẳn
  kiến trúc (từ SKU độc lập sang 1 sản phẩm nhiều biến thể), rủi ro cao,
  không đáng làm khi mới có 22 bài thật. Giữ mô hình hiện tại.

### File sửa

`render_phase2.py` (style INLINE cho mọi khối code-dựng, bỏ prefix
"lotech-", `tinh_delta_context`/`dung_tieu_de`/`khoi_ve_thuong_hieu` mới,
`khoi_chung_may_bien_ap` rút gọn, `dung_bai_html` wire brand block + title
SKU-first), `profiles.py` (6 field delta-context vào cot_ai của profile
VÀ outline), `prompts_phase2.py` (nhãn field mới, guidance dùng delta
context, rule 11 từ đồng nghĩa mềm), `giao-dien.py` (tính delta context
TRƯỚC khi gọi AI ở cả 3 điểm gọi, đổi tiêu đề bản), `test_round2_integration.py`
+ `test_v497_patch.py` + `test_v498_patch.py` (cập nhật theo hành vi mới,
có giải thích rõ lý do, không âm thầm nới lỏng).

### File mới

`test_v499_patch.py` (31 test: CSS inline, không còn "lotech-", delta
context tính đúng + Hard Block chấp nhận số thật/vẫn chặn số bịa —
**test quan trọng nhất bản này**, boilerplate dưới 40 từ, title SKU-first
không ngày tháng, brand block đúng/an toàn, regression 2 profile khác).

### Không làm

- **Pillar page** (kiến thức đầy đủ dầu/khô) — CHƯA viết, khối chung mới
  chỉ rút gọn chứ chưa có link về pillar (URL chưa tồn tại). Khi có bài
  thật, chỉ cần thêm `href` vào `khoi_chung_may_bien_ap()`, không cần sửa
  gì khác.
- **Cơ chế Hard Block fail → nhảy sản phẩm tiếp theo** (tiết kiệm quota
  request) — đã bàn từ Ver 4.9.8, chưa được xác nhận lại trong phiên này,
  chưa code.
- **Meta title/SEO title riêng cho Rank Math** — hiện chỉ có 1 field
  "title" (post title, thường = H1 theo theme). Rank Math có field SEO
  Title/Description RIÊNG (post meta) chưa được tool wire tới — cần xác
  nhận tên meta key thật trước khi code (giống vụ Schema Ver 4.9.6, không
  đoán mù).
- Chưa mở rộng title SKU-first ra ngoài `outline_may_bien_ap`.
