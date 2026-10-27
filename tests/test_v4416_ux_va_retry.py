# -*- coding: utf-8 -*-
"""Ver 4.4.1.6 — test 7 sửa đổi.

Chuỗi lỗi 403 dùng NGUYÊN VĂN từ log production 13/08/2026, không bịa:
trang chặn thật bắt đầu bằng <!DOCTYPE html> rồi <meta viewport> — chính
kiểu nội dung mà giới hạn 200 ký tự cũ cắt thành vô nghĩa.
"""
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TRANG_403 = (
    '<!DOCTYPE html>\n<html style="height:100%">\n<head>\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, '
    'shrink-to-fit=no" />\n<title>403 Forbidden</title>\n'
    '<style>@media (prefers-color-scheme: dark){body{background:#111}}</style>\n'
    '</head><body>Access denied. Reference #18.2f1c3b17.1755100000.abcdef\n'
    'mod_security rule triggered</body></html>'
)


class GiaResponse:
    def __init__(self, ma, than='', headers=None, ct='text/html'):
        self.status_code = ma
        self.text = than
        self.headers = dict(headers or {})
        self.headers.setdefault('Content-Type', ct)
        self._json = None

    def json(self):
        if self._json is None:
            raise ValueError('không phải JSON')
        return self._json


class TestTomTatLoiHTTP(unittest.TestCase):
    """Mục 3 — log 403 không còn bị cắt ở 200 ký tự."""

    def setUp(self):
        import ai_wp_adapter as AWP
        self.AWP = AWP

    def test_lay_duoc_title_thay_vi_doctype(self):
        r = GiaResponse(403, TRANG_403, {'Server': 'cloudflare', 'CF-Ray': 'abc123-SIN'})
        ngan, day_du = self.AWP.tom_tat_loi_http(r)
        self.assertIn('403 Forbidden', ngan)          # đọc được <title>
        self.assertNotIn('<!DOCTYPE', ngan)           # không đổ HTML thô
        self.assertNotIn('viewport', ngan)

    def test_giu_dau_moi_ai_chan(self):
        r = GiaResponse(403, TRANG_403, {'Server': 'cloudflare', 'CF-Ray': 'abc123-SIN'})
        _, day_du = self.AWP.tom_tat_loi_http(r)
        self.assertIn('cloudflare', day_du)           # thủ phạm nằm ở header
        self.assertIn('CF-Ray', day_du)
        self.assertIn('mod_security', day_du)

    def test_403_giai_thich_dung_ban_chat(self):
        r = GiaResponse(403, TRANG_403)
        ngan, _ = self.AWP.tom_tat_loi_http(r)
        self.assertIn('TẦNG SERVER', ngan)
        self.assertIn('thử lại', ngan.lower())

    def test_401_khong_bi_nham_la_tam_thoi(self):
        r = GiaResponse(401, '{"code":"rest_forbidden"}', ct='application/json')
        r._json = {'code': 'rest_forbidden', 'message': 'Sorry'}
        ngan, _ = self.AWP.tom_tat_loi_http(r)
        self.assertIn('Application Password', ngan)

    def test_dai_hon_200_ky_tu(self):
        r = GiaResponse(403, TRANG_403)
        _, day_du = self.AWP.tom_tat_loi_http(r)
        self.assertGreater(len(day_du), 200)


