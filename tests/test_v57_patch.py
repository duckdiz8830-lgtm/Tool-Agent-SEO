# -*- coding: utf-8 -*-
"""Ver 5.7 — khoá 3 vá còn lại của đợt audit 22/08/2026.

    A. giao-dien.py  — lambda không được bắt biến của `except ... as e`
    B. tab_seo_post  — mỗi luồng một kết nối SQLite
    C. render_phase2 — Hard Block không chặn ngày tháng, vẫn chặn số bịa

Không gọi mạng, không cần tkinter hiển thị.
"""
import ast
import os
import queue
import re
import sys
import tempfile
import threading

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC)

_sai = 0


def kt(ten, dieu_kien, ghi_chu=''):
    global _sai
    dat = bool(dieu_kien)
    _sai += 0 if dat else 1
    print(f'  {"PASS" if dat else "FAIL"}  {ten}{("  | " + str(ghi_chu)) if ghi_chu and not dat else ""}')


# ==================================================================== A
print('== A. giao-dien.py — closure không được bắt biến except ==')

# A1. Quét AST: KHÔNG file .py nào ở gốc được có lambda/def lồng trong khối
# except mà tham chiếu tên biến của chính except đó. Python 3 xoá tên đó khi
# thoát khối; nếu closure chạy trễ (queue UI, .after, Thread) sẽ nổ NameError
# và bị nuốt vào nhánh xử lý lỗi chung -> triệu chứng "nút kẹt, không báo gì".
vi_pham = []
for ten in sorted(os.listdir(GOC)):
    if not ten.endswith('.py'):
        continue
    try:
        cay = ast.parse(open(os.path.join(GOC, ten), encoding='utf-8', errors='replace').read())
    except SyntaxError:
        continue
    for n in ast.walk(cay):
        if isinstance(n, ast.ExceptHandler) and n.name:
            for sub in ast.walk(n):
                if isinstance(sub, (ast.Lambda, ast.FunctionDef)):
                    # default-arg được phép: giá trị đã bị "đóng băng" lúc tạo
                    mac_dinh = {id(d) for d in getattr(sub.args, 'defaults', [])}
                    trong_mac_dinh = set()
                    for d in getattr(sub.args, 'defaults', []):
                        trong_mac_dinh.update(id(x) for x in ast.walk(d))
                    for x in ast.walk(sub):
                        if isinstance(x, ast.Name) and x.id == n.name and id(x) not in trong_mac_dinh:
                            vi_pham.append(f'{ten}:{x.lineno} bắt {n.name!r}')
                            break
kt('không file nào bắt biến except vào closure', not vi_pham, vi_pham)

# A2. Tái hiện cơ chế thật: đẩy callback vào queue rồi chạy TRỄ.
q = queue.Queue()


def _kieu_cu():
    try:
        raise ValueError('key sai')
    except Exception as e:
        q.put(lambda: f'{type(e).__name__}: {e}')


def _kieu_moi():
    try:
        raise ValueError('key sai')
    except Exception as e:
        tin = f'{type(e).__name__}: {e}'
        q.put(lambda t=tin: t)


_kieu_cu()
try:
    q.get()()
    cu_no = False
except NameError:
    cu_no = True
kt('kiểu CŨ đúng là nổ NameError (chứng minh bug có thật)', cu_no)

_kieu_moi()
kt('kiểu MỚI trả đúng thông điệp lỗi', q.get()() == 'ValueError: key sai')


# ==================================================================== B
print('== B. kết nối SQLite theo từng luồng ==')
# Ver 5.8 — ĐẢM BẢO NÀY ĐÃ CHUYỂN CHỖ, KHÔNG BỊ BỎ.
# Ver 5.7 vá bằng tab_seo_post._con(app) (threading.local cục bộ).
# Ver 5.8 gỡ hàm đó và phổ quát hoá thành giac_cam.GiacCam.db() — mọi
# module tính năng dùng chung một cơ chế thay vì mỗi module tự vá.
# Test vẫn kiểm ĐÚNG hành vi cũ, chỉ đổi nơi kiểm.
import db_phase2 as DBP

DBP.DB_PATH = tempfile.mktemp(suffix='.db')
import giac_cam as GC

giac = GC.GiacCam(app=None, ten_module='test_v57')
con_chinh = giac.db()
kt('gọi 2 lần trong CÙNG luồng -> tái dùng 1 kết nối', giac.db() is con_chinh)

ket = {}


def _nen():
    con_nen = giac.db()
    ket['khac'] = con_nen is not con_chinh
    try:
        con_nen.execute('SELECT 1').fetchone()
        ket['dung_duoc'] = True
    except Exception as e:
        ket['dung_duoc'] = f'{type(e).__name__}: {e}'


t = threading.Thread(target=_nen)
t.start()
t.join()
kt('luồng NỀN nhận kết nối KHÁC luồng chính', ket.get('khac'))
kt('kết nối của luồng nền dùng được, không ProgrammingError',
   ket.get('dung_duoc') is True, ket.get('dung_duoc'))

# Dùng CHUNG kết nối qua luồng phải nổ — chứng minh bug gốc có thật.
loi_cu = {}


def _nen_dung_chung():
    try:
        con_chinh.execute('SELECT 1').fetchone()
        loi_cu['x'] = None
    except Exception as e:
        loi_cu['x'] = type(e).__name__


t = threading.Thread(target=_nen_dung_chung)
t.start()
t.join()
kt('dùng CHUNG kết nối qua luồng đúng là nổ ProgrammingError',
   loi_cu.get('x') == 'ProgrammingError', loi_cu.get('x'))

