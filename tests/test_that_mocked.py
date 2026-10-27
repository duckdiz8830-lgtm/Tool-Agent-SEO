import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
# -*- coding: utf-8 -*-
"""
Test Gate "Draft thật" bằng requests GIẢ LẬP (mock HTTP) — sandbox này không
gọi được generativelanguage.googleapis.com hay WordPress thật, nhưng toàn bộ
LOGIC (dựng request, xử lý status code, retry, idempotent, parse response)
kiểm được đầy đủ bằng cách giả lập requests.get/requests.post.

Chạy: python3 test_that_mocked.py
"""
import json as _json
import os
import sys
from unittest.mock import patch, MagicMock

KQ = []
def test(ma, mota, ok, gc=''):
    KQ.append((ma, mota, bool(ok)))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}' + (f' ({gc})' if gc else ''))


class FakeResp:
    def __init__(self, status_code, json_data=None, text='', headers=None):
        self.status_code = status_code
        self._json = json_data
        self.text = text
        self.headers = headers or {}
    def json(self):
        if self._json is None:
            raise ValueError('no json')
        return self._json


# ============================================================ setup: cau-hinh.env test riêng
os.environ['GOOGLE_API_KEY'] = 'FAKE_KEY_KHONG_THAT'
os.environ['MODEL_GEMINI'] = 'gemini-2.5-flash'
os.environ['WP_WEBSITE_URL'] = 'https://test.example.vn'
os.environ['WP_WEBSITE_USER'] = 'admin'
os.environ['WP_WEBSITE_APP_PW'] = 'abcd efgh ijkl mnop'
os.environ['WP_WEBSITE_TEN'] = 'Test Site'

import ai_wp_adapter as AWP
import nhap_phase2 as N
import validators as V

r = N.import_4_profile('du_lieu_goc/MASTER_4_PROFILE_SAN_PHAM.xlsx', chi_profile='cap_dien')
rows = V.validate_rows(r['cap_dien']['rows'])
row = next(x for x in rows if x['outline_id'] == 'outline_cap_dien' and x.get('vat_lieu_ruot'))
row['dataset_id'] = 'ds_test_001'

# ============================================================ 1. goi_ai_that — thành công
with patch('requests.post') as mock_post:
    mock_post.return_value = FakeResp(200, {
        'candidates': [{'content': {'parts': [{'text': _json.dumps({
            'meta_title': 'Dây điện tốt', 'meta_description': 'Mô tả sản phẩm.',
            'intro_html': '<p>Giới thiệu</p>', 'dac_diem_html': '<p>Đặc điểm</p>',
            'ung_dung_html': '<p>Ứng dụng</p>', 'huong_dan_chon_html': '<p>Hướng dẫn</p>',
        })}]}, 'finishReason': 'STOP'}],
        'usageMetadata': {'promptTokenCount': 100, 'candidatesTokenCount': 50},
    })
    kq = AWP.goi_ai_that(row, 'chuan', 'gemini-2.5-flash')
    test('AI-1', 'goi_ai_that thành công, parse đúng JSON', kq['ok'] and kq['data']['meta_title']=='Dây điện tốt')
    goi_thuc_te = mock_post.call_args
    test('AI-1', 'Request KHÔNG chứa nội dung API key bị log ra (chỉ nằm trong URL param)',
         'FAKE_KEY_KHONG_THAT' not in _json.dumps(goi_thuc_te.kwargs.get('json', {})))

# ============================================================ 2. goi_ai_that — 401 auth
with patch('requests.post') as mock_post:
    mock_post.return_value = FakeResp(401, text='API key invalid')
    kq = AWP.goi_ai_that(row, 'chuan', 'gemini-2.5-flash')
    test('AI-2', 'goi_ai_that báo rõ lỗi 401 (key sai)', not kq['ok'] and '401' in kq['loi'])

# ============================================================ 3. goi_ai_that — 404 model
with patch('requests.post') as mock_post:
    mock_post.return_value = FakeResp(404, text='model not found')
    kq = AWP.goi_ai_that(row, 'chuan', 'model-khong-ton-tai')
    test('AI-3', 'goi_ai_that báo rõ lỗi 404 (model không tồn tại)', not kq['ok'] and '404' in kq['loi'])

# ============================================================ 4. goi_ai_that — 429 hết ngày
with patch('requests.post') as mock_post:
    mock_post.return_value = FakeResp(429, {
        'error': {'message': 'quota exceeded per day', 'details': [
            {'@type': 'type.googleapis.com/google.rpc.QuotaFailure',
             'violations': [{'quotaId': 'GenerateContentPerDay'}]}]}})
    kq = AWP.goi_ai_that(row, 'chuan', 'gemini-2.5-flash')
    test('AI-4', 'goi_ai_that báo rõ hết lượt trong ngày (429 NGAY, không retry vô ích)',
         not kq['ok'] and 'ngày' in kq['loi'].lower())

