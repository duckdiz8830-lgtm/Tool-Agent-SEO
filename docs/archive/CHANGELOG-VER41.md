# CHANGELOG-VER41.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER39.md` cho lịch sử Ver 3.7.1/3.8/3.9.

---

## LOTECH AUTOPOST VER 4.1 — Gemini reliability + Hard Block layer 4 + Chuẩn hoá MASTER — 26/07/2026

Gộp chung "Ver 4.0" (ổn định Gemini thật) và "Ver 4.1" (chuẩn hoá MASTER)
thành 1 bản duy nhất theo yêu cầu — không tách 2 lần bàn giao.

**Bối cảnh bắt buộc phải làm:** log chạy thật 26/07 cho thấy batch 10 sản
phẩm thật → **0/10 thành công** (6 lỗi JSON hỏng, 4 lỗi Hard Block chặn
nhầm). Đây là nút thắt sản xuất thật, không phải tối ưu thêm.

### Phần 1 — Gemini thật ổn định hơn

**Thêm `responseSchema` vào request Gemini** (`ai_wp_adapter.goi_ai_that()`).
Trước đây chỉ có `responseMimeType: application/json` — Gemini tự do hơn
về cấu trúc, dễ lệch khi bài dài. Giờ ép đúng schema (OpenAPI subset) dựa
trên `prompts_phase2._json_schema()` đã có sẵn (trước đây tính ra nhưng bỏ
phí, gán vào biến `_schema` không dùng). Hàm chuyển đổi mới:
`_sang_gemini_schema()`.

**Log lỗi parse JSON kèm `finishReason`** — trước đây chỉ báo lỗi parse
suông, không biết Gemini tự báo đã viết xong (STOP) hay bị cắt
(MAX_TOKENS đã bắt riêng từ trước). Giúp chẩn đoán đúng nguyên nhân lần
sau nếu vẫn còn lỗi, không đoán mò.

*Việc CHỈ Thịnh làm được: chạy lại batch thật, xác nhận tỷ lệ 0/10 có
tăng lên không — sandbox không gọi được Gemini thật.*

### Phần 2 — Hard Block lớp 4 (chống chặn nhầm, KHÔNG nới lỏng thủng)

Bug thật từ log 26/07: field `cấp điện áp` lưu cặp không đơn vị
(`12.7/0.23` — điện áp sơ/thứ cấp máy biến áp). AI viết lại tự nhiên
thành `12.7KV` (tách 1 nửa cặp) — số có thật trong record, nhưng bị chặn
vì lớp 3 (token đơn lẻ) chưa từng thấy số này đứng riêng kèm đơn vị.

**Vá theo đúng yêu cầu của Thịnh:** không nới kiểu "thấy số là cho qua"
(dễ thủng thật) — chỉ nới khi **cả 3 điều kiện** cùng đúng: (1) giá trị là
số con thật tách từ 1 cụm ghép trong CHÍNH record này, (2) đơn vị AI viết
thuộc đúng **họ đơn vị** của field sinh ra cụm đó (điện áp chỉ chấp nhận
kV/V, không chấp nhận A/mm dù trùng giá trị số), (3) chỉ áp dụng cho field
đã khai báo rõ trong `_FIELD_HO_DON_VI` — không áp dụng tràn lan mọi field.

Test âm quan trọng nhất (`HB-C2`): số `12.7` đúng giá trị nhưng gắn đơn vị
`A` (dòng điện, sai họ so với field điện áp) — **vẫn phải bị chặn**, xác
nhận không thủng theo kiểu GPT cảnh báo.

### Phần 3 — Chuẩn hoá MASTER, đóng gói thành công cụ thật (`chuan_hoa_master.py`)

**Đã có 1 lần giao lỗi (GPT review bắt được), đã vá + test qua đúng
pipeline import thật, không lặp lại sai lầm cũ:**

