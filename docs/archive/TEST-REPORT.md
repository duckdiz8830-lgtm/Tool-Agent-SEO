# TEST-REPORT — LOTECH AUTOPOST VER 3

## VER 3.6 — Mock Batch Integrity + Tab Order (mới nhất)

Vá bug batch Mock thật (223/245 → 245/245) + siết test không cho pass giả +
đổi thứ tự tab. **181/181 PASS, 0 FAIL** — verify từ thư mục khác hẳn
(`/tmp/v36_check`), portable thật.

### Command chạy lại y hệt
```
rm -rf *.db __pycache__ cau-hinh.env
python3 test_that_mocked.py
python3 test_gate2.py
python3 test_phase2_full.py
python3 test_snapshot_regex.py
python3 test_round2_integration.py
python3 test_v36_regression.py
rm -rf *.db __pycache__ cau-hinh.env
xvfb-run -a python3 test_v35_idempotency.py
rm -rf *.db __pycache__ cau-hinh.env
xvfb-run -a python3 test_round2_ui_smoke.py
rm -rf *.db __pycache__ cau-hinh.env anh-bang-chung-ui
xvfb-run -a --server-args="-screen 0 1366x768x24" python3 test_ver3_ui.py
rm -rf *.db __pycache__ cau-hinh.env anh-bang-chung-ui
xvfb-run -a --server-args="-screen 0 1366x768x24" python3 test_v34_that_ui.py
```
(Trên Windows: bỏ `xvfb-run -a`, chạy thẳng `python test_xxx.py`.)

### Task 1 — Mock generator cắt giữa token kỹ thuật (bug batch 223/245) — ĐÃ VÁ

Review độc lập phát hiện batch Mock 245 sản phẩm máy biến áp chỉ đạt
223/245 (22 lỗi Hard Block). Nguyên nhân: `goi_ai_mock()` dùng
`ten[:60]`/`ten[:40]` — cắt thô theo số ký tự, có thể cắt ngay giữa token
kỹ thuật dính liền không dấu cách (`22/0.4KV`, `12.7/0.23KV`, `0.6/1kV`,
`3x50+1x25mm²`), tạo ra chuỗi trông giống số bịa/sai chính tả dù chỉ là bị
cắt dở — Hard Block đôi khi chặn nhầm, đôi khi lọt qua nhưng vẫn sai lệch
so với record gốc.

**Đã vá**: `render_phase2.rut_gon_an_toan()` — cắt tại ranh giới từ
(khoảng trắng), không bao giờ cắt giữa 1 từ/token. Nếu từ đầu tiên đã dài
hơn cả giới hạn (không có chỗ lùi an toàn), THÀ TRẢ DÀI HƠN một chút còn
hơn cắt hỏng. Áp dụng cho `meta_title` (mock), `title`/`meta_description`
(dùng chung Mock+Real trong `dung_bai_html()`); `faq.q` đổi hẳn sang dùng
NGUYÊN tên sản phẩm, né hẳn rủi ro cắt.

**Kết quả — batch thật 245 sản phẩm máy biến áp: 245/245 thành công, 0 lỗi**
(`test_v36_regression.py` mục BATCH-245, chạy lại độc lập từ
`test_v34_that_ui.py` mục MOCK-3 cũng ra đúng 245/245).

### Task 2 — Test batch không còn "pass giả" — ĐÃ SIẾT

Trước: `test('MOCK-3', ..., 'Xong' in nhãn_tiến_độ)` — bất kỳ nhãn nào
chứa chữ "Xong" đều PASS, kể cả `"Xong: 223/245 thành công, 22 lỗi"`. Đã
sửa: đếm CHÍNH XÁC qua `db_phase2.dashboard()`, assert
`thành_công == tổng_sản_phẩm và lỗi == 0`.

**Chứng minh assertion mới có giá trị thật** (`test_v36_regression.py` mục
PROOF-1/2/3): cố ý tiêm 1 lỗi thật (thêm `"IP99 bịa"` vào `meta_title` của
1 record trong batch 10 record) →
- Cách kiểm CŨ (`"Xong" in nhãn`) → **vẫn PASS dù có lỗi thật** (xác nhận
  đúng là pass giả).
- Cách kiểm MỚI (đếm chính xác) → **FAIL đúng** vì `lỗi=1 != 0`.

Đây không phải tự khai "đã sửa xong" — có test độc lập chứng minh assertion
cũ THẬT SỰ bỏ lọt lỗi, và assertion mới THẬT SỰ bắt được.

Regression token kỹ thuật (`test_v36_regression.py` mục TOK/TOK-BIEN):
4 pattern (`22/0.4KV`, `12.7/0.23KV`, `0.6/1kV`, `3x50+1x25mm²`) × 9 giới
hạn cắt khác nhau (20-60 ký tự) = 36 case, cộng 11 case biên off-by-one
quanh giới hạn 55-65 — không có case nào bị cắt dở.

### Task 3.1 — Đổi thứ tự tab — ĐÃ XONG

Thứ tự mới: **1. Cấu hình → 2. Nhập dữ liệu → 3. Sản phẩm → 4. Sinh & Đăng
→ 5. Theo dõi** (trước: Nhập dữ liệu, Sản phẩm, Cấu hình, Sinh & Đăng, Theo
dõi). Chỉ đổi THỨ TỰ GỌI hàm dựng tab (`self._v3_tab_3_cau_hinh()` gọi
trước `self._v3_tab_1_nhap_du_lieu()`...) + nhãn số thứ tự — không đổi tên
hàm, không đổi callback/state/widget bên trong từng tab (đúng yêu cầu
"chỉ đổi vị trí, không redesign nội dung").

`test_ver3_ui.py` cập nhật đúng 2 chỗ giả định thứ tự cũ (danh sách nhãn kỳ
vọng ở test I1; index chụp ảnh tab Cấu hình đổi từ `select(2)` sang
`select(0)`) — test I1-I8 vẫn 8/8 PASS, xác nhận RMU rollback không nhân
đôi tab/widget qua đổi thứ tự này.

### Task 3.2 — Harden 2 file `.bat` có sẵn — ĐÃ XONG

`PHAN-MEM.bat`: thêm thông báo rõ "đang mở/bước tiếp theo" ở CẢ 2 nhánh
thành công (Python bundle riêng + Python hệ thống) — trước đây launch xong
không in gì, cửa sổ đóng ngay không ai biết đã chạy hay chưa.

`CAI-DAT-LAN-DAU.bat`: đổi toàn bộ `set VAR=value` → `set "VAR=value"`
(6 chỗ) — an toàn với đường dẫn có dấu cách. Thông báo lỗi/thành công vốn
đã đủ (giữ nguyên, không cần sửa).

