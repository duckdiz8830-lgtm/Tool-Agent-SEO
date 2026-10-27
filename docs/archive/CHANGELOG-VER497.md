# CHANGELOG-VER497.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER496.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 4.9.7 CLAUDE — Khối cố định "về máy biến áp nói chung" — 29/07/2026

### Bối cảnh

Từ demo HTML mẫu (SKU MBT3P250A2608) Thịnh duyệt hướng: tách sự thật ĐÚNG
CHO CẢ DÒNG sản phẩm (nguyên lý làm mát, ứng dụng chung, tiêu chuẩn ngành,
lưu ý lắp đặt) ra khối do CODE viết cứng, không để AI đoán lại mỗi SKU —
vừa tăng độ dày content, vừa giảm rủi ro AI viết sai/không nhất quán giữa
các SKU cùng dòng.

### Vấn đề bắt buộc phải xử lý đúng: dầu và khô khác nguyên lý hoàn toàn

Máy biến áp DẦU (làm mát bằng dầu cách điện tuần hoàn tự nhiên — ONAN) và
máy biến áp KHÔ (không dầu, làm mát bằng không khí — AN/AF) là 2 công nghệ
khác nhau hoàn toàn. Gán nhầm khối dầu cho SKU khô (hoặc ngược lại) là bịa
sai thông tin kỹ thuật thật — vi phạm nguyên tắc cốt lõi của cả dự án
("không suy đoán số liệu kỹ thuật khi thiếu"). Đã tách 2 bản nội dung riêng
biệt, route theo loại phát hiện được từ Tên hàng.

### Cách nhận diện — đọc dữ liệu thật, không suy đoán mẫu

`_phat_hien_loai_lam_mat()`: đọc "dầu"/"khô" trực tiếp trong Tên hàng — đã
kiểm tra thật cả 245 dòng sheet `03_May_Bien_Ap_Do_Luong` trong MASTER,
MASTER đặt tên nhất quán "Máy biến áp dầu ..."/"Máy biến áp khô ...", không
phải suy đoán mẫu chưa kiểm chứng.

`_phat_hien_so_pha()`: đọc "1Pha"/"3Pha" — dùng để thêm 1 câu ngữ cảnh ứng
dụng (1 pha: phụ tải phân tán/nông thôn; 3 pha: phụ tải tập trung/công
nghiệp), KHÔNG tách hẳn 2 khối riêng vì nguyên lý làm mát không đổi theo số
pha — chỉ khác ở câu ứng dụng.

**Không nhận diện được loại (VD dòng "Vỏ mạ kẽm nhúng nóng MBA..." — đây là
phụ kiện vỏ, không phải máy) → hàm trả rỗng, KHÔNG hiện khối nào.** Đã quét
thật 165 dòng `outline_may_bien_ap`: 141 dòng nhận diện đúng, 24 dòng "Vỏ
mạ kẽm..." đúng là không nên có nguyên lý làm mát (không phải máy biến áp
hoàn chỉnh) — hàm xử lý đúng, không cần sửa gì thêm ở bước này.

### Nội dung khối (tóm tắt, xem code để đọc đầy đủ)

- **Dầu:** nguyên lý ONAN, ứng dụng phân phối trung/hạ thế VN, tiêu chuẩn
  TCVN 6306 + TCVN 8525, lưu ý lắp đặt (bệ móng, thông gió, thoát nước).
- **Khô:** nguyên lý AN/AF không dầu, ứng dụng ưu tiên trong nhà/PCCC
  nghiêm ngặt, tiêu chuẩn TCVN 6306-11 + IEC 60076-11 + TCVN 8525 (đối
  chiếu đúng với catalogue MBT/THIBIDI thật đã đọc trước đó — không bịa),
  lưu ý lắp đặt riêng cho khô (thông gió, không cần bể dầu sự cố, quạt AF
  cần nguồn riêng).

### Chỉ áp dụng đúng phạm vi

`khoi_chung_may_bien_ap()` chỉ chèn khi `outline_id == 'outline_may_bien_ap'`
— KHÔNG áp dụng cho `outline_do_luong` (TI/TU/MOF, khác hẳn nguyên lý, dù
tên hàng tình cờ có chữ "dầu"/"khô") và không áp dụng ngoài profile
`may_bien_ap_do_luong`.

### File sửa

`render_phase2.py` (thêm `_phat_hien_loai_lam_mat`, `_phat_hien_so_pha`,
`khoi_chung_may_bien_ap`, wire vào `dung_bai_html` trước CTA cuối trang),
`giao-dien.py` (đổi tiêu đề bản).

### File mới

`test_v497_patch.py` (22 test: đơn vị phát hiện loại/pha, nội dung đúng
loại không lẫn nguyên lý, an toàn khi mơ hồ/sai outline, wiring thật vào
`dung_bai_html`, quét toàn bộ 165 dòng MASTER thật xác nhận 0 lệch).

### Không làm

- Chưa tách khối riêng theo Silic/Amorphous (loại lõi) — đây là field
  thuộc về ĐẶC ĐIỂM riêng SKU (AI viết, dùng data thật), không phải khối
  chung cố định — không lẫn 2 khái niệm.
- 24 dòng "Vỏ mạ kẽm nhúng nóng" hiện route vào outline_may_bien_ap nhưng
  không nhận nguyên lý làm mát (đúng, vì không phải máy hoàn chỉnh) — có
  thể cân nhắc route riêng sang outline_phu_kien giống "Giá treo MBT" ở
  đợt sau, chưa làm trong bản này (ngoài phạm vi yêu cầu hôm nay).
