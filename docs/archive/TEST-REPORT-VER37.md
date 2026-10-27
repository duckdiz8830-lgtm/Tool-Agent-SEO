# TEST-REPORT-VER37.md

## Command chạy lại y hệt (từ thư mục gốc, đã verify portable từ /tmp/v37_check)

```
rm -rf *.db __pycache__ cau-hinh.env
python3 test_that_mocked.py
python3 test_gate2.py
python3 test_phase2_full.py
python3 test_snapshot_regex.py
python3 test_round2_integration.py
python3 test_v36_regression.py
rm -rf *.db __pycache__ cau-hinh.env
xvfb-run -a python3 test_v35_idempotency.py
rm -rf *.db __pycache__ cau-hinh.env
xvfb-run -a python3 test_round2_ui_smoke.py
rm -rf *.db __pycache__ cau-hinh.env anh-bang-chung-ui
xvfb-run -a --server-args="-screen 0 1366x768x24" python3 test_ver3_ui.py
rm -rf *.db __pycache__ cau-hinh.env anh-bang-chung-ui
xvfb-run -a --server-args="-screen 0 1366x768x24" python3 test_v34_that_ui.py
rm -rf *.db __pycache__ cau-hinh.env anh-bang-chung-ui
xvfb-run -a --server-args="-screen 0 1366x768x24" python3 test_v37_batch_real.py
```
(Trên Windows: bỏ `xvfb-run -a`, chạy thẳng `python test_xxx.py`.)

## Kết quả tổng

**189/189 PASS, 0 FAIL** (181 regression Ver 3.6 cũ — không đổi 1 test nào
ngoài `test_v34_that_ui.py` phải sửa theo hành vi mới — cộng 8 test mới
`test_v37_batch_real.py`).

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
| test_ver3_ui.py | 8/8 | không đổi |
| test_v34_that_ui.py | 8/8 | **sửa REAL-1/REAL-2**: thu hẹp selection về 1 record trước khi test Real (Ver 3.7 đổi `_v3_dang_draft_that` sang chọn-nhiều-record), bỏ assertion dựa vào `messagebox.showinfo` (không còn popup) |
| **test_v37_batch_real.py** | **8/8** | **MỚI — acceptance test Ver 3.7** |

Đã verify **portable**: copy toàn bộ thư mục sang `/tmp/v37_check` (khác
hẳn thư mục code gốc, mô phỏng giải nén ZIP trên máy khác), chạy lại
`test_v37_batch_real.py` — vẫn 8/8 PASS.

## Chi tiết 8 test mới (`test_v37_batch_real.py`)

Patch trực tiếp `ai_wp_adapter.goi_ai_that` / `ai_wp_adapter.dang_wp_that`
(thay vì giả `requests.post` thô) để test đúng phần code Ver 3.7 thật sự
thay đổi — vòng lặp/bỏ-qua/dừng-an-toàn trong `giao-dien.py` — không test
lại retry/idempotency nội bộ của 2 hàm adapter (đã có test riêng từ Ver
3.4/3.5, không đổi ở Ver 3.7).

| Test | Kịch bản | Kỳ vọng | Kết quả |
|---|---|---|---|
| T1 | Chọn 5 record, toàn bộ thành công | 5/5 da_dang, gọi AI đúng 5 lần | PASS |
| T1b | Đối chiếu DB sau T1 | 5/5 record `trang_thai=da_dang` | PASS |
| T2 | Chọn 17 record, cố ý làm record #5 lỗi (giả lập timeout) | 16/17 thành công, 1 lỗi — record 6-17 không bị chặn bởi lỗi của record 5 | PASS |
| T2b | Đối chiếu DB record lỗi | `trang_thai=loi`, có ghi lý do lỗi | PASS |
| T2c | Đối chiếu DB 16 record còn lại | Đủ 16/17 `da_dang` | PASS |
| T3 | Chạy lại ĐÚNG 17 record của T2 (lỗi đã "sửa" — Gemini trả OK cho tất cả lần này) | Chỉ gọi lại AI cho record đã lỗi trước đó (1 lần), 16 record `da_dang` cũ KHÔNG bị gọi lại — kết quả cuối 17/17 thành công, 16 "đã có từ trước" | PASS |
| T4 | Chọn 6 record mới, giả lập độ trễ mạng, bấm Dừng khẩn cấp sau khi 2 record đã xong | Record đã xong giữ nguyên `da_dang`, record chưa chạy ở trạng thái chờ (`chua_sinh`) — không kẹt, không mất dữ liệu | PASS |
| T4b | Chạy tiếp (không dừng) trên đúng 6 record của T4 | Hoàn tất đủ 6/6, chỉ gọi AI cho đúng số record còn thiếu (không đụng record đã `da_dang` từ T4) | PASS |

## Chưa test được trong sandbox này

- Gemini thật, WordPress thật — sandbox không có mạng ra ngoài (trừ domain pip/npm/github). Việc CHỈ Thịnh làm được: chạy batch thật N=5 → N=20 với Gemini/WordPress thật trên máy Thịnh, xác nhận Draft đúng số lượng, đúng nội dung trên WP Admin, không trùng bài.
- Test 2 file `.bat` trên Windows thật — không đổi ở Ver 3.7, không cần test lại.
