# -*- coding: utf-8 -*-
"""4.4.1.3 — partial image attach + upload-only watermark. Mock-only."""
import os, sys, tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
import xu_ly_anh as X
import workspace_anh as WS
import tab_anh as TA
import db_phase2 as DB
import ai_wp_adapter as AWP
import cauhinh as C

P=F=0
def ck(name, cond, detail=''):
    global P,F
    if cond:
        P+=1; print(f'PASS {name}: {detail}')
    else:
        F+=1; print(f'FAIL {name}: {detail}')

class DummyCon:
    def close(self): pass
class V:
    def __init__(self,x=''): self.x=x
    def get(self): return self.x

# ------------------------------------------------------------ A. watermark only on upload, canonical stays clean
D=Path(tempfile.mkdtemp())
row={'ma_goc':'SKU-WM','publish_sku':'SKU-WM','ten_goc':'MBA','profile_id':'may_bien_ap_do_luong','record_id':'r'}
tm=WS.tao_workspace(D,'S',1,row,title='MBA',slug='mba')
roles=WS.ma_vai_tro(row['profile_id'])
# Ver 5.7 — 900x600 có cạnh NGẮN = 600 < 800 nên bị cổng ảnh chặn.
# Nâng lên 1200x900 (cạnh ngắn 900) để ảnh 'good' đi hết đường watermark.
good=D/'good.jpg'; Image.new('RGB',(1200,900),(120,150,180)).save(good,quality=95)
bad=D/'bad.jpg'; bad.write_bytes(b'not-a-real-image')
WS.gan_anh(tm,good,roles[0]); WS.gan_anh(tm,bad,roles[1])
uploaded=[]
def up(path,ten,mime,*a,**kw):
    b=Path(path).read_bytes(); uploaded.append((Path(path),ten,b)); return 700+len(uploaded),f'https://img/{ten}'
with patch.dict(os.environ, {'WATERMARK_ENABLED':'1','WATERMARK_TEXT':'LOTECH-TEST','WATERMARK_OPACITY':'100'}, clear=False):
    k=X.dang_anh_cua_bai(tm,row,'siteA',tieu_de='MBA',slug='mba',upload=up)
clean_path=tm/X.ten_file('mba',roles[0])
clean_bytes=clean_path.read_bytes()
ck('PARTIAL-UPLOAD-KEEPS-GOOD', len(k['anh'])==1 and len(k['loi'])==1 and k.get('partial') is True, str(k))
ck('WATERMARK-UPLOAD-DIFFERS', uploaded and uploaded[0][2] != clean_bytes, f'upload={len(uploaded[0][2])} clean={len(clean_bytes)}')
ck('WATERMARK-CANONICAL-CLEAN', clean_path.is_file() and not (tm/'.wp-upload'/'sitea'/X.ten_file('mba',roles[0])).exists(), str(clean_path))
meta=WS.doc_meta(tm); rec=next(a for a in meta['anh'] if a['vai_tro']==roles[0]); d=(rec.get('delivery_by_site') or {}).get('siteA') or {}
ck('WATERMARK-SIG-PERSISTED', bool(d.get('watermark_sig')) and d.get('watermark_text')=='LOTECH-TEST', str(d))

# same watermark: good image skips, only corrupt slot retries and fails before upload
before=len(uploaded)
with patch.dict(os.environ, {'WATERMARK_ENABLED':'1','WATERMARK_TEXT':'LOTECH-TEST','WATERMARK_OPACITY':'100'}, clear=False):
    k2=X.dang_anh_cua_bai(tm,row,'siteA',tieu_de='MBA',slug='mba',upload=up)
ck('WATERMARK-IDEMPOTENT-SKIP', k2['bo_qua']==1 and len(uploaded)==before and len(k2['loi'])==1, str(k2))

# changing watermark signature must force reupload of the valid slot
with patch.dict(os.environ, {'WATERMARK_ENABLED':'1','WATERMARK_TEXT':'NEW-BRAND','WATERMARK_OPACITY':'100'}, clear=False):
    k3=X.dang_anh_cua_bai(tm,row,'siteA',tieu_de='MBA',slug='mba',upload=up)
