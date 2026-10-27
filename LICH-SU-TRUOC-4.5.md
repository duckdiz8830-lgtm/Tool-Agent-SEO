# SONEALEO ULTRA — lịch sử phiên bản (gộp)

27 file CHANGELOG/KẾT-QUẢ/HOTFIX rời trước 4.5 đã gộp vào đây.

---

## BAN-GIAO-VER-3.1

### BÀN GIAO SONEALEO ULTRA 3.1 — 06/08/2026 (Fable code chính)

Giải nén ĐÈ lên thư mục tool đang dùng. AN TOÀN vì gói này CỐ TÌNH
không chứa `phase2-du-lieu.db` và `cau-hinh.env` — dữ liệu và key của
bạn không bị đè. Lần đầu chạy lại nhớ bấm `CAI-DAT-LAN-DAU.bat` (đã
thêm tksheet vào danh sách cài).

## Đã sửa gì (7 việc + 1 màn hình mới)

**3 lỗi nối GUI (P0 — GPT bắt):**
1. Bước 2 đọc biển máy — hết văng `AttributeError`, xong báo rõ số
   lượt AI / cache / lỗi.
2. Bước 3 đọc PDF — hết cộng nhầm tuple, quota trừ theo LƯỢT AI thật.
3. Bước 5 ghép MASTER — hết `ValueError`; file tên có chữ "bien" tự
   được ưu tiên hơn catalogue.

**4 vá module vision/enrich:**
4. Lỗi `'parts'` tràn log hôm 06/08: model Gemini 3.x "suy nghĩ" ăn hết
   ngân sách token trước khi kịp trả lời. Giờ: sàn token 1000, thiếu
   thì tự thử lại với ngân sách gấp 4, JSON hỏng thử lại 1 lần, vẫn
   hỏng thì LƯU NGUYÊN VĂN vào `.vision-cache/raw-loi/` để soi. AI
   phân loại chết hẳn -> trang PDF có điểm từ khoá cao vẫn được đọc
   bằng rule (không vứt trang).
5. Vỏ mạ kẽm hết thành Pokémon điện ⚡ — 24+ dòng phụ kiện (vỏ, giá
   treo, ty, móc...) bị loại khỏi tính dòng định mức. Chạy lại Bước 1
   (TCVN) để có file sạch — file `_TCVN` cũ nên xoá.
6. Cache tính cả prompt + model — sửa prompt xong chạy lại là đọc lại
   thật, không ăn kết quả cũ.
7. Bảng TCVN máy khô mức 250kVA: 98,49 -> **98,46** (đối chiếu ảnh
   catalogue THIBIDI bạn chụp; mức 1000 và 2500 cũng được ảnh đó xác
   nhận đúng).

**Màn hình mới — 2 tab con trong nhóm 1. DỮ LIỆU** (file riêng
`man_hinh_du_lieu.py`, God Class chỉ thêm 5 dòng gọi):
- **Làm giàu dữ liệu (3.1)**: quăng file bất kỳ (ảnh / PDF / cả thư
  mục) vào hàng đợi -> "Moi dữ liệu" -> kết quả hiện lên BẢNG SỬA TẠI
  CHỖ, dòng nghi vấn TÔ VÀNG -> sửa/gỡ dấu X ngay trong bảng -> Lưu ->
  Ghép vào MASTER. Có đèn `● Đang đọc — tắt thoải mái` / `■ ĐANG GHI —
  đừng tắt` thay cho nút dừng (Alt+F4 lúc đèn xanh là vô hại).
- **Xem dữ liệu (3.1)**: mở master, chọn "Soi cột còn trống" -> thấy
  ngay "118/245 dòng ĐANG TRỐNG cột Po" — trả lời câu *còn phải đi
  kiếm data ở đâu*. Kèm nút **Mở trong Excel** + **Nạp lại** cho sửa
  nặng.

## Kiểm định (chạy trên máy Fable, môi trường giả lập màn hình)

- Test mới: 17 (vá lỗi) + 10 (màn hình mới, chạy GUI thật) — đều PASS
- Hồi quy: 36 (v2.9) + 24 (v3.0) — đều PASS
- Toàn bộ suite của tool: **36 PASS / 4 FAIL / 3 SKIP** so với baseline
  trước khi sửa **34 / 4 / 3** — tăng 2, và 4 fail là 4 fail luồng UI
  môi trường headless CÓ SẴN TỪ TRƯỚC (test_v34/v37/v37b/v39 — trên
  Windows màn hình thật thường không dính).
- App khởi động trọn vẹn, đủ 12 tab con, 2 tab mới hiện đúng nhóm.

## CHECKLIST TEST CHO THỊNH (mỗi mục ~2 phút, theo thứ tự)

1. `CAI-DAT-LAN-DAU.bat` -> mở tool -> nhóm **1. DỮ LIỆU** phải thấy 2
   tab mới `Làm giàu dữ liệu (3.1)` và `Xem dữ liệu (3.1)`.
2. **Xem dữ liệu**: mở master -> soi cột `Tổn hao không tải Po (W,
   catalogue)` -> con số X/245 hiện ra có hợp lý không, bấm *Mở trong
   Excel* có bật Excel không.
3. **Tab 10 Bước 1 (TCVN)**: chạy trên master GỐC (không phải file
   _TCVN cũ) -> log phải có dòng `Bỏ qua — PHỤ KIỆN`, và mở file ra:
   các dòng "Vỏ mạ kẽm..." KHÔNG còn số ở cột dòng điện.
4. **Làm giàu dữ liệu**: thêm 2-3 ảnh biển máy + 1 PDF catalogue, giới
   hạn 15 lượt -> Moi -> bảng kết quả hiện, dòng vàng có lý do -> sửa
   thử 1 ô -> Lưu -> mở file bằng Excel xem ô có đổi thật.
5. **Ghép vào MASTER** từ chính màn hình đó -> phải ra file `_VISION`
   + thông báo, KHÔNG văng lỗi.
6. **Tab 10 Bước 2/3/5** (đường cũ) -> bấm từng bước, không được văng
   `AttributeError`/`ValueError` như hôm 06/08.
7. Nhìn Nhật ký lúc đọc PDF: nếu vẫn có lỗi thì giờ mỗi lỗi phải kèm
   đường dẫn file raw trong `.vision-cache/raw-loi/` — zip thư mục đó
   gửi Fable là mình chỉnh prompt tiếp được ngay.

Mục nào fail: chụp màn hình + đoạn Nhật ký, gửi kèm số thứ tự mục.

## Chưa làm trong batch này (đúng kế hoạch, không phải quên)

- V5 (gom Cấu hình), V6 (Outline Studio nền -> Enhance 2.0), V7 phần
  còn lại (Việt hoá tên profile, ẩn record_id, ẩn Mock/Test, chuẩn hoá
  tên có Hoàn tác) — làm ở batch sau, sau khi batch này qua tay bạn.
- Batch thử 5-10 bài: chờ bạn ghép data mới xong rồi tự bấm.

---

## CHANGELOG-3.8

### CHANGELOG 3.8

## Gate 1 — Test không được đụng file production
- Sửa file nào, dòng nào: `run_tests.py`, hàm `_hash_file()`, `_tao_sandbox_test()`, `_chay_1_file()`, `main()`, khoảng dòng 20–124.
- Lỗi gì: test suite chạy trực tiếp trong thư mục tool; `tests/test_v35_idempotency.py` có lệnh xóa/ghi `cau-hinh.env` và `phase2-du-lieu.db`, nên có thể phá state production.
- Sửa thế nào: `run_tests.py` copy code + fixture sang `TemporaryDirectory`, không copy hai file production; mọi test chạy trong bản sandbox và runner tự so SHA-256 production trước/sau.
- Kiểm bằng cách nào, kết quả ra sao: chạy chính `run_tests.py` với `test_v35_idempotency.py` trên hai file sentinel; test PASS 1/1, runner báo `[PASS] TEST-SANDBOX`; SHA-256 env trước/sau đều `b76d63c935076035c2306fbb2dd628afda9a4cc0c87ced2aa7d8345d183bee87`, DB trước/sau đều `d277f5ac2d1cd1ee9bab47f4e62b4b309ed515ed53fd5c565ca126989e879e31`.

## Gate 2 — Đổi số liệu thì checksum phải đổi
- Sửa file nào, dòng nào: `nhap_phase2.py`, hàm `data_checksum()`, khoảng dòng 137–156; thêm `tests/test_v38_gate2_checksum.py`, hàm `main()`, khoảng dòng 8–42.
- Lỗi gì: `data_checksum()` chỉ hash field cố định trong `cot_import_keys`, bỏ qua `thong_so_dong`; đổi thông số động A→B vẫn giữ cùng dataset identity.
- Sửa thế nào: canonical hóa payload gồm `fixed` + `dynamic`, sort key bằng JSON để hash cả thông số động nhưng không phụ thuộc thứ tự cột/key.
- Kiểm bằng cách nào, kết quả ra sao: test thật cho `A=sha256:d3fce475...`, `B=sha256:512e4308...` (khác); đảo thứ tự cột và key dynamic đều trả lại `sha256:d3fce475...`; PASS.

## Gate 3 — Worker không được đụng Tkinter
- Sửa file nào, dòng nào: `giao-dien.py`, các hàm `_v3_dang_draft_that()`, `_v3_viec_dang_draft_that_hang_loat()`, `_phase2_chay_hang_loat()`, `_phase2_viec_chay_hang_loat()`, `_v3_anh_upload()`, `_v3_anh_upload_chay()`, `_v3_enhance_batch_bam()`, `_v3_enhance_batch_viec_chay()`, khoảng dòng 1840–3150 và 3890–3990; cập nhật 2 test direct-call truyền snapshot.
- Lỗi gì: worker nền đọc trực tiếp Tk variables (`.get()`) và dataset đang chọn từ widget, gây `RuntimeError: main thread is not in main loop` tùy timing.
- Sửa thế nào: snapshot toàn bộ giá trị Tk/dataset/site ở main thread trước `chay_nen_phase2()`, truyền plain Python value/dict vào worker; không đổi tên hàm/file, không di chuyển hàm.
- Kiểm bằng cách nào, kết quả ra sao: static scan 4 worker chính trả `BAD=[]`; `test_v34_that_ui.py` chạy Xvfb `TONG: 8/8 PASS`; `test_v37_batch_real.py` không còn chuỗi `main thread is not in main loop` (`grep: NONE`) nhưng còn fail do helper chờ cố định kết thúc quá sớm, để Gate 8 xử lý test runner/harness.

## Gate 4 — Uploader ảnh trả media_id, cache khoá theo hash
- Sửa file nào, dòng nào: `autopost.py` hàm `_url_anh_tren_wp()` khoảng dòng 662–686; `dulieu.py` bảng `anh_wp`, hàm `nho_anh_wp()`/`luu_anh_wp()` khoảng dòng 473–482 và 703–724; `tab_anh.py` hàm `_dang()` khoảng dòng 350–365; thêm `tests/test_v38_gate4_image_cache.py`.
- Lỗi gì: callback production của workflow ảnh trả `None, url`; cache chỉ dựa `path + site`, nên thay bytes cùng tên vẫn lấy media cũ và state có thể báo đã đăng sai.
- Sửa thế nào: thêm SHA-256 content vào cache, `_url_anh_tren_wp(..., tra_media_id=True)` trả `(media_id, url)` cho workflow 3.7; hash khác buộc POST lại, hash giống thì reuse.
- Kiểm bằng cách nào, kết quả ra sao: WordPress giả nhận đúng `POST_CALLS=2`; lần 1 `(101, ...101.webp)`, lần 2 cùng hash reuse ID 101 không POST, thay cùng tên sang bytes BBB trả ID 102 và POST bytes mới; PASS; chưa verify site thật.

## Gate 5 — Ảnh đi được từ thư mục vào bài
- Sửa file nào, dòng nào: `giao-dien.py` phần nạp tab ảnh và hàm `_v3_dang_draft_that()`/`_v3_viec_dang_draft_that_hang_loat()` khoảng dòng 171–178 và 1930–2135; `xu_ly_anh.py` hàm `dang_anh_cua_bai()` khoảng dòng 160–220; thêm `tests/test_v38_gate5_image_e2e.py`.
- Lỗi gì: workspace ảnh chỉ upload Media riêng lẻ, production posting không gọi `dang_anh_cua_bai()`/`khoi_anh_bai()`/`gan_anh_vao_san_pham()`, nên bài thật không nhận ảnh.
- Sửa thế nào: snapshot image root ở main thread, production worker tìm workspace theo record/SKU, upload ảnh, chèn `<img>` vào HTML rồi gắn media IDs vào Woo/Post sau khi Save Draft thành công; lần sau reuse media_id khi hash không đổi.
- Kiểm bằng cách nào, kết quả ra sao: mock WordPress E2E nhận `MEDIA_POSTS=1`, `MEDIA_BYTES=608`, `PRODUCT_POSTS=2`, `HAS_IMG=True`, attach payload `{'images':[{'id':501}]}`, meta `wp_media_id=501`, `da_dang`; lượt update thứ hai không upload media lại; PASS; chưa verify site thật.

## Gate 6 — Validation chặn thật, không chỉ ghi log
- Sửa file nào, dòng nào: `giao-dien.py`, hàm `_v3_viec_dang_draft_that_hang_loat()`, khoảng dòng 1990–2010; thêm `tests/test_v38_gate6_validation_block.py`.
- Lỗi gì: importer có gắn `nghi_van_dien_ap=True` nhưng production posting không đọc flag này, nên record nghi vấn vẫn gọi AI rồi WordPress.
- Sửa thế nào: kiểm `nghi_van_dien_ap is True` ngay đầu mỗi record, ghi trạng thái lỗi với lý do `BLOCKED` rồi `continue` trước mọi lệnh gọi AI/WordPress.
- Kiểm bằng cách nào, kết quả ra sao: test production worker với record có flag True cho `AI_CALLS=0`, `WP_CALLS=0`, DB `STATE=loi`, reason bắt đầu `BLOCKED: nghi_van_dien_ap=True`; PASS.

## Gate 7 — Woo category bằng ID, schema lên frontend
- Sửa file nào, dòng nào: `ai_wp_adapter.py`, hàm `dang_woo_that()`, khoảng dòng 511–620; `render_phase2.py`, hàm `dung_schema()` và `dung_bai_html()`, khoảng dòng 287–310 và 2050–2065; thêm `tests/test_v38_gate7_woo_schema.py`.
- Lỗi gì: Woo product payload gắn category bằng `name`; Product schema dùng `ma_goc` thay vì `publish_sku`, description lấy từ raw row nên có thể rỗng; `_snl_schema_jsonld` chỉ được ghi vào Woo meta nhưng source package không có consumer/hook đưa meta đó ra frontend.
- Sửa thế nào: tra category hiện có bằng Woo REST rồi chỉ gửi `{'id': ...}`; schema dùng `publish_sku` và meta description cuối; giữ schema ở meta hiện hữu, không tự bịa thêm hook/plugin khi chưa có bằng chứng site đang dùng cơ chế nào.
- Kiểm bằng cách nào, kết quả ra sao: mock Woo cho `CATEGORY_PAYLOAD=[{"id":123}]`, `BUILT_SCHEMA_SKU=SKU-B2`, `BUILT_SCHEMA_DESCRIPTION=Mô tả cuối.`, `PASS_GATE7_LOCAL=1`; grep production cho `PRODUCTION_CONSUMER_FILES=0`, nên **KHÔNG LÀM ĐƯỢC toàn Gate 7**: chưa thể chứng minh View Source có `"@type":"Product"` nếu không có hook/plugin frontend hoặc quyền verify site thật.

## Gate 8 — Bộ test chạy sạch, không timeout, không lỗi Tk
- Sửa file nào, dòng nào: `tests/test_v31_man_hinh.py` khoảng dòng 49–90; `tests/test_v34_that_ui.py` khoảng dòng 30–45; `tests/test_v37_1_patch.py`, `tests/test_v37_batch_real.py`, `tests/test_v39_article_jobs.py` ở helper chờ worker và mock AI; không sửa production ngoài các Gate 1–7.
- Lỗi gì: test cũ có 3 điểm làm harness sai với production hiện tại: ép `tksheet` mềm thành bắt buộc, chọn record nay bị Gate 6 block, và mock `goi_ai_that()` dù production đã gọi `goi_ai_co_du_phong()`; riêng `test_v37_batch_real.py` vẫn treo lâu sau T1 khi chạy tiếp batch.
- Sửa thế nào: test `tksheet` kiểm đúng fallback khi dependency vắng; chọn record không bị validation block cho test batch thường; mock đúng adapter production và chờ trạng thái worker thay vì fixed sleep; không giảm số record regression gốc.
- Kiểm bằng cách nào, kết quả ra sao: compile toàn project PASS; isolated `test_v31_man_hinh.py=7/7 PASS`, `test_v34_that_ui.py=8/8 PASS`, `test_v37_1_patch.py=7/7 PASS`, `test_v39_article_jobs.py=23/23 PASS`; nhưng full `run_tests.py` không kết thúc trong 300s và isolated `test_v37_batch_real.py` vẫn vượt 100s sau `T1/T1b PASS`, nên **KHÔNG LÀM ĐƯỢC Gate 8 / FAIL** vì chưa có bằng chứng suite sạch 0 timeout.

---

## CHANGELOG-3.9

### CHANGELOG SONEALEO ULTRA 3.9

## A1 — Layout tab Ảnh bài viết
- File/hàm/dòng: tab_anh.py → TabAnh._dung() → khoảng dòng 82-109; thêm tests/test_v39_a1_layout.py.
- Lỗi: 5 ô ảnh cao hơn viewport làm nút “Đăng ảnh lên bài” rơi khỏi màn hình và nhãn vai trò bị cắt ở màn hình thấp.
- Sửa: đặt 5 ô trong canvas cuộn dọc riêng, cố định panel phải 450px; ghim cụm nút ngoài vùng cuộn, giữ nguyên nhãn đầy đủ.
- Kiểm: Xvfb 1366x768 button=[1019,678,127,31] inside=true; 1920x1080 button=[1573,990,127,31] inside=true; cả hai trả đủ 5 nhãn không có “...”; screenshot /mnt/data/a1-1366x768.png và /mnt/data/a1-1920x1080.png.

## A2 — Gemini dò model quá lâu
- File/hàm/dòng: autopost.py → do_model() → khoảng dòng 953; thêm cache _MODEL_404_TRONG_PHIEN và tests/test_v39_a2_model_probe.py.
- Lỗi: Ver 3.8 quét toàn bộ model, ngủ 1.2s mỗi model và timeout 60s/probe dù config đã có model chạy được; model 404 bị thử lại ở lần dò sau.
- Sửa: ưu tiên MODEL_GEMINI đã lưu, dừng ngay khi HTTP 200, lưu model thành công bằng C.luu_gemini(), cache 404 trong phiên, timeout từng probe còn 12s; 429 rate-limit ngắn không được ghi như một success 200.
- Kiểm: mock cùng 10 model: Ver3.8=12.0021s/10 POST/timeout=60; Ver3.9=0.0002s/1 POST/timeout=12. Regression PASS: model nhớ chỉ 1 probe và model 404 có calls lần1=[5.0,3.6], lần2=[3.6]. Chưa gọi Gemini thật trong task đêm.

## A3 — Gate 8 suite timeout (harness batch)
- File/hàm/dòng: tests/test_v37_batch_real.py → harness trước T1; run_tests.py → _chay_nhom_test()/main(); cập nhật các regression cũ test_v364_dot_lon.py, test_v38_gate5_image_e2e.py, test_v496_patch.py, test_v51_patch.py, test_ver3_ui.py theo contract 3.9; KHÔNG giảm record 5 + 17 + 17 + 6.
- Lỗi: harness batch giữ sleep production 5s làm test vượt 100s; runner khởi động/copy sandbox quá nhiều lần; một số regression cũ kiểm contract đã bị thay hợp lệ bởi C/E nên fail giả.
- Sửa: harness batch đặt nghỉ=0 nhưng giữ nguyên số record; runner khởi động Xvfb một lần, chia suite thành 4 sandbox độc lập chạy song song và tuần tự bên trong; chỉ cập nhật assertion stale, không giảm coverage/record.
- Kiểm: test_v37_batch_real.py = 8/8 PASS, 3.58s; full run_tests.py chạy đủ 61 file trong 33.6s: 58 PASS / 0 FAIL / 3 SKIP legacy thiếu fixture / 0 TIMEOUT; TEST-SANDBOX checksum env+DB production không đổi.

