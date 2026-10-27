#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ver 3.5 — công cụ kiểm tra kết quả, không cần mở giao diện. In ra: record đã
xử lý, Gemini/Hard Block thành công hay lỗi, WP ID, URL, trạng thái Draft,
thời lượng, lỗi cuối.

DÙNG LẠI NGUYÊN các hàm đã có trong db_phase2.py (dashboard, liet_ke_dataset,
liet_ke_san_pham, dinh_dang_thoi_gian, dinh_dang_thoi_luong) — file này
KHÔNG tự viết logic đọc/định dạng DB riêng, chỉ gọi lại đúng hàm GUI cũng
đang dùng ở tab "5. Theo dõi". `5-KIEM-TRA-KET-QUA.bat` chỉ là wrapper gọi
thẳng file này, không có logic gì khác trong .bat.

Chạy: python3 cong_cu_kiem_tra_ket_qua.py [--dataset DATASET_ID] [--site SITE_KEY]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db_phase2 as DB   # noqa: E402


def in_bao_cao(dataset_id=None, site=None):
    con = DB.ket_noi()
    try:
        ds_list = DB.liet_ke_dataset(con)
        if not ds_list:
            print('Chưa có dataset nào — chưa nhập file Excel nào qua tab "1. Nhập dữ liệu".')
            return

        print('=' * 70)
        print('DANH SÁCH DATASET ĐÃ NHẬP')
        print('=' * 70)
        for d in ds_list:
            print(f'  {d["dataset_id"]:<28} {d["profile_id"]:<24} {d["row_count"]:>6} record   '
                 f'cập nhật {d["updated_at"]}')

        dash = DB.dashboard(con, dataset_id=dataset_id, site=site)
        print()
        print('=' * 70)
        print(f'BÀI VIẾT ĐÃ XỬ LÝ' + (f' — dataset={dataset_id}' if dataset_id else '')
             + (f' — site={site}' if site else ''))
        print('=' * 70)
        if not dash:
            print('  (chưa có bài nào được sinh/đăng)')
        else:
            ten_cache = {}
            tong_theo_trang_thai = {}
            for d in dash:
                if d['dataset_id'] not in ten_cache:
                    sp_list = DB.liet_ke_san_pham(con, dataset_id=d['dataset_id'])
                    ten_cache[d['dataset_id']] = {x['record_id']: x.get('ten_goc', '') for x in sp_list}
                ten_sp = ten_cache[d['dataset_id']].get(d['record_id'], '')
                bv = DB.lay_bai_viet(con, d['dataset_id'], d['record_id'], d['site'], d['mau'])
                loi = (bv or {}).get('loi') or ''
                tong_theo_trang_thai[d['trang_thai']] = tong_theo_trang_thai.get(d['trang_thai'], 0) + 1

                print(f'  [{d["trang_thai"]:<10}] {ten_sp[:40]:<40} mẫu={d["mau"]:<9} site={d["site"]}')
                print(f'      record_id: {d["record_id"]}')
                if d['wp_id']:
                    print(f'      WP ID: {d["wp_id"]}   URL: {d["wp_url"]}')
                if d['ngay_dang']:
                    print(f'      Đăng lúc: {DB.dinh_dang_thoi_gian(d["ngay_dang"])}   '
                         f'Thời lượng: {DB.dinh_dang_thoi_luong(d["thoi_luong_giay"])}')
                if loi:
                    print(f'      LỖI: {loi}')
                print()

            print('-' * 70)
            print('TỔNG KẾT:', ', '.join(f'{k}={v}' for k, v in tong_theo_trang_thai.items()))
    finally:
        con.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Kiểm tra kết quả sinh bài/đăng WordPress (Ver 3.5).')
    ap.add_argument('--dataset', default=None, help='Lọc theo dataset_id (mặc định: tất cả)')
    ap.add_argument('--site', default=None, help='Lọc theo site_key/URL đã chuẩn hoá (mặc định: tất cả)')
    args = ap.parse_args()
    in_bao_cao(dataset_id=args.dataset, site=args.site)
