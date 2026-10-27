# -*- coding: utf-8 -*-
"""Test tab Hàng đợi + bếp trưởng (Ver 3.5)."""
import sys, os, json, sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bep_truong as B

P = F = 0
def kt(ten, dk):
    global P, F
    if dk: P += 1; print('  PASS ', ten)
    else:  F += 1; print('  FAIL ', ten)

print('== 1. bep_truong.phan_hang ==')
mba = 'may_bien_ap_do_luong'
kt('ĐỦ khi có field kỹ thuật khai cứng',
   B.phan_hang({'profile_id': mba, 'cong_suat': '250', 'cap_dien_ap': '22/0.4',
                'ton_hao_khong_tai': '340'})['hang'] == B.DU)
kt('ĐỦ khi số kỹ thuật nằm ở CỘT ĐỘNG (tên cột đợt enrich mới)',
   B.phan_hang({'profile_id': mba, 'cong_suat': '250', 'cap_dien_ap': '22/0.4',
                'thong_so_dong': {'Tổn hao không tải Po cực đại theo tiêu chuẩn EVN (W)': '640'}})['hang'] == B.DU)
kt('VỪA khi có định danh, không có số kỹ thuật',
   B.phan_hang({'profile_id': mba, 'cong_suat': '160', 'cap_dien_ap': '22/0.4'})['hang'] == B.VUA)
kt('ĐÓI khi thiếu định danh',
   B.phan_hang({'profile_id': mba, 'ten_goc': 'MBA'})['hang'] == B.DOI)
kt('ô rỗng/"-"/"nan" không tính là có dữ liệu',
   B.phan_hang({'profile_id': mba, 'cong_suat': '-', 'cap_dien_ap': 'nan'})['hang'] == B.DOI)
kt('profile lạ không ném lỗi',
   B.phan_hang({'profile_id': 'khong_ton_tai'})['hang'] in (B.DU, B.VUA, B.DOI))
kt('luôn trả lý do để hiện lên giao diện',
   bool(B.phan_hang({'profile_id': mba})['ly_do']))
kt('thong_ke đếm đúng',
   B.thong_ke([{'profile_id': mba, 'cong_suat': '1', 'cap_dien_ap': '2', 'ton_hao_khong_tai': '3'},
               {'profile_id': mba}]) == {B.DU: 1, B.VUA: 0, B.DOI: 1})

print('== 2. cảnh báo + ký hiệu nguồn ==')
kt('canh_bao đọc cột Ghi chú - Cần kiểm lại',
   B.canh_bao({'ghi_chu_can_kiem': 'Po nội suy'}) == 'Po nội suy')
kt('canh_bao rỗng khi không có', B.canh_bao({}) == '')
kt('ky_hieu_so_lieu trả ≤ cho mức quy chuẩn EVN',
   B.ky_hieu_so_lieu({'nguon_ky_hieu': '≤'}) == '≤')

print('== 3. profiles khai 3 cột nguồn Ver5 ==')
import profiles as P2
ci = P2.PROFILES[mba]['cot_import']
kt('khai Nguồn - Ký hiệu hiển thị Po/Pk', ci.get('Nguồn - Ký hiệu hiển thị Po/Pk') == 'nguon_ky_hieu')
kt('khai Ghi chú - Cần kiểm lại', ci.get('Ghi chú - Cần kiểm lại') == 'ghi_chu_can_kiem')
kt('3 cột nguồn KHÔNG in ra bài (không nằm trong cot_bang)',
   not any(f in ('nguon_ky_hieu', 'nguon_loai_so_lieu', 'ghi_chu_can_kiem')
           for f, _ in P2.PROFILES[mba]['cot_bang']))

print('== 4. tab Hàng đợi dựng được ==')
try:
    import tksheet  # dependency giao diện chỉ có trên môi trường desktop đầy đủ
except ImportError:
    print('SKIP: thiếu dependency tksheet — bỏ riêng phần UI Hàng đợi; môi trường Windows production cài qua requirements.txt')
    print(f'\n===== KẾT QUẢ PHẦN CORE: PASS {P} / FAIL {F}; UI SKIP =====')
    sys.exit(77 if F == 0 else 1)
import tkinter as tk
from tkinter import ttk
import hang_doi as HD
root = tk.Tk(); root.withdraw()
nb = ttk.Notebook(root)
t = HD.gan_vao(nb, None)
kt('gan_vao trả về tab', t is not None)
kt('bảng tksheet dựng được', t.bang is not None)
kt('có đủ 4 ô đếm trạng thái', len(t.dem_nhan) == 4)
t.v_loc.set(B.DOI); t._ap_loc()
kt('lọc theo hạng Đói chỉ còn dòng Đói',
   all(d['hang'] == B.DOI for d in t.dang_hien))
t.v_loc.set('canh_bao'); t._ap_loc()
kt('lọc cảnh báo chỉ còn dòng có cảnh báo',
   all(d['canh_bao'] for d in t.dang_hien))
t.v_loc.set('tat_ca'); t._ap_loc()
t._chon_hang_loat(True)
kt('chọn hàng loạt tick hết dòng đang hiện',
   all(d['chon'] for d in t.dang_hien) if t.dang_hien else True)
t._chon_hang_loat(False)
kt('bỏ chọn hết', not any(d['chon'] for d in t.dang_hien))
root.destroy()

print(f'\n===== KẾT QUẢ: PASS {P} / FAIL {F} =====')
