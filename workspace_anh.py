# -*- coding: utf-8 -*-
"""WORKSPACE ẢNH — Ver 3.7, đợt 1.

VÌ SAO CÓ FILE NÀY
------------------
Cách làm cũ (`anh_san_pham.py`) đoán SKU từ tên file và đường dẫn. Đo trên
kho thật: ghép sai nhiều, phần lớn ra generic — không dùng được. Vấn đề
không nằm ở thuật toán đoán, mà ở chỗ ĐOÁN LÀ SAI HƯỚNG: kho ảnh công ty
không mang đủ thông tin để suy ra SKU.

Đổi hướng: mỗi bài có một THƯ MỤC RIÊNG, và thư mục đó tự khai mình thuộc
bài nào qua `meta.json`. Người dùng ném ảnh vào bằng mắt — việc mà mắt làm
trong 3 giây còn AI làm sai trong 3 giây. Tool lo phần cơ khí phía sau:
WebP, đổi tên, alt, upload, gắn vào bài.

NGUYÊN TẮC
----------
* `meta.json` là NGUỒN SỰ THẬT DUY NHẤT. Tool KHÔNG đọc tên thư mục để suy
  ra bài — người dùng rename thư mục thoải mái, ảnh không mồ côi.
* Số thứ tự trong tên thư mục lấy từ SỐ DÒNG MASTER, chỉ để người nhìn
  Explorer cho dễ. Code không được phụ thuộc vào nó.
* KHÔNG gọi AI. Workflow phải chạy 100% kể cả khi không có AI.
"""

import hashlib
import json
import os
import re
import shutil
import unicodedata
from pathlib import Path
from chuan_hoa import bo_dau_giu_hoa as _bo_dau   # Ver 5.7 — gom 9 bản _bo_dau về 1 nguồn (xem chuan_hoa.py)

TEN_META = 'meta.json'
THU_MUC_GOC_ANH = '_goc'

# Trạng thái từng ảnh trong meta.json
MOI = 'moi'          # đã chọn, chưa đăng
DA_DANG = 'da_dang'  # đã upload lên WP, hash khớp
LECH = 'lech'        # file trên đĩa đã đổi so với lúc upload -> cần đăng lại

# ---------------------------------------------------------------- vai trò ô ảnh
# CHỈ khai cho profile đã hiểu rõ. Ba profile còn lại để TRỐNG có chủ đích:
# đóng đinh 5 vai trò của máy biến áp cho cáp/tủ/phụ kiện là lặp lại đúng
# lỗi bep_truong._TRUC bản đầu — khai bừa rồi báo như sự thật.
VAI_TRO = {
    'may_bien_ap_do_luong': [
        ('hero', 'Ảnh đại diện',
         'Toàn cảnh máy, chụp chính diện hoặc chếch 3/4, nền gọn.'),
        ('bien_may', 'Biển máy (nameplate)',
         'Chụp thẳng tấm nhãn kim loại, đủ sáng, đọc rõ chữ. '
         'Chứng minh thông số là số thật, không phải chép catalogue.'),
        ('can_canh', 'Cận cảnh bộ phận',
         'Sứ cách điện, cánh tản nhiệt, bộ chuyển nấc hoặc van lấy mẫu dầu.'),
        ('lap_dat', 'Lắp đặt / toàn cảnh',
         'Máy đã lắp tại trạm, có bối cảnh công trình.'),
        ('giao_hang', 'Giao hàng / vận chuyển',
         'Máy trên xe cẩu, đang hạ xuống bệ. Có công nhân càng tốt.'),
    ],
}
VAI_TRO_MAC_DINH = []


def vai_tro_cua(profile_id):
    """Bộ ô ảnh của profile. Chưa khai -> rỗng, KHÔNG đoán."""
    return VAI_TRO.get(profile_id, VAI_TRO_MAC_DINH)


def ma_vai_tro(profile_id):
    return [v[0] for v in vai_tro_cua(profile_id)]


# ---------------------------------------------------------------- tiện ích
def ten_an_toan(s, dai=60):
    """Tên thư mục an toàn cho Windows: bỏ dấu, bỏ ký tự cấm, gọn khoảng trắng."""
    s = _bo_dau(s)
    s = re.sub(r'[<>:"/\\|?*]', '', s)
    s = re.sub(r'\s+', ' ', s).strip(' .')
    return s[:dai].strip(' .')


