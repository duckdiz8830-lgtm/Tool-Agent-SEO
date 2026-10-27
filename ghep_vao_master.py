# -*- coding: utf-8 -*-
"""
SONEALEO ULTRA 3.0 — GHÉP KẾT QUẢ VISION VÀO MASTER (bản sao).

Đầu vào : bien-may-ket-qua.xlsx và/hoặc catalogue-ket-qua.xlsx
          (ĐÃ ĐƯỢC NGƯỜI SOÁT — dòng 'Cần kiểm' còn dấu X sẽ BỎ QUA)
Đầu ra  : <master>_VISION.xlsx — bản sao master với cột mới hậu tố
          '[đọc từ ảnh]' + sheet 'DoiChieu' liệt kê xung đột.

LUẬT GHÉP (thà bỏ sót còn hơn ghép sai — đúng triết lý tool):
  1. Khớp SKU khi ĐỦ: cùng kVA + hãng khớp + (dầu/khô khớp nếu cả 2 bên
     có) + (số pha khớp nếu cả 2 bên có). Thiếu một tiêu chí bắt buộc
     -> không ghép.
  2. KHÔNG BAO GIỜ ghi đè: cột đã có giá trị thì giữ nguyên; giá trị
     vision khác giá trị sẵn có -> ghi vào sheet DoiChieu, người quyết.
  3. Nhiều nguồn vision cho cùng 1 SKU mà số khác nhau -> không điền,
     ghi DoiChieu.
  4. Ưu tiên nguồn: biển máy > catalogue (biển là máy thật).

CÁCH DÙNG
    python ghep_vao_master.py <file master.xlsx> [bien-may-ket-qua.xlsx] [catalogue-ket-qua.xlsx]
"""
import os
import re
import sys
import unicodedata
from chuan_hoa import bo_dau as _bo_dau   # Ver 5.7 — gom 9 bản _bo_dau về 1 nguồn (xem chuan_hoa.py)


_TRUONG_GHEP = [           # (khoá nguồn, tên cột đích, )
    ('to_dau_day', 'Tổ đấu dây [đọc từ ảnh]'),
    ('po_w', 'Tổn hao không tải Po (W) [đọc từ ảnh]'),
    ('pk_w', 'Tổn hao ngắn mạch Pk (W) [đọc từ ảnh]'),
    ('uk_pct', 'Điện áp ngắn mạch Uk (%) [đọc từ ảnh]'),
    ('io_pct', 'Dòng điện không tải Io (%) [đọc từ ảnh]'),
    ('khoi_luong_dau_kg', 'Khối lượng dầu (kg) [đọc từ ảnh]'),
    ('tong_khoi_luong_kg', 'Tổng khối lượng (kg) [đọc từ ảnh]'),
    ('kich_thuoc_mm', 'Kích thước (mm) [đọc từ ảnh]'),
    ('tieu_chuan', 'Tiêu chuẩn [đọc từ ảnh]'),
]
COT_NGUON = 'Nguồn ảnh đã đọc'

# cột sẵn có trong master mang cùng ý nghĩa — để ĐỐI CHIẾU (không ghi đè)
_DOI_CHIEU_COT_CU = {
    'po_w': 'Tổn hao không tải Po (W, catalogue)',
    'pk_w': 'Tổn hao ngắn mạch Pk (W, catalogue)',
    'uk_pct': 'Điện áp ngắn mạch Uk (%, catalogue)',
    'io_pct': 'Dòng điện không tải Io (%, catalogue)',
    'to_dau_day': 'Tổ đấu dây (catalogue)',
    'tong_khoi_luong_kg': 'Tổng khối lượng (kg, catalogue)',
    'khoi_luong_dau_kg': 'Khối lượng dầu (kg, catalogue)',
}


