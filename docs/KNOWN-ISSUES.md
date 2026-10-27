# KNOWN ISSUES — Ver 5.7 — cập nhật 22/08/2026

> Header cũ ghi "Ver 4.4.1.6" trong khi code chạy 5.4. Mục này viết lại đầu
> danh sách; phần lịch sử bên dưới giữ nguyên, không xoá.
>
> Quy ước: chỉ ghi lỗi **đã xác minh**. Nghi ngờ để riêng mục B và ghi rõ
> là nghi ngờ. Mỗi mục có **mức tin cậy**.

## MỞ — KỶ LUẬT VẬN HÀNH (không sửa được bằng code trong bản này)

- **[DATA] `record_id` gắn với SỐ DÒNG Excel → chỉ được APPEND, cấm chèn giữa.**
  Mức tin cậy: **cao** (đo được, không suy đoán).

  Khoá định danh hiện tại (`nhap_phase2.py:159`):

      record_id = f'{profile_id}::{source_sheet}::{source_row}::{sku}'

  `source_row` là **số thứ tự dòng trong sheet**. Hệ quả đã mô phỏng trên
  sheet 598 dòng: **chèn 1 dòng ở vị trí 100 → 500 record_id không còn khớp**.
  `db_phase2.chuyen_bai_sang_dataset_moi()` đối chiếu bài đã đăng theo
  `record_id`, nên 500 bài đó thành **mồ côi**: `dashboard()` JOIN không ra,
  `wp_id`/`site`/`mau` về None, và **không có cảnh báo nào** — app chạy êm,
  chỉ lộ khi bấm đúng một nút.

  Đây KHÔNG phải giả thuyết. Docstring của chính hàm đó ghi sự cố thật
  **13/08/2026: 245 bài mồ côi, mất nửa ngày mới truy ra**. Nguyên nhân gốc
  vẫn còn nguyên trong khoá.

  **QUY TẮC BẮT BUỘC khi sửa MASTER:**
  1. Dòng mới **luôn APPEND xuống cuối sheet**. Không `Insert Row`.
  2. Không sắp xếp lại (`Sort`) sheet đã import.
  3. Không xoá dòng — cần bỏ thì đánh dấu ở cột trạng thái.
  4. Đổi SKU của 1 dòng = 1 bài mồ côi. Đổi SKU hàng loạt phải chấp nhận
     đăng lại toàn bộ số đó.
  5. Sau mỗi lần import, đọc báo cáo `chuyen_bai_sang_dataset_moi` — mục
     `mo_coi` phải là **0**. Khác 0 là đã vi phạm 1 trong 4 điều trên.

  **Rủi ro sắp tới:** 336 dòng MBA thiếu spec + 446 SKU trung thế chờ ghép
  `catalogue-mv-cadivi.xlsx`. Cả hai đợt này phải append, không chèn.

  **Sửa tận gốc (chưa làm, ~1 ngày):** đổi khoá sang `profile_id::sku`
  (SKU vốn đã unique — `nhap_phase2.py` đã có sẵn bộ đếm `sku_trung`), kèm
  script migrate `bai_viet_phase2` + `article_jobs` của DB hiện có. Chưa
  làm vì né được bằng kỷ luật, và migrate sai thì mất toàn bộ liên kết bài.

- **[WOO] Lỗi 459 SKU sai thuộc tính `Cấp điện áp` KHÔNG do tool này.**
  Mức tin cậy: **cao**. Payload gửi WooCommerce (`ai_wp_adapter.dang_woo_that`)
  chỉ gồm: `name, type, status, description, short_description, sku, slug,
  categories, meta_data`. **Không có `attributes`, không có `images`.**
  Tool chưa từng ghi attribute nào lên Woo, nên `22/0,4 kV` bị tách thành
  `22/0` + `4 kV` phải đến từ đường khác (CSV import / plugin / nhập tay).
  **Sửa trong SONEALEO là sửa nhầm chỗ** — truy nguồn trước.