# ============================================================ 5. goi_ai_that — JSON hỏng
with patch('requests.post') as mock_post:
    mock_post.return_value = FakeResp(200, {
        'candidates': [{'content': {'parts': [{'text': '{khong phai json hop le'}]}, 'finishReason': 'STOP'}]})
    kq = AWP.goi_ai_that(row, 'chuan', 'gemini-2.5-flash')
    test('AI-5', 'goi_ai_that báo rõ JSON hỏng, không crash', not kq['ok'] and 'JSON' in kq['loi'])

# ============================================================ 6. goi_ai_that — SAFETY block
with patch('requests.post') as mock_post:
    mock_post.return_value = FakeResp(200, {
        'candidates': [{'content': {'parts': []}, 'finishReason': 'SAFETY'}]})
    kq = AWP.goi_ai_that(row, 'chuan', 'gemini-2.5-flash')
    test('AI-6', 'goi_ai_that báo rõ bị chặn SAFETY', not kq['ok'] and 'SAFETY' in kq['loi'])

# ============================================================ 7. Hard Block E2E
ai_data_bia = {
    'meta_title': 'Dây điện chuẩn IP65',              # bịa IP65 -> phải chặn
    'meta_description': 'Bảo hành 24 tháng chính hãng.',  # bịa bảo hành -> phải chặn
    'faq': [{'q': 'Có đạt IEC 62271 không?', 'a': 'Có.'}],  # bịa IEC -> phải chặn
}
vi_pham = AWP.kiem_tra_bia_toan_bo(ai_data_bia, row)
test('HB-1', f'Hard Block E2E chặn IP65 trong meta_title: {vi_pham.get("meta_title")}',
     'meta_title' in vi_pham)
test('HB-1', f'Hard Block E2E chặn "24 tháng" trong meta_description: {vi_pham.get("meta_description")}',
     'meta_description' in vi_pham)
test('HB-1', f'Hard Block E2E chặn IEC 62271 trong faq[0].q: {vi_pham.get("faq[0].q")}',
     'faq[0].q' in vi_pham)

ai_data_that = {
    'meta_title': row['ten_goc'][:50],
    'meta_description': f'{row["ten_goc"]}, vật liệu ruột {row.get("vat_lieu_ruot","")}.',
    'faq': [{'q': 'Sản phẩm có sẵn không?', 'a': 'Liên hệ để biết thêm.'}],
}
vi_pham2 = AWP.kiem_tra_bia_toan_bo(ai_data_that, row)
test('HB-2', f'Hard Block E2E KHÔNG chặn nội dung đúng dữ liệu thật: {vi_pham2}', not vi_pham2)

print()
p = sum(1 for _,_,ok in KQ if ok)
print(f'PHẦN AI: {p}/{len(KQ)} PASS')

print()
print('='*60)
print('PHẦN WORDPRESS')
print('='*60)
import db_phase2 as DB

DB_TEST = 'test_wp_that.db'
if os.path.exists(DB_TEST):
    os.remove(DB_TEST)
con = DB.ket_noi(DB_TEST)
DB.xac_nhan_dataset(con, 'cap_dien', 'test.xlsx', 'fc1', 'dc1', 1, ['ma_goc'])
DB.ghi_san_pham(con, 'ds_cap_dien_001', [row])

# monkeypatch ket_noi để dùng đúng DB test (dang_wp_that tự mở connection riêng)
import db_phase2
_ket_noi_goc = db_phase2.ket_noi
db_phase2.ket_noi = lambda *a, **k: _ket_noi_goc(DB_TEST)

# ---- kiem_tra_ket_noi_wp: thành công ----
with patch('requests.get') as mock_get:
    mock_get.return_value = FakeResp(200, {'name': 'admin', 'roles': ['administrator']})
    kq = AWP.kiem_tra_ket_noi_wp()
    test('WP-1', f'kiem_tra_ket_noi_wp thành công: {kq.get("thong_diep")}', kq['ok'])

# ---- kiem_tra_ket_noi_wp: auth sai ----
with patch('requests.get') as mock_get:
    mock_get.return_value = FakeResp(401, text='unauthorized')
    kq = AWP.kiem_tra_ket_noi_wp()
    test('WP-2', 'kiem_tra_ket_noi_wp báo rõ 401', not kq['ok'] and '401' in kq['loi'])

# ---- kiem_tra_ket_noi_wp: WAF (503 + HTML) ----
with patch('requests.get') as mock_get:
    def raise_json():
        raise ValueError('not json')
    resp = FakeResp(503, text='<html>Cloudflare blocked</html>')
    mock_get.return_value = resp
    kq = AWP.kiem_tra_ket_noi_wp()
    test('WP-3', f'kiem_tra_ket_noi_wp phát hiện khả năng WAF: {kq.get("loi")}',
         not kq['ok'] and ('WAF' in kq['loi'] or '503' in kq['loi']))

# ---- kiem_tra_ket_noi_wp: KHÔNG tạo bài (không gọi requests.post) ----
with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
    mock_get.return_value = FakeResp(200, {'name': 'admin', 'roles': ['administrator']})
    AWP.kiem_tra_ket_noi_wp()
    test('WP-4', 'kiem_tra_ket_noi_wp KHÔNG gọi requests.post (không tạo bài)', not mock_post.called)

