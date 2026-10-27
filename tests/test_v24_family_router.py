# -*- coding: utf-8 -*-
"""Test Ver 2.4 — Family Router: nhận diện họ sản phẩm, kiểm tra chéo.

Bao gồm 3 bug THẬT đã vấp khi viết module này (quét 5.264 SKU thật):
  - chữ 'đ' không bị NFD tách -> 'Đầu cáp' trượt regex
  - "Nắp chụp sứ MBA" bị nhận là máy biến áp (chỉ vì có chữ MBA)
  - "Thí nghiệm máy biến áp" bị nhận là máy biến áp (thực ra là dịch vụ)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import family_router as FR

so_pass = so_fail = 0


def kt(t, dk, gc=''):
    global so_pass, so_fail
    if dk:
        so_pass += 1
        print(f'[PASS] {t}')
    else:
        so_fail += 1
        print(f'[FAIL] {t} {gc}')


# ---------- A. Bug chữ 'đ' (NFD không tách được) ----------
kt("A1: _bo_dau xử lý đúng chữ 'đ' (bug thật đã vấp)",
   FR._bo_dau('Đầu cáp') == 'dau cap', FR._bo_dau('Đầu cáp'))
h, tt = FR.nhan_dien_ho('Đầu cáp 24KV 1 pha co nhiệt, trong nhà, 120mm2 - 3M')
kt('A2: "Đầu cáp..." nhận đúng họ đầu cáp (KHÔNG nhầm sang cáp điện)',
   h == 'dau_cap', f'thực tế {h}')

# ---------- B. Chặn nhầm: phụ trợ & dịch vụ ----------
h2, _ = FR.nhan_dien_ho('Nắp chụp sứ MBA,Re, LBS , ĐK 180')
kt('B1: "Nắp chụp sứ MBA" -> phụ trợ, KHÔNG phải máy biến áp', h2 == 'phu_tro', h2)
h3, _ = FR.nhan_dien_ho('Thí nghiệm máy biến áp 250kVA')
kt('B2: "Thí nghiệm máy biến áp" -> dịch vụ, KHÔNG phải máy biến áp',
   h3 == 'dich_vu', h3)
h4, _ = FR.nhan_dien_ho('Giá treo MBT 1 pha')
kt('B3: "Giá treo MBT" -> phụ trợ', h4 == 'phu_tro', h4)

# ---------- C. Nhận diện đúng các họ chính ----------
for ten, mong in (
        ('Máy biến áp dầu 3Pha 100KVA 22/0.4KV Loại Amorphous', 'may_bien_ap'),
        ('Dây CXV/DSTA3x70mm2 (0.6/1kV) - Cadivi', 'cap_dien'),
        ('Tủ RMU 24kV 630A', 'tu_dong_cat'),
        ('Dao cắt có tải LBS 24kV 630A', 'tu_dong_cat'),
        ('Chống sét van 12KV- ABB', 'su_cach_dien'),
        ('Vỏ mạ kẽm nhúng nóng MBA 3P 1500KVA', 'vo_may_bien_ap'),
):
    h5, _ = FR.nhan_dien_ho(ten)
    kt(f'C [{ten[:34]}] -> {mong}', h5 == mong, f'thực tế {h5}')

kt('C-none: tên lạ không nhận diện được -> None (KHÔNG đoán bừa)',
   FR.nhan_dien_ho('Sản phẩm XYZ 123')[0] is None)

# ---------- D. Kiểm tra chéo ----------
k1 = FR.kiem_tra_cheo('Đầu cáp 24KV 120mm2 - 3M', 'outline_may_bien_ap')
kt('D1: đầu cáp gán outline máy biến áp -> BẮT được, mức nghiêm trọng',
   not k1['khop'] and k1['muc_do'] == 'nghiem_trong')
kt('D2: có đề xuất outline thay thế', k1['outline_de_xuat'] == 'outline_dau_cap_ky_thuat',
   k1['outline_de_xuat'])
k2 = FR.kiem_tra_cheo('Máy biến áp dầu 3Pha 100KVA', 'outline_may_bien_ap')
kt('D3: đúng họ đúng outline -> khớp', k2['khop'])
k3 = FR.kiem_tra_cheo('Sản phẩm XYZ 123', 'outline_phu_kien')
kt('D4: không nhận diện được -> coi là khớp (không kết luận bừa)', k3['khop'])

# ---------- E. Quét cả dataset ----------
rows = [
    {'ma_goc': 'A', 'ten_goc': 'Đầu cáp 24KV 120mm2', 'outline_id': 'outline_may_bien_ap'},
    {'ma_goc': 'B', 'ten_goc': 'Máy biến áp dầu 100kVA', 'outline_id': 'outline_may_bien_ap'},
    {'ma_goc': 'C', 'ten_goc': 'Thí nghiệm FCO U<35kV', 'outline_id': 'outline_tu_dong_cat'},
]
lech = FR.quet_ca_dataset(rows)
kt('E1: quét dataset bắt đúng 2 ca lệch (A và C), bỏ qua B đúng',
   len(lech) == 2 and {l['ma_goc'] for l in lech} == {'A', 'C'},
   str([l['ma_goc'] for l in lech]))

print(f'\nTỔNG VER 2.4 (Family Router): {so_pass}/{so_pass + so_fail} PASS')
sys.exit(1 if so_fail else 0)