- **[ANH] `sweep_rac` luật `gia_list_lo` neo RẤT hẹp — đúng chủ ý, nhưng
  đừng kỳ vọng quá.** Mức tin cậy: **cao**. Nó chỉ khớp đúng dạng
  `' · <số> ₫'` ngay trước `</small>`. Đã kiểm: `'· 82.650.000 VNĐ'`,
  `'- 82.650.000 ₫'`, và cùng chuỗi trong `<span>` đều **SÓT**. Neo hẹp là
  để không xoá nhầm, không phải để quét sạch. Muốn biết còn dạng rò rỉ nào
  thì phải grep HTML thật trên WordPress, không suy từ code được.

## MỞ — cần Thịnh quyết, KHÔNG sửa được bằng code

- **[DATA] 17 SKU trùng trong MASTER** (12 cáp, 1 tủ/đóng cắt, 4 phụ kiện).
  Tool đã gán `publish_sku` riêng để khỏi đè nhau trên WooCommerce, nhưng
  cần xác nhận có phải lỗi nhập liệu không. Tin cậy: cao.
- **[DATA] 19 SKU gán sai họ sản phẩm.** VD `ABBLA12` "Chống sét van 12KV -
  ABB" đang ở `outline_tu_dong_cat`, đáng lẽ `outline_phu_kien`.
  **Nguy hơn lỗi văng**: bài vẫn ra êm, chỉ là viết sai bản chất sản phẩm.
  Tool cố ý KHÔNG tự sửa. Tin cậy: cao.
- **[DATA] Caveat QĐ 2608 mâu thuẫn.** Po=31W/Pk=570W lấy từ TCCS 10:2021
  hay QĐ 2608? Chỉ nhóm SKU A2608. **KHÔNG được xoá caveat bằng plugin
  replace** — đó là giấu lỗi, không phải sửa lỗi. Sửa ở MASTER
  (`nguon_tieu_chuan_vien_dan`) + `kien_thuc_bien_thien.py:276`.
  *Ghi chú 20/08:* Ver 4.6.2 đã thêm luật `caveat_a2608` vào `sweep_rac.py:65`
  để **dọn khỏi bài đã đăng**. Đó là dọn hiện tượng, **không thay thế việc
  trả lời câu hỏi gốc**. Nguồn số vẫn chưa xác định.
- **[DATA] Bảo hành và CO/CQ = 0/245.** Ver 5.4 đã khai sẵn 2 field ở
  `profiles.py:274`, MASTER chưa có cột. Chỉ thiếu số, không thiếu code.

## MỞ — rủi ro kỹ thuật

- **[TEST] Ver 5.4 chạy không có test.** `tests/` dừng ở `test_v53_patch.py`.
  Serper.dev + 10 cột catalogue MBA chưa có test nào. Tin cậy: cao.
- **[DATA] `du_lieu_bat_buoc` chưa tồn tại.** Grep toàn source: 0 kết quả.
  Outline báo giá trống giá vẫn sinh bài bình thường. Tin cậy: cao.
- **[ARCH] `giao-dien.py` = 5.336 dòng**, tăng 20% kể từ lúc ghi nợ ở 4.4.1.7
  (4.457). Ngưỡng kích hoạt xét lại: **6.000 dòng**.

## MỞ — chưa chốt scope (giữ nguyên từ 4.4.1.5, chưa tái kiểm ở 5.4)

- `enhance.khoang_trong_noi_dung` in ghi chú nội bộ ra cho khách
  (`enhance.py:398-402`) — nhồi `<ul>` vào cuối `huong_dan_chon_html` không có
  câu dẫn, khách đọc thành lời hứa cụt.
- `goc_nhin_bundle_cheo` giữ giọng chào hàng của đối thủ; trùng chức năng với
  `phu_kien_di_kem.py` nhưng bản kém hơn.
- Badge "Khảo sát thị trường" sai bản chất — là tổng hợp nội dung đối thủ.

