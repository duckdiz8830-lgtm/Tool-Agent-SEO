# BAO-CAO-KHOI-LUONG-VER38.md

| # | Trường | Nội dung |
|---|---|---|
| 1 | Thời gian thực hiện | 1 phiên làm việc liên tục (vá 2 bug → test âm → Outline Studio → test → full regression → tài liệu) |
| 2 | Số file đã sửa | 5 — `giao-dien.py`, `ai_wp_adapter.py`, `prompts_phase2.py`, `test_v34_that_ui.py` (không đổi hành vi, chỉ chạy lại xác nhận vẫn PASS), `test_ver3_ui.py` (cập nhật số tab 5→6) |
| 3 | Số file mới | 4 — `outline_studio.py`, `test_v37_batch_real.py` (đã có từ Ver 3.7, giữ nguyên), `test_v37_1_patch.py`, `test_v38_outline_studio.py` |
| 4 | Dòng code thêm/xóa | `giao-dien.py`: diff 414 dòng (patch batch loop + toàn bộ tab Outline Studio); `ai_wp_adapter.py`: diff 34 dòng (patch slug-2); `prompts_phase2.py`: diff 36 dòng (route qua override); `outline_studio.py`: 107 dòng mới; test mới: `test_v37_1_patch.py` 212 dòng, `test_v38_outline_studio.py` 172 dòng |
| 5 | Test mới | 7 (`test_v37_1_patch.py`) + 23 (`test_v38_outline_studio.py`) = 30 |
| 6 | Tổng test | 219/219 PASS, 0 FAIL (196 cũ + 23 mới của Ver 3.8; Ver 3.7.1 patch cộng thêm 7 vào con số 196 đó) |
| 7 | Hạng mục hoàn thành | Vá Bug 1 (exception chết batch), Bug 2 (slug-2) theo đúng yêu cầu GPT review; Outline Studio (Ver 3.8) — chỉnh góc nhìn + 4 mục hướng dẫn AI viết + ghi chú riêng, có Lưu/Khôi phục/Xem trước |
| 8 | Hạng mục chưa hoàn thành | Không có trong scope đã chốt (Filter Builder, Article Jobs vẫn ở version sau) |
| 9 | Phần không test được | Gemini thật, WordPress thật (sandbox không có mạng ra ngoài); 2 file `.bat` trên Windows |
| 10 | Việc Thịnh làm tiếp | (a) Gate GPT yêu cầu: chạy lại thật 1 Draft → 5 Draft → 20 Draft để xác nhận patch ổn định trên môi trường thật trước khi tin tưởng batch lớn hơn. (b) Vào tab "6. Outline Studio", thử sửa 1-2 outline (ví dụ outline_cap_dien — đúng loại Gemini vừa chê thin content), bấm Xem trước để đọc prompt thật, rồi chạy Real batch nhỏ (5 record) so sánh chất lượng bài trước/sau sửa. |
| 11 | Rủi ro còn lại | Thấp cho phần patch (đã test đúng kịch bản GPT fault-inject). Outline Studio là tính năng mới hoàn toàn — rủi ro chính là UI: Text widget thường (không có giới hạn ký tự, không cảnh báo nếu gõ quá dài) có thể khiến bài vượt giới hạn độ dài đã định trong `GIOI_HAN_DO_DAI` (giới hạn đó KHÔNG đổi qua Outline Studio, AI vẫn được dặn tuân theo, nhưng nếu Thịnh viết hướng dẫn mâu thuẫn với giới hạn thì AI có thể viết sai lệch — không phải lỗi code, là rủi ro dùng sai). |
| 12 | Rủi ro pháp lý/mất tiền | Không có — Outline Studio không đụng WordPress/Gemini/tiền, chỉ đổi văn bản hướng dẫn nội bộ. |
| 13 | ZIP bàn giao | `Lotech-Autopost-Ver3.8.zip` |

## Quyết định đáng chú ý

**Xem trước dùng prompt thật, không dùng Mock.** `goi_ai_mock()` có
template cứng riêng để test batch nhanh (không gọi Gemini), không đọc mô
tả section trong `OUTLINE_NOI_DUNG`. Nếu để "Xem trước" gọi Mock, Thịnh sửa
outline xong bấm xem trước sẽ thấy y hệt như cũ — tưởng nhầm là sửa không
có tác dụng, trong khi thực ra Gemini thật SẼ đổi. Chọn hiện prompt thật
(system + user) — trung thực hơn, đúng những gì Gemini thực sự nhận được,
và tận dụng lại được `PR.xay_prompt()` có sẵn, không viết thêm logic mock mới.

**Không thêm cột/trạng thái nào vào DB cho Outline Studio.** Lưu tuỳ chỉnh
vào 1 file JSON riêng (`outline-tuy-chinh.json`), độc lập hoàn toàn với
`phase2-du-lieu.db`. Lý do: đây là cấu hình ứng dụng (giống `cau-hinh.env`),
không phải dữ liệu sản phẩm — không có lý do gì phải đi qua SQLite, và tách
riêng giúp "Khôi phục mặc định" chỉ là xoá 1 key trong JSON, không đụng gì
tới dữ liệu sản phẩm/bài viết đã có.
