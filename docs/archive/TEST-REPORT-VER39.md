# TEST-REPORT-VER39.md

## Command chạy lại y hệt (đã verify portable từ /tmp/v39_check)

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
rm -rf *.db __pycache__ cau-hinh.env outline-tuy-chinh.json anh-bang-chung-ui
xvfb-run -a --server-args="-screen 0 1366x768x24" python3 test_v39_article_jobs.py
```
(Trên Windows: bỏ `xvfb-run -a`, chạy thẳng `python test_xxx.py`.)

## Kết quả tổng

**242/242 PASS, 0 FAIL.**

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
| test_ver3_ui.py | 8/8 | **sửa I1/I4**: 6 tab → 7 tab (thêm Article Jobs) |
| test_v34_that_ui.py | 8/8 | không đổi |
| test_v37_batch_real.py | 8/8 | không đổi |
| test_v37_1_patch.py | 7/7 | không đổi |
| test_v38_outline_studio.py | 23/23 | không đổi |
| **test_v39_article_jobs.py** | **23/23** | **MỚI — acceptance test Article Jobs** |

Đã verify **portable**: copy sang `/tmp/v39_check` (thư mục **đã đổi tên
đúng** `Lotech-Autopost-Ver3.9`, khác hẳn thư mục gốc), chạy lại
`test_v39_article_jobs.py` — vẫn xanh.

## Chi tiết test mới (`test_v39_article_jobs.py`)

**Nhóm A — CRUD `article_jobs` thuần (không cần UI):** tạo job mặc định
idempotent (chọn lại không tạo trùng), sequence tự tăng khi thêm job,
outline lấy đúng từ routing sẵn có, đổi outline/xoá job CHỈ khi PENDING —
job đã SUCCESS thì khoá cứng, không sửa/xoá được.

**Nhóm B — `render_phase2.py`:** job đầu tiên giữ nguyên slug như luồng
cũ (không phá bài thật đã đăng từ Ver 3.4-3.8), job 2/3 có slug khác nhau
và khác job 1.

**Nhóm C — `ai_wp_adapter.dang_wp_that()`:** đây là test quan trọng nhất
— giả lập 1 record ĐÃ có bài đăng qua luồng cũ Ver 3.7 (`wp_id=111` trong
`bai_viet_phase2`), sau đó tạo 1 Article Job MỚI cho CHÍNH record đó. Xác
nhận job mới PHẢI tạo bài MỚI (wp_id=222), TUYỆT ĐỐI không đọc nhầm/đè lên
wp_id=111 của luồng cũ. Đối chứng: job đã có wp_id riêng (chạy lại lần 2)
vẫn PUT đúng vào ID của chính nó.

**Nhóm D — UI đầy đủ:** tạo job mặc định cho 3 sản phẩm đã chọn, "+ Thêm
job" đổi outline theo dropdown, "- Xoá job" chỉ xoá được job PENDING, chạy
batch 3 job với 1 job cố ý lỗi (Gemini giả lập) không chặn 2 job còn lại,
nút Đăng/Dừng reset đúng sau batch, xác nhận `jobs_dung_lai` là Event
HOÀN TOÀN riêng biệt với `v3_dung_lai` của luồng Ver 3.7.

## Chưa test được trong sandbox này

- Gemini thật, WordPress thật cho luồng Job — sandbox không có mạng ra ngoài.
- 2 file `.bat` trên Windows.
- Chạy job với số lượng lớn (>20) để đo thời gian thật.
