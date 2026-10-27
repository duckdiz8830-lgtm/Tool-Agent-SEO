# -*- coding: utf-8 -*-
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))

import importlib.util
import json
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import ai_wp_adapter as AWP
import cauhinh as C
import db_phase2 as DB
import dulieu as DL
import nhap_phase2 as N
import workspace_anh as WS

BASE = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('giao_dien_gate5', BASE / 'giao-dien.py')
gd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gd)


class Resp:
    def __init__(self, status_code=200, data=None, text=''):
        self.status_code = status_code
        self._data = data
        self.text = text
    def json(self):
        return self._data


class FakeApp:
    def __init__(self):
        self.v3_dung_lai = threading.Event()
    def _con_phase2(self):
        return DB.ket_noi()
    def ui(self, fn):
        fn()
    def _v3_cap_nhat_tien_do_that(self, *args):
        pass
    def _v3_nap_dashboard(self):
        pass
    def _v3_ket_thuc_chay(self, *args):
        pass


def main():
    with tempfile.TemporaryDirectory(prefix='snl-g5-') as td:
        td = Path(td)
        DB.DB_PATH = td / 'phase2-test.db'
        DL.DB = td / 'du-lieu-test.db'
        # Cấu hình chỉ trỏ MOCK host; requests bị chặn hoàn toàn bên dưới.
        _os.environ['WP_WEBSITE_TEN'] = 'Mock WP'
        _os.environ['WP_WEBSITE_URL'] = 'https://mock.local'
        _os.environ['WP_WEBSITE_USER'] = 'mock'
        _os.environ['WP_WEBSITE_APP_PW'] = 'mock-pass'
        _os.environ['WP_WEBSITE_CHE_DO'] = 'woo_product'
        _os.environ['GIAO_DIEN_2_5'] = '1'  # production layout: body image roles use anchored slots

        rpt = N.import_phase2_pipeline(BASE / 'du_lieu_goc' / 'MASTER_4_PROFILE_SAN_PHAM.xlsx',
                                       db_path=DB.DB_PATH)
        did = rpt['ket_qua_theo_profile']['may_bien_ap_do_luong']['dataset_id']
        con = DB.ket_noi()
        rows = DB.liet_ke_san_pham(con, dataset_id=did)
        con.close()
        row = dict(rows[0])
        # Gate 5 cô lập image E2E; Gate 6 đã có test riêng cho validation blocker.
        row['nghi_van_dien_ap'] = False
        rid = row['record_id']
        parts = rid.split('::')
        sheet = parts[1]

        image_root = td / 'images'
        tm = WS.tao_workspace(image_root, sheet, int(row.get('source_row') or 1), row,
                              title=row.get('ten_goc', ''))
        src = td / 'bien_may.png'
        # Ver 5.7 — fixture phải >= ngưỡng cổng ảnh (cạnh ngắn 800px), nếu không
        # dang_anh_cua_bai() sẽ BỎ QUA đúng như thiết kế và test hiểu nhầm
        # thành lỗi upload. Để 1000x900 nhằm test đường upload THẬT với
        # cổng đang BẬT, thay vì tắt cổng đi cho qua chuyện.
        Image.new('RGB', (1000, 900)).save(src)
        WS.gan_anh(tm, src, 'bien_may')

        media_bytes = []
        product_payloads = []
        attach_payloads = []
        media_meta_payloads = []
        product_counter = {'id': 901}

        def fake_get(url, **kwargs):
            if url.endswith('/wp-json/wc/v3/products/categories'):
                ten = (kwargs.get('params') or {}).get('search', 'Danh mục test')
                return Resp(200, [{'id': 77, 'name': ten}])
            # Woo lookup trước create: chưa có sản phẩm trên mock server.
            return Resp(200, [])

        def fake_post(url, **kwargs):
            if url.endswith('/wp-json/wp/v2/media'):
                media_bytes.append(kwargs.get('data', b''))
                return Resp(201, {'id': 501, 'source_url': 'https://mock.local/media/bien-may.webp'})
            if url.endswith('/wp-json/wp/v2/media/501'):
                media_meta_payloads.append(kwargs.get('json') or {})
                return Resp(200, {'id': 501, 'source_url': 'https://mock.local/media/bien-may.webp'})
            if '/wp-json/wc/v3/products/' in url and 'json' in kwargs:
                attach_payloads.append(kwargs['json'])
                return Resp(200, {'id': product_counter['id']})
            if '/wp-json/wc/v3/products' in url:
                raw = kwargs.get('data', b'{}')
                if isinstance(raw, bytes):
                    raw = raw.decode('utf-8')
                product_payloads.append(json.loads(raw))
                return Resp(201, {'id': product_counter['id'],
                                  'permalink': 'https://mock.local/product/test/'})
            raise AssertionError('POST ngoài mock contract: ' + url)

        ai_data = {
            'meta_title': 'Test product', 'meta_description': 'Mô tả test.',
            'intro_html': '<p>Giới thiệu</p>', 'dac_diem_html': '<p>Đặc điểm</p>',
            'ung_dung_html': '<p>Ứng dụng</p>',
        }
        def fake_ai(*args, **kwargs):
            return ({'ok': True, 'data': dict(ai_data), 'da_thu': 1}, [])

        app = FakeApp()
        wc = C.doc_website()
        args = ([row], 'chuan', [('FAKE', 'MODEL')], wc, 0.0,
                False, {'bat': False, 'serper_key': '', 'cong_dong': False},
                {'ten': 'Mock WP'}, str(image_root))

        with patch.object(AWP, 'goi_ai_co_du_phong', side_effect=fake_ai), \
             patch('requests.get', side_effect=fake_get), \
             patch('requests.post', side_effect=fake_post):
            gd.PhanMem._v3_viec_dang_draft_that_hang_loat(app, *args)
            # Lần hai ép update để production path ảnh chạy lại; hash không đổi -> 0 media POST mới.
            args2 = list(args)
            args2[5] = True
            gd.PhanMem._v3_viec_dang_draft_that_hang_loat(app, *args2)

        meta = WS.doc_meta(tm)
        bien_may = next(a for a in meta['anh'] if a.get('vai_tro') == 'bien_may')
        print('MEDIA_POSTS=', len(media_bytes))
        print('MEDIA_BYTES=', len(media_bytes[0]) if media_bytes else 0)
        print('PRODUCT_POSTS=', len(product_payloads))
        print('MEDIA_META_POSTS=', len(media_meta_payloads))
        print('HAS_IMG=', bool(product_payloads and '<img ' in product_payloads[0].get('description', '')))
        print('ATTACH=', attach_payloads)
        print('META_MEDIA_ID=', bien_may.get('wp_media_id'))
        print('META_STATE=', bien_may.get('trang_thai'))

        assert len(media_bytes) == 1, 'Lần hai đã upload lại ảnh dù hash không đổi'
        assert media_bytes[0], 'Mock WordPress không nhận bytes ảnh'
        assert len(media_meta_payloads) == 1 and media_meta_payloads[0].get('alt_text'), 'Metadata alt/title chưa được POST đúng một lần'
        assert product_payloads and '<img ' in product_payloads[0]['description']
        assert attach_payloads and attach_payloads[0] == {'images': [{'id': 501}]}
        assert bien_may.get('wp_media_id') == 501 and bien_may.get('trang_thai') == WS.DA_DANG
        print('PASS: workspace -> bytes -> media_id -> <img> -> product attach; lần hai không upload lại')


if __name__ == '__main__':
    main()
