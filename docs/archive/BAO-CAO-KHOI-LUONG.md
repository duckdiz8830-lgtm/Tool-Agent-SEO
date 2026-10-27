# BÁO CÁO KHỐI LƯỢNG — VER 3.6: Mock Batch Integrity + Tab Order

## 1. Thời gian

- Bắt đầu: 2026-07-25 12:17:11 UTC
- Kết thúc: 2026-07-25 12:25:00 UTC
- Tổng: ~8 phút chạy công cụ đo được giữa 2 mốc git snapshot — **đây là
  khoảng cách giữa 2 lần commit, không phải đồng hồ bấm giờ liên tục** (một
  phần thời gian thật nằm ở các bước đọc/hiểu code, thiết kế, và không tính
  được tách bạch việc "nghĩ" khỏi việc "gõ lệnh"). Không thổi phồng thành số
  chính xác hơn mức này.

## 2. Số file đã sửa

8 file (6 code + 2 test), không tính 4 file tài liệu + 1 tracker cập nhật ở
bước cuối.

## 3. Danh sách file đã sửa và lý do

| File | Lý do sửa |
|---|---|
| `render_phase2.py` | Thêm `rut_gon_an_toan()` (Task 1) — cắt chuỗi tại ranh giới từ, không cắt giữa token kỹ thuật. Áp dụng cho `title`/`meta_description` trong `dung_bai_html()` (dùng chung Mock + Real). |
| `ai_wp_adapter.py` | `goi_ai_mock()`: `meta_title` dùng `rut_gon_an_toan()` thay `ten[:60]`; `faq.q` dùng nguyên tên thay `ten[:40]` (Task 1 — đúng nguyên nhân gây 22/245 lỗi batch). |
| `giao-dien.py` | Đổi thứ tự gọi hàm dựng 5 tab: Cấu hình → Nhập dữ liệu → Sản phẩm → Sinh & Đăng → Theo dõi (Task 3.1). Đổi nhãn số thứ tự 3 tab bị dịch vị trí. Không đổi callback/state bên trong từng tab. |
| `test_v34_that_ui.py` | MOCK-3 đổi từ kiểm chuỗi `"Xong" in nhãn` (pass giả) sang đếm chính xác qua DB, assert `thành_công == tổng và lỗi == 0` (Task 2). |
| `test_ver3_ui.py` | Cập nhật 2 chỗ giả định thứ tự tab cũ (danh sách nhãn kỳ vọng ở test I1, index chụp ảnh tab Cấu hình từ 2 → 0) khớp thứ tự mới (Task 3.1 kéo theo). |
| `PHAN-MEM.bat` | Thêm thông báo "bước tiếp theo" ở cả 2 nhánh thành công (trước đây launch xong không in gì) (Task 3.2). |
| `CAI-DAT-LAN-DAU.bat` | Đổi toàn bộ `set VAR=value` sang `set "VAR=value"` — an toàn với đường dẫn có dấu cách (Task 3.2). |

## 4. Số file mới

1 — `test_v36_regression.py` (16 test: token kỹ thuật không bị cắt qua 4
pattern × 9 giới hạn khác nhau + biên off-by-one, batch thật 245 record, và
3 test "PROOF" chứng minh assertion mới thật sự bắt được lỗi mà assertion
cũ bỏ lọt).

## 5. Dòng code thêm/xoá

`git diff --stat` (chỉ `.py`/`.md`/`.bat`, đã loại ảnh test):
```
8 files changed, 244 insertions(+), 29 deletions(-)
```

## 6. Test mới

16 test case trong `test_v36_regression.py` + 2 assertion mới thay thế 1
assertion cũ trong `test_v34_that_ui.py` (MOCK-3 tách thành 2 dòng kiểm
chặt hơn).

## 7. Collected/PASS/FAIL/SKIPPED

**181/181 PASS, 0 FAIL, 0 SKIPPED** — chạy từ thư mục khác hẳn thư mục code
gốc (`/tmp/v36_check`, mô phỏng giải nén ZIP trên máy khác), verify portable
thật, không chỉ verify tại chỗ.

| Bộ test | Kết quả |
|---|---|
| `test_that_mocked.py` | 21/21 |
| `test_gate2.py` | 23/23 |
| `test_phase2_full.py` | 12/12 |
| `test_snapshot_regex.py` | 39/39 |
| `test_round2_integration.py` | 34/34 |
| `test_v36_regression.py` (mới) | 16/16 |
| `test_v35_idempotency.py` | 11/11 |
| `test_round2_ui_smoke.py` | 9/9 |
| `test_ver3_ui.py` | 8/8 |
| `test_v34_that_ui.py` | 8/8 (MOCK-3 tách 2 dòng, trước là 7/7) |
| **TỔNG** | **181/181** |

Command chạy lại — xem `TEST-REPORT.md` mục "VER 3.6".

## 8. Hạng mục hoàn thành theo ID tracker

| ID tracker | Hạng mục | Trạng thái |
|---|---|---|
| (không có ID riêng — bug từ review độc lập) | Task 1: sửa `goi_ai_mock()` cắt token kỹ thuật | **XONG** — batch 245/245, 0 lỗi |
| (không có ID riêng — bug từ review độc lập) | Task 2: siết `test_v34_that_ui.py`, thêm regression | **XONG** — chứng minh được assertion cũ pass giả, assertion mới fail đúng |
| `REQ-UI-01` | Đổi thứ tự tab: Cấu hình(1) → Nhập dữ liệu(2) → Sản phẩm(3) → Sinh & Đăng(4) → Theo dõi(5) | **XONG** |
| (không có ID riêng) | Harden `PHAN-MEM.bat` + `CAI-DAT-LAN-DAU.bat` | **XONG** |
| (không có ID riêng) | `BAO-CAO-KHOI-LUONG.md` + cập nhật 4 tài liệu + tracker | **XONG** (file này) |

