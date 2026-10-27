import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image
import nhap_phase2 as N
import workspace_anh as WS
import xu_ly_anh as X

BASE = Path(__file__).resolve().parents[1]
MASTER = BASE / '8MASTER_ENRICHED_Ver8.xlsx'

# 1.1 — đếm trên MASTER Ver8 bằng importer production.
rows = N.import_4_profile(str(MASTER), chi_profile='may_bien_ap_do_luong')['may_bien_ap_do_luong']['rows']
mba = [r for r in rows if r.get('outline_id') == 'outline_may_bien_ap']
ho = {}
for r in mba:
    h = WS.ho_san_pham(r)
    assert h, r.get('ma_goc')
    ho.setdefault(h['key'], []).append(r)
assert len(mba) == 141, len(mba)
assert len(ho) == 11, {k: len(v) for k,v in ho.items()}
print('MASTER_VER8_MBA=141')
print('FAMILY_COUNT=11')
print('FAMILIES=' + ' | '.join(f"{(WS.ho_san_pham(v[0]) or {})['nhan']}:{len(v)}" for v in ho.values()))

# 1.2–1.3 — family fallback + riêng thắng theo từng slot + upload mock idempotent.
def row(sku, hang='THIBIDI', ten='Máy biến áp dầu 3Pha 250KVA 22/0.4KV Loại Silic'):
    return {'profile_id':'may_bien_ap_do_luong','outline_id':'outline_may_bien_ap',
            'record_id':'D::03_May_Bien_Ap_Do_Luong::'+sku,'ma_goc':sku,
            'publish_sku':sku,'thuong_hieu':hang,'ten_goc':ten,
            'thong_so_dong':{'Loại lõi (trích từ tên)':'Silic'}}

r1=row('A1'); r2=row('A2'); r3=row('A3', 'MBT')
with tempfile.TemporaryDirectory() as td:
    root=Path(td); sheet='03_May_Bien_Ap_Do_Luong'
    src=root/'src'; src.mkdir()
    for name, value in [('family-hero.jpg',40),('family-close.jpg',90),('private-hero.jpg',150)]:
        Image.new('RGB',(1000,900),(value,value,value)).save(src/name, quality=95)

    tmh=WS.tao_workspace_ho(root,sheet,r1)
    assert tmh.parent.name == '_HO'
    WS.gan_anh(tmh, src/'family-hero.jpg','hero')
    WS.gan_anh(tmh, src/'family-close.jpg','can_canh')

    e1=WS.anh_hieu_luc(root,sheet,r1,None)
    e2=WS.anh_hieu_luc(root,sheet,r2,None)
    e3=WS.anh_hieu_luc(root,sheet,r3,None)
    assert e1['nguon']=='ho' and e2['nguon']=='ho' and e3['nguon']=='trong'
    assert e1['o']['hero'] and e2['o']['hero']

    tmr=WS.tao_workspace(root,sheet,2,r2,title='A2')
    WS.gan_anh(tmr, src/'private-hero.jpg','hero')
    e2b=WS.anh_hieu_luc(root,sheet,r2,tmr)
    assert e2b['nguon']=='rieng'
    assert e2b['nguon_o']['hero']=='rieng'
    assert e2b['nguon_o']['can_canh']=='ho'
    assert WS.hash_file(e2b['o']['hero']['duong_dan']) == WS.hash_file(src/'private-hero.jpg')

    calls=[]
    def upload(path, name, mime):
        calls.append((Path(path).read_bytes(), name, mime))
        return 700+len(calls), f'https://mock.local/{name}'

    k1=X.dang_anh_hieu_luc(root,sheet,None,r1,'site',tieu_de='A1',slug='a1',upload=upload)
    first=len(calls)
    k2=X.dang_anh_hieu_luc(root,sheet,None,r2,'site',tieu_de='A2',slug='a2',upload=upload)
    second=len(calls)
    k3=X.dang_anh_hieu_luc(root,sheet,tmr,r2,'site',tieu_de='A2',slug='a2',upload=upload)
    third=len(calls)
    assert k1['ok'] and k2['ok'] and k3['ok']
    assert first == 2 and second == 2 and third == 3, (first,second,third)
    assert k3['nguon_o']['hero']=='rieng' and k3['nguon_o']['can_canh']=='ho'
    print(f'MOCK_UPLOAD_CALLS=first:{first},same_family_second:{second},private_override:{third}')
    print('FALLBACK_SAME_FAMILY=PASS; PRIVATE_OVERRIDES_HERO=PASS; FAMILY_FILLS_MISSING=PASS')

print('PASS V40-1 FAMILY IMAGES')
