# BÀN GIAO SONEALEO ULTRA 3.3 — bố cục A+ (06/08/2026)

Giải nén ĐÈ lên thư mục tool. Gói KHÔNG chứa `phase2-du-lieu.db` và
`cau-hinh.env` nên dữ liệu + key của bạn không bị đè.

## Việc bạn phải làm — 2 bước, không làm thì không thấy gì đổi

**1. Dán CSS lên WordPress**
WPCode / Code Snippets → snippet mới loại **CSS** → dán nguyên file
`CSS-MAU-A-PLUS.txt` → Active. Có snippet CSS cũ thì TẮT (đừng xoá vội).
File này cũng nằm sẵn trong tool: chạy `python css_a_plus.py` để xuất lại.

**2. Bật 2 cờ trong `cau-hinh.env`** (thiếu là bài ra bố cục cũ):
```
GIAO_DIEN_2_5=1
CSS_CLASS_MODE=1
```

## Đã làm gì

**Bố cục A+** — khung ảnh vuông 1:1 khớp Flatsome (đo từ ảnh Customizer:
~450×455px), dải 5 thumbnail, thông số nhanh kiểu nhãn-trái/giá-trị-phải,
đỏ làm màu nhấn. CSS phủ đủ **75/75 class** của cả hai bộ (trước đây 22
class của `render_phase2.ST` KHÔNG có CSS nào — đó là lý do bảng thông số
dính chữ và khối kiến thức thành tường chữ).

**4 chỗ chờ ảnh chèn thẳng vào bài** (`khoi_anh.py`):
- Ảnh 2 — biển máy, ngay sau bảng thông số
- Ảnh 4 — chi tiết bộ phận, sau sơ đồ cấu tạo
- Ảnh 5 — giao hàng/lắp đặt, trước khối liên hệ
- (Ảnh 1 — ảnh đại diện, do WooCommerce quản lý)

Mỗi khối ghi rõ **đặt ảnh gì, chọn thế nào, tỷ lệ bao nhiêu**, kèm HTML
comment hướng dẫn thay:
```html
<!-- ẢNH 2 — Ảnh biển máy... THAY cả khối div.snl-cho-anh bên dưới bằng:
     <div class="snl-anh-khung"><img src="URL_ANH" alt="..."></div> -->
```
Quên tấm nào thì khối vẫn đọc được như một ô trung thực, KHÔNG phải ảnh vỡ.

**2 biểu đồ sinh từ số catalogue** (0 lượt AI): cột tổn hao không tải 7
mức lân cận tô đỏ mức đang xem; thanh so Silic vs Amorphous kèm phép tính
kWh/năm. Tra không ra -> KHÔNG vẽ, không nội suy.

**4 lỗi đã vá:**
- Bảng so sánh: `250` -> `250 kVA`
- Bảng thông số: bỏ nhãn nội bộ `(trích từ tên)`, gọn `(W, catalogue THIBIDI)` -> `(W)`
- Tiêu đề "Kiến thức kỹ thuật liên quan" hết lặp 2 lần
- Mục lục hết link FAQ mồ côi khi FAQ bị bỏ

## Kiểm định
- Test mới `test_v33_bo_cuc.py`: **33/33 PASS**
- Hồi quy: v2.9 36, v3.0 24, v3.1 17, v3.2 34 — tất cả PASS
- Suite toàn dự án: **38 PASS** (lúc nhận bàn giao là 34), 4 fail là fail
  môi trường headless có sẵn từ trước
- Render thật SKU TBD3P250 qua trọn pipeline: 4 chỗ chờ ảnh, 2 biểu đồ,
  1 tiêu đề kiến thức, 0 nhãn nội bộ, FAQ khớp mục lục

## Chưa làm (đúng kế hoạch)
Batch cắt: gộp "Ứng dụng" với "Góc nhìn thị trường" đang trùng nguyên văn,
bỏ mục AI lộ đề bài, Enhance chuyển từ chèn thẳng sang gợi ý. Làm sau khi
bạn xem bố cục A+ trên site thật.
