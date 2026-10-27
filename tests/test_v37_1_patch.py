import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import importlib.util, os, sys, time
from unittest.mock import patch

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ver 5.1 -- test o tests/, du lieu/module chinh o thu muc goc (len 1 cap)
spec = importlib.util.spec_from_file_location('giao_dien', os.path.join(BASE, 'giao-dien.py'))
gd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gd)

import ai_wp_adapter as AWP
import db_phase2 as DB
import cauhinh as C
import autopost as A

KQ = []


def test(ma, mota, ok):
    KQ.append((ma, mota, bool(ok)))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}')


def cho_xong(app, vong=200, nghi=0.03):
    """Bơm Tk tới khi worker thật trả UI về trạng thái rảnh; không dùng fixed sleep."""
    het_han = time.time() + max(30.0, vong * nghi)
    while time.time() < het_han:
        app.update()
        if str(app.nut_v3_sinh_bai['state']) == 'normal':
            return
        time.sleep(nghi)
    raise AssertionError('Worker không kết thúc trong thời hạn test')


# ============================================================
# NHÓM A — Bug 1: exception ngoài dự kiến không được chết cả batch
# ============================================================
app = gd.PhanMem()
app.geometry('1366x768+0+0')
app.update()

app._phase2_lam_import(os.path.join(BASE, 'du_lieu_goc', 'MASTER_4_PROFILE_SAN_PHAM.xlsx'))
app._boc_hang_doi()
gt = [g for g in app.cb_phase2_dataset['values'] if 'may_bien_ap' in g][0]
app.v_phase2_dataset.set(gt)
app._v3_loc_san_pham()
app.update()
tat_ca_id = list(app.bang_phase2.get_children())
did = app._phase2_dataset_id_dang_chon()
con_loc = app._con_phase2()
try:
    tat_ca_id = [rid for rid in tat_ca_id
                 if not (DB.lay_san_pham(con_loc, did, rid) or {}).get('nghi_van_dien_ap')]
finally:
    con_loc.close()

app.v3_web_ten.set('Lotech Patch Test')
app.v3_web_url.set('https://patch-test.vn')
app.v3_web_user.set('admin')
app.v3_web_pw.set('abcd efgh ijkl')
app._v3_luu_website()
app.v3_gemini_key.set('FAKE_KEY')
C.luu_gemini('FAKE_KEY', 'gemini-2.5-flash')
app.v3_gemini_model.set('gemini-2.5-flash')
app.v3_che_do.set('that')
# Ver 3.9 A3 — harness: bỏ throttle production, giữ nguyên số record/job regression.
app.v3_nghi_giua_bai.set('0')
app.update()

import tkinter.messagebox as messagebox
_cu_askyesno = messagebox.askyesno
messagebox.askyesno = lambda *a, **k: True

site = app._v3_site_key()
_wp_counter = [3000]


def wp_ok(dataset_id, record_id, site, mau, title, slug, html, meta_desc):
    _wp_counter[0] += 1
    return {'ok': True, 'wp_id': _wp_counter[0], 'wp_url': f'https://patch-test.vn/?p={_wp_counter[0]}',
            'thoi_luong_giay': 0.01}


def ai_ok(row, mau, danh_sach_thu, site_cfg=None, **_kwargs):
    return ({'ok': True, 'data': {
        'meta_title': 'Tieu de san pham test', 'meta_description': 'Mo ta san pham dung de test batch.',
        'intro_html': '<p>gioi thieu</p>', 'dac_diem_html': '<p>dac diem</p>',
        'ung_dung_html': '<p>ung dung</p>',
    }, 'usage': {}, 'da_thu': 1, 'lich_su': []}, {})


def chon(ids):
    con = app._con_phase2()
    try:
        DB.dat_chon(con, did, tat_ca_id, chon=False)
        DB.dat_chon(con, did, ids, chon=True)
    finally:
        con.close()
    app._v3_loc_san_pham()
    app.update()


nhom_a = tat_ca_id[60:65]  # 5 record
rid_crash = nhom_a[1]      # record thứ 2 sẽ ném RuntimeError thật (không phải {'ok': False})
chon(nhom_a)


def ai_crash_record_2(row, mau, danh_sach_thu, site_cfg=None, **_kwargs):
    if row['record_id'] == rid_crash:
        raise RuntimeError('Lỗi giả lập KHÔNG được bắt bằng try/except thường (renderer hỏng, DB lỗi, v.v.)')
    return ai_ok(row, mau, danh_sach_thu, site_cfg)


with patch.object(AWP, 'goi_ai_co_du_phong', side_effect=ai_crash_record_2), \
     patch.object(AWP, 'dang_wp_that', side_effect=wp_ok):
    app._v3_dang_draft_that()
    cho_xong(app)

nhan_a = app.lb_v3_tien_do.cget('text')
test('PATCH-A1', f'RuntimeError ở record #2/5 KHÔNG làm chết batch — 4 record còn lại vẫn chạy xong '
                 f'— nhãn: "{nhan_a}"',
     'tạo/cập nhật 4, bỏ qua 0, lỗi 1 (tổng 5)' in nhan_a)

con = app._con_phase2()
bv_crash = DB.lay_bai_viet(con, did, rid_crash, site, 'chuan')
con.close()
test('PATCH-A2', f'Record crash được ghi trang_thai=loi kèm lý do (không bị bỏ trắng): {bv_crash}',
     bv_crash is not None and bv_crash['trang_thai'] == 'loi'
     and bv_crash['loi'] is not None and 'RuntimeError' in bv_crash['loi'])

