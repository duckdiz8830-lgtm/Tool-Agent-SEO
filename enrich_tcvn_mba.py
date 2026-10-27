# -*- coding: utf-8 -*-
"""
SONEALEO ULTRA 2.9 — ENRICH MBA THEO TCVN 8525:2015 + DÒNG ĐỊNH MỨC.

VÌ SAO
~160 SKU máy biến áp chỉ có tên + công suất + cấp điện áp -> Hard Block
chỉ cho AI nhắc đúng 2-3 con số -> bài mỏng. Script này sinh thêm thông
số THẬT bằng 2 nguồn không cần AI, không tốn quota Gemini:

  1. CÔNG THỨC ĐỊNH NGHĨA (I = S/(√3·U) cho 3 pha, I = S/U cho 1 pha)
     -> dòng điện danh định 2 phía. Đây là toán, không phải đoán.
  2. BẢNG TRA TCVN 8525:2015 (hiệu suất năng lượng tối thiểu MEPS)
     -> giá trị PHÁP QUY công khai theo mức kVA. Nguồn: toàn văn tiêu
     chuẩn trên thuvienphapluat.vn, đối chiếu chéo với bản OCR độc lập.

NGUYÊN TẮC (giữ đúng brief 2.8)
  - Thiếu dữ liệu -> ĐỂ TRỐNG, không đoán. Cụ thể:
      * TCVN 8525 CHỈ áp dụng máy BA PHA 5..4000 kVA, vào ≤35kV, ra ≤0.4kV
        -> máy 1 pha (12.7/0.23kV) KHÔNG được điền cột hiệu suất.
      * Không parse được cặp điện áp trung/hạ -> không tính dòng.
      * Không rõ dầu hay khô -> không tra bảng (2 bảng khác nhau).
  - KHÔNG ghi đè file nguồn — luôn xuất file mới `<tên>_TCVN.xlsx`.
  - Tên cột ghi ĐƠN VỊ TRONG NGOẶC để _kho_cua_dong (render_phase2) bóc
    được đơn vị -> Hard Block tự hiểu số mới là số hợp lệ.
  - Tên cột đã soi qua _TU_KHOA_COT_NOI_BO (profiles.py) — không dính
    từ khoá bị chặn ('nguồn', 'ghi chú', 'version'...), Dynamic Schema
    2.8 sẽ tự nhận, KHÔNG cần sửa dòng code nào của tool.

CÁCH DÙNG
    python enrich_tcvn_mba.py "duong/dan/toi/file.xlsx"
  - File master nhiều sheet: tự tìm sheet tên chứa 'May_Bien_Ap'.
  - File lẻ 1 sheet: dùng sheet active.
  - Chạy lại nhiều lần an toàn: cột đã có thì ghi đè giá trị tính lại,
    không nhân đôi cột (idempotent theo TÊN CỘT).
"""
import math
import os
import re
import sys
import unicodedata
from chuan_hoa import bo_dau as _bo_dau   # Ver 5.7 — gom 9 bản _bo_dau về 1 nguồn (xem chuan_hoa.py)

