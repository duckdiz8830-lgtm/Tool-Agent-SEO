# -*- coding: utf-8 -*-
import sys, sqlite3, json, os
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
import render_phase2 as R
import ai_wp_adapter as A

# Ver 5.7 — BỎ PHỤ THUỘC CỨNG VÀO ĐƯỜNG DẪN SẢN XUẤT.
# Bản cũ mở cứng '/mnt/data/phase2-du-lieu.db' — đường dẫn Linux tuyệt đối
# không tồn tại trên máy Windows của người dùng, cũng không tồn tại trong
# sandbox của run_tests.py:
#     sqlite3.OperationalError: unable to open database file
# Test này vì thế LUÔN đỏ ở mọi máy, kể cả khi code hoàn toàn đúng.
#
# ĐÃ THỬ VÀ BỎ: dựng fixture giả trong test. KHÔNG dùng được — kịch bản ở
# đây là "bẻ cong_suat thành 1 trong khi tên nguồn vẫn nói 25kVA, Hard Block
# phải bắt được 1kVA". Kho trắng của Hard Block dựng TỪ CHÍNH row, nên với
# fixture tự dựng thì '1' lọt vào kho trắng và không có vi phạm nào để bắt.
# Điều kiện chỉ tái hiện được với row THẬT (có đủ các trường phụ). Dựng
# fixture cho qua chuyện = biến test thành vô nghĩa mà vẫn xanh.
#
# Nên: tìm DB ở các vị trí HỢP LỆ; không thấy thì SKIP bằng exit 77
# (run_tests.py hiểu 77 = SKIP và KHÔNG tính là pass thật).
def _nap_row():
    ung_vien = [os.environ.get('SONEALEO_TEST_DB'),
                BASE / 'phase2-du-lieu.db']
    appdata = os.environ.get('APPDATA')
    if appdata:
        ung_vien.append(Path(appdata) / 'SONEALEO' / 'phase2-du-lieu.db')
    for p in ung_vien:
        if not p:
            continue
        p = Path(p)
        if not p.is_file():
            continue
        try:
            con = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
            r = con.execute("select du_lieu_json from san_pham_phase2 "
                            "where du_lieu_json like '%MBT1P25A2608%' limit 1").fetchone()
            con.close()
            if r:
                print(f'  (dùng row thật từ {p})')
                return json.loads(r[0])
        except Exception:
            continue
    print('SKIP: không tìm thấy phase2-du-lieu.db có SKU MBT1P25A2608.')
    print('      Test này cần row THẬT mới tái hiện được kịch bản Hard Block.')
    print('      Chỉ đường DB bằng biến môi trường SONEALEO_TEST_DB nếu muốn chạy.')
    raise SystemExit(77)


row = _nap_row()
# Windows log reported 1kVA in Rank Math. Reproduce by corrupting only the value
# that code meta reads while source name still says 25kVA, so Hard Block must reject 1kVA.
bad=dict(row); bad['cong_suat']='1'
meta,warn=R.dung_rank_math(bad, {'title':R.dung_tieu_de(bad)}, tra_canh_bao=True)
assert warn and 'Hard Block' in warn
assert all('1kVA' not in str(v) for v in meta.values())
assert meta['rank_math_description']
# Public two-arg API also must not raise.
meta2=R.dung_rank_math(bad, {'title':R.dung_tieu_de(bad)})
assert meta2['rank_math_description']
goi=R.dung_goi_cap_nhat_seo(bad)
assert goi['meta_rank_math']['rank_math_description'] and goi.get('canh_bao_meta')
# Body invariant stays hard: numeric violation outside META remains.
ai={'title':'X','meta_title':'X','meta_description':'X','dac_diem_html':'Thiết bị 99kV','ung_dung_html':'','huong_dan_chon_html':'','faq':[]}
_sach, vi_pham, _flags=A._xu_ly_vi_pham_phu(ai,row)
assert 'dac_diem_html' in vi_pham, vi_pham
print('PASS 7 / FAIL 0')
print('SEO_WARNING=', warn)
print('SEO_FALLBACK=', meta)
print('BODY_BLOCK_FIELDS=', sorted(vi_pham))
