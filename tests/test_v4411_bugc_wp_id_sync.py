# -*- coding: utf-8 -*-
"""BUG-C Ver 4.4.1.1 — phục hồi wp_id theo SKU + state Media/Attached. Mock-only."""
import os, sys, tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tab_anh as TA
import workspace_anh as WS
import xu_ly_anh as X
import autopost as A
import ai_wp_adapter as AWP
import db_phase2 as DB
import cauhinh as C

P = F = 0
def ck(name, cond, detail=''):
    global P, F
    if cond:
        P += 1; print(f'PASS {name}: {detail}')
    else:
        F += 1; print(f'FAIL {name}: {detail}')

class DummyCon:
    def close(self): pass

class V:
    def __init__(self, x=''): self.x=x
    def get(self): return self.x

obj = TA.TabAnh.__new__(TA.TabAnh)
obj.v_goc = V('/tmp/images')

base = {
    'dataset_id':'ds','record_id':'rid','site':'maybienapvn.vn','mau':'chuan',
    'sku':'MBT1P25A2608','wp_id':None,'row':{'publish_sku':'MBT1P25A2608','profile_id':'may_bien_ap_do_luong'},
    'sheet':'03_May_Bien_Ap_Do_Luong','thu_muc':None,'ten':'MBA 25kVA', 'slug':'mba-25'
}

# C1: missing local wp_id -> existing Woo product found by SKU -> DB healed.
writes=[]; calls=[]
with patch.object(A,'tim_san_pham_woo_theo_sku', side_effect=lambda site,sku: calls.append((site,sku)) or 2468), \
     patch.object(DB,'ket_noi', return_value=DummyCon()), \
     patch.object(DB,'cap_nhat_bai_viet', side_effect=lambda *a,**kw: writes.append(kw) or True):
    b=dict(base)
    r=obj._resolve_wp_id_theo_sku(b)
ck('C1-RESOLVE-SKU', r.get('ok') and r.get('wp_id')=='2468' and b['wp_id']=='2468', str(r))
ck('C1-PERSIST-DB', writes and writes[-1].get('wp_id')=='2468', str(writes))
ck('C1-CURRENT-SITE', calls==[(C.MA_SITE_VER3,'MBT1P25A2608')], str(calls))

# C2: truly not found is NOT an API error.
with patch.object(A,'tim_san_pham_woo_theo_sku', return_value=None):
    r=obj._resolve_wp_id_theo_sku(dict(base), ghi_db=False)
ck('C2-NOT-FOUND', (not r.get('ok')) and r.get('not_found') is True and 'chưa tồn tại' in r.get('loi','').lower(), str(r))

# C3: API failure must stay ERROR, never masquerade as not-found.
with patch.object(A,'tim_san_pham_woo_theo_sku', side_effect=RuntimeError('HTTP 503 synthetic')):
    r=obj._resolve_wp_id_theo_sku(dict(base), ghi_db=False)
ck('C3-API-ERROR', (not r.get('ok')) and r.get('not_found') is False and '503' in r.get('loi',''), str(r))

# C4: valid local ID -> no remote lookup.
with patch.object(A,'tim_san_pham_woo_theo_sku', side_effect=AssertionError('khong duoc lookup')):
    b=dict(base, wp_id='777')
    r=obj._resolve_wp_id_theo_sku(b)
ck('C4-LOCAL-ID-FIRST', r.get('ok') and r.get('wp_id')=='777' and r.get('tu_db') is True, str(r))

# C5: stale ID -> body returns invalid_id -> clear -> lookup SKU -> retry exactly once.
body_calls=[]; gal_calls=[]; db_writes=[]; lookup_calls=[]
obj2=TA.TabAnh.__new__(TA.TabAnh); obj2.v_goc=V('/tmp/images')
obj2._resolve_wp_id_theo_sku = lambda b, ghi_db=True: (
    {'ok':True,'wp_id':b['wp_id'],'tu_db':True} if b.get('wp_id') else
    (lookup_calls.append(b['sku']) or b.__setitem__('wp_id','888') or {'ok':True,'wp_id':'888','tu_db':False}))
def fake_body(wp_id, content, la_woo=True, timeout=60):
    body_calls.append(str(wp_id))
    if str(wp_id)=='1001': return {'ok':False,'loi':'HTTP 404: rest_post_invalid_id'}
    return {'ok':True}