# ---------------------------------------------------------------- TCVN 8525:2015
# Bảng 1 — MBA phân phối BA PHA loại NGÂM TRONG DẦU (kVA -> MEPS %).
# Chép nguyên văn từ toàn văn tiêu chuẩn (thuvienphapluat.vn, số hiệu
# TCVN 8525:2015), đối chiếu khớp 100% với bản OCR độc lập (studocu).
# Hàng '31,5/32' và '315/320' của tiêu chuẩn: cả 2 mức dùng chung 1 giá
# trị -> khai alias bên dưới.
_BANG_1_DAU = [
    (25, 98.40), (31.5, 98.50), (50, 98.66), (75, 98.77), (100, 98.87),
    (125, 98.92), (160, 98.97), (180, 99.01), (200, 99.06), (250, 99.10),
    (315, 99.16), (400, 99.19), (500, 99.21), (560, 99.22), (630, 99.26),
    (750, 99.28), (800, 99.30), (1000, 99.32), (1250, 99.35), (1500, 99.37),
    (1600, 99.39), (2000, 99.41), (2500, 99.42), (3000, 99.44), (3200, 99.46),
    (3500, 99.48), (4000, 99.50),
]
# Bảng 2 — MBA phân phối BA PHA loại KHÔ. Hàng đầu của tiêu chuẩn là
# '≤ 50 -> 97,50'. LƯU Ý NGUỒN: bản toàn văn công khai che 4 nhãn kVA
# (các giá trị hiệu suất 97,89 / 98,72 / 98,92 / 99,09 hiển thị nguyên
# văn nhưng nhãn kVA đứng trước bị che) — 4 nhãn này được suy từ vị trí
# duy nhất còn trống trong thang công suất chuẩn (100/500/1000/2500).
# Nếu có bản PDF gốc của tiêu chuẩn, đối chiếu lại 4 hàng đánh dấu (*).
_BANG_2_KHO = [
    # Ver 3.1 — đối chiếu ẢNH CATALOGUE THIBIDI thật (06/08/2026):
    # 12/13 mức khớp bản toàn văn; mức 250 catalogue in 98,46 (bản toàn
    # văn OCR ra 98,49 — tin catalogue in ấn chính thức hơn OCR).
    # Nhãn (*) 1000 và 2500 đã được catalogue XÁC NHẬN ĐÚNG; còn (*)
    # 100 và 500 catalogue THIBIDI không có mức đó, giữ nguyên suy luận.
    (50, 97.50), (100, 97.89),          # (*) 100 — chưa kiểm được
    (160, 98.15), (250, 98.46), (315, 98.59), (400, 98.66),
    (500, 98.72),                        # (*) 500
    (560, 98.77), (630, 98.80), (750, 98.85), (800, 98.86),
    (1000, 98.92),                       # (*) 1000
    (1250, 98.97), (1500, 99.01), (1600, 99.02), (2000, 99.06),
    (2500, 99.09),                       # (*) 2500
    (3000, 99.12), (3200, 99.13), (3500, 99.15), (4000, 99.18),
]
# Mức ghi kép trong tiêu chuẩn ('31,5/32', '315/320') — tra thẳng.
_ALIAS_KVA = {'dau': {32: 98.50, 320: 99.16}, 'kho': {320: 98.59}}

# Tên cột sinh ra — ĐƠN VỊ TRONG NGOẶC (Hard Block bóc từ tên cột),
# không chứa từ khoá nội bộ của profiles._TU_KHOA_COT_NOI_BO.
COT_I_TRUNG = 'Dòng điện danh định phía trung áp (A)'
COT_I_HA = 'Dòng điện danh định phía hạ áp (A)'
COT_MEPS = 'Hiệu suất năng lượng tối thiểu TCVN 8525:2015 (%)'
COT_TIEU_CHUAN = 'Tiêu chuẩn hiệu suất năng lượng áp dụng'


# ---------------------------------------------------------------- parse record
_RE_KVA = re.compile(r'(\d+(?:[.,]\d+)?)\s*kva\b', re.IGNORECASE)
_RE_AP_CAP = re.compile(r'(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)\s*kv\b',
                        re.IGNORECASE)
_RE_PHA = re.compile(r'\b([13])\s*pha\b|\b([13])p\b')
# 'biến áp dầu' / 'mba khô' — bắt theo CỤM để 'đầu cáp' (bo dấu = 'dau cap')
# không bị nhận nhầm là máy dầu.
_RE_LOAI = re.compile(r'(?:bien\s*ap|mba)\s+(?:\w+\s+)?(dau|kho)\b')
# Ver 3.1 — PHỤ KIỆN đi kèm MBA (vỏ, giá treo, ty, móc...) cũng chứa
# 'MBA 3P 560kVA' trong tên -> từng bị tính dòng định mức 808A cho...
# cái vỏ tôn (24 dòng sai, GPT bắt được). Tên bắt đầu bằng các từ này
# -> KHÔNG phải máy biến áp -> bỏ qua toàn bộ.
_RE_PHU_KIEN = re.compile(
    r'^\s*(vo|nap|gia|ty|moc|khung|canh|thung|su|boc|chup|de|bang tai)\b')


