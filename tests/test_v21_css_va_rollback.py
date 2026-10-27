# -*- coding: utf-8 -*-
"""Test Ver 2.1 — 2 tính năng từ audit kiến trúc:
  A. CSS ra ngoài (class thay inline) — giảm độ dài bài, KHÔNG đổi nội dung
  B. Gỡ bài hàng loạt (rollback) — đường lùi khi đăng nhầm

Chạy: python3 tests/test_v21_css_va_rollback.py
"""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import ai_wp_adapter as AWP
import db_phase2 as DB
import render_phase2 as R

so_pass = so_fail = 0


def kt(ten, dieu_kien, ghi_chu=''):
    global so_pass, so_fail
    if dieu_kien:
        so_pass += 1
        print(f'[PASS] {ten}')
    else:
        so_fail += 1
        print(f'[FAIL] {ten} {ghi_chu}')


# ==================================================== A. CSS class mode
def _row():
    return {'profile_id': 'may_bien_ap_do_luong', 'outline_id': 'outline_may_bien_ap',
            'ma_goc': 'TEST01', 'ten_goc': 'MBA dau 3 pha 250KVA 22/0.4KV Silic',
            'thuong_hieu': 'THIBIDI', 'dvt': 'Máy',
            'cong_suat': '250 kVA', 'cap_dien_ap': '22/0.4 kV'}


def _ai():
    doan = '<p>' + ' '.join(f'tu{i}' for i in range(80)) + '</p>'
    return {'meta_title': 'T', 'meta_description': 'M', 'intro_html': doan,
            'dac_diem_html': doan, 'ung_dung_html': doan, 'huong_dan_chon_html': doan}


def _text(h):
    return ' '.join(re.sub(r'<[^>]+>', ' ', h).split())


site = {'ten': 'Lotech', 'hotline': '0909'}

os.environ['CSS_CLASS_MODE'] = '0'
h_inline = R.dung_bai_html(_row(), _ai(), site)['html']
os.environ['CSS_CLASS_MODE'] = '1'
h_class = R.dung_bai_html(_row(), _ai(), site)['html']
os.environ['CSS_CLASS_MODE'] = '0'   # trả về mặc định, không ảnh hưởng test khác

kt('A1: chế độ INLINE (mặc định) vẫn sinh style= như cũ',
   'style="background:#f8fafc' in h_inline and 'class="snl-' not in h_inline)
kt('A2: chế độ CLASS sinh class= và KHÔNG còn inline style của ST',
   'class="snl-hero"' in h_class and 'style="background:#f8fafc' not in h_class)
kt('A3: NỘI DUNG TEXT giữ nguyên 100% giữa 2 chế độ (chỉ đổi cách gắn CSS)',
   _text(h_inline) == _text(h_class),
   f'inline={len(_text(h_inline))} vs class={len(_text(h_class))}')
giam = (1 - len(h_class) / len(h_inline)) * 100
kt(f'A4: chế độ CLASS giảm đáng kể độ dài bài (thực tế giảm {giam:.1f}%)', giam > 25)

css = R.xuat_file_css()
kt('A5: xuat_file_css() sinh đủ class cho MỌI khoá trong ST (không sót)',
   all(f'.{R.CLS[k]} ' in css for k in R.ST))
# Ver 2.5 — CSS xuất ra giờ GỘP cả bộ cũ (R.ST) lẫn bộ khối cao cấp
# (giao_dien_2_5.STYLE_2_5) + vài quy tắc media query, nên số khối {} lớn
# hơn len(R.ST). Chỉ kiểm cân bằng ngoặc và đủ class bộ cũ.
kt('A6: CSS cân bằng ngoặc và chứa đủ class bộ cũ',
   css.count('{') == css.count('}') and css.count('{') >= len(R.ST))

# ==================================================== B. Rollback
tmp_db = tempfile.mktemp(suffix='.db')
DB.DB_PATH = tmp_db
con = DB.ket_noi(tmp_db)
now = DB._now()
did = 'ds_rollback_test'
con.execute("INSERT INTO dataset VALUES (?,?,?,?,?,?,?,?,?,?,1)",
            (did, 'cap_dien', 'f.xlsx', 'c1', 'd1', 3, '[]', '2', now, now))
for i in range(3):
    rid = f'rec{i}'
    con.execute("INSERT INTO san_pham_phase2 VALUES (?,?,?,?,?,?,?,?)",
                (did, rid, 'cap_dien', 'outline_cap_dien', 'product',
                 json.dumps({'ma_goc': rid}), 1, 2))
    DB.upsert_bai_viet_khoi_tao(con, did, rid, 'site1', 'chuan')
    DB.cap_nhat_bai_viet(con, did, rid, 'site1', 'chuan', trang_thai='da_dang',
                         wp_id=str(700 + i), wp_url=f'https://x.vn/?p={700 + i}', ngay_dang=now)
# 1 bài CHƯA đăng — không được lọt vào danh sách gỡ
con.execute("INSERT INTO san_pham_phase2 VALUES (?,?,?,?,?,?,?,?)",
            (did, 'rec_chua_dang', 'cap_dien', 'outline_cap_dien', 'product',
             json.dumps({'ma_goc': 'rec_chua_dang'}), 1, 2))
DB.upsert_bai_viet_khoi_tao(con, did, 'rec_chua_dang', 'site1', 'chuan')
con.commit()

