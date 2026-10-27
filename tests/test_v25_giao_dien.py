# -*- coding: utf-8 -*-
"""Test Ver 2.5 — bố cục cao cấp.

Trọng tâm: bật/tắt không phá bố cục cũ, khối tự ẩn khi thiếu dữ liệu,
Hard Block và schema giữ nguyên (giao diện KHÔNG được đụng vào dữ liệu).
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import giao_dien_2_5 as G2
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


ROW = {'profile_id': 'may_bien_ap_do_luong', 'outline_id': 'outline_may_bien_ap',
       'ma_goc': 'TBD3P560A', 'thuong_hieu': 'THIBIDI', 'dvt': 'Máy',
       'ten_goc': 'Máy biến áp dầu 3Pha 560KVA 22/0.4KV Loại Amorphous, kiểu kín',
       'cong_suat': '560 kVA', 'cap_dien_ap': '22/0.4 kV'}
AI = {'meta_title': 'T', 'meta_description': 'M',
      'intro_html': '<p>Giới thiệu.</p>', 'dac_diem_html': '<p>Đặc điểm.</p>',
      'ung_dung_html': '<p>Ứng dụng.</p>', 'huong_dan_chon_html': '<p>Hướng dẫn.</p>',
      'faq': [{'q': 'Bảo hành?', 'a': 'Theo chính sách hãng.'}]}
SITE = {'ten': 'MBA VN', 'hotline': '0903924986'}


def _bai(bat):
    os.environ['GIAO_DIEN_2_5'] = '1' if bat else '0'
    h = R.dung_bai_html(ROW, AI, SITE)
    os.environ['GIAO_DIEN_2_5'] = '0'
    return h


cu, moi = _bai(False), _bai(True)

# ---------- A. Bật/tắt ----------
kt('A1: mặc định TẮT -> bố cục cũ giữ nguyên (không có class 2.5)',
   'snl-hero' not in cu['html'] and 'snl-kicker' not in cu['html'])
# Ver 2.6 — hero (chip/quick/giá/CTA) TÁCH sang short_description để
# WooCommerce hiện nó ngay cạnh ảnh ở đầu trang. Nên html chỉ còn thân
# bài; kiểm cả 2 phần cộng lại.
_ca_bai = moi['html'] + moi.get('short_description', '')
# Ver 3.6.2 — chip/quick BỎ khỏi hero theo góp ý sếp (lặp lại H1 tới 3 lần).
# Mặc định tắt, bật lại bằng HERO_HIEN_CHIP_QUICK=1. Test tách làm 2:
kt('A2: bật -> có đủ khối mới (hero/nav/faq/cta) trên cả 2 phần',
   all(k in _ca_bai for k in ('snl-hero', 'snl-nav', 'snl-faq', 'snl-cta')))
kt('A2-chip: chip/quick KHÔNG hiện khi chưa bật cờ (Ver 3.6.2)',
   'snl-chip' not in _ca_bai and 'snl-quick' not in _ca_bai)
os.environ['HERO_HIEN_CHIP_QUICK'] = '1'
_co_chip = G2.dung_bai_2_5(ROW, AI, SITE, tach_hero=True)["hero"]
os.environ.pop('HERO_HIEN_CHIP_QUICK', None)
kt('A2-chip2: bật cờ thì chip/quick hiện lại',
   'snl-chip' in _co_chip and 'snl-quick' in _co_chip)
kt('A2b: hero nằm ở short_description, KHÔNG nằm trong html (Ver 2.6)',
   'snl-hero' in moi.get('short_description', '') and 'snl-hero' not in moi['html'])
kt('A3: FAQ dùng <details> (gập/mở không cần JS)', '<details' in moi['html'])

# ---------- B. Dữ liệu KHÔNG bị giao diện đụng vào ----------
# Ver 2.5 — schema PHẢI trả qua key riêng, KHÔNG nhét vào html: WordPress
# lọc thẻ <script> khi POST REST API nhưng giữ text bên trong -> JSON-LD
# hiện thành chữ thật trên trang (lỗi đã xảy ra và đã vá ở bản trước).
kt('B1: schema KHÔNG nằm trong html ở cả 2 chế độ (chống lộ JSON thành chữ)',
   'application/ld+json' not in cu['html'] and 'application/ld+json' not in moi['html'])
kt('B1b: schema vẫn được trả qua key riêng ở bố cục mới',
   isinstance(moi.get('schema'), dict) and bool(moi.get('schema')))
kt('B2: title giống hệt nhau (giao diện không đổi tiêu đề)',
   cu['title'] == moi['title'], f"{cu['title']} vs {moi['title']}")
kt('B3: slug giống hệt nhau', cu['slug'] == moi['slug'])
kt('B4: meta_description giống hệt nhau',
   cu['meta_description'] == moi['meta_description'])
for so in ('560', '22/0.4'):
    kt(f'B5 [{so}]: số liệu thật vẫn xuất hiện ở bố cục mới', so in moi['html'])

# ---------- C. Khối tự ẩn khi thiếu dữ liệu ----------
kt('C1: chip bỏ mục rỗng', G2.khoi_chip([('A', False), ('', False), (None, False)])
   .count('<li') == 1)
kt('C2: chip rỗng hoàn toàn -> trả ""', G2.khoi_chip([('', False)]) == '')
kt('C3: quick bỏ cặp thiếu giá trị',
   G2.khoi_quick([('X', '1'), ('Y', ''), ('Z', None)]).count('snl-quick-o') == 1)
kt('C4: quick rỗng -> trả ""', G2.khoi_quick([('X', '')]) == '')
kt('C5: mục lục dưới 2 mục -> KHÔNG dựng (thừa)',
   G2.khoi_muc_luc([('a', 'A')]) == '')
kt('C6: FAQ thiếu câu trả lời -> bỏ mục đó',
   G2.khoi_faq([('Hỏi', ''), ('Hỏi 2', 'Đáp')]).count('<details') == 1)

# ---------- D. CSS ----------
css = R.xuat_file_css()
kt('D1: CSS xuất ra GỘP cả bộ cũ lẫn bộ 2.5 (dán 1 lần)',
   '.snl-specs-table {' in css and '.snl-hero {' in css)
kt('D2: mọi class trong STYLE_2_5 đều có trong CSS xuất ra',
   all(f'.snl-{k} ' in css for k in G2.STYLE_2_5))
kt('D3: CSS cân bằng ngoặc', css.count('{') == css.count('}'))

# ---------- E. Chống vỡ ----------
row_thieu = {'profile_id': 'phu_kien_va_khac', 'outline_id': 'outline_phu_kien',
             'ma_goc': 'X1', 'ten_goc': 'Phụ kiện abc', 'thuong_hieu': '', 'dvt': ''}
os.environ['GIAO_DIEN_2_5'] = '1'
try:
    h = R.dung_bai_html(row_thieu, {'meta_description': ''}, {})
    ok_thieu = bool(h['html'])
except Exception as e:
    ok_thieu = False
    print('   lỗi:', e)
os.environ['GIAO_DIEN_2_5'] = '0'
kt('E1: record thiếu gần hết dữ liệu vẫn dựng được bài, không crash', ok_thieu)

txt = lambda h: ' '.join(re.sub(r'<[^>]+>', ' ', h).split())
_text_moi = txt(moi['html'] + moi.get('short_description', ''))
kt('E2: bố cục mới KHÔNG làm mất nội dung text (tính cả short_description)',
   len(_text_moi) >= len(txt(cu['html'])) * 0.9,
   f"cũ {len(txt(cu['html']))} vs mới {len(_text_moi)}")

print(f'\nTỔNG VER 2.5 (bố cục cao cấp): {so_pass}/{so_pass + so_fail} PASS')
sys.exit(1 if so_fail else 0)
