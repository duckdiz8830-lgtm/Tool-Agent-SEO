# TEST-REPORT-VER42.md

## Kết quả tổng

**277/277 PASS, 0 FAIL** (265 cũ không đổi + 12 mới).

Chạy y hệt cách các bản trước, thêm `python3 test_v42_hero_cta.py` vào bộ
lệnh (xem `TEST-REPORT-VER41.md` cho danh sách đầy đủ). Đã verify portable
từ `/tmp/v42_check` (thư mục đổi tên đúng `Lotech-Autopost-Ver4.2`).

## Chi tiết test mới (`test_v42_hero_cta.py`)

| Test | Kịch bản | Kết quả |
|---|---|---|
| HERO-1..4 | Hero xuất hiện đầu HTML, có Mã hàng/Thương hiệu/Giá | PASS |
| HERO-5 | Hero độc lập với AI — đổi `ai_data` không ảnh hưởng | PASS |
| CTA-1 | CTA gọn xuất hiện đúng 2 lần (Hero + sau bảng specs) | PASS |
| CTA-2/3 | CTA đầy đủ vẫn ở cuối trang, đúng thứ tự Hero→Specs→CTA gọn→CTA cuối | PASS |
| **CTA-4** | `khoi_cta()` (CTA cuối trang) output **y hệt ký tự** Ver 3.4-4.1 — xác nhận không đổi hành vi cũ | PASS |
| CTA-5 | Không có hotline vẫn render an toàn, không crash | PASS |
| REG-1/2 | Regression: schema JSON-LD vẫn đúng 1 khối, dịch vụ vẫn không có schema | PASS |

## Chưa test được

- Hiển thị thật trên WordPress (CSS class mới cần theme style, chỉ kiểm tra được cấu trúc HTML/class name đúng, không kiểm tra được giao diện thật).
