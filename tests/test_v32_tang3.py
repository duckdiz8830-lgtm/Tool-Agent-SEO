# -*- coding: utf-8 -*-
"""Ver 3.2 — test Tầng 3 biến thiên + bảng tra THIBIDI. 0 lượt AI."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tra_cuu_thibidi as TC
import kien_thuc_bien_thien as K

PASS = FAIL = 0


def kiem(dk, ten):
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if dk else (PASS, FAIL + 1)
    print(f'  {"PASS" if dk else "FAIL"}  {ten}')


def chu(h):
    return re.sub('<[^>]+>', ' ', h or '')


R_TBD250 = {'ten_goc': 'Máy biến áp dầu 3Pha 250KVA 22/0.4KV Loại Silic - TBD',
            'cong_suat': '250 kVA', 'cap_dien_ap': '22/0.4 kV',
            'thuong_hieu': 'THIBIDI', 'outline_id': 'outline_may_bien_ap'}

print('== 1. Bảng tra khớp catalogue in ==')
b = TC.tra(250, 3, 'dau', 'THIBIDI')
kiem(b['po_silic'] == 340 and b['po_amorphous'] == 100 and b['pk'] == 2600 and b['uk'] == 4,
     'dầu 3 pha 250kVA: 340/100/2600/4')
kiem(TC.tra(15, 1, 'dau', 'THIBIDI')['po_silic'] == 52, 'dầu 1 pha 15kVA: Po Silic 52W')
k = TC.tra(3200, 3, 'kho', 'THIBIDI')
kiem(k['po_24kv'] == 6050 and k['hieu_suat'] == 99.13, 'khô 3200kVA: 6050W / 99,13%')
kiem(TC.tra(250, 3, 'dau', 'THIBIDI')['noi_suy'] is False
     and TC.tra(180, 3, 'dau', 'THIBIDI')['noi_suy'] is True,
     'mức 180kVA được đánh dấu NỘI SUY theo ghi chú catalogue')

print('== 2. KHÔNG suy sang hãng khác, không đoán ngoài bảng ==')
kiem(TC.tra(250, 3, 'dau', 'MBT') is None, 'hãng MBT -> None (không mượn số THIBIDI)')
kiem(TC.tra(250, 3, 'dau', 'KP/Hàn Quốc') is None, 'hãng KP -> None')
kiem(TC.tra(275, 3, 'dau', 'THIBIDI') is None, '275kVA ngoài bảng -> None (không nội suy bừa)')
kiem(TC.tra(250, 2, 'dau', 'THIBIDI') is None, 'số pha lạ -> None')

print('== 3. Kiến thức BIẾN THIÊN theo dữ liệu ==')
h250 = K.tat_ca_khoi(R_TBD250)
r15 = dict(R_TBD250, ten_goc='Máy biến áp dầu 1Pha 15KVA 12.7/0.23KV Loại Silic - TBD',
           cong_suat='15 kVA', cap_dien_ap='12.7/0.23 kV')
h15 = K.tat_ca_khoi(r15)
kiem(h250 and h15 and h250 != h15, '250kVA và 15kVA ra hai bản văn KHÁC NHAU')
kiem('250kVA' in chu(h250) and '15kVA' in chu(h15), 'mỗi bài nhắc đúng công suất của mình')
kiem('340W' in chu(h250) and '2.600W' in chu(h250), 'in đúng Po/Pk tra được của 250kVA')
kiem('nhà xưởng' in chu(h250) and 'nông thôn' in chu(h15),
     'ngữ cảnh sử dụng đổi theo dải công suất')

print('== 4. Số liệu luôn kèm nguồn + không mạo nhận là số đo ==')
kiem('Catalogue THIBIDI' in chu(h250), 'có ghi nguồn')
kiem('tối đa theo catalogue' in chu(h250), 'nói rõ là giá trị TỐI ĐA theo catalogue')
kiem('không phải kết quả đo' in chu(h250), 'nói rõ KHÔNG phải số đo từng máy')

print('== 5. Thiếu dữ liệu -> im lặng, không viết chay ==')
r_mbt = dict(R_TBD250, thuong_hieu='MBT', ten_goc='Máy biến áp dầu 3Pha 250KVA 22/0.4KV - MBT')
h_mbt = K.tat_ca_khoi(r_mbt)
kiem('340W' not in chu(h_mbt), 'SKU hãng MBT KHÔNG mượn số của THIBIDI')
kiem(h_mbt and '250kVA' in chu(h_mbt), 'vẫn có phần kiến thức không cần số')
kiem(K.tat_ca_khoi({'ten_goc': 'Vỏ mạ kẽm nhúng nóng MBA 3P 560kVA',
                    'outline_id': 'outline_may_bien_ap'}) == ''
     or 'tổn hao' not in chu(K.tat_ca_khoi({'ten_goc': 'Vỏ mạ kẽm nhúng nóng MBA 3P 560kVA',
                                            'outline_id': 'outline_may_bien_ap'})),
     'vỏ mạ kẽm không được gán kiến thức máy biến áp')
kiem(K.tat_ca_khoi(dict(R_TBD250, outline_id='outline_phu_kien')) == '',
     'outline khác -> không chèn khối MBA')

print('== 6. Phép tính có công thức, kiểm lại được ==')
# 340 - 100 = 240W ; 240 x 8760 / 1000 = 2102.4 -> 2.102 kWh
kiem('2.102' in chu(h250) and '8.760' in chu(h250),
     'điện năng tổn hao/năm tính đúng và in kèm công thức')

print('== 7. Suy số pha từ cấp điện áp (dòng KP không ghi pha) ==')
r_kp = {'ten_goc': 'Máy biến áp khô KP 250kVA 22/0,4kV (Cu/Cu)', 'cong_suat': '250 kVA',
        'cap_dien_ap': '22/0.4 kV', 'thuong_hieu': 'KP/Hàn Quốc',
        'outline_id': 'outline_may_bien_ap'}
d = K.dac_trung(r_kp)
kiem(d['pha'] == 3, 'hạ áp 0,4kV -> suy ra 3 pha')
kiem(d['vat_lieu'] == 'cu/cu', 'bóc được vật liệu cuộn dây (Cu/Cu) từ tên')
r_kp2 = dict(r_kp, ten_goc='Máy biến áp khô KP 400kVA 22/0,4kV (Cu/Cu)', cong_suat='400 kVA')
kiem(K.tat_ca_khoi(r_kp) != K.tat_ca_khoi(r_kp2), 'KP 250 và KP 400 KHÔNG còn trùng khít')




# ============================================================ Ver 3.2b
# Vá họ lỗi Ver 2.8 chỉ sửa 1/3 kho: cột quét động phải vào CẢ 3 kho hợp lệ.
# Sự cố thật 06/08: batch 5 bài chết vì Hard Block chặn 'TCVN 8525:2015',
# '99.1%', '4%' — toàn số CÓ THẬT trong record, do enrich sinh ra.
print('== 8. Hard Block không chặn nhầm cột enrich (sự cố batch 06/08) ==')
import render_phase2 as R

ROW_ENRICH = {
    'profile_id': 'may_bien_ap_do_luong', 'outline_id': 'outline_may_bien_ap',
    'ten_goc': 'Máy biến áp dầu 3Pha 250KVA 22/0.4KV Loại Silic - TBD',
    'cong_suat': '250 kVA', 'cap_dien_ap': '22/0.4 kV', 'thuong_hieu': 'THIBIDI',
    'thong_so_dong': {
        'Hiệu suất năng lượng tối thiểu TCVN 8525:2015 (%)': '99.1',
        'Tiêu chuẩn hiệu suất năng lượng áp dụng': 'TCVN 8525:2015',
        'Điện áp ngắn mạch Uk (%, catalogue THIBIDI)': '4',
        'Tổn hao không tải Po (W, catalogue THIBIDI)': '340',
        'Dòng điện danh định phía hạ áp (A)': '360.8',
    },
}
for cum in ('TCVN 8525:2015', 'hiệu suất tối thiểu 99.1%', 'Uk 4%',
            'Po 340W', 'dòng 360.8A'):
    kiem(not R.kiem_tra_bia(cum, ROW_ENRICH), f'CHO QUA số thật: "{cum}"')

print('== 9. Nhưng số BỊA vẫn bị chặn (không nới lỏng) ==')
for cum in ('hiệu suất 99.99%', 'TCVN 1234:2020', 'Uk 12%',
            'bảo hành 60 tháng', 'IP68', 'Po 999W'):
    kiem(bool(R.kiem_tra_bia(cum, ROW_ENRICH)), f'CHẶN số bịa: "{cum}"')

print(f'\n===== KẾT QUẢ (gồm mục 8-9): PASS {PASS} / FAIL {FAIL} =====')
sys.exit(1 if FAIL else 0)
