# BAO-CAO-KHOI-LUONG-VER37.md

| # | Trường | Nội dung |
|---|---|---|
| 1 | Thời gian thực hiện | 1 phiên làm việc liên tục (đọc code → sửa → test → verify portable → tài liệu) |
| 2 | Số file đã sửa | 2 |
| 3 | Danh sách file đã sửa | `giao-dien.py` — thay luồng Đăng Draft thật 1-record bằng batch-nhiều-record; `test_v34_that_ui.py` — sửa test REAL-1/REAL-2 theo hành vi mới |
| 4 | Số file mới | 1 — `test_v37_batch_real.py` |
| 5 | Dòng code thêm/xóa | `giao-dien.py`: diff 224 dòng (thay thế 2 hàm cũ bằng 3 hàm mới, phần lớn là logic vòng lặp + comment giải thích quyết định thiết kế); `test_v34_that_ui.py`: diff 36 dòng |
| 6 | Test mới | 8 test (`test_v37_batch_real.py`, mục T1/T1b/T2/T2b/T2c/T3/T4/T4b) |
| 7 | Tổng test | 189/189 PASS, 0 FAIL (181 regression Ver 3.6 cũ + 8 mới) |
| 8 | Hạng mục hoàn thành | P0-2 (đăng batch thật nhiều record), P0-3 (retry/chống trùng — xác nhận đã có sẵn, không cần code), P0-4 (chọn lô theo `selected`, tái dùng cơ chế cũ) — theo `01_ROADMAP` trong tracker |
| 9 | Hạng mục chưa hoàn thành | Không có trong scope Ver 3.7 đã chốt (Filter Builder, Outline Studio, Article Jobs vẫn ở version sau, không đụng tới) |
| 10 | Phần không test được | Gemini thật, WordPress thật (sandbox không có mạng ra ngoài); test 2 file `.bat` (không đổi ở Ver 3.7) |
| 11 | Việc Thịnh chạy Windows/thật | Giải nén ZIP → chạy `PHAN-MEM.bat` → tab "3. Cấu hình" nhập API key thật + website thật → tab "2. Sản phẩm" chọn 5 sản phẩm → chuyển "WordPress thật" → bấm "Đăng Draft lên WordPress" → xác nhận 5 Draft thật trên WP Admin, đúng nội dung, không trùng. Sau đó thử lại với 20 sản phẩm. |
| 12 | Rủi ro còn lại | Thấp — logic mới tái dùng gần như 100% hàm adapter đã qua test Ver 3.4/3.5 (goi_ai_that/dang_wp_that không đổi 1 dòng). Rủi ro chính nằm ở tốc độ thật khi chạy Gemini tuần tự cho số lượng lớn (5.264 sản phẩm) — chưa đo thời gian thật, chỉ đo được trên Mock (không delay mạng). |
| 13 | ZIP bàn giao | `Lotech-Autopost-Ver3.7.zip` |

## Quyết định đáng chú ý

**Không viết retry tự động phân loại lỗi như Work Order gốc yêu cầu (mục 7-8).**
Sau khi đọc `ai_wp_adapter.py`, xác nhận `goi_ai_that()` (Gemini) và
`dang_wp_that()` (WordPress) đã tự retry 3 lần với backoff, phân biệt lỗi
tạm thời (timeout/429/5xx — có retry, WordPress còn tự dò lại slug trước
khi thử lại) với lỗi cố định (401/403/4xx — không retry) từ tận Ver 3.4.
Viết thêm 1 lớp retry nữa ở tầng batch là trùng lặp, tốn thời gian mà
không tăng độ tin cậy. Việc này được ghi vào `CHANGELOG-VER37.md` và
`01_ROADMAP` của tracker để không ai tưởng nhầm là còn thiếu.

**Không thêm cột/trạng thái RUNNING vào DB.** Work Order gốc lo ngại trạng
thái RUNNING bị "treo" nếu app đóng giữa batch. Kiểm tra thực tế: thiết kế
hiện tại chỉ ghi 2 trạng thái cuối cùng (`da_dang`/`loi`) sau khi record xử
lý xong — không có bước ghi "đang chạy" vào DB. Nếu app đóng giữa chừng,
record dở dang vẫn ở `chua_sinh` (mặc định lúc khởi tạo) — đúng ý nghĩa
PENDING mà Work Order muốn, không cần sửa gì thêm. Đã viết test T4/T4b xác
nhận hành vi này bằng cách dừng giữa batch và chạy tiếp.
