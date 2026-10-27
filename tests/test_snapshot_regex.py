import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
# -*- coding: utf-8 -*-
"""
Unit test regex — dùng đúng snapshot 33 tên sản phẩm THẬT lấy từ Excel gốc,
liệt kê ở DATA-AUDIT-4-PROFILES.md mục 8 (A=9, B=8, C=6, D=10). Không tự
nghĩ case khác. Chạy: python3 test_snapshot_regex.py
"""
import validators as V

ket_qua = []


def kiem(mo_ta, dieu_kien):
    ket_qua.append((mo_ta, bool(dieu_kien)))


def rung(ten_goc, **extra):
    """Tạo 1 row giả tối thiểu để đưa qua validate_cap_dien/validate_may_bien_ap."""
    row = {'ten_goc': ten_goc, 'tiet_dien': '', 'cap_dien_ap': '',
           'vat_lieu_ruot': '', 'outline_id': 'outline_cap_dien'}
    row.update(extra)
    return row


# ============================================================ A. Điện áp "V" thường (9 tên)
A = [
    'Dây VCmo2x0.75mm2 (300/500V) - Cadivi',
    'Dây VCmo2x1mm2 (300/500V) - Cadivi',
    'Dây VCmo2x1.5mm2 (300/500V) - Cadivi',
    'Dây VCmo2x2.5mm2 (300/500V) - Cadivi',
    'Dây VC2.5mm2 (450/750V)-Cadivi',
    'Dây VC10mm2 (450/750V) -Cadivi',
    'Dây VC6mm2 (450/750V)-Cadivi',
    'Dây VC3mm2 (600V) - Cadivi',
    'Dây CV1.25mm2 (600V)-Cadivi',
]
KY_VONG_A = ['300/500V', '300/500V', '300/500V', '300/500V', '450/750V',
             '450/750V', '450/750V', '600V', '600V']
assert len(A) == 9, f'Snapshot A phải đúng 9 tên, đang có {len(A)}'
for ten, ky_vong in zip(A, KY_VONG_A):
    r = V.validate_cap_dien(rung(ten))
    kiem(f'A: "{ten[:45]}" -> điện áp = "{ky_vong}"', r['cap_dien_ap'] == ky_vong)

# ============================================================ B. Tiết diện đơn lõi (6 dương + 2 âm = 8 tên)
B_DUONG = [
    ('Dây VC2.5mm2 (450/750V)-Cadivi', '2.5'),
    ('Dây VC3mm2 (600V) - Cadivi', '3'),
    ('Dây VC10mm2 (450/750V) -Cadivi', '10'),
    ('Dây VC6mm2 (450/750V)-Cadivi', '6'),
    ('Dây CV1mm2 (0.6/1kV)-Cadivi', '1'),
    ('Dây CV1.25mm2 (600V)-Cadivi', '1.25'),
]
B_AM = [
    ('Dây VCmd2x0.5mm2 (0.6/1kV) - Cadivi', '2x0.5'),   # đã có sẵn từ nguồn, KHÔNG được đụng
    ('Dây CXV2X38mm2 - 600V - Cadivi', '2X38'),          # đã có sẵn từ nguồn, giữ chữ X hoa
]
assert len(B_DUONG) + len(B_AM) == 8, 'Snapshot B phải đúng 8 tên'
for ten, ky_vong in B_DUONG:
    r = V.validate_cap_dien(rung(ten))
    kiem(f'B(dương): "{ten[:40]}" -> tiết diện = "{ky_vong}"', r['tiet_dien'] == ky_vong)
for ten, gia_tri_co_san in B_AM:
    # case âm: field ĐÃ có giá trị sẵn (mô phỏng dữ liệu nguồn), validator
    # không được ghi đè vì chỉ bóc khi field đang RỖNG
    row = rung(ten)
    row['tiet_dien'] = gia_tri_co_san
    r = V.validate_cap_dien(row)
    kiem(f'B(âm, không regression): "{ten[:40]}" giữ nguyên "{gia_tri_co_san}"',
         r['tiet_dien'] == gia_tri_co_san)

# ============================================================ C. Cu-Al (6 tên)
C = [
    'Cosse ép Cu-Al  16mm2-N-TA dài 45mm chiều dài ép dây 21mm',
    'Cosse ép Cu-Al  16mm2-N-TA dài 52mm chiều dài ép dây 28mm',
    'Cosse ép Cu-Al  25mm2-N-TA dài 45mm chiều dài ép dây 21mm',
    'Cosse ép Cu-Al  35mm2-N-TA dài 51mm chiều dài ép dây 23mm',
    'Cosse ép Cu-Al  50mm2-N-TA dài 51mm chiều dài ép dây 23mm',
    'Cosse ép Cu-Al  70mm2-N-TA dài 58mm chiều dài ép dây 24mm',
]
assert len(C) == 6, 'Snapshot C phải đúng 6 tên'
for ten in C:
    row = rung(ten, vat_lieu_ruot='Đồng (Cu)')  # mô phỏng bug gốc: bị gán sai
    r = V.validate_cap_dien(row)
    kiem(f'C: "{ten[:40]}" -> vat_lieu_ruot bị xoá (không còn "Đồng (Cu)")',
         r['vat_lieu_ruot'] == '')

