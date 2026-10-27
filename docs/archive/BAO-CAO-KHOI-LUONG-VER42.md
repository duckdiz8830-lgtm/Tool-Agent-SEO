# BAO-CAO-KHOI-LUONG-VER42.md

| # | Trường | Nội dung |
|---|---|---|
| 1 | Thời gian | 1 phiên làm việc liên tục |
| 2 | File sửa | 2 — `render_phase2.py`, `giao-dien.py` (chỉ tiêu đề) |
| 3 | File mới | 1 — `test_v42_hero_cta.py` |
| 4 | Dòng diff | `render_phase2.py`: 213 dòng; test mới: 66 dòng |
| 5 | Test mới | 12 |
| 6 | Tổng test | 277/277 PASS, 0 FAIL |
| 7 | Hoàn thành | Block Hero (code-only), CTA 3 vị trí, giữ nguyên 100% CTA cuối trang cũ |
| 8 | Chưa làm | Quality Gate (4.3), sản phẩm liên quan (4.4), checklist báo giá (4.5), tài liệu kỹ thuật (4.6) |
| 9 | Không test được | Hiển thị CSS thật trên WordPress (cần theme style, ngoài phạm vi code) |
| 10 | Việc Thịnh làm | Xem thử 1 bài thật trên WordPress, đối chiếu Hero/CTA hiển thị ra sao, phối màu/style qua CSS theme (không phải việc code Python) |
| 11 | Rủi ro | Thấp — không sửa CTA cuối trang cũ (test xác nhận y hệt ký tự), Hero là block cộng thêm, không ai dùng phải chỉnh sửa gì |
| 12 | Rủi ro pháp lý | Không có |
| 13 | ZIP | `Lotech-Autopost-Ver4.2.zip` |

## Quyết định đáng chú ý

**Không sửa `khoi_cta()` gốc, chỉ thêm hàm mới cho 2 vị trí CTA còn lại.**
Vì `khoi_cta()` đã chạy ổn định từ Ver 3.4, sửa nó rủi ro cao hơn lợi ích
— test `CTA-4` khoá cứng output y hệt ký tự để đảm bảo mọi bản sau không
vô tình đổi hành vi này.
