# -*- coding: utf-8 -*-
"""Ver 3.9 C1-C6 — title/slug/meta + metadata-only Woo mock, không gọi site thật."""
import os, sys, json, inspect, re
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import nhap_phase2 as N
import render_phase2 as R
import ai_wp_adapter as AWP
import autopost
import requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(BASE, '8MASTER_ENRICHED_Ver8.xlsx')
rows = N.import_4_profile(MASTER, chi_profile='may_bien_ap_do_luong')['may_bien_ap_do_luong']['rows']
mba = [r for r in rows if r['outline_id'] == 'outline_may_bien_ap']
mof = [r for r in rows if r['outline_id'] == 'outline_do_luong' and re.search(r'\bMOF\b', r.get('ten_goc',''), re.I)]
target = [r for r in rows if R.dung_goi_cap_nhat_seo(r)]

assert len(rows) == 245, len(rows)
assert len(mba) == 141, len(mba)
assert len(mof) == 9, len(mof)
assert len(target) == 150, len(target)

# C1 + C3: title MBA duy nhất trên chính MASTER Ver8.
titles = defaultdict(list)
for r in mba:
    titles[R.dung_tieu_de(r)].append(r['ma_goc'])
assert not {k:v for k,v in titles.items() if len(v) > 1}
for sku in ('MBT3P250A107', 'MBT3P250A2608'):
    t = R.dung_tieu_de(next(r for r in mba if r['ma_goc'] == sku))
    assert ('QĐ 107' in t) if sku.endswith('A107') else ('QĐ 2608' in t)

# C2: file thật có 9 MOF (brief nêu 7); cả 9 title code đều mang tỷ số và unique.
mof_titles = [R.dung_tieu_de(r) for r in mof]
assert len(set(mof_titles)) == 9
for r, t in zip(mof, mof_titles):
    assert '\n' not in t and '\r' not in t
    assert re.search(r'\d+(?:-\d+)?/5A', t), (r['ma_goc'], t)

# C3: cả 20 A2608 có note nguồn dưới bảng, lấy từ field MASTER.
a2608 = [r for r in mba if 'A2608' in r['ma_goc']]
assert len(a2608) == 20
for r in a2608:
    h = R.bang_thong_so(r)
    assert 'TCCS 10:2021/EVN' in h and 'chưa đối chiếu QĐ 2608/QĐ-EVN SPC' in h

# C4: slug mới, không SKU/Cu-Cu/chuan; 141 MBA không collision.
slugs = defaultdict(list)
for r in mba:
    s = R.dung_slug(r)
    slugs[s].append(r['ma_goc'])
    assert 'cu-cu' not in s and not s.endswith('-chuan') and '-chuan-' not in s
    ma_slug = re.sub(r'[^a-z0-9]+', '-', r['ma_goc'].lower()).strip('-')
    assert ma_slug not in s, (r['ma_goc'], s)
assert not {k:v for k,v in slugs.items() if len(v) > 1}
assert R.dung_slug(next(r for r in mba if r['ma_goc']=='KPK2500CU')) == 'may-bien-ap-kho-kp-2500kva'
assert R.dung_slug(next(r for r in mba if r['ma_goc']=='TBD3P250')) == 'may-bien-ap-dau-thibidi-250kva-3-pha-silic'

# C5: 3 meta bằng code; title/description đúng độ dài, description qua Hard Block.
focus = defaultdict(list); seo_titles = defaultdict(list)
for r in mba:
    m = R.dung_rank_math(r, {'title': R.dung_tieu_de(r)})
    assert set(m) == {'rank_math_focus_keyword','rank_math_title','rank_math_description'}
    assert len(m['rank_math_title']) <= 60
    assert len(m['rank_math_description']) <= 160
    assert 'đang cập nhật' not in m['rank_math_description'].lower()
    assert 'báo giá' not in m['rank_math_description'].lower()
    assert R.kiem_tra_bia(m['rank_math_description'], r) == []
    focus[m['rank_math_focus_keyword']].append(r['ma_goc'])
    seo_titles[m['rank_math_title']].append(r['ma_goc'])
assert not {k:v for k,v in focus.items() if len(v) > 1}
assert not {k:v for k,v in seo_titles.items() if len(v) > 1}

# C6: mock HTTP. Không site thật. Payload phải CHỈ name/slug/meta_data.
class Resp:
    status_code = 200
    text = ''
    def json(self): return {'id': 999, 'permalink': 'https://mock.local/p/999'}

calls = []
old_auth = autopost._auth
old_post = requests.post
try:
    autopost._auth = lambda _site: ('https://mock.local', object())
    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return Resp()
    requests.post = fake_post
    sample = next(r for r in mba if r['ma_goc'] == 'TBD3P250')
    goi = R.dung_goi_cap_nhat_seo(sample)
    kq = AWP.cap_nhat_seo_woo_that('321', goi['title'], goi['slug'], goi['meta_rank_math'])
finally:
    autopost._auth = old_auth
    requests.post = old_post
assert kq['ok'] and len(calls) == 1
payload = json.loads(calls[0][1]['data'].decode('utf-8'))
assert set(payload) == {'name','slug','meta_data'}, payload
assert 'description' not in payload and 'short_description' not in payload and 'sku' not in payload

# Production wiring tồn tại: nút -> worker -> metadata-only adapter, worker không gọi AI/render content.
gui_src = open(os.path.join(BASE, 'giao-dien.py'), encoding='utf-8').read()
assert 'command=self._v3_bam_cap_nhat_seo' in gui_src
assert 'def _v3_cap_nhat_seo_worker' in gui_src
worker = gui_src[gui_src.index('    def _v3_cap_nhat_seo_worker'):gui_src.index('    def _v3_dang_draft_that', gui_src.index('    def _v3_cap_nhat_seo_worker'))]
assert 'cap_nhat_seo_woo_that' in worker
assert 'goi_ai' not in worker and 'dung_bai_html' not in worker

print('PASS C1: MASTER Ver8 MBA=141, duplicate title groups=0')
print('PASS C2: MASTER Ver8 MOF=9 (không phải 7), 9/9 title có tỷ số và unique')
print('PASS C3: A2608=20, 20/20 bảng có note nguồn TCCS/chưa đối chiếu QĐ2608')
print('PASS C4: 141/141 slug MBA unique; 0 slug chứa SKU/Cu-Cu/chuan')
print('PASS C5: 141/141 Rank Math qua Hard Block; focus/title duplicate groups=0; title<=60, desc<=160')
print('PASS C6: target từ MASTER Ver8=150 SKU (141 MBA + 9 MOF); mock Woo POST=1; payload keys=name,slug,meta_data; AI calls=0')
