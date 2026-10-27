# TEST-REPORT-VER499.md

## Ver 4.9.9 Claude — 29/07/2026

### Test mới: `test_v499_patch.py` — 31/31 PASS

| Nhóm | Test | Kết quả |
|---|---|---|
| CSS inline | CTA/Hero/bảng thông số dùng style="" (V1-01..03) | PASS |
| Bỏ dấu vết | HTML cuối cùng không còn chuỗi "lotech-" (V2-01) | PASS |
| Bỏ dấu vết | Vẫn giữ id neo chức năng (V2-02) | PASS |
| Delta context | Tier/SKU liền kề nhỏ-lớn tính đúng (V3-01..03) | PASS |
| Delta context | Tải ước tính có chú thích giả định cosφ (V3-04) | PASS |
| Delta context | Thiếu công suất/sai outline -> {} an toàn (V3-05, V3-06) | PASS |
| Đăng ký field | 6 field delta-context có trong CẢ profile lẫn outline cot_ai (V3-REG-*, 6 test) | PASS |
| **Hard Block** | **KHÔNG chặn khi AI viết đúng số delta context (V3-07)** | **PASS** |
| **Hard Block** | **VẪN chặn số % bịa không có trong delta context (V3-08)** | **PASS** |
| Boilerplate | Khối chung dưới 40 từ (thực tế 28) (V4-01) | PASS |
| Boilerplate | Vẫn phân biệt đúng dầu/khô (V4-02) | PASS |
| Title | SKU-first, có công suất/thương hiệu, không năm tháng (V5-01..04) | PASS |
| Title | Outline khác giữ hành vi cũ (V5-05) | PASS |
| Brand block | MBT có khối (data thật), brand chưa có nguồn -> rỗng (V6-01, V6-02) | PASS |
| Không bịa số | Không có "%" trong bất kỳ khối code cứng nào (V7-01) | PASS |
| Regression | cap_dien không đổi hành vi, field delta không lọt sang profile khác (V8-01, V8-02) | PASS |

### Full regression toàn bộ test cũ (12 file, có 3 file cập nhật theo hành vi mới)

| File | Kết quả | Ghi chú |
|---|---|---|
| test_gate2.py | 23/23 PASS | |
| test_phase2_full.py | 12/12 PASS | |
| test_round2_integration.py | 34/34 PASS | T2-09 cập nhật: kiểm tra style inline thay vì class="specs-table" |
| test_v451_patch.py | 13/13 PASS | |
| test_v46.py | 20/20 PASS | |
| test_v47.py | 13/13 PASS | |
| test_v48.py | 10/10 PASS | |
| test_v49.py | 9/9 PASS | |
| test_v495_patch.py | 21/21 PASS | |
| test_v496_patch.py | 14/14 PASS | |
| test_v497_patch.py | 22/22 PASS | 4 test cập nhật: chuỗi kiểm tra khớp nội dung rút gọn mới |
| test_v498_patch.py | 17/17 PASS | 6 test cập nhật: kiểm tra style inline thay vì class "lotech-*"/"btn-*" |

**Tổng cộng: 208/208 PASS (test trước Ver 4.9.9) + 31/31 PASS (test mới) = 239/239.**

### Về việc sửa 10 test cũ

Tất cả các chỗ sửa đều là do THAY ĐỔI HÀNH VI CÓ CHỦ ĐÍCH (bỏ class, rút
gọn boilerplate) — không phải nới lỏng tiêu chuẩn kiểm tra. Mỗi chỗ sửa
đều giữ nguyên Ý NGHĨA kiểm tra gốc (VD "bảng thông số không qua sanitizer"
vẫn kiểm tra y hệt, chỉ đổi cách nhận diện từ `class="specs-table"` sang
`style="`).

### Bằng chứng quan trọng nhất bản này: Delta Context không phá Hard Block

```
[PASS] V3-07: Hard Block KHÔNG chặn khi AI viết lại đúng số delta context (vi phạm: {})
[PASS] V3-08: Hard Block VẪN chặn số % bịa (15% tiết kiệm chi phí) không có trong delta context
```

Đây là rủi ro lớn nhất của cả cơ chế delta-context — nếu Hard Block chặn
nhầm số đã tính sẵn, batch đăng thật sẽ tốn quota vô ích (đúng vấn đề
"20 request/ngày" đã bàn trước đó). Đã verify bằng test thật, không chỉ
đọc code suy luận.

### Việc chỉ Thịnh làm được

1. **Xác nhận style inline sống sót qua WordPress thật** — chạy thử 2-3
   bài, kiểm tra nút bấm/bảng có màu đúng không (khác bug script cũ ở chỗ
   nếu có vấn đề chỉ là mất màu, không lộ chữ xấu).
2. Đọc thử 3-5 bài máy biến áp mới (có ≥2 SKU anh em) — xác nhận phần
   "Đặc điểm" giờ có nhắc so sánh với mã liền kề, không còn giống hệt bài
   khác cùng dòng.
3. Kiểm tra Title mới trên WordPress — xác nhận hiển thị đúng SKU-first,
   không bị cắt xén bởi theme.
4. Quyết định có viết Pillar page (dầu/khô) không — nếu có, gửi tao URL
   thật để wire link vào khối chung.
