# SONEALEO ULTRA 4.5

Bản này sửa **6 lỗi**, trong đó 3 lỗi đang gây thiệt hại thật trên
maybienapvn.vn. Không thêm tính năng mới.

## Đo được

| | Trước 4.5 | Sau 4.5 |
|---|---|---|
| Giá list Lotech in ra HTML công khai | có, 245 bài | **0** |
| MASTER Ver11 (581 dòng) → số URL riêng | 365 → **mất 216 bài** | **581, mất 0** |
| `_so_kva_tu_chuoi('25/40/63MVA')` | 25 kVA (sai 1.000 lần) | 25.000 kVA |
| Công tơ điện / biến dòng có URL `may-bien-ap-...` | 56 dòng | **0** |
| Chuỗi phiên bản trong code | 3 giá trị khác nhau | 1 |
| Test hồi quy | 53 pass | **54 pass**, 0 lỗi mới |

## 6 vá

### 1. Rò giá list ra HTML công khai — `phu_kien_di_kem.py`
`gia_list` nằm trong `FIELD_CAM_TUYET_DOI` của `profiles.py`, nhưng module này
đọc thẳng `row` nên **đi vòng qua hàng rào**. Giá list Lotech in ra công khai
trong khối "Lắp cho máy biến áp nào" trên 245 bài.

Đã bỏ hẳn: không đọc `gia_list`, xoá luôn hàm `_tien()` để không ai vô tình
dùng lại. Test khoá bằng cách quét mã nguồn — còn ký tự `₫` là fail.

> **Bài đã đăng không tự sạch.** Cần một lượt batch REST API xoá chuỗi giá khỏi
> `post_content`. Vá này chỉ chặn bài MỚI.

### 2. Slug trùng — kiến trúc "Slug chỉ định"
Đo trên MASTER Ver11: 581 dòng chỉ ra **365 URL riêng**. Đăng hết là WordPress
đè bài hoặc tự thêm `-2` → **mất 216 bài**.

Cách sửa **không phải** để tool tự tính slug thông minh hơn — đường đó làm đổi
URL của bài đã đăng (test `test_v39_c_seo_update.py` bắt được: KP khô có slug
ngắn cố ý theo brief C4, bị thêm cấp điện áp vào).

Thay bằng hợp đồng đơn giản: **MASTER có cột `Slug chỉ định` thì tool dùng
nguyên văn, không tính lại.** Excel thấy gì → web ra đúng vậy. Cột trống thì
hành vi giữ y như 3.9.

`tien_kiem_slug.py` sinh cột đó, bảo đảm không trùng, và **giữ nguyên slug của
dòng đã có** nên URL không bao giờ tự đổi sau lưng.

### 3. Nhận diện loại sản phẩm sai — bug chữ `đ`
Sheet 03 trộn máy biến áp / vỏ / giá treo / công tơ / biến dòng nhưng **mọi
dòng đều ra `may-bien-ap-...`**, kể cả công tơ điện Gelex EMIC (36 dòng cùng
một URL).

Nguyên nhân gốc sâu hơn: `unicodedata.normalize('NFD')` **không tách được `đ`**
(nó không phải nguyên âm mang dấu phụ), nên `điện` → `đien`, mọi regex chứa
`dien` đều trượt. Đã map `đ→d` trước khi NFD.

Kết quả: `bien-dong-dien` (26), `vo-may-bien-ap` (24), `cong-to-dien` (22),
`hop-bo-do-luong` (9), `dong-ho-do-dien` (8), `gia-treo-may-bien-ap` (7).
Vừa hết trùng, vừa đúng từ khoá trong URL.

### 4. `_so_kva_tu_chuoi()` đọc nhầm MVA — `render_phase2.py`
`'25/40/63MVA'` ra **25 kVA**, sai 1.000 lần. Ảnh hưởng slug (kVA nằm trong
URL), tier công suất, và các field delta context so sánh SKU liền kề. Nay nhận
đơn vị MVA và quy đổi ×1000. Chuỗi nhiều giá trị vẫn lấy số đầu như cũ.

### 5. Cờ nhường schema cho Rank Math
Rank Math + theme + SONEALEO đều có thể sinh `Product`/`FAQPage` → trùng schema,
GSC báo lỗi.

Đặt biến môi trường `SONEALEO_SCHEMA=0` để tool ngừng phát JSON-LD.
**Mặc định BẬT** — giữ nguyên hành vi cũ, an toàn cho site chưa cấu hình
Rank Math schema.