| Lỗi GPT phát hiện | Vá |
|---|---|
| Chèn dòng tiêu đề phía trên header → `nhap_phase2._doc_sheet_theo_header()` giả định cứng header ở dòng 1 → import chết | Bỏ hẳn dòng tiêu đề, header về đúng dòng 1 |
| `00_Dashboard` đặt sheet đầu → `nhan_dien_loai_nguon()` chỉ đọc `wb.sheetnames[0]` → nhận nhầm cả file sang định dạng cũ | Dashboard chuyển xuống CUỐI danh sách sheet |
| Parser máy biến áp: regex thiếu ranh giới đơn vị, bắt nhầm `2.5VA` (công suất biến dòng) thành `2.5V` (điện áp sai) — vẫn đóng dấu CONFIRMED | Copy đúng kỷ luật `\b` từ `_SO_DON_VI` (regex Hard Block thật, vốn đã đúng) sang regex trích xuất — verify lại: 26 dòng từng bị sai giờ về đúng trạng thái CAN_KIEM |
| (Dashboard lỗi công thức — GPT nêu, **không tái hiện được** sau khi rà soát kỹ, số liệu khớp tuyệt đối với đếm tay Python) | Không cần sửa, giữ nguyên |

**Bài học quy trình quan trọng nhất:** lần giao trước chỉ kiểm tra bằng
mắt (thứ tự dòng, giá trị) — KHÔNG chạy qua đúng hàm `import_4_profile()`
thật của app. Lần này bắt buộc: mọi lần chạy `chuan_hoa_master.py` đều có
test tự động gọi thẳng `nhan_dien_loai_nguon()` + `import_4_profile()` +
so sánh `record_id` tuyệt đối với file gốc — không chỉ tin vào "nhìn có vẻ
đúng".

**Đóng gói thành công cụ dùng lại được**, không phải file kết quả 1 lần:
```
python3 chuan_hoa_master.py --nguon du_lieu_goc --ra MASTER_ENRICHED.xlsx
```
Chạy lại bất cứ khi nào có bản `du_lieu_goc` mới — không phải nhờ Claude
làm lại từ đầu mỗi lần.

**Field trích được (regex, KHÔNG suy đoán/gọi AI):** Tiết diện, Cấp điện
áp, Công suất (điền vào ô trống, không đè giá trị đã có), Tiêu chuẩn
TCVN/IEC, Loại lõi MBA — mỗi field gắn `Trạng Thái Kiểm Duyệt`
(CONFIRMED/CAN_KIEM) + `Ghi Chú Kiểm Duyệt` giải thích rõ thiếu gì, field
nào là phụ (không bắt buộc, không hạ trạng thái). Đánh dấu (KHÔNG tự sửa)
nghi ngờ phân loại sai và trùng mã/tên.

### File sửa

- `ai_wp_adapter.py` — `responseSchema`, log `finishReason`.
- `render_phase2.py` — Hard Block lớp 4.
- `giao-dien.py` — chỉ đổi tiêu đề app "VER 4.1" (không đổi UI/luồng nào khác).

### File mới

- `chuan_hoa_master.py` — công cụ chuẩn hoá MASTER, chạy dòng lệnh.
- `test_v41_gemini_hardblock.py` — 10 test (schema + Hard Block lớp 4, gồm test âm chống thủng).
- `test_v41_chuan_hoa_master.py` — 13 test (chạy tool qua dòng lệnh thật, import qua pipeline thật, record_id, không ghi đè, regex đúng).

### Không làm (đúng scope đã chốt)

- Không sửa Article Jobs theo ngữ nghĩa slug/bài cũ — Thịnh nói để sau khi test xong.
- Không đụng UI cosmetic khác ngoài tiêu đề — vẫn để dành cho 4.x sau.
- Không tự động chạy `chuan_hoa_master.py` trong luồng import chính của app — vẫn là công cụ tách riêng, chạy tay khi cần, tránh rủi ro đổi hành vi import mặc định mà chưa được duyệt.
