# CHANGELOG-VER495.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER49.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 4.9.5 CLAUDE — Profile đầu cáp/hộp nối enrich catalogue — 29/07/2026

### 1. Bối cảnh

Đợt enrich MASTER bằng catalogue nhà sản xuất thật (ABB/3M, đầu cáp/hộp nối
co nguội/co nhiệt 24kV) đã ra 90 SKU có 6 field kỹ thuật thật (đường kính
cách điện áp dụng, kích thước lắp đặt I/L, chiều dài đường rò ngoài trời,
tiêu chuẩn áp dụng, kết quả test điện). Trước bản vá này, `profiles.py`
(Phase 2 Lite) chưa khai báo 6 field đó cho profile `phu_kien_va_khac` —
dữ liệu enrich nằm sẵn trong Excel nhưng KHÔNG lọt vào prompt AI hay bảng
thông số, vì kiến trúc chỉ đọc field đã khai báo trong `cot_import`.

### 2. Phát hiện + vá TRƯỚC khi thêm field (đọc code thật, không đoán mù)

`_doc_sheet_theo_header()` (`nhap_phase2.py`) coi TOÀN BỘ field trong
`cot_import` của 1 profile là bắt buộc — thiếu 1 cột trong Excel là
`RuntimeError`, dừng cả sheet. Nếu thêm thẳng 6 cột enrich vào `cot_import`
mà không sửa gì thêm, bất kỳ ai import bản MASTER GỐC (chưa enrich, không
có 6 cột này) sẽ bị crash toàn bộ profile `phu_kien_va_khac` — hồi quy
nghiêm trọng, phát hiện được TRƯỚC khi merge nhờ viết test thử với cả 2
loại file.

**Vá:** tách `cot_bat_buoc` (list cột Excel bắt buộc phải có) ra khỏi
`cot_import` (list cột được PHÉP đọc nếu có mặt). `_doc_sheet_theo_header()`
nhận thêm tham số `cot_bat_buoc` (mặc định `None` = toàn bộ `cot_import`,
giữ nguyên hành vi cũ cho 3 profile chưa khai báo field optional — không
đổi 1 dòng hành vi nào ở `cap_dien`/`tu_va_thiet_bi_dong_cat`/
`may_bien_ap_do_luong`). Cột thiếu trong Excel không nằm trong
`cot_bat_buoc` → field tương ứng chỉ trống, không crash.

### 3. Profile `phu_kien_va_khac` — 6 field enrich + 1 field nội bộ

`cot_import` thêm: `duong_kinh_cach_dien`, `kich_thuoc_i`, `kich_thuoc_l`,
`duong_ro_ngoai_troi`, `tieu_chuan_catalogue`, `test_dien` (vào `cot_ai` +
`cot_bang`) và `nguon_catalogue` (chỉ vào `cot_noi_bo` — dùng để routing,
KHÔNG BAO GIỜ ra prompt/bảng/schema, đúng nguyên tắc field nội bộ của kiến
trúc gốc).

### 4. Outline mới `outline_dau_cap_ky_thuat`

Tách riêng khỏi `outline_phu_kien` vì field kỹ thuật (đường kính cách điện,
kích thước lắp) không có ý nghĩa cho phụ kiện khác (cosse, băng keo...) —
đúng nguyên tắc outline giới hạn field theo ngữ nghĩa sản phẩm, không phải
theo profile. Routing (`xac_dinh_outline_id`): SKU có `nguon_catalogue`
(đã enrich thật) → `outline_dau_cap_ky_thuat`; SKU khác (kể cả MASTER
không có 6 cột này) → `outline_phu_kien` như cũ, không đổi.

`prompts_phase2.py::OUTLINE_NOI_DUNG` thêm cấu trúc nội dung riêng cho
outline mới (intro/đặc điểm/ứng dụng/hướng dẫn chọn theo đúng field kỹ
thuật thật, có FAQ). `render_phase2.py::NHAN_COT` + `prompts_phase2.py`
`nhan_cot` thêm nhãn hiển thị cho 6 field.

### 5. Đã xét và KHÔNG đổi: Product Schema thiếu `offers`

Rà lại yêu cầu "fix schema đang lỗi" — thử thêm `offers` (availability,
không price) vào `dung_schema()` để thoả điều kiện Google Rich Results.
Trước khi merge, chạy `test_gate2.py` phát hiện test `D1` đã khẳng định rõ
"không có Offer hoặc giá" là **quyết định có chủ đích** từ vòng duyệt
trước — Offer theo schema.org bắt buộc có `price`/`priceSpecification`, mà
Lotech không công khai giá list, nên Offer thiếu giá còn sai chuẩn hơn
không có Offer. **Đã revert**, giữ nguyên hành vi cũ, không tự ý đổi quyết
định đã chốt chỉ vì đoán. Nếu Thịnh có bằng chứng cụ thể (ảnh chụp Search
Console/Rich Results báo lỗi khác) thì cung cấp để xử lý đúng chỗ.

### File sửa

`nhap_phase2.py` (`_doc_sheet_theo_header` thêm tham số `cot_bat_buoc`,
`import_4_profile` truyền tham số mới), `profiles.py` (6 field + 1 field
nội bộ trong `phu_kien_va_khac`, outline `outline_dau_cap_ky_thuat`, routing
`xac_dinh_outline_id`), `prompts_phase2.py` (`OUTLINE_NOI_DUNG` + nhãn field
mới), `render_phase2.py` (`NHAN_COT` thêm nhãn field mới).

### File mới

`test_v495_patch.py` (21 test: registry đúng field/field cấm, import KHÔNG
crash MASTER gốc, routing đúng 90/90 SKU enrich, prompt/bảng/schema đúng
field mới không lộ giá, regression 3 profile khác không đổi).

### Không làm

- Không đụng RM6/SM6 Schneider (71 SKU, hệ modular) — để đợt riêng.
- Không thêm `offers` vào Schema — xem mục 5, quyết định có chủ đích.
- Chưa build outline riêng cho nhóm elbow/T-Plug/chống sét (family khác,
  chưa enrich xong).
