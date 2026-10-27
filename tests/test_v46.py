import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import sys
from unittest.mock import patch

import ai_wp_adapter as AWP
import cauhinh as C
import db_phase2 as DB

KQ = []


def test(ma, mota, ok):
    KQ.append((ma, mota, bool(ok)))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}')


class FakeResp:
    def __init__(self, status_code, json_data=None, text=''):
        self.status_code, self._json, self.text = status_code, json_data, text

    def json(self):
        return self._json


# ============================================================ NHÓM A — cấu hình site: che_do_dang round-trip
C.luu_website('Test Post', 'https://post-test.vn', 'admin', 'abcd efgh ijkl')
wc1 = C.doc_website()
test('CFG-1', f'Không truyền che_do_dang -> mặc định "post" (không đổi hành vi site cũ): {wc1["che_do_dang"]}',
     wc1['che_do_dang'] == 'post')

C.luu_website('Test Woo', 'https://woo-test.vn', 'admin', 'abcd efgh ijkl', 'woo_product')
wc2 = C.doc_website()
test('CFG-2', f'Lưu che_do_dang="woo_product" -> đọc lại đúng: {wc2["che_do_dang"]}',
     wc2['che_do_dang'] == 'woo_product')

C.luu_website('Test Sai', 'https://sai-test.vn', 'admin', 'abcd efgh ijkl', 'gia_tri_linh_tinh')
wc3 = C.doc_website()
test('CFG-3', f'Giá trị che_do_dang không hợp lệ -> tự về "post" an toàn, không crash: {wc3["che_do_dang"]}',
     wc3['che_do_dang'] == 'post')

# ============================================================ NHÓM B — dang_woo_that(): tạo mới, ép draft/simple, không set giá
C.luu_website('Woo Real Test', 'https://woo-real.vn', 'admin', 'abcd efgh ijkl', 'woo_product')
goi_da_gui = {}


def fake_post_tao_moi(url, **kwargs):
    import json as _json
    goi_da_gui['body'] = _json.loads(kwargs['data'])
    goi_da_gui['url'] = url
    return FakeResp(201, {'id': 999, 'permalink': 'https://woo-real.vn/product/cd150'})


def fake_get_chua_co(url, **kwargs):
    return FakeResp(200, [])


with patch('requests.post', side_effect=fake_post_tao_moi), \
     patch('requests.get', side_effect=fake_get_chua_co):
    kq = AWP.dang_woo_that('ds1', 'r1', 'woo-real.vn', 'chuan', 'Cáp CD150', 'cap-cd150',
                           '<p>noi dung</p>', 'mo ta ngan', ma_hang='CD150')

test('WOO-1', f'Tạo mới thành công, trả đúng wp_id/wp_url: {kq}',
     kq['ok'] is True and kq['wp_id'] == 999 and 'woo-real.vn' in kq['wp_url'])
test('WOO-2', f'POST đúng vào /wc/v3/products (endpoint WooCommerce, không phải /wp/v2/posts): {goi_da_gui["url"]}',
     goi_da_gui['url'].endswith('/wp-json/wc/v3/products'))
test('WOO-3', f'status LUÔN ép cứng draft: {goi_da_gui["body"].get("status")}',
     goi_da_gui['body'].get('status') == 'draft')
test('WOO-4', f'type LUÔN ép cứng simple: {goi_da_gui["body"].get("type")}',
     goi_da_gui['body'].get('type') == 'simple')
test('WOO-5', f'SKU gửi đúng mã hàng: {goi_da_gui["body"].get("sku")}',
     goi_da_gui['body'].get('sku') == 'CD150')
test('WOO-6', f'KHÔNG set regular_price/sale_price (đúng mô hình Liên hệ, không có giá): '
              f'{goi_da_gui["body"].get("regular_price")}, {goi_da_gui["body"].get("sale_price")}',
     'regular_price' not in goi_da_gui['body'] and 'sale_price' not in goi_da_gui['body'])

