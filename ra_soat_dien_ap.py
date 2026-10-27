# -*- coding: utf-8 -*-
"""Ver 4.6 — rà lại bộ lọc cấp điện áp trên các cột catalogue của sheet cáp.

LỖI ĐƯỢC VÁ
  ghep_master.py đặt `key = code if ha_the else None`, nhưng ngay dưới đó
  nhánh cáp CÓ GIÁP gán đè vô điều kiện:

      if code in ("CVV/DATA", "CVV/DSTA", ...):  key = "CVV_GIAP"
      elif code in ("CXV/DATA", "CXV/DSTA", ...): key = "CXV_GIAP"

  -> cáp trung thế mang mã có giáp lọt qua bộ lọc và ăn dòng tải của bảng
  0,6/1 kV. Đo trên Ver14: 1/1217 SKU dính (CXV/DSTA 3x95 - 1,8/3(3,6) kV
  nhận 315 A của bảng hạ thế).

  Số lượng nhỏ nhưng đây đúng là loại sai nguy hiểm nhất: số liệu đúng của
  cấp điện áp này gán sang cấp điện áp khác, trên trang bán cho kỹ sư.

Script này KHÔNG tính lại gì. Nó chỉ XOÁ số ở dòng không chứng minh được là
hạ thế, và ghi lý do vào cột 'Ly do khong co dong tai'.
"""
import re
import shutil

import pandas as pd

SHEET = '01_Cap_Dien'
COT_XOA = [
    'Dong dien dinh muc (A) [catalogue]',
    'Kieu lap dat cua dong dinh muc [catalogue]',
    'Do sut ap (mV/A/m) [catalogue]',
    'Dieu kien quy chieu dong tai [catalogue]',
    'Dien tro DC toi da 20C (Ohm/km) [catalogue]',
    'Duong kinh ruot dan (mm) [catalogue]',
    'Dong dien SUY LUAN (A) - KHONG co trong catalogue',
]
LY_DO = ('SKU co dau hieu TRUNG THE trong Ten hang / Cap Dien Ap. Catalogue ha the '
         'chi phu 0,6/1 kV tro xuong - KHONG ap so lieu ha the.')

_CAP = re.compile(r'(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)\s*'
                  r'(?:\(\s*(\d+(?:[.,]\d+)?)\s*\)\s*)?kv', re.I)
_DON = re.compile(r'(?<![\d/(,.])(\d+(?:[.,]\d+)?)\s*kv', re.I)


def dien_ap_max_kv(t):
    """Cấp điện áp CAO NHẤT nhắc đến trong chuỗi, đơn vị kV. None nếu không thấy."""
    hi = None
    for m in _CAP.finditer(str(t)):
        v = max(float(x.replace(',', '.')) for x in m.groups() if x)
        hi = v if hi is None else max(hi, v)
    for m in _DON.finditer(str(t)):
        v = float(m.group(1).replace(',', '.'))
        hi = v if hi is None else max(hi, v)
    return hi


def chay(nguon, dich):
    a = pd.read_excel(nguon, sheet_name=SHEET)
    cot = [c for c in COT_XOA if c in a.columns]
    if 'Ly do khong co dong tai' not in a.columns:
        a['Ly do khong co dong tai'] = None

    da_don = []
    for i in range(len(a)):
        r = a.iloc[i]
        if all(pd.isna(r.get(c)) for c in cot):
            continue
        kv = dien_ap_max_kv(f"{r.get('Tên hàng')} | {r.get('Cấp Điện Áp')}")
        if kv is not None and kv > 1.0:
            da_don.append((r.get('Mã hàng'), str(r.get('Tên hàng'))[:60], kv,
                           r.get('Dong dien dinh muc (A) [catalogue]')))
            for c in cot:
                a.iat[i, a.columns.get_loc(c)] = None
            a.iat[i, a.columns.get_loc('Ly do khong co dong tai')] = LY_DO

    shutil.copy(nguon, dich)
    with pd.ExcelWriter(dich, engine='openpyxl', mode='a',
                        if_sheet_exists='replace') as w:
        a.to_excel(w, sheet_name=SHEET, index=False)
        pd.DataFrame(da_don, columns=['Mã hàng', 'Tên hàng', 'Cấp điện áp (kV)',
                                      'Dòng tải đã xoá (A)']).to_excel(
            w, sheet_name='00_Da_Don_Trung_The', index=False)

    con = int(a['Dong dien dinh muc (A) [catalogue]'].notna().sum())
    print(f'Đã dọn {len(da_don)} SKU trung thế bị gán số hạ thế')
    for x in da_don:
        print(f'   {x[2]} kV | {x[1]} -> xoá {x[3]} A')
    print(f'SKU còn dòng tải hợp lệ: {con}')
    print(f'Đã ghi: {dich}')
    return da_don


if __name__ == '__main__':
    chay('/mnt/user-data/outputs/9MASTER_Ver14_MA_NOI_BO.xlsx',
         '/mnt/user-data/outputs/9MASTER_Ver15_LOC_DIEN_AP.xlsx')