### 6. Phiên bản gom về một nguồn — `phien_ban.py`
Trước 4.5 chuỗi phiên bản đã lệch nhau: `giao-dien.py` ghi `4.4.1.4 HF1`
(3 chỗ), `thu_muc_du_lieu.py` ghi `4.4.1.6`, tên zip ghi `4_4_1_7`. Ba con số
cho cùng một build.

Nay sửa duy nhất ở `phien_ban.py`, mọi nơi khác import.

## Dọn thư mục

- 27 file `.md` rời (CHANGELOG/KẾT-QUẢ/HOTFIX/REGRESSION) → gộp `LICH-SU-TRUOC-4.5.md`
- **Giữ `tests/`.** Bộ 82 test này vừa bắt được regression đổi URL bài đã đăng ở
  mục 2. Xoá để tiết kiệm 660KB là lỗ.

## Quy trình bắt buộc từ 4.5

```
1. Sửa MASTER
2. python tien_kiem_slug.py     -> phải ra "CON TRUNG: 0"
3. Mới render và đăng
```

Bước 2 không đạt thì **đừng đăng, đăng là mất bài**.

## Còn treo — KHÔNG nằm trong 4.5

- **Bản vá cáp VA-4.4.1.8 chưa gộp được** — thư mục đó không có trong zip
  4.4.1.7. Gửi lên thì gộp thành 4.5.1.
- 245 bài đã đăng vẫn còn chuỗi giá + 45 bài còn `div.snl-cho-anh` → cần một
  lượt batch REST API, chưa làm.
- 336 dòng mới sheet 03 chỉ có 5/17 dòng bảng thông số (thiếu Po/Pk/Uk/kích
  thước) → phải quay lại 7 PDF bóc bảng thông số.

---

# 4.5.1 — sự cố 17/08/2026: chỉ nhập được 248/581 dòng

Hai lỗi chồng nhau, **một do 4.5 gây ra**.

| | Trước 4.5.1 | Sau |
|---|---|---|
| Sheet 03 nhập được | **248 / 581** | **581 / 581** |
| Mã SKU bị trùng | — | 0 |
| MASTER thêm cột → import | chặn cứng, ngõ cụt | có đường xác nhận |

### Lỗi 1 — hàng rào cấu trúc cột thành ngõ cụt (do 4.5)
4.5 thêm `Hậu tố slug` + `Slug chỉ định` vào `cot_import`. `db_phase2.py` so
`column_structure` với dataset cũ, khác là raise — và **không có cờ bỏ qua**.
Sheet 03 bị chặn im, tool vẫn chạy dataset cũ 245 dòng.

Đây là lỗi thiết kế có sẵn mà 4.5 làm lộ ra: **thêm một cột hợp lệ vào profile
là vĩnh viễn không import lại được.** `confirm_new_dataset` chỉ xử lý đổi *dữ
liệu*, không xử lý đổi *cấu trúc*.

Nay: cảnh báo nêu **đúng cột nào thêm/bớt**, và nếu **chỉ THÊM** thì xác nhận
để tạo dataset mới (bài/WP ID cũ chuyển sang, không mất). **Có BỚT cột thì vẫn
chặn cứng** — mất cột là mất dữ liệu, không có cờ nào bỏ qua được.

### Lỗi 2 — 333 dòng bị loại vì trống Mã hàng
`nhap_phase2.py` dòng 234: `if not norm.get('ma_goc'): continue`. Catalogue hãng
không in SKU nên 333/336 dòng mới trống `Mã hàng` → rơi ngay tại cửa.
581 − 333 = **248**, đúng con số trên giao diện.

`sinh_ma_noi_bo.py` sinh mã suy từ dữ liệu có thật của chính dòng đó:

```
LTC-HBT-3P-100-22-DAU-SIL-KIN
```

- tiền tố `LTC-` + cột **`Nguồn mã hàng`** ghi rõ *"nội bộ Lotech (catalogue
  không in SKU)"* → không ai nhầm với mã hãng
- tất định: cùng dữ liệu ra cùng mã, chạy lại không đổi
- trùng thì thêm số thứ tự, không bao giờ 2 dòng chung mã
- dòng đã có mã hãng thì **không đụng**

**Đặt vào cột `Mã hàng` là đúng chuẩn, không phải chữa cháy:** theo schema.org
`sku` là mã của *người bán*, mã của *nhà sản xuất* là `mpn`.

### Kiểm bằng đường import thật
```
Ver13: so_dong=248 | hop_le=248 | thieu_ma=0
Ver14: so_dong=581 | hop_le=581 | thieu_ma=0 | sku_trung=[]
```