# tab_seo_post KHÔNG được quay lại kiểu cũ
src_tab = open(os.path.join(GOC, 'tab_seo_post.py'), encoding='utf-8').read()
kt('không còn gán app._sp_con = DB.ket_noi()',
   not re.search(r'app\._sp_con\s*=\s*DB\.ket_noi\(\)', src_tab))
kt('không còn hàm _con(app) tự vá cục bộ',
   not re.search(r'(?m)^def _con\(app\)', src_tab))
kt('tab_seo_post dùng giac.db()', 'giac.db()' in src_tab or '.giac.db()' in src_tab)

# Trong THÂN hàm chạy nền, mọi lời gọi widget phải qua giac.ui()/.after().
_cay_tab = ast.parse(src_tab)
_worker_xau = []
for _n in ast.walk(_cay_tab):
    if isinstance(_n, ast.FunctionDef) and _n.name == '_worker':
        for _c in ast.walk(_n):
            if not (isinstance(_c, ast.Call) and isinstance(_c.func, ast.Attribute)):
                continue
            if _c.func.attr not in ('config', 'configure', 'insert', 'delete'):
                continue
            an_toan = False
            for _a in ast.walk(_n):
                if (isinstance(_a, ast.Call) and isinstance(_a.func, ast.Attribute)
                        and _a.func.attr in ('after', 'ui')):
                    if any(_x is _c for _x in ast.walk(_a)):
                        an_toan = True
                        break
            if not an_toan:
                _worker_xau.append(f'dòng {_c.lineno}: .{_c.func.attr}()')
kt('_worker: mọi lời gọi widget đều qua giac.ui()/.after()',
   not _worker_xau, _worker_xau)


# ==================================================================== C
print('== C. render_phase2 — Hard Block: ngày tháng vs số bịa ==')
import render_phase2 as R

row = {'profile_id': 'may_bien_ap_do_luong', 'outline_id': 'outline_may_bien_ap',
       'ten_goc': 'Máy biến áp 3 pha 250kVA 22/0,4kV THIBIDI', 'ma_goc': 'MBT3P250',
       'thuong_hieu': 'THIBIDI', 'cap_dien_ap': '22/0,4', 'cong_suat': '250 kVA',
       'dvt': 'Cái', 'to_dau_day': 'Dyn11', 'ton_hao_khong_tai': '740',
       'ton_hao_ngan_mach': '2950', 'dien_ap_ngan_mach': '4', 'thong_so_dong': {}}

print('  -- C1. ngày tháng PHẢI QUA --')
for t_ in ['Báo giá cập nhật ngày 22/08/2026.',
           'Bảng giá tháng 8/2026',
           'Áp dụng từ 01/09/2026 tới hết quý.',
           'Cập nhật 12/2026',
           'Giao hàng dự kiến 5/9/2026']:
    kt(f'qua: {t_[:38]}', not R.kiem_tra_bia(t_, row), R.kiem_tra_bia(t_, row))

print('  -- C2. số kỹ thuật BỊA vẫn PHẢI CHẶN (hàng rào không được thủng) --')
for t_ in ['Máy này 400kVA công suất lớn.',
           'Cáp 3x120mm² đi kèm.',
           'Cấp điện áp 35/0,4kV.',
           'Dòng định mức 100/5A.',
           'Tiết diện 1x240mm2.',
           'Bảo hành 24 tháng.',
           'Đạt IEC 60076.',
           'Tổn hao 999W.']:
    kt(f'chặn: {t_[:38]}', R.kiem_tra_bia(t_, row))

print('  -- C3. số THẬT của record vẫn PHẢI QUA --')
for t_ in ['Máy 250kVA, cấp điện áp 22/0,4kV, tổ đấu dây Dyn11.',
           'Sơ cấp 22kV, thứ cấp 0,4kV.',
           'Tổn hao không tải 740W, ngắn mạch 2950W.',
           'Điện áp ngắn mạch 4%.']:
    kt(f'qua: {t_[:44]}', not R.kiem_tra_bia(t_, row), R.kiem_tra_bia(t_, row))

print('  -- C4. _la_ngay_thang() chặt đúng phạm vi --')
for s, mong in [('22/08/2026', True), ('8/2026', True), ('01/09/2026', True),
                ('22/0,4', False), ('22/0,4kV', False), ('3x50', False),
                ('100/5A', False), ('1/3', False), ('13/2026', False),
                ('32/08/2026', False), ('8/1899', False)]:
    kt(f'_la_ngay_thang({s!r}) == {mong}', R._la_ngay_thang(s) is mong, R._la_ngay_thang(s))


# ==================================================================== D
print('== D. chuan_hoa — một nguồn bỏ dấu duy nhất ==')
import chuan_hoa as CH

kt("bo_dau('Đầu cáp') == 'dau cap'  (NFD KHÔNG tách được 'đ')",
   CH.bo_dau('Đầu cáp') == 'dau cap', CH.bo_dau('Đầu cáp'))
kt("bo_dau('điện áp') == 'dien ap'", CH.bo_dau('điện áp') == 'dien ap')
kt("bo_dau_giu_hoa giữ chữ hoa",
   CH.bo_dau_giu_hoa('Đầu cáp THIBIDI') == 'Dau cap THIBIDI')
kt('bo_dau(None) == ""', CH.bo_dau(None) == '')

con_dinh_nghia = []
for ten in sorted(os.listdir(GOC)):
    if not ten.endswith('.py') or ten == 'chuan_hoa.py':
        continue
    src = open(os.path.join(GOC, ten), encoding='utf-8', errors='replace').read()
    if re.search(r'(?m)^\s*def _bo_dau\(', src):
        con_dinh_nghia.append(ten)
kt('không file nào còn tự định nghĩa _bo_dau', not con_dinh_nghia, con_dinh_nghia)

print(f'\nTONG SAI: {_sai}')
raise SystemExit(1 if _sai else 0)
