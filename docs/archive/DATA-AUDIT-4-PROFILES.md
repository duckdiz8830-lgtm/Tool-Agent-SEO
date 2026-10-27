# DATA AUDIT — 4 Profile Sản Phẩm (5.264 record)

**Bản sửa sau review: đã sửa lại mục 6.1 (con số 70 → 185, sai ở bản trước).
Xem "Đính chính" ngay dưới đây trước khi đọc tiếp.**

Đã tự đọc bằng pandas/openpyxl, không dùng số mày cho sẵn. Mức tin cậy: **cao**
cho mọi số ở dưới (đếm trực tiếp trên dữ liệu thật, không suy diễn).

## 0. Đính chính so với bản trước

Bản trước ghi "70 dòng phụ kiện lẫn trong cap_dien" — **sai**. Nguyên nhân: khi
đếm bằng `value_counts()`, mặc định `dropna=True` nên 89 dòng có
`Ghi Chú Ban Đầu` **trống hẳn (NaN)** bị rớt khỏi phép đếm, cộng thêm lỗi cộng
tay khi liệt kê danh sách. Số đúng, đã kiểm lại 2 lần bằng 2 cách tính khác
nhau (dùng `!=` trực tiếp và dùng `.fillna()` trước khi so sánh, ra cùng kết
quả): **185 dòng**, đúng bằng `3.387 − 3.202 = 185`. Chi tiết và tiêu chí đếm
ở mục 6.1.

## 1. Tổng quan số lượng

| Profile | File con | Sheet trong MASTER | Số dòng | Khớp MASTER |
|---|---|---|---|---|
| cap_dien | 01_Cap_Dien.xlsx | 01_Cap_Dien | 3.387 | Đúng, `.equals()` = True |
| tu_va_thiet_bi_dong_cat | 02_Tu_Va_Thiet_Bi_Dong_Cat.xlsx | 02_Tu_Va_Thiet_Bi_Dong_Cat | 300 | Đúng |
| may_bien_ap_do_luong | 03_May_Bien_Ap_Do_Luong.xlsx | 03_May_Bien_Ap_Do_Luong | 245 | Đúng |
| phu_kien_va_khac | 04_Phu_Kien_Va_Khac.xlsx | 04_Phu_Kien_Va_Khac | 1.332 | Đúng |
| **Tổng** | | | **5.264** | Khớp con số mày đưa |

Mỗi file con so từng ô với sheet tương ứng trong MASTER (fillna rồi `.equals()`)
— khớp tuyệt đối cả 4. File MASTER dùng được làm nguồn nhập duy nhất, không
cần đọc riêng 4 file con.

## 2. Cấu trúc cột — QUAN TRỌNG, khác hẳn importer hiện tại

Cả 4 sheet đều **có header thật** (tên cột ở dòng 1), không phải dạng
"STT / mã / cấu hình" như file tủ RMU cũ. `dulieu.py::nhap_excel()` hiện đọc
theo **vị trí cột cố định** (`r[0]`=STT, `r[1]`=mã, `r[2]`=cấu hình, bỏ dòng
nếu `r[0]` không phải số) — logic này **không dùng được** cho bộ dữ liệu mới,
phải đọc theo tên cột.

8 cột chung cho mọi profile:
`Mã hàng, Tên hàng, Nhãn Hiệu / Xuất Xứ, Quy Cách / Áp Lực, ĐVT, Giá List (VNĐ), Ghi Chú Ban Đầu, Nhóm Nguồn`

Cột riêng thêm:

| Profile | Cột thêm |
|---|---|
| cap_dien | `Tiết Diện (mm²)`, `Cấp Điện Áp`, `Vật Liệu Ruột` |
| may_bien_ap_do_luong | `Công Suất (kVA)`, `Cấp Điện Áp (kV)` |
| tu_va_thiet_bi_dong_cat | không có |
| phu_kien_va_khac | không có |

## 3. Tỷ lệ trống theo cột (%)