**Tin cậy cả 3 mục: thấp** — đọc từ doc 4.4.1.5, chưa đối chiếu lại với code 5.4.
Ai xử cụm này thì grep lại trước, đừng tin dòng này.

## ĐÃ ĐÓNG — xác minh lại ngày 20/08/2026 bằng cách đọc code

| Từng ghi là lỗi | Thực tế | Bằng chứng |
|---|---|---|
| `thinkingConfig` chưa vào request thật | đã nối, có fallback 400 | `autopost.py:496,509-523` |
| HTML từ AI chưa sanitize | đã có `bleach.clean` | `render_phase2.py:243-283` |
| `MODEL_GEMINI` trỏ model đã chết | mặc định `gemini-3.6-flash`, 3 nơi khớp nhau | `autopost.py:68` |
| Rò `gia_list` ra HTML công khai | vá ở 4.6.2 + luật dọn `gia_list_lo` | `sweep_rac.py:55` |
| Bài đã có `wp_id` bị bỏ qua vĩnh viễn | vá ở 5.3 | `giao-dien.py:1907` |
| Ô "Nghỉ giữa 2 bài" không được đọc | vá ở 5.1 | `giao-dien.py:2197` |

## KHÔNG PHẢI LỖI — đừng sửa

- **Hard Block chặn `1kVA`**: guard chạy ĐÚNG, ngăn bài sai công suất.
  Tắt nó là mở cửa cho nội dung sai.
- **403 khi upload**: host chặn theo tốc độ. 4.4.1.6 đã tự retry.
- **Gemini timeout / 503**: phía Google, transient.
- **`giao-dien.py` God Class**: cố ý không refactor (xem TIEN-DO.md mục C).
- **Nhánh RMU Ver 1/Ver 2** không dùng nhưng còn trong code — chạy được thì để yên.

---
---

# KNOWN ISSUES — cập nhật 13/08/2026 (Ver 4.4.1.6)

## MỞ — cần Thịnh quyết, KHÔNG sửa được bằng code
- **[DATA] 17 SKU trùng trong MASTER** (12 cáp điện, 1 tủ/đóng cắt,
  4 phụ kiện). Tool đã gán `publish_sku` riêng để khỏi đè nhau trên
  WooCommerce, nhưng cần xác nhận đây có phải lỗi nhập liệu không.
- **[DATA] 19 SKU gán sai họ sản phẩm.** Ví dụ `ABBLA12` "Chống sét van
  12KV - ABB" đang ở `outline_tu_dong_cat`, đáng lẽ `outline_phu_kien`.
  **Nguy hơn lỗi văng**: bài vẫn ra êm, chỉ là viết sai bản chất sản phẩm.
  Tool cố ý KHÔNG tự sửa.
- **[DATA] Caveat QĐ 2608 mâu thuẫn.** Po=31W/Pk=570W lấy từ TCCS 10:2021
  hay QĐ 2608? Chỉ nhóm SKU A2608. **KHÔNG được xoá caveat bằng plugin
  replace** — đó là giấu lỗi, không phải sửa lỗi.

## MỞ — chưa chốt scope
- `enhance.khoang_trong_noi_dung` in ghi chú nội bộ ra cho khách
  (`enhance.py:398-402`).
- `goc_nhin_bundle_cheo` giữ giọng chào hàng của đối thủ; trùng chức năng
  với `phu_kien_di_kem.py` nhưng bản kém hơn.
- Badge "Khảo sát thị trường" sai bản chất.

## KHÔNG PHẢI LỖI — đừng sửa
- **Hard Block chặn `1kVA`**: guard chạy ĐÚNG, ngăn bài sai công suất.
  Tắt nó là mở cửa cho nội dung sai.
- **403 khi upload**: host chặn theo tốc độ. 4.4.1.6 đã tự retry.
- **Gemini timeout / 503**: phía Google, transient.