### File dùng để sinh bài
**`9MASTER_Ver14_MA_NOI_BO.xlsx`** — không dùng Ver11/12/13 nữa.
Lần nhập đầu tool sẽ hỏi *"MASTER có thêm cột mới"* → bấm Yes.

---

# 4.5.2 — UX tab Hàng đợi: không cô lập được "chưa render"

Phát hiện bằng cách **chạy thật giao diện dưới Xvfb** với DB 581 record,
giả lập 245 bài đã đăng — không phải đọc code suy đoán.

### Đo TRƯỚC vá

| Bộ lọc | Dòng hiện | Trong đó ĐÃ ĐĂNG |
|---|---|---|
| Tất cả | 581 | **245** |
| Đủ | 377 | 150 |
| Vừa | 115 | 15 |
| Đói | 89 | 80 |
| Có cảnh báo | 25 | 21 |

Tab chỉ lọc theo **hạng nguyên liệu**, không có trục **trạng thái**. Không bộ
lọc nào cô lập được nhóm chưa render. Bấm "Chọn hết" ở Tất cả → chọn 581, gồm
**245 bài đã đăng** → render lại, đốt quota AI, ghi đè bài đang có thứ hạng.

Và 4 ô đếm "Chưa render / Chờ duyệt / Đã đăng / Cần kiểm" **trông y như nút lọc
nhưng là nhãn chết** — bấm không có gì xảy ra.

### 4 vá

1. **Trục lọc thứ 2 — Trạng thái**: Mọi trạng thái / Chưa render / Chờ duyệt /
   Đã đăng / Lỗi. Giao với trục hạng (AND).
2. **4 ô đếm bấm được** → lọc đúng nhóm đó, con trỏ đổi thành bàn tay.
3. **Nút "Chọn các SKU CHƯA render"** đặt TRƯỚC nút "Chọn hết" — đây là thao
   tác hay dùng nhất, không bao giờ chạm bài đã đăng.
4. **Chặn tai nạn**: "Chọn hết" mà trong bộ lọc có bài ĐÃ ĐĂNG thì hỏi lại,
   mặc định **No**, và chỉ đường sang nút an toàn. Nhãn dưới bảng hiện thêm
   *"(trong đó N ĐÃ ĐĂNG)"*.

### Đo SAU vá (chạy thật)
```
Chưa render     : 336 dòng, đã đăng   0
Đã đăng         : 245 dòng, đã đăng 245
Nút "Chọn SKU CHƯA render" → chọn 336, trong đó ĐÃ ĐĂNG: 0
```

---

# 4.6 — mở đường cho thông số điện, và trả lời "chịu tải bao nhiêu"

## Căn cứ

GSC 8 site: **41 truy vấn "chịu tải bao nhiêu", 1.681 impression, vị trí TB 3,1
nhưng CTR chỉ 2,97%** (vị trí 3 bình thường ~10%). `dây nhôm 16mm chịu tải bao
nhiêu`: 69 impression, vị trí 3,32, **0 click**. Đã xếp hạng, trang không trả
lời được câu hỏi.

Trong khi đó `cot_bang` của cáp có 12 dòng — **không dòng nào là thông số
điện**, toàn nhận dạng và giải mã ký hiệu. 1.217 SKU có dòng định mức và 1.646
có điện trở DC bóc từ catalogue CADIVI **nằm chết trong MASTER**, không có
đường vào bài.

## 5 vá

### 1. Mở `cot_import` + `cot_bang` cho thông số điện
`cot_import` 19 → 27, `cot_bang` 12 → 18. Thêm dòng định mức, độ sụt áp, điện
trở DC, đường kính ruột, nhóm ruột dẫn, kiểu lắp đặt. `cot_ai` cũng nhận 4
trường số để AI viết bám số thật.

### 2. Khối "chịu tải bao nhiêu" — `khoi_chiu_tai.py`
Đặt **trước** các khối kiến thức chung vì đây là câu người mua gõ. Không có số
thì không hiện khối. Điều kiện quy chiếu **luôn** đi kèm — dòng tải trần là sai
kỹ thuật.

### 3. Giá trị suy ra — cái phá trùng lặp thật
Nhãn cột giống nhau thì thêm bao nhiêu cột cũng giống nhau: đo bảng thông số
CXV/DSTA 3x95 vs 3x120 → **98,1% giống, thêm 5 cột chỉ xuống 97,2%**.

Cái khác nhau thật là câu **tính ra từ số của chính SKU đó**:
- chiều dài tuyến tối đa theo ngưỡng sụt áp 2,5% (IEE 522-8, catalogue tr.8)
- chiều dài khi chạy non tải 80%
- tổn hao công suất trên 100 m ở dòng định mức