| Cột | cap_dien | tu_dong_cat | may_bien_ap | phu_kien |
|---|---|---|---|---|
| Mã hàng / Tên hàng / ĐVT / Nhóm Nguồn | 0% | 0% | 0% | 0% |
| Quy Cách / Áp Lực | 96.8% | 73.7% | 41.2% | 56.7% |
| Giá List (VNĐ) | 23.1% | 50.0% | 9.8% | 32.2% |
| Ghi Chú Ban Đầu | 2.6% | 19.7% | 68.2% | 22.7% |
| Tiết Diện (mm²) | 31.5% | — | — | — |
| Cấp Điện Áp | 35.2% | — | — | — |
| Vật Liệu Ruột | **97.3%** | — | — | — |
| Công Suất (kVA) | — | — | 32.7% | — |
| Cấp Điện Áp (kV) | — | — | 29.0% | — |

`Quy Cách / Áp Lực` trống gần hết mọi profile — đừng thiết kế outline dựa vào
cột này. `Vật Liệu Ruột` trống 97.3% ở cap_dien — chỉ 93/3.387 dòng có giá
trị, coi như cột phụ, không phải cột chính.

## 4. SKU trùng — đúng 17 như mày báo

| Profile | Số SKU trùng | Dòng liên quan |
|---|---|---|
| cap_dien | 12 | 24 |
| tu_va_thiet_bi_dong_cat | 1 | 2 |
| may_bien_ap_do_luong | 0 | 0 |
| phu_kien_va_khac | 4 | 8 |
| **Tổng** | **17** | **34** |

Không có SKU trùng **chéo** giữa 2 profile khác nhau (đã kiểm, 0 trường hợp)
— nghĩa là khoá `(profile_id, sku)` đã đủ để tách theo profile, nhưng **vẫn
không đủ** để tách các bản ghi trùng SKU trong cùng profile (12+1+4 = 17 cặp
này vẫn đè nhau nếu chỉ khoá theo `(profile_id, sku)`), đúng như mày cảnh báo.
Ví dụ: `TTTCVV250` xuất hiện 2 lần trong cap_dien — 1 lần là cáp đơn 3 lõi
(`CVV250mm2 - 0.6/1KV (cs)`), 1 lần là cáp 2 lõi 50mm² (`CVV 2x50mm2 (sc)`) —
hai sản phẩm khác nhau thật, không phải lỗi nhập liệu, phải giữ cả hai.

## 5. Lỗi regex đã xác nhận

### 5.1. `Cấp Điện Áp (kV)` lấy nhầm số kVA — xác nhận đúng như mày mô tả

- **165/245 dòng** của toàn file `03_May_Bien_Ap_Do_Luong.xlsx` có
  `Cấp Điện Áp (kV) == Công Suất (kVA)` về mặt số — chắc chắn là bug copy nhầm
  cột, không phải trùng hợp.
- Khoanh vùng chính xác hơn: bug nằm **100% trong Nhóm Nguồn "05. Máy Biến
  Áp"** — 165/172 dòng của nhóm này bị (7 dòng còn lại của nhóm 05 có vẻ thoát
  bug, cần soát tay).
- Nhóm **"08. Đo Lường & Biến Dòng" (73 dòng) không bị bug này** — cột
  `Cấp Điện Áp (kV)` của nhóm 08 lấy đúng từ chuỗi "24kV" viết thẳng trong tên
  (VD: "Hợp bộ đo lường (MOF) 24kV..."), cột `Công Suất (kVA)` của nhóm 08
  hầu như trống (không có kVA trong tên loại này) — không lẫn lộn.
- Kết luận: sửa regex chỉ cần áp cho nhóm 05, có thể chừa nhóm 08.

### 5.2. cap_dien — điện áp không bóc được