## 9. Hạng mục chưa hoàn thành

Không có mục nào trong phạm vi đã duyệt (Task 1/2/3 của cả 2 bản GPT prompt
+ REQ-UI-01) bị bỏ dở.

**Cố ý KHÔNG làm** (đúng giới hạn đã chốt, không phải thiếu sót):
`REQ-FILTER-01` (Filter Builder, Ver 3.7), `REQ-OUTLINE-02` (Outline Studio,
Ver 3.8), `REQ-PLAN-01`/`REQ-PLAN-02`/`REQ-POST-01` (Article Jobs/số lượng
bài +/-/đăng toàn bộ batch thật, Ver 3.9) — tracker `10_YEU_CAU_MOI_25_07`
đã tự xếp các mục này vào Gate sau trước khi tao bắt đầu, không phải tao tự
quyết định cắt.

## 10. Phần không test được do giới hạn môi trường

Không đổi so với Ver 3.5 — sandbox này vẫn không gọi được
`generativelanguage.googleapis.com` hay WordPress thật. Ver 3.6 không đụng
gì tới luồng Gemini/WordPress thật (đúng giới hạn "Không đổi logic Save
Draft đang PASS regression" và "Không sửa API key logging") nên rủi ro phát
sinh mới ở mảng đó gần như bằng 0 — chỉ sửa Mock generator, test, thứ tự
tab, và 2 file `.bat`.

Bản thân 2 file `.bat` (`PHAN-MEM.bat`, `CAI-DAT-LAN-DAU.bat`) chưa chạy thử
trên Windows thật — chỉ soát cú pháp/logic bằng mắt và đối chiếu checklist
(quote đường dẫn, `set "VAR=value"`, kiểm `errorlevel`, in nguyên nhân +
`pause` khi lỗi, in bước tiếp theo khi thành công).

## 11. Việc Thịnh cần chạy trên Windows

1. Mở app, xác nhận **đúng thứ tự 5 tab**: Cấu hình → Nhập dữ liệu → Sản
   phẩm → Sinh & Đăng → Theo dõi.
2. Chạy thử batch Mock (tab Sinh & Đăng, chế độ Mock/Test) trên 1 dataset
   bất kỳ, xác nhận không còn lỗi Hard Block do cắt token kỹ thuật.
3. Test `PHAN-MEM.bat`/`CAI-DAT-LAN-DAU.bat` trên thư mục có dấu cách trong
   tên (VD `C:\Users\Thinh Nguyen\Lotech App\`) — chưa test được trên
   Windows thật ở đây.
4. **CHƯA đổi gì về Gemini/WordPress thật** — nếu vẫn muốn tiếp tục Draft
   thật, làm theo đúng `HUONG-DAN-DANG-DRAFT-THAT.md` (không đổi từ 3.4/3.5).

## 12. Rủi ro còn lại

- Đổi thứ tự tab là thay đổi UI trực tiếp người dùng nhìn thấy đầu tiên khi
  mở app — dù test tự động xác nhận đúng thứ tự và không nhân đôi
  widget/callback, vẫn nên Thịnh tự mở thử 1 lần để chắc chắn không có gì
  "cảm giác sai" mà test tự động không đo được (bố cục, thói quen bấm).
- `rut_gon_an_toan()` có thể tạo ra `meta_title`/`meta_description` **ngắn
  hơn dự kiến** trong trường hợp cực đoan (tên sản phẩm có từ đầu tiên dài
  hơn cả giới hạn) — đã test case này (case "MOTUTHONGNOICUCDAIKHONGCODAUCACH..."
  trả nguyên chuỗi, dài hơn giới hạn) nhưng đây là dữ liệu giả lập cực đoan,
  chưa chắc khớp 100% với tên sản phẩm thật dài nhất trong MASTER.
- 2 file `.bat` chưa chạy thật trên Windows (xem mục 10).

## 13. File ZIP bàn giao

`Lotech-Autopost-Ver3.6.zip`

---

## Kết luận rõ ràng (theo đúng yêu cầu bàn giao)

- **Batch 245 sản phẩm máy biến áp (Mock): PASS** — 245/245 thành công, 0 lỗi.
- **Tổng regression (181 test, 10 file): PASS** — 0 FAIL, verify portable từ thư mục khác thư mục code gốc.
- **Thứ tự tab: PASS** — đúng Cấu hình(1)→Nhập dữ liệu(2)→Sản phẩm(3)→Sinh & Đăng(4)→Theo dõi(5), test tự động xác nhận không nhân đôi tab/widget khi chuyển RMU↔Ver3.
- **Bug còn mở**: không có bug mới phát sinh từ Ver 3.6. Các mục còn treo từ trước (Gemini/WordPress thật chưa test mạng thật, `.bat` chưa test Windows thật, 1 dòng máy biến áp lỗi đánh máy nguồn) không đổi, xem `KNOWN-ISSUES.md`.
- **Việc Thịnh cần test tiếp**: xem mục 11 ở trên.

Dừng đúng theo yêu cầu — không tự chuyển sang Gate Draft thật, không động
tới Outline Studio hay Article Jobs.
