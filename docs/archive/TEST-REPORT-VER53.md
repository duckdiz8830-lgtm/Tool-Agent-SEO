# TEST-REPORT-VER53.md

## Ver 5.3 Claude — 30/07/2026

### Test mới: `tests/test_v53_patch.py` — 30/30 PASS

| Nhóm | Test | Kết quả |
|---|---|---|
| B5 — cập nhật bài đã đăng | Checkbox tồn tại, mặc định TẮT, nhánh không-skip đúng, log rõ ràng (4 test) | PASS |
| B6 — Hard Block fail nhanh | Bằng mock thật: Hard Block → đúng 1 lần gọi AI; lỗi mạng → vẫn 3 lần thử như cũ (3 test) | PASS |
| C6 — Khối "Về lõi" | Đúng nội dung Silic/Amorphous, KHÔNG có %, rỗng cho vỏ/không rõ loại (5 test) | PASS |
| C7 — Khối "Bảo trì" | Đúng nội dung dầu/khô, rỗng cho vỏ (3 test) | PASS |
| C8 — Bullet/in đậm | Rule 12 có trong QUY_TAC_CHUNG, whitelist đã sẵn strong/ul/li (3 test) | PASS |
| C9 — Grid liên quan | CSS Grid thay list, giữ đủ link/tên, rỗng khi không có (3 test) | PASS |
| C10 — Nút catalogue | Rỗng khi chưa có link, hiện đúng khi có, field optional đúng cả 4 profile (3 test) | PASS |
| Wiring thật | Cả 5 tính năng xuất hiện/ẩn đúng trong `dung_bai_html()` (5 test) | PASS |
| Import | MASTER import không crash dù thêm cột mới (1 test) | PASS |

### Full regression toàn bộ test cũ (21 file chạy được trong sandbox)

| File | Kết quả | Ghi chú |
|---|---|---|
| test_gate2.py | 23/23 PASS | |
| test_phase2_full.py | 36/36 PASS | |
| test_snapshot_regex.py | 39/39 PASS | |
| test_that_mocked.py | 21/21 PASS | |
| test_round2_integration.py | 16/16 PASS | |
| test_v41_chuan_hoa_master.py | 13/13 PASS | |
| test_v41_gemini_hardblock.py | 10/10 PASS | |
| test_v42_hero_cta.py | 13/13 PASS | |
| test_v451_patch.py | 13/13 PASS | |
| test_v46.py | 20/20 PASS | |
| test_v47.py | 13/13 PASS | DP-3 cập nhật theo hành vi B6 mới |
| test_v48.py | 10/10 PASS | |
| test_v49.py | 9/9 PASS | |
| test_v495_patch.py | 21/21 PASS | |
| test_v496_patch.py | 14/14 PASS | |
| test_v497_patch.py | 22/22 PASS | |
| test_v498_patch.py | 17/17 PASS | |
| test_v499_patch.py | 32/32 PASS | |
| test_v50_patch.py | 22/22 PASS | |
| test_v51_patch.py | 20/20 PASS | X1-03 cập nhật theo tham số mới |
| test_v52_patch.py | 17/17 PASS | |
| test_v53_patch.py | 30/30 PASS | Mới |

**Tổng: 21/21 file chạy được đều 100% PASS (481 test case cộng dồn). 9/30
file cần tkinter — KHÔNG XÁC ĐỊNH trong sandbox này, cần Thịnh tự chạy
trên Windows.**

### Hồi quy thật tự phát hiện + vá TRƯỚC khi đóng gói (không lọt ra ngoài)

Lần chạy full regression ĐẦU TIÊN của bản này phát hiện
`test_phase2_full.py::Test 10` lệch số (165→141 dòng bug kVA/kV) — do
`validators.py::validate_may_bien_ap()` chưa cập nhật gate theo outline
mới `outline_vo_may_bien_ap` (tách ở Ver 5.2), khiến ~24 dòng "Vỏ mạ
kẽm..." bị bỏ sót bước tự sửa bug kVA/kV. Đã vá (mở rộng gate), chạy lại
ĐỦ 30 file, đếm chính xác số dòng `[FAIL]` (thay vì chỉ đọc dòng tổng kết
cuối — cách cũ suýt khiến lỗi này lọt qua vì đọc nhầm dòng tổng kết của 1
file khác trong log). Xác nhận 0 FAIL thật trước khi đóng gói giao.

### Về 2 test bị sửa (không phải hồi quy)

`test_v47.py::DP-3` và `test_v51_patch.py::X1-03` đổi kỳ vọng vì hành vi
CÓ CHỦ ĐÍCH thay đổi ở chính bản này (B6 — Hard Block fail-fast; B5 —
thêm tham số mới vào hàm batch). Cả 2 đều có comment giải thích rõ lý do
ngay trong code test, không xoá âm thầm.

### Việc chỉ Thịnh làm được

1. Test nút "Cập nhật lại bài đã đăng" trên batch thật nhỏ (1-2 sản phẩm
   đã đăng cũ như KPK250CU) — xác nhận nội dung mới thật sự lên site.
2. Quan sát log qua vài chục sản phẩm xem tần suất Hard Block có giảm số
   request tốn phí không so với trước.
3. Đọc thử vài bài mới — xác nhận khối "Về lõi"/"Bảo trì" đọc hợp lý.
4. Khi có PDF catalogue thật, thêm cột "Catalogue PDF URL" vào MASTER
   (không bắt buộc) để bật nút Tải Catalogue.
