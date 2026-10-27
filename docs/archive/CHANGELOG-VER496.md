# CHANGELOG-VER496.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER495.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 4.9.6 CLAUDE — Vá 4 lỗi phát hiện từ ảnh chụp production thật — 29/07/2026

Toàn bộ mục dưới đây xuất phát từ Thịnh gửi ảnh chụp thật trang preview
`maybienapvn.vn` (sản phẩm MBT3P250A2608, 29/07/2026) — không phải suy đoán.

### 1. BUG THẬT — Schema JSON-LD hiện ra thành chữ trên trang

**Hiện tượng (ảnh chụp):** nguyên khối JSON `{"@context": "https://schema.org", ...}`
hiện ra như VĂN BẢN THƯỜNG ngay dưới mục "Liên hệ báo giá", khách nhìn thấy
được.

**Gốc rễ (đọc code thật + đối chiếu tài liệu WordPress):**
`dung_bai_html()` (render_phase2.py) build đúng chuỗi
`<script type="application/ld+json">...</script>` — bản thân hàm này KHÔNG
sai. Nhưng chuỗi này bị nhét CHUNG vào field `description` gửi qua
WooCommerce REST API (`ai_wp_adapter.py::dang_woo_that`). WordPress lọc nội
dung post (`wp_kses`) không cho phép thẻ `<script>` — kses XOÁ CẶP THẺ
nhưng GIỮ NGUYÊN text bên trong, nên toàn bộ JSON hiện ra thành chữ. Nhét
`<script>` vào `post_content`/`description` qua REST API KHÔNG BAO GIỜ sống
sót trừ khi tài khoản gọi API có quyền `unfiltered_html` — không kiểm chứng
được từ code, phụ thuộc cấu hình WordPress phía Thịnh.

**Vá:** `dung_bai_html()` KHÔNG còn nhét schema vào `html` nữa. Trả riêng
qua key `schema` (dict) để nơi gọi tự quyết định đường đi an toàn hơn sau
này (VD custom field cho Rank Math đọc — plugin đã cài sẵn theo ảnh chụp,
nhưng cần xác nhận tên meta key thật trước khi code tiếp, không đoán mù).
Trước mắt: KHÔNG có Product Schema nào được đăng — còn hơn đăng JSON lộ ra
thành chữ như hiện tại.

**Đã kiểm tra kỹ trước khi merge:** không đụng lại quyết định "không có
Offer/giá" (khác với vụ schema này — 2 vấn đề độc lập, xem CHANGELOG-VER495).

### 2. Bỏ khối "Thông tin cần cung cấp để nhận báo giá"

Thịnh xác nhận LẦN THỨ HAI (đã nhắc ở phiên trước, bị miss — ghi rõ vào
code lần này để không lặp lại): khối checklist rào cản làm khách ngại điền,
giảm lead thay vì tăng. `khoi_checklist_bao_gia()` GIỮ NGUYÊN định nghĩa
(không xoá code, phòng cần dùng dạng khác sau), chỉ KHÔNG GỌI trong
`dung_bai_html()` nữa.

### 3. Content "Hướng dẫn lựa chọn" đọc như mẫu soạn sẵn

Ví dụ thật Thịnh trích: *"Quý khách vui lòng gửi bản vẽ thiết kế hoặc
thông số công trình để được tư vấn chính xác mã sản phẩm MBT3P250A2608."*
— câu này bắt nguồn từ `QUY_TAC_CHUNG` quy tắc #10 (`prompts_phase2.py`),
trước đây CHỈ ĐỘNG VIÊN "gợi ý khách gửi bản vẽ", AI hiểu thành công thức
cố định, lặp lại gần như y hệt cho nhiều sản phẩm.

**Vá:** viết lại quy tắc #10 — yêu cầu VIẾT TỰ NHIÊN như người tư vấn thực
tế (ứng dụng/công trình phù hợp, tiêu chí kỹ thuật, điểm mạnh), CẤM RÕ công
thức "Quý khách vui lòng gửi bản vẽ... để được tư vấn chính xác mã sản
phẩm [mã hàng]" lặp lại y hệt. Áp dụng cho MỌI outline (rule nằm trong
`QUY_TAC_CHUNG`, dùng chung).

