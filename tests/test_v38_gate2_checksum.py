# -*- coding: utf-8 -*-
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))

import nhap_phase2 as N


def main():
    base = {
        'ma_goc': 'SKU-001',
        'ten_goc': 'Sản phẩm thử',
        'thong_so_dong': {'Cột kỹ thuật mới': 'Giá trị A', 'Vật liệu': 'Đồng'},
    }
    changed = {
        'ma_goc': 'SKU-001',
        'ten_goc': 'Sản phẩm thử',
        'thong_so_dong': {'Cột kỹ thuật mới': 'Giá trị B', 'Vật liệu': 'Đồng'},
    }
    reordered_dynamic = {
        'ma_goc': 'SKU-001',
        'ten_goc': 'Sản phẩm thử',
        'thong_so_dong': {'Vật liệu': 'Đồng', 'Cột kỹ thuật mới': 'Giá trị A'},
    }

    h_a = N.data_checksum([base], ['ma_goc', 'ten_goc'])
    h_b = N.data_checksum([changed], ['ma_goc', 'ten_goc'])
    h_reorder_cols = N.data_checksum([base], ['ten_goc', 'ma_goc'])
    h_reorder_dynamic = N.data_checksum([reordered_dynamic], ['ma_goc', 'ten_goc'])

    print('A=', h_a)
    print('B=', h_b)
    print('REORDER_COLUMNS=', h_reorder_cols)
    print('REORDER_DYNAMIC=', h_reorder_dynamic)

    assert h_a != h_b, 'Đổi giá trị thong_so_dong nhưng checksum không đổi'
    assert h_a == h_reorder_cols, 'Đổi thứ tự cột cố định làm checksum đổi'
    assert h_a == h_reorder_dynamic, 'Đổi thứ tự key dynamic làm checksum đổi'
    print('PASS: dynamic A->B đổi checksum; reorder cột/key giữ nguyên checksum')


if __name__ == '__main__':
    main()