def ho_san_pham(row):
    """Trả định danh HỌ ẢNH cho máy biến áp thật.

    Họ được dựng CHỈ từ dữ liệu record: thương hiệu + dầu/khô + số pha +
    loại lõi. Nếu record không ghi số pha/lõi thì giữ trạng thái ``khong-ro``
    thay vì đoán. Record không phải ``outline_may_bien_ap`` trả None để vỏ,
    giá treo và thiết bị đo lường không vô tình dùng ảnh máy biến áp.
    """
    row = row or {}
    outline = str(row.get('outline_id') or '').strip()
    ten = str(row.get('ten_goc') or '').strip()
    ten_thuong = ten.casefold()
    if outline:
        if outline != 'outline_may_bien_ap':
            return None
    else:
        # Hỗ trợ record test/chưa route, nhưng vẫn chặn rõ vỏ/giá treo/MOF.
        if 'máy biến áp' not in ten_thuong or ten_thuong.startswith(('vỏ ', 'giá treo')):
            return None

    hang = str(row.get('thuong_hieu') or '').strip()
    if not hang:
        return None
    if 'khô' in ten_thuong:
        loai, nhan_loai = 'kho', 'khô'
    elif 'dầu' in ten_thuong:
        loai, nhan_loai = 'dau', 'dầu'
    else:
        return None

    m = re.search(r'\b([13])\s*pha\b|\b([13])p\b', ten, re.IGNORECASE)
    pha = (m.group(1) or m.group(2)) if m else ''

    dong = row.get('thong_so_dong') or {}
    loi = str(dong.get('Loại lõi (trích từ tên)') or '').strip()
    if not loi:
        if 'amorphous' in ten_thuong:
            loi = 'Amorphous'
        elif 'silic' in ten_thuong:
            loi = 'Silic'
    if loi.casefold() == 'silic':
        loi = 'Silic'
    elif loi.casefold() == 'amorphous':
        loi = 'Amorphous'

    pha_key = f'{pha}-pha' if pha else 'khong-ro-pha'
    loi_key = loi if loi else 'khong-ro-loi'
    khoa = '__'.join([
        ten_an_toan(hang, 40) or 'khong-ro-hang', loai, pha_key,
        ten_an_toan(loi_key, 40) or 'khong-ro-loi',
    ])
    nhan = f'{hang} · {nhan_loai} · {pha + " pha" if pha else "không ghi pha"} · {loi or "không ghi lõi"}'
    return {'key': khoa, 'nhan': nhan, 'hang': hang, 'loai': loai,
            'so_pha': pha, 'loi': loi}


def thu_muc_ho(goc, sheet, row):
    """Đường dẫn ``<gốc>/<sheet>/_HO/<family-key>``; None nếu không có họ."""
    ho = ho_san_pham(row)
    if not ho:
        return None
    return Path(goc) / ten_an_toan(sheet, 80) / '_HO' / ho['key']


def tao_workspace_ho(goc, sheet, row):
    """Tạo workspace 5 ô cho họ sản phẩm. Không đụng workspace từng SKU."""
    ho = ho_san_pham(row)
    if not ho:
        raise ValueError('Record không xác định được họ ảnh máy biến áp.')
    tm = thu_muc_ho(goc, sheet, row)
    tm.mkdir(parents=True, exist_ok=True)
    meta = doc_meta(tm) or {}
    meta.update({
        'loai_workspace': 'ho',
        'family_key': ho['key'],
        'family_label': ho['nhan'],
        'profile': row.get('profile_id') or 'may_bien_ap_do_luong',
        'sheet': sheet,
        'title': ho['nhan'],
        'slug': 'ho-' + ten_an_toan(ho['key'], 100).replace(' ', '-').lower(),
    })
    meta.setdefault('anh', [])
    ghi_meta(tm, meta)
    return tm


def tim_workspace_ho(goc, sheet, row):
    tm = thu_muc_ho(goc, sheet, row)
    return tm if tm and tm.is_dir() and doc_meta(tm) else None


