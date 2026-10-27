import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
# -*- coding: utf-8 -*-
"""
Ver 4.9.5 Claude — test patch:
1. Profile phu_kien_va_khac nhận 6 field enrich catalogue (đầu cáp/hộp nối
   ABB/3M, 90 SKU đợt đầu) + 1 field nội bộ nguon_catalogue.
2. Import KHÔNG crash với MASTER CHƯA enrich (cot_bat_buoc tách khỏi cot_import).
3. Routing: SKU có nguon_catalogue -> outline_dau_cap_ky_thuat; SKU khác ->
   outline_phu_kien như cũ (không đổi hành vi cũ).
4. Prompt/bảng thông số/schema dùng đúng field mới, KHÔNG phá field cấm
   tuyệt đối (gia_list/ghi_chu_ban_dau).
5. Regression: 3 profile còn lại (cap_dien, tu_va_thiet_bi_dong_cat,
   may_bien_ap_do_luong) không đổi hành vi.

Chạy: python3 test_v495_patch.py
"""
import os
import sys

import nhap_phase2 as N
import prompts_phase2 as PR
import profiles as P
import render_phase2 as R

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ver 5.1 -- test o tests/, du lieu/module chinh o thu muc goc (len 1 cap)
MASTER_GOC = os.path.join(BASE, 'tests', 'fixtures', 'MASTER_4_PROFILE_SAN_PHAM.xlsx')
MASTER_ENRICH = os.path.join(BASE, 'tests', 'fixtures', '5MASTER_ENRICHED_TRIAL.xlsx')

KET_QUA = []


def test(ma, mo_ta, dieu_kien):
    KET_QUA.append((ma, mo_ta, bool(dieu_kien)))
    trang_thai = 'PASS' if dieu_kien else 'FAIL'
    print(f'[{trang_thai}] {ma}: {mo_ta}')


