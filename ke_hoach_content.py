# -*- coding: utf-8 -*-
"""Ver 5.5 — KE_HOACH_CONTENT: đọc file GSC export -> ra kế hoạch viết bài.

CHẠY:
    python ke_hoach_content.py <thu_muc_chua_file_GSC> [file_ket_qua.xlsx]

VD:
    python ke_hoach_content.py D:\\GSC KE-HOACH-CONTENT.xlsx

Script ĐỘC LẬP, chạy được ngay, không cần SONEALEO. Chỉ cần pandas + openpyxl.
Dùng chung hàm doan_content_type() của prompts_seo_post.py — nên kế hoạch xuất
ra khớp đúng 8 content type mà tool sẽ sinh, không phải hai hệ quy chiếu khác nhau.

ĐỌC ĐƯỢC: file .xlsx export thẳng từ Google Search Console (sheet "Queries" và
"Pages"). Không cần sửa gì trước khi đưa vào.

RA CÁI GÌ — 4 sheet:
    1. KE-HOACH     : danh sách bài nên viết, đã xếp theo điểm ưu tiên
    2. SUA-BAI-CU   : trang đã có, hạng tốt, CTR kém -> sửa rẻ hơn viết mới
    3. TRUNG-LAP    : từ khoá nhiều site cùng tranh -> chọn 1 site, đừng viết thêm
    4. TONG-QUAN    : số tổng theo site và theo content type

CÁCH TÍNH ĐIỂM ƯU TIÊN (ghi rõ để không phải đoán):
    diem = impression * he_so_ctr * he_so_type
      he_so_ctr  = 1 + (ctr_kha_thi - ctr_hien_tai)   -> đang phí nhiều thì điểm cao
      he_so_type = bao_gia 1.4 | catalogue 1.3 | so_sanh 1.2 | con lai 1.0
                   (bao_gia và catalogue là 2 nhóm CTR cao nhất đo được trên hệ)
    Đây là HEURISTIC để xếp thứ tự, không phải dự báo traffic. Đừng đọc nó như
    con số tuyệt đối.
"""
import os
import sys
import glob
import re
import warnings

warnings.filterwarnings('ignore')

try:
    import pandas as pd
except ImportError:
    sys.exit('Thiếu pandas. Chạy: pip install pandas openpyxl')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import prompts_seo_post as P
except ImportError:
    sys.exit('Không tìm thấy prompts_seo_post.py — để cùng thư mục với file này.')


# ============================================================ tham số

HE_SO_TYPE = {
    'bao_gia': 1.4,        # 758 KW / 1.178 clicks / CTR 3.40% — nhóm mạnh nhất hệ
    'catalogue': 1.3,      # CTR 3.89% — cao nhất hệ, đang bỏ trống
    'so_sanh': 1.2,        # ý định gần chuyển đổi
    'top_list': 1.1,
    'complete_guide': 1.0,
    'huong_dan_chon': 1.0,
    'tieu_chuan': 0.9,     # ít traffic, ăn trust
    'du_an': 0.6,          # gần như không ăn search
}

# CTR khả thi theo hạng — mốc tham chiếu ngành, dùng để ước phần đang bỏ phí.
CTR_KHA_THI = {1: 0.28, 2: 0.16, 3: 0.11, 4: 0.08, 5: 0.06,
               6: 0.05, 7: 0.04, 8: 0.033, 9: 0.028, 10: 0.025}

NGUONG_IMPR_TOI_THIEU = 50      # dưới mức này không đáng mở 1 bài riêng
NGUONG_CTR_KEM = 0.02           # CTR dưới 2% ở hạng <=10 = đang phí
NGUONG_HANG_DA_TOT = 10         # hạng <=10 coi như đã có mặt, ưu tiên SỬA


def ctr_kha_thi(pos):
    try:
        return CTR_KHA_THI.get(int(round(float(pos))), 0.02)
    except (TypeError, ValueError):
        return 0.02


