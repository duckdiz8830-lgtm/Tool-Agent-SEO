# ARCHITECTURE DRAFT — Phase 2 Lite: 4 Profile Registry

**Đã duyệt để bắt đầu code (vòng duyệt 2). Bản này đã sửa 6 điểm theo yêu cầu
vòng duyệt 2 — xem mục 12 "Vòng duyệt 2" để đối chiếu từng điểm. Kèm
`TEST-REPORT.md` khi giao code, ghi PASS/FAIL từng test ở mục 10.**

Đã đọc `dulieu.py`, `autopost.py`, `cauhinh.py`, `prompts.py`, `giao-dien.py`
thật của v2.8 để bản vẽ này khớp code hiện có, không phải vẽ trên giấy trắng.

## 0. Phát hiện quan trọng nhất

`nhap_excel()` hiện tại đọc Excel theo **vị trí cột cố định**, không có
header: `r[0]`=STT (bắt buộc là số), `r[1]`=mã, `r[2]`=cấu hình. Viết riêng
cho layout file tủ RMU. Bộ dữ liệu mới có **header thật, tên cột tiếng Việt có
dấu**. Không sửa vá được — theo quyết định #4, importer RMU cũ chuyển thành
**legacy adapter**, có 1 dispatcher chung phía trên gọi đúng adapter theo
loại nguồn (xem mục 9), không còn 2 pipeline độc lập chạy song song không ai
quản.

`boc_thong_so()`, `tach_model()`, cách ghép `ten_san_pham` trong
`nhap_excel()` (dòng `f'Tủ RMU {hang} {series}...'`) toàn bộ đặc thù RMU —
đóng gói lại thành 1 hàm `import_rmu_legacy()` gọi nguyên xi code cũ, không
sửa logic bên trong.

`prompts.py::MAU` và `cauhinh.py::COT_BANG` hiện là hằng số toàn cục duy
nhất, không phân theo profile — đây là chỗ Profile Registry thay thế.

## 1. Luồng import mới

```
Excel (MASTER hoặc 1 trong 4 file con) HOẶC file RMU cũ
  → dispatcher_import() nhận diện loại nguồn (xem mục 9)
  → đọc raw cell -> normalize_cell() từng ô NGAY LÚC ĐỌC (mục 1.1) — mọi bước
    sau đây chỉ thao tác trên dữ liệu đã normalize, không đụng lại raw pandas
  → tính file_checksum (sha256 nội dung file vật lý) VÀ data_checksum (hash
    nội dung dữ liệu đã normalize, tính riêng theo từng sheet/profile) — xem
    mục 3
  → so dataset: giống hệt -> giữ dataset_id cũ; khác -> tạo dataset_id mới,
    cảnh báo, không ghi đè dữ liệu dataset cũ (mục 3)
  → với mỗi dòng: build record_id, khoá lưu trữ = (dataset_id, record_id)
  → chuẩn hoá field theo Profile Registry + Outline Registry: tách
    cot_import/cot_ai/cot_bang/cot_noi_bo, tính effective_cot_ai/
    effective_cot_bang theo outline_id đã route (mục 2)
  → routing outline_id theo field nội bộ (ghi_chu_ban_dau / nhom_nguon) — mục 4
  → validate theo STRICT DATA RULES (mục 4)
  → ghi vào kho dữ liệu chung (SQLite, giữ cấu trúc bảng hiện có, thêm cột)
```

### 1.1. `normalize_cell()` — chuẩn hoá ngay ở tầng importer

Theo quyết định #5 của vòng duyệt này: pandas đọc Excel ra kiểu dữ liệu không
đồng nhất (NaN kiểu float, số đọc thành `int`/`float`/`numpy.float64`, chuỗi
có khoảng trắng thừa ở đầu/cuối như đã thấy ở ĐVT). Toàn bộ chỗ trong code cũ
dùng trực tiếp `(row.get(k) or '').strip()` lên dữ liệu vừa đọc từ pandas là
**không an toàn** — `.strip()` gọi lên `NaN` (float) sẽ lỗi, gọi lên `int`
cũng lỗi, phải ép kiểu trước.

```python
def normalize_cell(v):
    """Chuẩn hoá 1 ô dữ liệu đọc từ Excel, chạy NGAY LÚC IMPORT, một lần duy
    nhất. Từ đây về sau, mọi nơi khác trong code (prompt, bảng HTML, schema,
    validator) chỉ đọc giá trị đã qua hàm này, không đọc lại ô Excel gốc."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ''
    if isinstance(v, (int, float)):
        # số nguyên không hiện .0 thừa (Excel hay trả 15.0 cho ô ghi "15")
        return str(int(v)) if float(v).is_integer() else str(v)
    return str(v).strip()
```

Áp dụng ngay trong `import_4_profile()`/`import_rmu_legacy()`, trước khi field
được xếp vào `cot_import`. Sau bước này, `row.get(k)` luôn trả về `str` (rỗng
hoặc có nội dung đã strip), không bao giờ trả `NaN`/`None`/số thô — mọi hàm
downstream (`bang_thong_so`, `dung_prompt`, `dung_schema`, validator) được
phép viết thẳng `row.get(k, '')` mà không cần `or ''`/`.strip()` phòng thủ lại
lần nữa. Đây là điểm sửa bắt buộc ở `dulieu.py` (hàm nhập mới) và rà lại
`autopost.py::bang_thong_so()` (đang có `(row.get(k) or "").strip()`, sau khi
normalize ở tầng import thì dòng này thừa nhưng không sai — có thể giữ như
lớp phòng thủ kép, không bắt buộc xoá).

## 2. Profile Registry + Outline Registry — 4 lớp cấu hình cột, không hard-code class

Theo quyết định #2, mỗi profile không còn 1 danh sách cột duy nhất mà tách
thành **4 lớp**, mỗi field Excel chỉ được xếp vào đúng lớp cần thiết — không
tự động lọt sang lớp khác:

| Lớp | Ý nghĩa | Giá List (VNĐ) được nằm ở đây? |
|---|---|---|
| `cot_import` | Toàn bộ field đọc được từ Excel, kể cả field không dùng sau này. Nguồn sự thật gốc. | Có |
| `cot_noi_bo` | Field chỉ dùng để routing/validate/audit trong phần mềm, KHÔNG BAO GIỜ ra khỏi backend (không vào prompt, không vào HTML, không vào schema). | Có |
| `cot_ai` | Field được phép đưa vào prompt cho AI viết diễn giải. | **Không** |
| `cot_bang` | Field được phép render ra bảng thông số / Schema `additionalProperty`. | **Không** |

`cot_ai` và `cot_bang` luôn là tập con của `cot_import`, và **loại trừ cứng**
`gia_list` cùng `ghi_chu_ban_dau` (xem quyết định #9) ở tầng khai báo, không
phải ở tầng lọc runtime — nghĩa là nếu ai đó code sai, thêm nhầm `gia_list`
vào `cot_ai` của 1 profile, việc build registry phải tự chặn (assert lúc khởi
động), không im lặng chạy tiếp.

```python
PROFILES = {
  'cap_dien': {
      'nhan': 'Cáp điện',
      'cot_import': {   # tên cột Excel -> field nội bộ, ĐẦY ĐỦ mọi cột đọc được
          'Mã hàng': 'ma_goc', 'Tên hàng': 'ten_goc',
          'Nhãn Hiệu / Xuất Xứ': 'thuong_hieu', 'Quy Cách / Áp Lực': 'quy_cach',
          'ĐVT': 'dvt', 'Giá List (VNĐ)': 'gia_list', 'Ghi Chú Ban Đầu': 'ghi_chu_ban_dau',
          'Nhóm Nguồn': 'nhom_nguon', 'Tiết Diện (mm²)': 'tiet_dien',
          'Cấp Điện Áp': 'cap_dien_ap', 'Vật Liệu Ruột': 'vat_lieu_ruot',
      },
      'cot_noi_bo': ['gia_list', 'ghi_chu_ban_dau', 'nhom_nguon'],
      'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt',
                 'tiet_dien', 'cap_dien_ap', 'vat_lieu_ruot'],
      'cot_bang': [
          ('ma_goc', 'Mã hàng'), ('thuong_hieu', 'Thương hiệu'),
          ('tiet_dien', 'Tiết diện'), ('cap_dien_ap', 'Cấp điện áp'),
          ('vat_lieu_ruot', 'Vật liệu ruột'), ('quy_cach', 'Quy cách'),
          ('dvt', 'Đơn vị tính'),
      ],
      'outline_id_mac_dinh': 'outline_cap_dien',
      'routing_outline': {
          'cot_kiem_tra': 'ghi_chu_ban_dau',
          'quy_tac': 'khac "Cáp điện" (kể cả rỗng/NaN) -> outline_id = outline_phu_kien',
      },
      'validator': 'validate_cap_dien',
      'content_type': 'product',
  },
  'tu_va_thiet_bi_dong_cat': {
      'nhan': 'Tủ và thiết bị đóng cắt',
      'cot_import': { 8 cột chung },
      'cot_noi_bo': ['gia_list', 'ghi_chu_ban_dau', 'nhom_nguon'],
      'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
      'cot_bang': [('ma_goc','Mã hàng'), ('thuong_hieu','Thương hiệu'),
                   ('quy_cach','Quy cách'), ('dvt','Đơn vị tính')],
      'outline_id_mac_dinh': 'outline_tu_dong_cat',
      'routing_outline': {
          'cot_kiem_tra': 'nhom_nguon',
          'quy_tac': '"10. Tủ Điện & Trung Thế" -> outline_id = outline_vo_tu',
      },
      'validator': 'validate_tu_dong_cat',
      'content_type': 'product',
  },
  'may_bien_ap_do_luong': {
      'nhan': 'Máy biến áp & đo lường',
      'cot_import': { 8 cột chung + 'Công Suất (kVA)': 'cong_suat', 'Cấp Điện Áp (kV)': 'cap_dien_ap' },
      'cot_noi_bo': ['gia_list', 'ghi_chu_ban_dau', 'nhom_nguon'],
      'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt', 'cong_suat', 'cap_dien_ap'],
      'cot_bang': [('ma_goc','Mã hàng'), ('thuong_hieu','Thương hiệu'),
                   ('cong_suat','Công suất'), ('cap_dien_ap','Cấp điện áp'), ('dvt','Đơn vị tính')],
      'outline_id_theo_nhom_nguon': {
          '05. Máy Biến Áp': 'outline_may_bien_ap',
          '08. Đo Lường & Biến Dòng': 'outline_do_luong',
      },
      'routing_outline_phu': {
          'cot_kiem_tra': 'ten_goc',
          'quy_tac': 'chứa "Giá treo" -> outline_id = outline_phu_kien',
      },
      'validator': 'validate_may_bien_ap',
      'content_type': 'product',
  },
  'phu_kien_va_khac': {
      'nhan': 'Phụ kiện và khác',
      'cot_import': { 8 cột chung },
      'cot_noi_bo': ['gia_list', 'ghi_chu_ban_dau', 'nhom_nguon'],
      'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
      'cot_bang': [('ma_goc','Mã hàng'), ('thuong_hieu','Thương hiệu'),
                   ('quy_cach','Quy cách'), ('dvt','Đơn vị tính')],
      'outline_id_mac_dinh': 'outline_phu_kien',
      'validator': 'validate_phu_kien',
      'content_type_theo_nhom_nguon': {
          '09. Thí Nghiệm & Kiểm Định': 'service',
          '__default__': 'product',
      },
  },
}
```

`ghi_chu_ban_dau` và `nhom_nguon` **luôn nằm trong `cot_noi_bo`, không bao giờ
trong `cot_ai` hay `cot_bang`** ở cả 4 profile — đúng quyết định #9. Chúng chỉ
được đọc bởi lớp routing (`routing_outline`) và validator, không có đường nào
để lọt vào prompt hoặc bài viết — kể cả khi code sau này thêm profile mới mà
quên khai báo, vì mặc định 1 field KHÔNG được liệt kê trong `cot_ai` hoặc
`cot_bang` thì coi như bị cấm, không phải mặc định cho phép.

### 2.1. Outline Registry — field override theo outline, không chỉ theo profile

Vấn đề cụ thể cần giải: 185 dòng cap_dien route sang `outline_phu_kien` (mục
4) hiện chỉ đổi `outline_id`, nhưng `cot_ai`/`cot_bang` vẫn đang lấy nguyên
từ `PROFILES['cap_dien']` — nghĩa là field `vat_lieu_ruot` (mang ngữ nghĩa
"vật liệu ruột dẫn của cáp") vẫn có thể lọt vào prompt/bảng cho 1 dòng thực ra
là cosse Cu-Al, dù dòng đó đã bị validator để trống giá trị. Để trống giá trị
là chưa đủ — bản thân cái field đó (tên field, ý nghĩa) không nên xuất hiện
trong ngữ cảnh phụ kiện dù có giá trị hay không, vì nhãn "Vật liệu ruột" hiện
trong bảng thông số của 1 cosse là sai ngữ nghĩa cho khách đọc.

Theo quyết định #6: thêm 1 registry riêng cho outline, mỗi outline khai báo
tập field nó **cho phép**, độc lập với profile:

```python
OUTLINES = {
    'outline_cap_dien': {
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt',
                   'tiet_dien', 'cap_dien_ap', 'vat_lieu_ruot'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'tiet_dien', 'cap_dien_ap',
                     'vat_lieu_ruot', 'quy_cach', 'dvt'],
    },
    'outline_phu_kien': {
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
        # KHÔNG có tiet_dien/cap_dien_ap/vat_lieu_ruot -> dù profile cap_dien
        # cho phép, outline phụ kiện không cho phép, field bị loại ở bước giao nhau
    },
    'outline_tu_dong_cat': {
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
    },
    'outline_vo_tu': {
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
        # 14 dòng vỏ tủ: cùng field với outline_tu_dong_cat ở Phase 2 Lite vì
        # tu_va_thiet_bi_dong_cat không có field kỹ thuật riêng để loại bớt —
        # tách outline riêng chỉ để đổi VĂN PHONG/outline nội dung (mục 4),
        # không phải để giới hạn thêm field.
    },
    'outline_may_bien_ap': {
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt', 'cong_suat', 'cap_dien_ap'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'cong_suat', 'cap_dien_ap', 'dvt'],
    },
    'outline_do_luong': {
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt', 'cap_dien_ap'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'cap_dien_ap', 'dvt'],
        # không có cong_suat -> nhóm đo lường không dùng field công suất (mục 6.3 DATA-AUDIT)
    },
}


def effective_cot_ai(profile_id, outline_id):
    """Giao giữa field profile cho phép và field outline cho phép — cả 2 lớp
    đều phải đồng ý thì field mới lọt vào prompt."""
    p = set(PROFILES[profile_id]['cot_ai'])
    o = set(OUTLINES[outline_id]['cot_ai'])
    return [f for f in PROFILES[profile_id]['cot_ai'] if f in (p & o)]


def effective_cot_bang(profile_id, outline_id):
    p = {k for k, _ in PROFILES[profile_id]['cot_bang']}
    o = set(OUTLINES[outline_id]['cot_bang'])
    return [(k, nhan) for k, nhan in PROFILES[profile_id]['cot_bang'] if k in (p & o)]
```

Với 1 dòng cap_dien bị route sang `outline_phu_kien`:
`effective_cot_bang('cap_dien', 'outline_phu_kien')` = giao giữa
`{ma_goc, thuong_hieu, tiet_dien, cap_dien_ap, vat_lieu_ruot, quy_cach, dvt}`
(của profile) và `{ma_goc, thuong_hieu, quy_cach, dvt}` (của outline_phu_kien)
= `{ma_goc, thuong_hieu, quy_cach, dvt}` — `vat_lieu_ruot`/`tiet_dien`/
`cap_dien_ap` bị loại **ở đúng bước này**, không phải nhờ giá trị rỗng, dù
Excel có điền giá trị cho field đó ở dòng này (VD 1 dòng cosse nào đó lỡ có
giá trị hợp lệ ở cột `Tiết Diện` cũng vẫn bị loại, vì outline phụ kiện không
công nhận field đó có ý nghĩa cho loại sản phẩm này).

Mọi nơi build prompt (`dung_prompt()`, mục 5) và render bảng/schema
(`bang_thong_so()`, `dung_schema()`, mục 6/8) đều gọi
`effective_cot_ai(profile_id, outline_id)` /
`effective_cot_bang(profile_id, outline_id)`, **không gọi thẳng
`PROFILES[profile_id]['cot_ai']`** nữa — đây là điểm sửa thay thế lời gọi cũ
ở mục 5/6/8 của bản trước.

## 3. record_id + dataset_id + metadata dataset

Theo quyết định #3 (vòng duyệt trước) — chấp nhận record_id theo `source_row`
cho Phase 2 Lite. Theo quyết định #3 và #4 của **vòng duyệt này** — sửa lại 2
điểm: (a) không dùng `file_checksum` làm căn cứ duy nhất so dataset, thêm
`data_checksum`; (b) khoá lưu trữ chính thức là `(dataset_id, record_id)`,
không phải `record_id` một mình.

### 3.1. Hai loại checksum, hai mục đích khác nhau

```python
def record_id(profile_id, source_sheet, source_row, sku):
    return f'{profile_id}::{source_sheet}::{source_row}::{sku}'

# Lưu riêng từng field, KHÔNG chỉ mã hoá trong 1 chuỗi ID:
{
    'record_id': ...,
    'dataset_id': 'ds_20260724_1',      # mới — xem 3.2
    'source_sheet': '01_Cap_Dien',
    'source_row': 42,
    'file_checksum': 'sha256:...',       # hash NGUYÊN FILE VẬT LÝ đã import
    'data_checksum': 'sha256:...',       # hash NỘI DUNG DỮ LIỆU đã normalize, tính theo từng sheet/profile
}
```

- **`file_checksum`**: sha256 trên byte gốc của file Excel — dùng để **audit**
  ("đúng file này đã được import lúc nào, có sửa lại file gốc sau đó không").
  Không dùng để quyết định dataset giống/khác, vì 2 file khác nhau tuyệt đối
  ở mức byte (VD MASTER đóng gói 4 sheet vào 1 workbook, file con là 4 workbook
  riêng — metadata Excel, thứ tự sheet, compression khác nhau) vẫn hoàn toàn
  có thể chứa **cùng một dữ liệu**, đã kiểm chứng thực tế: `01_Cap_Dien.xlsx`
  và sheet `01_Cap_Dien` trong `MASTER_4_PROFILE_SAN_PHAM.xlsx` có
  `file_checksum` chắc chắn khác nhau nhưng dữ liệu **giống tuyệt đối**
  (`.equals()` = True, đã kiểm ở DATA-AUDIT mục 1).
- **`data_checksum`**: sha256 trên dữ liệu đã qua `normalize_cell()` (mục
  1.1), tính theo từng cặp (profile, sheet) — ghép các dòng đã normalize
  thành 1 chuỗi ổn định (VD nối theo thứ tự cột cố định + `\n` giữa các dòng)
  rồi hash. Đây mới là căn cứ để so "có phải cùng dataset không".

```python
def data_checksum(rows_normalized, cot_import_keys):
    """rows_normalized: list[dict] đã qua normalize_cell(). cot_import_keys:
    thứ tự cột cố định để hash ổn định, không phụ thuộc thứ tự dict."""
    buf = '\n'.join(
        '|'.join(row.get(k, '') for k in cot_import_keys)
        for row in rows_normalized
    )
    return 'sha256:' + hashlib.sha256(buf.encode('utf-8')).hexdigest()
```

**Quy tắc**: nếu `data_checksum` của 1 sheet trong MASTER trùng với
`data_checksum` của file con tương ứng, hệ thống coi đó là **cùng một
dataset**, dù `file_checksum` khác nhau — không cảnh báo "dataset mới" trong
trường hợp này, không tạo `dataset_id` trùng lặp cho cùng 1 dữ liệu chỉ vì
người dùng đổi từ nhập 4 file con sang nhập 1 file MASTER hoặc ngược lại.

### 3.2. `dataset_id` — sinh mới khi xác nhận dataset thay đổi thật

```python
def kiem_tra_dataset(profile_id, data_checksum_moi, cau_truc_cot_moi):
    ds_gan_nhat = lay_dataset_gan_nhat(profile_id)
    if ds_gan_nhat is None:
        return tao_dataset_id_moi(profile_id)   # lần đầu import, không cần hỏi
    if data_checksum_moi == ds_gan_nhat.data_checksum:
        return ds_gan_nhat.dataset_id           # cùng dữ liệu, dùng lại dataset_id cũ
    if cau_truc_cot_moi != ds_gan_nhat.cau_truc_cot:
        # cấu trúc cột đổi -> cảnh báo mạnh, chặn tới khi xác nhận tay
        raise CanhBaoCauTrucDoi(...)
    # data_checksum khác, cấu trúc cột giống -> cảnh báo "dataset đã đổi",
    # liệt kê số dòng thêm/bớt/khác, CHỜ người dùng xác nhận
    if not nguoi_dung_xac_nhan_dataset_moi():
        return None   # dừng import, không tự quyết
    return tao_dataset_id_moi(profile_id)   # xác nhận rồi mới sinh dataset_id mới
```

Khi `dataset_id` mới được tạo (do xác nhận dataset thật sự đổi): các record
thuộc `dataset_id` cũ **giữ nguyên toàn bộ** — URL đã đăng, WP Post ID, trạng
thái, ngày đăng — không bị đụng tới. Record mới thuộc `dataset_id` mới, kể cả
khi `record_id` (theo `profile_id::source_sheet::source_row::sku`) trùng với
1 record của dataset cũ, vẫn là 2 dòng lưu trữ tách biệt.

### 3.3. Khoá lưu trữ chính thức

Theo quyết định #4 của vòng duyệt này: **khoá lưu trữ = `(dataset_id,
record_id)`**, không phải `record_id` một mình — sửa lại so với bản trước
(bản trước ngầm định `record_id` là đủ, chưa tính trường hợp import lại cùng
file/cùng cấu trúc nhưng dữ liệu đã đổi).

```sql
PRIMARY KEY (dataset_id, record_id)
```

Mọi thao tác ghi dashboard, ghi WP Post ID, cập nhật trạng thái đều phải
truyền cả 2 giá trị, không được suy `dataset_id` ngầm từ "dataset đang active"
toàn cục nếu có nhiều dataset cùng tồn tại cho 1 profile (VD dataset cũ còn
bài đang chạy dở, dataset mới vừa xác nhận) — tránh việc ghi nhầm bài của
dataset cũ vào dataset mới chỉ vì code giả định luôn có đúng 1 dataset active.

`(profile_id, sku)` vẫn giữ làm khoá phụ chỉ để cảnh báo SKU trùng (17 cặp đã
audit) — không dùng để lưu trữ chính, không ảnh hưởng khoá `(dataset_id,
record_id)`.

`sinh_mot_bai`, dashboard, WP post mapping trong `autopost.py` hiện định danh
theo `row['sku']` ở nhiều chỗ (`ghi_log`, `_url_anh_tren_wp`...) — cần rà lại
toàn bộ chỗ dùng `sku` làm khoá thao tác và đổi sang `(dataset_id,
record_id)`. Đây vẫn là điểm sửa lan rộng nhất của vòng này.

## 4. Validator riêng từng profile + routing outline_id

Chạy 1 lần lúc import, trước khi ghi vào kho.

- **validate_may_bien_ap(row)**:
  - Chỉ áp cho `Nhóm Nguồn == '05. Máy Biến Áp'` (165/172 dòng bug — xem
    DATA-AUDIT mục 5.1).
  - Regex ưu tiên bắt cụm điện áp thật đứng sau cụm công suất kVA trong tên
    (VD "15KVA 12.7/0.23KV" -> công suất=15kVA, điện áp=12.7/0.23kV, không
    lấy lại số công suất làm điện áp).
  - Trước khi regex sửa xong: đánh cờ `canh_bao_dien_ap = True`, KHÔNG hiển
    thị `Cấp Điện Áp (kV)` gốc.
  - Theo quyết định #10: regex này phải sửa xong ngay trong vòng code đầu
    tiên, không dời backlog.
  - 7 dòng "Giá treo MBT" trong cùng nhóm 05 (phát hiện thêm khi review, xem
    DATA-AUDIT mục 6.3) không bug (2 cột đều trống) nhưng cũng không phải máy
    biến áp -> route sang `outline_phu_kien` qua `routing_outline_phu`.
  - Unit test bắt buộc: dùng đúng snapshot 33 tên thật ở DATA-AUDIT mục 8,
    nhóm D (8 dòng bug + 2 dòng nhóm đo lường không bug + 2 dòng giá treo).

- **validate_cap_dien(row)**:
  - Routing: `ghi_chu_ban_dau` khác "Cáp điện" (kể cả NaN) -> gắn
    `outline_id = outline_phu_kien`. **`profile_id` giữ nguyên `cap_dien`,
    không đổi** — đúng chốt #1. `record_id` vẫn tính theo `profile_id=cap_dien`
    nên không bị xáo trộn dù outline khác.
  - Field `tiet_dien`/`cap_dien_ap`/`vat_lieu_ruot`: **không còn lọc thủ công
    trong validator này** như bản trước — theo quyết định #6 của vòng duyệt
    này, việc loại field theo outline chuyển hẳn sang `effective_cot_ai()`/
    `effective_cot_bang()` (mục 2.1), vì đây là logic chung cho MỌI profile bị
    route outline khác mặc định (không chỉ cap_dien), để 1 chỗ duy nhất, tránh
    validator riêng từng profile phải tự viết lại cùng 1 kiểu lọc. Validator
    chỉ còn việc: xác định đúng `outline_id`, gắn vào record; việc field nào
    lọt/không lọt vào prompt-bảng-schema là việc của Outline Registry.
  - Vật liệu ruột: nếu `ten_goc` chứa "Cu-Al"/"Cu/Al" (không phân biệt hoa
    thường) -> không dùng giá trị cột `vat_lieu_ruot` gốc (đang sai "Đồng
    (Cu)"), để trống khi lưu — không tự suy đoán "lưỡng kim". Đây là sửa GIÁ
    TRỊ (khác với việc loại cả field ở Outline Registry) — 2 cơ chế cộng lại:
    dòng Cu-Al vừa bị route sang outline_phu_kien (field `vat_lieu_ruot` bị
    loại hoàn toàn khỏi output), vừa có giá trị gốc bị validator để trống nếu
    có dòng nào đó (ngoài 185 dòng đã route) lỡ vẫn giữ outline_cap_dien mà
    tên có Cu-Al — phòng thủ 2 lớp, không phải thừa.
  - Theo quyết định #10: regex điện áp dạng "V" thường (300/500V, 450/750V,
    600V) và regex tiết diện đơn lõi không "x" phải sửa xong trong vòng code
    đầu tiên, dùng đúng snapshot mục A/B trong DATA-AUDIT phụ lục.

- **validate_tu_dong_cat(row)**: routing `nhom_nguon == '10. Tủ Điện & Trung
  Thế'` (14 dòng) -> `outline_id = outline_vo_tu`, `profile_id` giữ nguyên
  `tu_va_thiet_bi_dong_cat` — đúng chốt #3. Field nào trống (dòng cắt, dòng
  định mức) thì bỏ qua, không ép hiện ra bảng thông số bằng chuỗi rỗng giả —
  cơ chế `bang_thong_so()` (mục 6.1) đã tự động không render field trống,
  không cần thêm code riêng.