## ĐÃ ĐÓNG 13/08/2026
- ~~Ô chờ ảnh lộ hướng dẫn chụp nội bộ ra trang khách~~ → 4.4.1.5
- ~~DB rỗng html thì bó tay~~ → 4.4.1.6 mục 1
- ~~403 bung thẳng ra mặt người dùng~~ → 4.4.1.6 mục 2
- ~~Log 403 cắt ở 200 ký tự~~ → 4.4.1.6 mục 3 *(bug tồn đọng)*
- ~~Không GET verify sau khi gắn ảnh~~ → 4.4.1.6 mục 4 *(bug tồn đọng)*
- ~~Ảnh đại diện bị thay ngầm~~ → 4.4.1.6 mục 5 *(bug tồn đọng)*
- ~~Copy `.db`/`.env` tay giữa các thư mục version~~ → 4.4.1.6 mục 7

---

# KNOWN ISSUES — cập nhật 13/08/2026 (Ver 4.4.1.5)

## MỞ — chặn bỏ noindex
- **[DATA] Caveat QĐ 2608 mâu thuẫn.** Bảng thông số in *"điền theo TCCS
  10:2021/EVN, **chưa đối chiếu** QĐ 2608/QĐ-EVN SPC"* trong khi tiêu đề
  sản phẩm ghi QĐ 2608; cuối cùng bài lại có *"(Nguồn: MASTER, số quy
  chuẩn/catalogue **đã đối chiếu**.)"*. Hai câu chửi nhau trên cùng trang.
  Câu hỏi thật: **Po=31W / Pk=570W lấy từ văn bản nào, hai văn bản có cùng
  số không?** Chỉ dính nhóm SKU A2608. Sửa ở MASTER
  (`nguon_tieu_chuan_vien_dan`) + `kien_thuc_bien_thien.py:276`.
  **KHÔNG được xoá caveat bằng plugin replace** — đó là giấu lỗi.

## MỞ — chưa chốt scope
- **[UX] `enhance.khoang_trong_noi_dung` in ra cho khách.** Đây là *khoảng
  trống nội dung phát hiện từ site đối thủ* (ghi chú "cần viết bài này"),
  đang nhồi thẳng `<ul>` vào cuối `huong_dan_chon_html` **không có câu
  dẫn** — khác 2 khối kia đều có `<p><strong>`. Khách đọc thành lời hứa
  cụt: *"Tài liệu hướng dẫn xử lý khi thiết bị có dấu hiệu quá nhiệt"*.
  (`enhance.py:398-402`)
- **[UX] `goc_nhin_bundle_cheo` giọng người bán.** *"Bán kèm bộ lọc ẩm
  chuyên dụng"* — scrape từ đối thủ, giữ nguyên giọng chào hàng của họ,
  thành cam kết Lotech có bán. Trùng chức năng với `phu_kien_di_kem.py`
  (cross-sell từ MASTER thật, có mã SKU + giá) nhưng bản kém hơn.
- **[UX] Badge "Khảo sát thị trường"** sai bản chất — là tổng hợp nội dung
  đối thủ, không phải khảo sát. Chờ chốt 2 mục trên rồi tính lại.

## ĐÃ ĐÓNG 13/08/2026
- ~~Ô chờ ảnh lộ hướng dẫn chụp nội bộ ra trang khách~~ → Ver 4.4.1.5,
  `sweep_rac.py` + nút Dọn rác + xoá `khoi_anh.O_ANH`.

---

# Lỗi đã biết — Ver 3.6.4 (2026-08-08)

Chỉ ghi lỗi ĐÃ XÁC MINH bằng cách chạy thật. Không ghi lỗi nghi ngờ.

## A. Lỗi môi trường test (không phải lỗi tool)

4 file test fail khi chạy headless trên Linux, đúng y hệt bản 3.3 chưa vá
— tức KHÔNG phải do Ver 3.5 gây ra:

| File | Nguyên nhân |
|---|---|
| `test_v34_that_ui.py` | `RuntimeError: main thread is not in main loop` |
| `test_v37_1_patch.py` | như trên |
| `test_v37_batch_real.py` | như trên |
| `test_v39_article_jobs.py` | như trên |