# ============================================================ đọc file GSC

def _ten_site(duong_dan):
    """Rút tên site — ĐỌC TỪ URL trong sheet Pages, không đọc tên file.

    Ver 5.5 — sửa bug đếm trùng site. Bản đầu rút tên từ tên file, nên
    `3months7sitetraffic_3.xlsx` thành một "site" riêng trong khi thực chất
    nó là cadivi-vn.vn ở cửa sổ 3 tháng. Kết quả: 16 site thay vì 8, và mọi
    con số theo site bị chia đôi. URL trong sheet Pages là nguồn duy nhất
    nói đúng site nào.
    """
    try:
        p = pd.read_excel(duong_dan, sheet_name='Pages', nrows=5)
        for u in p.iloc[:, 0].astype(str):
            m = re.match(r'https?://([^/]+)', u.strip())
            if m:
                return m.group(1).lower().replace('www.', '')
    except Exception:
        pass
    ten = os.path.basename(duong_dan)
    m = re.search(r'https?___([a-z0-9_\-]+?)_Performance', ten, re.IGNORECASE)
    if m:
        return m.group(1).replace('_', '.')
    return os.path.splitext(ten)[0][:28]


def _so_ngay(duong_dan):
    """Đọc cửa sổ thời gian từ sheet Filters -> số ngày.

    Cần thiết vì thư mục trộn 2 loại export: "Last 28 days" và "Last 3
    months". Không quy về cùng đơn vị thì impression của file 3 tháng lớn
    gấp ~3 lần, đè chết file 28 ngày khi gộp bằng max() và mọi con số
    "click bỏ phí/tháng" thành vô nghĩa.
    """
    try:
        fl = pd.read_excel(duong_dan, sheet_name='Filters')
        for _, r in fl.iterrows():
            gt = str(r.iloc[-1]).lower()
            if 'month' in gt:
                m = re.search(r'(\d+)', gt)
                return int(m.group(1)) * 30 if m else 90
            if 'day' in gt:
                m = re.search(r'(\d+)', gt)
                return int(m.group(1)) if m else 28
    except Exception:
        pass
    return 28


def doc_gsc(thu_muc):
    """Đọc mọi .xlsx trong thư mục, gom sheet Queries và Pages.

    File nào không có sheet Queries thì bỏ qua im lặng (có thể là file khác
    lẫn vào thư mục) nhưng báo tên ra để biết.
    """
    files = sorted(glob.glob(os.path.join(thu_muc, '*.xlsx')))
    if not files:
        sys.exit(f'Không thấy file .xlsx nào trong: {thu_muc}')

    q_all, p_all, bo_qua = [], [], []
    for f in files:
        try:
            q = pd.read_excel(f, sheet_name='Queries')
        except Exception:
            bo_qua.append(os.path.basename(f))
            continue
        site = _ten_site(f)
        ngay = _so_ngay(f)
        q.columns = [str(c).strip() for c in q.columns]
        q = q.rename(columns={q.columns[0]: 'tu_khoa'})
        q['site'] = site
        # Quy Clicks/Impressions về mức 28 NGÀY để file 3 tháng và file 28
        # ngày so sánh được với nhau. CTR và Position là tỷ lệ/trung bình,
        # KHÔNG quy đổi.
        he_so = 28.0 / ngay
        q['Clicks'] = pd.to_numeric(q['Clicks'], errors='coerce').fillna(0) * he_so
        q['Impressions'] = pd.to_numeric(q['Impressions'], errors='coerce').fillna(0) * he_so
        q['cua_so_ngay'] = ngay
        q_all.append(q)
        try:
            p = pd.read_excel(f, sheet_name='Pages')
            p.columns = [str(c).strip() for c in p.columns]
            p = p.rename(columns={p.columns[0]: 'url'})
            p['site'] = site
            p_all.append(p)
        except Exception:
            pass

    if not q_all:
        sys.exit('Không file nào có sheet "Queries" — đây có phải export từ GSC không?')

    q = pd.concat(q_all, ignore_index=True)
    p = pd.concat(p_all, ignore_index=True) if p_all else pd.DataFrame()

    # Gộp trùng: cùng từ khoá + cùng site có thể xuất hiện ở cả bản 28 ngày
    # lẫn bản 3 tháng. Số đã quy về mức 28 ngày nên lấy TRUNG BÌNH (không
    # lấy max — max thiên vị cửa sổ có đợt tăng đột biến), Position lấy tốt
    # nhất vì đó là hạng đã từng đạt được.
    q = (q.groupby(['site', 'tu_khoa'], as_index=False)
           .agg({'Clicks': 'mean', 'Impressions': 'mean',
                 'CTR': 'mean', 'Position': 'min'}))
    q['Clicks'] = q['Clicks'].round(0)
    q['Impressions'] = q['Impressions'].round(0)

    if bo_qua:
        print(f'  (bỏ qua {len(bo_qua)} file không có sheet Queries: {", ".join(bo_qua[:3])}...)')
    return q, p