## A4 — run_tests.py phân loại PASS giả
- File/hàm/dòng: run_tests.py → main() → khoảng dòng 106; thêm tests/test_v39_a4_runner_classification.py.
- Lỗi: biểu thức cũ có nhánh `or 'PASS' in out`, nên chỉ cần chữ PASS xuất hiện ở bất kỳ đâu là `co_tong_ket_pass=True`, kể cả file thực tế chỉ skip fixture.
- Sửa: dùng regex chỉ công nhận marker PASS ở đầu dòng ([PASS], PASS:/PASS_...) hoặc dòng tổng kết TỔNG/TONG/TOTAL ... PASS; exit code vẫn là điều kiện chính.
- Kiểm: regression PASS: câu `Expected result should PASS...` không match; `[PASS]`, `PASS:` và `TONG ... PASS` đều match đúng.


## B1 — Bỏ dấu ≤ khỏi Uk, xác nhận Io
- File/hàm/dòng: render_phase2.py → _RE_TON_HAO_QC/_dong_bang_thong_so_dong() → dòng 156-212; tests/test_v361_no_vat.py dòng 14-25; tests/test_v39_b1_b2_labels.py dòng 12-18.
- Lỗi: regression cũ còn kỳ vọng Uk có dấu ≤; renderer production hiện chỉ được phép áp ≤ cho Po/Pk, không cho Uk/Io.
- Sửa: giữ regex production chỉ Po/Pk, cập nhật test regression cũ theo yêu cầu kỹ thuật mới; không đổi giá trị MASTER.
- Kiểm: đọc record thật TBD1P15 từ MASTER Ver8: Po=52, Pk=213, Uk=2, Io=1; test PASS: Po/Pk có ≤, Uk=2 và Io=1 không có ≤.

## B2 — Nhãn catalogue hãng cho SKU KP
- File/hàm/dòng: render_phase2.py → _nhan_theo_nguon()/_dong_bang_thong_so_dong() → dòng 166-212; tests/test_v39_b1_b2_labels.py dòng 20-34.
- Lỗi: cột động có tên “cực đại theo tiêu chuẩn EVN” có thể dán nhãn quy chuẩn lên số lấy từ catalogue hãng.
- Sửa: khi field nguồn thật `nguon_loai_so_lieu == catalogue_hang`, bỏ nhãn EVN và đổi đơn vị W thành “(W, catalogue hãng)”; nguồn khác giữ nguyên.
- Kiểm: đếm trực tiếp MASTER Ver8 = 9 dòng `catalogue_hang`, trong đó 8 dòng thương hiệu có KP; test PASS toàn bộ 9 dòng không còn nhãn EVN và có nhãn catalogue hãng ở Po/Pk.

## B3 — Sửa cờ nguồn 20 dòng A2608 trong MASTER Ver8
- File/hàm/dòng: 8MASTER_ENRICHED_Ver8.xlsx → sheet 03_May_Bien_Ap_Do_Luong → AW100:AW119, AY100:AY119; sheet 00_Nhat_Ky_Sua_Loi → dòng 235-262.
- Lỗi: 20 SKU A2608 ở Ver7 mang cờ `quy_chuan_evn` dù Po/Pk/Uk được điền theo TCCS 10:2021/EVN, chưa đối chiếu QĐ 2608/QĐ-EVN SPC.
- Sửa: 19 dòng đổi AW thành `suy_tu_tieu_chuan_khac`; toàn bộ 20 dòng AY ghi đúng “điền theo TCCS 10:2021/EVN, chưa đối chiếu QĐ 2608/QĐ-EVN SPC”; giữ riêng MBT3P180A2608 cho B4.
- Kiểm: đọc lại workbook Ver8: A2608_COUNT=20, SOURCE_TYPES={suy_tu_tieu_chuan_khac:19, noi_suy:1}, AY có đúng 1 giá trị viện dẫn trên cả 20 dòng; nhật ký Ver8 có bảng 20 SKU ở dòng 243-262.

## B4 — MBT3P180A2608 đổi cờ thành nội suy
- File/hàm/dòng: 8MASTER_ENRICHED_Ver8.xlsx → sheet 03_May_Bien_Ap_Do_Luong → AW108; sheet 00_Nhat_Ky_Sua_Loi → dòng 239, 251.
- Lỗi: MBT3P180A2608 có ghi chú nguồn nói Po/Pk là nội suy nhưng cờ nguồn Ver7 vẫn là `quy_chuan_evn`.
- Sửa: AW108 = `noi_suy`; giữ nguyên cảnh báo nội suy đã có và bổ sung dấu vết Io của B5.
- Kiểm: đọc lại row 108: SKU=MBT3P180A2608, source_type=`noi_suy`, viện dẫn đúng TCCS 10:2021/EVN/chưa đối chiếu QĐ 2608.

## B5 — Gắn dấu vết cho 20 dòng mất Io, không khôi phục số
- File/hàm/dòng: 8MASTER_ENRICHED_Ver8.xlsx → sheet 03_May_Bien_Ap_Do_Luong → AN100:AN119 giữ trống, AZ100:AZ119 thêm ghi chú; sheet 00_Nhat_Ky_Sua_Loi → dòng 240, 243-262.
- Lỗi: 20 SKU A2608 bị mất Io sau khi xoá gói Po/Pk sai nhưng trạng thái trống không phân biệt được với trường hợp nguồn vốn không có.
- Sửa: KHÔNG điền lại Io; AZ ghi “Io đã từng có, đã xoá cùng gói Po/Pk sai; không khôi phục vì chưa có nguồn đã đối chiếu.”, nối sau ghi chú cũ nếu đã có.
- Kiểm: đọc lại workbook Ver8: 20/20 A2608 có Io trống (IO_NONEMPTY=0) và 20/20 có chuỗi dấu vết; nhật ký Ver8 ghi rõ B5 và danh sách 20 SKU.

## C1 — Tiêu đề MBA thêm số pha + cấp điện áp
- File/hàm/dòng: render_phase2.py → dung_tieu_de() → khoảng dòng 920-990; tests/test_v39_c_seo_update.py.
- Lỗi: brief báo title từng trùng do thiếu số pha/cấp điện áp; logic này đã có trong baseline 3.8 nhưng chưa đối chiếu lại với MASTER Ver8.
- Sửa: giữ nguyên nhánh code đã đúng, không vá lại; đưa vào regression C để khóa số pha + cấp điện áp và kiểm uniqueness trên dữ liệu thật.
- Kiểm: đọc MASTER Ver8 qua importer thật: 141 SKU outline_may_bien_ap, duplicate title groups=0, duplicate rows=0; vì vậy số 35/75 hay 31/72 không còn đúng với baseline 3.8 hiện tại.

## C2 — MOF thêm tỷ số biến dòng vào title, chuẩn hóa xuống dòng
- File/hàm/dòng: render_phase2.py → dung_tieu_de() + dung_bai_html() → khoảng dòng 930-955 và 2190; tests/test_v39_c_seo_update.py.
- Lỗi: production non-MBA ưu tiên meta_title AI; title MOF có thể mất phần tỷ số phân biệt và tên hàng nhiều dòng từng bị cắt.
- Sửa: riêng MOF dựng title bằng code từ Cấp điện áp + Thương hiệu/Xuất xứ + “Tỷ số biến dòng” đọc trong Tên hàng, gộp CR/LF; production path dùng dung_tieu_de() cho MOF thay vì meta_title AI.
- Kiểm: MASTER Ver8 thực tế có 9 MOF, không phải 7; test PASS 9/9 title có tỷ số /5A, không xuống dòng và 9/9 unique.

## C3 — Phân biệt A107/A2608 và ghi chú nguồn A2608 dưới bảng
- File/hàm/dòng: profiles.py → cot_import may_bien_ap_do_luong dòng 261-266; render_phase2.py → bang_thong_so()/dung_tieu_de() khoảng dòng 215-239, 960-990; tests/test_v39_c_seo_update.py.
- Lỗi: title cần giữ hậu tố QĐ 107/QĐ 2608; 20 A2608 cần nói rõ số liệu đang lấy TCCS 10:2021/EVN chứ chưa đối chiếu QĐ 2608.
- Sửa: giữ nhãn QĐ đã có ở title; map cột thật `Nguồn - Tiêu chuẩn viện dẫn` thành `nguon_tieu_chuan_vien_dan` và in đúng citation từ record ngay dưới bảng cho A2608.
- Kiểm: 141 MBA title duplicate groups=0; 20/20 A2608 render có “TCCS 10:2021/EVN” + “chưa đối chiếu QĐ 2608/QĐ-EVN SPC”.

## C4 — Slug MBA theo công thức mới, bỏ SKU/Cu-Cu/chuan
- File/hàm/dòng: render_phase2.py → _thuong_hieu_gon(), _slug_mba_39(), dung_slug() → dòng 399-482; tests/test_v39_c_seo_update.py.
- Lỗi: slug cũ phụ thuộc title/có thể mang mã hàng; công thức Fable nếu áp đúng từng chữ lại tạo 25 nhóm/50 dòng collision trên MASTER Ver8 do A107/A2608 và THIBIDI 1P khác cấp áp.
- Sửa: base slug = may-bien-ap-[dau|kho]-[hang]-[kVA]-[so-pha]-[loi], KP khô bỏ pha/Cu-Cu; không SKU/chuan; thêm tối thiểu QĐ và, riêng THIBIDI 1P Amorphous, cấp áp để giữ uniqueness mà không đưa SKU trở lại.
- Kiểm: 141/141 slug MBA unique, duplicate groups=0; 0 slug chứa SKU/Cu-Cu/chuan; mẫu đúng: KPK2500CU→may-bien-ap-kho-kp-2500kva, TBD3P250→may-bien-ap-dau-thibidi-250kva-3-pha-silic.

## C5 — Sinh 3 meta Rank Math bằng code, không AI
- File/hàm/dòng: render_phase2.py → _gia_tri_meta_an_toan(), dung_rank_math() → khoảng dòng 534-650; tests/test_v39_c_seo_update.py.
- Lỗi: meta 3.8 lấy title làm focus và description có câu báo giá/tư vấn; bộ định danh cơ bản còn trùng 25 nhóm/50 dòng; số catalogue có thể không qua được Hard Block nếu representation thiếu đơn vị.
- Sửa: MBA sinh focus/title/description từ record thật; dùng QĐ/cấp áp thật chỉ khi cần uniqueness; description thêm từng Po/Pk/Uk/Io/hiệu suất mà Hard Block hiện có xác minh được, không sửa/nới Hard Block, không “đang cập nhật”, không lời hứa giá.
- Kiểm: 141/141 MBA sinh đủ 3 meta; 0 Hard Block violation; focus duplicate groups=0, SEO title duplicate groups=0; mọi title<=60 và description<=160 ký tự.

## C6 — Một lượt metadata-only update, không render content/AI
- File/hàm/dòng: render_phase2.py → dung_goi_cap_nhat_seo(); ai_wp_adapter.py → cap_nhat_seo_woo_that() dòng 732-767; giao-dien.py → nút/handler/worker khoảng dòng 1791-1940; tests/test_v39_c_seo_update.py.
- Lỗi: muốn áp C1-C5 lên bài cũ mà dùng luồng “cập nhật lại bài đã đăng” sẽ gọi Gemini và ghi đè description/content, trái yêu cầu.
- Sửa: thêm nút “Cập nhật SEO (không AI)”; chỉ target MBA+MOF đã có wp_id; Woo payload chỉ có name/slug/meta_data, DB local chỉ cập nhật title/slug; worker không gọi goi_ai/dung_bai_html.
- Kiểm: MASTER Ver8 target=150 SKU (141 MBA + 9 MOF); mock Woo POST=1, payload keys đúng {name,slug,meta_data}, không description/short_description/sku; AI calls=0; CHƯA chạy update thật/site thật.

## D1 — Biểu đồ MBA đọc dữ liệu MASTER đã import thay bảng cứng THIBIDI
- File/hàm/dòng: khoi_anh.py → _nhom_bieu_do_master(), bieu_do_ton_hao(), bieu_do_loi() → khoảng dòng 84-260; giao_dien_2_5.py → _bieu_do()/dung_bai_2_5() → khoảng dòng 384-525; render_phase2.py → _dung_bai_2_5_wrapper() → khoảng dòng 2179.
- Lỗi: hai SVG production vẫn tra bảng cứng tra_cuu_thibidi nên MBT trả rỗng, dù khối kiến thức biến thiên đã biết đọc Po từ SKU anh em trong dataset.
- Sửa: truyền danh sách record cùng dataset từ cache _PK_kho_row() vào bố cục; biểu đồ ưu tiên Po thật trong record MASTER đã import, ghép cùng hãng/pha/dầu-khô/lõi/cấp áp/biến thể tiêu chuẩn; bảng THIBIDI chỉ còn fallback tương thích, không mở XLSX mỗi bài.
- Kiểm: đọc MASTER Ver8 qua importer thật: MBT outline_may_bien_ap=62 SKU; baseline 3.8 dựng 0+0 SVG, 3.9 dựng 61 SVG tổn hao + 56 SVG so lõi = 117 SVG inline; 56 SKU có đủ cả 2; render mẫu qua dung_bai_2_5 có 2 <svg>. Số ~86/~172 trong brief không khớp nguồn MASTER Ver8 hiện tại.

## D2 — Bảng so sánh công suất lấy cân hai phía
- File/hàm/dòng: db_phase2.py → tim_san_pham_cung_dong() → khoảng dòng 613-650; tests/test_v39_d_master_charts.py.
- Lỗi: brief mô tả nhánh cũ sort tăng rồi [:gioi_han], khiến SKU 800kVA chỉ thấy công suất thấp; baseline 3.8 hiện đã có logic lấy hai phía nhưng chưa có regression độc lập khóa hành vi.
- Sửa: giữ nguyên logic production đã đúng, không vá lại; thêm regression DB thật trong tempfile để khóa 3 mức dưới + 3 mức trên và chống quay lại [:6].
- Kiểm: dataset test 13 mức công suất, gọi record 800kVA trả chính xác [560, 630, 750, 1000, 1250, 1600] = 3 dưới + 3 trên; test_v39_d_master_charts.py PASS.

## E1 — Nén ảnh thực sự đạt <150KB
- File/hàm/dòng: xu_ly_anh.py → sang_webp() → khoảng dòng 29-79.
- Lỗi: điều kiện cũ `len<=target OR quality<=min` trả thành công ngay khi quality chạm đáy, nên ảnh khó nén có thể còn hàng MB nhưng state vẫn coi là đạt.
- Sửa: giới hạn cạnh dài tối đa 1200px; hạ quality tới min, nếu vẫn >150KB thì giảm tiếp cả hai chiều 15% và thử lại; tới cạnh dài 320px mà vẫn không đạt thì trả lỗi rõ, không báo thành công giả.
- Kiểm: ảnh nhiễu thật 1200x4000 tạo trong test → WebP 360x1200, 123.4KB <=150KB; PASS.

## E2 — Sửa orientation ảnh điện thoại theo EXIF
- File/hàm/dòng: xu_ly_anh.py → sang_webp() → khoảng dòng 38-45.
- Lỗi: code cũ convert RGB trước khi xử lý EXIF orientation, ảnh điện thoại có thể bị xoay ngang/ngược.
- Sửa: gọi `ImageOps.exif_transpose()` ngay sau mở file, rồi mới convert RGB/resize/nén.
- Kiểm: ảnh test lưu kích thước vật lý 40x20 với EXIF Orientation=6; output sau xử lý là 20x40 đúng chiều hiển thị; PASS.

## E3 — Escape thuộc tính HTML ảnh
- File/hàm/dòng: xu_ly_anh.py → the_img(), khoi_anh_bai() → khoảng dòng 122-151.
- Lỗi: url/alt/caption được chèn thẳng vào HTML, ký tự `"`, `&`, `<` có thể làm bẩn attribute/markup.
- Sửa: `html.escape(..., quote=True)` cho URL/alt và `html.escape()` cho caption; width/height ép int.
- Kiểm: input URL có `&"`, alt có `"&<`, caption có `&<x>` → output chứa `&amp;`, `&quot;`, `&lt;`, không còn `<x>` thô; PASS.

## E4 — Index workspace một lần, bỏ quét O(N²)
- File/hàm/dòng: workspace_anh.py → _lap_chi_muc_workspace(), tim_workspace(), tao_workspace() → khoảng dòng 114-195.
- Lỗi: mỗi lần tìm 1 SKU lại quét toàn bộ folder sheet và đọc mọi meta.json; N SKU có thể thành gần N×N lần đọc filesystem.
- Sửa: cache index theo (gốc, sheet): SKU→Path; lần đầu scan một lượt, các lookup sau O(1); workspace mới tạo cập nhật cache, path cache mất thì rebuild một lần.
- Kiểm: workspace test 300 SKU: lần dựng index đọc meta=300; 100 lookup tiếp theo đọc meta thêm=0; PASS.

## E5 — Ẩn tab ảnh legacy, giữ một nguồn sự thật trên UI
- File/hàm/dòng: giao-dien.py → PhanMem.__init__() → khoảng dòng 153; hàm _v3_tab_9_anh() giữ nguyên không xoá.
- Lỗi: UI đồng thời nạp tab “9. Ảnh sản phẩm” legacy và “Ảnh bài viết (3.7)”, tạo hai workflow/uploader cạnh nhau.
- Sửa: chỉ bỏ lời gọi `_v3_tab_9_anh()` khỏi khởi tạo UI; toàn bộ code legacy vẫn nằm nguyên để rollback, tab workspace 3.7 vẫn nạp bình thường.
- Kiểm: Xvfb instantiate app: HAS_LEGACY=False, HAS_37=True, IMAGE_TABS=['Ảnh bài viết (3.7)']; PASS.

## E6 — Force Stop ngắt được khoảng nghỉ giữa bài
- File/hàm/dòng: giao-dien.py → _v3_viec_dang_draft_that_hang_loat(), _jobs_viec_dang_hang_loat() → khoảng dòng 2073 và 3627.
- Lỗi: `time.sleep(nghi_giua_bai)` không nghe cờ dừng; đặt nghỉ 300s thì bấm Force Stop vẫn có thể chờ gần hết 300s.
- Sửa: thay sleep bằng `v3_dung_lai.wait()` và `jobs_dung_lai.wait()`; nếu event bật trong lúc nghỉ thì break ngay trước record/job kế.
- Kiểm: gọi đúng production worker với khoảng nghỉ 5s, set Force Stop sau 0.20s → ELAPSED=0.200s, record thứ hai chưa chạy; PASS.

## E7 — Chỉ dataset hiện hành giữ active=1
- File/hàm/dòng: db_phase2.py → xac_nhan_dataset() → khoảng dòng 218-239; semantics đối chiếu dataset_gan_nhat()/liet_ke_dataset() đều lọc `active=1`.
- Lỗi: khi xác nhận version dataset mới, code chỉ INSERT nên version cũ vẫn active; UI/list và “dataset gần nhất” có thể coi nhiều version lịch sử đều đang hiện hành.
- Sửa: chỉ ở nhánh `confirm_new_dataset=True`, trước INSERT version mới chạy `UPDATE dataset SET active=0 WHERE profile_id=? AND active=1`; không xoá dataset/sản phẩm/bài lịch sử.
- Kiểm: tạo 3 version trong DB tempfile → rows=[(ds_p_001,0),(ds_p_002,0),(ds_p_003,1)], liet_ke_dataset() chỉ trả ds_p_003, lay_dataset(ds_p_001) vẫn đọc được; PASS.

## E8 — Đồng bộ version hiện hành/user-facing thành 3.9
- File/hàm/dòng: README.md dòng 1,15; docs/SPEC.md dòng 1,60; giao-dien.py title/status/header dòng ~83,183,283; tab_anh.py label dòng ~396; 4 BAT title dòng 3.
- Lỗi: version hiện hành hiển thị lẫn 3.7/3.6.4/5.1; operator không biết artifact đang chạy là bản nào.
- Sửa: chỉ đổi chuỗi CURRENT/user-facing thành 3.9; KHÔNG sửa comment lịch sử, changelog/archive hay các mốc Ver 4.9.9–5.3 dùng để mô tả lịch sử patch; TEST-REPORT/KNOWN-ISSUES cũ giữ nguyên vì là snapshot lịch sử.
- Kiểm: grep current strings: README=3.9, SPEC current/updated=3.9, 3 vị trí GUI=3.9, tab ảnh='Ảnh bài viết (3.9)', 4 BAT title='LOTECH AUTOPOST VER 3.9'; py_compile GUI/tab PASS.

