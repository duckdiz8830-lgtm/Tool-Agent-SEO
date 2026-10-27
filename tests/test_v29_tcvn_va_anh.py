# -*- coding: utf-8 -*-
"""Ver 2.9 — test enrich TCVN 8525 + 3 vá module ảnh.

Chạy: python tests/test_v29_tcvn_va_anh.py  (từ thư mục v29)
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import enrich_tcvn_mba as E
import anh_san_pham as A

PASS = FAIL = 0


def kiem(dieu_kien, ten):
    global PASS, FAIL
    if dieu_kien:
        PASS += 1
        print(f'  PASS  {ten}')
    else:
        FAIL += 1
        print(f'  FAIL  {ten}')


print('== 1. TCVN 8525:2015 — tra bảng ==')
kiem(E.meps_tcvn(250, 3, 'dau', (22, 0.4)) == 99.10, 'dầu 250kVA -> 99.10')
kiem(E.meps_tcvn(320, 3, 'dau', (22, 0.4)) == 99.16, 'dầu 320kVA (alias 315/320) -> 99.16')
kiem(E.meps_tcvn(15, 3, 'dau', (22, 0.4)) == 98.40, 'dầu 15kVA (≤25) -> 98.40')
kiem(E.meps_tcvn(4000, 3, 'kho', (22, 0.4)) == 99.18, 'khô 4000kVA -> 99.18')
kiem(E.meps_tcvn(30, 3, 'kho', (22, 0.4)) == 97.50, 'khô 30kVA (≤50) -> 97.50')
# nội suy tuyến tính (chú thích Bảng 1): 300 nằm giữa 250(99.10) và 315(99.16)
noi_suy = E.meps_tcvn(300, 3, 'dau', (22, 0.4))
kiem(abs(noi_suy - 99.15) < 0.005, f'dầu 300kVA nội suy -> {noi_suy} (~99.15)')

print('== 2. TCVN — NGOÀI phạm vi thì trả None, không đoán ==')
kiem(E.meps_tcvn(50, 1, 'dau', (12.7, 0.23)) is None, 'máy 1 PHA -> None')
kiem(E.meps_tcvn(250, 3, None, (22, 0.4)) is None, 'không rõ dầu/khô -> None')
kiem(E.meps_tcvn(4500, 3, 'dau', (22, 0.4)) is None, '4500kVA (>4000) -> None')
kiem(E.meps_tcvn(4, 3, 'dau', (22, 0.4)) is None, '4kVA (<5) -> None')

print('== 3. Dòng định mức — công thức định nghĩa ==')
dd = E.dong_dinh_muc(250, (22, 0.4), 3)
kiem(dd == (6.6, 360.8), f'3 pha 250kVA 22/0.4 -> {dd} (6.6A / 360.8A)')
dd1 = E.dong_dinh_muc(50, (12.7, 0.23), 1)
kiem(dd1 == (3.9, 217.4), f'1 pha 50kVA 12.7/0.23 -> {dd1} (3.9A / 217.4A)')
kiem(E.dong_dinh_muc(250, None, 3) is None, 'thiếu điện áp -> None')

print('== 4. Parse điện áp — chặt, không đoán chiều đấu ==')
kiem(E.doc_cap_ap('22/0.4 kV', '') == (22, 0.4), "'22/0.4 kV' -> (22, 0.4)")
kiem(E.doc_cap_ap('12.7/0.23 kV', '') == (12.7, 0.23), "'12.7/0.23 kV' -> (12.7, 0.23)")
kiem(E.doc_cap_ap('220V', '') is None, "'220V' -> None")
kiem(E.doc_cap_ap('24 kV', '') is None, "'24 kV' (1 mức) -> None")
kiem(E.doc_cap_ap('230/400V', '') is None, "'230/400V' (không phải trung/hạ) -> None")

print('== 5. Parse loại máy từ tên hàng ==')
kiem(E.doc_loai('Máy biến áp dầu 3Pha 250KVA') == 'dau', 'biến áp dầu -> dau')
kiem(E.doc_loai('Báo Giá Máy biến áp Khô KP/Hàn Quốc 4000kVA') == 'kho', 'biến áp Khô -> kho')
kiem(E.doc_loai('Đầu cáp co nguội 24kV') is None, "'Đầu cáp' KHÔNG bị nhận là máy dầu")

print('== 6. Ảnh — dầu/khô là tiêu chí loại hẳn (vá sự cố batch 245) ==')
tt_dau = A.phan_tich_ten_file('mba dau thibidi 4000kva.jpg')
kiem(tt_dau['loai_may'] == 'dau', 'ảnh "mba dau thibidi 4000kva" -> loai_may=dau')
row_kho = {'ma_goc': 'KPK4000CU', 'ten_goc': 'Máy biến áp Khô KP 4000kVA',
           'cong_suat': '4000', 'thuong_hieu': 'KP', 'record_id': 1}
row_dau = {'ma_goc': 'TBD3P4000', 'ten_goc': 'Máy biến áp dầu 3Pha 4000KVA THIBIDI',
           'cong_suat': '4000', 'thuong_hieu': 'THIBIDI', 'record_id': 2}
r, ly = A.ghep_anh_voi_sku(tt_dau, [row_kho])
kiem(r is None, 'ảnh DẦU + chỉ có SKU KHÔ cùng 4000kVA -> KHÔNG ghép')
r2, _ = A.ghep_anh_voi_sku(tt_dau, [row_kho, row_dau])
kiem(r2 is row_dau, 'có cả 2 -> ghép đúng SKU DẦU')
tt_anh_kho = A.phan_tich_ten_file('may bien ap kho kp 4000kva.jpg')
r3, _ = A.ghep_anh_voi_sku(tt_anh_kho, [row_kho, row_dau])
kiem(r3 is row_kho, 'ảnh KHÔ -> ghép đúng SKU KHÔ')

print('== 7. Ảnh — tên file "đầu cáp" không dính bẫy dau ==')
tt_dc = A.phan_tich_ten_file('dau cap 3m 24kv.jpg')
kiem(tt_dc['loai_may'] is None, "'dau cap' (không có mba/bien ap) -> loai_may=None")

print('== 8. Ảnh — nhiều mức công suất trong tên -> cảnh báo + hạ tin cậy ==')
tt2 = A.phan_tich_ten_file('mba dau mbt 250kva 320kva.jpg')
kiem(tt2['canh_bao'] is not None, 'có canh_bao')
kiem(tt2['do_tin_cay'] == 'vua', "tin cậy hạ 'cao' -> 'vua'")
kiem(tt2['cong_suat'] == 250.0, 'vẫn lấy số đầu (hành vi cũ giữ nguyên)')

print('== 9. Ảnh — ghép mơ hồ không tự tick, không báo cao (quet_thu_muc) ==')
rows7 = [{'ma_goc': f'MBT3P250A260{i}', 'ten_goc': f'Máy biến áp dầu 3Pha 250KVA loại {i}',
          'cong_suat': '250', 'thuong_hieu': 'MBT', 'record_id': i} for i in range(7)]
with tempfile.TemporaryDirectory() as tmp:
    for f in ('mba dau mbt 250kva.jpg', 'mba dau mbt 999kva.jpg'):
        open(os.path.join(tmp, f), 'wb').write(b'x')
    kq = A.quet_thu_muc(tmp, rows7)
    d_mo_ho = next(d for d in kq['danh_sach'] if '250kva.jpg' in d['ten_file'])
    kiem(d_mo_ho['ma_goc'] != '', 'vẫn đề xuất 1 SKU (để người dùng đỡ tìm)')
    kiem(d_mo_ho['do_tin_cay'] == 'vua', "7 SKU đồng điểm -> 'vua', KHÔNG còn 'cao'")
    kiem(d_mo_ho['chon'] is False, 'KHÔNG tự tick chọn')
    kiem(d_mo_ho['anh_dai_dien'] is False, 'KHÔNG tự gắn sao đại diện')
    d_khong = next(d for d in kq['danh_sach'] if '999kva' in d['ten_file'])
    kiem(d_khong['ma_goc'] == '', 'không SKU nào khớp -> để trống như cũ')

print('== 10. Hồi quy — hành vi cũ không đổi khi ghép RÕ RÀNG ==')
tt_ro = A.phan_tich_ten_file('MBA_MBT_3P_560KVA (2).jpg')
row_560 = {'ma_goc': 'MBT3P560A2608', 'ten_goc': 'Máy biến áp dầu 3Pha 560KVA MBT',
           'cong_suat': '560', 'thuong_hieu': 'MBT', 'record_id': 9}
r560, ly560 = A.ghep_anh_voi_sku(tt_ro, [row_560] + rows7)
kiem(r560 is row_560 and 'cùng khớp' not in ly560, 'ghép duy nhất -> như 2.8')
with tempfile.TemporaryDirectory() as tmp:
    open(os.path.join(tmp, 'MBA_MBT_3P_560KVA (2).jpg'), 'wb').write(b'x')
    kq = A.quet_thu_muc(tmp, [row_560] + rows7)
    d = kq['danh_sach'][0]
    kiem(d['do_tin_cay'] == 'cao' and d['chon'] is True and d['anh_dai_dien'] is True,
         "ghép rõ ràng vẫn 'cao' + tự tick như 2.8")

print(f'\n===== KẾT QUẢ: PASS {PASS} / FAIL {FAIL} =====')
sys.exit(1 if FAIL else 0)
