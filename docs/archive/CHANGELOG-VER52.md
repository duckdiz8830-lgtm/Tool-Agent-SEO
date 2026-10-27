# CHANGELOG-VER52.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER51.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 5.2 CLAUDE — Vá 4 lỗi từ ảnh chụp site thật + outline riêng cho vỏ MBA — 30/07/2026

### Bối cảnh

Thịnh gửi ảnh chụp thật trang sản phẩm + đối chiếu tutrungthe.vn, phát
hiện 4 vấn đề — trong đó có 1 lỗi THẬT nghiêm trọng (gọi sai bản chất sản
phẩm), không phải góp ý thẩm mỹ.

### 0. Minh bạch: soát lại đúng-sai của 6 mục Ver 5.0

Trước khi vá, đã đọc lại code xác nhận: 6/6 mục Ver 5.0 ĐỀU có code (không
phải bỏ sót như tưởng), nhưng 3/6 mục làm SAI Ý ĐỊNH dù có code chạy —
title thêm "Báo Giá" nhưng để cuối câu, CTA chỉ đổi hình thức (to hơn)
không đổi hành vi (vẫn jump), bảng so sánh chỉ thêm link chứ không đổi mã
hàng thành tên. Ghi nhận công khai, không chối.

### 1. BUG THẬT NGHIÊM TRỌNG — "Vỏ mạ kẽm" bị gọi thành "Máy biến áp"

Phát hiện qua ảnh site thật: `MBTVM3P1500` ("Vỏ mạ kẽm nhúng nóng MBA 3P
1500KVA...") — ĐÂY LÀ VỎ THÉP bảo vệ, KHÔNG PHẢI máy biến áp — bị title
gọi thành "Máy biến áp MBT 1500kVA – Báo Giá" và có bảng "So sánh công
suất trong dòng" như thể đang so sánh công suất VẬN HÀNH của máy.

**Gốc rễ:** `dung_tieu_de()`/`tinh_delta_context()`/`khoi_so_sanh_cong_suat()`
(thêm ở Ver 4.9.9-5.0) chỉ gate theo `outline_id == 'outline_may_bien_ap'`
— lúc thêm các hàm này, không quay lại kiểm tra tác động lên 24 dòng "Vỏ
mạ kẽm" đã biết từ Ver 4.9.7 (lúc đó chỉ kiểm 1 hàm — khối "về máy biến áp
nói chung" — thấy an toàn rồi dừng, không kiểm các hàm thêm sau).

**Vá — outline RIÊNG theo yêu cầu Thịnh** (`outline_vo_may_bien_ap`,
`profiles.py`): route theo Tên hàng bắt đầu bằng "vỏ mạ kẽm"/"vỏ mã kẽm".
Title mới: "Báo Giá Vỏ bảo vệ máy biến áp [Thương hiệu] [X]kVA" — đúng
bản chất, không gọi là máy biến áp. `tinh_delta_context()` vẫn áp dụng
(so cỡ vỏ vẫn có ý nghĩa thật — khớp đúng cỡ máy nào), nhưng
`khoi_chung_may_bien_ap()` (khối ONAN/AN-AF) GIỮ NGUYÊN không áp dụng cho
vỏ (đúng như thiết kế cũ, vỏ không có nguyên lý làm mát riêng).

`db_phase2.py::tim_san_pham_cung_dong()` sửa để KHÔNG BAO GIỜ so sánh chéo
2 outline khác nhau (vỏ không so với máy thật) — lọc theo đúng
`outline_id` của chính record đang xét, không hard-code 1 outline cố định.

### 2. Title: "Báo Giá" chuyển lên ĐẦU câu

Trước: "...– Báo Giá" (cuối). Giờ: "Báo Giá Máy biến áp..." (đầu), áp
dụng cho cả `outline_may_bien_ap` và `outline_vo_may_bien_ap`.

### 3. CTA "Yêu cầu báo giá" — hành động NGAY, không nhảy trang

Trước: `href="#lien-he-bao-gia"` — chỉ cuộn xuống cuối trang. Giờ: khi có
hotline, đổi thành `tel:` (gọi thẳng — cùng đích với nút "Gọi") — khách
bấm là gọi ngay, không phải cuộn tìm. Không có hotline vẫn giữ fallback
jump-link cũ (không crash, không mất CTA).

**Không làm:** form nhập số điện thoại tại chỗ kiểu tutrungthe.vn — cần
biết plugin/backend nhận lead thật của site, Thịnh xác nhận không cần.

### 4. Bảng so sánh công suất — hiện TÊN SẢN PHẨM, không hiện mã hàng

Ver 5.0 chỉ thêm link (giải quyết "bấm được"), KHÔNG giải quyết "đọc hiểu
được" — mã hàng bấm được vẫn là mã hàng, khách vẫn không biết là gì. Giờ
`tim_san_pham_cung_dong()` trả thêm field `ten_goc`, `khoi_so_sanh_cong_suat()`
hiện tên (rút gọn an toàn, không cắt giữa từ) thay vì mã. Cột đầu bảng đổi
tên "Mã hàng" → "Sản phẩm".

### An toàn dữ liệu — từ chối 1 yêu cầu

Thịnh yêu cầu lưu cứng mật khẩu WordPress + Application Password + 3
Google API key thật vào prompt/code để đỡ nhập lại. ĐÃ TỪ CHỐI — file
code/prompt đi theo mọi lần đóng gói ZIP, nhét cứng nghĩa là mọi bản giao
từ giờ đều mang theo mật khẩu thật. Giải pháp đúng (đã có sẵn từ đầu dự
án, không cần code gì thêm): copy file `cau-hinh.env` từ thư mục bản cũ
dán vào thư mục bản mới — không cần nhập lại, không cần tao thấy giá trị
thật.

### File sửa

`profiles.py` (outline mới + routing), `prompts_phase2.py` (guidance
outline vỏ), `render_phase2.py` (`dung_tieu_de`, `tinh_delta_context`,
`khoi_so_sanh_cong_suat`, `khoi_cta_ngan`), `db_phase2.py`
(`tim_san_pham_cung_dong` — thêm ten_goc, chặn so sánh chéo outline),
`giao-dien.py` (đổi tiêu đề bản), `tests/test_v451_patch.py`,
`tests/test_v498_patch.py`, `tests/test_v50_patch.py` (cập nhật theo hành
vi mới, có giải thích).

### File mới

`tests/test_v52_patch.py` (17 test: outline vỏ route đúng/an toàn ngược,
title không gọi vỏ là máy + Báo Giá đứng đầu, CTA gọi thẳng, bảng so sánh
hiện tên + không so chéo outline).

### Không làm

- Form lead tại chỗ (theo yêu cầu Thịnh, không cần).
- Chưa rà toàn bộ MASTER xem còn nhóm sản phẩm "gắn nhãn nhầm outline"
  nào khác ngoài "Vỏ mạ kẽm" — chỉ mới xử lý đúng case Thịnh phát hiện.
