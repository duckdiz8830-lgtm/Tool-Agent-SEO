# -*- coding: utf-8 -*-
"""
SONEALEO ULTRA 3.3 — KHỐI ẢNH & BIỂU ĐỒ (bố cục A+).

HAI VIỆC:
  1. CHỖ CHỜ ẢNH — chèn sẵn 4 khối vào bài, mỗi khối ghi rõ đặt ảnh gì,
     chọn thế nào, tỷ lệ bao nhiêu; kèm HTML comment hướng dẫn thay thế.
     Thịnh mở bài trong WordPress là thấy, thay tay từng tấm.
     Lỡ quên tấm nào thì khối vẫn đọc được như một ô trung thực, KHÔNG
     phải ảnh vỡ.
  2. BIỂU ĐỒ sinh từ SỐ THẬT (tra_cuu_thibidi) — cột tổn hao không tải
     theo mức công suất, và thanh so Silic/Amorphous. Không AI, 0 quota,
     mỗi SKU một biểu đồ khác nhau.

KỶ LUẬT: mọi con số trên biểu đồ đến từ bảng tra catalogue. Không tra
được -> KHÔNG vẽ (trả ''), không nội suy, không ước lượng.
"""
import html

# ---------------------------------------------------------------- chỗ chờ ảnh
# Ver 4.4.1.5 — ĐÃ XOÁ dict O_ANH (5 ô: hero/bien_may/can_canh/lap_dat/
# giao_hang) chứa toàn văn hướng dẫn chụp ảnh nội bộ: "chụp thẳng tấm nhãn
# kim loại", "tỷ lệ 3:2 tối thiểu 1200x800px", "ảnh này chứng minh thông số
# phía trên là số thật, không phải chép catalogue".
#
# Từ Ver 4.4 cho_anh() đã trả '' nên dict thành code chết, KHÔNG còn chỗ
# nào đọc tới. Xoá hẳn vì để lại thì lần sau ai (hoặc AI nào) sửa file này
# rất dễ nối lại — chuỗi vẫn nằm sờ sờ đó, chỉ thiếu 1 dòng return.
# Bài cũ đã dính rác thì dọn bằng sweep_rac.don_rac_bai().

def cho_anh(ma):
    """Ver 4.4 A1/A2 — ô ảnh trống KHÔNG được xuất ra HTML production.

    Ảnh thật được pipeline workspace/xu_ly_anh chèn riêng. Placeholder cũ có
    div.snl-cho-anh + comment URL_ANH từng vỡ qua wpautop và lộ hướng dẫn cho
    khách, nên hành vi mặc định bây giờ là không in bất kỳ dấu vết nào.
    Mã lạ hay mã hợp lệ đều trả rỗng khi chưa có ảnh thật.
    """
    return ''


# ---------------------------------------------------------------- biểu đồ
def _dac_trung(row):
    try:
        import kien_thuc_bien_thien as K
        return K.dac_trung(row)
    except Exception:
        return None


def _po_master(row):
    """Po thật đã import trong record; không có thì None."""
    try:
        import kien_thuc_bien_thien as K
        return K._po_cua_record(row)
    except Exception:
        return None


def _nhom_bieu_do_master(row, anh_em):
    """Các mức cùng dòng từ dữ liệu MASTER đã import, không mở XLSX lúc render.

    Cùng hãng / dầu-khô / số pha / lõi / cấp áp / biến thể tiêu chuẩn.
    Điều kiện chặt để không trộn số Po của QĐ 107 và QĐ 2608 vào một đồ thị.
    """
    if not anh_em:
        return {}
    d0 = _dac_trung(row) or {}
    ten0 = str(row.get('ten_goc') or '')
    def bien_the(ten):
        t = str(ten or '').lower().replace(' ', '')
        if 'a2608' in t or 'qđ2608' in t or 'qd2608' in t:
            return '2608'
        if 'a107' in t or 'qđ107' in t or 'qd107' in t:
            return '107'
        return ''
    bt0 = bien_the(ten0)
    hang0 = str(row.get('thuong_hieu') or '').strip().lower()
    cap0 = str(row.get('cap_dien_ap') or '').strip().lower().replace(' ', '')
    out = {}
    for r in anh_em:
        d = _dac_trung(r) or {}
        if str(r.get('thuong_hieu') or '').strip().lower() != hang0:
            continue
        if d.get('loai') != d0.get('loai') or d.get('pha') != d0.get('pha'):
            continue
        if d0.get('loai') == 'dau' and d.get('loi') != d0.get('loi'):
            continue
        if str(r.get('cap_dien_ap') or '').strip().lower().replace(' ', '') != cap0:
            continue
        if bien_the(r.get('ten_goc')) != bt0:
            continue
        kva, po = d.get('kva'), _po_master(r)
        if kva is None or not po:
            continue
        # Nếu cùng kVA có hai số khác nhau thì không tự chọn đại một số.
        if kva in out and out[kva] != po:
            out[kva] = None
        else:
            out[kva] = po
    return {k: v for k, v in out.items() if v}