# ---- dang_wp_that: đăng mới thành công ----
with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
    mock_get.return_value = FakeResp(200, [])  # tim_bai_theo_slug -> chưa có bài nào
    mock_post.return_value = FakeResp(201, {'id': 555, 'link': 'https://test.example.vn/?p=555'})
    kq = AWP.dang_wp_that('ds_cap_dien_001', row['record_id'], 'test.example.vn', 'chuan',
                          'Tiêu đề', 'slug-test-chuan', '<p>nội dung</p>', 'excerpt')
    test('WP-5', f'dang_wp_that đăng mới thành công: wp_id={kq.get("wp_id")}',
         kq['ok'] and kq['wp_id']==555 and kq['thoi_luong_giay'] is not None)
    goi = mock_post.call_args
    payload = _json.loads(goi.kwargs['data'])
    test('WP-5', f'status LUÔN là draft (ép cứng, không đọc tham số ngoài): {payload.get("status")}',
         payload.get('status')=='draft')

# ---- idempotent: gọi lại đúng khoá -> PUT update, không tạo bài mới ----
DB.cap_nhat_bai_viet(con, 'ds_cap_dien_001', row['record_id'], 'test.example.vn', 'chuan',
                     wp_id='555', trang_thai='da_dang')
with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
    mock_post.return_value = FakeResp(200, {'id': 555, 'link': 'https://test.example.vn/?p=555'})
    kq2 = AWP.dang_wp_that('ds_cap_dien_001', row['record_id'], 'test.example.vn', 'chuan',
                           'Tiêu đề 2', 'slug-test-chuan', '<p>nội dung mới</p>', 'excerpt')
    api_goi = mock_post.call_args.args[0]
    test('WP-6', f'Gọi lại đúng khoá -> PUT vào ĐÚNG wp_id=555 (URL: {api_goi}), KHÔNG tạo bài mới',
         kq2['ok'] and '/posts/555' in api_goi)
    test('WP-6', 'KHÔNG gọi tim_bai_theo_slug nữa vì đã có wp_id lưu sẵn (không dò lại thừa)',
         not mock_get.called)

# ---- timeout rồi phát hiện bài đã tạo thật (không retry mù) ----
DB.ghi_san_pham(con, 'ds_cap_dien_001', [dict(row, record_id=row['record_id']+'_2')])
DB.cap_nhat_bai_viet(con, 'ds_cap_dien_001', row['record_id']+'_2', 'test.example.vn', 'chuan',
                     trang_thai='chua_sinh')
import requests as _requests
goi_dem = {'post': 0, 'get': 0}
def fake_post(*a, **k):
    goi_dem['post'] += 1
    if goi_dem['post'] == 1:
        raise _requests.exceptions.Timeout('gia lap timeout')
    return FakeResp(200, {'id': 777, 'link': 'https://test.example.vn/?p=777'})
def fake_get(*a, **k):
    goi_dem['get'] += 1
    if goi_dem['get'] == 1:
        return FakeResp(200, [])  # lần đầu kiểm tra slug: chưa có
    return FakeResp(200, [{'id': 777}])  # sau timeout, dò lại: server ĐÃ tạo bài thật rồi
with patch('requests.post', side_effect=fake_post), patch('requests.get', side_effect=fake_get), \
     patch('time.sleep'):
    kq3 = AWP.dang_wp_that('ds_cap_dien_001', row['record_id']+'_2', 'test.example.vn', 'chuan',
                           'Tiêu đề 3', 'slug-test-3', '<p>nd</p>', 'excerpt')
    test('WP-7', f'Sau timeout, dò lại slug thấy bài ĐÃ TẠO -> lần 2 PUT update đúng ID (không đẻ mới): '
                f'ok={kq3["ok"]}, wp_id={kq3.get("wp_id")}, số lần POST={goi_dem["post"]}, số lần GET={goi_dem["get"]}',
         kq3['ok'] and goi_dem['post']==2 and goi_dem['get']==2)

# ---- 401 khi đăng thật ----
DB.ghi_san_pham(con, 'ds_cap_dien_001', [dict(row, record_id=row['record_id']+'_3')])
with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
    mock_get.return_value = FakeResp(200, [])
    mock_post.return_value = FakeResp(401, text='unauthorized')
    kq4 = AWP.dang_wp_that('ds_cap_dien_001', row['record_id']+'_3', 'test.example.vn', 'chuan',
                           'T', 'slug-4', '<p>x</p>', 'e')
    test('WP-8', 'dang_wp_that báo rõ 401 khi đăng, không mơ hồ', not kq4['ok'] and '401' in kq4['loi'])

con.close()
db_phase2.ket_noi = _ket_noi_goc
os.remove(DB_TEST)

print()
p2 = sum(1 for _,_,ok in KQ if ok)
print(f'TỔNG TOÀN BỘ: {p2}/{len(KQ)} PASS')
if p2 != len(KQ):
    sys.exit(1)
