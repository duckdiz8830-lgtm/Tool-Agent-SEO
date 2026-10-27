# -*- coding: utf-8 -*-
"""Test Ver 2.3 (Mốc 2) — hình kỹ thuật SVG sinh từ dữ liệu.

Trọng tâm: KHÔNG vẽ khi thiếu dữ liệu (nguyên tắc y hệt Hard Block —
thà không có hình còn hơn vẽ sai cấu tạo).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import hinh_ky_thuat as H
import render_phase2 as R

so_pass = so_fail = 0


def kt(t, dk, gc=''):
    global so_pass, so_fail
    if dk:
        so_pass += 1
        print(f'[PASS] {t}')
    else:
        so_fail += 1
        print(f'[FAIL] {t} {gc}')


cap_du = {'outline_id': 'outline_cap_dien', 'tiet_dien': '3x70',
          'vat_lieu_ruot_giai_ma': 'Đồng (Cu)', 'loai_cach_dien_giai_ma': 'XLPE',
          'vo_boc_giai_ma': 'PVC', 'giap_bao_ve_giai_ma': 'Giáp thép dạng băng/dải 2 lớp'}
cap_thieu = {'outline_id': 'outline_cap_dien', 'tiet_dien': '2x1.5'}
mba_du = {'outline_id': 'outline_may_bien_ap', 'kich_thuoc_a': '1450 mm',
          'kich_thuoc_b': '1000 mm', 'kich_thuoc_c': '1450 mm'}
mba_thieu = {'outline_id': 'outline_may_bien_ap', 'cong_suat': '250 kVA'}

h_cap = H.hinh_cho_row(cap_du)
h_mba = H.hinh_cho_row(mba_du)

kt('H1: cáp đủ dữ liệu -> có SVG', '<svg' in h_cap and 'Đồng (Cu)' in h_cap)
kt('H2: cáp THIẾU dữ liệu -> KHÔNG vẽ (không đoán)', H.hinh_cho_row(cap_thieu) == '')
kt('H3: MBA đủ kích thước -> có SVG', '<svg' in h_mba)
kt('H4: MBA THIẾU kích thước -> KHÔNG vẽ', H.hinh_cho_row(mba_thieu) == '')
kt('H5: outline không thuộc loại có hình -> KHÔNG vẽ',
   H.hinh_cho_row({'outline_id': 'outline_phu_kien'}) == '')
kt('H6: mọi hình ghi rõ "không theo tỷ lệ" (chống hiểu nhầm là bản vẽ thi công)',
   'không theo tỷ lệ' in h_cap and 'không theo tỷ lệ' in h_mba)
kt('H7: SVG KHÔNG chứa script/style/ảnh ngoài (an toàn khi đăng WordPress)',
   all(x not in h_cap for x in ('<script', '<style', '<image', 'onload')))

for td, mong in (('3x70', 3), ('2x0.5', 2), ('95', 1), ('3x50+1x35', 4),
                 ('abc', None), (None, None), ('12x2.5', None)):
    kt(f'H8 [{td!r}]: số lõi -> {mong}', H._so_loi(td) == mong, f'thực tế {H._so_loi(td)}')

ai = {'meta_title': 'T', 'meta_description': 'M', 'intro_html': '<p>a</p>',
      'dac_diem_html': '<p>b</p>', 'ung_dung_html': '<p>c</p>',
      'huong_dan_chon_html': '<p>d</p>'}
row_bai = dict(cap_du, profile_id='cap_dien', ma_goc='X',
               ten_goc='Dây CXV/DSTA3x70mm2', thuong_hieu='Cadivi', dvt='M',
               cap_dien_ap='0.6/1kV')
bai = R.dung_bai_html(row_bai, ai, {'ten': 'X'})['html']
kt('H9: bài CÓ hình -> KHÔNG còn ô placeholder ảnh (2 thứ cùng chỗ là thừa)',
   '<svg' in bai and 'CHỖ CHÈN' not in bai)

row_khong_hinh = {'profile_id': 'phu_kien_va_khac', 'outline_id': 'outline_phu_kien',
                  'ma_goc': 'Y', 'ten_goc': 'Phụ kiện', 'thuong_hieu': 'X', 'dvt': 'Cái'}
bai2 = R.dung_bai_html(row_khong_hinh, ai, {'ten': 'X'})['html']
kt('H10: Ver 4.4 bài KHÔNG có hình -> ẩn hoàn toàn placeholder',
   '<svg' not in bai2 and 'CHỖ CHÈN' not in bai2 and 'snl-cho-anh' not in bai2 and 'URL_ANH' not in bai2)

print(f'\nTỔNG VER 2.3 (hình kỹ thuật): {so_pass}/{so_pass + so_fail} PASS')
sys.exit(1 if so_fail else 0)