- 1.192/3.387 dòng `Cấp Điện Áp` trống. Trong đó:
  - 291 dòng tên hàng **có** pattern kiểu "300/500V" hoặc số+V nhưng cột vẫn
    trống → regex hiện tại chỉ nhận dạng `kV`, không nhận `V` thường (300/500V,
    600V, 450/750V). Đây là lỗi bóc tách thật, sửa được.
  - 901 dòng còn lại tên hàng **không có bất kỳ pattern điện áp nào** (VD dây
    nhôm trần "ACKP16/2.7mm2 - TCVN5064") → không phải lỗi, đơn giản là dữ
    liệu nguồn không ghi điện áp, phải để trống, không suy đoán.

### 5.3. cap_dien — tiết diện không bóc được

- 1.068/3.387 dòng `Tiết Diện (mm²)` trống. Trong đó **867 dòng tên hàng có
  chữ "mm2" nhưng cột vẫn trống**. Nguyên nhân xác định được: regex hiện tại
  chỉ bắt được dạng nhiều lõi `NxM` (VD "2x1.5mm2" → đã bóc đúng thành
  "2x1.5"), còn dạng **đơn lõi không có "x"** (VD "VC2.5mm2", "CXV2X38mm2" viết
  hoa X) bị bỏ sót hoàn toàn.
  - Ví dụ đã bóc đúng: `Dây VCmd2x0.5mm2` → `2x0.5` (2.319 dòng dạng này OK).
  - Ví dụ bỏ sót: `Dây VC2.5mm2 (450/750V)` → trống (phải là `2.5`),
    `Dây CXV2X38mm2` → cũng dạng NxM nhưng chữ X hoa, cột `Tiết Diện` **có**
    giá trị "2X38" (đã bắt được, không phân biệt hoa/thường) — vậy lỗi cụ thể
    là **thiếu case đơn lõi không "x"**, không phải lỗi hoa/thường.

### 5.4. cap_dien — Vật Liệu Ruột: Cu-Al bị gán nhầm "Đồng (Cu)" — xác nhận

- Cột `Vật Liệu Ruột` chỉ có 2 giá trị: "Đồng (Cu)" (79 dòng), "Nhôm (Al)" (14
  dòng).
- 48 dòng tên hàng chứa "Cu-Al" (cosse ép lưỡng kim nối đồng-nhôm, KHÔNG phải
  dây cáp có ruột dẫn) đều bị gán "Đồng (Cu)" — đúng bug mày mô tả. Đây thực
  ra là phụ kiện (cosse), không phải cáp, nằm lẫn trong file cap_dien (xem mục
  6.1 bên dưới) — sửa đúng phải tách nhóm này ra khỏi field "Vật Liệu Ruột"
  luôn, không chỉ sửa tên vật liệu.

### 5.5. Chưa được cảnh báo trước nhưng phát hiện thêm

- 2 dòng tên hàng bị lặp brand 2 lần ("... - Cadivi - Cadivi") — lỗi nhập liệu
  nhỏ, không đáng kể, có thể bỏ qua hoặc regex strip trùng cuối chuỗi.
- Cột `ĐVT` không chuẩn hoá khoảng trắng: `"Bộ"` và `"Bộ "` (có space cuối),
  `"Cái"` và `" Cái"` (space đầu) được pandas coi là 2 giá trị khác nhau —
  tu_dong_cat có 3 biến thể cho "Bộ", phu_kien có tới 6+ biến thể tương tự.
  Cần `.strip()` khi nhập, không thì filter/group theo ĐVT sẽ sai.

## 6. Rủi ro theo từng profile

### 6.1. cap_dien (3.387 dòng, lớn nhất — rủi ro cao nhất)

**Tiêu chí đếm (đã chốt lại):** "không phải cáp thật" = mọi dòng có
`Ghi Chú Ban Đầu` **khác chuỗi `"Cáp điện"`**, kể cả khi ô đó **trống hẳn
(NaN)**. Bản trước chỉ đếm các dòng có ghi chú khác nhưng KHÔNG rỗng (dùng
`value_counts()` mặc định bỏ NaN), nên thiếu mất 89 dòng và ra số sai (70,
thực ra cộng tay cũng sai so với chính danh sách đã liệt kê). Đếm lại bằng 2
cách độc lập (so sánh `!=` trực tiếp, và `.fillna("__TRONG__")` trước khi so
sánh) cho cùng 1 kết quả:

