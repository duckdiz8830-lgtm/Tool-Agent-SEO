import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
# -*- coding: utf-8 -*-
"""
Content Safety Gate 2 — bộ test theo đúng mục D của work order:
1. Product E2E (Schema JSON-LD)
2. Service E2E (không Schema)
3. Hard Block chặn khi record KHÔNG có (bảo hành/IP/IEC/nhiệt độ/%)
4. Hard Block cho phép khi record THỰC SỰ có
5. Regression composite cũ (0.6/1kV, 300/500V, 3x50mm², 3x50+1x25mm²)
6. Hai mẫu (HTML khác, slug khác, chạy lại không tạo bài mới)
7. Xác nhận KHÔNG gọi WordPress thật (chỉ audit code, không network thật)

Chạy: python3 test_gate2.py
"""
import json
import os

import cauhinh as C
import nhap_phase2 as N
import db_phase2 as DB
import validators as V
import render_phase2 as R
import prompts_phase2 as PR
import ai_wp_adapter as AWP

MASTER = 'du_lieu_goc/MASTER_4_PROFILE_SAN_PHAM.xlsx'
DB_TEST = 'test_gate2_official.db'

KET_QUA = []


def test(ma, mo_ta, dieu_kien, ghi_chu=''):
    ok = bool(dieu_kien)
    KET_QUA.append((ma, mo_ta, ok, ghi_chu))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mo_ta}' + (f'  ({ghi_chu})' if ghi_chu else ''))
    return ok


