# TEST-REPORT-VER41.md

## Command chạy lại y hệt (đã verify portable từ /tmp/v41_check, thư mục đã đổi tên đúng Ver4.1)

```
rm -rf *.db __pycache__ cau-hinh.env outline-tuy-chinh.json
python3 test_that_mocked.py
python3 test_gate2.py
python3 test_phase2_full.py
python3 test_snapshot_regex.py
python3 test_round2_integration.py
python3 test_v36_regression.py
python3 test_v41_gemini_hardblock.py
python3 test_v41_chuan_hoa_master.py
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
rm -rf *.db __pycache__ cau-hinh.env outline-tuy-chinh.json anh-bang-chung-ui
xvfb-run -a --server-args="-screen 0 1366x768x24" python3 test_v39_article_jobs.py
```
(Trên Windows: bỏ `xvfb-run -a`, chạy thẳng `python test_xxx.py`.)

## Kết quả tổng

**265/265 PASS, 0 FAIL.**

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
| test_v34_that_ui.py | 8/8 | không đổi |
| test_v37_batch_real.py | 8/8 | không đổi |
| test_v37_1_patch.py | 7/7 | không đổi |
| test_v38_outline_studio.py | 23/23 | không đổi |
| test_v39_article_jobs.py | 23/23 | không đổi |
| **test_v41_gemini_hardblock.py** | **10/10** | **MỚI** |
| **test_v41_chuan_hoa_master.py** | **13/13** | **MỚI** |

## Chi tiết test Gemini + Hard Block (`test_v41_gemini_hardblock.py`)

| Test | Kịch bản | Kết quả |
|---|---|---|
| SCHEMA-1/2/3 | `_sang_gemini_schema()` chuyển đúng schema đơn giản sang định dạng Gemini (OBJECT/ARRAY/properties/required, faq không bắt buộc) | PASS |
| HB-1/HB-2 | Case thật từ log 26/07: "12.7KV"/"0.23KV" (nửa cặp điện áp sơ/thứ cấp có thật) không còn bị chặn nhầm | PASS |
| **HB-C1** | Giá trị bịa thật (99.9KV không có trong record) **vẫn phải bị chặn** | PASS |
| **HB-C2 (quan trọng nhất)** | Đúng SỐ (12.7) nhưng SAI HỌ đơn vị (A thay vì kV) — **vẫn phải bị chặn**, xác nhận không nới lỏng kiểu "thấy số là cho qua" | PASS |
| HB-C3 | Trường hợp bình thường (không qua lớp 4) vẫn hoạt động như cũ | PASS |
| HB-D1/D2 | Regression: case Hard Block cũ (Ver 3.4-3.9) không đổi hành vi | PASS |

## Chi tiết test Chuẩn hoá MASTER (`test_v41_chuan_hoa_master.py`)

Test qua ĐÚNG cách Thịnh sẽ chạy thật (subprocess dòng lệnh), rồi xác nhận
qua ĐÚNG hàm `nhan_dien_loai_nguon()` + `import_4_profile()` thật của app —
đây là bước GPT phát hiện tao đã bỏ sót lần giao trước.

| Test | Kịch bản | Kết quả |
|---|---|---|
| CHM-A1 | Chạy `chuan_hoa_master.py` qua dòng lệnh | PASS |
| CHM-B1/B2 | Sheet đầu tiên là sheet dữ liệu thật; `nhan_dien_loai_nguon()` nhận đúng `4_profile` | PASS |
| **CHM-C-*** | `record_id` khớp 100% với file gốc cho cả 4 profile (3387+300+245+1332 dòng) — điều kiện sống còn để không mất liên kết bài đã đăng | PASS |
| CHM-D1 | Không ô nào bị ghi đè sai giá trị gốc | PASS |
| CHM-E1/E2 | Regex không còn bắt nhầm VA/KVA thành V/kV | PASS |
| CHM-F1/F2 | Nội dung/Dashboard hợp lệ | PASS |

## Chưa test được trong sandbox này

- Gemini thật với `responseSchema` — cần Thịnh chạy thật để xác nhận tỷ lệ thành công tăng so với 0/10 ban đầu.
- 2 file `.bat` trên Windows.
