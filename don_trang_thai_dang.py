# -*- coding: utf-8 -*-
"""DỌN TRẠNG THÁI ĐĂNG BÀI — chạy SAU KHI đã xoá sản phẩm trên WooCommerce.

VÌ SAO CẦN
----------
Xoá 245 sản phẩm trên site KHÔNG tự xoá trạng thái trong tool. Bảng
`bai_viet_phase2` vẫn giữ đủ 245 dòng với `wp_id` cũ, nên lượt đăng sau
tool sẽ tưởng bài đã có và gửi lệnh CẬP NHẬT cho một wp_id không còn tồn
tại -> đúng lỗi `woocommerce_rest_product_invalid_id` vừa gặp.

Dọn xong thì tool coi như chưa đăng gì, lượt sau sẽ TẠO MỚI sạch sẽ.

AN TOÀN
-------
* Tự sao lưu file .db trước khi đụng vào bất cứ thứ gì.
* Mặc định CHỈ IN RA, không xoá. Muốn xoá thật phải thêm --that.
* Chỉ xoá theo đúng site chỉ định, không đụng site khác.
* Không đụng bảng `san_pham_phase2` — 245 SKU và dữ liệu MASTER giữ nguyên.

DÙNG
----
    python don_trang_thai_dang.py --site maybienapvn.vn
    python don_trang_thai_dang.py --site maybienapvn.vn --that
    python don_trang_thai_dang.py --liet-ke        (xem có những site nào)
"""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent / 'phase2-du-lieu.db'


def mo():
    if not DB.exists():
        sys.exit(f'Không thấy {DB}. Chạy script này trong thư mục tool.')
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def liet_ke(con):
    print(f'{"SITE":28s} {"TRẠNG THÁI":12s}  SỐ DÒNG')
    print('-' * 52)
    for r in con.execute('SELECT site, trang_thai, COUNT(*) n FROM bai_viet_phase2 '
                         'GROUP BY site, trang_thai ORDER BY site, trang_thai'):
        print(f'{r["site"]:28s} {r["trang_thai"]:12s}  {r["n"]}')
    print()
    n_job = con.execute('SELECT COUNT(*) FROM article_jobs').fetchone()[0]
    print(f'article_jobs: {n_job} dòng (script này KHÔNG đụng tới)')


def sao_luu():
    dich = DB.with_name(f'{DB.stem}-truoc-khi-don-'
                        f'{datetime.now():%Y%m%d-%H%M%S}.db')
    shutil.copy(DB, dich)
    print(f'Đã sao lưu: {dich.name}')
    return dich


def don(con, site, that):
    rows = con.execute('SELECT trang_thai, COUNT(*) n, '
                       'SUM(CASE WHEN wp_id IS NOT NULL THEN 1 ELSE 0 END) co_wpid '
                       'FROM bai_viet_phase2 WHERE site=? GROUP BY trang_thai',
                       (site,)).fetchall()
    if not rows:
        print(f'Không có dòng nào cho site "{site}". Bấm --liet-ke xem tên site đúng.')
        return
    tong = sum(r['n'] for r in rows)
    print(f'\nSite: {site}')
    for r in rows:
        print(f'  {r["trang_thai"]:12s} {r["n"]:4d} dòng '
              f'({r["co_wpid"]} dòng có wp_id)')
    print(f'  {"TỔNG":12s} {tong:4d} dòng sẽ bị xoá khỏi bai_viet_phase2')

    mau = con.execute('SELECT record_id, wp_id, wp_url FROM bai_viet_phase2 '
                      'WHERE site=? AND wp_id IS NOT NULL LIMIT 3', (site,)).fetchall()
    if mau:
        print('\n  Ví dụ dòng sắp xoá:')
        for m in mau:
            print(f'    wp_id={m["wp_id"]}  {str(m["record_id"])[:52]}')

    if not that:
        print('\n[CHẠY THỬ] Chưa xoá gì. Thêm --that để xoá thật.')
        return

    sao_luu()
    con.execute('DELETE FROM bai_viet_phase2 WHERE site=?', (site,))
    con.commit()
    con_lai = con.execute('SELECT COUNT(*) FROM bai_viet_phase2 WHERE site=?',
                          (site,)).fetchone()[0]
    print(f'\nĐã xoá {tong} dòng. Còn lại cho site này: {con_lai}')

    sp = con.execute('SELECT COUNT(*) FROM san_pham_phase2').fetchone()[0]
    print(f'Kiểm tra: san_pham_phase2 vẫn còn {sp} dòng (KHÔNG bị đụng tới).')
    print('\nGiờ tool coi như chưa đăng bài nào lên site này.')
    print('Lượt đăng tới sẽ TẠO MỚI, không phải cập nhật.')
    print('\nNHỚ: tắt ô "Cho phép cập nhật lại bài ĐÃ ĐĂNG" trước khi chạy.')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--site', help='khoá site trong DB, xem bằng --liet-ke')
    p.add_argument('--that', action='store_true', help='xoá thật (mặc định chỉ chạy thử)')
    p.add_argument('--liet-ke', action='store_true', help='liệt kê site và số dòng')
    a = p.parse_args()
    con = mo()
    try:
        if a.liet_ke or not a.site:
            liet_ke(con)
            if not a.site:
                print('\nChưa chọn site. Chạy lại với --site <tên site ở cột SITE>')
            return
        don(con, a.site, a.that)
    finally:
        con.close()


main()