# ============================================================ NHÓM C — dang_woo_that(): idempotent theo SKU (không đẻ trùng)
so_lan_tao_moi = {'n': 0}


def fake_post_da_co(url, **kwargs):
    if url.endswith('/999'):
        return FakeResp(200, {'id': 999, 'permalink': 'https://woo-real.vn/product/cd150'})
    so_lan_tao_moi['n'] += 1
    return FakeResp(201, {'id': 999, 'permalink': 'https://woo-real.vn/product/cd150'})


def fake_get_da_co_sku(url, **kwargs):
    return FakeResp(200, [{'id': 999}])


with patch('requests.post', side_effect=fake_post_da_co), \
     patch('requests.get', side_effect=fake_get_da_co_sku):
    kq2 = AWP.dang_woo_that('ds1', 'r1', 'woo-real.vn', 'chuan', 'Cáp CD150 sửa', 'cap-cd150',
                            '<p>noi dung moi</p>', 'mo ta moi', ma_hang='CD150')

test('WOO-7', f'SKU đã có sẵn (999) -> PUT cập nhật đúng ID, KHÔNG tạo mới: ok={kq2["ok"]}, '
             f'so_lan_tao_moi={so_lan_tao_moi["n"]}',
     kq2['ok'] is True and kq2['wp_id'] == 999 and so_lan_tao_moi['n'] == 0)

# ============================================================ NHÓM D — dang_woo_that(): không retry mù khi timeout mơ hồ
so_lan_tao_moi_2 = {'n': 0}
so_lan_get = {'n': 0}


def fake_post_timeout(url, **kwargs):
    if url.endswith('/wp-json/wc/v3/products'):
        so_lan_tao_moi_2['n'] += 1
        raise __import__('requests').exceptions.Timeout('gia lap timeout')
    raise AssertionError('khong duoc goi endpoint khac')


def fake_get_lan_1_ok_lan_2_loi_mang(url, **kwargs):
    so_lan_get['n'] += 1
    if so_lan_get['n'] == 1:
        return FakeResp(200, [])   # kiem tra SKU LAN DAU (truoc khi POST) -> chua co, binh thuong
    raise __import__('requests').exceptions.ConnectionError('gia lap dut mang khi do lai SKU sau POST timeout')


with patch('requests.post', side_effect=fake_post_timeout), \
     patch('requests.get', side_effect=fake_get_lan_1_ok_lan_2_loi_mang), \
     patch('time.sleep', return_value=None):
    kq3 = AWP.dang_woo_that('ds2', 'r2', 'woo-real.vn', 'chuan', 'SP moi', 'sp-moi',
                            '<p>x</p>', 'y', ma_hang='SPMOI')

test('WOO-8', f'POST timeout + kiểm tra SKU lại cũng lỗi mạng -> KHÔNG được trả ok=True, dừng hẳn: {kq3}',
     kq3['ok'] is False and 'không thử tạo lại' in kq3['loi'].lower())
test('WOO-9', f'Chỉ thử tạo mới ĐÚNG 1 lần (không đẻ trùng khi không chắc chắn): {so_lan_tao_moi_2["n"]}',
     so_lan_tao_moi_2['n'] == 1)

# ============================================================ NHÓM E — required-field: JSON hợp lệ nhưng thiếu field -> FAILED
class FakeGeminiResp:
    def __init__(self, status_code, json_data):
        self.status_code, self._json = status_code, json_data

    def json(self):
        return self._json


import prompts_phase2 as PR
schema_thieu = PR._json_schema('outline_cap_dien', mau='chuan')
truong_bat_buoc_mau = [k for k, v in schema_thieu.items() if isinstance(v, str)][0]

du_lieu_thieu_field = {k: ('noi dung du dai cho field nay de qua duoc kiem do dai neu co' if isinstance(v, str) else [])
                       for k, v in schema_thieu.items()}
del du_lieu_thieu_field[truong_bat_buoc_mau]   # cố ý xoá 1 field bắt buộc

