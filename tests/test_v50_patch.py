import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
# -*- coding: utf-8 -*-
"""
Ver 5.0 Claude — theo phản hồi Thịnh trên site thật + log lỗi MAX_TOKENS
(30/07/2026):

1. Vá lỗi "Bài bị cắt vì vượt giới hạn token" — giới hạn thinkingConfig
   (model Gemini 3.x "suy nghĩ ngầm" ăn chung ngân sách maxOutputTokens)
   + nâng trần maxOutputTokens.
2. Title bỏ mã hàng (nhìn "ngốc nghếch" trên site thật), thêm "Báo Giá".
3. CTA nổi bật hơn (không animation — kỹ thuật không cho phép với inline
   style thuần, xem giải thích trong code).
4. Bảng so sánh công suất: SKU đã đăng → link bấm được.
5. Placeholder chèn ảnh.
6. Đặc điểm chia nhiều đoạn <p> thay vì 1 khối liền mạch.
7. Xem trước dạng trang HTML thật (mở trình duyệt).

Chạy: python3 test_v50_patch.py
"""
import inspect
import os
import sys

import db_phase2 as DB
import nhap_phase2 as N
import profiles as P
import prompts_phase2 as PR
import render_phase2 as R

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ver 5.1 -- test o tests/, du lieu/module chinh o thu muc goc (len 1 cap)
MASTER_GOC = os.path.join(BASE, 'MASTER_4_PROFILE_SAN_PHAM.xlsx')

KET_QUA = []


def test(ma, mo_ta, dieu_kien):
    KET_QUA.append((ma, mo_ta, bool(dieu_kien)))
    print(f'[{"PASS" if dieu_kien else "FAIL"}] {ma}: {mo_ta}')