- **validate_phu_kien(row)**: `nhom_nguon == '09. Thí Nghiệm & Kiểm Định'` ->
  `content_type = service`, còn lại `product`.

- **Validator dùng chung mọi profile**: chuẩn hoá `dvt` (`.strip()`, gộp biến
  thể khoảng trắng), phát hiện 17 cặp SKU trùng trong cùng profile -> cảnh
  báo, không gộp.

## 5. Dữ liệu truyền cho AI

Giữ nguyên cơ chế `dien_bien()`/`ThieuThiRong` (thiếu field trả rỗng, không
nổ lỗi). Thay đổi bắt buộc: `dung_prompt()` trong `autopost.py` chỉ build
dict truyền vào prompt từ đúng `effective_cot_ai(profile_id, outline_id)`
(mục 2.1) — **không phải `PROFILES[profile_id]['cot_ai']` một mình** như bản
trước, vì đã có Outline Registry giao thêm 1 lớp lọc theo outline. Không
truyền nguyên `row` đầy đủ vào hàm build prompt.

Vì `cot_ai` của mọi profile lẫn mọi outline theo thiết kế mục 2/2.1 không bao
giờ chứa `gia_list` hay `ghi_chu_ban_dau`, không cần thêm 1 lớp lọc runtime
riêng — bản thân việc build dict theo whitelist `effective_cot_ai` đã là cơ
chế chặn duy nhất, không có đường vòng.