def fake_gal(wp_id,mids,la_woo=True,timeout=60): gal_calls.append((str(wp_id),list(mids))); return {'ok':True}
with patch.object(DB,'ket_noi', return_value=DummyCon()), \
     patch.object(DB,'lay_bai_viet', return_value={'html':'<div><!--SNL_IMAGE_SLOT:bien_may--></div>'}), \
     patch.object(DB,'cap_nhat_bai_viet', side_effect=lambda *a,**kw: db_writes.append(kw) or True), \
     patch.object(AWP,'cap_nhat_noi_dung_bai_that', side_effect=fake_body), \
     patch.object(AWP,'gan_anh_vao_san_pham', side_effect=fake_gal), \
     patch.object(C,'doc_website', return_value={'che_do_dang':'woo_product'}), \
     patch.object(WS,'danh_dau_da_gan_vao_bai', return_value=1):
    b=dict(base, wp_id='1001')
    rr=obj2._gan_anh_vao_bai_ngay(b, {'anh':[{'vai_tro':'bien_may','url':'u','alt':'a','rong':10,'cao':10,'wp_media_id':55}]})
ck('C5-STALE-ID-RECOVER', rr.get('ok') and body_calls==['1001','888'] and lookup_calls==['MBT1P25A2608'], f'{rr} body={body_calls} lookup={lookup_calls}')
ck('C5-GALLERY-NEW-ID', gal_calls==[('888',[55])], str(gal_calls))
ck('C5-NULL-THEN-HEAL', any(x.get('wp_id','x') is None for x in db_writes) and any(x.get('wp_id')=='888' for x in db_writes), str(db_writes))

# C6: batch sync separates found / not-found / API error.
obj3=TA.TabAnh.__new__(TA.TabAnh)
seq={'A':{'ok':True,'wp_id':'1'}, 'B':{'ok':False,'not_found':True,'loi':'none'}, 'C':{'ok':False,'not_found':False,'loi':'503'}}
def resolver(b, ghi_db=True):
    r=dict(seq[b['sku']]);
    if r.get('ok'): b['wp_id']=r['wp_id']
    return r
obj3._resolve_wp_id_theo_sku=resolver
rows=[dict(base,record_id='A',sku='A'),dict(base,record_id='B',sku='B'),dict(base,record_id='C',sku='C')]
st=obj3._dong_bo_wp_id_core(rows, ghi_log=lambda *_:None)
ck('C6-BATCH-SUMMARY', st=={'thieu':3,'tim_thay':1,'khong_tim_thay':1,'loi_api':1,'bo_qua_identity':0}, str(st))

# State split, full 5/5: upload to Media first, then mark attached to post.
from PIL import Image
D=Path(tempfile.mkdtemp()); row={'ma_goc':'SKU5','ten_goc':'MBA','profile_id':'may_bien_ap_do_luong','record_id':'r5'}
tm=WS.tao_workspace(D,'S',5,row,title='MBA',slug='mba')
roles=WS.ma_vai_tro('may_bien_ap_do_luong')
for i,role in enumerate(roles):
    # Ver 5.7 — 200x120 nằm dưới ngưỡng cổng ảnh 800px nên bị bỏ qua.
        # Nâng lên 1000x850 để test đúng cái nó định test (đồng bộ wp_id),
        # không phải test cổng ảnh.
        p=D/f'a{i}.jpg'; Image.new('RGB',(1000,850),(20+i,40,60)).save(p); WS.gan_anh(tm,p,role)
ctr=[0]
def up(p,ten,mime): ctr[0]+=1; return 500+ctr[0], f'https://x/{ten}'
k=X.dang_anh_hieu_luc(D,'S',tm,row,'siteA',tieu_de='MBA',slug='mba',upload=up)
t1=WS.trang_thai_hieu_luc(D,'S',row,tm,ma_site='siteA',wp_post_id='900')[0]
WS.danh_dau_da_gan_vao_bai(D,'S',row,tm,'siteA','900',k['anh'])
t2=WS.trang_thai_hieu_luc(D,'S',row,tm,ma_site='siteA',wp_post_id='900')[0]
ck('STATE-MEDIA', t1=='Đã lên Media 5/5', t1)
ck('STATE-ATTACHED', t2=='Đã gắn vào bài 5/5', t2)

# UI contract.
src=Path('tab_anh.py').read_text(encoding='utf-8')
ck('UI-BUTTON-UPDATE', "text='Cập nhật ảnh lên WordPress'" in src)
ck('UI-BUTTON-SYNC', "text='ĐỒNG BỘ WP ID'" in src)
ck('UI-NO-LYING-LABEL', 'Đã lên Media' in Path('workspace_anh.py').read_text(encoding='utf-8') and 'Đã gắn vào bài' in Path('workspace_anh.py').read_text(encoding='utf-8'))

print(f'TỔNG: PASS {P} / FAIL {F}')
raise SystemExit(1 if F else 0)
