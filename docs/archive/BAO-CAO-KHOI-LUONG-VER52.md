# BAO-CAO-KHOI-LUONG-VER52.md

| # | Hạng mục | Nội dung |
|---|---|---|
| 1 | Phiên bản | Ver 5.2 Claude |
| 2 | Ngày | 30/07/2026 |
| 3 | Nguồn gốc | Ảnh chụp production thật + đối chiếu tutrungthe.vn (Thịnh gửi) |
| 4 | Minh bạch trước khi vá | Soát lại 6 mục Ver 5.0: cả 6 đều có code, nhưng 3 mục làm sai ý định (title Báo Giá sai vị trí, CTA chỉ đổi hình thức không đổi hành vi, bảng so sánh chỉ thêm link không đổi hiển thị) |
| 5 | Bug nghiêm trọng đã vá | "Vỏ mạ kẽm nhúng nóng MBA..." (vỏ thép, không phải máy biến áp) bị title/nội dung gọi thành "Máy biến áp" — sai sự thật. Tách outline riêng `outline_vo_may_bien_ap` |
| 6 | 3 sửa UX theo yêu cầu | Title "Báo Giá" chuyển lên đầu; CTA "Yêu cầu báo giá" gọi thẳng (tel:) thay vì nhảy trang; bảng so sánh công suất hiện tên sản phẩm thay vì mã hàng |
| 7 | Từ chối 1 yêu cầu (an toàn dữ liệu) | Không lưu cứng mật khẩu WordPress/Application Password/API key thật vào prompt hoặc code — giải thích rủi ro, hướng dẫn dùng cau-hinh.env sẵn có |
| 8 | File sửa | `profiles.py`, `prompts_phase2.py`, `render_phase2.py`, `db_phase2.py`, `giao-dien.py`, 3 file test cũ |
| 9 | File mới | `tests/test_v52_patch.py`, 3 file doc Ver 5.2 |
| 10 | Test | 17 test mới (100%) + 20/20 file cũ chạy được đều PASS. 8 file cần tkinter chưa xác định |
| 11 | Chưa làm | Form lead tại chỗ (Thịnh xác nhận không cần); chưa rà toàn bộ MASTER tìm thêm case gắn sai outline tương tự |
| 12 | Việc chỉ Thịnh làm được | Copy cau-hinh.env sang thư mục mới; xem lại trang Vỏ mạ kẽm + nút gọi thẳng trên site thật |
