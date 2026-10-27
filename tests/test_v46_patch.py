import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# -*- coding: utf-8 -*-
"""Ver 4.6 — test khối chịu tải, giá trị suy ra, cổng chất lượng, lọc điện áp."""
import khoi_chiu_tai as KCT
import cong_chat_luong as CG
import ra_soat_dien_ap as RS
import profiles as P

so_fail = 0


def kiem(nhan, dk, ct=''):
    global so_fail
    if dk:
        print(f'  OK  {nhan}')
    else:
        so_fail += 1
        print(f'  SAI {nhan} {ct}')


_st = lambda k: 'class="x"'
_esc = lambda s: str(s)


def r(**kw):
    d = {'outline_id': 'outline_cap_dien', 'ten_goc': 'Cáp CXV/DSTA 3x95 (0.6/1kV)',
         'dong_dien_dinh_muc_catalogue': '', 'kieu_lap_dat_catalogue': '',
         'do_sut_ap_catalogue': '', 'dieu_kien_quy_chieu_catalogue': '',
         'dien_tro_dc_catalogue': '', 'duong_kinh_ruot_dan_catalogue': '',
         'nguon_du_lieu_catalogue': ''}
    d.update(kw)
    return d


print('== A. Khối chịu tải chỉ hiện khi CÓ số ==')
kiem('không có dòng tải -> không hiện khối', KCT.khoi_chiu_tai(r(), _st, _esc) == '')
kiem('outline khác -> không hiện',
     KCT.khoi_chiu_tai(r(outline_id='outline_may_bien_ap',
                         dong_dien_dinh_muc_catalogue='315'), _st, _esc) == '')
h = KCT.khoi_chiu_tai(r(dong_dien_dinh_muc_catalogue='315'), _st, _esc)
kiem('có dòng tải -> hiện khối', bool(h))
kiem('tiêu đề bám đúng truy vấn "chịu tải bao nhiêu"', 'chịu tải bao nhiêu' in h)
kiem('có ghi 315 A', '315 A' in h)

print('== B. Điều kiện quy chiếu LUÔN đi kèm ==')
# Dòng tải trần không kèm điều kiện quy chiếu là sai kỹ thuật.
kiem('không có cột điều kiện -> vẫn có câu nhắc chiết giảm', 'chiết giảm' in h)
h2 = KCT.khoi_chiu_tai(r(dong_dien_dinh_muc_catalogue='315',
                         dieu_kien_quy_chieu_catalogue='Nhiet do dat 15 C'), _st, _esc)
kiem('có cột điều kiện -> in nguyên văn', 'Nhiet do dat 15 C' in h2)

print('== C. Giá trị suy ra — công thức IEE 522-8 ==')
# L = V_cho_phep * 1000 / (dV * I) ; 3 pha 380V cho phép 9,5 V
kiem('3 pha: dV=0,45 I=315 -> ~67 m',
     abs(KCT.chieu_dai_toi_da(0.45, 315, 3) - 9.5 * 1000 / (0.45 * 315)) < 1e-6)
kiem('1 pha dùng ngưỡng 5,5 V',
     abs(KCT.chieu_dai_toi_da(1.0, 100, 1) - 55.0) < 1e-6)
kiem('thiếu số -> None', KCT.chieu_dai_toi_da(None, 315) is None)
# P = k*I^2*R/10 ; k=3 cho 3 pha
kiem('tổn hao 100m: R=0,193 I=315 3pha',
     abs(KCT.ton_hao_100m(0.193, 315, 3) - 3 * 315 ** 2 * 0.0193) < 1e-6)
kiem('thiếu R -> None', KCT.ton_hao_100m(None, 315) is None)

print('== D. Hai SKU anh em ra hai khối KHÁC NHAU ==')
import difflib
a = KCT.khoi_chiu_tai(r(ten_goc='Cáp CXV/DSTA 3x95', dong_dien_dinh_muc_catalogue='315',
                        do_sut_ap_catalogue='0.45', dien_tro_dc_catalogue='0.193'),
                      _st, _esc)
