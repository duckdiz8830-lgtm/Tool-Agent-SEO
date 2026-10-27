# TIẾN ĐỘ — LOTECH AUTOPOST VER 3

File này là nguồn sự thật duy nhất. Vòng sau chỉ cần đưa file này + một báo lỗi
theo khuôn trong `SPEC.md`, không cần kể lại lịch sử — đỡ tốn token.

Cập nhật lần cuối: **VER 3.6 — Mock Batch Integrity + Tab Order** — 25/07/2026.

---

## VER 3.6 — Mock Batch Integrity + Tab Order

Vá bug batch Mock thật (223/245 → 245/245) + siết test không cho pass giả
+ đổi thứ tự tab. **181/181 test PASS, 0 FAIL** — verify portable từ thư
mục khác thư mục code gốc. Chi tiết đầy đủ `BAO-CAO-KHOI-LUONG.md` (13 mục
theo đúng format đã thống nhất) và `TEST-REPORT.md` mục "VER 3.6".

| # | Hạng mục | Trước | Kết quả | Test | Trạng thái |
|---|---|---|---|---|---|
| 1 | Mock cắt giữa token kỹ thuật | `ten[:60]`/`ten[:40]` cắt thô, batch 245 SP máy biến áp chỉ 223/245 | `render_phase2.rut_gon_an_toan()` cắt tại ranh giới từ, FAQ dùng nguyên tên | Batch thật 245/245, 0 lỗi | PASS |
| 2 | Test batch pass giả | MOCK-3 chỉ tìm chữ "Xong" trong nhãn, PASS dù có lỗi | Đếm chính xác qua DB, assert thành_công==tổng và lỗi==0 | Test PROOF chứng minh cách cũ pass sai, cách mới fail đúng | PASS |
| 3.1 | Thứ tự tab | Nhập dữ liệu, Sản phẩm, Cấu hình, Sinh & Đăng, Theo dõi | Cấu hình, Nhập dữ liệu, Sản phẩm, Sinh & Đăng, Theo dõi (`REQ-UI-01`) | test_ver3_ui.py I1-I8 8/8 PASS, không nhân đôi tab | PASS |
| 3.2 | Harden `PHAN-MEM.bat`/`CAI-DAT-LAN-DAU.bat` | Thiếu thông báo bước tiếp theo, `set` chưa quote an toàn | Thêm thông báo thành công, `set "VAR=value"` toàn bộ | Soát checklist bằng mắt, CHƯA test Windows thật | PASS (logic) |
| — | `REQ-FILTER-01`/`REQ-OUTLINE-02`/`REQ-PLAN-01,02`/`REQ-POST-01` | — | **Không làm** — tracker đã tự xếp Ver 3.7/3.8/3.9 (ROADMAP) trước khi bắt đầu | — | Đúng giới hạn đã chốt |

**CHỈ Thịnh làm được**: mở app xác nhận đúng thứ tự tab; chạy batch Mock
thật trên Windows; test 2 file `.bat` trên thư mục có dấu cách; Gemini/
WordPress thật (không đổi từ 3.4/3.5, xem `HUONG-DAN-DANG-DRAFT-THAT.md`).

---

## VER 3.5 — Real Draft Readiness & Windows Handoff

Vá 3 lỗ hổng GPT phát hiện qua kiểm tra độc lập trên bản 3.4 (đã xác nhận cả
5 điểm đúng bằng cách đọc thẳng code, không chối). **164/164 test PASS**,
verify từ thư mục khác hẳn (`/tmp/portability_check`) — không còn kiểu "tài
liệu ghi X nhưng ZIP chỉ chạy được Y".