Đo khối này giữa 3x95 và 3x120: **66,6% giống** — so với 97–99% của bảng thông
số.

### 4. Cổng chất lượng — `cong_chat_luong.py`
Đo TRƯỚC khi render, tốn 0 token AI:
- **MỎNG**: bảng dưới 6 dòng, hoặc văn bản hiển thị dưới 1.200 ký tự
- **TRÙNG**: so `difflib` trên **văn bản hiển thị** (đã bóc thẻ — đo HTML thô
  sẽ bị thẻ và class thổi phồng) với **SKU anh em** cùng mã cáp

Chạy thử 12 SKU CXV/DSTA: bắt 10 bài mỏng, 29 cặp trùng. Biến bài học đắt nhất
của dự án (phát hiện trùng 99,96% sau khi đã đăng 245 bài) thành hàng rào tự
động thấy được ở SKU thứ 3.

### 5. Vá lỗ bộ lọc cấp điện áp — `ra_soat_dien_ap.py`
`ghep_master.py` đặt `key = code if ha_the else None` nhưng nhánh cáp CÓ GIÁP
gán đè vô điều kiện:
```python
elif code in ("CXV/DATA", "CXV/DSTA", ...):
    key = "CXV_GIAP"        # không kiểm ha_the
```
→ cáp trung thế mang mã có giáp ăn dòng tải bảng 0,6/1 kV. Đo trên Ver14:
**1/1.217 SKU dính** (CXV/DSTA 3x95 - 1,8/3(3,6) kV nhận 315 A của bảng hạ thế).

Số lượng nhỏ nhưng đúng loại sai nguy hiểm nhất — số của cấp điện áp này gán
sang cấp điện áp khác, trên trang bán cho kỹ sư. Đã dọn, xuất
**`9MASTER_Ver15_LOC_DIEN_AP.xlsx`**.

## Hồi quy
PASS 66 → **67**, FAIL giữ nguyên 16 (đều là test cần môi trường Windows thật).

## File dùng để sinh bài
**`9MASTER_Ver15_LOC_DIEN_AP.xlsx`** — bỏ Ver14.

## Chưa làm — để 4.6.1
**Title/meta theo khuôn.** CTR ở vị trí 1 mới 7,6% trong khi chuẩn 25–30% →
traffic đang mất ở tầng tiêu đề, không phải tầng xếp hạng. GSC đã chứng minh
truy vấn cấp SKU (có tiết diện) CTR **6,07% vs 2,74%** — người ta gõ tiết diện
thì title phải có tiết diện. Đây là chỗ rẻ nhất còn lại.

---

# 4.6.1 — vá lỗi text trong MASTER

Text bẩn ở nguồn thì bài sinh ra cũng bẩn. Ký tự xuống dòng nằm trong ô Excel
phá cấu trúc HTML khi render; "Cadivi - Cadivi" hiện nguyên si lên tiêu đề.

`va_chinh_ta.py` — **sửa 1.510 ô**, không mất một ô dữ liệu nào:

| Số ô | Lỗi |
|---|---|
| 521 | khoảng trắng đầu/cuối |
| 497 | xuống dòng trong ô |
| 408 | khoảng trắng đôi |
| 62 | khoảng trắng trước dấu câu |
| 9 | nháy cong |
| 7 | ký tự tab |
| 3 | dấu câu thừa cuối Tên hàng |
| 3 | lặp thương hiệu ("Cadivi - Cadivi", "DTR - DTR") |

## Hai thứ CỐ Ý không đụng

**`mm2` → `mm²` (3.998 ô).** Không phải typo. Nhà phân phối viết vậy và người
mua cũng gõ `mm2` trên Google. Đổi sẽ làm lệch khoá tách `Tiết Diện` và đổi
slug bài đã đăng. Rủi ro cao, lợi ích không rõ.

**Gạch ngang dài `–` → `-` (3.059 ô).** Đây là dấu gạch nối đúng chính tả
trong `27kV – 630A`. `slugify()` tự xử khi sinh URL. Sửa là đổi 3.059 ô để lấy
về con số 0.

## Bản vá đầu tiên đã SAI, ghi lại để khỏi lặp

Luật "cắt dấu câu thừa cuối" chạy lần đầu sửa **2.893 ô** — nghe nhiều là biết
sai. Soi ra: nó cắt dấu chấm **cuối câu hợp lệ** trong cột ghi chú
(`Ly do khong co dong tai` 1.909 ô, `Ghi Chú Kiểm Duyệt` 341 ô…) — đó là câu
văn hoàn chỉnh, dấu chấm là ĐÚNG.

