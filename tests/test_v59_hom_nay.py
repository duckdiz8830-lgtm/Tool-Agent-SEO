# -*- coding: utf-8 -*-
"""Ver 5.9 — test màn hình "Hôm nay" + PHÉP THỬ HỢP ĐỒNG giac_cam.

Test này KHÔNG dựng tkinter, KHÔNG cần Xvfb, chạy trong tích tắc.
Trước Ver 5.8 điều đó bất khả: muốn test bất cứ tab nào cũng phải dựng cả
app 787 widget dưới Xvfb. Đó là lợi ích lớn nhất của giac_cam.py, và file
này tồn tại để CHỨNG MINH nó, không phải để nói suông.

Kiểm 3 nhóm:
    A. doc_so_lieu()      — đọc số đúng, DB rỗng/hỏng không nổ
    B. dung_viec_can_lam() — sinh việc đúng thứ tự ưu tiên
    C. hợp đồng           — module mới KHÔNG phải nới giac_cam dòng nào
"""
import os
import sqlite3
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC)

import giac_cam as GC
import tab_hom_nay as T

_sai = 0


def kt(ten, dieu_kien, ghi_chu=''):
    global _sai
    dat = bool(dieu_kien)
    _sai += 0 if dat else 1
    them = f'  | {ghi_chu}' if ghi_chu and not dat else ''
    print(f'  {"PASS" if dat else "FAIL"}  {ten}{them}')


def _db(rong=False, khong_bang=False):
    con = sqlite3.connect(':memory:')
    if khong_bang:
        return con
    con.execute('CREATE TABLE san_pham_phase2 (dataset_id TEXT, record_id TEXT, '
                'profile_id TEXT, selected INTEGER DEFAULT 0)')
    con.execute('CREATE TABLE bai_viet_phase2 (dataset_id TEXT, record_id TEXT, '
                'site TEXT, mau TEXT, trang_thai TEXT, wp_id INTEGER, '
                'wp_url TEXT, ngay_dang TEXT)')
    if rong:
        return con
    sp = [('ds1', f'r{i}', 'may_bien_ap_do_luong') for i in range(10)]
    sp += [('ds1', f'c{i}', 'cap_dien') for i in range(6)]
    con.executemany('INSERT INTO san_pham_phase2 (dataset_id,record_id,profile_id) '
                    'VALUES (?,?,?)', sp)
    hn = T._hom_nay()
    bv = [('ds1', 'r0', 'maybienapvn.vn', 'm', 'da_dang', 1, 'u', hn + 'T09:00:00'),
          ('ds1', 'r1', 'maybienapvn.vn', 'm', 'da_dang', 2, 'u', hn + 'T10:00:00'),
          ('ds1', 'r2', 'maybienapvn.vn', 'm', 'da_dang', 3, 'u', '2026-01-01T10:00:00'),
          ('ds1', 'r3', 'maybienapvn.vn', 'm', 'loi', None, None, None),
          ('ds1', 'r4', 'maybienapvn.vn', 'm', 'chua_sinh', None, None, None),
          ('ds1', 'r5', 'maybienapvn.vn', 'm', 'da_go', 9, 'u', '2026-02-02T10:00:00')]
    con.executemany('INSERT INTO bai_viet_phase2 VALUES (?,?,?,?,?,?,?,?)', bv)
    return con


print('== A. doc_so_lieu — đọc số từ DB ==')
so = T.doc_so_lieu(_db(), quota_ngay=20)
kt('tổng SKU', so['tong_sku'] == 16, so['tong_sku'])
kt('đã đăng', so['da_dang'] == 3, so['da_dang'])
kt('bài lỗi', so['bai_loi'] == 1, so['bai_loi'])
kt('đã gỡ', so['da_go'] == 1, so['da_go'])
# 10 SKU không có dòng bai_viet nào (r6..r9 + c0..c5) + 1 dòng 'chua_sinh'
kt('chưa sinh = SKU chưa có dòng + dòng chua_sinh',
   so['chua_sinh'] == 10 + 1, so['chua_sinh'])
kt('đăng HÔM NAY chỉ đếm hôm nay, không đếm bài cũ',
   so['dang_hom_nay'] == 2, so['dang_hom_nay'])
kt('quota còn = 20 - 2', so['quota_con'] == 18, so['quota_con'])
kt('nhóm sản phẩm đếm đúng',
   so['theo_profile'] == {'may_bien_ap_do_luong': 10, 'cap_dien': 6},
   so['theo_profile'])