Giá trị đưa vào dict đều đã qua `normalize_cell()` từ lúc import (mục 1.1) —
`dung_prompt()` không tự gọi `.strip()`/ép kiểu lại trên dữ liệu, chỉ đọc
thẳng `row.get(k, '')` vì đảm bảo luôn là `str` sạch.

`price_display` không lấy từ Excel, gán cứng "Liên hệ" ở tầng render, không
qua AI, không qua `cot_ai`.

## 6. Renderer bảng thông số + Sanitize HTML

### 6.1. Bảng thông số

Thay `bang_thong_so(row)` đọc `C.COT_BANG` (hằng số toàn cục) bằng đọc
`effective_cot_bang(profile_id, outline_id)` (mục 2.1) — không phải
`PROFILES[profile_id]['cot_bang']` một mình, vì cần giao thêm với field
outline cho phép:

```python
def bang_thong_so(row, profile_id, outline_id):
    cot_bang = effective_cot_bang(profile_id, outline_id)
    tr = [f'<tr><th>{html.escape(nhan)}</th><td>{html.escape(v)}</td></tr>'
          for k, nhan in cot_bang
          if (v := row.get(k, ''))]   # đã normalize từ lúc import, không .strip() lại
    if not tr:
        return '<p><em>Đang cập nhật thông số kỹ thuật.</em></p>'
    return '<table class="specs-table"><tbody>\n' + '\n'.join(tr) + '\n</tbody></table>'
```