def main():
    if os.path.exists(DB_TEST):
        os.remove(DB_TEST)

    rpt = N.import_phase2_pipeline(MASTER, db_path=DB_TEST)
    con = DB.ket_noi(DB_TEST)
    site_cfg = C.lay_site('site1')

    cd_did = rpt['ket_qua_theo_profile']['cap_dien']['dataset_id']
    pk_did = rpt['ket_qua_theo_profile']['phu_kien_va_khac']['dataset_id']
    cd_rows = DB.liet_ke_san_pham(con, dataset_id=cd_did)
    pk_rows = DB.liet_ke_san_pham(con, dataset_id=pk_did)

    # ============================================================ 1. Product E2E
    # Ver 4.9.6 — ĐỔI Ý NGHĨA TEST: trước đây schema JSON-LD được nhét
    # thẳng vào bai_sp['html'] dạng <script>. Đã xác nhận BẰNG ẢNH CHỤP
    # PRODUCTION THẬT (Thịnh gửi 29/07/2026) rằng cách này KHÔNG sống sót
    # qua WooCommerce REST API — WordPress kses xoá cặp thẻ <script>,
    # ĐỂ LẠI JSON THÔ HIỆN RA THÀNH CHỮ TRÊN TRANG (bug thật, xem
    # CHANGELOG-VER495.md mục vá). Từ Ver 4.9.6, dung_bai_html() KHÔNG còn
    # nhét schema vào html — trả riêng qua key 'schema' (dict). Test đổi
    # theo đúng hành vi mới, không kiểm tra 'html' cho schema nữa.
    row_sp = next(x for x in cd_rows if x['outline_id'] == 'outline_cap_dien' and x.get('vat_lieu_ruot'))
    ai_data = {'meta_title': 'T', 'meta_description': 'M', 'intro_html': '<p>i</p>'}
    bai_sp = R.dung_bai_html(row_sp, ai_data, site_cfg)
    test('D1', 'Product E2E: HTML KHÔNG chứa JSON-LD thô (đã xác nhận bug thật nếu còn)',
         'application/ld+json' not in bai_sp['html'] and '@context' not in bai_sp['html'])
    parsed = bai_sp.get('schema') or {}
    test('D1', 'Product E2E: schema (dict riêng) parse/tồn tại được', bool(parsed))
    test('D1', f'Product E2E: @type là Product (thực tế {parsed.get("@type")})',
         parsed.get('@type') == 'Product')
    schema_str = json.dumps(parsed).lower()
    test('D1', 'Product E2E: không có Offer hoặc giá (offers/price/pricecurrency/gia_list)',
         not any(k in schema_str for k in ['offer', 'price', 'gia_list']))

    # ============================================================ 2. Service E2E
    row_dv = next(x for x in pk_rows if x['outline_id'] == 'outline_service')
    bai_dv = R.dung_bai_html(row_dv, ai_data, site_cfg)
    test('D2', 'Service E2E: HTML KHÔNG có Product JSON-LD',
         'application/ld+json' not in bai_dv['html'])

    # ============================================================ 3+4. Hard Block mở rộng
    row_hb = next(x for x in cd_rows if x.get('cap_dien_ap'))
    cases = [
        ('Bảo hành 24 tháng', 'Sản phẩm được bảo hành 24 tháng chính hãng.', 'quy_cach', 'bảo hành 24 tháng'),
        ('IP65', 'Vỏ đạt chuẩn IP65 chống nước.', 'quy_cach', 'IP65'),
        ('IEC 62271', 'Sản xuất theo tiêu chuẩn IEC 62271.', 'quy_cach', 'IEC 62271'),
        ('90°C', 'Chịu nhiệt độ hoạt động lên tới 90°C.', 'quy_cach', '90°C'),
        ('99%', 'Độ tin cậy vận hành đạt 99%.', 'quy_cach', '99%'),
    ]
    for ten, text, field, gia_tri_them in cases:
        chan = R.kiem_tra_bia(text, row_hb)
        test('D3', f'Hard Block chặn "{ten}" khi record KHÔNG có', bool(chan))

        row_co = dict(row_hb)
        row_co[field] = (row_co.get(field, '') + ' ' + gia_tri_them).strip()
        chan_co = R.kiem_tra_bia(text, row_co)
        test('D4', f'Hard Block CHO PHÉP "{ten}" khi record thực sự có', not chan_co)

    # ============================================================ 5. Regression composite
    r_06 = next(x for x in cd_rows if x.get('cap_dien_ap') == '0.6/1kV')
    test('D5', 'Regression 0.6/1kV: đúng -> PASS, giả 99/1kV -> BLOCK',
         not R.kiem_tra_bia('Điện áp 0.6/1kV.', r_06) and R.kiem_tra_bia('Điện áp 99/1kV.', r_06))

    r_300 = next((x for x in cd_rows if '300/500' in (x.get('cap_dien_ap') or '')), None)
    if r_300 is None:
        r_300 = dict(next(x for x in cd_rows if x['outline_id'] == 'outline_cap_dien'))
        r_300['cap_dien_ap'] = '300/500V'
    test('D5', 'Regression 300/500V: đúng -> PASS',
         not R.kiem_tra_bia('Điện áp 300/500V.', r_300))

    r_350 = dict(next(x for x in cd_rows if x['outline_id'] == 'outline_cap_dien'))
    r_350['tiet_dien'] = '3x50'
    test('D5', 'Regression 3x50mm²: đúng -> PASS, giả 9x50mm² -> BLOCK',
         not R.kiem_tra_bia('Tiết diện 3x50mm².', r_350) and R.kiem_tra_bia('Tiết diện 9x50mm².', r_350))

    r_3x50_1x25 = dict(r_350)
    r_3x50_1x25['tiet_dien'] = '3x50+1x25'
    test('D5', 'Regression 3x50+1x25mm²: đúng -> PASS',
         not R.kiem_tra_bia('Cáp 3x50+1x25mm2 dùng cho tải 3 pha.', r_3x50_1x25))

    # ============================================================ 6. Hai mẫu
    sp_mau = cd_rows[0]
    ai_c, _ = AWP.goi_ai_mock(sp_mau, mau='chuan')
    ai_n, _ = AWP.goi_ai_mock(sp_mau, mau='ngan_gon')
    bai_c = R.dung_bai_html(sp_mau, ai_c, site_cfg, mau='chuan')
    bai_n = R.dung_bai_html(sp_mau, ai_n, site_cfg, mau='ngan_gon')
    test('D6', 'Hai mẫu: HTML khác nhau', bai_c['html'] != bai_n['html'])
    test('D6', 'Hai mẫu: slug khác nhau', bai_c['slug'] != bai_n['slug'])

    AWP.reset_wp_mock()
    r1 = AWP.sinh_va_dang_mock(con, sp_mau['dataset_id'], sp_mau['record_id'], 'lotech', site_cfg, mau='chuan')
    bv1 = DB.lay_bai_viet(con, sp_mau['dataset_id'], sp_mau['record_id'], 'lotech', 'chuan')
    r1b = AWP.sinh_va_dang_mock(con, sp_mau['dataset_id'], sp_mau['record_id'], 'lotech', site_cfg, mau='chuan')
    bv1b = DB.lay_bai_viet(con, sp_mau['dataset_id'], sp_mau['record_id'], 'lotech', 'chuan')
    test('D6', 'Hai mẫu: chạy lại cùng dataset+record+site+mẫu KHÔNG tạo bài mới (wp_id giữ nguyên)',
         r1['ok'] and r1b['ok'] and bv1['wp_id'] == bv1b['wp_id'])

    # ============================================================ 7. Không gọi WordPress thật
    import inspect
    nguon_sinh_va_dang_mock = inspect.getsource(AWP.sinh_va_dang_mock)
    test('D7', 'sinh_va_dang_mock() (đường UI/test đang dùng) không gọi dang_wp_that/requests.post thật',
         'dang_wp_that' not in nguon_sinh_va_dang_mock and 'requests.post' not in nguon_sinh_va_dang_mock)

    con.close()
    if os.path.exists(DB_TEST):
        os.remove(DB_TEST)

    print()
    so_pass = sum(1 for _, _, ok, _ in KET_QUA if ok)
    print(f'TỔNG GATE 2: {so_pass}/{len(KET_QUA)} PASS')
    return KET_QUA


if __name__ == '__main__':
    kq = main()
    fail = [x for x in kq if not x[2]]
    if fail:
        print('\nFAIL:')
        for ma, mo_ta, ok, gc in fail:
            print(f'  {ma}: {mo_ta} ({gc})')
        raise SystemExit(1)