**185 dòng = 3.387 − 3.202**, đúng bằng số dòng "Cáp điện" thật trừ tổng dòng.

Chia làm 2 nhóm:

**(a) 96 dòng có Ghi Chú Ban Đầu khác "Cáp điện", có điền chữ** — 14 nhãn:

| Ghi chú | Số dòng | Ghi chú | Số dòng |
|---|---|---|---|
| Dây chì | 22 | Kẹp ngừng | 3 |
| Giáp níu | 16 | Kẹp quai | 3 |
| Ống nối đồng | 14 | Mốc bê tông | 2 |
| Recloser | 10 | Dây đai | 2 |
| LBS | 8 | băng cảnh báo | 1 |
| Khóa néo | 6 | Mốc gang | 1 |
| Cọc tiếp địa | 5 | cáp từ 35-300mm2 | 3 |

Đã soát tay nhãn "cáp từ 35-300mm2" (3 dòng, nhãn dễ gây hiểu lầm là cáp) —
thực tế là chống sét van (VD `LA 18kV, 10kA... Raychem/EU`), không phải dây
cáp, ghi chú nguồn đặt sai tên. Xếp đúng vào nhóm phụ kiện.

**(b) 89 dòng Ghi Chú Ban Đầu trống hoàn toàn (NaN)** — đã soát tay từng dòng
bằng `Tên hàng`, không phải cáp:

| Loại | Số dòng |
|---|---|
| Cosse ép Cu-Al | 48 (= toàn bộ 48 dòng bug mục 5.4, không có dòng Cu-Al nào nằm ngoài nhóm 185 này) |
| Ốc xiết cáp | 7 |
| Mốc sứ cảnh báo | 6 |
| Đầu nối / Hộp nối cáp ngầm trung thế (co nguội) | 12 |
| Chuỗi sứ đỡ / Chuỗi treo Polymer | 2 |
| Yếm cáp | 2 |
| Dây đai Inox | 2 |
| Băng cảnh báo cáp ngầm | 2 |
| Recloser / Máy cắt tự động | 2 |
| Máng che dây, Giá móc, Bộ cáp USB-RS485, LBS | 4 (1 mỗi loại) |
| **Tổng (b)** | **89** |

Không còn dòng nào chưa phân loại được lý do (96 + 89 = 185, khớp tuyệt đối).

**Hệ quả cho outline:** toàn bộ 185 dòng **không có ruột dẫn, không có tiết
diện theo nghĩa cáp** — outline "cấu tạo ruột dẫn/vật liệu" của profile
cap_dien sẽ áp sai nếu không lọc trước bằng đúng tiêu chí trên (khác
`"Cáp điện"`, tính cả NaN). 48/185 dòng trùng với bug Cu-Al ở mục 5.4 — không
phải 2 vấn đề tách biệt, là cùng một tập con.

- Null rate cao ở Cấp Điện Áp (35%) và Tiết Diện (31%) sau khi sửa regex vẫn
  còn ~901 dòng thật sự không có điện áp trong nguồn — outline phải chấp nhận
  bỏ trống mục này, không cố lấp.

### 6.2. tu_va_thiet_bi_dong_cat (300 dòng — rủi ro trung bình)

- Không có SKU trùng chéo, ít cột nhất (8 cột, không có cột kỹ thuật riêng).
- Nhóm Nguồn có 2 giá trị khác hẳn nhau về bản chất: "04. Thiết Bị Đóng Cắt"
  (286 dòng — cầu dao, LBS, Elbow, máy cắt) và **"10. Tủ Điện & Trung Thế" (14
  dòng — vỏ tủ nhựa composite, tủ đo đếm, hộp nguồn)**. 14 dòng này không phải
  "thiết bị đóng cắt" theo nghĩa chặt — không có thông số điện (dòng cắt, dòng
  định mức), chỉ có kích thước vật lý trong tên (VD "900x630x420"). Outline
  chung "Chức năng trong hệ thống điện" của profile này sẽ hơi gượng với 14
  dòng vỏ tủ — cân nhắc outline con nhẹ hơn cho nhóm 10, hoặc chấp nhận outline
  chung nhưng bỏ trống mục không có dữ liệu (đúng nguyên tắc AI không suy đoán).
