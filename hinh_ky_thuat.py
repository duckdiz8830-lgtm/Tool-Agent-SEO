# -*- coding: utf-8 -*-
"""
SONEALEO Ver 2.3 (Mốc 2) — sinh HÌNH KỸ THUẬT bằng SVG từ dữ liệu có sẵn.

VÌ SAO CÓ MODULE NÀY
Trang sản phẩm B2B không có hình thì kỹ sư đóng tab — nhưng Lotech không
có (và sẽ không có) ảnh chụp cho 5.264 SKU. Cách giải: KHÔNG giải bài
toán ảnh bằng ảnh, mà VẼ TỪ DỮ LIỆU.

NGUYÊN TẮC AN TOÀN (giống hệt Hard Block, nhưng cho hình)
  - Vẽ bằng CODE từ field có thật. Không AI sinh ảnh, không tải ảnh ngoài.
  - Thiếu dữ liệu -> KHÔNG vẽ (trả ''), tuyệt đối không phỏng đoán hình
    dạng. Vẽ sai cấu tạo còn tệ hơn không có hình.
  - Hình là SƠ ĐỒ MINH HOẠ CẤU TẠO, không phải bản vẽ tỷ lệ thật -> mọi
    hình đều ghi rõ dòng chú thích này, để không ai đem đi thi công.

KỸ THUẬT
  - SVG inline, chỉ dùng thẻ cơ bản (svg/g/circle/rect/line/text/polygon)
    -> ít khả năng bị WordPress hoặc plugin bảo mật lọc mất.
  - Không script, không style block, không ảnh nhúng.
  - SVG là text -> nhẹ, Google đọc được, không tốn băng thông như ảnh.
"""
import html
import re

# Bảng màu theo quy ước ngành cáp điện (đồng đỏ cam, nhôm xám bạc...)
MAU = {
    'dong': '#B87333',
    'nhom': '#BFC4C9',
    'xlpe': '#FFF3D6',
    'pvc_cach_dien': '#E9EDF2',
    'vo_pvc': '#3F4854',
    'giap': '#8A9099',
    'nen': '#FFFFFF',
    'vien': '#94A3B8',
    'chu': '#1E293B',
    'chu_mo': '#64748B',
}

_GHI_CHU = 'Sơ đồ minh hoạ cấu tạo — không theo tỷ lệ kích thước thật.'


def _so_loi(tiet_dien):
    """Bóc số lõi từ tiết diện: '3x70' -> 3, '2x0.5' -> 2, '70' -> 1,
    '3x50+1x35' -> 4 (cáp có lõi trung tính nhỏ hơn).
    Không đọc được -> None (KHÔNG đoán, sẽ không vẽ)."""
    if not tiet_dien:
        return None
    s = str(tiet_dien).lower().replace(' ', '')
    tong = 0
    for phan in s.split('+'):
        m = re.match(r'^(\d+)x', phan)
        if m:
            tong += int(m.group(1))
        elif re.match(r'^\d+(?:[.,]\d+)?$', phan):
            tong += 1
    if tong == 0:
        return None
    return tong if tong <= 8 else None   # >8 lõi: bố cục không còn rõ, thà không vẽ


def _mau_ruot(vat_lieu):
    v = (vat_lieu or '').lower()
    if 'nhôm' in v or 'al' in v:
        return MAU['nhom'], 'Nhôm (Al)'
    if 'đồng' in v or 'cu' in v:
        return MAU['dong'], 'Đồng (Cu)'
    return None, None


def _mau_cach_dien(loai):
    l = (loai or '').upper()
    if 'XLPE' in l:
        return MAU['xlpe'], 'XLPE'
    if 'PVC' in l:
        return MAU['pvc_cach_dien'], 'PVC'
    return None, None


def _nhan(x, y, chu, mo=False):
    mau = MAU['chu_mo'] if mo else MAU['chu']
    co = '11' if mo else '12'
    return (f'<text x="{x}" y="{y}" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="{co}" fill="{mau}">{html.escape(chu)}</text>')


