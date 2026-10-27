# -*- coding: utf-8 -*-
"""Ver 4.5.1 — sinh MÃ NỘI BỘ LOTECH cho dòng catalogue không in SKU.

VẤN ĐỀ NÓ GIẢI
  MASTER Ver13 sheet 03 có 581 dòng nhưng 333 dòng trống 'Mã hàng' (catalogue
  hãng không in SKU, người bóc PDF không bịa - đúng nguyên tắc). Nhưng
  'Mã hàng' nằm trong cot_bat_buoc -> 333 dòng bị loại ngay cửa import,
  chỉ vào được 248/581.

NGUYÊN TẮC
  1. KHÔNG bịa mã hãng. Mã sinh ra có tiền tố 'LTC-' và cột 'Nguồn mã hàng'
     ghi rõ 'nội bộ Lotech'. Ai đọc MASTER cũng phân biệt được ngay.
  2. Suy từ dữ liệu CÓ THẬT của chính dòng đó (hãng, pha, kVA, cấp áp, lõi,
     kín/hở). Cùng dữ liệu -> cùng mã, chạy lại không đổi.
  3. Dòng đã có mã hãng thì KHÔNG đụng.
  4. Trùng mã -> thêm số thứ tự, không bao giờ để 2 dòng chung mã.

VÌ SAO ĐẶT VÀO CỘT 'Mã hàng' LÀ ĐÚNG CHUẨN
  schema.org: 'sku' = mã của NGƯỜI BÁN, 'mpn' = mã của nhà sản xuất. Mã nội bộ
  Lotech nằm ở sku là đúng định nghĩa, không phải chữa cháy.
"""
import re
import shutil
import unicodedata

import pandas as pd
from chuan_hoa import bo_dau_giu_hoa as _bo_dau   # Ver 5.7 — gom 9 bản _bo_dau về 1 nguồn (xem chuan_hoa.py)

SHEET = '03_May_Bien_Ap_Do_Luong'
COT_NGUON = 'Nguồn mã hàng'
TIEN_TO = 'LTC'


def _gon(s, dai=10):
    """Chữ + số, viết hoa, bỏ dấu. 'Gelex EMIC' -> 'GELEXEMIC'."""
    t = re.sub(r'[^A-Za-z0-9]', '', _bo_dau(s)).upper()
    return t[:dai]


def _so(s):
    m = re.search(r'\d+(?:[.,]\d+)?', str(s or ''))
    if not m:
        return ''
    v = m.group(0).replace(',', '.')
    return str(int(float(v))) if float(v) == int(float(v)) else v.replace('.', '')


def sinh_ma(r):
    """Mã nội bộ từ dữ liệu có thật của dòng. Ví dụ: LTC-HBT-3P-100-22-KIN."""
    t = _bo_dau(str(r.get('Tên hàng') or '')).lower()
    phan = [TIEN_TO]

    hang = _gon(r.get('Nhãn Hiệu / Xuất Xứ'), 10)
    if hang:
        phan.append(hang)

    m = re.search(r'(\d)\s*pha|\b(\d)p\b', t)
    if m:
        phan.append((m.group(1) or m.group(2)) + 'P')

    kva = _so(r.get('Công Suất (kVA)'))
    if kva:
        phan.append(kva)

    cap = _so(r.get('Cấp Điện Áp (kV)'))
    if cap:
        phan.append(cap)

    if 'kho' in t and 'may bien ap kho' in t:
        phan.append('KHO')
    elif 'dau' in t:
        phan.append('DAU')

    if 'amorphous' in t:
        phan.append('AMO')
    elif 'silic' in t:
        phan.append('SIL')

    if 'loai kin' in t:
        phan.append('KIN')
    elif 'binh dau phu' in t or 'loai ho' in t:
        phan.append('HO')

    if 'cuon dong' in t:
        phan.append('CU')
    elif 'cuon nhom' in t:
        phan.append('AL')

    return '-'.join(p for p in phan if p)


def chay(nguon, dich):
    a = pd.read_excel(nguon, sheet_name=SHEET)
    goc = a['Mã hàng'].copy()

    ma, nguon_ma = [], []
    da_dung = set(str(v).strip() for v in goc.dropna())
    so_sinh = 0

    for i in range(len(a)):
        cu = goc.iloc[i]
        cu = '' if pd.isna(cu) else str(cu).strip()
        if cu:
            ma.append(cu)
            nguon_ma.append('mã hãng (catalogue/bảng giá)')
            continue
        m = sinh_ma(a.iloc[i])
        goc_m, n = m, 2
        while m in da_dung:          # không bao giờ để 2 dòng chung mã
            m = f'{goc_m}-{n}'
            n += 1
        da_dung.add(m)
        ma.append(m)
        nguon_ma.append('nội bộ Lotech (catalogue không in SKU)')
        so_sinh += 1

    a['Mã hàng'] = ma
    if COT_NGUON in a.columns:
        a = a.drop(columns=[COT_NGUON])
    a.insert(list(a.columns).index('Mã hàng') + 1, COT_NGUON, nguon_ma)

    shutil.copy(nguon, dich)
    with pd.ExcelWriter(dich, engine='openpyxl', mode='a',
                        if_sheet_exists='replace') as w:
        a.to_excel(w, sheet_name=SHEET, index=False)
        a.loc[a[COT_NGUON].str.startswith('nội bộ'),
              ['Mã hàng', COT_NGUON, 'Tên hàng', 'Nhãn Hiệu / Xuất Xứ',
               'Công Suất (kVA)', 'Cấp Điện Áp (kV)']].to_excel(
            w, sheet_name='00_Ma_Noi_Bo', index=False)

    trung = len(a) - a['Mã hàng'].nunique()
    print(f'Tổng dòng              : {len(a)}')
    print(f'Đã có mã hãng          : {len(a) - so_sinh}')
    print(f'Sinh mã nội bộ         : {so_sinh}')
    print(f'Mã trùng nhau          : {trung}')
    print(f'Dòng trống Mã hàng     : {int(a["Mã hàng"].eq("").sum())}')
    print(f'\nVí dụ mã sinh ra:')
    for v in a.loc[a[COT_NGUON].str.startswith('nội bộ'), 'Mã hàng'].head(6):
        print('   ', v)
    print(f'\nĐã ghi: {dich}')
    return trung == 0 and so_sinh > 0


if __name__ == '__main__':
    chay('/mnt/user-data/outputs/9MASTER_Ver13_SLUG_CHI_DINH.xlsx',
         '/mnt/user-data/outputs/9MASTER_Ver14_MA_NOI_BO.xlsx')
