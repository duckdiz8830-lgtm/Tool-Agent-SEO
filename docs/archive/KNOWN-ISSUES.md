# KNOWN ISSUES & BACKLOG — Lotech Autopost MAIN

Không xoá mục nào ở đây khi làm xong tính năng liên quan trong code — chuyển
xuống phần "Đã xong" kèm số bản, để còn tra lại lịch sử.

## VER 3.6 — việc còn lại, chỉ Thịnh làm được

Bug batch Mock (223/245) đã vá, test siết lại không cho pass giả, thứ tự
tab đã đổi, 2 file `.bat` đã harden. 181/181 test PASS (xem
`BAO-CAO-KHOI-LUONG.md`/`TEST-REPORT.md`). Còn lại:

1. **Mở app xác nhận đúng thứ tự tab trên Windows thật** — test tự động đã
   xác nhận qua Xvfb (Linux), chưa chạm màn hình Windows thật.
2. **Chạy batch Mock thật trên Windows** — xác nhận không còn lỗi cắt token
   kỹ thuật trên máy thật (đã test kỹ trên sandbox, số liệu chắc đúng,
   nhưng "chạy thật lần đầu trên Windows" luôn là bước cuối cần Thịnh làm).
3. **Test `PHAN-MEM.bat`/`CAI-DAT-LAN-DAU.bat` trên thư mục có dấu cách** —
   đã soát logic/cú pháp bằng mắt theo checklist, CHƯA chạy trên Windows
   thật.
4. Toàn bộ mục "chỉ Thịnh làm được" từ Ver 3.5 (Gemini thật, WordPress
   thật, Draft thật) — KHÔNG đổi gì ở Ver 3.6, xem mục "VER 3.5" bên dưới.

## Đã xong ở Ver 3.6 — trước đây là bug từ review độc lập

- [x] **Batch Mock 245 sản phẩm máy biến áp: 245/245, 0 lỗi** (trước 223/245)
      — `goi_ai_mock()` không còn cắt giữa token kỹ thuật
      (`22/0.4KV`/`3x50+1x25mm²`...) nhờ `rut_gon_an_toan()` mới.
- [x] **`test_v34_that_ui.py` MOCK-3 không còn pass giả** — đếm chính xác
      qua DB thay vì chỉ tìm chữ "Xong", có test riêng chứng minh assertion
      cũ thật sự bỏ lọt lỗi.
- [x] **Thứ tự tab đúng `REQ-UI-01`**: Cấu hình(1) → Nhập dữ liệu(2) → Sản
      phẩm(3) → Sinh & Đăng(4) → Theo dõi(5).
- [x] **`PHAN-MEM.bat`/`CAI-DAT-LAN-DAU.bat` harden** — thông báo bước tiếp
      theo khi thành công, `set "VAR=value"` an toàn dấu cách.

## VER 3.5 — việc còn lại, chỉ Thịnh làm được

Code Ver 3.5 đã xong (vá 3 lỗ hổng GPT phát hiện độc lập trên bản 3.4 +
hoàn thiện idempotency), test đầy đủ 164/164 PASS verify từ thư mục khác hẳn
(xem `TEST-REPORT.md`). Còn lại CHỈ việc cần mạng thật + tài khoản thật —
sandbox code chạy không ra ngoài internet được, nên KHÔNG có cách nào tự
làm các việc dưới đây được:

1. **Xác nhận Gemini thật hoạt động** — nhập `GOOGLE_API_KEY` thật vào tab
   "3. Cấu hình", bấm "Kiểm tra API key và model". Logic chắc đúng (test
   mock 6/6 case + Hard Block đã gộp dùng chung), còn việc request thật có
   đi qua được hay không thì chỉ chạy thật mới biết.
2. **Xác nhận kết nối WordPress thật** — nhập URL/Username/Application
   Password site thật, bấm "Kiểm tra kết nối". Logic đã test kỹ bằng mock
   (kể cả case idempotency/migration qua `test_v35_idempotency.py`) nhưng
   chưa chạm request thật lần nào.
3. **Tạo Draft thật đầu tiên** — mục tiêu chính. Chọn 1 record, chuyển chế
   độ "WordPress thật", bấm "Đăng Draft lên WordPress", xác nhận Draft xuất
   hiện đúng trong WordPress Admin. Xem `HUONG-DAN-DANG-DRAFT-THAT.md`.