**Chưa test trên Windows thật** — chỉ soát logic/cú pháp bằng mắt theo
đúng checklist (`cd /d "%~dp0"`, quote path, kiểm `errorlevel`, in nguyên
nhân + `pause` khi lỗi, in bước tiếp theo khi thành công).

---

## VER 3.5 — Real Draft Readiness & Windows Handoff (mới nhất)

Vá đúng 3 lỗ hổng GPT phát hiện qua kiểm tra độc lập trên bản 3.4 (không tự
sửa, không tự khai) + hoàn thiện idempotency WordPress. **Số liệu dưới đây
lấy từ 1 lần chạy thật, verify bằng cách copy toàn bộ code sang thư mục
`/tmp/portability_check` (khác hẳn thư mục code) rồi chạy — mô phỏng đúng
việc giải nén ZIP trên máy khác, đúng lỗi GPT bắt được ở bản 3.4 khi
`test_v34_that_ui.py` hard-code `/home/claude/work/build`.**

### Tổng test — 164/164 PASS

| Bộ test | Kết quả |
|---|---|
| `test_that_mocked.py` | 21/21 |
| `test_gate2.py` | 23/23 |
| `test_phase2_full.py` | 12/12 |
| `test_snapshot_regex.py` | 39/39 |
| `test_round2_integration.py` | 34/34 |
| `test_v35_idempotency.py` (mới) | 11/11 |
| `test_round2_ui_smoke.py` | 9/9 |
| `test_ver3_ui.py` | 8/8 |
| `test_v34_that_ui.py` | 7/7 |
| **TỔNG** | **164/164** |

**Command chạy lại y hệt** (từ thư mục gốc project, copy sang đâu cũng chạy
được — không còn path hard-code):
```
rm -rf *.db __pycache__ cau-hinh.env
python3 test_that_mocked.py
python3 test_gate2.py
python3 test_phase2_full.py
python3 test_snapshot_regex.py
python3 test_round2_integration.py
rm -rf *.db __pycache__ cau-hinh.env
xvfb-run -a python3 test_v35_idempotency.py
rm -rf *.db __pycache__ cau-hinh.env
xvfb-run -a python3 test_round2_ui_smoke.py
rm -rf *.db __pycache__ cau-hinh.env
xvfb-run -a --server-args="-screen 0 1366x768x24" python3 test_ver3_ui.py
rm -rf *.db __pycache__ cau-hinh.env anh-bang-chung-ui
xvfb-run -a --server-args="-screen 0 1366x768x24" python3 test_v34_that_ui.py
```
(Trên Windows: bỏ hẳn `xvfb-run -a`, chạy thẳng `python test_xxx.py` — có
màn hình thật thì không cần Xvfb.)

### 1. Lỗ hổng "Mock đăng thành công dù bịa số" — ĐÃ VÁ

GPT tiêm `IP65` vào `meta_title`, `"Bảo hành 24 tháng"` vào
`meta_description`, `"IEC 62271"` vào `faq.q`, gọi `sinh_va_dang_mock()` —
bản 3.4 trả `{'ok': True}`. Nguyên nhân: `sinh_va_dang_mock()` (Mock) và
`_phase2_chay_thu()` (nút "Xem trước HTML") tự kiểm 1 đoạn RIÊNG (chỉ 4
field văn xuôi + `faq.a`), không gọi `kiem_tra_bia_toan_bo()` — hàm ĐÃ VIẾT
từ bản 3.4 nhưng chỉ nối vào luồng Real, quên nối vào Mock/Preview.

**Đã sửa**: xoá đoạn kiểm riêng ở cả 2 chỗ, gọi thẳng
`kiem_tra_bia_toan_bo()` — CÙNG 1 hàm cho Mock, Preview, Real. Test tái hiện
đúng kịch bản GPT tiêm (`test_that_mocked.py` HB-1/HB-2, cộng test riêng
dùng `sinh_va_dang_mock()` thật xác nhận trả `{'ok': False, 'loi':
"Hard Block chặn: meta_title: [...]; meta_description: [...]; faq[0].q:
[...]"}`) — ghi rõ field + token bị chặn, đúng yêu cầu.

### 2. Idempotency WordPress dùng khoá URL, tách khỏi tên hiển thị — HOÀN THIỆN

Trước: `site = wc['ten'] or wc['url']` — đổi tên hiển thị làm mất liên kết
bài cũ. Đã sửa:
- `cauhinh.chuan_hoa_url()` — bỏ scheme/`www.`/dấu `/` cuối, hạ thường.
  `cauhinh.doc_website()` trả thêm `site_key` (khoá THẬT) tách biệt hẳn
  `ten` (CHỈ hiển thị).
- Toàn bộ nơi ghi DB (`_v3_viec_dang_draft_that`, `_phase2_viec_chay_hang_loat`
  qua `_v3_site_key()`) dùng `site_key`, không còn chỗ nào dùng `ten` làm
  khoá (grep xác nhận `wc['ten'] or wc['url']` không còn xuất hiện ở bất kỳ
  đâu ngoài mục đích hiển thị).
- `db_phase2.doi_khoa_site()` — migration đổi khoá `site`, **chỉ UPDATE 1
  cột**, không xoá-tạo-lại dòng nào, giữ nguyên `wp_id`/`wp_url`/`trạng
  thái`/`thời lượng`.
- **Tự động chạy lúc khởi động app** (`_v3_di_chuyen_du_lieu_khoa_cu()` gọi
  trong `__init__`) và **mỗi lần Lưu cấu hình website** — không cần Thịnh tự
  tay làm gì, dữ liệu bản 3.4 (nếu có) tự chuyển sang khoá mới.

**Test (`test_v35_idempotency.py`, 11/11 PASS)**: đổi tên giữ URL → cùng
site_key; đổi domain → site_key khác; migration giữ nguyên wp_id/url/trạng
thái/thời lượng; migration từ khoá không tồn tại → an toàn, không lỗi; **mở
app Ver 3.5 thật (qua Xvfb) với dữ liệu mô phỏng bản 3.4 → tự migration
đúng lúc khởi động, giữ nguyên wp_id** — test mạnh nhất, xác nhận hành vi
thật của app, không phải chỉ gọi hàm trần.

### 3. Path hard-code + số liệu tài liệu lệch nhau — ĐÃ VÁ

`test_v34_that_ui.py` dòng 4 sửa từ `BASE = '/home/claude/work/build'`
sang `BASE = os.path.dirname(os.path.abspath(__file__))` — portable thật,
xác nhận bằng cách chạy từ `/tmp/portability_check` (xem đầu mục này).
4 file tài liệu (`TEST-REPORT.md`, `TIEN-DO.md`, `NHAT-KY-THAY-DOI.md`,
`KNOWN-ISSUES.md`) giờ cùng ghi đúng **164/164** — lấy từ CÙNG 1 lần chạy,
không sửa tay số ở file nào riêng lẻ.