class TestRetryUpload(unittest.TestCase):
    """Mục 2 — 403 lỗ chỗ phải tự thử lại, không bung ra mặt người dùng."""

    def _vá_requests(self, chuoi_ma):
        """chuoi_ma: list mã HTTP trả về lần lượt."""
        import ai_wp_adapter as AWP
        self.goi = []
        gia = types.ModuleType('requests')

        class _E(Exception):
            pass
        gia.exceptions = types.SimpleNamespace(RequestException=_E)

        def post(u, **k):
            ma = chuoi_ma[min(len(self.goi), len(chuoi_ma) - 1)]
            self.goi.append(ma)
            if ma in (200, 201):
                r = GiaResponse(ma, '{}', ct='application/json')
                r._json = {'id': 999, 'source_url': 'https://x/a.webp'}
                return r
            return GiaResponse(ma, TRANG_403)
        gia.post = post
        gia.get = lambda *a, **k: GiaResponse(200, '{}')
        sys.modules['requests'] = gia

        gia_A = types.ModuleType('autopost')
        gia_A._auth = lambda *a, **k: ('https://x', ('u', 'p'))
        gia_A.HEADERS = {}
        sys.modules['autopost'] = gia_A
        gia_C = types.ModuleType('cauhinh')
        gia_C.MA_SITE_VER3 = 'website'
        sys.modules['cauhinh'] = gia_C
        return AWP

    def tearDown(self):
        for m in ('requests', 'autopost', 'cauhinh'):
            sys.modules.pop(m, None)

    def test_403_roi_thanh_cong_thi_tu_lanh(self):
        AWP = self._vá_requests([403, 403, 200])
        kq = AWP.upload_anh_media(b'x', 'a.webp', so_lan_thu=4)
        self.assertTrue(kq['ok'])
        self.assertEqual(self.goi, [403, 403, 200])   # đã thử lại thật

    def test_403_lien_tuc_thi_bao_tam_thoi(self):
        AWP = self._vá_requests([403])
        kq = AWP.upload_anh_media(b'x', 'a.webp', so_lan_thu=2)
        self.assertFalse(kq['ok'])
        self.assertTrue(kq['tam_thoi'])               # để caller biết nên retry
        self.assertIn('403', kq['loi'])

    def test_401_dung_ngay_khong_thu_lai(self):
        AWP = self._vá_requests([401])
        kq = AWP.upload_anh_media(b'x', 'a.webp', so_lan_thu=4)
        self.assertFalse(kq['ok'])
        self.assertFalse(kq.get('tam_thoi'))
        self.assertEqual(len(self.goi), 1)            # KHÔNG đập server 4 lần


class TestGomLoiUX(unittest.TestCase):
    """Mục 5 — hộp thoại gom theo loại, không đổ HTML."""

    def test_gom_403_thanh_mot_dong(self):
        import tab_anh
        ra = tab_anh._gom_loi_anh([f'hero: 403 {TRANG_403}',
                                   f'bien_may: 403 {TRANG_403}',
                                   f'can_canh: 403 {TRANG_403}'])
        self.assertIn('3 ảnh', ra)
        self.assertIn('403', ra)
        self.assertNotIn('<!DOCTYPE', ra)
        self.assertNotIn('viewport', ra)

    def test_nhieu_loai_loi_tach_rieng(self):
        import tab_anh
        ra = tab_anh._gom_loi_anh(['a: 403 x', 'b: 429 y', 'c: Timeout z'])
        self.assertIn('403', ra)
        self.assertIn('429', ra)
        self.assertIn('Mạng', ra)

    def test_khong_co_loi_thi_khong_vo(self):
        import tab_anh
        self.assertIsInstance(tab_anh._gom_loi_anh([]), str)