def anh_hieu_luc(goc, sheet, row, thu_muc_rieng=None):
    """Ghép ảnh theo vai trò: ảnh RIÊNG thắng, họ chỉ lấp ô còn trống.

    ``nguon`` trả đúng ba trạng thái cho bảng UI: ``rieng`` / ``ho`` /
    ``trong``. Nếu có ít nhất một ô riêng thì nguồn của bài được coi là
    ``rieng`` dù các ô còn thiếu có thể được họ lấp tự động.
    """
    ds = ma_vai_tro(row.get('profile_id', ''))
    rieng = quet(thu_muc_rieng) if thu_muc_rieng and Path(thu_muc_rieng).is_dir() else {'o': {}}
    tm_ho = tim_workspace_ho(goc, sheet, row) if goc else None
    ho = quet(tm_ho) if tm_ho else {'o': {}}
    o, nguon_o = {}, {}
    co_rieng = False
    co_ho = False
    for vt in ds:
        a_r = rieng.get('o', {}).get(vt)
        a_h = ho.get('o', {}).get(vt)
        if a_r:
            o[vt], nguon_o[vt], co_rieng = a_r, 'rieng', True
        elif a_h:
            o[vt], nguon_o[vt], co_ho = a_h, 'ho', True
        else:
            o[vt], nguon_o[vt] = None, 'trong'
    nguon = 'rieng' if co_rieng else ('ho' if co_ho else 'trong')
    return {'o': o, 'nguon_o': nguon_o, 'nguon': nguon,
            'thu_muc_ho': tm_ho, 'thu_muc_rieng': thu_muc_rieng}


def hash_file(duong_dan):
    """SHA-256 rút gọn 16 ký tự. Dùng để biết file đã bị thay chưa."""
    h = hashlib.sha256()
    with open(duong_dan, 'rb') as fh:
        for khoi in iter(lambda: fh.read(1 << 20), b''):
            h.update(khoi)
    return h.hexdigest()[:16]


DUOI_ANH = {'.jpg', '.jpeg', '.jfif', '.png', '.webp', '.heic', '.bmp', '.avif', '.gif', '.tif', '.tiff'}


def la_anh(p):
    return Path(p).suffix.lower() in DUOI_ANH


# ---------------------------------------------------------------- thư mục
def ten_thu_muc(so_dong, ten_bai, sku):
    """`018 - May bien ap dau MBT 15kVA 1 pha - MBT1P15A2608`

    Người đọc Explorer là ưu tiên số một: số thứ tự để sắp xếp, tên để nhận
    ra bài, SKU cuối làm khoá. Nhưng code KHÔNG parse tên này — nó đọc
    meta.json. Rename thoải mái.
    """
    return f'{int(so_dong):03d} - {ten_an_toan(ten_bai)} - {sku}'


_CHI_MUC_WORKSPACE = {}


def _khoa_chi_muc(goc, sheet):
    return (str(Path(goc).resolve()), ten_an_toan(sheet, 80))


def _lap_chi_muc_workspace(goc, sheet, lam_moi=False):
    """Quét meta.json MỘT LẦN cho cả sheet rồi cache sku -> Path."""
    khoa = _khoa_chi_muc(goc, sheet)
    if not lam_moi and khoa in _CHI_MUC_WORKSPACE:
        return _CHI_MUC_WORKSPACE[khoa]
    thu_muc_sheet = Path(goc) / ten_an_toan(sheet, 80)
    chi_muc = {}
    if thu_muc_sheet.is_dir():
        for con in thu_muc_sheet.iterdir():
            if not con.is_dir():
                continue
            m = doc_meta(con)
            sku = str((m or {}).get('sku', '')).strip()
            if sku:
                chi_muc[sku] = con
    _CHI_MUC_WORKSPACE[khoa] = chi_muc
    return chi_muc


