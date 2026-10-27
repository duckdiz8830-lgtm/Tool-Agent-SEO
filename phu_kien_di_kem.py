# -*- coding: utf-8 -*-
"""PHỤ KIỆN ĐI KÈM — Ver 3.6.

VÌ SAO CÓ FILE NÀY
------------------
24 vỏ mạ kẽm và 7 giá treo trong sheet máy biến áp là phụ kiện của chính
những cái máy đang bán trên site. Trước đây mỗi trang đứng một mình: trang
vỏ chỉ có 4 dòng thông số rồi hết (mỏng), trang máy thì không nhắc gì tới
vỏ (mất cơ hội bán kèm).

Module này nối hai chiều bằng DỮ LIỆU ĐÃ CÓ, không cần enrich thêm:
  trang MÁY  -> khối "Vỏ và giá treo dùng cho máy này"
  trang PHỤ KIỆN -> khối "Lắp cho máy biến áp nào"

Trang phụ kiện dày lên mà KHÔNG thêm một chữ văn nào — nội dung mới là số
của sản phẩm liên quan, hợp lệ vì đó đúng là thứ người mua vỏ cần biết.

KHÔNG GỘP TRANG. 1 SKU vẫn = 1 trang. Đây chỉ là một khối liên kết.

KHOÁ GHÉP
---------
(số pha, công suất kVA, cấp điện áp) — cả ba lấy từ CỘT DỮ LIỆU, không đọc
mã hàng. Mã hàng do người đặt, mỗi đợt một quy ước: đợt rà Amorphous đã
sót 20 dòng vì ghép cặp bằng ma.replace('A107',''). Không lặp lại.

NGOẠI LỆ DUY NHẤT — GIÁ TREO
----------------------------
7 giá treo có cột kVA và cấp điện áp ĐỀU TRỐNG, chỉ tên hàng mang thông
tin ("Giá treo MBT 1x25" = 1 pha x 25 kVA). Thịnh chốt: vẫn ghép, nhưng
mọi kết quả đọc từ tên đều mang cờ `suy_tu_ten=True` để soát lại được.
Rủi ro ở đây thấp hơn hẳn vụ Amorphous: sai thì ra một link gợi ý lệch,
KHÔNG phải một con số kỹ thuật sai in lên bài.
"""

import re

# Kiểu sản phẩm trong sheet máy biến áp
MAY = 'may'
VO = 'vo'
GIA_TREO = 'gia_treo'

# "Giá treo MBT 1x25" -> (1 pha, 25 kVA). CHỈ dùng cho giá treo.
_RE_GIA_TREO = re.compile(r'(\d)\s*[xX×]\s*(\d+(?:[.,]\d+)?)')


def _so(v):
    if v is None:
        return None
    m = re.search(r'\d+(?:[.,]\d+)?', str(v).replace(',', '.'))
    return float(m.group()) if m else None


def phan_loai(row):
    """Máy / vỏ / giá treo — đọc TÊN HÀNG (bản chất sản phẩm nằm ở tên,
    không nằm ở mã). Không phải máy biến áp thì trả None."""
    t = (row.get('ten_goc') or '').lower()
    if 'giá treo' in t:
        return GIA_TREO
    if t.startswith('vỏ') or ' vỏ ' in t[:30]:
        return VO
    if 'biến áp' in t:
        return MAY
    return None


def _pha(row):
    t = (row.get('ten_goc') or '')
    if re.search(r'1\s*pha|\b1P\b', t, re.I):
        return 1
    if re.search(r'3\s*pha|\b3P\b', t, re.I):
        return 3
    return None


def khoa(row):
    """Trả (khoa, suy_tu_ten).

    khoa = (pha, kVA, cấp điện áp chuẩn hoá) hoặc None nếu thiếu dữ liệu.
    suy_tu_ten = True nếu phải đọc từ tên hàng thay vì từ cột.
    """
    loai = phan_loai(row)
    pha = _pha(row)
    kva = _so(row.get('cong_suat'))
    kv = (row.get('cap_dien_ap') or '').strip()

    suy = False
    if loai == GIA_TREO and (pha is None or kva is None):
        m = _RE_GIA_TREO.search(row.get('ten_goc') or '')
        if not m:
            return None, False
        pha = int(m.group(1))
        kva = float(m.group(2).replace(',', '.'))
        suy = True
        # Giá treo không ghi cấp điện áp. Suy theo quy ước lưới phân phối
        # VN: máy treo cột 1 pha là 12,7/0,23 kV; 3 pha là 22/0,4 kV.
        kv = '12.7/0.23 kV' if pha == 1 else '22/0.4 kV'

    if pha is None or kva is None or not kv:
        return None, suy
    return (pha, kva, _chuan_kv(kv)), suy


def _chuan_kv(kv):
    """'12.7/0.23 kV' và '12,7/0,23kV' phải ra cùng một khoá."""
    s = str(kv).lower().replace(',', '.').replace('kv', '')
    return re.sub(r'\s+', '', s).strip('/')


def _hang(row):
    return re.sub(r'\s+', ' ', str(row.get('thuong_hieu') or '').strip().lower())