### 4. Dọn callback `after()` khi đóng app — ĐÃ VÁ

`self.after(80, self._boc_hang_doi)` tự lặp lại nhưng không có cơ chế huỷ —
`destroy()` không tự huỷ job đang chờ, Tcl báo lỗi `invalid command name
"..._boc_hang_doi"` (GPT phát hiện; trước đây bị coi nhầm là artifact vô
hại của test tự gọi `destroy()` — thực ra là thiếu dọn dẹp thật). Đã sửa:
lưu `self._boc_hang_doi_job`, gọi `self.after_cancel()` trong `_dong()`
trước khi `destroy()`. Test xác nhận đóng qua đúng luồng `_dong()` không
còn lỗi Tcl (trước đây có, giờ không còn).

### 5. `5-KIEM-TRA-KET-QUA.bat` — chỉ wrapper, không viết logic riêng

`cong_cu_kiem_tra_ket_qua.py` — dùng lại NGUYÊN `db_phase2.dashboard()`,
`liet_ke_dataset()`, `liet_ke_san_pham()`, `lay_bai_viet()`,
`dinh_dang_thoi_gian()`, `dinh_dang_thoi_luong()` (2 hàm định dạng cuối
cũng MỚI trích từ `giao-dien.py` sang `db_phase2.py` để dùng chung, xoá bản
trùng ở GUI). File `.bat` chỉ gọi `python cong_cu_kiem_tra_ket_qua.py`,
không có logic đọc DB nào trong `.bat`. **Không làm 6 file `.bat` còn lại**
(0/0b/2/3/4/4b) — đúng quyết định đã chốt, vì đã có sẵn trong GUI (Tab 3
"Kiểm tra API key và model"/"Kiểm tra kết nối", Tab 4 "Xem trước
HTML"/"Đăng Draft", Tab 5 dashboard).

### Việc CHỈ Thịnh làm được (không đổi từ bản 3.4)

Sandbox này vẫn không gọi được Gemini/WordPress thật. Nhập key/site thật,
bấm nút thật, xác nhận Draft thật trên WordPress Admin — theo đúng
`HUONG-DAN-DANG-DRAFT-THAT.md` đã có từ 3.4 (không đổi bước nào).

---

## Gate "First Real Draft" — Task 1+2+3 (bản 3.4)

Mục tiêu: Thịnh nhìn thấy 1 bài Draft thật trong WordPress Admin. **125/125
test cũ vẫn PASS + 28 test mới cho Task 1-3 (7 UI thật qua Xvfb + 21 backend
mock-HTTP) — tổng 153/153.**

**QUAN TRỌNG — giới hạn môi trường, nhắc lại rõ ràng:** sandbox chạy code
này KHÔNG gọi được `generativelanguage.googleapis.com` hay bất kỳ WordPress
site thật nào (network chỉ mở domain cố định: pip/npm/github...). Toàn bộ
test Task 2/3 dùng **`unittest.mock.patch` giả lập `requests.get`/
`requests.post`** — verify được 100% LOGIC (dựng request đúng, xử lý đúng
mọi mã lỗi, idempotent, retry không mù, parse response đúng) nhưng **CHƯA
xác nhận được request thật có thành công trên hạ tầng Google/WordPress thật
hay không**. Đây là việc CHỈ Thịnh làm được — nhập key thật, URL thật,
Application Password thật vào tab "3. Cấu hình", bấm nút thật.

### Task 1 — Selection + Nhật ký (đã làm ở lượt trước, nhắc lại tóm tắt)

Bug thật đã sửa: bảng bị xoá-dựng-lại làm mất focus dù dữ liệu báo đủ 245
đã chọn — khôi phục qua `v3_active_record_id`. Thêm 2 nút "Đánh dấu/Bỏ đánh
dấu viết cho dòng bôi đen" (tách biệt với "Chọn/Bỏ chọn dòng đang hiển thị").
Nhật ký chỉnh đúng ~35%. Thêm Force Stop + Progress Bar nổi bật (yêu cầu
thêm ngoài work order gốc). 11/11 test PASS — xem chi tiết log hội thoại
trước, không lặp lại ở đây.

### Task 2 — Gemini thật + Content Safety E2E

- **Tái sử dụng lớn nhất tìm được**: `autopost.do_model()` — hàm dò model
  Gemini THẬT đã có sẵn, chạy production ở nhánh RMU từ trước — dùng lại
  nguyên vẹn cho nút "Kiểm tra API key và model" ở Ver 3, không viết lại.
- `ai_wp_adapter.goi_ai_that()` — theo đúng pattern retry/lỗi của
  `autopost.goi_gemini()` (429 NGAY/PHÚT có backoff đúng theo Google trả
  về, 404, SAFETY, MAX_TOKENS, JSON hỏng) nhưng dùng
  `prompts_phase2.xay_prompt()` thay vì prompt RMU. Test mock-HTTP: 6/6 case
  (thành công, 401, 404, 429 hết ngày, JSON hỏng, SAFETY) đều báo đúng,
  KHÔNG treo UI (chạy trong luồng nền qua `chay_nen_phase2`).
- `ai_wp_adapter.kiem_tra_bia_toan_bo()` — Hard Block phủ đủ
  `meta_title/meta_description/faq.q/faq.a` (trước chỉ 4 field văn xuôi từ
  Gate 2). Dùng CHUNG `render_phase2.kiem_tra_bia()` (Composite Hard Block
  đã có), không viết lại logic chặn. Test: bịa IP65 trong meta_title, "bảo
  hành 24 tháng" trong meta_description, "IEC 62271" trong faq.q — cả 3 đều
  bị chặn đúng; dữ liệu thật thì không chặn.
- Sinh đúng 1 bài (không batch) — record active, chạy nền, lỗi API/JSON báo
  rõ ràng qua `messagebox` + log, không treo UI.

### Task 3 — Website Configuration + Save Draft thật

- `cauhinh.py` thêm `ghi_env()`/`luu_website()`/`doc_website()`/`luu_gemini()`
  — ghi đè đúng khoá `WP_WEBSITE_*`/`GOOGLE_API_KEY`/`MODEL_GEMINI` trong
  `cau-hinh.env`, **giữ nguyên comment và cấu trúc file cũ** (test xác nhận
  bằng cách đọc lại nội dung file sau khi ghi). Dùng namespace `WP_WEBSITE_*`
  khớp thẳng với `autopost.thong_tin_wp()`/`_auth()` có sẵn — **không phải
  sửa 1 dòng nào trong `autopost.py`**.
- `ai_wp_adapter.dang_wp_that()` — viết lại hoàn chỉnh:
  - `status` **luôn ép cứng `'draft'`** ngay trong code, không đọc tham số
    ngoài nào — test xác nhận payload gửi đi luôn có `status: draft` dù gọi
    thế nào.
  - Idempotent theo `(dataset_id, record_id, site, mau)`: đã có `wp_id` lưu
    → PUT thẳng, không dò slug lại (test xác nhận `requests.get` không bị
    gọi khi đã có `wp_id`).
  - **Test quan trọng nhất — "không retry mù"**: giả lập request đầu tiên
    bị Timeout NHƯNG server đã tạo bài thật (kịch bản thực tế: mất kết nối
    lúc nhận response, không phải lúc gửi). Lần retry, code tự dò lại slug
    TRƯỚC khi POST lần 2, phát hiện bài đã tồn tại → PUT update đúng ID
    thay vì tạo bài mới đẻ slug-2. Test xác nhận đúng 2 lần POST, 2 lần GET,
    kết quả trả về đúng ID đã tồn tại.
- `kiem_tra_ket_noi_wp()` — gọi `/wp-json/wp/v2/users/me`, xác nhận **không
  bao giờ gọi `requests.post`** (test kiểm tra thẳng `mock_post.called ==
  False`) — đúng yêu cầu "không tạo bài khi test kết nối". Phân biệt rõ
  401/403 (auth), 404 (sai URL), 503+non-JSON (nghi WAF/Cloudflare).
- `db_phase2.py` thêm cột `thoi_luong_giay` — migration `ALTER TABLE` an
  toàn cho DB cũ đã tồn tại (test trên DB giả lập schema cũ, không lỗi,
  không mất dữ liệu có sẵn).
- Hiển thị đúng định dạng yêu cầu: thời gian `25/07 10:51`, thời lượng
  `00:01:24` (lưu trữ trong DB vẫn ISO UTC + số giây thô — chỉ đổi tầng
  HIỂN THỊ, không đổi tầng lưu trữ).

**Bug thật phát hiện và sửa lúc nối UI (không phải lý thuyết)**: Tab "4.
Sinh & Đăng" và "5. Theo dõi" ban đầu (từ UI Gate trước) dùng dropdown
site1/site2 (`C.lay_site()`/`C.tat_ca_site()`) — **vi phạm thẳng yêu cầu
"Không hiển thị site1/site2 trong UI Ver 3"**. Phát hiện khi chạy test tích
hợp đầy đủ (`test_v34_that_ui.py`), gây crash `SystemExit: Không có site
"..."`. Sửa: cả 2 tab giờ dùng tên website thật từ `cauhinh.doc_website()`,
không còn tham chiếu `C.lay_site`/`C.tat_ca_site` ở bất kỳ đâu trong luồng
Ver 3 (đã grep xác nhận, chỉ còn ở nhánh RMU).

### T2-10 Integration Test đầy đủ (mock HTTP xuyên suốt UI thật)

`test_v34_that_ui.py` — kịch bản đầy đủ qua UI thật (không gọi hàm logic
trần): nhập MASTER → chọn record → chạy mock (chưa cấu hình gì) → cấu hình
website + AI → chuyển chế độ WordPress thật → nút đổi tên đúng → bấm đăng
(xác nhận qua hộp thoại) → Gemini thật (mock) → Hard Block PASS → dựng
HTML+Schema → WordPress thật (mock) → DB lưu đúng wp_id/url/trạng thái/thời
lượng. **7/7 PASS.**

### Việc CHỈ Thịnh làm được (không phải thiếu sót Gate này)

1. Nhập API key Google thật vào tab "3. Cấu hình", bấm "Kiểm tra API key và
   model" — xác nhận `do_model()` thật sự gọi được Gemini và trả model chạy
   được.
2. Nhập URL/Username/Application Password site WordPress thật, bấm "Kiểm
   tra kết nối" — xác nhận REST API thật trả đúng.
3. Chọn 1 record, chuyển chế độ "WordPress thật", bấm "Đăng Draft lên
   WordPress" — xác nhận **Draft thật xuất hiện trong WordPress Admin**
   (mục tiêu cuối của Gate này).
4. Báo lại kết quả — nếu lỗi, dùng đúng khuôn báo lỗi trong `SPEC.md`, kèm
   nội dung log ở khung Nhật ký (không chứa API key/Application Password —
   2 giá trị này không bao giờ được in ra log, đã verify bằng test AI-1).

---

## UI Gate — Ver 3 (mới nhất)

Mục tiêu duy nhất: đưa luồng MASTER 4-Profile thành UI mặc định (5 tab),
ẩn RMU (Ver 1/2) khỏi màn hình khởi động. Chỉ sửa `giao-dien.py` +
`test_round2_ui_smoke.py` (1 assertion cấu trúc) + thêm `test_ver3_ui.py`
mới. Không đụng AI adapter/prompt/schema/Hard Block/validators/database/
pipeline import.

**Kết quả: 125/125 PASS** trên toàn bộ 6 bộ test (không có bộ nào bị bỏ qua).

| Bộ test | Kết quả | Ghi chú |
|---|---|---|
| `test_ver3_ui.py` (8 test bắt buộc mục I work order) | **8/8 PASS** | Mới, qua Xvfb thật |
| `test_gate2.py` | 23/23 PASS | Không đụng UI, xác nhận business logic không vỡ |
| `test_round2_ui_smoke.py` | 9/9 PASS | 1 assertion cấu trúc cập nhật (xem bên dưới) |
| `test_phase2_full.py` | 12/12 PASS | Không đụng UI |
| `test_snapshot_regex.py` | 39/39 PASS | Không đụng UI |
| `test_round2_integration.py` | 34/34 PASS | Không đụng UI |

### 8 test bắt buộc (mục I work order) — kết quả chi tiết

| # | Test | Kết quả |
|---|---|---|
| I1 | Khởi động chỉ thấy đúng 5 tab Ver 3 | PASS — `['1. Nhập dữ liệu', '2. Sản phẩm', '3. Cấu hình', '4. Sinh & Đăng', '5. Theo dõi']` |
| I2 | Không thấy 7 tab Ver 1/Ver 2 trong giao diện mặc định | PASS — `app.tab.winfo_ismapped() == False` lúc khởi động |
| I3 | UI hiển thị ổn ở 1366×768 | PASS |
| I4 | Chuyển qua lại 5 tab không exception | PASS |
| I5 | Menu Công cụ mở được chế độ RMU | PASS — gọi đúng command menu trỏ tới, xác nhận `che_do_rmu` chuyển `True` |
| I6 | Từ RMU quay lại Ver 3 được | PASS |
| I7 | Chuyển qua lại RMU/Ver3 3 lần không nhân đôi tab/widget | PASS — số tab Ver3 (5→5) và RMU (6→6) không đổi qua 3 lần |
| I8 | Đóng và mở lại app vẫn khởi động ở Ver 3 | PASS — instance mới độc lập vẫn mặc định Ver 3 |

### Kiến trúc chuyển đổi RMU ↔ Ver 3

2 `ttk.Notebook` riêng biệt (`self.tab` = RMU 6 tab gốc, `self.tab_ver3` = 5
tab Ver 3 mới), cả 2 dựng **đúng 1 lần** lúc khởi động, cùng nằm trong 1
`Frame` cha (`self.khung_noi_dung`). Chuyển đổi chỉ `pack()`/`pack_forget()`
— không bao giờ tạo lại widget, nên không có đường nào dẫn tới nhân đôi
widget dù chuyển qua lại bao nhiêu lần (xác nhận qua I7).

Menu "Công cụ → Chế độ RMU (rollback)" — có hộp thoại xác nhận
(`messagebox.askyesno`), đổi nhãn hai chiều: RMU ↔ "Trở về LOTECH VER 3".

### Tái sử dụng logic cũ (không viết lại)

5 tab Ver 3 dùng LẠI đúng các widget/hàm xử lý đã có từ Round 2/Gate 2,
chỉ đổi vị trí đặt (từ 1 tab dồn 5 khối A-E, sang 5 tab riêng) + bổ sung
phần nhìn theo palette bắt buộc:
- `self.bang_phase2`, `_phase2_doi_chon`, `_phase2_chon_hang_loat` — bảng
  sản phẩm + chọn viết bài (nguyên vẹn, chỉ đổi hàm refresh cuối từ
  `_phase2_nap_danh_sach` sang `_v3_loc_san_pham` để có lọc Outline/tìm
  kiếm + thống kê).
- `self.txt_phase2_thu`, `_phase2_xem_prompt`, `_phase2_chay_thu` — xem
  trước prompt/HTML (nguyên vẹn).
- `_phase2_lam_import`, `_phase2_hoi_xac_nhan_dataset` — luồng nhập +
  cảnh báo dataset đổi (nguyên vẹn, chỉ thêm lưu `rpt` để hiện bảng báo cáo).
- `_phase2_chay_hang_loat`, `_phase2_viec_chay_hang_loat`, `_phase2_mau_dang_chon`
  — chạy hàng loạt mock (nguyên vẹn, kể cả bản vá thread-safety từ Gate 2).
- `db_phase2.dashboard/liet_ke_san_pham/liet_ke_dataset/lay_bai_viet` —
  TOÀN BỘ dùng nguyên hàm có sẵn, không sửa `db_phase2.py`. Cột "Tên sản
  phẩm"/"Lỗi" mới trong bảng Theo dõi lấy qua gọi thêm các hàm này (không
  phải sửa module, không phải viết SQL mới trong `db_phase2.py`).

