# CHANGELOG-VER38.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER37.md` cho lịch sử Ver 3.7.

---

## LOTECH AUTOPOST VER 3.8 — Outline Studio — 26/07/2026

### Ver 3.7.1 — patch trước khi làm 3.8 (theo yêu cầu GPT review độc lập)

GPT review `Lotech-Autopost-Ver3.7.zip` → FAIL, 2 bug chặn. Cả 2 đã vá,
xác nhận bằng test âm (fault injection), KHÔNG chỉ sửa rồi tin suông.

| Bug | File | Vá | Test xác nhận |
|---|---|---|---|
| Exception ngoài dự kiến (không phải `{'ok': False}`) làm chết cả batch, kẹt UI | `giao-dien.py`, `_v3_viec_dang_draft_that_hang_loat()` | Bọc try/except riêng từng record trong vòng lặp; exception nào cũng bị bắt, ghi `trang_thai=loi` kèm tên lỗi, record kế tiếp vẫn chạy. Đưa `self.ui(_v3_nap_dashboard)`/`self.ui(_v3_ket_thuc_chay)` vào `finally` — nút Sinh/Đăng và Dừng LUÔN được reset đúng trạng thái dù có lỗi gì | `test_v37_1_patch.py` PATCH-A1..A4: tiêm `RuntimeError` giả ở record #2/5 → 4 record còn lại vẫn chạy xong, nút bấm được reset đúng |
| Vẫn có đường đẻ `slug-2`: POST tạo mới timeout (không biết server đã tạo chưa) + dò slug lại cũng lỗi mạng → code cũ vẫn thử POST tạo mới lần nữa | `ai_wp_adapter.py`, `dang_wp_that()` | Chỉ khi **cả 2** điều kiện đúng cùng lúc — (a) đây là lần đầu đăng record này (`da_co is None`) VÀ (b) request tạo mới hoàn toàn không có phản hồi (`r is None` — timeout/lỗi mạng, không phải 5xx có phản hồi) — mà bước dò slug ngay sau đó CŨNG lỗi mạng, thì DỪNG HẲN, trả lỗi rõ ràng, KHÔNG thử tạo lại. Trường hợp đã biết chắc bài tồn tại (`da_co` có sẵn) thì hành vi cũ giữ nguyên, không ảnh hưởng | `test_v37_1_patch.py` PATCH-B1/B2: giả lập đúng kịch bản GPT nêu → xác nhận CHỈ 1 lần POST tạo mới, không có lần 2. PATCH-B3 (đối chứng): trường hợp an toàn vẫn retry PUT bình thường, không đổi hành vi |

Sai lệch tài liệu GPT nêu, đã sửa:
- Tracker `P0-4` (lọc theo site/trạng thái) từng ghi DONE — **sai, đã sửa lại TODO**. Ver 3.7 chỉ làm P0-2/P0-3, chưa làm bộ lọc.
- Tracker "không còn known issue chặn" — đã sửa đúng thực tế trước/sau patch.
- KHÔNG sửa: tên thư mục ZIP (`Lotech-Autopost-Ver3.6`), tiêu đề app ("LOTECH AUTOPOST VER 3"), UI chưa hiện tên record đang chạy (chỉ in console) — theo đúng yêu cầu Thịnh: "lỗi UI để sau khi đi hết 3.9".

---

### Ver 3.8 — Outline Studio

**Mục tiêu:** cho Thịnh tự chỉnh cách AI viết bài (giọng văn, hướng dẫn
từng mục) mà không cần nhờ Claude sửa code mỗi lần — đúng nhu cầu vừa bàn
(Excel thiếu field kỹ thuật thì Outline Studio giải quyết ĐƯỢC phần "cách
viết", KHÔNG giải quyết được phần "thiếu số liệu" — việc đó vẫn cần bổ
sung cột dữ liệu, ngoài phạm vi Ver 3.8).

**Nguyên tắc khoá cứng (không thương lượng):** CHỈ cho sửa phần "block AI"
— góc nhìn (đối tượng đọc/giọng văn) + hướng dẫn viết 4 mục (giới thiệu,
đặc điểm, ứng dụng, hướng dẫn lựa chọn) + ghi chú riêng outline. KHÔNG cho
sửa qua UI: danh sách field AI được trả, giới hạn độ dài, `co_faq`
(đổi field này đổi cả JSON schema), và **tuyệt đối không đụng
`QUY_TAC_CHUNG`** (luật Hard Block chống bịa số) — luật này nằm cứng trong
code, Outline Studio không có đường nào chạm tới.

**File mới:**
- `outline_studio.py` — đọc/ghi/trộn tuỳ chỉnh, lưu vào 1 file JSON riêng
  (`outline-tuy-chinh.json`, không đổi DB/schema). File hỏng/tay sửa sai →
  coi như chưa có tuỳ chỉnh, không crash. `OUTLINE_NOI_DUNG` gốc trong
  `prompts_phase2.py` không bao giờ bị sửa — khôi phục mặc định lúc nào
  cũng ra đúng bản gốc.

**File sửa:**
- `prompts_phase2.py` — `he_thong()`/`nguoi_dung()` đọc cfg qua
  `_cfg_hieu_luc()` (trộn override), KHÔNG đổi `_json_schema()` hay
  `truong_ai_duoc_tra()` — 2 hàm này vẫn đọc thẳng `OUTLINE_NOI_DUNG` gốc,
  đảm bảo cấu trúc JSON/Hard Block không bị Outline Studio ảnh hưởng.
- `giao-dien.py` — thêm tab "6. Outline Studio": chọn outline, 6 ô nhập
  (góc nhìn + 4 mục + ghi chú), nút Lưu/Khôi phục mặc định/Xem trước.
  "Xem trước" hiển thị ĐÚNG prompt thật (system + user) sẽ gửi Gemini,
  KHÔNG dùng bản Mock giả lập — vì `goi_ai_mock()` có template cứng riêng,
  không đọc mô tả section nên không phản ánh được thay đổi (nếu preview
  bằng Mock sẽ trông như "không đổi gì" dù đã sửa, gây hiểu lầm).

**Không làm** (đúng scope đã chốt, không tự mở rộng):
- Không cho tạo outline mới, không xoá outline có sẵn (7 outline cố định).
- Không cho đổi `co_faq`, không cho thêm/bớt field AI được trả.
- Không đổi bảng thông số kỹ thuật, Schema.org JSON-LD — vẫn 100% code kiểm soát.
- Không làm UI đẹp hơn mức cần thiết để dùng được (Text widget thường, không rich-text editor).