- Cột `Quy Cách / Áp Lực` với 73.7% trống — không đáng tin cậy làm nguồn dữ
  liệu chính, thông số phải bóc từ `Tên hàng`.

### 6.3. may_bien_ap_do_luong (245 dòng — rủi ro cao nhất về mặt dữ liệu, dù ít dòng)

- Bug kVA/kV (mục 5.1) là rủi ro số 1 — nếu không sửa trước khi build outline,
  165 sản phẩm sẽ bị in ra cấp điện áp sai (VD in "15kV" cho máy 15kVA thật ra
  chạy 12.7/0.23kV) — đây là rủi ro **hiển thị số liệu sai cho khách hàng**,
  không phải chỉ lỗi hiển thị.
- **Phát hiện thêm khi đối chiếu lại 165 dòng bug**: 7 dòng "sạch" còn lại của
  nhóm "05. Máy Biến Áp" (172 − 165 = 7, đã nói ở bản trước là "cần soát tay")
  **không hề sạch theo nghĩa dữ liệu tốt** — soát tay xong thấy cả 7 dòng đều
  là **"Giá treo MBT"** (giá treo máy biến áp lên trụ, VD `Giá treo MBT 1x25`,
  `Giá treo MBT 3x100`), tức cũng là phụ kiện lẫn trong nhóm máy biến áp,
  giống hệt tình huống 185 dòng phụ kiện lẫn trong cap_dien ở mục 6.1. Cả
  `Công Suất (kVA)` và `Cấp Điện Áp (kV)` của 7 dòng này đều trống — không bug
  vì không có gì để bug, không phải vì regex đúng. Nhóm "05. Máy Biến Áp"
  thực chất là 165 máy biến áp thật (đều dính bug) + 7 phụ kiện giá treo (dữ
  liệu trống, không bug nhưng cũng không phải máy biến áp).
