# -*- coding: utf-8 -*-
"""Ver 3.8 Gate 7: chứng minh local contract Woo category ID + schema payload.
KHÔNG chứng minh frontend WordPress thật; phần đó phải có consumer/hook trên site.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from unittest.mock import patch

import ai_wp_adapter as AWP
import cauhinh as C
import render_phase2 as R

class Resp:
    def __init__(self, code, data):
        self.status_code = code
        self._data = data
        self.text = json.dumps(data, ensure_ascii=False)
        self.headers = {'Content-Type': 'application/json'}
    def json(self):
        return self._data


def main():
    with tempfile.TemporaryDirectory() as td:
        os.environ['SONEALEO_ENV_PATH'] = os.path.join(td, 'test.env')
        os.environ['SONEALEO_DB_PATH'] = os.path.join(td, 'test.db')
        C.luu_website('Mock Woo', 'https://mock.local', 'admin', 'abcd efgh ijkl', 'woo_product')
        sent = {}

        def fake_get(url, **kwargs):
            if url.endswith('/products/categories'):
                print('CATEGORY_QUERY=' + str(kwargs.get('params')))
                return Resp(200, [{'id': 123, 'name': 'Máy biến áp', 'slug': 'may-bien-ap'}])
            # tim_san_pham_woo_theo_sku
            return Resp(200, [])

        def fake_post(url, **kwargs):
            sent['payload'] = json.loads(kwargs['data'].decode('utf-8'))
            return Resp(201, {'id': 9001, 'permalink': 'https://mock.local/p/x'})

        schema = {
            '@context': 'https://schema.org', '@type': 'Product',
            'name': 'MBA test', 'sku': 'SKU-B2', 'description': 'Mô tả cuối.'
        }
        faq_schema = {
            '@context': 'https://schema.org', '@type': 'FAQPage',
            'mainEntity': [{'@type': 'Question', 'name': 'Q',
                            'acceptedAnswer': {'@type': 'Answer', 'text': 'A'}}]
        }
        with patch('requests.get', side_effect=fake_get), patch('requests.post', side_effect=fake_post):
            kq = AWP.dang_woo_that(
                'ds', 'rid', 'site', 'chuan', 'MBA test', 'mba-test', '<p>x</p>', 'short',
                ma_hang='SKU-B2', da_co_woo_id=None,
                danh_muc=['Máy biến áp'], schema=schema, faq_schema=faq_schema)

        payload = sent.get('payload') or {}
        cats = payload.get('categories')
        metas = payload.get('meta_data') or []
        schema_meta = next((x.get('value') for x in metas if x.get('key') == '_snl_schema_jsonld'), None)
        faq_meta = next((x.get('value') for x in metas if x.get('key') == '_snl_faq_schema_jsonld'), None)
        print('WOO_OK=' + str(kq.get('ok')))
        print('CATEGORY_PAYLOAD=' + json.dumps(cats, ensure_ascii=False))
        print('SCHEMA_META=' + json.dumps(schema_meta, ensure_ascii=False))
        print('FAQ_SCHEMA_META=' + json.dumps(faq_meta, ensure_ascii=False))

        row = {
            'content_type': 'product', 'profile_id': 'may_bien_ap',
            'outline_id': 'outline_may_bien_ap', 'ten_goc': 'MBA test',
            'ma_goc': 'SKU', 'publish_sku': 'SKU-B2', 'thuong_hieu': 'TEST'
        }
        # effective_cot_bang phụ thuộc profile thật; chỉ kiểm schema identity/description.
        with patch('profiles.effective_cot_bang', return_value=[]):
            built = R.dung_schema(row, description='Mô tả cuối.')
        print('BUILT_SCHEMA_SKU=' + str(built.get('sku')))
        print('BUILT_SCHEMA_DESCRIPTION=' + str(built.get('description')))

        assert kq.get('ok') is True
        assert cats == [{'id': 123}]
        assert all('name' not in x for x in cats)
        assert schema_meta and schema_meta.get('@type') == 'Product'
        assert faq_meta and faq_meta.get('@type') == 'FAQPage'
        assert built.get('sku') == 'SKU-B2'
        assert built.get('description') == 'Mô tả cuối.'
        print('PASS_GATE7_LOCAL=1')

if __name__ == '__main__':
    main()
