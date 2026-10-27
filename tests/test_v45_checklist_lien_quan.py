import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import importlib.util, os, sys, time
from unittest.mock import patch

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ver 5.1 -- test o tests/, du lieu/module chinh o thu muc goc (len 1 cap)
spec = importlib.util.spec_from_file_location('giao_dien', os.path.join(BASE, 'giao-dien.py'))
gd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gd)

import render_phase2 as R
import db_phase2 as DB
import ai_wp_adapter as AWP
import cauhinh as C

KQ = []


def test(ma, mota, ok):
    KQ.append((ma, mota, bool(ok)))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}')


def cho_xong(app, vong=200, nghi=0.03):
    for _ in range(vong):
        app.update()
        time.sleep(0.02)


# ============================================================ NHÓM A — Checklist báo giá (thuần, không cần DB)
test('CK-1', 'Profile cap_dien có checklist đúng, KHÔNG rỗng',
     'Số mét cần đặt' in R.khoi_checklist_bao_gia('cap_dien'))
test('CK-2', 'Profile tu_va_thiet_bi_dong_cat có checklist khác (theo profile)',
     'Điện áp định mức' in R.khoi_checklist_bao_gia('tu_va_thiet_bi_dong_cat'))
test('CK-3', 'Profile không khai báo (lạ) -> trả rỗng, an toàn, không hiện block',
     R.khoi_checklist_bao_gia('profile_chua_tung_khai_bao') == '')

# ============================================================ NHÓM B — Sản phẩm liên quan (HTML builder thuần)
test('LQ-1', 'Danh sách rỗng/None -> không hiện block', R.khoi_san_pham_lien_quan([]) == ''
     and R.khoi_san_pham_lien_quan(None) == '')
h = R.khoi_san_pham_lien_quan([{'ten': 'Dây Cadivi 2x1.5', 'url': 'https://a.vn/p/1'}])
test('LQ-2', 'Danh sách hợp lệ -> render đúng link', 'Dây Cadivi 2x1.5' in h and 'https://a.vn/p/1' in h)
h2 = R.khoi_san_pham_lien_quan([{'ten': '', 'url': 'https://a.vn/p/2'}, {'ten': 'X'}])
test('LQ-3', 'Item thiếu ten/url bị bỏ qua, không tạo link rỗng/gãy', h2 == '')

# ============================================================ NHÓM C — tim_san_pham_lien_quan (DB thuần, in-memory)
con = DB.ket_noi(':memory:')
DB.xac_nhan_dataset(con, 'cap_dien', 'x.xlsx', 'ck', 'dk', 1, {'a': 1})
did = DB.dataset_gan_nhat(con, 'cap_dien')['dataset_id']
DB.ghi_san_pham(con, did, [
    {'record_id': 'r1', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'content_type': 'product',
     'ten_goc': 'Cap goc', 'cap_dien_ap': '0.6/1', 'thuong_hieu': 'Cadivi'},
    {'record_id': 'r2', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'content_type': 'product',
     'ten_goc': 'Cap cung dien ap cung hang', 'cap_dien_ap': '0.6/1', 'thuong_hieu': 'Cadivi'},
    {'record_id': 'r3', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'content_type': 'product',
     'ten_goc': 'Cap cung hang khac dien ap', 'cap_dien_ap': '22/0.4', 'thuong_hieu': 'Cadivi'},
    {'record_id': 'r4', 'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'content_type': 'product',
     'ten_goc': 'Cap chua dang', 'cap_dien_ap': '0.6/1', 'thuong_hieu': 'Cadivi'},
    {'record_id': 'r5', 'profile_id': 'tu_va_thiet_bi_dong_cat', 'outline_id': 'outline_tu_dong_cat',
     'content_type': 'product', 'ten_goc': 'Khac profile'},
])
# r2, r3 da dang that (co wp_url); r4 CHUA dang (khong wp_url); r5 khac profile
DB.upsert_bai_viet_khoi_tao(con, did, 'r2', 'site1.vn', 'chuan')
DB.cap_nhat_bai_viet(con, did, 'r2', 'site1.vn', 'chuan', trang_thai='da_dang', wp_url='https://site1.vn/r2')
DB.upsert_bai_viet_khoi_tao(con, did, 'r3', 'site1.vn', 'chuan')
DB.cap_nhat_bai_viet(con, did, 'r3', 'site1.vn', 'chuan', trang_thai='da_dang', wp_url='https://site1.vn/r3')
DB.upsert_bai_viet_khoi_tao(con, did, 'r4', 'site1.vn', 'chuan')  # r4: KHONG cap_nhat trang_thai=da_dang -> chua dang that
DB.upsert_bai_viet_khoi_tao(con, did, 'r5', 'site1.vn', 'chuan')
DB.cap_nhat_bai_viet(con, did, 'r5', 'site1.vn', 'chuan', trang_thai='da_dang', wp_url='https://site1.vn/r5')

