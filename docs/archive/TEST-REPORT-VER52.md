# TEST-REPORT-VER52.md

## Ver 5.2 Claude — 30/07/2026

### Test mới: `tests/test_v52_patch.py` — 17/17 PASS

| Nhóm | Test | Kết quả |
|---|---|---|
| Outline vỏ | Đăng ký đúng, vỏ route riêng, máy thật vẫn route cũ (Y1-01..03) | PASS |
| Title | Vỏ không gọi "Máy biến áp", có "Vỏ bảo vệ", Báo Giá đứng đầu (Y2-01..03) | PASS |
| Title | Máy biến áp thật vẫn đúng công thức cũ + Báo Giá đầu (Y2-04, Y2-05) | PASS |
| CTA | Có hotline → tel: gọi thẳng, không còn jump; không hotline → fallback an toàn (Y3-01..03) | PASS |
| Bảng so sánh | Có SKU anh em, có field ten_goc mới, không còn mã hàng, header đổi tên (Y4-01..04) | PASS |
| An toàn | Không so sánh chéo outline (vỏ ≠ máy thật), khối ONAN vẫn không áp cho vỏ (Y4-05, Y4-06) | PASS |

### Full regression (3 file cập nhật theo hành vi mới có chủ đích)

20/20 file chạy được trong sandbox: 100% PASS (bao gồm cả `test_v52_patch.py`
mới). 8 file cần tkinter vẫn KHÔNG XÁC ĐỊNH được trong sandbox này (không
đổi so với Ver 5.1) — cần Thịnh tự chạy trên Windows.

3 file test cũ được cập nhật do THAY ĐỔI HÀNH VI CÓ CHỦ ĐÍCH (không phải
nới lỏng để né lỗi):

- `test_v451_patch.py::CTA-ANCHOR-2` — kiểm tra nút "Yêu cầu báo giá" gọi
  thẳng (`tel:`) thay vì jump link.
- `test_v498_patch.py::U2-02` — kiểm tra bảng so sánh hiện TÊN sản phẩm
  thay vì mã hàng.
- `test_v50_patch.py::W4-04` — kiểm tra link trong bảng so sánh hiện tên
  sản phẩm.

Mỗi chỗ sửa có comment giải thích rõ lý do ngay trong file test.

### Việc chỉ Thịnh làm được

1. Copy file `cau-hinh.env` từ thư mục bản cũ vào thư mục Ver 5.2 mới —
   không cần nhập lại key/mật khẩu.
2. Xem lại trang "Vỏ mạ kẽm" thật trên site — xác nhận không còn bị gọi
   là "Máy biến áp" nữa, title đúng "Vỏ bảo vệ máy biến áp...".
3. Test nút "Yêu cầu báo giá" trên điện thoại thật — xác nhận gọi thẳng,
   không nhảy trang.
4. Rà thêm xem còn nhóm sản phẩm nào khác bị gắn sai outline tương tự
   "Vỏ mạ kẽm" không (lần này chỉ xử lý đúng case Thịnh phát hiện).
