# CHANGELOG-VER498.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER497.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 4.9.8 CLAUDE — CTA đồng bộ + So sánh công suất + CSS giao diện — 29/07/2026

Theo phản hồi Thịnh trên demo HTML "ultra" (29/07/2026): giao diện đẹp/gọn
gàng cũng là uy tín, CTA phải đồng bộ, tăng thêm chiều sâu content bằng
bảng so sánh công suất trong dòng, gộp "2 góc nhìn" thành 1 đoạn tự nhiên.

### 1. CSS giao diện — dán 1 lần vào Theme, KHÔNG nhét vào từng bài

Cân nhắc kỹ trước khi làm: nhét `<style>` vào `description` mỗi bài sẽ dính
ĐÚNG bug đã vá ở Ver 4.9.6 (WordPress kses xử lý `<style>` giống
`<script>` — xoá thẻ, giữ text, lộ CSS thành chữ trên trang). Thay vào đó:
toàn bộ HTML do tool sinh đã dùng sẵn class `lotech-*`/`specs-table`/
`btn-*` nhất quán — chỉ cần dán **1 lần duy nhất** file `lotech-theme.css`
(gửi kèm) vào WordPress > Giao diện > Tùy biến > CSS bổ sung, áp dụng cho
MỌI bài sinh sau đó, không phải làm lại mỗi bài.

Thêm class bọc còn thiếu để CSS áp đúng chỗ: `khoi_chung_may_bien_ap()`
giờ bọc trong `<div class="lotech-khoi-chung">`.

### 2. CTA cuối trang đồng bộ với CTA gọn

Trước đây `khoi_cta()` (CTA đầy đủ cuối trang) là ĐOẠN VĂN XUÔI ("Gọi ngay
0900... hoặc Zalo...") khác hẳn kiểu 3 NÚT bấm của `khoi_cta_ngan()` ở
Hero/sau bảng thông số — không đồng bộ thị giác. Viết lại dùng ĐÚNG class
nút đã có (`btn-goi`/`btn-zalo`), bọc trong `<div class="lotech-cta-cuoi">`
để CSS tô nền khác biệt, nổi bật hơn CTA gọn giữa bài. `id="lien-he-bao-gia"`
(đích neo nút "Yêu cầu báo giá") GIỮ NGUYÊN, không đổi — đã test riêng
không phá anchor.

### 3. Bảng so sánh công suất trong dòng — CODE dựng, không qua AI

`db_phase2.py::tim_san_pham_cung_dong()` — tìm các SKU máy biến áp CÙNG
DÒNG (so khớp Tên hàng sau khi bỏ số công suất), khác mức công suất, trong
CÙNG dataset. Không cần các SKU kia đã đăng bài (khác `tim_san_pham_lien_quan`
— đây là bảng dữ liệu tham khảo, không phải link).

`render_phase2.py::khoi_so_sanh_cong_suat()` — dựng bảng từ kết quả trên,
100% CODE, không qua AI (tránh rủi ro AI lẫn số khi so sánh nhiều SKU cùng
lúc). Rỗng nếu không có SKU anh em nào (không đáng làm bảng chỉ 1 dòng).

**Phát hiện phụ khi build (không phải bug do tool gây ra):** cột "Cấp Điện
Áp (kV)" trong MASTER bị lỗi dữ liệu ở nhiều dòng máy biến áp — giá trị
trùng với công suất (VD dòng 100kVA lại ghi cấp điện áp "100 kV" thay vì
"22/0.4"). Bảng so sánh (nhiều dòng cạnh nhau) sẽ lộ lỗi này rất rõ, nên
**cố tình ẩn cột Cấp điện áp khỏi bảng so sánh** cho tới khi Thịnh xác nhận
sửa lại cột này trong MASTER. Bảng thông số chính (1 dòng) vẫn hiện field
này như cũ — chưa đụng, vì đây là quyết định dữ liệu, không phải bug code.

Đã wire vào cả 3 điểm gọi `dung_bai_html()` trong `giao-dien.py` (batch
đăng draft, batch theo Article Jobs, chạy thử preview).

### 4. Gộp "2 góc nhìn" (kỹ sư/đầu tư) thành 1 đoạn — không tách khối

Bản demo trước tách 2 card hiển thị riêng. Thịnh xác nhận: giữ Ý TƯỞNG
(lồng cả 2 khía cạnh) nhưng KHÔNG tách khối — viết như 1 đoạn "Đặc điểm"
liền mạch. Sửa guidance `dac_diem_html` của `outline_may_bien_ap`
(`prompts_phase2.py`) yêu cầu AI lồng ghép tự nhiên cả khía cạnh kỹ thuật
lẫn khía cạnh vận hành/đầu tư trong CÙNG 1 đoạn văn, không tách tiêu đề
phụ. Không đổi giới hạn độ dài (vẫn 80-150 từ, dùng chung mọi outline).

### File sửa

`render_phase2.py` (`khoi_cta` viết lại, `khoi_so_sanh_cong_suat` mới,
`khoi_chung_may_bien_ap` bọc class, `dung_bai_html` thêm tham số
`cung_dong`), `db_phase2.py` (`tim_san_pham_cung_dong`, `_ho_may_bien_ap`,
`_so_kva` mới), `prompts_phase2.py` (guidance `dac_diem_html` outline máy
biến áp), `giao-dien.py` (wire `cung_dong` vào 3 điểm gọi, đổi tiêu đề bản).

### File mới

`test_v498_patch.py` (17 test: CTA đồng bộ + giữ anchor, bảng so sánh
đúng/an toàn khi rỗng/ẩn đúng cột lỗi, wiring thật, prompt gộp góc nhìn
không mất rule cũ), `lotech-theme.css` (CSS dán vào Theme, không phải file
code Python).

### Không làm

- Chưa sửa cột "Cấp Điện Áp (kV)" bị lỗi trong MASTER — quyết định dữ liệu
  của Thịnh, tool chỉ ẩn field lỗi khỏi bảng so sánh mới, chưa đụng field
  cũ ở bảng thông số chính.
- Chưa thêm AI-written "nhận định nên chọn mức nào" bên cạnh bảng so sánh
  (bản demo có, bản thật này chỉ có bảng code thuần) — cần thêm field mới
  vào outline/schema/Hard Block, để đợt sau nếu Thịnh muốn.
- Cơ chế "Hard Block fail thì nhảy sản phẩm tiếp theo thay vì đốt cặp dự
  phòng" đã bàn nhưng CHƯA code — chờ xác nhận riêng.
