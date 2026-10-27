# HƯỚNG DẪN TEST ROUND 2 — Phase 2 (4-Profile)

Dành cho Thịnh, test trên máy Windows thật. Không cần đọc code, làm theo
từng bước.

## 1. Cài đặt (chỉ làm 1 lần)

Nếu máy đã cài từ trước (bản v2.8): mở `CAI-DAT-LAN-DAU.bat` chạy lại 1 lần
để cài thêm thư viện `bleach` (thư viện lọc HTML an toàn, Round 2 mới cần).

Nếu máy chưa cài gì: chạy `CAI-DAT-LAN-DAU.bat` như bình thường, `bleach` đã
được thêm sẵn vào danh sách cài.

## 2. Mở phần mềm

Bấm đúp `PHAN-MEM.bat`. Cửa sổ hiện ra sẽ có **7 tab**, tab cuối cùng tên
**"6. Phase 2 (4-Profile)"** — đây là tab mới của Round 2. 6 tab đầu (0-5) là
luồng tủ RMU cũ, không đổi gì, vẫn dùng như trước.

Nếu tab "6. Phase 2" báo thiếu thư viện `bleach` ở khung nhật ký phía dưới —
quay lại bước 1.

## 3. Thử luồng Phase 2 (5 bước, không cần Gemini/WordPress thật)

### Bước A — Nhập dữ liệu

Trong khối **A. Nhập MASTER hoặc file profile**, bấm **"Chọn file Excel..."**,
chọn file `MASTER_4_PROFILE_SAN_PHAM.xlsx` (hoặc 1 trong 4 file con:
`01_Cap_Dien.xlsx`, `02_Tu_Va_Thiet_Bi_Dong_Cat.xlsx`,
`03_May_Bien_Ap_Do_Luong.xlsx`, `04_Phu_Kien_Va_Khac.xlsx`).

Khung nhật ký phía dưới sẽ in ra 4 dòng — mỗi profile 1 dòng, kèm `dataset_id`
và số dòng đã nhập. Lần đầu nhập sẽ ra `(moi)`, nhập lại đúng file đó lần
nữa sẽ ra `(giong_het_import_lai)` — không tạo dataset mới, không mất dữ
liệu đã có.

**Nếu bạn sửa file Excel rồi nhập lại**: phần mềm sẽ hỏi "Dataset đã đổi —
xác nhận đây là dataset MỚI?". Bấm **Có** nếu đúng là bạn cố ý sửa dữ liệu
(bài viết cũ, WP ID cũ vẫn được giữ nguyên, không mất). Bấm **Không** nếu
bạn nhập nhầm file, sửa lại rồi thử nhập đúng file gốc.

### Bước B — Xem danh sách sản phẩm

Ở ô **Dataset** phía trên bảng, chọn 1 dataset (VD
`ds_cap_dien_001 (cap_dien, 3387 dòng)`). Bảng bên dưới hiện danh sách sản
phẩm của dataset đó.

**Bấm đúp vào 1 dòng** để bật/tắt chọn viết bài — cột "Chọn" hiện dấu ✓ khi
đã chọn. Có thể dùng nút "Chọn dòng hiện trên bảng" / "Bỏ chọn dòng hiện trên
bảng" để chọn/bỏ hàng loạt.

### Bước C — Xem trước 1 bài

Bấm chọn 1 dòng trong bảng (không cần bấm đúp, chỉ cần click chọn), rồi:

- **"Xem prompt"** — hiện đúng nội dung sẽ gửi cho AI thật sau này (system +
  dữ liệu sản phẩm + cấu trúc bài + JSON schema bắt buộc). Đọc để kiểm tra
  prompt có hợp lý không, có thiếu dữ liệu gì không.
- **"Chạy AI mock + dựng HTML"** — chạy thử toàn bộ luồng (AI giả lập viết
  nội dung mẫu, dựng bảng thông số, dựng HTML, kiểm chống bịa số) và hiện
  kết quả. Dòng "Hard Block" cuối cùng cho biết có số nào bị chặn không (bình
  thường sẽ không có gì bị chặn, vì AI giả lập chỉ dùng đúng dữ liệu có sẵn).

**Lưu ý:** AI ở bước này là **giả lập** (viết theo khuôn mẫu cố định, không
phải AI thật) — dùng để kiểm tra đường ống kỹ thuật (prompt đúng chưa, bảng
thông số đúng chưa, chống bịa số có hoạt động không), KHÔNG phải để đánh giá
văn phong AI thật sẽ viết.

### Bước D — Chạy hàng loạt (vẫn là mock)

Chọn **Site** (site đã cấu hình ở tab "2. Cấu hình"), điền **Mẫu** (gõ tự do,
VD `chuan`), bấm **"Chạy cho SP đã chọn"**. Phần mềm sẽ chạy AI mock + "đăng"
WordPress mock (không đăng thật) cho tất cả sản phẩm đang có dấu ✓ ở bảng B.

### Bước E — Xem dashboard

Bấm **"Tải lại dashboard"** — bảng hiện toàn bộ bài đã "đăng" (mock), có thể
lọc theo Site. Cột cuối "WP ID / URL" là dữ liệu giả lập (VD
`1001 https://lotech.mock/...`) — không phải link thật, chỉ để kiểm tra
luồng lưu trữ đúng.

## 4. Những gì CHƯA làm được ở Round 2 (cần bạn xác nhận trước khi làm tiếp)

- **Chưa gọi Gemini thật** — nút ở Bước C/D hiện tại luôn dùng AI giả lập.
  Khi nào bạn có API key và muốn thử AI thật, báo lại để nối tiếp.
- **Chưa đăng WordPress thật** — tương tự, cần site + Application Password
  thật.
- **Chưa test trên máy Windows** — Round 2 tao chỉ test được trên máy ảo
  Linux (không có màn hình thật). Nếu tab "6. Phase 2" có gì hiển thị lệch,
  chữ bị cắt, hoặc nút bấm không phản hồi trên Windows — báo lại theo khuôn
  lỗi ở `SPEC.md`, kèm ảnh chụp màn hình nếu được.

## 5. Nếu muốn tự chạy lại bộ test bằng tay (không bắt buộc)

Mở Command Prompt tại thư mục phần mềm, gõ lần lượt:

```
python test_phase2_full.py
python test_snapshot_regex.py
python test_round2_integration.py
python test_round2_ui_smoke.py
```

3 lệnh đầu chạy vài giây, in ra `PASS`/`FAIL` từng dòng, kết thúc bằng dòng
tổng kết kiểu `TỔNG: 34/34 PASS`. Lệnh cuối (`test_round2_ui_smoke.py`) sẽ
tự mở và tự đóng 1 cửa sổ phần mềm để test — đừng bấm gì vào cửa sổ đó khi
nó tự chạy, đợi nó tự đóng xong (khoảng 5-10 giây).

## 6. Báo lỗi (nếu có)

Dùng đúng khuôn trong `SPEC.md`:
```
VERSION: Phase 2 Round 2
LỖI: ...
CÁCH TÁI HIỆN: 1. 2. 3.
KẾT QUẢ HIỆN TẠI: ...
KẾT QUẢ MONG MUỐN: ...
FILE: (ảnh chụp màn hình nếu có)
```
