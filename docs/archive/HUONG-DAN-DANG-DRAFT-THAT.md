# HƯỚNG DẪN — Đăng Draft thật đầu tiên (bản 3.4)

Đây là bước quan trọng nhất: tao (Claude) không gọi được internet trong môi
trường code, nên KHÔNG tự test được đoạn này — chỉ mày làm được. Làm đúng
theo thứ tự dưới đây.

## 1. Mở phần mềm

Bấm đúp `PHAN-MEM.bat`. Vào thẳng tab "3. Cấu hình".

## 2. Cấu hình AI (Google Gemini)

1. Vào [aistudio.google.com](https://aistudio.google.com), lấy API key
   miễn phí (nếu chưa có).
2. Dán vào ô "Google API key".
3. Bấm **"Kiểm tra API key và model"**.
   - Phần mềm sẽ gọi thật từng model Gemini (mất khoảng 1 phút), in tiến
     trình vào khung Nhật ký phía dưới.
   - Nếu OK: dropdown "Model đang chọn" tự điền model chạy được, đề xuất
     model đầu danh sách (thường là bản flash, hạn mức miễn phí cao nhất).
   - Nếu lỗi: đọc dòng chữ màu đỏ ngay dưới nút — key sai, hết quota, hay
     lỗi mạng đều báo rõ ràng, không chỉ nói "lỗi" chung chung.

**Nếu bấm xong mà không thấy gì xảy ra hoặc treo lâu quá 2 phút** — đó là
lỗi thật, chụp màn hình khung Nhật ký gửi lại theo khuôn báo lỗi ở mục 6.

## 3. Cấu hình Website WordPress

1. Trong WordPress: **Users → Profile → kéo xuống cuối → Application
   Passwords**. Gõ tên bất kỳ (VD "autopost"), bấm "Add New". WordPress hiện
   ra chuỗi dạng `abcd EFGH 1234 ijkl MNOP 5678` — **copy nguyên cả khoảng
   trắng**, đây không phải mật khẩu đăng nhập thường.
2. Quay lại phần mềm, điền:
   - Tên website (tự đặt, chỉ để hiển thị, VD "Lotech")
   - URL WordPress (VD `https://lotech.com.vn`, không cần `/wp-json` phía
     sau — phần mềm tự thêm)
   - Username (tài khoản WordPress của mày)
   - Application Password (dán nguyên chuỗi vừa copy)
3. Bấm **"Lưu cấu hình"**.
4. Bấm **"Kiểm tra kết nối"**.
   - **Bước này KHÔNG tạo bài nào cả** — chỉ xác nhận đăng nhập được.
   - OK: hiện dòng xanh "Kết nối OK — đăng nhập là ...".
   - Lỗi: hiện dòng đỏ, phân biệt rõ 3 loại: sai Username/Password (401),
     sai URL (404), hoặc bị chặn bởi tường lửa/Cloudflare (503 + không phải
     JSON).

**Không bấm "Đăng Draft" ở bước 4 nếu "Kiểm tra kết nối" chưa ra dòng xanh.**

## 4. Chọn 1 sản phẩm để thử

1. Sang tab "1. Nhập dữ liệu" → "Chọn file MASTER..." → chọn file Excel →
   "Nhập dữ liệu".
2. Sang tab "2. Sản phẩm" → chọn 1 dataset ở ô lọc → click 1 dòng bất kỳ
   trong bảng (không cần bấm đúp, chỉ cần click để nó thành dòng "đang xem").

## 5. Đăng Draft thật

1. Sang tab "4. Sinh & Đăng".
2. Chọn Mẫu (`chuan` hoặc `ngan_gon`).
3. Ở "Chế độ", chọn **"WordPress thật"** (chỉ chọn được nếu bước 3 đã lưu
   cấu hình xong — nếu vẫn mờ, quay lại bước 3).
4. Nút sẽ tự đổi tên thành **"Đăng Draft lên WordPress"**.
5. Bấm nút đó. Hộp thoại xác nhận hiện ra, đọc kỹ tên sản phẩm/website rồi
   mới bấm "Có" — đây là request THẬT, tốn quota Gemini thật và tạo 1 bài
   thật trên site thật (dù chỉ ở dạng Draft, chưa Publish).
6. Đợi khoảng 10-30 giây (gọi Gemini + kiểm tra Hard Block + đăng WordPress).
7. Kết quả:
   - **Thành công**: hộp thoại hiện URL bài viết. Vào WordPress Admin →
     Posts → tìm đúng bài đó, phải thấy trạng thái **Draft**, KHÔNG phải
     Published.
   - **Thất bại**: hộp thoại đỏ nói rõ lỗi ở bước nào (Gemini/Hard
     Block/WordPress). Xem chi tiết ở tab "5. Theo dõi", cột "Lỗi".

## 6. Nếu có lỗi, báo lại theo khuôn

```
VERSION: 3.4 (Gate First Real Draft)
LỖI: ...
BƯỚC: (2 Cấu hình AI / 3 Cấu hình Website / 5 Đăng Draft)
CÁCH TÁI HIỆN: 1. 2. 3.
KẾT QUẢ HIỆN TẠI: ...
KẾT QUẢ MONG MUỐN: ...
LOG: copy nguyên đoạn chữ trong khung Nhật ký (không cần xoá gì, phần mềm
     không bao giờ in API key/Application Password ra đó)
```

## 7. Sau khi Draft đầu tiên thành công

Dừng lại, không tự bấm thêm hàng loạt — Gate này chỉ làm đúng 1 bài để xác
nhận đường ống chạy đúng. Báo lại kết quả, đợi duyệt trước khi làm Gate tiếp
theo (Outline Studio đã chốt làm sau).

## Lưu ý an toàn

- Application Password **không bao giờ hiện ra** trong Nhật ký hay bất kỳ
  đâu ngoài ô nhập (ô đó cũng có dấu `*` che ký tự).
- File `cau-hinh.env` (chứa key/mật khẩu thật) **không được gửi cho ai,
  không đóng gói khi gửi phần mềm đi** — đúng cảnh báo đã ghi sẵn ở đầu file
  đó.
- Trạng thái đăng LUÔN là Draft — phần mềm không có lựa chọn Publish ở bản
  này, không cần lo bấm nhầm mà bài lên thẳng trang chủ.