fake_gemini_body = {
    'candidates': [{'finishReason': 'STOP',
                    'content': {'parts': [{'text': __import__('json').dumps(du_lieu_thieu_field, ensure_ascii=False)}]}}],
    'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 10},
}
row_test = {'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'ten_goc': 'Cap test',
           'tiet_diem': '2x1.5', 'ma_goc': 'CD1'}
C.luu_gemini('FAKE_KEY', 'gemini-2.5-flash')

with patch('requests.post', return_value=FakeGeminiResp(200, fake_gemini_body)):
    kq_thieu = AWP.goi_ai_that(row_test, 'chuan', 'gemini-2.5-flash', site_cfg={'ten': 'Test'})

test('REQ-1', f'JSON hợp lệ (parse được) nhưng THIẾU field bắt buộc "{truong_bat_buoc_mau}" -> phải FAILED: {kq_thieu}',
     kq_thieu['ok'] is False and truong_bat_buoc_mau in kq_thieu['loi'])

# ---- đối chứng: đủ field bắt buộc -> vẫn OK bình thường ----
du_lieu_du = {k: ('noi dung du dai cho field nay de qua duoc kiem do dai neu co' if isinstance(v, str) else [])
              for k, v in schema_thieu.items()}
fake_gemini_body_du = {
    'candidates': [{'finishReason': 'STOP',
                    'content': {'parts': [{'text': __import__('json').dumps(du_lieu_du, ensure_ascii=False)}]}}],
    'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 10},
}
with patch('requests.post', return_value=FakeGeminiResp(200, fake_gemini_body_du)):
    kq_du = AWP.goi_ai_that(row_test, 'chuan', 'gemini-2.5-flash', site_cfg={'ten': 'Test'})
test('REQ-2', f'Đối chứng: đủ field bắt buộc -> vẫn ok=True bình thường (không bị chặn nhầm): {kq_du["ok"]}',
     kq_du['ok'] is True)

# ============================================================ NHÓM F — kiem_tra_chat_luong_text: FAQ rác
test('FAQ-1', 'Ký tự lặp liên tiếp bất thường bị chặn',
     AWP.kiem_tra_chat_luong_text('aaaaaaaaaaaaaaaaaaaaaa', None) != [])
test('FAQ-2', 'Từ lặp liên tục >=5 lần bị chặn',
     AWP.kiem_tra_chat_luong_text('tốt tốt tốt tốt tốt tốt sản phẩm', None) != [])
test('FAQ-3', 'Văn bản bình thường KHÔNG bị chặn nhầm',
     AWP.kiem_tra_chat_luong_text('Sản phẩm có sẵn hàng, giao trong 2-3 ngày làm việc.', 'faq_a') == [])
test('FAQ-4', 'FAQ quá ngắn (dưới ngưỡng) bị chặn theo độ dài',
     AWP.kiem_tra_chat_luong_text('ok', 'faq_a') != [])

vi_pham_rac = AWP.kiem_tra_bia_toan_bo(
    {'meta_title': 'Tieu de hop le du dai', 'meta_description': 'Mo ta hop le du dai cho field nay.',
     'faq': [{'q': 'Có sẵn hàng không?', 'a': 'tốt tốt tốt tốt tốt tốt tốt'}]},
    {'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'ten_goc': 'Cap test'})
test('FAQ-5', f'kiem_tra_bia_toan_bo() bắt được FAQ rác (từ lặp), không chỉ số bịa: {vi_pham_rac}',
     'faq[0].a' in vi_pham_rac)

# ============================================================ NHÓM G — maxOutputTokens tăng lên
import inspect
src = inspect.getsource(AWP.goi_ai_that)
test('TOKEN-1', '"maxOutputTokens" trong goi_ai_that() đã tăng (Ver 4.7: 24000, từ 16000 ở Ver 4.6)', '24000' in src)

print()
p = sum(1 for _, _, ok in KQ if ok)
print(f'TONG VER 4.6: {p}/{len(KQ)} PASS')
if p != len(KQ):
    sys.exit(1)
