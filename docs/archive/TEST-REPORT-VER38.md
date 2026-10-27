# TEST-REPORT-VER38.md

## Command chạy lại y hệt (đã verify portable từ /tmp/v38_check)

```
rm -rf *.db __pycache__ cau-hinh.env outline-tuy-chinh.json
python3 test_that_mocked.py
python3 test_gate2.py
python3 test_phase2_full.py
python3 test_snapshot_regex.py
python3 test_round2_integration.py
python3 test_v36_regression.py
rm -rf *.db __pycache__ cau-hinh.env outline-tuy-chinh.json
xvfb-run -a python3 test_v35_idempotency.py
rm -rf *.db __pycache__ cau-hinh.env outline-tuy-chinh.json
xvfb-run -a python3 test_round2_ui_smoke.py
rm -rf *.db __pycache__ cau-hinh.env outline-tuy-chinh.json anh-bang-chung-ui
xvfb-run -a --server-args="-screen 0 1366x768x24" python3 test_ver3_ui.py
rm -rf *.db __pycache__ cau-hinh.env outline-tuy-chinh.json anh-bang-chung-ui
xvfb-run -a --server-args="-screen 0 1366x768x24" python3 test_v34_that_ui.py
rm -rf *.db __pycache__ cau-hinh.env outline-tuy-chinh.json anh-bang-chung-ui
xvfb-run -a --server-args="-screen 0 1366x768x24" python3 test_v37_batch_real.py
rm -rf *.db __pycache__ cau-hinh.env outline-tuy-chinh.json anh-bang-chung-ui
xvfb-run -a --server-args="-screen 0 1366x768x24" python3 test_v37_1_patch.py
rm -rf *.db __pycache__ cau-hinh.env outline-tuy-chinh.json anh-bang-chung-ui
xvfb-run -a --server-args="-screen 0 1366x768x24" python3 test_v38_outline_studio.py
```
(Trên Windows: bỏ `xvfb-run -a`, chạy thẳng `python test_xxx.py`.)

## Kết quả tổng

**219/219 PASS, 0 FAIL.**

| File | PASS | Ghi chú |
|---|---|---|
| test_that_mocked.py | 21/21 | không đổi |
| test_gate2.py | 23/23 | không đổi |
| test_phase2_full.py | 12/12 | không đổi |
| test_snapshot_regex.py | 39/39 | không đổi |
| test_round2_integration.py | 34/34 | không đổi |
| test_v36_regression.py | 16/16 | không đổi |
| test_v35_idempotency.py | 11/11 | không đổi |
| test_round2_ui_smoke.py | 9/9 | không đổi |
| test_ver3_ui.py | 8/8 | **sửa I1/I4**: 5 tab → 6 tab (Ver 3.8 thêm Outline Studio) |
| test_v34_that_ui.py | 8/8 | không đổi so với Ver 3.7 |
| test_v37_batch_real.py | 8/8 | không đổi so với Ver 3.7 |
| **test_v37_1_patch.py** | **7/7** | **MỚI — xác nhận vá Bug 1 + Bug 2 GPT nêu** |
| **test_v38_outline_studio.py** | **23/23** | **MỚI — acceptance test Outline Studio** |

Đã verify **portable**: copy sang `/tmp/v38_check` (thư mục khác hẳn), chạy
lại `test_v37_1_patch.py` và `test_v38_outline_studio.py` — vẫn xanh.

## Chi tiết test patch (`test_v37_1_patch.py`)

| Test | Kịch bản | Kết quả |
|---|---|---|
| PATCH-A1 | Batch 5 record, record #2 ném `RuntimeError` thật (không phải `{'ok': False}`) | 4/5 record còn lại vẫn chạy xong — batch không chết |
| PATCH-A2 | Đối chiếu DB record crash | `trang_thai=loi`, lý do có ghi rõ tên exception |
| PATCH-A3 | Nút Sinh/Đăng sau batch có crash | Mở lại `normal`, không kẹt disabled |
| PATCH-A4 | Nút Dừng sau batch có crash | Khoá lại `disabled`, không kẹt normal |
| PATCH-B1 | POST tạo mới timeout + dò slug lại cũng lỗi mạng (đúng kịch bản GPT fault-inject) | Trả `ok=False`, lỗi rõ ràng, KHÔNG thử tạo lại |
| PATCH-B2 | Đếm số lần POST vào collection endpoint trong kịch bản trên | Đúng 1 lần — không đẻ `slug-2` |
| PATCH-B3 (đối chứng) | `wp_id` đã có sẵn từ trước (an toàn), lỗi dò slug chỉ tạm thời | Vẫn retry PUT thành công bình thường — xác nhận KHÔNG đổi hành vi cũ trong trường hợp an toàn |

## Chi tiết test Outline Studio (`test_v38_outline_studio.py`)

Nhóm A (module thuần, không cần UI) — đọc/ghi/trộn override, field lạ bị
bỏ qua, file hỏng không crash, `OUTLINE_NOI_DUNG` gốc bất biến.

Nhóm B (`xay_prompt()` thật) — xác nhận override thật sự đổi được nội dung
prompt gửi Gemini (không chỉ đổi ở tầng cfg), đồng thời `QUY_TAC_CHUNG`
(luật chống bịa số) và JSON schema **không hề bị ảnh hưởng** bởi bất kỳ
tuỳ chỉnh nào — đây là test quan trọng nhất, xác nhận "block AI" và "block
CODE/SCHEMA" tách biệt hoàn toàn.

Nhóm C (UI) — chọn outline, gõ, Lưu, Khôi phục mặc định, Xem trước hiển
thị đúng prompt thật (không phải bản Mock giả).

## Chưa test được trong sandbox này

- Gemini thật, WordPress thật — không đổi so với Ver 3.7, sandbox vẫn không có mạng ra ngoài.
- Test 2 file `.bat` trên Windows thật — không đổi ở Ver 3.7.1/3.8.