| # | Hạng mục | Trước | Kết quả | Test | Trạng thái |
|---|---|---|---|---|---|
| 1 | Gộp Hard Block Mock/Preview/Real | `sinh_va_dang_mock()`/`_phase2_chay_thu()` tự kiểm riêng, thiếu meta_title/meta_description/faq.q | Cả 3 đường dùng chung `kiem_tra_bia_toan_bo()`, xoá đoạn trùng | Tái hiện đúng kịch bản GPT tiêm IP65/bảo hành/IEC — PASS | PASS |
| 2 | Idempotency dùng URL chuẩn hoá | `site = wc['ten'] or wc['url']` — đổi tên mất liên kết | `cauhinh.chuan_hoa_url()`/`site_key`, `db_phase2.doi_khoa_site()` migration giữ nguyên wp_id/url/trạng thái, tự chạy lúc khởi động + lúc lưu | `test_v35_idempotency.py` 11/11 PASS, kể cả mở app thật qua Xvfb tự migration | PASS |
| 3 | Sửa path hard-code + số liệu tài liệu | `test_v34_that_ui.py` hard-code `/home/claude/work/build`, 4 file tài liệu ghi 2 số khác nhau | Path portable, 4 file cùng ghi 164/164 lấy từ 1 lần chạy | Verify chạy từ thư mục khác hẳn | PASS |
| 4 | Dọn callback `after()` lúc đóng app | `destroy()` không huỷ job `_boc_hang_doi`, Tcl báo lỗi | Lưu job id, `after_cancel()` trong `_dong()` | Đóng qua đúng luồng `_dong()`, không còn lỗi Tcl | PASS |
| 5 | `5-KIEM-TRA-KET-QUA.bat` | Chưa có | Wrapper mỏng gọi `cong_cu_kiem_tra_ket_qua.py` (dùng nguyên hàm `db_phase2.py`, không viết logic riêng) | Chạy thật, in đúng dataset/bài viết/WP ID/thời lượng | PASS |
| — | 6 file `.bat` còn lại (0/0b/2/3/4/4b) | — | **Không làm** — đúng quyết định đã chốt, trùng chức năng GUI | — | Cắt theo yêu cầu |

**Tổng test: 164/164 PASS** (9 file test, danh sách + command đầy đủ ở
`TEST-REPORT.md` mục "VER 3.5").

**CHƯA làm — đúng phạm vi đã chốt**: Outline Studio, ảnh/PDF, portable,
nhiều website, Publish, batch 20 bài thật, 6 BAT trùng GUI. **CHỈ Thịnh làm
được**: nhập key/site thật, bấm nút thật, xác nhận Draft thật trên WordPress
Admin (không đổi từ 3.4, xem `HUONG-DAN-DANG-DRAFT-THAT.md`).

---

## Gate "First Real Draft" — bản 3.4

Mục tiêu: Thịnh thấy 1 Draft thật trong WordPress Admin. Bảng theo dõi theo
đúng 3 Task của work order:

| Task | Hạng mục | Trước | Kết quả | Test | Trạng thái |
|---|---|---|---|---|---|
| 1.1 | Multi-select bôi đen + 2 nút đánh dấu | Chưa có | `selectmode='extended'` + nút "Đánh dấu/Bỏ đánh dấu viết cho dòng bôi đen" | 2/2 PASS | PASS |
| 1.2 | Sửa bug preview báo sai "chưa chọn" | Mất focus sau refresh | Ghi nhớ `v3_active_record_id`, khôi phục sau mỗi lần lọc/refresh | 4/4 PASS | PASS |
| 1.3 | Nhật ký ~35%, kéo giãn được | Công thức tính sai (~40%, lệch do cộng nhầm header) | Tính lại trên `chia_man.winfo_height()`, đúng 35% | 1/1 PASS | PASS |
| — | Force Stop + Progress Bar nổi bật (yêu cầu thêm) | Chưa có | Cờ `v3_dung_lai`, dừng sau record đang xử lý (không kill giữa chừng); progress bar dày 24px màu teal | 4/4 PASS | PASS |
| 2.1 | Cấu hình AI tối giản (bỏ Nhà cung cấp) | Chưa có UI thật | API key + nút "Kiểm tra API key và model" (tái dùng `autopost.do_model()`) + dropdown model | Test khởi tạo UI qua Xvfb | PASS |
| 2.2 | Gọi Gemini thật đúng 1 record | Chưa có | `ai_wp_adapter.goi_ai_that()`, theo pattern retry của `autopost.goi_gemini()` | 6/6 PASS (mock HTTP: OK/401/404/429/JSON hỏng/SAFETY) | PASS (logic), CHƯA xác nhận network thật |
| 2.3 | Hard Block E2E đủ field (meta_title/meta_description/faq.q/faq.a) | Chỉ 4 field văn xuôi | `kiem_tra_bia_toan_bo()`, dùng chung Composite Hard Block có sẵn | 3/3 case bịa bị chặn, dữ liệu thật không chặn | PASS |
| 3.1 | 1 website: Lưu/Sửa/Xoá/Kiểm tra kết nối | Chưa có, disable từ Gate UI | `cauhinh.py` ghi/đọc `cau-hinh.env` khoá `WP_WEBSITE_*`, khoá/mở form đúng trạng thái | Round-trip PASS, giữ nguyên comment file | PASS |
| 3.2 | Kiểm tra kết nối không tạo bài | Chưa có | `kiem_tra_ket_noi_wp()` chỉ GET `/users/me` | Test xác nhận KHÔNG gọi `requests.post` | PASS (logic), CHƯA xác nhận network thật |
| 3.3 | Save Draft thật, idempotent, không retry mù | Chưa có | `dang_wp_that()` ép cứng `status=draft`, dò lại slug trước khi retry sau lỗi mạng | Test "timeout rồi phát hiện bài đã tạo" PASS — case khó nhất | PASS (logic), CHƯA xác nhận network thật |
| — | Hiển thị thời gian/thời lượng đúng định dạng | Chưa có cột thời lượng | `25/07 10:51` + `00:01:24`, migration `ALTER TABLE` cột `thoi_luong_giay` | Test định dạng riêng PASS | PASS |
| — | Bug thật: site1/site2 lọt vào UI Ver 3 | Phát hiện lúc test tích hợp | Sửa 3 chỗ dùng `C.lay_site()`/`C.tat_ca_site()` còn sót trong luồng Ver 3 | Test tích hợp đầy đủ 7/7 PASS sau khi sửa | PASS |

**Tổng test: 153/153 PASS** (125 kế thừa không đổi + 28 mới). Chi tiết đầy đủ
`TEST-REPORT.md` (mục "Gate First Real Draft").

**CHƯA làm — đúng giới hạn work order, không phải thiếu sót**: batch 20 bài,
nhiều website, Publish, ảnh/PDF, portable, Outline Studio, tự chuyển Gate.
**CHỈ Thịnh làm được**: nhập key/site thật, bấm nút thật, xác nhận Draft
thật xuất hiện trên WordPress Admin — sandbox này không có mạng ra ngoài để
tự làm bước cuối đó.

---

## UI Gate — Ver 3 giao diện chính (mới nhất)

Đổi UI mặc định từ 7 tab RMU/Phase-2-lẫn-lộn sang đúng **5 tab Ver 3**
(Nhập dữ liệu / Sản phẩm / Cấu hình / Sinh & Đăng / Theo dõi). RMU (Ver 1/2)
ẩn mặc định, vào lại qua **Công cụ → Chế độ RMU (rollback)**.

Chỉ sửa `giao-dien.py` (đúng phạm vi work order) — không đụng AI adapter,
prompt, schema, Hard Block, validators, database, pipeline import.

**8/8 test bắt buộc PASS** (`test_ver3_ui.py`), kèm 6 ảnh bằng chứng thật qua
Xvfb + ImageMagick (`anh-bang-chung-ui/`). Regression: `test_gate2.py` 23/23,
`test_round2_ui_smoke.py` 9/9 (1 assertion cấu trúc tab cập nhật lại cho
đúng — RMU giờ chỉ còn 6 tab gốc, không lẫn tab Phase 2 cũ),
`test_phase2_full.py` 12/12, `test_snapshot_regex.py` 39/39,
`test_round2_integration.py` 34/34. **Tổng 125/125 PASS.**

