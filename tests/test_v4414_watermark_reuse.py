# -*- coding: utf-8 -*-
"""4.4.1.4 — watermark domain+hotline + reuse ảnh cross-SKU, mock-only."""
import os, sys, tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
import xu_ly_anh as X
import workspace_anh as WS
import cauhinh as C

P=F=0
def ck(name, cond, detail=''):
    global P,F
    if cond:
        P += 1; print(f'PASS {name}: {detail}')
    else:
        F += 1; print(f'FAIL {name}: {detail}')

# A. Default watermark = domain + hotline, không lấy bừa site khác
with patch.dict(os.environ, {
    'WP_WEBSITE_URL':'https://www.maybienapvn.vn/',
    'WATERMARK_ENABLED':'1',
    'WATERMARK_TEXT':'',
    'WATERMARK_PHONE':'0903924986',
}, clear=False):
    c = X.cau_hinh_watermark('website')
ck('WM-DOMAIN', c.get('domain') == 'maybienapvn.vn', str(c))
ck('WM-PHONE', c.get('phone') == '0903924986', str(c))
ck('WM-TWO-LINES', c.get('lines') == ['maybienapvn.vn','0903924986'], str(c.get('lines')))
ck('WM-TEXT-COMBINED', c.get('text') == 'maybienapvn.vn | 0903924986', c.get('text'))

with patch.dict(os.environ, {
    'WP_WEBSITE_URL':'https://www.maybienapvn.vn/',
    'WATERMARK_ENABLED':'1',
    'WATERMARK_TEXT':'{domain}\\nHOTLINE {phone}',
    'WATERMARK_PHONE':'0903924986',
}, clear=False):
    c2 = X.cau_hinh_watermark('website')
ck('WM-TEMPLATE', c2.get('lines') == ['maybienapvn.vn','HOTLINE 0903924986'], str(c2.get('lines')))

# Phone rỗng: không được tự lấy hotline legacy site1/site2 khi ma_site=website
with patch.dict(os.environ, {
    'WP_WEBSITE_URL':'https://example.vn',
    'WATERMARK_ENABLED':'1',
    'WATERMARK_TEXT':'',
    'WATERMARK_PHONE':'',
    'WP_WEBSITE_HOTLINE':'',
}, clear=False):
    c3 = X.cau_hinh_watermark('website')
ck('WM-NO-WRONG-PHONE', c3.get('lines') == ['example.vn'] and not c3.get('phone'), str(c3))


# A2. Hotline có field ngay trong cấu hình Website, để không phải sửa WATERMARK_PHONE riêng
with patch.dict(os.environ, {
    'WP_WEBSITE_URL':'https://maybienapvn.vn', 'WP_WEBSITE_TEN':'MBA',
    'WP_WEBSITE_USER':'u', 'WP_WEBSITE_APP_PW':'p',
    'WP_WEBSITE_CHE_DO':'woo_product', 'WP_WEBSITE_HOTLINE':'0903924986'
}, clear=False):
    wc = C.doc_website()
ck('WEB-CONFIG-HOTLINE-READ', wc.get('hotline')=='0903924986', str(wc))
kw=[]
with patch.object(C,'ghi_env',side_effect=lambda **x: kw.append(x)):
    C.luu_website('MBA','https://maybienapvn.vn','u','p','woo_product',hotline='0903924986')
ck('WEB-CONFIG-HOTLINE-SAVE', bool(kw) and kw[0].get('WP_WEBSITE_HOTLINE')=='0903924986', str(kw))
ui_src=Path(__file__).resolve().parents[1].joinpath('giao-dien.py').read_text(encoding='utf-8')
ck('WEB-CONFIG-HOTLINE-UI', 'Hotline watermark' in ui_src and 'v3_web_hotline' in ui_src, '')

# B. Render watermark thật, canonical input không bị ghi đè
D = Path(tempfile.mkdtemp())
src = D/'src.webp'
Image.new('RGB',(1000,700),(180,190,200)).save(src,'WEBP',quality=90)
b0 = src.read_bytes()
with patch.dict(os.environ, {
    'WP_WEBSITE_URL':'https://maybienapvn.vn',
    'WATERMARK_ENABLED':'1', 'WATERMARK_TEXT':'', 'WATERMARK_PHONE':'0903924986',
    'WATERMARK_OPACITY':'110'
}, clear=False):
    bw, info = X.them_watermark_webp(b0,'website')
ck('WM-BYTES-CHANGED', bw != b0 and info.get('phone')=='0903924986', f"{len(b0)}->{len(bw)}")
ck('WM-SOURCE-UNCHANGED', src.read_bytes() == b0, str(src))

# C. Cùng một ảnh nguồn được phép gán cho 3 SKU khác nhau, KHÔNG chặn reuse
root = D/'images'; root.mkdir()
source = D/'same.jpg'; Image.new('RGB',(1100,800),(100,130,160)).save(source,quality=95)
rows=[]; workspaces=[]
for i in range(1,4):
    row={'ma_goc':f'SKU{i}','publish_sku':f'SKU{i}','ten_goc':f'MBA {i}',
         'profile_id':'may_bien_ap_do_luong','record_id':f'r{i}'}
    tm=WS.tao_workspace(root,'S',i,row,title=f'MBA {i}',slug=f'sku-{i}')
    role=WS.ma_vai_tro(row['profile_id'])[0]
    WS.gan_anh(tm,source,role)
    rows.append(row); workspaces.append(tm)

m0=WS.doc_meta(workspaces[0]); h0=m0['anh'][0].get('hash_goc')
ck('REUSE-THREE-SAME-HASH', all((WS.doc_meta(tm)['anh'][0].get('hash_goc')==h0) for tm in workspaces), h0)
ck('REUSE-COUNT-NONBLOCK', WS.dem_dung_chung(root,'S',h0)==2, str(WS.dem_dung_chung(root,'S',h0)))

uploads=[]
def up(path,ten,mime,*a,**kw):
    uploads.append((ten,Path(path).read_bytes()))
    return 800+len(uploads), f'https://img/{ten}'

results=[]
with patch.dict(os.environ, {'WATERMARK_ENABLED':'0'}, clear=False):
    for i,(row,tm) in enumerate(zip(rows,workspaces),1):
        results.append(X.dang_anh_cua_bai(tm,row,'website',tieu_de=f'MBA {i}',slug=f'sku-{i}',upload=up))
ck('REUSE-3-SKU-UPLOADS', all(r.get('ok') and len(r.get('anh') or [])==1 for r in results) and len(uploads)==3, str([r.get('loi') for r in results]))
ck('REUSE-SEO-FILENAME-PER-SKU', [u[0] for u in uploads] == ['sku-1-hero.webp','sku-2-hero.webp','sku-3-hero.webp'], str([u[0] for u in uploads]))

# D. Contract: 1 slot lỗi không được chặn attach phần tốt vẫn còn trong 4.4.1.4
src_code=Path(__file__).resolve().parents[1].joinpath('tab_anh.py').read_text(encoding='utf-8')
ck('FORCE-BEST-EFFORT-CONTRACT', "if kq.get('anh')" in src_code and "không dùng ``loi`` upload làm công tắc chặn attach" in src_code, '')

print(f'TỔNG: PASS {P} / FAIL {F}')
raise SystemExit(1 if F else 0)
