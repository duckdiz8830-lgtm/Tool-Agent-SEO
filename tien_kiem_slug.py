# -*- coding: utf-8 -*-
"""Tien kiem slug truoc khi dang loat — sheet 03.

Chay TRUOC moi dot dang. Doc MASTER, tinh slug cho tung dong, dong nao con
trung thi ghi hau to phan biet vao cot 'Hau to slug'.

Uu tien hau to (chi dung DU LIEU CO THAT, khong bia):
  1. Ma hang           - dinh danh that cua san pham
  2. Quy cach / Ap luc - tieu chuan ky thuat
  3. so thu tu dong    - chot chan cuoi cung, ghi ro trong bao cao de nguoi soat

Ket qua: moi dong ra 1 URL rieng => dang N dong nhan ve N bai, khong mat bai.
"""
import os
import re
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_phase2 as R          # noqa: E402
import dulieu as D                 # noqa: E402
import va_slug as V                # noqa: E402

SHEET = '03_May_Bien_Ap_Do_Luong'
COT_HAU_TO = 'Hậu tố slug'
MAP = {'Mã hàng': 'ma_goc', 'Tên hàng': 'ten_goc', 'Nhãn Hiệu / Xuất Xứ': 'thuong_hieu',
       'Quy Cách / Áp Lực': 'quy_cach', 'Công Suất (kVA)': 'cong_suat',
       'Cấp Điện Áp (kV)': 'cap_dien_ap', 'Nhóm Nguồn': 'nhom_nguon',
       'Nguồn - Tiêu chuẩn viện dẫn': 'nguon_tieu_chuan_vien_dan'}


def _sach(v):
    """Doc o Excel an toan: NaN/'nan'/rong -> '' (khong bao gio thanh chuoi 'nan')."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ''
    t = str(v).strip()
    return '' if t.lower() in ('nan', 'none', 'nat') else t


def _rieng(r, a):
    """Lay phan chu RIENG cua ten hang so voi cac dong cung hang.
    Vi du 6 dong Hitachi khac nhau o 'truyen tai' / 'noi dat' / 'ngoai khoi'."""
    ten = _sach(r.get('Tên hàng'))
    hang = _sach(r.get('Nhãn Hiệu / Xuất Xứ'))
    t = ten
    for bo in ('Máy biến áp', 'máy biến áp', hang, 'dầu', 'khô'):
        if bo:
            t = t.replace(bo, ' ')
    t = re.sub(r'\s+', ' ', t).strip()
    return t[:40] or ten[:40]


def _row(r, hau_to=''):
    d = {v: ('' if pd.isna(r.get(k)) else str(r.get(k))) for k, v in MAP.items()}
    d['outline_id'] = 'outline_may_bien_ap'
    d['hau_to_slug'] = hau_to
    return d


def chay(nguon, dich):
    a = pd.read_excel(nguon, sheet_name=SHEET)
    hau_to = [''] * len(a)
    ly_do = [''] * len(a)

    def tinh():
        return [V.slug_moi(_row(a.iloc[i], hau_to[i]), R, D) for i in range(len(a))]

    slugs = tinh()
    truoc = len(set(slugs))

    for vong, (nhan, lay) in enumerate([
        ('mã hàng', lambda i: _sach(a.iloc[i].get('Mã hàng'))),
        ('quy cách', lambda i: _sach(a.iloc[i].get('Quy Cách / Áp Lực'))),
        ('tên hàng', lambda i: _rieng(a.iloc[i], a)),
        ('số dòng Excel', lambda i: f'r{i + 2}'),
    ], 1):
        dem = {}
        for s in slugs:
            dem[s] = dem.get(s, 0) + 1
        con = [i for i, s in enumerate(slugs) if dem[s] > 1]
        if not con:
            break
        for i in con:
            v = lay(i)
            if v:
                # con trung sau vong truoc -> thay bang hau to CU THE HON
                hau_to[i] = v
                ly_do[i] = f'trùng slug, phân biệt bằng {nhan}'
        slugs = tinh()

    dem = {}
    for s in slugs:
        dem[s] = dem.get(s, 0) + 1
    con_trung = [i for i, s in enumerate(slugs) if dem[s] > 1]

    # GIU SLUG CU: dong nao da co 'Slug chi dinh' (bai da dang) thi khong doi.
    cu = a['Slug chỉ định'] if 'Slug chỉ định' in a.columns else None
    if cu is not None:
        for i in range(len(a)):
            v = _sach(cu.iloc[i])
            if v:
                slugs[i] = v
                ly_do[i] = 'giữ nguyên slug đã đăng'
    a[COT_HAU_TO] = hau_to
    a['Slug chỉ định'] = slugs
    a['Slug dự kiến'] = slugs
    a['Ghi chú slug'] = ly_do

    # ghi ra file moi, giu nguyen cac sheet khac
    import shutil
    shutil.copy(nguon, dich)
    with pd.ExcelWriter(dich, engine='openpyxl', mode='a',
                        if_sheet_exists='replace') as w:
        a.to_excel(w, sheet_name=SHEET, index=False)
        bc = a.loc[a[COT_HAU_TO] != '',
                   ['Mã hàng', 'Tên hàng', COT_HAU_TO, 'Slug dự kiến', 'Ghi chú slug']]
        bc.to_excel(w, sheet_name='00_TienKiem_Slug', index=False)

    print(f'Tong dong          : {len(a)}')
    print(f'URL rieng TRUOC va : {truoc}  -> mat {len(a) - truoc} bai neu dang ngay')
    print(f'URL rieng SAU va   : {len(set(slugs))}')
    print(f'Dong phai gan hau to: {sum(1 for h in hau_to if h)}')
    print(f'CON TRUNG          : {len(con_trung)}')
    if con_trung:
        for i in con_trung[:10]:
            print('   !', slugs[i], '|', str(a.iloc[i]["Tên hàng"])[:50])
    print(f'\nDa ghi: {dich}')
    return len(con_trung) == 0


if __name__ == '__main__':
    ok = chay('/mnt/user-data/uploads/9MASTER_Ver11_QA_DA_VAI_BO_SUNG_PDF_MBA.xlsx',
              '/mnt/user-data/outputs/9MASTER_Ver13_SLUG_CHI_DINH.xlsx')
    print('KET QUA:', 'DAT - moi dong 1 URL rieng' if ok else 'CHUA DAT')