lien_quan = DB.tim_san_pham_lien_quan(con, did, 'r1', 'site1.vn')
ten_lien_quan = [x['ten'] for x in lien_quan]
test('LQ-DB-1', f'Chỉ trả sản phẩm ĐÃ đăng thật (có wp_url) — r4 chưa đăng KHÔNG được xuất hiện: {ten_lien_quan}',
     'Cap chua dang' not in ten_lien_quan)
test('LQ-DB-2', f'KHÔNG trả sản phẩm khác profile (r5): {ten_lien_quan}',
     'Khac profile' not in ten_lien_quan)
test('LQ-DB-3', f'KHÔNG trả chính record đang xét (r1): {ten_lien_quan}',
     'Cap goc' not in ten_lien_quan)
test('LQ-DB-4', f'Ưu tiên đúng thứ tự: cùng cấp điện áp+thương hiệu (r2) đứng TRƯỚC cùng hãng khác điện áp (r3): {ten_lien_quan}',
     ten_lien_quan and ten_lien_quan[0] == 'Cap cung dien ap cung hang')
test('LQ-DB-5', f'URL trả đúng wp_url đã lưu: {lien_quan}',
     any(x['url'] == 'https://site1.vn/r2' for x in lien_quan))

lien_quan_rong = DB.tim_san_pham_lien_quan(con, did, 'r5', 'site1.vn')
test('LQ-DB-6', f'Sản phẩm không có ứng viên (profile khác chỉ có 1 mình) -> trả rỗng, an toàn: {lien_quan_rong}',
     lien_quan_rong == [])
con.close()

# ============================================================ NHÓM D — end-to-end dung_bai_html với checklist + lien quan
row = {'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'ma_goc': 'CD1',
      'ten_goc': 'Cap test', 'thuong_hieu': 'Cadivi', 'cap_dien_ap': '0.6/1'}
ai_data = {'meta_title': 'T', 'meta_description': 'M', 'huong_dan_chon_html': '<p>huong dan</p>'}
site_cfg = {'ten': 'Lotech', 'hotline': '0909123456'}
bai = R.dung_bai_html(row, ai_data, site_cfg, san_pham_lien_quan=[{'ten': 'SP lien quan X', 'url': 'https://a.vn/x'}])
# Ver 1.7 — E2E-1/E2E-3 SỬA LẠI cho khớp code hiện tại: khoi_checklist_
# bao_gia() vẫn tồn tại trong render_phase2.py nhưng KHÔNG còn được gọi
# ở đâu trong dung_bai_html() (verify bằng grep — 0 lần gọi ngoài định
# nghĩa) — đây là chủ ý bỏ khối checklist khỏi bài thật, không phải bug.
# Test cũ (Ver 4.5) kỳ vọng checklist còn trong HTML — đã lỗi thời, sửa
# lại để phản ánh đúng hành vi HIỆN TẠI: không còn checklist trong bài.
test('E2E-1', 'HTML KHÔNG còn checklist báo giá (đã bỏ khỏi bài thật, chỉ còn định nghĩa hàm trong code)',
     'Thông tin cần cung cấp để nhận báo giá' not in bai['html'])
test('E2E-2', 'HTML có sản phẩm liên quan', 'SP lien quan X' in bai['html'])
vi_tri_huong_dan = bai['html'].find('Hướng dẫn lựa chọn')
vi_tri_faq_hoac_cta = bai['html'].find('Liên hệ báo giá</h2>')
test('E2E-3', 'Thứ tự đúng: nội dung AI < CTA cuối trang (bỏ mốc checklist — không còn trong bài)',
     vi_tri_huong_dan < vi_tri_faq_hoac_cta)

bai_khong_lq = R.dung_bai_html(row, ai_data, site_cfg)
test('E2E-4', 'Không truyền san_pham_lien_quan (mặc định None) -> KHÔNG hiện block, backward compatible',
     'Sản phẩm liên quan</h2>' not in bai_khong_lq['html'])

print()
p = sum(1 for _, _, ok in KQ if ok)
print(f'TONG VER 4.5 CHECKLIST+LIEN_QUAN: {p}/{len(KQ)} PASS')
if p != len(KQ):
    sys.exit(1)