ck('WATERMARK-CONFIG-CHANGE-REUPLOAD', len(uploaded)==before+1 and k3['da_xu_ly']==1, str(k3))

# ------------------------------------------------------------ B. partial upload must still attach valid images
obj=TA.TabAnh.__new__(TA.TabAnh); obj.v_goc=V(str(D))
b={'dataset_id':'ds','record_id':'rid','site':'site.local','mau':'chuan','sku':'SKU-WM','wp_id':'900',
   'row':row,'sheet':'S','thu_muc':tm,'ten':'MBA','slug':'mba'}
db_writes=[]; body_calls=[]; gal_calls=[]; mark_calls=[]
with patch.object(DB,'ket_noi',return_value=DummyCon()), \
     patch.object(DB,'lay_bai_viet',return_value={'html':'<div><!--SNL_IMAGE_SLOT:hero--><!--SNL_IMAGE_SLOT:bien_may--></div>'}), \
     patch.object(DB,'cap_nhat_bai_viet',side_effect=lambda *a,**kw: db_writes.append(kw) or True), \
     patch.object(AWP,'cap_nhat_noi_dung_bai_that',side_effect=lambda wid,html,la_woo=True: body_calls.append((wid,html)) or {'ok':True}), \
     patch.object(AWP,'gan_anh_vao_san_pham',side_effect=lambda wid,mids,la_woo=True: gal_calls.append((wid,list(mids))) or {'ok':True}), \
     patch.object(C,'doc_website',return_value={'che_do_dang':'woo_product'}), \
     patch.object(WS,'danh_dau_da_gan_vao_bai',side_effect=lambda *a,**kw: mark_calls.append(a[-1]) or len(a[-1])):
    rr=obj._gan_anh_vao_bai_ngay(b,k)
ck('PARTIAL-STILL-ATTACHES', rr.get('ok') and rr.get('partial') and rr.get('so_anh')==1, str(rr))
ck('PARTIAL-GALLERY-VALID-ONLY', gal_calls==[('900',[k['anh'][0]['wp_media_id']])], str(gal_calls))
ck('PARTIAL-BODY-VALID-ONLY', len(body_calls)==1 and 'https://img/' in body_calls[0][1], str(body_calls))
ck('PARTIAL-MARK-VALID-ONLY', len(mark_calls)==1 and len(mark_calls[0])==1, str(mark_calls))

# ------------------------------------------------------------ C. body success + gallery fail: persist remote body in DB
obj2=TA.TabAnh.__new__(TA.TabAnh); obj2.v_goc=V(str(D))
db_writes2=[]
with patch.object(DB,'ket_noi',return_value=DummyCon()), \
     patch.object(DB,'lay_bai_viet',return_value={'html':'<div><!--SNL_IMAGE_SLOT:hero--></div>'}), \
     patch.object(DB,'cap_nhat_bai_viet',side_effect=lambda *a,**kw: db_writes2.append(kw) or True), \
     patch.object(AWP,'cap_nhat_noi_dung_bai_that',return_value={'ok':True}), \
     patch.object(AWP,'gan_anh_vao_san_pham',return_value={'ok':False,'loi':'HTTP 400 synthetic'}), \
     patch.object(C,'doc_website',return_value={'che_do_dang':'woo_product'}):
    rr2=obj2._gan_anh_vao_bai_ngay(dict(b),{'anh':k['anh'],'loi':[]})
ck('GALLERY-FAIL-REPORTS-BODY-OK', (not rr2.get('ok')) and rr2.get('body_ok') is True and rr2.get('gallery_ok') is False, str(rr2))
ck('GALLERY-FAIL-DB-SYNCED-BODY', any('html' in w for w in db_writes2), str(db_writes2))

# ------------------------------------------------------------ D. truthful partial state
# Mark only the good slot as attached in real meta; bad slot remains local but not media.
WS.danh_dau_da_gan_vao_bai(D,'S',row,tm,'siteA','900',[dict(a, nguon='rieng') for a in k3['anh']])
tt=WS.trang_thai_hieu_luc(D,'S',row,tm,ma_site='siteA',wp_post_id='900')[0]
ck('STATE-PARTIAL-COUNT', tt.startswith('Đã gắn vào bài 1/5'), tt)

