import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
# -*- coding: utf-8 -*-
"""
Ver 4.9.9 Claude — theo review SEO (Gemini, qua Thịnh) về duplicate content
giữa các SKU cùng dòng:
1. CSS inline (không phụ thuộc file CSS ngoài, không cần Thịnh thao tác tay).
2. Bỏ hẳn prefix "lotech-"/tên riêng trong class — không để lại dấu vết
   tool/domain trong source HTML.
3. Delta Context tính BẰNG CODE (tier, chênh lệch kVA/%, tải ước tính),
   đưa vào prompt AI để chống trùng lặp giữa các SKU cùng dòng — và phải
   được Hard Block CHẤP NHẬN (không chặn nhầm số đã tính sẵn).
4. Boilerplate "khối chung" rút gọn còn 1 câu (chống Site-wide Quality bị
   Google đánh giá thấp vì lặp y nguyên).
5. Title/H1 SKU-first, CODE dựng cố định (không phụ thuộc AI), KHÔNG có
   ngày tháng.
6. Khối "Về thương hiệu" — data catalogue thật (MBT/THIBIDI), brand khác
   để trống, không bịa.
7. KHÔNG đưa số bịa (% tiết kiệm chi phí, % tăng công suất AF không nguồn)
   vào bất kỳ đâu.

Chạy: python3 test_v499_patch.py
"""
import os
import sys

