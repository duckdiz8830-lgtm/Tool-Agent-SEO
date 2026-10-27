# -*- coding: utf-8 -*-
"""Ver 4.4 — functional UI logic smoke. Không dùng làm bằng chứng visual Windows."""
import os, sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tkinter as tk
import tab_anh as TA

P = F = 0

def ck(name, cond, detail=''):
    global P, F
    if cond:
        P += 1; print(f'PASS {name}: {detail}')
    else:
        F += 1; print(f'FAIL {name}: {detail}')

root = tk.Tk()
root.geometry('1280x800+0+0')
try:
    with patch.object(TA.TabAnh, 'nap', lambda self: None):
        tab = TA.TabAnh(root, giac=None)
    tab.f.pack(fill='both', expand=True)
    tab.bai = [
        {'sku':'MBT3P750','ten':'Máy biến áp dầu MBT 750kVA 3 pha','co':0,'tong':5,'nguon':'trong','tt':'CHƯA CÓ ẢNH',
         'so_dong':1,'ho_nhan':'MBT · dầu · 3 pha · Amorphous','row':{'thuong_hieu':'MBT'}},
        {'sku':'TBD3P250','ten':'Máy biến áp dầu THIBIDI 250kVA 3 pha','co':3,'tong':5,'nguon':'ho','tt':'ĐÃ ĐĂNG',
         'so_dong':2,'ho_nhan':'THIBIDI · dầu · 3 pha · Silic','row':{'thuong_hieu':'THIBIDI'}},
        {'sku':'TBD3P400','ten':'Máy biến áp dầu THIBIDI 400kVA 3 pha','co':1,'tong':5,'nguon':'rieng','tt':'ĐÃ ĐĂNG',
         'so_dong':3,'ho_nhan':'THIBIDI · dầu · 3 pha · Silic','row':{'thuong_hieu':'THIBIDI'}},
    ]
    tab.cb_ho_anh['values'] = ['(tất cả)','MBT · dầu · 3 pha · Amorphous','THIBIDI · dầu · 3 pha · Silic']
    tab._ap_loc(); root.update_idletasks()
    ck('C1-SEARCH-BASE', len(tab.dang_hien)==3, f'rows={len(tab.dang_hien)}')

    tab.v_tim_anh.set('THIBIDI'); root.update_idletasks()
    ck('C1-SEARCH-BRAND', len(tab.dang_hien)==2 and all('TBD' in b['sku'] for b in tab.dang_hien),
       str([b['sku'] for b in tab.dang_hien]))
    tab.v_tim_anh.set('750kVA'); root.update_idletasks()
    ck('C1-SEARCH-TITLE', [b['sku'] for b in tab.dang_hien]==['MBT3P750'], str([b['sku'] for b in tab.dang_hien]))

    tab.v_tim_anh.set('')
    tab.v_ho_anh.set('THIBIDI · dầu · 3 pha · Silic'); tab._ap_loc()
    ck('C5-FAMILY-FILTER', len(tab.dang_hien)==2, str([b['sku'] for b in tab.dang_hien]))

    tab.v_ho_anh.set('(tất cả)')
    tab._sort_anh_col='anh'; tab._sort_anh_desc=False; tab._ap_loc()
    ck('C2-SORT-IMAGE-ASC', [b['co'] for b in tab.dang_hien]==[0,1,3], str([b['co'] for b in tab.dang_hien]))

    ids=tab.bang.get_children()
    tab.bang.selection_set(ids[0], ids[1])
    ck('C6-MULTISELECT', len(tab._bai_da_chon())==2, str([b['sku'] for b in tab._bai_da_chon()]))
    ck('C4-STT-COLUMN', 'stt' in tab.bang['columns'] and tab.nhan_dong.cget('text').endswith('/3'), tab.nhan_dong.cget('text'))
    ck('A-SCROLLBAR-LOGIC', str(tab.cuon_doc.cget('orient'))=='vertical' and tab.canvas_o.cget('yscrollcommand') != '',
       'scrollbar/canvas wired')
finally:
    root.destroy()

print(f'TỔNG UI LOGIC: PASS {P} / FAIL {F}')
raise SystemExit(1 if F else 0)
