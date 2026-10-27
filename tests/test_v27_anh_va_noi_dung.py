# -*- coding: utf-8 -*-
"""Test Ver 2.7 ULTRA — module ảnh sản phẩm + các sửa đổi nhóm 1."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import anh_san_pham as A
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


# ---------- A. Parse tên file (mẫu THẬT từ Drive của Thịnh) ----------
for ten, cs_mong, hang_mong, tin_mong in (
        ('mba dau mbt 250kva.jpg', 250.0, 'MBT', 'cao'),
        ('mba mbt 1p 25kva.jpg', 25.0, 'MBT', 'cao'),
        ('MBA_MBT_3P_560KVA (2).jpg', 560.0, 'MBT', 'cao'),
        ('mba dau mbt 320kv.jpg', 320.0, 'MBT', 'cao'),
        ('z7247219391950_47.jpg', None, None, 'khong'),
        ('phan phoi mba dau.jpg', None, None, 'khong'),
):
    p = A.phan_tich_ten_file(ten)
    kt(f'A [{ten[:26]}] -> {cs_mong} kVA / {hang_mong}',
       p['cong_suat'] == cs_mong and p['thuong_hieu'] == hang_mong
       and p['do_tin_cay'] == tin_mong,
       f"thực tế {p['cong_suat']}/{p['thuong_hieu']}/{p['do_tin_cay']}")

kt('A-dienap: "22kv" KHÔNG bị nhận nhầm thành công suất (là điện áp)',
   A.phan_tich_ten_file('mba mbt 22kv.jpg')['cong_suat'] is None)

# ---------- B. Ghép ảnh với SKU ----------
ROWS = [
    {'ma_goc': 'MBT3P250A2608', 'record_id': 'r1', 'thuong_hieu': 'MBT',
     'ten_goc': 'Máy biến áp dầu 3Pha 250KVA 22/0.4KV Loại Amorphous', 'cong_suat': '250 kVA'},
    {'ma_goc': 'MBT1P25A2608', 'record_id': 'r2', 'thuong_hieu': 'MBT',
     'ten_goc': 'Máy biến áp dầu 1Pha 25KVA 12.7/0.23KV Loại Amorphous', 'cong_suat': '25 kVA'},
    {'ma_goc': 'TBD3P250', 'record_id': 'r3', 'thuong_hieu': 'THIBIDI',
     'ten_goc': 'Máy biến áp dầu 3Pha 250KVA 22/0.4KV Silic', 'cong_suat': '250 kVA'},
]

row, ly_do = A.ghep_anh_voi_sku(A.phan_tich_ten_file('mba dau mbt 250kva.jpg'), ROWS)
kt('B1: ảnh MBT 250kVA ghép đúng SKU MBT (không nhầm sang THIBIDI cùng 250kVA)',
   row and row['ma_goc'] == 'MBT3P250A2608', row['ma_goc'] if row else None)

row2, _ = A.ghep_anh_voi_sku(A.phan_tich_ten_file('mba mbt 1p 25kva.jpg'), ROWS)
kt('B2: ảnh 1 pha 25kVA ghép đúng', row2 and row2['ma_goc'] == 'MBT1P25A2608')

row3, ly_do3 = A.ghep_anh_voi_sku(A.phan_tich_ten_file('z7247219391950.jpg'), ROWS)
kt('B3: tên vô nghĩa -> KHÔNG ghép, báo cần gán tay',
   row3 is None and 'gán tay' in ly_do3)

row4, ly_do4 = A.ghep_anh_voi_sku(A.phan_tich_ten_file('mba mbt 999kva.jpg'), ROWS)
kt('B4: công suất không có SKU nào -> KHÔNG ghép bừa', row4 is None)

row5, _ = A.ghep_anh_voi_sku(A.phan_tich_ten_file('mba mbt 3p 25kva.jpg'), ROWS)
kt('B5: số pha MÂU THUẪN (ảnh 3 pha, SKU 25kVA là 1 pha) -> loại',
   row5 is None, row5['ma_goc'] if row5 else 'None')

# ---------- C. Tên file SEO + alt ----------
ten_seo = A.ten_file_seo(ROWS[0])
kt('C1: tên file SEO có nghĩa, đuôi webp',
   ten_seo.endswith('.webp') and 'may-bien-ap' in ten_seo, ten_seo)
kt('C2: ảnh thứ 2 có hậu tố khác để không đè nhau',
   A.ten_file_seo(ROWS[0], thu_tu=2) != ten_seo)
kt('C3: alt text chứa tên sản phẩm', 'Máy biến áp' in A.alt_text(ROWS[0]))
kt('C4: alt ảnh thứ 3 khác ảnh thứ 1 (không trùng lặp)',
   A.alt_text(ROWS[0], 3) != A.alt_text(ROWS[0], 1))

# ---------- D. Tối ưu ảnh ----------
try:
    from PIL import Image
    tmp = tempfile.mktemp(suffix='.jpg')
    Image.new('RGB', (3000, 2000), (200, 60, 40)).save(tmp, 'JPEG', quality=95)
    goc_kb = os.path.getsize(tmp) / 1024
    data, duoi = A.toi_uu_anh(tmp, rong_toi_da=1200)
    kt('D1: tối ưu trả về bytes WebP', data is not None and duoi == 'webp', str(duoi))
    kt('D2: dung lượng GIẢM đáng kể',
       data and len(data) / 1024 < goc_kb * 0.6,
       f'{goc_kb:.0f}KB -> {len(data) / 1024:.0f}KB' if data else '')
    if data:
        with Image.open(__import__('io').BytesIO(data)) as im2:
            kt('D3: resize đúng chiều rộng tối đa', im2.width == 1200, str(im2.width))
    os.remove(tmp)
except ImportError:
    print('[BỎ QUA] D: thiếu Pillow')

# ---------- E. Quét thư mục ----------
tmpdir = tempfile.mkdtemp()
try:
    from PIL import Image
    for f in ('mba dau mbt 250kva.jpg', 'z999.jpg', 'ghi-chu.txt'):
        if f.endswith('.jpg'):
            Image.new('RGB', (100, 100)).save(os.path.join(tmpdir, f))
        else:
            open(os.path.join(tmpdir, f), 'w').write('x')
    kq = A.quet_thu_muc(tmpdir, ROWS)
    kt('E1: quét chỉ lấy file ảnh, bỏ file khác',
       kq['ok'] and len(kq['danh_sach']) == 2, str(len(kq.get('danh_sach', []))))
    ghep_duoc = [d for d in kq['danh_sach'] if d['ma_goc']]
    kt('E2: ảnh có tên nghĩa được ghép, ảnh vô nghĩa để trống',
       len(ghep_duoc) == 1 and ghep_duoc[0]['ma_goc'] == 'MBT3P250A2608')
    kt('E3: ảnh chưa ghép được thì KHÔNG tự tick chọn',
       all(not d['chon'] for d in kq['danh_sach'] if not d['ma_goc']))
except ImportError:
    pass
kt('E4: thư mục không tồn tại -> báo lỗi rõ, không crash',
   A.quet_thu_muc('/duong/dan/khong/co', ROWS)['ok'] is False)

# ---------- F. Nhóm 1: các sửa đổi khác ----------
d = R.tinh_delta_context(
    {'ma_goc': 'X', 'cong_suat': '100', 'outline_id': 'outline_may_bien_ap', 'ten_goc': 'MBA'},
    [{'ma_goc': 'MBT3P160A2608', 'cong_suat': '160', 'ten_goc': 'MBA 160', 'wp_url': ''}])
kt('F1: delta context KHÔNG còn chứa mã SKU (lỗi Thịnh nhắc 3 lần)',
   'MBT3P160A2608' not in str(d), str(d))
kt('F2: chênh lệch ghi RÕ CẢ HAI CHIỀU (37.5% và 60%)',
   '37.5' in d.get('chenh_lech_lon', '') and '60' in d.get('chenh_lech_lon', ''),
   d.get('chenh_lech_lon'))

s = R.dung_faq_schema({'faq': [{'q': 'Bảo hành?', 'a': '<p>Theo hãng.</p>'}]})
kt('F3: FAQ schema đúng kiểu FAQPage, đã bóc HTML khỏi câu trả lời',
   s and s['@type'] == 'FAQPage'
   and s['mainEntity'][0]['acceptedAnswer']['text'] == 'Theo hãng.')
kt('F4: không có FAQ -> KHÔNG dựng schema rỗng', R.dung_faq_schema({}) is None)

kt('F5: khối cấu tạo chỉ hiện cho máy DẦU, không hiện cho máy khô',
   R.khoi_cau_tao_phu_kien({'outline_id': 'outline_may_bien_ap',
                            'ten_goc': 'MBA dầu 3 pha 100kVA'})
   and not R.khoi_cau_tao_phu_kien({'outline_id': 'outline_may_bien_ap',
                                    'ten_goc': 'MBA khô 3 pha 1000kVA'}))

print(f'\nTỔNG VER 2.7 ULTRA: {so_pass}/{so_pass + so_fail} PASS')
sys.exit(1 if so_fail else 0)
