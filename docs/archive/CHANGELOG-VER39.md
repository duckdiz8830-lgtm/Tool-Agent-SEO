# CHANGELOG-VER39.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER38.md` cho lịch sử Ver 3.7.1/3.8.

---

## LOTECH AUTOPOST VER 3.9 — Article Jobs — 26/07/2026

**Sạn đã sửa theo GPT review:** thư mục bên trong ZIP + tiêu đề app giờ
đúng "Ver 3.9", không còn ghi "Ver 3.6"/"VER 3" trơ trơ nữa.

**Đã bake vào code (không cần Thịnh gõ tay từng outline):** 3 gợi ý của
Gemini (đa dạng hoá cách mở đầu, xử lý khi dữ liệu mỏng, CTA kỹ thuật) đưa
thẳng vào `QUY_TAC_CHUNG` trong `prompts_phase2.py` — áp dụng chung cho cả
7 outline, không lặp code. Gợi ý #2 của Gemini ("chuyển hướng sang tiêu
chuẩn chung của dòng sản phẩm") đã **sửa lại cách diễn đạt** thành "công
dụng chung/lưu ý khi chọn mua" — bản gốc nếu làm đúng nghĩa đen có nguy cơ
xui AI tự thêm tiêu chuẩn không có trong Excel, vi phạm Hard Block.

### Mục tiêu Ver 3.9

1 sản phẩm có thể có NHIỀU bài (job), mỗi job outline riêng, đăng riêng,
trạng thái riêng — theo đúng REQ-PLAN-01/02, REQ-POST-01 đã chốt.

### Kiến trúc — vì sao tách hẳn khỏi luồng Ver 3.7

Bảng dữ liệu mới **`article_jobs`**, KHÔNG dùng lại `bai_viet_phase2` —
bảng đó khoá theo (dataset_id, record_id, site, mau), không đủ chỗ chứa
nhiều job của cùng 1 record/site/mẫu. `job_id` là khoá thật duy nhất.

Tab UI mới **"7. Article Jobs"**, tách hẳn khỏi tab "4. Sinh & Đăng" — nút
Đăng, nút Dừng, cờ Force Stop (`jobs_dung_lai`) đều RIÊNG, không đụng
`v3_dung_lai`/nút của luồng Ver 3.7. Lý do: nhu cầu "mục tiêu tối thượng"
(đăng hết 5.264 sản phẩm, 1 bài/sản phẩm) đã được Ver 3.7 giải quyết ổn —
Article Jobs là tính năng NÂNG CAO cộng thêm, không thay thế, không có lý
do gì phải đánh đổi rủi ro của luồng đã test kỹ để đổi lấy tính năng mới.

### 2 rủi ro kỹ thuật đã lường trước và vá ngay từ đầu (không đợi review lần 2)

| Rủi ro | Vá |
|---|---|
| 2 job của CÙNG 1 sản phẩm sinh ra CÙNG 1 slug → WordPress/idempotency coi là cùng 1 bài, job sau đè job trước | `render_phase2.dung_slug()`/`dung_bai_html()` thêm tham số `hau_to_slug` tuỳ chọn — job đầu tiên (sequence=1) giữ NGUYÊN slug như luồng cũ (không phá bài đã đăng thật từ Ver 3.4-3.8), job thứ 2 trở đi tự thêm hậu tố (`-b2`, `-b3`...) |
| `dang_wp_that()` tự tra `bai_viet_phase2` (khoá theo record/site/mau, KHÔNG có sequence) để tìm `wp_id` đã có — với nhiều job cùng record, tra nhầm sẽ khiến job B đè nội dung lên bài của job A | Thêm tham số `da_co_wp_id` (sentinel, mặc định KHÔNG truyền = hành vi cũ y nguyên). Luồng Job LUÔN truyền rõ `wp_id` của chính job đó (lấy từ `article_jobs.wp_id`), bỏ qua hẳn bước tra `bai_viet_phase2` |

Cả 2 đều có test âm xác nhận (JOB-B1/B2/B3, JOB-C1/C2/C3 trong
`test_v39_article_jobs.py`) — không chỉ tin lý thuyết.

### Bài học từ Bug 1 (Ver 3.7.1) áp dụng ngay từ đầu

Vòng lặp job có try/except riêng từng job từ lúc viết đầu tiên, không đợi
GPT review lần 2 mới vá như Ver 3.7. 1 job crash không lường trước vẫn ghi
`trang_thai=ERROR` + lý do, không chặn job kế tiếp.

### Chức năng

- **Tạo job mặc định**: cho sản phẩm đã chọn ở tab 3, mỗi sản phẩm CHƯA có
  job nào (site/mẫu hiện tại) thì tạo đúng 1 job — idempotent, chọn lại
  không tạo trùng.
- **+ Thêm job**: thêm 1 job nữa cho sản phẩm của dòng đang chọn, outline
  lấy theo dropdown đang chọn (mặc định = outline của record).
- **Đổi outline / Xoá job**: chỉ áp dụng được với job còn PENDING (chưa
  chạy) — job đã SUCCESS/ERROR giữ nguyên lịch sử, không sửa ngược.
- **Đăng Draft THẬT toàn bộ job PENDING**: chạy tuần tự, mỗi job dùng
  outline riêng của nó (không phải outline mặc định của sản phẩm) — override
  `row['outline_id']` trước khi dựng prompt/render, tương tự cách Outline
  Studio override cfg.

### File sửa

- `db_phase2.py` — thêm bảng `article_jobs` + 8 hàm CRUD (`tao_job`,
  `dam_bao_job_mac_dinh`, `liet_ke_jobs`, `lay_job`, `xoa_job`,
  `doi_outline_job`, `cap_nhat_job`).
- `render_phase2.py` — `dung_slug()`/`dung_bai_html()` thêm tham số hậu tố
  slug tuỳ chọn, mặc định rỗng = không đổi hành vi cũ.
- `ai_wp_adapter.py` — `dang_wp_that()` thêm tham số `da_co_wp_id` (sentinel
  pattern), mặc định KHÔNG truyền = hành vi cũ y nguyên.
- `prompts_phase2.py` — `QUY_TAC_CHUNG` thêm 3 quy tắc từ Gemini review.
- `giao-dien.py` — tab "7. Article Jobs" (UI + toàn bộ handler), tiêu đề
  app đổi thành "LOTECH AUTOPOST VER 3.9".
- `test_ver3_ui.py` — cập nhật số tab 6→7.
- `test_v34_that_ui.py` — không đổi hành vi, chạy lại xác nhận vẫn PASS.

### File mới

- `test_v39_article_jobs.py` — 23 test (CRUD job thuần, slug không đè
  nhau, idempotency chống đọc nhầm `bai_viet_phase2`, UI đầy đủ tạo/+/-
  /đổi outline/chạy batch/lỗi 1 job không chặn job khác/Force Stop riêng).

### Không làm (đúng scope, không tự mở rộng)

- Không thêm chế độ Mock cho Article Jobs — job chỉ chạy THẬT (Gemini +
  WordPress thật). Muốn xem trước dùng "Xem trước HTML"/tab Outline Studio
  ở luồng thường trước, rồi mới tạo job thật.
- Không gộp 2 luồng (Ver 3.7 record-based và Ver 3.9 job-based) làm 1 —
  giữ tách biệt để không phải test lại từ đầu luồng đã ổn định.
- Không sửa UI cosmetic khác ngoài tên (progress hiện tên record đang
  chạy, redesign UI...) — theo đúng yêu cầu Thịnh: để dành sau khi đi hết
  scope này, gộp vào 4.0.
