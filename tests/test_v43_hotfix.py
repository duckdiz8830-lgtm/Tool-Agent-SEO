# -*- coding: utf-8 -*-
"""Hotfix 4.3: timeout/fallback, tab ảnh Windows-scroll contract, Mock state."""
import os
import sqlite3
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ai_wp_adapter as AWP
import db_phase2 as DB
import tab_anh as TA
import workspace_anh as WS

P = F = 0

def ck(name, cond, detail=''):
    global P, F
    if cond:
        P += 1; print(f'PASS {name}: {detail}')
    else:
        F += 1; print(f'FAIL {name}: {detail}')

# 1) Timeout một cặp phải thoát ngay, không retry 3 lần cùng cặp.
import requests
calls=[]
def slow_timeout(*a, **kw):
    calls.append(kw.get('timeout'))
    time.sleep(0.03)
    raise requests.exceptions.Timeout('synthetic timeout')
with patch('prompts_phase2.xay_prompt', return_value=('sys','user',{'meta_title':'string'})), \
     patch('requests.post', side_effect=slow_timeout):
    t=time.perf_counter()
    r=AWP.goi_ai_that({'ma_goc':'X'}, 'chuan', 'dead-model', timeout=45, api_key='fake')
    elapsed=time.perf_counter()-t
ck('AI-TIMEOUT-ONE-SHOT', (not r['ok']) and len(calls)==1 and calls==[45], f'calls={len(calls)}, timeout={calls}, elapsed={elapsed:.3f}s')

# 2) Cặp fallback thắng phải được đưa lên đầu cho bài kế.
pairs=[('k','dead'),('k','good')]
def fake_ai(row, mau, model, site_cfg=None, timeout=45, api_key=None):
    if model=='dead':
        time.sleep(0.06); return {'ok':False,'loi':'timeout synthetic'}
    time.sleep(0.01); return {'ok':True,'data':{'x':'ok'},'usage':{}}
with patch.object(AWP,'goi_ai_that', side_effect=fake_ai), \
     patch.object(AWP,'kiem_tra_bia_toan_bo', return_value={}):
    times=[]; used=[]
    for _ in range(3):
        t=time.perf_counter(); kq,_=AWP.goi_ai_co_du_phong({'ma_goc':'X'},'chuan',pairs,site_cfg={}); times.append(time.perf_counter()-t); used.append(kq.get('model_da_dung'))
ck('AI-FALLBACK-REORDER', pairs[0][1]=='good' and used==['good','good','good'] and times[1] < times[0]/2 and times[2] < times[0]/2,
   f'times={[round(x,3) for x in times]}, order={[x[1] for x in pairs]}')

# 3) Ctrl-select nhiều file chỉ rót vào ô trống theo thứ tự.
obj=TA.TabAnh.__new__(TA.TabAnh)
obj.chon={'row':{'profile_id':'may_bien_ap_do_luong'}, 'sheet':'S', 'thu_muc':'/tmp/x'}
class V: 
    def get(self): return '/tmp/root'
obj.v_goc=V(); obj._bao_dam_thu_muc=lambda:'/tmp/x'; obj._lam_moi_bai=lambda:None
roles=[x[0] for x in WS.vai_tro_cua('may_bien_ap_do_luong')]
assigned=[]
with patch('tab_anh.filedialog.askopenfilenames', return_value=('a.jpg','b.jpg','c.jpg','d.jpg')), \
     patch.object(WS,'vai_tro_cua', return_value=[(r,r,'') for r in roles]), \
     patch.object(WS,'anh_hieu_luc', return_value={'o':{}}), \
     patch.object(WS,'gan_anh', side_effect=lambda tm,p,r: assigned.append((p,r))):
    obj._chon_anh(roles[0])
ck('IMAGE-MULTI-4', len(assigned)==min(4,len(roles)) and [r for _,r in assigned]==roles[:4], f'assigned={assigned}')

# 4) Mouse wheel gọi scroll trên canvas.
scroll=[]
class C:
    def yview_scroll(self, n, unit): scroll.append((n,unit))
obj.canvas_o=C()
class E: delta=-120
obj._cuon_chuot(E())
ck('IMAGE-WHEEL', scroll==[(1,'units')], f'scroll={scroll}')

# 5) Mock vẫn ghi Dashboard nhưng wp_id/wp_url trong production state phải NULL.
class DummyCon: pass
row={'ma_goc':'X','record_id':'R'}
writes=[]
with patch.object(DB,'lay_san_pham', return_value=row), \
     patch.object(DB,'upsert_bai_viet_khoi_tao', return_value=None), \
     patch.object(DB,'cap_nhat_bai_viet', side_effect=lambda *a,**kw: writes.append(kw) or True), \
     patch.object(AWP,'goi_ai_mock', return_value=({'meta_title':'x'},{})), \
     patch.object(AWP.R,'dung_bai_html', return_value={'title':'T','slug':'s','html':'<p>x</p>','meta_description':'m'}), \
     patch.object(AWP,'kiem_tra_bia_toan_bo', return_value={}), \
     patch.object(AWP,'dang_wp_mock', return_value=('1001','https://site.mock/s/')):
    mr=AWP.sinh_va_dang_mock(DummyCon(),'D','R','site',{})