Thành phần đang **disable, ghi "Sẽ triển khai ở Gate sau"**: nút Kiểm tra
model/kết nối (tab Cấu hình, khối AI); toàn bộ khối Website (Lưu/Sửa/Xoá/
Kiểm tra kết nối); radio "WordPress thật" (tab Sinh & Đăng); nút Xuất
tracker (tab Theo dõi).

Chi tiết đầy đủ: `TEST-REPORT.md` (mục "UI Gate — Ver 3").

**Không tự chuyển Gate** — dừng lại sau UI Gate, CHƯA làm cấu hình website
hoạt động thật, CHƯA nối `dang_wp_that()`.

---

## Bảng theo dõi bắt buộc — Content Safety Gate 2

Trạng thái chỉ dùng: CHƯA LÀM / ĐANG LÀM / PASS / FAIL / BLOCKED / TẠM GÁC.

| ID | Hạng mục | Trước Gate 2 | Kết quả Gate 2 | Bằng chứng/Test | Trạng thái | Còn tồn tại |
|---|---|---|---|---|---|---|
| Task 1 | Schema JSON-LD trong HTML thật | `dung_schema()` chỉ trả dict, chưa gắn vào HTML | `dung_schema_script()` bọc `<script type="application/ld+json">`, gắn cuối `dung_bai_html()` | D1 4/4 PASS (Product), D2 1/1 PASS (Service không có schema) | PASS | Không |
| Task 2 | Mở rộng Hard Block | Chỉ chặn token đơn + cụm kỹ thuật (điện áp/dòng/công suất) | Thêm lớp cụm mở rộng: bảo hành, IPxx, IEC/TCVN, nhiệt độ, % | D3 5/5 PASS (chặn khi thiếu), D4 5/5 PASS (cho phép khi có thật), D5 4/4 PASS (regression không vỡ) | PASS | Không |
| Task 3 | 2 mẫu `chuan`/`ngan_gon` hoạt động thật | `mau` chỉ là chuỗi tự do trong DB, không ảnh hưởng nội dung | Prompt/JSON schema/HTML/slug khác nhau thật theo `MAU_BIEN_THE` | D6 3/3 PASS (HTML khác, slug khác, không đẻ bài trùng) | PASS | Không |
| Task 4 | Đổi tên phiên bản VER 3 | "Lotech Autopost - Claude v2.8" | "LOTECH AUTOPOST VER 3" — title cửa sổ, header, 3 file `.bat`, tài liệu | Xác nhận `app.title()=='LOTECH AUTOPOST VER 3'` qua Xvfb | PASS | Không |
| — | Bug thread-safety Tkinter | — | `_phase2_mau_dang_chon()` (có `messagebox`) bị gọi từ luồng nền — đã sửa: validate ở luồng chính, truyền qua tham số | Phát hiện khi sửa Task 3, sửa xong verify lại qua `test_round2_ui_smoke.py` | PASS | Không |
| D7 | Xác nhận không gọi WordPress thật | — | `inspect.getsource()` xác nhận `sinh_va_dang_mock()` không có `dang_wp_that`/`requests.post` | PASS | PASS | Không |

**Tổng test Gate 2 + regression toàn bộ: 117/117 PASS** (`test_gate2.py` 23,
`test_phase2_full.py` 12, `test_snapshot_regex.py` 39,
`test_round2_integration.py` 34, `test_round2_ui_smoke.py` 9).

Chi tiết đầy đủ: `TEST-REPORT.md` (mục "Content Safety Gate 2", đầu file).

**Không tự đổi thứ tự Gate** — dừng lại sau Gate 2, CHƯA làm UI Ver 3 (Gate
3), CHƯA cấu hình website (Gate 3), CHƯA nối `dang_wp_that()` (Gate 4).

---

## Bảng theo dõi bắt buộc — Round 2

