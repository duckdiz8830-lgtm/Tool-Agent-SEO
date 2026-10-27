import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
# -*- coding: utf-8 -*-
"""
Ver 4.9.6 Claude — test patch, theo phản hồi thật của Thịnh trên site
maybienapvn.vn (ảnh chụp 29/07/2026):

1. Schema JSON-LD không còn nhét thẳng vào 'html' (bug thật: WordPress kses
   xoá thẻ <script>, để lại JSON hiện ra thành chữ trên trang).
2. Bỏ khối "Thông tin cần cung cấp để nhận báo giá" (giảm lead).
3. Rule prompt không còn ép AI viết câu công thức cứng "gửi bản vẽ...".
4. Slug có từ khoá SEO từ tiêu đề, không chỉ mã hàng suông.
5. ai_wp_adapter: Ver 4.4 gửi 'slug' khi update Woo để áp công thức SEO mới;
   WordPress post thường giữ policy cũ.

Chạy: python3 test_v496_patch.py
"""
import inspect
import sys

import ai_wp_adapter as AWA
import prompts_phase2 as PR
import render_phase2 as R

KET_QUA = []


def test(ma, mo_ta, dieu_kien):
    KET_QUA.append((ma, mo_ta, bool(dieu_kien)))
    print(f'[{"PASS" if dieu_kien else "FAIL"}] {ma}: {mo_ta}')


def main():
    row = {
        'profile_id': 'may_bien_ap_do_luong', 'outline_id': 'outline_may_bien_ap',
        'content_type': 'product',
        'ma_goc': 'MBT3P250A2608', 'ten_goc': 'Máy biến áp dầu 3Pha 250KVA 22/0.4KV Loại Amorphous, kiểu kín, sứ gốm',
        'thuong_hieu': 'MBT', 'quy_cach': '', 'dvt': 'Máy', 'cong_suat': '250', 'cap_dien_ap': '22/0.4',
    }
    ai_data = {'meta_title': 'T', 'meta_description': 'M', 'intro_html': '<p>i</p>',
               'dac_diem_html': '<p>d</p>', 'ung_dung_html': '<p>u</p>',
               'huong_dan_chon_html': '<p>h</p>'}
    site_cfg = {'ten': 'Máy Biến Áp Việt Nam', 'hotline': '0903924986', 'zalo': '0903924986'}

    bai = R.dung_bai_html(row, ai_data, site_cfg)

    # ============================================================ 1. Schema
    test('S1-01', 'Schema KHÔNG còn trong html (không còn "application/ld+json")',
         'application/ld+json' not in bai['html'])
    test('S1-02', 'Schema KHÔNG còn trong html (không còn "@context" lộ ra thành chữ)',
         '@context' not in bai['html'])
    test('S1-03', "dung_bai_html() trả riêng key 'schema' (dict) đúng nội dung Product",
         isinstance(bai.get('schema'), dict) and bai['schema'].get('@type') == 'Product')

    # ============================================================ 2. Checklist báo giá
    test('S2-01', 'Bỏ khối "Thông tin cần cung cấp để nhận báo giá" khỏi bài',
         'Thông tin cần cung cấp để nhận báo giá' not in bai['html'])

    # ============================================================ 3. Content tự nhiên hơn
    test('S3-01', 'QUY_TAC_CHUNG KHÔNG còn ép câu công thức cứng "để được tư vấn đúng mã sản phẩm"',
         'để được tư vấn đúng mã sản phẩm' not in PR.QUY_TAC_CHUNG)
    test('S3-02', 'QUY_TAC_CHUNG CÓ cảnh báo rõ cấm công thức "Quý khách vui lòng gửi bản vẽ"',
         'Quý khách vui lòng gửi bản vẽ' in PR.QUY_TAC_CHUNG and 'TUYỆT ĐỐI KHÔNG dùng công thức cố định' in PR.QUY_TAC_CHUNG)

    # ============================================================ 4. Slug SEO
    slug = bai['slug']
    test('S4-01', f'Slug CÓ từ khoá sản phẩm, không chỉ mã hàng suông (thực tế: {slug})',
         'may-bien-ap' in slug and slug != 'mbt3p250a2608-chuan')
    test('S4-02', 'Slug MBA 3.9 BỎ mã hàng theo công thức SEO mới',
         'mbt3p250a2608' not in slug)
    test('S4-03', 'Slug MBA 3.9 BỎ suffix chuan theo yêu cầu C4',
         not slug.endswith('-chuan'))
    row_khong_ten = {'ma_goc': 'ABC123'}
    slug2 = R.dung_slug(row_khong_ten, 'chuan')
    test('S4-04', 'Slug KHÔNG crash khi record không có ten_goc (fallback về mã hàng)',
         slug2 == 'abc123-chuan')

    # ============================================================ 5. Ver 4.4: Woo update phải gửi slug
    src_woo = inspect.getsource(AWA.dang_woo_that)
    src_wp = inspect.getsource(AWA.dang_wp_that)
    test('S5-01', "dang_woo_that(): Ver 4.4 gán slug ngoài nhánh CREATE để UPDATE cũng đổi slug",
         "if slug:" in src_woo and "goi['slug'] = slug" in src_woo)
    test('S5-02', "dang_wp_that(): CHỈ gán goi['slug'] BÊN TRONG nhánh 'if da_co is None' (không resend khi update)",
         "if da_co is None:\n            goi['slug'] = slug" in src_wp)
    test('S5-03', "dang_woo_that(): payload nền vẫn không hardcode slug; slug chỉ thêm khi tham số có giá trị",
         "goi = {'name': title, 'type': 'simple'" in src_woo and "if slug:" in src_woo and "goi['slug'] = slug" in src_woo)
    test('S5-04', "dang_wp_that(): 'goi' KHÔNG khởi tạo sẵn key 'slug'",
         "goi = {'title': title, 'content': content" in src_wp)

    tong = len(KET_QUA)
    dat = sum(1 for _, _, ok in KET_QUA if ok)
    print(f'\nTỔNG VER 4.9.6 PATCH: {dat}/{tong} PASS')
    if dat != tong:
        sys.exit(1)


if __name__ == '__main__':
    main()
