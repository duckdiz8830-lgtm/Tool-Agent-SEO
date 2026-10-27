# TEST-REPORT-VER51.md

## Ver 5.1 Claude — 30/07/2026

### Test mới: `tests/test_v51_patch.py` — 20/20 PASS

| Nhóm | Test | Kết quả |
|---|---|---|
| Nghỉ giữa 2 bài | Hàm đọc UI tồn tại, `time.sleep()` xuất hiện thật trong cả 2 vòng lặp batch (X1-01..03) | PASS |
| Ma trận key/model | Có tổ hợp key phụ×model phụ trước đây thiếu, đủ 4/4 tổ hợp, cặp chính vẫn ưu tiên trước (X2-01..04) | PASS |
| Title chống trùng | Title ngắn giữ nguyên, title dài thêm mã hàng, không crash khi thiếu mã (X3-01..04) | PASS |
| Title chống trùng | Số dòng trùng thật trên MASTER giảm mạnh (X3-05) | PASS |
| SKU trùng → publish_sku | Mọi dòng có field mới, case thật BHSLBS24M tách đúng, ma_goc không đổi, SKU không trùng thì publish_sku=ma_goc (X4-01..07) | PASS |
| Wire vào WooCommerce | `dang_woo_that()` dùng `publish_sku`, không còn dùng thẳng `ma_goc` (X5-01) | PASS |

### Rà soát lại TOÀN BỘ 28 file test cũ (lần đầu tiên thật sự đầy đủ)

| File | Kết quả | Ghi chú |
|---|---|---|
| test_gate2.py | 23/23 PASS | |
| test_phase2_full.py | 12/12 PASS | Sửa 1 đường dẫn subprocess vỡ do chuyển vào tests/ |
| test_round2_integration.py | 34/34 PASS | |
| test_round2_ui_smoke.py | KHÔNG XÁC ĐỊNH | cần tkinter, sandbox không chạy được |
| test_snapshot_regex.py | 39/39 PASS | |
| test_that_mocked.py | 21/21 PASS | |
| test_v34_that_ui.py | KHÔNG XÁC ĐỊNH | cần tkinter |
| test_v35_idempotency.py | KHÔNG XÁC ĐỊNH | cần tkinter |
| test_v36_regression.py | 16/16 PASS | |
| test_v37_1_patch.py | KHÔNG XÁC ĐỊNH | cần tkinter |
| test_v37_batch_real.py | KHÔNG XÁC ĐỊNH | cần tkinter |
| test_v38_outline_studio.py | KHÔNG XÁC ĐỊNH | cần tkinter |
| test_v39_article_jobs.py | KHÔNG XÁC ĐỊNH | cần tkinter |
| test_v41_chuan_hoa_master.py | 13/13 PASS | |
| test_v41_gemini_hardblock.py | 10/10 PASS | |
| test_v42_hero_cta.py | 13/13 PASS | **Sửa 5 assertion lỗi thời** (class CSS, schema-trong-html) — trước khi sửa chỉ 7/12 |
| test_v451_patch.py | 13/13 PASS | |
| test_v45_checklist_lien_quan.py | KHÔNG XÁC ĐỊNH | cần tkinter |
| test_v46.py | 20/20 PASS | |
| test_v47.py | 13/13 PASS | |
| test_v48.py | 10/10 PASS | |
| test_v49.py | 9/9 PASS | |
| test_v495_patch.py | 21/21 PASS | |
| test_v496_patch.py | 14/14 PASS | |
| test_v497_patch.py | 22/22 PASS | |
| test_v498_patch.py | 17/17 PASS | |
| test_v499_patch.py | 32/32 PASS | |
| test_v50_patch.py | 22/22 PASS | |
| test_v51_patch.py | 20/20 PASS | |
| test_ver3_ui.py | KHÔNG XÁC ĐỊNH | cần tkinter |

**Tổng: 20/20 file chạy được đều 100% PASS (411 test case cộng dồn). 8/28
file KHÔNG chạy được trong sandbox này (thiếu tkinter) — trạng thái thật
CHƯA XÁC ĐỊNH, không phải "đã pass".**

### Minh bạch về nợ test trước đây

Từ Ver 4.9.5 tới Ver 5.0, mỗi lần báo "full regression PASS" thực chất chỉ
chạy một tập con (khoảng 19/28 file) — 9 file (gồm cả `test_v42_hero_cta.py`
vừa sửa) chưa từng được chạy lại. Đây là lỗi quy trình, tự phát hiện khi
audit lại tool theo yêu cầu Thịnh, không phải do review bên ngoài phát
hiện trước — nhưng review của GPT đã gợi ý đúng hướng nghi ngờ. Từ Ver
5.1 trở đi, quy trình "full regression" phải chạy ĐỦ toàn bộ `tests/*.py`
đang chạy được (20 file, không phải tập con), 8 file còn lại ghi rõ
"không xác định" thay vì ngầm coi là đã qua.

### Việc chỉ Thịnh làm được

1. **Chạy 8 file test cần tkinter trên máy Windows thật** — xác nhận
   trạng thái thật, báo lại nếu có FAIL.
2. Kiểm tra lại MASTER — 17 SKU trùng đã liệt kê trong cảnh báo console
   khi import, xác nhận có phải lỗi nhập liệu không (Thịnh/Quỳnh).
3. Kiểm tra 22 dòng title vẫn còn trùng sau khi vá — đây là do Tên hàng
   GỐC trong MASTER đã trùng nhau (không phải lỗi cắt chuỗi), cần sửa từ
   nguồn dữ liệu nếu muốn hết hẳn.
4. Chạy `TAO-SHORTCUT-CO-ICON.bat` để có icon riêng trên Desktop.
5. Thử batch thật với ô "Nghỉ giữa 2 bài" có giá trị > 0, xác nhận có
   nghỉ thật giữa các sản phẩm (xem log console có khoảng dừng đúng giây
   đã nhập).
