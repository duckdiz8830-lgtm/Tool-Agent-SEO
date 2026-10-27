# -*- coding: utf-8 -*-
"""Ver 6.3 — test kho ảnh nguồn (kho_anh_nguon.py + panel_anh.py).

Kiểm ba nhóm:
  A. Chuẩn hoá + tách folder + suy loại  — phần dễ sai nhất, không cần Tk.
  B. Xếp hạng đề xuất trên kho ảnh giả   — cần Pillow, không cần Tk.
  C. Bất biến CHỈ-ĐỌC                     — module không được ghi vào kho ảnh.

Không cần Xvfb: phần UI chỉ kiểm import được và có đúng hàm điểm vào.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kho_anh_nguon as K  # noqa: E402

so_pass = 0
so_fail = 0


def kiem(ten, dieu_kien, chi_tiet=''):
    global so_pass, so_fail
    if dieu_kien:
        so_pass += 1
        print(f'[PASS] {ten}')
    else:
        so_fail += 1
        print(f'[FAIL] {ten}  {chi_tiet}')


# ---------------------------------------------------------------- A
print('--- A. Chuẩn hoá / tách folder / suy loại ---')

kiem('A1 bỏ dấu tiếng Việt', K.chuan_hoa('Máy Biến Áp  EMIC') == 'may bien ap emic')
kiem('A2 chữ đ', K.chuan_hoa('Đầu cáp 3M') == 'dau cap 3m')
kiem('A3 tách LOẠI+HÃNG', K.tach_folder('BIEN AP TU EMIC') == ('bien ap tu', 'emic'))
kiem('A4 folder không hãng', K.tach_folder('CHI ONG') == ('chi ong', ''))
kiem('A5 hoa/thường lẫn lộn', K.tach_folder('Contactor Hyundai') == ('contactor', 'hyundai'))

# Cụm dài phải thắng cụm ngắn — 'dau cap' KHÔNG được rơi vào 'cap'.
kiem('A6 đầu cáp không bị nhận thành cáp',
     K.suy_loai_tu_ten('Đầu cáp co nguội 3M 24kV') == 'dau cap',
     K.suy_loai_tu_ten('Đầu cáp co nguội 3M 24kV'))
kiem('A7 cáp vẫn ra cáp', K.suy_loai_tu_ten('Cáp ngầm CADIVI CXV 3x50') == 'cap')
kiem('A8 biến áp', K.suy_loai_tu_ten('Máy biến áp dầu EMIC 250kVA') == 'bien ap')
kiem('A9 biến dòng khác biến áp',
     K.suy_loai_tu_ten('Máy biến dòng EMIC 100/5A') == 'bien dong ti')
kiem('A10 tên rỗng không nổ', K.suy_loai_tu_ten('') == '')

r = K.tu_row({'ten_goc': 'Máy biến áp dầu 250kVA', 'ma_goc': 'MBA-250',
              'thuong_hieu': 'EMIC'})
kiem('A11 tu_row bóc đủ 3 trường',
     r == {'sku': 'MBA-250', 'loai': 'bien ap', 'hang': 'EMIC'}, r)
kiem('A12 row rỗng không ném lỗi', K.tu_row({})['loai'] == '')
kiem('A13 row None không ném lỗi', K.tu_row(None)['sku'] == '')

# Đuôi ảnh phải khớp workspace_anh, không thì hai bên bất đồng "cái gì là ảnh"
import workspace_anh as WS  # noqa: E402
kiem('A14 DUOI_ANH khớp workspace_anh', K.DUOI_ANH == WS.DUOI_ANH,
     f'lệch: {K.DUOI_ANH ^ WS.DUOI_ANH}')

# ---------------------------------------------------------------- B
print('--- B. Xếp hạng trên kho giả ---')
try:
    from PIL import Image
    co_pil = True
except ImportError:
    co_pil = False
    print('  (bỏ qua B: thiếu Pillow)')

if co_pil:
    tmp = tempfile.mkdtemp(prefix='kho-anh-test-')
    mau = {
        'BIEN AP TU EMIC': [('EMIC-250-22-0.4.jpg', 1400, 1000),
                            ('IMG_20260815_1430.jpg', 1600, 1200),
                            ('nho.jpg', 400, 300)],
        'BIEN AP': [('bien ap kho.jpg', 1200, 900)],
        'DAU CAP 3M': [('92-EB-5-1.jpg', 1300, 1000)],
        'CAP CADIVI': [('cadivi cvv.jpg', 1500, 1100)],
    }
    for tm, files in mau.items():
        Path(tmp, tm).mkdir(parents=True, exist_ok=True)
        for ten, w, h in files:
            Image.new('RGB', (w, h), (120, 120, 120)).save(Path(tmp, tm, ten))

    cache = Path(tmp) / 'cache.json'
    kho = K.KhoAnh(tmp, file_cache=str(cache))
    n = kho.nap_index()
    kiem('B1 quét đủ ảnh', n == 6, f'đếm được {n}')

    ds = kho.de_xuat(sku='EMIC-250-22/0.4', loai='bien ap', hang='EMIC')
    kiem('B2 tên file khớp SKU lên đầu',
         ds and ds[0].ten_file == 'EMIC-250-22-0.4.jpg',
         ds[0].ten_file if ds else 'rỗng')

    ten_ra = [u.ten_file for u in ds]
    kiem('B3 ảnh tên rác vẫn ra nhờ folder', 'IMG_20260815_1430.jpg' in ten_ra, ten_ra)
    kiem('B4 folder khác hãng xếp sau',
         ten_ra.index('EMIC-250-22-0.4.jpg') < ten_ra.index('bien ap kho.jpg'), ten_ra)

    ds2 = kho.de_xuat(sku='EMIC-250', loai='bien ap', hang='EMIC', toi_thieu_px=800)
    kiem('B5 lọc kích thước loại ảnh nhỏ',
         all(u.rong >= 800 for u in ds2), [(u.ten_file, u.rong) for u in ds2])

    # SKU mã ngắn: mọi mảnh đều <3 ký tự, phải bắt bằng tầng so chuỗi liền
    ds3 = kho.de_xuat(sku='3M-92-EB-5-1', loai='dau cap', hang='3M')
    kiem('B6 SKU mã ngắn vẫn khớp tên file',
         ds3 and ds3[0].ten_file == '92-EB-5-1.jpg',
         ds3[0].ten_file if ds3 else 'rỗng')

    # "đã dùng": so theo hash_goc, KHÔNG theo đường dẫn
    dd = str(Path(tmp, 'BIEN AP TU EMIC', 'EMIC-250-22-0.4.jpg'))
    h = K.hash_file(dd)
    kiem('B7 hash khớp workspace_anh.hash_file', h == WS.hash_file(dd), h)
    ds4 = kho.de_xuat(sku='EMIC-250-22/0.4', loai='bien ap', hang='EMIC',
                      hash_da_dung={h})
    danh_dau = [u for u in ds4 if u.da_dung]
    kiem('B8 ảnh đã dùng bị đánh dấu',
         len(danh_dau) == 1 and danh_dau[0].ten_file == 'EMIC-250-22-0.4.jpg',
         [u.ten_file for u in danh_dau])
    kiem('B9 ảnh đã dùng bị trừ điểm nhưng KHÔNG bị ẩn',
         any(u.ten_file == 'EMIC-250-22-0.4.jpg' for u in ds4))

    # SKU không thuộc loại nào trong kho -> phải rỗng, không được bịa
    ds5 = kho.de_xuat(sku='DELTA-VFD-007', loai='bien tan', hang='Delta')
    kiem('B10 loại không có trong kho -> không đề xuất bừa', ds5 == [], ds5)

    # cache phải trúng, không quét lại
    kho2 = K.KhoAnh(tmp, file_cache=str(cache))
    kiem('B11 cache đọc lại được', kho2.doc_cache() and len(kho2.index) == 4)

    # ---------------------------------------------------------------- C
    print('--- C. Bất biến CHỈ-ĐỌC ---')
    truoc = {str(p): p.stat().st_mtime_ns for p in Path(tmp).rglob('*') if p.is_file()
             and p.name != 'cache.json'}
    kho3 = K.KhoAnh(tmp, file_cache=str(cache))
    kho3.nap_index(ep_quet_lai=True)
    kho3.de_xuat(sku='EMIC-250', loai='bien ap', hang='EMIC', hash_da_dung={h})
    sau = {str(p): p.stat().st_mtime_ns for p in Path(tmp).rglob('*') if p.is_file()
           and p.name != 'cache.json'}
    kiem('C1 không thêm/xoá file nào trong kho', set(truoc) == set(sau),
         f'lệch: {set(truoc) ^ set(sau)}')
    kiem('C2 không sửa file nào trong kho', truoc == sau)

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

# ---------------------------------------------------------------- D
print('--- D. UI import được ---')
try:
    import panel_anh  # noqa: F401
    kiem('D1 panel_anh import được', True)
    kiem('D2 có hàm điểm vào mo_cua_so_anh', callable(panel_anh.mo_cua_so_anh))
    kiem('D3 có class PanelDeXuatAnh', hasattr(panel_anh, 'PanelDeXuatAnh'))
except Exception as e:
    kiem('D1 panel_anh import được', False, repr(e))

import tab_anh  # noqa: E402
kiem('D4 tab_anh có nút kho ảnh', hasattr(tab_anh.TabAnh, '_mo_kho_anh_nguon'))
kiem('D5 tab_anh có nguồn hash đã dùng',
     hasattr(tab_anh.TabAnh, '_anh_da_dung_trong_workspace'))

print(f'\nTỔNG VER 6.3 KHO ẢNH NGUỒN: {so_pass}/{so_pass + so_fail} PASS')
sys.exit(1 if so_fail else 0)
