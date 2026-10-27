# -*- coding: utf-8 -*-
"""Ver 4.4.1.7 — test kéo bài đã đăng theo dataset mới.

Tái hiện đúng sự cố 13/08/2026: sửa MASTER -> tạo dataset mới ->
245 bài đã đăng mồ côi ở dataset cũ -> dashboard() JOIN rỗng ->
"thiếu identity DB" chặn 245/245, KHÔNG có cảnh báo nào.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_TMP = tempfile.mkdtemp()
os.environ['SONEALEO_DATA_DIR'] = _TMP

import db_phase2 as DB   # noqa: E402

PROFILE = 'may_bien_ap_do_luong'


def rid(dong, sku):
    return f'{PROFILE}::03_May_Bien_Ap_Do_Luong::{dong}::{sku}'


class TestChuyenBai(unittest.TestCase):

    def setUp(self):
        self.f = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.f.close()
        self.con = DB.ket_noi(self.f.name)
        self._ds('ds_cu', active=0)
        self._ds('ds_moi', active=1)

    def tearDown(self):
        self.con.close()
        os.unlink(self.f.name)

    def _ds(self, did, active=1):
        self.con.execute(
            'INSERT INTO dataset (dataset_id, profile_id, source_file, file_checksum,'
            ' data_checksum, row_count, column_structure, pipeline_version,'
            ' created_at, updated_at, active) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
            (did, PROFILE, 'x.xlsx', 'fc', 'dc' + did, 0, '[]', 'v',
             '2026-08-13T00:00:00', '2026-08-13T00:00:00', active))
        self.con.commit()

    def _sp(self, did, danh_sach_rid):
        for r in danh_sach_rid:
            # KHÔNG dùng INSERT OR IGNORE: nó nuốt luôn lỗi NOT NULL, khiến
            # san_pham không được ghi rồi bai_viet vỡ khoá ngoại ở tận dòng
            # dưới — mất công truy ngược. Ghi đủ mọi cột NOT NULL.
            self.con.execute(
                'INSERT INTO san_pham_phase2 (dataset_id, record_id, profile_id,'
                ' outline_id, content_type, du_lieu_json, pipeline_version)'
                ' VALUES (?,?,?,?,?,?,?)',
                (did, r, PROFILE, 'outline_mba', 'san_pham', '{}', 'test'))
        self.con.commit()

    def _bai(self, did, r, wp_id=None, site='maybienapvn.vn', mau='chuan'):
        self.con.execute(
            'INSERT INTO bai_viet_phase2 (dataset_id, record_id, site, mau, wp_id)'
            ' VALUES (?,?,?,?,?)', (did, r, site, mau, wp_id))
        self.con.commit()

    def _dem(self, did):
        return self.con.execute(
            'SELECT COUNT(*) FROM bai_viet_phase2 WHERE dataset_id=?', (did,)).fetchone()[0]

    # ------------------------------------------------------------------
    def test_tai_hien_su_co_13_08_va_sua_duoc(self):
        """243 record giữ nguyên record_id, 2 record đổi SKU (sửa newline)."""
        cu = [rid(100 + i, f'SKU{i}') for i in range(243)]
        cu += [rid(343, 'ETPB3KAAGHT-5-\nCL0.5'), rid(344, 'ETPB3KAAGGHT-5-\nCL0.2')]
        moi = [rid(100 + i, f'SKU{i}') for i in range(243)]
        moi += [rid(343, 'ETPB3KAAGHT-5-CL0.5'), rid(344, 'ETPB3KAAGGHT-5-CL0.2')]
        self._sp('ds_cu', cu)
        self._sp('ds_moi', moi)
        for i, r in enumerate(cu):
            self._bai('ds_cu', r, wp_id=(1000 + i) if i < 243 else None)

        bc = DB.chuyen_bai_sang_dataset_moi(self.con, PROFILE, 'ds_moi')

        self.assertEqual(bc['bai_chuyen'], 243)
        self.assertEqual(len(bc['mo_coi']), 2)
        self.assertEqual(self._dem('ds_moi'), 243)
        self.assertEqual(self._dem('ds_cu'), 2)      # mồ côi GIỮ NGUYÊN, không xoá

    def test_join_dashboard_song_lai(self):
        """Đúng phép JOIN mà dashboard() dùng — nguồn gốc 'thiếu identity'."""
        rs = [rid(1, 'A'), rid(2, 'B')]
        self._sp('ds_cu', rs)
        self._sp('ds_moi', rs)
        for r in rs:
            self._bai('ds_cu', r, wp_id=1)
        truoc = self.con.execute(
            'SELECT COUNT(*) FROM bai_viet_phase2 bv JOIN san_pham_phase2 sp '
            'ON bv.dataset_id=sp.dataset_id AND bv.record_id=sp.record_id '
            'WHERE bv.dataset_id=?', ('ds_moi',)).fetchone()[0]
        self.assertEqual(truoc, 0)                   # đúng trạng thái hỏng
        DB.chuyen_bai_sang_dataset_moi(self.con, PROFILE, 'ds_moi')
        sau = self.con.execute(
            'SELECT COUNT(*) FROM bai_viet_phase2 bv JOIN san_pham_phase2 sp '
            'ON bv.dataset_id=sp.dataset_id AND bv.record_id=sp.record_id '
            'WHERE bv.dataset_id=?', ('ds_moi',)).fetchone()[0]
        self.assertEqual(sau, 2)

    def test_giu_nguyen_wp_id(self):
        r = rid(1, 'A')
        self._sp('ds_cu', [r]); self._sp('ds_moi', [r])
        self._bai('ds_cu', r, wp_id=1290)
        DB.chuyen_bai_sang_dataset_moi(self.con, PROFILE, 'ds_moi')
        self.assertEqual(self.con.execute(
            'SELECT wp_id FROM bai_viet_phase2 WHERE dataset_id=?',
            ('ds_moi',)).fetchone()[0], '1290')  # cột wp_id kiểu TEXT

    def test_KHONG_ghi_de_bai_da_co_o_dataset_moi(self):
        r = rid(1, 'A')
        self._sp('ds_cu', [r]); self._sp('ds_moi', [r])
        self._bai('ds_cu', r, wp_id=111)
        self._bai('ds_moi', r, wp_id=999)            # bản mới đang sống
        bc = DB.chuyen_bai_sang_dataset_moi(self.con, PROFILE, 'ds_moi')
        self.assertEqual(bc['bai_chuyen'], 0)
        self.assertEqual(len(bc['trung_khoa']), 1)
        self.assertEqual(self.con.execute(
            'SELECT wp_id FROM bai_viet_phase2 WHERE dataset_id=?',
            ('ds_moi',)).fetchone()[0], '999')         # KHÔNG bị 111 đè

    def test_chay_lai_lan_hai_khong_lam_gi_them(self):
        rs = [rid(1, 'A'), rid(2, 'B')]
        self._sp('ds_cu', rs); self._sp('ds_moi', rs)
        for r in rs:
            self._bai('ds_cu', r, wp_id=1)
        DB.chuyen_bai_sang_dataset_moi(self.con, PROFILE, 'ds_moi')
        bc2 = DB.chuyen_bai_sang_dataset_moi(self.con, PROFILE, 'ds_moi')
        self.assertEqual(bc2['bai_chuyen'], 0)
        self.assertEqual(self._dem('ds_moi'), 2)

    def test_bao_cao_ro_bai_mo_coi_co_wp_id(self):
        """Mồ côi mà CÓ wp_id = bài thật trên web mất liên kết — phải nói ra."""
        self._sp('ds_cu', [rid(1, 'CU')])
        self._sp('ds_moi', [rid(1, 'MOI')])
        self._bai('ds_cu', rid(1, 'CU'), wp_id=1290)
        bc = DB.chuyen_bai_sang_dataset_moi(self.con, PROFILE, 'ds_moi')
        self.assertEqual(len(bc['mo_coi']), 1)
        self.assertEqual(str(bc['mo_coi'][0]['wp_id']), '1290')

    def test_khong_co_dataset_cu_thi_khong_vo(self):
        self._sp('ds_moi', [rid(1, 'A')])
        self.con.execute("DELETE FROM dataset WHERE dataset_id='ds_cu'")
        self.con.commit()
        bc = DB.chuyen_bai_sang_dataset_moi(self.con, PROFILE, 'ds_moi')
        self.assertEqual(bc['bai_chuyen'], 0)
        self.assertEqual(bc['loi'], '')

    def test_goi_sai_thu_tu_thi_bao_loi_chu_khong_im(self):
        """Gọi trước ghi_san_pham: dataset mới chưa có sản phẩm nào."""
        self._sp('ds_cu', [rid(1, 'A')])
        self._bai('ds_cu', rid(1, 'A'), wp_id=1)
        bc = DB.chuyen_bai_sang_dataset_moi(self.con, PROFILE, 'ds_moi')
        self.assertIn('sai thứ tự', bc['loi'])
        self.assertEqual(self._dem('ds_cu'), 1)      # không đụng gì

    def test_article_jobs_di_theo(self):
        r = rid(1, 'A')
        self._sp('ds_cu', [r]); self._sp('ds_moi', [r])
        self._bai('ds_cu', r, wp_id=1)
        # Ghi đủ cột NOT NULL. KHÔNG bọc try/skipTest: test bị skip là test
        # không kiểm gì cả — schema đổi thì phải ĐỎ để biết mà sửa.
        self.con.execute(
            'INSERT INTO article_jobs (job_id, dataset_id, record_id, site, mau,'
            ' outline_id, sequence, trang_thai, created_at, updated_at)'
            ' VALUES (?,?,?,?,?,?,?,?,?,?)',
            ('j1', 'ds_cu', r, 'maybienapvn.vn', 'chuan', 'outline_mba', 1,
             'DONE', '2026-08-13T00:00:00', '2026-08-13T00:00:00'))
        self.con.commit()
        bc = DB.chuyen_bai_sang_dataset_moi(self.con, PROFILE, 'ds_moi')
        self.assertEqual(bc['job_chuyen'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