b = KCT.khoi_chiu_tai(r(ten_goc='Cáp CXV/DSTA 3x120', dong_dien_dinh_muc_catalogue='360',
                        do_sut_ap_catalogue='0.36', dien_tro_dc_catalogue='0.153'),
                      _st, _esc)
ty = difflib.SequenceMatcher(None, a, b).ratio()
kiem(f'độ giống dưới 90% (đo được {100 * ty:.1f}%)', ty < 0.90)

print('== E. Cổng chất lượng ==')
bo = [{'record_id': 'r1', 'ten_goc': 'A', 'html': '<table><tr></tr></table>x' * 3,
       'row': {'thuong_hieu': 'H', 'outline_id': 'o'}},
      {'record_id': 'r2', 'ten_goc': 'B', 'html': '<table><tr></tr></table>x' * 3,
       'row': {'thuong_hieu': 'H', 'outline_id': 'o'}}]
bc, cb = CG.soat(bo)
kiem('bắt được bài mỏng', bc['so_mong'] == 2, f"-> {bc['so_mong']}")
kiem('bắt được bài trùng', bc['so_trung'] >= 1, f"-> {bc['so_trung']}")
kiem('bóc thẻ HTML trước khi đo',
     CG.van_ban_hien_thi('<p>xin <b>chào</b></p>') == 'xin chào')
kiem('đếm đúng số dòng bảng',
     CG.dem_dong_bang('<table><tr></tr><tr></tr></table>') == 2)

print('== F. Lọc cấp điện áp — lỗi cáp có giáp lọt lưới ==')
# Bug 4.6: nhánh CVV_GIAP/CXV_GIAP gán đè key vô điều kiện -> cáp trung thế
# mang mã có giáp ăn dòng tải bảng 0,6/1 kV.
kiem('1.8/3(3.6)kV -> 3.6', RS.dien_ap_max_kv('CXV/DSTA3x95mm2- 1.8/3(3.6)kV') == 3.6)
kiem('0.6/1kV -> 1.0', RS.dien_ap_max_kv('CXV/DSTA3x95mm2 (0.6/1kV)') == 1.0)
kiem('12/20(24)kV -> 24', RS.dien_ap_max_kv('Cáp 12/20(24)kV') == 24.0)
kiem('không có kV -> None', RS.dien_ap_max_kv('Cáp CXV 3x95') is None)

print('== G. Thông số điện đã có đường vào bài ==')
pr = P.PROFILES['cap_dien']
for c in ('Dong dien dinh muc (A) [catalogue]',
          'Dien tro DC toi da 20C (Ohm/km) [catalogue]'):
    kiem(f'cot_import khai "{c[:28]}..."', c in pr['cot_import'])
khoa_bang = [k for k, _ in pr['cot_bang']]
kiem('cot_bang có dòng định mức', 'dong_dien_dinh_muc_catalogue' in khoa_bang)
kiem('cot_bang có điện trở DC', 'dien_tro_dc_catalogue' in khoa_bang)
kiem('gia_list vẫn không lọt vào bảng',
     not (set(khoa_bang) & P.FIELD_CAM_TUYET_DOI))

print('== H. Ver 4.6.1 — vá text: sửa đúng, không sửa quá tay ==')
import va_chinh_ta as VCT
kiem('xuống dòng trong ô -> khoảng trắng',
     VCT.sua_o('Máy cắt\n27kV')[0] == 'Máy cắt 27kV')
kiem('khoảng trắng đôi', VCT.sua_o('Dây CV22mm2  - Cadivi')[0] == 'Dây CV22mm2 - Cadivi')
kiem('khoảng trắng đầu/cuối', VCT.sua_o('  VNBCB50010   ')[0] == 'VNBCB50010')
kiem('lặp thương hiệu',
     VCT.sua_o('Dây CV1.5mm2 - Cadivi - Cadivi')[0] == 'Dây CV1.5mm2 - Cadivi')