class TestThuMucDuLieu(unittest.TestCase):
    """Mục 7 — DB/env ra thư mục chung, di cư an toàn."""

    def setUp(self):
        import shutil
        import tempfile
        self.tmp = tempfile.mkdtemp()
        self.cu = os.path.join(self.tmp, 'version-cu')
        self.chung = os.path.join(self.tmp, 'chung')
        os.makedirs(self.cu)
        os.environ['SONEALEO_DATA_DIR'] = self.chung
        self._shutil = shutil
        import thu_muc_du_lieu as TM
        TM._nhat_ky_di_cu.clear()
        self.TM = TM

    def tearDown(self):
        os.environ.pop('SONEALEO_DATA_DIR', None)
        self._shutil.rmtree(self.tmp, ignore_errors=True)

    def test_di_cu_file_tu_thu_muc_version(self):
        with open(os.path.join(self.cu, 'phase2-du-lieu.db'), 'wb') as f:
            f.write(b'DU-LIEU-CU')
        self.TM.chuan_bi(self.cu)
        dich = os.path.join(self.chung, 'phase2-du-lieu.db')
        self.assertTrue(os.path.isfile(dich))
        with open(dich, 'rb') as f:
            self.assertEqual(f.read(), b'DU-LIEU-CU')

    def test_KHONG_BAO_GIO_de_ban_cu_de_ban_moi(self):
        """Quan trọng nhất: thư mục chung luôn thắng. Đây đúng kiểu mất dữ
        liệu âm thầm mà bản cũ gây ra khi copy tay ngược chiều."""
        os.makedirs(self.chung, exist_ok=True)
        with open(os.path.join(self.chung, 'phase2-du-lieu.db'), 'wb') as f:
            f.write(b'DU-LIEU-MOI-DANG-DUNG')
        with open(os.path.join(self.cu, 'phase2-du-lieu.db'), 'wb') as f:
            f.write(b'DU-LIEU-CU-TU-2-THANG-TRUOC')
        self.TM.chuan_bi(self.cu)
        with open(os.path.join(self.chung, 'phase2-du-lieu.db'), 'rb') as f:
            self.assertEqual(f.read(), b'DU-LIEU-MOI-DANG-DUNG')

    def test_copy_ca_file_wal(self):
        for hau_to in ('', '-wal', '-shm'):
            with open(os.path.join(self.cu, 'phase2-du-lieu.db' + hau_to), 'wb') as f:
                f.write(b'x' + hau_to.encode())
        self.TM.chuan_bi(self.cu)
        for hau_to in ('', '-wal', '-shm'):
            self.assertTrue(os.path.isfile(
                os.path.join(self.chung, 'phase2-du-lieu.db' + hau_to)),
                'thiếu %s — mất giao dịch chưa checkpoint' % hau_to)

    def test_chay_lai_khong_di_cu_lan_hai(self):
        with open(os.path.join(self.cu, 'phase2-du-lieu.db'), 'wb') as f:
            f.write(b'A')
        self.TM.chuan_bi(self.cu)
        with open(os.path.join(self.chung, 'phase2-du-lieu.db'), 'wb') as f:
            f.write(b'DA-SUA-SAU-DO')
        self.TM.chuan_bi(self.cu)
        with open(os.path.join(self.chung, 'phase2-du-lieu.db'), 'rb') as f:
            self.assertEqual(f.read(), b'DA-SUA-SAU-DO')

    def test_giu_lai_ban_cu_khong_xoa(self):
        with open(os.path.join(self.cu, 'phase2-du-lieu.db'), 'wb') as f:
            f.write(b'A')
        self.TM.chuan_bi(self.cu)
        con_lai = os.listdir(self.cu)
        self.assertTrue(any('da-chuyen-doi' in x for x in con_lai),
                        'bản cũ phải còn để lùi được, chỉ đổi tên')


if __name__ == '__main__':
    unittest.main(verbosity=2)


class TestMotDuongUploadDuyNhat(unittest.TestCase):
    """Ver 4.4.1.6b — CẢ HAI hàm upload phải đi qua wp_http.post_media.

    Bug thật của 4.4.1.6: retry được thêm vào ai_wp_adapter.upload_anh_media
    (1 caller) trong khi 403 người dùng gặp đi qua autopost._url_anh_tren_wp
    (4 caller, gồm tab Ảnh). Sửa một sợi trong bó dây mà tưởng sửa cả bó.
    Test này chốt lại: chỉ còn MỘT chỗ chạm mạng.
    """

    def test_chi_mot_noi_goi_endpoint_media(self):
        import glob
        import re as _re
        goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        thu_pham = []
        for f in glob.glob(os.path.join(goc, '*.py')):
            if os.path.basename(f) == 'wp_http.py':
                continue
            noi_dung = open(f, encoding='utf-8').read()
            # Chỉ bắt UPLOAD binary: POST .../v2/media KHÔNG kèm /{id}.
            # POST .../v2/media/{media_id} là cập nhật alt/title — khác việc,
            # không cần retry upload, không tính là đường upload thứ hai.
            for m in _re.finditer(r"requests\.post\(\s*f?['\"][^'\"]*"
                                  r"wp-json/wp/v2/media['\"]",
                                  noi_dung):
                thu_pham.append(os.path.basename(f))
        self.assertEqual(thu_pham, [],
                         'Còn %s gọi thẳng endpoint media, không qua wp_http '
                         '-> sẽ lại có đường không retry.' % set(thu_pham))

    def test_autopost_nem_runtimeerror_nhu_cu(self):
        """4 caller đang bắt RuntimeError. Đổi kiểu ngoại lệ là phá cả 4."""
        import inspect
        import autopost
        src = inspect.getsource(autopost._url_anh_tren_wp)
        self.assertIn('raise RuntimeError', src)
        self.assertIn('wp_http', src)

    def test_loi_khong_con_bi_cat_200(self):
        import inspect
        import autopost
        src = inspect.getsource(autopost._url_anh_tren_wp)
        self.assertNotIn('r.text[:200]', src)
