# -*- coding: utf-8 -*-
"""Ver 4.6 — khối "chịu tải bao nhiêu" + giá trị suy ra, cho outline_cap_dien.

VÌ SAO CÓ KHỐI NÀY
  GSC 8 site: 41 truy vấn "chịu tải bao nhiêu", 1.681 impression, vị trí TB
  3,1 nhưng CTR chỉ 2,97% (vị trí 3 bình thường ~10%). `dây nhôm 16mm chịu
  tải bao nhiêu`: 69 impression, vị trí 3,32, 0 CLICK. Đã xếp hạng rồi, trang
  không trả lời được câu hỏi nên không ai bấm.

  Dữ liệu để trả lời đã nằm sẵn trong MASTER từ đợt bóc catalogue CADIVI hạ
  thế (1.217 SKU có dòng định mức, 1.646 có điện trở DC) nhưng cot_bang của
  cap_dien có 12 dòng mà KHÔNG dòng nào là thông số điện -> dữ liệu nằm chết.

NGUYÊN TẮC
  1. Không có số thì KHÔNG hiện khối. Không đoán, không nội suy.
  2. Dòng tải luôn đi kèm ĐIỀU KIỆN QUY CHIẾU. Dòng tải trần là sai kỹ thuật.
  3. Giá trị suy ra phải ghi rõ công thức và nguồn (IEE 522-8, catalogue tr.8).
  4. Cột "Dòng điện SUY LUẬN" (CXV 4 lõi) KHÔNG dùng ở đây — nó không phải
     số in trong catalogue.
"""
import re


# ---------- đọc số an toàn ----------
def _so(v):
    if v is None:
        return None
    t = str(v).strip().replace(',', '.')
    if t.lower() in ('', 'nan', 'none', '-'):
        return None
    m = re.search(r'\d+(?:\.\d+)?', t)
    return float(m.group(0)) if m else None


def _chu(v):
    t = str(v or '').strip()
    return '' if t.lower() in ('nan', 'none', '-') else t


def _sogon(x):
    """1234.0 -> '1.234' ; 0.193 -> '0,193' (kiểu VN)."""
    if x is None:
        return ''
    if x == int(x):
        return f'{int(x):,}'.replace(',', '.')
    return f'{x:g}'.replace('.', ',')


# ---------- B. giá trị suy ra ----------
def chieu_dai_toi_da(sut_ap_mv_a_m, dong_tai_a, so_pha=3):
    """Chiều dài tuyến tối đa để sụt áp không vượt ngưỡng cho phép.

    Catalogue CADIVI hạ thế trang 8, dẫn IEE 522-8: sụt áp toàn tuyến không
    quá 2,5% điện áp danh nghĩa ->
        mạch 1 pha 220 V  : cho phép 5,5 V
        mạch 3 pha 380 V  : cho phép 9,5 V
    Độ sụt áp tra bảng có đơn vị mV/A/m nên:
        L(m) = V_cho_phep(V) * 1000 / (ΔV(mV/A/m) * I(A))
    """
    if not sut_ap_mv_a_m or not dong_tai_a:
        return None
    cho_phep = 9.5 if so_pha == 3 else 5.5
    return cho_phep * 1000.0 / (sut_ap_mv_a_m * dong_tai_a)


def ton_hao_100m(r_dc_ohm_km, dong_tai_a, so_pha=3):
    """Tổn hao công suất trên 100 m ở dòng tải cho trước.

    P = k · I² · R ; k = 3 cho mạch 3 pha, 2 cho mạch 1 pha (đi và về).
    R của 100 m = R_dc(Ω/km) / 10. Dùng R_dc ở 20 °C nên đây là cận DƯỚI —
    vận hành nóng thì điện trở tăng, tổn hao thực cao hơn. Có ghi chú trong
    bài, không được nói đây là con số vận hành.
    """
    if not r_dc_ohm_km or not dong_tai_a:
        return None
    k = 3 if so_pha == 3 else 2
    return k * (dong_tai_a ** 2) * (r_dc_ohm_km / 10.0)


