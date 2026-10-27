---
name: sonealeo-code-change
description: Quy trình bắt buộc khi sửa code hoặc đóng gói SONEALEO ULTRA (app Python/Tkinter, file chính giao-dien.py, pipeline MASTER Excel → Gemini → HTML/Schema → WooCommerce). Dùng skill này BẤT CỨ KHI NÀO người dùng nhắc tới SONEALEO, giao-dien.py, phien_ban.py, cot_import, import_phase2_pipeline, MAU_RAC, phase2-du-lieu.db, tab Hàng đợi, hoặc yêu cầu sửa/thêm tính năng/đóng gói ZIP/bump version cho công cụ autopost của Lotech — kể cả khi họ chỉ nói "sửa cái này" mà không nhắc tên hệ thống. Skill chứa 4 luật không thương lượng, checklist tiền đóng gói, và script đóng gói ZIP đúng chuẩn.
---

# SONEALEO ULTRA — quy trình sửa code

Hệ thống này do một người duy nhất (Tim) phát triển và vận hành. Không có code review từ người khác, không có CI. Nghĩa là mọi guard rail phải nằm trong quy trình, không nằm trong tổ chức. Đó là lý do 4 luật dưới đây tồn tại — mỗi luật sinh ra từ một lần đã hỏng thật.

## 4 luật không thương lượng

### 1. Đụng `cot_import` → phải chạy `import_phase2_pipeline` trên MASTER thật trước khi đóng gói

`column_structure` có guard sẽ **chặn im lặng** nếu cấu trúc cột lệch. Không exception, không log rõ ràng — dữ liệu chỉ đơn giản không vào. Test bằng fixture lý tưởng không bắt được lỗi này vì fixture luôn đúng cấu trúc.

Chạy trên file MASTER thật đang dùng, không phải bản rút gọn.

### 2. Không suy ra UX từ việc đọc code

Đọc code Tkinter rồi kết luận "nút này nằm ở đây, luồng chạy thế này" là sai nhiều hơn đúng. Phải chạy giao diện thật dưới Xvfb rồi đo.

Cần: `python3-tk`, `xvfb`, `tksheet`.

```bash
xvfb-run -a python3 giao-dien.py
```

Nếu môi trường không chạy được Xvfb thì **nói thẳng là chưa verify**, đừng mô tả UX bằng suy đoán.

### 3. Không bao giờ xoá thư mục `tests/`

Kể cả khi đóng gói, kể cả khi test đang fail, kể cả khi có vẻ thừa. `tests/` đi kèm mọi bản ZIP.

### 4. Bump `phien_ban.py` mỗi lần đổi code

Kể cả sửa một dòng. `phien_ban.py` là nguồn sự thật duy nhất về version.

Từng có lần `phien_ban.py` đứng ở `4.6.2` suốt 5 đợt phát triển trong khi marker trong code đã đi tới `5.4` — hậu quả là hai bug đã fix xong vẫn hiện ra như đang mở trong tài liệu. Doc rot có giá thật.

**Đã có sẵn công cụ bắt lỗi này, dùng nó:**

```bash
python3 phien_ban.py
```

Script tự quét mọi file `.py` (trừ `tests/`, `qa/`, `docs/`) tìm mốc `Ver x.y` cao nhất trong comment, đối chiếu với hằng `PHIEN_BAN`, lệch thì báo đỏ. Chạy lệnh này **trước** khi đóng gói. `scripts/dong_goi.py` cũng gọi nó tự động.

Cùng lúc bump version, cập nhật (chú ý: nằm trong `docs/`, không phải thư mục gốc):
- `docs/NHAT-KY-THAY-DOI.md` — viết **lúc** làm, không viết sau
- `docs/TIEN-DO.md` — trạng thái hạng mục
- `docs/KNOWN-ISSUES.md` — đóng issue đã fix, đừng để tồn

## Quy tắc đóng gói ZIP

Mọi bản ZIP:
- **Loại trừ**: `phase2-du-lieu.db`, `cau-hinh.env` (chứa API key và dữ liệu cục bộ — không bao giờ vào gói)
- **Bao gồm**: `tests/`
- Version string trong `phien_ban.py` đã bump

