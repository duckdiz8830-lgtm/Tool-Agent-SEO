import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# -*- coding: utf-8 -*-
"""Ver 4.5 — test 5 vá. Không gọi mạng, không cần tkinter.

Mỗi test khoá một lỗi ĐÃ XẢY RA THẬT trên production, không phải giả định.
"""
import re

import phien_ban as PB
import render_phase2 as R
import profiles as P
import va_slug as V
import phu_kien_di_kem as PK

so_fail = 0


def kiem(nhan, dieu_kien, chi_tiet=''):
    global so_fail
    if dieu_kien:
        print(f'  OK  {nhan}')
    else:
        so_fail += 1
        print(f'  SAI {nhan} {chi_tiet}')


print('== A. Rò giá list ra HTML công khai ==')
# Bug thật: 245 bài trên maybienapvn.vn in giá list Lotech trong khối phụ kiện.
src = open(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         'phu_kien_di_kem.py'), encoding='utf-8').read()
than = re.sub(r'#[^\n]*', '', src)          # bỏ comment, chỉ soi code thật
kiem('không còn ký tự ₫ trong code', '₫' not in than)
kiem('không còn đọc gia_list', 'gia_list' not in than)
kiem('không còn hàm _tien()', 'def _tien' not in than)

_st = lambda k: 'class="x"'
_esc = lambda s: str(s)
ds = [{'ma': 'MBT1P100', 'ten': 'Máy biến áp 100kVA', 'loai': PK.MAY,
       'gia': '82650000', 'url': '/a'}]
html = PK.khoi_html({'ten_goc': 'Vỏ mạ kẽm'}, ds, _st, _esc)
kiem('HTML sinh ra không chứa số tiền', '82' not in html and '₫' not in html,
     f'-> {html[:90]}')

print('== B. _so_kva_tu_chuoi đọc MVA ==')
# Bug thật: '25/40/63MVA' ra 25 kVA, sai 1.000 lần -> hỏng slug + tier.
for vao, mong in (('160 kVA', 160.0), ('25/40/63MVA', 25000.0), ('63MVA', 63000.0),
                  ('1,6 MVA', 1600.0), ('560(500) kVA', 560.0), ('12.7', 12.7)):
    kiem(f'{vao!r} -> {mong}', R._so_kva_tu_chuoi(vao) == mong,
         f'-> {R._so_kva_tu_chuoi(vao)}')

print('== C. Bỏ dấu tiếng Việt: chữ đ ==')
# Bug thật: NFD không tách 'đ' -> 'điện' thành 'đien' -> 22 dòng công tơ điện
# bị nhận nhầm thành máy biến áp.
kiem("'điện' -> 'dien'", V._bo_dau('điện') == 'dien', f"-> {V._bo_dau('điện')}")
kiem('công tơ nhận đúng loại',
     V.loai_san_pham('Công tơ điện tử 3 pha Gelex EMIC') == 'cong-to-dien')
kiem('biến dòng nhận đúng loại',
     V.loai_san_pham('Biến dòng hạ thế CXX0.5 hình xuyến 50/5A') == 'bien-dong-dien')
kiem('máy biến áp vẫn đúng',
     V.loai_san_pham('Máy biến áp dầu 3 pha HBT loại kín') == 'may-bien-ap')

print('== D. Slug sheet 03 không trùng ==')
# Bug thật: 581 dòng MASTER Ver11 chỉ ra 365 URL -> đăng là mất 216 bài.
def r(ten, **kw):
    d = {'outline_id': 'outline_may_bien_ap', 'ten_goc': ten, 'thuong_hieu': 'HBT',
         'slug_chi_dinh': '',
         'cong_suat': '100 kVA', 'cap_dien_ap': '22/0.4 kV', 'ma_goc': '',
         'quy_cach': '', 'nhom_nguon': '05. Máy Biến Áp',
         'nguon_tieu_chuan_vien_dan': '', 'hau_to_slug': ''}
    d.update(kw)
    return d

# va_slug tinh 4 bien the ra 4 slug khac nhau
bo = [
    r('Máy biến áp dầu 3 pha HBT loại kín Silic 100kVA 22/0.4kV'),
    r('Máy biến áp dầu 3 pha HBT loại kín Silic 100kVA 35/0.4kV', cap_dien_ap='35/0.4 kV'),
    r('Máy biến áp dầu 3 pha HBT loại hở có bình dầu phụ Silic 100kVA 22/0.4kV'),
    r('Máy biến áp dầu 3 pha HBT loại hở có bình dầu phụ Silic 100kVA 35/0.4kV',
      cap_dien_ap='35/0.4 kV'),
]
import dulieu as D
sl = [V.slug_moi(x, R, D) for x in bo]
kiem('4 biến thể kín/hở × 22/35kV ra 4 slug khác nhau', len(set(sl)) == 4, f'-> {sl}')

print('== D2. Slug chỉ định được dùng nguyên văn ==')
# Đây là hợp đồng quan trọng nhất của 4.5: Excel ghi gì -> URL ra đúng vậy,
# tool KHÔNG tự tính lại, nên bài đã đăng không bao giờ tự đổi URL.
kiem('dùng nguyên văn cột Slug chỉ định',
     R.dung_slug(r('Máy biến áp X', slug_chi_dinh='may-bien-ap-kho-kp-2500kva'))
     == 'may-bien-ap-kho-kp-2500kva')