Ô trống tự động không sinh dòng `<tr>` — chỉ tham số hoá theo profile+outline.
Giá trị `row.get(k, '')` không còn cần `(... or '').strip()` phòng thủ như bản
trước, vì dữ liệu đã qua `normalize_cell()` từ lúc import (mục 1.1) — không
đọc trực tiếp `(row.get(k) or '').strip()` lên dữ liệu pandas thô nữa, đúng
quyết định #5 của vòng duyệt này.

`bang_gia()` (gộp bảng giá nhiều cấu hình) không dùng trong vòng này —
outline HTML (`prompts.py::HTML`) bỏ khối `{bang_gia}` và
`<h2>Bảng giá...</h2>`, thay bằng khối cố định "Liên hệ để nhận báo giá",
không đọc từ `gia_list`.

### 6.2. sanitize_html — MỚI, theo yêu cầu bổ sung #5

HTML do AI trả về (các field `*_html`, `faq[].a` trong JSON response Gemini)
phải qua `sanitize_html()` trước khi ghép vào template và trước khi lưu/đăng
WordPress. Bảng thông số do code tự dựng (mục 6.1, đã `html.escape` từng ô)
**không đi qua `sanitize_html()` lần nữa** — nó là HTML do code kiểm soát
100%, không phải input không tin cậy; chạy sanitize lần 2 có nguy cơ bị
whitelist chung xén mất `class="specs-table"`, `colspan`, `rowspan`.

