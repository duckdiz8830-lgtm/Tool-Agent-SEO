import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import sys
from unittest.mock import patch

import ai_wp_adapter as AWP
import autopost as A
import cauhinh as C

KQ = []


def test(ma, mota, ok):
    KQ.append((ma, mota, bool(ok)))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}')


class FakeResp:
    def __init__(self, status_code, json_data=None, text=''):
        self.status_code, self._json, self.text = status_code, json_data, text

    def json(self):
        return self._json


# ============================================================ NHÓM A — tim_san_pham_woo_theo_sku: status='any' mặc định
C.luu_website('SKU Status Test', 'https://sku-status.vn', 'admin', 'abcd efgh ijkl', 'woo_product')
goi_params = {}


def fake_get_ghi_lai_params(url, **kwargs):
    goi_params['params'] = kwargs.get('params')
    return FakeResp(200, [])


with patch('requests.get', side_effect=fake_get_ghi_lai_params):
    A.tim_san_pham_woo_theo_sku(C.MA_SITE_VER3, 'SKU1')
test('SKU-STATUS-1', f'Mặc định gửi status=any (bug thật đã vá — trước đây thiếu, WooCommerce tự mặc định '
                     f'publish, bỏ sót draft): {goi_params["params"]}',
     goi_params['params'].get('status') == 'any')

with patch('requests.get', side_effect=fake_get_ghi_lai_params):
    A.tim_san_pham_woo_theo_sku(C.MA_SITE_VER3, 'SKU1', trang_thai='trash')
test('SKU-STATUS-2', f'Truyền trang_thai="trash" thì gửi đúng status=trash (để tra riêng thùng rác): '
                     f'{goi_params["params"]}', goi_params['params'].get('status') == 'trash')

# ============================================================ NHÓM B — dang_woo_that: phát hiện đúng case trong Thùng rác, báo rõ ràng
so_lan_get_theo_status = []


def fake_post_trung_sku(url, **kwargs):
    return FakeResp(400, {'message': 'SKU đã có trong bảng tra cứu'})


def fake_get_any_khong_thay_trash_co(url, **kwargs):
    status = kwargs.get('params', {}).get('status')
    so_lan_get_theo_status.append(status)
    if status == 'trash':
        return FakeResp(200, [{'id': 777}])
    return FakeResp(200, [])   # status='any' (mặc định) -> khong thay (khong con o draft/publish)


with patch('requests.post', side_effect=fake_post_trung_sku), \
     patch('requests.get', side_effect=fake_get_any_khong_thay_trash_co):
    kq = AWP.dang_woo_that('ds1', 'r1', 'sku-status.vn', 'chuan', 'SP 1', 'sp-1',
                           '<p>x</p>', 'y', ma_hang='SP_TRASH')

test('TRASH-1', f'Phát hiện đúng SKU đang bị giữ bởi sản phẩm trong THÙNG RÁC, báo lỗi rõ ràng, không đoán mò: {kq["loi"]}',
     kq['ok'] is False and 'thùng rác' in kq['loi'].lower() and '777' in kq['loi'])
test('TRASH-2', 'KHÔNG tự động khôi phục/xoá sản phẩm trong thùng rác (chỉ báo, không tự sửa dữ liệu)',
     'tool không tự xoá' in kq['loi'].lower() or 'không tự' in kq['loi'].lower())

# ============================================================ NHÓM C — goi_ai_co_du_phong: bỏ FAQ khi chỉ FAQ lỗi, giữ nguyên nội dung khác
class FakeGeminiResp:
    def __init__(self, status_code, json_data):
        self.status_code, self._json = status_code, json_data

    def json(self):
        return self._json


import prompts_phase2 as PR
SCHEMA = PR._json_schema('outline_cap_dien', mau='chuan')
DATA_FAQ_DAI = {k: ('noi dung du dai qua nguong do dai kiem tra field nay binh thuong' if isinstance(v, str) else [])
               for k, v in SCHEMA.items()}
DATA_FAQ_DAI['faq'] = [{'q': 'x' * 200, 'a': 'noi dung du dai qua nguong do dai kiem tra field nay binh thuong'}]


def body_json(d):
    import json
    return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps(d, ensure_ascii=False)}]}}],
           'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 10}}


ROW = {'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'ten_goc': 'Cap test', 'ma_goc': 'CD1'}

with patch('requests.post', return_value=FakeGeminiResp(200, body_json(DATA_FAQ_DAI))):
    kq2, vp2 = AWP.goi_ai_co_du_phong(ROW, 'chuan', [('k1', 'model_a')], site_cfg={'ten': 'T'})

test('FAQ-DROP-1', f'CHỈ FAQ lỗi (nội dung khác sạch) -> vẫn coi là THÀNH CÔNG, không đổi cặp key/model: '
                   f'ok={kq2["ok"]}, faq_bi_bo={kq2.get("faq_bi_bo")}',
     kq2['ok'] is True and kq2.get('faq_bi_bo') is True)
test('FAQ-DROP-2', f'FAQ đã bị xoá khỏi data trả về (mảng rỗng): {kq2["data"].get("faq")}',
     kq2['data'].get('faq') == [])
test('FAQ-DROP-3', 'Nội dung KHÁC (dac_diem_html...) vẫn giữ nguyên, không bị xoá theo',
     bool(kq2['data'].get('dac_diem_html')))
test('FAQ-DROP-4', 'da_thu=1 (không cần đổi cặp key/model chỉ vì FAQ)', kq2.get('da_thu') == 1)

# ---- đối chứng: lỗi KHÔNG chỉ ở FAQ (có field khác cũng lỗi) -> KHÔNG được tự ý bỏ qua ----
DATA_LOI_CA_CORE = dict(DATA_FAQ_DAI)
DATA_LOI_CA_CORE['meta_title'] = 'x' * 5  # qua ngan (< 5 ky tu toi thieu neu co, hoac gia lap loi khac)
DATA_LOI_CA_CORE['dac_diem_html'] = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'  # ky tu lap bat thuong

with patch('requests.post', return_value=FakeGeminiResp(200, body_json(DATA_LOI_CA_CORE))):
    kq3, vp3 = AWP.goi_ai_co_du_phong(ROW, 'chuan', [('k1', 'model_a')], site_cfg={'ten': 'T'})

test('FAQ-DROP-5', f'Nếu có field CỐT LÕI cũng lỗi (không chỉ FAQ) -> KHÔNG được tự ý bỏ qua, vẫn báo lỗi: '
                   f'ok={kq3["ok"]}', kq3['ok'] is False)

print()
p = sum(1 for _, _, ok in KQ if ok)
print(f'TONG VER 4.9: {p}/{len(KQ)} PASS')
if p != len(KQ):
    sys.exit(1)
