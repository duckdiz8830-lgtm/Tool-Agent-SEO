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
import render_phase2 as R

KQ = []


def test(ma, mota, ok):
    KQ.append((ma, mota, bool(ok)))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}')


def cho_xong(app, vong=200, nghi=0.03):
    """Bơm Tk tới khi worker thật trả UI về trạng thái rảnh; không dùng fixed sleep."""
    het_han = time.time() + max(30.0, vong * nghi)
    while time.time() < het_han:
        app.update()
        if str(app.nut_jobs_dang['state']) == 'normal':
            return
        time.sleep(nghi)
    raise AssertionError('Worker không kết thúc trong thời hạn test')


# ============================================================
# NHÓM A — db_phase2.py: CRUD article_jobs thuần (không cần UI)
# ============================================================
con_a = DB.ket_noi(':memory:')
DB.xac_nhan_dataset(con_a, 'cap_dien', 'x.xlsx', 'ck1', 'dk1', 1, {'a': 1})
did_a = DB.dataset_gan_nhat(con_a, 'cap_dien')['dataset_id']
DB.ghi_san_pham(con_a, did_a, [{'record_id': 'r1', 'profile_id': 'cap_dien',
                                   'outline_id': 'outline_cap_dien', 'content_type': 'product',
                                   'ten_goc': 'Cap test'}])

test('JOB-A1', 'Chưa có job nào -> liet_ke_jobs() trả rỗng',
     DB.liet_ke_jobs(con_a, dataset_id=did_a) == [])

moi = DB.dam_bao_job_mac_dinh(con_a, did_a, ['r1'], 'site1.vn', 'chuan')
test('JOB-A2', f'dam_bao_job_mac_dinh() tạo đúng 1 job mặc định cho record chưa có job: {moi}',
     len(moi) == 1)

moi2 = DB.dam_bao_job_mac_dinh(con_a, did_a, ['r1'], 'site1.vn', 'chuan')
test('JOB-A3', 'Gọi lại dam_bao_job_mac_dinh() trên record ĐÃ có job -> KHÔNG tạo thêm (idempotent)',
     moi2 == [] and len(DB.liet_ke_jobs(con_a, dataset_id=did_a)) == 1)

job1 = DB.liet_ke_jobs(con_a, dataset_id=did_a)[0]
test('JOB-A4', f'Job mặc định lấy đúng outline_id đã routing sẵn của record: {job1["outline_id"]}',
     job1['outline_id'] == 'outline_cap_dien' and job1['sequence'] == 1 and job1['trang_thai'] == 'PENDING')

job_id_2 = DB.tao_job(con_a, did_a, 'r1', 'site1.vn', 'chuan', 'outline_phu_kien')
jobs_sau_them = DB.liet_ke_jobs(con_a, dataset_id=did_a)
test('JOB-A5', f'+ Thêm job: record giờ có 2 job, sequence tự tăng: {[(j["sequence"], j["outline_id"]) for j in jobs_sau_them]}',
     len(jobs_sau_them) == 2 and {j['sequence'] for j in jobs_sau_them} == {1, 2})

ok_doi = DB.doi_outline_job(con_a, job_id_2, 'outline_service')
test('JOB-A6', 'Đổi outline cho job PENDING -> thành công',
     ok_doi and DB.lay_job(con_a, job_id_2)['outline_id'] == 'outline_service')

DB.cap_nhat_job(con_a, job_id_2, trang_thai='SUCCESS', wp_id='999')
ok_doi_2 = DB.doi_outline_job(con_a, job_id_2, 'outline_cap_dien')
test('JOB-A7', 'Đổi outline cho job ĐÃ SUCCESS -> KHÔNG cho đổi (giữ nguyên lịch sử)',
     ok_doi_2 is False and DB.lay_job(con_a, job_id_2)['outline_id'] == 'outline_service')

ok_xoa_success = DB.xoa_job(con_a, job_id_2)
test('JOB-A8', 'Xoá job ĐÃ SUCCESS -> KHÔNG cho xoá',
     ok_xoa_success is False and len(DB.liet_ke_jobs(con_a, dataset_id=did_a)) == 2)

ok_xoa_pending = DB.xoa_job(con_a, job1['job_id'])
test('JOB-A9', 'Xoá job PENDING -> thành công',
     ok_xoa_pending and len(DB.liet_ke_jobs(con_a, dataset_id=did_a)) == 1)
con_a.close()