Trạng thái chỉ dùng: CHƯA LÀM / ĐANG LÀM / PASS / FAIL / BLOCKED / TẠM GÁC.

| ID | Hạng mục | Trước Round 2 | Kết quả Round 2 | Bằng chứng/Test | Trạng thái | Còn tồn tại |
|---|---|---|---|---|---|---|
| R2-01 | Import Orchestrator | `import_4_profile()`/`validate_rows()` gọi rời rạc, không có hàm tổng | `import_phase2_pipeline()` trong `nhap_phase2.py` — gộp đủ 10 bước, trả báo cáo/lỗi/cảnh báo | T2-01, T2-02 PASS (`test_round2_integration.py`) | PASS | Không |
| R2-02 | Database đa site/đa mẫu | 1 bảng `ban_ghi` phẳng (Round 1), không tách site/mẫu | 3 bảng `dataset`/`san_pham_phase2`/`bai_viet_phase2`, khoá đúng yêu cầu | T2-04, T2-05 PASS (`db_phase2.py`) | PASS | Không |
| R2-03 | Import lại dataset (UPSERT) | Round 1 dùng `INSERT OR IGNORE` — không cập nhật lại nội dung khi data đổi nhẹ | `ghi_san_pham()` UPSERT: cập nhật `du_lieu_json`/profile/outline/content_type/pipeline_version, giữ `selected`, không đụng `bai_viet_phase2` | Test riêng lúc code `db_phase2.py` (mục "Bug thật" TEST-REPORT), PASS | PASS | Không |
| R2-04 | Dataset metadata | Có `data_checksum`/`file_checksum` rời rạc trong bảng dataset Round 1, thiếu `source_file`/`column_structure`/`pipeline_version` tường minh | Đủ 10 field yêu cầu trong bảng `dataset` | T2-02 PASS | PASS | Không |
| R2-05 | Prompt Phase 2 thật | `dung_prompt()` đơn giản (Round 1), không phân outline, không JSON schema tường minh | `prompts_phase2.py` — đủ 7 outline (kể cả `outline_service` mới tách), system instruction/section/JSON schema riêng từng outline | T2-06 Golden Prompt Test 18/18 PASS (2 record thật × 9 outline) | PASS | Không |
| R2-06 | Render HTML | Chỉ có `bang_thong_so()`/`dung_schema()` rời rạc, chưa ghép thành 1 bài | `dung_bai_html()` trong `render_phase2.py` — ghép AI (đã sanitize) + bảng (không sanitize) + CTA thật từ `cauhinh.py` + `price_display` cố định | Test riêng lúc code (field lạ AI tự thêm bị lọc, Giá List không lọt), T2-10 PASS | PASS | Không |
| R2-07 | Giữ nguyên đơn vị | Nhãn "Tiết diện"/"Công suất"/"Cấp điện áp" KHÔNG mang đơn vị | Nhãn mang đơn vị đúng header gốc (`"Tiết diện (mm²)"`, `"Công suất (kVA)"`, `"Cấp điện áp (kV)"`); giá trị máy biến áp bỏ hậu tố đơn vị trùng lặp | Kiểm thật: `"Công suất (kVA): 15"` (không lặp "kVA kVA"); `test_snapshot_regex.py` 39/39 PASS sau khi cập nhật kỳ vọng | PASS | Không |
| R2-08 | Chống bịa số theo cụm | Round 1 chỉ chặn token đơn (1 số + 1 đơn vị) — lỗ hổng: cụm giả `"99/1kV"` lọt qua nếu token con `"1kV"` hợp lệ ở nơi khác | Composite Hard Block: kiểm cụm kỹ thuật hoàn chỉnh (`x`/`+`/`/`) trước, token đơn sau | T2-07 5/5 PASS, gồm đúng 4 case GPT yêu cầu + case đa lõi cộng tự thêm | PASS | Không |
| R2-09 | Sanitize HTML | Có từ Round 1 (`bleach` whitelist cơ bản) | Verify lại đúng danh sách thẻ/thuộc tính R2-09, thêm xoá NỘI DUNG bên trong `<script>`/`<style>` (Round 1 chỉ xoá tag, giữ text) | T2-09 2/2 PASS | PASS | Không |
| R2-10 | UI Integration | 0% — chưa có gì | Tab "6. Phase 2 (4-Profile)" thật trong `giao-dien.py`, đủ khối A (nhập) — B (danh sách/chọn) — C (thử 1 bài) — D (chạy) — E (dashboard) | `test_round2_ui_smoke.py` 9/9 PASS qua Xvfb thật (3 lần liên tiếp ổn định), T2-11 PASS | PASS | Đã test qua `Xvfb` (Linux headless), CHƯA test trên Windows thật của Thịnh |
| R2-11 | AI/WordPress Adapter | 0% — chưa có gì | `ai_wp_adapter.py`: `goi_ai_mock()`/`dang_wp_mock()` đầy đủ, idempotent; khung `dang_wp_that()` tái sử dụng `autopost.py` qua import (không copy) | T2-04, T2-05, T2-10 PASS (mock) | PASS (mock) | Phần THẬT (`dang_wp_that`) chưa test — không có site/key thật ở môi trường này, đúng phạm vi Round 2 |
| R2-12 | Dependency & gói giao | `bleach` chưa có trong `.bat`/kiểm tra thư viện | Thêm `bleach` vào `CAI-DAT-LAN-DAU.bat`, `PHAN-MEM.bat`, `_kiem_thu_vien()` | Grep xác nhận cả 3 chỗ; T2-12 kiểm ZIP sạch — xem dưới | PASS | Không |
| T2-01 | Import MASTER đủ 5.264 record | — | Đếm trực tiếp qua `db_phase2.dem_san_pham()` | `test_round2_integration.py`: 5264/5264 | PASS | Không |
| T2-02 | 4 file con data_checksum khớp MASTER | — | So `data_checksum` MASTER-solo vs file con cho cả 4 profile | PASS cả 4 | PASS | Không |
| T2-03 | Không mất record SKU trùng | — | 17 cặp SKU trùng đếm lại đúng, tổng record trong DB = 5.264 | PASS | PASS | Không |
| T2-04 | 1 record đăng 2 site -> 2 dòng độc lập | — | `wp_id`/`wp_url` khác nhau giữa `lotech` và `cadivi-vn` cho cùng `record_id` | PASS | PASS | Không |
| T2-05 | 1 record, 1 site, 2 mẫu -> 2 dòng độc lập | — | `wp_id` khác nhau giữa mẫu `chuan` và `ngan_gon` cùng site | PASS | PASS | Không |
| T2-06 | Golden Prompt Test | — | 2 record thật/outline × 9 outline (7 outline chính + 2 route phụ của cap_dien/máy biến áp vào outline_phu_kien) — đúng field/strict rules/JSON schema/không Giá List/giữ đơn vị | 18/18 PASS | PASS | Không |
| T2-07 | Composite Hard Block | — | `99/1kV` giả từ `0.6/1kV` BLOCK; `9x50mm²` giả từ `3x50` BLOCK; giá trị đúng PASS; số ở record khác BLOCK | 5/5 PASS | PASS | Không |
| T2-08 | Dịch vụ không Product Schema | — | 41 record `outline_service` đều `dung_schema()=None` | PASS | PASS | Không |
| T2-09 | Sanitize HTML | — | Xoá sạch `script`/`onclick`/`style`/`javascript:`/`iframe`; giữ `specs-table`/`colspan`/`rowspan` ở bảng code tự dựng | 2/2 PASS | PASS | Không |
| T2-10 | Integration Test (mock) | — | Import MASTER → lưu 5.264 → chọn 20 → AI mock → HTML → WP mock → dashboard đúng | 20/20 thành công, dashboard hiện đủ dòng | PASS | Không |
| T2-11 | Luồng RMU legacy smoke test | — | App khởi động đủ 7 tab, toàn bộ hàm nạp dữ liệu RMU (tab 0-5) chạy không crash qua Xvfb thật | PASS (`test_round2_ui_smoke.py`) | PASS | Không |
| T2-12 | ZIP không chứa DB test/bí mật | — | Kiểm tay trước khi đóng gói: không có `.db`, không API key, không App Password, không `sites-them.json` chứa dữ liệu thật | Xem mục "Đóng gói" trong `TEST-REPORT.md` | PASS | Không |

