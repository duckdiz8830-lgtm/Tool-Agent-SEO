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


app = gd.PhanMem()
app.geometry('1366x768+0+0')
app.update()

# ---- Import MASTER, chọn dataset máy biến áp (245 record) ----
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

# ---- Cấu hình website + Gemini giả, chuyển chế độ 'that' ----
app.v3_web_ten.set('Lotech Test 37')
app.v3_web_url.set('https://test37.vn')
app.v3_web_user.set('admin')
app.v3_web_pw.set('abcd efgh ijkl')
app._v3_luu_website()
app.v3_gemini_key.set('FAKE_KEY')
import cauhinh as C
C.luu_gemini('FAKE_KEY', 'gemini-2.5-flash')
app.v3_gemini_model.set('gemini-2.5-flash')
app.v3_che_do.set('that')
# Ver 3.9 A3 — harness: khoảng nghỉ 5s là throttle production, không phải
# hành vi cần regression ở test batch. Giữ NGUYÊN 5+17+17+6 record nhưng
# đặt nghỉ=0 để test không tự chờ hàng chục giây giữa các record mock.
app.v3_nghi_giua_bai.set('0')
app.update()

import tkinter.messagebox as messagebox
_cu_askyesno = messagebox.askyesno
messagebox.askyesno = lambda *a, **k: True

_wp_counter = [2000]


def wp_ok(dataset_id, record_id, site, mau, title, slug, html, meta_desc):
    _wp_counter[0] += 1
    return {'ok': True, 'wp_id': _wp_counter[0], 'wp_url': f'https://test37.vn/?p={_wp_counter[0]}',
            'thoi_luong_giay': 0.01}


def chon(ids):
    app._phase2_chon_hang_loat(False)
    con = app._con_phase2()
    try:
        DB.dat_chon(con, did, ids, chon=True)
    finally:
        con.close()
    app._v3_loc_san_pham()
    app.update()


# ============================================================
# T1 — 5 record, tất cả thành công
# ============================================================
nhom1 = tat_ca_id[0:5]
chon(nhom1)
goi_ai_lan = {'n': 0}


def ai_ok_luon(row, mau, danh_sach_thu, site_cfg=None, **_kwargs):
    goi_ai_lan['n'] += 1
    return ({'ok': True, 'data': {
        'meta_title': 'Tieu de that', 'meta_description': 'Mo ta that.',
        'intro_html': '<p>gioi thieu</p>', 'dac_diem_html': '<p>dac diem</p>',
        'ung_dung_html': '<p>ung dung</p>',
    }, 'usage': {}, 'da_thu': 1, 'lich_su': []}, {})


with patch.object(AWP, 'goi_ai_co_du_phong', side_effect=ai_ok_luon), \
     patch.object(AWP, 'dang_wp_that', side_effect=wp_ok):
    app._v3_dang_draft_that()
    cho_xong(app)

nhan1 = app.lb_v3_tien_do.cget('text')
test('T1', f'Chọn 5 record, tất cả thành công — nhãn: "{nhan1}"',
     'tạo/cập nhật 5, bỏ qua 0, lỗi 0 (tổng 5)' in nhan1 and goi_ai_lan['n'] == 5)

con = app._con_phase2()
site = app._v3_site_key()
so_da_dang = sum(1 for rid in nhom1
                  if (DB.lay_bai_viet(con, did, rid, site, 'chuan') or {}).get('trang_thai') == 'da_dang')
con.close()
test('T1b', f'DB xác nhận đúng 5/5 record trạng thái da_dang (thực tế {so_da_dang}/5)', so_da_dang == 5)

# ============================================================
# T2 — 17 record, cố ý làm record thứ 5 lỗi -> 6..17 vẫn chạy tiếp
# ============================================================
nhom2 = tat_ca_id[10:27]  # 17 record mới, không đụng nhóm 1
chon(nhom2)
rid_loi = nhom2[4]  # record thứ 5 trong danh sách chọn


def ai_loi_1_record(row, mau, danh_sach_thu, site_cfg=None, **_kwargs):
    if row['record_id'] == rid_loi:
        return ({'ok': False, 'loi': 'Timeout gia lap khi goi Gemini', 'da_thu': 1, 'lich_su': []}, {})
    return ai_ok_luon(row, mau, danh_sach_thu, site_cfg)


with patch.object(AWP, 'goi_ai_co_du_phong', side_effect=ai_loi_1_record), \
     patch.object(AWP, 'dang_wp_that', side_effect=wp_ok):
    app._v3_dang_draft_that()
    cho_xong(app)

nhan2 = app.lb_v3_tien_do.cget('text')
test('T2', f'Chọn 17 record, record #5 lỗi, 16 record còn lại vẫn chạy xong — nhãn: "{nhan2}"',
     'tạo/cập nhật 16, bỏ qua 0, lỗi 1 (tổng 17)' in nhan2)

con = app._con_phase2()
bv_loi = DB.lay_bai_viet(con, did, rid_loi, site, 'chuan')
so_da_dang2 = sum(1 for rid in nhom2
                   if (DB.lay_bai_viet(con, did, rid, site, 'chuan') or {}).get('trang_thai') == 'da_dang')
