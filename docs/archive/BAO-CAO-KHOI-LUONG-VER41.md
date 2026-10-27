# BAO-CAO-KHOI-LUONG-VER41.md

| # | Trường | Nội dung |
|---|---|---|
| 1 | Thời gian thực hiện | 1 phiên làm việc liên tục (vá Gemini schema → Hard Block lớp 4 → sửa 3 lỗi GPT bắt được ở bản MASTER trước → đóng gói tool → test qua pipeline thật → full regression → tài liệu) |
| 2 | Số file đã sửa | 3 — `ai_wp_adapter.py`, `render_phase2.py`, `giao-dien.py` (chỉ đổi tiêu đề) |
| 3 | Số file mới | 3 — `chuan_hoa_master.py`, `test_v41_gemini_hardblock.py`, `test_v41_chuan_hoa_master.py` |
| 4 | Dòng code thêm/xóa | `ai_wp_adapter.py`: diff 138 dòng; `render_phase2.py`: diff 125 dòng; `chuan_hoa_master.py`: 353 dòng mới; test mới: 80 + 92 dòng |
| 5 | Test mới | 10 (`test_v41_gemini_hardblock.py`) + 13 (`test_v41_chuan_hoa_master.py`) = 23 |
| 6 | Tổng test | 265/265 PASS, 0 FAIL (242 cũ không đổi 1 kết quả nào + 23 mới) |
| 7 | Hạng mục hoàn thành | responseSchema Gemini; Hard Block lớp 4 (chống chặn nhầm, có test âm chống thủng); công cụ chuẩn hoá MASTER đã sửa đúng 3 lỗi GPT review phát hiện, test qua pipeline import thật |
| 8 | Hạng mục chưa hoàn thành | Article Jobs ngữ nghĩa slug/bài cũ — Thịnh nói để sau |
| 9 | Phần không test được | Gemini thật (cần Thịnh xác nhận tỷ lệ thành công tăng); 2 file `.bat` |
| 10 | Việc Thịnh làm tiếp | (a) Chạy lại batch thật, xác nhận tỷ lệ thành công có tăng so với 0/10. (b) Chạy `python3 chuan_hoa_master.py --nguon du_lieu_goc --ra MASTER_ENRICHED.xlsx` để tự tạo bản MASTER làm giàu mới nhất, tự soát lại cột "Nghi Ngờ Phân Loại Sai"/"Trùng Mã/Tên" trước khi quyết định sửa. (c) Muốn dùng file enrich để đăng thật thì copy đè vào `du_lieu_goc/0X_*.xlsx` tương ứng rồi import lại bình thường qua tab 2 — không cần thao tác gì khác vì record_id đã đảm bảo khớp 100%. |
| 11 | Rủi ro còn lại | Thấp cho Gemini/Hard Block (đã test kỹ, có test âm). Công cụ MASTER: đã học bài học "phải test qua pipeline thật" nên độ tin cậy cao hơn hẳn lần trước — nhưng vẫn chỉ trích được field có THẬT trong tên/cột gốc, không giải quyết được phần dữ liệu hoàn toàn thiếu (dòng cắt kA, tổ đấu dây...) — việc đó vẫn cần catalogue hãng, ngoài phạm vi regex. |
| 12 | Rủi ro pháp lý/mất tiền | Không có thay đổi liên quan thanh toán/pháp lý. |
| 13 | ZIP bàn giao | `Lotech-Autopost-Ver4.1.zip` — thư mục bên trong đúng tên `Lotech-Autopost-Ver4.1`, tiêu đề app "LOTECH AUTOPOST VER 4.1" |

## Quyết định đáng chú ý

**Không tự động chạy `chuan_hoa_master.py` trong luồng import chính.**
Cân nhắc giữa 2 phương án: (a) tích hợp thẳng vào `nhap_phase2.py` để mọi
lần import đều tự làm giàu, hay (b) giữ là công cụ tách riêng, chạy tay.
Chọn (b) vì: import chính đã qua 219+ test ổn định qua nhiều bản, đổi
hành vi mặc định của nó (dù chỉ thêm bước) kéo theo rủi ro không tương
xứng lợi ích ở giai đoạn này. Công cụ tách riêng cho phép Thịnh tự quyết
định khi nào chạy, xem kết quả trước khi quyết định có đưa vào import
chính hay không.

**Bài học quy trình được đúc kết thành quy tắc bắt buộc trong chính file
`chuan_hoa_master.py`** (docstring đầu file liệt kê 5 ràng buộc bất biến) —
không chỉ sửa lỗi mà còn ghi lại LÝ DO để không lặp lại nếu file này được
sửa tiếp trong tương lai (kể cả bởi phiên Claude khác).