def _nguon_bieu_do_master(row):
    nguon = str(row.get('nguon_tieu_chuan_vien_dan') or '').strip()
    return nguon or 'MASTER — dữ liệu đã import và đối chiếu theo record'


def bieu_do_ton_hao(row, anh_em=None):
    """Cột Po các mức lân cận. Ưu tiên dữ liệu MASTER đã import;
    bảng THIBIDI cũ chỉ là fallback tương thích khi caller không có anh_em.
    """
    d = _dac_trung(row)
    if not d or d.get('kva') is None:
        return ''

    bang_master = _nhom_bieu_do_master(row, anh_em)
    if bang_master and float(d['kva']) in bang_master:
        bang = bang_master
        lay = lambda b: b
        nguon = _nguon_bieu_do_master(row)
    else:
        try:
            import tra_cuu_thibidi as TC
        except Exception:
            return ''
        if not TC.tra(d['kva'], d['pha'], d['loai'], d['hang']):
            return ''
        if d['loai'] == 'kho':
            bang, lay = TC.KHO_3PHA, (lambda b: b[0])
        elif d['pha'] == 1:
            bang, lay = TC.DAU_1PHA, (lambda b: b[1] if d['loi'] == 'amorphous' else b[0])
        else:
            bang, lay = TC.DAU_3PHA, (lambda b: b[1] if d['loi'] == 'amorphous' else b[0])
        nguon = TC.NGUON

    muc = sorted(bang)
    kva = float(d['kva'])
    if kva not in muc:
        return ''
    i = muc.index(kva)
    hien = muc[max(0, i - 3): i + 4]
    if len(hien) < 2:
        return ''
    vals = [lay(bang[k]) for k in hien]
    if not all(vals):
        return ''
    vmax = max(vals)
    W, HH, L, B = 620, 250, 44, 44
    gap = (W - L - 16) / len(hien)
    bw = gap * 0.6
    cot = []
    for n, k in enumerate(hien):
        v = lay(bang[k])
        h = (HH - B - 30) * v / vmax
        x = L + n * gap + (gap - bw) / 2
        y = HH - B - h
        cur = (k == kva)
        cot.append(
            f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw:.0f}" height="{h:.0f}" '
            f'fill="{"#d0342c" if cur else "#c3cdd8"}"/>'
            f'<text x="{x + bw / 2:.0f}" y="{y - 6:.0f}" text-anchor="middle" font-size="11.5" '
            f'font-weight="{"700" if cur else "400"}" '
            f'fill="{"#d0342c" if cur else "#5a6675"}">{v:g}</text>'
            f'<text x="{x + bw / 2:.0f}" y="{HH - B + 16:.0f}" text-anchor="middle" '
            f'font-size="11.5" font-weight="{"700" if cur else "400"}" '
            f'fill="{"#0f3d5c" if cur else "#5a6675"}">{k:g}</text>')
    return (
        f'<div class="snl-tech-card"><svg viewBox="0 0 {W} {HH}" width="100%" height="auto" '
        f'role="img" xmlns="http://www.w3.org/2000/svg" '
        f'aria-label="Tổn hao không tải theo mức công suất"><title>Tổn hao không tải theo '
        f'mức công suất</title>'
        f'<text x="6" y="20" font-size="12" font-weight="700" fill="#0f3d5c">'
        f'Tổn hao không tải (W)</text>'
        f'<line x1="{L}" y1="{HH - B}" x2="{W - 12}" y2="{HH - B}" stroke="#dde3ea"/>'
        + ''.join(cot) +
        f'<text x="{L}" y="{HH - 8}" font-size="11" fill="#5a6675">Công suất định mức (kVA)</text>'
        f'</svg><p class="snl-tech-note">Nguồn: {html.escape(str(nguon))} — giá trị từ dữ liệu nguồn, '
        f'không phải kết quả đo của từng máy.</p></div>')