con.close()
test('T2b', f'Record lỗi đúng trạng thái loi, có ghi lý do: {bv_loi}',
     bv_loi is not None and bv_loi['trang_thai'] == 'loi' and bool(bv_loi['loi']))
test('T2c', f'16/17 record còn lại đã da_dang (thực tế {so_da_dang2}/17)', so_da_dang2 == 16)

# ============================================================
# T3 — chạy lại CÙNG 17 record: 16 đã da_dang phải được BỎ QUA (không gọi
# lại Gemini/WordPress), chỉ record lỗi cũ được xử lý lại
# ============================================================
goi_ai_lan['n'] = 0
goi_lai_theo_id = []


def ai_dem_goi(row, mau, danh_sach_thu, site_cfg=None, **_kwargs):
    goi_lai_theo_id.append(row['record_id'])
    return ai_ok_luon(row, mau, danh_sach_thu, site_cfg)


with patch.object(AWP, 'goi_ai_co_du_phong', side_effect=ai_dem_goi), \
     patch.object(AWP, 'dang_wp_that', side_effect=wp_ok):
    app._v3_dang_draft_that()
    cho_xong(app)

nhan3 = app.lb_v3_tien_do.cget('text')
test('T3', f'Chạy lại 17 record cũ: chỉ gọi AI cho ĐÚNG 1 record (đã lỗi lần trước), '
          f'16 record da_dang được bỏ qua — nhãn: "{nhan3}", record đã gọi lại: {goi_lai_theo_id}',
     'tạo/cập nhật 1, bỏ qua 16, lỗi 0 (tổng 17)' in nhan3
     and goi_lai_theo_id == [rid_loi])

# ============================================================
# T4 — Dừng an toàn giữa batch: bấm Force Stop giữa chừng, tiến độ các
# record ĐÃ xong không bị mất; record chưa chạy vẫn ở trạng thái chờ và
# chạy tiếp được ở lần sau
# ============================================================
nhom4 = tat_ca_id[40:46]  # 6 record mới
chon(nhom4)
da_goi_t4 = []


def ai_cham(row, mau, danh_sach_thu, site_cfg=None, **_kwargs):
    da_goi_t4.append(row['record_id'])
    time.sleep(0.15)  # giả lập độ trễ mạng để có thời gian bấm Dừng giữa batch
    return ai_ok_luon(row, mau, danh_sach_thu, site_cfg)


with patch.object(AWP, 'goi_ai_co_du_phong', side_effect=ai_cham), \
     patch.object(AWP, 'dang_wp_that', side_effect=wp_ok):
    app._v3_dang_draft_that()
    # đợi đúng 2 record chạy xong rồi bấm Dừng khẩn cấp
    for _ in range(60):
        app.update()
        time.sleep(0.03)
        if len(da_goi_t4) >= 2:
            break
    app._v3_force_stop()
    cho_xong(app, vong=100)

con = app._con_phase2()
trang_thai_t4 = {rid: (DB.lay_bai_viet(con, did, rid, site, 'chuan') or {}).get('trang_thai', 'chua_sinh')
                 for rid in nhom4}
con.close()
so_da_xong_t4 = sum(1 for v in trang_thai_t4.values() if v == 'da_dang')
so_chua_chay_t4 = sum(1 for v in trang_thai_t4.values() if v == 'chua_sinh')
test('T4', f'Dừng giữa batch: record đã xong không mất tiến độ, record chưa chạy vẫn ở trạng thái '
          f'chờ (không kẹt lỡ dở) — chi tiết: {trang_thai_t4}',
     so_da_xong_t4 >= 1 and so_da_xong_t4 < len(nhom4) and so_chua_chay_t4 == (len(nhom4) - so_da_xong_t4))

# ---- chạy lại phần còn lại sau khi dừng: phải hoàn tất nốt, không đụng
# record đã da_dang ----
da_goi_t4b = []


def ai_dem_t4b(row, mau, danh_sach_thu, site_cfg=None, **_kwargs):
    da_goi_t4b.append(row['record_id'])
    return ai_ok_luon(row, mau, danh_sach_thu, site_cfg)


with patch.object(AWP, 'goi_ai_co_du_phong', side_effect=ai_dem_t4b), \
     patch.object(AWP, 'dang_wp_that', side_effect=wp_ok):
    app._v3_dang_draft_that()
    cho_xong(app)

nhan4b = app.lb_v3_tien_do.cget('text')
test('T4b', f'Chạy tiếp sau khi dừng: hoàn tất đủ {len(nhom4)}/{len(nhom4)}, không gọi lại record đã '
           f'xong (chỉ gọi {len(da_goi_t4b)} record còn thiếu) — nhãn: "{nhan4b}"',
     f'tạo/cập nhật {so_chua_chay_t4}, bỏ qua {so_da_xong_t4}, lỗi 0 (tổng {len(nhom4)})' in nhan4b and len(da_goi_t4b) == so_chua_chay_t4)

messagebox.askyesno = _cu_askyesno
app.destroy()

print()
p = sum(1 for _, _, ok in KQ if ok)
print(f'TONG VER 3.7: {p}/{len(KQ)} PASS')
if p != len(KQ):
    sys.exit(1)
