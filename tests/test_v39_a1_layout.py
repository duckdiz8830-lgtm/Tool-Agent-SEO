# -*- coding: utf-8 -*-
"""Ver 3.9 A1 — kiểm layout tab ảnh ở đúng kích thước màn hình yêu cầu."""
import json
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import tab_anh

# Không đọc DB trong visual test; chỉ dựng đúng widget production.
tab_anh.TabAnh.nap = lambda self: None

w = int(os.environ.get('TEST_W', '1366'))
h = int(os.environ.get('TEST_H', '768'))
out = os.environ.get('TEST_SHOT', str(BASE / f'a1-{w}x{h}.png'))
root = tk.Tk()
root.title('SONEALEO A1 layout test')
root.geometry(f'{w}x{h}+0+0')
nb = ttk.Notebook(root)
nb.pack(fill='both', expand=True)
t = tab_anh.TabAnh(nb)
nb.add(t.f, text='  Ảnh bài viết (3.7)  ')
t.chon = {
    'ten': 'Máy biến áp dầu THIBIDI 250kVA 3 pha 22/0.4kV lõi Silic',
    'thu_muc': None,
    'sheet': '03_May_Bien_Ap_Do_Luong',
    'row': {'profile_id': 'may_bien_ap_do_luong'},
}
t._ve_o()
root.update_idletasks(); root.update()
rx, ry = root.winfo_rootx(), root.winfo_rooty()
bx, by = t.nut_dang.winfo_rootx(), t.nut_dang.winfo_rooty()
bw, bh = t.nut_dang.winfo_width(), t.nut_dang.winfo_height()
inside = (bx >= rx and by >= ry and bx + bw <= rx + w and by + bh <= ry + h)
labels = []
for outer in t.khung_o.winfo_children():
    for child in outer.winfo_children():
        if isinstance(child, ttk.Label):
            text = child.cget('text')
            if text and text[:1].isdigit():
                labels.append(text)
subprocess.run(['scrot', out], check=True)
print(json.dumps({'size': [w,h], 'button': [bx,by,bw,bh], 'inside': inside,
                  'labels': labels, 'shot': out}, ensure_ascii=False))
root.destroy()
if not inside or len(labels) != 5 or any('...' in x for x in labels):
    print('FAIL: layout acceptance không đạt')
    raise SystemExit(1)
print('PASS: layout acceptance đạt')
