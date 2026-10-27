# TEST-REPORT-VER45.md

## Kết quả tổng

**293/293 PASS, 0 FAIL** (277 cũ không đổi + 16 mới).

Chạy y hệt cách các bản trước, thêm `python3 test_v45_checklist_lien_quan.py`
vào bộ lệnh. Đã verify portable từ `/tmp/v45_check` (thư mục đổi tên đúng
`Lotech-Autopost-Ver4.5`).

## Chi tiết test mới (`test_v45_checklist_lien_quan.py`)

| Test | Kịch bản | Kết quả |
|---|---|---|
| CK-1/2/3 | Checklist đúng theo từng profile, profile lạ trả rỗng an toàn | PASS |
| LQ-1/2/3 | HTML builder: rỗng không hiện block, item thiếu ten/url bị bỏ qua | PASS |
| **LQ-DB-1** | Sản phẩm CHƯA đăng thật (không có `wp_url`) **không được** xuất hiện trong danh sách liên quan | PASS |
| LQ-DB-2/3 | Không trả sản phẩm khác profile, không trả chính record đang xét | PASS |
| **LQ-DB-4** | Ưu tiên đúng: cùng cấp điện áp + thương hiệu đứng trước chỉ cùng thương hiệu | PASS |
| LQ-DB-5/6 | URL đúng dữ liệu đã lưu; không có ứng viên nào thì trả rỗng an toàn | PASS |
| E2E-1/2/3 | `dung_bai_html()` có đủ checklist + sản phẩm liên quan, đúng thứ tự | PASS |
| E2E-4 | Không truyền tham số mới -> không hiện block, backward compatible | PASS |

## Chưa test được

- Nối thật qua WordPress (cần Thịnh chạy thật để thấy block Sản phẩm liên quan chỉ hiện khi đã có ≥1 sản phẩm khác cùng profile đã đăng — batch đầu tiên của 1 profile mới sẽ chưa có gì để liên kết, đây là hành vi ĐÚNG, không phải lỗi).