last=writes[-1] if writes else {}
ck('MOCK-NO-FAKE-ID-IN-PROD-STATE', mr['ok'] and mr['wp_id']=='1001' and last.get('wp_id','sentinel') is None and last.get('wp_url','sentinel') is None, f'return={mr}, db_write={last}')

# 6) Cleaner chỉ xóa .mock, giữ URL thật.
con=sqlite3.connect(':memory:')
con.execute('CREATE TABLE bai_viet_phase2 (wp_url TEXT)')
con.executemany('INSERT INTO bai_viet_phase2(wp_url) VALUES(?)', [('https://a.mock/x',),('https://real.vn/x',),(None,)])
n=DB.don_bai_viet_mock(con)
left=[r[0] for r in con.execute('SELECT wp_url FROM bai_viet_phase2')]
ck('MOCK-CLEANER', n==1 and 'https://real.vn/x' in left and len(left)==2, f'deleted={n}, left={left}')
con.close()


# 7) Sau Mock sạch state, đường WordPress thật phải POST collection để TẠO MỚI.
class FakeCon:
    def close(self): pass
class Resp:
    status_code=201; text=''; headers={'Content-Type':'application/json'}
    def json(self): return {'id':777,'link':'https://real.vn/p/777'}
posted=[]
def fake_post(url,*a,**kw):
    posted.append(url); return Resp()
with patch('cauhinh.doc_website', return_value={'url':'https://real.vn','user':'u','app_pw':'p'}), \
     patch('autopost._auth', return_value=('https://real.vn', ('u','p'))), \
     patch('autopost.tim_bai_theo_slug', return_value=None), \
     patch.object(DB,'ket_noi', return_value=FakeCon()), \
     patch.object(DB,'lay_bai_viet', return_value=None), \
     patch('requests.post', side_effect=fake_post):
    rr=AWP.dang_wp_that('D','R','real.vn','chuan','T','slug','<p>x</p>','e')
ck('MOCK-TO-REAL-CREATE', rr['ok'] and len(posted)==1 and posted[0].endswith('/wp-json/wp/v2/posts'), f'posted={posted}, result={rr}')

# 8) Source UI production mock phải truyền ghi_trang_thai=False.
src=Path('giao-dien.py').read_text(encoding='utf-8')
ck('MOCK-UI-WIRING', 'Dọn state .mock' in src and 'wp_id=None, wp_url=None' in Path('ai_wp_adapter.py').read_text(encoding='utf-8'), 'Mock DB giữ dashboard nhưng không giữ fake ID/URL + có cleaner')
# Ver 5.6 — timeout Gemini hạ 45s -> 20s, và chuyển sang hằng số
# AWP.TIMEOUT_GEMINI để UI/adapter không lệch nhau. Assert cũ neo vào chuỗi
# 'timeout=45' nên phải đổi theo; ý nghĩa test KHÔNG đổi (vẫn kiểm UI có
# truyền timeout + có persist model thắng cuộc).
ck('MODEL-PERSIST-WIRING', "C.luu_gemini('', model_ok)" in src and 'timeout=AWP.TIMEOUT_GEMINI' in src, 'winning model persist + timeout hằng số')

# 10) Windows/pythonw có thể khởi động với stdout gốc=None hoặc stream đã đóng.
#     Test trực tiếp đúng class router nhưng không import toàn GUI/tksheet.
import ast, io, queue, threading
_gui_src=Path('giao-dien.py').read_text(encoding='utf-8')
_tree=ast.parse(_gui_src)
_node=next(n for n in _tree.body if isinstance(n, ast.ClassDef) and n.name=='ChuyenHuongIn')
_ns={'io':io, 'threading':threading}
exec(compile(ast.Module(body=[_node], type_ignores=[]), 'giao-dien.py', 'exec'), _ns)
_Router=_ns['ChuyenHuongIn']
r_none=_Router(None)
none_ok=(r_none.write('[CSS] test\n')==len('[CSS] test\n') and r_none.flush() is None)
closed=io.StringIO(); closed.close(); r_closed=_Router(closed)
closed_ok=(r_closed.write('x')==1 and r_closed.flush() is None)
q=queue.Queue(); r_none.gan_thread(q); r_none.write('worker-log'); queue_ok=(q.get_nowait()=='worker-log')
ck('STDOUT-NONE-CLOSED', none_ok and closed_ok and queue_ok, f'none={none_ok}, closed={closed_ok}, worker_queue={queue_ok}')

print(f'TỔNG: PASS {P} / FAIL {F}')
raise SystemExit(1 if F else 0)
