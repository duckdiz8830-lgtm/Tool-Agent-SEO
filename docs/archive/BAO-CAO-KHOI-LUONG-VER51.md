# BAO-CAO-KHOI-LUONG-VER51.md

| # | Hạng mục | Nội dung |
|---|---|---|
| 1 | Phiên bản | Ver 5.1 Claude |
| 2 | Ngày | 30/07/2026 |
| 3 | Nguồn gốc | Audit lại toàn bộ tool theo `Audit-Checklist-Ver5.0.xlsx` (tự kiểm chứng lại review Gemini + GPT bằng code/data thật) |
| 4 | Phát hiện quy trình (trước khi vá gì khác) | "Full regression" trước đây chỉ chạy ~19/28 file test, bỏ sót 9 file — chạy lại đủ phát hiện `test_v42_hero_cta.py` có 5 assertion lỗi thời, đã sửa |
| 5 | 4 bug đã vá (đều tự verify bằng code/data thật trước khi vá) | SKU trùng đè nhau trên WooCommerce (17 mã/34 dòng); Title bị cắt trùng nhau (50 nhóm/120 dòng, giảm còn 22); Nút "Nghỉ giữa 2 bài" chết hoàn toàn; Ma trận key/model dự phòng thiếu tổ hợp |
| 6 | Gọn thư mục | Gom 59 file `.md` vào `docs/`, 30 file `test_*.py` vào `tests/` — KHÔNG di chuyển file `.py` chính (rủi ro vỡ import > lợi ích thẩm mỹ) |
| 7 | Icon | Windows không cho gắn `.ico` trực tiếp vào `.bat` — thêm `TAO-SHORTCUT-CO-ICON.bat` tự tạo shortcut Desktop có icon riêng |
| 8 | File sửa | `nhap_phase2.py`, `render_phase2.py`, `giao-dien.py`, `tests/test_phase2_full.py`, `tests/test_v42_hero_cta.py`, 17 file test khác (sửa BASE path), 4 file `.bat` |
| 9 | File mới | `tests/test_v51_patch.py`, `README.md`, `icon/lotech-autopost.ico`, `TAO-SHORTCUT-CO-ICON.bat`, 3 file doc Ver 5.1 |
| 10 | File xoá | `lotech-theme.css` (lỗi thời từ khi chuyển CSS inline ở Ver 4.9.9) |
| 11 | Test | 20 test mới (100%) + 20/28 file cũ chạy được đều 100% PASS (411 test case). 8/28 file cần tkinter — KHÔNG XÁC ĐỊNH, không phải đã pass |
| 12 | Quyết định KHÔNG làm (theo yêu cầu Thịnh) | Không xoá code legacy RMU (autopost.py 87% không dùng nhưng giữ nguyên — "code chạy được thì để yên") |
| 13 | Chưa làm (còn treo) | Gate CONFIRMED/CAN_KIEM (điểm thấp nhất audit, 2/10, cần thiết kế UI riêng); Schema→Rank Math; xác nhận 8 file test cần tkinter |
| 14 | Việc chỉ Thịnh làm được | Chạy 8 file test cần tkinter trên Windows thật; kiểm tra lại MASTER theo cảnh báo SKU trùng; chạy `TAO-SHORTCUT-CO-ICON.bat`; thử "Nghỉ giữa 2 bài" trên batch thật |