## E9 — Không cho worker giành process-global sys.stdout
- File/hàm/dòng: giao-dien.py → ChuyenHuongIn, _bat_stdout_worker(), _tat_stdout_worker(), chay_nen_phase2(), chay_nen() → khoảng dòng 65-125, 3840, 4510.
- Lỗi: mỗi worker lưu/ghi/restore `sys.stdout` toàn process; hai thread chạy chồng có thể restore object stale và log đi nhầm queue.
- Sửa: giữ tên ChuyenHuongIn nhưng biến thành router theo thread; mỗi worker đăng ký queue theo thread id, worker khác dùng route riêng, chỉ restore stdout gốc khi route cuối cùng kết thúc.
- Kiểm: chạy đồng thời 2 production chay_nen_phase2 với 2 queue, mỗi thread print 80 dòng: queue A nhận 80 A/0 B, queue B nhận 80 B/0 A, `sys.stdout is original=True`; PASS.

## E10 — UI callback lỗi phải để lại traceback
- File/hàm/dòng: giao-dien.py → _boc_hang_doi() → khoảng dòng 4280.
- Lỗi: callback UI ném exception bị `except Exception: pass` nuốt sạch, không log/trace nên lỗi thread/UI thành lỗi ma.
- Sửa: giữ lifecycle cũ, chỉ thay `pass` bằng `self.log('LỖI UI callback:\n' + traceback.format_exc(), 'loi')`.
- Kiểm: Xvfb enqueue callback cố ý `1/0` → ô Nhật ký có `LỖI UI callback:` và `ZeroDivisionError`; PASS.

---

## CHANGELOG-4.0

### CHANGELOG SONEALEO ULTRA 4.0

## 1.1 — Định nghĩa họ sản phẩm từ record
- File+dòng: workspace_anh.py → ho_san_pham() khoảng dòng 87-141; tests/test_v40_1_family_images.py.
- Vấn đề: ảnh phải dùng chung theo họ nhưng Ver 3.9 chỉ có workspace từng SKU; không có identity hãng + dầu/khô + số pha + lõi.
- Làm thế nào: thêm family key chỉ từ field thật của record; thiếu pha/lõi ghi `khong-ro`, không đoán; chỉ nhận outline_may_bien_ap.
- Kiểm ra sao: importer production đọc MASTER Ver8 = 141 SKU máy biến áp thật, đếm được 11 họ; breakdown thật được in trong test_v40_1_family_images.py và test PASS.

## 1.2 — Thư mục _HO và 5 ô ảnh theo họ
- File+dòng: workspace_anh.py → thu_muc_ho()/tao_workspace_ho()/tim_workspace_ho() khoảng dòng 143-176.
- Vấn đề: chưa có nơi lưu ảnh mặc định dùng chung, nên mỗi SKU buộc phải có thư mục ảnh riêng.
- Làm thế nào: tạo `<gốc>/<sheet>/_HO/<family-key>/meta.json`, giữ cùng profile và cùng 5 role ảnh hiện có; không đụng thư mục SKU.
- Kiểm ra sao: test tạo family workspace xác nhận `tmh.parent.name == '_HO'`, gán hero + cận cảnh và quét lại đủ role; PASS.

## 1.3 — Fallback ảnh họ, ảnh riêng thắng
- File+dòng: workspace_anh.py → anh_hieu_luc()/trang_thai_hieu_luc(); xu_ly_anh.py → dang_anh_hieu_luc() khoảng dòng 229; giao-dien.py khoảng dòng 2214-2240.
- Vấn đề: production chỉ tìm workspace SKU; SKU không có ảnh riêng thì bài không có ảnh dù cùng họ có thể dùng chung hợp lệ.
- Làm thế nào: merge theo từng role: riêng > họ > trống; family media_id được tái dùng, HTML alt được tạo lại theo SKU hiện tại; production posting gọi flow hiệu lực mới, không POST site trong test.
- Kiểm ra sao: mock uploader: SKU đầu upload 2 ảnh họ, SKU thứ hai cùng họ giữ tổng 2 call, SKU có hero riêng tăng lên 3 call; hero riêng thắng còn cận cảnh lấy từ họ; PASS.

## 1.4 — Màn “Gán ảnh cho họ”
- File+dòng: tab_anh.py → nút khoảng dòng 57; CuaSoAnhHo khoảng dòng 409-570; tests/test_v40_1_family_ui.py.
- Vấn đề: không có UI để người dùng gán 5 ảnh mặc định cho một họ mà phải thao tác từng bài.
- Làm thế nào: thêm cửa sổ danh sách họ + số SKU, 5 ô ảnh cùng role hiện tại, chọn nhiều file liên tiếp, gỡ ảnh và mở thư mục họ; không gọi AI/WordPress.
- Kiểm ra sao: Xvfb family UI: có nút “Gán ảnh cho họ”, 1 họ giả hiện 1 dòng/5 slot; regression layout chạy thật 1366x768 và 1920x1080 đều `inside=true`, đủ 5 nhãn không `...`; PASS.

## 1.5 — Cột Nguồn riêng / họ / trống
- File+dòng: tab_anh.py → Treeview và nap/_ap_loc/_ve_o khoảng dòng 73-260; workspace_anh.py → trang_thai_hieu_luc().
- Vấn đề: danh sách bài không cho biết ảnh đang đến từ workspace riêng, fallback họ hay hoàn toàn trống.
- Làm thế nào: thêm cột `Nguồn`; nếu có ít nhất một ảnh riêng ghi “riêng”, nếu không có riêng nhưng có họ ghi “họ”, không có cả hai ghi “trống”; ô family trong panel gắn nhãn [HỌ].
- Kiểm ra sao: Xvfb xác nhận cột `nguon` có heading “Nguồn”; test logic xác nhận row cùng họ=`ho`, row khác họ=`trong`, row có override=`rieng`; PASS.

## 2.1 — Lọc rác kho ảnh tầng 1, không AI
- File+dòng: xu_ly_anh.py → laplacian_variance()/loc_kho_anh() khoảng dòng 31-190; tests/test_v40_2_image_filter.py.
- Vấn đề: kho ảnh vài GB có file trùng byte, ảnh nhỏ, ảnh mờ và file rác; chưa có bước lọc cơ học trước khi người dùng chọn ảnh.
- Làm thế nào: SHA-256 loại byte-trùng; cạnh ngắn <800px loại; đo Laplacian variance trên grayscale tối đa 320px, ngưỡng mờ cố định 80.0; file không đọc được bằng Pillow loại riêng; không gọi AI.
- Kiểm ra sao: test dựng 5 file: sharp/duplicate/small/blur/txt; sharp Laplacian=22396.025, blur=0.224, threshold=80.0; phân loại đúng 1 file cho mỗi lý do và PASS.

## 2.2 — Không xoá kho gốc, chỉ hardlink/copy sang _DA_LOC
- File+dòng: xu_ly_anh.py → loc_kho_anh() nhánh output/hardlink-copy khoảng dòng 120-185.
- Vấn đề: công cụ lọc không được phá kho ảnh công ty hoặc di chuyển file gốc.
- Làm thế nào: tạo `<kho>/_DA_LOC/`, ưu tiên os.link; hardlink lỗi thì shutil.copy2; giữ cấu trúc thư mục con; rerun không quét `_DA_LOC`; không có lệnh delete/move.
- Kiểm ra sao: sau test tất cả 4 ảnh nguồn vẫn tồn tại, `_DA_LOC` có đúng 1 ảnh đạt; ORIGINAL_FILES_UNTOUCHED=PASS.

## 2.3 — Báo cáo lọc ảnh
- File+dòng: xu_ly_anh.py → loc_kho_anh() phần `bao` và `bao-cao-loc-anh.json` khoảng dòng 95-190.
- Vấn đề: lọc xong cần biết vào bao nhiêu, ra bao nhiêu và vì sao bị loại, không được chỉ hiện “xong”.
- Làm thế nào: ghi JSON gồm tổng file, số ảnh hợp lệ đầu vào, số giữ lại, 4 reason counter, kích thước/Laplacian/hash và trạng thái từng file.
- Kiểm ra sao: test thật trả in=5, image_in=4, out=1, không_phải_ảnh=1, trùng_byte=1, ảnh_nhỏ=1, ảnh_mờ=1; file report tồn tại; PASS.

## 2.4 — Chạy lọc bằng double-click, không gõ lệnh
- File+dòng: loc_kho_anh.py toàn file; LOC-KHO-ANH.bat toàn file.
- Vấn đề: người dùng marketing không muốn mở terminal/gõ command để lọc kho.
- Làm thế nào: BAT ưu tiên `_python\\python.exe`, fallback `python`, mở Tk chọn thư mục rồi gọi loc_kho_anh(); cuối lượt hiện MessageBox số vào/ra + đường dẫn report.
- Kiểm ra sao: loc_kho_anh.py py_compile PASS; lõi được test bằng thư mục giả ở 2.1-2.3. BAT chưa chạy native Windows trong môi trường audit Linux, nhưng không cần site/API và không có lệnh xoá.


## 3.1 — Mô tả 9 danh mục từ số thật MASTER
- File+dòng: category_preview.py → gom_danh_muc()/dung_html_danh_muc() dòng 60-114; tests/test_v40_3_category_preview.py.
- Vấn đề: category Woo chỉ có lưới sản phẩm, chưa có mô tả tổng hợp số SKU/dải công suất/hãng/cấp điện áp từ nguồn dữ liệu thật.
- Làm thế nào: dùng chính nhap_phase2.import_4_profile() + render_phase2.dung_danh_muc(); source sinh 11 tên category, bỏ đúng 2 root `Máy biến áp` và `Thiết bị đo lường điện` còn 9 category con; số liệu lấy từ record, không gọi AI.
- Kiểm ra sao: MASTER Ver8 qua production importer cho 9 category preview; test in thật: Máy biến áp dầu=120 SKU/23 mức kVA, khô=21/21, MOF=9, Công tơ=27, Biến dòng=26, Đồng hồ=11, Phụ kiện=31, Vỏ=24, Giá treo=7; PASS.

## 3.2 — Mục lục kVA và liên kết nội bộ SKU
- File+dòng: category_preview.py → _link_san_pham()/dung_html_danh_muc() dòng 42-45 và 115-125.
- Vấn đề: category chưa gom các SKU theo mức kVA, nên thiếu landing-page structure và lưới internal link theo công suất.
- Làm thế nào: group record theo `cong_suat`; mỗi kVA một `<tr>`, mỗi SKU là link `/san-pham/{dung_slug(record)}/`; category không có kVA hợp lệ thì ghi rõ không dựng bảng giả.
- Kiểm ra sao: preview `Máy biến áp dầu` dựng 23 hàng kVA từ 1kVA đến 3200kVA, `Máy biến áp khô` 21 hàng; test xác nhận có `<table>` và link `/san-pham/`; PASS.

## 3.3 — Hard Block cho số kỹ thuật category, không sửa Hard Block
- File+dòng: category_preview.py → _assert_hard_block() và filter số dòng 48-57, 75-120; render_phase2.py không sửa.
- Vấn đề: category summary sinh bằng code vẫn có thể đưa số ngoài field hợp lệ của outline nếu chỉ đọc raw row (VD vỏ máy có thể mang theo cột điện áp nhưng outline vỏ không expose điện áp).
- Làm thế nào: mọi kVA/cấp điện áp phát ra đều phải được `render_phase2.kiem_tra_bia()` hiện có chấp nhận trên CHÍNH record nguồn; số raw bị Hard Block từ chối thì không đưa lên category; không nới/đụng logic Hard Block.
- Kiểm ra sao: cả 9 HTML generate hoàn tất dưới validation thật; test in `HARD_BLOCK_WIRING=PASS`; category_preview.py không import ai_wp_adapter/requests/Gemini; PASS.

## 3.4 — Xuất 9 HTML preview, không WordPress
- File+dòng: category_preview.py → xuat_9_danh_muc() dòng 131-152; thư mục category-preview-4.0/.
- Vấn đề: cần file xem trước để Thịnh tự duyệt, tuyệt đối không tự đẩy WordPress.
- Làm thế nào: ghi đúng 9 file `.html` local; module không có transport WordPress và không gọi AI.
- Kiểm ra sao: `HTML_FILES=9`, `NO_AI_NO_WP_TRANSPORT=PASS`; file mẫu bên dưới là output thật `06-may-bien-ap-kho.html`.

### Mẫu output thật — 06-may-bien-ap-kho.html
```html
<section class="snl-category-description">
<h2>Máy biến áp khô</h2>
<p>Danh mục hiện có <strong>21 SKU</strong> trong MASTER Ver8. Dải công suất có dữ liệu từ <strong>160kVA</strong> đến <strong>4000kVA</strong>. Hãng có mặt: <strong>KP/Hàn Quốc</strong>. Cấp điện áp có dữ liệu: <strong>22/0.4 kV</strong>.</p>
<p>Dữ liệu dưới đây được dựng trực tiếp từ MASTER; mục nào nguồn không có thì không tự bổ sung hoặc ước lượng.</p>
<h2>Mục lục theo công suất</h2>
<table><thead><tr><th>Công suất</th><th>Sản phẩm</th></tr></thead><tbody>
<tr><td>160kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-160kva/">KPK160CU</a></td></tr>
<tr><td>180kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-180kva/">KPK180CU</a></td></tr>
<tr><td>200kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-200kva/">KPK200CU</a></td></tr>
<tr><td>250kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-250kva/">KPK250CU</a></td></tr>
<tr><td>320kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-320kva/">KPK320CU</a></td></tr>
<tr><td>400kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-400kva/">KPK400CU</a></td></tr>
<tr><td>500kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-500kva/">KPK500CU</a></td></tr>
<tr><td>560kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-560kva/">KPK560CU</a></td></tr>
<tr><td>630kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-630kva/">KPK630CU</a></td></tr>
<tr><td>750kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-750kva/">KPK750CU</a></td></tr>
<tr><td>800kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-800kva/">KPK800CU</a></td></tr>
<tr><td>1000kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-1000kva/">KPK1000CU</a></td></tr>
<tr><td>1250kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-1250kva/">KPK1250CU</a></td></tr>
<tr><td>1500kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-1500kva/">KPK1500CU</a></td></tr>
<tr><td>1600kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-1600kva/">KPK1600CU</a></td></tr>
<tr><td>2000kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-2000kva/">KPK2000CU</a></td></tr>
<tr><td>2500kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-2500kva/">KPK2500CU</a></td></tr>
<tr><td>3000kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-3000kva/">KPK3000CU</a></td></tr>
<tr><td>3200kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-3200kva/">KPK3200CU</a></td></tr>
<tr><td>3500kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-3500kva/">KPK3500CU</a></td></tr>
<tr><td>4000kVA</td><td><a href="/san-pham/may-bien-ap-kho-kp-4000kva/">KPK4000CU</a></td></tr>
</tbody></table>
</section>```

## 4.1 — Snippet PHP đưa `_snl_schema_jsonld` ra frontend
- File+dòng: WPCode-SCHEMA-SONEALEO.php dòng 1-47; ai_wp_adapter.py nguồn meta key dòng 609 chỉ được đọc đối chiếu, không sửa.
- Vấn đề: Python hiện lưu Product schema vào custom meta `_snl_schema_jsonld`, package không có PHP consumer đảm bảo JSON-LD được in trong View Source WordPress.
- Làm thế nào: file snippet riêng hook `wp_head` priority 99, chỉ chạy ở Woo product, đọc đúng meta key, chấp nhận meta dạng array/object hoặc JSON string, encode bằng `wp_json_encode`; kèm đúng 3 dòng hướng dẫn ở đầu file; không nhét snippet vào tool.
- Kiểm ra sao: `php -l` = No syntax errors; WordPress mock stub chạy callback thật cho post_id 321 và in `MOCK_WP_HEAD=PASS`, `META_KEY=_snl_schema_jsonld`, `HAS_PRODUCT_JSONLD=PASS`; CHƯA verify site thật theo lệnh cấm POST/site.

## 4.2 — Ba legacy test không còn SKIP vì thiếu MASTER cũ
- File+dòng: tests/fixtures/MASTER_4_PROFILE_SAN_PHAM.xlsx + 5MASTER_ENRICHED_TRIAL.xlsx; tests/test_v495_patch.py dòng 27-28; test_v498_patch.py dòng 28; test_v499_patch.py dòng 35 và assertion V5-05 khoảng dòng 127-132.
- Vấn đề: 3 test legacy trước đây exit 0/SKIP khi thiếu fixture ở root; sau khi có fixture, test_v499 còn lộ 1 assertion cũ “MOF phải trả nguyên ten_goc” đã bị yêu cầu C2 Ver 3.9 cố ý thay thế.
- Làm thế nào: dựng fixture TỐI THIỂU tự chứa bằng artifact_tool: MASTER cũ 1 cap + 1 tủ + 5 MBA (160/180/250/320/400) + 1 phụ kiện, và trial đúng 90 phụ kiện enrich; đổi riêng đường dẫn test sang tests/fixtures; cập nhật duy nhất assertion MOF legacy sang contract Ver 3.9 hiện hành, không sửa production logic.
- Kiểm ra sao: test_v495_patch=21/21 PASS, test_v498_patch=17/17 PASS, test_v499_patch trước cập nhật stale assertion=31/32 rồi sau=32/32 PASS; không còn nhánh thiếu fixture được kích hoạt.

## Đóng gói — Nhãn release 4.0
- File+dòng: README.md dòng 1,15; PHAN-MEM.bat dòng 3; giao-dien.py dòng 132,232,332; tab_anh.py dòng 586.
- Vấn đề: artifact 4.0 nếu giữ nhãn 3.9 ở UI/BAT/docs sẽ gây nhầm bản đang chạy; comment lịch sử không phải nhãn release hiện hành.
- Làm thế nào: chỉ đổi chuỗi version user-facing/current docs thành `4.0`; giữ nguyên tên file/hàm và không viết lại comment lịch sử.
- Kiểm ra sao: grep đọc đúng 7 vị trí user-facing `4.0`; extract artifact 4.0 chạy compile + 7 regression chính + layout 1366x768/1920x1080 + PHP lint/mock đều PASS; SHA-256 MASTER Ver8 vẫn `b0c0cf00ae08ddc49b512e79544d8e63f0e9430b78e834c39f38ca1486671498`; ZIP 3.9 gốc vẫn `e7079af3ccbb15d1f36702fc4816741e543be63b86feb8c4799d7253478c03e4`.

---

## CHANGELOG-4.1

### CHANGELOG 4.1

## BUG-01 (R23) — Image state theo site
- File+dòng: `xu_ly_anh.py`, `dang_anh_cua_bai()` khoảng dòng 301–380.
- Vấn đề: workspace dùng chung `wp_media_id/media_url` giữa site A và B nên B có thể nhận media của A.
- Sửa thế nào: thêm `delivery_by_site[ma_site]` vào từng ảnh; skip chỉ khi đúng site + đúng hash; giữ top-level field để tương thích API cũ; không chuyển WebP processed vào `_goc` khi upload site thứ hai.
- Kiểm ra sao: cross-site mock thật trên production function: `CROSS_SITE_CALLS_A 1 B 1`, `B_MEDIA_ID 601`, `B_URL https://b.local/601.webp`, rerun B `da_co=True` — PASS R23.

## BUG-02 (R48) — SEO-only validation blocker
- File+dòng: `giao-dien.py`, `_v3_bam_cap_nhat_seo()` và `_v3_cap_nhat_seo_worker()` khoảng dòng 1900–1970.
- Vấn đề: record `nghi_van_dien_ap=True` vẫn có thể đi qua SEO-only transport dù Save Draft đã chặn.
- Sửa thế nào: loại blocker ngay lúc lập danh sách và kiểm lại trong worker trước mọi WordPress call; không sửa Hard Block.
- Kiểm ra sao: worker mock với blocked row trả `SEO_AI_CALLS 0`, `SEO_WP_CALLS 0`; Save Draft giữ test Gate 6 cũ AI=0/WP=0 — PASS R48 logic.