### Thành phần đang DISABLE, ghi "Sẽ triển khai ở Gate sau"

- Tab Cấu hình, khối AI: nút "Kiểm tra model / kết nối".
- Tab Cấu hình, khối Website: TOÀN BỘ (Tên website/URL/Username/App
  Password đều `state='disabled'`; nút Lưu/Sửa/Xoá/Kiểm tra kết nối đều
  disable) — ghi rõ "Sẽ triển khai ở Gate WordPress".
- Tab Sinh & Đăng: radio "WordPress thật" — disable, ghi "Chưa mở ở Gate
  hiện tại".
- Tab Theo dõi: nút "Xuất tracker" — disable, ghi "Sẽ triển khai ở Gate sau".

Không có nút nào tên chung chung ("Chạy"/"Bắt đầu"/"Thực hiện") — nút sinh
bài ghi đúng **"Sinh bài Mock"**.

### Ảnh bằng chứng (`anh-bang-chung-ui/`, 6 ảnh, chụp thật qua Xvfb+ImageMagick)

`01_khoi_dong.png` (khởi động, đủ 5 tab hiện trên thanh tab), `02_tab_san_pham.png`
(tab 2), `03_tab_cau_hinh.png` (tab 3, thấy rõ nút disable + ghi chú Gate
sau), `04_tab_sinh_dang.png` (tab 4, radio WordPress thật bị mờ/disable),
`06_che_do_rmu.png` (chế độ RMU — đúng 6 tab gốc, KHÔNG lẫn tab Ver 3),
`07_tab_theo_doi.png` (tab 5, đủ 11 cột dashboard).