---

## Phase 2 Lite — tổng quan 2 vòng

```
Round 1 (Data Core: Profile/Outline Registry, importer, validator, regex)
████████████████████ 100%  — 12/12 + 39/39 PASS, không đổi ở Round 2

Round 2 (Database đa site, Import Orchestrator, Prompt/Render thật,
         Composite Hard Block, UI Integration, AI/WP Adapter mock)
████████████████████ 100%  — 34/34 (integration) + 9/9 (UI smoke) PASS

Còn lại — CHỈ Thịnh làm/xác nhận được (không phải thiếu sót Round 2)
- Gọi Gemini thật + verify model gemini-3.6-flash
- Đăng WordPress thật (dang_wp_that() đã viết khung, chưa test)
- Chạy PHAN-MEM.bat trên Windows thật (Round 2 test bằng Xvfb Linux)
```

Chi tiết đầy đủ: `TEST-REPORT.md` (PASS/FAIL từng test, mock vs thật, bug thật
phát hiện trong lúc code), `KNOWN-ISSUES.md`, `HUONG-DAN-TEST-ROUND-2.md`.

---

## Tiến độ tổng thể (nhánh RMU — MAIN v0.1, không đổi so với Round 1)

```
Hạ tầng vận hành (nhập Excel, sinh bài, đăng WordPress, resume, dashboard)
██████████████████░░  90%   — MAIN v0.1, còn 2 mục chưa tự test được (cần key/WP thật)

Chống bịa và an toàn nội dung (số liệu, danh tính, trùng lặp)
████████████████░░░░  80%   — chặn số liệu + danh tính + vân tay thông số + trùng văn biên tập xong

Hệ thống outline theo ngành hàng (profile, nhận diện tự động, module bật/tắt)
██░░░░░░░░░░░░░░░░░░  10%   — mới có 2 outline cứng cho 1 ngành (tủ RMU), CHƯA có
                               nhận diện ngành, CHƯA có hồ sơ ngành, CHƯA optional module

Ảnh, Schema, WordPress nâng cao (featured image, category/tag, alt/caption)
████░░░░░░░░░░░░░░░░  20%   — có upload ảnh cơ bản, chưa resize/WebP/featured/schema
```

