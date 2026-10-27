# -*- coding: utf-8 -*-
import json, sqlite3, tempfile, sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import nhap_phase2 as N
import khoi_anh as KA
import giao_dien_2_5 as G2
import db_phase2 as DB

master=BASE/'8MASTER_ENRICHED_Ver8.xlsx'
rows=N.import_4_profile(str(master), chi_profile='may_bien_ap_do_luong')['may_bien_ap_do_luong']['rows']
mbt=[r for r in rows if r.get('outline_id')=='outline_may_bien_ap' and str(r.get('thuong_hieu') or '').strip().lower().startswith('mbt')]
ton=sum(bool(KA.bieu_do_ton_hao(r, rows)) for r in mbt)
loi=sum(bool(KA.bieu_do_loi(r, rows)) for r in mbt)
both=[r for r in mbt if KA.bieu_do_ton_hao(r,rows) and KA.bieu_do_loi(r,rows)]
assert len(mbt)==62, len(mbt)
assert ton==61, ton
assert loi==56, loi
assert both
sample=both[0]
out=G2.dung_bai_2_5(sample, {'huong_dan_chon_html':'<p>x</p>'}, {}, tach_hero=True, anh_em=rows)
assert out['than'].count('<svg') >= 2
print(f'PASS D1: SOURCE=MASTER Ver8; MBT={len(mbt)}; ton_hao_svg={ton}; loi_svg={loi}; total_svg={ton+loi}; sample_body_svg={out["than"].count("<svg")}')

with tempfile.TemporaryDirectory() as td:
    con=DB.ket_noi(Path(td)/'d.db')
    now='2026-08-09T00:00:00+00:00'
    con.execute("INSERT INTO dataset(dataset_id,profile_id,source_file,file_checksum,data_checksum,row_count,column_structure,pipeline_version,created_at,updated_at,active) VALUES(?,?,?,?,?,?,?,?,?,?,1)",
                ('D','may_bien_ap_do_luong','x','f','d',13,'[]','p',now,now))
    vals=[160,250,400,560,630,750,800,1000,1250,1600,2000,2500,3200]
    for kva in vals:
        rid=f'R{kva}'
        row={'dataset_id':'D','record_id':rid,'profile_id':'may_bien_ap_do_luong','outline_id':'outline_may_bien_ap','content_type':'product','ma_goc':rid,'ten_goc':f'Máy biến áp dầu TEST {kva}kVA 3 pha lõi Silic','cong_suat':f'{kva} kVA','cap_dien_ap':'22/0.4 kV'}
        con.execute("INSERT INTO san_pham_phase2(dataset_id,record_id,profile_id,outline_id,content_type,du_lieu_json,selected,pipeline_version) VALUES(?,?,?,?,?,?,0,?)",
                    ('D',rid,'may_bien_ap_do_luong','outline_may_bien_ap','product',json.dumps(row,ensure_ascii=False),'p'))
    con.commit()
    got=DB.tim_san_pham_cung_dong(con,'D','R800',gioi_han=6)
    kvas=[float(str(x['cong_suat']).split()[0]) for x in got]
    assert kvas==[560.0,630.0,750.0,1000.0,1250.0,1600.0], kvas
    print('PASS D2: 800kVA ->', kvas, '(3 dưới + 3 trên)')
    con.close()
