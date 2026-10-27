# -*- coding: utf-8 -*-
"""Test Ver 2.8 — Dynamic Schema (quét cột động).

Chỉ test chỗ RỦI RO THẬT: lọc cột nội bộ, Hard Block không chặn nhầm,
không phá luồng cũ.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import profiles as P
import render_phase2 as R

so_pass = so_fail = 0


def kt(t, dk, gc=''):
    global so_pass, so_fail
    if dk:
        so_pass += 1
        print(f'[PASS] {t}')
    else:
        so_fail += 1
        print(f'[FAIL] {t} {gc}')


RAW = {
    'Mã hàng': 'X1', 'Tên hàng': 'MBA 100kVA',
    'Giá List (VNĐ)': 208300000,
    'Ghi Chú Kiểm Duyệt': 'cần xem lại',
    'Nghi Ngờ Phân Loại Sai': 'X',
    'Độ Tin Cậy Bổ Sung': 'Cao',
    'Trạng Thái Kiểm Duyệt': 'CAN_KIEM',
    'Nguồn catalogue': 'THIBIDI p.4',
    'Tổn hao không tải Po (W)': 340,
    'Độ ồn (dB)': 55,
    'Tổ đấu dây': 'Dyn11',
    'Ghi chú dài': 'x' * 300,
}
COT_IMPORT = {'Mã hàng': 'ma_goc', 'Tên hàng': 'ten_goc'}

row = P.normalize_row(RAW, COT_IMPORT)
dong = row.get('thong_so_dong') or {}

# ---------- A. Lọc cột nội bộ ----------
for cot in ('Giá List (VNĐ)', 'Ghi Chú Kiểm Duyệt', 'Nghi Ngờ Phân Loại Sai',
            'Độ Tin Cậy Bổ Sung', 'Trạng Thái Kiểm Duyệt', 'Nguồn catalogue'):
    kt(f'A [{cot[:30]}] bị CHẶN, không lọt vào bài', cot not in dong)

kt('A-dai: giá trị quá dài (>200 ký tự) bị bỏ', 'Ghi chú dài' not in dong)
kt('A-giu: cột kỹ thuật thật ĐƯỢC giữ',
   dong.get('Tổn hao không tải Po (W)') == '340'
   and dong.get('Tổ đấu dây') == 'Dyn11' and dong.get('Độ ồn (dB)') == '55',
   str(dong))
kt('A-khai: cột ĐÃ khai báo không bị lặp lại ở cột động',
   'Mã hàng' not in dong and 'Tên hàng' not in dong)

# ---------- B. Hard Block không chặn nhầm ----------
row_full = dict(row, profile_id='may_bien_ap_do_luong',
                outline_id='outline_may_bien_ap', thuong_hieu='MBT', dvt='Máy',
                cong_suat='100 kVA', cap_dien_ap='22/0.4 kV')
kho = R._kho_cua_dong(row_full)
kt('B1: số ở cột động vào được kho hợp lệ (đơn vị bóc từ TÊN CỘT)',
   '340w' in kho and '55db' in kho, str(sorted(kho)))
kt('B2: Hard Block KHÔNG chặn số thật từ cột động',
   not R.kiem_tra_bia('<p>Tổn hao không tải 340W.</p>', row_full))
kt('B3: Hard Block VẪN chặn số bịa',
   bool(R.kiem_tra_bia('<p>Tổn hao 999W.</p>', row_full)))

# ---------- C. Không phá luồng cũ ----------
row_cu = {'profile_id': 'may_bien_ap_do_luong', 'outline_id': 'outline_may_bien_ap',
          'ma_goc': 'Y1', 'ten_goc': 'MBA', 'thuong_hieu': 'MBT', 'dvt': 'Máy',
          'cong_suat': '250 kVA', 'cap_dien_ap': '22/0.4 kV'}
kt('C1: record KHÔNG có cột động vẫn chạy bình thường',
   bool(R.bang_thong_so(row_cu)) and 'thong_so_dong' not in row_cu)
bang = R.bang_thong_so(row_full)
kt('C2: bảng thông số có thêm dòng từ cột động',
   'Tổ đấu dây' in bang and 'Dyn11' in bang)
kt('C3: bảng vẫn giữ các dòng cũ', 'Công suất' in bang and '100 kVA' in bang)

print(f'\nTỔNG VER 2.8 (Dynamic Schema): {so_pass}/{so_pass + so_fail} PASS')
sys.exit(1 if so_fail else 0)
