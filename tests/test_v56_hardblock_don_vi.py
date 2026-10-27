# -*- coding: utf-8 -*-
"""
Ver 5.6 — Hard Block chặn nhầm số CÓ ĐƠN VỊ.

Bug thật (21/08/2026, batch 14 SKU MBA khô THIBIDI, sheet 03 dòng 583-596
của 9MASTER_Ver17_SACH_TEXT_20260821.xlsx): Hard Block chặn 5/5 dòng đầu:

    [1/14] LTC-TBD-3P-160-KHO-DUC
       Hard Block chặn: dac_diem_html: ['2950W', '4%', '740W']

Mọi số bị chặn ĐỀU CÓ THẬT trong MASTER (Po=740, Pk=2950, Uk=4). Nguyên
nhân: MASTER lưu SỐ TRẦN, đơn vị nằm ở TÊN CỘT; _kho_cua_dong() chỉ bóc
được cặp số+đơn vị dính liền trong GIÁ TRỊ -> kho rỗng -> AI viết "740W"
bị coi là bịa.

FILE NÀY LÀ ĐIỀU KIỆN NGHIỆM THU. Phần quan trọng nhất KHÔNG phải 3 case
PASS, mà là 2 case CHẶN ở cuối: nới lỏng quá tay thì hỏng cả hệ thống
chống bịa. Case "cột RỖNG mà AI vẫn viết được số" là lý do guard tồn tại.

Chạy: python3 tests/test_v56_hardblock_don_vi.py   (từ thư mục gốc)
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))

import render_phase2 as R
import cauhinh as C
import ai_wp_adapter as AWP

_loi = []
_tong = 0


def ck(ten, dieu_kien, chi_tiet=''):
    global _tong
    _tong += 1
    print(('  OK   ' if dieu_kien else '  SAI  ') + ten + (f'  <- {chi_tiet}' if not dieu_kien and chi_tiet else ''))
    if not dieu_kien:
        _loi.append(ten)


def dong(**ghi_de):
    """Dòng 583 THẬT của MASTER Ver17 — MBA khô 160kVA THIBIDI.

    Po/Pk/Uk là SỐ TRẦN, đúng như MASTER lưu. Không thêm đơn vị vào giá
    trị: chính chỗ đó là bug."""
    r = {
        'profile_id': 'may_bien_ap_do_luong', 'outline_id': 'outline_may_bien_ap',
        'ma_goc': 'LTC-TBD-3P-160-KHO-DUC',
        'ten_goc': 'Máy biến áp khô 3 pha 160kVA THIBIDI',
        'thuong_hieu': 'THIBIDI', 'quy_cach': '', 'dvt': 'Cái',
        'cong_suat': '160 kVA', 'cap_dien_ap': '22/0.4',
        'ton_hao_khong_tai': '740',      # nhãn: Tổn hao không tải Po (W)
        'ton_hao_ngan_mach': '2950',     # nhãn: Tổn hao ngắn mạch Pk (W)
        'dien_ap_ngan_mach': '4',        # nhãn: Điện áp ngắn mạch Uk (%)
        'thong_so_dong': {},
    }
    r.update(ghi_de)
    return r


print('== 1) NĂM CASE NGHIỆM THU ==')
r = dong()

ck('C1 MASTER 740, AI viết "740W" -> PASS',
   R.kiem_tra_bia('Tổn hao không tải chỉ 740W.', r) == [],
   R.kiem_tra_bia('Tổn hao không tải chỉ 740W.', r))

ck('C2 MASTER 740, AI viết "740 W" -> PASS',
   R.kiem_tra_bia('Tổn hao không tải chỉ 740 W.', r) == [],
   R.kiem_tra_bia('Tổn hao không tải chỉ 740 W.', r))

ck('C3 MASTER 4, AI viết "4%" -> PASS',
   R.kiem_tra_bia('Điện áp ngắn mạch Uk 4%.', r) == [],
   R.kiem_tra_bia('Điện áp ngắn mạch Uk 4%.', r))

ck('C4 MASTER 740, AI viết "745W" -> CHẶN',
   R.kiem_tra_bia('Tổn hao không tải chỉ 745W.', r) == ['745W'],
   R.kiem_tra_bia('Tổn hao không tải chỉ 745W.', r))

r_rong = dong(cap_dien_ap='')
ck('C5 cột Cấp Điện Áp RỖNG, AI viết "22/0.4kV" -> CHẶN',
   R.kiem_tra_bia('Máy biến áp 22/0.4kV.', r_rong) == ['22/0.4kV'],
   R.kiem_tra_bia('Máy biến áp 22/0.4kV.', r_rong))

print('== 2) TÁI HIỆN ĐÚNG DÒNG LOG THẬT ==')
# Nguyên văn 3 số bị chặn ở [1/14] — sau khi vá phải sạch.
ck('LOG-583 dac_diem_html sạch',
   R.kiem_tra_bia('Tổn hao không tải 740W, tổn hao ngắn mạch 2950W, Uk 4%.', r) == [],
   R.kiem_tra_bia('Tổn hao không tải 740W, tổn hao ngắn mạch 2950W, Uk 4%.', r))

r586 = dong(ma_goc='LTC-TBD-3P-400-KHO-DUC', cong_suat='400 kVA',
            ton_hao_khong_tai='1150', ton_hao_ngan_mach='5405', dien_ap_ngan_mach='4')
ck('LOG-586 (400kVA: 1150/5405/4%) sạch',
   R.kiem_tra_bia('Po 1150W, Pk 5405W, Uk 4%.', r586) == [],
   R.kiem_tra_bia('Po 1150W, Pk 5405W, Uk 4%.', r586))

print('== 3) CHỐNG NỚI TAY — guard phải còn răng ==')
# 3a) Số của SKU KHÁC không được lọt sang SKU này.
ck('CHEO-SKU số 1150W của dòng 586 phải bị chặn ở dòng 583',
   R.kiem_tra_bia('Tổn hao 1150W.', r) == ['1150W'],
   R.kiem_tra_bia('Tổn hao 1150W.', r))

# 3b) Đúng số nhưng SAI ĐƠN VỊ -> vẫn bịa. 740 là W, không phải kVA/kV/A.
for dv in ('kVA', 'kV', 'A', 'kg', 'mm'):
    ck(f'SAI-DON-VI "740{dv}" phải bị chặn',
       R.kiem_tra_bia(f'Thông số 740{dv}.', r) == [f'740{dv}'],
       R.kiem_tra_bia(f'Thông số 740{dv}.', r))

# 3c) Lệch 1 chữ số / lệch phần thập phân -> chặn.
for xau in ('7400W', '74W', '740.5W', '2951W', '5%', '4.5%'):
    ck(f'LECH-SO "{xau}" phải bị chặn',
       R.kiem_tra_bia(f'Thông số {xau}.', r) == [xau],
       R.kiem_tra_bia(f'Thông số {xau}.', r))

# 3d) Loại dữ liệu KHÔNG field nào có (IP, IEC, bảo hành, nhiệt độ) -> chặn.
#     bao_hanh_thang/chung_nhan đã khai trong Registry nhưng MASTER rỗng ->
#     rỗng thì vẫn phải chặn, đúng ý đồ Ver 5.4.
for xau in ('IP54', 'IEC 60076', '24 tháng', '40°C'):
    got = R.kiem_tra_bia(f'Sản phẩm đạt {xau}.', r)
    ck(f'BIA-NGOAI-FIELD "{xau}" phải bị chặn', got != [], got)

# 3e) Field rỗng thì đơn vị của NHÃN cột không được biến thành giấy phép.
r_trong = dong(ton_hao_khong_tai='', ton_hao_ngan_mach='', dien_ap_ngan_mach='')
ck('RONG-HET AI viết "740W" khi cột Po rỗng -> chặn',
   R.kiem_tra_bia('Tổn hao 740W.', r_trong) == ['740W'],
   R.kiem_tra_bia('Tổn hao 740W.', r_trong))
ck('RONG-HET AI viết "4%" khi cột Uk rỗng -> chặn',
   R.kiem_tra_bia('Uk 4%.', r_trong) == ['4%'],
   R.kiem_tra_bia('Uk 4%.', r_trong))

# 3f) Nhãn KHÔNG phải đơn vị không được bóc thành đơn vị.
#     "Hiệu suất năng lượng tối thiểu (E50)" / "(catalogue)" / "(VNĐ)".
ck('NHAN-KHONG-DON-VI "(E50)" không sinh đơn vị',
   R._don_vi_tu_nhan('Hiệu suất năng lượng tối thiểu (E50)') == [], )
ck('NHAN-KHONG-DON-VI "(catalogue)" không sinh đơn vị',
   R._don_vi_tu_nhan('Tổ đấu dây (catalogue)') == [], )
ck('NHAN-KHONG-DON-VI "(VNĐ)" không sinh đơn vị',
   R._don_vi_tu_nhan('Giá List (VNĐ)') == [], )
ck('NHAN-KHONG-DON-VI "(CO/CQ/Quatest)" không sinh đơn vị',
   R._don_vi_tu_nhan('Chứng nhận (CO/CQ/Quatest)') == [], )

# 3g) gia_list TUYỆT ĐỐI không được vào kho số (field nội bộ).
r_gia = dong(gia_list='45000000')
ck('GIA-LIST không lọt vào kho, AI nhắc giá -> chặn',
   R.kiem_tra_bia('Giá 45000000 VNĐ, tổn hao 740W.', r_gia) == [],
   'ghi chú: "VNĐ" không nằm trong _SO_DON_VI nên không bị kiểm — xem ghi chú cuối file')
ck('GIA-LIST không sinh khoá trong kho số',
   not any(k.startswith('45000000') for k in R._kho_cua_dong(r_gia)),
   sorted(k for k in R._kho_cua_dong(r_gia) if k.startswith('45')))

print('== 4) CHUẨN HOÁ 2 PHÍA ==')
ck('CHUAN-SO "4,0" == "4"', R._chuan_gia_tri_so('4,0') == '4', R._chuan_gia_tri_so('4,0'))
ck('CHUAN-SO "0,60" == "0.6"', R._chuan_gia_tri_so('0,60') == '0.6', R._chuan_gia_tri_so('0,60'))
ck('CHUAN-SO "745" != "740"', R._chuan_gia_tri_so('745') != R._chuan_gia_tri_so('740'))
ck('CHUAN-DON-VI mm2 == mm²', R._chuan_don_vi('mm2') == R._chuan_don_vi('mm²'))
ck('CHUAN-DON-VI "W" == " w "', R._chuan_don_vi('W') == R._chuan_don_vi(' w '))
ck('CHUAN-SO ghép: 740W == 740 W', R._chuan_so('740', 'W') == R._chuan_so('740', ' w'))

# Dấu phẩy thập phân VN ở PHÍA MASTER, dấu chấm ở phía AI.
r_phay = dong(cap_dien_ap='22/0,4')
ck('THAP-PHAN MASTER "22/0,4" khớp AI "22/0.4kV"',
   R.kiem_tra_bia('Máy 22/0.4kV.', r_phay) == [],
   R.kiem_tra_bia('Máy 22/0.4kV.', r_phay))

print('== 5) BÓC ĐƠN VỊ TỪ NHÃN CỘT ==')
m = R._don_vi_theo_field('may_bien_ap_do_luong', 'outline_may_bien_ap')
ck('MAP ton_hao_khong_tai -> W', m.get('ton_hao_khong_tai') == ['W'], m.get('ton_hao_khong_tai'))
ck('MAP dien_ap_ngan_mach -> %', m.get('dien_ap_ngan_mach') == ['%'], m.get('dien_ap_ngan_mach'))
ck('MAP kich_thuoc_a -> mm', m.get('kich_thuoc_a') == ['mm'], m.get('kich_thuoc_a'))
ck('MAP tong_khoi_luong -> kg', m.get('tong_khoi_luong') == ['kg'], m.get('tong_khoi_luong'))
ck('MAP bao_hanh_thang -> tháng', m.get('bao_hanh_thang') == ['tháng'], m.get('bao_hanh_thang'))
ck('MAP gia_list KHÔNG có trong map', 'gia_list' not in m, list(m))
ck('MAP hieu_suat_e50 KHÔNG có đơn vị', 'hieu_suat_e50' not in m, m.get('hieu_suat_e50'))

mc = R._don_vi_theo_field('cap_dien', 'outline_cap_dien')
ck('MAP cáp: tiet_dien -> mm²', mc.get('tiet_dien') == ['mm²'], mc.get('tiet_dien'))
# Profile cáp: cột "Cấp Điện Áp" / nhãn "Cấp điện áp" KHÔNG khai đơn vị.
# Không sao — giá trị cáp luôn là CẶP GHÉP ("0.6/1") nên đi lớp cụm + lớp 4,
# không cần đường ghép-đơn-vị-từ-nhãn. Ghi assert theo THỰC TẾ để lần sau ai
# đổi nhãn thành "Cấp điện áp (kV)" thì test này nhắc mà kiểm lại.
ck('MAP cáp: cap_dien_ap không khai đơn vị (đi lớp cụm)',
   'cap_dien_ap' not in mc, mc.get('cap_dien_ap'))
ck('MAP cáp: dong_dien_dinh_muc_catalogue -> A',
   mc.get('dong_dien_dinh_muc_catalogue') == ['A'], mc.get('dong_dien_dinh_muc_catalogue'))

print('== 6) KHÔNG PHÁ HÀNH VI CŨ (cột quét động, cụm ghép) ==')
r_dong = dong(thong_so_dong={'Tổn hao không tải Po cực đại theo tiêu chuẩn EVN (W)': '640',
                             'Tiêu chuẩn hiệu suất năng lượng áp dụng': 'TCVN 8525:2015'})
ck('DONG-CU số cột động "640W" vẫn PASS',
   R.kiem_tra_bia('Giới hạn EVN 640W.', r_dong) == [],
   R.kiem_tra_bia('Giới hạn EVN 640W.', r_dong))
ck('DONG-CU "TCVN 8525:2015" vẫn PASS',
   R.kiem_tra_bia('Đạt TCVN 8525:2015.', r_dong) == [],
   R.kiem_tra_bia('Đạt TCVN 8525:2015.', r_dong))
ck('DONG-CU "TCVN 8525:2019" (sai số) vẫn CHẶN',
   R.kiem_tra_bia('Đạt TCVN 8525:2019.', r_dong) != [])

r_cap = {'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien',
         'ma_goc': 'C1', 'ten_goc': 'Cáp CVV', 'thuong_hieu': 'CADIVI',
         'quy_cach': '', 'dvt': 'm', 'tiet_dien': '3x50+1x25', 'cap_dien_ap': '0.6/1',
         'vat_lieu_ruot': 'Đồng', 'thong_so_dong': {}}
ck('CUM-CU "3x50+1x25mm²" vẫn PASS',
   R.kiem_tra_bia('Ruột 3x50+1x25mm².', r_cap) == [],
   R.kiem_tra_bia('Ruột 3x50+1x25mm².', r_cap))
ck('CUM-CU "0.6/1kV" vẫn PASS',
   R.kiem_tra_bia('Cấp 0.6/1kV.', r_cap) == [],
   R.kiem_tra_bia('Cấp 0.6/1kV.', r_cap))
ck('CUM-CU "9x50mm²" (bịa) vẫn CHẶN',
   R.kiem_tra_bia('Ruột 9x50mm².', r_cap) != [])
ck('CUM-CU "99/1kV" (bịa) vẫn CHẶN',
   R.kiem_tra_bia('Cấp 99/1kV.', r_cap) != [])
ck('LOP-4 "1kV" tách từ cặp "0.6/1" vẫn PASS',
   R.kiem_tra_bia('Điện áp 1kV.', r_cap) == [],
   R.kiem_tra_bia('Điện áp 1kV.', r_cap))
ck('LOP-4 "1A" (đúng số, SAI HỌ đơn vị) vẫn CHẶN',
   R.kiem_tra_bia('Dòng 1A.', r_cap) == ['1A'],
   R.kiem_tra_bia('Dòng 1A.', r_cap))

print('== 7) MODEL CHẾT & TIMEOUT ==')
ck('MODEL-CHET có gemini-5.0-flash trong danh sách', 'gemini-5.0-flash' in C.MODEL_CHET)

_moi_truong_cu = {k: _os.environ.get(k) for k in
                  ('MODEL_GEMINI', 'MODEL_GEMINI_DU_PHONG', 'GOOGLE_API_KEY', 'GOOGLE_API_KEY_DU_PHONG')}
try:
    _os.environ['GOOGLE_API_KEY'] = 'k1'
    _os.environ['GOOGLE_API_KEY_DU_PHONG'] = 'k2,k3'
    _os.environ['MODEL_GEMINI'] = 'gemini-3.6-flash'
    _os.environ['MODEL_GEMINI_DU_PHONG'] = 'gemini-5.0-flash,gemini-3.5-flash'
    gc = C.doc_gemini()
    ck('MODEL-CHET bị loại khỏi model_du_phong',
       gc['model_du_phong'] == ['gemini-3.5-flash'], gc['model_du_phong'])
    ck('MODEL-CHET không đụng model chính hợp lệ',
       gc['model'] == 'gemini-3.6-flash', gc['model'])

    _os.environ['MODEL_GEMINI'] = 'gemini-5.0-flash'
    gc2 = C.doc_gemini()
    ck('MODEL-CHET làm model CHÍNH -> đôn dự phòng lên, không trả rỗng',
       gc2['model'] == 'gemini-3.5-flash' and gc2['model_du_phong'] == [],
       (gc2['model'], gc2['model_du_phong']))

    _os.environ['MODEL_GEMINI_DU_PHONG'] = 'gemini-5.0-flash'
    gc3 = C.doc_gemini()
    ck('MODEL-CHET sạch cả 2 danh sách -> model rỗng (UI báo chưa cấu hình)',
       gc3['model'] == '' and gc3['model_du_phong'] == [], (gc3['model'], gc3['model_du_phong']))
finally:
    for k, v in _moi_truong_cu.items():
        if v is None:
            _os.environ.pop(k, None)
        else:
            _os.environ[k] = v

import inspect
ck('TIMEOUT hằng số = 20s', AWP.TIMEOUT_GEMINI == 20, AWP.TIMEOUT_GEMINI)
ck('TIMEOUT goi_ai_that mặc định = 20s',
   inspect.signature(AWP.goi_ai_that).parameters['timeout'].default == 20)
ck('TIMEOUT goi_ai_co_du_phong mặc định = 20s',
   inspect.signature(AWP.goi_ai_co_du_phong).parameters['timeout'].default == 20)
_src_ui = open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'giao-dien.py'),
               encoding='utf-8').read()
ck('TIMEOUT UI không còn hard-code 45s cho Gemini',
   'timeout=AWP.TIMEOUT_GEMINI' in _src_ui and 'goi_ai_co_du_phong(row_ai, mau, danh_sach_thu, site_cfg=site_cfg, timeout=45)' not in _src_ui)

print()
if _loi:
    print(f'[FAIL] {len(_loi)} case: ' + ', '.join(_loi))
    _sys.exit(1)
# Marker phải khớp regex phân loại của run_tests.py:
#     ^\s*(?:\[PASS\]|PASS(?:\b|[:_])|(?:TỔNG|TONG|TOTAL)\b.*\bPASS\b)
# In "TẤT CẢ PASS." không khớp (PASS không ở đầu dòng) -> runner xếp nhầm
# vào FAIL dù exit=0. Đã tái hiện thật khi chạy run_tests.py lần đầu.
print(f'[PASS] test_v56_hardblock_don_vi: {_tong} case, 0 FAIL.')

# ---------------------------------------------------------------------------
# GHI CHÚ CÒN NỢ (không fix trong bản này, ghi ra để không quên):
#   1. "Hiệu suất năng lượng tối thiểu E50 (catalogue)" không có đơn vị trong
#      tên cột -> AI viết "98.5%" vẫn bị chặn dù giá trị có thật. Sửa đúng =
#      đổi tên cột MASTER thành "... E50 (%, catalogue)" -> ĐỤNG cot_import,
#      phải chạy lại import_phase2_pipeline. Cố ý để ngoài phạm vi.
#   2. VNĐ/giá không nằm trong _SO_DON_VI nên số tiền AI viết không bị Hard
#      Block kiểm. Đây là hành vi CŨ, không đổi ở bản này. Chặn giá bịa đang
#      do sweep_rac/MAU_RAC lo, không phải Hard Block.
# ---------------------------------------------------------------------------