Dùng `scripts/dong_goi.py` thay vì zip tay. Script tự kiểm tra 3 điều kiện trên và **từ chối đóng gói** nếu thiếu. Xem phần Script bên dưới.

## Cách bàn giao code

Giao **file hoàn chỉnh đã hợp nhất**, không giao patch từng phần, không giao hướng dẫn kiểu "mày mở file rồi tìm dòng 3.412 sửa thành...".

Lý do: `giao-dien.py` đang **5.344 dòng** (đo trên bản 5.5). Patch thủ công trên file cỡ này là nguồn lỗi lớn hơn cả bug đang sửa. (Ngưỡng 6.000 dòng đã được đặt làm mốc cân nhắc tách file — khi chạm tới thì nêu ra, đừng tự tách.)

## Kỷ luật phát biểu

Gắn mức tin cậy cho mọi nhận định kỹ thuật, phân biệt rõ ba loại:

- **Xác nhận từ code** — đã đọc đúng đoạn đó trong file thật
- **Dựng ngược** — suy ra từ hành vi, log, hoặc code liên quan; chưa thấy trực tiếp
- **Giả định** — chưa có bằng chứng

Không trộn ba loại này vào cùng một câu khẳng định. Không biết thì nói không biết.

## Code từ AI khác

Có một nhánh phát triển song song do AI khác (Fable) làm, và GPT được dùng review độc lập ở một số điểm. **Không nhận code từ nhánh đó vào codebase mà chưa đọc lại**.

Khi review nhận định của AI khác: đối chiếu với code thật, xác nhận điểm đúng, phản bác điểm sai kèm bằng chứng. Không mặc định họ đúng, cũng không mặc định họ sai.

## Bối cảnh hệ thống (để khỏi hỏi lại)

- **Phiên bản hiện tại: 5.5** (`PHIEN_BAN = '5.5'`, khớp với mốc cao nhất trong code)
- App Python/Tkinter, file chính `giao-dien.py`, ~60 module `.py` ở thư mục gốc
- Chạy test: `python3 run_tests.py` — `tests/` hiện có 87 file
- Định nghĩa profile & bản đồ cột: `profiles.py`, dict `PROFILES`
- DB: `%APPDATA%\SONEALEO\phase2-du-lieu.db`
- Config: `%APPDATA%\SONEALEO\cau-hinh.env`
- Pipeline: MASTER Excel → Gemini API → HTML + Schema JSON-LD → WooCommerce REST
- ~5.264 SKU, 8 site WordPress
- Gemini: quota free tier tính **theo Google Cloud project**, không theo key. Thêm key trong cùng project không tăng quota.

## Script

`scripts/dong_goi.py` — hai chế độ:

```bash
# Chỉ kiểm tra, không tạo file
python3 scripts/dong_goi.py kiem-tra /duong/dan/toi/source

# Kiểm tra rồi đóng gói
python3 scripts/dong_goi.py dong-goi /duong/dan/toi/source --ra /duong/dan/output
```

Script kiểm tra: `phien_ban.py` tồn tại và đọc được version, `tests/` tồn tại và không rỗng, không có file cấm nào lọt vào danh sách đóng gói. Nếu bất kỳ điều kiện nào fail, script thoát với mã lỗi và **không tạo ZIP**.

Nếu `phien_ban.py` chưa bump so với lần đóng gói trước, script cảnh báo nhưng vẫn cho chạy nếu có cờ `--bo-qua-version` — dùng cờ này thì phải nói rõ với người dùng là đã bỏ qua.

## Việc đang tồn đọng (đọc trước khi đề xuất việc mới)

- Patch cáp `VA-4.4.1.8` chưa merge — thiếu file
- 336 dòng MBA mới: mới có 5/17 dòng bảng thông số
- `catalogue-mv-cadivi.xlsx` chưa join vào 446 SKU trung thế
- `du_lieu_bat_buoc` đang 0 dòng code
- Chưa có test cho Ver 5.4
- 17 SKU trùng, 19 SKU sai outline — đã hạ ưu tiên có chủ đích, đừng tự nâng lên

Trước khi đề xuất tính năng mới, đối chiếu danh sách này. Việc tồn đọng thường có giá trị cao hơn tính năng mới.