def tao_workspace(goc, sheet, so_dong, row, wp_post_id=None, title=None, slug=None):
    """Tạo thư mục cho 1 bài + ghi meta.json. Đã có thì cập nhật meta, KHÔNG
    tạo trùng và KHÔNG đụng ảnh bên trong.

    Trả Path thư mục.
    """
    goc = Path(goc)
    sku = str(row.get('publish_sku') or row.get('ma_goc') or '').strip()
    if not sku:
        raise ValueError('Record không có SKU — không tạo được thư mục.')

    cu = tim_workspace(goc, sheet, sku)
    if cu:
        tm = cu
    else:
        tm = goc / ten_an_toan(sheet, 80) / ten_thu_muc(so_dong, title or row.get('ten_goc', ''), sku)
        tm.mkdir(parents=True, exist_ok=True)
        _lap_chi_muc_workspace(goc, sheet)[sku] = tm

    meta = doc_meta(tm) or {}
    meta.update({
        'sku': sku,
        'record_id': row.get('record_id', ''),
        'profile': row.get('profile_id', ''),
        'sheet': sheet,
        'so_dong': so_dong,
        'title': title or row.get('ten_goc', ''),
        'slug': slug or meta.get('slug', ''),
    })
    if wp_post_id:
        meta['wp_post_id'] = wp_post_id
    meta.setdefault('anh', [])
    ghi_meta(tm, meta)
    return tm


def tim_workspace(goc, sheet, sku):
    """Tìm workspace bằng index SKU dựng một lần cho mỗi sheet.

    Nếu folder trong cache bị rename/xoá bên ngoài, rebuild index một lần.
    """
    sku = str(sku).strip()
    if not sku:
        return None
    chi_muc = _lap_chi_muc_workspace(goc, sheet)
    tm = chi_muc.get(sku)
    if tm and tm.is_dir():
        return tm
    if tm:
        chi_muc = _lap_chi_muc_workspace(goc, sheet, lam_moi=True)
        return chi_muc.get(sku)
    return None


# ---------------------------------------------------------------- meta.json
def doc_meta(thu_muc):
    p = Path(thu_muc) / TEN_META
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        # Ver 4.2 audit debt: file hỏng khác hoàn toàn file không tồn tại.
        # Giữ nguyên dấu vết bằng bản backup rồi fail loud, không âm thầm dựng meta mới.
        import time
        backup = p.with_name(f'{p.name}.corrupt-{time.strftime("%Y%m%d-%H%M%S")}')
        try:
            shutil.copy2(p, backup)
        except OSError:
            backup = None
        raise ValueError(f'meta.json hỏng: {p}' + (f' — đã backup {backup.name}' if backup else '')) from e


def ghi_meta(thu_muc, meta):
    p = Path(thu_muc) / TEN_META
    tam = p.with_suffix('.json.tam')
    tam.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    tam.replace(p)   # atomic visibility; không tuyên bố durability khi mất điện


# ---------------------------------------------------------------- quét ảnh
def quet(thu_muc):
    """Đọc thực trạng thư mục, đối chiếu với meta.json.

    Trả dict:
      {'meta': {...},
       'o': {vai_tro: {...ảnh...} | None},
       'chua_gan': [tên file chưa được gán ô nào],
       'thieu': [vai trò còn trống]}

    Tự phát hiện trạng thái `lech`: file trên đĩa đổi so với lúc upload.
    Không có trạng thái này thì người dùng thay ảnh xong không bao giờ biết
    bài trên web vẫn đang dùng ảnh cũ.
    """
    thu_muc = Path(thu_muc)
    meta = doc_meta(thu_muc) or {'anh': []}
    ds_vai_tro = ma_vai_tro(meta.get('profile', ''))

    tren_dia = {p.name for p in thu_muc.iterdir() if p.is_file() and la_anh(p)}
    o = {v: None for v in ds_vai_tro}
    da_dung = set()

    for a in meta.get('anh', []):
        ten = a.get('ten_tren_dia') or a.get('ten_goc')
        if not ten or ten not in tren_dia:
            continue   # file đã bị xoá tay -> bỏ khỏi ô, không báo lỗi
        p = thu_muc / ten
        try:
            h_moi = hash_file(p)
        except OSError:
            continue
        b = dict(a)
        b['ten_tren_dia'] = ten
        b['duong_dan'] = str(p)
        if b.get('trang_thai') == DA_DANG and b.get('hash') != h_moi:
            b['trang_thai'] = LECH
        b['hash_hien_tai'] = h_moi
        vt = b.get('vai_tro')
        if vt in o:
            o[vt] = b
        da_dung.add(ten)

    chua_gan = sorted(tren_dia - da_dung)
    return {'meta': meta, 'o': o, 'chua_gan': chua_gan,
            'thieu': [v for v in ds_vai_tro if not o.get(v)]}