**Không chụp được** ảnh menu Công cụ đang MỞ (dropdown) — môi trường Xvfb ở
đây không có window manager, click chuột giả lập qua `xdotool` không kích
hoạt được popup menu native đúng cách. Đã xác nhận chức năng THẬT qua test
I5 (gọi đúng command menu trỏ tới, kết quả chuyển chế độ đúng) thay vì ảnh
chụp — nói rõ ở đây thay vì đưa ảnh không đúng nội dung.

---

## Content Safety Gate 2

4 task: (1) Schema JSON-LD gắn vào HTML thật, (2) mở rộng Hard Block (bảo
hành/IP/IEC-TCVN/nhiệt độ/%), (3) 2 mẫu `chuan`/`ngan_gon` hoạt động thật
khác nhau, (4) đổi tên phiên bản → **LOTECH AUTOPOST VER 3**.

**Kết quả: 117/117 PASS** trên dữ liệu thật (5.264 record), không dùng dữ
liệu giả lập trừ vài field tiêm tay để test nhánh "record thực sự có" của
Hard Block mở rộng (ghi rõ trong từng test).

| Bộ test | Kết quả |
|---|---|
| `test_gate2.py` (D1-D7, bộ test chính thức Gate 2) | **23/23 PASS** |
| `test_phase2_full.py` (Data Core regression) | **12/12 PASS** |
| `test_snapshot_regex.py` (33 tên thật) | **39/39 PASS** |
| `test_round2_integration.py` (T2-01→T2-12) | **34/34 PASS** |
| `test_round2_ui_smoke.py` (UI thật qua Xvfb) | **9/9 PASS** |

Chạy lại: `python3 test_gate2.py` (và 4 lệnh còn lại như `HUONG-DAN-TEST-ROUND-2.md`).

### Task 1 — Schema JSON-LD trong HTML thật

`render_phase2.dung_schema_script()` mới — bọc `dung_schema()` thành
`<script type="application/ld+json">`, gắn vào cuối `dung_bai_html()`.
Escape `</script` bên trong JSON đề phòng (dữ liệu nguồn khó có chuỗi này,
nhưng phòng thủ không thừa).

- **D1 Product E2E** (4/4 PASS): đúng 1 khối JSON-LD, parse được,
  `@type=Product`, không có `offers`/`price`/`pricecurrency`/`gia_list` ở
  bất kỳ đâu trong schema.
