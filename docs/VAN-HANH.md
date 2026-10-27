# SONEALEO — Hướng dẫn vận hành

Dành cho **người tiếp quản tool**, không cần biết lập trình.
Đọc hết mất ~10 phút. Chỉ mô tả cách DÙNG, không mô tả code.

---

## Tool này làm gì

Đọc file Excel danh mục sản phẩm → gọi AI viết nội dung → dựng trang HTML
→ đăng lên WordPress ở dạng **Bản nháp (Draft)**.

Không bao giờ tự đăng công khai. Người vận hành phải vào WordPress duyệt
và bấm Publish.

---

## Chạy lần đầu trên máy mới

1. Bấm đúp `CAI-DAT-LAN-DAU.bat` — chờ vài phút, nó tự tải Python về thư
   mục con. Chỉ cần làm 1 lần.
2. Từ đó về sau: bấm đúp `PHAN-MEM.bat`.

---

## Cần chuẩn bị 3 thứ trước khi dùng

| Cần gì | Lấy ở đâu | Điền vào đâu |
|---|---|---|
| API key Gemini | aistudio.google.com (miễn phí) | Tab 1. Cấu hình |
| Website WordPress + Application Password | WP > Users > Profile > Application Passwords | Tab 1. Cấu hình |
| File Excel danh mục | File `5MASTER_ENRICHED_*.xlsx` | Tab 2. Nhập dữ liệu |

API key Serper (tab 8) chỉ cần nếu dùng tính năng Enhance — không bắt buộc.

---

## Quy trình hàng ngày (5 bước)

1. **Tab 2 — Nhập dữ liệu**: chọn file Excel, bấm Nhập. Chỉ làm lại khi
   Excel có sản phẩm mới.
2. **Tab 3 — Sản phẩm**: bấm đúp để chọn những sản phẩm muốn đăng hôm nay.
3. **Tab 4 — Sinh & Đăng**: bấm nút chạy. Xem tiến độ ở cột Nhật ký bên phải.
4. **Tab 5 — Theo dõi**: xem bài nào đã đăng, bài nào lỗi.
5. **Vào WordPress**: duyệt nội dung từng bản nháp trước khi Publish.

Chạy được bao nhiêu bài/ngày phụ thuộc hạn mức Gemini miễn phí
(khoảng 20 lượt/ngày/model, có thể thêm model dự phòng ở tab 1 để tăng).

---

## 3 thứ dễ gây sự cố nhất

**1. Đăng nhầm hàng loạt**
→ Tab 5 có nút **"⟲ Gỡ bài hàng loạt"**. Bài sẽ vào Thùng rác WordPress,
khôi phục được. Luôn chạy thử 3-5 bài trước khi chạy hàng trăm bài.

**2. Dữ liệu Excel sai**
→ Lúc nhập, tool tự cảnh báo dòng nghi ngờ (VD cột điện áp không khớp tên
sản phẩm). **Đọc cảnh báo trong Nhật ký, đừng bỏ qua.** Tool không tự sửa
dữ liệu — người vận hành phải sửa trong Excel rồi nhập lại.

**3. Bài mất định dạng (chữ trần, không có bảng đẹp)**
→ Do tab 1 đã bật "Dùng CSS class" nhưng chưa dán CSS lên website. Cách
sửa: hoặc tắt ô đó đi, hoặc làm đúng 4 bước ở mục dưới.

---

## Bật chế độ CSS class (không bắt buộc, nhưng nên làm)

Giúp mỗi bài ngắn hơn ~36%, tốt cho SEO.

1. Tab 1 > bấm **"Xuất file CSS để dán lên WordPress"** > lưu file.
2. Mở file, copy toàn bộ nội dung.
3. WordPress > **Code Snippets** (hoặc Appearance > Customize >
   Additional CSS) > dán vào > Lưu.
4. Quay lại tab 1 > tick ô **"Dùng CSS class"**.
5. Đăng thử 1 bài, mở xem có đúng định dạng không rồi mới chạy hàng loạt.

---

## Khi gặp lỗi

Mọi thứ tool làm đều ghi ở cột **Nhật ký** bên phải. Copy nội dung đó khi
cần nhờ người khác hỗ trợ — trong đó có đủ thông tin để tìm nguyên nhân.

Lỗi hay gặp nhất và cách xử lý:

| Nhật ký báo | Nghĩa là | Làm gì |
|---|---|---|
| `Hết lượt miễn phí trong ngày` | Hết hạn mức Gemini | Chờ hôm sau, hoặc thêm model dự phòng ở tab 1 |
| `Hard Block chặn` | AI viết ra số liệu không khớp dữ liệu gốc | Bình thường — tool tự chặn để không đăng sai. Bài đó bị bỏ qua, không đăng |
| `File này là dữ liệu RMU cũ` | Chọn nhầm file Excel | Chọn đúng file `5MASTER_ENRICHED_*.xlsx` |
| `Chưa cấu hình website` | Thiếu thông tin WordPress | Điền lại tab 1 |

---

## Những giới hạn cần biết trước

- **Tool không tự kiểm tra nội dung có đúng sự thật hay không.** Nó chỉ
  đảm bảo các con số trong bài khớp với file Excel. Nếu Excel sai thì bài
  sai — luôn phải có người đọc duyệt.
- **Chưa từng chạy thử ở quy mô hàng nghìn bài.** Batch lớn nhất từng
  chạy khoảng vài chục bài. Tăng dần, đừng chạy hết một lần.
- **Ảnh sản phẩm chưa tự động.** Bài đăng ra có ô đánh dấu chỗ chèn ảnh,
  phải thay ảnh thật bằng tay trong WordPress.

---

## File quan trọng, đừng xoá

| File | Là gì |
|---|---|
| `phase2-du-lieu.db` | Toàn bộ lịch sử: sản phẩm, bài đã đăng, WP ID. **Mất file này là mất dấu vết mọi bài đã đăng.** Nên copy backup định kỳ. |
| `cau-hinh.env` | API key + mật khẩu WordPress. Không gửi cho ai, không đưa lên mạng. |
| `du_lieu_goc/*.xlsx` | File danh mục sản phẩm gốc |

---

## Tài liệu khác trong `docs/`

- `SPEC.md` — mô tả kỹ thuật hiện tại (cho người biết code)
- `NHAT-KY-THAY-DOI.md` — lịch sử thay đổi từng phiên bản
- `SONEALEO-TRACKLOG.xlsx` — bảng theo dõi việc đã làm / còn tồn đọng
- `archive/` — tài liệu cũ, chỉ để tra cứu lịch sử

---
Cập nhật: Ver 2.1 — 01/08/2026