def gan_anh(thu_muc, duong_dan_nguon, vai_tro):
    """Chép ảnh vào thư mục bài và gán vào một ô.

    Người dùng ném `IMG_3827.jpg` hay `zalo-abc.jpg` vào đều được — KHÔNG
    bắt đổi tên tay. Tool đổi tên ở khâu đăng, không đổi lúc này (giữ tên
    gốc để đối chiếu khi cần).

    Ô đã có ảnh -> thay. Ảnh cũ vẫn nằm trong thư mục, không xoá.
    """
    thu_muc = Path(thu_muc)
    nguon = Path(duong_dan_nguon)
    if not nguon.is_file():
        raise FileNotFoundError(duong_dan_nguon)
    if not la_anh(nguon):
        raise ValueError(f'Không phải file ảnh: {nguon.name}')

    dich = thu_muc / nguon.name
    if nguon.resolve() != dich.resolve():
        i = 1
        while dich.exists() and hash_file(dich) != hash_file(nguon):
            dich = thu_muc / f'{nguon.stem}_{i}{nguon.suffix}'
            i += 1
        if not dich.exists():
            shutil.copy2(nguon, dich)

    meta = doc_meta(thu_muc) or {'anh': []}
    meta.setdefault('anh', [])
    # bỏ ảnh cũ khỏi ô này, và bỏ ảnh này khỏi ô khác (1 ảnh 1 vai trò)
    meta['anh'] = [a for a in meta['anh']
                   if a.get('vai_tro') != vai_tro
                   and (a.get('ten_tren_dia') or a.get('ten_goc')) != dich.name]
    h = hash_file(dich)
    meta['anh'].append({
        'ten_goc': nguon.name,
        'ten_tren_dia': dich.name,
        'vai_tro': vai_tro,
        'hash': h,
        # `hash_goc` KHÔNG BAO GIỜ đổi sau khi xử lý, còn `hash` thì đổi
        # sang bản .webp. Tách hai trường vì chúng trả lời hai câu khác
        # nhau: `hash` = "file trên đĩa có bị thay không" (phát hiện lệch),
        # `hash_goc` = "tấm ảnh này có đang dùng ở bài khác không".
        'hash_goc': h,
        'trang_thai': MOI,
        'wp_media_id': None,
        'ten_sau_doi': '',
    })
    ghi_meta(thu_muc, meta)
    return dich


def doi_o(thu_muc, vai_tro_a, vai_tro_b):
    """Đổi ảnh giữa hai ô, không phải chọn lại từ đầu."""
    meta = doc_meta(thu_muc) or {'anh': []}
    for a in meta.get('anh', []):
        if a.get('vai_tro') == vai_tro_a:
            a['vai_tro'] = '__tam__'
    for a in meta.get('anh', []):
        if a.get('vai_tro') == vai_tro_b:
            a['vai_tro'] = vai_tro_a
    for a in meta.get('anh', []):
        if a.get('vai_tro') == '__tam__':
            a['vai_tro'] = vai_tro_b
    ghi_meta(thu_muc, meta)


def bo_anh(thu_muc, vai_tro):
    """Gỡ ảnh khỏi ô. KHÔNG xoá file — người dùng tự xoá trong Explorer nếu
    muốn. Tool không được tự xoá dữ liệu của người dùng."""
    meta = doc_meta(thu_muc) or {'anh': []}
    meta['anh'] = [a for a in meta.get('anh', []) if a.get('vai_tro') != vai_tro]
    ghi_meta(thu_muc, meta)


def chuyen_vao_goc(thu_muc, ten_file):
    """Chuyển ảnh gốc vào `_goc/` sau khi đã xử lý. Không xoá."""
    thu_muc = Path(thu_muc)
    goc = thu_muc / THU_MUC_GOC_ANH
    goc.mkdir(exist_ok=True)
    nguon = thu_muc / ten_file
    if nguon.is_file():
        dich = goc / ten_file
        if dich.exists():
            dich = goc / f'{nguon.stem}_{hash_file(nguon)}{nguon.suffix}'
        shutil.move(str(nguon), str(dich))
        return dich
    return None


