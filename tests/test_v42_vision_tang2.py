# -*- coding: utf-8 -*-
import tempfile
from pathlib import Path
from PIL import Image
import sys
BASE=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(BASE))
import loc_kho_anh_ai as L
import workspace_anh as W

P=F=0
def ck(cond,msg):
    global P,F
    if cond: P+=1; print('PASS',msg)
    else: F+=1; print('FAIL',msg)

with tempfile.TemporaryDirectory() as td:
    root=Path(td); da=root/'_DA_LOC'; da.mkdir(); ws=root/'workspace'
    p=da/'a.jpg'; Image.new('RGB',(900,900),'white').save(p)
    # Không AI: phải bỏ qua, không phá tầng 1/file nguồn.
    old=L.V.doc_cau_hinh
    L.V.doc_cau_hinh=lambda: {'keys':[]}
    try:
        r=L.chay_tang2(da,ws)
    finally:
        L.V.doc_cau_hinh=old
    ck(r['tong_anh']==1 and r['khong_ai']==1,'không có AI -> tầng 2 bỏ qua rõ ràng')
    ck(p.is_file(),'không AI không xoá/sửa ảnh tầng 1')

with tempfile.TemporaryDirectory() as td:
    root=Path(td); da=root/'_DA_LOC'; da.mkdir(); ws=root/'workspace'; sheet='03_May_Bien_Ap_Do_Luong'
    p1=da/'dau3.jpg'; p2=da/'moho.jpg'
    Image.new('RGB',(900,900),'white').save(p1); Image.new('RGB',(900,900),'gray').save(p2)
    row={'profile_id':'may_bien_ap_do_luong','thuong_hieu':'THIBIDI','ten_goc':'Máy biến áp dầu 3 pha lõi Silic','ma_goc':'X'}
    W.tao_workspace_ho(ws,sheet,row)
    def fake(path,prompt):
        if Path(path).name=='dau3.jpg':
            return {'ok':True,'json':{'may':'dau','pha':'3','vai_tro':'san_pham'}}
        return {'ok':True,'json':{'may':None,'pha':None,'vai_tro':None}}
    r=L.chay_tang2(da,ws,sheet=sheet,vision_func=fake)
    ck(r['tong_anh']==2,'mock tầng 2 đọc đủ ảnh')
    ck(r['phan_loai_ok']==1,'AI chỉ phân loại ảnh đủ bằng chứng')
    ck(r['chua_phan_loai']>=1,'không chắc -> chưa phân loại, không đoán')
    txt=(ws/W.ten_an_toan(sheet,80)/'_HO'/'BAO-CAO-TANG2.json').read_text(encoding='utf-8')
    ck('kva' not in txt.lower(),'report không sinh/đoán công suất kVA')

print(f'TỔNG: PASS {P} / FAIL {F}')
raise SystemExit(1 if F else 0)
