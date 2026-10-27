# -*- coding: utf-8 -*-
"""
Ver 5.2 Claude — theo phản hồi Thịnh trên site thật (ảnh chụp 30/07/2026):

1. "Vỏ mạ kẽm nhúng nóng MBA..." (VỎ THÉP, không phải máy biến áp) bị gọi
   nhầm "Máy biến áp MBT 1500kVA - Báo Giá" — SAI SỰ THẬT. Tách outline
   RIÊNG (outline_vo_may_bien_ap).
2. Title "Báo giá" phải đứng ĐẦU câu, không phải cuối.
3. Nút "Yêu cầu báo giá" phải hành động NGAY (gọi thẳng), không nhảy
   xuống cuối trang.
4. Bảng so sánh công suất phải hiện TÊN SẢN PHẨM, không hiện mã hàng.

Chạy: python3 tests/test_v52_patch.py
"""
import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))

import os
import sys

import db_phase2 as DB
import nhap_phase2 as N
import profiles as P
import render_phase2 as R

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_GOC = os.path.join(BASE, 'MASTER_4_PROFILE_SAN_PHAM.xlsx')

KET_QUA = []


def test(ma, mo_ta, dieu_kien):
    KET_QUA.append((ma, mo_ta, bool(dieu_kien)))
    print(f'[{"PASS" if dieu_kien else "FAIL"}] {ma}: {mo_ta}')


