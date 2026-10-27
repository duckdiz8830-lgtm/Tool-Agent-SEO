import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
# -*- coding: utf-8 -*-
"""
Ver 4.9.8 Claude — theo yêu cầu Thịnh (demo "ultra" 29/07/2026):
1. CTA cuối trang đồng bộ dạng nút với CTA gọn (khoi_cta_ngan) — không còn
   đoạn văn xuôi khác kiểu.
2. Bảng so sánh công suất trong dòng — CODE dựng, KHÔNG qua AI, dùng
   db_phase2.tim_san_pham_cung_dong().
3. Gộp "2 góc nhìn" (kỹ sư/đầu tư) vào 1 đoạn dac_diem_html tự nhiên,
   không tách khối riêng.
4. Class CSS đồng bộ (.lotech-khoi-chung, .lotech-cta-cuoi,
   .lotech-so-sanh-table) — style thật nằm ở lotech-theme.css (dán 1 lần
   vào Theme, KHÔNG nhét <style> vào content — tránh lặp bug schema cũ).

Chạy: python3 test_v498_patch.py
"""
import os
import sys

import db_phase2 as DB
import nhap_phase2 as N
import profiles as P
import prompts_phase2 as PR
import render_phase2 as R

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ver 5.1 -- test o tests/, du lieu/module chinh o thu muc goc (len 1 cap)
MASTER_GOC = os.path.join(BASE, 'tests', 'fixtures', 'MASTER_4_PROFILE_SAN_PHAM.xlsx')

KET_QUA = []


def test(ma, mo_ta, dieu_kien):
    KET_QUA.append((ma, mo_ta, bool(dieu_kien)))
    print(f'[{"PASS" if dieu_kien else "FAIL"}] {ma}: {mo_ta}')


