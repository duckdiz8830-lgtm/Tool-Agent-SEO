# TEST-REPORT-VER495.md

## Ver 4.9.5 Claude — 29/07/2026

### Test mới: `test_v495_patch.py` — 21/21 PASS

| Nhóm | Test | Kết quả |
|---|---|---|
| Registry | Assert field cấm tuyệt đối không lọt (R1-01) | PASS |
| Registry | outline_dau_cap_ky_thuat tồn tại (R1-02) | PASS |
| Registry | 6 field enrich trong cot_ai (R1-03) | PASS |
| Registry | nguon_catalogue chỉ trong cot_noi_bo, không lọt cot_ai/cot_bang (R1-04) | PASS |
| Backward compat | Import MASTER GỐC (chưa enrich) không crash — 1332 dòng (R2-01) | PASS |
| Backward compat | Field enrich rỗng khi cột không tồn tại (R2-02) | PASS |
| Backward compat | Không dòng nào route sai sang outline mới khi chưa enrich (R2-03) | PASS |
| Import enrich | Đúng 90/90 SKU route sang outline_dau_cap_ky_thuat (R3-01) | PASS |
| Import enrich | Field kỹ thuật có giá trị thật (R3-02) | PASS |
| Import enrich | nguon_catalogue có giá trị dùng cho routing (R3-03) | PASS |
| Prompt | Field mới xuất hiện trong prompt (R4-01) | PASS |
| Prompt | Không lộ Giá List/gia_list (R4-02) | PASS |
| Prompt | Field thiếu vào đúng mục "DỮ LIỆU KHÔNG CÓ" (R4-03) | PASS |
| Bảng thông số | Chứa cột kỹ thuật mới (R5-01) | PASS |
| Bảng thông số | Không lộ giá (R5-02) | PASS |
| Schema | Vẫn KHÔNG có offers/price — quyết định cũ giữ nguyên (R5-03) | PASS |
| Schema | additionalProperty có field mới (R5-04) | PASS |
| Regression | cap_dien import bình thường — 3387 dòng (R6-01) | PASS |
| Regression | tu_va_thiet_bi_dong_cat import bình thường — 300 dòng (R6-02) | PASS |
| Regression | may_bien_ap_do_luong import bình thường — 245 dòng (R6-03) | PASS |
| Regression | Field mới không lọt sang profile khác (R6-04) | PASS |

### Full regression 8 bộ test cũ — chạy lại sau khi sửa, KHÔNG có xáo trộn nào

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

**Tổng cộng: 134/134 PASS (test cũ) + 21/21 PASS (test mới) = 155/155.**

`test_v45_checklist_lien_quan.py` không chạy được trong môi trường test này
do thiếu module `tkinter` ở sandbox (file này `import giao-dien.py` full UI)
— không liên quan tới thay đổi của bản vá này, cần Thịnh tự chạy trên máy
Windows thật (đã có sẵn tkinter) để xác nhận, giống thông lệ các bản trước.

### Xác nhận riêng: không phá quyết định cũ

Trước khi merge, thử thêm `offers` vào Product Schema (nghĩ đây là "schema
đang lỗi" Thịnh nhắc) — chạy `test_gate2.py` phát hiện ngay `D1 FAIL` vì
test cũ khẳng định rõ "không có Offer" là quyết định có chủ đích. Đã revert
trước khi đóng gói, không có bản build nào từng chứa thay đổi sai này.

### Việc chỉ Thịnh làm được

1. Test import thật `5MASTER_ENRICHED_TRIAL.xlsx` qua UI (tab Nhập dữ liệu)
   trên Windows, xác nhận 90 SKU hiện đúng trong bảng Sản phẩm.
2. Sinh thử 3-5 bài thật (Gemini thật) cho nhóm outline_dau_cap_ky_thuat,
   đọc lại xem content có dày hơn nhóm outline_phu_kien cũ không.
3. Xác nhận lại xem "schema đang lỗi" Thịnh nhắc có phải là vụ thiếu
   offers hay là lỗi khác — gửi ảnh chụp/thông báo cụ thể nếu có.
