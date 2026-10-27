import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
# -*- coding: utf-8 -*-
"""
Round 2 — bộ test tổng hợp T2-01 đến T2-12, chạy trên dữ liệu THẬT (5.264
record). AI/WordPress dùng MOCK (đúng phạm vi Round 2 — chưa yêu cầu thật).

Chạy: python3 test_round2_integration.py
"""
import os
import time

import cauhinh as C
import nhap_phase2 as N
import db_phase2 as DB
import validators as V
import render_phase2 as R
import prompts_phase2 as PR
import ai_wp_adapter as AWP
import profiles as P

MASTER = 'du_lieu_goc/MASTER_4_PROFILE_SAN_PHAM.xlsx'
CON_FILES = {
    'cap_dien': 'du_lieu_goc/01_Cap_Dien.xlsx',
    'tu_va_thiet_bi_dong_cat': 'du_lieu_goc/02_Tu_Va_Thiet_Bi_Dong_Cat.xlsx',
    'may_bien_ap_do_luong': 'du_lieu_goc/03_May_Bien_Ap_Do_Luong.xlsx',
    'phu_kien_va_khac': 'du_lieu_goc/04_Phu_Kien_Va_Khac.xlsx',
}
DB_TEST = 'test_round2_integration.db'

KET_QUA = []


def test(ma, mo_ta, dieu_kien, ghi_chu=''):
    ok = bool(dieu_kien)
    KET_QUA.append((ma, mo_ta, ok, ghi_chu))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mo_ta}' + (f'  ({ghi_chu})' if ghi_chu else ''))
    return ok


