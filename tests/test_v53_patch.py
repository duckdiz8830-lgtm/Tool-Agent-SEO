# -*- coding: utf-8 -*-
"""
Ver 5.3 Claude — thực thi "Giai đoạn 1" trong DE-XUAT-TOAN-DIEN-LOTECH-
AUTOPOST.md (7 hạng mục code ngay, không chờ dữ liệu/quyết định gì thêm):

B5. Nút "Cập nhật lại bài đã đăng" — bỏ qua bước skip khi bật, tận dụng
    cơ chế UPDATE-theo-SKU/wp_id sẵn có.
B6. Hard Block chặn nội dung cốt lõi -> thất bại NGAY, không đốt hết cặp
    dự phòng cho 1 sản phẩm (lỗi mạng/429 vẫn thử tiếp như cũ).
C6. Khối "Về lõi Silic/Amorphous" — kiến thức ngành chung.
C7. Khối "Bảo trì & lắp đặt" — tách riêng dầu/khô.
C8. Rule bullet points + in đậm trong prompt.
C9. "Sản phẩm liên quan" dạng grid thẻ.
C10. Nút "Tải Catalogue" — field optional, ẩn tới khi có link thật.

Chạy: python3 tests/test_v53_patch.py (từ thư mục gốc)
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))

import inspect
import os
import sys
from unittest.mock import patch

import ai_wp_adapter as AWP
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
    # ============================================================ B5 — nút cập nhật lại bài đã đăng
    with open(os.path.join(BASE, 'giao-dien.py'), encoding='utf-8') as f:
        src_gd = f.read()
    test('Y-B5-01', 'Có biến v3_cho_phep_cap_nhat (checkbox UI)', 'v3_cho_phep_cap_nhat' in src_gd)
    test('Y-B5-02', 'Vòng lặp batch record CÓ nhánh "không skip khi cho_phep_cap_nhat"',
         'da_dang_truoc and not cho_phep_cap_nhat' in src_gd)
    test('Y-B5-03', 'Log rõ ràng [CẬP NHẬT LẠI] khi ghi đè bài cũ', '[CẬP NHẬT LẠI]' in src_gd)
    test('Y-B5-04', 'Mặc định checkbox là TẮT (an toàn ngược, không đổi hành vi cũ nếu không bật)',
         'tk.BooleanVar(value=False)' in src_gd and 'v3_cho_phep_cap_nhat' in src_gd)

    # ============================================================ B6 — Hard Block fail nhanh
    row = {'profile_id': 'may_bien_ap_do_luong', 'outline_id': 'outline_may_bien_ap',
          'ma_goc': 'X', 'ten_goc': 'Test', 'thuong_hieu': 'T', 'cong_suat': '10 kVA'}

    def fake_luon_bi_chan(row, mau, model, site_cfg=None, timeout=120, api_key=None):
        return {'ok': True, 'data': {'dac_diem_html': 'Bịa số 999999kVA không có trong dữ liệu nguồn.'}}

    with patch('ai_wp_adapter.goi_ai_that', side_effect=fake_luon_bi_chan) as mock_fn:
        kq, vi_pham = AWP.goi_ai_co_du_phong(row, 'chuan', [('k1', 'm1'), ('k2', 'm2'), ('k3', 'm3')])
    test('Y-B6-01', f'Hard Block chặn nội dung cốt lõi -> CHỈ gọi AI 1 lần (thực tế {mock_fn.call_count}), không đốt hết 3 cặp',
         mock_fn.call_count == 1)
    test('Y-B6-02', 'Trả về ok=False, da_thu=1 khi bị Hard Block chặn ngay từ cặp đầu', kq['ok'] is False and kq.get('da_thu') == 1)

    dem = {'n': 0}

    def fake_loi_mang_roi_thanh_cong(row, mau, model, site_cfg=None, timeout=120, api_key=None):
        dem['n'] += 1
        if dem['n'] < 3:
            return {'ok': False, 'loi': 'Lỗi mạng tạm thời'}
        return {'ok': True, 'data': {'dac_diem_html': 'Công suất 10 kVA.'}}

    with patch('ai_wp_adapter.goi_ai_that', side_effect=fake_loi_mang_roi_thanh_cong) as mock_fn2:
        kq2, _ = AWP.goi_ai_co_du_phong(row, 'chuan', [('k1', 'm1'), ('k2', 'm2'), ('k3', 'm3')])
    test('Y-B6-03', f'Lỗi mạng/429 VẪN thử tiếp như cũ (thực tế {mock_fn2.call_count} lần, không bị fail-fast nhầm)',
         mock_fn2.call_count == 3 and kq2['ok'] is True)

    # ============================================================ C6/C7 — khối lõi + bảo trì
    if not os.path.exists(MASTER_GOC):
        print('THIẾU MASTER — bỏ qua phần cần import thật.')
    else:
        r = N.import_4_profile(MASTER_GOC, chi_profile='may_bien_ap_do_luong')
        rows = r['may_bien_ap_do_luong']['rows']
        test('Y-IMPORT-01', f'Import MASTER KHÔNG crash dù thêm cột catalogue_pdf_url mới (thực tế {len(rows)} dòng)',
             len(rows) > 0)

    row_silic = {'outline_id': 'outline_may_bien_ap', 'ten_goc': 'Máy biến áp dầu 3Pha 2000KVA Loại Silic'}
    row_amor = {'outline_id': 'outline_may_bien_ap', 'ten_goc': 'Máy biến áp dầu 1Pha 15KVA Loại Amorphous'}
    row_kho = {'outline_id': 'outline_may_bien_ap', 'ten_goc': 'Máy biến áp khô KP 160kVA'}
    row_vo = {'outline_id': 'outline_vo_may_bien_ap', 'ten_goc': 'Vỏ mạ kẽm nhúng nóng MBA'}

    test('Y-C6-01', 'Khối "Về lõi" hiện đúng cho Silic', 'lõi thép Silic' in R.khoi_ve_loi(row_silic).lower()
         or 'Silic' in R.khoi_ve_loi(row_silic))
    test('Y-C6-02', 'Khối "Về lõi" hiện đúng cho Amorphous', 'Amorphous' in R.khoi_ve_loi(row_amor))
    test('Y-C6-03', 'KHÔNG có số % nào trong khối lõi (tránh lặp lỗi CAPEX bịa)',
         '%' not in R.khoi_ve_loi(row_silic) and '%' not in R.khoi_ve_loi(row_amor))
    test('Y-C6-04', 'Khối "Về lõi" RỖNG cho outline vỏ (vỏ không có lõi)', R.khoi_ve_loi(row_vo) == '')
    test('Y-C6-05', 'Khối "Về lõi" RỖNG khi không nhận diện được loại (không đoán)',
         R.khoi_ve_loi({'outline_id': 'outline_may_bien_ap', 'ten_goc': 'Máy biến áp ABC không rõ loại lõi'}) == '')

    test('Y-C7-01', 'Khối "Bảo trì" đúng nội dung dầu (nhắc dầu cách điện)', 'dầu cách điện' in R.khoi_bao_tri_lap_dat(row_silic))
    test('Y-C7-02', 'Khối "Bảo trì" đúng nội dung khô (nhắc vệ sinh bụi)', 'bụi' in R.khoi_bao_tri_lap_dat(row_kho))
    test('Y-C7-03', 'Khối "Bảo trì" RỖNG cho outline vỏ', R.khoi_bao_tri_lap_dat(row_vo) == '')

    # ============================================================ C8 — rule bullet/bold trong prompt
    import prompts_phase2 as PR
    test('Y-C8-01', 'QUY_TAC_CHUNG có rule 12 (định dạng bullet/in đậm)',
         '12. ĐỊNH DẠNG DỄ ĐỌC' in PR.QUY_TAC_CHUNG)
    test('Y-C8-02', 'Rule 12 nhắc <ul><li> và <strong>', '<ul>' in PR.QUY_TAC_CHUNG and '<strong>' in PR.QUY_TAC_CHUNG)
    test('Y-C8-03', 'ALLOWED_TAGS (sanitize) đã có sẵn strong/ul/li (không cần sửa whitelist)',
         'strong' in R.ALLOWED_TAGS and 'ul' in R.ALLOWED_TAGS and 'li' in R.ALLOWED_TAGS)

    # ============================================================ C9 — grid san pham lien quan
    ds = [{'ten': 'Máy biến áp dầu 1Pha 15KVA', 'url': 'https://x.vn/a'},
         {'ten': 'Máy biến áp dầu 1Pha 25KVA', 'url': 'https://x.vn/b'}]
    grid = R.khoi_san_pham_lien_quan(ds)
    test('Y-C9-01', 'Sản phẩm liên quan dùng CSS Grid (display:grid), không còn <ul><li>', 'display:grid' in grid)
    test('Y-C9-02', 'Grid vẫn chứa đủ link + tên sản phẩm', 'https://x.vn/a' in grid and 'https://x.vn/b' in grid)
    test('Y-C9-03', 'Rỗng khi không có sản phẩm liên quan nào', R.khoi_san_pham_lien_quan([]) == '')

    # ============================================================ C10 — nút catalogue
    test('Y-C10-01', 'Nút catalogue RỖNG khi row không có catalogue_pdf_url (MASTER hiện chưa có cột này)',
         R.khoi_nut_catalogue(row_silic) == '')
    row_co_pdf = dict(row_silic, catalogue_pdf_url='https://x.vn/mbt.pdf')
    test('Y-C10-02', 'Nút catalogue HIỆN đúng khi có link thật', 'https://x.vn/mbt.pdf' in R.khoi_nut_catalogue(row_co_pdf))
    test('Y-C10-03', "field 'Catalogue PDF URL' đã đăng ký OPTIONAL ở cả 4 profile (không phá import cũ)",
         all('catalogue_pdf_url' in P.PROFILES[pid]['cot_import'].values()
             and 'Catalogue PDF URL' not in (P.PROFILES[pid].get('cot_bat_buoc') or [])
             for pid in ('cap_dien', 'tu_va_thiet_bi_dong_cat', 'may_bien_ap_do_luong', 'phu_kien_va_khac')))

    # ============================================================ Wiring thật vào dung_bai_html
    ai_data = {'meta_title': 'T', 'meta_description': 'M', 'intro_html': '<p>i</p>',
              'dac_diem_html': '<p>d</p>', 'ung_dung_html': '<p>u</p>', 'huong_dan_chon_html': '<p>h</p>'}
    row_full = dict(row_silic, ma_goc='TEST123', profile_id='may_bien_ap_do_luong', content_type='product',
                    thuong_hieu='MBT', quy_cach='', dvt='Máy', cong_suat='2000')
    bai = R.dung_bai_html(row_full, ai_data, {'ten': 'Test', 'hotline': '0900000000'},
                          san_pham_lien_quan=ds)
    test('Y-WIRE-01', 'dung_bai_html() CÓ chèn khối "Về lõi"', 'Về lõi' in bai['html'])
    test('Y-WIRE-02', 'dung_bai_html() CÓ chèn khối "Bảo trì"', 'Lưu ý bảo trì' in bai['html'])
    test('Y-WIRE-03', 'dung_bai_html() dùng grid cho sản phẩm liên quan', 'display:grid' in bai['html'])
    test('Y-WIRE-04', 'dung_bai_html() KHÔNG hiện nút catalogue khi row không có link', 'Tải Catalogue' not in bai['html'])

    bai2 = R.dung_bai_html(dict(row_full, catalogue_pdf_url='https://x.vn/mbt.pdf'), ai_data,
                           {'ten': 'Test', 'hotline': '0900000000'})
    test('Y-WIRE-05', 'dung_bai_html() CÓ hiện nút catalogue khi row có link', 'Tải Catalogue' in bai2['html'])

    tong = len(KET_QUA)
    dat = sum(1 for _, _, ok in KET_QUA if ok)
    print(f'\nTỔNG VER 5.3 PATCH: {dat}/{tong} PASS')
    if dat != tong:
        sys.exit(1)


if __name__ == '__main__':
    main()
