# -*- coding: utf-8 -*-
"""Ver 3.9 B1-B2: dấu ≤ chỉ Po/Pk; nhãn catalogue_hang đúng nguồn."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import nhap_phase2 as N
import render_phase2 as R

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
master = os.path.join(base, '8MASTER_ENRICHED_Ver8.xlsx')
data = N.import_4_profile(master, chi_profile='may_bien_ap_do_luong')['may_bien_ap_do_luong']['rows']

# B1 dùng đúng record thật trong MASTER Ver8: TBD1P15 có Po=52, Pk=213, Uk=2, Io=1, ký hiệu ≤.
r = next(x for x in data if x['ma_goc'] == 'TBD1P15')
html = R._dong_bang_thong_so_dong(r)
assert '≤ 52' in html, html
assert '≤ 213' in html, html
assert '>≤ 2</td>' not in html, html
assert '>≤ 1</td>' not in html, html

# B2: đếm đúng từ MASTER Ver8, không lấy số từ brief.
cat = [x for x in data if x.get('nguon_loai_so_lieu') == 'catalogue_hang']
kp = [x for x in cat if 'KP' in str(x.get('thuong_hieu','')).upper()]
assert len(cat) == 9, len(cat)
assert len(kp) == 8, len(kp)
for x in cat:
    h = R._dong_bang_thong_so_dong(x)
    assert 'cực đại theo tiêu chuẩn EVN' not in h, (x['ma_goc'], h)
    # chỉ những cột gốc có nhãn W/EVN mới đổi thành catalogue hãng;
    # ít nhất Po/Pk thật trong các row catalogue phải có nhãn này.
    if x.get('thong_so_dong'):
        assert 'catalogue hãng' in h, (x['ma_goc'], h)

print('PASS B1: TBD1P15 Po/Pk có ≤; Uk=2 và Io=1 không có ≤')
print(f'PASS B2: MASTER Ver8 catalogue_hang={len(cat)} dòng; trong đó KP={len(kp)} dòng; nhãn EVN bị loại đúng nguồn')
