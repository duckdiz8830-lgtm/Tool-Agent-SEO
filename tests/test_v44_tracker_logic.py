# -*- coding: utf-8 -*-
"""Ver 4.4 — functional logic cho bảng Theo dõi, không cần Tk/Xvfb visual."""
import importlib.util, json, sqlite3, sys, tempfile
from pathlib import Path
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
import db_phase2 as DB
spec=importlib.util.spec_from_file_location('giao_dien_v44_tracker', BASE/'giao-dien.py')
G=importlib.util.module_from_spec(spec); spec.loader.exec_module(G)

P=F=0
def ck(name, cond, detail=''):
    global P,F
    if cond: P+=1; print(f'PASS {name}: {detail}')
    else: F+=1; print(f'FAIL {name}: {detail}')

class Var:
    def __init__(self,v=''): self.v=v
    def get(self): return self.v
    def set(self,v): self.v=v
class Box:
    def __init__(self): self.d={}
    def __setitem__(self,k,v): self.d[k]=v
    def __getitem__(self,k): return self.d.get(k, ())
class Label:
    def __init__(self): self.text=''
    def config(self,**kw): self.text=kw.get('text',self.text)
class Tree:
    def __init__(self): self.rows=[]
    def get_children(self): return [r[0] for r in self.rows]
    def delete(self,*ids): self.rows=[]
    def insert(self,parent,index,iid=None,values=(),tags=()): self.rows.append((iid,tuple(values),tuple(tags))); return iid

with tempfile.TemporaryDirectory() as td:
    dbp=Path(td)/'t.db'
    con=DB.ket_noi(dbp)
    now='2026-08-10T00:00:00+00:00'
    con.execute("INSERT INTO dataset(dataset_id,profile_id,source_file,file_checksum,data_checksum,row_count,column_structure,pipeline_version,created_at,updated_at,active) VALUES(?,?,?,?,?,?,?,?,?,?,1)",
                ('D','may_bien_ap_do_luong','x.xlsx','f','d',3,'[]','p',now,now))
    rows=[
      ('R1','MBT3P750','Máy biến áp dầu MBT 3 pha 750KVA 22/0.4KV Loại Amorphous','MBT'),
      ('R2','TBD3P250','Máy biến áp dầu THIBIDI 3 pha 250KVA 22/0.4KV Loại Silic','THIBIDI'),
      ('R3','TBD3P400','Máy biến áp dầu THIBIDI 3 pha 400KVA 22/0.4KV Loại Silic','THIBIDI'),
    ]
    for rid,sku,ten,hang in rows:
        data={'dataset_id':'D','record_id':rid,'profile_id':'may_bien_ap_do_luong','outline_id':'outline_may_bien_ap','content_type':'product','ma_goc':sku,'publish_sku':sku,'ten_goc':ten,'thuong_hieu':hang}
        con.execute("INSERT INTO san_pham_phase2(dataset_id,record_id,profile_id,outline_id,content_type,du_lieu_json,selected,pipeline_version) VALUES(?,?,?,?,?,?,1,?)",
                    ('D',rid,'may_bien_ap_do_luong','outline_may_bien_ap','product',json.dumps(data,ensure_ascii=False),'p'))
    states=[('R1','da_dang','101','https://real/p1',''),('R2','loi',None,None,'Hard Block chặn meta dài chi tiết'),('R3','da_dang','103','https://real/p3','')]
    for rid,st,wid,url,loi in states:
        con.execute("INSERT INTO bai_viet_phase2(dataset_id,record_id,site,mau,trang_thai,wp_id,wp_url,loi) VALUES(?,?,?,?,?,?,?,?)",('D',rid,'real.local','chuan',st,wid,url,loi))
    con.commit(); con.close()

    o=object.__new__(G.PhanMem)
    o._con_phase2=lambda: DB.ket_noi(dbp)
    o.v3_dash_dataset=Var('D'); o.v_phase2_dash_site=Var('(tất cả)'); o.v3_dash_trang_thai=Var('(tất cả)'); o.v3_dash_mau=Var('(tất cả)')
    o.v3_dash_tim=Var(''); o.v3_dash_ho=Var('(tất cả)'); o.cb_v3_dash_ho=Box(); o.cb_v3_dash_dataset=Box(); o.cb_v3_dash_site=Box(); o.lb_v3_dash_dong=Label(); o.tt=Label(); o.bang_phase2_dash=Tree()
    o._v3_dash_sort_col='stt'; o._v3_dash_sort_desc=False; o._v3_dash_iid_map={}; o._v3_dash_rows=[]

    with patch.object(G.C,'doc_website',return_value={'site_key':'real.local','ten':'Máy Biến Áp Việt Nam','url':'https://real.local'}):
        G.PhanMem._v3_nap_dashboard(o)
        ck('C8-SUMMARY-BASE', o.tt.text=='Tổng quan: 3 bài cần làm, 2 đã đăng, 1 còn lại', o.tt.text)
        ck('C4-STT-TRACKER', len(o.bang_phase2_dash.rows)==3 and o.lb_v3_dash_dong.text=='dòng 0/3', o.lb_v3_dash_dong.text)
        o.v3_dash_tim.set('THIBIDI'); G.PhanMem._v3_nap_dashboard(o)
        ck('C1-TRACKER-SEARCH', len(o.bang_phase2_dash.rows)==2, str([r[1][3] for r in o.bang_phase2_dash.rows]))
        o.v3_dash_tim.set(''); o.v3_dash_trang_thai.set('loi'); G.PhanMem._v3_nap_dashboard(o)
        ck('C8-SUMMARY-INDEPENDENT-FILTER', o.tt.text=='Tổng quan: 3 bài cần làm, 2 đã đăng, 1 còn lại', o.tt.text)
        ck('C7-FULL-ERROR-STORED', len(o._v3_dash_iid_map)==1 and next(iter(o._v3_dash_iid_map.values()))['loi']=='Hard Block chặn meta dài chi tiết', str(o._v3_dash_iid_map))
        o.v3_dash_trang_thai.set('(tất cả)'); o.v3_dash_ho.set('THIBIDI · dầu · 3 pha · Silic'); G.PhanMem._v3_nap_dashboard(o)
        ck('C5-TRACKER-FAMILY', len(o.bang_phase2_dash.rows)==2, str([r[1][3] for r in o.bang_phase2_dash.rows]))

print(f'TỔNG TRACKER LOGIC: PASS {P} / FAIL {F}')
raise SystemExit(1 if F else 0)