# ============================================================ dựng kế hoạch

def _tieu_de_goi_y(type_id, tu_khoa, nam=2026):
    """Sinh tiêu đề gợi ý từ mẫu của content type. Người vẫn sửa lại được."""
    chu_de = re.sub(
        r'^(báo giá|bảng giá|giá|catalogue|catalog|top \d+|so sánh|phân biệt|cách chọn|cách tính|tìm hiểu)\s*',
        '', str(tu_khoa).strip(), flags=re.IGNORECASE)
    chu_de = re.sub(r'\s*(là gì|pdf|mới nhất|\d{4})\s*$', '', chu_de, flags=re.IGNORECASE).strip()
    chu_de = chu_de or str(tu_khoa)
    mau = P.mau_tieu_de(type_id)[0]
    return (mau.replace('{chu_de}', chu_de).replace('{nam}', str(nam))
               .replace('{thang}', '08').replace('{n}', '7')
               .replace('{so_sku}', 'nhiều').replace('{a}', chu_de).replace('{b}', '...')
               .replace('{loai_cong_trinh}', 'công trình'))


def dung_ke_hoach(q):
    """Trả (ke_hoach_df, sua_bai_df)."""
    d = q[q['Impressions'] >= NGUONG_IMPR_TOI_THIEU].copy()

    types, tin_cays = [], []
    for kw in d['tu_khoa']:
        tid, tc, _ = P.doan_content_type(kw)
        types.append(tid)
        tin_cays.append(tc)
    d['content_type'] = types
    d['do_tin_cay'] = tin_cays
    d['nhan_type'] = d['content_type'].map(lambda t: P.CONTENT_TYPE[t]['nhan'])
    d['can_sku'] = d['content_type'].map(P.can_sku)

    d['ctr_kha_thi'] = d['Position'].map(ctr_kha_thi)
    d['ctr_hien_tai'] = pd.to_numeric(d['CTR'], errors='coerce').fillna(0)
    d['click_bo_phi'] = ((d['ctr_kha_thi'] - d['ctr_hien_tai']).clip(lower=0)
                         * d['Impressions']).round(0)
    d['diem'] = (d['Impressions']
                 * (1 + (d['ctr_kha_thi'] - d['ctr_hien_tai']).clip(lower=0))
                 * d['content_type'].map(HE_SO_TYPE).fillna(1.0)).round(0)

    # SỬA BÀI CŨ: đã có mặt ở hạng tốt nhưng CTR kém -> rẻ hơn viết mới nhiều lần
    sua = d[(d['Position'] <= NGUONG_HANG_DA_TOT) &
            (d['ctr_hien_tai'] < NGUONG_CTR_KEM)].copy()
    sua = sua.sort_values('click_bo_phi', ascending=False)
    sua['viec_can_lam'] = sua.apply(
        lambda r: (f'Viết lại title + meta cho trang đang xếp hạng {r["Position"]:.0f}. '
                   f'Mở đầu title bằng "{"Báo giá" if r["content_type"] == "bao_gia" else "Tải"}" '
                   f'nếu hợp ý định.'), axis=1)

    # KẾ HOẠCH VIẾT MỚI: loại bỏ những cái đã nằm trong danh sách sửa
    moi = d[~d.index.isin(sua.index)].copy()
    # từ khoá không map được type (tên sản phẩm thuần) -> việc của luồng SKU, bỏ
    moi = moi[moi['do_tin_cay'] != 'thap']
    moi = moi.sort_values('diem', ascending=False)
    moi['tieu_de_goi_y'] = [
        _tieu_de_goi_y(t, k) for t, k in zip(moi['content_type'], moi['tu_khoa'])]

    return moi, sua


