# Ver 6.3 — 31/08/2026 — Tra kho ảnh gốc công ty từ tab Ảnh

Bài thiếu ảnh thì đường đi cũ là: nhớ xem kho công ty có folder nào hợp,
mở Explorer, lội tay. Kho ~2,2 GB, folder đặt theo `LOẠI + HÃNG`
(`BIEN AP TU EMIC`, `DAU CAP 3M`, `CHI ONG ABB`…). 6.3 rút đường đó xuống
một nút, đặt cạnh `Google Images` trong tab Ảnh.

## Phạm vi — cố ý hẹp

CHỈ ĐỀ XUẤT. Bấm chọn thì copy đường dẫn vào clipboard, hết. Việc gán vào ô
vai trò vẫn phải bấm `Chọn ảnh…` như cũ.

Không tự gán vì tên folder chỉ nói được chủng loại + hãng, **không** nói được
tấm này là mặt trước hay tem nhãn. Máy đoán vai trò là đoán sai, và sai kiểu
này chỉ lộ ra sau khi bài đã lên web.

## Ba tầng khớp

| tầng | ví dụ | dùng khi |
|---|---|---|
| tên file chứa SKU | `EMIC-250-22-0.4.jpg` | ảnh đã đặt tên tử tế |
| tên file khớp mã | `3M-92-EB-5-1` ↔ `92-EB-5-1.jpg` | SKU dạng mã ngắn, mọi mảnh <3 ký tự |
| chỉ folder | `IMG_20260815_1430.jpg` trong `BIEN AP TU EMIC` | ảnh tải từ Zalo/web hãng |

Tầng 3 gánh phần lớn: ảnh nguồn hầu hết tên rác nhưng nằm trong folder có tên.
Không khớp gì thì rơi về danh sách folder nên mở tay — vẫn ngắn hơn lội từ gốc.

## "Ảnh đã dùng" — so bằng `hash_goc`, không phải đường dẫn

`WS.gan_anh()` CHÉP ảnh vào thư mục bài và đổi tên khi trùng, nên đường dẫn
nguồn không được lưu ở đâu cả. Thứ duy nhất nối được tấm trong kho gốc với
tấm đã gán là `hash_goc` — cùng khoá mà `WS.dem_dung_chung()` đang dùng.

`kho_anh_nguon.hash_file()` phải khớp `workspace_anh.hash_file()`
(SHA-256 rút gọn 16 ký tự). Test B7 canh chỗ này.

Hash chỉ tính cho ứng viên đã lọt top (≤48 tấm), không tính cho cả kho: đọc
2,2 GB để tô một cái nhãn là không đáng. Ảnh trùng bị **trừ 25 điểm + gắn
nhãn đỏ**, không bị ẩn — kho ảnh công ty vốn ít, dùng lại một tấm cho vài bài
là chuyện sẽ xảy ra; chặn thì bí, giấu thì không biết mình đang loãng tài sản.

## Bất biến

- Module **CHỈ ĐỌC**. Không ghi `phase2-du-lieu.db`, không đụng MASTER, không
  gọi WooCommerce, không sửa gì trong kho ảnh. Test C1/C2 đối chiếu mtime toàn
  bộ file trước/sau khi quét + đề xuất.
- Thứ duy nhất ghi ra là cache index JSON trong `%APPDATA%\SONEALEO\`.
  **Không** ghi cạnh thư mục ảnh: kho có thể nằm trên ổ mạng hoặc Drive
  read-only. Ghi hỏng thì bỏ qua, mất cache chỉ tốn thêm một lần quét.
- Cache key dùng **md5** đường dẫn, không dùng `hash()` — `hash()` đổi mỗi lần
  chạy process nên cache sẽ không bao giờ trúng và đẻ file rác mỗi lần mở app.
- `kho_anh_nguon.DUOI_ANH` phải khớp `workspace_anh.DUOI_ANH`. Lệch thì hai
  bên bất đồng ý kiến về "cái gì là ảnh". Test A14 canh.
- Điểm số chỉ để **xếp thứ tự**, không phải ngưỡng chấp nhận. Đừng lọc tự động
  theo điểm.

## Suy LOẠI từ tên hàng

`kien_thuc_bien_thien.dac_trung()` trả `loai` là dầu/khô (kiểu MBA), không
phải chủng loại sản phẩm, nên không dùng lại được. `suy_loai_tu_ten()` neo vào
cụm **dài trước**: `dau cap` phải thắng `cap`, không thì đầu cáp bị chỉ sang
folder cáp. Test A6/A7 canh đúng cặp này.

## File

| file | dòng | vai trò |
|---|---:|---|
| `kho_anh_nguon.py` | ~330 | lõi: quét, index, chuẩn hoá, xếp hạng. Không Tk. |
| `panel_anh.py` | ~380 | lưới thumbnail, lọc, mở Explorer |
| `tab_anh.py` | +80 | nút `Kho ảnh công ty` + nguồn hash đã dùng |
| `tests/test_v63_kho_anh_nguon.py` | ~180 | 32 test |

## Cấu hình

Khoá `KHO_ANH_NGUON` trong `cau-hinh.env`. Chưa có thì lần đầu bấm nút sẽ hỏi
chọn thư mục rồi tự ghi. **Không đoán bừa** một thư mục mặc định — đoán sai
thì quét nhầm cả ổ đĩa.

## Còn phải làm trên máy công ty

1. Chạy `python kho_anh_nguon.py "D:\W-ANH GOC"` — in ra folder nào chưa nhận
   ra LOẠI. Bổ sung `TU_KHOA_LOAI` / `ANH_XA_LOAI` / `ANH_XA_HANG` cho khớp
   cách gọi trong MASTER. Đây là chỗ duy nhất cần bảo trì tay.
2. Đo thời gian quét thật trên 2,2 GB. Chưa đo, chỉ mới chạy trên kho giả.

## Kiểm chứng

Chạy thật dưới Xvfb: dựng `TabAnh`, gán bài đang chọn, bấm nút. Cửa sổ mở,
xếp hạng đúng, ảnh tên Zalo ra được nhờ folder, nhãn ĐÃ DÙNG, lọc tên, lọc
kích thước, fallback khi không khớp. 32/32 test PASS.

**Chưa kiểm chứng:** hiệu năng trên kho 2,2 GB thật, và tỉ lệ khớp với tên
folder thật trên máy công ty.

---

# Ver 6.2 — 28/08/2026 — Hạ trùng lặp văn xuôi từ 99,6% xuống 39,3%

Nối tiếp 6.1. 6.1 mới bật khối biến thiên; đo lại thì vẫn trùng 82,7% vì
bản thân các khối đó là câu mẫu chỉ thay số. 6.2 xử ba nguồn trùng còn lại.

## Đo trước khi sửa — bóc từng khối, 6 SKU dầu 3 pha 250→2000kVA

| khối | ký tự TB | giống nhau |
|---|---:|---:|
| `khoi_ve_thuong_hieu` | 171 | 100,0% |
| **LEGACY** `khoi_chung_may_bien_ap` | 111 | **100,0%** |
| **LEGACY** `khoi_ve_loi` | 423 | **100,0%** |
| **LEGACY** `khoi_bao_tri_lap_dat` | 314 | **100,0%** |
| `BT khoi_so_sanh_loi` | 397 | 95,4% |
| `BT khoi_doc_hieu_thong_so` | 627 | 90,9% |
| `BT khoi_chon_cong_suat` | 407 | 85,6% |
| `BT khoi_lap_dat_van_chuyen` | 284 | 71,5% |
| `BT khoi_ung_dung` | 341 | 69,4% |

## A. Biến thể câu chữ ổn định theo SKU — `_bien_the(row, n, muoi)`

Chỉ số biến thể = `md5(mã SKU + muối khối) % n`. **Không random**: bài đã
đăng render lại phải ra ĐÚNG chữ cũ, nếu không thì mỗi lần đăng lại đổi văn
và không bao giờ đối chiếu được bài live với bài trong kho. Đã kiểm: render
2 lần ra byte-identical.

`muối` khác nhau mỗi khối để cả bài không rơi hết vào "biến thể 0".

4 biến thể/khối cho cả 5 khối. Kết quả:

| khối | trước | sau |
|---|---:|---:|
| `khoi_so_sanh_loi` | 95,4% | **38,2%** |
| `khoi_doc_hieu_thong_so` | 90,9% | **54,9%** |
| `khoi_chon_cong_suat` | 85,6% | **45,8%** |
| `khoi_ung_dung` | 69,4% | **52,1%** |
| `khoi_lap_dat_van_chuyen` | 71,5% | **59,6%** |

## B. Xáo thứ tự khối theo SKU (`tat_ca_khoi`)

Giữ khối ứng dụng luôn đứng đầu (thứ người đọc cần trước), 4 khối còn lại
xoay vòng theo `_bien_the`. Hai bài cạnh nhau không còn đi đúng mạch 1-2-3-4-5.

## C. Gỡ 3 khối kiến thức viết chết khỏi luồng dựng bài

848 ký tự byte-identical trên MỌI bài = 25% khối lượng chữ code sinh. Nội
dung đã có bản biến thiên tương ứng nên giữ cả hai là nói hai lần cùng ý:

    khoi_ve_loi           -> khoi_so_sanh_loi        (Po thật của 2 lõi)
    khoi_bao_tri_lap_dat  -> khoi_lap_dat_van_chuyen (theo dải kVA + dầu/khô)
    khoi_chung_may_bien_ap-> khoi_ung_dung

Hàm GIỮ NGUYÊN, chỉ không gọi. Bật lại: `SNL_KHOI_KIEN_THUC_CU=1`.

## Kết quả cuối

15 cặp SKU, bỏ bảng thông số, **giữ NGUYÊN văn AI** để cô lập phần code sinh:

    BẢN ĐANG CHẠY THẬT : TB 99,6%   cao nhất 99,8%   thấp nhất 99,5%
    BẢN 6.2            : TB 39,3%   cao nhất 84,0%   thấp nhất 27,2%
    Số cặp còn >70%    : 1/15
    Độ dài TB          : 2.769 ký tự

Hiệu chuẩn thang đo (difflib, văn kỹ thuật tiếng Việt):

    hai đoạn khác hẳn chủ đề (MBA vs cáp vs RMU) : 21-34%
    cùng câu, chỉ đổi số                          : 98,6%
    cùng chủ đề, viết lại khác hẳn                : 25,1%

Nên 39,3% ≈ "viết khác hẳn, cùng chủ đề". Đúng vùng cần tới.

## Sự cố trong lúc làm — ghi lại để không lặp

Bản nháp 6.2 diễn đạt lại cụm miễn trừ cho đỡ trùng ("ngưỡng tối đa", "mức
trần catalogue") và bỏ công thức `(240W x 8.760h : 1.000)` ở 2 biến thể.
→ FAIL 3 assertion `tests/test_v32_tang3.py` mục 4 và 6.

Cả 3 đều là fail ĐÚNG: hai cụm `tối đa theo catalogue` / `không phải kết quả
đo` là câu chống mạo nhận số catalogue thành số đo của máy, và công thức là
kỷ luật số liệu của chính module. **Đa dạng hoá chỉ được đụng phần đuôi câu,
không đụng cụm bắt buộc.** Đã cố định lại, 34/34 PASS.

## Test

    test_v32_tang3.py       34/34 PASS
    test_v33_bo_cuc.py      31/31 PASS
    test_v36_regression.py  16/16 PASS
    test_phase2_full.py     12/12 PASS
    test_v364_dot_lon.py    45/45 PASS
    test_v35_idempotency.py lỗi thiếu tkinter — CÓ SẴN trên bản 6.0 gốc, không do 6.2

## Trần còn lại

- Sàn không hạ được nữa: `khoi_ve_thuong_hieu` 171 ký tự giống 100% theo
  hãng, hero + 2 khối CTA ~203 ký tự giống 100%. Cộng lại ~374 ký tự/bài.
- 1/15 cặp còn 84,0% — hai SKU rơi trùng biến thể ở nhiều khối. Nâng lên 6
  biến thể/khối sẽ giảm tiếp, chưa làm.
- Con số 39,3% đo trong điều kiện **văn AI giữ nguyên**. Bài thật văn AI
  cũng khác nhau nên số thật thấp hơn — nhưng chưa đo được nếu không đốt quota.
- **VẪN KHÔNG giải quyết duplicate do dữ liệu mỏng.** SKU không có spec khác
  biệt thì đây chỉ là thay áo. Kết luận cũ giữ nguyên.

# Ver 6.1 — 28/08/2026 — Khối kiến thức biến thiên chạy ở bố cục MẶC ĐỊNH

## Lỗi gốc

`kien_thuc_bien_thien.py` (TẦNG 3, viết ở Ver 3.2 đúng để chống "cùng một
khuôn") CHỈ được gọi trong `render_phase2._dung_bai_2_5_wrapper()` — tức chỉ
chạy khi `GIAO_DIEN_2_5=1`. Cờ đó mặc định `0` (`cau-hinh.env.MAU:143`).

Nghĩa là ở bố cục đang chạy thật, module này **chưa từng chạy một lần nào**.
Toàn bộ bài đã đăng chỉ có 3 khối kiến thức viết chết.

## Bằng chứng đo được (không phải suy đoán)

Gọi thẳng 3 khối cũ trên 5 SKU trải từ 25kVA đến 1600kVA:

| khối | số biến thể / 5 SKU |
|---|---|
| `khoi_chung_may_bien_ap` | 2 (chỉ tách dầu/khô) |
| `khoi_bao_tri_lap_dat`   | 2 (chỉ tách dầu/khô) |
| `khoi_ve_loi`            | 3 (silic/amorphous/rỗng) |

250kVA và 1600kVA ra HTML **byte-identical** ở cả 3 khối.

Dựng bài đầy đủ cho 6 SKU dầu 3 pha (250→2000kVA), giữ NGUYÊN văn AI để cô
lập phần code sinh, bỏ bảng thông số rồi so văn xuôi từng cặp (15 cặp):

    TRƯỚC: giống nhau trung bình 99,6%  (cao nhất 99,8%)
    SAU  : giống nhau trung bình 82,7%  (cao nhất 96,8%)

Độ dài bài tăng ~2.100–2.600 ký tự/bài.

## Sửa

### A. `render_phase2.dung_bai_html()` — gọi `tat_ca_khoi()` ở nhánh cũ

Chèn sau `khoi_bao_tri_lap_dat`, đúng vị trí tương ứng trong nhánh 2.5. Bọc
`try` — lỗi khối này KHÔNG được làm hỏng bài. **Tốn 0 token Gemini**, toàn
bộ do code sinh từ kVA/số pha/dầu-khô/lõi/hãng + Po/Pk/Uk tra catalogue.

### B. `kien_thuc_bien_thien.dac_trung()` — nới regex nhận diện dầu/khô

    cũ : (?:bien\s*ap|mba)\s+(?:\w+\s+)?(dau|kho)\b      -> tối đa 1 chữ đệm
    mới: (?:bien\s*ap|mba)\s+(?:\w+\s+){0,3}?(dau|kho)\b -> tối đa 3

Tên thật có dạng "Máy biến áp **cấp nguồn** Dầu 1 pha…" (2 chữ đệm) nên
regex cũ trượt. VẪN giữ neo `biến áp|mba` — bỏ neo thì "đầu cáp" (bỏ dấu →
`dau cap`) bị nhận nhầm thành máy dầu.

Đo trên MASTER thật, sheet `03_May_Bien_Ap_Do_Luong`, 174 dòng MBA:

    regex cũ : 139 dòng (79%)
    regex mới: 141 dòng (81%)   — 0 dòng đổi kết quả so với cũ

## Chưa làm / giới hạn

- Con số 99,6%→82,7% đo trong điều kiện **giữ nguyên văn AI**. Bài thật văn
  AI cũng khác nhau nên số thật sẽ khác; đây là phần đóng góp riêng của code.
- Hai SKU cùng hãng, cùng dầu/khô, cùng dải kVA vẫn ra chữ gần giống nhau.
  Khối biến thiên chỉ giảm cảm giác cùng khuôn, KHÔNG giải quyết duplicate
  do dữ liệu mỏng.
- Chưa đụng `GIAO_DIEN_2_5` — cờ đó vẫn mặc định tắt, bố cục không đổi.

# Ver 6.0 — 23/08/2026 — MASTER Ver17 về 0 cảnh báo

## Kết quả

    import_4_profile('9MASTER_Ver17_SACH_TEXT_20260821.xlsx')
    TRƯỚC: 4 loại cảnh báo (17 mã trùng + 19 SKU sai họ)
    SAU  : 0 cảnh báo, 5.614 dòng — không mất dòng nào

## Sửa ở HAI CHỖ KHÁC NHAU, có lý do

### A. Excel — 18 mã SKU trùng (sửa TẠI CHỖ)

Kiểm từng cặp: **không cặp nào là dòng lặp**. Tất cả là sản phẩm KHÁC NHAU
bị gán trùng mã. Nên sửa = đổi mã, KHÔNG phải xoá dòng.

| mã cũ | dòng | thành | vì sao |
|---|---|---|---|
| `TTTCVV250` | 2503 | `TTTCVV2X50` | mã gộp nhầm "250mm²" với "2x50mm²" |
| `TTTCVV350` | 2521 | `TTTCVV3X50` | như trên |
| `TTTCXVFR250` | 2863 | `TTTCXVFR2X50` | như trên |
| `TTTCXVFR350` | 2892 | `TTTCXVFR3X50` | như trên |
| `TTTCVVDSTA2xx` | 2504–2509 | `TTTCVVDATA2xx` | giáp DATA bị gán mã DSTA (6 dòng) |
| `TTTVCM2.5` | 2703 | `TTTVCM1.5` | VCm1.5 mang mã của VCm2.5 |
| `TTTCXWBSC10` | 3109/3110 | `...120` / `...150` | mã "10" sai cho cả hai dòng |
| `BHSLBS24M` | 241 | `BHSLBS24MKMR` | bản không mở rộng 42tr (bản SCADA 46tr giữ mã) |
| `TAIPCTT300300T` | 524 | `...T712` | vỏ cách điện 7–12mm vs 3–7mm |
| `P36NGNT1xxx` | 986–988 | `...NT` | bản ngoài trời vs trong nhà (3 dòng) |

**RÀNG BUỘC ĐÃ TÔN TRỌNG:** `record_id = profile::sheet::SỐ DÒNG::sku`.
Xoá/chèn dòng làm mọi dòng bên dưới đổi record_id -> mồ côi bài đã đăng.
Nên chỉ sửa GIÁ TRỊ Ô, không đụng vị trí dòng. Đo lại:

    record_id GIỮ NGUYÊN : 5.596 / 5.614  (99,68%)
    record_id ĐỔI        : 18  — đúng bằng số mã đã sửa, không hơn
    ô công thức          : 73 -> 73  (dùng data_only=False, không giết công thức)
    sheet                : 15 -> 15, số dòng mọi sheet không đổi

18 mã đổi định danh là **không tránh được** — đổi SKU thì record_id phải
đổi. Nhưng 18 dòng đó vốn đang trùng mã nên chưa từng publish sạch.

Đã ghi 18 dòng vào sheet `00_Nhat_Ky_Sua_Loi` sẵn có của file (append cuối).

### B. Code — 19 SKU sai họ (KHÔNG dời dòng sang sheet khác)

Family Router phát hiện 19 SKU trong sheet 02 không phải thiết bị đóng cắt.
Để nguyên thì bài viết mô tả chống sét van như thể nó là tủ đóng cắt — sai
bản chất VÀ rank nhầm truy vấn.

Cách sai: dời 19 dòng sang sheet 04. Làm vậy là xoá dòng khỏi sheet 02 ->
mọi dòng bên dưới đổi record_id -> mồ côi hàng loạt.

Cách đã dùng: thêm định tuyến theo TÊN trong `profiles.xac_dinh_outline_id`,
**cùng khuôn mẫu đã có sẵn** cho `may_bien_ap_do_luong` (vá Ver 5.2 khi
"Vỏ mạ kẽm" bị gọi là máy biến áp):

    'thi nghiem' / 'kiem dinh'          -> outline_service     (9 SKU dịch vụ)
    'do dem' / 'cong to'                -> outline_do_luong    (1 SKU)
    'chong set'/'su do'/'bass su'/
    'hop nguon'                         -> outline_phu_kien    (9 SKU)

Sửa trong code còn lợi hơn sửa Excel: **bản MASTER sau vẫn được vá**, không
phải sửa tay lại từ đầu mỗi lần xuất file mới.

`outline_service` chọn thay vì `outline_phu_kien` cho nhóm thí nghiệm vì
`family_router` chấp nhận cả hai, mà service đúng bản chất hơn — đây là
dịch vụ kiểm định, không phải hàng bán.

## Một test đỏ theo — KHÔNG phải hồi quy

`test_phase2_full` Test 11 kỳ vọng `vỏ tủ -> outline_vo_tu = 14`, thực tế
còn 9. Truy ra 5 dòng chênh:

    VNHNTC1P/1PC/1PLS/3P   "Hộp nguồn lắp đặt..."   -> outline_phu_kien
    SNDTDD                 "Tủ đo đếm (TU,TI...)"   -> outline_do_luong

**Cả 5 đều nằm trong danh sách 19 SKU sai họ.** Chúng có
`nhom_nguon='10. Tủ Điện & Trung Thế'` nên trước đây bị gom vào vỏ tủ dù
hộp nguồn không phải vỏ tủ trung thế. 14 -> 9 là cải thiện. Đã sửa kỳ vọng
kèm lý do đầy đủ trong test.

Bộ test: **88 PASS / 1 FAIL / 1 SKIP** (FAIL = `test_v39_a1_layout` thiếu
`scrot`, chỉ Linux).

## Hai lần suýt báo tin xấu SAI trong đợt này

1. Nhét thẳng header tiếng Việt từ Excel vào `bang_thong_so()` -> ra "100%
   bài trùng nhau". Sai: pipeline thật đi qua ánh xạ cột `cot_import`.
   Chạy đúng `import_4_profile()` thì **0% trùng trên 600 SKU**.
2. Tự ánh xạ cột bằng tay -> MBA nổ 15/120 dòng `AttributeError: 'int'
   object has no attribute 'replace'`. Qua hàm import thật thì **0 lỗi** —
   bước import có normalize số.

Bài học: **mô phỏng pipeline là tự tạo ra bug không tồn tại.** Phải gọi
đúng hàm thật.

---

## Ver 5.9 — Bước 1 xong: TOÀN HỆ VỀ 0 điểm chạm

`tab_anh.py` (1.508 dòng) chuyển sang hợp đồng: `app.ui` -> `giac.ui`,
`app.chay_nen_phase2` -> `giac.chay_nen`, `getattr(app,'log')` -> `giac.log`,
`gan_vao(nb, app)` -> `gan_vao(nb, giac)`.

    tab_anh.py        2 -> 0
    TOÀN HỆ           2 -> 0   (5 module tính năng, không module nào với vào vỏ)

## ĐO CHI PHÍ BƯỚC 2 — kết quả đổi hẳn quy mô

Trước khi tách, đo 38 lời gọi "ra ngoài nhóm" của 4 nhóm ứng viên
(ui_jobs, ui_enhance, ui_outline, ui_anh). Tưởng là 38 chỗ phải gỡ. Thực
tế chỉ là **6 hàm** lặp lại:

| hàm | số lần | thật ra là gì |
|---|---|---|
| `_con_phase2()` | 14 | ĐÃ là chân `giac.db()` |
| `_phase2_dataset_id_dang_chon()` | 8 | state chọn dùng chung |
| `_v3_the()` | 7 | tiện ích dựng thẻ |
| `_v3_tab_cuon()` | 3 | ĐÃ có `ui_tien_ich.khung_cuon()` |
| `_phase2_mau_dang_chon()` | 2 | state chọn dùng chung |
| `_v3_site_cfg` + 2 hàm cấu hình | 4 | ĐÃ là chân `giac.cau_hinh()` |

18/38 đã có chỗ. 10 là tiện ích tkinter thuần. Còn đúng **10 lời gọi** là
khái niệm thật sự thiếu.

### Chân thứ 6: `giac.dang_chon()` — cân nhắc, không phải phình cho tiện

Trả `{'dataset_id', 'mau', 'site'}`. Đây LÀ state của vỏ ứng dụng (ô chọn
dataset và ô nhập mẫu nằm ở tab khác), đúng tiêu chí đã đặt: **cần state/
dịch vụ của vỏ -> chân cắm; chỉ cần tkinter -> tiện ích**.

Không có chân này thì mỗi module tách ra phải `thoat_hiem()` hoặc tự dựng ô
chọn riêng -> **mỗi tab một dataset**, đúng loại lỗi khó tìm nhất.

Vỏ ứng dụng cung cấp qua `PhanMem.dang_chon()`, bọc try từng phần: một ô
chưa dựng (tab chưa mở) không được làm chết cả hàm.

LƯU Ý ghi trong docstring: **gọi tại lúc dùng, đừng cache** — người dùng đổi
dataset ở tab khác bất cứ lúc nào, giá trị cache là giá trị sai.

### `ui_tien_ich.the()` — tiện ích, KHÔNG phải chân

Chép từ `PhanMem._v3_the`. 7 lời gọi trong nhóm ui_anh. tkinter thuần.

## Hai test đỏ theo — đều là hệ quả trực tiếp, không phải hồi quy

  * `test_v58_ranh_gioi`: assert `CHAN_HOP_LE == 5`. Sửa thành 6 **kèm lý do
    đầy đủ trong comment**. Đổi con số này mà không ghi vì sao = đang phình
    hợp đồng.
  * `test_v44_ui_logic`: `TabAnh(root, app=None)` -> `giac=None`.

Bộ test: **88 PASS / 1 FAIL / 1 SKIP**. FAIL là `test_v39_a1_layout` thiếu
`scrot` (chỉ Linux).

## Bước 2 & 3 — CHƯA làm, và vì sao

Bước 2 giờ là việc **cơ học nhưng dài**: 38 method / 976 dòng phải đọc kỹ
từng widget rồi chuyển. Không khó nữa (đường đã dọn: 6 chân + 2 tiện ích
phủ hết 38 lời gọi ra ngoài), nhưng cần đọc ~1.000 dòng source cẩn thận.

Bước 3 (vỏ mới) chỉ làm được SAU Bước 2, vì trước đó vỏ mới chỉ chứa được
5/24 tab.

---

# Ver 5.9 — 22/08/2026 — màn hình "HÔM NAY"

> Tính năng MỚI đầu tiên viết SAU hợp đồng giac_cam.py. Mục đích kép: (1)
> lấp một lỗ thật trong tool, (2) làm PHÉP THỬ xem hợp đồng có dùng được để
> ráp tính năng mới hay chỉ đẹp trên giấy.

## Vấn đề

Tool có 23 tab con, bồi thêm theo từng version, không theo cách một người
làm SEO đi hết một ngày. Không tab nào trả lời câu hỏi mở tool ra là hỏi
đầu tiên: **"Hôm nay làm gì? Cái gì đang chặn?"**

    Còn bao nhiêu SKU chưa sinh?  -> mở tab Hàng đợi, bấm lọc
    Hôm nay đốt bao nhiêu quota?  -> đếm tay trong log
    Bài nào lỗi?                  -> mở tab Theo dõi, kéo tìm

Ba câu hỏi, ba tab, không câu nào có sẵn số. **Sắp xếp lại 23 tab thành 5
nhóm khác vẫn là 23 tab** — cái thiếu là một màn hình tổng hợp, nên làm
cái đó trước khi bàn chuyện bày biện.

## Đã làm

`tab_hom_nay.py` — chèn lên ĐẦU nhóm DỮ LIỆU, mở app là thấy trước tiên.

  * 5 ô số: SKU trong kho / chưa sinh / đã đăng / đang lỗi / quota còn
  * Danh sách việc xếp theo mức chặn (CHẶN > NÊN LÀM > OK), sinh TỪ SỐ LIỆU
  * Kho hàng theo nhóm sản phẩm + site đang dùng

Việc sinh ra bám đúng thứ tự ưu tiên đã chốt: nhắc **"Soát mỏng/trùng…"
TRƯỚC khi sinh lô**; cảnh báo quota nêu rõ **tính theo GOOGLE CLOUD PROJECT
chứ không theo key** (thêm key cùng project không tăng hạn mức).

### Nguyên tắc số liệu

Chỉ hiện số ĐỌC ĐƯỢC TỪ DB. Chưa đo được thì hiện `—` kèm lý do, KHÔNG ước
lượng. Đặc biệt: thiếu bảng thì để `None` chứ **không phải 0** — 0 và
"không biết" là hai chuyện khác nhau, lẫn lộn là mất uy tín cả bảng số.

## PHÉP THỬ HỢP ĐỒNG — kết quả

Module này viết sau `giac_cam.py` và **không sửa hợp đồng dòng nào**. Nếu
ráp một tính năng mới mà phải nới hợp đồng thì hợp đồng sai. Đo được:

    điểm chạm ngoài 5 chân            0
    thuộc tính nhét vào app           0
    tự dựng threading.Thread          0   (đi qua giac.chay_nen)
    gọi os.environ trực tiếp          0   (đi qua giac.cau_hinh)
    import giao-dien / đụng PhanMem   0

**Lợi ích lớn nhất, đo được:** `test_v59_hom_nay.py` — 25 assert, chạy
**191 ms, KHÔNG cần Xvfb**. Trước Ver 5.8 điều này bất khả: muốn test bất
cứ tab nào cũng phải dựng cả app 787 widget dưới Xvfb (~1 giây/lần, cộng
chi phí Xvfb). Logic đọc số tách hẳn khỏi giao diện (`doc_so_lieu`,
`dung_viec_can_lam` là hàm thuần) nên test được bằng SQLite in-memory.

Đây là thứ đáng giá nhất của cả đợt chuẩn hoá, hơn cả việc chia file.

## Ratchet đã siết

    tab_hom_nay.py       thêm vào danh sách, ngưỡng 0/0 — module mới phải
                         sạch từ đầu, không có ân hạn
    test_ver3_ui I1b     14 -> 15 tab con, CÓ CHỦ ĐÍCH kèm lý do

Con số tab được phép đổi khi cố ý thêm/bớt, nhưng phải đổi ở đúng chỗ và
ghi lý do. Đổi mà không hiểu vì sao đổi thì đang che một hồi quy.

Bộ test: **88 PASS / 1 FAIL / 1 SKIP**. FAIL là `test_v39_a1_layout` thiếu
`scrot` (chỉ Linux).

## CHƯA làm — nói rõ để khỏi hiểu nhầm

Đây **không phải** vỏ giao diện mới. Vỏ mới hôm nay chỉ chứa được 5/24 tab
(những cái đã là module rời). 18 tab còn lại vẫn dựng inline trong
`PhanMem`, muốn dời phải tách trước. Thứ tự còn lại:

    1. tab_anh.py — 2 điểm chạm cuối, ~10 phút
    2. Tách giao-dien.py (5.359 dòng -> ~3.700)
    3. Lúc đó mới dựng được vỏ mới xếp theo luồng làm việc

---

# Ver 5.8 — 22/08/2026 — GIẮC CẮM: hợp đồng module tính năng

> Bước 1 của việc chuẩn hoá. **Chưa tách file nào** — cố ý. Tách trước khi
> có chuẩn thì mỗi mảnh gỡ ra lại tự chế chấu riêng, đúng cái đang xảy ra.

## Đo trước khi làm

5 module tính năng đang chạy, bề mặt tiếp xúc với vỏ ứng dụng:

| module | dòng | điểm chạm `app` |
|---|---|---|
| `tab_anh.py` | 1.508 | 2 |
| `hang_doi.py` | 436 | 0 |
| `man_hinh_du_lieu.py` | 492 | 0 |
| `tab_seo_post.py` | 410 | 57 (trên 14 tên) |

3.023 dòng gần như đã tự lập. Nhưng **0 thứ được ≥2 module cùng dùng** —
không có chuẩn chung. Mỗi module tự chế chấu riêng.

Phân tích coupling trong `giao-dien.py`: 92% class (178/194 method) là MỘT
khối liên thông. Nhưng bỏ cạnh "gọi method", chỉ tính state chung, khối lớn
nhất tụt còn 34% / 58 cụm. Kết luận: dây điện chủ yếu là **lời gọi method**,
không phải state — nên tách được bằng pattern uỷ nhiệm đã có sẵn.

## Ba mâu thuẫn `giac_cam.py` sinh ra để giải

1. **API an toàn trông như hack, API trông chuẩn thì không an toàn.**
   `print()` từ luồng nền là HỢP LỆ (`ChuyenHuongIn` router stdout theo
   thread, marshal về luồng chính). `app.log()` ghi THẲNG vào widget
   `self.log_o`, không marshal — gọi từ luồng nền là đúng loại bug đã vá ở
   `tab_seo_post.py` Ver 5.7. Người ráp tính năng mới sẽ chọn nhầm.
   -> `giac.log()` tự nhận luồng, chọn đúng đường.

2. **Hai runner nền, cái tên "chung" mới là cái hỏng.** `chay_nen()` khoá
   cứng `self.nut_chay`/`self.nut_dung` — 2 nút của tab 5 RMU, tức UI
   `manager=NONE` không bao giờ hiện. `chay_nen_phase2()` mới là bản sạch.
   -> `giac.chay_nen()` trỏ về bản sạch.

3. **18 chỗ gọi `ket_noi()`, không kỷ luật luồng.**
   -> `giac.db()` phổ quát hoá cách vá Ver 5.7 (`threading.local()`).

## Năm chân cắm

    giac.log(msg, muc='')         an toàn mọi luồng
    giac.ui(fn)                   nhờ luồng chính chạy
    giac.chay_nen(fn, ten='')     chạy nền
    giac.db()                     kết nối SQLite đúng luồng
    giac.cau_hinh(ten, md=None)   đọc cấu hình

`GiacCam` **chặn thật, không phải ghi luật suông**: `__getattr__` /
`__setattr__` ném `LoiViPhamGiac` nêu đích danh tên thuộc tính và nhắc dùng
chân nào. Cửa `thoat_hiem('lý do')` cho chuyển dần, bắt buộc nêu lý do, và
bị test đếm — con số CHỈ ĐƯỢC GIẢM.

## Lợi ích lớn nhất, không phải việc chia file

`giac_cam.py` KHÔNG import tkinter. `GiacCamGia()` chạy headless: `log` gom
vào list, `ui`/`chay_nen` chạy đồng bộ (test tất định), `db` in-memory.
-> Module tính năng test được **không cần Xvfb, không cần dựng app 787
widget**. Với người định ráp nhiều tính năng thì đây là thứ đáng giá nhất.

## `test_v58_ranh_gioi.py` — cái ratchet

Chia file KHÔNG giữ được kiến trúc. Sáu tháng sau module thứ 12 sẽ tự chế
dây riêng, chỉ khác là nhiều file hơn. File test này đo 4 chốt, chỉ được
siết: điểm vào chuẩn, điểm chạm ngoài 5 chân, thuộc tính nhét vào app, số
lần thoát hiểm. Ngưỡng hiện tại là ẢNH CHỤP thực trạng, không phải mục tiêu.
**Nâng ngưỡng = đang xây lại God Class, chỉ chậm hơn.**

## Ba lỗi của chính đợt này, đã sửa

- **Đặt tên sai: `khung`.** Chữ `khung` đã là tên quen của `ttk.Frame` trong
  repo (66 lần, `khung = ttk.Frame(...)` ở `giao-dien.py:196`,
  `hang_doi.py:92`). Đặt trùng khiến test báo oan `hang_doi.py` ngay lần
  chạy đầu. Đổi thành `giac_cam.py` / `giac`.
- **Đo nhầm đơn vị.** Ghi ngưỡng `tab_seo_post = 14` (số tên duy nhất) trong
  khi máy đếm 57 (lượt chạm). Lượt chạm mới là thước đúng vì nó đo khối
  lượng việc phải gỡ.
- **Phân loại nhầm.** Xếp `giao_dien_2_5.py` vào module tính năng, nhưng nó
  là THƯ VIỆN dựng HTML (`xuat_css_2_5`, `khoi_chip`) — không nhận app,
  không tạo tab. Tiêu chí đúng: module tính năng = nhận `app`/`giac` VÀ tự
  gắn mình vào giao diện.

## Việc tiếp theo (chưa làm)

Bước 2: cho 5 module hiện có tuân chuẩn. `tab_seo_post.py` nặng nhất — 57
lượt chạm + 15 thuộc tính nhét vào app. 3 module kia gần như không phải sửa.
Bước 3: mới tách `giao-dien.py` theo kế hoạch 4 đợt.

---

## Bước 2 — `tab_seo_post.py` gỡ sạch (cùng ngày)

| | trước | sau |
|---|---|---|
| lượt với vào app | 57 | **0** |
| thuộc tính nhét vào app | 15 | **0** |
| điểm chạm toàn hệ | 59 | **2** |

State nay nằm trong class `TabSeoPost`, y hệt `TabHangDoi` và `TabAnh` vốn
đã sạch từ đầu. Vỏ ứng dụng không còn biết tab này có bao nhiêu widget.
Điểm vào đổi `dung_tab(app)` -> `gan_vao(nb, giac)`.

### Ba lỗi CHỈ LỘ KHI CHẠY THẬT, không lộ khi đọc code

1. **Mất tính năng cuộn.** Bản cũ gọi `app._v3_tab_cuon()` — hàm đó dựng
   Canvas + Scrollbar + bắt con lăn chuột. Bản viết lại dùng `ttk.Frame`
   trần: tab 4 khối tràn khỏi cửa sổ, mất luôn hàng nút cuối.
   -> Tách `ui_tien_ich.khung_cuon()`.
   **KHÔNG thêm chân thứ 6 vào hợp đồng.** Quy tắc phân loại: cần state/dịch
   vụ của vỏ -> chân cắm; chỉ cần tkinter -> tiện ích, import thẳng. Nhét
   tiện ích vào hợp đồng thì hợp đồng phình theo mỗi tiện ích mới — đúng
   cách God Class được nuôi lớn, chỉ khác chỗ đứng.

2. **Nhãn tab đổi.** `_v3_tab_cuon()` cắt tiền tố số trước khi hiện, nên
   `'11. SEO Post'` phải hiện thành `'SEO Post'`. Bản đầu hiện cả số.

3. **LỖI THIẾT KẾ TRONG CHÍNH HỢP ĐỒNG — nặng nhất.**
   `db_seo_post.ket_noi()` = `db_phase2.ket_noi()` **+ `tao_schema()``.
   `giac.db()` chỉ làm vế đầu. Trên máy dev có sẵn DB cũ nên KHÔNG lộ; chỉ
   lộ khi chạy với thư mục dữ liệu TRỐNG: bảng `bai_seo` chưa tồn tại ->
   `liet_ke()` ném lỗi -> tab không dựng được -> app còn **13 tab thay vì
   14**. Bắt được nhờ `test_ver3_ui` chạy trong sandbox sạch của
   `run_tests.py` — chạy tay ở thư mục dev thì 9/9 PASS.
   -> Ghi rõ giới hạn vào docstring chân `db()`: chân này chỉ trả KẾT NỐI,
   module có schema riêng phải tự gọi `tao_schema()` một lần.
   -> `nap_bai()` bọc try: lỗi DB hiện lên nhãn trạng thái thay vì kéo chết
   cả tab.

