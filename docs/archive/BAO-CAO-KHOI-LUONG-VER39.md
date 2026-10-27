# BAO-CAO-KHOI-LUONG-VER39.md

| # | Trường | Nội dung |
|---|---|---|
| 1 | Thời gian thực hiện | 1 phiên làm việc liên tục (thiết kế data model → patch adapter/render → UI tab mới → test → full regression → tài liệu) |
| 2 | Số file đã sửa | 7 — `giao-dien.py`, `db_phase2.py`, `ai_wp_adapter.py`, `render_phase2.py`, `prompts_phase2.py`, `test_ver3_ui.py` (cập nhật số tab), `test_v34_that_ui.py` (không đổi hành vi) |
| 3 | Số file mới | 1 — `test_v39_article_jobs.py` |
| 4 | Dòng code thêm/xóa | `giao-dien.py`: diff 802 dòng (tab Article Jobs + toàn bộ handler + runner); `db_phase2.py`: diff 155 dòng (bảng + 8 hàm CRUD); `ai_wp_adapter.py`: diff 76 dòng; `render_phase2.py`: diff 60 dòng; `prompts_phase2.py`: diff 41 dòng (3 quy tắc Gemini); test mới 319 dòng |
| 5 | Test mới | 23 (`test_v39_article_jobs.py`, nhóm A/B/C/D) |
| 6 | Tổng test | 242/242 PASS, 0 FAIL (219 cũ không đổi 1 kết quả nào + 23 mới) |
| 7 | Hạng mục hoàn thành | Article Jobs đầy đủ: data model, tạo mặc định, +/-, đổi outline, chạy batch thật, cô lập hoàn toàn khỏi luồng Ver 3.7 (bug slug/wp_id đã lường trước và vá ngay, không đợi review lần 2). Sửa tên thư mục ZIP + tiêu đề app theo GPT review. Bake 3 gợi ý Gemini vào code dùng chung 7 outline. |
| 8 | Hạng mục chưa hoàn thành | Không có trong scope Ver 3.9 đã chốt |
| 9 | Phần không test được | Gemini/WordPress thật cho luồng Job (sandbox không có mạng); 2 file `.bat`; chạy job số lượng lớn (>20) đo thời gian thật |
| 10 | Việc Thịnh làm tiếp | (a) Vào tab "7. Article Jobs", chọn vài sản phẩm ở tab 3, bấm "Tạo job mặc định", thử "+ Thêm job" với outline khác, chạy Draft thật 3-5 job xác nhận WordPress ra đúng số bài, không trùng slug. (b) Việc GPT/Gemini gợi ý dùng đúng để đánh giá thin content: chạy 1 lô nhỏ (5-10 sản phẩm cáp điện) qua Ver 3.7 hoặc Job, đọc thử content mới xem 3 quy tắc vừa bake vào có thật sự giảm lặp câu chữ không. |
| 11 | Rủi ro còn lại | Thấp cho phần logic (đã lường trước 2 rủi ro thật — đè slug, đọc nhầm wp_id — và vá kèm test âm ngay từ đầu, không phải đợi review lần 2 mới phát hiện như Ver 3.7). Rủi ro vận hành: job không có chế độ Mock, mọi lần test job đều tốn quota Gemini thật — Thịnh cần cân nhắc số lượng khi thử nghiệm. |
| 12 | Rủi ro pháp lý/mất tiền | Không có thay đổi nào liên quan thanh toán/pháp lý. |
| 13 | ZIP bàn giao | `Lotech-Autopost-Ver3.9.zip` — **thư mục bên trong ZIP đã đổi tên đúng thành `Lotech-Autopost-Ver3.9`** (sửa theo GPT review, không còn ghi "Ver3.6" nữa) |

## Quyết định đáng chú ý

**Tách hẳn tab/luồng Article Jobs khỏi tab "4. Sinh & Đăng" (Ver 3.7), không
gộp chung.** Đây là quyết định kiến trúc quan trọng nhất của Ver 3.9. Lý do:
mục tiêu tối thượng (đăng hết 5.264 sản phẩm, 1 bài/sản phẩm) đã được Ver
3.7 giải quyết và test kỹ (196 test qua patch 3.7.1). Article Jobs là nhu
cầu THÊM (nhiều bài/sản phẩm khi cần), không PHẢI thay thế nhu cầu gốc.
Gộp chung 2 luồng vào 1 sẽ buộc phải sửa lại toàn bộ code Ver 3.7 đã ổn
định — rủi ro cao, lợi ích thấp. Tách riêng: luồng cũ không đổi 1 dòng
hành vi, luồng mới xây độc lập, dễ test, dễ rollback nếu có vấn đề (chỉ
cần không dùng tab 7, tab 4 vẫn chạy y như cũ).

**Bug slug-đè-nhau và wp_id-đọc-nhầm được lường trước và vá NGAY khi
viết, không đợi GPT review phát hiện như Ver 3.7.** Đây là áp dụng trực
tiếp bài học từ đợt patch 3.7.1 — trước khi viết vòng lặp job, đã tự hỏi
"2 job cùng sản phẩm có đụng nhau chỗ nào không" và lần theo code
`dung_slug()`/`dang_wp_that()` để tìm ra 2 điểm xung đột thật sự trước khi
viết bất kỳ dòng UI nào.