def tim_trung_lap(q):
    """Từ khoá mà >=2 site cùng có impression — nguồn cannibalization.

    Nguyên tắc xử lý: chọn site có Position tốt nhất làm site chủ lực, các site
    còn lại KHÔNG viết thêm bài cho cụm này.
    """
    g = (q.groupby('tu_khoa')
           .agg(so_site=('site', 'nunique'),
                tong_impr=('Impressions', 'sum'),
                tong_click=('Clicks', 'sum'))
           .reset_index())
    g = g[g['so_site'] >= 2].sort_values('tong_impr', ascending=False)

    tot_nhat = (q.sort_values('Position').groupby('tu_khoa')
                  .agg(site_tot_nhat=('site', 'first'),
                       hang_tot_nhat=('Position', 'first')).reset_index())
    g = g.merge(tot_nhat, on='tu_khoa', how='left')
    ds_site = (q.groupby('tu_khoa')['site']
                 .apply(lambda s: ', '.join(sorted(set(s)))).reset_index(name='cac_site'))
    return g.merge(ds_site, on='tu_khoa', how='left')


# ============================================================ xuất Excel

def xuat_excel(moi, sua, trung, q, duong_dan):
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    cot_moi = ['tu_khoa', 'nhan_type', 'can_sku', 'tieu_de_goi_y', 'site',
               'Impressions', 'Clicks', 'Position', 'ctr_hien_tai', 'click_bo_phi',
               'diem', 'do_tin_cay']
    ten_moi = ['Từ khoá đích', 'Dạng bài', 'Cần SKU?', 'Tiêu đề gợi ý', 'Site',
               'Impression', 'Click', 'Hạng TB', 'CTR hiện tại', 'Click bỏ phí/tháng',
               'Điểm ưu tiên', 'Độ tin cậy']

    cot_sua = ['tu_khoa', 'site', 'Position', 'ctr_hien_tai', 'Impressions',
               'click_bo_phi', 'nhan_type', 'viec_can_lam']
    ten_sua = ['Từ khoá', 'Site', 'Hạng TB', 'CTR hiện tại', 'Impression',
               'Click bỏ phí/tháng', 'Dạng bài phù hợp', 'Việc cần làm']

    cot_tr = ['tu_khoa', 'so_site', 'cac_site', 'site_tot_nhat', 'hang_tot_nhat',
              'tong_impr', 'tong_click']
    ten_tr = ['Từ khoá bị tranh', 'Số site tranh', 'Các site', 'Site nên giữ',
              'Hạng tốt nhất', 'Tổng impression', 'Tổng click']

    # tổng quan
    tq_type = (moi.groupby('nhan_type')
                 .agg(so_bai=('tu_khoa', 'count'), tong_impr=('Impressions', 'sum'),
                      tong_diem=('diem', 'sum'))
                 .reset_index().sort_values('tong_diem', ascending=False))
    tq_site = (q.groupby('site')
                 .agg(so_tu_khoa=('tu_khoa', 'count'), clicks=('Clicks', 'sum'),
                      impr=('Impressions', 'sum')).reset_index()
                 .sort_values('clicks', ascending=False))
    tq_site['CTR'] = (tq_site['clicks'] / tq_site['impr']).round(4)

    with pd.ExcelWriter(duong_dan, engine='openpyxl') as w:
        moi[cot_moi].rename(columns=dict(zip(cot_moi, ten_moi))).to_excel(
            w, sheet_name='KE-HOACH', index=False)
        sua[cot_sua].rename(columns=dict(zip(cot_sua, ten_sua))).to_excel(
            w, sheet_name='SUA-BAI-CU', index=False)
        trung[cot_tr].rename(columns=dict(zip(cot_tr, ten_tr))).to_excel(
            w, sheet_name='TRUNG-LAP', index=False)
        tq_type.rename(columns={'nhan_type': 'Dạng bài', 'so_bai': 'Số bài',
                                'tong_impr': 'Tổng impression',
                                'tong_diem': 'Tổng điểm'}).to_excel(
            w, sheet_name='TONG-QUAN', index=False, startrow=1)
        tq_site.rename(columns={'site': 'Site', 'so_tu_khoa': 'Số từ khoá',
                                'clicks': 'Clicks', 'impr': 'Impression'}).to_excel(
            w, sheet_name='TONG-QUAN', index=False, startrow=len(tq_type) + 5)

    # định dạng
    from openpyxl import load_workbook
    wb = load_workbook(duong_dan)
    dam = Font(name='Arial', bold=True, color='FFFFFF', size=10)
    nen = PatternFill('solid', fgColor='2F5496')
    thuong = Font(name='Arial', size=10)
    rong = {'KE-HOACH': [34, 26, 11, 46, 16, 12, 8, 9, 12, 17, 12, 11],
            'SUA-BAI-CU': [34, 16, 9, 12, 12, 17, 26, 60],
            'TRUNG-LAP': [34, 12, 40, 16, 12, 15, 12],
            'TONG-QUAN': [30, 10, 16, 12, 12]}

    for ten_sheet in wb.sheetnames:
        ws = wb[ten_sheet]
        for i, w_ in enumerate(rong.get(ten_sheet, []), start=1):
            ws.column_dimensions[get_column_letter(i)].width = w_
        for hang in ws.iter_rows():
            for o in hang:
                o.font = thuong
        if ten_sheet != 'TONG-QUAN':
            for o in ws[1]:
                if o.value:
                    o.font = dam
                    o.fill = nen
                    o.alignment = Alignment(vertical='center', wrap_text=True)
            ws.freeze_panes = 'A2'
            for hang in ws.iter_rows(min_row=2):
                for o in hang:
                    if isinstance(o.value, float) and 0 < o.value < 1:
                        o.number_format = '0.00%'
    ws = wb['TONG-QUAN']
    ws['A1'] = 'THEO DẠNG BÀI'
    ws['A1'].font = Font(name='Arial', bold=True, size=11)
    wb.save(duong_dan)


# ============================================================ main

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    thu_muc = sys.argv[1]
    ra = sys.argv[2] if len(sys.argv) > 2 else 'KE-HOACH-CONTENT.xlsx'

    print(f'Đọc file GSC trong: {thu_muc}')
    q, p = doc_gsc(thu_muc)
    print(f'  {len(q):,} từ khoá / {q["site"].nunique()} site')

    moi, sua = dung_ke_hoach(q)
    trung = tim_trung_lap(q)

    print(f'\n  KE-HOACH   : {len(moi):,} bài nên viết mới')
    print(f'  SUA-BAI-CU : {len(sua):,} trang nên sửa (bỏ phí ~{int(sua["click_bo_phi"].sum()):,} click/tháng)')
    print(f'  TRUNG-LAP  : {len(trung):,} từ khoá bị >=2 site tranh')

    xuat_excel(moi, sua, trung, q, ra)
    print(f'\nXong: {os.path.abspath(ra)}')


if __name__ == '__main__':
    main()
