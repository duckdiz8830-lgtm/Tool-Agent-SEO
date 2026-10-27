import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import importlib.util, os, sys, time
from unittest.mock import patch

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ver 5.1 -- test o tests/, du lieu/module chinh o thu muc goc (len 1 cap)
spec = importlib.util.spec_from_file_location('giao_dien', os.path.join(BASE,'giao-dien.py'))
gd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gd)

KQ = []
def test(ma, mota, ok, gc=''):
    KQ.append((ma,mota,bool(ok)))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}' + (f' ({gc})' if gc else ''))

class FakeResp:
    def __init__(self, status_code, json_data=None, text=''):
        self.status_code, self._json, self.text = status_code, json_data, text
    def json(self):
        return self._json

app = gd.PhanMem()
app.geometry('1366x768+0+0')
app.update()

# ---- import dữ liệu, chọn 1 record ----
app._phase2_lam_import(os.path.join(BASE,'du_lieu_goc','MASTER_4_PROFILE_SAN_PHAM.xlsx'))
app._boc_hang_doi()
gt = [g for g in app.cb_phase2_dataset['values'] if 'may_bien_ap' in g][0]
app.v_phase2_dataset.set(gt)
app._v3_loc_san_pham()
app.update()
import db_phase2 as DB
_did_real = app._phase2_dataset_id_dang_chon()
_con_real = app._con_phase2()
try:
    mot_dong = next(rid for rid in app.bang_phase2.get_children()
                    if not (DB.lay_san_pham(_con_real, _did_real, rid) or {}).get('nghi_van_dien_ap'))
finally:
    _con_real.close()
app.bang_phase2.focus(mot_dong)
app.bang_phase2.selection_set(mot_dong)
app.update()

# ---- Luồng mock vẫn hoạt động sau khi đổi site_cfg (không crash) ----
app._phase2_xem_prompt()
test('MOCK-1', 'Xem prompt vẫn hoạt động (không crash do site_cfg mới)', 'SYSTEM' in app.txt_phase2_thu.get('1.0','end'))
app._phase2_chay_thu()
test('MOCK-2', 'Chạy thử AI mock vẫn hoạt động', 'Title:' in app.txt_phase2_thu.get('1.0','end'))

app._phase2_chon_hang_loat(True)
app.update()
app.v_phase2_mau.set('chuan')
app._phase2_viec_chay_hang_loat('chuan', app._phase2_dataset_id_dang_chon(), app._v3_site_key(), app._v3_site_cfg())
app.update()

# Ver 3.6 Task 2 — SIẾT test, không cho pass giả: trước đây chỉ kiểm chuỗi
# "Xong" có mặt trong nhãn tiến độ (PASS dù có lỗi, miễn nhãn có chữ "Xong:
# 223/245 thành công, 22 lỗi" — vẫn chứa "Xong" nên PASS SAI). Giờ đếm THẬT
# qua DB, assert CHÍNH XÁC thành_cong == tổng và lỗi == 0.
import db_phase2 as DB
con_kiem = app._con_phase2()
try:
    did_kiem = app._phase2_dataset_id_dang_chon()
    tong_sp = DB.dem_san_pham(con_kiem, dataset_id=did_kiem)
    dash_kiem = DB.dashboard(con_kiem, dataset_id=did_kiem)
    thanh_cong = sum(1 for d in dash_kiem if d['trang_thai'] == 'da_dang')
    that_bai = sum(1 for d in dash_kiem if d['trang_thai'] == 'loi')
finally:
    con_kiem.close()
test('MOCK-3', f'Batch Mock ĐÚNG {tong_sp}/{tong_sp} thành công, 0 lỗi (đếm thật qua DB, không chỉ '
              f'kiểm chuỗi "Xong") — thực tế: {thanh_cong}/{tong_sp} thành công, {that_bai} lỗi',
     thanh_cong == tong_sp and that_bai == 0)
test('MOCK-3', f'Nhãn tiến độ khớp đúng số liệu DB: "{app.lb_v3_tien_do.cget("text")}"',
     f'{tong_sp}/{tong_sp}' in app.lb_v3_tien_do.cget('text') or f'Xong: {tong_sp}/{tong_sp}' in
     app.lb_v3_tien_do.cget('text'))

# ---- Cấu hình website + AI thật ----
app.v3_web_ten.set('Lotech Test')
app.v3_web_url.set('https://test-lotech.vn')
app.v3_web_user.set('admin')
app.v3_web_pw.set('abcd efgh ijkl')
app._v3_luu_website()
app.update()
test('CFG-1', f'Sau khi lưu website: site hiển thị = "{app.v_phase2_site.get()}", radio thật đã mở: '
             f'{str(app.rb_v3_that["state"])}',
     app.v_phase2_site.get()=='Lotech Test' and str(app.rb_v3_that['state'])=='normal')

