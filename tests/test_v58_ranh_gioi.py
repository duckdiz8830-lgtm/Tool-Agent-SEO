# -*- coding: utf-8 -*-
r"""Ver 5.8 — TEST RANH GIỚI: giữ cho Lego không rữa thành mì Ý.

Chia file KHÔNG giữ được kiến trúc. Sáu tháng sau, module thứ 12 sẽ tự chế
dây riêng y như 5 module hiện tại, chỉ khác là nhiều file hơn. Thứ giữ được
là một cái thước chạy tự động mỗi lần `python run_tests.py`.

FILE NÀY ĐO 4 THỨ, mỗi thứ là một CÁI CHỐT chỉ được siết, không được nới:

    1. Module tính năng có đúng điểm vào `gan_vao(parent, giac)`.
    2. Module tính năng KHÔNG với vào app ngoài 5 chân của khung.py.
    3. Số lần dùng `thoat_hiem()` CHỈ ĐƯỢC GIẢM.
    4. Module tính năng KHÔNG gán thuộc tính vào app.

NGƯỠNG HIỆN TẠI nằm ở NGUONG bên dưới. Đó là ẢNH CHỤP thực trạng ngày
22/08/2026, KHÔNG phải mục tiêu. Luật dùng file này:

    * Sửa cho một module sạch hơn  -> HẠ số trong NGUONG xuống. Tốt.
    * Thêm module mới              -> để 0. Module mới phải sạch từ đầu.
    * Muốn NÂNG một số lên         -> DỪNG LẠI. Nâng ngưỡng là đang xây
      lại đúng cái God Class vừa gỡ, chỉ chậm hơn. Nếu thật sự cần thì
      dùng thoat_hiem() có lý do và ghi vào docs/KNOWN-ISSUES.md, để món
      nợ hiện ra chỗ đếm được thay vì lẩn vào 5.000 dòng.
"""
import ast
import os
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC)

import giac_cam as K

# Module tính năng = thứ gắn vào vỏ ứng dụng để thêm một mảng chức năng.
# KHÔNG tính: thư viện thuần (render_phase2, db_phase2...) vì chúng không
# nhận app; và không tính chính vỏ (giao-dien.py).
# LƯU Ý phân loại (tao đã xếp nhầm một lần, ghi lại để khỏi nhầm nữa):
# giao_dien_2_5.py KHÔNG phải module tính năng. Nó là THƯ VIỆN dựng HTML
# (xuat_css_2_5, khoi_chip, _esc...) — không nhận app, không tạo tab, bật
# tắt bằng biến môi trường GIAO_DIEN_2_5. Xếp nó vào đây thì test đòi nó
# phải có gan_vao() và báo đỏ vĩnh viễn vì một lỗi phân loại.
# Tiêu chí: module tính năng = NHẬN app/giac VÀ tự gắn mình vào giao diện.
MODULE_TINH_NANG = [
    'tab_anh.py',
    'tab_seo_post.py',
    'tab_hom_nay.py',     # Ver 5.9 — module MỚI, sạch từ đầu (ngưỡng 0)
    'hang_doi.py',
    'man_hinh_du_lieu.py',
]

# Ảnh chụp thực trạng 22/08/2026. Số điểm chạm vào app ngoài 5 chân.
# Đơn vị đo là LƯỢT CHẠM, không phải số tên duy nhất. Bản đầu tao ghi 14
# cho tab_seo_post vì đếm nhầm sang tên duy nhất; đếm đúng là 57 lượt trên
# 14 tên. Lượt chạm mới là thước đúng vì nó đo KHỐI LƯỢNG VIỆC phải gỡ.
NGUONG = {
    'tab_anh.py': 0,            # Ver 5.9 GỠ SẠCH: 2 -> 0. Toàn hệ về 0.
    'tab_seo_post.py': 0,       # Ver 5.8 GỠ SẠCH: 57 -> 0. Trước là module bẩn nhất hệ.
    'tab_hom_nay.py': 0,        # Ver 5.9 — viết sau hợp đồng, sạch từ đầu
    'hang_doi.py': 0,           # đã sạch — giữ nguyên
    'man_hinh_du_lieu.py': 0,   # đã sạch — giữ nguyên
}

# Số thuộc tính module NHÉT vào app. Đây là cách God Class được nuôi lớn.
NGUONG_GAN = {
    'tab_anh.py': 0,
    'tab_seo_post.py': 0,       # Ver 5.8 GỠ SẠCH: 15 -> 0. State nay nằm trong class TabSeoPost.
    'tab_hom_nay.py': 0,
    'hang_doi.py': 0,
    'man_hinh_du_lieu.py': 0,
}

