# CHANGELOG-VER51.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER50.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 5.1 CLAUDE — Audit lại toàn bộ tool + vá 4 lỗi thật + gọn thư mục — 30/07/2026

### Bối cảnh

Thịnh đưa 2 bài review độc lập (Gemini — content/SEO, GPT — kiến trúc/vận
hành) trên bản Ver 4.9.9. Trước khi tin theo, đã TỰ KIỂM CHỨNG LẠI từng
claim bằng cách chạy code/đếm data thật (không nghe kể) — kết quả:
`Audit-Checklist-Ver5.0.xlsx` (đã gửi Thịnh riêng, 22 mục, mỗi mục có bằng
chứng). Bản này vá 4 lỗi mức độ nghiêm trọng nhất từ audit đó.

### 0. Tự phát hiện lỗi quy trình của chính mình (trước khi vá gì khác)

Chạy lại TOÀN BỘ 28 file test cũ (trước giờ mỗi "full regression" chỉ chạy
1 tập con ~19 file, bỏ sót 9 file chưa từng đụng lại từ Ver 4.9.5) —
`test_v42_hero_cta.py` cho ra 7/12 PASS (5 FAIL thật, vì kiểm tra hành vi
CŨ — class CSS và schema-trong-html — đã bị thay đổi có chủ đích từ lâu
nhưng chưa cập nhật lại test). Đã sửa lại 5 assertion lỗi thời, chạy lại:
13/13 PASS. 8/28 file còn lại cần `tkinter` — không chạy được trong môi
trường test hiện tại, **trạng thái thật của 8 file này vẫn CHƯA XÁC ĐỊNH**,
cần Thịnh tự chạy trên máy có tkinter.

### 1. VÁ LỖI THẬT — SKU trùng khiến WooCommerce đè sản phẩm (Audit Tool #3)

Đếm thật trên MASTER: **17 mã SKU bị trùng, ảnh hưởng 34 dòng** (phát
hiện cùng cơ chế đã tồn tại từ Ver 2.x — `sku_trung` trong báo cáo import
— nhưng chỉ nằm trong báo cáo, KHÔNG có hành động bảo vệ nào). Case thật:
`BHSLBS24M` — 2 sản phẩm khác nhau (có/không SCADA, giá 46tr/42tr) dùng
chung 1 mã. WooCommerce tra theo SKU để update → sản phẩm đăng sau **đè**
sản phẩm đăng trước, tool vẫn báo "THÀNH CÔNG" bình thường.

**Vá:** thêm field `publish_sku` (tính ở `nhap_phase2.py::import_4_profile`)
— record ĐẦU TIÊN gặp mỗi mã giữ nguyên SKU gốc; record thứ 2, 3... của
CÙNG 1 mã trùng được gắn hậu tố `-B2`, `-B3`... `ma_goc` (hiện trong nội
dung/bảng thông số) KHÔNG đổi — khách vẫn thấy đúng mã catalogue thật.
`ai_wp_adapter.py::dang_woo_that()` giờ nhận `publish_sku` làm SKU thật
gửi lên WooCommerce, không còn dùng thẳng `ma_goc`. In cảnh báo console
khi phát hiện SKU trùng, kèm gợi ý kiểm tra lại MASTER.

### 2. VÁ LỖI THẬT — Title bị cắt 70 ký tự gây trùng (Audit Tool #4)

Đếm thật: **50 nhóm title trùng nhau sau khi cắt 70 ký tự, ảnh hưởng 120
dòng** — 2 SKU chỉ khác nhau ở phần ĐUÔI Tên hàng, bị cắt mất đúng phần
khác biệt → 2 title tag giống hệt nhau trên Google (hại SEO thật).

**Vá:** `render_phase2.py::rut_gon_tieu_de_chong_trung()` — khi câu GỐC dài
hơn giới hạn (chắc chắn bị cắt), CHỪA sẵn chỗ cho mã hàng ở cuối trước khi
cắt phần văn bản. Mã hàng luôn duy nhất tuyệt đối trong MASTER, nên 2
title từ 2 SKU khác nhau không bao giờ trùng nữa dù phần đầu giống nhau.
Kết quả sau vá: còn **22 dòng trùng** (giảm từ 120) — phần còn lại KHÔNG
phải lỗi cắt chuỗi, mà là **Tên hàng GỐC trong MASTER đã trùng nhau ngay
từ đầu** (VD `TTTCVV395150`/`TTTCVV395170` có cùng Tên hàng
"CVV 3x951+1x0mm2 (sc)" — số phân biệt 150/170 bị thiếu ngay trong tên,
không phải do tool cắt) — đây là lỗi dữ liệu MASTER, không phải lỗi code,
KHÔNG tự sửa/suy đoán số bị thiếu. `outline_may_bien_ap` KHÔNG áp cơ chế
này — Thịnh đã quyết không muốn mã hàng trong title máy biến áp (Ver 5.0),
giữ nguyên quyết định đó.

### 3. VÁ LỖI THẬT — Nút "Nghỉ giữa 2 bài" chết (Audit Tool #6)