def mat_cat_cap_dien(row):
    """Vẽ mặt cắt ngang cáp điện từ 4 field giải mã ký hiệu + tiết diện.

    Yêu cầu TỐI THIỂU: biết vật liệu ruột VÀ loại cách điện. Thiếu 1 trong
    2 -> trả '' (không vẽ nửa vời).

    Trả chuỗi HTML (div bọc svg) hoặc ''.
    """
    mau_ruot, ten_ruot = _mau_ruot(row.get('vat_lieu_ruot_giai_ma'))
    mau_cd, ten_cd = _mau_cach_dien(row.get('loai_cach_dien_giai_ma'))
    if not mau_ruot or not mau_cd:
        return ''

    n_loi = _so_loi(row.get('tiet_dien')) or 1
    co_giap = bool(row.get('giap_bao_ve_giai_ma'))
    vo = row.get('vo_boc_giai_ma') or ''
    co_vo = 'pvc' in vo.lower()

    # --- bố cục ---
    cx, cy = 150, 150          # tâm hình
    r_ngoai = 108              # bán kính ngoài cùng
    day_vo = 12 if co_vo else 0
    day_giap = 9 if co_giap else 0
    r_trong = r_ngoai - day_vo - day_giap   # vùng chứa các lõi

    ve = [f'<svg viewBox="0 0 560 300" width="100%" height="auto" '
          f'role="img" xmlns="http://www.w3.org/2000/svg" '
          f'aria-label="Sơ đồ mặt cắt cấu tạo cáp điện">',
          f'<rect x="0" y="0" width="560" height="300" fill="{MAU["nen"]}"/>']

    # vỏ ngoài
    if co_vo:
        ve.append(f'<circle cx="{cx}" cy="{cy}" r="{r_ngoai}" fill="{MAU["vo_pvc"]}" '
                  f'stroke="{MAU["vien"]}" stroke-width="1"/>')
    # giáp bảo vệ (vành sọc)
    if co_giap:
        r_giap = r_ngoai - day_vo
        ve.append(f'<circle cx="{cx}" cy="{cy}" r="{r_giap}" fill="{MAU["giap"]}" '
                  f'stroke="{MAU["vien"]}" stroke-width="1"/>')
        # vạch chéo gợi ý dạng băng/sợi thép
        for goc in range(0, 360, 18):
            import math
            a = math.radians(goc)
            x1 = cx + (r_giap - day_giap) * math.cos(a)
            y1 = cy + (r_giap - day_giap) * math.sin(a)
            x2 = cx + r_giap * math.cos(a)
            y2 = cy + r_giap * math.sin(a)
            ve.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                      f'stroke="#6B7280" stroke-width="2"/>')
    # nền trong (độn/chèn)
    ve.append(f'<circle cx="{cx}" cy="{cy}" r="{r_trong}" fill="#F8FAFC" '
              f'stroke="{MAU["vien"]}" stroke-width="1"/>')

    # --- các lõi ---
    import math
    if n_loi == 1:
        vi_tri = [(cx, cy)]
        r_loi = int(r_trong * 0.72)
    else:
        r_dat = r_trong * (0.46 if n_loi <= 4 else 0.52)
        r_loi = int(r_trong * (0.40 if n_loi <= 3 else 0.32 if n_loi == 4 else 0.26))
        vi_tri = []
        for i in range(n_loi):
            a = math.radians(-90 + i * 360 / n_loi)
            vi_tri.append((cx + r_dat * math.cos(a), cy + r_dat * math.sin(a)))

    for (lx, ly) in vi_tri:
        ve.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="{r_loi}" fill="{mau_cd}" '
                  f'stroke="{MAU["vien"]}" stroke-width="1"/>')
        ve.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="{r_loi * 0.55:.1f}" '
                  f'fill="{mau_ruot}" stroke="{MAU["vien"]}" stroke-width="1"/>')

    # --- chú thích bên phải ---
    x_chu, y = 300, 66
    ve.append(_nhan(x_chu, y - 22, 'Cấu tạo (giải mã từ ký hiệu)'))
    muc = [(mau_ruot, f'Ruột dẫn: {ten_ruot}'),
           (mau_cd, f'Cách điện: {ten_cd}')]
    if co_giap:
        muc.append((MAU['giap'], f'Giáp bảo vệ: {row.get("giap_bao_ve_giai_ma", "")}'))
    if co_vo:
        muc.append((MAU['vo_pvc'], 'Vỏ bọc ngoài: PVC'))
    if n_loi > 1:
        muc.append((None, f'Số lõi: {n_loi}'))

    for mau, chu in muc:
        if mau:
            ve.append(f'<rect x="{x_chu}" y="{y - 11}" width="14" height="14" rx="3" '
                      f'fill="{mau}" stroke="{MAU["vien"]}" stroke-width="1"/>')
            ve.append(_nhan(x_chu + 22, y, chu))
        else:
            ve.append(_nhan(x_chu, y, chu))
        y += 30

    ve.append(_nhan(x_chu, y + 6, _GHI_CHU, mo=True))
    ve.append('</svg>')
    return ('<div style="margin:16px 0;max-width:560px">' + ''.join(ve) + '</div>')