ds = DB.liet_ke_bai_da_dang(con, dataset_id=did)
kt('B1: liet_ke_bai_da_dang CHỈ trả bài đã đăng có wp_id (bỏ qua bài chưa đăng)',
   len(ds) == 3 and all(b['wp_id'] for b in ds))
con.close()

# giả lập WP: bài 701 lỗi, 702 trả 404 (coi như đã gỡ), còn lại OK
goc_go_1_bai = AWP.go_1_bai


def _gia_lap(wp_id, la_woo=False, vinh_vien=False, timeout=30):
    if wp_id == '701':
        return {'ok': False, 'loi': 'HTTP 500 (giả lập)'}
    if wp_id == '702':
        return {'ok': True, 'wp_id': wp_id, 'ghi_chu': 'Không tìm thấy trên WP'}
    return {'ok': True, 'wp_id': wp_id}


AWP.go_1_bai = _gia_lap
kq = AWP.go_bai_hang_loat(ds)
AWP.go_1_bai = goc_go_1_bai

kt('B2: lỗi 1 bài KHÔNG dừng cả batch (2 OK / 1 lỗi)',
   kq['ok'] == 2 and kq['loi'] == 1, str(kq))

con = DB.ket_noi(tmp_db)
tt = {r[0]: r[1] for r in con.execute(
    "SELECT record_id, trang_thai FROM bai_viet_phase2 WHERE dataset_id=?", (did,))}
kt('B3: bài gỡ thành công -> trang_thai=da_go', tt.get('rec0') == 'da_go', str(tt))
kt('B4: bài gỡ LỖI -> giữ nguyên da_dang (vì vẫn còn trên WP)',
   tt.get('rec1') == 'da_dang', str(tt))
kt('B5: bài 404 (đã xoá tay trước đó) -> vẫn đánh dấu da_go, không báo lỗi giả',
   tt.get('rec2') == 'da_go', str(tt))

wp_id_con = {r[0]: r[1] for r in con.execute(
    "SELECT record_id, wp_id FROM bai_viet_phase2 WHERE dataset_id=? AND record_id='rec0'", (did,))}
kt('B6: wp_id GIỮ NGUYÊN sau khi gỡ (để truy vết/khôi phục)',
   wp_id_con.get('rec0') == '700', str(wp_id_con))

con.close()
os.remove(tmp_db)

print(f'\nTỔNG VER 2.1 (CSS + ROLLBACK): {so_pass}/{so_pass + so_fail} PASS')


# ==================================================== C. Ver 2.2 — bỏ khối thừa + khử trùng công suất
import importlib
importlib.reload(R)

os.environ['BO_CTA_CUOI'] = '0'
os.environ['BO_ANH_PLACEHOLDER'] = '0'
os.environ['GIAO_DIEN_2_5'] = '0'   # Ver 2.6 — ép bố cục CŨ, phần C này test đúng bố cục cũ
h_cu = R.dung_bai_html(_row(), _ai(), {'ten': 'MBA VN'})['html']
os.environ['BO_CTA_CUOI'] = '1'
os.environ['BO_ANH_PLACEHOLDER'] = '1'
h_moi = R.dung_bai_html(_row(), _ai(), {'ten': 'MBA VN'})['html']
os.environ['BO_CTA_CUOI'] = '0'
os.environ['BO_ANH_PLACEHOLDER'] = '0'

# Ver 2.6 — record máy biến áp giờ VẼ ĐƯỢC sơ đồ nguyên lý (không cần
# kích thước) nên không còn ô placeholder. Dùng record KHÔNG vẽ được hình
# (phụ kiện) để kiểm hành vi placeholder.
_row_khong_hinh = {'profile_id': 'phu_kien_va_khac', 'outline_id': 'outline_phu_kien',
                   'ma_goc': 'PK01', 'ten_goc': 'Phụ kiện abc', 'thuong_hieu': 'X', 'dvt': 'Cái'}
_h_pk = R.dung_bai_html(_row_khong_hinh, _ai(), {'ten': 'MBA VN'})['html']
kt('C1: Ver 4.4 -> ô ảnh trống bị ẩn mặc định, CTA cuối vẫn giữ theo cờ riêng',
   'Liên hệ báo giá' in h_cu and 'CHỖ CHÈN' not in _h_pk and 'snl-cho-anh' not in _h_pk)
kt('C2: bật cờ -> bỏ khối "Liên hệ báo giá" cuối bài',
   'Liên hệ báo giá' not in h_moi)
kt('C3: bật cờ -> bỏ ô placeholder ảnh',
   'CHỖ CHÈN' not in h_moi)
kt('C4: KHÔNG còn link chết #lien-he-bao-gia sau khi bỏ khối đích',
   '#lien-he-bao-gia' not in h_moi)

# _so_kva phải parse được dữ liệu THẬT có đơn vị (bug ẩn Ver 2.2)
kt('C5: _so_kva parse đúng dữ liệu thật có đơn vị ("100 kVA")',
   DB._so_kva('100 kVA') == 100.0 and DB._so_kva('37.5kVA') == 37.5,
   f"100 kVA->{DB._so_kva('100 kVA')}, 37.5kVA->{DB._so_kva('37.5kVA')}")
kt('C6: _so_kva vẫn parse được số trần và trả None khi không có số',
   DB._so_kva('250') == 250.0 and DB._so_kva('abc') is None and DB._so_kva(None) is None)

print(f'\nTỔNG VER 2.2 (bỏ khối thừa + _so_kva): {so_pass}/{so_pass + so_fail} PASS tích luỹ')
sys.exit(1 if so_fail else 0)