kt('site đang dùng', so['site_dang_dung'] == ['maybienapvn.vn'], so['site_dang_dung'])

print('== A2. DB rỗng / thiếu bảng — KHÔNG được nổ ==')
so_rong = T.doc_so_lieu(_db(rong=True))
kt('DB rỗng: tổng = 0, không nổ', so_rong['tong_sku'] == 0)
kt('DB rỗng: không báo lỗi đọc', so_rong['loi_doc'] is None)
so_hong = T.doc_so_lieu(_db(khong_bang=True))
kt('THIẾU BẢNG: không nổ, có thông điệp dẫn đường',
   so_hong['loi_doc'] and 'Nhập dữ liệu' in so_hong['loi_doc'], so_hong['loi_doc'])
kt('THIẾU BẢNG: số để None chứ KHÔNG phải 0 (0 và "không biết" là 2 chuyện)',
   so_hong['tong_sku'] is None)

print('== B. dung_viec_can_lam — thứ tự ưu tiên ==')
v = T.dung_viec_can_lam(so)
kt('có sinh việc', len(v) >= 2, v)
kt('việc CHẶN xếp trước việc NÊN LÀM',
   [m for m, _, _ in v].index('chan') < [m for m, _, _ in v].index('nen'))
kt('nhắc soát mỏng/trùng TRƯỚC khi sinh',
   any('Soát mỏng' in g for _, _, g in v))

het = dict(so, quota_con=0, dang_hom_nay=20)
v2 = T.dung_viec_can_lam(het)
kt('hết quota -> báo CHẶN', any(m == 'chan' and 'quota' in t.lower() for m, t, _ in v2))
kt('giải thích quota nêu đúng: tính theo PROJECT không theo key',
   any('PROJECT' in g for _, _, g in v2))

sach = {'tong_sku': 100, 'chua_sinh': 0, 'da_dang': 100, 'bai_loi': 0,
        'da_go': 0, 'quota_con': 20, 'dang_hom_nay': 0, 'quota_ngay': 20}
v3 = T.dung_viec_can_lam(sach)
kt('sạch hết -> 1 dòng OK, không bịa việc', len(v3) == 1 and v3[0][0] == 'xong', v3)

v4 = T.dung_viec_can_lam({'loi_doc': 'Chưa có bảng dữ liệu nào.'})
kt('lỗi đọc -> chỉ báo lỗi, không đoán số', len(v4) == 1 and v4[0][0] == 'chan')

print('== C. PHÉP THỬ HỢP ĐỒNG ==')
giac = GC.GiacCamGia({'GEMINI_QUOTA_NGAY': '20'})
kt('module chạy được với GiacCamGia (không cần tkinter)',
   giac.cau_hinh_int('GEMINI_QUOTA_NGAY', 5) == 20)

import ast
src = open(os.path.join(GOC, 'tab_hom_nay.py'), encoding='utf-8').read()
cay = ast.parse(src)
ts = set()
for n in ast.walk(cay):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for a in n.args.args:
            if a.arg in ('app', 'giac'):
                ts.add(a.arg)
bd = set()
for n in ast.walk(cay):
    if isinstance(n, ast.Assign) and isinstance(n.value, ast.Name) and n.value.id in ts:
        for t in n.targets:
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == 'self':
                bd.add(('self', t.attr))
            elif isinstance(t, ast.Name):
                bd.add((None, t.id))
cham = []
for n in ast.walk(cay):
    if not isinstance(n, ast.Attribute):
        continue
    v_ = n.value
    la = ((isinstance(v_, ast.Name) and v_.id in ts)
          or (isinstance(v_, ast.Attribute) and isinstance(v_.value, ast.Name)
              and v_.value.id == 'self' and ('self', v_.attr) in bd)
          or (isinstance(v_, ast.Name) and (None, v_.id) in bd))
    if la and n.attr not in GC.CHAN_HOP_LE and n.attr not in GC.CHAN_TIEN_DUNG:
        cham.append(f'dòng {n.lineno}: .{n.attr}')
kt('tính năng MỚI không với ra ngoài 5 chân', not cham, cham)
kt('không import giao-dien / không đụng PhanMem',
   'PhanMem' not in src and 'giao-dien' not in src)
kt('không tự dựng threading.Thread (phải đi qua giac.chay_nen)',
   'threading.Thread' not in src)
kt('không gọi os.environ trực tiếp (phải đi qua giac.cau_hinh)',
   'os.environ' not in src)

print(f'\nTONG SAI: {_sai}')
raise SystemExit(1 if _sai else 0)