# ---------------------------------------------------------------- trạng thái bài
def trang_thai_bai(thu_muc):
    """Một dòng trạng thái cho danh sách bài: 'CHƯA CÓ ẢNH' | '3/5' |
    '5/5 SẴN SÀNG' | 'LỆCH 2' | 'Đã lên Media'."""
    if not thu_muc or not Path(thu_muc).is_dir():
        return 'CHƯA CÓ THƯ MỤC', 0, 0
    kq = quet(thu_muc)
    ds = ma_vai_tro(kq['meta'].get('profile', ''))
    co = [v for v in ds if kq['o'].get(v)]
    lech = [v for v in co if kq['o'][v].get('trang_thai') == LECH]
    da_dang = [v for v in co if kq['o'][v].get('trang_thai') == DA_DANG]
    if lech:
        return f'LỆCH {len(lech)}', len(co), len(ds)
    if not co:
        return 'CHƯA CÓ ẢNH', 0, len(ds)
    if len(da_dang) == len(co):
        return f'Đã lên Media {len(co)}/{len(ds)}', len(co), len(ds)
    return f'{len(co)}/{len(ds)}', len(co), len(ds)


def dem_dung_chung(goc, sheet, hash_anh):
    """Đếm số bài KHÁC đang dùng cùng tấm ảnh này (so theo `hash_goc`).

    Không chặn tái sử dụng — chỉ cho biết mức độ. Kho ảnh công ty vốn ít,
    một tấm dùng cho vài bài là chuyện sẽ xảy ra; chặn thì người dùng bí,
    giấu thì người dùng không biết mình đang loãng tài sản hình ảnh.
    """
    thu_muc_sheet = Path(goc) / ten_an_toan(sheet, 80)
    if not thu_muc_sheet.is_dir():
        return 0
    n = 0
    for con in thu_muc_sheet.iterdir():
        if not con.is_dir():
            continue
        m = doc_meta(con)
        # Audit 3.7 mục 36: metadata cũ không được tính reuse nếu file vật lý
        # đã bị xoá. Hash gốc vẫn là identity tái sử dụng, path chỉ xác nhận
        # asset còn tồn tại trong workspace.
        if m and any((a.get('hash_goc') or a.get('hash')) == hash_anh
                     and (con / str(a.get('ten_tren_dia') or a.get('ten_goc') or '')).is_file()
                     for a in m.get('anh', [])):
            n += 1
    return max(0, n - 1)


def _delivery_site(anh, ma_site):
    if not anh or not ma_site:
        return {}
    return (anh.get('delivery_by_site') or {}).get(str(ma_site)) or {}


def _da_gan_post(anh, ma_site, wp_post_id):
    if not wp_post_id:
        return False
    delivery = _delivery_site(anh, ma_site)
    ids = {str(x) for x in (delivery.get('attached_wp_post_ids') or []) if x not in (None, '')}
    return str(wp_post_id) in ids


def danh_dau_da_gan_vao_bai(goc, sheet, row, thu_muc_rieng, ma_site, wp_post_id, danh_sach_anh):
    """Đánh dấu delivery Media đã thật sự được gắn vào đúng bài WordPress.

    Với ảnh HỌ, một media có thể được dùng cho nhiều SKU nên lưu danh sách
    ``attached_wp_post_ids`` theo site, không dùng một cờ boolean toàn cục.
    Thay/re-upload ảnh sẽ tạo delivery mới và tự xoá dấu gắn cũ.
    """
    if not ma_site or not wp_post_id:
        return 0
    h = anh_hieu_luc(goc, sheet, row, thu_muc_rieng)
    tm_ho = h.get('thu_muc_ho')
    theo_tm = {}
    for a in danh_sach_anh or []:
        vt = a.get('vai_tro')
        nguon = a.get('nguon')
        tm = thu_muc_rieng if nguon == 'rieng' else (tm_ho if nguon == 'ho' else None)
        if vt and tm:
            theo_tm.setdefault(str(tm), set()).add(vt)
    da = 0
    for tm_s, roles in theo_tm.items():
        tm = Path(tm_s)
        meta = doc_meta(tm) or {}
        doi = False
        for m in meta.get('anh', []):
            if m.get('vai_tro') not in roles:
                continue
            delivery = m.setdefault('delivery_by_site', {}).get(str(ma_site))
            if not isinstance(delivery, dict) or not delivery.get('wp_media_id'):
                continue
            ids = [str(x) for x in (delivery.get('attached_wp_post_ids') or []) if x not in (None, '')]
            sid = str(wp_post_id)
            if sid not in ids:
                ids.append(sid)
                delivery['attached_wp_post_ids'] = ids
                doi = True
            da += 1
        if doi:
            if thu_muc_rieng and tm == Path(thu_muc_rieng):
                meta['wp_post_id'] = wp_post_id
            ghi_meta(tm, meta)
    return da