Grep xác nhận: biến `v3_nghi_giua_bai` chỉ xuất hiện ở chỗ khai báo UI,
không `.get()` ở đâu khác, không `time.sleep()` nào dùng nó — nhập 5 hay
500 giây đều vô nghĩa.

**Vá:** `_v3_nghi_giua_bai_giay()` đọc giá trị TRÊN LUỒNG CHÍNH (an toàn
Tkinter), truyền vào cả 2 vòng lặp batch (record-based và job-based) qua
tham số, `time.sleep()` thật giữa các sản phẩm (bỏ qua sản phẩm đầu tiên).

### 4. VÁ LỖI THẬT — Ma trận key/model dự phòng thiếu tổ hợp (Audit Tool #7)

Đọc code xác nhận: chỉ thử (key chính×model phụ) và (key phụ×model chính),
KHÔNG BAO GIỜ thử (key phụ×model phụ). Nếu key chính hết quota VÀ model
chính lỗi cùng lúc, tổ hợp duy nhất có thể cứu batch chưa từng được thử.

**Vá:** `_v3_danh_sach_key_model_du_phong()` bổ sung vòng lặp tổ hợp còn
thiếu — mọi (key phụ, model phụ), không trùng lặp với các tổ hợp đã có.

### 5. Gọn lại thư mục (KHÔNG đụng code) + icon cho shortcut

Theo yêu cầu Thịnh ("giải nén thấy rối"). Gom **59 file `.md`** (tài liệu)
vào `docs/` (lịch sử từng bản riêng ở `docs/lich-su-phien-ban/`), gom
**30 file `test_*.py`** vào `tests/`. **KHÔNG di chuyển bất kỳ file `.py`
chính nào** (`giao-dien.py` và 16 module còn lại) — cân nhắc kỹ: chuyển
vào thư mục con có rủi ro thật với cách Python tìm module, lợi ích chỉ là
thẩm mỹ, áp dụng đúng nguyên tắc đã thống nhất "code chạy được thì để
yên". Sau khi gom `tests/`, phải vá thêm 2 chỗ đường dẫn tương đối bị vỡ
(`BASE` trong 17 file test tự viết, và 1 lệnh `subprocess` gọi file test
khác) — đã fix, chạy lại xác nhận 100% các test chạy được vẫn PASS.

Icon: Windows không cho gắn `.ico` trực tiếp vào `.bat` — thêm
`TAO-SHORTCUT-CO-ICON.bat` (chạy 1 lần) tự tạo shortcut Desktop dùng icon
riêng (`icon/lotech-autopost.ico`, tự vẽ, tông màu cam trùng nút CTA thật
trên site). Cập nhật luôn tiêu đề cửa sổ CMD trong 4 file `.bat` (còn ghi
"VER 3" từ rất lâu — GPT chỉ đúng chỗ này).

### File sửa

`nhap_phase2.py` (`publish_sku`), `ai_wp_adapter.py` không đổi logic
(chỉ nhận tham số `ma_hang` khác từ nơi gọi), `render_phase2.py`
(`rut_gon_tieu_de_chong_trung` mới), `giao-dien.py` (đọc `nghi_giua_bai`,
`time.sleep()`, ma trận key/model đủ tổ hợp, dùng `publish_sku` khi đăng
Woo, đổi tiêu đề bản), `tests/test_phase2_full.py` (sửa đường dẫn
subprocess), `tests/test_v42_hero_cta.py` (rà lại 5 assertion lỗi thời),
17 file test khác (sửa `BASE` path sau khi chuyển vào `tests/`), 4 file
`.bat` (đổi tiêu đề VER 3 → VER 5.1).

### File mới

`tests/test_v51_patch.py` (20 test: nghỉ giữa 2 bài hoạt động thật, ma
trận key/model đủ 4 tổ hợp, title chống trùng, publish_sku đúng case thật
BHSLBS24M), `README.md` (giải thích cấu trúc thư mục mới), `icon/
lotech-autopost.ico`, `TAO-SHORTCUT-CO-ICON.bat`.

### File xoá

`lotech-theme.css` (Ver 4.9.8, đã lỗi thời từ khi chuyển sang CSS inline
ở Ver 4.9.9 — giữ lại sẽ gây hiểu nhầm phải dán CSS, không còn đúng).

### Không làm (còn treo, chưa được yêu cầu lại trong phiên này)

- Gate CONFIRMED/CAN_KIEM (Audit Tool #5) — ~50% MASTER chưa xác nhận vẫn
  được viết bình thường. Đây là mục điểm thấp nhất trong audit (2/10)
  nhưng cần thiết kế UI override, không làm vội trong bản vá nhanh này.
- Schema → Rank Math meta field thật — vẫn cần Thịnh xác nhận tên meta
  key trước (đã nhắc từ Ver 4.9.6).
- 8 file test cần tkinter — chưa xác nhận được trong sandbox, cần Thịnh
  tự chạy trên Windows.
- Dọn code legacy RMU song song (autopost.py 87% không dùng) — Thịnh xác
  nhận không dùng nữa nhưng chọn GIỮ NGUYÊN, không xoá ("code chạy được
  thì để yên").
