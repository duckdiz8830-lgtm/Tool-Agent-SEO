# BAO-CAO-KHOI-LUONG-VER498.md

| # | Hạng mục | Nội dung |
|---|---|---|
| 1 | Phiên bản | Ver 4.9.8 Claude |
| 2 | Ngày | 29/07/2026 |
| 3 | Nguồn gốc | Phản hồi Thịnh trên demo HTML "ultra" — giao diện đẹp, CTA đồng bộ, thêm chiều sâu content |
| 4 | Nội dung chính | CSS giao diện dán 1 lần vào Theme (tránh lặp bug script/style bị WordPress kses xoá); CTA cuối trang đồng bộ dạng nút; bảng so sánh công suất trong dòng (code, data thật); gộp góc nhìn kỹ sư/đầu tư thành 1 đoạn |
| 5 | Rủi ro tự phát hiện & tránh | Nhét `<style>` vào content sẽ dính lại bug JSON-LD lộ chữ (Ver 4.9.6) — chuyển hẳn sang file CSS riêng dán vào Theme |
| 6 | Phát hiện phụ | Cột "Cấp Điện Áp (kV)" trong MASTER sai dữ liệu ở nhiều dòng máy biến áp — đã né bằng cách ẩn cột này khỏi bảng so sánh mới, không tự sửa MASTER |
| 7 | File sửa | `render_phase2.py`, `db_phase2.py`, `prompts_phase2.py`, `giao-dien.py` |
| 8 | File mới | `test_v498_patch.py`, `lotech-theme.css`, `CHANGELOG-VER498.md`, `TEST-REPORT-VER498.md`, `BAO-CAO-KHOI-LUONG-VER498.md` |
| 9 | Test | 17 test mới (100% PASS) + 191 test trước đó chạy lại xác nhận không hồi quy = 208/208 |
| 10 | Chưa làm | AI-written nhận định "nên chọn mức nào" cạnh bảng so sánh; cơ chế Hard Block fail nhảy sản phẩm tiếp theo (đã bàn, chưa code, chờ xác nhận riêng); sửa cột Cấp Điện Áp trong MASTER |
| 11 | Việc chỉ Thịnh làm được | Dán `lotech-theme.css` vào Theme (bắt buộc để thấy giao diện đẹp); kiểm tra/sửa cột Cấp Điện Áp trong MASTER; đọc thử bài mới có bảng so sánh |
