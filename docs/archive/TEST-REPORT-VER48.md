# TEST-REPORT-VER48.md

## Kết quả tổng

**341/341 PASS, 0 FAIL** (331 cũ không đổi + 10 mới).

Đã verify portable từ `/tmp/v48_check` (thư mục đổi tên đúng
`Lotech-Autopost-Ver4.8-Claude`).

## Chi tiết `test_v48.py` (10 test)

| Test | Kịch bản | Kết quả |
|---|---|---|
| CHM-FILE-1/2/3 | Chuẩn hoá từ 1 file gộp (không phải thư mục) chạy đúng, nhận đúng định dạng, record_id khớp 100% | PASS |
| CHM-DIR-1 | Vẫn chạy được với thư mục kiểu cũ (tương thích ngược) | PASS |
| CHM-ERR-1 | Nguồn không tồn tại báo lỗi rõ ràng | PASS |
| **WOO-RECOVER-1/2** | Đúng kịch bản thật: tạo mới bị từ chối vì trùng SKU -> tự tra lại -> tìm thấy -> chuyển sang cập nhật thành công, chỉ thử tạo đúng 1 lần | PASS |
| WOO-RECOVER-3 | Đối chứng: tra lại vẫn không thấy -> báo lỗi rõ ràng, KHÔNG lặp vô hạn | PASS |
| LICHSU-1/2 | `goi_ai_co_du_phong()` trả đủ lịch sử từng lần thử, ghi rõ model từng lần | PASS |

## Chưa test được

- Chạy thật với WooCommerce/site thật để xác nhận lỗi trùng SKU đã hết.
- Chưa xác nhận 100% nguyên nhân gốc lỗi tra SKU lần đầu không tìm ra (lớp phục hồi là phòng thủ, không phải fix tận gốc nguyên nhân chưa rõ).