Đã siết: luật này chỉ chạy trên **cột định danh ngắn** (Tên hàng, Mã hàng,
ĐVT…) và chỉ khi ô không phải câu văn. **2.893 → 3 ô.**

Cột `Slug chỉ định` / `Slug dự kiến` / `Hậu tố slug` nằm ngoài vùng sửa — đụng
vào là đổi URL bài đã đăng.

## Kiểm
- Đối chiếu Ver15 vs Ver16 từng cột: **không mất ô nào**
- Import thật: 4/4 profile OK, đủ 3387/292/581/1340 dòng
- `Slug chỉ định` nguyên vẹn 581/581
- Hồi quy PASS 67, FAIL 16 — không đổi

## File dùng để sinh bài
**`9MASTER_Ver16_SACH_TEXT.xlsx`** — bỏ Ver15.

---

# 4.6.2 — gỡ ảnh hàng loạt, cổng vào UI, dọn rác, title cáp

## 1. Gỡ ảnh hàng loạt — `tab_anh.py`
Trước 4.6.2 tab ảnh **bất đối xứng**: có "Gán ảnh chung…" gán cho N bài một
phát, nhưng gỡ thì bấm từng ô, từng bài. Gán nhầm một cái là ngồi sửa tay N lần.

Nút mới **"Gỡ ảnh hàng loạt…"**: chọn nhiều dòng → chọn ô 1–5, hoặc **0 = gỡ
tất cả các ô**. Hỏi xác nhận, mặc định **No**.

**Không xoá file ảnh** — chỉ bỏ gán khỏi bài, đúng nguyên tắc có sẵn của
`workspace_anh.bo_anh`: tool không tự xoá dữ liệu người dùng.

## 2. Cổng chất lượng vào UI — `hang_doi.py`
`cong_chat_luong.py` viết ở 4.6 nhưng **không có đường bấm** — module có mà
không ai dùng được. Nút **"Soát mỏng/trùng…"** dựng thử bài của các SKU đang
chọn rồi đo, **không gọi AI, không ghi gì, tốn 0 quota**.

Chạy thật 20 SKU máy biến áp khô HBT: **20 MỎNG, 48 cặp TRÙNG 96–98%**. Đây
chính là 336 dòng mới chỉ có 5/17 dòng bảng thông số — giờ nhìn thấy trước khi
sinh, không phải sau khi đăng.

## 3. Hai luật dọn rác — `sweep_rac.py`
- `gia_list_lo` — chuỗi giá Lotech lộ trong khối phụ kiện. Neo chặt: phải đúng
  dạng ` · <số> ₫` ngay trước `</small>`.
- `caveat_a2608` — câu rào đón nội bộ A2608 / QĐ-EVN lọt ra bài bán hàng.

Thử: xoá đúng chuỗi giá và đúng câu caveat, **giữ nguyên mã hàng và câu bên
cạnh**. 4.5 đã chặn ở tầng sinh; hai luật này dọn phần ĐÃ ĐĂNG — không tốn
quota, không gọi AI, chạy thử được trước bằng `chi_thu=True`.

## 4. Title cáp điện — `render_phase2.dung_tieu_de()`
Trước 4.6.2 cáp lấy **nguyên Tên hàng** làm title:
`Dây CXV/DSTA3x95mm2 (0.6/1kV) - Cadivi`

GSC: CTR ở vị trí 1 mới **7,6%** trong khi chuẩn 25–30% → traffic mất ở tầng
tiêu đề, không phải tầng xếp hạng. Truy vấn cấp SKU (có tiết diện) CTR **6,07%
vs 2,74%**.

Title mới đưa **dòng tải** vào — vừa bắt cụm "chịu tải bao nhiêu" (41 truy vấn,
vị trí TB 3,1, CTR 2,97%), vừa là con số khác nhau giữa từng SKU:

```
Cáp CXV/DSTA3x95mm2 (0.6/1kV) Cadivi 315A — báo giá          (51 ký tự)
Cáp CXV/DSTA3x120mm2 (0.6/1kV) Cadivi 360A — báo giá         (52 ký tự)
Cáp AV16mm2 (0.6/1kV) Cadivi 70A — báo giá, thông số kỹ thuật (61 ký tự)
```

Tự cắt đuôi khi vượt 65 ký tự. Bỏ chữ "Dây" và đuôi "- Cadivi" lặp.

**Một bug bắt được lúc test:** `rstrip('0')` biến `360` thành `36`, `20` thành
`2`. Đã thay bằng ép float rồi format `%g`.

## Hồi quy
PASS 67, FAIL 16 — không đổi. Chạy thật cả `hang_doi` và `tab_anh` dưới Xvfb.