### 4. Slug không cắn từ khoá SEO

Trước đây: `slug = f'{ma_slug}-{mau_slug}'` → `mbt3p250a2608-chuan` — không
có 1 từ khoá SEO nào trong URL, đi ngược mục tiêu SEO cơ bản nhất.

**Vá:** `dung_slug()` giờ ghép tiêu đề sản phẩm (rút gọn an toàn, không cắt
giữa từ, bỏ dấu) + mã hàng (giữ để đảm bảo duy nhất tuyệt đối) + mẫu. VD:
`may-bien-ap-dau-3pha-250kva-22-0-4kv-loai-amorphous-kieu-kin-mbt3p250a2608-chuan`.
Tái dùng `dulieu.slugify()`/`khong_dau()` đã có sẵn (không viết lại logic
bỏ dấu tiếng Việt).

**An toàn ngược — QUAN TRỌNG:** đổi công thức slug sẽ đổi slug của MỌI bài
sinh MỚI, nhưng nếu code cũ resend slug khi UPDATE bài ĐÃ ĐĂNG THẬT (15 sản
phẩm đã đăng qua Ver 4.9), URL sống đã index/backlink sẽ bị đổi theo — phá
SEO thay vì giúp. Đã vá riêng (xem mục 5) để chặn việc này.

### 5. An toàn ngược: không đổi slug bài đã đăng khi update

`dang_woo_that()`/`dang_wp_that()` (ai_wp_adapter.py) trước đây LUÔN gửi
`slug` trong mọi request, kể cả UPDATE (PUT) bài đã có `wp_id`. Giờ CHỈ gán
`goi['slug']` khi thật sự đang TẠO MỚI (`da_co is None`) — bài đã có giữ
nguyên slug cũ.

**Rủi ro còn lại, CHỈ THỊNH XÁC NHẬN ĐƯỢC:** `dang_wp_that()` (luồng
WordPress Post thường, không phải Woo) dùng slug làm 1 phần cơ chế tra bài
đã đăng (`tim_bai_theo_slug`) khi chưa biết `wp_id`. Nếu site nào đã đăng
bài TRƯỚC Ver 4.9.6 bằng luồng này (slug kiểu cũ), sinh lại bằng bản mới sẽ
tra theo slug MỚI — không tìm thấy bài cũ — có thể tạo bài trùng thay vì
update. Luồng WooCommerce (`dang_woo_that`) AN TOÀN hơn vì tra theo SKU
trước, ít rủi ro này hơn. Thịnh cần tự kiểm tra thủ công nếu có site nào
dùng luồng WordPress Post thường và đã đăng bài trước bản này.

### File sửa

`render_phase2.py` (bỏ schema khỏi html, trả qua key `schema`; bỏ gọi
`khoi_checklist_bao_gia`; `dung_slug()` viết lại), `prompts_phase2.py`
(`QUY_TAC_CHUNG` quy tắc #10), `ai_wp_adapter.py` (`dang_woo_that`,
`dang_wp_that` — chỉ gửi slug khi tạo mới), `giao-dien.py` (đổi tiêu đề
bản), `test_gate2.py` (cập nhật D1 theo hành vi schema mới, có giải thích
rõ lý do đổi, không âm thầm nới lỏng test).

### File mới

`test_v496_patch.py` (14 test: schema không lộ ra html, checklist đã bỏ,
rule content không còn công thức cứng, slug có từ khoá + vẫn duy nhất + an
toàn khi thiếu tên, ai_wp_adapter không resend slug khi update).

### Không làm

- Chưa wire schema vào Rank Math custom field — cần xác nhận tên meta key
  thật trước, không đoán mù (xem mục 1).
- Chưa tự động rà 15 sản phẩm đã đăng trước bản này xem có bị trùng do đổi
  slug hay không — Thịnh tự kiểm tra (xem mục 5).
- Chưa đụng RM6/SM6 Schneider — vẫn để đợt riêng.