### Ngưỡng đã hạ (ratchet siết)

    tab_seo_post  chạm 57 -> 0     gán 15 -> 0
    toàn hệ       chạm 59 -> 2     (2 còn lại là app.ui/app.chay_nen_phase2 của tab_anh)

Bộ test: **87 PASS / 1 FAIL / 1 SKIP**. FAIL là `test_v39_a1_layout` thiếu
`scrot` (chỉ Linux). SKIP là `test_v441_meta_failsoft` cần DB thật.

### Còn lại

`tab_anh.py` 2 điểm chạm (`app.ui`, `app.chay_nen_phase2`) — đổi sang
`giac.ui` / `giac.chay_nen` là về 0. Chưa làm vì file 1.508 dòng, để đợt
riêng. Sau đó mới tách `giao-dien.py`.

---

# Ver 5.7 — 22/08/2026 — đợt vá sau audit code

> Mục này **viết LÚC làm**, không tái dựng ngược. Mọi con số dưới đây đều
> đo/chạy được, không suy từ đọc code. Chỗ nào không chắc thì ghi thẳng.

## Bối cảnh

Audit toàn bộ source (149 file `.py`, 39.977 dòng) ngày 22/08/2026. Ra 11
việc. **2 trong số đó, sau khi kiểm chứng, hoá ra là kết luận SAI của chính
đợt audit** — ghi lại ở mục "Đã BÁC BỎ" bên dưới để lần sau không ai làm lại.

## LỖI THẬT đã vá

### 1. `giao-dien.py` — nút "Kiểm tra key" kẹt vĩnh viễn  *(mức tin cậy: cao)*

`_v3_viec_kiem_tra_gemini()` bắt lỗi rồi truyền vào `self.ui(lambda: ... e ...)`.
Python 3 **xoá tên biến của `except ... as e` ngay khi thoát khối except**, mà
`self.ui()` chỉ ĐẨY lambda vào queue để `_boc_hang_doi()` chạy SAU ở luồng chính.
Lúc chạy thì `e` không còn:

    NameError: cannot access free variable 'e' where it is not associated
               with a value in enclosing scope

`_boc_hang_doi()` nuốt NameError vào nhánh `'LỖI UI callback'`, nên
`_v3_ket_qua_kiem_tra_gemini()` **không bao giờ được gọi khi kiểm tra key thất
bại** → nút kẹt `disabled`, label kẹt "Đang kiểm tra...", lỗi API thật không
bao giờ hiện. Đã tái hiện bằng mô phỏng queue.

**Sửa:** hoá lỗi thành chuỗi trong khối except, bắt bằng default-arg
(`lambda t=tin_loi:`) thay vì free variable. `pyflakes` còn **0** `undefined name`.

### 2. `tab_seo_post.py` — tab SEO Post hỏng 100% khi chạy hàng loạt  *(cao)*

Dòng 29 mở kết nối SQLite ở **luồng chính**, cất vào `app._sp_con`. `_worker()`
chạy ở **luồng nền** lại dùng chính kết nối đó. `sqlite3.connect()` mặc định
`check_same_thread=True`:

    sqlite3.ProgrammingError: SQLite objects created in a thread can only
    be used in that same thread.

`except Exception` nuốt lỗi, đếm `loi+1` → mọi bài đều fail, người dùng chỉ
thấy "0 thành công, N lỗi". Đã tái hiện bằng cách gọi đúng đường
`C.sinh_bai()` từ luồng nền.

**Sửa:** bỏ cache, thêm `_con(app)` dùng `threading.local()` — mỗi luồng một
kết nối. Thay 11 chỗ gọi. Chi phí: `ket_noi()` đo được **0,24 ms/lần**
(5.264 SKU = 1,3 giây tổng), không đáng kể.

### 3. `tab_seo_post.py:351` — đụng tkinter từ luồng nền  *(cao)*

`app._sp_lb_tt.config()` gọi thẳng từ `_worker()`. Đây là **chỗ duy nhất
trong toàn repo** vi phạm quy tắc mà chính docstring của app đặt ra
("Luồng nền TUYỆT ĐỐI không đụng vào tkinter"); `man_hinh_du_lieu.py` bọc
`.after()` đúng ở cả 2 chỗ tương tự. Tkinter không thread-safe → treo/crash
ngẫu nhiên, không tái hiện theo ý muốn được.

**Sửa:** bọc qua `.after(0, ...)` như dòng tổng kết cuối hàm vẫn làm.

### 4. `render_phase2.py` — Hard Block chặn nhầm NGÀY THÁNG  *(cao)*

Phần đơn vị của `_CUM_KY_THUAT_RE` là **optional**, nên `\d+(/\d+)+` khớp
luôn ngày tháng. `kiem_tra_bia_toan_bo()` là **cổng cứng**: dính 1 field là
chặn **cả bài**, kể cả FAQ. Chạy thật với row MBA 250kVA:

    CHẶN  "Báo giá cập nhật ngày 22/08/2026."  -> ['22/08/2026']
    CHẶN  "Bảng giá tháng 8/2026"              -> ['8/2026']
    CHẶN  "Áp dụng từ 01/09/2026"              -> ['01/09/2026']

Mà framing "Bảng giá/Báo giá cập nhật tháng X" chính là dạng đang chạy tốt
nhất cho nhóm truy vấn báo giá → Hard Block đang chặn oan đúng nhóm bài
quan trọng nhất.

**Sửa:** thêm `_NGAY_THANG_RE` + `_la_ngay_thang()`, bỏ qua cụm chỉ khi đủ
**cả 3** điều kiện: không mang đơn vị kỹ thuật, khớp trọn khuôn ngày, không
chứa dấu thập phân. Kết quả đo sau vá:

| nhóm | trước | sau |
|---|---|---|
| ngày tháng (5 mẫu) | 5 chặn oan | **5/5 qua** |
| bịa số kỹ thuật (8 mẫu) | 8 chặn | **8/8 vẫn chặn** |
| số thật của record (4 mẫu) | 4 qua | **4/4 vẫn qua** |

Hàng rào **không thủng chỗ nào**. `22/0,4kV`, `3x120mm²`, `35/0,4kV`,
`100/5A`, `24 tháng`, `IEC 60076` đều bị chặn như cũ.

### 5. `xu_ly_anh.py` — ngưỡng 800px KHÔNG nằm trên đường upload  *(cao)*

`CANH_NGAN_TOI_THIEU = 800` và `laplacian_variance()` có sẵn từ lâu, nhưng
**chỉ được gọi từ `loc_kho_anh()`** — mà `loc_kho_anh()` chỉ có đúng 1 người
gọi là script CLI `loc_kho_anh.py` (`LOC-KHO-ANH.bat`). Đường upload thật
(`dang_anh_cua_bai` → `sang_webp` → watermark) **không có một lệnh kiểm kích
thước hay độ mờ nào**: `sang_webp()` chỉ THU NHỎ ảnh quá to, không CHẶN ảnh
quá nhỏ. Nghĩa là ngưỡng 800px trước bản này chỉ có tác dụng nếu người dùng
tự nhớ chạy file `.bat`.

**Sửa:** chèn cổng vào `dang_anh_cua_bai` ngay trước `sang_webp`. Đọc
`rong/cao` từ meta, thiếu thì mở file đọc bằng PIL. Dưới ngưỡng → không
upload, ô ảnh để trống (bài tự ẩn ô trống từ Ver 4.4). Thêm bộ đếm
`bo_qua_nho` xuyên suốt 2 tầng return. Đã kiểm bằng ảnh dựng thật:

    1200x900 -> upload      800x800  -> upload
    640x480  -> BỎ QUA      1500x300 -> BỎ QUA   (cạnh ngắn mới tính)

### 6. `run_tests.py` — runner chấm FAIL OAN 4 test đậu sạch  *(cao)*

Regex marker PASS chỉ nhận dạng chữ "PASS". Test viết bằng `unittest` in ra
`Ran 10 tests in 0.001s / OK` — **không có chữ PASS nào** — nên rơi xuống
nhánh `else` và bị chấm FAIL dù `exit=0`. Test kiểu bộ đếm sai cũng vậy:
`TONG SAI: 0` là ĐẬU nhưng không có chữ PASS.

4 test bị chấm oan: `test_v4415_sweep_rac`, `test_v4416_ux_va_retry`,
`test_v4417_chuyen_dataset`, `test_v46_patch`.

Hậu quả thật: bộ test báo 9 FAIL trong khi chỉ có 5 lỗi thật → người đọc quen
với "lúc nào chả đỏ" rồi bỏ qua cả lỗi thật.

**Sửa:** nới marker ĐẬU (unittest `OK` + `Ran N tests` + không `FAILED/ERROR`;
hoặc `TONG SAI: 0`). **Không đụng marker FAIL**, nên không thể làm lọt lỗi.

### 7. `tests/test_v36_phu_kien.py:72` — test đang BẢO VỆ lỗ rò giá  *(cao)*

