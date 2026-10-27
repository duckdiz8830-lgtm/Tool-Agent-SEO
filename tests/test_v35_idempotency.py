import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
# -*- coding: utf-8 -*-
"""
Ver 3.5 — test "website identity": đổi TÊN hiển thị không được đổi khoá lưu
trữ; đổi DOMAIN phải coi là website khác; dữ liệu bản < 3.5 (khoá theo tên)
phải tự di chuyển sang khoá URL khi mở app / lưu lại cấu hình, GIỮ NGUYÊN
wp_id/wp_url/trạng thái/thời lượng.

Chạy: python3 test_v35_idempotency.py
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ver 5.1 -- test o tests/, du lieu/module chinh o thu muc goc (len 1 cap)

KQ = []


def test(ma, mota, ok, gc=''):
    ok = bool(ok)
    KQ.append((ma, mota, ok))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}' + (f'  ({gc})' if gc else ''))
    return ok


def main():
    import cauhinh as C
    import db_phase2 as DB

    # ---------------------------------------------------- 1. chuan_hoa_url
    test('ID-1', 'Đổi TÊN (không đổi URL) -> cùng site_key',
         C.chuan_hoa_url('https://lotech.com.vn') == C.chuan_hoa_url('https://lotech.com.vn'))
    test('ID-1', '3 dạng viết URL cùng site -> cùng 1 site_key',
         C.chuan_hoa_url('https://Lotech.com.vn/') == C.chuan_hoa_url('http://www.lotech.com.vn')
         == C.chuan_hoa_url('lotech.com.vn'))
    test('ID-1', 'Domain khác nhau -> site_key khác nhau',
         C.chuan_hoa_url('https://a.vn') != C.chuan_hoa_url('https://b.vn'))

    # ---------------------------------------------------- 2. doc_website() trả đủ site_key
    if os.path.exists(os.path.join(BASE, 'cau-hinh.env')):
        os.remove(os.path.join(BASE, 'cau-hinh.env'))
    C.luu_website('Lotech A', 'https://lotech-a.vn', 'admin', 'pw pw pw')
    wc1 = C.doc_website()
    test('ID-2', f'doc_website() trả site_key đúng: {wc1["site_key"]}', wc1['site_key'] == 'lotech-a.vn')

    # ĐỔI TÊN, giữ nguyên URL -> site_key KHÔNG đổi
    C.luu_website('Lotech A (tên mới)', 'https://lotech-a.vn', 'admin', 'pw pw pw')
    wc2 = C.doc_website()
    test('ID-2', f'Đổi TÊN, giữ URL -> site_key KHÔNG đổi: {wc1["site_key"]} == {wc2["site_key"]}',
         wc1['site_key'] == wc2['site_key'])

    # ĐỔI DOMAIN -> site_key ĐỔI (coi là website khác)
    C.luu_website('Lotech A (tên mới)', 'https://lotech-b.vn', 'admin', 'pw pw pw')
    wc3 = C.doc_website()
    test('ID-2', f'Đổi DOMAIN -> site_key ĐỔI (site khác): {wc2["site_key"]} != {wc3["site_key"]}',
         wc2['site_key'] != wc3['site_key'])

    # ---------------------------------------------------- 3. migration giữ nguyên wp_id/url/trạng thái
    DB_TEST = os.path.join(BASE, 'test_id.db')
    if os.path.exists(DB_TEST):
        os.remove(DB_TEST)
    con = DB.ket_noi(DB_TEST)
    did, _ = DB.xac_nhan_dataset(con, 'cap_dien', 't.xlsx', 'fc', 'dc', 1, ['a'])
    DB.ghi_san_pham(con, did, [{'record_id': 'r1', 'profile_id': 'cap_dien',
                                'outline_id': 'o', 'content_type': 'product'}])
    # mô phỏng dữ liệu bản < 3.5: site = TÊN hiển thị (không phải URL)
    DB.cap_nhat_bai_viet(con, did, 'r1', 'Lotech A (tên mới)', 'chuan',
                         wp_id='42', wp_url='https://lotech-b.vn/?p=42', trang_thai='da_dang',
                         ngay_dang='2026-01-01T00:00:00+00:00', thoi_luong_giay=7.5)

    so = DB.doi_khoa_site(con, 'Lotech A (tên mới)', wc3['site_key'])
    test('ID-3', f'Migration chuyển đúng {so} dòng (kỳ vọng 1)', so == 1)

    bv_moi = DB.lay_bai_viet(con, did, 'r1', wc3['site_key'], 'chuan')
    test('ID-3', f'Sau migration: bài viết tra được dưới site_key mới, GIỮ NGUYÊN wp_id/wp_url/'
                f'trạng thái/thời lượng: {bv_moi}',
         bv_moi is not None and bv_moi['wp_id'] == '42'
         and bv_moi['wp_url'] == 'https://lotech-b.vn/?p=42'
         and bv_moi['trang_thai'] == 'da_dang' and bv_moi['thoi_luong_giay'] == 7.5)

    bv_cu = DB.lay_bai_viet(con, did, 'r1', 'Lotech A (tên mới)', 'chuan')
    test('ID-3', 'Dưới khoá CŨ (tên hiển thị) không còn tra được nữa (đã chuyển hẳn, không nhân đôi)',
         bv_cu is None)

    # migration không đụng gì nếu khoá cũ không tồn tại (an toàn, không lỗi)
    so2 = DB.doi_khoa_site(con, 'khong-ton-tai-bao-gio', wc3['site_key'])
    test('ID-3', f'Migration từ khoá không tồn tại -> trả 0, không lỗi (thực tế {so2})', so2 == 0)

    con.close()
    if os.path.exists(DB_TEST):
        os.remove(DB_TEST)

    # ---------------------------------------------------- 4. auto-migration qua UI thật (giao-dien.py)
    import importlib.util
    spec = importlib.util.spec_from_file_location('giao_dien', os.path.join(BASE, 'giao-dien.py'))
    gd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gd)

    if os.path.exists(os.path.join(BASE, 'cau-hinh.env')):
        os.remove(os.path.join(BASE, 'cau-hinh.env'))
    if os.path.exists(os.path.join(BASE, 'phase2-du-lieu.db')):
        os.remove(os.path.join(BASE, 'phase2-du-lieu.db'))

    # bước 1: cấu hình lần đầu (mô phỏng bản 3.4 -- lưu wc rồi tự tay ghi bài
    # dưới khoá TÊN, đúng hành vi bản cũ)
    C.luu_website('Site Cu 34', 'https://sitecu34.vn', 'admin', 'pw pw pw')
    con2 = DB.ket_noi()
    did2, _ = DB.xac_nhan_dataset(con2, 'cap_dien', 't2.xlsx', 'fc2', 'dc2', 1, ['a'])
    DB.ghi_san_pham(con2, did2, [{'record_id': 'r2', 'profile_id': 'cap_dien',
                                  'outline_id': 'o', 'content_type': 'product'}])
    DB.cap_nhat_bai_viet(con2, did2, 'r2', 'Site Cu 34', 'chuan', wp_id='99',
                         wp_url='https://sitecu34.vn/?p=99', trang_thai='da_dang')
    con2.close()

    # bước 2: mở app Ver 3.5 -- __init__ phải TỰ migration ngay lúc khởi động
    import subprocess
    xvfb_can = 'DISPLAY' in os.environ
    if xvfb_can:
        app = gd.PhanMem()
        app.update()
        con3 = DB.ket_noi()
        bv_sau_khoi_dong = DB.lay_bai_viet(con3, did2, 'r2', C.doc_website()['site_key'], 'chuan')
        con3.close()
        test('ID-4', f'Mở app Ver 3.5 TỰ migration dữ liệu bản cũ lúc khởi động, giữ nguyên wp_id: '
                    f'{bv_sau_khoi_dong}',
             bv_sau_khoi_dong is not None and bv_sau_khoi_dong['wp_id'] == '99')
        app.destroy()
    else:
        test('ID-4', 'Bỏ qua (không có DISPLAY, cần chạy qua xvfb-run)', True, 'skip')

    for f in ('cau-hinh.env', 'phase2-du-lieu.db'):
        p = os.path.join(BASE, f)
        if os.path.exists(p):
            os.remove(p)

    print()
    p = sum(1 for _, _, ok in KQ if ok)
    print(f'TỔNG: {p}/{len(KQ)} PASS')
    return KQ


if __name__ == '__main__':
    kq = main()
    if any(not ok for _, _, ok in kq):
        sys.exit(1)