Whitelist đề xuất (dùng `bleach` hoặc tương đương, chốt thư viện cụ thể ở
vòng code):

```python
ALLOWED_TAGS = ['h2', 'h3', 'h4', 'p', 'ul', 'ol', 'li',
                 'table', 'thead', 'tbody', 'tr', 'th', 'td',
                 'a', 'strong', 'em', 'b', 'i', 'br']

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'target'],
    'table': ['class'],
    'td': ['colspan', 'rowspan', 'class'],
    'th': ['colspan', 'rowspan', 'class'],
}

# class chỉ nhận đúng giá trị đã biết trước ({'specs-table','bg-cta','bg-specs'}),
# không nhận chuỗi tuỳ ý -> lọc thêm 1 bước sau bleach.
# href chỉ nhận scheme http/https/tel hoặc đúng domain zalo.me -> chặn
# javascript:, data:, vbscript:.
# CẤM TUYỆT ĐỐI: <script>, <style>, style="...", mọi thuộc tính on*
# (onclick, onerror, onload...), <iframe>, <object>, <embed>.
```

Vì phần HTML do code dựng (mục 6.1) không qua sanitizer, nó tự do dùng
`class="specs-table"`/`colspan`/`rowspan` mà không lo bị xén — đây là cách kỹ
thuật thoả yêu cầu "không làm mất" các thuộc tính đó mà không phải nới lỏng
whitelist cho phần AI (phần AI không có lý do chính đáng để tự chèn bảng, chỉ
viết văn xuôi `<p>`/`<h3>`/`<ul>` theo đúng `prompts.py::SYSTEM`).

## 7. Validator chống bịa — Hard Block, không hạ cấp xuống Warning

Sửa lại nguyên tắc của `kiem_tra_bia()`:

- Số có trong chính record hiện tại (`_kho_cua_dong(row)`) -> cho phép, không
  đổi so với code cũ.
- Số chỉ tồn tại ở record khác (kể cả cùng profile hay khác profile) ->
  **Hard Block**, không đăng bài. Đây là thay đổi so với v2.8 hiện tại — bản
  cũ có 2 mức `chan`/`canh_bao`, mức `canh_bao` (số có ở `kho_toan_bo` nhưng
  không có ở record hiện tại) cho phép vẫn đăng, chỉ ghi log. Bỏ mức
  `canh_bao` như một cơ chế "cho qua" — mọi số không thuộc chính record đó
  đều bị chặn cứng.
- `kho_toan_bo()` và kho theo từng profile vẫn giữ, nhưng đổi mục đích: chỉ
  dùng để ghi log, thống kê, điều tra lỗi — không còn nằm trên đường đi quyết
  định chặn/không chặn.

```python
def kiem_tra_bia(text, row, tat_ca):
    """Chỉ số có trong CHÍNH row này mới được phép. kho_toan_bo/kho theo
    profile chỉ dùng để log & điều tra, KHÔNG dùng trong logic chặn."""
    rieng = _kho_cua_dong(row)
    chan = []
    for so, dv in SO_DON_VI.findall(text or ''):
        t = chuan(so + dv)
        if t not in rieng:
            chan.append(f'{so}{dv}')
    for ma in MA_KT.findall(text or ''):
        t = chuan(ma)
        if t not in rieng:
            chan.append(ma)
    _log_dieu_tra_bia(chan, row, tat_ca)   # chỉ ghi log, không đổi kết quả chặn
    return sorted(set(chan))
```

`_kho_kien_thuc(row)` (kho kiến thức đã kiểm chứng CỦA CHÍNH dòng đó) vẫn
được cộng vào `rieng` — đây là kiến thức gán cho đúng record đó, không phải
"record khác", không vi phạm quyết định #5.

## 8. Schema builder

```python
def dung_schema(row, profile_id, outline_id):
    ct = row.get('content_type', 'product')
    if ct == 'service':
        return None
    cot_bang = effective_cot_bang(profile_id, outline_id)  # profile giao outline -> loại gia_list/ghi_chu VÀ field ngoài phạm vi outline
    schema = {
        '@context': 'https://schema.org', '@type': 'Product',
        'name': row.get('ten_goc'), 'sku': row.get('ma_goc'),
        'brand': {'@type': 'Brand', 'name': row.get('thuong_hieu')} if row.get('thuong_hieu') else None,
        'description': row.get('meta_description'),
        'additionalProperty': [
            {'@type': 'PropertyValue', 'name': nhan, 'value': row[k]}
            for k, nhan in cot_bang if row.get(k)
        ],
    }
    return {k: v for k, v in schema.items() if v}
```