## BUG-03 (R06+R07) — runner PASS giả
- File+dòng: `run_tests.py`, vòng phân loại output khoảng dòng 130–155.
- Vấn đề: exit code 0 vẫn bị tính PASS dù không có PASS marker; output `FAIL 1` cũng lọt PASS.
- Sửa thế nào: PASS chỉ khi exit0 + có marker PASS thật + không có `[FAIL]`/`FAIL n` với n>0; bỏ fallback exit0=>PASS.
- Kiểm ra sao: synthetic no-assert bị `[FAIL]`; `test_v35_hang_doi.py` có `FAIL 1` bị `[FAIL]`; runner synthetic summary thật `PASS 61 / FAIL 5 / SKIP 0 / 33.3s` — PASS R06/R07, đồng thời lộ thêm FAIL thật cần giữ nguyên.

## BUG-04 (R51) — category preview không aggregate blocker
- File+dòng: `category_preview.py`, `dung_html_danh_muc()` vòng gom specs khoảng dòng 55–80.
- Vấn đề: row đã bị importer flag vẫn đóng góp cấp điện áp/công suất vào landing category.
- Sửa thế nào: pre-filter `nghi_van_dien_ap=True` trước aggregate; Hard Block giữ nguyên.
- Kiểm ra sao: sinh lại đủ 9 HTML từ MASTER Ver8 hiện hành, `FILES 9`, toàn bộ preview `HAS_1_KV False` — PASS R51 trước khi sửa dữ liệu BUG-08.

## BUG-06 (R41) — alt/title WordPress Media
- File+dòng: `ai_wp_adapter.py` thêm `cap_nhat_meta_anh_media()` gần uploader ảnh; `giao-dien.py` production callback ảnh khoảng dòng 2225.
- Vấn đề: image workflow mới chỉ POST binary `/media`, alt/title chỉ tồn tại local.
- Sửa thế nào: sau media create/cache, production callback gọi metadata endpoint `/media/{id}` với `alt_text` + `title`; uploader callback cũ 3 tham số vẫn được hỗ trợ.
- Kiểm ra sao: fake WordPress production path ghi `POST_COUNT 2`, endpoints `/media` + `/media/77`, `HAS_MEDIA_METADATA_POST True` — PASS R41; chưa verify site thật.

## BUG-05 (R15) — MASTER Ver8 Dashboard cached formula #NAME?
- File+dòng: `8MASTER_ENRICHED_Ver8.xlsx`, sheet `00_Dashboard` 50 ô công thức B5:F8 và C12:E21; workbook được tạo lại từ Ver7 bằng artifact_tool.
- Vấn đề: Ver8 cũ giữ công thức nhưng cached value thành `#NAME?`, làm data_only đọc sai.
- Sửa thế nào: dựng lại Ver8 từ Ver7, viết lại 50 công thức với sheet reference có quote để calculator tính được cache; giữ công thức sống, không chuyển thành static value.
- Kiểm ra sao: raw XLSX `sheet5.xml` có 50 `<x:f>`; B5 cache=3387, B8 cache=1340, C17 cache=524, E21 cache=41; artifact inspect Dashboard B5:F8 toàn numeric, không `#NAME?` — PASS R15.

## BUG-07 (R16) — Dashboard phụ kiện thiếu 8 record
- File+dòng: `8MASTER_ENRICHED_Ver8.xlsx`, `00_Dashboard` B8:F8 và C17:E21.
- Vấn đề: range kết thúc ở dòng 1333 nên Dashboard đếm 1332, importer đọc đủ 1340.
- Sửa thế nào: toàn bộ công thức phụ kiện mở range tới dòng 1341, đúng sheet có header + 1.340 data rows.
- Kiểm ra sao: B8 formula `COUNTA('04_Phu_Kien_Va_Khac'!K2:K1341)` cache=1340; production importer `PHU_KIEN_ROWS 1340` — PASS R16.

## BUG-08 — sửa điện áp VNMBA trong MASTER
- File+dòng: `8MASTER_ENRICHED_Ver8.xlsx`, sheet `03_May_Bien_Ap_Do_Luong` J165/J166; log append sheet `00_Nhat_Ky_Sua_Loi` rows 263–270.
- Vấn đề: VNMBA1P1S/VNMBA1P2S bị gán nhầm công suất `1 kV` vào cấp điện áp.
- Sửa thế nào: đổi J165=`12.7/0.22 kV`, J166=`22/0.22 kV` bóc trực tiếp từ tên `12700/220V` và `22000/220V`; đồng thời giữ B3-B5: 20 A2608 source flag, MBT3P180A2608=`noi_suy`, cờ Io không khôi phục số.
- Kiểm ra sao: production importer đọc hai SKU đúng cấp điện áp, cả hai `nghi_van_dien_ap=None`, tổng flag điện áp trong profile=0; log Ver8 có đủ block sửa — PASS.


---

## CHANGELOG-4.2

### CHANGELOG — SONEALEO ULTRA 4.2

## VIỆC 1 — Full suite / harness isolation
- File+dòng: `run_tests.py` dòng 87-164; `tests/test_v38_gate5_image_e2e.py` dòng 83-155; `tests/test_v39_a1_layout.py` dòng 47-54.
- Vấn đề: runner 4.1 gom nhiều test stateful vào cùng một sandbox và không log thời gian từng subprocess; strict PASS marker cũng làm layout test exit0 bị tính FAIL, còn Gate5 mock chưa theo contract metadata Media mới nên FAIL giả sau BUG-06.
- Làm thế nào: giữ 4 worker song song nhưng tạo sandbox RIÊNG cho từng file test; instrument `[RUN]/[DONE] + giây + exit`; cập nhật Gate5 mock nhận POST `/media/{id}` và layout test in PASS marker thật. Không giảm test/record, không chuyển suite sang tuần tự.
- Kiểm ra sao: full `run_tests.py` trên Xvfb kết thúc `PASS=64 / FAIL=0 / SKIP=1`, `33.3s`, checksum env/DB không đổi. Lần timeout cũ không tái hiện ổn định; instrumentation cho thấy clean run không có test nào >12.5s, nên không có bằng chứng để quy timeout cũ cho DB lock/port/Tk race cụ thể.

## VIỆC 2 — `test_v35_hang_doi.py` thiếu tksheet
- File+dòng: `tests/test_v35_hang_doi.py` dòng 51-57; `run_tests.py` dòng 151-159.
- Vấn đề: môi trường Linux audit không cài `tksheet`, nhưng test vẫn assert bảng tksheet phải tồn tại nên tạo `PASS 20 / FAIL 1`; đây là thiếu dependency môi trường, không phải logic hàng đợi production đã được chứng minh hỏng.
- Làm thế nào: nếu import `tksheet` thất bại, test kết thúc bằng exit code 77 với lý do rõ; runner phân loại exit 77 thành SKIP riêng, không tính PASS và không giấu khỏi summary. Các assertion core trước phần UI vẫn chạy.
- Kiểm ra sao: chạy trực tiếp trả `PASS 14 / FAIL 0; UI SKIP`, exit=77; full suite hiển thị `[SKIP] test_v35_hang_doi.py` và tổng `64 PASS / 0 FAIL / 1 SKIP`.

## VIỆC 3.1A — Rà nợ audit 3.7: workspace ảnh + mock/UI
- File+dòng: `tab_anh.py` khoảng dòng 137-370; `workspace_anh.py` khoảng dòng 317-510; `giao-dien.py` khoảng dòng 2400, 4159-4205.
- Vấn đề: audit 3.7 còn chỉ ra workspace mới thiếu slug/source_row, lookup bài có thể lấy wp_id sai site/mẫu, reuse counter có thể tính metadata của file đã xoá, mock batch thiếu per-record exception/final cleanup và UI còn nút tracker chết.
- Làm thế nào: dùng `source_row` thật; slug lấy từ `render_phase2.dung_slug()`; dashboard ảnh lọc theo site hiện tại và chỉ nhận wp_id khi record có đúng 1 bài trên site; reuse chỉ đếm asset còn file vật lý; mock batch bọc từng record + cleanup trong finally; ẩn nút tracker disabled. Không đổi tên/move hàm, không đụng Hard Block/chống trùng/core import.
- Kiểm ra sao: `python -m compileall -q tab_anh.py workspace_anh.py giao-dien.py` exit=0; `test_v37_anh.py` = `PASS 47 / FAIL 0`; `test_v40_1_family_ui.py` PASS; `test_v39_a1_layout.py` PASS trên Xvfb. Test `test_v34_that_ui.py` chạy trực tiếp trên worktree bẩn cho FAIL do DB state đã bị các lượt test trước để lại, nên KHÔNG dùng kết quả đó làm regression; full suite per-test sandbox ở VIỆC 1 mới là bằng chứng release.

## VIỆC 3.1B — Rà nợ audit 3.7: dependency manifest
- File+dòng: `CAI-DAT-LAN-DAU.bat` dòng 41-45; `PHAN-MEM.bat` dòng 34-48; `requirements.txt`.
- Vấn đề: audit 3.7 ghi installer/fallback tự liệt kê dependency riêng nên drift; chính môi trường audit hiện thiếu `tksheet` đã làm test UI phải SKIP.
- Làm thế nào: cả installer Python riêng và fallback Python hệ thống đều cài từ một `requirements.txt`; fallback kiểm luôn `fitz` + `tksheet`. Không sửa cơ chế Tk ABI vì Linux không chứng minh được bản vá Windows an toàn.
- Kiểm ra sao: grep production BAT xác nhận cả hai đường đều dùng `requirements.txt`; `requirements.txt` hiện có `requests/openpyxl/Pillow/bleach/pymupdf/tksheet`. Rủi ro copy Tk từ Python hệ thống khác ABI vẫn ghi KHÔNG LÀM ĐƯỢC/CHƯA VERIFY WINDOWS, không tô PASS.

## VIỆC 3 — AI Vision tầng 2 hoàn tất đường chạy tùy chọn
- File+dòng: `loc_kho_anh_ai.py` toàn file; `LOC-KHO-ANH-AI.bat`; `LOC-KHO-ANH.bat`; `tests/test_v42_vision_tang2.py`.
- Vấn đề: tầng 2 cần hoạt động độc lập, không đoán kVA, không làm hỏng tầng 1 khi thiếu AI; hai BAT lọc ảnh lại trỏ nhầm `_python/.python` trong khi installer thật tạo thư mục `python`.
- Làm thế nào: giữ đúng 3 trục Vision (dầu/khô, 1/3 pha, vai trò), bất kỳ trục không chắc -> `_CHUA_PHAN_LOAI`; không hỏi/ghi công suất; sửa BAT dùng `python\\python.exe`, fallback Python hệ thống; không có API key -> `bo_qua_khong_ai`.
- Kiểm ra sao: `tests/test_v42_vision_tang2.py` chạy mock/no-AI: `PASS 6 / FAIL 0`; xác nhận file tầng 1 còn nguyên, 1 ảnh mock đủ bằng chứng được phân loại, ảnh mơ hồ vào chưa phân loại, report không có kVA. Không gọi Gemini thật.

## VIỆC 3.1C — Rà nốt nợ audit 3.7 trong phạm vi được phép
- File+dòng: `xu_ly_anh.py` khoảng 180-394; `workspace_anh.py` khoảng 317-510; `db_phase2.py` khoảng 31-40, 226-253; `cauhinh.py` khoảng 270-283; `ai_wp_adapter.py` khoảng 1040-1090; `giao-dien.py` khoảng 100-125, 232, 2132, 3273, 3624, 3697, 4325, 4688; `.gitignore`; `requirements.txt`.
- Vấn đề: audit 3.7 còn nợ alpha ảnh, meta corrupt, stale reuse, SQLite writer, HTTPS credential, lỗi metadata Media bị nuốt, stop/close worker, stdout/UI callback, version user-facing và dependency drift; một số nợ khác đã hết hiệu lực hoặc bị cấm theo phạm vi task.
- Làm thế nào: alpha composite nền trắng trước RGB; meta corrupt backup+raise; reuse chỉ đếm file còn tồn tại; WAL+busy_timeout; production URL bắt HTTPS; metadata Media trả warning khi update lỗi; close set các stop event đang có; stdout router theo thread và UI callback log traceback; đồng bộ chuỗi release hiện hành 4.2; dependency dùng `requirements.txt`. Không refactor, không đổi tên hàm, không đụng Hard Block/chống trùng/SKU duplicate.
- Kiểm ra sao: grep production xác nhận các đường trên đã nối; alpha fixture cho corner RGB `(255,255,255)`; `test_v37_anh.py=PASS 47/FAIL 0`; audit item schema frontend R55 vẫn PARTIAL, Tk ABI installer Windows và legacy Claude optional vẫn CHƯA VERIFY/KHÔNG LÀM ĐƯỢC, không tô PASS.

## VIỆC 1B — Instrument harness tới ranh giới copy / subprocess / cleanup
- File+dòng: `run_tests.py` trong `_chay_nhom_test()` khoảng dòng 91-113.
- Vấn đề: log `[RUN]`→`[DONE]` chưa phân biệt được lần treo lịch sử xảy ra lúc copy sandbox, subprocess test hay cleanup thư mục tạm; một final-artifact run vừa dừng ở `[RUN] test_v48.py` nên chưa đủ bằng chứng quy cho test_v48.
- Làm thế nào: thêm timestamp riêng `[COPY]`, `[EXEC]`, `[CLEAN]`, vẫn giữ 4 worker, cùng test, cùng timeout 90s; không đổi acceptance, không tăng timeout.
- Kiểm ra sao: checkpoint source compile sau patch; full suite sẽ được chạy lại từ ZIP sạch và log phase cụ thể dùng làm bằng chứng cuối cho VIỆC 1.

## VIỆC 1C — Chốt root cause harness treo và giữ chạy song song
- File+dòng: `run_tests.py` import executor và block chạy 4 worker khoảng dòng 22, 135-149.
- Vấn đề: cùng group 16 test chạy từ main thread hoàn tất tới cuối, nhưng chính group đó chạy trong `ThreadPoolExecutor(max_workers=1)` treo khi gọi subprocess ở test cuối; lần full suite khác treo ở `test_v48.py`. Test riêng `test_v48.py` hoàn tất 11.73s. Vậy lỗi không gắn cố định với test_v48 mà nằm ở harness gọi subprocess từ long-lived worker thread.
- Làm thế nào: đổi CHỈ executor của harness từ ThreadPool sang ProcessPool, vẫn 4 worker song song, vẫn subprocess riêng + sandbox riêng cho từng file, vẫn timeout 90s; không chuyển tuần tự, không tăng timeout, không bỏ test.
- Kiểm ra sao: diagnostic thật: group2 main-thread `16/16` kết thúc và v48=11.53s; cùng group trong ThreadPool đã đi qua v48=11.71s rồi treo ở v51 trước `[EXEC]`. Full ProcessPool suite sẽ được chạy trên artifact sạch và dùng làm acceptance cuối.

## VIỆC 1D — Loại executor wrapper, giữ 4 subprocess song song
- File+dòng: `run_tests.py` hàm mới `_chay_song_song_main()` và block scheduler trong `main()`.
- Vấn đề: ProcessPool không giải quyết triệt để: full run vẫn dừng ở v48; chạy không DISPLAY đã in xong summary sau 36.4s nhưng process không thoát trước outer 90s, chứng minh còn lỗi shutdown/executor chứ không phải test cụ thể. ThreadPool trước đó treo bên trong `subprocess.run()` ở test thay đổi theo lượt.
- Làm thế nào: scheduler nằm ở MAIN THREAD, tối đa 4 `Popen` chạy song song; mỗi test sandbox riêng; stdout/stderr ghi file riêng thay vì PIPE; timeout mỗi test giữ nguyên 90s. Không giảm test, không tuần tự hóa, không tăng timeout.
- Kiểm ra sao: source compile PASS; acceptance kế tiếp là full `run_tests.py` phải tự thoát, trả exit thật và summary thật từ artifact sạch. Nếu vẫn treo sẽ ghi KHÔNG LÀM ĐƯỢC, không tăng timeout.

## VIỆC 1 — ACCEPTANCE CUỐI full suite trên worktree 4.2
- File+dòng: `run_tests.py`; toàn bộ `tests/test_*.py` (66 file đọc trực tiếp từ thư mục tests).
- Vấn đề: R05 của 4.1 FAIL vì full runner không tự kết thúc; phải có số thật, thời gian thật và không được giấu SKIP.
- Làm thế nào: dùng scheduler main-thread tối đa 4 subprocess, sandbox từng file, output file riêng, strict PASS/FAIL/SKIP; `test_v35_hang_doi.py` thiếu tksheet vẫn là SKIP 77 có lý do.
- Kiểm ra sao: background process tự kết thúc; output thật `PASS: 65`, `FAIL: 0`, `SKIP: 1`, `Thời gian: 36.4s`, checksum production env/DB không đổi; `test_v48.py` trong chính full run hoàn tất `13.02s`. Nguồn: `/tmp/suite42bg.log` từ `run_tests.py` hiện hành.

## VIỆC 3.1D — Rà nợ audit 3.7: FAQ schema được delivery tới Woo meta + WPCode
- File+dòng: `ai_wp_adapter.py` dòng 511-615; `giao-dien.py` dòng 2265-2271; `WPCode-SCHEMA-SONEALEO.php` dòng 6-50; `tests/test_v38_gate7_woo_schema.py`.
- Vấn đề: audit 3.7 mục FAQ schema xác nhận `render_phase2.py` đã sinh `faq_schema` nhưng production Woo không truyền nó, và snippet frontend chỉ đọc Product schema; feature tồn tại ở renderer nhưng chết ở delivery.
- Làm thế nào: giữ nguyên tên/API cũ, chỉ thêm tham số optional `faq_schema=None`; production truyền `bai['faq_schema']` vào Woo meta `_snl_faq_schema_jsonld`; WPCode lặp qua cả Product + FAQ key. Không đụng Hard Block, chống trùng hay SKU duplicate.
- Kiểm ra sao: `test_v38_gate7_woo_schema.py` thật in `FAQ_SCHEMA_META={"@type":"FAQPage",...}` + `PASS_GATE7_LOCAL=1`; `php -l WPCode-SCHEMA-SONEALEO.php` = `No syntax errors detected`. Frontend site thật vẫn CHƯA VERIFY theo luật không POST/không truy cập site production.

## VIỆC 1 — REGRESSION SAU FAQ DELIVERY
- File+dòng: toàn bộ source 4.2 sau `VIỆC 3.1D`; `run_tests.py`; 66 file `tests/test_*.py` đọc trực tiếp từ source.
- Vấn đề: thêm delivery FAQ sau lần full-suite trước có thể tạo regression; không được dùng kết quả 36.4s cũ để ký artifact mới.
- Làm thế nào: chạy lại nguyên full suite, giữ 4 subprocess song song, timeout từng test 90s, không bỏ test/không đổi acceptance.
- Kiểm ra sao: `run_tests.py` tự kết thúc exit=0; `PASS=65 / FAIL=0 / SKIP=1`, `33.5s`; SKIP duy nhất `test_v35_hang_doi.py` vì môi trường audit thiếu `tksheet`, phần core của test vẫn `PASS 14 / FAIL 0`; checksum production env/DB không đổi. Nguồn: `/tmp/suite42_afterfaq.log`.

## VIỆC 3.1E — Rà nợ audit 3.7: current version traceability còn sót
- File+dòng: `giao-dien.py` dòng 362; `README.md` dòng 29.
- Vấn đề: release hiện hành là 4.2 nhưng một status label user-facing vẫn ghi `VER 5.3 Claude`, README current tree vẫn nói 46 test trong khi source hiện có 66 `tests/test_*.py`; audit 3.7 đã chỉ ra đúng loại lệch release trace này.
- Làm thế nào: chỉ sửa hai chuỗi CURRENT thành `VER 4.2` và `66 file`; không rewrite comment/test/changelog lịch sử mang mốc 2.x/3.x/4.9.x/5.x.
- Kiểm ra sao: grep current UI/BAT cho thấy `PHAN-MEM`, `CAI-DAT-LAN-DAU`, `KIEM-THU-30-BAI`, `5-KIEM-TRA-KET-QUA` và status label đều 4.2; `find tests -maxdepth 1 -name 'test_*.py' | wc -l` = 66; `py_compile giao-dien.py` exit=0.