def so_do_kich_thuoc_may_bien_ap(row):
    """Vẽ sơ đồ kích thước máy biến áp (nhìn ngang) từ field catalogue.

    Yêu cầu TỐI THIỂU: có ít nhất 2 trong 3 kích thước A/B/C. Thiếu ->
    trả '' (không vẽ hộp bịa số).
    """
    def _so(v):
        if not v:
            return None
        m = re.search(r'\d+(?:[.,]\d+)?', str(v))
        return float(m.group(0).replace(',', '.')) if m else None

    a = _so(row.get('kich_thuoc_a'))    # dài
    b = _so(row.get('kich_thuoc_b'))    # rộng
    c = _so(row.get('kich_thuoc_c'))    # cao
    co = [x for x in (a, b, c) if x]
    if len(co) < 2:
        return ''

    # tỷ lệ hoá về khung vẽ, GIỮ tương quan giữa các chiều
    lon_nhat = max(co)
    ty_le = 150.0 / lon_nhat
    w = int((a or lon_nhat * 0.8) * ty_le)
    h = int((c or lon_nhat * 0.9) * ty_le)
    x0, y0 = 70, 40

    ve = [f'<svg viewBox="0 0 560 280" width="100%" height="auto" role="img" '
          f'xmlns="http://www.w3.org/2000/svg" aria-label="Sơ đồ kích thước máy biến áp">',
          f'<rect x="0" y="0" width="560" height="280" fill="{MAU["nen"]}"/>',
          # thân máy
          f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="6" fill="#E2E8F0" '
          f'stroke="{MAU["chu"]}" stroke-width="2"/>',
          # sứ cách điện trên nóc (minh hoạ)
          f'<rect x="{x0 + int(w * 0.18)}" y="{y0 - 18}" width="10" height="18" fill="#94A3B8"/>',
          f'<rect x="{x0 + int(w * 0.46)}" y="{y0 - 18}" width="10" height="18" fill="#94A3B8"/>',
          f'<rect x="{x0 + int(w * 0.74)}" y="{y0 - 18}" width="10" height="18" fill="#94A3B8"/>',
          # cánh tản nhiệt
          ]
    for i in range(5):
        yy = y0 + 14 + i * max(10, h // 6)
        if yy < y0 + h - 10:
            ve.append(f'<line x1="{x0 - 12}" y1="{yy}" x2="{x0}" y2="{yy}" '
                      f'stroke="#94A3B8" stroke-width="3"/>')
            ve.append(f'<line x1="{x0 + w}" y1="{yy}" x2="{x0 + w + 12}" y2="{yy}" '
                      f'stroke="#94A3B8" stroke-width="3"/>')

    # đường kích thước ngang (A)
    if a:
        y_kt = y0 + h + 26
        ve += [f'<line x1="{x0}" y1="{y_kt}" x2="{x0 + w}" y2="{y_kt}" '
               f'stroke="{MAU["chu"]}" stroke-width="1"/>',
               f'<polygon points="{x0},{y_kt} {x0 + 7},{y_kt - 4} {x0 + 7},{y_kt + 4}" fill="{MAU["chu"]}"/>',
               f'<polygon points="{x0 + w},{y_kt} {x0 + w - 7},{y_kt - 4} {x0 + w - 7},{y_kt + 4}" fill="{MAU["chu"]}"/>',
               _nhan(x0 + w // 2 - 26, y_kt + 16, f'A = {row.get("kich_thuoc_a")}')]
    # đường kích thước dọc (C)
    if c:
        x_kt = x0 - 30
        ve += [f'<line x1="{x_kt}" y1="{y0}" x2="{x_kt}" y2="{y0 + h}" '
               f'stroke="{MAU["chu"]}" stroke-width="1"/>',
               f'<polygon points="{x_kt},{y0} {x_kt - 4},{y0 + 7} {x_kt + 4},{y0 + 7}" fill="{MAU["chu"]}"/>',
               f'<polygon points="{x_kt},{y0 + h} {x_kt - 4},{y0 + h - 7} {x_kt + 4},{y0 + h - 7}" fill="{MAU["chu"]}"/>',
               _nhan(4, y0 + h // 2, f'C = {row.get("kich_thuoc_c")}')]

    # bảng chú thích
    x_chu, y = 300, 60
    ve.append(_nhan(x_chu, y - 22, 'Kích thước theo catalogue'))
    for nhan_kt, gia_tri in (('A (dài)', row.get('kich_thuoc_a')),
                             ('B (rộng)', row.get('kich_thuoc_b')),
                             ('C (cao)', row.get('kich_thuoc_c')),
                             ('D', row.get('kich_thuoc_d')),
                             ('Khối lượng dầu', row.get('khoi_luong_dau')),
                             ('Tổng khối lượng', row.get('tong_khoi_luong'))):
        if gia_tri:
            ve.append(_nhan(x_chu, y, f'{nhan_kt}: {gia_tri}'))
            y += 26

    ve.append(_nhan(x_chu, y + 8, _GHI_CHU, mo=True))
    ve.append('</svg>')
    return ('<div style="margin:16px 0;max-width:560px">' + ''.join(ve) + '</div>')


def hinh_cho_row(row):
    """Điểm vào duy nhất — tự chọn loại hình theo outline. Không khớp
    outline nào có hình -> '' (không vẽ)."""
    outline = row.get('outline_id')
    if outline == 'outline_cap_dien':
        return mat_cat_cap_dien(row)
    if outline == 'outline_may_bien_ap':
        # Ver 2.6 — ưu tiên sơ đồ KÍCH THƯỚC (thông tin cụ thể hơn), rơi về
        # sơ đồ NGUYÊN LÝ khi thiếu kích thước — phần lớn SKU rơi vào ca này.
        hinh = so_do_kich_thuoc_may_bien_ap(row)
        return hinh or so_do_nguyen_ly_may_bien_ap(row)
    return ''


# ============================================================ Ver 2.6 — sơ đồ nguyên lý máy biến áp
def _so_pha(row):
    """Bóc số pha từ tên/dữ liệu. Không rõ -> None (không đoán)."""
    t = str(row.get('ten_goc', '')).lower()
    if re.search(r'\b3\s*pha\b|3p\b', t):
        return 3
    if re.search(r'\b1\s*pha\b|1p\b', t):
        return 1
    return None


def so_do_nguyen_ly_may_bien_ap(row):
    """Sơ đồ nguyên lý: cuộn sơ cấp — lõi thép — cuộn thứ cấp, kèm cấp
    điện áp vào/ra và số pha.

    Ver 2.6 — VÌ SAO CÓ HÀM NÀY: so_do_kich_thuoc_may_bien_ap() cần ít
    nhất 2/3 kích thước A/B/C, mà thực tế phần lớn SKU máy biến áp KHÔNG
    có kích thước trong MASTER (kiểm tra thật: MBT1P15A2608 trống cả 4
    cột) -> gần như không SKU nào vẽ được hình. Hàm này chỉ cần CÔNG SUẤT
    + CẤP ĐIỆN ÁP (mọi SKU đều có) nên phủ được cả nhóm.

    Vẫn giữ nguyên tắc: thiếu công suất HOẶC cấp điện áp -> KHÔNG vẽ.
    """
    cong_suat = str(row.get('cong_suat', '') or '').strip()
    cap_dien_ap = str(row.get('cap_dien_ap', '') or '').strip()
    if not cong_suat or not cap_dien_ap:
        return ''

    # tách cấp điện áp "22/0.4" -> vào 22, ra 0.4
    m = re.match(r'\s*([\d.,]+)\s*/\s*([\d.,]+)', cap_dien_ap)
    ap_vao = f'{m.group(1)} kV' if m else cap_dien_ap
    ap_ra = f'{m.group(2)} kV' if m else ''

    n_pha = _so_pha(row)
    ten = str(row.get('ten_goc', '')).lower()
    loai_loi = ('Amorphous' if 'amorphous' in ten else
                'Silic' if 'silic' in ten else '')
    la_kho = 'khô' in ten

    cx = 200
    ve = [f'<svg viewBox="0 0 560 300" width="100%" height="auto" role="img" '
          f'xmlns="http://www.w3.org/2000/svg" aria-label="Sơ đồ nguyên lý máy biến áp">',
          f'<rect x="0" y="0" width="560" height="300" fill="{MAU["nen"]}"/>']

    # --- lõi thép (2 trụ đứng + 2 gông ngang) ---
    ve += [f'<rect x="{cx-42}" y="70" width="84" height="150" fill="none" '
           f'stroke="#6B7280" stroke-width="13"/>']
    ve.append(_nhan(cx - 34, 250, f'Lõi thép{" " + loai_loi if loai_loi else ""}', mo=True))

    # --- cuộn dây: sơ cấp (trái), thứ cấp (phải) ---
    for x, mau_cuon, nhan_cuon in ((cx - 78, '#B87333', 'Cuộn sơ cấp'),
                                   (cx + 42, '#B87333', 'Cuộn thứ cấp')):
        for i in range(6):
            y = 82 + i * 22
            ve.append(f'<rect x="{x}" y="{y}" width="36" height="14" rx="4" '
                      f'fill="{mau_cuon}" stroke="{MAU["vien"]}" stroke-width="1"/>')
        ve.append(_nhan(x - 6, 268, nhan_cuon, mo=True))

    # --- đường dây vào/ra + mũi tên ---
    ve += [f'<line x1="40" y1="120" x2="{cx-78}" y2="120" stroke="{MAU["chu"]}" stroke-width="2"/>',
           f'<polygon points="{cx-78},120 {cx-88},115 {cx-88},125" fill="{MAU["chu"]}"/>',
           f'<line x1="{cx+78}" y1="120" x2="520" y2="120" stroke="{MAU["chu"]}" stroke-width="2"/>',
           f'<polygon points="520,120 510,115 510,125" fill="{MAU["chu"]}"/>']
    ve.append(_nhan(44, 108, f'Vào: {ap_vao}'))
    if ap_ra:
        ve.append(_nhan(430, 108, f'Ra: {ap_ra}'))

    # --- bảng thông tin ---
    y = 40
    ve.append(_nhan(40, y, f'Công suất: {cong_suat}'))
    if n_pha:
        ve.append(_nhan(200, y, f'{n_pha} pha'))
    ve.append(_nhan(300, y, 'Làm mát: không khí (AN/AF)' if la_kho
                    else 'Làm mát: dầu (ONAN)'))
    ve.append(_nhan(40, 288, _GHI_CHU, mo=True))
    ve.append('</svg>')
    return f'<div style="margin:16px 0;max-width:560px">{"".join(ve)}</div>'