def main():
    if not os.path.exists(MASTER_GOC):
        print('THIẾU MASTER_4_PROFILE_SAN_PHAM.xlsx — bỏ qua test này.')
        sys.exit(0)

    r = N.import_4_profile(MASTER_GOC, chi_profile='may_bien_ap_do_luong')
    info = r['may_bien_ap_do_luong']
    cot_import_keys = list(P.PROFILES['may_bien_ap_do_luong']['cot_import'].values())
    con = DB.ket_noi(':memory:')
    did, _ = DB.xac_nhan_dataset(con, 'may_bien_ap_do_luong', 'test.xlsx', info['file_checksum'],
                                 info['data_checksum'], len(info['rows']), cot_import_keys)
    DB.ghi_san_pham(con, did, info['rows'])
    row250 = next(x for x in info['rows'] if x['ma_goc'] == 'MBT3P250A2608')

    # ============================================================ 1. CTA đồng bộ
    site_cfg = {'ten': 'Test Site', 'hotline': '0900000000', 'zalo': '0900000000'}
    cta = R.khoi_cta(site_cfg)
    test('U1-01', 'CTA cuối trang dùng style nút Gọi giống CTA gọn (Ver 4.9.9: inline style, không class)', 'tel:' in cta and 'background:#16a34a' in cta)
    test('U1-02', 'CTA cuối trang dùng style nút Zalo', 'zalo.me' in cta and 'background:#0ea5e9' in cta)
    test('U1-03', 'CTA cuối trang vẫn giữ id="lien-he-bao-gia" (đích neo nút Yêu cầu báo giá)',
         'id="lien-he-bao-gia"' in cta)
    test('U1-04', 'CTA cuối trang bọc trong div có style nền riêng (Ver 4.9.9, không dùng class)',
         '<div style=' in cta and 'lien-he-bao-gia' in cta)
    cta_khong_hotline = R.khoi_cta({'ten': 'X'})
    test('U1-05', 'CTA khi KHÔNG có hotline vẫn giữ id neo, không crash',
         'id="lien-he-bao-gia"' in cta_khong_hotline)

    # ============================================================ 2. Bảng so sánh công suất
    cung_dong = DB.tim_san_pham_cung_dong(con, did, row250['record_id'])
    test('U2-01', f'Tìm được SKU anh em cùng dòng cho MBT3P250A2608 (thực tế {len(cung_dong)})',
         len(cung_dong) >= 3)
    bang = R.khoi_so_sanh_cong_suat(row250, cung_dong)
    test('U2-02', 'Ver 5.2: Bảng so sánh CÓ chứa TÊN sản phẩm anh em thật (không còn mã hàng — Thịnh: "mã hàng ai biết")',
         any('Máy biến áp' in sp.get('ten_goc', '') for sp in cung_dong) and 'MBT3P400A2608' not in bang)
    test('U2-03', 'Bảng so sánh KHÔNG hiện cột Cấp điện áp (dữ liệu MASTER đang lỗi ở cột này)',
         'Cấp điện áp' not in bang and 'Cấp Điện Áp' not in bang)
    test('U2-04', 'Bảng so sánh dùng style inline (Ver 4.9.9, không class)', 'style=' in bang and '<table' in bang)
    test('U2-05', 'Không có SKU anh em (cung_dong rỗng) -> trả rỗng, không hiện bảng cụt',
         R.khoi_so_sanh_cong_suat(row250, []) == '')
    test('U2-06', 'Không có SKU anh em (cung_dong None) -> trả rỗng, không crash',
         R.khoi_so_sanh_cong_suat(row250, None) == '')

    # ============================================================ 3. Wiring thật + class khối chung
    khoi_chung = R.khoi_chung_may_bien_ap(row250)
    test('U3-01', 'Khối "về máy biến áp nói chung" có style inline (Ver 4.9.9, không class)',
         'style=' in khoi_chung)

    ai_data = {'meta_title': 'T', 'meta_description': 'M', 'intro_html': '<p>i</p>',
               'dac_diem_html': '<p>d</p>', 'ung_dung_html': '<p>u</p>', 'huong_dan_chon_html': '<p>h</p>'}
    bai = R.dung_bai_html(row250, ai_data, site_cfg, cung_dong=cung_dong)
    test('U4-01', 'dung_bai_html() CÓ chèn bảng so sánh công suất khi truyền cung_dong',
         'So sánh công suất trong dòng' in bai['html'])
    test('U4-02', 'dung_bai_html() KHÔNG chèn bảng so sánh khi không truyền cung_dong (mặc định None)',
         'So sánh công suất trong dòng' not in R.dung_bai_html(row250, ai_data, site_cfg)['html'])
    test('U4-03', 'HTML cuối cùng dùng CTA dạng nút (style nền xanh) chứ không phải đoạn văn cũ',
         'background:#16a34a' in bai['html'])

    # ============================================================ 4. Prompt gộp 2 góc nhìn — không tách khối
    cfg = PR.OUTLINE_NOI_DUNG['outline_may_bien_ap']
    dac_diem_guidance = cfg['sections']['dac_diem_html']
    test('U5-01', 'Prompt dac_diem_html yêu cầu chia 2-3 đoạn <p> ngắn (Ver 5.0, đổi từ "1 đoạn liền mạch" theo Thịnh xem thật thấy khó đọc)',
         '2-3 ĐOẠN' in dac_diem_guidance and 'KHÔNG dồn thành 1 khối' in dac_diem_guidance)
    test('U5-02', 'Prompt vẫn giữ nguyên tắc không bịa loại máy ngoài dữ liệu (KHÔNG bị mất khi sửa)',
         'KHÔNG bịa thêm loại máy' in dac_diem_guidance)

    tong = len(KET_QUA)
    dat = sum(1 for _, _, ok in KET_QUA if ok)
    print(f'\nTỔNG VER 4.9.8 PATCH: {dat}/{tong} PASS')
    if dat != tong:
        sys.exit(1)


if __name__ == '__main__':
    main()
