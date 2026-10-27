# -*- coding: utf-8 -*-
"""HF1 2026-08-11 — Google Images phải theo outline đã route, không đoán bằng profile/kVA."""
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import tab_anh as T


def query_for(row, ten):
    got = []
    old = T.webbrowser.open
    try:
        T.webbrowser.open = lambda url: got.append(url) or True
        obj = T.TabAnh.__new__(T.TabAnh)
        obj.chon = {'row': row, 'ten': ten, 'sku': row.get('ma_goc', '')}
        obj._mo_google_images()
    finally:
        T.webbrowser.open = old
    assert len(got) == 1, got
    return parse_qs(urlparse(got[0]).query).get('q', [''])[0]


# Case production vừa bắt: cùng profile MBA + có 320kVA nhưng outline là VỎ.
ten_vo = 'Vỏ mạ kẽm nhúng nóng MBA 3P 320KVA 22/0,4KV- MBT'
row_vo = {
    'profile_id': 'may_bien_ap_do_luong',
    'outline_id': 'outline_vo_may_bien_ap',
    'ma_goc': 'MBTVM3P320',
    'ten_goc': ten_vo,
    'thuong_hieu': 'MBT',
    'cong_suat': '320 kVA',
    'cap_dien_ap': '22/0,4 kV',
}
q_vo = query_for(row_vo, ten_vo)
assert q_vo == ten_vo, q_vo
assert not q_vo.casefold().startswith('máy biến áp '), q_vo

# An toàn ngược: MBA thật vẫn giữ query gọn theo đặc trưng.
ten_mba = 'Máy biến áp dầu 3Pha 320KVA 22/0.4KV MBT'
row_mba = {
    'profile_id': 'may_bien_ap_do_luong',
    'outline_id': 'outline_may_bien_ap',
    'ma_goc': 'MBA320TEST',
    'ten_goc': ten_mba,
    'thuong_hieu': 'MBT',
    'cong_suat': '320 kVA',
    'cap_dien_ap': '22/0.4 kV',
}
q_mba = query_for(row_mba, ten_mba)
assert q_mba == 'máy biến áp dầu MBT 320kVA 3 pha', q_mba

print('PASS HF1 Google Images')
print('VỎ  :', q_vo)
print('MBA :', q_mba)
