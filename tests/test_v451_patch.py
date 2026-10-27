import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import sys
import db_phase2 as DB
import render_phase2 as R

KQ = []


def test(ma, mota, ok):
    KQ.append((ma, mota, bool(ok)))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}')


# ============================================================ NHÓM A — P0: Article Jobs là nguồn ứng viên hợp lệ
con = DB.ket_noi(':memory:')
DB.xac_nhan_dataset(con, 'cap_dien', 'x.xlsx', 'ck', 'dk', 1, {'a': 1})
did = DB.dataset_gan_nhat(con, 'cap_dien')['dataset_id']
DB.ghi_san_pham(con, did, [
    {'record_id': 'r1', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'content_type': 'product',
     'ten_goc': 'Cap goc', 'cap_dien_ap': '0.6/1', 'thuong_hieu': 'Cadivi'},
    {'record_id': 'r_job_only', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'content_type': 'product',
     'ten_goc': 'Cap chi dang qua Article Jobs', 'cap_dien_ap': '0.6/1', 'thuong_hieu': 'Cadivi'},
    {'record_id': 'r_job_pending', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'content_type': 'product',
     'ten_goc': 'Cap job chua xong', 'cap_dien_ap': '0.6/1', 'thuong_hieu': 'Cadivi'},
])
# r_job_only: CHỈ có trong article_jobs, trang_thai=SUCCESS -> phải được tìm thấy
job_id = DB.tao_job(con, did, 'r_job_only', 'site1.vn', 'chuan', 'outline_cap_dien')
DB.cap_nhat_job(con, job_id, trang_thai='SUCCESS', wp_url='https://site1.vn/job-only')
# r_job_pending: có job nhưng CHƯA SUCCESS -> KHÔNG được tính là ứng viên
job_id2 = DB.tao_job(con, did, 'r_job_pending', 'site1.vn', 'chuan', 'outline_cap_dien')
DB.cap_nhat_job(con, job_id2, trang_thai='PENDING')

lien_quan = DB.tim_san_pham_lien_quan(con, did, 'r1', 'site1.vn')
ten_lien_quan = [x['ten'] for x in lien_quan]
test('P0-1', f'Sản phẩm CHỈ đăng qua Article Jobs (SUCCESS) vẫn được tìm thấy: {ten_lien_quan}',
     'Cap chi dang qua Article Jobs' in ten_lien_quan)
test('P0-2', f'Job CHƯA SUCCESS (PENDING) không được tính là ứng viên: {ten_lien_quan}',
     'Cap job chua xong' not in ten_lien_quan)
url_job = next(x['url'] for x in lien_quan if x['ten'] == 'Cap chi dang qua Article Jobs')
test('P0-3', f'URL lấy đúng từ article_jobs.wp_url: {url_job}', url_job == 'https://site1.vn/job-only')

# ---- canonical: record có URL ở CẢ 2 nguồn -> ưu tiên bai_viet_phase2 ----
DB.ghi_san_pham(con, did, [
    {'record_id': 'r_ca_2', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'content_type': 'product',
     'ten_goc': 'Cap ca 2 nguon', 'cap_dien_ap': '0.6/1', 'thuong_hieu': 'Cadivi'},
])
DB.upsert_bai_viet_khoi_tao(con, did, 'r_ca_2', 'site1.vn', 'chuan')
DB.cap_nhat_bai_viet(con, did, 'r_ca_2', 'site1.vn', 'chuan', trang_thai='da_dang', wp_url='https://site1.vn/tu-bv')
job_id3 = DB.tao_job(con, did, 'r_ca_2', 'site1.vn', 'chuan', 'outline_cap_dien')
DB.cap_nhat_job(con, job_id3, trang_thai='SUCCESS', wp_url='https://site1.vn/tu-job')
lien_quan2 = DB.tim_san_pham_lien_quan(con, did, 'r1', 'site1.vn')
url_ca_2 = next(x['url'] for x in lien_quan2 if x['ten'] == 'Cap ca 2 nguon')
test('P0-4', f'Record có URL ở cả 2 nguồn -> ưu tiên bai_viet_phase2 (canonical): {url_ca_2}',
     url_ca_2 == 'https://site1.vn/tu-bv')
con.close()

# ============================================================ NHÓM B — P1: lọc theo site
con = DB.ket_noi(':memory:')
DB.xac_nhan_dataset(con, 'cap_dien', 'x.xlsx', 'ck', 'dk', 1, {'a': 1})
did = DB.dataset_gan_nhat(con, 'cap_dien')['dataset_id']
DB.ghi_san_pham(con, did, [
    {'record_id': 'r1', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'content_type': 'product',
     'ten_goc': 'Cap goc', 'cap_dien_ap': '0.6/1', 'thuong_hieu': 'Cadivi'},
    {'record_id': 'r_2_site', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'content_type': 'product',
     'ten_goc': 'Cap dang 2 site', 'cap_dien_ap': '0.6/1', 'thuong_hieu': 'Cadivi'},
])
DB.upsert_bai_viet_khoi_tao(con, did, 'r_2_site', 'site-a.vn', 'chuan')
DB.cap_nhat_bai_viet(con, did, 'r_2_site', 'site-a.vn', 'chuan', trang_thai='da_dang', wp_url='https://site-a.vn/p')
DB.upsert_bai_viet_khoi_tao(con, did, 'r_2_site', 'site-b.vn', 'chuan')
DB.cap_nhat_bai_viet(con, did, 'r_2_site', 'site-b.vn', 'chuan', trang_thai='da_dang', wp_url='https://site-b.vn/p')