# ============================================================
# NHÓM B — render_phase2.py: slug không đè nhau giữa các job
# ============================================================
row_b = {'ma_goc': 'CD150', 'record_id': 'r_b', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien'}
slug_job1 = R.dung_slug(row_b, 'chuan')                 # job đầu tiên — KHÔNG hậu tố
slug_job2 = R.dung_slug(row_b, 'chuan', hau_to='b2')    # job thứ 2
slug_job3 = R.dung_slug(row_b, 'chuan', hau_to='b3')

test('JOB-B1', f'Job đầu tiên (sequence=1) giữ NGUYÊN slug như luồng cũ (không hậu tố): {slug_job1}',
     slug_job1 == 'cd150-chuan')
test('JOB-B2', f'Job 2 và job 3 của CÙNG record có slug KHÁC nhau và khác job 1: {slug_job1}, {slug_job2}, {slug_job3}',
     len({slug_job1, slug_job2, slug_job3}) == 3)

bai_job2 = R.dung_bai_html(row_b, {'meta_title': 'T', 'meta_description': 'M'}, {'ten': 'X'},
                           mau='chuan', hau_to_slug='b2')
test('JOB-B3', f'dung_bai_html() với hau_to_slug áp đúng vào slug đầu ra: {bai_job2["slug"]}',
     bai_job2['slug'] == slug_job2)

# ============================================================
# NHÓM C — ai_wp_adapter.dang_wp_that: da_co_wp_id không đọc nhầm bai_viet_phase2
# ============================================================
class FakeResp:
    def __init__(self, status_code, json_data=None, text=''):
        self.status_code, self._json, self.text = status_code, json_data, text
    def json(self):
        return self._json


import cauhinh as C
C.luu_website('Job Test', 'https://job-test.vn', 'admin', 'abcd efgh ijkl')

con_c = DB.ket_noi(':memory:')
DB.xac_nhan_dataset(con_c, 'cap_dien', 'y.xlsx', 'ck2', 'dk2', 1, {'a': 1})
did_c = DB.dataset_gan_nhat(con_c, 'cap_dien')['dataset_id']
DB.ghi_san_pham(con_c, did_c, [{'record_id': 'rc1', 'profile_id': 'cap_dien',
                                   'outline_id': 'outline_cap_dien', 'content_type': 'product'}])
# Giả lập: record này ĐÃ có 1 bài đăng qua luồng CŨ (Ver 3.7, bai_viet_phase2), wp_id=111
DB.upsert_bai_viet_khoi_tao(con_c, did_c, 'rc1', 'job-test.vn', 'chuan')
DB.cap_nhat_bai_viet(con_c, did_c, 'rc1', 'job-test.vn', 'chuan', wp_id='111')
con_c.close()

so_lan_post = {'tao_moi': 0, 'update_111': 0}


def fake_post_job(url, **kwargs):
    if url.endswith('/wp-json/wp/v2/posts'):
        so_lan_post['tao_moi'] += 1
        return FakeResp(201, {'id': 222, 'link': 'https://job-test.vn/?p=222'})
    if url.endswith('/111'):
        so_lan_post['update_111'] += 1
        return FakeResp(200, {'id': 111, 'link': 'https://job-test.vn/?p=111'})
    return FakeResp(404, {})


def fake_get_chua_co_bai(url, **kwargs):
    return FakeResp(200, [])   # tim_bai_theo_slug: chưa có bài nào trùng slug này


with patch('requests.post', side_effect=fake_post_job), \
     patch('requests.get', side_effect=fake_get_chua_co_bai):
    # Job MỚI của record rc1 (job['wp_id'] = None, vì đây là job KHÁC, chưa từng đăng)
    # -> phải TẠO MỚI, KHÔNG được đè lên wp_id=111 của luồng cũ dù cùng record/site/mau
    kq_job_moi = AWP.dang_wp_that(did_c, 'rc1', 'job-test.vn', 'chuan', 'Tieu de job 2', 'rc1-chuan-b2',
                                  '<p>noi dung job 2</p>', 'meta', da_co_wp_id=None)

test('JOB-C1', f'Job MỚI (da_co_wp_id=None) của record đã có bài cũ (wp_id=111 ở bai_viet_phase2) '
              f'PHẢI tạo bài MỚI, không đè lên 111: {kq_job_moi}',
     kq_job_moi['ok'] is True and kq_job_moi['wp_id'] == 222)
test('JOB-C2', f'Đúng 1 lần POST tạo mới, KHÔNG có lần nào PUT vào /111: '
              f'tao_moi={so_lan_post["tao_moi"]}, update_111={so_lan_post["update_111"]}',
     so_lan_post['tao_moi'] == 1 and so_lan_post['update_111'] == 0)

# ---- đối chứng: job ĐÃ CÓ wp_id riêng (chạy lại lần 2) phải PUT đúng vào ID của NÓ ----
so_lan_post2 = {'update_222': 0}


def fake_post_job2(url, **kwargs):
    if url.endswith('/222'):
        so_lan_post2['update_222'] += 1
        return FakeResp(200, {'id': 222, 'link': 'https://job-test.vn/?p=222'})
    raise AssertionError('Job đã có wp_id=222 từ trước -> KHÔNG được POST vào collection endpoint')


with patch('requests.post', side_effect=fake_post_job2):
    kq_job_rerun = AWP.dang_wp_that(did_c, 'rc1', 'job-test.vn', 'chuan', 'Tieu de job 2 sua',
                                    'rc1-chuan-b2', '<p>sua lai</p>', 'meta', da_co_wp_id='222')

test('JOB-C3', f'Chạy lại job đã có wp_id riêng -> PUT đúng vào wp_id của job đó: {kq_job_rerun}',
     kq_job_rerun['ok'] is True and kq_job_rerun['wp_id'] == 222 and so_lan_post2['update_222'] == 1)

# ============================================================
# NHÓM D — UI đầy đủ: tạo job mặc định, +/- job, đổi outline, chạy batch,
#          1 job lỗi không chặn job khác, Force Stop riêng biệt với tab 4
# ============================================================
app = gd.PhanMem()
app.geometry('1366x768+0+0')
app.update()
app._phase2_lam_import(os.path.join(BASE, 'du_lieu_goc', 'MASTER_4_PROFILE_SAN_PHAM.xlsx'))
app._boc_hang_doi()
gt = [g for g in app.cb_phase2_dataset['values'] if g.startswith('ds_cap_dien')][0]
app.v_phase2_dataset.set(gt)
app._v3_loc_san_pham()
app.update()
did = app._phase2_dataset_id_dang_chon()
tat_ca_id = list(app.bang_phase2.get_children())

app.v3_web_ten.set('Job UI Test')
app.v3_web_url.set('https://job-ui-test.vn')
app.v3_web_user.set('admin')
app.v3_web_pw.set('abcd efgh ijkl')
app._v3_luu_website()
app.v3_gemini_key.set('FAKE_KEY')
C.luu_gemini('FAKE_KEY', 'gemini-2.5-flash')
app.v3_gemini_model.set('gemini-2.5-flash')
# Ver 3.9 A3 — harness: bỏ throttle production, giữ nguyên số record/job regression.
app.v3_nghi_giua_bai.set('0')
app.update()

import tkinter.messagebox as messagebox
_cu_askyesno = messagebox.askyesno
_cu_info = messagebox.showinfo
_cu_warn = messagebox.showwarning
messagebox.askyesno = lambda *a, **k: True
messagebox.showinfo = lambda *a, **k: None
messagebox.showwarning = lambda *a, **k: None

nhom_d = tat_ca_id[0:3]
con = app._con_phase2()
try:
    DB.dat_chon(con, did, tat_ca_id, chon=False)
    DB.dat_chon(con, did, nhom_d, chon=True)
finally:
    con.close()
app._v3_loc_san_pham()
app.update()

app._jobs_tao_mac_dinh()
app.update()
con = app._con_phase2()
try:
    jobs_ban_dau = DB.liet_ke_jobs(con, dataset_id=did)
finally:
    con.close()
test('JOB-D1', f'Bấm "Tạo job mặc định" cho 3 sản phẩm đã chọn -> đúng 3 job PENDING: {len(jobs_ban_dau)}',
     len(jobs_ban_dau) == 3 and all(j['trang_thai'] == 'PENDING' for j in jobs_ban_dau))
test('JOB-D2', 'Bảng Treeview hiện đủ 3 dòng job',
     len(app.bang_jobs.get_children()) == 3)

# ---- + Thêm job cho 1 record, đổi outline ----
app.bang_jobs.focus(app.bang_jobs.get_children()[0])
app.bang_jobs.selection_set(app.bang_jobs.get_children()[0])
oid_khac = [k for k, v in app._jobs_outline_map.items() if v == 'outline_phu_kien'][0]
app.v_jobs_outline.set(oid_khac)
app._jobs_them()
app.update()
con = app._con_phase2()
try:
    jobs_sau_them = DB.liet_ke_jobs(con, dataset_id=did)
finally:
    con.close()
test('JOB-D3', f'"+ Thêm job" tạo thêm đúng 1 job (tổng 4), outline theo dropdown đang chọn: '
              f'{[(j["record_id"][-4:], j["sequence"], j["outline_id"]) for j in jobs_sau_them]}',
     len(jobs_sau_them) == 4 and any(j['sequence'] == 2 and j['outline_id'] == 'outline_phu_kien'
                                     for j in jobs_sau_them))

# ---- xoá đúng job vừa thêm (job PENDING, xoá được) ----
app._jobs_nap()
app.update()
iid_job2 = None
for iid in app.bang_jobs.get_children():
    if int(app.bang_jobs.item(iid, 'values')[2]) == 2:
        iid_job2 = iid
        break
app.bang_jobs.focus(iid_job2)
app.bang_jobs.selection_set(iid_job2)
app._jobs_xoa()
app.update()
con = app._con_phase2()
try:
    jobs_sau_xoa = DB.liet_ke_jobs(con, dataset_id=did)
finally:
    con.close()
test('JOB-D4', f'"- Xoá job" xoá đúng job PENDING vừa thêm, về lại 3 job: {len(jobs_sau_xoa)}',
     len(jobs_sau_xoa) == 3)

# ---- chạy batch job THẬT (mock qua adapter), 1 job lỗi không chặn job khác ----
rid_loi_job = jobs_sau_xoa[1]['record_id']


def ai_ok(row, mau, danh_sach_thu, site_cfg=None, **_kwargs):
    return ({'ok': True, 'data': {
        'meta_title': 'Tieu de test job', 'meta_description': 'Mo ta san pham dung de test job batch.',
        'intro_html': '<p>i</p>', 'dac_diem_html': '<p>d</p>', 'ung_dung_html': '<p>u</p>',
    }, 'usage': {}, 'da_thu': 1, 'lich_su': []}, {})


def ai_loi_1_job(row, mau, danh_sach_thu, site_cfg=None, **_kwargs):
    if row['record_id'] == rid_loi_job:
        return ({'ok': False, 'loi': 'Loi Gemini gia lap cho 1 job', 'da_thu': 1, 'lich_su': []}, {})
    return ai_ok(row, mau, danh_sach_thu, site_cfg)


_wp_ctr = [5000]


def wp_ok(dataset_id, record_id, site, mau, title, slug, html, meta_desc, da_co_wp_id=None):
    _wp_ctr[0] += 1
    return {'ok': True, 'wp_id': _wp_ctr[0], 'wp_url': f'https://job-ui-test.vn/?p={_wp_ctr[0]}',
           'thoi_luong_giay': 0.01}


with patch.object(AWP, 'goi_ai_co_du_phong', side_effect=ai_loi_1_job), \
     patch.object(AWP, 'dang_wp_that', side_effect=wp_ok):
    app._jobs_dang_that()
    cho_xong(app)

nhan_jobs = app.lb_jobs_tien_do.cget('text')
test('JOB-D5', f'Chạy batch 3 job, 1 job lỗi (Gemini giả lập) không chặn 2 job còn lại — nhãn: "{nhan_jobs}"',
     'Xong: 2/3 job thành công, 1 lỗi' in nhan_jobs)

con = app._con_phase2()
try:
    jobs_ket_qua = DB.liet_ke_jobs(con, dataset_id=did)
finally:
    con.close()
so_success = sum(1 for j in jobs_ket_qua if j['trang_thai'] == 'SUCCESS')
so_error = sum(1 for j in jobs_ket_qua if j['trang_thai'] == 'ERROR')
test('JOB-D6', f'DB xác nhận đúng 2 SUCCESS, 1 ERROR: success={so_success}, error={so_error}',
     so_success == 2 and so_error == 1)

test('JOB-D7', 'Sau batch, nút Đăng Jobs mở lại, nút Dừng Jobs khoá lại',
     str(app.nut_jobs_dang['state']) == 'normal' and str(app.nut_jobs_dung['state']) == 'disabled')

# ---- Force Stop của tab Article Jobs KHÔNG đụng cờ/nút của tab 4 (Ver 3.7) ----
test('JOB-D8', 'jobs_dung_lai là Event RIÊNG, khác hẳn v3_dung_lai (2 luồng độc lập)',
     app.jobs_dung_lai is not app.v3_dung_lai)

messagebox.askyesno = _cu_askyesno
messagebox.showinfo = _cu_info
messagebox.showwarning = _cu_warn
app.destroy()

print()
p = sum(1 for _, _, ok in KQ if ok)
print(f'TONG VER 3.9 ARTICLE JOBS: {p}/{len(KQ)} PASS')
if p != len(KQ):
    sys.exit(1)
