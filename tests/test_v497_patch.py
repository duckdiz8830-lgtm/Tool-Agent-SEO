import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
# -*- coding: utf-8 -*-
"""
Ver 4.9.7 Claude — khối cố định "về máy biến áp [dầu/khô] nói chung",
CODE viết cứng, KHÔNG phải AI đoán mỗi lần. Thịnh duyệt hướng qua demo HTML
mẫu SKU MBT3P250A2608 (29/07/2026).

Điểm bắt buộc phải test kỹ: dầu và khô KHÁC NGUYÊN LÝ LÀM MÁT HOÀN TOÀN —
gán nhầm là bịa sai thông tin kỹ thuật thật (dầu = ONAN tuần hoàn dầu, khô
= AN/AF không dầu). Không nhận diện được loại -> PHẢI trả rỗng, không đoán.

Chạy: python3 test_v497_patch.py
"""
import os
import sys

import nhap_phase2 as N
import render_phase2 as R

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ver 5.1 -- test o tests/, du lieu/module chinh o thu muc goc (len 1 cap)
MASTER_GOC = os.path.join(BASE, 'MASTER_4_PROFILE_SAN_PHAM.xlsx')

KET_QUA = []


def test(ma, mo_ta, dieu_kien):
    KET_QUA.append((ma, mo_ta, bool(dieu_kien)))
    print(f'[{"PASS" if dieu_kien else "FAIL"}] {ma}: {mo_ta}')