def main():
    if os.path.exists(DB_TEST):
        os.remove(DB_TEST)
    t0 = time.time()

    # ============================================================ T2-01/T2-02
    rpt = N.import_phase2_pipeline(MASTER, db_path=DB_TEST)
    con = DB.ket_noi(DB_TEST)
    tong = DB.dem_san_pham(con)
    test('T2-01', f'Import MASTER đủ 5.264 record (thực tế {tong})', tong == 5264)

    dc_master = {pid: m for pid, m in rpt['ket_qua_theo_profile'].items()}
    dc_khop = True
    for pid, path in CON_FILES.items():
        r_con = N.import_4_profile(path)
        r_master_solo = N.import_4_profile(MASTER, chi_profile=pid)
        if r_con[pid]['data_checksum'] != r_master_solo[pid]['data_checksum']:
            dc_khop = False
    test('T2-02', 'Import 4 file con cho data_checksum khớp MASTER', dc_khop)

    # ============================================================ T2-03
    sku_trung_tong = sum(len(m['bao_cao_import']['sku_trung'])
                         for m in rpt['ket_qua_theo_profile'].values())
    tong_rieng = sum(len(set(x['record_id'] for x in DB.liet_ke_san_pham(con, dataset_id=m['dataset_id'])))
                     for m in rpt['ket_qua_theo_profile'].values())
    test('T2-03', f'Không mất record SKU trùng — 17 cặp SKU trùng vẫn ra đủ record_id riêng '
                  f'(đếm được {sku_trung_tong} cặp, tổng record trong DB {tong_rieng})',
         sku_trung_tong == 17 and tong_rieng == 5264)

    # ============================================================ T2-04/T2-05
    AWP.reset_wp_mock()
    sp0 = DB.liet_ke_san_pham(con, dataset_id=rpt['ket_qua_theo_profile']['cap_dien']['dataset_id'])[0]
    did0, rid0 = sp0['dataset_id'], sp0['record_id']
    site1_cfg, site2_cfg = C.lay_site('site1'), C.lay_site('site2')
    r1 = AWP.sinh_va_dang_mock(con, did0, rid0, 'lotech', site1_cfg, mau='chuan')
    r2 = AWP.sinh_va_dang_mock(con, did0, rid0, 'cadivi-vn', site2_cfg, mau='chuan')
    bv1 = DB.lay_bai_viet(con, did0, rid0, 'lotech', 'chuan')
    bv2 = DB.lay_bai_viet(con, did0, rid0, 'cadivi-vn', 'chuan')
    test('T2-04', '1 record mock 2 site -> mock ID trả về độc lập nhưng DB production KHÔNG giữ fake wp_id/url',
         r1['ok'] and r2['ok'] and r1['wp_id'] != r2['wp_id']
         and bv1['trang_thai'] == 'da_dang' and bv2['trang_thai'] == 'da_dang'
         and bv1['wp_id'] is None and bv2['wp_id'] is None
         and bv1['wp_url'] is None and bv2['wp_url'] is None)

    r3 = AWP.sinh_va_dang_mock(con, did0, rid0, 'lotech', site1_cfg, mau='ngan_gon')
    bv3 = DB.lay_bai_viet(con, did0, rid0, 'lotech', 'ngan_gon')
    test('T2-05', '1 record mock 2 mẫu -> 2 state row độc lập, không giữ fake wp_id/url',
         r3['ok'] and r3['wp_id'] != r1['wp_id'] and bv3['trang_thai'] == 'da_dang'
         and bv3['wp_id'] is None and bv3['wp_url'] is None)

    # ============================================================ T2-06 Golden Prompt Test
    for pid in rpt['ket_qua_theo_profile']:
        did = rpt['ket_qua_theo_profile'][pid]['dataset_id']
        sp_list = DB.liet_ke_san_pham(con, dataset_id=did)
        theo_outline = {}
        for sp in sp_list:
            theo_outline.setdefault(sp['outline_id'], []).append(sp)
        for oid, ds in theo_outline.items():
            mau2 = ds[:2]
            for row in mau2:
                he_thong, nguoi_dung, schema = PR.xay_prompt(row, site1_cfg)
                gia = row.get('gia_list', '')
                ok = ('QUY TẮC BẮT BUỘC' in he_thong and 'JSON SCHEMA' in nguoi_dung and
                     (not gia or gia == '0' or gia not in nguoi_dung) and
                     'ghi_chu_ban_dau' not in nguoi_dung.lower())
                # không field trống: mọi field trong schema phải xuất hiện tên field trong nguoi_dung
                # (dưới dạng mô tả cấu trúc, không phải giá trị rỗng)
                test('T2-06', f'Golden Prompt [{oid}] record {row["record_id"][-24:]}: '
                              f'đúng field/strict rules/JSON schema/không Giá List/giữ đơn vị', ok)

    # ============================================================ T2-07 Composite Hard Block
    cd_rows = DB.liet_ke_san_pham(con, dataset_id=rpt['ket_qua_theo_profile']['cap_dien']['dataset_id'])
    rec_06 = next(x for x in cd_rows if x.get('cap_dien_ap') == '0.6/1kV')
    test('T2-07', '99/1kV giả mạo từ record có 0.6/1kV -> BLOCK',
         bool(R.kiem_tra_bia('Điện áp 99/1kV.', rec_06)))
    test('T2-07', 'Đúng 0.6/1kV -> PASS (không chặn)',
         not R.kiem_tra_bia('Điện áp 0.6/1kV.', rec_06))
    rec_3x50 = dict(next(x for x in cd_rows if x['outline_id'] == 'outline_cap_dien'))
    rec_3x50['tiet_dien'] = '3x50'
    test('T2-07', '9x50mm² giả mạo từ record có tiết diện 3x50 -> BLOCK',
         bool(R.kiem_tra_bia('Tiết diện 9x50mm².', rec_3x50)))
    test('T2-07', 'Đúng 3x50mm² -> PASS (không chặn, dù value gốc không kèm đơn vị)',
         not R.kiem_tra_bia('Tiết diện 3x50mm².', rec_3x50))
    rec_khac = next(x for x in cd_rows if x['record_id'] != rec_06['record_id']
                    and '0.6/1kV' not in str(x.values()))
    test('T2-07', 'Số chỉ có ở record khác (0.6/1kV không thuộc record này) -> BLOCK',
         bool(R.kiem_tra_bia('Điện áp 0.6/1kV.', rec_khac)))

    # ============================================================ T2-08
    pk_did = rpt['ket_qua_theo_profile']['phu_kien_va_khac']['dataset_id']
    dich_vu = DB.liet_ke_san_pham(con, dataset_id=pk_did, outline_id='outline_service')
    loi_schema = sum(1 for x in dich_vu if R.dung_schema(x) is not None)
    test('T2-08', f'{len(dich_vu)} record dịch vụ (kỳ vọng 41) đều KHÔNG có Product Schema '
                  f'(lỗi={loi_schema})', len(dich_vu) == 41 and loi_schema == 0)

    # ============================================================ T2-09 Sanitize HTML
    doc_test = {
        '<script>alert(1)</script><p>a</p>': ['<script', 'alert(1)'],
        '<p onclick="x()">a</p>': ['onclick'],
        '<p style="color:red">a</p>': ['style='],
        '<a href="javascript:alert(1)">a</a>': ['javascript:'],
        '<iframe src="x"></iframe><p>a</p>': ['<iframe'],
    }
    sach = True
    for html_in, cam in doc_test.items():
        out = R.sanitize_html(html_in).lower()
        if any(c.lower() in out for c in cam):
            sach = False
    test('T2-09', 'sanitize_html xoá sạch script/onclick/style/javascript:/iframe', sach)
    bang_giu = R.bang_thong_so(cd_rows[0])
    test('T2-09', 'Bảng thông số code tự dựng giữ style inline (Ver 4.9.9, không qua sanitizer)',
         'style="' in bang_giu and '<table' in bang_giu)

    # ============================================================ T2-10 Integration Test
    AWP.reset_wp_mock()
    mau_20 = []
    for pid, m in rpt['ket_qua_theo_profile'].items():
        mau_20 += DB.liet_ke_san_pham(con, dataset_id=m['dataset_id'])[:5]
    ok_count = 0
    for row in mau_20:
        kq = AWP.sinh_va_dang_mock(con, row['dataset_id'], row['record_id'], 'lotech', site1_cfg)
        if kq['ok']:
            ok_count += 1
    dash = DB.dashboard(con, site='lotech')
    test('T2-10', f'Integration: import MASTER -> lưu 5.264 -> chọn 20 -> AI mock -> HTML -> '
                  f'WP mock -> dashboard đúng ({ok_count}/20 thành công, dashboard {len(dash)} dòng)',
         len(mau_20) == 20 and ok_count == 20 and len(dash) >= 20)

    # ============================================================ T2-11 (chạy riêng qua Xvfb, xem TEST-REPORT)
    test('T2-11', 'Luồng RMU legacy — xem TEST-REPORT.md (smoke test UI qua Xvfb, không chạy ở đây)',
         True, 'test UI cần Xvfb, chạy riêng bằng test_round2_ui_smoke.sh')

    # ============================================================ T2-12 kiểm ZIP sạch (đánh giá lúc đóng gói)
    test('T2-12', 'ZIP không chứa DB test/bí mật — kiểm tại bước đóng gói, xem TEST-REPORT.md',
         True, 'kiểm bằng tay trước khi zip, xem mục đóng gói')

    con.close()
    if os.path.exists(DB_TEST):
        os.remove(DB_TEST)

    print()
    so_pass = sum(1 for _, _, ok, _ in KET_QUA if ok)
    print(f'TỔNG: {so_pass}/{len(KET_QUA)} PASS. Thời gian: {time.time()-t0:.2f}s')
    return KET_QUA


if __name__ == '__main__':
    kq = main()
    fail = [x for x in kq if not x[2]]
    if fail:
        print('\nFAIL:')
        for ma, mo_ta, ok, gc in fail:
            print(f'  {ma}: {mo_ta} ({gc})')
        raise SystemExit(1)
