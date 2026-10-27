import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import sys
from unittest.mock import patch

import ai_wp_adapter as AWP
import cauhinh as C
import chuan_hoa_master as CHM

KQ = []


def test(ma, mota, ok):
    KQ.append((ma, mota, bool(ok)))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}')


class FakeResp:
    def __init__(self, status_code, json_data=None, text=''):
        self.status_code, self._json, self.text = status_code, json_data, text

    def json(self):
        return self._json


# ============================================================ NHÓM A — Chuẩn hoá MASTER nhận file gộp
import nhap_phase2 as N

CHM.chuan_hoa('du_lieu_goc/MASTER_4_PROFILE_SAN_PHAM.xlsx', '/tmp/test_v48_tu_file_gop.xlsx')
test('CHM-FILE-1', 'Nhận file gộp (không phải thư mục) chạy được, không lỗi',
     __import__('os').path.exists('/tmp/test_v48_tu_file_gop.xlsx'))
loai = N.nhan_dien_loai_nguon('/tmp/test_v48_tu_file_gop.xlsx')
test('CHM-FILE-2', f'File ra từ nguồn dạng file gộp vẫn nhận đúng định dạng 4_profile: {loai}',
     loai == '4_profile')

goc = N.import_4_profile('du_lieu_goc/MASTER_4_PROFILE_SAN_PHAM.xlsx')
moi = N.import_4_profile('/tmp/test_v48_tu_file_gop.xlsx')
khop = all([r['record_id'] for r in goc[pid]['rows']] == [r['record_id'] for r in moi[pid]['rows']]
          for pid in goc)
test('CHM-FILE-3', 'record_id khớp 100% dù chạy chuẩn hoá từ nguồn dạng file gộp (không phải thư mục)', khop)

# Vẫn còn dùng được kiểu thư mục cũ (không phá tương thích ngược)
CHM.chuan_hoa('du_lieu_goc', '/tmp/test_v48_tu_thu_muc.xlsx')
test('CHM-DIR-1', 'Vẫn chạy được với nguồn dạng thư mục (tương thích ngược, không phá cách dùng cũ)',
     __import__('os').path.exists('/tmp/test_v48_tu_thu_muc.xlsx'))

try:
    CHM.chuan_hoa('/duong/dan/khong/ton/tai', '/tmp/test_v48_loi.xlsx')
    test('CHM-ERR-1', 'Nguồn không tồn tại phải báo lỗi rõ ràng', False)
except (FileNotFoundError, ValueError) as e:
    test('CHM-ERR-1', f'Nguồn không tồn tại báo lỗi rõ ràng, không crash mơ hồ: {e}', True)

# ============================================================ NHÓM B — WooCommerce: phục hồi khi trùng SKU
C.luu_website('Woo Recover Test', 'https://woo-recover.vn', 'admin', 'abcd efgh ijkl', 'woo_product')

so_lan_post = {'tao_moi': 0, 'put_999': 0}


def fake_post_trung_sku(url, **kwargs):
    if url.endswith('/999'):
        so_lan_post['put_999'] += 1
        return FakeResp(200, {'id': 999, 'permalink': 'https://woo-recover.vn/p/999'})
    so_lan_post['tao_moi'] += 1
    return FakeResp(400, {'code': 'woocommerce_rest_product_not_created',
                          'message': 'Sản phẩm có SKU (SP1) bạn đang cố gắng thêm đã có trong bảng tra cứu'})


so_lan_get = {'n': 0}


def fake_get_khong_thay_luc_dau_thay_lan_2(url, **kwargs):
    so_lan_get['n'] += 1
    if so_lan_get['n'] == 1:
        return FakeResp(200, [])   # kiem tra SKU LAN DAU (truoc khi POST) -> chua co, binh thuong
    return FakeResp(200, [{'id': 999}])   # lan do lai SAU KHI bi tu choi (trung SKU) -> tim thay


with patch('requests.post', side_effect=fake_post_trung_sku), \
     patch('requests.get', side_effect=fake_get_khong_thay_luc_dau_thay_lan_2):
    kq = AWP.dang_woo_that('ds1', 'r1', 'woo-recover.vn', 'chuan', 'SP 1', 'sp-1',
                           '<p>x</p>', 'y', ma_hang='SP1')

test('WOO-RECOVER-1', f'Bị từ chối vì trùng SKU -> tự tra lại, tìm thấy -> chuyển sang CẬP NHẬT thành công: {kq}',
     kq['ok'] is True and kq['wp_id'] == 999)
test('WOO-RECOVER-2', f'Chỉ thử tạo mới ĐÚNG 1 lần trước khi phát hiện trùng, rồi PUT đúng 1 lần: '
                     f'tao_moi={so_lan_post["tao_moi"]}, put_999={so_lan_post["put_999"]}',
     so_lan_post['tao_moi'] == 1 and so_lan_post['put_999'] == 1)

# ---- đối chứng: nếu tra lại vẫn KHÔNG thấy, vẫn báo lỗi rõ ràng, không lặp vô hạn ----
so_lan_post2 = {'tao_moi': 0}


def fake_post_tu_choi_mai(url, **kwargs):
    so_lan_post2['tao_moi'] += 1
    return FakeResp(400, {'message': 'Loi khac, khong lien quan SKU'})


def fake_get_khong_bao_gio_thay(url, **kwargs):
    return FakeResp(200, [])


with patch('requests.post', side_effect=fake_post_tu_choi_mai), \
     patch('requests.get', side_effect=fake_get_khong_bao_gio_thay):
    kq2 = AWP.dang_woo_that('ds1', 'r2', 'woo-recover.vn', 'chuan', 'SP 2', 'sp-2',
                            '<p>x</p>', 'y', ma_hang='SP2')

test('WOO-RECOVER-3', f'Tra lại vẫn không thấy -> báo lỗi rõ ràng, KHÔNG lặp vô hạn (chỉ thử tạo đúng 1 lần): '
                     f'ok={kq2["ok"]}, so_lan_tao={so_lan_post2["tao_moi"]}',
     kq2['ok'] is False and so_lan_post2['tao_moi'] == 1)

# ============================================================ NHÓM C — lịch sử đầy đủ các lần thử (chẩn đoán)
class FakeGeminiResp:
    def __init__(self, status_code, json_data):
        self.status_code, self._json = status_code, json_data

    def json(self):
        return self._json


def post_het_quota(url, **kwargs):
    return FakeGeminiResp(200, {'candidates': [{'finishReason': 'MAX_TOKENS', 'content': {'parts': []}}],
                                'usageMetadata': {}})


ROW = {'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'ten_goc': 'Cap test'}
with patch('requests.post', side_effect=post_het_quota):
    kq3, _ = AWP.goi_ai_co_du_phong(ROW, 'chuan', [('k1', 'model_a'), ('k1', 'model_b')], site_cfg={'ten': 'T'})

test('LICHSU-1', f'Có lịch sử đủ 2 lần thử, không chỉ lần cuối: {kq3.get("lich_su")}',
     len(kq3.get('lich_su', [])) == 2)
test('LICHSU-2', 'Lịch sử ghi rõ model của TỪNG lần thử (không chỉ lần cuối)',
     'model_a' in kq3['lich_su'][0] and 'model_b' in kq3['lich_su'][1])

print()
p = sum(1 for _, _, ok in KQ if ok)
print(f'TONG VER 4.8: {p}/{len(KQ)} PASS')
if p != len(KQ):
    sys.exit(1)