Không nhánh nào tạo `offers`/`price` — `gia_list` không nằm trong `cot_bang`
của bất kỳ profile/outline nào nên không có đường nào để giá lọt vào schema,
không cần code né tránh riêng. Dùng `effective_cot_bang` thay vì
`PROFILES[profile_id]['cot_bang']` một mình để 1 dòng cap_dien route sang
`outline_phu_kien` không mang `vat_lieu_ruot` vào `additionalProperty` — đúng
quyết định #6 của vòng duyệt này.

## 9. Dispatcher import chung — không còn 2 pipeline độc lập

```python
def dispatcher_import(duong_dan, **kwargs):
    """Điểm vào DUY NHẤT cho mọi việc nhập Excel."""
    loai = nhan_dien_loai_nguon(duong_dan)
    if loai == 'rmu_legacy':
        return import_rmu_legacy(duong_dan, **kwargs)   # gọi nguyên xi nhap_excel() cũ
    elif loai == '4_profile':
        return import_4_profile(duong_dan, **kwargs)     # hàm mới, đọc theo header, mục 1
    else:
        raise RuntimeError('Không nhận diện được cấu trúc file, không import liều.')
```

`giao-dien.py` (UI) chỉ gọi `dispatcher_import()`, không gọi trực tiếp
`D.nhap_excel()` như hiện tại (dòng 451: `D.nhap_excel(p, danh_muc=...)`) —
điểm sửa UI cần rà khi code.

`nhan_dien_loai_nguon()` không dùng AI, chỉ đọc dòng đầu tiên: số thứ tự tăng
dần không tên cột -> `rmu_legacy`; dòng đầu là text khớp tập tên cột đã biết
của 1 trong 4 profile -> `4_profile`. Không khớp cả 2 -> dừng, không đoán.

## 10. Test plan

Không đọc từng dòng qua LLM, dùng pandas/dataframe theo batch. Sắp theo đúng
7 bước thứ tự code đã chốt, để `TEST-REPORT.md` khi giao có thể map thẳng
1-1 với từng bước.

**Bước 1 — normalize_cell + Profile/Outline Registry:**

1. Test `normalize_cell()`: `NaN`/`None` -> `''`; `15.0` (float) -> `'15'`
   (không có `.0` thừa); `37.5` -> `'37.5'` (giữ số thập phân thật); chuỗi có
   khoảng trắng đầu/cuối -> đã strip. Test bằng giá trị đọc thật từ pandas
   (`pd.read_excel` rồi lấy ô thật ra, không tự tạo `NaN` giả).
2. Test registry tĩnh (assert chạy lúc khởi động, không phải test riêng chạy
   tay): `gia_list` và `ghi_chu_ban_dau` không xuất hiện trong `cot_ai` hay
   `cot_bang` của bất kỳ `PROFILES[*]` nào; không xuất hiện trong `cot_ai`/
   `cot_bang` của bất kỳ `OUTLINES[*]` nào.
3. Test `effective_cot_ai`/`effective_cot_bang`: với `profile_id='cap_dien'`,
   `outline_id='outline_phu_kien'` -> kết quả KHÔNG chứa `vat_lieu_ruot`,
   `tiet_dien`, `cap_dien_ap`, dù `PROFILES['cap_dien']['cot_ai']` có các
   field này. Với `outline_id='outline_cap_dien'` -> kết quả CÓ đủ 3 field.

**Bước 2 — importer dispatcher + data_checksum/dataset_id/record_id:**

4. Test import số lượng — đúng 3.387/300/245/1.332/tổng 5.264, MASTER và 4
   file con phải giống hệt nhau.
5. Test `record_id` — không trùng trong 5.264 dòng; 17 cặp SKU trùng vẫn ra 2
   `record_id` riêng.
6. Test `data_checksum` MASTER = file con — import sheet `01_Cap_Dien` trong
   MASTER và import `01_Cap_Dien.xlsx` riêng -> `data_checksum` phải giống hệt
   dù `file_checksum` khác nhau; hệ thống không cảnh báo "dataset mới" khi
   chuyển từ nhập 4 file con sang nhập 1 file MASTER (hoặc ngược lại) nếu dữ
   liệu thực chất giống nhau.
7. Test cảnh báo dataset đổi thật — sửa 1 ô dữ liệu rồi import lại (giữ cấu
   trúc cột) -> `data_checksum` đổi -> cảnh báo "dataset đã đổi", liệt kê số
   dòng khác, chờ xác nhận. Đổi tên 1 cột rồi import lại -> cảnh báo mạnh
   hơn, chặn tới khi xác nhận tay.
8. Test tạo `dataset_id` mới không đụng dataset cũ — xác nhận dataset mới sau
   test 7 -> record của `dataset_id` cũ giữ nguyên `wp_id`/`trang_thai`/URL,
   không bị ghi đè; record mới thuộc `dataset_id` mới dù `record_id` (tính
   theo `profile_id::source_sheet::source_row::sku`) trùng với record cũ.
9. Test khoá lưu trữ `(dataset_id, record_id)` — dashboard, bảng ghi WP Post
   ID phải dùng đủ cặp khoá này; test 2 record cùng `record_id` nhưng khác
   `dataset_id` ra 2 dòng riêng, không ghi đè nhau.

**Bước 3 — validator và regex:**

10. Unit test regex kVA/kV, 300/500V, mm² đơn lõi, Cu-Al — dùng đúng bộ
    snapshot **33 tên thật** ở `DATA-AUDIT-4-PROFILES.md` mục 8 (A=9, B=8,
    C=6, D=10), gồm cả case dương lẫn case âm (không regression case đã
    đúng: `2x0.5`, `2X38`, nhóm đo lường 08, "Giá treo MBT").
11. Test routing outline_id — 185 dòng cap_dien (`ghi_chu_ban_dau != "Cáp
    điện"`, kể cả NaN) ra `outline_id = outline_phu_kien`; 14 dòng vỏ tủ ra
    `outline_vo_tu`; 7 dòng "Giá treo MBT" trong nhóm 05 ra `outline_phu_kien`.
    Đếm lại đúng 185/14/7, không lệch so với DATA-AUDIT.

**Bước 4 — prompt/bảng/schema/sanitize:**

12. Test Giá List không lọt vào `cot_ai`/prompt/HTML/schema — assert tĩnh
    (đã ở bước 1, mục 2) cộng thêm assert động: chuỗi giá trị Giá List của
    mọi record không xuất hiện trong prompt gửi AI và trong HTML bài đã ghép.