app.v3_gemini_key.set('FAKE_KEY')
import cauhinh as C
C.luu_gemini('FAKE_KEY', 'gemini-2.5-flash')
app.v3_gemini_model.set('gemini-2.5-flash')

# ---- chuyển sang chế độ thật, nút đổi tên ----
app.v3_che_do.set('that')
app.update()
test('CFG-2', f'Nút Sinh bài đổi tên đúng khi chọn WordPress thật: "{app.nut_v3_sinh_bai["text"]}"',
     app.nut_v3_sinh_bai['text']=='Đăng Draft lên WordPress')

# ---- Ver 3.7: _v3_dang_draft_that() giờ chạy theo TOÀN BỘ record đang
# 'selected', không còn theo record active. Batch Mock ở trên (dòng 42) đã
# selected=1 cho CẢ dataset (245 record) — phải thu hẹp lại về đúng 1 record
# (mot_dong) trước khi test luồng Real, để test REAL-1/REAL-2 vẫn nhẹ và giữ
# đúng ý định gốc (kiểm 1 record thật, không phải benchmark 245 record thật).
app._phase2_chon_hang_loat(False)
import db_phase2 as DB
con_chon = app._con_phase2()
try:
    DB.dat_chon(con_chon, app._phase2_dataset_id_dang_chon(), [mot_dong], chon=True)
finally:
    con_chon.close()
app._v3_loc_san_pham()
app.update()

# ---- bấm đăng thật (mock toàn bộ HTTP + auto-confirm messagebox) ----
import tkinter.messagebox as messagebox
_cu_askyesno = messagebox.askyesno
messagebox.askyesno = lambda *a, **k: True
_cu_showinfo = messagebox.showinfo
_cu_showerror = messagebox.showerror
thong_bao_nhan = []
messagebox.showinfo = lambda tieu_de, nd: thong_bao_nhan.append(('info', tieu_de, nd))
messagebox.showerror = lambda tieu_de, nd: thong_bao_nhan.append(('error', tieu_de, nd))

with patch('requests.post') as mock_post, patch('requests.get') as mock_get:
    def fake_post(url, **kwargs):
        if 'generativelanguage' in url:
            return FakeResp(200, {
                'candidates': [{'content': {'parts': [{'text': __import__('json').dumps({
                    'meta_title': 'May bien ap that', 'meta_description': 'Mo ta that.',
                    'intro_html': '<p>gioi thieu</p>', 'dac_diem_html': '<p>dac diem</p>',
                    'ung_dung_html': '<p>ung dung</p>', 'huong_dan_chon_html': '<p>huong dan</p>',
                })}]}, 'finishReason': 'STOP'}],
                'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 10},
            })
        return FakeResp(201, {'id': 999, 'link': 'https://test-lotech.vn/?p=999'})
    def fake_get(url, **kwargs):
        # Ver 4.4.1 regression fixture: Woo product category assignment từ 3.8+
        # lookup category bằng ID trước khi create/update sản phẩm.
        if '/wp-json/wc/v3/products/categories' in url:
            ten = (kwargs.get('params') or {}).get('search', 'Danh mục test')
            return FakeResp(200, [{'id': 77, 'name': ten}])
        return FakeResp(200, [])  # tim_bai_theo_slug/SKU: chưa có bài nào
    mock_post.side_effect = fake_post
    mock_get.side_effect = fake_get

    app._v3_dang_draft_that()
    for _ in range(20):
        app.update()
        time.sleep(0.05)

test('REAL-1', f'Đăng Draft thật batch N=1 (mock HTTP) thành công, nhãn tiến độ: '
              f'"{app.lb_v3_tien_do.cget("text")}", lỗi messagebox: {thong_bao_nhan}',
     len(thong_bao_nhan) == 0 and 'tạo/cập nhật 1, bỏ qua 0, lỗi 0 (tổng 1)' in app.lb_v3_tien_do.cget('text'))

con = app._con_phase2()
import db_phase2 as DB
bv = DB.lay_bai_viet(con, app._phase2_dataset_id_dang_chon(), mot_dong, app._v3_site_key(), 'chuan')
con.close()
test('REAL-2', f'DB lưu đúng wp_id/url/trạng thái/thời lượng: {bv}',
     bv is not None and bv['wp_id']=='999' and bv['trang_thai']=='da_dang' and bv['thoi_luong_giay'] is not None)

messagebox.askyesno = _cu_askyesno
messagebox.showinfo = _cu_showinfo
messagebox.showerror = _cu_showerror

app.destroy()
print()
p = sum(1 for _,_,ok in KQ if ok)
print(f'TONG: {p}/{len(KQ)} PASS')
if p != len(KQ):
    sys.exit(1)
