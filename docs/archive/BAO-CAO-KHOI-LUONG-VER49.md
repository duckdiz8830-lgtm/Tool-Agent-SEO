# BAO-CAO-KHOI-LUONG-VER49.md

| # | Trường | Nội dung |
|---|---|---|
| 1 | Thời gian | 1 phiên, có tra cứu web xác nhận 2 vấn đề trước khi code (WooCommerce status default, Gemini quota per-project) |
| 2 | File sửa | 3 — `autopost.py`, `ai_wp_adapter.py`, `giao-dien.py`, cộng cập nhật kịch bản `test_v47.py` |
| 3 | File mới | 1 — `test_v49.py` |
| 4 | Test mới | 9 |
| 5 | Tổng test | 350/350 PASS, 0 FAIL |
| 6 | Hoàn thành | Vá tận gốc lỗi trùng SKU (status=any); phát hiện + báo rõ case thùng rác; FAQ trở thành field có thể bỏ thay vì chặn cả bài |
| 7 | Chưa làm | HTTP 503 "high demand" từ Google — ngoài khả năng kiểm soát |
| 8 | Không test được | Chạy thật với site thật |
| 9 | Việc Thịnh làm | (a) Vào WordPress Admin > Products > Trash, xoá vĩnh viễn các sản phẩm cũ trùng SKU (VD MBT1P100A2608) nếu muốn tool tạo lại sạch. (b) Chạy lại batch, xem lỗi trùng SKU đã hết chưa. (c) Xem log có dòng "đã bỏ FAQ vì nội dung bất thường" — nếu có, xác nhận bài vẫn đăng đầy đủ phần khác, chỉ thiếu FAQ. |
| 10 | Rủi ro | Thấp — có test đối chứng đầy đủ cho từng nhánh quyết định. Rủi ro thật còn lại nằm ngoài code: quota Gemini theo project (đã xác nhận qua tài liệu Google) và lỗi 503 tạm thời từ Google. |
| 11 | Rủi ro pháp lý/bảo mật | Không có thay đổi mới. |
| 12 | ZIP | `Lotech-Autopost-Ver4.9-Claude.zip` |

## Quyết định đáng chú ý

**Không tự động xử lý sản phẩm trong thùng rác.** Cân nhắc giữa tự động
khôi phục (untrash) hoặc tự động xoá vĩnh viễn để giải phóng SKU — cả 2
đều là hành động ảnh hưởng dữ liệu thật trên site, không phải quyết định
Claude nên tự đưa ra thay Thịnh. Chọn: chỉ phát hiện + báo rõ vấn đề kèm
hướng dẫn cụ thể, để Thịnh tự quyết định và tự thao tác.
