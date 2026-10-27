# BAO-CAO-KHOI-LUONG-VER497.md

| # | Hạng mục | Nội dung |
|---|---|---|
| 1 | Phiên bản | Ver 4.9.7 Claude |
| 2 | Ngày | 29/07/2026 |
| 3 | Nguồn gốc | Thịnh duyệt hướng qua demo HTML mẫu (SKU MBT3P250A2608), yêu cầu "code mọi thứ về máy biến áp mà mày biết — 1 pha, 3 pha, dầu hay khô" |
| 4 | Nội dung chính | Khối cố định "về máy biến áp [dầu/khô] nói chung" — CODE viết cứng, không phải AI đoán mỗi SKU |
| 5 | Rủi ro đã xử lý | Dầu/khô khác nguyên lý làm mát hoàn toàn — gán nhầm là bịa sai thông tin kỹ thuật; đã tách 2 bản riêng, an toàn khi không nhận diện được (trả rỗng, không đoán) |
| 6 | Phạm vi áp dụng | Chỉ outline_may_bien_ap, không áp dụng outline_do_luong dù tên hàng tình cờ trùng từ khoá |
| 7 | Đối chiếu thật | Tiêu chuẩn khô (TCVN 6306-11 + IEC 60076-11) đối chiếu đúng với catalogue MBT/THIBIDI đã đọc trước đó, không bịa |
| 8 | File sửa | `render_phase2.py`, `giao-dien.py` |
| 9 | File mới | `test_v497_patch.py`, `CHANGELOG-VER497.md`, `TEST-REPORT-VER497.md`, `BAO-CAO-KHOI-LUONG-VER497.md` |
| 10 | Test | 22 test mới (100% PASS) + 169 test trước đó chạy lại xác nhận không hồi quy = 191/191 |
| 11 | Quét thật | 165 dòng outline_may_bien_ap: 141 nhận đúng khối, 24 dòng phụ kiện vỏ đúng là không nhận (an toàn) |
| 12 | Chưa làm | Route lại 24 dòng "Vỏ mạ kẽm nhúng nóng" sang outline khác (quyết định phân loại, không phải bug); RM6/SM6 (71 SKU) |
| 13 | Việc chỉ Thịnh làm được | Đọc thử bài mới sinh cả 2 loại dầu/khô; quyết định có route lại 24 dòng vỏ mạ kẽm không |
