# TEST-REPORT-VER50.md

## Ver 5.0 Claude — 30/07/2026

### Test mới: `test_v50_patch.py` — 22/22 PASS

| Nhóm | Test | Kết quả |
|---|---|---|
| **Vá MAX_TOKENS** | **thinkingConfig.thinkingBudget có mặt (W1-01)** | **PASS** |
| **Vá MAX_TOKENS** | **maxOutputTokens nâng lên 48000 (W1-02)** | **PASS** |
| **Vá MAX_TOKENS** | **thinkingBudget=6000, không phải 0 (W1-03)** | **PASS** |
| Title | Bỏ mã hàng, có "Báo Giá", vẫn còn công suất/thương hiệu (W2-01..03) | PASS |
| CTA | Có box-shadow, cỡ chữ 16px, không animation (W3-01, W3-02) | PASS |
| Bảng so sánh | Không truyền site → url luôn rỗng, an toàn ngược (W4-01) | PASS |
| Bảng so sánh | SKU đã đăng → url đúng, SKU chưa đăng → url rỗng (W4-02, W4-03) | PASS |
| Bảng so sánh | HTML có `<a href>` đúng cho SKU đã đăng, không có cho SKU chưa đăng (W4-04, W4-05) | PASS |
| Placeholder ảnh | Có emoji/chữ nhận diện, màu viền nổi bật (W5-01, W5-02) | PASS |
| Placeholder ảnh | Chèn đúng vị trí trong dung_bai_html, link SKU anh em xuất hiện đúng (W5-03, W5-04) | PASS |
| Đặc điểm | Guidance chia 2-3 đoạn, giới hạn chung cũng nhắc đoạn `<p>` (W6-01, W6-02) | PASS |
| Preview trình duyệt | Hàm + nút UI tồn tại đúng, dùng webbrowser chuẩn (W7-01..03) | PASS |

### Full regression toàn bộ test cũ (13 file, 2 file cập nhật theo hành vi mới)

| File | Kết quả | Ghi chú |
|---|---|---|
| test_gate2.py | 23/23 PASS | |
| test_phase2_full.py | 12/12 PASS | |
| test_round2_integration.py | 34/34 PASS | |
| test_v451_patch.py | 13/13 PASS | |
| test_v46.py | 20/20 PASS | |
| test_v47.py | 13/13 PASS | |
| test_v48.py | 10/10 PASS | |
| test_v49.py | 9/9 PASS | |
| test_v495_patch.py | 21/21 PASS | |
| test_v496_patch.py | 14/14 PASS | |
| test_v497_patch.py | 22/22 PASS | |
| test_v498_patch.py | 17/17 PASS | U5-01 cập nhật: kiểm tra chia 2-3 đoạn thay vì "1 đoạn liền mạch" |
| test_v499_patch.py | 32/32 PASS | V5-01 cập nhật: title KHÔNG còn mã hàng (đảo ngược Ver 4.9.9 theo yêu cầu Thịnh) |

**Tổng cộng: 240/240 PASS (test trước Ver 5.0) + 22/22 PASS (test mới) = 262/262.**

### Về việc "đảo ngược" quyết định Ver 4.9.9 (title có mã hàng)

Không phải hồi quy — đây là ĐIỀU CHỈNH THEO PHẢN HỒI THẬT sau khi Thịnh
xem trên site production. Ver 4.9.9 quyết định SKU-first (có mã hàng)
dựa trên khuyến nghị SEO tổng quát (Gemini). Ver 5.0 điều chỉnh sau khi
có bằng chứng thị giác thật (ảnh chụp site) cho thấy kết quả không như ý
muốn thẩm mỹ. Đã cập nhật test để phản ánh ĐÚNG quyết định mới nhất, có
ghi chú rõ lý do trong code, không xoá âm thầm.

### Việc chỉ Thịnh làm được

1. **Quan trọng nhất: chạy lại batch thật (≥10-20 sản phẩm), quan sát
   log có còn "Bài bị cắt vì vượt giới hạn token" không.** Nếu vẫn còn
   xảy ra (dù ít hơn), cần điều chỉnh thêm `thinkingBudget` (giảm xuống
   nếu vẫn cắt do budget quá cao, hoặc đây là dấu hiệu cần bớt field
   trong prompt).
2. Xem trang sản phẩm mới — xác nhận title/CTA/bảng so sánh/placeholder
   ảnh hiển thị đúng ý.
3. Test nút "Mở trong trình duyệt" trên máy Windows thật (sandbox test
   không mở được trình duyệt thật, chỉ verify code/logic).
4. Bắt đầu chèn ảnh thật vào các bài đã đăng (placeholder đã đánh dấu rõ
   vị trí).
