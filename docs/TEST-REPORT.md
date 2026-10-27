# TEST REPORT — Ver 4.4.1.7 — 13/08/2026

`python3 run_tests.py`, Ubuntu 24 / Python 3.12, một lần chạy thật.

## 73 file PASS / 4 file FAIL
Cả 4 FAIL đã đối chứng **FAIL Y HỆT trên ZIP gốc 4.4.1.4** (`/tmp/goc`):
`test_v30` + `test_v31_va_loi` (thiếu `fitz`), `test_v39_a1_layout`
(thiếu `scrot`), `test_v441_meta_failsoft` (hardcode `/mnt/data/`).

## `tests/test_v4417_chuyen_dataset.py` — 9/9 PASS, KHÔNG skip
1. **Tái hiện sự cố 13/08** — 243 record khớp, 2 record đổi SKU (sửa
   newline): chuyển 243, mồ côi 2, mồ côi **giữ nguyên không xoá**.
2. **JOIN của `dashboard()` sống lại** — trước khi chuyển JOIN=0 (đúng
   trạng thái hỏng), sau khi chuyển JOIN=2.
3. `wp_id` giữ nguyên qua lần chuyển.
4. **KHÔNG ghi đè** bài đã có sẵn ở dataset mới (bản đang sống thắng).
5. Chạy lại lần hai không làm gì thêm.
6. Báo cáo rõ record mồ côi **có wp_id** — bài thật sắp mất liên kết.
7. Không có dataset cũ thì không vỡ.
8. **Gọi sai thứ tự** (trước `ghi_san_pham`) thì báo lỗi chứ không im lặng
   và không đụng dữ liệu.
9. `article_jobs` đi theo.

## Các bản trước giữ nguyên
`test_v4416_ux_va_retry` 19/19 · `test_v4415_sweep_rac` 10/10

## KHÔNG test được ở đây
Toàn bộ phần gọi HTTP thật (retry 403, GET verify, đọc bài từ WordPress).
Sandbox không ra mạng ngoài — **chưa chạy thật lần nào**.
