# SPEC — Lotech Autopost MAIN

Nguồn gốc: Claude v2.3, giờ là nhánh MAIN duy nhất. Không còn bản GPT chạy song
song — bản GPT cũ đóng băng làm tài liệu tham khảo, không phát triển tiếp.

Vai trò: **Claude = lead dev, GPT = reviewer/test engineer, Thịnh = test và chốt scope.**

## LOTECH AUTOPOST VER 3 — Content Safety Gate 2 — scope đã đạt (25/07/2026)

Đổi tên phiên bản từ Round 2 sang **LOTECH AUTOPOST VER 3**. Gate 2 trong
chuỗi 4 Gate bắt buộc đã chốt thứ tự (work order): (1) Content Safety Gate 2
— **đã đạt**, (2) UI Ver 3 (chuyển Phase 2 thành luồng chính, ẩn RMU), (3)
Website Configuration, (4) WordPress Draft thật. Không được tự đổi thứ tự.

4 task Gate 2: Schema JSON-LD gắn vào HTML thật, mở rộng Hard Block (bảo
hành/IPxx/IEC-TCVN/nhiệt độ/%), 2 mẫu `chuan`/`ngan_gon` hoạt động thật khác
nhau, đổi tên phiên bản. **117/117 test PASS** — chi tiết `TIEN-DO.md` (bảng
bắt buộc) và `TEST-REPORT.md`.

Gate 2 KHÔNG bao gồm (đúng giới hạn work order, không phải thiếu sót):
thiết kế lại UI, nối `dang_wp_that()` vào nút, gửi request WordPress thật,
cấu hình website, đóng gói portable.

## Phase 2 — Round 2 — scope đã đạt (25/07/2026)

Nhánh SONG SONG với MAIN v0.1 (RMU) bên dưới — không thay thế, không đụng
code RMU. Phạm vi Round 2: nối Data Core (Round 1: Profile/Outline Registry,
import, validator, regex — xem `ARCHITECTURE-DRAFT-4-PROFILES.md`) thành
luồng giả lập hoàn chỉnh UI → import → chọn → prompt Phase 2 thật → AI mock →
HTML/bảng/schema → sanitize → WordPress mock → dashboard.

12 hạng mục bắt buộc (R2-01 → R2-12) + 12 test bắt buộc (T2-01 → T2-12) —
danh sách đầy đủ và trạng thái từng dòng nằm ở `TIEN-DO.md` (bảng theo dõi
bắt buộc). Toàn bộ đạt PASS, chi tiết PASS/FAIL từng test ở `TEST-REPORT.md`.

**Điều kiện nghiệm thu Round 2** (đối chiếu trực tiếp với `TEST-REPORT.md`):

| # | Tiêu chí | Trạng thái |
|---|---|---|
| 1 | UI nhập được MASTER | ĐẠT |
| 2 | Database lưu đủ 5.264 sản phẩm | ĐẠT |
| 3 | Chọn được 20 sản phẩm | ĐẠT |
| 4 | AI mock sinh được nội dung | ĐẠT |
| 5 | HTML và Schema được dựng đúng | ĐẠT |
| 6 | WP mock lưu được WP ID/URL | ĐẠT |
| 7 | Dashboard hiển thị đúng | ĐẠT |
| 8 | Multi-site không ghi đè | ĐẠT |
| 9 | Multi-outline không ghi đè | ĐẠT (field theo outline lọc đúng qua Outline Registry) |
| 10 | Hard Block cụm kỹ thuật PASS | ĐẠT (Composite Hard Block, R2-08) |
| 11 | Giá List không rò rỉ | ĐẠT (test động trên toàn bộ 5.264 record) |
| 12 | ZIP sạch | ĐẠT (không DB test, không key/mật khẩu) |
| 13 | Luồng RMU cũ không bị phá | ĐẠT (smoke test qua Xvfb, T2-11) |

**CHƯA đạt / ngoài phạm vi Round 2 (không phải trượt nghiệm thu — đúng ranh
giới đã định từ đầu)**: Gemini thật, WordPress thật, test UI trên Windows
thật — cả 3 chỉ Thịnh làm/xác nhận được, xem `KNOWN-ISSUES.md`.

## Scope MAIN v0.1 — đã đóng băng (nhánh RMU, không đổi)

Sáu việc, không hơn:

1. Nhập Excel nhiều sheet, chuẩn hoá, gộp mã trùng.
2. Chọn sản phẩm cần viết (tick chọn/bỏ theo dòng).
3. Chọn mẫu bài (outline) — hiện có `bao_gia`, `thong_so`, khai trong `prompts.py`.
4. Sinh liên tục N bài, lỗi bài nào lưu bài đó, không dừng cả lô.
5. Tắt máy giữa chừng, mở lại chạy tiếp đúng chỗ dừng.
6. Đăng WordPress dạng Draft, xuất dashboard Excel.

## Tạm gác — ghi backlog, chưa cho lên xe

- Pipeline ảnh hoàn chỉnh (resize, WebP, featured image, alt/caption tự động).
- Hệ thống nhiều outline/nhiều ngành hàng theo profile (tủ RMU, cáp điện, đầu
  cáp... mỗi ngành một bộ trường + outline riêng). Tầm nhìn đã chốt, xem
  `KNOWN-ISSUES.md` mục "Kiến trúc profile ngành hàng" để không quên hướng đi.
- Schema (Product/FAQPage) tuỳ biến sâu, bật/tắt từng khối theo tick chọn.
- Keyword ownership giữa các site (chống cannibalization).
- GSC, crawl website, rank tracking.
- Tối ưu giao diện sâu hơn mức đang có.
- **Dò model nâng cao và đóng gói Python portable** — chủ động gác lại từ
  v2.6 theo yêu cầu, tập trung vào luồng vận hành trước. Không phải quên,
  không cần nhắc lại ở báo lỗi vòng sau trừ khi có lỗi thật liên quan.

## Tiêu chí nghiệm thu MAIN v0.1

Đạt cả bảy dòng dưới đây thì dừng sửa lõi, chuyển sang dùng thật:

| # | Tiêu chí | Trạng thái |
|---|---|---|
| 1 | Import đúng file RMU (98 sản phẩm, đúng series) | ĐẠT |
| 2 | Sinh 30 bài demo (chế độ `thu`) | ĐẠT |
| 3 | Sinh 5 bài Gemini thật | **Chưa test — cần key thật** |
| 4 | Resume sau khi dừng | ĐẠT (mô phỏng, chưa test kill process thật) |
| 5 | Đăng 10 WordPress Draft | **Chưa test — cần WordPress thật** |
| 6 | Chạy lại không tạo slug -2 | ĐẠT (test bằng giả lập HTTP) |
| 7 | Excel dashboard khớp dữ liệu | ĐẠT |

Dòng 3 và 5 chỉ tay Thịnh test được — không có key/WordPress thật để tự chạy.

## Quy trình báo lỗi cho vòng tiếp theo

```
VERSION: Claude v2.x
LỖI: ...
CÁCH TÁI HIỆN: 1. 2. 3.
KẾT QUẢ HIỆN TẠI: ...
KẾT QUẢ MONG MUỐN: ...
FILE: ZIP + log
```

Một vòng sửa đúng một cụm lỗi đã nêu trong báo cáo, không tiện tay sửa thêm việc
khác cùng lúc. Xong thì đóng ZIP, kèm đủ 4 file: `SPEC.md` (file này),
`NHAT-KY-THAY-DOI.md` (= CHANGELOG), `KNOWN-ISSUES.md`, `TEST-REPORT.md`.