## VIỆC 3.1F — Chốt ledger nợ audit 3.7, không tô PASS phần chưa chứng minh
- File+dòng: `docs/AUDIT-DEBT-4.2.md`; đối chiếu các mục audit 3.7 từ uploader/schema/thread/SQLite/installer tới release traceability.
- Vấn đề: các vá 4.2 nằm rải nhiều file; nếu chỉ ghi “rà nợ audit” thì người tiếp quản không biết mục nào đã xử lý, mục nào hết hiệu lực, mục nào còn nợ thật.
- Làm thế nào: lập bảng từng mục audit 9-47 với trạng thái `ĐÃ XỬ LÝ / HẾT HIỆU LỰC / PARTIAL / CHƯA LÀM ĐƯỢC`, và ghi thẳng 5 phần chưa được ký PASS; không sửa các phần bị cấm để làm đẹp số.
- Kiểm ra sao: static trace source xác nhận các nợ còn thật: `tim_workspace(goc,sheet,sku)` chưa có dataset identity; `dang_wp_that()` chưa schema transport; `_dong()` chưa join registry; installer vẫn copy `_tkinter.pyd` từ system Python; R55 frontend còn cần View Source. Các mục này được giữ PARTIAL/CHƯA LÀM ĐƯỢC.

## VIỆC 3.2 — Chạy lại ĐÚNG 59 case REGRESSION-4.0 trên 4.2
- File+dòng: matrix gốc `REGRESSION-4.0.md` R01-R59; source/data trong artifact 4.2; không sửa/thêm/bỏ case acceptance.
- Vấn đề: 4.1 còn R05 FAIL và task bắt buộc dùng nguyên 59 case cũ để tránh tự viết bài dễ rồi tự chấm PASS.
- Làm thế nào: chạy lại artifact/compile/GUI, runner synthetic, checksum, raw XLSX, family/image/filter/SEO/category/charts, Woo mocks, 3 legacy fixture và R59 3 fresh rounds; HTTP Woo/Gemini đều mock, không site thật.
- Kiểm ra sao: trước bước đóng ZIP cuối, matrix cho `58 PASS / 0 FAIL / 1 PARTIAL`; R05 đổi `FAIL→PASS` với full suite `65 PASS / 0 FAIL / 1 SKIP`, 33.3s; R55 vẫn PARTIAL vì frontend site thật chưa View Source. R59 fresh extract 3 vòng = 6/6 rc0, `TKERR=0`. Bằng chứng raw: `/tmp/final42_latest.log`, `/tmp/reg42_custom_latest.log`, `/tmp/reg42_targeted_latest.log`, `/tmp/xlsx_raw_reg_latest.log`, `/tmp/r59_fresh_latest.log`.

## VIỆC 4 — Tự đề xuất: release ZIP không mang runtime secret/state/cache
- File+dòng: bước đóng gói release 4.2; `.gitignore`; không đổi production logic.
- Vấn đề: kiểm trực tiếp `SONEALEO-ULTRA-4_1.zip` thấy có `cau-hinh.env` và nhiều `__pycache__/*.pyc`; release artifact không nên bê config/runtime state và rác interpreter đi theo.
- Làm thế nào: package 4.2 loại `cau-hinh.env`, `phase2-du-lieu.db*`, `__pycache__`, `*.pyc`, screenshot test `a1-*.png`, `.vision-cache`; vẫn giữ MASTER Ver8, source, test, docs và file mẫu config.
- Kiểm ra sao: `unzip -l` của ZIP 4.2 cuối phải cho 0 entry khớp danh sách cấm; extract sạch phải compile và full suite từ chính artifact. SHA-256 cuối ghi ở `REGRESSION-4.2.md` bên ngoài ZIP để tránh vòng lặp hash tự tham chiếu.

---

## CHANGELOG-4.3.1

### CHANGELOG 4.3.1

## 1. Hard Block META fail-soft
- **File + dòng:** `ai_wp_adapter.py:389-443`, `giao-dien.py:2189-2335`.
- **Vấn đề:** Windows thật cho thấy `meta_title/meta_description` có số bị Hard Block làm cả record thành `loi`, không tạo Draft dù thân bài không vi phạm.
- **Sửa:** chỉ khi vi phạm còn lại nằm hoàn toàn ở META thì thay bằng meta code-only không số, không rỗng, không gọi AI lại; thân bài vi phạm vẫn chặn ngay. Khi Draft thành công, cảnh báo META được ghi vào cột `loi` để rà sau.
- **Kiểm:** `qa/test_v431_meta_hardblock.py`: `META-ONLY-FAIL-SOFT` PASS, `META-FALLBACK-NOT-EMPTY` PASS, `BODY-STILL-BLOCKS` PASS, `WARNING-PERSIST-WIRING` PASS.

## 2. Máy biến áp tương thích cho vỏ MBA
- **File + dòng:** `render_phase2.py:1734-1764,1820+`, `profiles.py:282-288,386-389,439-453`, `prompts_phase2.py:121-133,266`.
- **Vấn đề:** source thật route vỏ mạ kẽm vào `outline_vo_may_bien_ap`; outline cố ý không dùng `cap_dien_ap`, nên cụm máy tương thích trong Tên hàng chưa có field hợp lệ. Đồng thời `22/0,4kV` nguồn và `22/0.4kV` AI bị so khác nhau.
- **Sửa:** bóc `may_tuong_thich` CHỈ từ Tên hàng khi có đủ pha + kVA + cặp kV; đưa field vào prompt/Hard Block; chuẩn hoá dấu phẩy/dấu chấm khi so cụm kỹ thuật. Không suy từ SKU, không biến điện áp máy thành điện áp của vỏ.
- **Kiểm:** 7 SKU acceptance PASS 7/7. Đối chiếu DB thật đã gửi: 24/24 dòng `Vỏ mạ kẽm` bóc được field và meta chứa máy tương thích qua Hard Block; 7/7 `Giá treo MBT` không bị suy diễn khi tên không đủ dữ liệu.

## 3. Regression cũ vẫn kiểm Hard Block thân bài
- **File + dòng:** `tests/test_v36_regression.py:102-108`.
- **Vấn đề:** proof test cũ cố ý bịa số trong META; luật 4.3.1 mới cho META fallback nên case đó không còn là lỗi hợp lệ.
- **Sửa:** giữ nguyên mục tiêu test runner nhưng chuyển dữ liệu phá sang `dac_diem_html` (`99kV`) để kiểm invariant thân bài vẫn bị chặn.
- **Kiểm:** `test_v36_regression.py`: `TỔNG: 16/16 PASS`.

## 4. Regression tổng
- **File + dòng:** toàn bộ test tự động của release.
- **Vấn đề:** cần chắc hotfix không làm case đang PASS thành FAIL.
- **Sửa:** không thay harness, không giảm test.
- **Kiểm:** `run_tests.py` đã in summary thật `PASS: 66 / FAIL: 0 / SKIP: 1`, thời gian `35.2s`; SKIP là `test_v35_hang_doi.py`, core `PASS 14 / FAIL 0`, UI thiếu dependency ở môi trường Linux. Outer invocation của container không tự thoát sạch sau summary nên không tuyên bố exit-code của harness đã được chứng minh.

---

## CHANGELOG-4.3

### CHANGELOG 4.3 — HOTFIX WINDOWS

## VIỆC 1 — Render chậm do AI fallback
- File+dòng: `ai_wp_adapter.py` 213–290, 384–490; `giao-dien.py` 2176–2326.
- Vấn đề: source 4.2 dùng `timeout=120` và retry cùng cặp 3 lần khi Timeout; một cặp chết có thể giữ tối đa 3×120s + 2×5s = 370s trước fallback. Windows thật do Thịnh đo: bài 1=398.8s, bài 2=419.0s.
- Sửa: timeout mỗi cặp còn 45s; Timeout/429 chuyển ngay cặp kế; cặp thắng đưa lên đầu list cho bài kế; model thắng ghi lại `MODEL_GEMINI` vào `cau-hinh.env`; thêm timing AI từng cặp + render + ảnh + WP + tổng bài.
- Kiểm: synthetic cùng workload: 4.2 ba bài=`0.0704/0.0704/0.0704s`; 4.3=`0.0704/0.0101/0.0102s`; one dead pair 4.2=`3 calls timeout 120`, 4.3=`1 call timeout 45`. `test_v43_hotfix.py` PASS. Đây là mock timing, chưa phải Windows/Gemini thật <60s.

## VIỆC 2 — Tab ảnh Windows cuộn + multi-select
- File+dòng: `tab_anh.py` 95–150, 335–351.
- Vấn đề: action buttons nằm sau canvas nên DPI/theme Windows có thể bị canvas đẩy/che; MouseWheel trên widget con không đi vào canvas; chọn nhiều file chưa bảo đảm chỉ lấp ô trống.
- Sửa: action frame pack `side=bottom` trước canvas; scrollbar `tk.Scrollbar` visible; `MouseWheel` scroll canvas khi pointer nằm trong vùng ảnh; Ctrl-select nhiều file lấp các slot trống theo thứ tự, single-file vẫn thay slot được bấm.
- Kiểm: `IMAGE-MULTI-4` gán `hero/bien_may/can_canh/lap_dat`; `IMAGE-WHEEL` phát sinh `yview_scroll(1,'units')`; frozen R27/R28 vẫn chạy. Không dùng Xvfb để tuyên bố Windows visual đã PASS; cần Thịnh nhìn lại màn Windows thật 1366×768.

## VIỆC 3 — Mock làm bẩn wp_id production
- File+dòng: `ai_wp_adapter.py` 165–175; `db_phase2.py` 369–377; `giao-dien.py` 1794–1795, 4166–4188.
- Vấn đề: Mock lưu fake `wp_id/wp_url=.mock` vào `bai_viet_phase2`; Real đọc ID giả rồi UPDATE và WordPress trả `rest_post_invalid_id` 404, restart không hết vì DB đã bẩn.
- Sửa: Mock vẫn ghi content/status cho Dashboard nhưng `wp_id=NULL`, `wp_url=NULL`; thêm cleaner chỉ DELETE row có `wp_url` chứa `.mock`; thêm nút `Dọn state .mock`.
- Kiểm: `MOCK-NO-FAKE-ID-IN-PROD-STATE` PASS; cleaner xóa 1 mock và giữ URL thật; `MOCK-TO-REAL-CREATE` gọi collection `/wp-json/wp/v2/posts` thay vì `/posts/1001`; `test_round2_integration.py` 36/36 PASS.

## HOTFIX BỔ SUNG — stdout Windows `None` (bug production đã báo ngay trước task)
- File+dòng: `giao-dien.py` 87–108; `tests/test_v43_hotfix.py`.
- Vấn đề: `ChuyenHuongIn` có thể chụp `sys.stdout=None` khi chạy `pythonw`; `write()` gọi thẳng `self.stdout_goc.write()` nên dòng log như `[CSS] ...` có thể làm GUI crash. Không có code nào chủ động set `stdout_goc=None`; giá trị `None` đi vào từ `sys.stdout` của process Windows.
- Sửa: guard `None` và stream đã đóng cho cả `write()`/`flush()`; worker có queue vẫn ghi queue như cũ; không đổi kiến trúc stdout.
- Kiểm: `STDOUT-NONE-CLOSED` dựng router với `None`, stream đã đóng, và worker queue; cả ba đường không crash. Đây là test trực tiếp class, chưa phải chạy `pythonw.exe` trên máy Windows thật.


---

## CHANGELOG-4.4.1.1

### CHANGELOG 4.4.1.1 — BUG-C WP ID RECOVERY

## BUG-C1 — tự phục hồi WP ID khi DB lệch WordPress
- File+dòng: `tab_anh.py:396+`, dùng lại `autopost.tim_san_pham_woo_theo_sku()` hiện hữu.
- Lỗi: bài thật đã tồn tại trên WooCommerce nhưng `bai_viet_phase2.wp_id=NULL` sau lịch sử Mock/cleanup BUG-B; tab Ảnh coi NULL là “bài chưa có” và bỏ cuộc.
- Sửa: khi thiếu `wp_id`, tra lại WooCommerce theo `publish_sku/SKU`; tìm thấy thì ghi `wp_id` về đúng `(dataset_id, record_id, site, mau)` rồi tiếp tục cập nhật ảnh; NOT_FOUND và API ERROR tách riêng.
- Kiểm: `tests/test_v4411_bugc_wp_id_sync.py` C1/C2/C3/C4 PASS.

## BUG-C2 — WP ID cũ chết tự invalidate và resolve lại 1 lần
- File+dòng: `tab_anh.py:462+`.
- Lỗi: DB có `wp_id` nhưng ID đã chết/sai có thể trả `rest_post_invalid_id`/404 và chặn cập nhật ảnh.
- Sửa: gặp invalid ID thì set local `wp_id=NULL`, tra lại theo SKU, ghi ID thật và retry đúng 1 lần; không loop vô hạn, không tạo bài mới.
- Kiểm: regression C5 PASS: `1001 -> 404 -> lookup SKU -> 888 -> body+gallery dùng 888`.

## BUG-C3 — nút ĐỒNG BỘ WP ID one-time
- File+dòng: `tab_anh.py:110`, `tab_anh.py:500+`.
- Lỗi: nhiều record lịch sử có bài thật trên site nhưng DB mất `wp_id`, sửa từng bài bằng tay không khả thi.
- Sửa: thêm `ĐỒNG BỘ WP ID`; quét record thiếu ID trong tab/site hiện tại, tra SKU, chỉ ghi ID tìm thấy; thống kê `Tìm thấy / Không tìm thấy / Lỗi API / thiếu identity`; không create/update content.
- Kiểm: regression C6 PASS, phân biệt chính xác FOUND/NOT_FOUND/API_ERROR.

## BUG-C4 — trạng thái Media khác trạng thái đã gắn vào bài
- File+dòng: `workspace_anh.py:475+`, `workspace_anh.py:519+`, `xu_ly_anh.py:441+`, `tab_anh.py:235+`.
- Lỗi: UI ghi `ĐÃ ĐĂNG 5/5` ngay khi chỉ có `media_id`, dù product chưa nhận gallery/body.
- Sửa: tách `Đã lên Media N/5` và `Đã gắn vào bài N/5`; delivery mới có `attached_wp_post_ids` theo site+post, ảnh họ dùng chung được phép ghi nhiều post ID; thay/re-upload ảnh reset attachment state của delivery mới.
- Kiểm: regression STATE-MEDIA/STATE-ATTACHED PASS với 5/5 ảnh.

## UX-C5 — đổi tên nút cập nhật ảnh
- File+dòng: `tab_anh.py:142`.
- Lỗi: `Đăng ảnh lên bài` dễ bị hiểu là đăng lại content.
- Sửa: đổi thành `Cập nhật ảnh lên WordPress`; nút single và batch đều resolve WP ID trước khi upload để tránh tạo Media mồ côi khi bài thật sự không tồn tại.
- Kiểm: UI contract PASS; `test_v44_ui_logic.py` 8/8 PASS dưới Xvfb.

---

## CHANGELOG-4.4.1.2

### CHANGELOG 4.4.1.2 — DUAL IMAGE DELIVERY

## BUG-D — Ảnh đã gắn Woo gallery nhưng không xuất hiện trong body bài cũ

1. **File/dòng:** `xu_ly_anh.py` — `chen_anh_vao_bai()`, `_figure_anh_noi_dung()`; `giao_dien_2_5.py` — `_slot_anh()` và vị trí mở body.
2. **Lỗi:** Ver 4.4.1.1 chỉ cập nhật body khi HTML lưu trong DB còn marker `SNL_IMAGE_SLOT`/placeholder legacy; nhiều bài production cũ đã mất marker nên 5 media_id chỉ hiện ở Woo product gallery. Hero còn bị cố ý loại khỏi body theo rule cũ.
3. **Sửa:** giữ đủ 5 ảnh trong Woo gallery **và** đưa đủ 5 role vào body. Ưu tiên marker; nếu bài cũ không còn marker thì chèn theo section semantic (`thong-so`, `cau-tao/dac-diem`, `ung-dung/huong-dan`) và fallback cuối body. Figure mới có `data-snl-role` để re-run thay ảnh, không nhân đôi. Renderer tương lai phát thêm marker `hero`.
4. **Kiểm:** `test_v4412_dual_image_delivery.py` PASS; `test_v441_image_placement.py` PASS; BUG-C 15/15 PASS; `test_v37_anh.py` 47/47 PASS; `test_v44_release.py` 12/12 PASS; `test_v44_ui_logic.py` 8/8 PASS dưới Xvfb; `test_v43_hotfix.py` 10/10 PASS; `test_v441_resume_tracker.py` 5/5 PASS; Ver 2.5 24/24 PASS; Ver 2.7 28/28 PASS.

---

## CHANGELOG-4.4.1.3

### CHANGELOG 4.4.1.3 — IMAGE PRODUCTION HOTFIX

Phạm vi bản vá: **chỉ pipeline ảnh + trạng thái delivery + watermark upload**. Không sửa `render_phase2.py`, `prompts_phase2.py`, classification, schema, Rank Math, slug hay logic sinh content.

## BUG-E1 — Một slot lỗi làm cả bộ ảnh không được gắn vào bài

1. **File/function:** `tab_anh.py` — `_dang()`, `_dang_hang_loat()`, `_gan_anh_vao_bai_ngay()`; `giao-dien.py` — production image path.
2. **Lỗi gốc:** `dang_anh_*()` vẫn trả các ảnh upload/reuse thành công trong `kq['anh']`, nhưng caller dùng `kq['loi']` như kill-switch. Chỉ một GIF/file hỏng/upload lỗi khiến bước attach gallery + body bị bỏ qua, để các ảnh tốt nằm orphan trong Media Library.
3. **Sửa:** attach mọi ảnh có đủ `url + wp_media_id`; slot lỗi giữ riêng để retry. Batch báo `PARTIAL`, chỉ hard-fail khi không còn ảnh hợp lệ hoặc WordPress attach thật sự thất bại. Lỗi của nguồn HỌ/RIÊNG được hạ thành cảnh báo nếu cùng role đã có fallback nguồn kia thành công.
4. **Kiểm:** `test_v4413_partial_watermark.py` + regression ảnh 4.4.1.2/4.4.1.1/3.7/4.4 đều PASS; chưa ký production PASS cho tới khi kiểm Windows/live.

## BUG-E2 — Media ID stale làm Woo reject toàn gallery

1. **File/function:** `ai_wp_adapter.py::gan_anh_vao_san_pham()`, `dulieu.py::xoa_cache_anh_wp_theo_media()`, `workspace_anh.py::vo_hieu_delivery_media()`, `tab_anh.py::_gan_anh_vao_bai_ngay()`, production path trong `giao-dien.py`.
2. **Lỗi gốc:** local `delivery_by_site`/cache có thể giữ `wp_media_id` của ảnh đã bị xoá trên WordPress. Pipeline skip upload vì tưởng Media còn sống, sau đó Woo trả `woocommerce_product_invalid_image_id` và từ chối cả mảng gallery.
3. **Sửa:** parse đúng media ID lỗi từ Woo; purge đúng cache + đúng delivery của site/role đó; giữ các ID còn sống; rebuild body để bỏ URL stale; retry gallery **một lần** với phần hợp lệ. Slot stale được để ở trạng thái cần upload lại, không xoá file local và không đụng state site khác.
4. **Kiểm:** regression mô phỏng `#1526 is an invalid image ID` xác nhận không nhặt nhầm HTTP status `400`, gallery retry chỉ dùng ID còn sống và body không giữ URL stale.

## BUG-E3 — Trạng thái UI có thể nói đầy đủ dù delivery chỉ một phần

1. **File/function:** `workspace_anh.py::trang_thai_hieu_luc()`.
2. **Lỗi gốc:** có đủ 5 file local nhưng chỉ một phần đã Media/attached có thể rơi về nhãn đếm file, gây hiểu nhầm là đã hoàn tất.
3. **Sửa:** ưu tiên hiển thị trạng thái thực: `Đã lên Media x/5` hoặc `Đã gắn vào bài x/5` kể cả partial.
4. **Kiểm:** regression xác nhận 1/5 attached hiển thị `Đã gắn vào bài 1/5`, không hiện `5/5` giả.

## WATERMARK — Chỉ đóng lên asset upload, không phá ảnh gốc