def vo_hieu_delivery_media(goc, sheet, row, thu_muc_rieng, ma_site, danh_sach_anh):
    """4.4.1.3 — WordPress báo media ID stale thì xoá CHỈ delivery site đó.

    Không xoá ảnh local, không xoá delivery của site khác. Lần sau pipeline
    thấy thiếu delivery_by_site[site] sẽ upload lại đúng slot.
    """
    if not ma_site:
        return 0
    h = anh_hieu_luc(goc, sheet, row, thu_muc_rieng)
    tm_ho = h.get('thu_muc_ho')
    theo_tm = {}
    for a in danh_sach_anh or []:
        vt = a.get('vai_tro')
        nguon = a.get('nguon')
        tm = thu_muc_rieng if nguon == 'rieng' else (tm_ho if nguon == 'ho' else None)
        if vt and tm:
            theo_tm.setdefault(str(tm), {}).setdefault(vt, set()).add(str(a.get('wp_media_id')))
    n = 0
    for tm_s, role_ids in theo_tm.items():
        tm = Path(tm_s)
        meta = doc_meta(tm) or {}
        doi = False
        for m in meta.get('anh', []):
            vt = m.get('vai_tro')
            if vt not in role_ids:
                continue
            by_site = m.get('delivery_by_site') or {}
            d = by_site.get(str(ma_site))
            if not isinstance(d, dict):
                continue
            if str(d.get('wp_media_id')) not in role_ids[vt]:
                continue
            by_site.pop(str(ma_site), None)
            m['delivery_by_site'] = by_site
            # Top-level legacy fields chỉ xoá nếu đang trỏ đúng ID stale;
            # site khác vẫn có state riêng trong delivery_by_site.
            if str(m.get('wp_media_id')) in role_ids[vt]:
                m['wp_media_id'] = None
                m['media_url'] = ''
            doi = True
            n += 1
        if doi:
            ghi_meta(tm, meta)
    return n


def trang_thai_hieu_luc(goc, sheet, row, thu_muc_rieng=None, ma_site=None, wp_post_id=None):
    """Trạng thái ảnh mà BÀI THỰC SỰ sẽ nhận sau fallback riêng -> họ.

    Ver 4.4.1.1: tách rõ ``đã lên Media`` và ``đã gắn vào bài``.
    ``ma_site``/``wp_post_id`` là optional để caller cũ không vỡ.
    """
    h = anh_hieu_luc(goc, sheet, row, thu_muc_rieng)
    ds = ma_vai_tro(row.get('profile_id', ''))
    co = [v for v in ds if h['o'].get(v)]
    lech = [v for v in co if h['o'][v].get('trang_thai') == LECH]
    da_dang_legacy = [v for v in co if h['o'][v].get('trang_thai') == DA_DANG]
    media = []
    gan_bai = []
    if ma_site:
        for v in co:
            a = h['o'][v]
            d = _delivery_site(a, ma_site)
            if d.get('wp_media_id') and d.get('hash') == a.get('hash_hien_tai'):
                media.append(v)
                if _da_gan_post(a, ma_site, wp_post_id):
                    gan_bai.append(v)
    if lech:
        tt = f'LỆCH {len(lech)}'
    elif not co:
        tt = 'CHƯA CÓ ẢNH'
    elif ma_site and wp_post_id and gan_bai:
        # 4.4.1.3: nói thật cả trạng thái partial. 5 file local nhưng chỉ 4
        # attach không được phép hiện trơ trọi "5/5" như thể đã hoàn tất.
        tt = f'Đã gắn vào bài {len(gan_bai)}/{len(ds)}'
    elif ma_site and media:
        tt = f'Đã lên Media {len(media)}/{len(ds)}'
    elif not ma_site and len(da_dang_legacy) == len(co):
        tt = f'Đã lên Media {len(co)}/{len(ds)}'
    else:
        tt = f'{len(co)}/{len(ds)}'
    return tt, len(co), len(ds), h.get('nguon', 'trong')