4. **Test UI trên Windows thật** (treo từ Round 2, chưa đổi) — mọi test ở
   đây chạy qua `Xvfb` (Linux headless). Toàn bộ file `test_*ui*.py` viết
   sẵn chạy được trên Windows (bỏ `xvfb-run -a`).
5. **Chạy thử `5-KIEM-TRA-KET-QUA.bat`** trên Windows thật — logic đã test
   kỹ qua `cong_cu_kiem_tra_ket_qua.py` chạy trực tiếp, nhưng bản thân file
   `.bat` (đường dẫn Python bundle, `chcp`, dấu cách thư mục) chưa test trên
   Windows thật.
6. **1 dòng máy biến áp không tự sửa được bug kVA/kV** (treo từ Round 1,
   chưa đổi) — lỗi đánh máy nguồn thiếu chữ "V".
7. **Ảnh, category, tag WordPress cho nhánh 4-profile** — ngoài phạm vi mọi
   Gate tới giờ, không phải quên.
8. **Gộp `phase2-du-lieu.db` với `du-lieu.db` cũ** (treo từ Round 1, chưa
   đổi) — chưa quyết, hỏi Thịnh trước khi động vào.
9. **`goi_ai_mock()` vẫn là mô phỏng đơn giản** cho chế độ Mock/Test — không
   phản ánh văn phong AI thật, chỉ dùng để test đường ống kỹ thuật.

## Đã xong ở Ver 3.5 — trước đây là lỗ hổng GPT phát hiện qua kiểm tra độc lập

- [x] **Hard Block Mock/Preview giờ CHẶN ĐÚNG** dữ liệu bịa trong
      `meta_title`/`meta_description`/`faq.q` — trước đây (bản 3.4) Mock tự
      kiểm 1 đoạn RIÊNG hẹp hơn Real, có thể báo "đăng thành công" dù dữ
      liệu bịa vẫn còn. Đã gộp dùng chung `kiem_tra_bia_toan_bo()`.
- [x] **Idempotency dùng khoá URL chuẩn hoá** (`site_key`), tách khỏi tên
      hiển thị — đổi tên website không còn làm mất liên kết bài cũ; đổi
      domain được coi đúng là website khác. Migration tự động, giữ nguyên
      wp_id/url/trạng thái/thời lượng.
- [x] **`test_v34_that_ui.py` hết hard-code path** — chạy được từ ZIP đã
      bàn giao, không chỉ chạy được trên máy dev.
- [x] **4 file tài liệu thống nhất số liệu test** (164/164), lấy từ 1 lần
      chạy thật, verify portable.
- [x] **Dọn callback `after()` lúc đóng app** — hết lỗi Tcl
      `invalid command name`.
- [x] **`5-KIEM-TRA-KET-QUA.bat`** — xem kết quả không cần mở GUI, wrapper
      mỏng dùng lại nguyên hàm `db_phase2.py`.

## Đã xong ở Gate "First Real Draft" (bản 3.4) — trước đây nằm trong mục "chưa xây"

