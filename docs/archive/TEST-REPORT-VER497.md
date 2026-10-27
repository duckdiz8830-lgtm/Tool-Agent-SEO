# TEST-REPORT-VER497.md

## Ver 4.9.7 Claude — 29/07/2026

### Test mới: `test_v497_patch.py` — 22/22 PASS

| Nhóm | Test | Kết quả |
|---|---|---|
| Đơn vị | Nhận diện "dầu"/"khô"/không có/rỗng-None (T1-01..04) | PASS |
| Đơn vị | Nhận diện 1Pha/3Pha/không có (T1-05..07) | PASS |
| Nội dung | Khối dầu có ONAN, không lẫn AN/AF (T2-01, T2-02) | PASS |
| Nội dung | Khối khô có AN/AF, không lẫn ONAN (T2-03, T2-04) | PASS |
| Nội dung | Khối khô nêu rõ KHÔNG dùng dầu (T2-05) | PASS |
| Nội dung | Tiêu chuẩn trích dẫn khác nhau đúng loại (T2-06) | PASS |
| An toàn | Sai outline (outline_do_luong) → luôn rỗng dù tên có "dầu" (T3-01) | PASS |
| An toàn | Không nhận diện được → rỗng, không đoán (T3-02) | PASS |
| An toàn | Row rỗng/thiếu field → không crash (T3-03) | PASS |
| Wiring | dung_bai_html() chèn đúng khối cho outline_may_bien_ap (T4-01) | PASS |
| Wiring | dung_bai_html() KHÔNG chèn cho outline_do_luong (T4-02) | PASS |
| Quét thật | 165 dòng outline_may_bien_ap từ MASTER không crash (T5-01) | PASS |
| Quét thật | Mọi dòng "dầu" → khối ONAN đúng, 0 lệch (T5-02) | PASS |
| Quét thật | Mọi dòng "khô" → khối đúng, 0 lệch (T5-03) | PASS |
| Quét thật | 73 dòng outline_do_luong không dòng nào dính khối máy biến áp (T5-04) | PASS |

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

**Tổng cộng: 169/169 PASS (test trước Ver 4.9.7) + 22/22 PASS (test mới) = 191/191.**

### Kết quả quét thật đáng chú ý

165 dòng `outline_may_bien_ap` trong MASTER: 141 dòng nhận đúng khối
dầu/khô, 24 dòng "Vỏ mạ kẽm nhúng nóng MBA..." (phụ kiện vỏ, không phải
máy biến áp hoàn chỉnh) đúng là không nhận khối nào — hàm xử lý an toàn,
không gán nhầm nguyên lý làm mát cho phụ kiện.

### Việc chỉ Thịnh làm được

1. Đọc thử 3-5 bài mới sinh (cả dòng dầu lẫn khô) — xác nhận khối mới đọc
   tự nhiên, không bị trùng lặp ý với phần AI viết phía trên.
2. Cân nhắc: 24 dòng "Vỏ mạ kẽm nhúng nóng" có nên route sang
   `outline_phu_kien` (giống "Giá treo MBT") thay vì `outline_may_bien_ap`
   không — hiện tại chúng vẫn dùng outline máy biến áp nhưng thiếu khối
   nguyên lý, có thể tạo cảm giác nội dung mỏng hơn các SKU khác cùng
   outline. Đây là quyết định phân loại, không phải bug.
