# -*- coding: utf-8 -*-
"""Ver 4.6.1 — vá lỗi text trong MASTER.

VÌ SAO
  Text bẩn ở nguồn thì bài sinh ra cũng bẩn. Ký tự xuống dòng nằm trong ô
  Excel sẽ phá cấu trúc HTML khi render; khoảng trắng thừa làm lệch khoá
  so khớp; "Cadivi - Cadivi" hiện nguyên si lên tiêu đề bài.

NGUYÊN TẮC — chỉ sửa cái KHÔNG đổi nghĩa kỹ thuật
  Sửa:  khoảng trắng, xuống dòng, tab, nháy cong, lặp thương hiệu,
        khoảng trắng trước dấu câu, dấu chấm thừa cuối tên.
  KHÔNG sửa: bất cứ con số, ký hiệu kỹ thuật, đơn vị nào.

HAI THỨ CỐ Ý KHÔNG ĐỤNG
  1. 'mm2' -> 'mm²' (3.998 ô). Đây KHÔNG phải typo — nhà phân phối viết vậy,
     và người mua cũng gõ 'mm2' trên Google. Đổi sẽ làm lệch khoá tách
     'Tiết Diện' và đổi slug của bài đã đăng. Rủi ro cao, lợi ích không rõ.
  2. Gạch ngang dài '–' -> '-' (3.059 ô). Đây là dấu gạch nối đúng chính tả
     trong '27kV – 630A'. slugify() tự xử lý khi sinh URL. Sửa là đổi 3.059
     ô để lấy về con số 0.
"""
import re
import shutil
import unicodedata
from collections import Counter

import pandas as pd

SHEET_DL = ['01_Cap_Dien', '02_Tu_Va_Thiet_Bi_Dong_Cat',
            '03_May_Bien_Ap_Do_Luong', '04_Phu_Kien_Va_Khac']

# Cột KHÔNG được đụng: khoá định danh, có thể đang khớp với dữ liệu ngoài.
COT_KHOA = {'Slug chỉ định', 'Slug dự kiến', 'Hậu tố slug'}


# Chỉ mấy cột NGẮN, dạng định danh mới được cắt dấu câu cuối. Cột ghi chú là
# câu văn hoàn chỉnh — dấu chấm cuối là ĐÚNG, cắt đi mới là làm hỏng.
COT_CAT_DUOC = {'Tên hàng', 'Mã hàng', 'Nhãn Hiệu / Xuất Xứ', 'ĐVT',
                'Quy Cách / Áp Lực', 'Quy Cách', 'Tiết Diện (mm²)',
                'Cấp Điện Áp', 'Cấp Điện Áp (kV)', 'Công Suất (kVA)',
                'Vật Liệu Ruột', 'Nhóm Nguồn'}


def sua_o(v, cot=''):
    """Trả về (giá trị mới, list tên lỗi đã sửa)."""
    if not isinstance(v, str):
        return v, []
    goc, da = v, []

    if '\ufeff' in v or any(unicodedata.category(c) == 'Cf' for c in v):
        v = ''.join(c for c in v if unicodedata.category(c) != 'Cf')
        da.append('ký tự điều khiển ẩn')

    if '\xa0' in v:
        v = v.replace('\xa0', ' ')
        da.append('khoảng trắng cứng (nbsp)')

    if '\t' in v:
        v = v.replace('\t', ' ')
        da.append('ký tự tab')

    if '\n' in v or '\r' in v:
        v = re.sub(r'[\r\n]+', ' ', v)
        da.append('xuống dòng trong ô')

    if re.search(r'[\u2018\u2019\u201c\u201d]', v):
        v = (v.replace('\u2018', "'").replace('\u2019', "'")
              .replace('\u201c', '"').replace('\u201d', '"'))
        da.append('nháy cong')

    if re.search(r'\s[,.;:](?:\s|$)', v):
        v = re.sub(r'\s+([,.;:])', r'\1', v)
        da.append('khoảng trắng trước dấu câu')

    # "Cadivi - Cadivi" -> "Cadivi"
    m = re.search(r'([A-Za-zÀ-ỹ]{3,20})(\s*-\s*)\1\b', v, re.I)
    if m:
        v = re.sub(r'([A-Za-zÀ-ỹ]{3,20})(\s*-\s*)\1\b', r'\1', v, flags=re.I)
        da.append(f'lặp thương hiệu "{m.group(1)}"')

    if '  ' in v:
        v = re.sub(r' {2,}', ' ', v)
        da.append('khoảng trắng đôi')

    if v != v.strip():
        v = v.strip()
        da.append('khoảng trắng đầu/cuối')

    # Dấu câu thừa cuối — CHỈ cho cột định danh ngắn, và chỉ khi cả ô không
    # phải câu văn (không có '. ' ở giữa).
    if (cot in COT_CAT_DUOC and re.search(r'[\wÀ-ỹ)][.,]$', v)
            and '. ' not in v and '; ' not in v):
        v = v[:-1]
        da.append('dấu câu thừa cuối')

    return (v, da) if v != goc else (goc, [])


def chay(nguon, dich):
    x = pd.ExcelFile(nguon)
    dem = Counter()
    nhat_ky = []
    sheet_moi = {}

    for s in x.sheet_names:
        a = pd.read_excel(nguon, sheet_name=s)
        if s not in SHEET_DL:
            continue
        doi = False
        for c in a.columns:
            if c in COT_KHOA:
                continue
            for i in range(len(a)):
                v = a.iat[i, a.columns.get_loc(c)]
                if not isinstance(v, str):
                    continue
                moi, da = sua_o(v, cot=c)
                if da:
                    a.iat[i, a.columns.get_loc(c)] = moi
                    doi = True
                    for k in da:
                        dem[k] += 1
                    if len(nhat_ky) < 4000:
                        nhat_ky.append((s, c, i + 2, v[:90], moi[:90], '; '.join(da)))
        if doi:
            sheet_moi[s] = a

    shutil.copy(nguon, dich)
    with pd.ExcelWriter(dich, engine='openpyxl', mode='a',
                        if_sheet_exists='replace') as w:
        for s, a in sheet_moi.items():
            a.to_excel(w, sheet_name=s, index=False)
        pd.DataFrame(nhat_ky, columns=['Sheet', 'Cột', 'Dòng Excel',
                                       'Trước', 'Sau', 'Lỗi đã sửa']).to_excel(
            w, sheet_name='00_Va_Chinh_Ta', index=False)

    print(f'Đã sửa {sum(dem.values())} ô trên {len(sheet_moi)} sheet:')
    for k, n in dem.most_common():
        print(f'   {n:5d}  {k}')
    print(f'\nKHÔNG đụng: mm2->mm² (3.998 ô), gạch ngang dài (3.059 ô) — xem docstring.')
    print(f'Đã ghi: {dich}')
    return dem


if __name__ == '__main__':
    chay('/mnt/user-data/outputs/9MASTER_Ver15_LOC_DIEN_AP.xlsx',
         '/mnt/user-data/outputs/9MASTER_Ver16_SACH_TEXT.xlsx')
