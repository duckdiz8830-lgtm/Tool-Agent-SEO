# CHANGELOG-VER48.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER47.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 4.8 CLAUDE — Chuẩn hoá nhận file gộp + Vá trùng SKU WooCommerce + Log đầy đủ — 28/07/2026

Bối cảnh: Thịnh test thật, phát hiện 3 vấn đề cụ thể từ nút "Chuẩn hoá
MASTER" (Ver 4.7) và luồng đăng WooCommerce thật (log kèm theo). Đã kiểm
chứng bằng data thật trước khi vá, không đoán.

### 1. Chuẩn hoá MASTER — giờ chọn FILE, không bắt chọn thư mục

Trước đây bắt Thịnh chọn THƯ MỤC `du_lieu_goc` (chứa 4 file rời) — không
khớp cách Thịnh thực tế làm việc (luôn cầm 1 file MASTER gộp sẵn 4 sheet).

`chuan_hoa_master.chuan_hoa()` giờ **tự nhận diện cả 2 kiểu nguồn**:
- 1 file `.xlsx` gộp sẵn 4 sheet đúng tên (`01_Cap_Dien`, `02_...`,
  `03_...`, `04_...`) — kiểu MỚI, khớp cách dùng thật.
- Thư mục chứa 4 file rời — kiểu CŨ, vẫn chạy được (tương thích ngược,
  dùng dòng lệnh `--nguon du_lieu_goc` như trước không đổi gì).

Nút UI đổi sang `askopenfilename` (chọn file) thay vì `askdirectory`
(chọn thư mục). Không viết thêm logic riêng cho UI — vẫn gọi đúng 1 hàm
`chuan_hoa()`, chỉ đổi cách người dùng chọn nguồn.

### 2. Vá lỗ hổng đăng trùng SKU trên WooCommerce

Log thật: tạo sản phẩm MỚI (record chưa từng đăng qua tool) nhưng
WooCommerce từ chối "SKU đã có trong bảng tra cứu" — bước tra SKU trước
khi tạo (`tim_san_pham_woo_theo_sku`) không tìm ra sản phẩm dù nó thật sự
đã tồn tại trên site (nhiều khả năng do 1 công cụ/lần chạy khác đã tạo
trước đó).

**Không đoán chắc nguyên nhân gốc** (không chắc 100% hành vi API `?sku=`
của WooCommerce theo đúng bản/plugin Thịnh dùng) — thay vào đó thêm lớp
PHÒNG THỦ: khi tạo mới bị từ chối (4xx) và có mã hàng, tự động tra lại SKU
**đúng 1 lần** trước khi chịu thua; nếu lần này tìm ra, chuyển sang CẬP
NHẬT đúng ID đó thay vì báo lỗi luôn. Có test đối chứng: nếu tra lại vẫn
không thấy, vẫn báo lỗi rõ ràng, không lặp vô hạn.

### 3. Log đầy đủ lịch sử từng lần thử key/model dự phòng

Trước đây khi hết sạch danh sách dự phòng vẫn lỗi, log chỉ hiện lỗi CỦA
LẦN CUỐI — không thấy được đã thử những gì ở các lần trước, khó chẩn đoán
tại sao dự phòng "không cứu được" (VD case thật: cả 2 cặp cùng dính quota
hết hạn — cần thấy rõ CẢ 2 lần đều bị quota mới hiểu đúng vấn đề).

`goi_ai_co_du_phong()` giờ trả thêm `'lich_su'` — danh sách mô tả từng lần
thử (model + tóm tắt kết quả). Log in ra đầy đủ từng dòng, không chỉ dòng
cuối.

### File sửa

`chuan_hoa_master.py` (thêm `_nap_du_lieu_nguon()` tự nhận diện file/thư
mục), `ai_wp_adapter.py` (vá phục hồi trùng SKU + lịch sử đầy đủ),
`giao-dien.py` (nút chọn file thay vì thư mục, in lịch sử khi lỗi, tiêu đề
"VER 4.8 Claude").

### File mới

`test_v48.py` (10 test: chuẩn hoá từ file gộp lẫn thư mục cũ đều chạy
đúng, phục hồi trùng SKU thành công + đối chứng không lặp vô hạn khi
không tìm thấy, lịch sử đầy đủ từng lần thử).

### Không làm

- Chưa xác nhận 100% nguyên nhân gốc vì sao WooCommerce từ chối trùng SKU
  ở lần tra đầu tiên (thiếu dữ liệu để kết luận chắc — có thể là hành vi
  API cụ thể của bản WooCommerce Thịnh dùng). Lớp phục hồi thêm vào là
  phòng thủ hợp lý bất kể nguyên nhân gốc là gì.
- Chưa sửa gì thêm về FAQ/token — đợi Thịnh test bản 4.8 xem lỗi trùng SKU
  và luồng chuẩn hoá đã ổn chưa trước khi bàn tiếp.
