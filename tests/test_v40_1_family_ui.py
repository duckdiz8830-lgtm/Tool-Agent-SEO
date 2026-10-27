import sys, tkinter as tk
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tkinter import ttk
import tab_anh as T

orig=T.TabAnh.nap
T.TabAnh.nap=lambda self: None
root=tk.Tk(); root.geometry('1200x760')
nb=ttk.Notebook(root); nb.pack(fill='both', expand=True)
t=T.TabAnh(nb,None); nb.add(t.f,text='Ảnh')
T.TabAnh.nap=orig
row={'profile_id':'may_bien_ap_do_luong','outline_id':'outline_may_bien_ap','record_id':'D::S::A',
     'ma_goc':'A','publish_sku':'A','thuong_hieu':'THIBIDI',
     'ten_goc':'Máy biến áp dầu 3Pha 250KVA Loại Silic',
     'thong_so_dong':{'Loại lõi (trích từ tên)':'Silic'}}
t.bai=[{'row':row,'sku':'A','sheet':'S','so_dong':1,'ten':'A','wp_id':None,'thu_muc':None,
        'tt':'CHƯA CÓ ẢNH','co':0,'tong':5,'nguon':'trong'}]
t._ap_loc(); root.update_idletasks()
assert 'nguon' in t.bang['columns']
assert t.bang.heading('nguon')['text']=='Nguồn'
buttons=[]
def walk(w):
    for c in w.winfo_children():
        if isinstance(c, ttk.Button): buttons.append(c.cget('text'))
        walk(c)
walk(t.f)
assert 'Gán ảnh cho họ' in buttons
cw=T.CuaSoAnhHo(t); root.update_idletasks()
assert len(cw.ho)==1
assert len(cw.bang.get_children())==1
slot_labels=[]
def collect_labels(w):
    for c in w.winfo_children():
        if isinstance(c, ttk.Label): slot_labels.append(c.cget('text'))
        collect_labels(c)
collect_labels(cw.o)
assert sum(x.startswith(('1. ','2. ','3. ','4. ','5. ')) for x in slot_labels)==5
print('UI_SOURCE_COLUMN=PASS; FAMILY_BUTTON=PASS; FAMILY_SCREEN_ROWS=1; FAMILY_SLOTS=5')
cw.top.destroy(); root.destroy()
print('PASS V40-1 FAMILY UI')