- Đúng như mày nói: **"Loại máy"** hầu như không tồn tại như 1 trường riêng —
  cột `Quy Cách / Áp Lực` chủ yếu chứa số hiệu quyết định kỹ thuật ("Tiêu chuẩn
  kỹ thuật\n96/QĐ-HĐTV...") chứ không phải loại máy (dầu/khô/silic...). "Loại
  máy nếu có trong dữ liệu" trong outline nên hiểu là: chỉ lấy được từ chính
  `Tên hàng` (VD "Máy biến áp dầu... Loại Silic"), không có cột riêng để
  render vào bảng thông số có cấu trúc — nếu SPEC muốn 1 cột "Loại máy" trong
  bảng thì phải trích xuất từ Tên hàng bằng regex, không có sẵn.
- Số pha: 122/245 dòng tên hàng có chữ "Pha" — trích được từ Tên hàng, không
  có cột riêng, tương tự trên.
- Phân biệt máy biến áp (nhóm 05, 172 dòng) vs đo lường (nhóm 08, 73 dòng) đã
  rõ ràng qua cột `Nhóm Nguồn`, không cần đoán — outline chọn đúng theo cột
  này là đủ, không cần AI can thiệp.

### 6.4. phu_kien_va_khac (1.332 dòng — rủi ro thấp, nhưng 5 nhóm nguồn khác hẳn nhau)

- 5 giá trị Nhóm Nguồn: Phụ Kiện Cơ Khí (524), Đầu Cáp & Hộp Nối (478), Vật Tư
  Khác (180), Sứ & Cách Điện (109), **Thí Nghiệm & Kiểm Định (41)**.
- Nhóm "09. Thí Nghiệm & Kiểm Định" (41 dòng) đúng là dịch vụ (VD "Thí nghiệm
  MBA 1 pha 10KVA"), không phải sản phẩm vật lý — xác nhận đúng yêu cầu gắn
  `content_type=service`, không dùng Product Schema. Nhận diện được 100% qua
  cột `Nhóm Nguồn`, không cần đoán từ tên.
- 4/17 cặp SKU trùng của toàn hệ nằm ở đây (đầu cáp co nguội trong nhà/ngoài
  trời cùng mã, nối bọc MV cùng mã khác độ dày vỏ) — cùng rủi ro record_id như
  mục 4.
- Đa dạng ĐVT nhất (Cái, Cây, Bộ, Cuộn, Mét, Sợi, Bịch, Ống, Lọ, Chai, Cục,
  Tuýp, Hộp, Bao, Kg) — outline "generic" phải xử lý được ĐVT bất kỳ, không
  hard-code "Cái".

## 7. Tóm tắt rủi ro theo mức ưu tiên sửa trước khi code outline

1. **Phải sửa trước** (sai số liệu hiển thị cho khách): bug kVA→kV (165 dòng
   may_bien_ap).
2. **Phải lọc trước** (sai outline/field áp dụng): 185 dòng phụ kiện lẫn trong
   cap_dien (dùng `Ghi Chú Ban Đầu`), trong đó 48 dòng là Cu-Al bị gán sai vật
   liệu (mục 5.4, là tập con của 185, không phải vấn đề tách biệt); 7 dòng
   "Giá treo MBT" lẫn trong nhóm máy biến áp (mục 6.3), dữ liệu trống hoàn
   toàn ở công suất/điện áp — cùng loại vấn đề, cần route outline riêng.
3. **Nên sửa** (tăng độ đầy dữ liệu, không sửa vẫn chạy được, chỉ bỏ trống
   nhiều hơn cần thiết): regex điện áp thiếu case `V` thường, regex tiết diện
   thiếu case đơn lõi không "x".
4. **Bắt buộc cho khoá dữ liệu**: 17 cặp SKU trùng cần `record_id` ổn định
   theo `profile_id + source_sheet + source_row + sku`, không dùng
   `(profile_id, sku)`.
5. **Chuẩn hoá vặt, không khẩn**: ĐVT có khoảng trắng thừa, 2 dòng brand lặp.

## 8. Phụ lục — Snapshot tên sản phẩm thật để làm unit test

Lấy trực tiếp từ Excel (không tự nghĩ ra), dùng cho unit test regex ở vòng
code đầu tiên. Đủ 4 nhóm, mỗi nhóm đủ đại diện case dương (cần sửa) lẫn case
âm (không được đụng vào, dùng để chống regression).

**A. Điện áp dạng "V" thường (300/500V, 450/750V, 600V) — case cần bóc đúng:**
```
Dây VCmo2x0.75mm2 (300/500V) - Cadivi
Dây VCmo2x1mm2 (300/500V) - Cadivi
Dây VCmo2x1.5mm2 (300/500V) - Cadivi
Dây VCmo2x2.5mm2 (300/500V) - Cadivi
Dây VC2.5mm2 (450/750V)-Cadivi
Dây VC10mm2 (450/750V) -Cadivi
Dây VC6mm2 (450/750V)-Cadivi
Dây VC3mm2 (600V) - Cadivi
Dây CV1.25mm2 (600V)-Cadivi
```
Kỳ vọng sau sửa: cột điện áp nhận đúng "300/500V", "450/750V", "600V" — hiện
tại 3 dạng này đều bị bỏ sót, cột `Cấp Điện Áp` trống dù tên có đủ dữ liệu.

**B. Tiết diện đơn lõi (không có ký tự "x") — case cần bóc đúng:**
```
Dây VC2.5mm2 (450/750V)-Cadivi          -> kỳ vọng: 2.5
Dây VC3mm2 (600V) - Cadivi              -> kỳ vọng: 3
Dây VC10mm2 (450/750V) -Cadivi          -> kỳ vọng: 10
Dây VC6mm2 (450/750V)-Cadivi            -> kỳ vọng: 6
Dây CV1mm2 (0.6/1kV)-Cadivi             -> kỳ vọng: 1
Dây CV1.25mm2 (600V)-Cadivi             -> kỳ vọng: 1.25
```
Case âm (đa lõi, đã đúng từ trước, KHÔNG được để regression):
```
Dây VCmd2x0.5mm2 (0.6/1kV) - Cadivi     -> phải vẫn ra: 2x0.5
Dây CXV2X38mm2 - 600V - Cadivi          -> phải vẫn ra: 2X38 (chữ X hoa)
```

**C. Cu-Al bị gán sai "Đồng (Cu)" — case cần chặn, không tự đoán vật liệu mới:**
```
Cosse ép Cu-Al  16mm2-N-TA dài 45mm chiều dài ép dây 21mm
Cosse ép Cu-Al  16mm2-N-TA dài 52mm chiều dài ép dây 28mm
Cosse ép Cu-Al  25mm2-N-TA dài 45mm chiều dài ép dây 21mm
Cosse ép Cu-Al  35mm2-N-TA dài 51mm chiều dài ép dây 23mm
Cosse ép Cu-Al  50mm2-N-TA dài 51mm chiều dài ép dây 23mm
Cosse ép Cu-Al  70mm2-N-TA dài 58mm chiều dài ép dây 24mm
```
Kỳ vọng: field `Vật Liệu Ruột` bị bỏ trống cho các dòng này (không hiện "Đồng
(Cu)"), đồng thời cả 6 dòng này thuộc nhóm 185 dòng "không phải cáp" (mục 6.1)
nên còn phải test thêm: outline áp dụng phải là `outline_phu_kien`, không phải
outline cáp.

**D. Máy biến áp kVA/kV bug — case cần chặn hiển thị sai:**
```
Máy biến áp dầu 1Pha 15KVA 12.7/0.23KV Loại Silic - TBD    (bug: 15kV sai, đúng phải lấy "12.7/0.23KV")
Máy biến áp dầu 1Pha 25KVA 12.7/0.23KV Loại Silic - TBD
Máy biến áp dầu 1Pha 37.5KVA 12.7/0.23KV Loại Silic - TBD
Máy biến áp dầu 1Pha 50KVA 12.7/0.23KV Loại Silic - TBD
Máy biến áp dầu 3Pha 50KVA 22/0.4KV Loại Silic - TBD
Máy biến áp dầu 3Pha 75KVA 22/0.4KV Loại Silic - TBD
```
Case âm — nhóm "08. Đo Lường & Biến Dòng", KHÔNG được đụng vào (không bug,
đừng để regex mới lỡ sửa nhầm sang nhóm này):
```
Hợp bộ đo lường (MOF) 24kV\nTỷ số biến dòng: 10-20/5A.\nTỷ số biến áp: 22:√3/0.11:√3 (kV)\nDung lượng: 25 (VA), CC0.5 -Young-hwa/ Hàn Quốc
Hợp bộ đo lường (MOF) 24kV\nTỷ số biến dòng:15-30/5A.\nTỷ số biến áp: 22:√3/0.11:√3 (kV)\nDung lượng: 25 (VA), CC0.5 -Young-hwa/ Hàn Quốc
```
Case âm khác — nhóm "05. Máy Biến Áp" nhưng là phụ kiện giá treo, cả 2 cột
đều phải giữ trống, không suy đoán:
```
Giá treo MBT 1x25
Giá treo MBT 3x100
```

Tổng cộng phụ lục này: A=9 (case dương "V" thường) + B=8 (6 dương tiết diện
đơn lõi + 2 âm đa lõi) + C=6 (Cu-Al) + D=10 (6 dương kVA/kV + 2 âm nhóm đo
lường + 2 âm giá treo MBT) = **33 tên sản phẩm thật**, đủ điều kiện "20–30
tên thật" theo yêu cầu review (33 vẫn nằm trong tinh thần "20-30", chỉ nhỉnh
hơn cận trên 3 dòng vì cần đủ case âm chống regression cho cả 4 nhóm).