test('PATCH-A3', f'Sau batch có lỗi crash, nút Sinh/Đăng phải MỞ LẠI (không kẹt disabled) — '
                 f'thực tế state={app.nut_v3_sinh_bai["state"]}',
     str(app.nut_v3_sinh_bai['state']) == 'normal')
test('PATCH-A4', f'Sau batch có lỗi crash, nút Dừng phải KHOÁ LẠI (không kẹt normal) — '
                 f'thực tế state={app.nut_v3_dung["state"]}',
     str(app.nut_v3_dung['state']) == 'disabled')

# ============================================================
# NHÓM B — Bug 2: không được đẻ slug-2 khi POST timeout VÀ dò slug cũng lỗi mạng
# ============================================================
class FakeResp:
    def __init__(self, status_code, json_data=None, text=''):
        self.status_code, self._json, self.text = status_code, json_data, text
    def json(self):
        return self._json


C.luu_website('B Test', 'https://bugb-test.vn', 'admin', 'abcd efgh ijkl')
so_lan_post_tao_moi = [0]
so_lan_get = [0]


def fake_post(url, **kwargs):
    if url.endswith('/wp-json/wp/v2/posts'):   # POST vào collection endpoint = TẠO MỚI
        so_lan_post_tao_moi[0] += 1
        raise __import__('requests').exceptions.Timeout('gia lap timeout')
    return FakeResp(200, {'id': 111, 'link': 'https://bugb-test.vn/?p=111'})


def fake_get_lan_1_ok_lan_2_loi_mang(url, **kwargs):
    so_lan_get[0] += 1
    if so_lan_get[0] == 1:
        return FakeResp(200, [])   # kiểm tra slug LẦN ĐẦU (trước khi POST) -> chưa có bài, bình thường
    raise __import__('requests').exceptions.ConnectionError('gia lap dut mang khi do slug LAN 2 (sau POST timeout)')


with patch('requests.post', side_effect=fake_post), \
     patch('requests.get', side_effect=fake_get_lan_1_ok_lan_2_loi_mang), \
     patch('time.sleep', return_value=None):   # bỏ qua 5s sleep thật cho test nhanh
    kq = AWP.dang_wp_that('ds_test', 'r_test', 'bugb-test.vn', 'chuan', 'Tieu de', 'slug-test',
                          '<p>noi dung</p>', 'meta mo ta')

test('PATCH-B1', f'POST tạo mới timeout + dò slug lại cũng lỗi mạng -> KHÔNG được trả ok=True, '
                 f'phải trả lỗi rõ ràng: {kq}',
     kq['ok'] is False and 'không thử tạo lại' in kq['loi'].lower())
test('PATCH-B2', f'CHỈ được thử POST tạo mới ĐÚNG 1 LẦN (không được đẻ slug-2) — '
                 f'thực tế số lần POST vào collection endpoint: {so_lan_post_tao_moi[0]}',
     so_lan_post_tao_moi[0] == 1)

# ---- Đối chứng: nếu da_co đã CÓ SẴN từ trước (bài chắc chắn tồn tại), lỗi
# dò slug tạm thời KHÔNG được chặn — vẫn phải thử PUT cập nhật lại bình
# thường (không đổi hành vi cũ trong trường hợp AN TOÀN). Dùng 1 record CÓ
# THẬT đã import (tránh vi phạm FOREIGN KEY của bảng san_pham_phase2). ----
con_cd = app._con_phase2()
try:
    did_cd = [g for g in app.cb_phase2_dataset['values'] if g.startswith('ds_cap_dien')]
    sp_cd = DB.liet_ke_san_pham(con_cd, dataset_id='ds_cap_dien_001')
    rid_cd = sp_cd[0]['record_id']
    DB.upsert_bai_viet_khoi_tao(con_cd, 'ds_cap_dien_001', rid_cd, 'bugb-test.vn', 'chuan')
    DB.cap_nhat_bai_viet(con_cd, 'ds_cap_dien_001', rid_cd, 'bugb-test.vn', 'chuan', wp_id='222')
finally:
    con_cd.close()

so_lan_put = [0]


def fake_post_put_ok_lan_2(url, **kwargs):
    if url.endswith('/222'):
        so_lan_put[0] += 1
        if so_lan_put[0] == 1:
            raise __import__('requests').exceptions.Timeout('gia lap timeout lan 1')
        return FakeResp(200, {'id': 222, 'link': 'https://bugb-test.vn/?p=222'})
    raise AssertionError('KHONG duoc POST vao collection endpoint khi da_co wp_id=222 tu truoc')


def fake_get_luon_loi(url, **kwargs):
    raise __import__('requests').exceptions.ConnectionError('gia lap dut mang')


with patch('requests.post', side_effect=fake_post_put_ok_lan_2), \
     patch('requests.get', side_effect=fake_get_luon_loi), \
     patch('time.sleep', return_value=None):
    kq2 = AWP.dang_wp_that('ds_cap_dien_001', rid_cd, 'bugb-test.vn', 'chuan', 'Tieu de 2', 'slug-test-2',
                           '<p>noi dung 2</p>', 'meta 2')

test('PATCH-B3', f'Khi ĐÃ có wp_id từ trước (an toàn), lỗi dò slug tạm thời KHÔNG chặn retry PUT — '
                 f'vẫn thành công ở lần thử sau: {kq2}',
     kq2['ok'] is True and kq2['wp_id'] == 222)

messagebox.askyesno = _cu_askyesno
app.destroy()

print()
p = sum(1 for _, _, ok in KQ if ok)
print(f'TONG VER 3.7.1 PATCH: {p}/{len(KQ)} PASS')
if p != len(KQ):
    sys.exit(1)