# ============================================================ D. Máy biến áp kVA/kV (6 dương + 2+2 âm = 10 tên)
D_DUONG = [
    ('Máy biến áp dầu 1Pha 15KVA 12.7/0.23KV Loại Silic - TBD', '15', '15', '12.7/0.23'),
    ('Máy biến áp dầu 1Pha 25KVA 12.7/0.23KV Loại Silic - TBD', '25', '25', '12.7/0.23'),
    ('Máy biến áp dầu 1Pha 37.5KVA 12.7/0.23KV Loại Silic - TBD', '37.5', '37.5', '12.7/0.23'),
    ('Máy biến áp dầu 1Pha 50KVA 12.7/0.23KV Loại Silic - TBD', '50', '50', '12.7/0.23'),
    ('Máy biến áp dầu 3Pha 50KVA 22/0.4KV Loại Silic - TBD', '50', '50', '22/0.4'),
    ('Máy biến áp dầu 3Pha 75KVA 22/0.4KV Loại Silic - TBD', '75', '75', '22/0.4'),
]
D_AM_DO_LUONG = [
    'Hợp bộ đo lường (MOF) 24kV\nTỷ số biến dòng: 10-20/5A.\nTỷ số biến áp: 22:\u221a3/0.11:\u221a3 (kV)\nDung lượng: 25 (VA), CC0.5 -Young-hwa/  Hàn Quốc',
    'Hợp bộ đo lường (MOF) 24kV\nTỷ số biến dòng:15-30/5A.\nTỷ số biến áp: 22:\u221a3/0.11:\u221a3 (kV)\nDung lượng: 25 (VA), CC0.5 -Young-hwa/  Hàn Quốc',
]
D_AM_GIA_TREO = ['Giá treo MBT 1x25', 'Giá treo MBT 3x100']
assert len(D_DUONG) + len(D_AM_DO_LUONG) + len(D_AM_GIA_TREO) == 10, 'Snapshot D phải đúng 10 tên'

for ten, kva, kv_bug_ban_dau, ky_vong_sau_sua in D_DUONG:
    row = {'ten_goc': ten, 'cong_suat': f'{kva} kVA', 'cap_dien_ap': f'{kv_bug_ban_dau} kV',
           'outline_id': 'outline_may_bien_ap', 'profile_id': 'may_bien_ap_do_luong'}
    r = V.validate_may_bien_ap(row)
    kiem(f'D(dương): "{ten[:40]}" -> điện áp sửa = "{ky_vong_sau_sua}"',
         r['cap_dien_ap'] == ky_vong_sau_sua)
    kiem(f'D(dương): "{ten[:40]}" -> có gắn canh_bao_dien_ap', r.get('canh_bao_dien_ap') is True)

for ten in D_AM_DO_LUONG:
    # case âm: nhóm đo lường, KHÔNG được coi là bug (outline_id không phải
    # outline_may_bien_ap nên validator bỏ qua nguyên vẹn)
    row = {'ten_goc': ten, 'cong_suat': '', 'cap_dien_ap': '24 kV', 'outline_id': 'outline_do_luong',
           'profile_id': 'may_bien_ap_do_luong'}
    r = V.validate_may_bien_ap(row)
    kiem(f'D(âm, nhóm đo lường): "{ten[:40]}" không bị đụng bug-fix (chỉ strip đơn vị R2-07)',
         r['cap_dien_ap'] == '24' and not r.get('canh_bao_dien_ap'))

for ten in D_AM_GIA_TREO:
    # case âm: giá treo, đã bị route sang outline_phu_kien ở bước routing
    # (profiles.py), validator không áp cho outline này
    row = {'ten_goc': ten, 'cong_suat': '', 'cap_dien_ap': '', 'outline_id': 'outline_phu_kien',
           'profile_id': 'may_bien_ap_do_luong'}
    r = V.validate_may_bien_ap(row)
    kiem(f'D(âm, giá treo): "{ten}" không bị đụng vào (2 field vẫn rỗng, không suy đoán)',
         r['cap_dien_ap'] == '' and not r.get('canh_bao_dien_ap'))


# ============================================================ tổng kết
if __name__ == '__main__':
    tong_a = 9
    tong_b = 6 + 2
    tong_c = 6
    tong_d = 6 + 2 + 2
    print(f'Snapshot: A={tong_a} B={tong_b} C={tong_c} D={tong_d} | Tổng = {tong_a+tong_b+tong_c+tong_d} (kỳ vọng 33)')
    print()
    so_pass = sum(1 for _, ok in ket_qua if ok)
    for mo_ta, ok in ket_qua:
        print(('PASS' if ok else 'FAIL'), '-', mo_ta)
    print()
    print(f'KẾT QUẢ: {so_pass}/{len(ket_qua)} PASS')
    if so_pass != len(ket_qua):
        raise SystemExit(1)