1. **File/function:** `xu_ly_anh.py::cau_hinh_watermark()`, `them_watermark_webp()`, `dang_anh_cua_bai()`; `cau-hinh.env.MAU`.
2. **Yêu cầu:** ảnh đưa lên WordPress có watermark nhưng kho ảnh/canonical local phải giữ sạch để đổi brand/site hoặc regenerate sau này.
3. **Sửa:** watermark text bán trong suốt được render vào file WebP tạm `.wp-upload/<site>/...` ngay trước upload. Mặc định text lấy domain site, opacity `82/255`, góc phải dưới, scale `0.026`; file canonical `.webp` local không bị watermark. Signature watermark nằm trong `delivery_by_site`, nên cùng config không reupload; đổi config hoặc legacy chưa có watermark sẽ reupload đúng một lần. Watermark fail thì fail-soft upload ảnh sạch, không làm chết slot.
4. **Kiểm:** regression xác nhận bytes upload khác canonical, canonical vẫn sạch, config không đổi thì skip, config đổi thì reupload, delivery lưu watermark signature.

## Version

- UI/README: `4.4.1.3`
- Giữ nguyên bản `4.4.1.2` để rollback.

---

## CHANGELOG-4.4.1.4

### CHANGELOG 4.4.1.4 — WATERMARK + REUSE POLICY

## F1 — Watermark có DOMAIN + HOTLINE
1. **File/function:** `xu_ly_anh.py` — `_hotline_watermark()`, `cau_hinh_watermark()`, `them_watermark_webp()`.
2. **Lỗi/thiếu:** 4.4.1.3 mặc định chỉ in domain; chưa có hotline và watermark một dòng dài khi thêm số điện thoại.
3. **Sửa:** watermark mặc định thành 2 dòng `domain` + `hotline`; vẫn chỉ đóng lên bản upload, không sửa ảnh gốc/canonical. `WATERMARK_TEXT` vẫn override và hỗ trợ `{domain}`, `{phone}`. Signature v2 gồm domain+phone để đổi cấu hình thì reupload đúng một lần.
4. **Kiểm:** `tests/test_v4414_watermark_reuse.py` — WM-DOMAIN/PHONE/TWO-LINES/TEMPLATE/NO-WRONG-PHONE/WM-BYTES-CHANGED/SOURCE-UNCHANGED PASS.

## F2 — Hotline nằm ngay trong cấu hình Website
1. **File/function:** `cauhinh.py` — `doc_website()`, `luu_website()`, `xoa_website()`; `giao-dien.py` — Website WordPress / `_v3_luu_website()`.
2. **Lỗi/thiếu:** Ver 3 chỉ lưu tên/URL/user/password/chế độ đăng, nên watermark không có nguồn hotline đáng tin; không được phép đoán hotline của site khác.
3. **Sửa:** thêm field `Hotline watermark`, lưu `WP_WEBSITE_HOTLINE`; API cũ vẫn tương thích vì tham số hotline có default. `WATERMARK_PHONE` cũ vẫn là override/fallback.
4. **Kiểm:** WEB-CONFIG-HOTLINE-READ/SAVE/UI PASS; `test_v34_that_ui.py` 8/8 PASS; `test_v35_idempotency.py` 11/11 PASS; `test_v46.py` 20/20 PASS; `test_v37_1_patch.py` 7/7 PASS.

## F3 — Cho phép một ảnh dùng cho nhiều SKU, không chặn reuse
1. **File/function:** `workspace_anh.py::gan_anh()/dem_dung_chung()` (giữ policy), `tab_anh.py::_gan_anh_chung()` (nói rõ policy trên UI), regression mới.
2. **Lỗi/thiếu:** Kho ảnh thiếu, một ảnh thực tế phải có thể dùng cho 2–3 bài; reuse chỉ được cảnh báo/đếm, tuyệt đối không được biến thành hard block.
3. **Sửa:** xác nhận và khóa contract `reuse cross-SKU = ALLOW`; nút Gán ảnh chung tiếp tục gán cùng source cho nhiều bài, thông báo rõ “không chặn”. Mỗi workspace/SKU vẫn có filename WebP riêng theo slug để alt/filename không bị trói chung.
4. **Kiểm:** REUSE-THREE-SAME-HASH, REUSE-COUNT-NONBLOCK, REUSE-3-SKU-UPLOADS, REUSE-SEO-FILENAME-PER-SKU PASS; `test_v37_anh.py` mục “đếm dùng chung, KHÔNG chặn” PASS.

## F4 — Giữ nguyên best-effort attach của 4.4.1.3
1. **File/function:** `tab_anh.py::_dang()` / `_gan_anh_vao_bai_ngay()`.
2. **Lỗi lịch sử:** một slot lỗi từng làm toàn bộ ảnh chỉ lên Media nhưng không gắn vào product.
3. **Sửa:** không mở rộng logic mới; giữ nguyên contract 4.4.1.3: có ít nhất một ảnh hợp lệ thì vẫn attach phần tốt vào body + gallery; slot lỗi/stale để retry.
4. **Kiểm:** `test_v4413_partial_watermark.py` 19/19 PASS; `test_v4412_dual_image_delivery.py` 12/12 PASS; `test_v4411_bugc_wp_id_sync.py` 15/15 PASS.

## Phạm vi không đụng
- `render_phase2.py`
- `prompts_phase2.py`
- `autopost.py`
- family/classification/content generation
- slug/schema/related-product logic
- WordPress Mock/Real state rules ngoài image path

---

## CHANGELOG-4.4.1

### CHANGELOG — SONEALEO ULTRA 4.4.1

## 1. Ảnh đúng vị trí + nút Đăng ảnh cập nhật bài ngay
- File+dòng: `giao_dien_2_5.py:384+`; `xu_ly_anh.py:316-373`; `tab_anh.py:387+`; `ai_wp_adapter.py:1143+`; production posting trong `giao-dien.py`.
- Vấn đề: 4.3 prepend cả 5 ảnh thành một cột đầu body; placeholder/comment cũ vẫn nằm giữa bài; nút `Đăng ảnh lên bài` chỉ upload Media rồi chờ lượt render sau.
- Sửa: `hero` chỉ vào Woo gallery; `bien_may/can_canh/lap_dat/giao_hang` thay đúng marker/placeholder theo vai trò; bóc cột figure legacy đầu bài; slot thiếu ảnh/comment `URL_ANH` bị xóa; nút Đăng ảnh cập nhật body + gallery + DB ngay, không gọi AI.
- Kiểm: `tests/test_v441_image_placement.py` = `PASS 12 / FAIL 0`, `BODY_URLS=[2,3,4,5]`, 3 ảnh gồm hero+bien+lap chỉ còn 2 figure body, `IMMEDIATE_ATTACH=PASS body=1 gallery=1 db=1`; `test_v38_gate5_image_e2e.py` vẫn PASS end-to-end mock.

## 2. META Rank Math fail-soft ở mọi đường sinh meta
- File+dòng: `render_phase2.py:550-706`; `giao-dien.py:2044-2046,2340-2466`.
- Vấn đề: `dung_goi_cap_nhat_seo()` còn có thể nhận `ValueError` từ Rank Math khi META chứa token bị Hard Block, làm chết cả lượt cập nhật SEO.
- Sửa: giữ nguyên Hard Block core; mọi Rank Math đi qua `_rank_math_fail_soft()`. META-only vi phạm được thay bằng meta code-only không số, không rỗng và trả cảnh báo để ghi cột `Lỗi`; Hard Block ở thân bài vẫn chặn nguyên bài như cũ.
- Kiểm: `tests/test_v441_meta_failsoft.py` = `PASS 7 / FAIL 0`; synthetic `1kVA` không raise và sinh fallback `Máy biến áp MBT...`; `qa/test_v431_meta_hardblock.py` = `PASS 5 / FAIL 0`, BODY `99kV` vẫn bị chặn.

## 3.1. Tiếp tục từ chỗ dừng
- File+dòng: `giao-dien.py:1899,2130-2191`.
- Vấn đề: Force Stop báo còn record chưa chạy nhưng tab Sinh & Đăng không có đường resume riêng.
- Sửa: thêm nút `Tiếp tục từ chỗ dừng`; chỉ đưa vào worker các record đang chọn chưa có `wp_id` ở đúng site/mẫu, luôn `cho_phep_cap_nhat=False`, nên bài đã xong không bị đụng lại.
- Kiểm: `tests/test_v441_resume_tracker.py` = `PASS 5 / FAIL 0`; fixture A có WP ID bị bỏ, chỉ B+C chưa có WP ID được chạy.

## 3.2. Bộ lọc CHƯA CHẠY ở tab Theo dõi
- File+dòng: `giao-dien.py:2568,4105-4169`.
- Vấn đề: dashboard cũ chỉ thấy record đã từng có state row, nên record chưa từng chạy không thể lọc ra.
- Sửa: thêm `CHƯA CHẠY`; ghép thêm record nguồn chưa có WP ID trên site/mẫu hiện tại, kể cả chưa từng có dòng trong `bai_viet_phase2`.
- Kiểm: `tests/test_v441_resume_tracker.py` = `TRACKER_CHUA_CHAY=WIRED_BY_NO_WP_ID`; `test_v44_tracker_logic.py` = `PASS 6 / FAIL 0` cho search/family/KPI/error detail.

## 3.3. Khối A gốc 4.4: Đăng ảnh phải chèn vào bài NGAY
- File+dòng: `tab_anh.py:387+` + `ai_wp_adapter.py:1143+`, dùng `xu_ly_anh.chen_anh_vao_bai()`.
- Vấn đề: 4.4 chỉ xử lý ẩn placeholder nhưng chưa thực hiện yêu cầu nút `Đăng ảnh lên bài` phải cập nhật bài đã có ngay.
- Sửa: sau upload Media, cả nút đơn và batch ảnh cập nhật body đúng vai trò + Woo gallery, rồi persist HTML mới vào DB; không render lại và không gọi AI.
- Kiểm: `tests/test_v441_image_placement.py` = `IMMEDIATE_ATTACH=PASS body=1 gallery=1 db=1`; mock xác nhận media IDs `[101,102,103,104,105]` được gửi gallery.

## Regression fixture alignment
- File+dòng: `tests/test_v34_that_ui.py` mock category lookup; `tests/test_v38_gate5_image_e2e.py` dùng role `bien_may` thay vì `hero` trong body.
- Vấn đề: fixture cũ giả định Woo không lookup category ID và giả định hero nằm trong body, trái contract production đã có từ các bản trước và trái luật ảnh 4.4.1.
- Sửa: chỉ cập nhật fake response/category và role test, không thay acceptance của thread/Gate5, không giảm record regression.
- Kiểm: R59 chạy 3 fresh rounds, `v34` + `v37` đều rc=0/TKERR=0; Gate5 vẫn `MEDIA_POSTS=1`, bytes>0, `<img>`=true, attach media ID và lần hai không upload lại.

---

## CHANGELOG-4.4

### CHANGELOG — SONEALEO ULTRA 4.4

## A1–A2 — Ẩn ô ảnh trống, bỏ comment URL_ANH
- File+dòng: `khoi_anh.py::cho_anh`, `render_phase2.py::khoi_anh_placeholder`, `giao-dien.py` khối Cấu hình Hiển thị.
- Vấn đề: placeholder `snl-cho-anh`/caption/comment hướng dẫn vẫn lọt ra frontend; công tắc cũ chỉ nối vào placeholder legacy chứ không khống chế các ô của bố cục 2.5.
- Sửa: placeholder luôn trả rỗng; bỏ công tắc placeholder khỏi UI; ảnh thật vẫn do workspace `xu_ly_anh` chèn, nên bài 3 ảnh chỉ có đúng 3 ảnh thật.
- Kiểm: `py_compile` 3 file PASS; acceptance HTML/renderer sẽ được ghi tiếp sau test 4.4, không dùng Xvfb làm bằng chứng UI.

## B1 — UPDATE Woo gửi slug mới
- File+dòng: `ai_wp_adapter.py::dang_woo_that`, nhánh payload trước POST/UPDATE.
- Vấn đề: code 4.3.1 cố tình chỉ gửi `slug` khi CREATE, nên bài đã có wp_id giữ URL cũ dù title/SEO đã đổi.
- Sửa: khi có slug hợp lệ, cả CREATE lẫn UPDATE đều gửi `slug`; lookup/idempotency wp_id/SKU giữ nguyên, không đổi chống đăng trùng.
- Kiểm: `py_compile` PASS; test fake Woo CREATE+UPDATE và SEO-only sẽ ghi kết quả sau. Bài đã đăng bằng 4.3 cần một lượt update (rẻ nhất là `Cập nhật SEO (không AI)`) để URL đổi; chỉ cài 4.4 không tự đổi URL.

## C1–C6 + D2–D4 — Tab Ảnh: tìm/sort/họ/multi-select và tiện ích file
- File+dòng: `tab_anh.py` bảng bài, bộ lọc, thao tác hàng loạt; `requirements.txt`; `xu_ly_anh.py` đăng ký HEIC/AVIF opener.
- Vấn đề: 241+ dòng khó tìm/sort, không thao tác nhiều dòng; picker chặn JFIF/HEIC/AVIF; phải gõ từ khoá Google Images và tự điều hướng Downloads.
- Sửa: tìm realtime, Ctrl+F, sort heading, STT+dòng N/tổng, dropdown họ, Ctrl/Shift multi-select + gán ảnh chung/đăng ảnh hàng loạt; picker thêm JFIF/WebP/HEIC/BMP/AVIF và mở Downloads; nút Google Images ghép query từ record; thêm `pillow-heif` để Windows có decoder HEIC/AVIF.
- Kiểm: `tab_anh.py` và `xu_ly_anh.py` `py_compile` PASS; test logic/filter/bulk sẽ ghi kết quả tiếp, UI visual chỉ chấp nhận screenshot Windows thật của Thịnh sau khi cài.

## C1–C8 + D1 — Tab Theo dõi và copy toàn tool
- File+dòng: `giao-dien.py::_v3_tab_5_theo_doi`, `_v3_nap_dashboard`, các handler sort/search/retry/copy context.
- Vấn đề: bảng Phase2 không search/sort/family/STT/multi-select; lỗi bị cắt; tổng quan dùng dashboard cũ nên hiện 0; label/table khó copy text.
- Sửa: tìm realtime mã/tên/brand, Ctrl+F, click heading sort hai chiều, STT+dòng N/tổng, family dropdown từ dữ liệu thật, extended selection, retry nhiều bài `loi` bằng chính worker đăng hiện có, nút xem lỗi đầy đủ; status bar đếm từ Phase2; chuột phải Copy áp dụng class Label/TLabel/Treeview toàn app.
- Kiểm: `giao-dien.py` `py_compile` PASS; retry giữ nguyên worker Hard Block/idempotency. Functional test trên DB/fake UI sẽ ghi tiếp; visual chỉ xác nhận bằng Windows thật sau khi Thịnh cài.

## D2 bổ sung — workspace nhận đúng extension mới
- File+dòng: `workspace_anh.py::DUOI_ANH`.
- Vấn đề: dù file picker cho chọn HEIC/AVIF/JFIF thì `gan_anh()` vẫn có thể từ chối do whitelist workspace cũ.
- Sửa: thêm `.jfif`, `.heic`, `.avif` vào whitelist; WebP/BMP đã có từ trước.
- Kiểm: `workspace_anh.py` `py_compile` PASS; test filetypes/whitelist sẽ ghi ở test 4.4.

## Regression legacy — cập nhật expectation bị supersede bởi spec 4.4
- File+dòng: `tests/test_v21_css_va_rollback.py` C1, `tests/test_v23_hinh_ky_thuat.py` H10, `tests/test_v496_patch.py` S5.
- Vấn đề: 3 test cũ khóa đúng hành vi mà task 4.4 yêu cầu bỏ: giữ placeholder ảnh trống và không gửi slug khi UPDATE Woo.
- Sửa: chỉ đổi expectation test sang spec 4.4; không đổi case trong REGRESSION-4.0 59 case và không nới assertion khác.
- Kiểm: `test_v21_css_va_rollback.py` = 18/18 PASS; `test_v23_hinh_ky_thuat.py` = 16/16 PASS; `test_v496_patch.py` = 14/14 PASS.

## C4/C8 + D3 bổ sung — số dòng/tổng quan/query không lệch khi lọc
- File+dòng: `tab_anh.py::_ap_loc/_bam_bai/_mo_google_images`; `giao-dien.py::_v3_chon_dashboard/_v3_nap_dashboard`.
- Vấn đề: mẫu đầu hiển thị mẫu số theo tập đã lọc thay vì tổng nguồn; thanh Tổng quan có thể tụt số khi đang lọc trạng thái; Google Images không được gắn tiền tố MBA cho profile khác.
- Sửa: nhãn dòng dùng tổng số record nguồn; KPI đã đăng đếm độc lập filter bằng record_id có `da_dang`+wp_id; Google Images chỉ ráp query MBA khi record là MBA, profile khác dùng tên thật.
- Kiểm: `py_compile tab_anh.py giao-dien.py` PASS; functional regression 4.4 chạy tiếp phía dưới, không dùng Xvfb làm bằng chứng visual.

## Release identity — user-facing 4.4
- File+dòng: `giao-dien.py` title/header/status; `README.md` header; `PHAN-MEM.bat` title.
- Vấn đề: artifact mới vẫn hiện 4.3.1 nếu chỉ gộp patch mà không đổi nhãn release.
- Sửa: đổi chuỗi user-facing hiện hành thành 4.4; giữ nguyên comment lịch sử 4.3.1 trong code.
- Kiểm: `py_compile giao-dien.py` PASS; grep user-facing 4.3.1 sẽ chạy lại trước đóng ZIP.

## C1/C5 UI width — tránh ép hàng lọc ở màn 1366
- File+dòng: `tab_anh.py::_dung`, hàng Tìm/Họ.
- Vấn đề: cột trái tab Ảnh hẹp hơn tracker; Entry/Combobox quá rộng có thể đẩy nhãn `dòng N/tổng` khỏi vùng nhìn trên DPI Windows.
- Sửa: giảm width Tìm 24→18 và Họ 28→22; không đổi dữ liệu/filter.
- Kiểm: `py_compile tab_anh.py` PASS. Visual 1366×768 vẫn để trạng thái CHƯA VERIFY WINDOWS vì môi trường audit không phải Windows.

## C functional smoke — search/sort/family/multi-select/scroll wiring
- File+dòng: `tests/test_v44_ui_logic.py` (mới), gọi trực tiếp `TabAnh` thật với widget Tk.
- Vấn đề: static grep chỉ chứng minh control tồn tại, chưa chứng minh lọc/sort/extended selection chạy đúng.
- Sửa: thêm functional test UI logic với 3 record giả; KHÔNG dùng kết quả này làm bằng chứng visual Windows.
- Kiểm: `PASS 8 / FAIL 0`: search brand/title, family filter, Ảnh sort 0→1→3, multi-select 2 dòng, STT/tổng và scrollbar-canvas wiring đều PASS.

## C tracker functional smoke — search/family/KPI/error
- File+dòng: `tests/test_v44_tracker_logic.py` (mới), gọi trực tiếp `_v3_nap_dashboard()` trên SQLite fixture thật.
- Vấn đề: source grep chưa chứng minh KPI/filter dùng đúng state DB, đặc biệt khi lọc `loi` dễ làm `đã đăng` tụt về 0.
- Sửa: thêm fixture 3 bài (2 `da_dang`, 1 `loi`) và kiểm search/họ/KPI/error text.
- Kiểm: `PASS 6 / FAIL 0`; KPI giữ `3 cần làm / 2 đã đăng / 1 còn lại` kể cả khi filter `loi`; search THIBIDI=2; family THIBIDI=2; lỗi đầy đủ giữ nguyên.

## C5 bổ sung — dropdown Họ lấy từ sản phẩm nguồn, không phụ thuộc bài đã chạy
- File+dòng: `giao-dien.py::_v3_nap_dashboard`.
- Vấn đề: nếu lấy họ từ dashboard thì SKU chưa từng render chưa có `bai_viet_phase2`, dropdown có thể thiếu họ dù dataset nguồn đã có đủ.
- Sửa: dựng danh sách họ từ toàn bộ sản phẩm `selected=1` của dataset; KPI dùng cùng tập nguồn này.
- Kiểm: tracker functional fixture vẫn `PASS 6 / FAIL 0`; test family MASTER Ver8 riêng xác nhận 141 MBA → 11 họ.

