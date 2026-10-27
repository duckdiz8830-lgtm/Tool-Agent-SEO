# -*- coding: utf-8 -*-
"""4.4.1.2 — 5 ảnh phải đồng thời ở Woo gallery và body, kể cả HTML cũ mất marker."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import xu_ly_anh as X

def img(role, n):
    return {'vai_tro': role, 'url': f'https://img.local/{n}.webp', 'alt': role,
            'rong': 1200, 'cao': 800, 'wp_media_id': 200+n}

imgs=[img('hero',1),img('bien_may',2),img('can_canh',3),img('lap_dat',4),img('giao_hang',5)]
html=(
    '<div class="snl-page"><nav class="snl-nav">NAV</nav>'
    '<section class="snl-section" id="thong-so"><h2>Thông số kỹ thuật</h2><table><tr><td>x</td></tr></table></section>'
    '<section class="snl-section" id="dac-diem"><h2>Đặc điểm</h2><p>a</p></section>'
    '<section class="snl-section" id="ung-dung"><h2>Ứng dụng</h2><p>b</p></section>'
    '<section class="snl-section" id="kien-thuc"><h2>Kiến thức</h2><p>c</p></section></div>'
)
out=X.chen_anh_vao_bai(html, imgs)
for i in range(1,6):
    assert out.count(f'https://img.local/{i}.webp')==1, (i, out.count(f'https://img.local/{i}.webp'))
for role in ('hero','bien_may','can_canh','lap_dat','giao_hang'):
    assert out.count(f'data-snl-role="{role}"')==1
assert out.index('/1.webp') < out.index('id="thong-so"')
assert out.index('id="thong-so"') < out.index('/2.webp') < out.index('id="dac-diem"')
assert out.index('id="dac-diem"') < out.index('/3.webp')
assert out.index('id="ung-dung"') < out.index('/4.webp')
assert out.index('/5.webp') > out.index('id="kien-thuc"')
imgs2=[dict(a, url=a['url'].replace('img.local','img2.local')) for a in imgs]
out2=X.chen_anh_vao_bai(out, imgs2)
for i in range(1,6):
    assert out2.count(f'https://img2.local/{i}.webp')==1
    assert f'https://img.local/{i}.webp' not in out2
print('PASS dual-delivery markerless + idempotent: 12/12')