kiem('cột trống -> tính như cũ (3.9 không đổi)',
     R.dung_slug(r('Máy biến áp khô KP 2500kVA Cu/Cu', thuong_hieu='KP',
                   cong_suat='2500 kVA', slug_chi_dinh=''))
     == R._slug_mba_39(r('Máy biến áp khô KP 2500kVA Cu/Cu', thuong_hieu='KP',
                         cong_suat='2500 kVA')))

print('== E. Phiên bản gom về một nguồn ==')
# Ver 5.7 — KHÔNG hard-code số phiên bản trong test nữa. Bản cũ ghim
# '4.6.2' nên mỗi lần bump phien_ban.py là test này đỏ, dù không có lỗi
# gì. Đó chính là họ lỗi mà phien_ban.py sinh ra để chống. Nay chỉ kiểm
# HỢP ĐỒNG: PHIEN_BAN tồn tại, là chuỗi, đúng dạng số chấm số.
kiem(f'phien_ban.PHIEN_BAN đúng dạng x.y[.z] (thực tế {PB.PHIEN_BAN!r})',
     isinstance(PB.PHIEN_BAN, str)
     and re.fullmatch(r'\d+(?:\.\d+){1,3}', PB.PHIEN_BAN) is not None)
gd = open(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                        'giao-dien.py'), encoding='utf-8').read()
gd_code = re.sub(r'#[^\n]*', '', gd)
kiem('giao-dien.py không còn chuỗi phiên bản cứng',
     '4.4.1.4 HF1' not in gd_code)
kiem('giao-dien.py dùng hằng số', 'PB.NHAN_DAY_DU' in gd_code)

print('== F. Cờ nhường schema cho Rank Math ==')
_os.environ['SONEALEO_SCHEMA'] = '0'
kiem('SONEALEO_SCHEMA=0 -> tắt', R._bat_schema() is False)
_os.environ['SONEALEO_SCHEMA'] = '1'
kiem('SONEALEO_SCHEMA=1 -> bật', R._bat_schema() is True)
_os.environ.pop('SONEALEO_SCHEMA', None)
kiem('mặc định BẬT (giữ hành vi cũ)', R._bat_schema() is True)

print('== G. Cột Hậu tố slug đã khai trong profile ==')
kiem('cot_import có Hậu tố slug',
     'Hậu tố slug' in P.PROFILES['may_bien_ap_do_luong']['cot_import'])
kiem('cot_import có Slug chỉ định',
     'Slug chỉ định' in P.PROFILES['may_bien_ap_do_luong']['cot_import'])
kiem('gia_list vẫn nằm trong FIELD_CAM_TUYET_DOI',
     'gia_list' in P.FIELD_CAM_TUYET_DOI)

print('== H. Ver 4.5.1 — mã nội bộ cho dòng catalogue không in SKU ==')
# Sự cố 17/08/2026: 333/581 dòng trống Mã hàng -> nhap_phase2 dòng 234
# 'if not norm.get(ma_goc): continue' loại thẳng, chỉ vào được 248/581.
import sinh_ma_noi_bo as SM
r1 = {'Tên hàng': 'Máy biến áp dầu 3 pha HBT loại kín Silic 100kVA 22/0.4kV',
      'Nhãn Hiệu / Xuất Xứ': 'HBT', 'Công Suất (kVA)': '100 kVA',
      'Cấp Điện Áp (kV)': '22/0.4 kV'}
r2 = dict(r1, **{'Tên hàng': 'Máy biến áp dầu 3 pha HBT loại hở có bình dầu phụ '
                             'Silic 100kVA 22/0.4kV'})
m1, m2 = SM.sinh_ma(r1), SM.sinh_ma(r2)
kiem('mã có tiền tố LTC- (phân biệt với mã hãng)', m1.startswith('LTC-'), f'-> {m1}')
kiem('kín và hở ra mã khác nhau', m1 != m2, f'-> {m1} / {m2}')
kiem('chạy lại ra cùng mã (tất định)', SM.sinh_ma(r1) == m1)
kiem('mã không chứa dấu tiếng Việt', all(ord(c) < 128 for c in m1), f'-> {m1}')

print('== I. Ver 4.5.1 — di trú khi MASTER thêm cột ==')
# Trước 4.5.1: thêm cột hợp lệ vào profile = vĩnh viễn không import lại được.
import db_phase2 as DB
import inspect
sig = inspect.signature(DB.xac_nhan_dataset).parameters
kiem('xac_nhan_dataset có cờ confirm_doi_cau_truc', 'confirm_doi_cau_truc' in sig)
e = DB.CanhBaoCauTrucDoi('p', {'dataset_id': 'ds_1'}, ['A', 'B'], ['A', 'B', 'C'])
kiem('cảnh báo nêu đúng cột THÊM', e.them == ['C'] and e.bot == [], f'-> {e.them}/{e.bot}')
e2 = DB.CanhBaoCauTrucDoi('p', {'dataset_id': 'ds_1'}, ['A', 'B'], ['A'])
kiem('cảnh báo nêu đúng cột BỚT', e2.bot == ['B'])
kiem('thông điệp có nêu tên cột', 'C' in str(e))

print(f'\nTONG SAI: {so_fail}')
_sys.exit(1 if so_fail else 0)
