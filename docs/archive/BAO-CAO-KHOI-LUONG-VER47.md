# BAO-CAO-KHOI-LUONG-VER47.md

| # | Trường | Nội dung |
|---|---|---|
| 1 | Thời gian | 1 phiên làm việc, gồm 1 lượt "khoan làm, bàn trước" rồi mới code |
| 2 | File sửa | 8 — `ai_wp_adapter.py`, `giao-dien.py`, `cauhinh.py`, `prompts_phase2.py`, `test_v37_batch_real.py`, `test_v37_1_patch.py`, `test_v39_article_jobs.py`, `test_v46.py` |
| 3 | File mới | 1 — `test_v47.py` |
| 4 | Dòng diff (tích luỹ từ Ver 3.6) | `ai_wp_adapter.py`: 422; `giao-dien.py`: 993; `cauhinh.py`: 67; `prompts_phase2.py`: 50; test mới: 139 |
| 5 | Test mới | 13 |
| 6 | Tổng test | 331/331 PASS, 0 FAIL |
| 7 | Hoàn thành | Cơ chế tự động thử key/model dự phòng (cả lỗi cắt token lẫn FAQ rác); UI nhập dự phòng; giới hạn độ dài câu hỏi FAQ; tăng token 16000→24000; nút "Chuẩn hoá MASTER"; vá banner cũ |
| 8 | Chưa làm | Chưa xác định chắc nguyên nhân gốc lỗi máy biến áp (nghi vấn model, chưa loại trừ hẳn) |
| 9 | Không test được | Cơ chế dự phòng chạy với model/key thật |
| 10 | Việc Thịnh làm | (a) Nhập thêm 1-2 model dự phòng + API key dự phòng (nếu có) ở tab Cấu hình. (b) Chạy lại batch máy biến áp, xem log có dòng "thành công sau khi đổi cặp key/model" không — nếu có, xác nhận cơ chế hoạt động thật. (c) Xác nhận lại giúp: lúc chạy 20 bài cáp điện mượt, model dùng có phải cùng `gemini-3.6-flash` không — cần biết để kết luận chắc nguyên nhân. |
| 11 | Rủi ro | Thấp cho phần logic (test kỹ 2 kịch bản thật). Rủi ro thật: cơ chế dự phòng chỉ giảm thiểu, không chữa tận gốc nếu Gemini thật sự đang có vấn đề ổn định ở model cụ thể — cần Thịnh quan sát thêm sau khi dùng bản này. |
| 12 | Rủi ro pháp lý/bảo mật | Không có thay đổi mới. |
| 13 | ZIP | `Lotech-Autopost-Ver4.7-Claude.zip` |

## Quyết định đáng chú ý

**Gộp Hard Block vào chung vòng thử dự phòng, không tách riêng.** Ban đầu
có thể nghĩ "chỉ lỗi Gemini mới cần đổi model, Hard Block là vấn đề khác"
— nhưng thực tế đọc log cho thấy FAQ rác (Hard Block chặn) và cắt token
đều là DẤU HIỆU CỦA CÙNG 1 NGUYÊN NHÂN (model bất ổn), nên gộp chung 1 cơ
chế xử lý là đúng, không phải 2 vấn đề tách biệt.

**Trung thực về giới hạn của giải pháp.** Đã nói rõ trong CHANGELOG: giới
hạn độ dài câu hỏi trong prompt là giảm nhẹ, không phải fix triệt để. Cơ
chế dự phòng cũng chỉ là giảm thiểu tác động (retry với lựa chọn khác),
không sửa được hành vi gốc của model Gemini — đây là giới hạn thật, không
tô hồng để nghe hay hơn.