kiem('khoảng trắng trước dấu phẩy',
     VCT.sua_o('LA 18kV , 10kA')[0] == 'LA 18kV, 10kA')
kiem('nháy cong -> nháy thẳng', "'" in VCT.sua_o('mã \u2018ABC\u2019')[0])
kiem('tab -> khoảng trắng', '\t' not in VCT.sua_o('LBS\t25.8kV')[0])

# KHÔNG được sửa quá tay
kiem('KHÔNG cắt dấu chấm cuối CÂU trong cột ghi chú',
     VCT.sua_o('SKU không phải hạ thế. Không áp số liệu.',
               cot='Ly do khong co dong tai')[0].endswith('.'))
kiem('CÓ cắt dấu chấm thừa ở Tên hàng',
     not VCT.sua_o('Dao cắt có tải LBS 24kV.', cot='Tên hàng')[0].endswith('.'))
kiem('KHÔNG đổi mm2 thành mm²', 'mm2' in VCT.sua_o('Dây CV1.5mm2')[0])
kiem('KHÔNG đổi gạch ngang dài', '\u2013' in VCT.sua_o('Recloser 27kV \u2013 630A')[0])
kiem('cột khoá slug nằm ngoài vùng sửa', 'Slug chỉ định' in VCT.COT_KHOA)
kiem('ô sạch -> không báo sửa', VCT.sua_o('Dây CXV 3x95')[1] == [])

print('== I. Ver 4.6.2 — title cáp có tiết diện + dòng tải ==')
import render_phase2 as R2
def tt(ten, I=''):
    return R2.dung_tieu_de({'outline_id': 'outline_cap_dien', 'ten_goc': ten,
                            'thuong_hieu': 'Cadivi',
                            'dong_dien_dinh_muc_catalogue': I})
t1 = tt('Dây CXV/DSTA3x95mm2 (0.6/1kV) - Cadivi', '315.0')
t2 = tt('Dây CXV/DSTA3x120mm2 (0.6/1kV) - Cadivi', '360')
kiem('title có tiết diện', '3x95' in t1)
kiem('title có dòng tải', '315A' in t1, f'-> {t1}')
kiem('KHÔNG cắt số 0 cuối (360 chứ không phải 36)', '360A' in t2, f'-> {t2}')
kiem('315.0 -> 315A, không phải 315.0A', '315.0A' not in t1)
kiem('có từ khoá ý định', 'báo giá' in t1.lower())
kiem('bỏ đuôi "- Cadivi" lặp', t1.count('Cadivi') == 1, f'-> {t1}')
kiem('dài <= 65 ký tự', len(t1) <= 65 and len(t2) <= 65, f'-> {len(t1)}/{len(t2)}')
kiem('không có dòng tải vẫn ra title', bool(tt('Dây CXV4x300mm2 (0.6/1kV) - Cadivi')))
kiem('hai SKU anh em ra title khác nhau', t1 != t2)

print('== J. Ver 4.6.2 — dọn rác: giá list và caveat A2608 ==')
import sweep_rac as SR
ma = [m[0] for m in SR.MAU_RAC]
kiem('có luật gia_list_lo', 'gia_list_lo' in ma)
kiem('có luật caveat_a2608', 'caveat_a2608' in ma)
h = ('<small>MBT1P100 · Máy biến áp · 82.650.000 ₫</small>'
     '<p>Theo A2608/QĐ-EVN SPC thì...</p><p>Giữ lại câu này.</p>')
sach, bc2 = SR.don_rac_bai(h)
kiem('xoá được chuỗi giá', '₫' not in sach and '82' not in sach)
kiem('xoá được caveat A2608', 'A2608' not in sach)
kiem('GIỮ NGUYÊN câu bên cạnh', 'Giữ lại câu này' in sach)
kiem('giữ nguyên mã hàng trong khối', 'MBT1P100' in sach)

print(f'\nTONG SAI: {so_fail}')
_sys.exit(1 if so_fail else 0)