# ------------------------------------------------------------ E. stale media ID: remove only bad slot, retry good gallery
import dulieu as DL
obj3=TA.TabAnh.__new__(TA.TabAnh); obj3.v_goc=V(str(D))
k_stale={'anh':[
    {'vai_tro':'hero','url':'https://img/1.webp','alt':'1','rong':100,'cao':100,'wp_media_id':701,'nguon':'rieng'},
    {'vai_tro':'bien_may','url':'https://img/2.webp','alt':'2','rong':100,'cao':100,'wp_media_id':702,'nguon':'rieng'},
], 'loi':[]}
gal_seq=[]; body_seq=[]; invalidated=[]; purged=[]; marked=[]
def gal_stale(wid,mids,la_woo=True,timeout=60):
    gal_seq.append(list(mids))
    if len(gal_seq)==1:
        return {'ok':False,'loi':'HTTP 400: #701 is an invalid image ID','invalid_media_ids':['701']}
    return {'ok':True}
with patch.object(DB,'ket_noi',return_value=DummyCon()), \
     patch.object(DB,'lay_bai_viet',return_value={'html':'<div><!--SNL_IMAGE_SLOT:hero--><!--SNL_IMAGE_SLOT:bien_may--></div>'}), \
     patch.object(DB,'cap_nhat_bai_viet',return_value=True), \
     patch.object(AWP,'cap_nhat_noi_dung_bai_that',side_effect=lambda wid,html,la_woo=True: body_seq.append(html) or {'ok':True}), \
     patch.object(AWP,'gan_anh_vao_san_pham',side_effect=gal_stale), \
     patch.object(C,'doc_website',return_value={'che_do_dang':'woo_product'}), \
     patch.object(WS,'vo_hieu_delivery_media',side_effect=lambda *a,**kw: invalidated.append(a[-1]) or 1), \
     patch.object(DL,'xoa_cache_anh_wp_theo_media',side_effect=lambda site,mid: purged.append(str(mid)) or 1), \
     patch.object(WS,'danh_dau_da_gan_vao_bai',side_effect=lambda *a,**kw: marked.append(a[-1]) or len(a[-1])):
    rs=obj3._gan_anh_vao_bai_ngay(dict(b),k_stale)
ck('STALE-ID-RETRY-REMAINDER', rs.get('ok') and rs.get('partial') and rs.get('stale_media_ids')==['701'] and gal_seq==[[701,702],[702]], f'{rs} gal={gal_seq}')
ck('STALE-ID-PURGE-CACHE', purged==['701'] and len(invalidated)==1 and invalidated[0][0]['wp_media_id']==701, f'purged={purged}')
ck('STALE-ID-BODY-REMOVES-BAD', len(body_seq)==2 and 'https://img/1.webp' not in body_seq[-1] and 'https://img/2.webp' in body_seq[-1], str(body_seq))
ck('STALE-ID-MARK-GOOD-ONLY', len(marked)==1 and [a['wp_media_id'] for a in marked[0]]==[702], str(marked))

# ------------------------------------------------------------ F. Woo error parser extracts invalid image ID, not HTTP status
class Resp:
    status_code=400
    text='{"code":"woocommerce_product_invalid_image_id","message":"#1526 is an invalid image ID.","data":{"status":400}}'
    def json(self): return {'code':'woocommerce_product_invalid_image_id','message':'#1526 is an invalid image ID.','data':{'status':400}}
import autopost as AP
with patch.object(AP,'_auth',return_value=('https://x',None)), patch('requests.post',return_value=Resp()):
    rp=AWP.gan_anh_vao_san_pham('99',[1525,1526],la_woo=True)
ck('WOO-INVALID-ID-PARSED', rp.get('invalid_media_ids')==['1526'], str(rp))

# ------------------------------------------------------------ G. fallback source errors become warning if effective role exists
# Unit check via source contract to keep test independent from family workspace setup.
src=Path('xu_ly_anh.py').read_text(encoding='utf-8')
ck('FALLBACK-ERROR-DOWNGRADED', "canh_bao if role in role_ok else loi" in src)

print(f'TỔNG: PASS {P} / FAIL {F}')
raise SystemExit(1 if F else 0)