def la_phu_kien(ten_hang):
    """True nếu dòng là PHỤ KIỆN của MBA chứ không phải máy."""
    return bool(_RE_PHU_KIEN.search(_bo_dau(ten_hang)))


def _so(chuoi):
    return float(str(chuoi).replace(',', '.'))


def doc_kva(o_cong_suat, ten_hang):
    """Ưu tiên cột 'Công Suất (kVA)'; thiếu thì bóc từ Tên hàng (cùng
    triết lý các cột '(trích từ tên)' sẵn có của tool)."""
    for nguon in (o_cong_suat, ten_hang):
        m = _RE_KVA.search(str(nguon or ''))
        if m:
            return _so(m.group(1))
        # cột kVA đôi khi chỉ ghi số trần
        if nguon is o_cong_suat and str(nguon or '').strip():
            m2 = re.fullmatch(r'\s*(\d+(?:[.,]\d+)?)\s*', str(nguon))
            if m2:
                return _so(m2.group(1))
    return None


def doc_cap_ap(o_cap_ap, ten_hang):
    """Trả (trung_ap_kV, ha_ap_kV) khi có dạng 'A/B kV' hợp lý
    (A>1kV, B≤0.46kV — lưới hạ áp VN 0.4/0.23). Dạng '220V', '24 kV',
    '230/400V' -> None (không đoán chiều đấu)."""
    for nguon in (o_cap_ap, ten_hang):
        m = _RE_AP_CAP.search(str(nguon or ''))
        if m:
            a, b = _so(m.group(1)), _so(m.group(2))
            if a > 1 and 0 < b <= 0.46:
                return a, b
    return None


def doc_pha(ten_hang):
    m = _RE_PHA.search(_bo_dau(ten_hang))
    if m:
        return int(m.group(1) or m.group(2))
    return None


def doc_loai(ten_hang):
    m = _RE_LOAI.search(_bo_dau(ten_hang))
    return m.group(1) if m else None   # 'dau' | 'kho' | None


# ---------------------------------------------------------------- tính toán
def dong_dinh_muc(kva, cap_ap, pha):
    """(I_trung_A, I_ha_A) từ công thức định nghĩa. Trả None nếu thiếu
    bất kỳ đầu vào nào — không đoán."""
    if not (kva and cap_ap and pha in (1, 3)):
        return None
    trung, ha = cap_ap
    if pha == 3:
        i_trung = kva / (math.sqrt(3) * trung)
        i_ha = kva / (math.sqrt(3) * ha)
    else:
        i_trung = kva / trung
        i_ha = kva / ha
    return round(i_trung, 1), round(i_ha, 1)


def meps_tcvn(kva, pha, loai, cap_ap):
    """MEPS (%) theo TCVN 8525:2015. Trả None khi NGOÀI PHẠM VI tiêu
    chuẩn: khác 3 pha, <5 hoặc >4000 kVA, không rõ dầu/khô, trung áp
    >35kV, hạ áp >0.4kV. Mức trung gian: nội suy tuyến tính (chú thích
    Bảng 1 của chính tiêu chuẩn)."""
    if pha != 3 or not loai or not kva or not (5 <= kva <= 4000):
        return None
    if cap_ap and (cap_ap[0] > 35 or cap_ap[1] > 0.46):
        return None
    alias = _ALIAS_KVA.get(loai, {})
    if kva in alias:
        return alias[kva]
    bang = _BANG_1_DAU if loai == 'dau' else _BANG_2_KHO
    if kva <= bang[0][0]:
        return bang[0][1]      # hàng đầu là '≤ X kVA'
    if kva > bang[-1][0]:
        return None
    for (k1, e1), (k2, e2) in zip(bang, bang[1:]):
        if kva == k2:
            return e2
        if k1 < kva < k2:
            return round(e1 + (e2 - e1) * (kva - k1) / (k2 - k1), 2)
    return None