# ---------- A. khối HTML ----------
def khoi_chiu_tai(row, _st, _esc):
    """Khối trả lời trực tiếp truy vấn "… chịu tải bao nhiêu"."""
    if row.get('outline_id') != 'outline_cap_dien':
        return ''

    I = _so(row.get('dong_dien_dinh_muc_catalogue'))
    if not I:
        return ''                       # không có số -> không hiện khối

    ten = _chu(row.get('ten_goc'))
    kieu = _chu(row.get('kieu_lap_dat_catalogue'))
    dk = _chu(row.get('dieu_kien_quy_chieu_catalogue'))
    dv = _so(row.get('do_sut_ap_catalogue'))
    rdc = _so(row.get('dien_tro_dc_catalogue'))

    so_pha = 3
    if re.search(r'\b1\s*pha|\b2\s*l[õo]i\b', ten.lower()):
        so_pha = 1

    h = [f'<h2>{_esc(ten)} chịu tải bao nhiêu?</h2>']
    h.append(f'<p><strong>Dòng điện định mức: {_sogon(I)} A</strong>'
             + (f' — {_esc(kieu)}.' if kieu else '.') + '</p>')

    # bảng số liệu — mỗi dòng chỉ hiện khi CÓ số
    dong = [('Dòng điện định mức', f'{_sogon(I)} A')]
    if dv:
        dong.append(('Độ sụt áp', f'{_sogon(dv)} mV/A/m'))
    if rdc:
        dong.append(('Điện trở DC tối đa ở 20 °C', f'{_sogon(rdc)} Ω/km'))
    dk_ruot = _so(row.get('duong_kinh_ruot_dan_catalogue'))
    if dk_ruot:
        dong.append(('Đường kính ruột dẫn', f'{_sogon(dk_ruot)} mm'))
    h.append('<table><tbody>' + ''.join(
        f'<tr><th>{_esc(a)}</th><td>{_esc(b)}</td></tr>' for a, b in dong)
        + '</tbody></table>')

    # --- giá trị suy ra: mỗi SKU ra câu KHÁC NHAU ---
    suy = []
    if dv:
        L = chieu_dai_toi_da(dv, I, so_pha)
        if L:
            u = '380 V ba pha' if so_pha == 3 else '220 V một pha'
            suy.append(
                f'Chạy ở đúng dòng định mức {_sogon(I)} A trên lưới {u}, tuyến '
                f'cáp dài tối đa khoảng <strong>{_sogon(round(L))} m</strong> thì '
                f'sụt áp chạm ngưỡng cho phép 2,5% điện áp danh nghĩa.')
            L2 = chieu_dai_toi_da(dv, I * 0.8, so_pha)
            if L2:
                suy.append(
                    f'Chạy non tải ở mức 80% ({_sogon(round(I * 0.8))} A), chiều '
                    f'dài tối đa nới lên khoảng <strong>{_sogon(round(L2))} m</strong>.')
    if rdc:
        P = ton_hao_100m(rdc, I, so_pha)
        if P:
            suy.append(
                f'Ở dòng định mức, tổn hao công suất trên mỗi 100 m tuyến vào '
                f'khoảng <strong>{_sogon(round(P))} W</strong> (tính theo điện trở '
                f'một chiều ở 20 °C — vận hành nóng thì điện trở tăng nên tổn hao '
                f'thực tế cao hơn).')
    if suy:
        h.append('<h3>Suy ra từ thông số trên</h3><ul>'
                 + ''.join(f'<li>{s}</li>' for s in suy) + '</ul>')

    # --- điều kiện quy chiếu: BẮT BUỘC ---
    if dk:
        h.append(f'<p><em>Điều kiện quy chiếu của dòng định mức: {_esc(dk)}. '
                 f'Lắp đặt khác điều kiện này (nhiệt độ môi trường cao hơn, nhiều '
                 f'sợi đi chung, chôn sâu khác) phải chiết giảm theo hệ số tương '
                 f'ứng.</em></p>')
    else:
        h.append('<p><em>Dòng định mức tra theo catalogue nhà sản xuất. Điều kiện '
                 'lắp đặt thực tế khác điều kiện quy chiếu thì phải chiết giảm.</em></p>')

    nguon = _chu(row.get('nguon_du_lieu_catalogue'))
    if nguon:
        h.append(f'<p><small>Nguồn số liệu: {_esc(nguon)}.</small></p>')

    return f'<div {_st("khoi_chung")}>' + ''.join(h) + '</div>'