13. Test dịch vụ không dùng Product Schema — 41 record nhóm "09. Thí Nghiệm &
    Kiểm Định" -> `dung_schema()` trả `None`.
14. Test `effective_cot_bang` áp trong `dung_schema`/`bang_thong_so` thật —
    1 record cap_dien route `outline_phu_kien` -> HTML bảng thông số và JSON
    schema đều KHÔNG có nhãn "Vật liệu ruột"/"Tiết diện"/"Cấp điện áp".
15. Test `sanitize_html` — input chứa `<script>`, `onclick=`, `style=`,
    `href="javascript:..."` -> bị xén hết; bảng do code dựng có
    `class="specs-table"` + `colspan` (không qua sanitizer) -> giữ nguyên
    100%, test riêng khẳng định 2 luồng không lẫn vào nhau.
16. Test Hard Block chống bịa — record A có "22kV", record B không có nhưng
    "22kV" có trong `kho_toan_bo` -> bài của record B chứa "22kV" phải bị
    Hard Block, không phải chỉ cảnh báo.

**Bước 5 — dashboard và WP mapping theo record_id:**

17. Test dashboard không ghi đè — 2 record cùng SKU khác `record_id` ra 2
    dòng dashboard riêng (đã một phần ở test 9, thêm test riêng cho hiển thị
    dashboard, không chỉ tầng lưu trữ).

**Bước 6-7 — chạy toàn bộ + 20 record đại diện:**

18. Chạy toàn bộ import 5.264 record, xác nhận không lỗi, không crash, thời
    gian chạy hợp lý (ghi số liệu cụ thể vào TEST-REPORT).
19. Test nội dung 20 record đại diện (5 mỗi profile: đầy đủ + thiếu thông số
    + SKU trùng + tên bất thường + rìa/routing khác mặc định như 1 dòng phụ
    kiện lẫn cap_dien hoặc 1 dòng "Giá treo MBT") — chạy chế độ 'thu' (giả
    lập), không chạy Gemini thật ở vòng code này.

## 11. Việc KHÔNG làm trong vòng này

- Không xây nhận diện ngành hàng bằng AI/độ tin cậy % — 4 profile lấy thẳng
  từ tên sheet/file qua dispatcher, không có bước "đoán".
- Không sửa logic bên trong `import_rmu_legacy()` — đóng gói nguyên xi.
- Không tạo profile thứ 5 cho phụ kiện lẫn trong cap_dien hay vỏ tủ trong
  tu_dong_cat — dùng `routing_outline` để đổi outline_id, giữ nguyên
  profile_id.
- Không làm outline sâu theo hãng/series trong từng profile.
- Không sửa pipeline ảnh/category/tag WordPress.

## 12. Tóm tắt các điểm đã chốt

### Vòng duyệt 1

| # | Chủ đề | Quyết định cuối |
|---|---|---|
| 1 | Phụ kiện lẫn trong cap_dien (185 dòng) | `profile_id` giữ `cap_dien`, chỉ đổi `outline_id = outline_phu_kien` qua routing theo `ghi_chu_ban_dau` |
| 2 | Kho chống bịa | Chỉ số trong chính record mới được phép; số ở record khác = Hard Block; kho toàn hệ/profile chỉ dùng log & điều tra |
| 3 | 14 dòng vỏ tủ + 7 dòng giá treo MBT | Giữ nguyên `profile_id`, route `outline_id` riêng, field thiếu thì bỏ qua |
| 4 | Ghi Chú Ban Đầu | Chỉ nằm trong `cot_noi_bo`, không có đường vào `cot_ai`/`cot_bang` |
| 5 | sanitize_html | Whitelist thẻ/thuộc tính cụ thể (mục 6.2), giữ `class="specs-table"`/`colspan`/`rowspan` bằng cách KHÔNG chạy sanitizer lên HTML code tự dựng |
| 6 | Unit test regex | Dùng đúng bộ snapshot tên sản phẩm thật trong DATA-AUDIT mục 8, không tự nghĩ case |

### Vòng duyệt 2 — đã sửa trực tiếp vào tài liệu, KHÔNG còn là việc tồn đọng

| # | Chủ đề | Quyết định cuối |
|---|---|---|
| 1 | Số 70 dòng phụ kiện cap_dien | Sửa thành **185 dòng** ở mọi chỗ nhắc tới (DATA-AUDIT mục 6.1, 7) — tiêu chí đếm: `ghi_chu_ban_dau != "Cáp điện"`, tính cả NaN |
| 2 | Số lượng snapshot unit test | Sửa thành **33 tên** (A=9, B=8, C=6, D=10) ở mọi chỗ nhắc "29 tên" trong cả 2 file |
| 3 | Căn cứ so dataset | Thêm `data_checksum` (hash dữ liệu đã normalize theo sheet/profile) song song `file_checksum` (audit file vật lý) — mục 3.1. MASTER và file con có `data_checksum` giống nhau = cùng dataset dù `file_checksum` khác |
| 4 | Khoá lưu trữ | `(dataset_id, record_id)`, không phải `record_id` một mình — mục 3.3. Dataset mới -> `dataset_id` mới, không ghi đè URL/WP Post ID/trạng thái dataset cũ — mục 3.2 |
| 5 | normalize_cell | Thêm mục 1.1 — chuẩn hoá `NaN/None -> ''`, số -> chuỗi chuẩn, text -> strip, chạy 1 lần lúc import; mọi nơi khác (prompt/bảng/schema/validator) chỉ đọc giá trị đã chuẩn hoá, không tự `.strip()` lại trên dữ liệu pandas thô |
| 6 | Outline Registry | Thêm mục 2.1 — `effective_cot_ai`/`effective_cot_bang` = giao giữa field profile cho phép và field outline cho phép; cap_dien route `outline_phu_kien` không mang `vat_lieu_ruot` vào prompt/bảng/schema dù profile gốc có field đó |

Không còn câu hỏi mở. Kiến trúc đã duyệt để bắt đầu code theo đúng thứ tự 7
bước ở mục 10 (test plan) — phạm vi cố định theo mục 11, không mở rộng.
