# -*- coding: utf-8 -*-
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))

import importlib.util
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

import ai_wp_adapter as AWP
import db_phase2 as DB
import nhap_phase2 as N

BASE = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('giao_dien_gate6', BASE / 'giao-dien.py')
gd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gd)


class FakeApp:
    def __init__(self): self.v3_dung_lai = threading.Event()
    def _con_phase2(self): return DB.ket_noi()
    def ui(self, fn): fn()
    def _v3_cap_nhat_tien_do_that(self, *args): pass
    def _v3_nap_dashboard(self): pass
    def _v3_ket_thuc_chay(self, *args): pass


def main():
    with tempfile.TemporaryDirectory(prefix='snl-g6-') as td:
        DB.DB_PATH = Path(td) / 'phase2.db'
        rpt = N.import_phase2_pipeline(BASE / 'du_lieu_goc' / 'MASTER_4_PROFILE_SAN_PHAM.xlsx', db_path=DB.DB_PATH)
        did = rpt['ket_qua_theo_profile']['may_bien_ap_do_luong']['dataset_id']
        con = DB.ket_noi(); row = DB.liet_ke_san_pham(con, dataset_id=did)[0]; con.close()
        row = dict(row)
        row['nghi_van_dien_ap'] = True
        calls = {'ai': 0, 'wp': 0}

        def fake_ai(*a, **k):
            calls['ai'] += 1
            raise AssertionError('AI không được gọi khi validation BLOCK')
        def fake_wp(*a, **k):
            calls['wp'] += 1
            raise AssertionError('WordPress không được gọi khi validation BLOCK')

        wc = {'site_key': 'mock.local', 'che_do_dang': 'woo_product', 'ten': 'Mock', 'url': 'https://mock.local'}
        app = FakeApp()
        with patch.object(AWP, 'goi_ai_co_du_phong', side_effect=fake_ai), \
             patch.object(AWP, 'dang_woo_that', side_effect=fake_wp), \
             patch.object(AWP, 'dang_wp_that', side_effect=fake_wp):
            gd.PhanMem._v3_viec_dang_draft_that_hang_loat(
                app, [row], 'chuan', [('K','M')], wc, 0.0, False,
                {'bat': False, 'serper_key': '', 'cong_dong': False}, {'ten':'Mock'}, '')

        con = DB.ket_noi()
        bv = DB.lay_bai_viet(con, did, row['record_id'], 'mock.local', 'chuan')
        con.close()
        print('AI_CALLS=', calls['ai'])
        print('WP_CALLS=', calls['wp'])
        print('STATE=', bv.get('trang_thai') if bv else None)
        print('REASON=', bv.get('loi') if bv else None)
        assert calls == {'ai': 0, 'wp': 0}
        assert bv and bv['trang_thai'] == 'loi' and 'BLOCKED: nghi_van_dien_ap=True' in (bv['loi'] or '')
        print('PASS: validation chặn trước AI/WordPress')

if __name__ == '__main__': main()
