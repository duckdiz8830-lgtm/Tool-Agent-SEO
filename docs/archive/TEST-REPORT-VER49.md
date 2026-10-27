# TEST-REPORT-VER49.md

## Kết quả tổng

**350/350 PASS, 0 FAIL** (341 cũ, cộng 1 test cũ (`test_v47.py` DP-3) đổi
kịch bản cho khớp thay đổi có chủ đích, + 9 mới).

Đã verify portable từ `/tmp/v49_check` (thư mục đổi tên đúng
`Lotech-Autopost-Ver4.9-Claude`).

## Chi tiết `test_v49.py` (9 test)

| Test | Kịch bản | Kết quả |
|---|---|---|
| SKU-STATUS-1 | Tra SKU mặc định gửi `status=any` (vá bug thật) | PASS |
| SKU-STATUS-2 | Truyền `trang_thai='trash'` gửi đúng `status=trash` | PASS |
| **TRASH-1** | Đúng tình huống thật (ảnh Thịnh gửi): SKU bị giữ bởi sản phẩm trong thùng rác — báo lỗi rõ ràng, có ID cụ thể | PASS |
| TRASH-2 | KHÔNG tự động khôi phục/xoá thùng rác | PASS |
| **FAQ-DROP-1/2/3/4** | Chỉ FAQ lỗi -> tự bỏ FAQ, coi thành công, giữ nguyên nội dung khác, không cần đổi cặp key/model | PASS |
| **FAQ-DROP-5** | Đối chứng: lỗi ở field CỐT LÕI (không chỉ FAQ) -> KHÔNG tự ý bỏ qua | PASS |

## Chưa test được

- Chạy thật với site thật để xác nhận lỗi trùng SKU đã hết (kể cả case trong thùng rác, sau khi Thịnh tự xoá vĩnh viễn).
- HTTP 503 "high demand" — không phải lỗi code, không kiểm soát được.
