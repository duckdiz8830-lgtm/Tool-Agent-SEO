# -*- coding: utf-8 -*-
import importlib.util, sys
from pathlib import Path
from unittest.mock import patch
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
spec=importlib.util.spec_from_file_location('gui441', BASE/'giao-dien.py')
G=importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
import db_phase2 as DB

class V:
    def __init__(self,x): self.x=x
    def get(self): return self.x
class W:
    def config(self,**kw): pass
class E:
    def clear(self): pass
class Con:
    def close(self): pass
class Fake:
    v3_che_do=V('that'); v3_dung_lai=E(); nut_v3_sinh_bai=W(); nut_v3_tiep_tuc=W(); nut_v3_dung=W(); tien_do_v3=W(); lb_v3_tien_do=W()
    def _phase2_dataset_id_dang_chon(self): return 'D'
    def _phase2_mau_dang_chon(self): return 'chuan'
    def _con_phase2(self): return Con()
    def _v3_danh_sach_key_model_du_phong(self,gc): return [('k','m')]
    def _v3_nghi_giua_bai_giay(self): return 0.0
    def _v3_site_cfg(self): return {'ten':'x'}
    def chay_nen_phase2(self,fn): fn()
    def _v3_viec_dang_draft_that_hang_loat(self,*args): self.called=args

f=Fake()
rows=[{'record_id':'A'},{'record_id':'B'},{'record_id':'C'}]
def bv(_c,_d,rid,_s,_m):
    return {'wp_id':'111'} if rid=='A' else ({'wp_id':None} if rid=='B' else None)
with patch.object(G.C,'doc_website',return_value={'site_key':'site','url':'https://site','ten':'S'}), \
     patch.object(G.C,'doc_gemini',return_value={'api_key':'k','model':'m'}), \
     patch.object(DB,'liet_ke_san_pham',return_value=rows), \
     patch.object(DB,'lay_bai_viet',side_effect=bv), \
     patch.object(G.messagebox,'askyesno',return_value=True):
    G.PhanMem._v3_tiep_tuc_tu_cho_dung(f)
assert [r['record_id'] for r in f.called[0]] == ['B','C'], f.called[0]
assert f.called[5] is False, 'resume không được bật cập nhật bài có WP ID'

src=(BASE/'giao-dien.py').read_text(encoding='utf-8')
assert "'CHƯA CHẠY'" in src
assert 'loc_chua_chay' in src and 'co_wp' in src
assert "if not (bv and bv.get('wp_id'))" in src
print('PASS 5 / FAIL 0')
print('RESUME_RECORDS=B,C; A_WITH_WP_ID_SKIPPED=True')
print('TRACKER_CHUA_CHAY=WIRED_BY_NO_WP_ID')
