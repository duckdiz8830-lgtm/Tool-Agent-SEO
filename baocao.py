# -*- coding: utf-8 -*-
"""
Xuất bảng điều khiển ra Excel. SQLite là bộ nhớ thật, Excel là bảng đem đi khoe
hoặc đem đi chửi.

3 sheet:
    Tổng quan  -> gửi sếp. Mỗi site một dòng.
    Sản phẩm   -> đưa người điền dữ liệu. Thiếu cột nào, thiếu ảnh không.
    Bài viết   -> theo dõi từng bài, chết ở chặng nào.
"""
import time
from pathlib import Path

import cauhinh as C
import dulieu as DL

BASE = Path(__file__).parent

XANH, VANG, DO, XAM = 'FFC6EFCE', 'FFFFEB9C', 'FFFFC7CE', 'FFF2F2F2'
NAVY = 'FF1F3864'

NHAN_TRANG_THAI = {'DA_DANG': 'Đã đăng', 'DA_SINH': 'Đã sinh', 'BI_CHAN': 'Bị chặn',
                   'LOI': 'Lỗi', 'CHUA_LAM': 'Chưa làm'}
NHAN_KIEM_TRA = {'DAT': 'Đạt', 'CANH_BAO': 'Cảnh báo', 'CHAN': 'Bị chặn', '': ''}
MAU_TRANG_THAI = {'Đã đăng': XANH, 'Đã sinh': VANG, 'Bị chặn': DO, 'Lỗi': DO,
                  'Chưa làm': XAM}


def _thu_vien():
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        raise RuntimeError('Chưa có openpyxl. Gõ: python -m pip install openpyxl')


def _dau_bang(ws, tieu_de, hang=1):
    from openpyxl.styles import Font, PatternFill, Alignment
    for i, t in enumerate(tieu_de, 1):
        o = ws.cell(row=hang, column=i, value=t)
        o.font = Font(bold=True, color='FFFFFFFF', size=10)
        o.fill = PatternFill('solid', fgColor=NAVY)
        o.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.freeze_panes = ws.cell(row=hang + 1, column=1)
    ws._current_row = hang        # để ws.append() ghi ngay dưới dòng tiêu đề


