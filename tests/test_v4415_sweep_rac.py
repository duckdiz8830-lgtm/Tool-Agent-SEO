# -*- coding: utf-8 -*-
"""Ver 4.4.1.5 — test dọn rác bài đã đăng.

HTML mẫu lấy NGUYÊN VĂN từ bài production maybienapvn.vn (MBT1P50A2608),
không phải fixture tự bịa — vì bug gốc là do div lồng div, mẫu bịa gọn
gàng sẽ không tái hiện được.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sweep_rac as SR
import xu_ly_anh as X


# --- nguyên văn từ bài đang sống, ô "Ảnh 2" nằm trong section Thông số ---
O_ANH_2 = (
    '<div class="snl-cho-anh"><span class="snl-cho-anh-nhan">Ảnh 2</span>'
    '<div class="snl-cho-anh-ten">Ảnh biển máy (nameplate)</div>'
    '<p class="snl-cho-anh-mo-ta">Chụp thẳng tấm nhãn kim loại trên thân máy, '
    'đủ sáng, đọc rõ chữ. Ảnh này chứng minh thông số phía trên là số thật, '
    'không phải chép catalogue.</p>'
    '<p class="snl-cho-anh-kt">Tỷ lệ 3:2 ngang · tối thiểu 1200×800px</p></div>'
    '<p class="snl-anh-caption">Biển thông số máy, ảnh chụp thực tế</p>'
)
O_ANH_5 = (
    '<div class="snl-cho-anh"><span class="snl-cho-anh-nhan">Ảnh 5</span>'
    '<div class="snl-cho-anh-ten">Ảnh giao hàng / vận chuyển</div>'
    '<p class="snl-cho-anh-mo-ta">Máy trên xe cẩu, đang hạ xuống bệ. '
    'Có công nhân càng tốt.</p>'
    '<p class="snl-cho-anh-kt">Tỷ lệ 3:2 ngang · tối thiểu 1200×800px</p></div>'
    '<p class="snl-anh-caption">Vận chuyển và bàn giao</p>'
)
ANH_THAT = (
    '<figure class="snl-hinh" data-snl-role="hero">'
    '<img src="https://maybienapvn.vn/wp-content/uploads/2026/08/x-hero.webp" '
    'alt="Máy biến áp dầu 1Pha 50KVA" width="720" height="960" '
    'loading="lazy" class="snl-anh"></figure>'
)
BANG = ('<table class="snl-specs-table"><tbody><tr>'
        '<th class="snl-specs-th">Mã hàng</th>'
        '<td class="snl-specs-td">MBT1P50A2608</td></tr></tbody></table>')


class TestDonRac(unittest.TestCase):

    def test_xoa_duoc_o_cho_anh_du_co_div_long(self):
        """Bug gốc: div.snl-cho-anh chứa div.snl-cho-anh-ten bên trong.
        Regex '.*?</div>' ngây thơ sẽ dừng ở </div> của div CON, để lại
        đuôi rác. Neo theo p.snl-cho-anh-kt mới cắt đúng."""
        html = f'<section id="thong-so">{BANG}{O_ANH_2}</section>'
        sach, da_xoa = SR.don_rac_bai(html)
        self.assertNotIn('snl-cho-anh', sach)
        self.assertNotIn('cho-anh-ten', sach)      # không sót div con
        self.assertNotIn('Tỷ lệ 3:2', sach)
        self.assertNotIn('không phải chép catalogue', sach)
        self.assertEqual(da_xoa.get('cho_anh'), 1)

    def test_xoa_ca_caption_di_kem(self):
        sach, _ = SR.don_rac_bai(f'<div>{O_ANH_2}</div>')
        self.assertNotIn('Biển thông số máy', sach)

    def test_xoa_nhieu_o_trong_mot_bai(self):
        html = f'<div>{BANG}{O_ANH_2}<p>văn xuôi</p>{O_ANH_5}</div>'
        sach, da_xoa = SR.don_rac_bai(html)
        self.assertNotIn('snl-cho-anh', sach)
        self.assertEqual(da_xoa.get('cho_anh'), 2)
        self.assertIn('văn xuôi', sach)

    def test_khong_dung_toi_anh_that(self):
        html = f'<div>{ANH_THAT}{O_ANH_2}{BANG}</div>'
        sach, _ = SR.don_rac_bai(html)
        self.assertIn('x-hero.webp', sach)
        self.assertIn('data-snl-role="hero"', sach)
        self.assertIn('snl-specs-table', sach)
        self.assertIn('MBT1P50A2608', sach)

    def test_bai_sach_khong_bi_doi(self):
        html = f'<div>{ANH_THAT}{BANG}<p>nội dung</p></div>'
        sach, da_xoa = SR.don_rac_bai(html)
        self.assertEqual(sach, html)
        self.assertEqual(da_xoa, {})

    def test_chay_lai_lan_hai_khong_doi_gi_them(self):
        """Idempotent — bấm nút 2 lần không được hỏng bài."""
        html = f'<div>{ANH_THAT}{O_ANH_2}{BANG}</div>'
        lan1, _ = SR.don_rac_bai(html)
        lan2, da_xoa2 = SR.don_rac_bai(lan1)
        self.assertEqual(lan1, lan2)
        self.assertEqual(da_xoa2, {})

    def test_xoa_marker_va_comment_cu(self):
        html = ('<div><!--SNL_IMAGE_SLOT:bien_may-->'
                '<!-- ẢNH 3 — thay URL_ANH vào src -->' + BANG + '</div>')
        sach, da_xoa = SR.don_rac_bai(html)
        self.assertNotIn('SNL_IMAGE_SLOT', sach)
        self.assertNotIn('URL_ANH', sach)
        self.assertIn('MBT1P50A2608', sach)

    def test_input_rong(self):
        self.assertEqual(SR.don_rac_bai(''), ('', {}))
        self.assertEqual(SR.don_rac_bai(None), ('', {}))


class TestLuongDangAnh(unittest.TestCase):
    """chen_anh_vao_bai phải sạch KỂ CẢ khi không có ảnh nào —
    đây chính là case production đã lọt: role thiếu file thì
    _thay_slot_legacy bị bỏ qua, ô ở nguyên."""

    def test_khong_co_anh_nao_van_sach(self):
        html = f'<div>{BANG}{O_ANH_2}{O_ANH_5}</div>'
        ra = X.chen_anh_vao_bai(html, [])
        self.assertNotIn('snl-cho-anh', ra)
        self.assertNotIn('Tỷ lệ 3:2', ra)
        self.assertIn('MBT1P50A2608', ra)

    def test_co_anh_mot_phan_van_sach(self):
        """3/5 role có ảnh — 2 role còn lại không được để ô lại."""
        html = f'<div>{BANG}{O_ANH_2}{O_ANH_5}</div>'
        anh = [{'vai_tro': 'hero', 'url': 'https://x/a.webp',
                'alt': 'a', 'rong': 720, 'cao': 960}]
        ra = X.chen_anh_vao_bai(html, anh)
        self.assertNotIn('snl-cho-anh', ra)
        self.assertIn('a.webp', ra)


if __name__ == '__main__':
    unittest.main(verbosity=2)