# ---------------------------------------------------------------- ghi Excel
def enrich_file(duong_dan):
    import openpyxl
    wb = openpyxl.load_workbook(duong_dan)
    ws = None
    for ten in wb.sheetnames:
        if 'may_bien_ap' in _bo_dau(ten).replace(' ', '_'):
            ws = wb[ten]
            break
    ws = ws or wb.active
    print(f'Sheet: {ws.title} — {ws.max_row - 1} dòng')

    hdr = {str(c.value).strip(): i + 1
           for i, c in enumerate(ws[1]) if c.value}

    def cot(ten):
        """Lấy index cột theo tên; chưa có thì tạo ở cuối (idempotent)."""
        if ten not in hdr:
            hdr[ten] = ws.max_column + 1
            ws.cell(row=1, column=hdr[ten], value=ten)
        return hdr[ten]

    i_ten = hdr.get('Tên hàng')
    i_cs = hdr.get('Công Suất (kVA)')
    i_ap = hdr.get('Cấp Điện Áp (kV)') or hdr.get('Cấp Điện Áp')
    if not i_ten:
        print('LỖI: không thấy cột "Tên hàng" — dừng, không ghi gì.')
        return None
    c_it, c_ih = cot(COT_I_TRUNG), cot(COT_I_HA)
    c_me, c_tc = cot(COT_MEPS), cot(COT_TIEU_CHUAN)

    dem = {'dong': 0, 'meps': 0, 'bo_thieu_ap': 0, 'bo_1pha_meps': 0,
           'bo_thieu_kva': 0, 'bo_khong_ro_loai': 0, 'bo_phu_kien': 0}
    for r in range(2, ws.max_row + 1):
        ten = ws.cell(row=r, column=i_ten).value
        if not ten:
            continue
        if la_phu_kien(ten):
            dem['bo_phu_kien'] += 1      # Ver 3.1 — vỏ/giá treo... không phải máy
            continue
        kva = doc_kva(ws.cell(row=r, column=i_cs).value if i_cs else None, ten)
        cap = doc_cap_ap(ws.cell(row=r, column=i_ap).value if i_ap else None, ten)
        pha = doc_pha(ten)
        loai = doc_loai(ten)

        if not kva:
            dem['bo_thieu_kva'] += 1
            continue
        dd = dong_dinh_muc(kva, cap, pha)
        if dd:
            ws.cell(row=r, column=c_it, value=dd[0])
            ws.cell(row=r, column=c_ih, value=dd[1])
            dem['dong'] += 1
        elif not cap:
            dem['bo_thieu_ap'] += 1

        me = meps_tcvn(kva, pha, loai, cap)
        if me is not None:
            ws.cell(row=r, column=c_me, value=me)
            ws.cell(row=r, column=c_tc, value='TCVN 8525:2015')
            dem['meps'] += 1
        elif pha == 1:
            dem['bo_1pha_meps'] += 1
        elif pha == 3 and not loai:
            dem['bo_khong_ro_loai'] += 1

    goc, duoi = os.path.splitext(duong_dan)
    ra = f'{goc}_TCVN{duoi}'
    wb.save(ra)
    print(f'\nĐiền dòng định mức : {dem["dong"]} SKU')
    print(f'Điền MEPS TCVN 8525: {dem["meps"]} SKU (chỉ máy 3 pha trong phạm vi tiêu chuẩn)')
    print(f'Bỏ qua — thiếu kVA : {dem["bo_thieu_kva"]}')
    print(f'Bỏ qua — PHỤ KIỆN (vỏ, giá treo... không phải máy): {dem["bo_phu_kien"]}')
    print(f'Bỏ qua — thiếu cặp điện áp trung/hạ: {dem["bo_thieu_ap"]}')
    print(f'Không điền MEPS — máy 1 pha (ngoài phạm vi TCVN): {dem["bo_1pha_meps"]}')
    print(f'Không điền MEPS — 3 pha nhưng không rõ dầu/khô  : {dem["bo_khong_ro_loai"]}')
    print(f'\nXuất: {ra}\n(File gốc KHÔNG bị sửa. Import file _TCVN vào tool là Dynamic Schema tự nhận cột mới.)')
    return ra


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Cách dùng: python enrich_tcvn_mba.py <file.xlsx>')
        sys.exit(1)
    enrich_file(sys.argv[1])


