# TEST-REPORT-VER498.md

## Ver 4.9.8 Claude — 29/07/2026

### Test mới: `test_v498_patch.py` — 17/17 PASS

| Nhóm | Test | Kết quả |
|---|---|---|
| CTA | Dùng class btn-goi/btn-zalo đồng bộ CTA gọn (U1-01, U1-02) | PASS |
| CTA | Vẫn giữ id="lien-he-bao-gia" — không phá anchor nút Yêu cầu báo giá (U1-03) | PASS |
| CTA | Bọc div.lotech-cta-cuoi để CSS style riêng (U1-04) | PASS |
| CTA | Không hotline vẫn giữ anchor, không crash (U1-05) | PASS |
| So sánh công suất | Tìm đúng 6 SKU anh em thật cho MBT3P250A2608 (U2-01) | PASS |
| So sánh công suất | Bảng chứa mã hàng anh em thật (U2-02) | PASS |
| So sánh công suất | ẨN đúng cột Cấp điện áp (dữ liệu MASTER lỗi) (U2-03) | PASS |
| So sánh công suất | Dùng class lotech-so-sanh-table (U2-04) | PASS |
| So sánh công suất | Rỗng/None -> trả rỗng, không crash (U2-05, U2-06) | PASS |
| Class CSS | Khối chung máy biến áp bọc div.lotech-khoi-chung (U3-01) | PASS |
| Wiring | dung_bai_html() chèn đúng bảng so sánh khi có cung_dong (U4-01) | PASS |
| Wiring | Không chèn khi không truyền cung_dong — an toàn ngược (U4-02) | PASS |
| Wiring | HTML dùng CTA nút mới, không còn đoạn văn cũ (U4-03) | PASS |
| Prompt | dac_diem_html yêu cầu 1 đoạn liền mạch (U5-01) | PASS |
| Prompt | Vẫn giữ rule cũ "không bịa loại máy" sau khi sửa (U5-02) | PASS |

### Full regression toàn bộ test cũ

| File | Kết quả |
|---|---|
| test_gate2.py | 23/23 PASS |
| test_phase2_full.py | 12/12 PASS |
| test_round2_integration.py | 34/34 PASS |
| test_v451_patch.py | 13/13 PASS |
| test_v46.py | 20/20 PASS |
| test_v47.py | 13/13 PASS |
| test_v48.py | 10/10 PASS |
| test_v49.py | 9/9 PASS |
| test_v495_patch.py | 21/21 PASS |
| test_v496_patch.py | 14/14 PASS |
| test_v497_patch.py | 22/22 PASS |

**Tổng cộng: 191/191 PASS (test trước Ver 4.9.8) + 17/17 PASS (test mới) = 208/208.**

### Phát hiện phụ đáng chú ý (không phải bug tool)

Cột "Cấp Điện Áp (kV)" trong MASTER bị sai dữ liệu ở nhiều dòng máy biến
áp — giá trị trùng công suất thay vì đúng cấp điện áp thật (VD SKU 100kVA
ghi "100 kV"). Phát hiện khi build bảng so sánh (nhiều dòng cạnh nhau lộ
rõ pattern sai). Đã né bằng cách ẩn cột này khỏi bảng so sánh mới — KHÔNG
tự sửa dữ liệu MASTER, đây là quyết định của Thịnh.

### Việc chỉ Thịnh làm được

1. **Dán `lotech-theme.css` vào WordPress > Giao diện > Tùy biến > CSS bổ
   sung** (1 lần, áp dụng mọi bài sau đó) — nếu không dán, HTML vẫn đúng
   cấu trúc/class nhưng hiển thị theo style mặc định của theme, không có
   màu nút/bảng như demo.
2. Kiểm tra lại cột "Cấp Điện Áp (kV)" trong MASTER — xác nhận có đúng là
   lỗi nhập liệu không, sửa lại nếu cần.
3. Đọc thử 2-3 bài máy biến áp mới sinh (SKU có ≥2 SKU anh em cùng dòng để
   thấy bảng so sánh) — xác nhận hiển thị đúng khi lên WordPress thật.