def main():
    # ============================================================ 1. Outline riêng cho vỏ
    row_vo = {'nhom_nguon': '05. Máy Biến Áp', 'ten_goc': 'Vỏ mạ kẽm nhúng nóng MBA 1P 15KVA 12,7/0,23KV-  MBT'}
    row_that = {'nhom_nguon': '05. Máy Biến Áp', 'ten_goc': 'Máy biến áp dầu 1Pha 15KVA'}
    test('Y1-01', "Outline riêng 'outline_vo_may_bien_ap' đã đăng ký", 'outline_vo_may_bien_ap' in P.OUTLINES)
    test('Y1-02', 'Vỏ mạ kẽm route đúng outline riêng, KHÔNG còn outline_may_bien_ap',
         P.xac_dinh_outline_id('may_bien_ap_do_luong', row_vo) == 'outline_vo_may_bien_ap')
    test('Y1-03', 'Máy biến áp thật vẫn route outline_may_bien_ap như cũ (an toàn ngược)',
         P.xac_dinh_outline_id('may_bien_ap_do_luong', row_that) == 'outline_may_bien_ap')

    # ============================================================ 2. Title: KHÔNG còn gọi vỏ là "máy biến áp", Báo Giá đứng đầu
    row_vo_du = dict(row_vo, outline_id='outline_vo_may_bien_ap', thuong_hieu='MBT', cong_suat='1500 kVA')
    tieu_de_vo = R.dung_tieu_de(row_vo_du)
    test('Y2-01', 'Title vỏ KHÔNG chứa "Máy biến áp" (tránh gọi vỏ thành máy — lỗi Thịnh phát hiện)',
         'Máy biến áp' not in tieu_de_vo)
    # Ver 3.5.1 — title chuyển sang sentence case, so khớp không phân biệt hoa/thường
    test('Y2-02', 'Title vỏ CÓ nhắc "vỏ bảo vệ" (đúng bản chất sản phẩm)',
         'vỏ bảo vệ' in tieu_de_vo.lower())
    test('Y2-03', 'Title vỏ bắt đầu bằng "Báo giá" (Thịnh: đứng đầu không phải cuối)',
         tieu_de_vo.startswith('Báo giá'))

    row_mba_du = dict(row_that, outline_id='outline_may_bien_ap', thuong_hieu='MBT', cong_suat='250 kVA')
    tieu_de_mba = R.dung_tieu_de(row_mba_du)
    test('Y2-04', 'Title máy biến áp thật CŨNG bắt đầu bằng "Báo giá"', tieu_de_mba.startswith('Báo giá'))
    test('Y2-05', 'Title máy biến áp thật vẫn nhắc "máy biến áp" (không đổi cho SKU thật)',
         'máy biến áp' in tieu_de_mba.lower())

    # ============================================================ 3. CTA gọi thẳng, không jump
    site_cfg = {'ten': 'Test', 'hotline': '0900000000', 'zalo': '0900000000'}
    cta = R.khoi_cta_ngan(site_cfg)
    test('Y3-01', 'CTA gọn CÓ hotline -> nút "Yêu cầu báo giá" là tel: (gọi thẳng, không jump)',
         'tel:0900000000' in cta)
    test('Y3-02', 'CTA gọn KHÔNG còn dùng href="#lien-he-bao-gia" khi có hotline',
         '#lien-he-bao-gia' not in cta)
    cta_khong_hotline = R.khoi_cta_ngan({})
    test('Y3-03', 'CTA gọn KHÔNG hotline -> vẫn có fallback #lien-he-bao-gia (không crash, không mất CTA)',
         '#lien-he-bao-gia' in cta_khong_hotline)

    # ============================================================ 4. Bảng so sánh hiện tên, không hiện mã
    if os.path.exists(MASTER_GOC):
        r = N.import_4_profile(MASTER_GOC, chi_profile='may_bien_ap_do_luong')
        info = r['may_bien_ap_do_luong']
        cot_import_keys = list(P.PROFILES['may_bien_ap_do_luong']['cot_import'].values())
        con = DB.ket_noi(':memory:')
        did, _ = DB.xac_nhan_dataset(con, 'may_bien_ap_do_luong', 'test.xlsx', info['file_checksum'],
                                     info['data_checksum'], len(info['rows']), cot_import_keys)
        DB.ghi_san_pham(con, did, info['rows'])

        vo_row = next(x for x in info['rows'] if x['ma_goc'] == 'MBTVMK1P15')
        cung_dong_vo = DB.tim_san_pham_cung_dong(con, did, vo_row['record_id'])
        test('Y4-01', f'Vỏ mạ kẽm CÓ SKU anh em cùng dòng (thực tế {len(cung_dong_vo)})', len(cung_dong_vo) > 0)
        test('Y4-02', "cung_dong trả về CÓ field 'ten_goc' (mới, để hiện tên thay vì mã)",
             all('ten_goc' in sp for sp in cung_dong_vo))

        bang_vo = R.khoi_so_sanh_cong_suat(vo_row, cung_dong_vo)
        test('Y4-03', 'Bảng so sánh của vỏ KHÔNG chứa mã hàng dạng "MBTVMK" (chỉ còn tên)',
             'MBTVMK' not in bang_vo)
        test('Y4-04', 'Header bảng ghi "Sản phẩm" (không phải "Mã hàng")', '>Sản phẩm<' in bang_vo)

        # Kiểm tra KHÔNG so sánh chéo vỏ với máy biến áp thật (2 outline khác nhau)
        mba_row = next(x for x in info['rows'] if x['outline_id'] == 'outline_may_bien_ap' and x.get('cong_suat'))
        cung_dong_mba = DB.tim_san_pham_cung_dong(con, did, mba_row['record_id'])
        test('Y4-05', 'Máy biến áp thật KHÔNG có "Vỏ mạ kẽm" trong danh sách anh em (không so chéo khác outline)',
             all('Vỏ mạ kẽm' not in sp.get('ten_goc', '') for sp in cung_dong_mba))

        # khoi_chung_may_bien_ap vẫn PHẢI rỗng cho vỏ (nguyên lý làm mát không áp dụng)
        test('Y4-06', 'Khối "về máy biến áp nói chung" (ONAN/AN-AF) vẫn KHÔNG áp dụng cho vỏ',
             R.khoi_chung_may_bien_ap(vo_row) == '')

    tong = len(KET_QUA)
    dat = sum(1 for _, _, ok in KET_QUA if ok)
    print(f'\nTỔNG VER 5.2 PATCH: {dat}/{tong} PASS')
    if dat != tong:
        sys.exit(1)


if __name__ == '__main__':
    main()