def _rong_cot(ws, rong):
    from openpyxl.utils import get_column_letter
    for i, w in enumerate(rong, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def _to_mau(ws, cot, bang_mau, tu_hang=2):
    from openpyxl.styles import PatternFill
    for h in range(tu_hang, ws.max_row + 1):
        o = ws.cell(row=h, column=cot)
        mau = bang_mau.get(str(o.value or ''))
        if mau:
            o.fill = PatternFill('solid', fgColor=mau)


def _to_ty_le(ws, cot, tu_hang=2, nguong_do=0.4, nguong_vang=0.7):
    """Cột dạng 'x/10': đỏ khi thiếu nhiều, vàng khi thiếu vừa, xanh khi đủ."""
    from openpyxl.styles import PatternFill
    for h in range(tu_hang, ws.max_row + 1):
        o = ws.cell(row=h, column=cot)
        try:
            a, b = str(o.value).split('/')
            t = int(a) / int(b)
        except Exception:
            continue
        mau = DO if t < nguong_do else (VANG if t < nguong_vang else XANH)
        o.fill = PatternFill('solid', fgColor=mau)


# ---------------------------------------------------------------- gom số liệu
def gom_du_lieu(ma_site=None):
    """Ghép sản phẩm và bài viết thành ma trận SKU x mẫu bài."""
    import prompts as P
    sites = [ma_site] if ma_site else list(C.tat_ca_site())
    bai = {}
    for b in DL.doc_bai_viet():
        bai[(b['site'], b['sku'], b['mau'])] = b

    dong_bai, dong_sp = [], []
    for s in sites:
        sp = DL.doc_san_pham_db(C.tat_ca_site()[s].get('danh_muc') or None)
        nhom_vt = DL.nhom_trung_van_tay(sp)
        for r in sp:
            co, tong = C.cham_du_lieu(r)
            co_anh = bool((r.get('anh_1_url') or '').strip() or DL.gan_anh(r))
            dang_chon = int(r.get('chon', 1) or 0) == 1
            da_co = 0
            for mau in P.MAU:
                b = bai.get((s, r['sku'], mau))
                dong_bai.append({
                    'site': s, 'danh_muc': r.get('danh_muc', 'chung'), 'sku': r['sku'],
                    'ten': r.get('ten_san_pham', ''), 'mau': P.MAU[mau]['ten'],
                    'du_lieu': b['du_lieu_day'] if b and b['du_lieu_day'] else f'{co}/{tong}',
                    'anh': (b['so_anh'] if b else (1 if co_anh else 0)),
                    'so_tu': (b['so_tu'] if b else 0),
                    'kiem_tra': NHAN_KIEM_TRA.get((b or {}).get('kiem_tra', ''), ''),
                    'wp': (b or {}).get('wp_trang_thai', '') or '',
                    'trang_thai': NHAN_TRANG_THAI.get(
                        (b or {}).get('trang_thai', 'CHUA_LAM'), 'Chưa làm'),
                    'link': (b or {}).get('wp_url', '') or '',
                    'wp_id': (b or {}).get('wp_id') or '',
                    'ngay': (b or {}).get('ngay', '') or '',
                    'ghi_chu': (b or {}).get('ghi_chu', '') or '',
                    'tieu_de': (b or {}).get('tieu_de', '') or '',
                    'meta_title': (b or {}).get('meta_title', '') or '',
                    'meta_description': (b or {}).get('meta_description', '') or '',
                    'slug': (b or {}).get('slug', '') or '',
                    'chon': 'Có' if dang_chon else 'Không',
                })
                if b and b['trang_thai'] in ('DA_SINH', 'DA_DANG'):
                    da_co += 1
            thieu = [n for k, n in C.COT_BANG if not (r.get(k) or '').strip()]
            trung_vt = nhom_vt.get(r['sku'], [])
            dong_sp.append({
                'site': s, 'danh_muc': r.get('danh_muc', 'chung'), 'sku': r['sku'],
                'ten': r.get('ten_san_pham', ''), 'du_lieu': f'{co}/{tong}',
                'anh': 'Có' if co_anh else 'Chưa',
                'chon': 'Có' if dang_chon else 'Không',
                'trung_van_tay': (f'{len(trung_vt)} SKU: ' + ', '.join(trung_vt[:3])
                                 + (' ...' if len(trung_vt) > 3 else '')) if trung_vt else '',
                'da_co': f'{da_co}/{len(P.MAU)}',
                'thieu': ', '.join(thieu[:6]) + (' ...' if len(thieu) > 6 else ''),
            })
    return dong_bai, dong_sp


# ---------------------------------------------------------------- xuất file
def xuat(duong_dan=None, ma_site=None):
    _thu_vien()
    import openpyxl
    from openpyxl.styles import Font, Alignment

    dong_bai, dong_sp = gom_du_lieu(ma_site)
    wb = openpyxl.Workbook()

    # ---------- sheet 1: Tổng quan ----------
    ws = wb.active
    ws.title = 'Tổng quan'
    ws['A1'] = 'BẢNG ĐIỀU KHIỂN LOTECH AUTOPOST'
    ws['A1'].font = Font(bold=True, size=14, color=NAVY)
    ws['A2'] = 'Xuất lúc ' + time.strftime('%H:%M %d/%m/%Y')
    ws['A2'].font = Font(size=9, italic=True, color='FF808080')

    tieu_de = ['Site', 'Tên hiển thị', 'Ngành hàng', 'Tổng SKU', 'Đang chọn viết',
               'Đã bỏ chọn', 'Tổng bài cần làm', 'Đã đăng', 'Đã sinh chưa đăng',
               'Bị chặn', 'Lỗi', 'Còn lại', 'Tiến độ']
    _dau_bang(ws, tieu_de, hang=4)
    h = 5
    for s in ([ma_site] if ma_site else list(C.tat_ca_site())):
        # chỉ tính bài của sản phẩm đang bật "chọn viết", khớp với thẻ KPI
        # trong app — không thì hai chỗ hiện hai con số khác nhau, dễ nghi ngờ nhầm
        d = [x for x in dong_bai if x['site'] == s and x.get('chon') == 'Có']
        sp = [x for x in dong_sp if x['site'] == s]
        dem = {k: sum(1 for x in d if x['trang_thai'] == k)
               for k in ('Đã đăng', 'Đã sinh', 'Bị chặn', 'Lỗi', 'Chưa làm')}
        tong, chon = len(d), sum(1 for x in sp if x['chon'] == 'Có')
        xong = dem['Đã đăng'] + dem['Đã sinh']
        for i, v in enumerate([
                s, C.tat_ca_site()[s]['ten'],
                ', '.join(C.tat_ca_site()[s].get('danh_muc') or []) or 'tất cả',
                len(sp), chon, len(sp) - chon,
                tong, dem['Đã đăng'], dem['Đã sinh'], dem['Bị chặn'], dem['Lỗi'],
                dem['Chưa làm'],
                f'{xong * 100 // tong}%' if tong else '0%'], 1):
            ws.cell(row=h, column=i, value=v)
        h += 1
    _rong_cot(ws, [10, 24, 18, 10, 14, 12, 16, 11, 17, 10, 9, 10, 10])

    ws[f'A{h + 2}'] = 'Ghi chú'
    ws[f'A{h + 2}'].font = Font(bold=True, color=NAVY)
    for i, t in enumerate([
            'Tổng bài cần làm = số sản phẩm x số mẫu bài.',
            'Bị chặn = bài AI bịa số liệu hoặc lộ danh tính, KHÔNG đăng. Xem lý do ở sheet Bài viết.',
            'Sheet Sản phẩm là danh sách cần điền thêm dữ liệu, cột nào trống thì bài mỏng đi.'], 0):
        ws[f'A{h + 3 + i}'] = t
        ws[f'A{h + 3 + i}'].font = Font(size=9, color='FF808080')

    # ---------- sheet 2: Sản phẩm ----------
    ws = wb.create_sheet('Sản phẩm')
    _dau_bang(ws, ['Site', 'Ngành hàng', 'SKU', 'Tên sản phẩm', 'Chọn viết', 'Dữ liệu',
                   'Ảnh', 'Trùng vân tay thông số', 'Đã có bài', 'Còn thiếu cột'])
    for r in dong_sp:
        ws.append([r['site'], r['danh_muc'], r['sku'], r['ten'], r['chon'], r['du_lieu'],
                   r['anh'], r['trung_van_tay'], r['da_co'], r['thieu']])
    _rong_cot(ws, [10, 16, 26, 46, 10, 10, 8, 34, 11, 60])
    _to_mau(ws, 5, {'Có': XANH, 'Không': XAM})
    _to_ty_le(ws, 6)
    _to_mau(ws, 7, {'Có': XANH, 'Chưa': DO})
    for h in range(2, ws.max_row + 1):
        if ws.cell(row=h, column=8).value:
            from openpyxl.styles import PatternFill
            ws.cell(row=h, column=8).fill = PatternFill('solid', fgColor=VANG)
    ws.auto_filter.ref = ws.dimensions

    # ---------- sheet 3: Bài viết ----------
    ws = wb.create_sheet('Bài viết')
    _dau_bang(ws, ['Site', 'Ngành hàng', 'SKU', 'Tên sản phẩm', 'Outline', 'Chọn viết',
                   'Dữ liệu', 'Ảnh', 'Số từ', 'Kiểm tra', 'WordPress', 'WP Post ID',
                   'Trạng thái', 'Ngày đăng', 'URL đã đăng', 'Ghi chú / Nội dung lỗi'])
    for r in dong_bai:
        ws.append([r['site'], r['danh_muc'], r['sku'], r['ten'], r['mau'], r['chon'],
                   r['du_lieu'], r['anh'], r['so_tu'], r['kiem_tra'], r['wp'], r['wp_id'],
                   r['trang_thai'], str(r['ngay'])[:16], r['link'], r['ghi_chu']])
    _rong_cot(ws, [9, 15, 24, 40, 13, 10, 9, 7, 8, 11, 11, 11, 12, 17, 34, 46])
    _to_mau(ws, 6, {'Có': XANH, 'Không': XAM})
    _to_ty_le(ws, 7)
    _to_mau(ws, 10, {'Đạt': XANH, 'Cảnh báo': VANG, 'Bị chặn': DO})
    _to_mau(ws, 13, MAU_TRANG_THAI)
    for h in range(2, ws.max_row + 1):
        ws.cell(row=h, column=16).alignment = Alignment(wrap_text=True, vertical='top')
    ws.auto_filter.ref = ws.dimensions

    duong_dan = Path(duong_dan or BASE / 'bang-dieu-khien.xlsx')
    wb.save(duong_dan)
    return duong_dan, len(dong_bai), len(dong_sp)


if __name__ == '__main__':
    f, nb, ns = xuat()
    print(f'Đã xuất {f}  |  {nb} dòng bài viết, {ns} dòng sản phẩm')