# Số lần dùng cửa thoát hiểm trên toàn repo. Chỉ được giảm.
NGUONG_THOAT_HIEM = 0

_sai = 0


def kt(ten, dieu_kien, ghi_chu=''):
    global _sai
    dat = bool(dieu_kien)
    _sai += 0 if dat else 1
    them = f'  | {ghi_chu}' if ghi_chu and not dat else ''
    print(f'  {"PASS" if dat else "FAIL"}  {ten}{them}')


def _bi_danh_app(cay):
    """Tìm mọi tên trỏ về tham số app/khung: self.app = app, k = khung, ..."""
    # Ver 5.8 — CHỈ nhận diện app qua THAM SỐ HÀM. Bản đầu coi mọi định
    # danh tên 'khung' là app -> báo oan hang_doi.py vì file đó dùng
    # `khung = ttk.Frame(...)` làm biến cục bộ. Đó cũng là lý do đổi tên
    # hợp đồng thành `giac`: chữ 'khung' đã là tên quen của Frame (66 lần
    # trong repo), đặt trùng là cầm đèn chạy trước ô tô.
    ten_tham_so = set()
    for _n in ast.walk(cay):
        if isinstance(_n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for _a in _n.args.args:
                if _a.arg in ('app', 'giac'):
                    ten_tham_so.add(_a.arg)
    bi_danh = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Name) and n.value.id in ten_tham_so:
            for t in n.targets:
                if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == 'self':
                    bi_danh.add(('self', t.attr))
                elif isinstance(t, ast.Name):
                    bi_danh.add((None, t.id))
    return ten_tham_so, bi_danh


def _quet(duong_dan):
    """Trả (điểm chạm ngoài chân, điểm gán vào app, có gan_vao, chữ ký gan_vao)."""
    src = open(duong_dan, encoding='utf-8', errors='replace').read()
    cay = ast.parse(src)
    ten_tham_so, bi_danh = _bi_danh_app(cay)

    def la_app(node):
        if isinstance(node, ast.Name) and node.id in ten_tham_so:
            return True
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id == 'self' and ('self', node.attr) in bi_danh):
            return True
        if isinstance(node, ast.Name) and (None, node.id) in bi_danh:
            return True
        return False

    cham, gan = [], []
    for n in ast.walk(cay):
        if not isinstance(n, ast.Attribute):
            continue
        if not la_app(n.value):
            continue
        if isinstance(n.ctx, ast.Store):
            gan.append((n.lineno, n.attr))
        elif n.attr not in K.CHAN_HOP_LE and n.attr not in K.CHAN_TIEN_DUNG \
                and n.attr != 'thoat_hiem':
            cham.append((n.lineno, n.attr))

    diem_vao = None
    for n in cay.body:
        if isinstance(n, ast.FunctionDef) and n.name == K.DIEM_VAO:
            diem_vao = [a.arg for a in n.args.args]
    return cham, gan, diem_vao, src


print('== A. khung.py — hợp đồng tự nó phải đúng ==')
# Ver 5.9 — 5 -> 6 chân. Thêm dang_chon(), CÓ CÂN NHẮC không phải phình
# cho tiện: đo 38 lời gọi ra ngoài của 4 nhóm sắp tách, 18 đã có chỗ
# (db/cau_hinh), 10 là tiện ích tkinter thuần, còn đúng 10 là "đang chọn
# dataset/mẫu nào" — thứ CẦN state của vỏ, đúng tiêu chí làm chân.
# Đổi số này phải kèm lý do như trên. Không thì đang phình hợp đồng.
kt('CHAN_HOP_LE đúng 6 chân', len(K.CHAN_HOP_LE) == 6, sorted(K.CHAN_HOP_LE))
kt('DIEM_VAO là "gan_vao"', K.DIEM_VAO == 'gan_vao')
# Kiểm IMPORT thật bằng AST. Bản đầu tìm chuỗi 'tkinter' trong source nên
# dính cả chữ nằm trong chú thích -> báo oan chính file hợp đồng.
_cay_gc = ast.parse(open(os.path.join(GOC, 'giac_cam.py'), encoding='utf-8').read())
_imp_gc = set()
for _n in ast.walk(_cay_gc):
    if isinstance(_n, ast.Import):
        _imp_gc |= {a.name.split('.')[0] for a in _n.names}
    elif isinstance(_n, ast.ImportFrom) and _n.module:
        _imp_gc.add(_n.module.split('.')[0])