def main():
    # ============================================================ 1. Đơn vị: phát hiện loại + số pha
    test('T1-01', 'Nhận diện "dầu" -> dau', R._phat_hien_loai_lam_mat('Máy biến áp dầu 3Pha 250KVA') == 'dau')
    test('T1-02', 'Nhận diện "khô" -> kho', R._phat_hien_loai_lam_mat('Máy biến áp khô KP 160kVA') == 'kho')
    test('T1-03', 'Không có từ khoá nào -> None (không đoán)',
         R._phat_hien_loai_lam_mat('Hợp bộ đo lường MOF 24kV') is None)
    test('T1-04', 'Chuỗi rỗng/None -> không crash, trả None',
         R._phat_hien_loai_lam_mat('') is None and R._phat_hien_loai_lam_mat(None) is None)
    test('T1-05', 'Nhận diện 1Pha -> "1"', R._phat_hien_so_pha('Máy biến áp dầu 1Pha 15KVA') == '1')
    test('T1-06', 'Nhận diện 3Pha -> "3"', R._phat_hien_so_pha('Máy biến áp dầu 3Pha 250KVA') == '3')
    test('T1-07', 'Không có số pha -> None', R._phat_hien_so_pha('Máy biến áp khô KP 160kVA') is None)

    # ============================================================ 2. khoi_chung_may_bien_ap — nội dung đúng loại
    row_dau = {'outline_id': 'outline_may_bien_ap', 'ten_goc': 'Máy biến áp dầu 3Pha 250KVA 22/0.4KV Loại Amorphous'}
    row_kho = {'outline_id': 'outline_may_bien_ap', 'ten_goc': 'Máy biến áp khô KP 160kVA 22/0,4kV'}
    row_khac = {'outline_id': 'outline_do_luong', 'ten_goc': 'Máy biến áp dầu đo lường'}  # tên có "dầu" nhưng SAI outline
    row_khong_ro = {'outline_id': 'outline_may_bien_ap', 'ten_goc': 'Vỏ mạ kẽm nhúng nóng MBA 1P 15KVA'}

    khoi_dau = R.khoi_chung_may_bien_ap(row_dau)
    khoi_kho = R.khoi_chung_may_bien_ap(row_kho)

    test('T2-01', 'Khối dầu CÓ nhắc ONAN (nguyên lý làm mát đúng cho dầu)', 'ONAN' in khoi_dau)
    test('T2-02', 'Khối dầu KHÔNG nhắc AN/AF (nguyên lý của máy khô, tránh lẫn)', 'AN/AF' not in khoi_dau and '(AF)' not in khoi_dau)
    test('T2-03', 'Khối khô CÓ nhắc "AN/AF" (nguyên lý làm mát đúng cho khô)',
         'AN/AF' in khoi_kho)
    test('T2-04', 'Khối khô KHÔNG nhắc ONAN/dầu cách điện tuần hoàn (nguyên lý của máy dầu, tránh lẫn)',
         'ONAN' not in khoi_kho)
    test('T2-05', 'Khối khô CÓ nhắc không dùng dầu (đặc điểm phân biệt chính)', 'không dùng dầu' in khoi_kho)
    test('T2-06', 'Khối dầu và khối khô khác tiêu chuẩn trích dẫn (dầu: TCVN 6306; khô thêm IEC 60076-11)',
         'IEC 60076-11' in khoi_kho and 'IEC 60076-11' not in khoi_dau)

    # ============================================================ 3. An toàn — không đoán khi mơ hồ / sai outline
    test('T3-01', 'outline KHÁC outline_may_bien_ap -> LUÔN rỗng dù tên có "dầu" (không áp nhầm sang đo lường)',
         R.khoi_chung_may_bien_ap(row_khac) == '')
    test('T3-02', 'Không nhận diện được dầu/khô (VD "Vỏ mạ kẽm...") -> rỗng, KHÔNG đoán',
         R.khoi_chung_may_bien_ap(row_khong_ro) == '')
    test('T3-03', 'Thiếu hẳn field outline_id/ten_goc -> không crash, trả rỗng', R.khoi_chung_may_bien_ap({}) == '')

    # ============================================================ 4. Wiring thật vào dung_bai_html()
    ai_data = {'meta_title': 'T', 'meta_description': 'M', 'intro_html': '<p>i</p>'}
    site_cfg = {'ten': 'Test', 'hotline': '0900000000'}
    row_full = dict(row_dau, ma_goc='MBTTEST', profile_id='may_bien_ap_do_luong', content_type='product',
                    thuong_hieu='MBT', quy_cach='', dvt='Máy', cong_suat='250', cap_dien_ap='22/0.4')
    bai = R.dung_bai_html(row_full, ai_data, site_cfg)
    test('T4-01', 'dung_bai_html() CÓ chèn khối máy biến áp DẦU (nhắc ONAN) khi outline đúng + nhận diện được loại',
         'ONAN' in bai['html'])

    row_full_dl = dict(row_khac, ma_goc='DLTEST', profile_id='may_bien_ap_do_luong', content_type='product',
                       thuong_hieu='X', quy_cach='', dvt='Bộ')
    bai_dl = R.dung_bai_html(row_full_dl, ai_data, site_cfg)
    test('T4-02', 'dung_bai_html() KHÔNG chèn khối này cho outline_do_luong dù tên có chữ "dầu"',
         'Về máy biến áp' not in bai_dl['html'])

    # ============================================================ 5. Quét toàn bộ MASTER thật — không dòng nào bị gán sai
    if os.path.exists(MASTER_GOC):
        r = N.import_4_profile(MASTER_GOC, chi_profile='may_bien_ap_do_luong')
        rows = r['may_bien_ap_do_luong']['rows']
        mba_rows = [x for x in rows if x['outline_id'] == 'outline_may_bien_ap']
        do_luong_rows = [x for x in rows if x['outline_id'] == 'outline_do_luong']
        test('T5-01', f'Quét {len(mba_rows)} dòng outline_may_bien_ap thật: không dòng nào crash', True)
        sai_lan = [x for x in mba_rows if 'dầu' in x['ten_goc'].lower()
                   and 'ONAN' not in R.khoi_chung_may_bien_ap(x)]
        test('T5-02', f'Mọi dòng có "dầu" trong tên đều ra khối ONAN đúng (lệch: {len(sai_lan)})', len(sai_lan) == 0)
        sai_lan2 = [x for x in mba_rows if 'khô' in x['ten_goc'].lower()
                    and 'không dùng dầu' not in R.khoi_chung_may_bien_ap(x)]
        test('T5-03', f'Mọi dòng có "khô" trong tên đều ra khối đúng (lệch: {len(sai_lan2)})', len(sai_lan2) == 0)
        test('T5-04', f'{len(do_luong_rows)} dòng outline_do_luong: KHÔNG dòng nào có khối máy biến áp',
             all(R.khoi_chung_may_bien_ap(x) == '' for x in do_luong_rows))
    else:
        print('  (Bỏ qua mục 5 — thiếu MASTER_4_PROFILE_SAN_PHAM.xlsx để quét thật)')

    tong = len(KET_QUA)
    dat = sum(1 for _, _, ok in KET_QUA if ok)
    print(f'\nTỔNG VER 4.9.7 PATCH: {dat}/{tong} PASS')
    if dat != tong:
        sys.exit(1)


if __name__ == '__main__':
    main()