# ================================================================ Ver 3.2
# ENRICH TỪ CATALOGUE THIBIDI (bóc từ PDF bằng toạ độ, xem tra_cuu_thibidi).
# Chạy SAU phần TCVN. Chỉ điền ô ĐANG TRỐNG, không ghi đè; chỉ áp cho SKU
# hãng THIBIDI; tên cột ghi rõ "(catalogue THIBIDI)" để không ai nhầm là
# số đo của chính máy đó.
COT_TB = {
    'po': 'Tổn hao không tải Po (W, catalogue THIBIDI)',
    'pk': 'Tổn hao có tải Pk (W, catalogue THIBIDI)',
    'uk': 'Điện áp ngắn mạch Uk (%, catalogue THIBIDI)',
    'hs': 'Hiệu suất năng lượng tối thiểu (%, catalogue THIBIDI)',
    'nguon': 'Nguồn số liệu catalogue',
}


def enrich_thibidi(duong_dan):
    import openpyxl
    import tra_cuu_thibidi as TC
    import kien_thuc_bien_thien as K
    wb = openpyxl.load_workbook(duong_dan)
    ws = next((wb[t] for t in wb.sheetnames
               if 'may_bien_ap' in _bo_dau(t).replace(' ', '_')), wb.active)
    hdr = {str(c.value).strip(): i + 1 for i, c in enumerate(ws[1]) if c.value}

    def cot(ten):
        if ten not in hdr:
            hdr[ten] = ws.max_column + 1
            ws.cell(row=1, column=hdr[ten], value=ten)
        return hdr[ten]

    i_ten = hdr.get('Tên hàng')
    i_cs, i_ap = hdr.get('Công Suất (kVA)'), hdr.get('Cấp Điện Áp (kV)')
    i_th = hdr.get('Nhãn Hiệu / Xuất Xứ')
    if not i_ten:
        print('LỖI: thiếu cột "Tên hàng".')
        return None
    dem = 0
    for r in range(2, ws.max_row + 1):
        ten = ws.cell(row=r, column=i_ten).value
        if not ten or la_phu_kien(ten):
            continue
        row = {'ten_goc': ten,
               'cong_suat': ws.cell(row=r, column=i_cs).value if i_cs else '',
               'cap_dien_ap': ws.cell(row=r, column=i_ap).value if i_ap else '',
               'thuong_hieu': ws.cell(row=r, column=i_th).value if i_th else ''}
        d = K.dac_trung(row)
        b = TC.tra(d['kva'], d['pha'], d['loai'], d['hang'])
        if not b:
            continue
        if b['loai'] == 'dau':
            gia = {'po': b['po_amorphous'] if d['loi'] == 'amorphous' else b['po_silic'],
                   'pk': b['pk'], 'uk': b['uk']}
        else:
            gia = {'po': b['po_24kv'], 'pk': b['pk_24kv'], 'uk': b['uk'],
                   'hs': b['hieu_suat']}
        da_dien = False
        for k, v in gia.items():
            if v is None:
                continue
            o = ws.cell(row=r, column=cot(COT_TB[k]))
            if o.value in (None, ''):        # KHÔNG ghi đè
                o.value = v
                da_dien = True
        if da_dien:
            o = ws.cell(row=r, column=cot(COT_TB['nguon']))
            if not o.value:
                o.value = b['nguon'] + (' (mức nội suy)' if b['noi_suy'] else '')
            dem += 1
    goc, duoi = os.path.splitext(duong_dan)
    ra = f'{goc}_THIBIDI{duoi}'
    wb.save(ra)
    print(f'Điền thông số catalogue THIBIDI: {dem} SKU')
    print(f'Xuất: {ra} (file vào KHÔNG bị sửa)')
    return ra