- [x] `goi_ai_that()` — gọi Gemini thật đúng 1 record, theo pattern retry đã
      chứng minh đúng ở `autopost.goi_gemini()`. Logic test đầy đủ bằng mock
      HTTP (6/6 case), CHƯA chạy request thật (xem mục còn lại #1).
- [x] `dang_wp_that()` viết lại hoàn chỉnh — ép cứng draft, idempotent, dò
      lại slug trước khi retry (không retry mù). Logic test đầy đủ (8/8 case
      mock HTTP kể cả case "timeout nhưng server đã tạo bài thật"), CHƯA
      chạy request thật (xem mục còn lại #2, #3).
- [x] Cấu hình 1 website Ver 3 (Lưu/Sửa/Xoá/Kiểm tra kết nối) — `cauhinh.py`
      ghi/đọc `cau-hinh.env` khoá `WP_WEBSITE_*`, không đụng `autopost.py`.
- [x] Hard Block E2E phủ đủ `meta_title/meta_description/faq.q/faq.a`.

## Đã xong ở Round 2 (trước đây nằm trong mục "chưa xây" ở Round 1)

- [x] Wiring `giao-dien.py` — tab "6. Phase 2 (4-Profile)" đủ 5 khối A-E,
      test qua Xvfb thật, PASS 9/9 ổn định 3/3 lần.
- [x] Cảnh báo dataset mới hiển thị qua `messagebox.askyesno`, không còn là
      exception thô ném ra ngoài.
- [x] Dashboard hiển thị theo `(dataset_id, record_id, site, mau)`.
- [x] Prompt Phase 2 thật cho AI — `prompts_phase2.py`, đủ 7 outline.

## Kiến trúc profile ngành hàng — tầm nhìn đã chốt, chưa xây (nhánh RMU)

Ý tưởng: phần mềm không dùng một outline chung cho mọi sản phẩm. Nó phải hoạt
động như khuôn lắp ráp linh hoạt:

```
Excel đầu vào
→ nhận diện sản phẩm thuộc nhóm nào
→ nạp cấu hình của nhóm đó (hồ sơ ngành hàng)
→ chọn outline phù hợp
→ giữ nguyên dữ liệu kỹ thuật
→ chỉ giao đúng phần cần thiết cho AI
→ bật/tắt Schema, FAQ, ảnh, CTA theo lựa chọn
→ sinh bài
```

**Ba lớp cấu hình cần có:**

1. **Hồ sơ loại sản phẩm** — bộ trường kỹ thuật riêng từng ngành. Tủ RMU cần
   relay/số ngăn/dòng ngắn mạch; cáp điện cần số lõi/tiết diện/vật liệu ruột
   dẫn — hai bộ trường không giống nhau, không ép chung một khuôn.
2. **Công thức nội dung** — mỗi nhóm sản phẩm có outline riêng (tủ RMU cần giải
   thích ngăn/relay; cáp điện cần bảng quy cách/cách chọn tiết diện).
3. **Khối bật/tắt** — tick chọn: Bảng thông số, Ứng dụng, FAQ, Product Schema,
   Article Schema, CTA báo giá, Sản phẩm liên quan, Bảng giá, Catalogue, So
   sánh sản phẩm. Sản phẩm chưa có giá thì tắt Bảng giá, không ép mọi bài mặc
   cùng bộ đồ.

**Chính sách dữ liệu theo từng trường:**

| Loại dữ liệu | Ai cung cấp | AI được sửa? |
|---|---|---|
| Model, điện áp, thông số kỹ thuật, giá, tình trạng kho | Excel/người dùng | Không |
| Giải thích cấu hình, ứng dụng, mở bài | AI dựa trên dữ liệu | Có |
| FAQ | AI nhưng phải bám dữ liệu | Có, có giới hạn |
| CTA | Cấu hình website | Có giới hạn |
| Schema | Phần mềm dựng | AI không tự viết tuỳ tiện |

Nguyên tắc: **AI được phép diễn giải, không được phép phát minh thông số.**

**Cấu trúc thư mục dự kiến khi xây:**

```
profiles/
├── tu-rmu
├── may-bien-ap
├── cap-dien
├── dau-cap
├── chong-set-van
├── su-cach-dien
├── phu-kien-duong-day
└── generic          <- chưa có profile riêng thì dùng cái này, vẫn sinh
                          được bài cơ bản chứ không chết cứng
```

Mỗi profile chứa: cách nhận diện, trường kỹ thuật bắt buộc/tuỳ chọn, trường AI
được bổ sung, outline mặc định, module được phép bật, quy tắc Schema/ảnh/FAQ,
quy tắc chống bịa riêng ngành đó.

**Nhận diện tự động khi nhập Excel** (chưa xây): engine cố xác định
Ngành hàng → Nhóm sản phẩm → Loại sản phẩm → Hãng → Series → Outline mặc định.
Độ tin cậy thấp thì hỏi lại người dùng, không đoán bừa rồi áp outline sai ngành
(vd. lôi outline tủ RMU trùm lên đầu cốt nhôm).

**Dashboard cần hiện quyết định của hệ thống:**

| SKU | Nhóm phát hiện | Độ tin cậy | Outline | Module bật | Thiếu dữ liệu |
|---|---|---|---|---|---|
| RM6-DE-B | Tủ RMU | 96% | Sản phẩm | Spec, FAQ, Schema | Thiếu ảnh |
| CVV-4x16 | Cáp hạ thế | 93% | Báo giá | Spec, Giá, FAQ | Thiếu giá |
| ABC-123 | Chưa rõ | 42% | Generic | Spec cơ bản | Cần chọn nhóm |

Người dùng sửa được: nhóm sản phẩm, outline, module bật/tắt, trường nào cho AI
viết, trường nào giữ nguyên.

**Trước mắt:** chỉ làm profile Tủ RMU cho file test (đã có sẵn, nằm trong
`prompts.py` dạng đơn giản, chưa tách thành hồ sơ riêng). Lõi phần mềm phải
thiết kế sao cho thêm cáp điện/máy biến áp/đầu cáp/phụ kiện đường dây sau này
không phải đập code làm lại — giống lắp thêm khuôn vào máy ép, không phải mua
lại cả nhà máy. **Chưa bắt tay xây, đang ở giai đoạn chốt kiến trúc.**

---

## Lỗi/thiếu đã xác nhận, chưa sửa — thứ tự ưu tiên

1. `du_lieu_bat_buoc` cho từng outline — outline báo giá mà trống giá thì đừng
   sinh bài rỗng.
2. HTML từ AI chưa được lọc thẻ an toàn (sanitize), câu trả lời FAQ chưa
   escape — rủi ro AI lỡ chèn thẻ lạ vào bài.
3. Cache `kho_toan_bo` (danh sách trắng chống bịa số) không tự làm mới khi sửa
   `products.csv` bằng tay rồi nhập lại qua đường CSV thay vì qua Excel.
4. Ảnh: khớp tên file theo mã đầy đủ (không chỉ mã rút gọn kiểu `RM6-DE-B.jpg`
   khớp nhầm nhiều SKU), resize, WebP, featured image, alt/caption.
5. Liên kết nội bộ: thiếu hậu tố outline trong URL khi có nhiều outline cùng
   sản phẩm, có thể trỏ tới bài chưa đăng (chỉ nên trỏ bài đã DA_DANG).
6. Gán chuyên mục và thẻ khi đăng WordPress — hiện bài rơi hết vào "Chưa phân
   loại".
7. Bộ nghiệm thu 30 bài mô phỏng resume bằng đọc lại kho dữ liệu, chưa test
   bằng cách kill process thật rồi mở lại.
8. Selection (`chon`) hiện là thuộc tính toàn cục của (danh_muc, sku), không
   phân theo site. Hai site cùng bán chung một danh mục thì bật/tắt chọn viết
   sẽ ảnh hưởng cả hai site cùng lúc. Chưa rõ đây có phải hành vi mong muốn hay
   không — cần Thịnh xác nhận trước khi đổi.
9. Ngưỡng trùng văn biên tập (75%) chưa hiệu chỉnh trên dữ liệu AI thật, mới
   test bằng giả lập. Chạy 30-50 bài thật rồi xem tỷ lệ cảnh báo có hợp lý
   không, chỉnh `NGUONG_TRUNG_VAN` trong `autopost.py` nếu cần.

## Đã xong

- Lọc sản phẩm theo site/ngành hàng khi sinh bài — v2.4.
- Gộp nhầm SM6 vào series RM6 do sheet quét trước thắng — v2.4.
- SKU làm khoá toàn cục, hai ngành trùng SKU đè nhau — v2.4 (đổi khoá kép
  `(danh_muc, sku)`).
- Bài lỗi không ghi vào dashboard, chỉ vào log.csv — v2.4.
- WordPress có thể đẻ bài `-2` khi mạng chập chờn giữa lúc đăng — v2.4.
- `thinkingConfig` chưa vào request sinh bài thật, model mới cắt JSON giữa
  chừng — v2.5.
- `MODEL_GEMINI` mặc định là model đã chết (404) — v2.4.
- Nút "Lưu cấu hình" bị khuất ngoài màn hình ở cửa sổ nhỏ — v2.4.
- `CAI-DAT-LAN-DAU.bat` đoán sai cấu trúc gói tkinter — v2.4.
- Sản phẩm trùng bị tự gộp, mất record — v2.6 (giữ riêng, không gộp).
- UI thêm/xoá site WordPress không cần sửa code — v2.6.
- Vân tay thông số + trùng văn biên tập — v2.7.