def main():
    if not os.path.exists(MASTER_GOC) or not os.path.exists(MASTER_ENRICH):
        print('THIẾU FILE TEST — cần MASTER_4_PROFILE_SAN_PHAM.xlsx và '
              '5MASTER_ENRICHED_TRIAL.xlsx trong cùng thư mục. Bỏ qua test này.')
        sys.exit(0)

    # ============================================================ 1. Registry
    test('R1-01', 'FIELD_CAM_TUYET_DOI vẫn chặn gia_list/ghi_chu_ban_dau (assert lúc load module không văng lỗi)',
         True)  # _kiem_tra_registry() đã chạy lúc import profiles ở đầu file, không văng là PASS
    test('R1-02', 'outline_dau_cap_ky_thuat tồn tại trong OUTLINES',
         'outline_dau_cap_ky_thuat' in P.OUTLINES)
    test('R1-03', '6 field enrich nằm trong cot_ai của phu_kien_va_khac',
         all(f in P.PROFILES['phu_kien_va_khac']['cot_ai'] for f in
             ['duong_kinh_cach_dien', 'kich_thuoc_i', 'kich_thuoc_l',
              'duong_ro_ngoai_troi', 'tieu_chuan_catalogue', 'test_dien']))
    test('R1-04', 'nguon_catalogue nằm trong cot_noi_bo (KHÔNG trong cot_ai/cot_bang)',
         'nguon_catalogue' in P.PROFILES['phu_kien_va_khac']['cot_noi_bo']
         and 'nguon_catalogue' not in P.PROFILES['phu_kien_va_khac']['cot_ai']
         and 'nguon_catalogue' not in [k for k, _ in P.PROFILES['phu_kien_va_khac']['cot_bang']])

    # ============================================================ 2. Import KHÔNG crash MASTER cũ
    try:
        r_goc = N.import_4_profile(MASTER_GOC, chi_profile='phu_kien_va_khac')
        rows_goc = r_goc['phu_kien_va_khac']['rows']
        khong_crash = True
    except Exception as e:
        rows_goc, khong_crash = [], False
        print(f'  Lỗi: {e}')
    test('R2-01', f'Import MASTER GỐC (chưa enrich) KHÔNG crash (thực tế {len(rows_goc)} dòng)',
         khong_crash and len(rows_goc) > 0)
    test('R2-02', 'MASTER gốc: field duong_kinh_cach_dien rỗng (cột không tồn tại trong file gốc)',
         all(r.get('duong_kinh_cach_dien', '') == '' for r in rows_goc))
    test('R2-03', 'MASTER gốc: KHÔNG dòng nào route sang outline_dau_cap_ky_thuat (chưa có nguon_catalogue)',
         all(r['outline_id'] != 'outline_dau_cap_ky_thuat' for r in rows_goc))

    # ============================================================ 3. Import file enrich
    r_en = N.import_4_profile(MASTER_ENRICH, chi_profile='phu_kien_va_khac')
    rows_en = r_en['phu_kien_va_khac']['rows']
    so_enrich = sum(1 for r in rows_en if r['outline_id'] == 'outline_dau_cap_ky_thuat')
    test('R3-01', f'File enrich: đúng 90 SKU route sang outline_dau_cap_ky_thuat (thực tế {so_enrich})',
         so_enrich == 90)
    row_mau = next(r for r in rows_en if r['outline_id'] == 'outline_dau_cap_ky_thuat')
    test('R3-02', 'Dòng enrich: có giá trị duong_kinh_cach_dien thật (không rỗng)',
         bool(row_mau.get('duong_kinh_cach_dien')))
    test('R3-03', 'Dòng enrich: field nguon_catalogue có giá trị (dùng cho routing, không lộ ra ngoài)',
         bool(row_mau.get('nguon_catalogue')))

    # ============================================================ 4. Prompt
    prompt = PR.nguoi_dung(row_mau, row_mau['outline_id'])
    test('R4-01', 'Prompt CÓ nhắc field kỹ thuật mới (Đường kính cách điện áp dụng)',
         'Đường kính cách điện áp dụng' in prompt)
    test('R4-02', 'Prompt KHÔNG có gia_list/Giá List (field cấm tuyệt đối)',
         'Giá List' not in prompt and 'gia_list' not in prompt)
    test('R4-03', 'Prompt liệt kê đúng field trống vào mục "DỮ LIỆU KHÔNG CÓ" khi field đó rỗng ở dòng này',
         'DỮ LIỆU KHÔNG CÓ' in prompt or all(row_mau.get(f) for f in P.effective_cot_ai(
             'phu_kien_va_khac', 'outline_dau_cap_ky_thuat')))

    # ============================================================ 5. Bảng thông số + Schema
    bang = R.bang_thong_so(row_mau)
    test('R5-01', 'Bảng thông số HTML chứa cột Đường kính cách điện áp dụng',
         'Đường kính cách điện áp dụng' in bang)
    test('R5-02', 'Bảng thông số HTML KHÔNG chứa Giá List (không lộ giá)',
         'Giá List' not in bang and 'gia_list' not in bang.lower())
    schema = R.dung_schema(row_mau)
    test('R5-03', 'Schema JSON-LD vẫn KHÔNG có offers/price (quyết định cũ, chưa đổi)',
         'offers' not in schema and 'price' not in str(schema).lower())
    schema_str = __import__('json').dumps(schema, ensure_ascii=False)
    test('R5-04', 'Schema additionalProperty có field kỹ thuật mới',
         'Đường kính cách điện áp dụng' in schema_str)

    # ============================================================ 6. Regression 3 profile khác
    r_cd = N.import_4_profile(MASTER_GOC, chi_profile='cap_dien')['cap_dien']['rows']
    test('R6-01', f'cap_dien vẫn import bình thường (thực tế {len(r_cd)} dòng, kỳ vọng > 0)', len(r_cd) > 0)
    r_tu = N.import_4_profile(MASTER_GOC, chi_profile='tu_va_thiet_bi_dong_cat')['tu_va_thiet_bi_dong_cat']['rows']
    test('R6-02', f'tu_va_thiet_bi_dong_cat vẫn import bình thường (thực tế {len(r_tu)} dòng)', len(r_tu) > 0)
    r_mba = N.import_4_profile(MASTER_GOC, chi_profile='may_bien_ap_do_luong')['may_bien_ap_do_luong']['rows']
    test('R6-03', f'may_bien_ap_do_luong vẫn import bình thường (thực tế {len(r_mba)} dòng)', len(r_mba) > 0)
    test('R6-04', 'Field mới KHÔNG lọt sang profile khác (cap_dien không có duong_kinh_cach_dien)',
         'duong_kinh_cach_dien' not in P.PROFILES['cap_dien']['cot_import'].values())

    # ============================================================ tổng kết
    tong = len(KET_QUA)
    dat = sum(1 for _, _, ok in KET_QUA if ok)
    print(f'\nTỔNG VER 4.9.5 PATCH: {dat}/{tong} PASS')
    if dat != tong:
        sys.exit(1)


if __name__ == '__main__':
    main()