## Full suite worktree — sau toàn bộ patch 4.4
- File+dòng: `run_tests.py` chạy trên worktree 4.4, không sửa runner trong task này.
- Vấn đề: cần chắc patch UI/slug/placeholder không làm regression các test cũ.
- Sửa: không sửa thêm logic; chạy toàn bộ test trong sandbox từng file.
- Kiểm: 70 file test = `69 PASS / 0 FAIL / 1 SKIP`, thời gian `34.3s`; SKIP duy nhất `test_v35_hang_doi.py` do Linux thiếu `tksheet`, phần core của test=`PASS 14 / FAIL 0`; checksum production env/DB không đổi.

---

## HOTFIX-4.4.1.4-HF1

### SONEALEO ULTRA 4.4.1.4 HF1 — Google Images query

## Phạm vi
Chỉ sửa lỗi nút Google Images coi mọi record thuộc profile `may_bien_ap_do_luong` hoặc có kVA là máy biến áp.

## Root cause
`tab_anh.py::_mo_google_images()` dùng profile/kVA để suy ra `la_mba`, trong khi record đã có `outline_id` do router xác định.
Vỏ mạ kẽm có `profile_id=may_bien_ap_do_luong` và có kVA nên bị query sai thành máy biến áp.

## Sửa
`la_mba` chỉ đúng khi `outline_id == 'outline_may_bien_ap'`.
Các outline khác dùng đúng tên sản phẩm hiện hữu làm query.

## Regression
- Vỏ `MBTVM3P320` -> `Vỏ mạ kẽm nhúng nóng MBA 3P 320KVA 22/0,4KV- MBT`
- MBA thật -> `máy biến áp dầu MBT 320kVA 3 pha`
- `tests/test_v4414_hf1_google_images.py`: PASS
- `tests/test_v4414_watermark_reuse.py`: PASS 16/16
- `tests/test_v4413_partial_watermark.py`: PASS 19/19
- `py_compile`: PASS

Không thay đổi logic upload/attach/reuse/watermark.

---

## KET-QUA-3.9

| Việc | Kết quả | Bằng chứng | Thịnh phải làm gì |
| ---- | ------- | ---------- | ----------------- |
| A1 | XONG | Xvfb 1366x768 và 1920x1080 đều thấy nút Đăng; đủ 5 nhãn, không bị cắt | không |
| A2 | XONG | Mock: 3.8 = 12.0021s/10 probe/timeout 60s; 3.9 = 0.0002s/1 probe/timeout 12s; 404 không dò lại trong phiên | có — lần chạy Gemini thật đầu tiên xem log model được nhớ |
| A3 | XONG, còn 3 SKIP legacy | run_tests.py chạy 61 file trong 33.6s: 58 PASS / 0 FAIL / 3 SKIP thiếu fixture / 0 TIMEOUT; test_v37_batch_real 8/8 PASS, 3.58s | có — chỉ khi muốn chạy 3 test legacy thì bổ sung fixture cũ |
| A4 | XONG | Regression: câu có chữ PASS giữa output không được tính đạt; chỉ marker PASS/tổng kết hợp lệ mới match | không |
| B1 | XONG | MASTER Ver8 TBD1P15: Po=52, Pk=213 có ≤; Uk=2 và Io=1 không có ≤ | không |
| B2 | XONG | MASTER Ver8 có 9 dòng catalogue_hang, 8 dòng KP; 9/9 hiển thị “(W, catalogue hãng)”, không nhãn EVN | không |
| B3 | XONG | MASTER Ver8 A2608=20; nguồn = 19 suy_tu_tieu_chuan_khac + 1 noi_suy; 20/20 có viện dẫn TCCS 10:2021/EVN/chưa đối chiếu QĐ 2608 | có — dùng MASTER Ver8 thay Ver7 sau khi xem nhật ký |
| B4 | XONG | MBT3P180A2608 đọc lại AW108 = noi_suy | không |
| B5 | XONG | 20/20 A2608 Io vẫn trống; 20/20 có ghi chú “đã từng có, đã xoá cùng gói Po/Pk sai”; không khôi phục số | không |
| C1 | XONG | Đếm trên MASTER Ver8/importer thật: 141 SKU MBA, duplicate title groups=0 | không |
| C2 | XONG | MASTER Ver8 thực tế có 9 MOF; 9/9 title có tỷ số /5A, không xuống dòng, 9/9 unique | không |
| C3 | XONG | 20/20 A2608 render có TCCS 10:2021/EVN + “chưa đối chiếu QĐ 2608/QĐ-EVN SPC”; title A107/A2608 không trùng | không |
| C4 | XONG | 141/141 slug MBA unique; 0 slug chứa SKU/Cu-Cu/chuan; công thức mới giữ uniqueness bằng QĐ/cấp áp khi cần | không |
| C5 | XONG | 141/141 MBA có đủ 3 meta Rank Math; 0 Hard Block violation; focus/title duplicate groups=0; title≤60, description≤160 | không |
| C6 | XONG BẰNG MOCK | Target đếm từ MASTER Ver8 = 150 SKU (141 MBA + 9 MOF); mock Woo payload chỉ name/slug/meta_data, AI calls=0 | có — sáng tự bấm “Cập nhật SEO (không AI)” khi muốn áp thật |
| D1 | XONG | MASTER Ver8 có 62 MBT MBA; baseline 3.8 dựng 0 SVG, 3.9 dựng 117 SVG (61 tổn hao + 56 so lõi), 56 SKU có đủ 2 | không |
| D2 | XONG | DB regression tại 800kVA trả [560,630,750,1000,1250,1600] = 3 dưới + 3 trên | không |
| E1 | XONG | Ảnh nhiễu 1200x4000 → WebP 360x1200, 123.4KB ≤150KB | không |
| E2 | XONG | Ảnh test 40x20 EXIF Orientation=6 → output 20x40 đúng chiều | không |
| E3 | XONG | URL/alt/caption có &, ", < đều được escape thành HTML an toàn | không |
| E4 | XONG | 300 workspace: lần index đầu đọc 300 meta; 100 lookup tiếp theo đọc thêm 0 meta | không |
| E5 | XONG | Xvfb: tab legacy không còn trên UI; chỉ còn “Ảnh bài viết (3.9)”; code legacy vẫn giữ nguyên | không |
| E6 | XONG | Production worker nghỉ 5s nhưng Force Stop sau 0.20s → elapsed 0.200s, record thứ hai không chạy | không |
| E7 | XONG | DB tempfile 3 version: active = [(001,0),(002,0),(003,1)]; list active chỉ trả 003; lịch sử vẫn đọc được | không |
| E8 | XONG | README/SPEC/GUI/tab ảnh/4 BAT current strings = 3.9; comment và tài liệu lịch sử không bị sửa giả lịch sử | không |
| E9 | XONG | 2 worker song song, mỗi worker print 80 dòng: queue A=80A/0B, queue B=80B/0A; sys.stdout phục hồi đúng | không |
| E10 | XONG | Callback cố ý ZeroDivisionError → log UI có “LỖI UI callback:” + traceback, không còn nuốt lỗi | không |

- CẦN THỊNH QUYẾT: không có quyết định kiến trúc bắt buộc; sáng chỉ cần chọn có dùng MASTER Ver8 và có bấm lượt “Cập nhật SEO (không AI)” thật hay chưa.
- CHƯA VERIFY SITE THẬT: C6 mới test bằng mock WordPress, chưa POST site thật; Gate 7 schema frontend giữ nguyên theo lệnh cấm và vẫn cần Thịnh View Source khi rảnh.
- KHÔNG LÀM ĐƯỢC: 3 test legacy `test_v495_patch.py`, `test_v498_patch.py`, `test_v499_patch.py` chưa chạy assertion thật vì package không có fixture MASTER legacy mà chúng yêu cầu; runner ghi SKIP, không tính PASS.

---

## KET-QUA-4.0

### KẾT QUẢ SONEALEO ULTRA 4.0

| Việc | Kết quả | Bằng chứng | Thịnh phải làm gì |
| --- | --- | --- | --- |
| 1.1 Định nghĩa họ sản phẩm | XONG | MASTER Ver8 qua production importer: 141 SKU `outline_may_bien_ap`, đếm đúng 11 họ theo hãng + dầu/khô + pha + lõi; số thiếu pha/lõi giữ `không ghi`, không đoán. | không |
| 1.2 Thư mục `_HO/` + 5 ô | XONG | Test tạo `<gốc>/<sheet>/_HO/<family-key>/meta.json`, cùng 5 role ảnh của profile máy biến áp; PASS. | không |
| 1.3 Ảnh riêng thắng ảnh họ | XONG | Mock uploader: SKU 1 upload 2 ảnh họ; SKU 2 cùng họ vẫn tổng 2 call; thêm hero riêng cho SKU 2 thành 3 call, hero riêng thắng còn cận cảnh vẫn lấy họ; PASS. | không |
| 1.4 Màn “Gán ảnh cho họ” | XONG | Xvfb: nút tồn tại, 1 họ giả hiện 1 dòng và đúng 5 slot; regression layout 1366x768 + 1920x1080 đều thấy nút và đủ 5 nhãn; PASS. | không |
| 1.5 Cột Nguồn riêng/họ/trống | XONG | UI test xác nhận cột `Nguồn`; logic test ra `ho` cho fallback, `trong` khi không có, `rieng` khi có override; PASS. | không |
| 2.1 Lọc kho ảnh không AI | XONG | Test 5 file: Laplacian sharp=22396.025, blur=0.224, ngưỡng=80.0; kết quả loại đúng 1 trùng byte + 1 nhỏ + 1 mờ + 1 file rác, giữ 1 ảnh. | không |
| 2.2 Không xoá kho gốc | XONG | Sau test, toàn bộ file nguồn còn nguyên; `_DA_LOC/` chỉ có ảnh đạt, dùng hardlink và fallback copy2; `ORIGINAL_FILES_UNTOUCHED=PASS`. | không |
| 2.3 Báo cáo lọc | XONG | `bao-cao-loc-anh.json`: in=5, image_in=4, out=1, khong_phai_anh=1, trung_byte=1, anh_nho=1, anh_mo=1; PASS. | không |
| 2.4 Chạy không cần gõ lệnh | XONG | Có `LOC-KHO-ANH.bat` + `loc_kho_anh.py`; core lọc đã test thật. BAT Windows chưa thể native-test trong môi trường Linux. | double-click BAT 1 lần để xác nhận Windows mở hộp chọn thư mục |
| 3.1 Mô tả 9 category | XONG | Router production đọc MASTER Ver8 sinh 11 tên; bỏ 2 root `Máy biến áp` + `Thiết bị đo lường điện` còn đúng 9 child category. Ví dụ: dầu=120 SKU/23 mức kVA, khô=21/21. | xem preview nếu muốn chỉnh câu chữ |
| 3.2 Mục lục kVA + internal link | XONG | `Máy biến áp dầu` sinh 23 hàng kVA 1→3200kVA; `Máy biến áp khô` 21 hàng; từng SKU có link `/san-pham/{slug}/`; PASS. | không |
| 3.3 Hard Block category | XONG | Mỗi kVA/cấp điện áp phát ra phải qua `render_phase2.kiem_tra_bia()` trên chính record nguồn; 9 file generate thành công; không sửa/nới Hard Block. | không |
| 3.4 Xuất HTML preview | XONG | Có đúng 9 file trong `category-preview-4.0/`; `category_preview.py` không import requests/ai_wp_adapter/Gemini, không có transport WordPress. | mở 9 HTML để duyệt trước khi tự đưa lên Woo category |
| 4.1 Snippet schema frontend | XONG | `php -l` không lỗi; mock WordPress wp_head đọc đúng `_snl_schema_jsonld` và in `"@type":"Product"`; chưa verify site thật. | dán `WPCode-SCHEMA-SONEALEO.php` vào WPCode, Activate, rồi View Source tìm `"@type":"Product"` |
| 4.2 Ba legacy test thiếu fixture | XONG | Fixture tối thiểu: test_v495=21/21 PASS, test_v498=17/17 PASS, test_v499 sau cập nhật 1 assertion MOF đã lỗi thời=32/32 PASS; không còn SKIP vì thiếu MASTER. | không |
| Đóng gói nhãn release 4.0 | XONG | README/BAT/GUI/tab ảnh hiển thị 4.0; MASTER Ver8 SHA-256 giữ nguyên `b0c0cf00...71498`, ZIP 3.9 gốc giữ nguyên `e7079af3...03e4`. | không |
| QA cuối: extract artifact + targeted regression | XONG | Extract ZIP 4.0: compile PASS; 7 test 4.0/legacy PASS; layout 1366x768 + 1920x1080 đều `inside=true`/đủ 5 nhãn; PHP lint + mock JSON-LD PASS. | không |
| QA cuối: `run_tests.py` toàn bộ | KHÔNG LÀM ĐƯỢC | Runner 65 file không trả summary sau >900s trong môi trường audit; baseline 3.9 dùng cùng `run_tests.py`/`test_v48.py` cũng có hành vi treo dài, nên không ghi PASS giả. | không; đây không chặn bằng chứng riêng của các việc 1.1–4.2 |

---

## KET-QUA-4.1

### KẾT QUẢ SONEALEO 4.1

| Việc | Kết quả | Bằng chứng | Thịnh phải làm gì |
|---|---|---|---|
| BUG-01 / R23 image state theo site | XONG | A=1 upload, B=1 upload; B URL=`b.local`; rerun B không upload | không |
| BUG-02 / R48 SEO-only validation | XONG | synthetic blocker: AI=0, WP=0; Save Draft Gate6 vẫn AI=0/WP=0 | không |
| BUG-03 / R06+R07 runner PASS giả | XONG | no-assert=`[FAIL]`; `test_v35_hang_doi.py` có `FAIL 1` cũng=`[FAIL]` | không |
| BUG-04 / R51 category blocker | XONG | 9 preview: không `1 kV`; sau data fix có `12.7/0.22 kV` + `22/0.22 kV` | không |
| BUG-05 / R15 Dashboard #NAME? | XONG | 50 formula cells có cache số; B5=3387, B8=1340; Dashboard không còn #NAME? | không |
| BUG-06 / R41 WP Media alt/title | XONG | mock POST count=2; `/media/{id}` metadata=true | không |
| BUG-07 / R16 Dashboard phụ kiện | XONG | B8 formula range K2:K1341 cache=1340; importer=1340 | không |
| BUG-08 VNMBA sai điện áp | XONG | VNMBA1P1S=`12.7/0.22 kV`, VNMBA1P2S=`22/0.22 kV`; flag count điện áp profile=0 | không |
| 59-case regression cố định | FAIL | 8 case cũ chuyển PASS nhưng R05 mới FAIL: full `run_tests.py` không kết thúc trong 240s | không |
| Verdict 4.1 | NO-GO | R05 release suite chưa sạch; R55 frontend schema vẫn PARTIAL/site thật chưa verify | có: View Source schema khi tiện |

- CẦN THỊNH QUYẾT: không có quyết định code; R55 cần Thịnh tự View Source site thật như kế hoạch cũ.
- CHƯA VERIFY SITE THẬT: image media alt/title, Woo transport, Product JSON-LD frontend.
- KHÔNG LÀM ĐƯỢC: full suite 4.1 dưới timeout; chuyển sang Giai đoạn 2 để sửa harness, không che bằng tăng timeout.

---

## KET-QUA-4.3.1

### KẾT QUẢ SONEALEO ULTRA 4.3.1

| Việc | Kết quả | Bằng chứng | Thịnh phải làm gì |
|---|---|---|---|
| META Hard Block không vứt cả bài | XONG | QA: META-only fallback PASS; fallback không rỗng; warning persist PASS | Không |
| Hard Block thân bài giữ nguyên | XONG | QA: `dac_diem_html=99kV` vẫn bị chặn PASS | Không |
| `may_tuong_thich` cho 7 SKU vỏ acceptance | XONG | 7/7 derive + prompt + meta Hard Block sạch | Không |
| Rà toàn bộ vỏ trong DB thật đã gửi | XONG | DB thật: 24/24 vỏ hợp lệ; 7/7 giá treo không bị suy diễn | Không |
| Woo Draft contract | XONG trên fake WP | 7/7 request đi endpoint CREATE, `status=draft`, `type=simple` | Windows thật xác nhận khi chạy lại record lỗi |
| Regression tổng | CÓ ĐIỀU KIỆN | Runner in `66 PASS / 0 FAIL / 1 SKIP`, 35.2s; outer Linux invocation không tự thoát sạch sau summary | Không cần chạy lúc batch 4.3 đang hoạt động |

## VERDICT
**GO CÓ ĐIỀU KIỆN cho hotfix production.** Không có POST site thật trong lúc làm bản vá.

## LƯU Ý NGUỒN THẬT
- DB thật đã gửi có **31** dòng tên vỏ/giá treo MBA: **24 vỏ mạ kẽm + 7 giá treo**. Đây là số đọc trực tiếp từ `phase2-du-lieu.db` đã gửi, không phải giả định.
- 24 vỏ đang dùng `outline_vo_may_bien_ap`, không phải `outline_phu_kien`. Vì vậy hotfix sửa đúng outline thực tế và vẫn khai field cho `outline_phu_kien` để không tạo hai luật khác nhau.
- 7 giá treo không có đủ pha + kVA + cặp điện áp viết rõ trong tên, nên 4.3.1 **không đoán** `may_tuong_thich` cho chúng.

## CÁCH ĐỔI BẢN
Không thay file của 4.3 khi batch đang chạy. Khi batch kết thúc hoặc đã Force Stop an toàn: đóng app, backup DB, mở 4.3.1 với DB hiện tại rồi chạy lại các record trạng thái `loi`. Không cần re-import MASTER cho hotfix này vì field tương thích được bóc runtime từ Tên hàng.

---

## KET-QUA-4.4.1.1

### KẾT QUẢ 4.4.1.1 — BUG-C

| Gate | Kết quả | Bằng chứng |
|---|---|---|
| Resolve `wp_id=NULL` theo SKU | PASS MOCK | C1: lookup SKU -> ID 2468 -> persist DB |
| NOT_FOUND khác API ERROR | PASS MOCK | C2/C3 |
| `wp_id` hợp lệ không lookup thừa | PASS MOCK | C4 |
| `wp_id` chết -> invalidate -> SKU -> retry 1 lần | PASS MOCK | C5 |
| Batch `ĐỒNG BỘ WP ID` | PASS MOCK | C6 FOUND=1 / NOT_FOUND=1 / API_ERROR=1 |
| Trạng thái `Đã lên Media` / `Đã gắn vào bài` | PASS MOCK | 5/5 -> Media, mark post -> Attached |
| Image placement cũ | PASS | `test_v441_image_placement.py` PASS |
| Workspace/image regression | PASS | `test_v37_anh.py` 47/47 |
| UI image tab | PASS | `test_v44_ui_logic.py` 8/8 dưới Xvfb |
| BUG-B hotfix regression | PASS | `test_v43_hotfix.py` 10/10 |
| Full `run_tests.py` | CHƯA KÝ | official harness tiếp tục không kết thúc trong phiên chạy; đã tới nhóm `test_v49x`. `test_v48.py` chạy riêng 10/10 PASS. |
| `test_v441_meta_failsoft.py` | PRE-EXISTING FAIL | chạy cả base 4.4.1 lẫn patch đều lỗi `no such table: san_pham_phase2` khi không có production DB; không sửa ngoài scope BUG-C. |
| WordPress real MBT1P25A2608 | CHƯA KÝ | không có credential/site runtime trong môi trường QA; phải verify trên Windows thật theo checklist dưới. |

## CHECK REAL BẮT BUỘC
1. Chọn `MBT1P25A2608`, DB đang `wp_id=NULL` nhưng bài đã có trên WordPress.
2. Bấm `Cập nhật ảnh lên WordPress`.
3. Log phải có lookup SKU và phục hồi WP ID, không tạo product mới.
4. UI chuyển `Đã gắn vào bài 5/5` sau khi body+gallery thành công.
5. Mở bài thật, xác nhận featured/gallery/body đúng 5 ảnh.
6. Tắt/mở app, WP ID vẫn còn trong DB và bấm lại không upload Media trùng.

## VERDICT
**Patch BUG-C đã qua mock/regression mục tiêu. Chưa ký E2E WordPress real cho tới khi case MBT1P25A2608 được chạy trên máy công ty.**

---

## KET-QUA-4.4.1.2

### KẾT QUẢ 4.4.1.2 — DUAL IMAGE DELIVERY