- **D2 Service E2E** (1/1 PASS): dịch vụ (`content_type=service`) → HTML
  không có khối JSON-LD nào (vì `dung_schema()` đã trả `None` từ Round 2,
  `dung_schema_script()` chỉ bọc thêm, không đổi logic quyết định có/không).

### Task 2 — Mở rộng Hard Block

Thêm lớp thứ 3 (`_CUM_MO_RONG_RE`) chạy TRƯỚC lớp cụm kỹ thuật (R2-08) và
lớp token đơn (Round 1): bảo hành theo tháng/năm, cấp bảo vệ `IPxx`, tiêu
chuẩn `IEC`/`TCVN` kèm số, nhiệt độ `°C`, phần trăm `%`. Cùng cơ chế
"chỉ cho phép nếu có trong chính record" như 2 lớp cũ — không field nào
trong 4 profile hiện có mang loại dữ liệu này, nên trong thực tế các cụm
này gần như luôn bị chặn (đúng ý đồ: AI không có cơ sở nào để nhắc).

- **D3** (5/5 PASS): `"Bảo hành 24 tháng"`, `"IP65"`, `"IEC 62271"`,
  `"90°C"`, `"99%"` đều bị BLOCK khi record không có.
- **D4** (5/5 PASS): tiêm tay từng giá trị vào field `quy_cach` của 1 record
  test (mô phỏng "record thực sự có" — hiện chưa profile nào có field thật
  loại này) → cùng nội dung đó KHÔNG bị chặn. Xác nhận cơ chế so khớp đúng,
  không phải hard-code chặn cứng theo từ khoá.
- **D5 Regression** (4/4 PASS): `0.6/1kV`, `300/500V`, `3x50mm²`,
  `3x50+1x25mm²` — giá trị đúng vẫn PASS, giá trị giả (`99/1kV`, `9x50mm²`)
  vẫn BLOCK như Round 2. Không bị 2 lớp mới làm nứt gãy.

### Task 3 — 2 mẫu `chuan`/`ngan_gon` hoạt động thật

`prompts_phase2.MAU_BIEN_THE` — khác nhau ở TẦNG PROMPT (không chỉ dặn AI
"viết ngắn hơn"): `ngan_gon` bỏ hẳn mục `huong_dan_chon_html` và `faq` khỏi
cấu trúc yêu cầu + JSON schema, hệ số độ dài giảm còn ~50%. `goi_ai_mock()`
và `dung_bai_html()` tôn trọng đúng cấu hình này. `dung_slug()` luôn suffix
theo mẫu (`ma-chuan` / `ma-ngan-gon`) — 2 mẫu của cùng sản phẩm, cùng site
không bao giờ trùng slug.

- **D6** (3/3 PASS): HTML khác nhau, slug khác nhau, chạy lại đúng
  `(dataset_id, record_id, site, mau)` KHÔNG tạo bài mới (`wp_id` giữ
  nguyên qua 2 lần gọi liên tiếp).

**Bug thread-safety thật phát hiện và sửa lúc code**: `_phase2_mau_dang_chon()`
(hàm mới, validate tên mẫu người dùng gõ) có thể gọi `messagebox` — nếu gọi
từ luồng nền (`_phase2_viec_chay_hang_loat` chạy qua `chay_nen_phase2`) sẽ vi
phạm nguyên tắc Tkinter không thread-safe (chỉ luồng chính được đụng
widget/dialog). Đã sửa: validate `mau` ở luồng chính (`_phase2_chay_hang_loat`,
hàm gọi trực tiếp từ `command=` của nút bấm) TRƯỚC khi tạo luồng nền, truyền
`mau` đã hợp lệ vào qua tham số — hàm chạy nền không tự đọc/validate lại
widget. Đổi chữ ký `_phase2_viec_chay_hang_loat(self)` →
`_phase2_viec_chay_hang_loat(self, mau)`.

### Task 4 — Đổi tên phiên bản → LOTECH AUTOPOST VER 3

Đổi ở: tiêu đề cửa sổ (`self.title()`), header trong `_dau_trang()`, 3 file
`.bat` (`CAI-DAT-LAN-DAU.bat`, `PHAN-MEM.bat`, `KIEM-THU-30-BAI.bat`), file
tài liệu này, `TIEN-DO.md`. Xác nhận thật qua Xvfb:
`app.title() == 'LOTECH AUTOPOST VER 3'`.

### D7 — Xác nhận KHÔNG gọi WordPress thật

Kiểm bằng `inspect.getsource()` trên `sinh_va_dang_mock()` (hàm UI/test đang
dùng cho toàn bộ luồng Gate 2) — xác nhận không có `dang_wp_that`/
`requests.post` nào trong thân hàm. `dang_wp_that()` (khung thật từ Round 2)
vẫn tồn tại trong `ai_wp_adapter.py` nhưng KHÔNG được gọi ở bất kỳ đường nào
đang chạy trong Gate 2 — đúng giới hạn "không nối `dang_wp_that()` vào nút,
không gửi request WordPress thật" của work order.

### Việc CHƯA làm trong Gate 2 (đúng giới hạn scope, không phải thiếu sót)

- Thiết kế lại UI Ver 3 (5 tab, ẩn RMU) — đó là Gate tiếp theo, chưa được
  phép làm ở Gate 2.
- Cấu hình 1 website chỉnh sửa được — Gate sau Gate UI Ver 3.
- Nối `dang_wp_that()` vào nút, gửi request WordPress thật — Gate cuối cùng.

---

# TEST-REPORT — Round 2 (Data Core Integration + UI)

Chạy trên dữ liệu THẬT: `MASTER_4_PROFILE_SAN_PHAM.xlsx` + 4 file con (5.264
record). AI và WordPress dùng **MOCK** — đúng phạm vi Round 2 ("Chưa yêu cầu
Gemini thật hoặc WordPress thật"). UI test qua **Xvfb thật** (Tkinter thật,
không phải gọi hàm logic trần).

**Kết quả tổng:**
- `test_phase2_full.py` (Data Core regression, không đổi từ Round 1): **12/12 PASS**
- `test_snapshot_regex.py` (33 tên thật, cập nhật theo R2-07): **39/39 PASS**
- `test_round2_integration.py` (T2-01 → T2-10, T2-12 tĩnh): **34/34 PASS**
- `test_round2_ui_smoke.py` (T2-11 + R2-10 A-E qua Xvfb thật): **9/9 PASS**, ổn định 3/3 lần chạy liên tiếp

Tổng cộng: **94/94 PASS**. Không có test nào bị xoá hay bỏ qua để né lỗi.

Chạy lại:
```
python3 test_phase2_full.py
python3 test_snapshot_regex.py
python3 test_round2_integration.py
xvfb-run -a python3 test_round2_ui_smoke.py     # Linux không màn hình
python3 test_round2_ui_smoke.py                  # Windows/máy có màn hình thật
```

