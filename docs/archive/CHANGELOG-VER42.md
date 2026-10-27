# CHANGELOG-VER42.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER41.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 4.2 — Tách block Hero/Specs/CTA theo chuẩn High-end Content — 26/07/2026

Bước đầu tiên trong lộ trình đạt High-end Content đã thống nhất với
Thịnh (định nghĩa: Dữ liệu thật + giao diện tra cứu nhanh + CTA rõ ràng +
code/rule kiểm soát phần kỹ thuật, AI chỉ làm phần ngôn ngữ).

### Thay đổi

**Thêm Block Hero** (`khoi_hero()`) — mở đầu bài viết, 100% dựng từ dữ
liệu record + cấu hình site, KHÔNG qua AI:
- Mã hàng, Thương hiệu.
- Tối đa 6 thông số chính (lấy từ `effective_cot_bang`, field trống tự ẩn — đúng nguyên tắc "thiếu dữ liệu thì ẩn, không ghi N/A").
- Giá: Liên hệ.
- CTA gọn (Gọi điện / Zalo / Yêu cầu báo giá).

**CTA xuất hiện đúng 3 vị trí** theo chuẩn đã chốt:
1. Hero (đầu trang) — `khoi_cta_ngan()`, dạng nút gọn.
2. Ngay sau bảng thông số kỹ thuật — `khoi_cta_ngan()`, cùng dạng gọn.
3. Cuối trang — `khoi_cta()`, dạng đầy đủ, **giữ NGUYÊN 100% như Ver
   3.4-4.1** (test `CTA-4` xác nhận output y hệt ký tự, không đổi hành vi
   cũ — bài đã đăng cũ không bị ảnh hưởng gì nếu chạy lại).

### Nguyên tắc giữ đúng khi thiết kế

- Hero **không đi qua `sanitize_html()`** — cùng nguyên tắc với bảng
  thông số/CTA cũ: block do code dựng từ dữ liệu đã kiểm soát, không phải
  nội dung AI viết nên không cần lọc HTML của AI.
- Đổi `ai_data` (kể cả rỗng) **không ảnh hưởng** nội dung Hero — test
  `HERO-5` xác nhận Hero độc lập hoàn toàn với AI.
- Không sửa `khoi_cta()` gốc — chỉ thêm hàm mới `khoi_cta_ngan()` cho 2 vị
  trí mới, tránh rủi ro đổi hành vi CTA cuối trang đã chạy ổn định qua
  nhiều bản.

### File sửa

- `render_phase2.py` — thêm `khoi_hero()`, `khoi_cta_ngan()`, nối vào
  `dung_bai_html()`. `khoi_cta()` không đổi.
- `giao-dien.py` — chỉ đổi tiêu đề app "VER 4.2".

### File mới

- `test_v42_hero_cta.py` — 12 test (Hero content, CTA đúng 3 vị trí và
  đúng thứ tự, `khoi_cta()` backward-compat, regression schema/service).

### Chưa làm (đúng lộ trình đã chốt, để dành 4.3+)

- Quality Gate chấm điểm 0-100 (Ver 4.3).
- Sản phẩm liên quan, code tự tìm theo profile/cấp điện áp/brand (Ver 4.4).
- Checklist yêu cầu báo giá theo rule/profile (Ver 4.5).
- Block Tài liệu kỹ thuật — cần dữ liệu nguồn catalogue trước (Ver 4.6).
- CSS/style cho các class mới (`lotech-hero`, `lotech-cta-ngan`, `btn-goi`...) — thuộc theme WordPress, ngoài phạm vi code Python.
