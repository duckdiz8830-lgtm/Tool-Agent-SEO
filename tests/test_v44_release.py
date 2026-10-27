# -*- coding: utf-8 -*-
"""Ver 4.4 — acceptance tối thiểu A/B/C/D, không mạng thật."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ai_wp_adapter as AWP
import khoi_anh as KA
import render_phase2 as R
import workspace_anh as WS
import xu_ly_anh as XA
import tab_anh as TA

P = F = 0

def ck(name, cond, detail=''):
    global P, F
    if cond:
        P += 1; print(f'PASS {name}: {detail}')
    else:
        F += 1; print(f'FAIL {name}: {detail}')

# A1/A2: placeholder/comment URL_ANH biến mất hoàn toàn.
roles = ['hero','bien_may','can_canh','lap_dat','giao_hang']
ck('A1-EMPTY-SLOTS-HIDDEN', all(KA.cho_anh(r) == '' for r in roles), str([KA.cho_anh(r) for r in roles]))
ck('A1-LEGACY-PLACEHOLDER-HIDDEN', R.khoi_anh_placeholder('ảnh sản phẩm') == '', repr(R.khoi_anh_placeholder()))
three = XA.khoi_anh_bai([
    {'url':'https://x/1.webp','alt':'a','rong':100,'cao':100,'nhan':'1'},
    {'url':'https://x/2.webp','alt':'b','rong':100,'cao':100,'nhan':'2'},
    {'url':'https://x/3.webp','alt':'c','rong':100,'cao':100,'nhan':'3'},
])
ck('A1-THREE-MEANS-THREE', three.count('<figure') == 3 and 'snl-cho-anh' not in three and 'URL_ANH' not in three,
   f'figures={three.count("<figure")}')

# B1: Woo UPDATE có wp_id cũ vẫn gửi slug mới trong payload.
class Con:
    def close(self): pass
class Resp:
    status_code = 200; text = ''; headers = {'Content-Type':'application/json'}
    def json(self): return {'id': 321, 'permalink':'https://real.local/san-pham/slug-moi/'}
posted=[]
def fake_post(url, *a, **kw):
    payload=json.loads((kw.get('data') or b'{}').decode('utf-8'))
    posted.append((url,payload))
    return Resp()
with patch('cauhinh.doc_website', return_value={'url':'https://real.local','user':'u','app_pw':'p'}), \
     patch('autopost._auth', return_value=('https://real.local', ('u','p'))), \
     patch('db_phase2.ket_noi', return_value=Con()), \
     patch('requests.post', side_effect=fake_post):
    out=AWP.dang_woo_that('D','R','real.local','chuan','Tên','may-bien-ap-dau-mbt-750kva-3-pha-amorphous',
                          '<p>x</p>','m',ma_hang='SKU',da_co_woo_id=321)
ck('B1-WOO-UPDATE-SENDS-SLUG', out.get('ok') and posted and posted[0][0].endswith('/products/321')
   and posted[0][1].get('slug') == 'may-bien-ap-dau-mbt-750kva-3-pha-amorphous', str(posted))

# SEO-only path đã là đường rẻ cho bài đang tồn tại.
posted.clear()
with patch('cauhinh.doc_website', return_value={'url':'https://real.local','user':'u','app_pw':'p'}), \
     patch('autopost._auth', return_value=('https://real.local', ('u','p'))), \
     patch('requests.post', side_effect=fake_post):
    out2=AWP.cap_nhat_seo_woo_that(321,'Tên mới','slug-moi',{'rank_math_title':'SEO'})
ck('B1-SEO-ONLY-SENDS-SLUG', out2.get('ok') and posted[0][1].get('slug') == 'slug-moi', str(posted))

# C/D static contract: extensions thật đi qua workspace + UI helper có đủ chức năng.
exts=['.jfif','.webp','.heic','.bmp','.avif']
ck('D2-WORKSPACE-EXTENSIONS', all(WS.la_anh('x'+e) for e in exts), str([(e,WS.la_anh('x'+e)) for e in exts]))
obj=TA.TabAnh.__new__(TA.TabAnh)
ft=' '.join(x[1] for x in obj._filetypes_anh())
ck('D2-PICKER-EXTENSIONS', all(e.lstrip('.') in ft for e in exts), ft)
src=Path('tab_anh.py').read_text(encoding='utf-8')
ck('C-TAB-IMAGE-CONTRACT', all(x in src for x in ['trace_add','_sap_xep_anh','<Control-f>','selectmode=\'extended\'','Gán ảnh chung','Đăng ảnh hàng loạt','dòng {n}/']), 'search/sort/ctrl-f/multiselect/stt')
gui=Path('giao-dien.py').read_text(encoding='utf-8')
ck('C-TRACKER-CONTRACT', all(x in gui for x in ['v3_dash_tim','_v3_sort_dashboard','Đăng lại bài lỗi đã chọn','_v3_xem_loi_chi_tiet','selectmode=\'extended\'']), 'tracker search/sort/retry/error/multiselect')
ck('D1-COPY-CONTEXT', "bind_class('Treeview', '<Button-3>'" in gui and "bind_class('TLabel', '<Button-3>'" in gui, 'Treeview+Label')
ck('D3-GOOGLE-IMAGES', 'tbm=isch' in src and 'quote_plus(q)' in src, 'Google Images URL')
ck('D4-DOWNLOADS', "Path.home() / 'Downloads'" in src and 'initialdir=self._downloads()' in src, 'picker initialdir')

print(f'TỔNG: PASS {P} / FAIL {F}')
raise SystemExit(1 if F else 0)