def bieu_do_loi(row, anh_em=None):
    """Thanh so Po Silic/Amorphous ở đúng kVA. Ưu tiên record MASTER đã
    import; nếu có nhiều số đối nghịch khác nhau thì bỏ, không tự chọn.
    """
    d = _dac_trung(row)
    if not d or d.get('loai') != 'dau' or d.get('kva') is None:
        return ''

    s = a = None
    nguon = None
    po_minh = _po_master(row)
    if anh_em and po_minh and d.get('loi') in ('silic', 'amorphous'):
        hang0 = str(row.get('thuong_hieu') or '').strip().lower()
        cap0 = str(row.get('cap_dien_ap') or '').strip().lower().replace(' ', '')
        doi = []
        for r in anh_em:
            dr = _dac_trung(r) or {}
            if dr.get('loai') != 'dau' or dr.get('pha') != d.get('pha'):
                continue
            if dr.get('kva') != d.get('kva') or dr.get('loi') == d.get('loi'):
                continue
            if str(r.get('thuong_hieu') or '').strip().lower() != hang0:
                continue
            if str(r.get('cap_dien_ap') or '').strip().lower().replace(' ', '') != cap0:
                continue
            po = _po_master(r)
            if po:
                doi.append(po)
        doi = sorted(set(doi))
        if len(doi) == 1:
            if d['loi'] == 'silic':
                s, a = po_minh, doi[0]
            else:
                s, a = doi[0], po_minh
            nguon = _nguon_bieu_do_master(row)

    # Fallback cũ cho THIBIDI nếu dataset không đủ cặp.
    if not (s and a):
        try:
            import tra_cuu_thibidi as TC
        except Exception:
            return ''
        b = TC.tra(d['kva'], d['pha'], d['loai'], d['hang'])
        if not b or b['loai'] != 'dau':
            return ''
        s, a = b['po_silic'], b['po_amorphous']
        nguon = TC.NGUON
    if not (s and a and s > a):
        return ''

    W, HH = 620, 186
    xw = W - 160
    wa = xw * a / s
    kwh = f'{round((s - a) * 8760 / 1000):,}'.replace(',', '.')
    return (
        f'<div class="snl-tech-card"><svg viewBox="0 0 {W} {HH}" width="100%" height="auto" '
        f'role="img" xmlns="http://www.w3.org/2000/svg" aria-label="So sánh tổn hao lõi Silic '
        f'và Amorphous"><title>So sánh tổn hao lõi Silic và Amorphous</title>'
        f'<text x="6" y="19" font-size="12" font-weight="700" fill="#0f3d5c">'
        f'Tổn hao không tải tối đa ở {d["kva"]:g} kVA (W)</text>'
        f'<text x="6" y="56" font-size="12.5" fill="#1a2430">Lõi Silic</text>'
        f'<rect x="106" y="40" width="{xw:.0f}" height="26" fill="#c3cdd8"/>'
        f'<text x="{112 + xw:.0f}" y="58" font-size="13" font-weight="700" fill="#5a6675">{s:g} W</text>'
        f'<text x="6" y="102" font-size="12.5" fill="#1a2430">Lõi Amorphous</text>'
        f'<rect x="106" y="86" width="{wa:.0f}" height="26" fill="#d0342c"/>'
        f'<text x="{112 + wa:.0f}" y="104" font-size="13" font-weight="700" fill="#d0342c">{a:g} W</text>'
        f'<line x1="106" y1="128" x2="{W - 16}" y2="128" stroke="#dde3ea"/>'
        f'<text x="106" y="152" font-size="12" fill="#5a6675">Chênh lệch {s - a:g} W — tương đương '
        f'khoảng {kwh} kWh mỗi năm nếu vận hành liên tục</text>'
        f'<text x="106" y="172" font-size="11" fill="#8a93a5">({s - a:g} W × 8.760 h ÷ 1.000)</text>'
        f'</svg><p class="snl-tech-note">Nguồn: {html.escape(str(nguon))}</p></div>')