**Test chập chờn (flaky)**: `test_round2_ui_smoke.py::R2-10.B` fail khoảng
2/4 lần, CẢ TRÊN BẢN NỀN CHƯA VÁ. Lỗi focus của Tkinter dưới Xvfb, không
liên quan tới code nghiệp vụ. Chạy lại là qua.

Đây là đặc thù Tkinter chạy dưới Xvfb, chưa xác nhận có tái hiện trên
Windows hay không. **Cần Thịnh chạy `run_tests.py` trên máy thật để kết
luận.** Mức tin cậy hiện tại: vừa.

## B. Nghi ngờ chưa xử

1. **Bộ đếm batch có thể sai.** `test_v37_batch_real` in ra
   "245/245 thành công, 13 lỗi" — thành công cộng lỗi vượt quá tổng. Có
   thể chỉ là hệ quả của lỗi môi trường ở mục A, có thể là bug đếm thật.
   Chưa tách bạch được.

2. **`man_hinh_du_lieu.gan_vao()` nuốt lỗi.** Bọc try/except rồi chỉ
   `print` ra console — máy thiếu `tksheet` thì tab biến mất im lặng.
   `hang_doi.py` đã KHÔNG lặp lại lỗi này (báo thẳng lên giao diện), nhưng
   file cũ chưa sửa vì nằm ngoài scope đã chốt.

## B2. Ver 3.6 — hai dòng không ghép được phụ kiện

1. **`MBTVM3P2500`** (vỏ 3 pha 2.500 kVA, MBT) — không có máy MBT 2.500 kVA
   nào trong MASTER. Chỉ THIBIDI có mức này, và ghép chéo hãng đã bị chặn
   có chủ ý. Không phải lỗi.
2. **`KNGTMBA325`** ("Giá treo MBT 3x25") — đọc tên ra 3 pha 25 kVA, nhưng
   MASTER không có máy 3 pha 25 kVA nào (3 pha bắt đầu từ 50 kVA). Nhiều
   khả năng "3x25" nghĩa là BA giá treo cho máy 1 pha 25 kVA, không phải
   một giá treo cho máy 3 pha. Đây đúng là loại nhập nhằng mà cờ
   `suy_tu_ten` sinh ra để bắt. **Cần Thịnh hỏi công ty xác nhận.**

## C. Vấn đề dữ liệu (không phải code)

1. **19 SKU Amorphous từng bị gán số của bản Silic** — đã xoá ở MASTER
   Ver5, hiện để trống. Cần bảng gốc QĐ 107/QĐ-HĐTV 21/9/2021 (MBA phân
   phối tổn hao thấp) để điền lại.
2. **`TBD3P3200A107`** có Po = 554 W trùng đúng `TBD3P2500A107`, tỷ lệ so
   với bản Silic là 23,7% trong khi 25 cặp còn lại nằm gọn 26,9–30,9%.
   Nghi chép nhầm, đã gắn cờ, chưa xoá.
3. **4 SKU có Po/Pk nội suy** (`TBD3P180`, `TBD3P2500` và 2 bản A107).
   Nội suy tuyến tính là thao tác được chính bảng EVN cho phép, nhưng phải
   in kèm ghi chú, không được để trần như số catalogue.
4. **Dung sai Po +5% / Pk +3%** lấy từ văn bản EVN **NPC (miền Bắc)**.
   Lotech bán ở địa bàn EVN SPC / EVNHCMC. Chưa kiểm hai tổng công ty này
   có quy định khác không.
5. **Bảo hành và CO/CQ đang 0%** trên toàn bộ 245 SKU. Không phải việc
   code — phải hỏi công ty.

## D. Đã biết, cố ý không sửa

- `giao-dien.py` 4.457 dòng, God Class. Viết lại là rủi ro lớn hơn lợi
  ích; mọi tab mới từ 3.1 trở đi đều nằm ở file riêng.
- Nhánh RMU (Ver 1/Ver 2) không dùng nhưng vẫn còn trong code. Code chạy
  được thì để yên.