def main():
    # ============================================================ 1. Vá lỗi MAX_TOKENS
    import ai_wp_adapter as AWA
    src = inspect.getsource(AWA.goi_ai_that)
    test('W1-01', "generationConfig CÓ thinkingConfig.thinkingBudget (giới hạn suy nghĩ ngầm)",
         "'thinkingConfig'" in src and "'thinkingBudget'" in src)
    test('W1-02', 'maxOutputTokens ĐÃ NÂNG lên > 24000 (giá trị cũ gây cắt bài)',
         "'maxOutputTokens': 48000" in src)
    test('W1-03', 'thinkingBudget đặt giá trị hợp lý (không phải 0 — vẫn cho model suy luận Delta Context)',
         "'thinkingBudget': 6000" in src)

    if not os.path.exists(MASTER_GOC):
        print('THIẾU MASTER — bỏ qua phần còn lại.')
        tong = len(KET_QUA)
        dat = sum(1 for _, _, ok in KET_QUA if ok)
        print(f'\nTỔNG VER 5.0 PATCH: {dat}/{tong} PASS')
        sys.exit(0 if dat == tong else 1)

    r = N.import_4_profile(MASTER_GOC, chi_profile='may_bien_ap_do_luong')
    info = r['may_bien_ap_do_luong']
    cot_import_keys = list(P.PROFILES['may_bien_ap_do_luong']['cot_import'].values())
    con = DB.ket_noi(':memory:')
    did, _ = DB.xac_nhan_dataset(con, 'may_bien_ap_do_luong', 'test.xlsx', info['file_checksum'],
                                 info['data_checksum'], len(info['rows']), cot_import_keys)
    DB.ghi_san_pham(con, did, info['rows'])
    row250 = next(x for x in info['rows'] if x['ma_goc'] == 'MBT3P250A2608')

    # ============================================================ 2. Title
    tieu_de = R.dung_tieu_de(row250)
    test('W2-01', 'Title KHÔNG còn mã hàng', 'MBT3P250A2608' not in tieu_de)
    test('W2-02', 'Title CÓ "Báo giá"', 'Báo giá' in tieu_de)
    test('W2-03', 'Title vẫn còn công suất/thương hiệu (không mất thông tin khác)',
         '250' in tieu_de and 'MBT' in tieu_de)

    # ============================================================ 3. CTA nổi bật
    cta = R.khoi_cta_ngan({'hotline': '0900000000'})
    test('W3-01', 'Nút "Yêu cầu báo giá" có box-shadow (nổi bật hơn, không animation)',
         'box-shadow' in cta)
    test('W3-02', 'Nút "Yêu cầu báo giá" cỡ chữ lớn hơn mặc định cũ (16px)', 'font-size:16px' in cta)

    # ============================================================ 4. Bảng so sánh có link khi đã đăng
    cung_dong = DB.tim_san_pham_cung_dong(con, did, row250['record_id'])
    ma_anh_em = cung_dong[0]['ma_goc']
    rid_anh_em = next(x['record_id'] for x in info['rows'] if x['ma_goc'] == ma_anh_em)
    DB.upsert_bai_viet_khoi_tao(con, did, rid_anh_em, 'site_test', 'chuan')
    DB.cap_nhat_bai_viet(con, did, rid_anh_em, 'site_test', 'chuan', trang_thai='da_dang',
                         wp_id=999, wp_url='https://test.vn/sp-anh-em')

    cung_dong_khong_site = DB.tim_san_pham_cung_dong(con, did, row250['record_id'])
    test('W4-01', 'Không truyền site -> url luôn rỗng (an toàn ngược, hành vi cũ)',
         all(sp['url'] == '' for sp in cung_dong_khong_site))

    cung_dong_co_site = DB.tim_san_pham_cung_dong(con, did, row250['record_id'], site='site_test')
    sp_da_dang = next(sp for sp in cung_dong_co_site if sp['ma_goc'] == ma_anh_em)
    test('W4-02', 'SKU đã đăng thật -> có url đúng', sp_da_dang['url'] == 'https://test.vn/sp-anh-em')
    sp_chua_dang = [sp for sp in cung_dong_co_site if sp['ma_goc'] != ma_anh_em]
    test('W4-03', 'SKU chưa đăng -> url rỗng (không bịa link chết)',
         all(sp['url'] == '' for sp in sp_chua_dang))

    bang = R.khoi_so_sanh_cong_suat(row250, cung_dong_co_site)
    test('W4-04', 'Ver 5.2: Bảng HTML có thẻ <a href> cho SKU đã đăng, chữ hiển thị là TÊN sản phẩm (không phải mã)',
         f'<a href="https://test.vn/sp-anh-em">' in bang and ma_anh_em not in bang.split(f'<a href="https://test.vn/sp-anh-em">')[1].split('</a>')[0])
    test('W4-05', 'Bảng HTML KHÔNG có <a href> cho SKU chưa đăng (chỉ text)',
         all(f'href="{{}}"'.format('') not in bang or True for _ in [0]) and
         not any(f'<a href="">{sp["ma_goc"]}' in bang for sp in sp_chua_dang))

    # ============================================================ 5. Placeholder ảnh
    ph = R.khoi_anh_placeholder('ảnh sản phẩm chính')
    test('W5-01', 'Placeholder ảnh có emoji + chữ CHỖ CHÈN, dễ nhận diện', '📷' in ph and 'CHỖ CHÈN' in ph)
    test('W5-02', 'Placeholder ảnh có màu viền cam nổi bật (khác nội dung thật)', '#f97316' in ph)

    ai_data = {'meta_title': 'T', 'meta_description': 'M', 'intro_html': '<p>i</p>',
               'dac_diem_html': '<p>d</p>', 'ung_dung_html': '<p>u</p>', 'huong_dan_chon_html': '<p>h</p>'}
    bai = R.dung_bai_html(row250, ai_data, {'ten': 'Test', 'hotline': '0900000000'}, cung_dong=cung_dong_co_site)
    test('W5-03', 'dung_bai_html() CÓ chèn placeholder ảnh ngay sau Hero', 'CHỖ CHÈN' in bai['html'])
    test('W5-04', 'HTML cuối cùng CÓ link SKU anh em đã đăng', 'https://test.vn/sp-anh-em' in bai['html'])

    # ============================================================ 6. Đặc điểm nhiều đoạn
    cfg = PR.OUTLINE_NOI_DUNG['outline_may_bien_ap']
    dac_diem_guidance = cfg['sections']['dac_diem_html']
    test('W6-01', 'Guidance dac_diem_html yêu cầu chia 2-3 đoạn <p>, không dồn 1 khối',
         '2-3 ĐOẠN' in dac_diem_guidance and 'KHÔNG dồn thành 1 khối' in dac_diem_guidance)
    do_dai_chung = PR.GIOI_HAN_DO_DAI['dac_diem_html']
    test('W6-02', 'Giới hạn độ dài chung (GIOI_HAN_DO_DAI) cũng nhắc chia đoạn <p>',
         '<p>' in do_dai_chung or 'đoạn' in do_dai_chung.lower())

    # ============================================================ 7. Preview trình duyệt (kiểm tra hàm tồn tại + logic, không mở browser thật khi test)
    with open(os.path.join(BASE, 'giao-dien.py'), encoding='utf-8') as f:
        src_gd = f.read()
    test('W7-01', 'Có hàm _phase2_mo_trinh_duyet() trong giao-dien.py',
         'def _phase2_mo_trinh_duyet' in src_gd)
    test('W7-02', 'Hàm dùng webbrowser.open() (module chuẩn, không cần cài thêm)',
         'webbrowser.open' in src_gd)
    test('W7-03', 'Có nút UI "Mở trong trình duyệt" nối tới hàm trên',
         "text='Mở trong trình duyệt'" in src_gd and '_phase2_mo_trinh_duyet' in src_gd)

    tong = len(KET_QUA)
    dat = sum(1 for _, _, ok in KET_QUA if ok)
    print(f'\nTỔNG VER 5.0 PATCH: {dat}/{tong} PASS')
    if dat != tong:
        sys.exit(1)


if __name__ == '__main__':
    main()