## Test nào chạy THẬT, test nào MOCK, test nào CHƯA test được

| Thành phần | Trạng thái | Ghi chú |
|---|---|---|
| Đọc Excel, normalize, validator, regex, routing | **THẬT** | Trên đúng 5.264 record gốc |
| Database (`db_phase2.py`) | **THẬT** | SQLite thật, thao tác UPSERT/khoá kép thật |
| Prompt Phase 2 (`prompts_phase2.py`) | **THẬT** | Text prompt thật sinh ra, chưa gửi đi đâu |
| AI viết nội dung | **MOCK** | `goi_ai_mock()` — theo đúng phạm vi Round 2 |
| Đăng WordPress | **MOCK** | `dang_wp_mock()` — theo đúng phạm vi Round 2 |
| UI (`giao-dien.py` tab Phase 2) | **THẬT** | Tkinter thật, chạy qua Xvfb (Linux headless) |
| UI trên Windows thật | **CHƯA TEST** | Môi trường này không có Windows — cần Thịnh xác nhận |
| Gemini thật (model `gemini-3.6-flash`) | **CHƯA TEST** | Không có API key |
| WordPress thật | **CHƯA TEST** | Không có site/Application Password thật |

## Chi tiết theo hạng mục R2-01 → R2-12

### R2-01 Import Orchestrator
`import_phase2_pipeline()` gộp đủ 10 bước. Test T2-01 (5.264/5.264) + T2-02
(data_checksum MASTER = 4 file con) đều PASS. Trả đúng báo cáo
`{ok, loai_nguon, ket_qua_theo_profile, loi}` — đã kiểm cả nhánh lỗi (dataset
đổi → raise đúng loại cảnh báo, không tự nối).

### R2-02 Database đa site/đa mẫu
3 bảng `dataset`/`san_pham_phase2`/`bai_viet_phase2`, khoá đúng yêu cầu. Test
T2-04 (2 site độc lập) + T2-05 (2 mẫu độc lập) PASS, kèm test idempotent
(gọi lại đúng khoá trả cùng `wp_id`, không đẻ bài mới).

### R2-03 Import lại dataset — UPSERT
Test riêng lúc code (không nằm trong bộ test tự động, chạy tay 1 lần, kết
quả ghi lại ở đây để không mất dấu): sửa 1 field rồi import lại cùng
`data_checksum` → `du_lieu_json` cập nhật, `selected` giữ nguyên, bài viết đã
đăng (`wp_id`/`trang_thai`) giữ nguyên 100%. PASS.

### R2-04 Dataset metadata
Đủ 10 field: `dataset_id, profile_id, source_file, file_checksum,
data_checksum, row_count, column_structure, pipeline_version, created_at,
updated_at`. Test T2-02 xác nhận qua `data_checksum`.

### R2-05 Prompt Phase 2 thật
7 outline (`outline_cap_dien, outline_tu_dong_cat, outline_vo_tu,
outline_may_bien_ap, outline_do_luong, outline_phu_kien, outline_service`),
mỗi outline có system instruction/cấu trúc nội dung/JSON schema riêng qua 1
hàm lắp ráp dùng chung (`xay_prompt()`). AI chỉ được trả field biên tập
(`meta_title, meta_description, intro_html, dac_diem_html, ung_dung_html,
huong_dan_chon_html`, `faq` nếu outline cho phép) — không tự dựng bảng/schema.

**Golden Prompt Test (T2-06)**: lấy 2 record thật cho mỗi outline_id thực tế
xuất hiện trong dữ liệu (9 nhóm — 7 outline chính + 2 lần route phụ vào
`outline_phu_kien` từ cap_dien-phụ-kiện và máy-biến-áp-giá-treo) = 18 record,
kiểm đủ: có strict rules, có JSON schema, không Giá List, giữ đơn vị. **18/18
PASS.**

### R2-06 Render HTML
`dung_bai_html()` ghép: AI editorial (đã `sanitize_html`) + bảng thông số
(code tự dựng, KHÔNG sanitize) + `<p><strong>Giá:</strong> Liên hệ</p>` (cố
định, không đọc `gia_list`) + CTA (code tự dựng từ `cauhinh.py` thật, không
phải AI viết). Test riêng: field lạ AI tự thêm (`'gia_list_co_the_lo':
'999999'`) bị lọc, không lọt vào HTML — **PASS**.

### R2-07 Giữ nguyên đơn vị
Sửa nhãn `cot_bang` mang đúng đơn vị theo cột nguồn: `"Tiết diện (mm²)"`,
`"Công suất (kVA)"`, `"Cấp điện áp (kV)"`. Với 2 cột sau (máy biến áp), giá
trị được strip hậu tố đơn vị lặp lại (validator mới:
`_chuan_hoa_don_vi_may_bien_ap()`), để không hiện `"Công suất (kVA): 15
kVA"` (sai, lặp đơn vị) mà đúng `"Công suất (kVA): 15"`. Cột `"Cấp điện áp"`
của cáp điện (không có đơn vị trong tên cột gốc) giữ nguyên embedded-unit vì
đơn vị đổi theo từng dòng (V hoặc kV) — **không** áp strip. Verify thật trên
dữ liệu: `<tr><th>Công suất (kVA)</th><td>15</td></tr>`. `test_snapshot_regex.py`
đã cập nhật lại kỳ vọng nhóm D theo format mới, 39/39 PASS.

### R2-08 Chống bịa số theo cụm — Composite Hard Block
Nâng cấp `kiem_tra_bia()`: bắt cụm kỹ thuật hoàn chỉnh (số nối bằng
`x`/`+`/`/`, có thể kèm đơn vị) TRƯỚC, cắt phần đã xét ra khỏi text, phần còn
lại mới kiểm token đơn như cũ. So sánh cụm sau khi bỏ đơn vị (phần SỐ mới là
thứ cần chống bịa, đơn vị có/không tuỳ quy ước field theo R2-07).

**T2-07 — đúng 4 case GPT yêu cầu + 1 case tự thêm, cả 5 đều PASS:**
- Record có `0.6/1kV`, AI viết `99/1kV` → **BLOCK**
- Record có tiết diện `3x50`, AI viết `9x50mm²` → **BLOCK**
- Giá trị đúng nguyên cụm (`0.6/1kV`, `3x50mm²`) → **PASS** (không chặn)
- Số chỉ có ở record khác → **BLOCK**
- (Thêm) đa lõi cộng `3x50+1x25mm²` đúng → PASS; `3x50+1x95mm2` sai → BLOCK

