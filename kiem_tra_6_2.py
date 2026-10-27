# -*- coding: utf-8 -*-
"""Chạy thử cuối: dựng 6 bài thật, kiểm 5 điều kiện phải đúng trước khi đăng."""
import sys, re, difflib, itertools, statistics
sys.path.insert(0,'.')
import render_phase2 as R
R._PK_kho_row = lambda row: []
AI={'meta_title':'t','meta_description':'d','intro_html':'<p>Mở bài.</p>',
    'dac_diem_html':'<p>Đặc điểm.</p>','ung_dung_html':'<p>Ứng dụng.</p>',
    'huong_dan_chon_html':'<p>Chọn.</p>'}
mau=[("Máy biến áp Dầu 3 pha 250kVA 22/0.4kV Silic THIBIDI","250"),
     ("Máy biến áp Dầu 3 pha 400kVA 22/0.4kV Silic THIBIDI","400"),
     ("Máy biến áp Dầu 3 pha 750kVA 22/0.4kV Silic THIBIDI","750"),
     ("Máy biến áp Dầu 3 pha 1000kVA 22/0.4kV Silic THIBIDI","1000"),
     ("Máy biến áp Dầu 3 pha 1600kVA 22/0.4kV Silic THIBIDI","1600"),
     ("Máy biến áp Dầu 3 pha 2000kVA 22/0.4kV Amorphous THIBIDI","2000")]
def bai(ten,kva):
    row={'outline_id':'outline_may_bien_ap','ten_goc':ten,'ma_goc':'TBD3P'+kva,
         'cong_suat':kva+' kVA','cap_dien_ap':'22/0.4 kV','thuong_hieu':'THIBIDI',
         'slug':'s'+kva,'profile_id':'may_bien_ap_do_luong','dataset_id':'d',
         'thong_so_dong':{},'content_type':'product'}
    r=R.dung_bai_html(row,dict(AI),site_cfg={'ten':'Lotech'})
    return r['html'] if isinstance(r,dict) else r
def txt(h):
    h=re.sub(r'(?is)<table.*?</table>',' ',h); h=re.sub(r'(?is)<script.*?</script>',' ',h)
    return re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',h)).strip()
hs=[bai(t,k) for t,k in mau]; vs=[txt(h) for h in hs]
ok=lambda b,m: print(("  OK   " if b else "  HỎNG ")+m) or b
r=[]
r.append(ok(all(h and len(h)>2000 for h in hs), "6 bài dựng được, không bài nào rỗng"))
r.append(ok(hs==[bai(t,k) for t,k in mau], "render 2 lần ra y hệt (đăng lại không đổi chữ)"))
d=[difflib.SequenceMatcher(None,a,b).ratio() for a,b in itertools.combinations(vs,2)]
r.append(ok(statistics.mean(d)<0.50, f"trùng lặp TB {statistics.mean(d)*100:.1f}% < 50%"))
r.append(ok(all('tối đa theo catalogue' in v and 'không phải kết quả đo' in v
               for v in vs if 'catalogue' in v), "câu miễn trừ catalogue còn nguyên mọi bài"))
r.append(ok(all('8.760' in v for v in vs if 'kWh' in v), "công thức tổn hao/năm còn in ra"))
r.append(ok(not any(re.search(r'\b(IP\d\d|bảo hành \d+)', v) for v in vs), "không có số bịa"))
print("\n=> " + ("SẴN SÀNG CHẠY" if all(r) else "CHƯA ĐƯỢC, dừng lại"))