kt('giac_cam.py KHÔNG import tkinter (để test headless được)',
   'tkinter' not in _imp_gc, sorted(_imp_gc))
for chan in sorted(K.CHAN_HOP_LE):
    kt(f'GiacCam có chân {chan}()', callable(getattr(K.GiacCam, chan, None)))

print('== B. điểm vào chuẩn ==')
for ten in MODULE_TINH_NANG:
    p = os.path.join(GOC, ten)
    if not os.path.isfile(p):
        kt(f'{ten} tồn tại', False, 'không thấy file')
        continue
    _, _, diem_vao, _ = _quet(p)
    if NGUONG.get(ten, 0) > 0:
        # module chưa chuyển: chỉ ghi nhận, không ép
        print(f'  ....  {ten}: điểm vào = {diem_vao} (chưa chuyển, bỏ qua)')
    else:
        kt(f'{ten} có gan_vao(parent, giac)',
           diem_vao is not None and len(diem_vao) >= 2, f'thấy {diem_vao}')

print('== C. CHỐT: điểm chạm ngoài 5 chân — chỉ được GIẢM ==')
tong_cham = 0
for ten in MODULE_TINH_NANG:
    p = os.path.join(GOC, ten)
    if not os.path.isfile(p):
        continue
    cham, gan, _, _ = _quet(p)
    tong_cham += len(cham)
    nguong = NGUONG.get(ten, 0)
    dat = len(cham) <= nguong
    if not dat:
        _sai += 1
    dau = 'PASS' if dat else 'FAIL'
    xu = ''
    if len(cham) < nguong:
        xu = f'  <-- SẠCH HƠN NGƯỠNG {nguong}, hạ NGUONG xuống {len(cham)}'
    elif not dat:
        xu = f'  <-- VƯỢT NGƯỠNG {nguong}, KHÔNG được nâng ngưỡng'
    print(f'  {dau}  {ten:24s} chạm {len(cham):2d} / ngưỡng {nguong:2d}{xu}')
    if cham and not dat:
        for dong, a in cham[:8]:
            print(f'          dòng {dong}: .{a}')

print('== D. CHỐT: module KHÔNG được gán thuộc tính vào app ==')
for ten in MODULE_TINH_NANG:
    p = os.path.join(GOC, ten)
    if not os.path.isfile(p):
        continue
    _, gan, _, _ = _quet(p)
    nguong = NGUONG_GAN.get(ten, 0)
    kt(f'{ten} gán {len(gan)} thuộc tính (ngưỡng {nguong})',
       len(gan) <= nguong, [f'dòng {d}: {a}' for d, a in gan[:6]])

print('== E. CHỐT: cửa thoát hiểm chỉ được GIẢM ==')
dem_th = 0
noi_th = []
for ten in sorted(os.listdir(GOC)):
    if not ten.endswith('.py') or ten in ('giac_cam.py',):
        continue
    src = open(os.path.join(GOC, ten), encoding='utf-8', errors='replace').read()
    n = src.count('.thoat_hiem(')
    if n:
        dem_th += n
        noi_th.append(f'{ten}:{n}')
kt(f'thoat_hiem dùng {dem_th} lần (ngưỡng {NGUONG_THOAT_HIEM})',
   dem_th <= NGUONG_THOAT_HIEM, noi_th)

print('== F. GiacCam chặn thật, không phải chỉ ghi luật ==')
kg = K.GiacCamGia({'X': '1'})
try:
    kg.nut_chay
    kt('đọc thuộc tính lạ bị chặn', False)
except K.LoiViPhamGiac:
    kt('đọc thuộc tính lạ bị chặn', True)
try:
    kg.bang_phase2 = 1
    kt('gán thuộc tính bị chặn', False)
except K.LoiViPhamGiac:
    kt('gán thuộc tính bị chặn', True)
kt('GiacCamGia chạy được không cần tkinter', kg.ui(lambda: 1) == 1)
kt('GiacCamGia.db() dùng được', kg.db() is not None)

print(f'\n  Tổng điểm chạm toàn hệ: {tong_cham} '
      f'(ngưỡng cộng dồn {sum(NGUONG.values())})')
print(f'\nTONG SAI: {_sai}')
raise SystemExit(1 if _sai else 0)