def cung_hang(a, b):
    """Vỏ là chi tiết CƠ KHÍ — kích thước thùng khác nhau theo hãng, nên vỏ
    MBT không lắp vừa máy THIBIDI dù cùng kVA và cùng cấp điện áp. Ghép vỏ
    BẮT BUỘC cùng hãng.

    Giá treo thì không ràng buộc: nó là kết cấu thép bắt vào cột, cột nào
    cũng như nhau. Hãng trong MASTER ghi 'VN', còn chữ 'MBT' trong tên
    ('Giá treo MBT 1x25') là viết tắt của MÁY BIẾN ÁP chứ không phải tên
    hãng MBT — không được coi đó là khoá hãng.
    """
    return _hang(a) == _hang(b)


def tim_di_kem(row, tat_ca_row, gioi_han=4):
    """Trả list sản phẩm đi kèm cho `row`.

    Máy      -> vỏ + giá treo cùng khoá
    Vỏ/giá treo -> máy cùng khoá
    Mỗi phần tử: dict(ma, ten, gia, loai, suy_tu_ten, po, pk).
    """
    loai = phan_loai(row)
    if loai is None:
        return []
    k, _ = khoa(row)
    if k is None:
        return []
    muon = (VO, GIA_TREO) if loai == MAY else (MAY,)

    ra = []
    for r in tat_ca_row:
        if r.get('record_id') and r.get('record_id') == row.get('record_id'):
            continue
        loai2 = phan_loai(r)
        if loai2 not in muon:
            continue
        k2, suy2 = khoa(r)
        if k2 != k:
            continue
        # ràng buộc hãng chỉ áp cho cặp máy <-> vỏ
        if VO in (loai, loai2) and not cung_hang(row, r):
            continue
        ra.append({
            'ma': r.get('ma_goc', ''), 'ten': (r.get('ten_goc') or '').replace('\n', ' ').strip(),
            # Ver 4.5 — BỎ 'gia'. gia_list nằm trong FIELD_CAM_TUYET_DOI của
            # profiles.py, nhưng module này đọc thẳng row nên đi vòng qua hàng
            # rào -> giá list Lotech bị in ra HTML công khai trên 245 bài.
            # Không đọc gia_list ở đây nữa, dưới mọi hình thức.
            'loai': loai2,
            'suy_tu_ten': suy2, 'url': r.get('_url', ''),
            'po': r.get('ton_hao_khong_tai', ''), 'pk': r.get('ton_hao_ngan_mach', ''),
        })
    # máy trước, rồi vỏ, rồi giá treo; trong cùng nhóm thì mã nào chắc chắn
    # (không suy từ tên) đứng trước
    thu_tu = {MAY: 0, VO: 1, GIA_TREO: 2}
    ra.sort(key=lambda x: (thu_tu[x['loai']], x['suy_tu_ten'], x['ma']))
    return ra[:gioi_han]


def canh_bao_suy_tu_ten(ds):
    """Danh sách mã đã ghép bằng cách đọc tên — để tab Hàng đợi soát."""
    return [x['ma'] for x in ds if x['suy_tu_ten']]


_NHAN = {MAY: 'Máy biến áp', VO: 'Vỏ bảo vệ', GIA_TREO: 'Giá treo'}


def khoi_html(row, danh_sach, _st, _esc):
    """Dựng khối 'sản phẩm đi kèm'. Trả '' nếu không có gì để hiện.

    `_st` và `_esc` truyền từ render_phase2 (_st, html.escape) để khối này
    dùng ĐÚNG hệ style/class snl-* của tool — không tự đẻ CSS riêng. Đây là
    ranh giới đã thống nhất với nhánh plugin giao diện: tool sinh cấu trúc
    và class, plugin chỉ style.
    """
    if not danh_sach:
        return ''
    loai = phan_loai(row)
    if loai == MAY:
        tieu_de = 'Vỏ và giá treo dùng cho máy này'
        dan = ('Máy treo cột cần vỏ bảo vệ và giá treo đúng công suất. '
               'Các mã dưới đây khớp công suất và cấp điện áp của máy này.')
    else:
        tieu_de = 'Lắp cho máy biến áp nào'
        dan = 'Phụ kiện này dùng cho các máy biến áp cùng công suất và cấp điện áp dưới đây.'

    the = []
    for x in danh_sach:
        if not x.get('ten'):
            continue
        nhan = _NHAN.get(x['loai'], '')
        phu = ' · '.join(p for p in (x.get('ma', ''), nhan) if p)
        noi = f'{_esc(x["ten"])}<br><small>{_esc(phu)}</small>'
        if x.get('url'):
            the.append(f'<a href="{_esc(x["url"])}" {_st("lien_quan_card")}>{noi}</a>')
        else:
            the.append(f'<div {_st("lien_quan_card")}>{noi}</div>')
    if not the:
        return ''
    return (f'<h2>{tieu_de}</h2><p>{_esc(dan)}</p>'
            f'<div {_st("lien_quan_grid")}>' + ''.join(the) + '</div>')
