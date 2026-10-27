# BAO-CAO-KHOI-LUONG-VER45.md

| # | Trường | Nội dung |
|---|---|---|
| 1 | Thời gian | 1 phiên làm việc liên tục |
| 2 | File sửa | 3 — `render_phase2.py`, `db_phase2.py`, `giao-dien.py` (nối 2 luồng đăng thật + tiêu đề) |
| 3 | File mới | 1 — `test_v45_checklist_lien_quan.py` |
| 4 | Dòng diff | `render_phase2.py`: 277 dòng (tích luỹ từ 4.2); `db_phase2.py`: 196 dòng (tích luỹ); test mới: 109 dòng |
| 5 | Test mới | 16 |
| 6 | Tổng test | 293/293 PASS, 0 FAIL |
| 7 | Hoàn thành | Checklist báo giá rule theo profile; Sản phẩm liên quan chỉ link bài đã đăng thật, ưu tiên cùng cấp điện áp+thương hiệu; nối vào cả luồng Ver 3.7 và Ver 3.9 |
| 8 | Chưa làm | Quality Gate chấm điểm, Block Tài liệu kỹ thuật (chờ data) |
| 9 | Không test được | Hiển thị thật khi có nhiều sản phẩm cùng profile đã đăng trên WordPress thật |
| 10 | Việc Thịnh làm | Đăng thử ≥2 sản phẩm cùng profile (cùng cấp điện áp/thương hiệu nếu có), xem sản phẩm thứ 2 có tự động link về sản phẩm thứ 1 trong block "Sản phẩm liên quan" không |
| 11 | Rủi ro | Thấp — có phòng thủ đầy đủ (không link sản phẩm chưa đăng, không link chính nó, item thiếu dữ liệu bị bỏ qua). Batch đầu tiên của 1 profile sẽ không có sản phẩm liên quan (chưa có ai đăng trước) — đây là hành vi đúng, không phải bug |
| 12 | Rủi ro pháp lý | Không có |
| 13 | ZIP | `Lotech-Autopost-Ver4.5.zip` |

## Quyết định đáng chú ý

**`render_phase2.py` không tự truy vấn DB.** Giữ đúng kiến trúc hiện có
(module này chỉ nhận dữ liệu đã có sẵn, không phụ thuộc DB — giống
`bang_thong_so`/`khoi_cta`). Việc tìm sản phẩm liên quan (`db_phase2.
tim_san_pham_lien_quan()`) do tầng gọi (`giao-dien.py`) thực hiện trước,
rồi truyền kết quả vào. Giữ module render dễ test độc lập, không cần mock DB.

**Không nối vào "Chạy thử" (Mock preview).** Đây là công cụ xem nhanh nội
dung AI viết, không phải luồng đăng thật — nối thêm DB query vào đây
không có giá trị tương xứng, giữ đúng phạm vi yêu cầu.
