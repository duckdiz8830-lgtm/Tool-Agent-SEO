# -*- coding: utf-8 -*-
"""Ver 4.4.1 — ảnh đúng vị trí + không dồn đầu bài, mock-only."""
import sys
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import xu_ly_anh as X

def legacy(so, ten):
    return (f'<!-- ẢNH {so} — {ten}. hướng dẫn (Tỷ lệ 3:2). THAY cả khối div.snl-cho-anh bên dưới bằng: '
            f'<div class="snl-anh-khung"><img src="URL_ANH" alt="{ten}"></div> -->'
            f'<div class="snl-cho-anh"><span class="snl-cho-anh-nhan">Ảnh {so}</span>'
            f'<div class="snl-cho-anh-ten">{ten}</div><p class="snl-cho-anh-mo-ta">hướng dẫn</p>'
            f'<p class="snl-cho-anh-kt">Tỷ lệ</p></div><p class="snl-anh-caption">caption</p>')

def img(role, n):
    return {'vai_tro': role, 'url': f'https://img.local/{n}.webp', 'alt': role, 'rong': 1200, 'cao': 800,
            'wp_media_id': 100+n}

old_top = ''.join(f'<figure class="snl-hinh"><img src="https://old.local/{i}.webp" alt="old" width="1" height="1"></figure>' for i in range(1,6))
html = (old_top + '<div class="snl-page">'
        '<section id="thong-so"><h2>Thông số</h2>' + legacy(2, 'Ảnh biển máy (nameplate)') + '</section>'
        '<section id="cau-tao"><h2>Sơ đồ cấu tạo</h2>' + legacy(3, 'Ảnh cận cảnh bộ phận') + '</section>'
        + legacy(4, 'Ảnh lắp đặt / toàn cảnh') + legacy(5, 'Ảnh giao hàng / vận chuyển') + '</div>')
imgs = [img('hero',1), img('bien_may',2), img('can_canh',3), img('lap_dat',4), img('giao_hang',5)]
out = X.chen_anh_vao_bai(html, imgs)
assert out.count('https://img.local/1.webp') == 1, '4.4.1.2: hero cũng phải nằm body'
assert 'old.local' not in out, 'cột ảnh 4.3 ở đầu bài phải bị bóc'
assert 'snl-cho-anh' not in out and 'URL_ANH' not in out and 'hướng dẫn' not in out
for i in (2,3,4,5):
    assert out.count(f'https://img.local/{i}.webp') == 1
assert out.index('id="thong-so"') < out.index('/2.webp') < out.index('id="cau-tao"')
assert out.index('id="cau-tao"') < out.index('/3.webp') < out.index('/4.webp') < out.index('/5.webp')

# HTML marker: có 3 ảnh (hero+bien+lap) => cả 3 phải vào body, marker trống biến mất.
html2 = ('<div class="snl-page"><!--SNL_IMAGE_SLOT:hero--><section id="thong-so">X<!--SNL_IMAGE_SLOT:bien_may--></section>'
         '<section id="cau-tao">Y<!--SNL_IMAGE_SLOT:can_canh--></section>'
         '<!--SNL_IMAGE_SLOT:lap_dat--><!--SNL_IMAGE_SLOT:giao_hang--></div>')
out2 = X.chen_anh_vao_bai(html2, [img('hero',1), img('bien_may',2), img('lap_dat',4)])
assert out2.count('<figure class="snl-hinh"') == 3
assert '/1.webp' in out2 and '/2.webp' in out2 and '/4.webp' in out2
assert 'SNL_IMAGE_SLOT' not in out2
print('PASS 12 / FAIL 0')
print('BODY_URLS=', [x for x in range(1,6) if f'/'+str(x)+'.webp' in out])
print('THREE_IMAGE_BODY_FIGURES=', out2.count('<figure class="snl-hinh"'))

# Nút Đăng ảnh: mock WordPress phải cập nhật body + gallery NGAY, không chờ render sau.
import tab_anh as TA, ai_wp_adapter as AWP, db_phase2 as DB, cauhinh as C
class DummyCon:
    def close(self): pass
calls = {'body':0,'gallery':0,'db':0}
old_ket, old_lay, old_cap = DB.ket_noi, DB.lay_bai_viet, DB.cap_nhat_bai_viet
old_body, old_gal, old_web = AWP.cap_nhat_noi_dung_bai_that, AWP.gan_anh_vao_san_pham, C.doc_website
try:
    DB.ket_noi = lambda: DummyCon()
    DB.lay_bai_viet = lambda con,did,rid,site,mau: {'html': html}
    def cap(*args, **kwargs):
        calls['db'] += 1; calls['db_html'] = kwargs.get('html'); return True
    DB.cap_nhat_bai_viet = cap
    def body(wp_id, content, la_woo=True, timeout=60):
        calls['body'] += 1; calls['content'] = content; return {'ok':True}
    def gal(wp_id, mids, la_woo=True, timeout=60):
        calls['gallery'] += 1; calls['mids'] = list(mids); return {'ok':True}
    AWP.cap_nhat_noi_dung_bai_that = body
    AWP.gan_anh_vao_san_pham = gal
    C.doc_website = lambda: {'che_do_dang':'woo_product'}
    b = {'wp_id':'1277','dataset_id':'ds','record_id':'rid','site':'maybienapvn.vn','mau':'chuan'}
    kq = {'anh': imgs}
    got = TA.TabAnh._gan_anh_vao_bai_ngay(object(), b, kq)
    assert got['ok'] and got['gan_bai']
    assert calls['body'] == 1 and calls['gallery'] == 1 and calls['db'] == 1
    assert calls['mids'] == [101,102,103,104,105]
    assert '/1.webp' in calls['content'] and '/2.webp' in calls['content']
    assert 'snl-cho-anh' not in calls['content'] and 'URL_ANH' not in calls['content']
finally:
    DB.ket_noi, DB.lay_bai_viet, DB.cap_nhat_bai_viet = old_ket, old_lay, old_cap
    AWP.cap_nhat_noi_dung_bai_that, AWP.gan_anh_vao_san_pham, C.doc_website = old_body, old_gal, old_web
print('IMMEDIATE_ATTACH=PASS body=1 gallery=1 db=1')