def _doc_ket_qua(duong_dan, uu_tien):
    """Đọc file kết quả vision đã soát -> list dict. Bỏ dòng còn 'Cần kiểm'."""
    import openpyxl
    if not duong_dan or not os.path.exists(duong_dan):
        return []
    wb = openpyxl.load_workbook(duong_dan, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    # map tên cột hiển thị -> khoá kỹ thuật (đảo từ COT_XUAT của 2 script kia)
    dao = {'Hãng': 'thuong_hieu', 'Hãng (đọc từ biển)': 'thuong_hieu',
           'Dầu/Khô': 'loai_may', 'Số pha': 'so_pha',
           'Công suất (kVA)': 'cong_suat_kva', 'Điện áp': 'dien_ap',
           'Tổ đấu dây': 'to_dau_day', 'Tổn hao không tải Po (W)': 'po_w',
           'Tổn hao ngắn mạch Pk (W)': 'pk_w', 'Điện áp ngắn mạch Uk (%)': 'uk_pct',
           'Dòng không tải Io (%)': 'io_pct', 'Khối lượng dầu (kg)': 'khoi_luong_dau_kg',
           'Tổng khối lượng (kg)': 'tong_khoi_luong_kg', 'Kích thước (mm)': 'kich_thuoc_mm',
           'Tiêu chuẩn': 'tieu_chuan', 'Cần kiểm': 'can_kiem',
           'Ảnh nguồn': 'nguon', 'Nguồn (file / trang)': 'nguon'}
    hdr = [dao.get(str(h).strip(), None) if h else None for h in rows[0]]
    ra = []
    for r in rows[1:]:
        d = {k: v for k, v in zip(hdr, r) if k}
        if not d or d.get('can_kiem'):
            continue                     # người chưa gỡ dấu X -> chưa tin
        if d.get('cong_suat_kva') in (None, ''):
            continue
        d['_uu_tien'] = uu_tien
        ra.append(d)
    wb.close()
    return ra


def _khop_row_master(d, ten_hang, thuong_hieu_cot, kva_cot):
    """d (kết quả vision) có khớp dòng master này không? Trả bool."""
    # kVA — bắt buộc
    m = re.search(r'\d+(?:[.,]\d+)?', str(kva_cot or ''))
    kva_master = float(m.group(0).replace(',', '.')) if m else None
    if kva_master is None:
        m2 = re.search(r'(\d+(?:[.,]\d+)?)\s*kva', _bo_dau(ten_hang))
        kva_master = float(m2.group(1).replace(',', '.')) if m2 else None
    if kva_master is None or float(d['cong_suat_kva']) != kva_master:
        return False
    # hãng — bắt buộc
    th_v = _bo_dau(d.get('thuong_hieu'))
    kho_master = _bo_dau(f'{thuong_hieu_cot} {ten_hang}')
    if not th_v or th_v not in kho_master:
        return False
    # dầu/khô — bắt buộc khi cả 2 bên có
    lm_v = (d.get('loai_may') or '').lower()
    mm = re.search(r'(?:bien\s*ap|mba)\s+(?:\w+\s+)?(dau|kho)\b', _bo_dau(ten_hang))
    lm_m = mm.group(1) if mm else None
    if lm_v in ('dau', 'kho') and lm_m and lm_v != lm_m:
        return False
    # số pha — bắt buộc khi cả 2 bên có
    p_v = d.get('so_pha')
    mp = re.search(r'\b([13])\s*pha\b', _bo_dau(ten_hang))
    p_m = int(mp.group(1)) if mp else None
    if p_v and p_m and int(p_v) != p_m:
        return False
    return True


def ghep(master_path, cac_file_ket_qua):
    import openpyxl
    nguon = []
    for duong_dan, uu_tien in cac_file_ket_qua:
        nguon += _doc_ket_qua(duong_dan, uu_tien)
    if not nguon:
        print('Không có dòng kết quả nào dùng được (chưa có file, hoặc mọi dòng còn "Cần kiểm").')
        return None
    nguon.sort(key=lambda d: d['_uu_tien'])     # biển máy (0) trước catalogue (1)

    wb = openpyxl.load_workbook(master_path)
    ws = None
    for t in wb.sheetnames:
        if 'may_bien_ap' in _bo_dau(t).replace(' ', '_'):
            ws = wb[t]
            break
    ws = ws or wb.active
    hdr = {str(c.value).strip(): i + 1 for i, c in enumerate(ws[1]) if c.value}

    def cot(ten):
        if ten not in hdr:
            hdr[ten] = ws.max_column + 1
            ws.cell(row=1, column=hdr[ten], value=ten)
        return hdr[ten]

    i_ten, i_th = hdr.get('Tên hàng'), hdr.get('Nhãn Hiệu / Xuất Xứ')
    i_kva = hdr.get('Công Suất (kVA)')
    doi_chieu, dem_dien, dem_sku = [], 0, 0

    for r in range(2, ws.max_row + 1):
        ten = ws.cell(row=r, column=i_ten).value if i_ten else None
        if not ten:
            continue
        th = ws.cell(row=r, column=i_th).value if i_th else ''
        kva = ws.cell(row=r, column=i_kva).value if i_kva else ''
        khop = [d for d in nguon if _khop_row_master(d, ten, th, kva)]
        if not khop:
            continue
        dem_sku += 1
        nguon_da_dung = []
        for khoa, ten_cot in _TRUONG_GHEP:
            gia_tri = [(d.get(khoa), d.get('nguon', '?')) for d in khop
                       if d.get(khoa) not in (None, '')]
            if not gia_tri:
                continue
            # luật 3 — nhiều nguồn lệch nhau: không điền
            phan_biet = {str(v).strip() for v, _n in gia_tri}
            if len(phan_biet) > 1:
                doi_chieu.append([ten, ten_cot, ' | '.join(
                    f'{v} ({n})' for v, n in gia_tri), 'nhiều nguồn lệch nhau — không điền'])
                continue
            v, n = gia_tri[0]
            # luật 2 — đối chiếu với cột catalogue sẵn có (không ghi đè)
            cot_cu = _DOI_CHIEU_COT_CU.get(khoa)
            if cot_cu and cot_cu in hdr:
                cu = ws.cell(row=r, column=hdr[cot_cu]).value
                if cu not in (None, '') and str(cu).strip() != str(v).strip():
                    doi_chieu.append([ten, ten_cot, f'ảnh: {v} ({n})  vs  master: {cu}',
                                      'lệch với dữ liệu sẵn có — người quyết'])
                    continue
            o = ws.cell(row=r, column=cot(ten_cot))
            if o.value in (None, ''):
                o.value = v
                dem_dien += 1
                if n not in nguon_da_dung:
                    nguon_da_dung.append(n)
        if nguon_da_dung:
            o = ws.cell(row=r, column=cot(COT_NGUON))
            if not o.value:
                o.value = '; '.join(nguon_da_dung)

    if doi_chieu:
        ws2 = wb.create_sheet('DoiChieu') if 'DoiChieu' not in wb.sheetnames else wb['DoiChieu']
        if ws2.max_row <= 1:
            ws2.append(['Tên hàng', 'Trường', 'Giá trị', 'Ghi chú'])
        for dong in doi_chieu:
            ws2.append(dong)

    goc, duoi = os.path.splitext(master_path)
    ra = f'{goc}_VISION{duoi}'
    wb.save(ra)
    print(f'Đã điền {dem_dien} ô cho {dem_sku} SKU khớp. Xung đột chờ người quyết: {len(doi_chieu)} (sheet DoiChieu).')
    print(f'Xuất: {ra} (master gốc KHÔNG bị sửa)')
    return ra


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Cách dùng: python ghep_vao_master.py <master.xlsx> [bien-may-ket-qua.xlsx] [catalogue-ket-qua.xlsx]')
        sys.exit(1)
    master = sys.argv[1]
    bm = sys.argv[2] if len(sys.argv) > 2 else 'bien-may-ket-qua.xlsx'
    cl = sys.argv[3] if len(sys.argv) > 3 else 'catalogue-ket-qua.xlsx'
    ghep(master, [(bm, 0), (cl, 1)])