**Bug thật phát hiện lúc code**: nếu chỉ kiểm ở mức token đơn, cụm giả
`"99/1kV"` sẽ KHÔNG bị chặn — vì token con `"1kV"` trích ra từ nó trùng với
token `"1kV"` trích từ giá trị hợp lệ `"0.6/1kV"` của chính record đó. Đây
đúng là lỗ hổng R2-08 mô tả, đã xác nhận tái hiện được trước khi sửa, và
Composite Hard Block đã chặn đúng sau khi sửa.

### R2-09 Sanitize HTML
Whitelist đúng danh sách R2-09 (`h2,h3,p,ul,ol,li,strong,em,table,thead,
tbody,tr,th,td,a,br` + `class="specs-table"`/`colspan`/`rowspan`/`href` có
kiểm soát). Sửa 1 điểm lúc code: `bleach` mặc định chỉ xoá TAG `<script>`/
`<style>` nhưng GIỮ text bên trong — thêm bước xoá cả nội dung trước khi đưa
qua `bleach`. **T2-09: 2/2 PASS** (xoá sạch `script/onclick/style/
javascript:/iframe`, giữ nguyên bảng code tự dựng có `class="specs-table"`).

### R2-10 UI Integration
Tab "6. Phase 2 (4-Profile)" thật trong `giao-dien.py`, 5 khối A-E:
- **A**: nút "Chọn file Excel..." gọi `import_phase2_pipeline()` qua
  dispatcher chung, tự nhận diện MASTER/file con/RMU cũ; cảnh báo dataset đổi
  qua `messagebox.askyesno` (Có → tự động chạy lại với `confirm_new_dataset=True`).
- **B**: Treeview hiện `dataset_id`/`record_id`/`profile`/`outline`/`ten`,
  bấm đúp bật/tắt chọn viết.
- **C**: "Xem prompt" (đúng prompt Phase 2 thật) + "Chạy AI mock + dựng HTML"
  hiện Title/Meta/Slug/kết quả Hard Block.
- **D**: chạy hàng loạt AI mock + đăng WP mock cho sản phẩm đã chọn.
- **E**: dashboard lọc theo site, hiện `wp_id`/`wp_url`/trạng thái.

**Bug thật phát hiện VÀ SỬA lúc test qua Xvfb** (không phải giả định — tái
hiện được, sửa xong verify lại ổn định 3/3 lần):
`_phase2_doi_chon()` (bấm đúp chọn/bỏ chọn) gọi `_phase2_nap_danh_sach()` để
refresh bảng — hàm này XOÁ HẾT rồi CHÈN LẠI toàn bộ Treeview, làm **mất
focus/selection** đang có. Hậu quả thật: sau khi người dùng bấm đúp 1 dòng để
chọn, nếu bấm tiếp "Xem prompt" mà không click lại vào dòng đó trước, hàm
không tìm thấy dòng đang chọn. Đã sửa: `_phase2_doi_chon()` khôi phục lại
`focus()`/`selection_set()` đúng dòng vừa bấm sau khi refresh xong; đồng thời
`_phase2_dong_dang_chon()` thêm fallback dùng `.selection()` nếu `.focus()`
trống, giảm rủi ro tương tự ở các đường gọi khác.

**T2-11 luồng RMU legacy**: `test_round2_ui_smoke.py` xác nhận app khởi động
đủ 7 tab (RMU 0-5 nguyên vẹn + Phase 2 tab 6), gọi lại toàn bộ hàm nạp dữ
liệu RMU cũ (`doc_cau_hinh, nap_san_pham, nap_kien_thuc_bang, nap_dashboard,
_nap_sp_thu`) không crash. **PASS.**

### R2-11 AI/WordPress Adapter
`ai_wp_adapter.py`:
- `goi_ai_mock()` — chỉ dùng field có thật trong `effective_cot_ai(row)`,
  không bịa, nên tự nhiên đi qua Hard Block như AI thật phải tuân thủ.
- `dang_wp_mock()` — idempotent theo khoá `(dataset_id, record_id, site,
  mau)`, gọi lại không đẻ bài mới.
- `dang_wp_that()` — khung cho lúc có site/key thật, TÁI SỬ DỤNG
  `autopost.go_json`/`doc_429`/`Usage`/`_auth`/`tim_bai_theo_slug`/`HEADERS`
  qua **import trực tiếp** (không copy code) — các hàm đó vốn đã generic
  (nhận `ma_site`, không phụ thuộc schema RMU) nên dùng lại được nguyên vẹn.
  **CHƯA TEST** — không có site/key thật ở môi trường này.

### R2-12 Dependency & gói giao
Thêm `bleach` vào `CAI-DAT-LAN-DAU.bat` (dòng cài `pip install`),
`PHAN-MEM.bat` (dòng kiểm tra + cài lần đầu), `_kiem_thu_vien()` trong
`giao-dien.py` (log cảnh báo nếu thiếu, kèm ghi chú riêng cho `bleach`). Kiểm
ZIP sạch — xem mục "Đóng gói" bên dưới.

## Đóng gói (T2-12)

Trước khi nén ZIP, đã kiểm tay:
- Không có file `.db` nào trong gói (`phase2-du-lieu.db`, `test_*.db` đều bị
  xoá trước khi zip — DB tự tạo rỗng lúc app chạy lần đầu, đúng yêu cầu).
- Không có `cau-hinh.env` thật (chỉ có `cau-hinh.env.MAU` — file mẫu, không
  chứa key/mật khẩu thật).
- Không có `sites-them.json` (file site thêm tay qua UI, không tồn tại ở môi
  trường build này vì chưa ai thêm site qua UI).
- Không có API key, Application Password, hay `products.csv`/dữ liệu nội bộ
  sinh ra từ test.
- `du_lieu_goc/` CÓ giữ lại 5 file Excel gốc (dữ liệu sản phẩm thật của
  Thịnh, không phải bí mật/key) — giữ để `test_round2_integration.py`/
  `test_round2_ui_smoke.py` chạy lại được ngay khi Thịnh nhận gói, không phải
  dữ liệu cần giấu.

## Việc CHỈ Thịnh làm/xác nhận được (không phải thiếu sót Round 2)

1. Chạy `PHAN-MEM.bat` trên Windows thật — Round 2 chỉ test được qua `Xvfb`
   (Linux headless) vì môi trường này không có Windows.
2. Gọi Gemini thật, verify model `gemini-3.6-flash` tồn tại.
3. Đăng WordPress thật — `dang_wp_that()` đã viết khung, tái sử dụng máy móc
   `autopost.py`, chưa test vì không có site/Application Password thật.
4. 1 dòng máy biến áp lỗi đánh máy nguồn thiếu chữ "V" (đã flag từ Round 1,
   không đổi ở Round 2) — cần sửa tay Excel gốc nếu muốn dòng đó có điện áp.