import ai_wp_adapter as AWP
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
    cung_dong = DB.tim_san_pham_cung_dong(con, did, row250['record_id'])

    # ============================================================ 1. CSS inline, không class riêng
    site_cfg = {'ten': 'Test', 'hotline': '0900000000', 'zalo': '0900000000'}
    cta = R.khoi_cta(site_cfg)
    hero = R.khoi_hero(row250, site_cfg)
    bang = R.bang_thong_so(row250)
    test('V1-01', 'CTA dùng style="" inline, không phụ thuộc class', 'style="' in cta)
    test('V1-02', 'Hero dùng style="" inline', 'style="' in hero)
    test('V1-03', 'Bảng thông số dùng style="" inline', 'style="' in bang)

    # ============================================================ 2. Không còn prefix "lotech-"
    ai_data = {'meta_title': 'T', 'meta_description': 'M', 'intro_html': '<p>i</p>',
               'dac_diem_html': '<p>d</p>', 'ung_dung_html': '<p>u</p>', 'huong_dan_chon_html': '<p>h</p>'}
    bai = R.dung_bai_html(row250, ai_data, site_cfg, cung_dong=cung_dong)
    test('V2-01', 'HTML cuối cùng KHÔNG còn chuỗi "lotech-" nào (không để lại dấu vết tool)',
         'lotech-' not in bai['html'])
    test('V2-02', 'Vẫn giữ id="lien-he-bao-gia" (chức năng, không phải thẩm mỹ)',
         'id="lien-he-bao-gia"' in bai['html'])

    # ============================================================ 3. Delta context — tính đúng + Hard Block chấp nhận
    delta = R.tinh_delta_context(row250, cung_dong)
    test('V3-01', 'Tính đúng tier (250-1000kVA -> "trung")', 'trung' in delta.get('tier_cong_suat', ''))
    test('V3-02', 'Tính đúng SKU liền kề nhỏ hơn (180kVA)', '180' in delta.get('sku_lien_ke_nho', ''))
    test('V3-03', 'Tính đúng SKU liền kề lớn hơn (320kVA)', '320' in delta.get('sku_lien_ke_lon', ''))
    test('V3-04', 'Tải ước tính CÓ chú thích "ước tính, giả định cosφ"',
         'ước tính' in delta.get('tai_uoc_tinh', '') and 'cosφ' in delta.get('tai_uoc_tinh', ''))
    test('V3-05', 'Field delta_context KHÔNG có công suất (thiếu cong_suat) -> trả {} (không suy đoán)',
         R.tinh_delta_context({'outline_id': 'outline_may_bien_ap', 'cong_suat': ''}, []) == {})
    test('V3-06', 'Sai outline -> trả {} dù có đủ data khác', R.tinh_delta_context({'outline_id': 'x', 'cong_suat': '160 kVA'}, []) == {})

    # Field delta context ĐÃ đăng ký trong Profile/Outline Registry (bắt buộc để Hard Block nhận)
    ca_profile = P.PROFILES['may_bien_ap_do_luong']['cot_ai']
    ca_outline = P.OUTLINES['outline_may_bien_ap']['cot_ai']
    for f in ['tier_cong_suat', 'sku_lien_ke_nho', 'sku_lien_ke_lon', 'chenh_lech_nho', 'chenh_lech_lon', 'tai_uoc_tinh']:
        test(f'V3-REG-{f}', f'Field "{f}" có trong CẢ profile lẫn outline cot_ai (bắt buộc để Hard Block nhận)',
             f in ca_profile and f in ca_outline)

    # Hard Block: giả lập AI VIẾT LẠI đúng số delta context -> KHÔNG được chặn
    row_ai = dict(row250, **delta)
    text_gia_lap = (f"So với mã {delta['sku_lien_ke_nho']}, sản phẩm này có công suất lớn hơn "
                    f"{delta['chenh_lech_nho'].split('(')[0].strip()}, phù hợp tải ước tính "
                    f"{delta['tai_uoc_tinh']}.")
    vi_pham = AWP.kiem_tra_bia_toan_bo({'dac_diem_html': text_gia_lap}, row_ai)
    test('V3-07', f'Hard Block KHÔNG chặn khi AI viết lại đúng số delta context (vi phạm: {vi_pham})',
         not vi_pham)

    # Hard Block vẫn PHẢI chặn nếu AI bịa số % không có trong delta context
    text_bia = f"So với mã {delta['sku_lien_ke_nho']}, tiết kiệm 15% chi phí đầu tư."
    vi_pham2 = AWP.kiem_tra_bia_toan_bo({'dac_diem_html': text_bia}, row_ai)
    test('V3-08', 'Hard Block VẪN chặn số % bịa (15% tiết kiệm chi phí) không có trong delta context',
         bool(vi_pham2))

    # ============================================================ 4. Boilerplate rút gọn
    khoi_chung = R.khoi_chung_may_bien_ap(row250)
    so_tu = len(khoi_chung.split())
    test('V4-01', f'Khối chung rút gọn dưới 40 từ (thực tế {so_tu} từ) — chống Boilerplate/Site-wide Quality',
         so_tu < 40)
    test('V4-02', 'Khối chung vẫn phân biệt đúng dầu/khô (không lẫn nguyên lý)',
         'ONAN' in khoi_chung)

    # ============================================================ 5. Title SKU-first, không ngày tháng
    tieu_de = R.dung_tieu_de(row250)
    test('V5-01', 'Title KHÔNG còn mã hàng (Ver 5.0 — Thịnh xem thật thấy "ngốc nghếch", bỏ theo yêu cầu)',
         'MBT3P250A2608' not in tieu_de)
    test('V5-01B', 'Title CÓ "Báo giá" (Ver 3.5.1: sentence case) (yêu cầu gốc bị Ver 4.9.9 làm sót)', 'Báo giá' in tieu_de)
    test('V5-02', 'Title chứa công suất', '250' in tieu_de)
    test('V5-03', 'Title chứa thương hiệu', 'MBT' in tieu_de)
    test('V5-04', 'Title KHÔNG chứa số năm 4 chữ số dạng ngày tháng (VD 2026)', '2026' not in tieu_de)
    # Ver 3.9 C2 đã CỐ Ý thay contract riêng cho MOF: title không còn trả
    # nguyên ten_goc mà chuẩn hoá thành Hợp bộ đo lường (MOF) + discriminator
    # nếu source có. Assertion legacy 'trả ten_goc' vì vậy đã lỗi thời.
    tieu_de_khac_outline = R.dung_tieu_de({'outline_id': 'outline_do_luong', 'ten_goc': 'MOF 24kV'})
    test('V5-05', 'Regression hiện hành: MOF dùng title chuẩn hoá Ver 3.9 C2, không quay lại contract legacy',
         tieu_de_khac_outline == 'Hợp bộ đo lường (MOF) chính hãng')

    # ============================================================ 6. Khối thương hiệu
    kh_mbt = R.khoi_ve_thuong_hieu(row250)
    test('V6-01', 'Brand MBT có khối giới thiệu (data catalogue thật)', 'MBT' in kh_mbt and 'ISO 9001' in kh_mbt)
    kh_khac = R.khoi_ve_thuong_hieu({'thuong_hieu': 'KP/Hàn Quốc'})
    test('V6-02', 'Brand chưa có nguồn (KP) -> trả rỗng, KHÔNG bịa thông tin công ty', kh_khac == '')

    # ============================================================ 7. Không có số bịa trong bất kỳ đâu
    test('V7-01', 'Không đâu trong khối chung/thương hiệu/title có "%" (không có số % nào bị bịa cứng vào code)',
         '%' not in khoi_chung and '%' not in kh_mbt and '%' not in tieu_de)

    # ============================================================ 8. Regression: 3 profile khác không đổi hành vi
    r_cd = N.import_4_profile(MASTER_GOC, chi_profile='cap_dien')['cap_dien']['rows']
    test('V8-01', f'cap_dien vẫn import bình thường (thực tế {len(r_cd)} dòng)', len(r_cd) > 0)
    test('V8-02', 'Field delta-context KHÔNG lọt sang profile khác',
         'tier_cong_suat' not in P.PROFILES['cap_dien']['cot_ai'])

    tong = len(KET_QUA)
    dat = sum(1 for _, _, ok in KET_QUA if ok)
    print(f'\nTỔNG VER 4.9.9 PATCH: {dat}/{tong} PASS')
    if dat != tong:
        sys.exit(1)


if __name__ == '__main__':
    main()
