# -*- coding: utf-8 -*-
"""VA 4.4.1.9 — slug sheet 03 duy nhat cho TUNG DONG.

Muc tieu: dang het 581 dong thi phai nhan ve 581 URL. Slug trung nghia la
WordPress de bai hoac tu them '-2' -> mat bai, KHONG phai muc tieu.

Ba lop, xai theo thu tu, chi xuong lop sau khi lop truoc chua du:
  L1. Tien to dung loai san pham (may bien ap / vo / gia treo / cong to / bien dong).
      Hien tai MOI dong deu ra 'may-bien-ap-...' ke ca cong to dien.
  L2. Bo sung dac diem CO THAT trong du lieu: cap dien ap, kin/ho, so pha.
  L3. Hau to phan biet ghi vao cot Excel 'Hau to slug' - CHI cho dong con trung.
      Day la duoi URL, khong phai thong so ky thuat -> khong vi pham luat khong bia.
"""
import re
import unicodedata
from chuan_hoa import bo_dau as _bo_dau   # Ver 5.7 — gom 9 bản _bo_dau về 1 nguồn (xem chuan_hoa.py)


# ---------- L1: tien to theo loai san pham that ----------
_LOAI = [
    ('vo-may-bien-ap', r'\bvo (ma kem|bao ve|may bien ap)|\bvo mba\b'),
    ('gia-treo-may-bien-ap', r'\bgia treo\b'),
    ('hop-bo-do-luong', r'\bhop bo do luong\b|\bmof\b'),
    ('cong-to-dien', r'\bcong to dien\b'),
    ('bien-dong-dien', r'\bbien dong\b|\bbien ap do luong\b'),
    ('dong-ho-do-dien', r'\bdong ho (ampe|ka|von|vol)\b'),
    ('may-bien-ap', r'\bmay bien ap\b|\bmba\b'),
]


def loai_san_pham(ten_goc, nhom_nguon=''):
    t = _bo_dau(ten_goc)
    for nhan, pat in _LOAI:
        if re.search(pat, t):
            return nhan
    if 'do luong' in _bo_dau(nhom_nguon):
        return 'thiet-bi-do-luong'
    return 'may-bien-ap'


# ---------- L2: dac diem co that trong du lieu ----------
def dac_diem_them(row, R, D):
    """Tra list phan slug bo sung, lay tu DU LIEU, khong suy dien."""
    them = []
    cap = R._cap_ap_gon(row.get('cap_dien_ap'))
    if cap:
        them.append(D.slugify(cap, dai=24))
    t = _bo_dau(row.get('ten_goc', ''))
    if 'loai kin' in t:
        them.append('kin')
    elif 'binh dau phu' in t or 'loai ho' in t:
        them.append('ho')
    if 'cuon dong' in t:
        them.append('cuon-dong')
    elif 'cuon nhom' in t:
        them.append('cuon-nhom')
    m = re.search(r'\b(\d+)\s*x\s*(\d+)\b', t)   # 'Gia treo MBT 1x25' -> 1x25
    if m:
        them.append(f'{m.group(1)}x{m.group(2)}')
    m = re.search(r'\bccx\s*([\d.,/]+)', t)      # 'Bien dong ha the CXX 0,5'
    if m:
        them.append('ccx-' + D.slugify(m.group(1), dai=12))
    return [x for x in them if x]


def slug_moi(row, R, D):
    """Slug L1 + L2 + hau_to (L3, doc tu cot Excel neu co)."""
    goc = R._slug_mba_39(row)
    loai = loai_san_pham(row.get('ten_goc', ''), row.get('nhom_nguon', ''))
    if goc.startswith('may-bien-ap') and loai != 'may-bien-ap':
        goc = loai + goc[len('may-bien-ap'):]
    phan = [goc] + dac_diem_them(row, R, D)
    ht = str(row.get('hau_to_slug', '') or '').strip()
    if ht:
        phan.append(D.slugify(ht, dai=24))
    return re.sub(r'-+', '-', '-'.join(p for p in phan if p)).strip('-')