lq_a = DB.tim_san_pham_lien_quan(con, did, 'r1', 'site-a.vn')
lq_b = DB.tim_san_pham_lien_quan(con, did, 'r1', 'site-b.vn')
test('P1-SITE-1', f'Đang đăng site-a.vn -> chỉ trả URL của site-a.vn: {lq_a}',
     lq_a and lq_a[0]['url'] == 'https://site-a.vn/p')
test('P1-SITE-2', f'Đang đăng site-b.vn -> chỉ trả URL của site-b.vn, KHÔNG lẫn site-a: {lq_b}',
     lq_b and lq_b[0]['url'] == 'https://site-b.vn/p')
con.close()

# ============================================================ NHÓM C — P1: điểm > 0, content_type, sort ổn định
con = DB.ket_noi(':memory:')
DB.xac_nhan_dataset(con, 'cap_dien', 'x.xlsx', 'ck', 'dk', 1, {'a': 1})
did = DB.dataset_gan_nhat(con, 'cap_dien')['dataset_id']
DB.ghi_san_pham(con, did, [
    {'record_id': 'r1', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'content_type': 'product',
     'ten_goc': 'Cap goc', 'cap_dien_ap': '0.6/1', 'thuong_hieu': 'Cadivi'},
    {'record_id': 'r_diem_0', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'content_type': 'product',
     'ten_goc': 'Khac ca dien ap lan thuong hieu', 'cap_dien_ap': '22/0.4', 'thuong_hieu': 'LS'},
    {'record_id': 'r_bang_diem_a', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'content_type': 'product',
     'ten_goc': 'B trung ten', 'cap_dien_ap': '99/1', 'thuong_hieu': 'Cadivi'},
    {'record_id': 'r_bang_diem_b', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'content_type': 'product',
     'ten_goc': 'A trung ten', 'cap_dien_ap': '99/1', 'thuong_hieu': 'Cadivi'},
    {'record_id': 'r_service', 'profile_id': 'cap_dien', 'outline_id': 'outline_service', 'content_type': 'service',
     'ten_goc': 'Dich vu cung profile', 'cap_dien_ap': '0.6/1', 'thuong_hieu': 'Cadivi'},
])
for rid, url in [('r_diem_0', 'https://s.vn/0'), ('r_bang_diem_a', 'https://s.vn/a'),
                 ('r_bang_diem_b', 'https://s.vn/b'), ('r_service', 'https://s.vn/sv')]:
    DB.upsert_bai_viet_khoi_tao(con, did, rid, 'site1.vn', 'chuan')
    DB.cap_nhat_bai_viet(con, did, rid, 'site1.vn', 'chuan', trang_thai='da_dang', wp_url=url)

lq = DB.tim_san_pham_lien_quan(con, did, 'r1', 'site1.vn')
ten_lq = [x['ten'] for x in lq]
test('P1-DIEM-1', f'Ứng viên điểm 0 (khác cả điện áp lẫn thương hiệu) KHÔNG được xuất hiện: {ten_lq}',
     'Khac ca dien ap lan thuong hieu' not in ten_lq)
test('P1-CT-1', f'Service KHÔNG xuất hiện trong danh sách liên quan của Product cùng profile: {ten_lq}',
     'Dich vu cung profile' not in ten_lq)
test('P1-SORT-1', f'2 ứng viên bằng điểm (chỉ cùng thương hiệu) sort ổn định theo tên: {ten_lq}',
     'A trung ten' in ten_lq and 'B trung ten' in ten_lq
     and ten_lq.index('A trung ten') < ten_lq.index('B trung ten'))
con.close()

# ============================================================ NHÓM D — P1: anchor CTA có đích thật
row = {'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'ma_goc': 'CD1',
      'ten_goc': 'Cap test', 'thuong_hieu': 'Cadivi', 'cap_dien_ap': '0.6/1'}
ai_data = {'meta_title': 'T', 'meta_description': 'M'}
site_cfg = {'ten': 'Lotech', 'hotline': '0909123456'}
bai = R.dung_bai_html(row, ai_data, site_cfg)
h = bai['html']
test('CTA-ANCHOR-1', 'HTML có id="lien-he-bao-gia" (đích thật cho CTA cuối trang — vẫn cần khi KHÔNG có hotline)',
     'id="lien-he-bao-gia"' in h)
test('CTA-ANCHOR-2', 'Ver 5.2: Nút "Yêu cầu báo giá" (CTA gọn) khi CÓ hotline -> gọi thẳng (tel:), không còn jump link (Thịnh: "khách nhấn vào là bắt luôn")',
     'tel:0909123456' in h and h.count('Yêu cầu báo giá') >= 1)

# ============================================================ NHÓM E — P2: Hero không còn lặp mã hàng/thương hiệu
h_hero = R.khoi_hero(row, site_cfg)
so_lan_ma = h_hero.count('CD1')
so_lan_hang = h_hero.count('Cadivi')
test('HERO-DEDUP-1', f'Mã hàng "CD1" chỉ xuất hiện đúng 1 lần trong Hero (không lặp ở specs): {so_lan_ma} lần',
     so_lan_ma == 1)
test('HERO-DEDUP-2', f'Thương hiệu "Cadivi" chỉ xuất hiện đúng 1 lần trong Hero: {so_lan_hang} lần',
     so_lan_hang == 1)

print()
p = sum(1 for _, _, ok in KQ if ok)
print(f'TONG VER 4.5.1 PATCH: {p}/{len(KQ)} PASS')
if p != len(KQ):
    sys.exit(1)