**Tóm một câu:** nhánh RMU không đổi ở Round 2. Nhánh Phase 2 giờ chạy được
trọn luồng giả lập từ UI tới dashboard (import → chọn → prompt → AI mock →
HTML → sanitize → WP mock → dashboard), còn thiếu 2 việc chỉ Thịnh làm được
(Gemini thật, WordPress thật) và test trên Windows thật.

---

## Đã làm (MAIN v0.1 + các bản vá — nhánh RMU)

- [x] Nhập Excel nhiều sheet, chuẩn hoá đơn vị, gộp mã trùng, tách thông số bằng regex
- [x] Đọc series theo chữ trong mã (SM6/RM6), không theo thứ tự sheet
- [x] Chọn sản phẩm cần viết (tick chọn/bỏ từng dòng hoặc hàng loạt)
- [x] Ngăn kho theo ngành hàng (`danh_muc`), khoá kép chống hai ngành trùng SKU
- [x] Sinh liên tục N bài, lỗi bài nào lưu bài đó, không dừng cả lô
- [x] Bài lỗi ghi vào dashboard, không chỉ vào log.csv
- [x] WordPress: chống đẻ bài `-2` khi mạng chập chờn
- [x] `thinkingConfig` đúng request Gemini
- [x] Dashboard (app + Excel) lọc đúng theo site, tính đúng sản phẩm đang chọn