- PASS: 5 ảnh vẫn được gắn Woo `images[]`, ảnh đầu là featured.
- PASS: 5 ảnh đồng thời xuất hiện trong body nếu workspace có đủ 5 role.
- PASS: bài cũ mất marker vẫn được chèn ảnh bằng fallback section semantic, không cần render lại, không gọi AI.
- PASS: re-run thay URL ảnh cũ bằng URL mới, không nhân đôi figure do tool chèn.
- PASS: BUG-C lookup WP ID theo SKU vẫn giữ nguyên.
- PASS: ENV, `render_phase2.py`, `autopost.py`, `ai_wp_adapter.py`, prompt logic không đổi ngoài wiring marker body ở `giao_dien_2_5.py`.

## Production Gate
Chưa ký PASS production cho tới khi test một bài thật: bấm **Cập nhật ảnh lên WordPress** → gallery có 5 ảnh → body có đủ 5 ảnh → refresh lần 2 không nhân đôi.

---

## KET-QUA-4.4.1.3

### KẾT QUẢ 4.4.1.3 — IMAGE PRODUCTION HOTFIX

## Verdict hiện tại

**CODE/REGRESSION: PASS**  
**WINDOWS/LIVE PRODUCTION: CHƯA PASS — cần user xác minh trên site thật.**

Không có POST live từ môi trường test này.

## Kiểm tra đã chạy

| Test | Kết quả |
|---|---:|
| `python -m py_compile` toàn bộ 43 file Python root | PASS 43/43 |
| `tests/test_v4413_partial_watermark.py` | PASS 19 / FAIL 0 |
| `tests/test_v4412_dual_image_delivery.py` | PASS 12/12 |
| `tests/test_v4411_bugc_wp_id_sync.py` | PASS 15/15 |
| `tests/test_v37_anh.py` | PASS 47/47 |
| `tests/test_v44_release.py` | PASS 12/12 |
| `tests/test_v441_image_placement.py` | PASS 12/12 |
| `tests/test_v441_resume_tracker.py` | PASS 5/5 |
| `tests/test_v43_hotfix.py` | PASS 10/10 |
| `tests/test_v44_tracker_logic.py` | PASS 6/6 |
| `xvfb-run -a python tests/test_v44_ui_logic.py` | PASS 8/8 |

## Test không được tính regression failure của bản vá

`tests/test_v441_meta_failsoft.py` dừng ngay với `sqlite3.OperationalError: no such table: san_pham_phase2`. Chạy cùng test trên **4.4.1.2 gốc** cho đúng lỗi y hệt, trước khi đi vào logic cần test. Vì vậy đây là fixture/environment defect có sẵn, không phải regression 4.4.1.3. Không tăng timeout và không sửa ngoài scope để làm xanh giả.

## Production contract cần xác minh trên Windows/live

1. Chọn SKU đã từng có ảnh nhưng local giữ media ID bị xoá/stale.
2. `Cập nhật ảnh lên WordPress` phải giữ/gắn các ảnh còn hợp lệ, không làm cả bộ chết vì một ID stale.
3. Slot stale phải bị xoá local delivery/cache và lần kế tiếp upload lại được.
4. Một file hỏng/GIF lỗi trong 5 slot không được chặn 4 ảnh tốt vào gallery + body.
5. Ảnh mới upload có watermark nhẹ; ảnh canonical/local gốc không bị watermark.
6. Chạy lần hai không nhân đôi body figure và không upload lại asset có cùng hash + watermark signature.
7. Khi đủ 5 ảnh hợp lệ: Woo gallery đủ 5, body đủ 5.

Chỉ sau khi các bước trên thấy đúng trên trang thật mới ký **PRODUCTION PASS**.

---

## KET-QUA-4.4.1.4

### KẾT QUẢ 4.4.1.4 — WATERMARK + REUSE POLICY

## Regression mới
- `tests/test_v4414_watermark_reuse.py`: **16/16 PASS**
  - domain watermark
  - hotline watermark
  - 2 dòng domain + phone
  - template `{domain}` / `{phone}`
  - không đoán hotline site khác
  - watermark chỉ ở upload bytes, ảnh nguồn không đổi
  - config Website đọc/lưu hotline
  - cùng một ảnh source dùng cho 3 SKU
  - reuse counter chỉ đếm, không chặn
  - 3 SKU upload thành công với filename riêng
  - best-effort contract còn tồn tại

## Regression image/WP cũ
- `test_v4413_partial_watermark.py`: **19/19 PASS**
- `test_v4412_dual_image_delivery.py`: **12/12 PASS**
- `test_v4411_bugc_wp_id_sync.py`: **15/15 PASS**
- `test_v37_anh.py`: **47/47 PASS**
- `test_v441_image_placement.py`: **12/12 PASS**
- `test_v44_release.py`: **12/12 PASS**
- `test_v441_resume_tracker.py`: **5/5 PASS**
- `test_v43_hotfix.py`: **10/10 PASS**
- `test_v44_tracker_logic.py`: **6/6 PASS**

## Regression cấu hình/UI
- `test_v34_that_ui.py` qua Xvfb: **8/8 PASS**
- `test_v37_1_patch.py` qua Xvfb: **7/7 PASS**
- `test_v35_idempotency.py` qua Xvfb: **11/11 PASS**
- `test_v46.py` qua Xvfb: **20/20 PASS**

## Compile
- Root Python modules: **43/43 compile PASS**

## Production gate
**CHƯA PRODUCTION PASS.**

Cần Windows/site thật xác nhận tối thiểu:
1. Vào Cấu hình Website, điền `Hotline watermark` một lần.
2. Gán cùng một ảnh cho 2–3 SKU khác nhau và cập nhật WordPress.
3. Xác nhận ảnh upload có 2 dòng watermark domain + hotline.
4. Xác nhận mỗi SKU vẫn có featured/gallery/body đúng, không bị chặn vì reuse.
5. Tạo case 1 slot lỗi + các slot còn lại tốt, xác nhận ảnh tốt vẫn vào bài.

---

## KET-QUA-4.4

### KẾT QUẢ — SONEALEO ULTRA 4.4

| Việc | Kết quả | Bằng chứng | Thịnh phải làm gì |
|---|---|---|---|
| Gộp 4.3.1 | XONG | `qa/test_v431_meta_hardblock.py`: 5 PASS / 0 FAIL | Không |
| A1 Ẩn ô ảnh trống | XONG | `test_v44_release.py`: placeholder/comment/`URL_ANH` = 0; 3 ảnh thật → 3 `<figure>` | Kiểm 1 bài thật sau khi cài |
| A2 Comment ảnh | XONG | Placeholder/comment hướng dẫn không còn được emit, nên không còn comment nhiều dòng để wpautop bẻ | Không |
| B1 Slug UPDATE | XONG | Fake Woo UPDATE `/products/321` nhận `slug` mới; SEO-only cũng gửi `slug` | Chạy **Cập nhật SEO (không AI)** một lượt cho các bài 4.3 đã đăng nếu muốn đổi URL ngay |
| C1–C6 Tab Ảnh | XONG logic | Search realtime, sort, Ctrl+F, STT, family, multi-select; UI logic `8 PASS / 0 FAIL`; MASTER Ver8 test ra 11 họ | **Visual Windows 1366×768 chưa verify trong môi trường GPT** |
| C1–C8 Tab Theo dõi | XONG logic | SQLite fixture: `6 PASS / 0 FAIL`; KPI `3 cần / 2 đăng / 1 còn`, filter lỗi không làm KPI sai | Visual Windows thật kiểm sau khi cài |
| C7 Lỗi đầy đủ | XONG | Nút `Xem lỗi` đọc nguyên `loi`; right-click cell copy nguyên value | Không |
| C8 Tổng quan | XONG | KPI lấy `selected=1` + record `da_dang` có wp_id, độc lập filter tìm/trạng thái | Không |
| D1 Copy | XONG | Right-click Copy cho `Treeview`, `Label`, `TLabel` | Không |
| D2 File ảnh | XONG | Picker + workspace nhận JFIF/WebP/HEIC/BMP/AVIF; thêm `pillow-heif` vào requirements | Lần cài/update dependency cho phép pip cài `pillow-heif` |
| D3 Google Images | XONG | Query MBA thật: `máy biến áp dầu MBT 750kVA 3 pha`; profile khác dùng tên sản phẩm | Không |
| D4 Downloads | XONG | Picker ảnh mở `~/Downloads` nếu thư mục tồn tại | Không |
| 59 regression cố định | 58 PASS / 0 FAIL / 1 PARTIAL | Không case PASS của 4.3 chuyển FAIL; R55 vẫn PARTIAL vì schema frontend cần View Source site thật | Khi rảnh verify schema View Source |
| Full suite | XONG | 70 file = 69 PASS / 0 FAIL / 1 SKIP; SKIP là UI Hàng đợi do Linux thiếu `tksheet`, core test 14 PASS / 0 FAIL | Không |
| ZIP state safety | XONG | Final archive scan: không `phase2-du-lieu.db`, không `cau-hinh.env`, không thư mục `anh`/workspace ảnh | Giải nén đè lên folder 4.3 sau khi batch dừng |

## VERDICT

**GO CÓ ĐIỀU KIỆN.** Code/regression sạch; điều kiện còn lại là visual UI 4.4 trên Windows thật và R55 schema frontend.

## SLUG 245 BÀI ĐÃ ĐĂNG

Chỉ cài 4.4 **không tự đổi URL các bài đã tồn tại**. Lượt render/update bình thường bằng 4.4 sẽ gửi slug mới, nhưng rẻ nhất là chạy riêng **Cập nhật SEO (không AI)** để sửa title/slug/Rank Math mà không render lại body và không gọi Gemini.

## ZIP OVERLAY

ZIP 4.4 được đóng để dùng như gói code overlay. Nó không chứa DB thật, env thật hoặc thư mục ảnh, nên giải nén đè không ghi đè ba loại state đó.

---

## KET-QUA

| Gate | Kết quả              | Bằng chứng                      | Việc Thịnh phải làm |
| ---- | -------------------- | ------------------------------- | ------------------- |
| 1    | XONG | `test_v35_idempotency.py` PASS 1/1; env SHA trước/sau `b76d63c...bee87`, DB SHA trước/sau `d277f5ac...79e31` | không |
| 2    | XONG | A=`d3fce475...64e281`, B=`512e4308...7eb809`; đảo thứ tự cột/key dynamic = A | không |
| 3    | XONG | static worker scan `BAD=[]`; `test_v34_that_ui.py` 8/8 PASS; không còn output `main thread is not in main loop` | không |
| 4    | XONG | mock WP: `POST_CALLS=2`; cùng hash reuse ID 101, cùng tên nhưng hash mới upload ID 102 | không |
| 5    | XONG | mock E2E: `MEDIA_POSTS=1`, `MEDIA_BYTES=608`, `HAS_IMG=True`, media ID 501; lượt 2 không re-upload | không |
| 6    | XONG | record `nghi_van_dien_ap=True`: `AI_CALLS=0`, `WP_CALLS=0`, DB `STATE=loi` với `BLOCKED` | không |
| 7    | FAIL | category mock gửi `[{'id':123}]`, schema SKU/description đúng; grep production `PRODUCTION_CONSUMER_FILES=0`, chưa chứng minh View Source | có |
| 8    | FAIL | compile toàn project PASS; 7/7 + 8/8 + 7/7 + 23/23 test chọn lọc PASS, nhưng full runner >300s và `test_v37_batch_real.py` >100s | không |

- CẦN QUYÊN QUYẾT: Gate 7 — xác nhận hook/plugin frontend nào đọc `_snl_schema_jsonld`, hoặc cho phép verify trên staging thật.
- CHƯA VERIFY TRÊN SITE THẬT: Gate 4 cache/media_id ảnh; Gate 5 ảnh workspace → bài; Gate 7 category ID và Product schema frontend.
- KHÔNG LÀM ĐƯỢC: Gate 7 — package không có consumer/hook render schema ra frontend và chưa verify site thật; Gate 8 — bộ test chưa chạy sạch vì `test_v37_batch_real.py` vẫn timeout/treo sau T1.

---

## REGRESSION-4.1

### REGRESSION MATRIX — SONEALEO ULTRA 4.0 RED TEAM

> Kết quả được lấy từ artifact 4.0, MASTER Ver8, source production hoặc external mocks/fuzz. Không POST site thật.

| ID | Khu vực | Case | Kết quả | Bằng chứng / nguồn |
|---|---|---|---|---|
| R01 | Artifact | SHA-256 artifact cố định | PASS | `6428e30c...3499b25d` — sha256sum ZIP |
| R02 | Artifact | ZIP không cần source dev ngoài artifact để compile | PASS | compileall exit0 — extract sạch |
| R03 | Artifact | Python compile toàn bộ | PASS | `python -m compileall -q .` exit0 |
| R04 | GUI | Smoke launch 4.0 | PASS | title `SONEALEO ULTRA · Ver 4.0`, 1280x800 — Xvfb |
| R05 | Suite | Full runner kết thúc dưới timeout | **FAIL** | 4.1 `run_tests.py` không kết thúc trong 240s; diagnostic cho thấy harness/group execution còn treo — nguồn: runner thật |
| R06 | Suite | Silent exit0 không được PASS | PASS | synthetic no-assert bị `[FAIL]` — runner 4.1 thật |
| R07 | Suite | Test in FAIL counter phải fail suite | PASS | `test_v35_hang_doi.py` output `FAIL 1`, exit0 nhưng runner 4.1 phân loại `[FAIL]` |
| R08 | Data checksum | Dynamic A→B đổi checksum | PASS | `d3fce475...` → `512e4308...` — production function |
| R09 | Data checksum | Reorder columns giữ checksum | PASS | reorder=A — production function |
| R10 | MASTER | 4 product sheets ngoài MBA không bị value-edit Ver7→Ver8 | PASS | Cap=0, Tu=0, PhuKien=0 — raw XLSX diff |
| R11 | MASTER | 19 A2608 source flag đổi đúng | PASS | 19 `suy_tu_tieu_chuan_khac` — col AW |
| R12 | MASTER | MBT3P180A2608 = noi_suy | PASS | col AW — MASTER Ver8 |
| R13 | MASTER | 20 A2608 Io vẫn blank | PASS | cols U/AN blank — MASTER Ver8 |
| R14 | MASTER | Nhật ký Ver8 ghi B3-B5 | PASS | sheet `00_Nhat_Ky_Sua_Loi` rows 235+ |
| R15 | MASTER | Dashboard cache giữ numeric valid | PASS | 50 formula cells được dựng lại; Dashboard B5:F8 numeric, raw XLSX có formula+cache |
| R16 | MASTER | Dashboard accessory count = importer | PASS | B8 cache=1340, formula range K2:K1341; production importer=1340 |
| R17 | Family | Đếm family từ production record | PASS | 141 SKU → 11 họ — importer + `ho_san_pham()` |
| R18 | Family | Family key normalization collision | PASS | 0 collision — production key sweep |
| R19 | Family | Mọi transformer nhận family fallback | PASS | 141/141 — external family test |
| R20 | Family | Private image override family | PASS | 11/11 families — external family test |
| R21 | Family | Same-site rerun không reupload | PASS | uploader calls 1→1 — fake uploader |
| R22 | Family | Same filename, bytes khác reupload | PASS | state `lech`, ID 101→102 — hash test |
| R23 | Family | Site B không reuse media site A | PASS | `CROSS_SITE_CALLS_A 1 B 1`; B URL=`https://b.local/601.webp`; rerun B không upload |
| R24 | Family E2E | 2 SKU cùng họ dùng 1 upload | PASS | media=1, products=2, attachment=2 — production worker mock |
| R25 | Image E2E | Private workspace → bytes→media→img→attach | PASS | media_id=501, `<img>` true, rerun no upload — fake WP |
| R26 | Family UI | Màn family có button + 5 slot | PASS | v40 UI test — Xvfb |
| R27 | Layout | 1366x768 button visible/full labels | PASS | Xvfb geometry/screenshot test |
| R28 | Layout | 1920x1080 button visible/full labels | PASS | Xvfb geometry/screenshot test |
| R29 | UI | Cột Nguồn tồn tại | PASS | v40 UI/source-column test |
| R30 | Filter | Duplicate byte loại đúng | PASS | reason `trung_byte=1` — fuzz report |
| R31 | Filter | 799px short edge bị loại | PASS | `anh_nho` — fuzz fixture |
| R32 | Filter | 800px boundary được giữ nếu sharp | PASS | sharp800 kept — fuzz fixture |
| R33 | Filter | 801px được giữ nếu sharp | PASS | sharp801 kept — fuzz fixture |
| R34 | Filter | Blur bị loại | PASS | variance 0.0 → `anh_mo` — fuzz report |
| R35 | Filter | Fake/truncated/non-image bị loại | PASS | `khong_phai_anh=3` — fuzz report |
| R36 | Filter | PNG alpha hợp lệ không bị loại | PASS | alpha.png kept — fuzz report |
| R37 | Filter | Rerun không tự quét `_DA_LOC` | PASS | rerun total=9, kept=3 — external test |
| R38 | Compression | 1200x4000 đạt <150KB | PASS | 360x1200, 123.7KB — production function |
| R39 | EXIF | Orientation được transpose | PASS | output 1200x900 — EXIF fixture |
| R40 | HTML image | Escape URL/alt | PASS | `&amp;`, `&quot;`, `&lt;` — production HTML output |
| R41 | WP Media | Attachment alt/title được POST | PASS | mock `POST_COUNT 2`, `/media` + `/media/77`, metadata POST=true |
| R42 | SEO | Target count production | PASS | 150 = 141 transformer + 9 MOF — importer + target rules |
| R43 | SEO | Title duplicate | PASS | 0 duplicate groups — full target sweep |
| R44 | SEO | Slug duplicate | PASS | 0 duplicate groups — full target sweep |
| R45 | SEO | Focus keyword duplicate | PASS | 0 duplicate groups — full target sweep |
| R46 | SEO | Rank Math title <=60 | PASS | max=60, over=0 — full target sweep |
| R47 | SEO | Description <=160 | PASS | max=117, over=0 — full target sweep |
| R48 | SEO validation | Blocked record không vào SEO transport | PASS | synthetic blocked row SEO worker: AI=0, WP=0; VNMBA source rows sau data fix tự hết flag |
| R49 | Category | Xuất đúng 9 landing categories | PASS | source 11 minus 2 roots = 9 — MASTER + generator |
| R50 | Category | kVA TOC/link exact, no duplicate href | PASS | oil 120 links/23 levels; dry 21/21 — parsed HTML |
| R51 | Category validation | Blocked voltage không aggregate | PASS | 9 previews: không còn `1 kV`; có `12.7/0.22 kV` và `22/0.22 kV` sau data fix |
| R52 | Charts | MBT chart generation từ MASTER | PASS | MBT=62, SVG total=117 — v39 production test |
| R53 | Comparison | 3 dưới + 3 trên quanh 800kVA | PASS | `[560,630,750,1000,1250,1600]` — production query test |
| R54 | Validation posting | `nghi_van_dien_ap` chặn AI/WP | PASS | AI=0, WP=0, state=blocked/error — gate6 mock |
| R55 | Woo/schema local | Category ID + local schema + PHP syntax | PARTIAL | payload ID đúng; `php -l` sạch; frontend site thật chưa verify |
| R56 | Legacy | test_v495 fixture | PASS | 21/21 — direct test |
| R57 | Legacy | test_v498 fixture | PASS | 17/17 — direct test |
| R58 | Legacy | test_v499 fixture | PASS | 32/32 — direct test |
| R59 | Thread | v34 + v37 real batch, 3 fresh rounds | PASS | 6/6 subprocess PASS, không Tk main-loop error |

## TỔNG KẾT MATRIX

- Tổng case: **59** — **nguồn: số dòng R01–R59 trong bảng này**.
- FAIL hiện tại: **1 case** (`R05`) — **nguồn: runner 4.1 không kết thúc trong 240s**.
- 8 case FAIL của 4.0 đã chuyển PASS: `R06,R07,R15,R16,R23,R41,R48,R51`.
- R55 vẫn PARTIAL vì frontend schema cần Thịnh View Source site thật.
- PASS/FAIL count không được dùng thay cho mức độ nghiêm trọng. R23 và R48 là release-blocking đối với multi-site/bulk workflow.
- Site thật chưa verify: R55 frontend schema; toàn bộ HTTP WordPress trong audit là mock.