Assert cũ: `kt('có định dạng giá tiền', '27.950.000 ₫' in h_vo)` — đòi khối
phụ kiện **phải in giá ra HTML**. Nhưng Ver 4.5 đã cố ý bỏ hẳn việc đọc
`gia_list` ở đây (`phu_kien_di_kem.py:156`: *"BỎ 'gia'. gia_list nằm trong
FIELD_CAM_TUYET_DOI"*), và Ver 4.6.2 phải thêm luật `sweep_rac` `gia_list_lo`
để đi DỌN giá đã lỡ đăng. Test này đang assert đúng cái hành vi mà 2 phiên
bản sau đó phải đi sửa.

**Sửa:** đảo assert — giá TUYỆT ĐỐI không được ra HTML. Kết quả: PASS 27 / FAIL 0.

### 8. `tests/test_v45_patch.py` — ghim cứng số phiên bản  *(cao)*

`kiem('phien_ban.PHIEN_BAN == 4.6.2', ...)` — mỗi lần bump `phien_ban.py` là
test đỏ dù không có lỗi gì. Đó chính là họ lỗi mà `phien_ban.py` sinh ra để
chống, nay lại tái phát trong test của chính nó.

**Sửa:** kiểm HỢP ĐỒNG (`PHIEN_BAN` là chuỗi, đúng dạng `x.y[.z]`) thay vì
ghim giá trị.

### 9. `tests/test_ver3_ui.py` — đếm tab lạc hậu  *(cao)*

Assert `tong_tab_con == 13`. Đếm THẬT dưới Xvfb là **14** (5 + 7 + 2). Con số
13 là của bản trước khi thêm tab "Ảnh bài viết (4.0)".

### 10. `chuan_hoa.py` (MỚI) — gom 9 bản `_bo_dau`  *(cao)*

`_bo_dau()` được định nghĩa lại ở **9 file với 6 thân hàm khác nhau**. Chia
làm 2 nhóm hành vi: 7 file CÓ `.lower()`, 2 file KHÔNG (`sinh_ma_noi_bo`,
`workspace_anh`). Cùng một cái tên, hai hành vi → so khớp ra kết quả khác
nhau tuỳ module, loại lỗi không bao giờ báo.

**Sửa:** file mới `chuan_hoa.py` với `bo_dau()` (hạ chữ) và
`bo_dau_giu_hoa()` (giữ hoa). Gỡ 9 định nghĩa cục bộ, thay bằng import
alias đúng nhóm cũ. **Đã chụp hành vi trước khi sửa rồi đối chứng sau:
9/9 KHỚP, 0 module lệch.**

Kiến thức phải giữ (đã chép vào docstring): NFD **không tách được `đ`**
(U+0111 là ký tự độc lập, không phải `d` + dấu), phải map `đ`/`Đ` bằng tay
TRƯỚC khi normalize, nếu không `r'\bdien\b'` trượt trong im lặng.

### 11. `.gitignore` — không chặn một file `.xlsx` nào  *(cao)*

Bản cũ chỉ có `cau-hinh.env` + `*.db`. Trong khi thư mục code chứa
`8MASTER_ENRICHED_Ver8.xlsx` (**có cột "Giá List (VNĐ)"**),
`LOTECH_V3_PROGRESS_TRACKER_VER49.xlsx`, `du_lieu_goc/` 6 file Excel sản
phẩm, `kienthuc/` JSON catalogue hãng. `git add .` = đẩy bảng giá nội bộ
Lotech lên repo công khai.

**Sửa:** chặn theo ĐUÔI FILE (`*.xlsx/*.xls/*.csv/*.pdf`) thay vì theo tên,
cộng `du_lieu_goc/`, `kienthuc/`, `catalogue/`, `output/`,
`anh-bang-chung-ui/`. Giữ ngoại lệ `!cau-hinh.env.MAU`. Đã kiểm bằng
`git check-ignore`: chặn sạch, template không bị chặn nhầm.

### 12. `cau-hinh.env.MAU` — dạy SAI tên biến  *(cao)*

Template cũ hướng dẫn điền `WP_SITE1_URL / WP_SITE1_USER / WP_SITE1_APP_PW`.
**Không có dòng code nào đọc 3 biến đó** (đã đổi sang `WP_WEBSITE_*` từ
Ver 3). Ai cài máy mới theo template cũ sẽ **không kết nối được WordPress**
và không hiểu tại sao. Ngoài ra thiếu 15 biến code thật sự có đọc.

**Sửa:** viết lại toàn bộ, 5 nhóm, đủ 38 biến, mọi giá trị mặc định lấy từ
source thật (`WATERMARK_STYLE=ket_hop`, `WATERMARK_TILE_ALPHA=52`,
`WP_WEBSITE_CHE_DO=post`...), liệt kê 4 giá trị hợp lệ của `WATERMARK_STYLE`.

## Đã BÁC BỎ — kết luận SAI của đợt audit, đừng làm lại

### A. "23 file test không thể fail, cần thêm `sys.exit(1)`" — **SAI**

`run_tests.py:236` **đã có** lưới bắt marker `FAIL: N` / `[FAIL]` trong
output, không chỉ chấm theo exit code. `test_v36_phu_kien` in `FAIL 1` và
**đã bị chấm FAIL đúng**. Vấn đề thật thì **ngược lại** — runner quá chặt ở
phía PASS, chấm oan 4 test đậu (xem mục 6). Thêm `sys.exit(1)` cho 23 file
là công vô ích và làm nhiễu.

### B. "Gom 6 bản `_so()` về `chuan_hoa.py`" — **SAI, không làm**

6 bản `_so()` **không phải một hàm bị chép 6 lần**, mà là 6 hàm khác nhau
trùng tên riêng:

| file | hành vi |
|---|---|
| `enrich_tcvn_mba` | `float()` trần, **cố ý ném lỗi** khi dữ liệu bẩn |
| `hinh_ky_thuat` | trả `None` nếu rỗng, bóc số đầu tiên |
| `khoi_chiu_tai` | lọc thêm sentinel `'nan'/'none'/'-'` |
| `kien_thuc_bien_thien` | bóc số đầu, không lọc sentinel |
| `phu_kien_di_kem` | thay `,` **trước** khi bóc → khác kết quả với `'1.500,5'` |
| `sinh_ma_noi_bo` | trả **chuỗi**, không phải float |

Gom lại = đổi hành vi thật ở 6 chỗ để đổi lấy cái đẹp mắt. Lý do đã chép
vào docstring `chuan_hoa.py` để lần sau không ai gom nhầm.

## KHÔNG sửa trong bản này — đã ghi vào KNOWN-ISSUES

- `record_id` gắn số dòng Excel → **kỷ luật APPEND-ONLY**. Mô phỏng: chèn 1
  dòng ở vị trí 100 của sheet 598 dòng → **500 record_id lệch**. Né bằng kỷ
  luật (0 công) thay vì đổi khoá (~1 ngày + migrate rủi ro).
- Lỗi 459 SKU sai thuộc tính `Cấp điện áp` **không do tool này** — payload
  Woo không hề có `attributes`. Sửa ở đây là sửa nhầm chỗ.
- Phạm vi hẹp của luật `sweep_rac` `gia_list_lo` — neo hẹp là chủ ý đúng,
  chỉ cần biết để không kỳ vọng quá.

## Nợ cấu trúc — CỐ Ý chưa đụng

`giao-dien.py` vẫn là 1 class `PhanMem` với **195 method / 5.344 dòng**; UI
RMU 6 tab cũ vẫn dựng đủ mỗi lần khởi động với `manager=NONE` (không pack,
chỉ vào được qua *Công cụ → Chế độ RMU*); `autopost.py` + `cauhinh.SITES`
vẫn là hệ thống song song thứ hai (~2.190 dòng). Tách file là việc 1–2 ngày
và **không sửa lỗi nào đang gây thiệt hại** — để nguyên có chủ đích.

---

# TÁI DỰNG NHẬT KÝ 4.5 → 5.4 — viết ngày 20/08/2026

> **Đọc kỹ dòng này trước khi tin phần dưới.** Mục này KHÔNG phải nhật ký
> viết lúc làm. Nó được **tái dựng ngược từ comment trong source code**
> ngày 20/08/2026, vì nhật ký thật đứt ở 4.4.1.7 (13/08) trong khi code đã
> đi tới 5.4 — **9 phiên bản không có bản ghi nào**.
>
> Mỗi mục dưới đây đều dẫn `file:dòng` làm bằng chứng. Cái gì code không
> nói ra thì ghi thẳng là *không rõ* — **không suy đoán, không lấp chỗ trống**.
> Ngày tháng của từng bản: **không rõ** (comment không ghi ngày). Chỉ thứ
> tự là chắc.
>
> Mức tin cậy tổng thể: **vừa** — chắc về *cái gì đã đổi*, không chắc về
> *đổi hết chưa* (thay đổi nào không kèm comment `Ver x.y` thì vô hình
> với cách tái dựng này).

---

## Ver 5.6 — Hard Block chặn nhầm số CÓ ĐƠN VỊ (21/08/2026)

> Mục này **viết LÚC làm**, không tái dựng ngược. Mức tin cậy: **cao** —
> mọi nhận định dưới đây đã chạy repro trên code thật trước khi sửa.

### Triệu chứng thật
Batch 14 SKU máy biến áp khô THIBIDI (sheet 03, dòng 583–596 của
`9MASTER_Ver17_SACH_TEXT_20260821.xlsx`) bị Hard Block chặn 5/5 dòng đầu:

```
[1/14] LTC-TBD-3P-160-KHO-DUC
   Hard Block chặn: dac_diem_html: ['2950W', '4%', '740W']
[3/14] LTC-TBD-3P-320-KHO-DUC
   Hard Block chặn: meta_description: ['1020W', '4%', '4620W']
```

MASTER dòng 583: Po=740, Pk=2950, Uk=4. **Mọi số bị chặn đều CÓ THẬT.**
Không có số nào bị bịa.

### Nguyên nhân (xác nhận-từ-code)
`render_phase2._kho_cua_dong()` chỉ chạy `_SO_DON_VI.findall(giá_trị)` —
regex này đòi số và đơn vị **dính liền trong GIÁ TRỊ**. MASTER lưu số trần
`"740"`; đơn vị nằm ở **TÊN CỘT** (`'Tổn hao không tải Po (W, catalogue)'`)
và ở **nhãn bảng** (`('ton_hao_khong_tai', 'Tổn hao không tải Po (W)')`).
`effective_cot_bang()` trả `(field, nhãn)` nhưng kho vứt nhãn đi:
`{k for k, _ in ...}`. Kết quả: kho số của cả record chỉ có `{'160kva'}` —
toàn bộ 10 cột enrich catalogue **vô hình** với Hard Block.

Nhánh `thong_so_dong` (cột quét động) **đã có** đúng cơ chế bóc đơn vị từ
tên cột từ Ver 2.8 (`render_phase2.py:1962`). Nhánh field khai báo thì
không. Đây là **thiếu sót thuần tuý, không phải quyết định thiết kế**:
Ver 5.4 thêm 10 cột catalogue vào `cot_import`, chính động tác đó kéo
chúng ra khỏi đường quét động đang chạy đúng, sang đường không có bóc
đơn vị.

Repro trên source trước khi sửa:
```
kho so    : ['160kva']
'Tổn hao 740W, ngắn mạch 2950W, Uk 4%' -> ['2950W', '4%', '740W']
```

**Bác bỏ một giả thuyết phụ:** dấu cách KHÔNG liên quan. `_SO_DON_VI` đã
có `\s*` nên `"740 W"` và `"740W"` bị chặn y hệt nhau (đã chạy thử).
Lý do một vài số lọt ở dòng 250kVA là lần đó AI viết **số trần không kèm
đơn vị** → `_SO_DON_VI` không bắt → không kiểm tra luôn.

### Đã sửa
- `render_phase2.py` — thêm `_DON_VI_TU_NHAN` (**whitelist** đơn vị),
  `_don_vi_tu_nhan()`, `_don_vi_theo_field()` (gộp nhãn `cot_bang` + tên cột
  `cot_import`, cache theo `(profile_id, outline_id)`).
  Dùng whitelist chứ không "mọi chữ cái trong ngoặc" vì nhãn thật trong
  Registry có `(E50)`, `(catalogue)`, `(giải mã)`, `(CO/CQ/Quatest)`,
  `(VNĐ)` — không phải đơn vị.
- `render_phase2.py` — `_chuan_gia_tri_so()` + `_chuan_don_vi()` chuẩn hoá
  **CẢ HAI PHÍA** trước khi so khớp: bỏ khoảng trắng, dấu phẩy thập phân VN
  → dấu chấm, cắt số 0 thừa (`4,0` = `4`), gộp `mm2`=`mm²`, `Ohm/km`=`Ω/km`.
  `_chuan_so()` và `_chuan_cum()` dùng lại 2 hàm này.
- `render_phase2.py` — vá `_kho_cua_dong()` và `_kho_mo_rong_cua_dong()`
  ghép số trần với đơn vị của nhãn. Kho mở rộng là chỗ làm chết `'4%'`.
- `render_phase2.py` — `_SO_DON_VI` thêm `mA`, `cm`.
- `cauhinh.py` — `MODEL_CHET = {'gemini-5.0-flash'}`, lọc trong
  `doc_gemini()`. Model này không tồn tại phía Google (HTTP 404) nhưng nằm
  trong `cau-hinh.env` của máy Thịnh, mà file đó cố ý KHÔNG nằm trong ZIP —
  nên phải lọc ở chỗ **đọc**, là chokepoint duy nhất mọi caller đi qua.
  Có xử case nó là model *chính*: đôn dự phòng lên thay vì trả rỗng (trả
  rỗng thì UI báo "chưa cấu hình AI" và dừng cả batch).
- `ai_wp_adapter.py` — `TIMEOUT_GEMINI = 20` (từ 45), áp cho `goi_ai_that`
  và `goi_ai_co_du_phong`. Đo trên batch thật: mỗi SKU mất ~100s chỉ để chờ
  2 lần timeout của cặp key/model chết. Gemini trả bài đạt trong 6–12s.
- `giao-dien.py:2329` — bỏ hard-code `timeout=45`, dùng `AWP.TIMEOUT_GEMINI`
  để UI và adapter không lệch nhau (đúng bài học của chính `phien_ban.py`).

### Không đụng gì
`cot_import` **không đổi một ký tự** → không phải chạy lại
`import_phase2_pipeline`, `column_structure` guard không bị kích hoạt.

### Test
`tests/test_v56_hardblock_don_vi.py` — 66 case, tất cả PASS.

5 case nghiệm thu bắt buộc:

| MASTER | AI viết | Kỳ vọng | Kết quả |
|---|---|---|---|
| `740` | `740W` | PASS | PASS |
| `740` | `740 W` | PASS | PASS |
| `4` | `4%` | PASS | PASS |
| `740` | `745W` | **CHẶN** | CHẶN |
| Cấp Điện Áp **RỖNG** | `22/0.4kV` | **CHẶN** | CHẶN |

Nhóm chống-nới-tay (quan trọng hơn 5 case trên — nới quá tay là hỏng cả hệ
thống chống bịa): sai đơn vị (`740kVA`/`740kV`/`740A`/`740kg`/`740mm`) →
chặn; lệch số (`7400W`/`74W`/`740.5W`/`2951W`/`5%`/`4.5%`) → chặn; số của
SKU khác (`1150W` ở dòng 583) → chặn; loại dữ liệu không field nào có
(`IP54`/`IEC 60076`/`24 tháng`/`40°C`) → chặn; **field rỗng thì đơn vị của
nhãn KHÔNG thành giấy phép** → chặn; cụm bịa (`9x50mm²`/`99/1kV`) → chặn;
lớp 4 đúng số nhưng sai họ đơn vị (`1A` từ cặp `0.6/1`) → chặn;
`gia_list` không sinh khoá nào trong kho.

Hồi quy: `run_tests.py` baseline trước sửa **PASS 74 / FAIL 11**, sau sửa
**PASS 75 / FAIL 11** (đúng 11 FAIL cũ y hệt: thiếu `fitz`, thiếu `scrot`,
path `/mnt/data`, và vài file `exit=0` bị runner phân loại nhầm từ trước).
**Không có hồi quy.**

`tests/test_v43_hotfix.py` sửa **1 assert**: nó neo cứng vào chuỗi
`'timeout=45'` trong source `giao-dien.py`. Ý nghĩa test không đổi (vẫn
kiểm UI truyền timeout + persist model thắng cuộc), chỉ đổi chuỗi neo sang
`'timeout=AWP.TIMEOUT_GEMINI'`.

### Còn nợ (cố ý để ngoài phạm vi)
1. `hieu_suat_e50` — cột `'Hiệu suất năng lượng tối thiểu E50 (catalogue)'`
   **không khai đơn vị** trong tên cột, nên AI viết `"98.5%"` vẫn bị chặn dù
   giá trị có thật. Sửa đúng = đổi tên cột MASTER thành `(%, catalogue)` →
   **đụng `cot_import`**, phải chạy lại `import_phase2_pipeline`.
   (mức tin cậy: **suy ngược** — cùng họ lỗi, chưa gặp trong log thật vì
   cột này đang rỗng ở hầu hết SKU.)
2. Cố ý **KHÔNG** thêm đơn vị `m` trần vào `_SO_DON_VI` dù nằm trong danh
   sách yêu cầu: `"cuộn 100 m"`, `"dài 500m"` là văn nói bình thường trong
   bài cáp, mà không field nào có nhãn `(m)` → thêm vào sẽ đẻ ra đúng họ
   false-positive mà bản này đang đi sửa, đổi lại **zero** lợi ích chống
   bịa. `°C` cũng không thêm vì `_CUM_MO_RONG_RE` đã bắt sẵn.
3. `VNĐ`/giá không nằm trong `_SO_DON_VI` nên số tiền AI viết không bị Hard
   Block kiểm — **hành vi CŨ, không đổi ở bản này**. Chặn giá bịa đang do
   `sweep_rac`/`MAU_RAC` lo.

## Ver 5.4 — Serper.dev + 10 cột catalogue MBA

- `enhance.py:40,53` — Google đóng Custom Search JSON API với project MỚI
  (403 PERMISSION_DENIED vĩnh viễn). Đổi nguồn sang **Serper.dev**. Hằng số
  `GOOGLE_CSE_URL` giữ lại chỉ để tham chiếu, không gọi tới nữa.
- `profiles.py:259,461` + `prompts_phase2.py:272` — nối **10 cột enrich thật**
  từ `catalog_may_bien_ap_dau_mbt.pdf` vào profile MBA và vào prompt AI.
- `profiles.py:274` — khai 2 field **Bảo hành / Chứng nhận**, nhưng MASTER
  hiện CHƯA có cột này (vẫn 0 dữ liệu). Khai trước, chờ số.
- `profiles.py:324` — bảng thông số chỉ hiện khi SKU có enrich thật, không
  in bảng rỗng.

## Ver 5.3 — Chiều sâu nội dung + Hard Block siết lại

- `ai_wp_adapter.py:460` — **VÁ**: Hard Block chặn nội dung CỐT LÕI giờ
  FAIL NGAY thay vì đi tiếp. (`:497` ghi rõ: không nới Hard Block.)
- `giao-dien.py:1907` — **VÁ LỖ HỔNG THẬT**: bài đã có `wp_id` trước đây bị
  BỎ QUA vĩnh viễn ở mọi bản sau → mọi cải tiến content/UI từ 5.0 trở đi
  không bao giờ chạm được bài cũ. Giờ sinh lại nội dung + cập nhật.
- `render_phase2.py:1203,1217` — khối kiến thức về **loại lõi** (Silic/Amorphous),
  tách bạch với cấp điện áp.
- `render_phase2.py:1390` — khối **Bảo trì & lắp đặt** riêng.
- `render_phase2.py:1467,1681` + `profiles.py:142,232,258,370` — nút
  **"Tải Catalogue/Datasheet (PDF)"**, chỉ hiện khi có link PDF thật. Cột
  `Catalogue PDF URL` thêm vào 3 profile.
- `render_phase2.py:1491` — **VÁ theo phản hồi thật**: khối sản phẩm liên quan
  trước đây "vứt 1 chùm link dạng gạch đầu dòng".
- `validators.py:104` — **VÁ HỒI QUY**: 5.2 tách outline vỏ mạ kẽm làm hỏng
  validator, 5.3 sửa lại.
- `db_phase2.py:138` — chống Enhance sinh insight na ná nhau giữa các SKU
  cùng nhóm (tái tạo đúng lỗi boilerplate đã vá).

## Ver 5.2 — Sửa theo ảnh chụp site thật

Cả bản này là hệ quả của việc Thịnh mở site lên xem bằng mắt. Đáng ghi nhớ.

- `render_phase2.py:1166` — bảng/liên kết in ra toàn mã kiểu `MBTVM3P50`,
  *"người ta đéo biết đâu"*. 5.0 mới làm cho link **bấm được**; 5.2 mới làm
  cho nó **đọc được** (dùng tên sản phẩm).
- `db_phase2.py:676,683,691` — `tim_san_pham_cung_dong` trước chỉ áp dụng cho
  `outline_may_bien_ap`; mở rộng + trả `ten_goc`.
- `profiles.py:476,536` + `prompts_phase2.py:122` — tách **outline riêng cho
  "Vỏ mạ kẽm nhúng nóng MBA"**; trước đó nó bị viết như MÁY biến áp.
- `render_phase2.py:939,949` — **VÁ**: "tải ước tính (kW)" chỉ có nghĩa với
  MÁY biến áp thật, không áp cho vỏ.
- `render_phase2.py:1002` — vá 2 lỗi title phát hiện qua ảnh chụp.
- `render_phase2.py:1542` — CTA: *"khách nhấn vào là bắt luôn, không cho thoát"*.

## Ver 5.1 — Đợt vá sau audit lại tool

Bản này sinh ra từ một lần audit chủ động (`Audit-Checklist-Ver5.0`), không
phải từ sự cố. 65 mốc comment — bản dày nhất trong 5 bản.

- `giao-dien.py:2197` — ô **"Nghỉ giữa 2 bài"** có trên giao diện từ lâu
  **nhưng chưa bao giờ được đọc**. Vá + đọc trên luồng chính, không đọc
  StringVar trong luồng nền (`:2121`, `:4017`).
- `giao-dien.py:2218,2232` — ma trận key/model dự phòng trước chỉ có
  (key chính × model phụ); bổ sung **mọi key phụ × mọi model phụ**.
- `nhap_phase2.py:257`, `render_phase2.py:377` — 2 SKU có Tên hàng bất thường
  làm vỡ luồng, phát hiện khi audit.

## Ver 5.0 — Xuống dòng, liên kết nội bộ, sửa title

- `render_phase2.py:997` — **VÁ**: bản 4.9.9 nhét cả mã hàng vào title.
- `render_phase2.py:1164` — thêm link khi SKU anh em **đã đăng thật** (có URL).
- `prompts_phase2.py:111` — bắt AI viết **2-3 đoạn `<p>` ngắn**, không dồn
  một khối chữ liền.
- `giao-dien.py:4680` — xem HTML thô trong ô Text khó hình dung → thêm đường xem.
- `ai_wp_adapter.py:255` — vá theo **log production 30/07/2026**.
- `db_phase2.py:683` — Thịnh xem thật thấy *"mã hàng ai biết"*.
- `render_phase2.py:1666` — ô ảnh placeholder cho ảnh sản phẩm chính.

## Ver 4.6.2 — Cổng chất lượng + dọn rác

- `hang_doi.py:166` — **cổng chất lượng viết ở 4.6 nhưng chưa có đường bấm**;
  4.6.2 mới nối nút vào.
- `hang_doi.py:301` — "Soát mỏng/trùng": dựng thử bài của SKU đang chọn rồi
  đo MỎNG/TRÙNG *trước khi* đốt quota.
- `sweep_rac.py:55` — **GIÁ LIST LOTECH lộ ra HTML công khai** → thêm luật dọn.
- `sweep_rac.py:65` — caveat A2608 (câu rào đón nội bộ) lọt ra bài bán hàng.
- `render_phase2.py:1042` — CÁP ĐIỆN: trước lấy nguyên Tên hàng làm title.
- `tab_anh.py:429` — gỡ ảnh của nhiều bài cùng lúc.

## Ver 4.6.1 — `va_chinh_ta.py`

- `va_chinh_ta.py:2` — công cụ vá lỗi text trong MASTER. Bản 1 file, 1 việc.

## Ver 4.6 — WooCommerce thành luồng đăng chính + cổng chất lượng

Đây là bản đổi kiến trúc lớn nhất trong cả đoạn 4.5→5.4.

- `cong_chat_luong.py:2` — **file mới**: cổng chặn bài MỎNG và bài TRÙNG,
  chạy TRƯỚC khi render (tức trước khi tốn quota).
- `ai_wp_adapter.py:568` — **Save Draft THẬT vào WooCommerce** (`/wc/v3/products`)
  thay vì post thường.
- `giao-dien.py:2424` + `cauhinh.py:262` — Woo thành luồng đăng CHÍNH cho site
  đã bật; `che_do_dang` mặc định vẫn `'post'` cho site khác.
- `giao-dien.py:1620,1724` — dropdown "Loại đăng".
- `autopost.py:632,662` — tra product id theo SKU; dự phòng khi sản phẩm không có SKU.
- `ai_wp_adapter.py:335,364,536` — **JSON parse được ≠ đủ nội dung để đăng**;
  thêm `kiem_tra_chat_luong_text` chặn chuỗi quá ngắn/quá dài bất thường.
- `khoi_chiu_tai.py:2` + `render_phase2.py:17,1749` — **file mới**: khối
  "chịu tải bao nhiêu" cho `outline_cap_dien`, đặt TRƯỚC các khối kiến thức.
- `profiles.py:168,192,208,413` — thông số ĐIỆN bóc từ catalogue CADIVI hạ thế,
  cho AI thấy để viết bám số.
- `ra_soat_dien_ap.py:2` — **file mới**: rà bộ lọc cấp điện áp trên sheet cáp.

## Ver 4.5.1 — MASTER đổi cột thì không chết nữa

- `db_phase2.py:188,226` + `giao-dien.py:4444,4479,4494` + `nhap_phase2.py:453` —
  nói RÕ cột nào thêm/bớt và **cho đi tiếp sau xác nhận** khi chỉ THÊM cột.
  (Đây là gốc của quy tắc: đổi `cot_import` phải chạy `import_phase2_pipeline`
  trên MASTER thật trước khi đóng gói.)
- `sinh_ma_noi_bo.py:2` — **file mới**: sinh mã nội bộ Lotech cho dòng
  catalogue không in SKU.
- `db_phase2.py:787` — vá theo GPT review độc lập, 5 điểm.
- `render_phase2.py:1522` — `id="lien-he-bao-gia"` làm đích neo thật cho CTA.

## Ver 4.5 — Gom chuỗi phiên bản + Block 5/6

- `phien_ban.py` — **file mới**, nguồn duy nhất chuỗi phiên bản.
  *(Mỉa mai: chính file này sau đó đứng im ở 4.6.2 suốt 9 bản.)*
- `render_phase2.py:1452,1482,1610` — **Block 5** (checklist báo giá theo
  profile) + **Block 6** (sản phẩm liên quan).
- `render_phase2.py:297,2109,2127` — cờ **nhường schema cho Rank Math**.
- `render_phase2.py:459` — dùng cột `Slug chỉ định` của MASTER nếu có.
- `render_phase2.py:814` — **VÁ**: trước đọc `25/40/63MVA` ra 25 kVA — **sai
  1.000 lần**.
- `phu_kien_di_kem.py:156` — bỏ `gia` khỏi khối phụ kiện (`gia_list` thuộc
  `FIELD_CAM_TUYET_DOI`). *Lưu ý: rò giá vẫn xảy ra và phải vá lại ở 4.6.2 —
  guard khai đúng không có nghĩa là đường render đã sạch.*

---

## Cái tái dựng này KHÔNG nói được

Ghi ra để lần sau không tưởng nhầm là đã đủ:

1. **Ngày tháng từng bản** — không có trong comment.
2. **Thay đổi không kèm comment `Ver x.y`** — hoàn toàn vô hình.
3. **Cái gì đã XOÁ** — code bị gỡ thì không để lại dấu vết nào.
4. **Bản nào đã test tới đâu** — `tests/test_v5{0,1,2,3}_patch.py` tồn tại,
   nhưng **không có `test_v54`**. Ver 5.4 hiện **chưa có test riêng**. Tin cậy: cao.

---
---

# Ver 4.4.1.7 — 13/08/2026 — DATASET MỚI KÉO THEO BÀI ĐÃ ĐĂNG

## Bug được sửa — nghiêm trọng nhất còn sống trong codebase
`xac_nhan_dataset()` tắt `active` của dataset cũ rồi tạo dataset mới,
nhưng `bai_viet_phase2` và `article_jobs` **vẫn trỏ dataset CŨ**.
`dashboard()` JOIN theo `dataset_id` nên trả rỗng → `site`/`mau`/`wp_id`
thành None → mọi chức năng cần identity chết.

**Loại bug tệ nhất: không có cảnh báo nào.** App chạy êm ru, chỉ lộ ra khi
bấm đúng một nút. Sự cố thật 13/08/2026: sửa 2 ô SKU trong MASTER → import
lại → 245 bài mồ côi → "thiếu identity DB, bỏ qua an toàn" 245/245 → mất
nửa ngày mới truy ra nguyên nhân.

## Vì sao chuyển được
`record_id` = `profile::sheet::dòng::sku` — **không chứa dataset_id**. Nên
record giữ nguyên định danh qua các lần import; chỉ record bị sửa SKU hoặc
đổi số dòng mới lệch. Sự cố 13/08: 243/245 khớp nguyên vẹn.

## Đã làm
1. **`db_phase2.chuyen_bai_sang_dataset_moi()` (MỚI)** — kéo
   `bai_viet_phase2` + `article_jobs` sang dataset mới theo `record_id`.
2. **`nhap_phase2` gọi ở bước 9b**, SAU `ghi_san_pham()` — trước đó dataset
   mới chưa có sản phẩm nào để đối chiếu `record_id`.
3. **`giao-dien` in ra rõ ràng**: chuyển được bao nhiêu, mồ côi bao nhiêu,
   và **liệt kê record mồ côi CÓ wp_id** — đó là bài thật trên WordPress
   sắp mất liên kết, phải kiểm tay.

## An toàn
- CHỈ chuyển `record_id` có trong `san_pham_phase2` của dataset mới —
  không vi phạm khoá ngoại.
- Record không khớp: **để nguyên, không xoá**, báo cáo ra ngoài.
- Trùng khoá chính ở dataset mới: **bỏ qua, không ghi đè** bản đang sống.
- Chạy lại lần hai không làm gì thêm.
- **Không raise** — import không được chết vì bước này; lỗi thì rollback
  và ghi vào báo cáo.

## Ghi chú khi viết test
`INSERT OR IGNORE` trong fixture **nuốt luôn lỗi NOT NULL**, khiến
`san_pham_phase2` không được ghi rồi `bai_viet_phase2` vỡ khoá ngoại ở tận
dòng dưới — mất công truy ngược. Fixture giờ ghi đủ mọi cột NOT NULL và
không dùng `OR IGNORE`. Tương tự, test `article_jobs` trước bọc
`try/skipTest` — test bị skip là test không kiểm gì; đã bỏ, schema đổi thì
phải ĐỎ. Cột `wp_id` kiểu **TEXT**, không phải INTEGER.

---

# Ver 4.4.1.6b — 13/08/2026 — GỠ BÓ DÂY UPLOAD (sửa lỗi của chính 4.4.1.6)

## Lỗi của bản 4.4.1.6
4.4.1.6 thêm retry 403 vào `ai_wp_adapter.upload_anh_media`. Nhưng dự án
có **HAI** hàm upload ảnh, cùng gọi `POST /wp-json/wp/v2/media`:

| Hàm | Số caller | Ai gọi |
|---|---|---|
| `autopost._url_anh_tren_wp` | **4** | tab_anh:719, tab_anh:987, giao-dien:2396, autopost:323 |
| `ai_wp_adapter.upload_anh_media` | **1** | giao-dien:3513 |

Retry được thêm vào hàm **1 caller**. 403 thực tế người dùng gặp đi qua
hàm **4 caller** — nhận diện được vì thông báo trong log là
`RuntimeError: Tải ảnh lỗi 403`, đúng chữ của `_url_anh_tren_wp`.
Sửa một sợi trong bó dây rồi tưởng đã sửa cả bó.

## Sửa
`wp_http.py` (MỚI) là **SỢI DUY NHẤT chạm mạng** khi upload ảnh. Chứa
retry + `tom_tat_loi()`. Hai hàm trên giữ NGUYÊN chữ ký và NGUYÊN kiểu
ngoại lệ (`_url_anh_tren_wp` vẫn `raise RuntimeError` — 4 caller đang bắt
nó, đổi sang trả dict là phá cả 4 cùng lúc), nhưng bên trong đều gọi
xuống `wp_http`.

`wp_http` KHÔNG import `autopost`/`ai_wp_adapter` — cả hai import ngược
lên, vòng import là vỡ lúc khởi động.

## Test chốt lại, không cho tái phát
`test_chi_mot_noi_goi_endpoint_media` quét toàn bộ file .py, fail nếu có
file nào ngoài `wp_http.py` gọi thẳng endpoint upload. Thêm đường thứ ba
là suite đỏ ngay.
(Regex phân biệt `/v2/media` — upload binary — với `/v2/media/{id}` —
cập nhật alt/title, việc khác, không tính.)

---

# Ver 4.4.1.6 — 13/08/2026 — TỰ CHỮA LỖI + THƯ MỤC DỮ LIỆU CHUNG

Gồm cả Ver 4.4.1.5 (dọn rác bài đã đăng).

## 1. DB rỗng `html` → đọc bài thật từ WordPress  (`tab_anh.py`)
Trước: gặp record không có HTML trong DB là dừng hẳn — *"DB không có HTML
bài đã đăng; không đoán vị trí ảnh"*. Trong khi bản THẬT đang nằm trên
WordPress, chỉ cần đọc về. Giờ tự GET `content.raw` (không lấy `rendered`
— đã qua wpautop/shortcode, PUT ngược là hỏng bài), chèn ảnh, PUT lại, và
**lưu HTML về DB** để lần sau khỏi gọi mạng.

## 2. Upload ảnh tự thử lại  (`ai_wp_adapter.upload_anh_media`)
Bằng chứng từ log 13/08: media_id 2105-2108 OK, `hero`+`bien_may` ăn 403,
rồi 2109-2111 lại OK. **Lỗi lỗ chỗ = chặn theo tốc độ, không phải sai
quyền** (sai quyền thì hỏng toàn bộ). Giờ thử lại 4 lần, giãn 2s→5s→11s
kèm nhiễu ngẫu nhiên để nhiều ảnh trượt không dội lại server cùng lúc.
401/413 thì **dừng ngay** — thử lại vô nghĩa, chỉ tổ đập server.

## 3. Log lỗi HTTP không còn bị cắt 200 ký tự  (bug tồn đọng)
200 ký tự đầu của trang chặn toàn là `<!DOCTYPE html><meta viewport…`.
Thêm `tom_tat_loi_http()`: bóc `<title>`, dò `mod_security`/`Reference #`,
và **giữ header nhận diện** (`Server`, `CF-Ray`, `X-Sucuri-ID`,
`Retry-After`) — đó mới là chỗ chỉ ra ai chặn.

## 4. GET verify sau khi gắn ảnh  (bug tồn đọng #1)
HTTP 200 chỉ nói request được nhận, KHÔNG nói ảnh đã dính. Giờ đọc lại sản
phẩm, đối chiếu từng media id. Verify **không được biến thành công thành
thất bại**: GET hỏng thì vẫn `ok=True` kèm cảnh báo.

## 5. Ảnh đại diện bị thay ngầm  (bug tồn đọng #3)
Hero upload lỗi thì một ảnh khác **lặng lẽ** lên làm ảnh đại diện. Giờ
verify phát hiện `images[0]` khác ảnh đã gửi và **báo rõ** trước khi bỏ
noindex.

## 6. Hộp thoại lỗi đọc được  (`_gom_loi_anh`)
Trước: đổ nguyên HTML trang chặn vào mặt người dùng. Giờ gom theo LOẠI —
*"3 ảnh chưa lên được: Bị chặn ở tầng server (403) — bấm lại"* — chi tiết
kỹ thuật đẩy xuống Nhật ký.

## 7. `phase2-du-lieu.db` + `cau-hinh.env` ra `%APPDATA%\SONEALEO\`
Hết copy tay giữa các thư mục version. Di cư TỰ ĐỘNG lần đầu chạy, **copy
chứ không di chuyển**, bản cũ đổi tên `.da-chuyen-doi` để lùi được.
**Thư mục chung LUÔN thắng** — không bao giờ đè dữ liệu đang sống bằng file
cũ (đúng kiểu mất dữ liệu âm thầm mà copy tay ngược chiều gây ra).
Ép đường dẫn khác qua biến `SONEALEO_DATA_DIR`.

### 7b. Hệ quả bắt buộc phải xử — `run_tests.py`
DB ra thư mục chung nghĩa là sandbox copy-code-sang-temp **không còn đủ để
cách ly**: mọi test sẽ trỏ vào DB THẬT và ghi đè. Runner giờ ép
`SONEALEO_DATA_DIR` vào trong sandbox từng process. Không có bước này thì
chạy test = phá DB production.

## KHÔNG sửa (có chủ ý)
- **Hard Block chặn `1kVA`** — guard chạy ĐÚNG, nó ngăn bài sai công suất.
- **403/Gemini timeout** — phía host và phía Google, không phải lỗi code.
- **17 SKU trùng, 19 SKU sai outline** — lỗi DỮ LIỆU, cần người quyết.
- **Caveat QĐ 2608** — số nghi sai, không phải rác.

---

# Ver 4.4.1.5 — 13/08/2026 — DỌN RÁC BÀI ĐÃ ĐĂNG

## Vì sao có bản này
Bài production trên maybienapvn.vn còn hiện "ô chờ ảnh" — hướng dẫn chụp
ảnh nội bộ cho khách đọc: *"Chụp thẳng tấm nhãn kim loại trên thân máy…
Ảnh này chứng minh thông số phía trên là số thật, không phải chép
catalogue"*, *"Tỷ lệ 3:2 ngang · tối thiểu 1200×800px"*.

## Nguyên nhân gốc
`khoi_anh.cho_anh()` và `render_phase2.khoi_anh_placeholder()` đã trả `''`
từ Ver 4.4 — **bài sinh mới không còn bị**. Rác là của bài sinh TRƯỚC 4.4.

Chỗ đáng lẽ dọn được lại không dọn: `xu_ly_anh.chen_anh_vao_bai()` chỉ gọi
`_thay_slot_legacy()` khi role đó **có ảnh thật** (`if not fig: continue`,
dòng ~604). Role thiếu file thì ô ở nguyên. Cuối hàm có dọn marker
`SNL_IMAGE_SLOT` và comment `URL_ANH` nhưng **bỏ sót `div.snl-cho-anh``**.

Bẫy regex: `div.snl-cho-anh` **có div lồng bên trong**
(`div.snl-cho-anh-ten`), nên `.*?</div>` dừng ở thẻ đóng của div CON và để
lại đuôi rác. Phải neo theo `<p class="snl-cho-anh-kt">` — đúng cách
`_thay_slot_legacy` đang làm.

## Đã làm
1. **`sweep_rac.py` (MỚI)** — `don_rac_bai()` là hàm thuần (vào chuỗi, ra
   chuỗi + thống kê). Mọi mẫu rác khai trong `MAU_RAC`: thêm rác mới =
   thêm 1 dòng, không sửa logic. Kèm `quet_1_bai()` / `quet_hang_loat()`,
   **mặc định `chi_thu=True`** (chỉ đọc, không ghi).
2. **`ai_wp_adapter.doc_noi_dung_bai_that()` (MỚI)** — adapter trước đây
   chỉ có đường GHI, không có đường ĐỌC. Sweep phải đọc HTML **thật trên
   WP**, không lấy từ SQLite: DB có thể lệch bản đang sống. Lấy
   `content.raw`, **không lấy `rendered`** (đã qua wpautop/shortcode, PUT
   lại là hỏng bài).
3. **`xu_ly_anh.chen_anh_vao_bai()`** — cuối hàm gọi `SR.don_rac_bai()`.
   Đặt ở đây vì `giao-dien.py:2504` gọi `chen_anh_vao_bai(html, [])` **kể
   cả khi không có ảnh nào** → mọi lần đăng/đăng lại đều đi qua. Bọc
   try/except, lỗi sweep không được làm hỏng luồng đăng ảnh.
4. **`khoi_anh.O_ANH` — XOÁ HẲN.** Dict 5 ô chứa toàn văn hướng dẫn chụp
   ảnh, code chết từ Ver 4.4. Để lại thì lần sau rất dễ nối lại: chuỗi vẫn
   nằm đó, chỉ thiếu 1 dòng `return`.
5. **Nút "🧹 Dọn rác bài đã đăng"** ở tab Dashboard, cạnh "Gỡ bài hàng
   loạt". **Bắt buộc 2 bước**: chạy thử (chỉ đọc, báo số) → xem số → mới
   hỏi ghi thật. Chỉ ghi lên những bài thật sự có rác.
6. **Test cũ sửa theo**: `test_v33_bo_cuc.py` và `test_v37_anh.py` trước
   assert `sorted(KA.O_ANH) == sorted(WS.ma_vai_tro(...))`. Đảo ý: giờ
   assert `not hasattr(KA, 'O_ANH')` — dict **không được quay lại** — và
   `workspace_anh` là nguồn sự thật duy nhất về bộ vai trò ảnh.

## KHÔNG làm trong bản này (có chủ ý)
- **Không đụng caveat "chưa đối chiếu QĐ 2608/QĐ-EVN SPC".** Đó KHÔNG phải
  rác — là cảnh báo Po=31W / Pk=570W chưa đối chiếu đúng quyết định ghi
  trên tiêu đề. Xoá cảnh báo mà không kiểm số = giấu lỗi. Chuỗi đến từ cột
  `nguon_tieu_chuan_vien_dan` trong MASTER (`render_phase2.py:238`), sửa ở
  Excel. Câu mâu thuẫn cuối bài ở `kien_thuc_bien_thien.py:276`.
- **Không đụng nội dung do `enhance` sinh** (`khoang_trong_noi_dung`,
  `goc_nhin_bundle_cheo`, badge "Khảo sát thị trường") — chưa chốt scope.

---

# Nhật ký thay đổi

Bản mới nhất nằm trên cùng. Ai sửa ghi ở cột cuối.

Từ v2.5: mỗi ZIP kèm đủ 4 file — `SPEC.md`, file này (= CHANGELOG),
`KNOWN-ISSUES.md`, `TEST-REPORT.md`. Theo dõi tiến độ tổng thể xem
`TIEN-DO.md`.

---

## Ver 3.7 — 2026-08-08 — Workspace ảnh theo bài (đợt 1) — Claude

**Vấn đề**: module ảnh cũ (`anh_san_pham.py`) ĐOÁN SKU từ tên file và
đường dẫn. Đo trên kho thật: ghép sai nhiều, phần lớn ra generic — không
dùng được. Vấn đề không nằm ở thuật toán đoán mà ở chỗ đoán là sai hướng:
kho ảnh công ty không mang đủ thông tin để suy ra SKU.

Đổi hướng: **mỗi bài một thư mục riêng, thư mục tự khai mình thuộc bài nào
qua `meta.json`**. Người dùng ném ảnh vào bằng mắt — việc mà mắt làm trong
3 giây còn AI làm sai trong 3 giây. Tool lo phần cơ khí: WebP, đổi tên,
alt, upload, gắn vào bài.

**KHÔNG GỌI AI.** Toàn bộ đợt này chạy 100% khi mất mạng AI hoàn toàn.

### File mới

| File | Dòng | Việc |
|---|---|---|
| `workspace_anh.py` | 330 | Thư mục theo bài, `meta.json`, gán/đổi/gỡ ô, trạng thái |
| `xu_ly_anh.py` | 215 | WebP có ngưỡng KB, tên file, alt, thẻ img, đăng |
| `tab_anh.py` | 300 | Tab 3 cột: danh sách bài, 5 ô, thao tác |
| `tests/test_v37_anh.py` | 150 | 47 assertion, PASS 47/0 |

### Quyết định thiết kế

**`meta.json` là nguồn sự thật duy nhất.** Tool KHÔNG đọc tên thư mục để
suy ra bài — người dùng rename thư mục thoải mái, ảnh không mồ côi. Tên
thư mục `042 - May bien ap dau THIBIDI 250kVA - TBD3P250` chỉ để người
nhìn Explorer cho dễ; số thứ tự lấy từ số dòng MASTER, cố định.

**Vai trò ô khai theo profile, ba profile để TRỐNG.** Máy biến áp chốt 5 ô
(hero · bien_may · can_canh · lap_dat · giao_hang). Cáp, tủ, phụ kiện
KHÔNG tự đoán — đóng đinh 5 vai trò của máy biến áp cho cả 5.264 SKU là
lặp lại đúng lỗi `bep_truong._TRUC` bản đầu.

**Tách `hash` và `hash_goc`** — test bắt ra lỗi thiết kế này. Chúng trả lời
hai câu khác nhau: `hash` = "file trên đĩa có bị thay không" (phát hiện
trạng thái `lech`), `hash_goc` = "tấm này có đang dùng ở bài khác không".
Sau khi xử lý sang webp thì `hash` đổi, nếu dùng chung một trường thì mất
khả năng đếm dùng chung.

**Trạng thái `lech`** — đã đăng rồi thay file trong thư mục. Không có
trạng thái này thì người dùng thay ảnh xong không bao giờ biết bài trên web
vẫn đang dùng ảnh cũ.

**Chống upload lặp ngay đợt 1.** Bấm Đăng lần hai không upload thêm bản vô
nghĩa: ảnh `da_dang` và hash không đổi thì bỏ qua.

**Không replace binary trên WP Media.** Ảnh mới upload thành media mới rồi
đổi liên kết. Media cũ có thể đang dùng ở nơi khác.

**Tái sử dụng một tấm cho nhiều bài: CHO PHÉP, chỉ báo số lượng.** Kho ảnh
công ty vốn ít; chặn thì người dùng bí, giấu thì người dùng không biết mình
đang loãng tài sản hình ảnh.

**Gỡ ảnh khỏi ô KHÔNG xoá file.** Tool không tự xoá dữ liệu người dùng.

### SEO ảnh — sinh bằng code, không AI

- Tên file `{slug}-{vai_tro}.webp`. Tên trên đĩa khoá theo SKU, tên trên
  web khoá theo slug — slug đổi thì chỉ chạy lại lượt upload.
- Alt **mỗi vai trò một câu khác nhau**; 5 alt giống hệt nhau là nhồi từ
  khoá. Chỉ chèn thông số có dữ liệu thật.
- Ảnh hero KHÔNG lazy-load (nó là LCP), từ ảnh thứ hai trở đi mới lazy.
- Mọi thẻ `img` khai `width`/`height` chống giật layout.
- WebP hạ chất lượng dần cho tới khi dưới 150KB — `anh_san_pham.toi_uu_anh`
  cũ nén một lần với quality cố định, không đảm bảo dung lượng.

### Sửa kèm

`khoi_anh.py` từ 3 ô lên 5 ô, đổi `chi_tiet` -> `can_canh` cho cùng tên với
`workspace_anh`. `giao_dien_2_5` chèn đủ 5 chỗ chờ ảnh. Placeholder GIỮ
NGUYÊN — nó là checklist cho người quản trị, không phải lỗi hiển thị.

### Tái dùng, không viết lại

`anh_san_pham.toi_uu_anh()` (ý tưởng resize+WebP) và
`autopost._url_anh_tren_wp()` (upload WP Media, đã có cơ chế nhớ). Phần
đoán SKU từ tên file thì bỏ hẳn — thiết kế mới không cần đoán.

### Chưa làm (đợt sau)

Kéo thả từ Explorer (`tkinterdnd2`), AI gợi ý ảnh, lưới thumbnail kho ảnh
chung, bộ vai trò cho cáp/tủ/phụ kiện.

### Test

`test_v37_anh.py` 47/47. `run_tests.py` -> **43 file PASS / 4 FAIL**, đúng
4 file FAIL sẵn có của nền.

## Ver 3.6.4 — 2026-08-08 — Đợt vá lớn (14 mục) — Claude

### A. Sửa lỗi do chính tao gây ra

**A1. `bep_truong._TRUC` khai tên field BỊA cho 3 profile.** Bản đầu khai
`so_loi`, `dien_ap_dinh_muc`, `dong_dinh_muc`, `cap_bao_ve`, `kich_thuoc_a`,
`tiet_dien_ap_dung`, `kieu_thi_cong`, `vat_lieu`... — **không field nào tồn
tại trong `profiles.py`**. Chỉ `may_bien_ap_do_luong` khớp vì đó là profile
duy nhất được mở ra đọc lúc viết.

Hậu quả: 5.096/5.264 SKU bị chấm ĐÓI, và con số đó bị báo ra như tình trạng
DỮ LIỆU trong khi nó là tình trạng của đoạn khai báo. Khai lại toàn bộ bằng
field đối chiếu trực tiếp với `cot_import`:

| | Trước | Sau |
|---|---|---|
| ĐỦ | 155 | **324** |
| VỪA | 18 | 3.952 |
| ĐÓI | **5.096** | **988** |

Thêm test khoá: mọi trục phải tồn tại trong `cot_import` của profile.

**A2. Dấu `≤` áp nhầm cho Uk.** Bảng TCCS 10:2021/EVN (Điều 20/38/56) ghi
tiêu đề cột nguyên văn *"Điện áp ngắn mạch **nhỏ nhất** (Uk) (%)"* — Uk là
giá trị SÀN, không phải trần. In `≤ 2` là ngược dấu.

Về vật lý: Po/Pk thấp hơn trần là tốt; Uk thấp hơn thiết kế thì dòng ngắn
mạch CAO hơn, tức xấu đi. Kỹ sư dùng Uk để tính dòng ngắn mạch chọn máy cắt
và kiểm điều kiện vận hành song song — cả hai cần trị số xác định. Nay Uk và
Io in trần, chỉ Po/Pk có dấu.

### B. Trùng lặp và định danh

**B1. Tiêu đề thiếu số pha + cấp điện áp.** 35 nhóm / 75 SKU trùng nguyên
văn (`TBD1P50` với `TBD3P50`; `TBD1P50A107` 12,7kV với `TBD1P5022A107`
22kV). Thêm hai trường -> còn **2 nhóm**, và 2 nhóm đó đã sửa ở MASTER Ver8.

**B2. Nhãn phân biệt hai họ Amorphous.** A107 theo QĐ 107/QĐ-HĐTV, A2608
theo QĐ 2608/QĐ-EVN SPC; Po/Pk hiện giống hệt nên không có nhãn kỹ thuật
nào. Dùng số hiệu quyết định vì THIBIDI TỰ ghi "QĐ 107/QĐ-HĐTV" vào tên sản
phẩm — trong ngành này đó là cách phân biệt bình thường.

**B3. Tên hàng có xuống dòng bị WordPress cắt cụt.** 9 SKU MOF Young-hwa có
tên 3 dòng; WordPress lấy dòng đầu -> 7 sản phẩm cùng tên
"Hợp bộ đo lường (MOF) 24kV". Tool KHÔNG sinh trùng, dữ liệu bị cắt.
`normalize_row` gộp xuống dòng thành ` · `.

**B4. Slug cắt 55 ký tự làm mất phần phân biệt.** Ver 2.6 cắt 55 khi tiêu đề
còn ngắn; từ B1 phần phân biệt nằm ở cuối câu nên bị cắt trước tiên — đo
được 50 nhóm slug trùng. Nâng lên 95 -> còn 2.

### C. Nhãn dữ liệu

**C1.** 8 SKU KP có số thật từ catalogue IEC 60726 nhưng nhãn cột vẫn ghi
"cực đại theo tiêu chuẩn EVN" — dán nhãn quy chuẩn lên số của hãng là tự hạ
giá trị dữ liệu mình có. Renderer đọc `nguon_loai_so_lieu`, `catalogue_hang`
thì đổi nhãn thành "(W, catalogue hãng)".

### D. Bổ sung thiếu sót

**D1. Payload WooCommerce thiếu 3 thứ.** Trước đây chỉ gửi
`name/type/status/description/short_description/sku`:
- không `categories` -> sản phẩm TẠO MỚI rơi vào "Chưa phân loại" (bài đã có
  không bị ảnh hưởng: Woo giữ nguyên khi PUT không kèm trường này)
- không meta Rank Math -> Focus Keyword trống, điểm SEO đứng ở 15/100
- `render_phase2` sinh schema/faq_schema đàng hoàng nhưng **KHÔNG AI GỬI ĐI**

Thêm `dung_danh_muc()` và `dung_rank_math()`, đều sinh bằng code, 0 lượt AI.
Meta description CHỈ ghép chỉ số có dữ liệu thật — thiếu thì bỏ hẳn mệnh đề,
Hard Block áp cho trường này y như áp cho nội dung. Schema đi qua meta riêng,
tuyệt đối không nhét vào description (WordPress lọc `<script>` nhưng giữ
text -> JSON hiện thành chữ).

**D2. Biểu đồ so sánh lõi chỉ chạy cho THIBIDI.** `khoi_so_sanh_loi()` chỉ
tra `tra_cuu_thibidi.py` — bảng viết cứng chỉ có dữ liệu THIBIDI. Máy MBT tra
ra None nên 86 SKU MBT không bao giờ có biểu đồ, trong khi MASTER Ver7 đã đủ
Po cho cả bản Silic lẫn Amorphous của MBT. Thêm nguồn thứ hai: Po của SKU
anh em khác lõi cùng hãng/kVA/cấp áp. **50 -> 106 SKU có biểu đồ.** Đây là
nguồn hình sinh tự động, 0 lượt AI, không phải chụp tay.

**D3. Bảng so sánh cùng dòng cụt một đầu.** `db_phase2.py` sort tăng dần rồi
`[:6]` nên SKU công suất lớn LUÔN chỉ thấy mức nhỏ hơn mình (KP 800kVA chỉ
liệt kê 160-500). Nay lấy cân hai phía, thiếu bên nào bù bên kia.

### E. Family Router — 3 dương tính giả

- `\bsu\s*(...|dung|...)\b` bắt nhầm **"sử dụng"** (bỏ dấu ra "su dung",
  trùng khít "sứ đứng") -> "Module PLC ... 1 công tơ SỬ DỤNG 1 module" thành
  sứ cách điện. Thêm `cam_cum_co_dau` dò trên bản CÒN DẤU, nên "Sứ đứng
  24kV" vẫn nhận đúng.
- **"kiểm định" trong ngoặc** là thuộc tính đi kèm, không phải dịch vụ. Bỏ
  mọi cụm trong ngoặc trước khi dò dịch vụ.
- **"nắp che"** thiếu trong `_PHU_TRO` -> "Nắp che tole cho MBA 320kVA" thành
  máy biến áp.

### F. Prompt Enhance nhận cỡ máy

Quy tắc 5 cấm xét mã hàng cụ thể (đúng, để không nói xấu sản phẩm đối thủ),
tác dụng phụ là AI không biết máy này mấy kVA mấy pha nên rút bối cảnh "nhà
cao tầng, điện mặt trời hoà lưới" cho máy 1 pha 15kVA. Thêm quy tắc 5b và
dòng "CẤU HÌNH ĐANG XÉT" — **cỡ máy KHÔNG phải mã hàng**, quy tắc 5 giữ
nguyên.

### G. Dọn version

README ghi Ver 5.1, SPEC ghi Ver 1.7, cả hai đưa về 3.6.4. Ghi rõ trong
SPEC: số "Ver 1.x/2.x/4.x/5.x" rải trong comment code là LỊCH SỬ VÁ của
từng hàm, giữ có chủ đích — chúng ghi lỗi nào đã vấp ở đâu.

### Test

`tests/test_v364_dot_lon.py` — 45 assertion, PASS 45/0.
`run_tests.py` -> **42 file PASS / 4 FAIL**, đúng 4 file FAIL sẵn có của nền
(lỗi Tkinter headless). Không phát sinh lỗi mới.

Ghi nhận thêm: `test_round2_ui_smoke.py::R2-10.B` CHẬP CHỜN SẴN trên bản nền
chưa vá (2/4 lần fail) — lỗi focus của Tkinter dưới Xvfb, không phải do đợt
này. Đã ghi vào KNOWN-ISSUES.

## Ver 3.6.3 — 2026-08-08 — Vá 2 lỗi lọt lên bài thật — Claude

Thịnh phát hiện trên trang `MBT1P15A2608` đang chạy. Cả hai đều là lỗi tao
gây ra ở Ver 3.6.1.

**Lỗi 1 — bộ lọc câu hỏi mở bài CHƯA BAO GIỜ CHẠY.**

Ver 3.6.1 lọc ở khâu cuối, regex neo đầu chuỗi và chỉ cho phép tối đa MỘT
thẻ `<p>` đứng trước. Nhưng chuỗi thật lúc đó là:

```
<div class="snl-page"><div class="snl-hero"><div class="snl-hero-info">
<div class="snl-kicker">MBT</div><div class="snl-lead"><p>Bạn đang tìm...?
```

Bốn tầng thẻ, và chữ "MBT" của khối thương hiệu chen vào giữa nên chuỗi thẻ
mở không còn liền mạch. Regex trượt, câu hỏi lên trang.

Sửa: lọc ở `dung_bai_html()` **ngay khi nhận `ai_data`**, trước mọi khâu
ghép — lúc đó mỗi trường còn nguyên vẹn, chưa bị bọc gì. Thêm
`_loc_ai_data()`. Bài học: lọc chuỗi phải làm ở chỗ chuỗi còn đơn giản,
không làm sau khi đã ghép.

**Lỗi 2 — Markdown `**đậm**` hiện nguyên dấu sao trên trang.**

AI trả về Markdown, không ai chuyển sang HTML. Trang in ra
`**Máy biến áp dầu 1Pha 15KVA 12.7/0.23KV**`.

Sửa: `_doi_markdown_dam()` đổi `**...**` thành `<strong>`. CHỈ xử dấu sao
đôi — dấu sao đơn để nguyên vì có thể là dấu nhân trong công thức.

**Lỗi 3 (tự tạo rồi tự bắt lúc kiểm)**: bản vá đầu tiên áp `<strong>` cho
cả `meta_description`, mà meta phải là CHỮ TRẦN — Google in nguyên văn thẻ
nếu có. Với meta thì xoá dấu sao chứ không đổi thành thẻ, và hạ ngưỡng cắt
câu hỏi xuống 40 ký tự vì meta vốn ngắn.

**Test**: `test_v361_no_vat.py` +9 assertion (tổng 35/0), có ca "4 tầng thẻ
bọc ngoài" khoá đúng lỗi 1. `run_tests.py` → **41 file PASS / 4 FAIL**.

**Bài đã đăng**: KHÔNG cần render lại. Cả hai lỗi chỉ là chuỗi trong
`post_content`, sửa được bằng script cập nhật qua WooCommerce API, 0 lượt
Gemini. Gộp chung lượt với dấu Uk, categories, schema.

## Ver 3.6.2 — 2026-08-07 — Hero bỏ chip + bảng nhanh — Claude

**Góp ý của sếp Quân, Thịnh soát lại trên bài thật.** H1 đã ghi đủ
"Báo giá máy biến áp dầu MBT 15kVA (lõi Amorphous)", rồi hàng chip nhắc
lại y hệt bốn thứ đó (15 kVA / 12,7-0,23 kV / lõi Amorphous / MBT), rồi
bảng nhanh nhắc lần thứ ba (Mã hàng / Thương hiệu / Công suất / Cấp điện
áp), rồi bảng thông số đầy đủ phía dưới nhắc lần thứ tư.

Ba lần lặp trong 400px đầu tiên, đẩy đoạn văn thật và nút NHẬN BÁO GIÁ
xuống dưới màn hình. Trên điện thoại còn tệ hơn.

**Sửa** (`giao_dien_2_5.dung_bai_2_5`): thêm cờ `HERO_HIEN_CHIP_QUICK`,
**mặc định 0**. Hero còn lại đoạn văn mở đầu + dòng giá + nút CTA của
theme. Đo trên record thật: hero từ 1.147 xuống 340 ký tự.

MỘT cờ gom cả chip lẫn bảng nhanh, không tách thành 2-3 cờ — chúng luôn đi
cùng nhau, tách ra là mở đầu cho một tab cấu hình 20 dòng mà sáu tháng nữa
không ai nhớ cái nào làm gì. Bật lại bằng `HERO_HIEN_CHIP_QUICK=1`.

**Lưu ý về chỗ trống**: bỏ xong hero sẽ thưa. Thứ nên điền vào đó là bảo
hành bao nhiêu tháng và có CO/CQ không — hiện đang 0/245, phải hỏi công ty.
Đó là thứ duy nhất trên trang mà đối thủ không copy được, vì nó là chính
sách của Lotech.

**Test**: `test_v361_no_vat.py` +6 assertion (tổng 26/0). Sửa kỳ vọng
`test_v25_giao_dien.py::A2` — test cũ khẳng định hero PHẢI có `snl-chip`
và `snl-quick`; tách thành 2 assertion (mặc định không có / bật cờ thì có).
`run_tests.py` → **41 file PASS / 4 FAIL** (4 file FAIL sẵn có của nền).

## Ver 3.6.1 — 2026-08-07 — Xử cụm nợ vặt — Claude

**1. In dấu `≤` cho mức quy chuẩn EVN** (`render_phase2._dong_bang_thong_so_dong`)

Po/Pk/Uk trùng khít giữa THIBIDI và MBT vì cả hai in lại cùng bảng quy chuẩn
EVN — đó là mức TRẦN, không phải số đo của từng máy. In dấu `=` là sai sự
thật với người mua là kỹ sư. Ký hiệu đọc từ field `nguon_ky_hieu`
(cột `Nguồn - Ký hiệu hiển thị Po/Pk` của MASTER Ver5 trở đi): `≤` cho 93
SKU quy chuẩn, `=` cho 8 SKU catalogue KP.

Chỉ gắn dấu cho đúng nhóm Po/Pk/Uk và chỉ khi ô là số trần — không gắn vào
khối lượng, kích thước, hay chuỗi mô tả. MASTER cũ không có cột đó thì giữ
nguyên hành vi cũ.

**Không đụng Hard Block**: dấu `≤` thêm ở khâu dựng HTML, sau khi kho số đã
lập. AI không bao giờ thấy dấu này, kho vẫn chứa số trần.

**2. Bộ lọc dấu vết AI** (`loc_dau_vet_ai`)

Hai thứ làm bài đọc như AI viết: gạch ngang dài `—` rải khắp bài, và mở bài
bằng câu hỏi tu từ. Cả hai đến từ nhiều nguồn cùng lúc — AI viết, code tự
sinh (`kien_thuc_bien_thien` có hơn 10 chỗ), cột động — nên lọc ở ĐIỂM
NGHẼN CUỐI thay vì đi sửa từng nguồn rồi vẫn sót.

- `—` → dấu phẩy (đọc trôi hơn gạch nối trong văn xuôi tiếng Việt)
- **KHÔNG đụng gạch ngắn `–`**: dùng cho dải số ("15–100 kVA") là đúng
  chính tả, không phải dấu vết AI
- Câu hỏi mở bài: chỉ cắt khi phần còn lại vẫn đủ dài, không bao giờ để
  lại đoạn rỗng

**3. Xoá số sai còn sống trong code** (`tra_cuu_thibidi.py`)

Bảng cứng ghi `3200: (2340, 554, ...)` — Po Amorphous 554W trùng đúng mức
2500 kVA. Máy 3.200 kVA không thể có tổn hao không tải bằng máy 2.500 kVA.
Đối chiếu TCCS 10:2021/EVN: bảng tiêu chuẩn dừng ở 2.000 kVA, ghi chú cuối
bảng chỉ cho phép NỘI suy giữa 2 mức có sẵn — 3.200 là ngoại suy, không có
cơ sở. Đổi thành `None`; `khoi_so_sanh_loi()` tự không dựng khối khi thiếu
số nên trang 3.200 kVA hết vẽ biểu đồ sai.

MASTER đã sạch từ Ver7, nhưng số sai vẫn sống trong code — đây là lý do
phải rà cả hai nguồn.

**4. Rà `db_phase2._ho_may_bien_ap`** — cùng loại rủi ro với vụ Amorphous
(phân họ theo tên hàng). Chạy trên 245 dòng thật: 94 họ, **0 họ bị lẫn hãng
hoặc lẫn loại lõi**. Không phải sửa. Ghi lại để lần sau khỏi rà lại.

**Test**: `tests/test_v361_no_vat.py` 20 assertion, PASS 20/0.
`run_tests.py` → **41 file PASS / 4 FAIL**, đúng 4 file FAIL sẵn có của nền.

## Ver 3.6 — 2026-08-07 — Khối sản phẩm đi kèm (vỏ / giá treo ↔ máy) — Claude

**Vấn đề**: 24 vỏ mạ kẽm và 7 giá treo là phụ kiện của chính những máy đang
bán trên site, nhưng mỗi trang đứng một mình. Trang vỏ chỉ có 4 dòng thông
số rồi hết (mỏng thật, 3 ô còn để trống vì chưa có dữ liệu); trang máy thì
không nhắc gì tới vỏ nên mất cơ hội bán kèm.

**KHÔNG gộp trang.** 1 SKU vẫn = 1 trang. Đây chỉ là một khối liên kết
thêm vào, giống khối "So sánh công suất trong dòng" đã có — khác ở chỗ khối
cũ nối sang *mức công suất khác*, khối này nối sang *sản phẩm đi kèm*.

**Thêm mới**: `phu_kien_di_kem.py` (215 dòng, 0 lượt AI) +
`tests/test_v36_phu_kien.py` (27 assertion, PASS 27/0).

**Khoá ghép**: `(số pha, công suất kVA, cấp điện áp)` — cả ba lấy từ CỘT
DỮ LIỆU. Không đọc mã hàng làm khoá: đợt rà Amorphous đã sót 20 dòng vì
ghép cặp bằng `ma.replace('A107','')`.

**Ràng buộc hãng cho vỏ**: vỏ là chi tiết cơ khí, kích thước thùng khác
nhau theo hãng — vỏ MBT không lắp vừa máy THIBIDI dù cùng kVA và cùng cấp
điện áp. Bản đầu tiên ghép cả chéo hãng, đã sửa. Giá treo thì KHÔNG ràng
buộc: nó bắt vào cột điện, và chữ "MBT" trong "Giá treo MBT 1x25" là viết
tắt của MÁY BIẾN ÁP chứ không phải tên hãng.

**Ngoại lệ đọc từ tên (Thịnh chốt)**: 7 giá treo có cột kVA và cấp điện áp
đều trống, chỉ tên hàng mang thông tin. Vẫn ghép, nhưng mọi kết quả mang cờ
`suy_tu_ten=True`. Rủi ro thấp hơn vụ Amorphous: sai thì ra link gợi ý
lệch, không phải số kỹ thuật sai in lên bài.

**Kết quả trên dữ liệu thật** (MASTER Ver7, 245 dòng): 23/24 vỏ và 6/7 giá
treo ghép được; 74/150 máy có ít nhất một phụ kiện.

**Nối vào render**: `render_phase2._dung_bai_2_5_wrapper` gọi thêm một khối
vào `kien_thuc`, bọc try để lỗi ở đây không làm hỏng bài. Thêm
`_PK_kho_row()` có cache theo `dataset_id` — render 119 bài chỉ truy vấn DB
một lần. Khối dùng `_st()` và `html.escape` của tool nên ra đúng class
`snl-*`, không đẻ CSS riêng (giữ ranh giới với nhánh plugin giao diện).

**Test**: `run_tests.py` → **40 file PASS / 4 FAIL**, đúng 4 file FAIL sẵn
có của nền (lỗi Tkinter headless). Không phát sinh lỗi mới.

## Ver 3.5.1 — 2026-08-07 — Chuẩn hoá viết hoa tiêu đề — Claude

**Lỗi**: title viết hoa loạn, VD `Báo Giá Máy biến áp Dầu THIBIDI 2500kVA
(Lõi Silic)` — hoa, thường, hoa, thường trong cùng một câu.

**Nguyên nhân**: mỗi mảnh của tiêu đề do một chỗ khác nhau sinh ra và mỗi
chỗ tự quyết viết hoa. `dung_tieu_de()` ghép cứng `'Báo Giá '` và
`'Máy biến áp'`, dict `{'dau': 'Dầu', 'kho': 'Khô'}` hoa chữ đầu,
`_dac_tinh_loi()` trả `'Lõi Silic'` cũng hoa. Ghép lại thành hổ lốn.
Không ai sai riêng lẻ — sai vì không có một chỗ duy nhất quyết định.

**Sửa** (`render_phase2.py`): mọi mảnh trả về chữ thường, thêm
`_hoa_dau_cau()` hoa đúng một ký tự đầu tiên ở cuối đường. Dùng cắt chuỗi
thủ công chứ KHÔNG dùng `.capitalize()` — hàm đó sẽ hạ `THIBIDI` thành
`Thibidi`. Áp cho cả hai nhánh (máy biến áp và vỏ máy biến áp).

Kết quả: `Báo giá máy biến áp dầu THIBIDI 2500kVA (lõi Silic)`.
Thương hiệu, đơn vị kVA/kV, tên vật liệu (Silic, Amorphous, Cu/Cu) giữ
nguyên cách viết của MASTER và catalogue.

**Test**: sửa kỳ vọng ở 3 file đang khoá chuỗi `'Báo Giá'` viết hoa —
`test_v499_patch.py`, `test_v50_patch.py`, `test_v52_patch.py` (2 assertion
đổi sang so khớp không phân biệt hoa/thường). Chạy `run_tests.py`:
**39 file PASS / 4 FAIL**, đúng 4 file FAIL sẵn có của nền 3.3 (lỗi Tkinter
headless), không phát sinh lỗi mới.

**Chưa làm**: bỏ câu hỏi tu từ mở bài, khử dấu `—`. Hai việc đó thuộc bộ
lọc cuối, chưa động tới.

## Ver 3.5 — 2026-08-07 — Bếp trưởng (bước 1) + tab Hàng đợi — Claude

Nền: **Ver 3.3 thuần**. Không kế thừa `ban_do_du_lieu.py` của bản 3.4.

**Thêm mới**

| File | Dòng | Việc |
|---|---|---|
| `bep_truong.py` | 175 | Phân hạng nguyên liệu ĐỦ/VỪA/ĐÓI theo dữ liệu thật của từng SKU. Thuần Python, 0 lượt AI, 0 đọc mạng |
| `hang_doi.py` | 265 | Tab "Hàng đợi": 4 ô đếm trạng thái, lọc theo hạng, chọn hàng loạt, ghi cờ `selected` |
| `tests/test_v35_hang_doi.py` | 78 | 21 assertion cho cả hai file trên |

**Sửa**

1. `enhance.py` — GỠ lỗi lặp nội dung. Ver 2.6 tách `boi_canh_su_dung` +
   `goc_nhin_bundle_cheo` ra khối riêng `goc_nhin_thi_truong_html` nhưng
   QUÊN xoá 2 lệnh cộng chuỗi cũ vào `ung_dung_html`. Hậu quả: cùng một bộ
   `<li>` in ra HAI LẦN mỗi bài, trên toàn bộ 245 bài đã đăng. Đây là
   duplicate content do code tự sinh, không phải lỗi hiển thị.
2. `profiles.py` — khai 3 cột của MASTER Ver5 vào `cot_import` của
   `may_bien_ap_do_luong`: `Nguồn - Loại số liệu Po/Pk/Uk`,
   `Nguồn - Ký hiệu hiển thị Po/Pk`, `Ghi chú - Cần kiểm lại`. Phải khai
   vì tên cột chứa chữ "Nguồn"/"Ghi chú" nên `_la_cot_noi_bo()` lọc bỏ,
   không tới được `du_lieu_json`. Khai rồi vẫn KHÔNG in ra bài (không nằm
   trong `cot_bang`).
3. `giao-dien.py` — 8 dòng nối tab Hàng đợi + đổi nhãn phiên bản. Không
   sửa logic của 10 tab cũ.
4. `tests/test_enhance_mock.py`, `tests/test_ver3_ui.py` — cập nhật kỳ
   vọng. Test cũ đang khoá đúng hành vi lặp ở mục 1 (tức là khoá cái lỗi),
   và đếm 12 tab con trong khi nay có 13.

**KHÔNG làm trong bản này** (để đúng scope đã chốt): dàn ý riêng theo hạng
(bếp trưởng bước 2), in dấu `≤` trong bảng thông số, nối 103 SKU vào Tầng 3
`kien_thuc_bien_thien`, việt hoá UI.

**Quy tắc đóng gói đã tuân thủ**: ZIP KHÔNG chứa `phase2-du-lieu.db`,
KHÔNG chứa `cau-hinh.env` thật (chỉ có `cau-hinh.env.mau`).

## SONEALEO ULTRA VER 3.0 — VISION: đọc thông số từ ảnh biển máy & catalogue PDF — 06/08/2026

Gộp 5 module đọc thông số bằng AI vision (bản Fable đưa, đã verify chạy
thật 88/88 test) vào tool — thành **tab 10 "Đọc thông số (AI)"**, không
còn phải chạy 5 script rời bằng dòng lệnh.

**Vì sao đây là bước quan trọng:** nút thắt lớn nhất suốt nhiều phiên là
*độ sâu kỹ thuật 3,5/10* — chỉ 15/245 SKU có Po/Pk/kích thước. 12 file
PDF (200MB) đọc bằng thư viện Python không moi ra được vì bảng số bị vỡ
cấu trúc. Vision đọc được **ảnh biển máy** (bảng thông số gắn trên thân
máy thật đã bán) và **trang bảng trong catalogue** — nguồn số chuẩn hơn
cả catalogue vì là của chính con máy đó.

**5 module gộp vào:**
- `vision_chung.py` — gọi Gemini vision, **cache theo hash file** (chạy
  lại không tốn lượt), **tự xoay key** khi hết quota, bóc `RetryInfo` từ
  lỗi 429 để phân biệt hết-lượt-phút (chờ) với hết-lượt-ngày (đổi key).
- `doc_bien_may.py` — tự lọc ảnh biển máy trong đống ảnh, đọc Po/Pk/Uk/
  tổ đấu dây/khối lượng. **Đối chiếu chéo**: biển ghi 560kVA mà nằm
  trong thư mục `320` → tô vàng "Cần kiểm", không tin bên nào.
- `doc_catalogue_pdf.py` — lọc trang có bảng thông số bằng CHỮ trong PDF
  trước (0 quota), chỉ trang khả nghi mới hỏi vision. Mỗi dòng ghi rõ
  file nào / trang mấy.
- `ghep_vao_master.py` — ghép kết quả ĐÃ SOÁT vào bản sao master. Không
  ghi đè ô có sẵn; số lệch nhau vào sheet `DoiChieu` chờ người quyết;
  biển máy ưu tiên hơn catalogue; dòng còn dấu "Cần kiểm" bị LOẠI.
- `enrich_tcvn_mba.py` — tính dòng điện danh định 2 phía từ công thức
  (142/245 SKU) + tra hiệu suất tối thiểu TCVN 8525:2015 (82/245).
  **0 quota.**

**`anh_san_pham.py` nâng lên 3.0** — đọc CÂY THƯ MỤC làm metadata: ảnh
`z4395...jpg` nằm trong `MBA/320/` tự hiểu là 320kVA, folder `HBT` ra
hãng. Trước đó chỉ đọc tên file nên 143/182 ảnh không gán được. Kèm vá
2.9: dầu/khô là tiêu chí LOẠI HẲN (ảnh MBA dầu THIBIDI 4000kVA từng bị
gắn vào bài MBA khô KP 4000kVA), ghép mơ hồ không còn tự tick chọn.

**Quy tắc prompt MỚI — bắt buộc:** cột "Hiệu suất năng lượng tối thiểu
TCVN 8525:2015" là **MỨC SÀN tiêu chuẩn quy định**, KHÔNG phải hiệu suất
thực đo. Prompt giờ cấm viết "máy có hiệu suất X%", chỉ cho viết "đáp
ứng mức hiệu suất tối thiểu ... theo TCVN 8525:2015".

**Dependency mới:** `pymupdf` (đọc PDF) — đã thêm vào `CAI-DAT-LAN-DAU.bat`
và danh sách kiểm tra thư viện lúc khởi động.

Test: `test_v30.py` 24/24, `test_v29` 36/36, `test_v28` 15/15, `test_v27`
28/28, enhance 26/26, GUI 9/9 — **tất cả chạy lại trên bản gộp**, không
phải tin báo cáo.

**Điểm yếu đã biết, nói trước:** chất lượng đọc của vision trên biển máy
THẬT (biển phản sáng, biển cũ mờ chữ) chưa ai kiểm — mới chỉ test bằng
mock. Prompt vision gần như chắc chắn cần tinh chỉnh 1-2 vòng theo ảnh
thật. Kỳ vọng đúng lần chạy đầu: "chạy được, ra file, có dòng đúng có
dòng phải sửa".

---

## SONEALEO ULTRA VER 2.8 — Dynamic Schema: cột Excel không giới hạn — 05/08/2026

Ý của Thịnh: *"mỗi cell là 1 data, càng nhiều cột thông số bài càng dày,
không giới hạn, quét tới đâu chơi tới đó"*. Đúng — trước 2.8 danh sách
cột khai CỨNG trong `PROFILES`, enrich Excel thêm 20 cột mới thì tool
vẫn chỉ đọc đúng cột đã khai, data nằm chết trong file.

**`profiles.quet_cot_dong()`** — quét MỌI cột Excel có giá trị chưa được
khai báo, trả về `row['thong_so_dong']`. Thêm cột nào là bài dùng được
cột đó, KHÔNG cần sửa code.

**Ba lớp chặn (bản đối chiếu bỏ qua hết, chỉ nói "10-15 dòng ở 2 chỗ"):**

1. **Danh sách LOẠI TRỪ cột nội bộ** — quét mù thì AI sẽ viết *"sản phẩm
   này bị nghi ngờ phân loại sai"* hoặc giá vốn lên trang bán hàng. Chặn:
   giá, ghi chú kiểm duyệt, nghi ngờ, độ tin cậy, trạng thái... Chạy thật
   trên MASTER Ver7 phát hiện thêm 7 cột metadata của tool enrich ngoài
   (`Product ID`, `Catalog Row Hash`, `Schema Version`, `Claim Count`,
   `Last Enriched`...) — bổ sung vào danh sách chặn.
2. **Hard Block phải biết cột mới** — kho số hợp lệ trước đây lấy từ
   `cot_ai` khai cứng; không cập nhật thì Hard Block chặn nhầm chính số
   tool vừa đưa cho AI (đúng họ lỗi `row`/`row_ai` từng mất 5 bản mới ra).
   Xử lý thêm: Excel ghi đơn vị ở TÊN CỘT (`Tổn hao Po (W)`) còn ô chỉ có
   số trần (`340`) -> phải bóc đơn vị trong ngoặc rồi ghép lại.
3. **Bỏ giá trị >200 ký tự** — thường là ghi chú tự do, không phải thông số.

Mở rộng `_SO_DON_VI` thêm `W/kW/dB/kg/Hz/%` — cột động hay mang các đơn
vị này, thiếu thì Hard Block bỏ qua luôn số đó.

**Kết quả thật trên MASTER Ver7 (245 SKU máy biến áp):** mở khoá 7 cột —
Product Type / Phase / Capacity / Primary + Secondary Voltage / Core
Material Normalized, và "Loại lõi (trích từ tên)". Đều là dữ liệu CHUẨN
HOÁ của thông tin đã có, KHÔNG phải thông số kỹ thuật mới. Giá trị chính
của bản này là **sẵn sàng cho tương lai**: khi Excel có Po/Pk/độ ồn thật,
tool dùng được ngay không cần sửa code.

Test: `tests/test_v28_dynamic_schema.py` **15/15**. V2.7 28/28, V2.5
22/22, enhance 26/26, GUI 9/9.

---

## SONEALEO ULTRA VER 2.7 — Ảnh sản phẩm tự động + 8 sửa đổi nội dung — 05/08/2026

Đổi tên thành **SONEALEO ULTRA** (Thịnh đặt) — bản này gom cả nội dung
lẫn tài nguyên ảnh vào một luồng.

### NHÓM 2 — ẢNH SẢN PHẨM (module mới `anh_san_pham.py` + tab 9)

Lotech có sẵn kho ảnh THẬT trên Drive (chụp tại kho, lúc giao hàng, lúc
cẩu lắp) — giá trị hơn ảnh catalogue vì là bằng chứng đã bán/đã lắp, và
KHÔNG có rủi ro bản quyền như ảnh hãng. Việc còn thiếu chỉ là đường nối
tên file -> SKU -> WordPress.

- **Parse tên file**: bóc hãng + số pha + công suất + loại lõi.
  `mba mbt 1p 25kva.jpg` -> MBT / 1 pha / 25kVA (tin cậy CAO).
  `z7247219391950_47.jpg` -> không đọc được -> **để trống cho người gán
  tay, KHÔNG đoán bừa**.
- **Chống nhầm điện áp với công suất**: `320kv` -> 320kVA nhưng `22kv`
  -> KHÔNG nhận (lưới phân phối VN cao nhất 35kV nên số ≤50 kèm "kv" là
  điện áp).
- **Ghép SKU**: bắt buộc khớp công suất; hãng/pha/loại lõi là điểm cộng;
  **số pha mâu thuẫn thì loại hẳn** (ảnh 3 pha không gắn vào SKU 1 pha).
  Nhiều SKU cùng điểm -> cảnh báo "nên kiểm lại".
- **Tối ưu**: resize theo chiều rộng tối đa + chuyển WebP (Pillow, đã có
  sẵn). Ảnh Zalo 2-4MB xuống còn ~200KB.
- **SEO ảnh**: đổi tên file `z7247219391950_47.jpg` ->
  `may-bien-ap-dau-3pha-250kva-22-0-4kv.webp`, tự sinh alt text theo tên
  sản phẩm. Ảnh thứ 2, 3 có alt khác nhau (ảnh thực tế / ảnh lắp đặt /
  ảnh giao hàng) để không trùng lặp.
- **Upload + gắn**: `upload_anh_media()` đẩy lên Media Library, set
  alt/title; `gan_anh_vao_san_pham()` gắn vào sản phẩm — ảnh đầu tiên
  thành **ảnh đại diện** (WooCommerce quy ước `images[0]`).
- **Tab 9 UI**: chọn thư mục -> Quét -> bảng kết quả (bấm đúp để gán tay,
  gõ `*` cuối mã để đặt ảnh đại diện) -> **Xem trước xuất Excel** ->
  Upload. Upload là hành động RIÊNG, không bao giờ tự chạy.

### NHÓM 1 — 8 sửa đổi nội dung (từ feedback bài đã đăng)

1. **SVG xuống body** — sơ đồ kỹ thuật rời khỏi hero, vào mục "Sơ đồ cấu
   tạo" trong thân bài (Thịnh: sếp không muốn ảnh kiểu này lên Google
   Images như ảnh sản phẩm chính).
2. **Bỏ CTA ở hero và cuối bài** — theme đã có CTA riêng, 2 khối sát nhau
   gây ngộp. Chỉ giữ CTA GIỮA BÀI.
3. **Bỏ MÃ SKU khỏi delta context** — Thịnh nhắc lần thứ 3. Trước đây chỉ
   DẶN prompt đừng nhắc mã, nhưng mã vẫn nằm trong context nên AI vẫn
   dùng. Giờ context ghi `"phiên bản 160kVA"`, AI không có mã để nhắc.
4. **VÁ LỖI % HAI CHIỀU** (bản đối chiếu phát hiện, đã verify): 100→160
   là TĂNG 60% (mốc 100) nhưng 160→100 là GIẢM 37,5% (mốc 160). Bản cũ
   chỉ đưa 1 con số không ghi mốc -> AI viết ngược thành "160kVA cao hơn
   37,5%" là SAI. Giờ ghi rõ cả hai chiều kèm mốc.
5. **Bảng so sánh loại mức kVA trùng record đang xem** — Ver 2.2 mới khử
   trùng giữa các ứng viên, quên so với chính sản phẩm đang xem nên bảng
   hiện "100 (đang xem)" rồi ngay dưới lại "100".
6. **Chống lặp ý** giữa "Đặc điểm" và "Chọn công suất phù hợp" — quy tắc
   prompt mới: Đặc điểm nói CẤU TẠO/TÍNH CHẤT, Chọn công suất nói CÁCH RA
   QUYẾT ĐỊNH; đã nêu con số ở mục này thì mục kia không nhắc lại.
7. **Khối "Cấu tạo & phụ kiện tiêu chuẩn"** — kiến thức ngành TCVN 6306/
   IEC 60076 về bộ phận cấu thành máy dầu phân phối. Chỉ hiện cho máy
   DẦU (máy khô cấu tạo khác hẳn, không có dầu/bình dầu phụ).
8. **FAQ Schema** (FAQPage) — Rank Math đã cài sẵn nên có cơ hội rich
   snippet. Trả qua key riêng `faq_schema`, KHÔNG nhét vào html (cùng lý
   do Product schema: WordPress lọc `<script>` nhưng giữ text bên trong).

Test: `tests/test_v27_anh_va_noi_dung.py` **28/28 PASS** (parse tên file
với mẫu THẬT từ Drive, ghép SKU, chống nhầm điện áp, tối ưu WebP, SEO
tên file/alt, quét thư mục, và 5 sửa đổi nhóm 1). V2.5 22/22, V2.4 17/17,
V2.3 16/16, V2.2 18/18, enhance 26/26, GUI 9/9.

---

## SONEALEO VER 2.6 — Feedback từ bài đăng THẬT: short_description, gom tab, SVG máy biến áp — 05/08/2026

Thịnh đăng thật 5 bài (5/5 thành công) rồi gửi feedback chi tiết. Bản
này sửa đúng những gì phát hiện được từ trang thật.

**1. TÁCH HERO SANG `short_description` — thay đổi ăn tiền nhất**

Thịnh phát hiện: WooCommerce hiện `short_description` NGAY CẠNH ảnh và
nút mua ở ĐẦU trang, còn `description` bị đẩy xuống tab "Mô tả". Trước
2.6 toàn bộ hero (chip + thông số nhanh + giá + CTA) nằm trong
description -> thứ quan trọng nhất lại ở chỗ ít người cuộn tới. Giờ
`dung_bai_2_5(tach_hero=True)` trả `{'hero', 'than'}`, luồng đăng Woo
gửi hero làm short_description.

**2. SVG SƠ ĐỒ NGUYÊN LÝ MÁY BIẾN ÁP — phủ cả nhóm**

Thịnh báo "chưa thấy SVG". Kiểm tra data thật: `MBT1P15A2608` trống cả
4 cột kích thước -> `so_do_kich_thuoc_may_bien_ap()` đúng khi không vẽ.
Nhưng nghĩa là gần như KHÔNG SKU nào vẽ được. Thêm
`so_do_nguyen_ly_may_bien_ap()`: cuộn sơ cấp — lõi thép — cuộn thứ cấp,
điện áp vào/ra, số pha, kiểu làm mát. Chỉ cần công suất + cấp điện áp
(mọi SKU đều có). Ưu tiên sơ đồ kích thước, rơi về nguyên lý khi thiếu.

**Lưu ý quan trọng về SVG trên WordPress:** ảnh trang thật cho thấy chữ
bên trong SVG bị lộ ra thành text — `wp_kses` xoá thẻ `<svg>` nhưng giữ
nội dung, đúng cùng cơ chế đã gặp với JSON-LD. Cần thêm SVG vào
`wp_kses_allowed_html` qua WPCode. Lưu ý: bộ lọc chạy lúc LƯU vào DB,
nên bài đã đăng phải đăng lại (bật "cập nhật lại bài đã đăng") mới có
hiệu lực.

**3. GOM 8 TAB THÀNH 3 NHÓM** (Thịnh: "UI rườm rà, nhức đầu")
`1. DỮ LIỆU` (Nhập dữ liệu, Sản phẩm) · `2. SẢN XUẤT` (Sinh & Đăng,
Theo dõi, Article Jobs, Enhance) · `3. CẤU HÌNH & LOG` (Cấu hình,
Outline Studio). Dùng notebook LỒNG — các hàm `_v3_tab_*` KHÔNG phải
sửa, `_v3_tab_cuon()` tự tra bảng `_NHOM_TAB`. Tab lạ không có trong
bảng rơi về nhóm 3 (an toàn: không mất tab).

**4. ENHANCE CÓ KHỐI RIÊNG** — Thịnh nói "chưa thấy Enhance được ứng
dụng". Thực ra nó CÓ chạy (log: `fetch 8 URL, đã chèn insight sạch`)
nhưng lẫn vào cuối mục Ứng dụng nên không nhận ra. Giờ gom thành section
riêng "Góc nhìn từ thị trường" có nhãn nguồn.

**5. SLUG NGẮN** — trước: `may-bien-ap-dau-1pha-15kva-12-7-0-23kv-loai-amorphous-kieu-kin-mbt1p15a2608-chuan` (80+ ký tự, over-optimize).
Sau: `bao-gia-may-bien-ap-dau-mbt-15kva-loi-amorphous`. Bỏ mã hàng khi
tiêu đề đã đủ dài/duy nhất, bỏ hậu tố `-chuan`. **Bài đã đăng KHÔNG đổi
URL** (ai_wp_adapter không gửi lại slug khi UPDATE — vá Ver 4.9.6).

**6. Bốn lỗi nhỏ Thịnh chỉ ra:**
- Thêm đơn vị: `15` -> `15 kVA`, `12.7/0.23` -> `12.7/0.23 kV` (chỉ thêm
  khi giá trị CHƯA có đơn vị, không nhân đôi)
- Bỏ câu *"Số liệu lấy trực tiếp từ dữ liệu sản phẩm, không suy đoán"* —
  ngôn ngữ nội bộ nói về cách tool hoạt động, khách không quan tâm
- Sửa H2 trùng ở "So sánh công suất trong dòng" (khối tự sinh h2 +
  section cũng sinh h2)
- "Hướng dẫn lựa chọn" -> **"Chọn công suất phù hợp"**
- **CTA GIỮA BÀI** chèn sau mục Ứng dụng — đúng lúc khách vừa xác nhận
  sản phẩm hợp nhu cầu

Cờ mới: `SLUG_NGAN` (mặc định TẮT, bật cùng bố cục 2.5).

Test: `test_v25_giao_dien` **22/22**, `test_ver3_ui` **9/9** (thêm test
đếm đủ 8 tab con sau khi gom), V2.4 17/17, V2.3 16/16, V2.2 18/18,
enhance 26/26.

---

## SONEALEO VER 2.5 — BỐ CỤC CAO CẤP: hero 2 cột, chip, mục lục neo, FAQ gập — 04/08/2026

Thịnh nhấn mạnh giao diện là tiêu chí đánh giá quan trọng. Bản này nâng
trang sản phẩm từ "bảng thông số + vài đoạn văn" lên bố cục thương mại
B2B đúng chuẩn.

**Module mới `giao_dien_2_5.py`** — 52 class CSS, các khối:
- **Hero 2 cột**: hình kỹ thuật bên trái | kicker + lead + chip + thông
  số nhanh + giá + nút gọi/Zalo bên phải
- **Chip đặc điểm** rút từ dữ liệu THẬT (công suất, điện áp, loại lõi,
  vật liệu ruột giải mã) — không có thì bỏ, không bịa
- **Bảng thông số nhanh** 2 cột, chỉ hiện field có giá trị
- **Mục lục neo** — chỉ dựng khi có từ 2 mục trở lên
- **FAQ gập** dùng `<details>` — không cần JS, WordPress không lọc mất
- **CTA cuối** nền navy + nút gọi/Zalo

**Tách file riêng có chủ ý:** `render_phase2.py` giữ DỮ LIỆU + Hard Block,
`giao_dien_2_5.py` chỉ lo BỐ CỤC. Sửa giao diện không bao giờ đụng vào
logic chống bịa số.

**Suýt tái tạo lại lỗi đã vá — phát hiện nhờ test:** bản đầu của
`_dung_bai_2_5_wrapper()` nhét `dung_schema_script()` vào `html`. Nhưng
bản trước đã vá đúng chỗ này: WordPress lọc thẻ `<script>` khi POST qua
REST API nhưng GIỮ text bên trong -> nguyên khối JSON-LD hiện thành CHỮ
THẬT trên trang (đã xảy ra, có ảnh chụp). Đã sửa: schema trả qua key
riêng `'schema'`, KHÔNG nằm trong html. Test B1 giờ kiểm ngược lại —
đảm bảo JSON-LD KHÔNG có trong html.

**CSS gộp 1 file:** `xuat_file_css()` giờ xuất cả bộ cũ lẫn bộ 2.5 ->
Thịnh chỉ dán MỘT lần lên WordPress.

**MẶC ĐỊNH TẮT** (`GIAO_DIEN_2_5=0`) — bố cục cũ giữ nguyên 100%. Bật ở
tab 1, có cảnh báo nhắc bật kèm chế độ CSS class và dán CSS mới trước.
Lỗi bố cục mới được bọc `try/except` -> rơi về bố cục cũ, không chết batch.

Test: `tests/test_v25_giao_dien.py` **21/21 PASS** (gồm: bật/tắt không
phá bố cục cũ, title/slug/meta giữ nguyên ở cả 2 chế độ, khối tự ẩn khi
thiếu dữ liệu, record trống gần hết vẫn không crash). Ver 2.4 17/17,
Ver 2.3 16/16, Ver 2.2 18/18, enhance 26/26, GUI 8/8.

---

## SONEALEO VER 2.4 — FAMILY ROUTER: chặn lỗi viết sai bản chất sản phẩm — 04/08/2026

Lấy ý từ review chéo (bản GPT gặp lỗi đầu cáp 3M bị viết như máy biến
áp). Kiểm tra data thật: Excel của Thịnh **đúng** — `3M24NTN1120` nằm
đúng sheet phụ kiện. Nhưng rủi ro route sai vẫn có thật ở tool này.

**Module mới `family_router.py`** — lớp kiểm tra chéo ĐỘC LẬP: đọc TÊN
hàng (nguồn đáng tin nhất, do người nhập viết), suy ra họ sản phẩm, đối
chiếu với outline mà `profiles.xac_dinh_outline_id()` gán. Router cũ tin
`profile_id` + `nhom_nguon` từ Excel và chỉ vá theo từng ca phát hiện
được ("vỏ mạ kẽm", "giá treo") — bịt lỗ, không phải nhận diện có hệ thống.

**Kết quả quét thật 5.264 SKU: 27 SKU (0,51%) đang viết sai bản chất.**
- 14 ca **dịch vụ** ("Thí nghiệm Recloser", "Thí nghiệm FCO"...) đang
  dùng outline thiết bị -> bài viết như đang BÁN thiết bị, trong khi đây
  là dịch vụ thí nghiệm.
- 8 ca **chống sét van** xếp vào `outline_tu_dong_cat` — chống sét van
  không phải thiết bị đóng cắt.
- 5 ca lệch khác.

**3 BUG THẬT đã vấp khi viết chính module này** (quét lần đầu ra 90 ca
lệch, phần lớn là false positive của router — sửa xong còn 27 ca thật):

1. **Chữ 'đ' không bị NFD tách.** `unicodedata.normalize('NFD')` chỉ
   tách dấu TỔ HỢP (á, ề, ộ), không tách 'đ' vì đó là ký tự riêng.
   Hậu quả: `'Đầu cáp'` -> `'đau cap'`, regex `\bdau\s*cap\b` TRƯỢT ->
   **đầu cáp bị nhận nhầm thành cáp điện**. Phải thay 'đ'->'d' bằng tay
   trước khi normalize.
2. **"Nắp chụp sứ MBA"** bị nhận là máy biến áp chỉ vì có chữ "MBA" —
   thực ra là phụ kiện dùng CHO máy. Thêm lớp `_PHU_TRO` chặn trước.
3. **"Thí nghiệm máy biến áp 250kVA"** bị nhận là máy biến áp — thực ra
   là DỊCH VỤ. Thêm lớp `_DICH_VU` chặn trước tất cả.

**Nguyên tắc:** CHỈ CẢNH BÁO lúc import, KHÔNG tự sửa outline — giống
cách xử lý `sku_trung` và `nghi_van_dien_ap`. Tên hàng viết tắt lạ không
có nghĩa Excel sai. Không nhận diện được họ -> trả None, không đoán bừa.

Test: `tests/test_v24_family_router.py` **17/17 PASS**. Ver 2.3 16/16,
Ver 2.2 18/18, enhance 26/26, GUI 8/8 — không phát sinh lỗi mới.

**Ghi nhận từ review chéo, CHƯA làm:** claim ledger + guard (ý hay, nhưng
bản đối chiếu chỉ phủ 57/5.264 SKU = 1,1% và tốn quota Gemini lớn khi
đọc PDF); CSS kit giao diện cao cấp hơn.

**Số liệu đáng chú ý khi chọn catalogue để nạp** (đo từ MASTER thật):
Cadivi 2.171 SKU > TTT 903 > 3M 223 > MBT 86 > THIBIDI 56. Nạp catalogue
Cadivi phủ được gấp 38 lần THIBIDI cùng công sức.

---

## SONEALEO VER 2.3 — MỐC 2: hình kỹ thuật vẽ từ dữ liệu — 02/08/2026

Trang sản phẩm B2B không có hình thì kỹ sư đóng tab. Nhưng Lotech không
có và sẽ không có ảnh chụp cho 5.264 SKU. **Không giải bài toán ảnh bằng
ảnh — vẽ từ dữ liệu.**

Module mới `hinh_ky_thuat.py`:

**1. Mặt cắt cáp điện** — vẽ vòng tròn đồng tâm từ 4 field giải mã ký
hiệu (Ver 2.0): ruột dẫn (màu đồng/nhôm) -> cách điện (XLPE/PVC) ->
giáp bảo vệ (vành có vạch thép, chỉ khi có) -> vỏ PVC. Số lõi bóc từ
tiết diện (`3x70` -> 3 lõi, `3x50+1x35` -> 4). Chú thích màu bên phải.
**Phủ ~2.506 SKU** đã giải mã được vật liệu + cách điện.

**2. Sơ đồ kích thước máy biến áp** — thân máy + sứ + cánh tản nhiệt,
đường kích thước A/C có mũi tên, bảng chú thích A/B/C/D + khối lượng
dầu/tổng. Giữ tương quan tỷ lệ giữa các chiều thật. Chỉ vẽ khi có ít
nhất 2/3 kích thước.

**Nguyên tắc an toàn — y hệt Hard Block, nhưng cho hình:**
- Vẽ bằng CODE từ field có thật. Không AI sinh ảnh, không tải ảnh ngoài.
- **Thiếu dữ liệu -> KHÔNG vẽ.** Vẽ sai cấu tạo tệ hơn không có hình.
- Mọi hình ghi rõ *"Sơ đồ minh hoạ cấu tạo — không theo tỷ lệ kích thước
  thật"* để không ai đem đi thi công.
- SVG chỉ dùng thẻ cơ bản (svg/g/circle/rect/line/text/polygon), không
  script/style/ảnh nhúng -> ít khả năng bị WordPress hay plugin bảo mật
  lọc mất. SVG là text nên nhẹ và Google đọc được.
- Lỗi vẽ hình được bọc `try/except` — KHÔNG bao giờ làm hỏng cả bài.

Có hình thì bỏ ô placeholder ảnh (2 thứ cùng chỗ là thừa); không có hình
thì giữ nguyên hành vi cũ.

Test: `tests/test_v23_hinh_ky_thuat.py` **16/16 PASS**. Ver 2.2 18/18,
GUI 8/8 — không phát sinh lỗi mới.

**Chưa làm trong Mốc 2:** ảnh generic theo nhóm (Thịnh hoãn), biểu đồ so
sánh công suất.

---

## SONEALEO VER 2.2 — MỐC 1 "Hết hỏng": sửa 3 lỗi nhìn thấy trên trang thật — 02/08/2026

Bản này sửa những gì phát hiện được khi Thịnh đăng bài THẬT và gửi ảnh
trang — loại lỗi không bao giờ thấy khi chỉ đọc HTML.

**1. BUG ẨN NGHIÊM TRỌNG: `_so_kva()` không parse được dữ liệu thật**

Hàm này chỉ làm `float(str)` trần. Dữ liệu MASTER thật là `'15 kVA'`,
`'250 kVA'` — CÓ đơn vị -> trả `None` cho MỌI record. Hệ quả: bảng "So
sánh công suất trong dòng" **chưa bao giờ thực sự được sắp xếp** — mọi
SKU rơi vào nhánh "None đẩy xuống cuối", giữ nguyên thứ tự đọc từ DB.

Triệu chứng bị CHE suốt thời gian dài vì thứ tự trong file Excel vốn đã
tăng dần sẵn, nhìn ngoài tưởng sort đúng. Chỉ lộ ra khi viết test khử
trùng mức công suất. Giờ bóc số đầu chuỗi, chịu được `'250'`,
`'250 kVA'`, `'37.5kVA'`.

**2. Bảng so sánh hiện trùng mức công suất**

Ảnh trang thật: 100 / **100** / 160 / **160** / 250 / **250**. Nhiều SKU
khác nhau (khác tiêu chuẩn EVN/mã QĐ) cùng một mức kVA đều lọt vào bảng.
Bảng để so sánh giữa các MỨC công suất mà hiện trùng số thì vô dụng và
trông như lỗi dữ liệu.

Sửa: giữ 1 đại diện mỗi mức kVA, **ưu tiên SKU đã đăng** (có URL) để bảng
bấm được — SKU chưa đăng chỉ dùng khi mức đó chưa ai đăng.

**3. Hai khối thừa trong bài — 2 công tắc mới, mặc định TẮT**

- `BO_CTA_CUOI`: theme Flatsome đã có khối CTA riêng ngay dưới nội dung
  (xác nhận bằng ảnh: khối xanh đậm 3 nút). Khối "Liên hệ báo giá" do
  tool sinh ra là trùng lặp. Bật cờ -> bỏ.
  **Kèm chống link chết:** nút "Yêu cầu báo giá" neo tới
  `id="lien-he-bao-gia"` nằm trong chính khối bị bỏ — nếu site chưa cấu
  hình hotline thì nút sẽ trỏ vào hư không. Đã xử lý: bỏ luôn nút trong
  trường hợp đó, để CTA theme làm việc.
- `BO_ANH_PLACEHOLDER`: ô "CHỖ CHÈN ẢNH SẢN PHẨM" viền cam trông như lỗi
  hiển thị với khách. Chưa có ảnh thật thì không hiện gì còn hơn hiện ô
  báo thiếu.

Cả 2 mặc định TẮT (giữ nguyên hành vi cũ), bật ở tab 1.

Test: `tests/test_v21_css_va_rollback.py` **18/18 PASS** (thêm 6 test C1-C6).
GUI 8/8, enhance 26/26 — không phát sinh lỗi mới.

**Còn lại của Mốc 1 (việc của Thịnh, không phải code):** chạy pilot 30
bài, đọc liền 5 bài cùng nhóm, ghi ra chỗ nào thấy chán/thấy sai.

---

## SONEALEO VER 2.1 — Audit kiến trúc: CSS ra ngoài + đường lùi + tài liệu vận hành — 01/08/2026

Bản này KHÔNG thêm tính năng nội dung. Nó sửa 3 thứ tìm ra khi audit toàn
hệ thống — loại vấn đề mà quá trình vá-từng-mảnh trước đó không nhìn thấy
vì đứng quá gần code.

**1. CSS ra ngoài — đo được, không phải cảm tính**

Đo thật trên bài render (2 SKU cùng dòng, AI viết khác nhau hoàn toàn):

| Chỉ số | Trước | Sau |
|---|---|---|
| Độ dài bài | 8.374 ký tự | 5.394 |
| Inline CSS (không phải nội dung) | **55,9%** | 31,6% |
| Trùng lặp HTML 2 bài cùng dòng | 75,8% | 59,4% |

Hơn NỬA mỗi trang là `style="border:1px solid..."` lặp lại y hệt giữa mọi
SKU, nhân 5.264 trang. Đây là nút thắt thật của "content chưa ok" — lớn
hơn chuyện thiếu field dữ liệu mà mấy phiên trước tập trung vào.

Cách làm: thêm `CLS` dict + `_st()` trong `render_phase2.py`, thay 33 chỗ
`style="{ST[...]}"`. `xuat_file_css()` sinh CSS TỪ CHÍNH `ST` — không
viết tay lần 2 nên không bao giờ lệch với code render.

**AN TOÀN NGƯỢC: mặc định TẮT** (`CSS_CLASS_MODE=0`, giữ inline y Ver
2.0). Bật ở tab 1 sau khi đã dán CSS lên site. Bật mà chưa dán -> bài mất
định dạng, nên có cảnh báo rõ ngay cạnh ô tick.

**2. Đường lùi (rollback) — lỗ hổng vận hành lớn nhất còn lại**

Trước Ver 2.1: tool CHỈ biết đăng. Grep toàn codebase không có hàm nào gỡ
bài đã đăng. Đăng nhầm 400 bài (VD phát hiện dữ liệu nguồn sai như vụ 165
dòng điện áp) = ngồi xoá tay 400 bài trên WordPress.

Thêm: `db_phase2.liet_ke_bai_da_dang()` + `danh_dau_da_go()`,
`ai_wp_adapter.go_1_bai()` + `go_bai_hang_loat()`, nút "⟲ Gỡ bài hàng
loạt" ở tab 5.

Quyết định thiết kế (an toàn trước tiện):
- Mặc định chuyển **Thùng rác** WP (khôi phục được), KHÔNG xoá vĩnh viễn.
- Xác nhận có kèm SỐ LƯỢNG thật + mã hàng mẫu, không hỏi chung chung.
- Lỗi 1 bài không dừng batch; ghi DB ngay sau mỗi bài -> dừng giữa chừng
  vẫn đúng trạng thái.
- HTTP 404 (bài đã bị xoá tay trước đó) tính là THÀNH CÔNG, không phải
  lỗi — mục đích cuối cùng đã đạt.
- `wp_id` GIỮ NGUYÊN sau khi gỡ để còn truy vết/khôi phục.

**3. `docs/VAN-HANH.md` — tài liệu cho người không biết code**

Bus factor đang là 1. Tool 12.129 dòng, `giao-dien.py` một mình 3.777
dòng. Refactor kiến trúc đã bị loại (đúng, không hợp hoàn cảnh) — nhưng
thứ thay thế đáng làm là tài liệu bàn giao, rẻ hơn 20 lần và giá trị cao
hơn trong đúng kịch bản này.

Test: `tests/test_v21_css_va_rollback.py` **12/12 PASS** (6 CSS + 6
rollback, gồm cả ca lỗi/404/dừng giữa chừng). `run_tests.py`: 26 PASS /
4 FAIL (pre-existing, không phát sinh mới) / 3 SKIP. GUI 8/8.

**Ghi nhận từ audit, CHƯA sửa — cần quyết định của Thịnh:**
- Tool đo *số bài đăng*, mục tiêu thật là *số SĐT*. Không có dòng code nào
  nối GA4/GSC/lead. Vòng feedback chưa đóng. Thịnh chọn hoãn (đúng — chưa
  index thì chưa đo được gì).
- Hard Block chặn số rất kỹ nhưng KHÔNG chặn nhận định định tính
  ("phù hợp nhà máy vận hành liên tục" — không số, qua cửa, vẫn có thể sai).
- Quota Gemini free ~20 lượt/ngày/model: toán học không cho phép chạy hết
  5.264 SKU trong thời gian hợp lý nếu không trả phí.
- Batch lớn nhất từng chạy thật: 16 bài. Mục tiêu 5.264 = gấp 330 lần quy
  mô đã kiểm chứng.

---

## SONEALEO VER 2.0 — Batch lớn: giải mã cáp điện mở rộng + nối vào code + khối kiến thức chung + bugfix — 01/08/2026

Batch lớn theo yêu cầu Thịnh, đổi số version lên 2.0 (không còn 1.x —
đánh dấu bước ngoặt: lần đầu dữ liệu giải mã ký hiệu THẬT SỰ chảy vào
bài viết, không chỉ nằm trong Excel).

**Đã làm, test thật, xong:**

1. **Bugfix `_uoc_tinh_tai_kw`** — máy công suất nhỏ (VD 1kVA) ra
   "1-1 kW" (khoảng ước tính co về trùng số, đọc kỳ cục) — sửa: trùng số
   thì hiện 1 số duy nhất. Phát hiện lúc debug log lỗi Hard Block Thịnh
   gửi — KHÔNG tái hiện được chính xác nguyên nhân gốc gây chặn "1KVA"
   dù thử nhiều biến thể văn bản, nghi liên quan 2 SKU dữ liệu dị dạng
   đã biết từ trước (`VNMBA1P1S/2S`) — sửa được 1 phần, không dám báo
   "đã sửa xong hoàn toàn".
2. **Sửa tên cột sai sheet Cáp điện** — "Khối lượng recloser/tủ điều
   khiển" (thuật ngữ thiết bị đóng cắt, lỗi copy header cũ) đổi tên
   trung thực, không ảnh hưởng code (cột chưa từng được dùng).
3. **Nối 7 field giải mã cáp điện vào `profiles.py`** (profile `cap_dien`
   + `outline_cap_dien`) — AI giờ ĐỌC ĐƯỢC field này, bảng thông số tự
   hiện 12 dòng khi có giải mã, tự về 5 dòng khi không có. Test render
   thật xác nhận đúng, không vỡ SKU cũ.
4. **3 khối kiến thức chung CÁP ĐIỆN** — "Về cách điện XLPE/PVC", "Về
   lớp giáp bảo vệ", "Về khả năng chống cháy" — code viết cứng (kiến
   thức ngành TCVN/IEC công khai, KHÔNG phải AI đoán số riêng SKU), tự
   ẩn khi record không có field tương ứng. Test end-to-end xác nhận
   đúng: hiện/ẩn chính xác theo dữ liệu.
5. **1 khối kiến thức chung TỦ ĐÓNG CẮT/RMU** — "Về cấu tạo tủ đóng cắt
   trung thế" — áp dụng `outline_tu_dong_cat` + `outline_vo_tu`, hiện
   LUÔN (không cần field giải mã, vì đây là kiến thức chung cho cả
   nhóm). Test end-to-end xác nhận đúng.
9. **Mở rộng decoder cáp điện** — thêm nhóm `VCm*` (dây đơn/đôi mềm dân
   dụng, quy ước NGƯỢC thứ tự so với nhóm CVV/CXV — verify 6 nguồn web
   độc lập). Coverage tăng: 77.0%→78.5% (ít nhất 1 field), 72.5%→74.0%
   (độ tin cậy cao). File `5MASTER_ENRICHED_Ver5.xlsx` (giao riêng,
   ngoài ZIP) đã cập nhật theo số liệu mới.

**Chưa làm, không giấu:**
- **Việc 1** (kiểm 5 field mới catalogue gốc MBT) — BLOCKED, file
  catalogue gốc không có trong phiên làm việc này.
- **Việc 6** (nâng cấp outline TOÀN BỘ sản phẩm theo 5 khối buyer-persona
  — Nhận diện/Quyết định/Triển khai/Chứng minh/Thương mại) — quy mô lớn
  nhất trong batch, CHƯA làm, cần 1 phiên riêng để không làm ẩu.
- **Việc 7** (khung khối thương mại) — vẫn chờ Thịnh xác nhận chính
  sách bảo hành/vận chuyển thật (việc A, đã hoãn) — field đã khai sẵn từ
  Ver 5.4, chưa có nội dung vì chưa có data thật.
- **Việc C** (enrich catalogue tủ đóng cắt/phụ kiện) — không có nguồn
  PDF, dừng theo yêu cầu Thịnh, không nhắc lại.

Test: `test_enhance_mock.py` 26/26, `xvfb-run test_ver3_ui.py` 8/8 —
không vỡ gì cũ qua toàn bộ thay đổi trên.

---

## SONEALEO VER 1.7.1 — Light mode palette C + bỏ tab 0 + bỏ ghi chú header — 01/08/2026

3 việc UI còn treo từ hôm review GPT (bị gác lại vì rẽ sang bàn review),
Thịnh chốt xong sau khi xem 3 preview màu:

1. **Đổi hẳn sang light mode** — bỏ dark mode Ver 1.6 (bị chê "xấu hơn
   bản cũ", không giữ làm tuỳ chọn). Palette "C — Trung tính xám": nền
   `#F8FAFC` (xám-xanh rất nhạt), card trắng `#FFFFFF`, chữ than đậm
   `#1E293B`, accent teal `#0F766E` (nút chính/tab đang chọn/thanh
   header). Ô Nhật ký CỐ TÌNH giữ tối kiểu terminal (`#1E1E1E`), không
   đổi theo theme chung — quy ước phổ biến, tách "vùng output" khỏi
   "vùng điều khiển", đúng thiết kế gốc trước Ver 1.6.
2. **Bỏ tab "0. Bắt đầu"** — Thịnh không cần, hàm vẫn còn trong code
   (`_v3_tab_0_bat_dau`), chỉ không gọi nữa — dễ bật lại nếu đổi ý. Còn
   8 tab như trước Ver 1.6.
3. **Bỏ dòng ghi chú phụ ở header** ("MASTER 4-Profile → AI viết →
   HTML+Schema → WordPress · SEO Alone") — chỉ còn tiêu đề chính.

Test: cập nhật `test_ver3_ui.py` I1/I4 về lại 8 tab — 8/8 PASS. Test màu
trực tiếp xác nhận nền `#F8FAFC`, log `#1E1E1E`, tiêu đề "SONEALEO ·
Ver 1.7.1". `test_enhance_mock.py` 26/26 vẫn PASS (không đụng gì).

**Đã bàn nhưng KHÔNG làm trong bản này** (Thịnh mệt, dừng ở mức vá màu):
đổi hẳn sang React/Tailwind qua pywebview — đã phân tích chi phí/lợi ích
trong chat, để dành làm dự án riêng sau nếu thật sự cần, không làm giữa
lúc core nghiệp vụ còn đang ổn định dần.

---

## SONEALEO VER 1.7 — 9 mục vá theo review GPT (đã verify từng claim bằng code thật trước khi sửa) — 01/08/2026

Thịnh đưa 1 bài review GPT dài, chi tiết, chấm 6.8/10. Trước khi vá bất
kỳ gì, đã tự tay verify từng claim quan trọng bằng code/test thật (đúng
nguyên tắc "GPT review giá trị nhưng có thể sai, verify trước khi tin")
— hầu hết claim ĐÚNG, 1 claim (threading root cause) SAI 1 phần (chẩn
đoán sai cơ chế cụ thể, dù triệu chứng đúng). Chi tiết xem lịch sử chat.

Thịnh chọn 9/14 mục đề xuất để vá ngay (10-11 để dành, 12-14 dẹp vì
không hợp hoàn cảnh 1 người/3-6 tháng):

1. **`cau-hinh.env` không còn lọt vào ZIP** — verify trước: file NÀY
   THẬT SỰ có trong ZIP Ver 1.6 (may là chỉ chứa placeholder test, không
   phải key thật của Thịnh). Sửa tận gốc: `zip -x "cau-hinh.env"` ở
   bước đóng gói, không phụ thuộc nhớ xoá tay mỗi lần nữa.
2. **Đóng gói kèm `du_lieu_goc/5MASTER_ENRICHED_Ver4_CLEAN.xlsx`** —
   trước đó chỉ gửi rời, không có trong ZIP tool.
3. **Chặn prompt injection cho Enhance** — thêm quy tắc 8 vào
   `QUY_TAC_INSIGHT` (nội dung web = DỮ LIỆU, không phải LỆNH) + bọc
   marker rào trước/sau quanh nội dung nguồn trong prompt thật (2 lớp,
   không dựa 1 lớp duy nhất). Lỗ hổng GPT chỉ đúng — verify trước: prompt
   cũ hoàn toàn không có framing này.
4. **Sửa race lúc đóng app** — `_dong()` cũ chỉ huỷ đúng 1 job cố định
   (`_boc_hang_doi_job`), đổi sang huỷ TẤT CẢ `after()` job đang chờ
   (`self.tk.eval('after info')`) — tổng quát hơn, không cần biết trước
   tên biến lưu job. Test trực tiếp xác nhận: đặt 2 job giả treo, gọi
   `_dong()`, job không chạy. LƯU Ý: `test_v37_batch_real.py` vẫn fail
   sau vá — verify cho thấy đây là lỗi KHÁC (gọi Gemini thật thất bại
   giữa batch, không phải lúc đóng app), ngoài phạm vi việc 4, chưa sửa.
5. **Validation Gate lúc import** — `nhap_phase2._quet_nghi_van_dien_ap()`
   mới: dò Tên hàng dạng "X/YkV" đối chiếu cột Cấp Điện Áp, CẢNH BÁO +
   đánh dấu `row['nghi_van_dien_ap']=True`, KHÔNG tự sửa/không chặn
   import (đúng triết lý sẵn có — giống hệt cách xử lý SKU trùng). Test
   thật: chạy với MASTER gốc ra đúng 165/165 nghi vấn (khớp chính xác
   con số đã biết); chạy với CLEAN.xlsx chỉ còn đúng 2 dòng không tự sửa
   được từ trước (VNMBA1P1S/2S) — không false positive.
6. **`run_tests.py`** — gộp 33 file test thành 1 lệnh, tự phát hiện
   Xvfb, phân loại rõ PASS/FAIL/SKIP (SKIP không còn lẫn vào PASS như
   trước — verify: `test_v498_patch.py` thật sự tìm sai đường dẫn fixture,
   đúng như GPT chỉ ra). Kết quả sau vá: 26 PASS / 4 FAIL (đều pre-existing,
   verify bằng cách so với baseline gốc) / 3 SKIP.
7. **Dọn tài liệu** — archive toàn bộ file lỗi thời (`TIEN-DO.md`,
   `KNOWN-ISSUES.md`, `ARCHITECTURE-DRAFT*.md`, `DATA-AUDIT*.md`, 3 file
   `HUONG-DAN-*.md`, `SPEC.md` cũ — verify: SPEC.md cũ còn ghi "LOTECH
   AUTOPOST" và "Ver 3", lỗi thời thật) vào `docs/archive/` (gộp chung
   `lich-su-phien-ban/` cũ, 66 file). `docs/` giờ chỉ còn 3 file sống:
   `SPEC.md` (viết lại mới, ngắn, đúng Ver 1.7), `NHAT-KY-THAY-DOI.md`,
   `SONEALEO-TRACKLOG.xlsx`.
8. **Sửa `test_v45_checklist_lien_quan.py`** — verify: `khoi_checklist_
   bao_gia()` còn định nghĩa trong code nhưng 0 lần được gọi trong
   `dung_bai_html()` (chủ ý bỏ, không phải bug) — test cũ lỗi thời, đã
   sửa lại 2 assertion (E2E-1, E2E-3) khớp hành vi hiện tại. 16/16 PASS
   (trước 14/16).
9. **Chặn SSRF nhẹ cho Enhance** — `enhance._url_toi_noi_bo()`: chặn
   loopback/private IP/link-local/metadata endpoint/giao thức lạ trước
   khi fetch, TỰ kiểm lại từng bước redirect (không dùng
   `allow_redirects` mặc định — 1 redirect chain có thể dẫn tới địa chỉ
   nội bộ). Test: chặn đúng `localhost`/`127.0.0.1`/`169.254.169.254`/
   `192.168.x`/`10.x`/ftp/URL rác; KHÔNG chặn nhầm web thật.

Việc 10 (Delta review UI) + 11 (cannibalization gate mở rộng chống lặp
Enhance) — Thịnh thấy hay, để dành làm sau, CHƯA làm trong bản này.
Việc 12-14 (tách kiến trúc 6 tầng, keyring, requirements.lock) — Thịnh
quyết định KHÔNG làm, không hợp hoàn cảnh 1 người/3-6 tháng.

---

## SONEALEO VER 1.6 — 3 lỗi thật từ feedback Thịnh sau khi test Ver 1.5 — 31/07/2026

Thịnh test Ver 1.5 trên máy thật, gửi log + bài mẫu thật, tìm ra 3 lỗi
thật — không phải góp ý UI, là bug code:

1. **LỖI NGHIÊM TRỌNG — Enhance gần như CHƯA BAO GIỜ thực sự áp dụng
   được từ Ver 1.1 tới giờ.** `giao-dien.py` gọi
   `E.enhance_1_san_pham(row, ...)` bằng `row` GỐC (thiếu delta/tier
   context), trong khi nội dung AI gốc được viết dựa trên `row_ai`
   (CÓ delta context, tính bằng code trước khi gọi Gemini — Ver 4.9.9).
   Hard Block lớp cuối của Enhance dùng `row` thiếu context để đối
   chiếu, nên KHÔNG nhận ra số liệu delta hợp lệ ĐÃ CÓ SẴN trong bài
   gốc (VD "+25kVA, tăng 33.3%") — báo "số lạ" và HUỶ TOÀN BỘ insight
   Enhance vừa thêm, quay về ai_data gốc. Log thật cho thấy: 2/2 sản
   phẩm batch đầu tiên đều bị huỷ theo kiểu này. Sửa: dùng `row_ai`
   thay vì `row` khi gọi Enhance.

2. **File MASTER bị nhận nhầm "dữ liệu RMU cũ" dù đúng định dạng.**
   `nhan_dien_loai_nguon()` cũ CHỈ đọc sheet ĐẦU TIÊN — nếu sheet phụ
   (VD nhật ký sửa lỗi) lỡ nằm ở vị trí đầu, cả file bị coi là sai định
   dạng dù 4 sheet dữ liệu thật vẫn nguyên vẹn. Đã xảy ra thật 2 lần.
   Sửa: quét TẤT CẢ sheet tìm header "Mã hàng"+"Tên hàng", không còn
   phụ thuộc thứ tự sheet. Test: giả lập đúng tình huống lỗi (sheet log
   ở vị trí 0), xác nhận nhận diện đúng `4_profile`.

3. **Câu văn nhắc mã SKU liền kề TRẦN TRỤI không kèm số** — VD "...tăng
   thêm +25kVA (tương ứng mức tăng 33.3% so với TBD1P75A107)" — lần
   nhắc mã thứ 2 trong câu mất số kVA đi kèm, người đọc không tài nào
   nhớ nổi mã đó là bao nhiêu kVA. Sửa `prompts_phase2.py`: thêm quy
   tắc — ưu tiên gọi "phiên bản X kVA" thay vì nhắc mã SKU trong câu
   văn; nếu vẫn nhắc mã, MỌI lần nhắc đều phải kèm số ngay sau, không
   được để mã đứng trơ trọi.

**LƯU Ý QUAN TRỌNG cho Thịnh:** do lỗi #2, Thịnh đã phải import file
`5MASTER_ENRICHED_Ver4.xlsx` GỐC (chưa sửa Cấp Điện Áp) thay vì bản
CLEAN — nghĩa là 165 SKU máy biến áp đang có Cấp Điện Áp SAI trong
DB hiện tại. Giờ lỗi #2 đã sửa, cần **nhập lại đúng file CLEAN** để có
data đúng.

Test: `nhan_dien_loai_nguon` test riêng PASS, `test_enhance_mock.py`
26/26 vẫn PASS (không đổi), toàn bộ 33 test cũ chạy lại qua Xvfb — chỉ
còn đúng các lỗi pre-existing đã biết từ trước, không có lỗi mới.

**Chưa làm trong bản này (2 việc lớn hơn, cần bàn thêm với Thịnh
trước khi làm mù):** ~~(a) đại tu UI...~~ ~~(b) làm mượt lại flow...~~
**ĐÃ LÀM THÊM sau khi hỏi Thịnh chọn hướng (cùng trong Ver 1.6, xem bên
dưới) — 2 mục này coi như xong.**

**Cập nhật thêm (sau khi hỏi Thịnh 2 câu về màu sắc + điểm rối flow):**

**(a) Dark mode toàn bộ tab Ver 3** — đổi bảng màu `V3_*` từ nền sáng
sang nền tối (`V3_BG` #12181F, `V3_CARD` #1B232C, chữ #E4E9ED). Tách
`V3_NAVY` (trước dùng chung cho cả nền header LẪN màu chữ tiêu đề —
xung đột trên nền tối, chữ tối trên nền tối không đọc được) thành 2
hằng riêng: `V3_NAVY` (chỉ còn dùng làm nền thanh header) và
`V3_HEADING` (màu chữ tiêu đề, teal sáng, đọc được trên nền tối). Đổi
tên hiển thị: tiêu đề cửa sổ, header, status bar — từ "LOTECH AUTOPOST
VER 5.3" sang "SONEALEO · Ver 1.6".

**(b) Nhật ký chuyển sang PHẢI, chiếm ~40% chiều rộng** — đổi
`chia_man` từ `PanedWindow(orient='vertical')` (nhật ký xếp CHỒNG dưới,
chiếm hết chiều ngang) sang `orient='horizontal'` (tab trái ~60%, nhật
ký phải ~40%). Panel nhật ký đổi từ style sáng (thừa kế theo RMU cũ)
sang style `V3.*` tối, đồng bộ tông màu, không bị lệch cạnh tab.
Sash đặt tự động ~60/40 lúc mở app (`_dat_ti_le_chia_man()`), tự do kéo
lại sau đó như PanedWindow bình thường.

**(c) Tab MỚI "0. Bắt đầu"** — feedback thật: "lẫn giữa quá nhiều tab,
không biết bấm tab nào trước". Tab này KHÔNG có logic nghiệp vụ, chỉ
chia 8 tab còn lại thành 3 nhóm rõ ràng — "LÀM 1 LẦN" (Cấu hình, Nhập
dữ liệu), "LÀM MỖI LẦN" (Sản phẩm → Sinh & Đăng → Theo dõi), "NÂNG CAO/
TUỲ CHỌN" (Outline Studio, Article Jobs, Enhance) — mỗi dòng có nút
"Đi tới tab X" nhảy thẳng, test xác nhận nhảy đúng tab.

Test bổ sung: `_dat_ti_le_chia_man()` xác nhận sash ~60% khi mở app
bình thường (không resize ngay sau khởi tạo — kịch bản đó cho sai số,
đã xác minh không phải bug thật). Test nút nhảy tab (index 4 → "4. Sinh
& Đăng", index 8 → "8. Enhance") — đúng. `test_ver3_ui.py` cập nhật
lại I1/I4 cho khớp 9 tab (thêm "0. Bắt đầu") — 8/8 PASS.

---

## SONEALEO VER 1.5 — Enhance nguồn cộng đồng + lớp chặn rủi ro uy tín (Đợt 4/4 — HOÀN TẤT ROADMAP) — 31/07/2026

**Đợt 4/4, đợt cuối roadmap Enhance.** Thịnh yêu cầu làm dù chưa test
1.3/1.4 thật với API sống — đã cảnh báo 1 lần trước khi làm (theo đúng
nguyên tắc "flag 1 lần rồi thôi"), build có thêm lớp an toàn MỚI thay vì
làm ẩu cho xong việc.

**Quyết định phạm vi:** CHỈ thêm nguồn diễn đàn/cộng đồng qua Serper
(site: filter, dùng chung API đã có) — KHÔNG thêm YouTube (cần API/key
riêng, tăng bề mặt lỗi không cần thiết cho "đợt cuối", có thể làm sau
nếu thật sự cần).

**Thay đổi:**
- `enhance.DANH_SACH_DIEN_DAN` — danh sách diễn đàn kỹ thuật khởi điểm
  (webdien.com, dientuvietnam.net, tinhte.vn) — Thịnh tự sửa nếu biết
  forum khác phù hợp hơn.
- `enhance.tim_kiem_dien_dan()` — tìm riêng trong nhóm diễn đàn, dùng
  chung `tim_kiem_google()`/Serper, không thêm dependency.
- `xay_prompt_insight()` gắn nhãn `[Nguồn cộng đồng]` RIÊNG khi có nội
  dung diễn đàn — `QUY_TAC_INSIGHT` thêm quy tắc 7: cấm trích than
  phiền/đánh giá tiêu cực/sự cố từ nguồn cộng đồng.
- **Lớp chặn MỚI, áp dụng cho MỌI insight (không riêng nguồn cộng
  đồng)** — `_TU_KHOA_RUI_RO_UY_TIN`: blocklist từ khoá kiểu khiếu
  nại/sự cố/cháy nổ/lừa đảo/"đừng mua". Đây là phòng thủ theo chiều sâu
  — không tin riêng lớp "gắn nhãn nguồn" là đủ, vì nguồn thương mại
  cũng có thể vô tình chứa review tiêu cực nhúng trong bài (VD bài
  "so sánh, tránh mua loại X").
- `enhance_1_san_pham(..., bat_nguon_cong_dong=False)` — MẶC ĐỊNH TẮT,
  opt-in qua checkbox riêng ở tab 8 (tách khỏi checkbox Enhance chính).
  Lỗi ở bước tìm/fetch nguồn cộng đồng KHÔNG làm hỏng cả lần chạy — tự
  bỏ qua, dùng nguồn thương mại như bình thường.

Test: `tests/test_enhance_mock.py` **26/26 PASS** (5 test mới: lớp chặn
từ khoá rủi ro, nhãn nguồn cộng đồng trong prompt, quy tắc 7, lỗi rõ khi
thiếu key, xác nhận opt-in mặc định KHÔNG gọi tìm diễn đàn). GUI 8/8,
batch end-to-end 3/3 — không đổi hành vi khi checkbox mới để mặc định
tắt.

**ROADMAP ENHANCE (4 đợt) — HOÀN TẤT.** Việc tiếp theo: Thịnh chạy thật
Ver 1.3-1.5 trên máy với API sống (chưa test lần nào), báo lại kết quả
trước khi tính mở rộng thêm — xem `docs/SONEALEO-TRACKLOG.xlsx`.

---

## SONEALEO VER 1.4 — Enhance rút sâu hơn: bối cảnh sử dụng (Đợt 3/4) — 31/07/2026

**Đợt 3/4 trong roadmap Enhance** — thêm field thứ 4 `boi_canh_su_dung`:
so sánh 2-4 bối cảnh/trường hợp sử dụng thực tế khác nhau (VD "nhà xưởng
vận hành liên tục" khác "công trình dân dụng ngắn hạn" khác "khu hay mất
điện lưới"), viết dài hơn (1-2 câu/bối cảnh) thay vì 1 câu ngắn như 3
field cũ.

**Ranh giới quan trọng, khác 3 field trước** — field này rủi ro cao hơn
nếu làm ẩu (dễ vô tình "khen/chê" sản phẩm cụ thể của đối thủ), nên
thêm hẳn 1 quy tắc riêng trong prompt (`QUY_TAC_INSIGHT` mục 4): CẤM
khẳng định "sản phẩm X của đối thủ phù hợp/tốt hơn/có tính năng Y" —
chỉ được mô tả bối cảnh sử dụng CHUNG của cả LOẠI sản phẩm, không gán
nhận định cho sản phẩm cụ thể nào.

- `enhance.TRUONG_INSIGHT` thêm `boi_canh_su_dung` — tự động được cả bộ
  lọc số (`loc_bo_muc_co_so`) lẫn cơ chế chống lặp (Đợt 1) áp dụng, không
  cần sửa 2 chỗ đó (thiết kế từ Đợt 1 đã tính trước cho việc này).
- Merge vào `ung_dung_html` thành khối riêng có tiêu đề phụ "Một số bối
  cảnh sử dụng thường gặp" — tách khỏi khối bundle chéo, vì 2 mục đích
  khác nhau (1 gợi ý mua kèm, 1 giúp khách tự đối chiếu công trình).
- Tương thích ngược: AI/mock không trả field mới vẫn chạy bình thường
  (`.get()` mặc định rỗng) — xác nhận qua test batch cũ (mock 3 field)
  chạy lại không lỗi.

Test: `tests/test_enhance_mock.py` 21/21 PASS (2 test mới). GUI 8/8,
batch end-to-end vẫn 3/3 OK không đổi hành vi khi mock chưa có field mới.

Còn lại Đợt 4 (nguồn ngoài SERP) — vẫn đang cân nhắc lại, xem Backlog.

---

## SONEALEO VER 1.3 — Enhance chạy hàng loạt cho cả nhóm (Đợt 2/4) — 31/07/2026

**Đợt 2/4 trong roadmap Enhance** — chạy Enhance cho TOÀN BỘ sản phẩm
đang chọn (tab 2), không phải bấm tay từng SKU 1 (nút "Test Enhance"
Ver 1.1 chỉ làm được 1 SKU). Dùng `ai_data` MOCK (không tốn Gemini viết
bài) — mục đích là xem trước Enhance + chống lặp Đợt 1 chạy ổn trên cả
nhóm hay không, TRƯỚC KHI bật checkbox thật ở tab 4 (lúc đó mới tốn
Gemini viết bài đầy đủ).

- Tab 8 thêm khối "Chạy thử cho CẢ NHÓM đã chọn" — progress bar, nút
  Chạy/Dừng riêng (không đụng cờ dừng của luồng Sinh bài chính tab 4),
  chạy nền qua `chay_nen_phase2()` có sẵn (không tự viết threading mới).
- Xác nhận trước khi chạy (dialog): nói rõ tốn N credit Serper + N lượt
  gọi Gemini (rút insight, không phải viết bài) — không giấu chi phí.
- `giao-dien._v3_enhance_batch_viec_chay()` — lỗi 1 record không dừng cả
  batch (giống pattern Sinh bài chính), cập nhật tiến độ real-time.

**Test end-to-end thật** (không chỉ mock đơn lẻ như Đợt 1) — dựng 1
dataset 3 SKU cùng nhóm trong DB test riêng, monkeypatch Serper/Gemini
(không cần mạng thật), chạy `_v3_enhance_batch_viec_chay()` qua app
Tkinter thật (Xvfb) — xác nhận: 3/3 OK, DB ghi đúng 9 dòng lịch sử insight
(3 record × 3 ý/record), không exception, không trùng. Đây là lần đầu
Đợt 1 (chống lặp) được test THẬT với nhiều SKU trong 1 lần chạy, không
chỉ test đơn lẻ từng hàm.

`tests/test_enhance_mock.py` vẫn 19/19, `xvfb-run tests/test_ver3_ui.py`
vẫn 8/8 — không vỡ gì cũ.

Còn lại: #3 rút sâu hơn (so sánh use-case), #4 nguồn ngoài SERP (đang
cân nhắc lại) — xem sheet Backlog trong `docs/SONEALEO-TRACKLOG.xlsx`.

---

## SONEALEO VER 1.2 — Enhance chống lặp insight (Đợt 1/4) + file Tracklog — 31/07/2026

**Đợt 1/4 trong roadmap mở rộng Enhance** (Thịnh chọn ưu tiên: chống lặp
trước, vì #3 tự động chạy cả nhóm mà chưa có #1 sẽ nhân bản lỗi lặp ra
hàng loạt SKU — đúng lỗi boilerplate Ver 5.3 từng bị, chỉ khác nguồn).

- Thêm bảng `enhance_lich_su_insight` (db_phase2.py) — lưu lại từng ý
  insight ĐÃ THẬT SỰ dùng (Hard Block sạch, không bị cảnh báo) cho mỗi
  NHÓM sản phẩm (`ten_loai_san_pham` chuẩn hoá), không theo từng SKU
  riêng — đúng mục đích chống lặp GIỮA CÁC SKU CÙNG NHÓM.
- `enhance.enhance_1_san_pham()` nhận thêm `con=None` (tuỳ chọn, backward
  compatible) — có `con` thì tự đọc lịch sử trước khi gọi Gemini, nhét
  vào prompt dặn "đừng lặp ý này", tự ghi lại sau khi thành công.
- Nối `con` vào cả 2 chỗ gọi Enhance trong `giao-dien.py` (luồng chính
  tab 4 + nút Test tay tab 8).
- Test: `tests/test_enhance_mock.py` 19/19 PASS (5 test mới cho chống
  lặp: ghi/đọc lịch sử, cách ly giữa 2 nhóm khác nhau, prompt có câu dặn
  đúng, backward-compat khi `con=None`). `xvfb-run tests/test_ver3_ui.py`
  8/8 PASS (không vỡ GUI).

**Mới: `docs/SONEALEO-TRACKLOG.xlsx`** — file Excel theo dõi các bản
nâng cấp (Thịnh yêu cầu, để khỏi phải đọc lại toàn bộ CHANGELOG dài mỗi
lần cần biết bản này khác gì bản trước). 3 sheet: Tracklog (lịch sử theo
version), Backlog (việc chưa làm + lý do), Đọc trước (hướng dẫn dùng
file). KHÔNG thay thế 4 doc chuẩn (SPEC/CHANGELOG/KNOWN-ISSUES/
TEST-REPORT) — chỉ là bản tóm tắt dễ lướt, cập nhật tay mỗi bản.

Còn lại trong roadmap 4 đợt: #2 tự động chạy cả nhóm, #3 rút sâu hơn
(so sánh use-case), #4 nguồn ngoài SERP (đang cân nhắc lại, rủi ro chất
lượng nguồn cao — xem sheet Backlog).

---

## SONEALEO VER 1.1 — Đổi tên (từ Lotech Autopost Ver 5.4) — 31/07/2026

Đổi tên dự án thành **SONEALEO** ("SEO Alone" đọc lái — Thịnh làm SEO 1
mình từ Excel tới đăng bài, không có ai khác trong team). Đánh dấu 1
chặng, KHÔNG đổi kiến trúc/logic/số phiên bản nội bộ — code y hệt Ver
5.4 Claude (nối catalogue máy biến áp vào bảng thông số + khai sẵn bảo
hành/chứng nhận, xem mục Ver 5.4 bên dưới). Chỉ đổi tên thư mục + README.

**Module Enhance (`enhance.py`) — mới, CHƯA ghép vào `giao-dien.py`:**
Tự động lấy top URL Google cho 1 loại sản phẩm, rút insight cấu trúc/góc
nhìn (KHÔNG rút số liệu — 2 lớp chặn: `loc_bo_muc_co_so()` cấm mọi chữ
số trong insight + Hard Block `kiem_tra_bia()` chạy lại lần cuối trên
bản đã merge), chỉ chèn vào phần văn xuôi, không đụng bảng thông số.
Test mock 14/14 PASS (`tests/test_enhance_mock.py`).

Nguồn tìm URL: **thử Google Custom Search API trước, KHÔNG dùng được**
— Google đã đóng API này cho mọi project Cloud tạo mới (403
PERMISSION_DENIED vĩnh viễn, xác nhận qua báo cáo lỗi cộng đồng
5/2026, không phải lỗi cấu hình). Đổi sang **Serper.dev** — 1 API key
duy nhất, không cần Search Engine ID, free 2.500 query lúc đăng ký,
đủ dùng cho nhóm ưu tiên (máy biến áp + tủ RMU, ~537 SKU) mà không tốn
phí. Cấu hình lưu qua `cauhinh.luu_serper()`/`doc_serper()` — khoá env
`SERPER_API_KEY`.

Việc kế tiếp: ~~ghép tab Enhance vào `giao-dien.py`~~ ĐÃ GHÉP XONG — cài
được `python3-tk` + `Xvfb` (màn hình ảo) trong môi trường dev, nên thật
sự khởi động được app và test tab mới, không còn phải đoán mù. Tab
"8. Enhance" đã thêm: ô nhập/lưu Serper key, checkbox bật/tắt cho lần
Sinh bài tiếp theo (mặc định TẮT — hành vi cũ không đổi nếu không bật),
nút "Test Enhance" test tay 1 record bằng ai_data mock (không tốn Gemini,
chỉ tốn 1 credit Serper). Đã nối vào vòng lặp sinh bài chính (tab 4) —
lỗi Enhance KHÔNG chặn đăng bài, tự động dùng ai_data gốc nếu Enhance
lỗi. CHƯA nối vào luồng Article Jobs (tab 7) — phạm vi Ver 1.1 chỉ tab 4.

Chạy `xvfb-run -a python3 tests/test_ver3_ui.py` xác nhận 8/8 PASS (đã
sửa lại assertion cứng "7 tab" thành "8 tab"). Chạy lại toàn bộ 33 file
test cũ, đối chiếu với bản gốc Ver 5.3 chưa sửa gì: các lỗi còn lại
(test_v37_1_patch, test_v37_batch_real, test_v39_article_jobs,
test_v45_checklist_lien_quan) đã CÓ SẴN từ trước, KHÔNG liên quan tới
Enhance — xác nhận bằng cách chạy lại đúng test đó trên bản gốc, lỗi y
hệt. test_v34_that_ui chập chờn (flaky) trên cả bản gốc lẫn bản mới khi
chạy dưới Xvfb nhiều lần liên tiếp — môi trường, không phải code.

---

## LOTECH AUTOPOST VER 5.4 CLAUDE — Nối catalogue máy biến áp vào bảng thông số + khai sẵn bảo hành/chứng nhận — 31/07/2026

Theo phản hồi review thật (checklist B2B nhận từ Thịnh): bảng thông số
máy biến áp bị chê "quá sơ sài, thiếu tổ đấu dây/tổn hao/kích thước" —
đúng, vì 15 SKU MBT đã enrich catalogue thật (Ver trước) nhưng
`profiles.py` chưa từng đọc các cột đó.

1. **Nối 10 field catalogue máy biến áp** (Tổ đấu dây, Po, Pk, Io%, Uk%,
   E50, 4 kích thước A-D, khối lượng dầu, tổng khối lượng) vào
   `cot_import`/`cot_ai`/`cot_bang` của `may_bien_ap_do_luong` +
   `OUTLINES['outline_may_bien_ap']`. Không bắt buộc (`cot_bat_buoc`
   không đổi) — SKU chưa enrich vẫn import/đăng bình thường, bảng thông
   số tự bỏ dòng trống (`bang_thong_so()` đã có sẵn logic này, không sửa
   thêm). Hard Block chống bịa tự nhận field mới hợp lệ, không cần đăng
   ký thêm (`_kho_cua_dong()` lấy động từ `effective_cot_ai`/
   `effective_cot_bang`).
2. **Bullet/in đậm cho Đặc điểm/Ứng dụng**: đã có sẵn từ Ver 5.3 (rule
   12, `QUY_TAC_CHUNG`). Chỉ bổ sung nhãn tiếng Việt cho 12 field mới
   trong `nhan_cot` (prompts_phase2.py) — thiếu nhãn thì prompt hiện tên
   field thô (`to_dau_day`) thay vì "Tổ đấu dây".
3. **Khai sẵn field bảo hành/chứng nhận** (`bao_hanh_thang`,
   `chung_nhan`) vào cột Excel + bảng thông số — **chưa có dữ liệu thật**
   (Thịnh xác nhận không chắc data tồn tại), cố tình để trống, không bịa
   số tháng bảo hành/tên chứng nhận. Khi có data thật, thêm cột vào
   MASTER là chạy được ngay, không cần sửa code lần nữa. Chưa build khối
   trust-signal riêng có icon (review đề xuất) — hoãn tới khi có data.

Đã render thử qua code thật (không mock): SKU có catalogue (MBT3P250)
ra bảng 18 dòng, SKU thường (TBD1P25) vẫn 5 dòng như cũ — không vỡ bài
cũ. `_kiem_tra_registry()` pass.

**File sửa:** `profiles.py`, `prompts_phase2.py`.

---

## LOTECH AUTOPOST VER 5.3 CLAUDE — Giai đoạn 1 của Đề xuất toàn diện — 30/07/2026

Thực thi 7 hạng mục "code ngay" từ DE-XUAT-TOAN-DIEN-LOTECH-AUTOPOST.md:
(B5) nút "Cập nhật lại bài đã đăng" — giải quyết đúng vấn đề mọi fix
trước đây vô hình trên bài cũ; (B6) Hard Block chặn thì thất bại ngay
thay vì đốt hết cặp dự phòng, test bằng mock xác nhận đúng; (C6) khối
"Về lõi Silic/Amorphous"; (C7) khối "Bảo trì & lắp đặt"; (C8) bullet/in
đậm qua prompt; (C9) grid sản phẩm liên quan; (C10) hạ tầng nút Tải
Catalogue (field optional, chưa có nội dung tới khi có PDF thật). 30 test
mới + 21/30 file cũ chạy được đều PASS (481 test case). Chi tiết
`docs/lich-su-phien-ban/CHANGELOG-VER53.md`.

**File sửa:** `giao-dien.py`, `ai_wp_adapter.py`, `render_phase2.py`,
`profiles.py`, `prompts_phase2.py`, 2 file test.

**File mới:** `tests/test_v53_patch.py`.

---

## LOTECH AUTOPOST VER 5.2 CLAUDE — Outline riêng cho "Vỏ mạ kẽm" + CTA/bảng sửa theo phản hồi thật — 30/07/2026

Từ ảnh chụp site thật: "Vỏ mạ kẽm nhúng nóng MBA..." (vỏ thép, KHÔNG phải
máy biến áp) bị gọi nhầm "Máy biến áp MBT 1500kVA" trong title/so sánh
công suất/delta context — do các hàm này chỉ gate theo outline_id, thêm
tính năng mới sau Ver 4.9.7 mà không rà lại. Tách outline riêng
`outline_vo_may_bien_ap`. Đồng thời: title "Báo Giá" chuyển lên đầu câu,
bảng so sánh công suất hiện TÊN sản phẩm thay vì mã hàng, CTA "Yêu cầu
báo giá" đổi sang gọi thẳng thay vì nhảy trang. Phát hiện phụ: "tải ước
tính (kW)" từng tính nhầm cho vỏ (vỏ không tiêu thụ điện) — đã chặn. 17
test mới đều PASS. Chi tiết `docs/lich-su-phien-ban/CHANGELOG-VER52.md`.

**File sửa:** `profiles.py`, `render_phase2.py`, `db_phase2.py`,
`prompts_phase2.py`.

---

## LOTECH AUTOPOST VER 5.1 CLAUDE — Audit lại toàn bộ tool + vá 4 lỗi thật + gọn thư mục — 30/07/2026

Tự kiểm chứng lại review Gemini/GPT bằng code/data thật (không nghe kể) —
kết quả ghi vào `Audit-Checklist-Ver5.0.xlsx`. Vá 4 lỗi mức nghiêm trọng
nhất: SKU trùng đè nhau trên WooCommerce (17 mã/34 dòng, thêm publish_sku),
title bị cắt 70 ký tự gây trùng (50 nhóm/120 dòng, giảm còn 22, phần còn
lại là lỗi Tên hàng gốc trong MASTER), nút "Nghỉ giữa 2 bài" chết hoàn
toàn (giờ hoạt động thật), ma trận key/model dự phòng thiếu tổ hợp (đã bổ
sung). Tự phát hiện thêm: "full regression" trước giờ bỏ sót 9/28 file
test — chạy lại đủ, sửa 1 file thật sự lỗi thời. Gọn thư mục (gom .md vào
docs/, test vào tests/), KHÔNG đụng code chính theo đúng nguyên tắc "code
chạy được thì để yên". Thêm icon riêng cho shortcut. 20 test mới + 20/28
file cũ chạy được đều PASS (411 test case; 8 file cần tkinter chưa xác
định được trong sandbox). Chi tiết
`docs/lich-su-phien-ban/CHANGELOG-VER51.md`.

**File sửa:** `nhap_phase2.py`, `render_phase2.py`, `giao-dien.py`, nhiều
file test, 4 file `.bat`.

**File mới:** `tests/test_v51_patch.py`, `README.md`,
`icon/lotech-autopost.ico`, `TAO-SHORTCUT-CO-ICON.bat`.

---

## LOTECH AUTOPOST VER 5.0 CLAUDE — Vá lỗi MAX_TOKENS + hoàn thiện UX trang sản phẩm — 30/07/2026

Từ log production thật (batch 50 sản phẩm bị dừng ở #6, lỗi "Bài bị cắt
vì vượt giới hạn token") + ảnh chụp site thật: VÁ BUG THẬT — Gemini 3.x
"suy nghĩ ngầm" không giới hạn, ăn chung ngân sách maxOutputTokens với câu
trả lời JSON, gây cắt bài giữa chừng. Vá bằng thinkingConfig.thinkingBudget
=6000 + nâng maxOutputTokens 24000→48000. Cùng đợt: title bỏ mã hàng +
thêm "Báo Giá" (điều chỉnh sau khi xem thật thấy không hợp mắt), CTA nổi
bật hơn (không animation — giới hạn kỹ thuật thật của inline style), bảng
so sánh công suất có link khi SKU đã đăng, placeholder chèn ảnh, "Đặc
điểm" chia nhiều đoạn dễ đọc, thêm nút xem trước dạng trang HTML thật qua
trình duyệt. 22 test mới + 240 test cũ đều PASS (262/262). Chi tiết
`CHANGELOG-VER50.md`/`TEST-REPORT-VER50.md`.

**File sửa:** `ai_wp_adapter.py`, `render_phase2.py`, `db_phase2.py`,
`prompts_phase2.py`, `giao-dien.py`, `test_v498_patch.py`,
`test_v499_patch.py`.

**File mới:** `test_v50_patch.py`.

---

## LOTECH AUTOPOST VER 4.9.9 CLAUDE — Chống trùng lặp SEO (Delta Context) + CSS inline + Title SKU-first — 29/07/2026

Theo review SEO độc lập (Gemini) trên 2 bài đăng thật: phát hiện trùng lặp
~85% giữa SKU cùng dòng + boilerplate lặp 100%. Vá: Delta Context (tier/
chênh lệch kVA-%/tải ước tính) tính BẰNG CODE, đưa vào prompt AI để chống
trùng — test xác nhận Hard Block chấp nhận số thật nhưng vẫn chặn số AI tự
bịa thêm (quan trọng nhất bản này). CSS chuyển hẳn sang inline (không cần
Thịnh thao tác tay), bỏ prefix "lotech-" (không để dấu vết tool). Boilerplate
rút còn 1 câu. Title/H1 SKU-first, code dựng cố định, không ngày tháng.
Thêm khối "Về thương hiệu" (data catalogue thật MBT/THIBIDI). Đã phản biện
và KHÔNG áp dụng 2 đề xuất của Gemini có rủi ro bịa số (% AF, % tiết kiệm
chi phí) và 1 đề xuất đi ngược nguyên tắc Google (ép quota từ khoá). 31
test mới + 208 test cũ đều PASS (239/239). Chi tiết
`CHANGELOG-VER499.md`/`TEST-REPORT-VER499.md`.

**File sửa:** `render_phase2.py`, `profiles.py`, `prompts_phase2.py`,
`giao-dien.py`, `test_round2_integration.py`, `test_v497_patch.py`,
`test_v498_patch.py`.

**File mới:** `test_v499_patch.py`.

---

## LOTECH AUTOPOST VER 4.9.8 CLAUDE — CTA đồng bộ + So sánh công suất + CSS giao diện — 29/07/2026

Theo phản hồi Thịnh trên demo "ultra": CSS giao diện dán 1 lần vào Theme
(không nhét vào content — tránh lặp bug script/style bị WordPress kses
xoá); CTA cuối trang đổi sang dạng nút đồng bộ CTA gọn, giữ nguyên anchor;
bảng so sánh công suất trong dòng — 100% code, data thật từ MASTER, phát
hiện phụ: cột Cấp Điện Áp trong MASTER bị lỗi dữ liệu, đã ẩn khỏi bảng mới;
gộp "2 góc nhìn" kỹ sư/đầu tư thành 1 đoạn tự nhiên theo đúng yêu cầu. 17
test mới + 191 test cũ đều PASS (208/208). Chi tiết
`CHANGELOG-VER498.md`/`TEST-REPORT-VER498.md`.

**File sửa:** `render_phase2.py`, `db_phase2.py`, `prompts_phase2.py`,
`giao-dien.py`.

**File mới:** `test_v498_patch.py`, `lotech-theme.css`.

---

## LOTECH AUTOPOST VER 4.9.7 CLAUDE — Khối cố định "về máy biến áp nói chung" — 29/07/2026

Tách sự thật đúng cho CẢ DÒNG máy biến áp (nguyên lý làm mát, ứng dụng
chung, tiêu chuẩn ngành, lưu ý lắp đặt) ra khối do CODE viết cứng, không để
AI đoán lại mỗi SKU. Tách riêng 2 bản DẦU (ONAN) và KHÔ (AN/AF) vì khác
nguyên lý hoàn toàn — gán nhầm là bịa sai thông tin thật. Không nhận diện
được loại (VD dòng phụ kiện vỏ) thì để rỗng, không đoán. Chỉ áp dụng đúng
outline_may_bien_ap. 22 test mới + 169 test cũ đều PASS (191/191). Quét
thật 165 dòng MASTER xác nhận 0 lệch. Chi tiết
`CHANGELOG-VER497.md`/`TEST-REPORT-VER497.md`.

**File sửa:** `render_phase2.py`, `giao-dien.py`.

**File mới:** `test_v497_patch.py`.

---

## LOTECH AUTOPOST VER 4.9.6 CLAUDE — Vá 4 lỗi từ ảnh chụp production thật — 29/07/2026

Từ phản hồi thật của Thịnh trên site maybienapvn.vn: (1) BUG THẬT — Schema
JSON-LD lộ ra thành chữ trên trang do WordPress kses xoá thẻ `<script>`
khi lưu qua REST API, giờ trả riêng qua key `schema` thay vì nhét vào
`html`; (2) bỏ khối checklist báo giá (giảm lead); (3) sửa rule prompt để
content "hướng dẫn lựa chọn" bớt công thức cứng "gửi bản vẽ..."; (4) slug
thêm từ khoá SEO từ tiêu đề thay vì chỉ mã hàng suông; (5) tự phát hiện +
vá thêm: không resend slug khi update bài đã đăng thật (tránh phá URL đã
index). 14 test mới + 155 test cũ đều PASS (169/169). Chi tiết
`CHANGELOG-VER496.md`/`TEST-REPORT-VER496.md`.

**File sửa:** `render_phase2.py`, `prompts_phase2.py`, `ai_wp_adapter.py`,
`giao-dien.py`, `test_gate2.py`.

**File mới:** `test_v496_patch.py`.

---

## LOTECH AUTOPOST VER 4.9.5 CLAUDE — Profile đầu cáp/hộp nối enrich catalogue — 29/07/2026

Nối 90 SKU đầu cáp/hộp nối (ABB/3M) vừa enrich từ catalogue thật vào pipeline
Phase 2 Lite — profile `phu_kien_va_khac` thêm 6 field kỹ thuật, outline mới
`outline_dau_cap_ky_thuat`, routing tự động theo cột `nguon_catalogue`. Vá 1
bug backward-compat phát hiện trước khi merge (import MASTER chưa enrich sẽ
crash nếu không tách `cot_bat_buoc`). Thử thêm `offers` vào Product Schema
rồi revert vì phá quyết định cũ đã có test khẳng định. 21 test mới + 134 test
cũ đều PASS (155/155). Chi tiết `CHANGELOG-VER495.md`/`TEST-REPORT-VER495.md`.

**File sửa:** `nhap_phase2.py`, `profiles.py`, `prompts_phase2.py`,
`render_phase2.py`, `giao-dien.py` (đổi tiêu đề bản).

**File mới:** `test_v495_patch.py`.

---

## LOTECH AUTOPOST VER 3.6 — Mock Batch Integrity + Tab Order — 25/07/2026

Vá bug batch Mock thật (review độc lập phát hiện 223/245, không phải tự
khai) + siết test không cho pass giả + đổi thứ tự tab. **181/181 test PASS,
0 FAIL**, verify portable. Chi tiết `BAO-CAO-KHOI-LUONG.md` (file mới, đủ
13 mục).

**File sửa:**
- `render_phase2.py` — thêm `rut_gon_an_toan()` (cắt tại ranh giới từ,
  không cắt giữa token kỹ thuật), áp dụng cho `title`/`meta_description`
  trong `dung_bai_html()`.
- `ai_wp_adapter.py` — `goi_ai_mock()`: `meta_title` dùng
  `rut_gon_an_toan()`, `faq.q` dùng nguyên tên sản phẩm (không cắt).
- `giao-dien.py` — đổi thứ tự gọi hàm dựng 5 tab: Cấu hình → Nhập dữ liệu →
  Sản phẩm → Sinh & Đăng → Theo dõi; đổi nhãn số thứ tự 3 tab bị dịch vị
  trí. Không đổi callback/state/widget bên trong.
- `PHAN-MEM.bat` — thêm thông báo "bước tiếp theo" ở cả 2 nhánh thành công.
- `CAI-DAT-LAN-DAU.bat` — toàn bộ `set VAR=value` → `set "VAR=value"`.
- `test_v34_that_ui.py` — MOCK-3 đếm chính xác qua DB thay vì tìm chữ
  "Xong" trong nhãn.
- `test_ver3_ui.py` — cập nhật 2 chỗ giả định thứ tự tab cũ.

**File mới:**
- `test_v36_regression.py` — 16 test: token kỹ thuật không bị cắt (36 case
  pattern×giới hạn + 11 case biên), batch thật 245 record, và 3 test PROOF
  chứng minh assertion mới bắt lỗi thật mà assertion cũ bỏ lọt.
- `BAO-CAO-KHOI-LUONG.md` — báo cáo khối lượng đủ 13 mục.

**Bug thật phát hiện qua review độc lập, đã vá (không phải tự khai):**
1. `goi_ai_mock()` cắt `ten[:60]`/`ten[:40]` — cắt giữa token kỹ thuật dính
   liền (`22/0.4KV`, `3x50+1x25mm²`...) làm batch 245 sản phẩm máy biến áp
   chỉ đạt 223/245 (22 lỗi Hard Block do chuỗi cắt dở trông giống bịa số).
2. `test_v34_that_ui.py` MOCK-3 chỉ kiểm chữ "Xong" có trong nhãn — PASS dù
   có lỗi thật (chứng minh bằng test PROOF cố ý gây 1 lỗi, xác nhận cách cũ
   pass sai).

**Cố ý KHÔNG làm** (tracker đã tự xếp Gate sau, không phải bỏ sót):
Filter Builder (Ver 3.7), Outline Studio (Ver 3.8), Article Jobs/số lượng
bài +/-/đăng toàn batch (Ver 3.9).

---

## LOTECH AUTOPOST VER 3.5 — Real Draft Readiness & Windows Handoff — 25/07/2026

Vá 3 lỗ hổng GPT phát hiện qua kiểm tra độc lập trên bản 3.4 (không tự sửa
lời khai, xác nhận cả 5 điểm đúng bằng đọc thẳng code trước khi vá).
**164/164 test PASS** — verify từ thư mục khác hẳn (`/tmp/portability_check`),
không còn kiểu tài liệu ghi 1 số nhưng ZIP chỉ chạy được số khác.

**File sửa:**
- `ai_wp_adapter.py` — `sinh_va_dang_mock()` xoá đoạn Hard Block riêng (chỉ
  4 field văn xuôi), gọi thẳng `kiem_tra_bia_toan_bo()` — cùng hàm luồng
  Real dùng. Thêm `chuan_hoa_url()`/`site_key` liên quan qua `cauhinh.py`.
- `giao-dien.py` — `_phase2_chay_thu()` (nút "Xem trước HTML") cũng gộp
  dùng `kiem_tra_bia_toan_bo()`. Thêm `_v3_site_key()`, sửa mọi nơi ghi DB
  dùng `site_key` thay vì `wc['ten']`. Thêm `_v3_di_chuyen_du_lieu_khoa_cu()`
  (auto-migration lúc khởi động + lúc lưu website). Sửa Tab 5 dashboard:
  lọc theo site_key, hiển thị tên đẹp riêng. Lưu `self._boc_hang_doi_job`,
  `after_cancel()` trong `_dong()`. Xoá 2 hàm định dạng trùng lặp
  (`_v3_dinh_dang_thoi_gian/luong`), gọi lại bản dùng chung ở `db_phase2.py`.
- `cauhinh.py` — thêm `chuan_hoa_url()`, `site_key()`, `doc_website()` trả
  thêm field `site_key` (khoá THẬT, tách khỏi `ten` chỉ để hiển thị).
- `db_phase2.py` — thêm `doi_khoa_site()` (migration, chỉ UPDATE 1 cột, giữ
  nguyên wp_id/url/trạng thái/thời lượng), `liet_ke_site_dang_dung()`, và 2
  hàm định dạng dùng chung `dinh_dang_thoi_gian()`/`dinh_dang_thoi_luong()`
  (trích từ `giao-dien.py` để cả GUI lẫn CLI dùng chung).

**File mới:**
- `cong_cu_kiem_tra_ket_qua.py` — CLI đọc DB, dùng nguyên hàm `db_phase2.py`,
  không viết logic riêng.
- `5-KIEM-TRA-KET-QUA.bat` — wrapper mỏng gọi file trên.
- `test_v35_idempotency.py` — 11 test website identity + migration.

**File sửa nhẹ:** `test_v34_that_ui.py` — sửa hard-code path
`/home/claude/work/build` → portable; sửa verify dùng `site_key` thay vì
tên hiển thị cũ.

**Bug thật GPT phát hiện, đã verify và vá (không phải tự khai):**
1. Mock/Preview đăng "thành công" dù `meta_title`/`meta_description`/`faq.q`
   chứa số bịa — do dùng đoạn Hard Block RIÊNG, không phải
   `kiem_tra_bia_toan_bo()`. Tái hiện đúng kịch bản GPT tiêm, xác nhận vá.
2. Đổi tên website làm mất liên kết bài cũ (khoá theo `ten` thay vì URL).
3. `test_v34_that_ui.py` hard-code path sandbox, không chạy được từ ZIP.
4. Số liệu test lệch nhau giữa 4 file tài liệu (174 vs 153) — do sửa tay 2/4
   file, quên 2 file còn lại. Giờ cả 4 cùng lấy từ 1 lần chạy thật.
5. Callback `after()` không được huỷ lúc đóng app, Tcl báo lỗi.

---

## LOTECH AUTOPOST VER 3.4 — Gate "First Real Draft" — 25/07/2026

Mục tiêu: 1 Draft thật trên WordPress Admin. 153/153 test PASS (125 kế thừa
+ 28 mới, xem ghi chú sửa số ở mục Ver 3.5 phía trên). Chi tiết đầy đủ
`TEST-REPORT.md`/`TIEN-DO.md`.

**File sửa:**
- `giao-dien.py` — Task 1 (multi-select bôi đen, sửa bug preview, nhật ký
  35%, Force Stop, progress bar nổi bật — xem mục riêng lượt trước); Task 2
  (Tab 3 AI: API key + nút "Kiểm tra API key và model" gọi
  `autopost.do_model()`); Task 3 (Tab 3 Website: Lưu/Sửa/Xoá/Kiểm tra kết
  nối thật; Tab 4: chế độ Mock/WordPress thật, nút đổi tên động, luồng đăng
  1 record active; Tab 5: thêm cột Thời lượng, định dạng thời gian/thời
  lượng đúng chuẩn). Sửa bug thật: 3 chỗ còn sót dùng `C.lay_site()`/
  `C.tat_ca_site()` (site1/site2) trong luồng Ver 3, thay bằng
  `cauhinh.doc_website()`.
- `cauhinh.py` — thêm `import os`, `from pathlib import Path`, `BASE`
  (chưa từng có trước đây); thêm `ghi_env()`, `doc_website()`,
  `luu_website()`, `xoa_website()`, `luu_gemini()`, `doc_gemini()`,
  `MA_SITE_VER3='website'`.
- `ai_wp_adapter.py` — thêm `goi_ai_that()`, `kiem_tra_bia_toan_bo()`,
  `kiem_tra_ket_noi_wp()`; viết lại hoàn chỉnh `dang_wp_that()` (ép cứng
  draft, idempotent, không retry mù).
- `db_phase2.py` — thêm cột `thoi_luong_giay` (migration `ALTER TABLE` an
  toàn cho DB cũ), cập nhật `cap_nhat_bai_viet`/`lay_bai_viet`/`dashboard`.

**File mới:** `test_that_mocked.py` (21 test Gemini/WordPress thật với
`requests` giả lập), `test_v34_that_ui.py` (7 test tích hợp qua UI thật).

**Bug thật phát hiện và sửa trong lúc code:**
1. Site1/site2 (RMU) lọt vào 3 chỗ trong luồng Ver 3 (`_phase2_xem_prompt`,
   `_phase2_chay_thu`, `_phase2_viec_chay_hang_loat`) — vi phạm thẳng yêu
   cầu "không hiển thị site1/site2". Phát hiện qua crash `SystemExit` lúc
   chạy test tích hợp đầy đủ, không phải đọc code phát hiện trước.
2. (Kế thừa ghi chú Task 1 lượt trước) bug preview mất focus sau refresh,
   bug thread-safety `messagebox` gọi từ luồng nền.

---

## LOTECH AUTOPOST VER 3 — UI Gate — 25/07/2026

Đổi UI mặc định: 5 tab Ver 3 (Nhập dữ liệu / Sản phẩm / Cấu hình / Sinh &
Đăng / Theo dõi) thay cho 7 tab RMU/Phase-2-lẫn-lộn cũ. RMU ẩn mặc định,
vào qua menu "Công cụ → Chế độ RMU (rollback)". 125/125 test PASS.

**File sửa:** CHỈ `giao-dien.py` (đúng phạm vi work order — không đụng AI
adapter/prompt/schema/Hard Block/validators/database/pipeline import).

- Thêm palette màu riêng Ver 3 (`V3_NAVY`, `V3_TEAL`, `V3_BG`...) và style
  ttk riêng (`V3.TNotebook`, `V3.TButton`...), KHÔNG đụng hằng số màu/style
  RMU cũ (`NAVY`, `GREEN`... vẫn nguyên, RMU giữ đúng giao diện cũ 100%).
- Header giảm chiều cao (62→48px), cỡ chữ tiêu đề giảm về 16 (đúng giới hạn
  work order).
- Thêm menu bar + `_menu()`, `_chuyen_che_do_rmu()`, `_chuyen_ve_ver3()`.
- Tái cấu trúc `__init__`: 2 `ttk.Notebook` độc lập (`self.tab` = RMU,
  `self.tab_ver3` = Ver 3), cả 2 dựng 1 lần, chỉ pack/pack_forget khi
  chuyển chế độ — không nhân đôi widget.
- **Xoá `_tab_phase2()` cũ** (tab 6 "Phase 2 (4-Profile)" của Round 2/Gate 2)
  — tách thành 5 hàm `_v3_tab_1_nhap_du_lieu()` .. `_v3_tab_5_theo_doi()`,
  TÁI SỬ DỤNG nguyên các widget/hàm xử lý cũ (`self.bang_phase2`,
  `self.txt_phase2_thu`, `_phase2_xem_prompt`, `_phase2_chay_thu`,
  `_phase2_chay_hang_loat`...), chỉ đổi cách bố trí + thêm phần mới (báo
  cáo import dạng bảng, bộ lọc Outline/tìm kiếm, thống kê, radio chế độ
  Mock/WordPress thật, cột Tên sản phẩm + Lỗi ở dashboard).
- Thêm hàm mới: `_v3_loc_san_pham()` (lọc + thống kê, thay `_phase2_nap_danh_sach`
  làm hàm refresh chính), `_v3_nap_dashboard()` (dashboard 11 cột, dùng
  nguyên `db_phase2.py` không sửa gì), `_v3_nap_danh_sach_dataset()`,
  `_v3_cap_nhat_bao_cao()`, `_v3_mo_url()`.
- `_phase2_nap_dashboard()` (tên hàm cũ) giữ lại làm alias gọi
  `_v3_nap_dashboard()` — tương thích ngược cho chỗ gọi cũ.

**File mới:** `test_ver3_ui.py` (8 test bắt buộc mục I work order, qua
Xvfb thật + chụp 6 ảnh bằng chứng vào `anh-bang-chung-ui/`).

**File sửa nhẹ khác:** `test_round2_ui_smoke.py` — 1 assertion cấu trúc tab
cập nhật lại (RMU giờ đúng 6 tab gốc, không còn lẫn tab Phase 2 cũ — đúng ý
đồ UI Gate, không phải hồi quy).

---

## LOTECH AUTOPOST VER 3 — Content Safety Gate 2 — 25/07/2026

Đổi tên phiên bản từ "Claude v2.8" sang **LOTECH AUTOPOST VER 3** (title cửa
sổ, header, 3 file `.bat`). 4 task theo work order, 117/117 test PASS —
chi tiết `TIEN-DO.md` (bảng bắt buộc) và `TEST-REPORT.md`.

**File sửa:**
- `render_phase2.py` — thêm `dung_schema_script()` (Schema JSON-LD gắn vào
  HTML thật), thêm lớp Hard Block thứ 3 `_CUM_MO_RONG_RE`/
  `_kho_mo_rong_cua_dong()` (bảo hành/IPxx/IEC-TCVN/nhiệt độ/%, chạy trước
  lớp cụm kỹ thuật R2-08), `dung_slug()` nhận `mau` (luôn suffix), `dung_bai_html()`
  nhận `mau`.
- `prompts_phase2.py` — thêm `MAU_BIEN_THE` (`chuan`/`ngan_gon`), `he_thong()`/
  `nguoi_dung()`/`_json_schema()`/`xay_prompt()`/`truong_ai_duoc_tra()` đều
  nhận thêm tham số `mau`, tạo prompt/JSON schema khác nhau thật giữa 2 mẫu.
- `ai_wp_adapter.py` — `goi_ai_mock()` nhận `mau`, tôn trọng đúng cấu hình bỏ
  section/FAQ theo mẫu; `sinh_va_dang_mock()` truyền `mau` xuống cả 2 hàm trên.
- `giao-dien.py` — đổi title/header sang VER 3; nối widget "Mẫu" (đã có từ
  Round 2) vào `_phase2_xem_prompt()`/`_phase2_chay_thu()` qua hàm mới
  `_phase2_mau_dang_chon()`; sửa `_phase2_chay_hang_loat()`/
  `_phase2_viec_chay_hang_loat()` để validate `mau` ở luồng chính trước khi
  vào luồng nền (sửa bug thread-safety, xem bên dưới).
- `CAI-DAT-LAN-DAU.bat`, `PHAN-MEM.bat`, `KIEM-THU-30-BAI.bat` — đổi `title`.

**File mới:** `test_gate2.py` (bộ test D1-D7 chính thức Gate 2).

**Bug thật phát hiện và sửa trong lúc code:**
1. Thread-safety Tkinter — `_phase2_mau_dang_chon()` (có gọi `messagebox`)
   ban đầu được gọi từ trong `_phase2_viec_chay_hang_loat()`, hàm này chạy ở
   LUỒNG NỀN qua `chay_nen_phase2()`. Gọi `messagebox`/đụng widget từ luồng
   nền vi phạm nguyên tắc Tkinter không thread-safe (comment sẵn có trong
   code: "luồng nền TUYỆT ĐỐI không đụng vào tkinter"). Sửa: validate `mau`
   ở `_phase2_chay_hang_loat()` (luồng chính, gọi trực tiếp từ nút bấm),
   truyền qua tham số vào hàm chạy nền.

---

## Phase 2 — Round 2 — 25/07/2026

Nối Data Core (Round 1) thành luồng giả lập hoàn chỉnh: UI → import → chọn →
prompt Phase 2 thật → AI mock → HTML+bảng+schema → sanitize → WP mock →
dashboard. Đủ 12 hạng mục R2-01→R2-12, 12 test T2-01→T2-12 — chi tiết
`TIEN-DO.md` (bảng bắt buộc) và `TEST-REPORT.md`.

**File mới:**
- `db_phase2.py` — schema 3 bảng đa site/đa mẫu, thay bảng `ban_ghi` phẳng
  của Round 1 (đã xoá `kho_phase2.py` cũ).
- `prompts_phase2.py` — prompt Phase 2 thật, 7 outline (thêm `outline_service`
  tách riêng khỏi `outline_phu_kien` cho 41 dòng dịch vụ).
- `ai_wp_adapter.py` — AI/WordPress adapter: mock đầy đủ cho Round 2, khung
  thật tái sử dụng `autopost.py` qua import (chưa test, không có site/key).
- `test_round2_integration.py`, `test_round2_ui_smoke.py` — bộ test T2-01→T2-12.

**File sửa:**
- `nhap_phase2.py` — bỏ phần quản lý dataset SQLite cũ (chuyển hẳn sang
  `db_phase2.py`), thêm `import_phase2_pipeline()` (R2-01, gộp đủ 10 bước).
- `render_phase2.py` — xoá `dung_prompt()` cũ (thay bằng `prompts_phase2.py`),
  thêm `dung_bai_html()` (R2-06), nâng cấp Hard Block thành kiểm cụm kỹ thuật
  hoàn chỉnh trước token đơn (R2-08, Composite Hard Block).
- `profiles.py` — thêm `outline_service`; sửa nhãn `cot_bang` mang đơn vị
  đúng theo cột nguồn (R2-07: `"Tiết diện (mm²)"`, `"Công suất (kVA)"`,
  `"Cấp điện áp (kV)"`).
- `validators.py` — thêm bước bỏ hậu tố đơn vị trùng lặp cho máy biến áp
  (khớp nhãn mới mang đơn vị).
- `giao-dien.py` — thêm tab "6. Phase 2 (4-Profile)" (import/danh sách/thử 1
  bài/chạy/dashboard), thêm `bleach` vào kiểm tra thư viện khởi động.
- `CAI-DAT-LAN-DAU.bat`, `PHAN-MEM.bat` — thêm `bleach` vào danh sách cài.
- `test_phase2_full.py` — rút gọn còn phần Data Core không đổi (Registry +
  regex), phần DB/render cũ đã thay bằng bộ test Round 2.
- `test_snapshot_regex.py` — cập nhật kỳ vọng nhóm D theo format đơn vị mới
  (R2-07), thêm `profile_id` vào row giả lập cho đúng thực tế pipeline.

**Bug thật phát hiện và sửa trong lúc code (không phải lý thuyết) — chi tiết
đầy đủ ở `TEST-REPORT.md`:**
1. record_id lệch giữa MASTER và file con (Round 1, không tái phát ở Round 2
   — nhắc lại để không mất dấu lịch sử).
2. Composite Hard Block: token đơn lẻ trích từ cụm hợp lệ (`"1kV"` từ
   `"0.6/1kV"`) làm lọt cụm giả `"99/1kV"` nếu chỉ kiểm token — đã sửa bằng
   kiểm cụm trước.
3. `sanitize_html` giữ lại text bên trong `<script>`/`<style>` dù đã xoá tag
   — đã thêm bước xoá cả nội dung.
4. UI: `_phase2_doi_chon()` làm mất focus/selection của Treeview sau khi
   refresh bảng — đã sửa khôi phục lại focus đúng dòng.

---

## Phase 2 Lite — 24/07/2026 (nhánh mới, song song với v2.8 RMU)

Bản đầu tiên cho bộ dữ liệu chính thức 4 profile / 5.264 sản phẩm (thay bộ
tủ RMU cũ 98-111 sản phẩm dùng để test). Kiến trúc đã duyệt qua 2 vòng review
— xem `ARCHITECTURE-DRAFT-4-PROFILES.md` (mục 12: bảng tóm tắt mọi quyết
định) và `DATA-AUDIT-4-PROFILES.md`.

**File mới, KHÔNG đụng file cũ của nhánh RMU** (`dulieu.py`, `autopost.py`,
`cauhinh.py`, `prompts.py`, `giao-dien.py` giữ nguyên 100%, nhánh RMU vẫn
chạy độc lập):

1. `profiles.py` — Profile Registry (4 profile cố định) + Outline Registry +
   `normalize_cell()` + `effective_cot_ai()`/`effective_cot_bang()`. Có assert
   tĩnh chặn `gia_list`/`ghi_chu_ban_dau` lọt vào `cot_ai`/`cot_bang`, chạy
   ngay lúc import module.
2. `nhap_phase2.py` — dispatcher nhận diện nguồn (RMU cũ / 4-profile mới),
   đọc Excel theo header (không theo vị trí cột như `nhap_excel()` cũ),
   `file_checksum` + `data_checksum` (2 loại riêng biệt, xem kiến trúc mục
   3.1), quản lý `dataset_id` qua SQLite (`phase2-du-lieu.db`, DB riêng,
   không đụng `du-lieu.db` của nhánh RMU).
3. `validators.py` — validator riêng 4 profile: sửa bug kVA/kV (165 dòng máy
   biến áp), bóc thêm điện áp dạng "V" thường (291 dòng cáp), bóc thêm tiết
   diện đơn lõi (801 dòng cáp), xoá vật liệu sai cho 48 dòng Cu-Al. Routing
   `outline_id` cho 185 dòng phụ kiện lẫn trong cap_dien, 14 dòng vỏ tủ, 7
   dòng "Giá treo MBT".
4. `render_phase2.py` — `dung_prompt()`/`bang_thong_so()`/`dung_schema()`
   dùng `effective_cot_ai`/`effective_cot_bang` (Outline Registry), thêm
   `sanitize_html()` (whitelist qua `bleach`), đổi chống bịa số sang Hard
   Block tuyệt đối (bỏ mức "cảnh báo, vẫn đăng" của `autopost.py` cũ).
5. `kho_phase2.py` — dashboard + WP mapping theo khoá `(dataset_id,
   record_id)`, đảm bảo dataset mới không ghi đè URL/WP Post ID/trạng thái
   dataset cũ.
6. `test_phase2_full.py` + `test_snapshot_regex.py` — bộ test chạy trên dữ
   liệu THẬT (5.264 record), xem `TEST-REPORT.md`.

**Còn lại, CHƯA làm (ghi trong `KNOWN-ISSUES.md`)**: gắn `dispatcher_import()`
vào nút bấm thật trong `giao-dien.py` (UI Tkinter hiện vẫn gọi thẳng
`D.nhap_excel()` cho nhánh RMU, chưa có nút cho nhánh 4-profile mới) — cần
Thịnh xác nhận luồng UI mong muốn trước khi đụng vào file GUI 59KB.

---

## Claude v2.8 — 24/07/2026

6 việc đúng theo yêu cầu, không đụng kiến trúc, không thêm ngoài scope.

1. **Model mặc định** — đổi `gemini-2.5-flash` → `gemini-3.6-flash` ở cả 3 chỗ
   (GUI, `autopost.py`, `cau-hinh.env.MAU`). *Chưa verify được model này tồn
   tại thật vì không có key — tin theo yêu cầu, Thịnh tự kiểm khi chạy.*
2. **KPI dashboard chỉ tính sản phẩm đang chọn viết + lọc đúng site** — bug
   thật: trước đây KPI đếm cả site khác đang lọc và cả sản phẩm đã bỏ chọn.
3. **Trạng thái Lỗi tách riêng** — trước đây bài lỗi bị đếm gộp vào "Còn lại"
   (dashboard trong app) hoặc biến mất khỏi tổng (sheet Tổng quan Excel).
4. **Excel Bài viết** thêm cột WP Post ID, đổi nhãn rõ "Ngày đăng" / "URL đã
   đăng" / "Ghi chú / Nội dung lỗi".
5. **Bỏ `products.csv` cũ khỏi gói** — file đó là dữ liệu demo trước bản sửa
   lỗi trùng (v2.6), dùng sẽ ra 98 dòng thay vì đúng số record có giữ trùng
   riêng. Dữ liệu test bắt buộc import lại từ Excel gốc qua tab 1.
6. Slug/similarity/outline/dò model/portable — không đụng, đúng yêu cầu.

### Test — đúng luồng yêu cầu, trên dữ liệu thật (không dùng products.csv cũ)

Import Excel gốc (111 sản phẩm, giữ đủ 13 record trùng) → xem prompt 1 bài →
sinh lưu 1 bài (AI giả lập) → đăng thử 3 draft (WordPress giả lập, có
wp_id/URL riêng từng bài) → xuất Excel đối chiếu (khớp 100% với dữ liệu thật
trong DB) → chạy tiếp batch 20 bài (bỏ qua đúng bài đã làm, kể cả bài lỗi
được tự động thử lại). KPI trong app và trong Excel khớp nhau tuyệt đối ở mọi
bước. Nghiệm thu 5/5.

---

## Claude v2.7 — 24/07/2026

Làm tiếp mục #2 trong `TIEN-DO.md` (không có yêu cầu cụ thể mới, tiếp tục theo
đúng thứ tự backlog đã ghi).

### Thêm

- **Vân tay thông số.** Băm 8 cột quan trọng (`cap_dien_ap`, `dong_dinh_muc`,
  `dong_ngan_mach`, `ro_le`, `so_ngan`, `loai_ngan`, `cach_dien`, `mo_rong`).
  Hai SKU trùng cả 8 cột thì cảnh báo trong sheet Sản phẩm, cột "Trùng vân tay
  thông số", tô vàng. Chỉ cảnh báo, không chặn sinh bài. Test trên dữ liệu
  thật: 36/98 SKU dính — đúng khớp con số đã đo tay từ trước.
- **Trùng văn biên tập.** So phần AI viết (không so bảng thông số/cấu hình —
  phần đó được phép giống nhau) của bài mới với các bài đã sinh trước đó CÙNG
  SITE, dùng `difflib.SequenceMatcher`. Giống từ 75% trở lên thì đánh dấu
  "Cảnh báo" ở cột Kiểm tra và ghi rõ SKU nào giống, không chặn đăng.
- Thêm cột `van_bien_tap` vào bảng bài viết để lưu văn bản AI viết, dùng làm
  nguồn so sánh cho các bài sinh sau. Tự thêm cột khi mở DB cũ, không mất
  lịch sử.

### Test

- 2 kịch bản giả lập AI: văn giống hệt → đúng bị gắn "Cảnh báo" kèm tên SKU
  giống; văn khác nội dung thật → không báo trùng oan (một lần thử đầu bị báo
  nhầm vì bản thân câu test chỉ khác đúng 1 từ, không phải lỗi code — viết lại
  câu test khác hẳn nội dung thì đúng).
- Vân tay thông số: khớp đúng 36/98 SKU đã đo trước đó.
- Migrate DB V2 gốc (98 sản phẩm, 6 bài cũ) lên schema có `van_bien_tap`,
  không mất dữ liệu.
- Nghiệm thu 20 bài vẫn 5/5, GUI 6 tab không crash.

---

## Claude v2.6 — 24/07/2026

6 việc theo đúng yêu cầu, không đụng kiến trúc, không thêm gì ngoài danh sách.

### Thêm/sửa

| # | Việc | Chi tiết |
|---|---|---|
| 1 | Sản phẩm trùng giữ record riêng, không tự gộp | Trước đây mã trùng (theo `khoa_trung`) bị bỏ, chỉ giữ bản gặp đầu tiên. Giờ giữ cả hai, `sku` bản trùng thêm hậu tố tên sheet để không đè lên nhau, `slug` tự đánh số khác nhau (cơ chế đã có sẵn). `ma_goc` giữ nguyên không đổi để khớp ảnh và hiện đúng trong bảng. Test trên đúng file mẫu có 13 mã trùng thật: 13/13 giờ ra 2 record riêng, không mã nào đè mã nào |
| 2 | UI chỉnh cấu hình WordPress từng site + thêm site mới | Tab Cấu hình có nút "+ Site mới" (hộp thoại nhập mã/tên/hotline) và "Xoá site này". Site thêm qua UI lưu vào `sites-them.json`, không đụng `cauhinh.py`. Site mẫu (site1/site2) không xoá được, chỉ site tự thêm mới xoá được. Test: thêm/xoá qua `cauhinh.py` API và qua UI đều đúng |
| 3 | Chọn sản phẩm | Không đổi — giữ nguyên cơ chế tick chọn/bỏ ở tab Sản phẩm |
| 4 | Màn hình chạy thử 1 bài | Tab mới "4. Thử 1 bài": chọn site + sản phẩm + outline, nút "Xem prompt" (miễn phí, không gọi AI, in thẳng system+user prompt thật) và "Chạy thật 1 bài" (gọi AI thật, in ra: dữ liệu giữ nguyên từ Excel, phần AI viết, số từ/ảnh, cấu trúc HTML, đường dẫn file kết quả) |
| 5 | Dashboard/Excel theo dõi | Không cần sửa thêm — đã đúng từ v2.4/v2.5 (tổng bài, đã đăng, URL, trạng thái, lỗi). Test lại trên luồng 20 bài với dữ liệu có mã trùng thật, số liệu khớp |
| 6 | Slug -2 chỉ cảnh báo | Không hạ cấp xử lý đã có (v2.5 vẫn kiểm tra `wp_id` trước, hỏi lại slug khi mất kết nối) — mức đó đã cao hơn yêu cầu "chỉ cần cảnh báo", giữ nguyên, không tốn thêm việc |

### Tạm dừng theo yêu cầu

- Dò model nâng cao (không sửa thêm `do_model()`/hiển thị dung lượng).
- Đóng gói Python portable (không sửa thêm `CAI-DAT-LAN-DAU.bat`).

### Test

- Nghiệm thu 20 bài (`kiemthu.py --so 20`) trên đúng file mẫu có mã trùng thật:
  5/5, 111 sản phẩm (98 gốc + 13 giữ riêng), dashboard/Excel khớp số.
- Test riêng: giữ record trùng (13/13 đúng), thêm/xoá site qua API và UI,
  `sinh_mot_bai()` với AI giả lập chạy đúng qua đường ống màn hình thử 1 bài.
- GUI dựng đủ 6 tab trên màn hình ảo, không crash.

---

## Claude v2.5 — 24/07/2026

Đóng nốt mục cuối trong "MAIN v0.1" theo đúng scope đã chốt (xem `SPEC.md`).

### Sửa

- **`thinkingConfig` giờ vào đúng request sinh bài thật.** Đây là gốc lỗi cắt
  JSON giữa chừng ngày 24/07 (`gemini-3.5-flash`). Model có "suy nghĩ ngầm"
  (tra qua field `thinking` thật của API, không đoán theo tên) thì tự bù ngân
  sách token lên 24.576 và thêm `thinkingLevel: low`. Model từ chối tham số
  này thì tự bỏ đi thử lại, không phải sửa tay `prompts.py`.
- Tra dung lượng model chỉ 1 lần mỗi phiên chạy (nhớ lại trong bộ nhớ), không
  gọi thêm API mỗi bài.

### Tài liệu mới

- `SPEC.md` — scope đã đóng băng cho MAIN v0.1, tiêu chí nghiệm thu, khuôn báo
  lỗi cho vòng sau.
- `KNOWN-ISSUES.md` — backlog đầy đủ, gồm nguyên văn kiến trúc hệ thống profile
  ngành hàng đã bàn (chưa xây, giữ lại để không quên hướng đi).
- `TEST-REPORT.md` — test gì, bằng cách nào, còn thiếu gì cần Thịnh tự chạy.
- `TIEN-DO.md` — file theo dõi tiến độ tổng thể, cập nhật mỗi vòng, dùng thay
  cho việc dán lại lịch sử chat.

### Test

3 kịch bản giả lập HTTP cho từng nhánh (model có thinking / không thinking /
model từ chối tham số), cả 3 đúng như thiết kế. Nghiệm thu 30 bài vẫn 5/5.

---

## Claude v2.4 — 24/07/2026

Bản vá lõi sau khi mày đưa GPT review + hai ảnh chụp lỗi thật. Ưu tiên đúng thứ tự:
lỗi mày tự tay gặp trước, rồi tới từng P0 GPT nêu — kiểm tra bằng code và dữ liệu
thật trước khi tin, không chép nguyên bảng chấm điểm của nó.

### Lỗi mày tự gặp — sửa trước tiên

| | |
|---|---|
| Không bấm được "Lưu cấu hình" | PanedWindow hôm qua bóp khung tab xuống dưới nội dung cần hiện, nút bị đẩy khuất mà không cuộn tới được. Bọc 3 tab dễ tràn (Nhập Excel, Cấu hình, Chạy) trong khung cuộn, khung tab không bao giờ nhỏ hơn 420px |
| `CAI-DAT-LAN-DAU.bat` lỗi ở bước tkinter | Bản trước tao đoán mù cấu trúc thư mục bên trong gói NuGet, đoán sai. Viết lại: lấy tcl/tkinter từ chính bản Python đã cài trên máy đó (nếu có) thay vì tải một gói chưa kiểm chứng được cấu trúc |

### P0 GPT nêu — đối chiếu bằng code và dữ liệu thật

| # | GPT nói | Kiểm tra | Xử lý |
|---|---|---|---|
| 1 | GUI không lọc sản phẩm theo site | Đúng — `viec_sinh_bai()` và `viec_kiem_tra_wp()` gọi `doc_san_pham()` không truyền `ma_site` | Sửa, giờ site chỉ thấy đúng ngành hàng nó khai báo |
| 2 | 10 mã SM6 bị gắn nhãn RM6 | Đúng, và nặng hơn GPT nói — kiểm tra thẳng trên file mẫu: 10 dòng đó **nằm y hệt ở cả hai sheet trong file gốc** (sếp dán trùng), code cũ cứ sheet nào quét trước thắng | Đọc theo chữ trong mã (SM6/RM6) thay vì theo thứ tự sheet. Test lại trên đúng file mẫu: 10/10 đúng. Dọn luôn tên bị lặp chữ ("SM6 SM6 DM1-A" → "SM6 DM1-A") |
| 3 | SKU làm khoá toàn cục, hai ngành trùng SKU thì đè nhau | Đúng, tái hiện được | Đổi khoá chính thành `(danh_muc, sku)`. Migrate DB cũ tự động, test trên cả DB giả lẫn DB V2 thật (98 sản phẩm, 6 bài cũ) không mất gì |
| 4 | Bài lỗi không vào dashboard, chỉ vào log.csv | Đúng | Thêm `ghi_bai_loi()` dùng chung cho CLI/GUI/nghiệm thu, ghi cả vào SQLite. Test: dashboard giờ hiện đúng "Lỗi" |
| 5 | WordPress có thể đẻ bài `-2` khi mạng chập chờn | Đúng, và cách sửa GPT gợi ý cũng đúng | Viết lại `dang_wp()`: tin `wp_id` đã lưu trước (không phụ thuộc mạng lúc đăng), hỏi slug lỗi thì DỪNG thay vì đoán "chưa có bài", mất kết nối giữa POST thì hỏi lại slug trước khi thử tiếp — không bao giờ POST mù hai lần. Test bằng 3 kịch bản giả lập, cả 3 đúng |
| — | Model "thinking" không có trong schema chính thức | **Sai** — trang schema chính thức của Google (`ai.google.dev/api/models`) liệt kê rõ `thinking boolean · Whether the model supports thinking`. Có thể GPT dùng dữ liệu huấn luyện cũ | Giữ nguyên, không sửa theo góp ý này |
| — | Chọn sản phẩm chạy được nhưng dashboard/Excel không thấy | Đúng | Thêm cột "Chọn viết" vào sheet Sản phẩm và Bài viết, thêm cột "Đang chọn viết/Đã bỏ chọn" vào sheet Tổng quan, thêm thẻ KPI "SKU đang chọn viết" ngay trong app |
| — | `PHAN-MEM.bat` vẫn ghi tiêu đề v2.2 | Đúng | Sửa, đồng bộ v2.4 ở mọi nơi |

### Sửa thêm, không nằm trong danh sách GPT

- `MODEL_GEMINI` mặc định vẫn là `gemini-2.5-flash` — model này đã chết (log thật của mày báo 404 "no longer available to new users"). Đổi mặc định sang `gemini-3.5-flash`, đúng model do "Dò model" chọn ra trong log của mày.

### Vẫn còn — GPT nói đúng, chưa đủ sức làm trong đợt này

Ưu tiên cho đợt tới, đúng thứ tự:

1. **`thinkingConfig` chưa vào request sinh bài thật.** Đây là gốc lỗi cắt JSON hôm 24/07. Cột "suy nghĩ ngầm" ở tab Cấu hình mới là hiển thị, chưa nối vào lệnh gọi Gemini thật. Việc số 1 của đợt tới.
2. Vân tay thông số + trùng văn biên tập (đã đo trên dữ liệu thật ở phiên trước: 36/98 SKU đang trùng vân tay do cột trống, không phải sản phẩm giống nhau thật).
3. `du_lieu_bat_buoc` cho từng outline.
4. HTML từ AI chưa được lọc thẻ an toàn (sanitize), câu trả lời FAQ chưa escape — rủi ro AI lỡ chèn thẻ script/lạ vào bài.
5. Cache `kho_toan_bo` không tự làm mới khi sửa `products.csv` bằng tay rồi nhập lại — dễ đăng bài với danh sách trắng chống bịa số đã cũ.
6. Ảnh: khớp tên file theo mã đầy đủ (không chỉ mã rút gọn), resize, WebP, featured image, alt/caption.
7. Liên kết nội bộ: thiếu hậu tố outline trong URL, có thể trỏ tới bài chưa đăng.
8. Gán chuyên mục và thẻ khi đăng WordPress.
9. Bộ nghiệm thu 30 bài chưa test được tắt/mở lại process thật (mô phỏng bằng đọc lại kho, không phải kill process).

---

## Claude v2.3 — 24/07/2026

Tham khảo bản GPT làm để đối chiếu, lấy đúng phần đáng lấy, bỏ phần trùng hoặc yếu hơn.

### Thêm

| | Việc |
|---|---|
| Chọn sản phẩm cần viết | Tab 3 có cột "Viết", bấm đúp bật/tắt riêng từng dòng, có nút chọn/bỏ hàng loạt theo dòng đang lọc trên bảng. Sản phẩm tắt chọn không vào hàng đợi sinh bài, nhưng vẫn có mặt trong bảng giá và liên kết nội bộ của các bài khác — tách hai việc ra, không thì bảng giá hụt |
| Dung lượng model thật | Bấm "Dò model" ở tab 2 giờ hiện luôn input/output token limit và model có "suy nghĩ ngầm" (thinking) hay không, lấy trực tiếp từ API Google chứ không đoán theo tên. Bản GPT tham khảo không có mục này |
| Nhật ký to hơn | Chuyển sang khung kéo được (PanedWindow), mặc định nhật ký chiếm ~34% chiều cao cửa sổ, kéo tay chỉnh thêm được |
| Xem trước bài | Tab 0 Tổng quan có khung xem trước kiểu kết quả tìm kiếm Google: tiêu đề, mô tả, đường dẫn, nút mở file HTML hoặc mở link đã đăng |
| Lưu meta_title/meta_description | Trước đây hai trường này chỉ nằm trong file HTML, không lưu vào kho dữ liệu nên dashboard không hiện được. Giờ lưu kèm mỗi bài |

### Đối chiếu với bản GPT, quyết định không lấy

- **Điều khiển Gemini/ChatGPT qua trình duyệt (Chrome CDP)** — không có trong bản GPT tham khảo lần này, nhưng nếu thấy thì vẫn không lấy: dễ gãy khi web đổi giao diện, có nguy cơ vi phạm điều khoản dịch vụ, không hợp với nhịp 20-30 bài/ngày.
- **Preview mở file cục bộ (`webbrowser.open` vào file HTML)** — bản GPT làm vậy. Bản này làm khung xem trước ngay trong ứng dụng, khỏi mở thêm cửa sổ trình duyệt.

### Chưa làm, mẻ sau

- Lỗi cắt bài do model mới bật "suy nghĩ ngầm" ăn vào ngân sách token (xem log nghiệm thu ngày 24/07). Đã xác định nguyên nhân, tạm hoãn theo yêu cầu để làm mục ở trên trước.
- Vân tay thông số, trùng văn biên tập.
- `du_lieu_bat_buoc` cho từng outline.
- Ảnh: resize, WebP, featured image, alt/caption.
- Đặt chuyên mục và thẻ khi đăng WordPress.

---

## Claude v2.2 — 24/07/2026

Bản này thay cho gói tao đặt nhầm tên "V3" hôm qua. Từ giờ đánh số theo v2.x cho khớp
cách gọi của mày.

### Thêm

| | Việc |
|---|---|
| Tab 0 Tổng quan | Máy trạng thái từng chặng. 5 ô số to, lọc theo site và trạng thái, ô tìm kiếm, bấm đúp mở file HTML của bài |
| `baocao.py` | Xuất `bang-dieu-khien.xlsx` 3 sheet: Tổng quan (gửi sếp), Sản phẩm (đưa người điền dữ liệu), Bài viết (theo dõi từng bài). Có tô màu và bộ lọc sẵn |
| `kiemthu.py` | Bộ nghiệm thu tự chấm 5 mốc, trượt mốc nào in luôn nguyên nhân. Chạy bằng `KIEM-THU-30-BAI.bat` |
| Ngành hàng (`danh_muc`) | Ngăn kho theo ngành. Nạp file cáp điện đè lên tủ trung thế không còn trộn số liệu vào nhau |
| `CAI-DAT-LAN-DAU.bat` | Tải Python riêng vào thư mục `python\`, cài sẵn thư viện. Chạy một lần, sau đó không cần Python máy, không cần mạng |
| Theo dõi từng chặng | Mỗi bài lưu thêm: dữ liệu đầy bao nhiêu, mấy ảnh, bao nhiêu từ, kết quả kiểm tra, trạng thái WordPress |

### Sửa

- **Kho sản phẩm không ngăn theo ngành.** Trước đây `kho_toan_bo()` gộp số liệu mọi
  ngành làm danh sách trắng chống bịa số. Nạp thêm danh mục thứ hai là bộ chặn yếu đi
  ngay. Giờ lọc theo `danh_muc` khai báo ở từng site.
- `doc_san_pham()` đã lọc theo ngành mà rỗng thì trả rỗng, không âm thầm lùi về
  `products.csv` dùng chung.
- Nâng cấp DB tự động, giữ nguyên lịch sử: V2 (thiếu cột `site`) và v2.1 (thiếu các
  cột chặng) đều lên thẳng schema mới.
- `COT_QUAN_TRONG` trước khai ở hai file, lệch nhau lúc nào không biết. Gom về
  `cauhinh.py`.

### Chưa làm, mẻ sau

- Vân tay thông số: hai SKU trùng cả 8 cột thì cảnh báo. Hiện đo được **36/98 SKU**
  đang dính, nguyên nhân là cột trống chứ không phải sản phẩm giống nhau.
- Trùng văn biên tập: chỉ so phần AI viết, không so bảng thông số. Phần văn đã nằm
  tách sẵn trong biến `van_xuoi`, khoảng 30 dòng là xong.
- `du_lieu_bat_buoc` cho từng outline: outline báo giá mà trống giá thì đừng sinh.
- Ảnh: resize, WebP, featured image, alt/caption.
- Đặt chuyên mục và thẻ khi đăng WordPress.

---

## Claude v2.1 — 23/07/2026

(gói này tao đặt tên nhầm là "V3")

### Sửa 4 tính năng chết im lặng trong V2

- **Kho kiến thức chưa bao giờ chạy.** Thư mục `kienthuc/` không tồn tại, 4 file JSON
  nằm ở thư mục gốc, hàm nạp luôn trả rỗng. Giờ tự dọn file vào đúng chỗ.
- **Bảng giá chưa bao giờ hiện.** Gom theo cột `dong_may` — cột này không có trong dữ
  liệu. Mọi bài đều rơi xuống câu "gọi để nhận báo giá". Giờ gom theo `series` +
  `cap_dien_ap`, xếp theo số ngăn.
- **Chặn oan do dấu phẩy.** Bộ so số xoá dấu phẩy trước khi so, nên `0,4kV` trong dữ
  liệu không khớp `0.4kV` do AI viết. Giờ đổi dấu phẩy thập phân thành dấu chấm.
- **Ảnh ghép vào bài dạng `file:///C:/...`**, đăng lên là vỡ hết. Giờ tải lên thư viện
  WordPress, có nhớ để không tải trùng.

### Khác

- Một đường sinh bài duy nhất (`sinh_mot_bai`). Trước đây giao diện và dòng lệnh chạy
  hai đường khác nhau, đã lệch nhau.
- Chạy được nhiều site, khai trong `cauhinh.py`. Từ cấm gom về một chỗ.
- Con số trong kho kiến thức đã kiểm chứng được đưa vào danh sách trắng, không thì
  bật kiến thức lên là bài bị chặn oan.
- 8 file `.bat` gom còn 1.

---

## V2 — 23/07/2026 (bản gốc của Thịnh)

Nhập Excel nhiều sheet, gộp mã trùng, tách thông số bằng regex, kho kiến thức có cờ
`da_kiem_chung`, liên kết nội bộ 13-20 link, lưu trạng thái SQLite, đăng lại thì cập
nhật thay vì đẻ bài mới.

---

## Ver 5.5 — 20/08/2026 — MODULE SEO POST

### Thêm mới
- `prompts_seo_post.py` — 8 content type khoá cứng (bao_gia, complete_guide,
  top_list, so_sanh, huong_dan_chon, tieu_chuan, catalogue, du_an). Bộ luật
  chống bịa RIÊNG cho bài post: QUY_TAC_CO_SKU (S1-S5) khi có SKU,
  QUY_TAC_KHONG_SKU (K1-K6) khi không. Không dùng lại QUY_TAC_CHUNG của
  prompts_phase2 vì bộ đó giả định luôn có 1 record để bám.
- `db_seo_post.py` — 2 bảng `bai_seo` + `bai_seo_sku`. KHÔNG FK tới
  san_pham_phase2, nên bài chủ đề không cần SKU nào vẫn ghi được.
- `seo_post_core.py` — nạp từ khoá (gõ tay / dán list / import GSC), gộp N
  SKU thành dải, sinh, render, đăng post HOẶC product.
- `tab_seo_post.py` — Tab 11 giao diện.
- `ke_hoach_content.py` — script độc lập, đọc thư mục file GSC export ra
  kế hoạch content .xlsx (4 sheet: KE-HOACH / SUA-BAI-CU / TRUNG-LAP / TONG-QUAN).
- `tests/test_seo_post_prompts.py` — 11 test. Vá nợ "Ver 5.4 không có test".

### Trả nợ cũ
- `du_lieu_bat_buoc`: doc 4.x ghi món này nhiều đợt nhưng grep source = 0
  kết quả. Ở module post nó CÓ THẬT: `kiem_tra_du_dieu_kien()` chặn trước
  khi gọi API, type bao_gia thiếu SKU là raise ValueError.
- PHIEN_BAN: 4.6.2 -> 5.5 (bản 5.4 đã vá lệch, bản này tiếp tục đúng).

### Quyết định thiết kế cần biết
- Bài báo giá MẶC ĐỊNH không nêu số tiền (`che_do_gia='AN'`). Lý do:
  `gia_list` nằm trong FIELD_CAM_TUYET_DOI, Lotech không công khai giá.
  Bài bán CẤU TRÚC giá (yếu tố làm giá đổi, cách đọc báo giá) chứ không
  bán con số. Có công tắc 'CONG_KHAI' khi nào có cột giá được phép hiện.
- Đăng `post` là mặc định, `product` chọn được từng bài. Đăng product với
  nhiều SKU gộp sẽ đẻ lỗi schema Rank Math (thiếu `offers`) — tool CẢNH BÁO
  chứ không chặn, vì đó là quyết định nghiệp vụ đã chốt.
- `dang_bai()` KHÔNG mượn `ai_wp_adapter.dang_wp_that()`: hàm đó tra bảng
  `bai_viet` theo (dataset_id, record_id) của luồng sản phẩm. Đường đăng
  riêng, idempotent bằng chính `bai_seo.wp_id`.

### Chưa làm
- Liên kết nội bộ tự động giữa bài post và trang sản phẩm.
- Vòng phản hồi GSC -> đo bài đã đăng sau 28 ngày.
- Chưa có test cho seo_post_core (mới có cho prompts).

### Ver 5.5b — 20/08/2026 — ẢNH: watermark mới + dọn ảnh hàng loạt

**Watermark — `xu_ly_anh.py`**
- Thêm `WATERMARK_STYLE`: `ket_hop` (mặc định) | `goc` (hành vi v2, giữ lại
  để quay về) | `cheo` | `thanh`.
- `ket_hop` = lặp chéo 30 độ alpha 52 (chống crop) + thanh chân trang
  (đọc được ở thumbnail 200px). Đây là "mức B" đã chốt sau khi so 4 mức.
- Cả hai lớp TỰ ĐẢO MÀU theo độ sáng nền (`_do_sang_trung_binh`).
  Lý do: bản v2 dùng chữ trắng alpha 82 trên hộp đen alpha 51 — trên ảnh
  catalogue nền trắng gần như vô hình, mà đó là nhóm ảnh đông nhất trong kho.
  Đo trực tiếp: ở 200px bản v2 không đọc ra số nào.
- `_chu_co_vien()` cho phép bỏ hộp nền đè lên ảnh.
- Signature bump v2 -> v3, có `kieu` + `cheo_alpha`, nên đổi kiểu là ảnh
  upload lại đúng một lần rồi tiếp tục idempotent.
- Chi phí: ~24 KB (v2 ~4 KB) trên ảnh mẫu. Vẫn dưới ngân sách 150 KB.

**Đã cân nhắc và BÁC BỎ: kiểu chữ to đè ngang thân sản phẩm.**
Lý do: (1) không chặn được ai — Generative Fill xoá trong 10 giây;
(2) ảnh máy biến áp không khan hiếm, đối thủ lấy từ catalogue nhà sản xuất;
(3) Google nói watermark không ảnh hưởng thứ hạng ảnh, nhưng làm giảm chất
lượng cảm nhận thì người dùng bấm ít hơn; (4) Merchant Center cấm hẳn
watermark nếu sau này muốn free listing.

**Dọn ảnh — `don_anh.py` (mới) + nút "Dọn ảnh…" ở tab Ảnh**
Ba mức theo độ không hồi lại được:
1. `go_anh_khoi_bai()` — gỡ khỏi sản phẩm/bài, file vẫn còn. Hồi được.
2. `xoa_media(force=False)` — vào thùng rác WP, hồi được ~30 ngày.
3. `xoa_media(force=True)` — vĩnh viễn, đòi `xac_nhan='XOA VINH VIEN'`.
`xoa_anh_local()` mặc định chuyển vào `_da_xoa/` thay vì xoá thật.
`tim_anh_mo_coi()` tìm media không gắn bài nào — nhóm an toàn nhất để dọn.

Chốt chặn: mọi hàm mặc định `chay_thu=True`; `bo_qua_dang_dung=True` tự bỏ
qua media đang gắn vào bài; ghi log JSON TRƯỚC khi gọi API xoá.

**Test:** `tests/test_v55_anh.py` — 15 test, gồm test đo % pixel thay đổi
trên nền trắng (chống lặp lại lỗi watermark vô hình) và test các chốt chặn
an toàn của dọn ảnh.
