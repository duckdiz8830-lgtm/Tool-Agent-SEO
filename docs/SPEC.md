# SPEC — SONEALEO (hiện tại, Ver 4.2)

Bản trước (`archive/SPEC-cu-lotech-ver3.md`) đã lỗi thời (còn ghi "LOTECH
AUTOPOST", nhắc "Ver 3" — không còn đúng từ lâu). File này thay thế, viết
ngắn, chỉ mô tả TRẠNG THÁI HIỆN TẠI — không phải lịch sử (lịch sử xem
`NHAT-KY-THAY-DOI.md`, hoặc chi tiết từng bản cũ trong `archive/`).

## Luồng chính

```
Excel MASTER (4 profile: cáp điện, tủ/đóng cắt, máy biến áp, phụ kiện)
  → nhap_phase2.py (import + Validation Gate chống lỗi dữ liệu)
  → SQLite (db_phase2.py)
  → ai_wp_adapter.py (gọi Gemini, có key/model dự phòng)
  → Hard Block (render_phase2.kiem_tra_bia — chặn AI bịa số)
  → [tuỳ chọn] enhance.py — Serper tìm SERP, rút insight cấu trúc
    (KHÔNG rút số liệu, 2 lớp lọc riêng)
  → render_phase2.py (HTML + bảng thông số + schema, code dựng, AI không đụng)
  → WordPress/WooCommerce (Draft only)
```

## File chính

| File | Vai trò |
|---|---|
| `giao-dien.py` | GUI Tkinter + orchestration (lớn, ~3.700 dòng — biết là "God Class", chưa refactor, xem Tracklog Backlog) |
| `nhap_phase2.py` | Import Excel + Validation Gate |
| `db_phase2.py` | SQLite: dataset, sản phẩm, bài viết, article jobs, lịch sử Enhance |
| `profiles.py` | Định nghĩa 4 profile + outline mỗi profile |
| `prompts_phase2.py` | Prompt Gemini viết nội dung |
| `ai_wp_adapter.py` | Gọi Gemini thật + đăng WordPress/WooCommerce |
| `render_phase2.py` | Dựng HTML/bảng thông số/schema + Hard Block chống bịa |
| `enhance.py` | Serper + rút insight cấu trúc + chống lặp + chống prompt injection |
| `cauhinh.py` | Đọc/ghi `cau-hinh.env` (secret — KHÔNG đóng gói khi giao bản) |

## Nguyên tắc cứng, không đổi

1. AI KHÔNG được tự bịa số liệu kỹ thuật — mọi số trong bài phải khớp
   MASTER hoặc field code tính sẵn (Hard Block chặn, kiểm 2 lớp với Enhance).
2. Bảng thông số luôn do CODE dựng — AI chỉ viết phần văn xuôi.
3. Mọi bài đăng ở trạng thái Draft — không auto-publish.
4. SKU trùng trong MASTER: giữ nguyên record, gắn `publish_sku` riêng
   — không tự gộp/xoá dữ liệu nguồn.

## Nhánh legacy (RMU)

`autopost.py`, `dulieu.py`, UI RMU (`self.tab` trong `giao-dien.py`) —
nhánh cũ, giữ ở chế độ rollback (menu Công cụ), không phải luồng chính.
Chưa xoá hẳn (xem Backlog trong Tracklog nếu cân nhắc dọn sau này).

## Version

Đặt tên: `SONEALEO Ver X.Y` (đổi từ 31/07/2026, trước đó là "Lotech
Autopost"). `PIPELINE_VERSION` trong code (`db_phase2.py`) vẫn ghi
`'phase2-lite-r2'` — tên nội bộ cũ, KHÔNG đồng bộ với version hiển thị
— biết là chưa chuẩn hoá, chưa sửa (rủi ro thấp, chỉ gây rối tên gọi,
không ảnh hưởng chức năng).

---
Cập nhật lần cuối: Ver 4.2 — 09/08/2026.

Ghi chú đánh số: số hiệu phiên bản SẢN PHẨM là số duy nhất dùng ở
README / SPEC / TEST-REPORT / KNOWN-ISSUES / giao diện / tên ZIP.
Các số "Ver 1.x", "Ver 2.x", "Ver 4.x", "Ver 5.x" nằm rải trong
comment code là LỊCH SỬ VÁ của từng hàm, giữ nguyên có chủ đích —
chúng ghi lại lỗi nào đã vấp ở đâu, không phải số phiên bản sản phẩm.
