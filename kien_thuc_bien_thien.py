# -*- coding: utf-8 -*-
"""
SONEALEO ULTRA 3.2 — TẦNG 3: KIẾN THỨC NGÀNH BIẾN THIÊN THEO DỮ LIỆU.

VÌ SAO CÓ FILE NÀY
Khối kiến thức cũ (`khoi_chung_may_bien_ap` v.v.) viết CHẾT một đoạn văn
cho mọi SKU cùng loại -> Google coi là boilerplate -> Ver 4.9.9 phải cắt
còn 1 câu -> bài mỏng. Nguyên nhân bài mỏng KHÔNG phải Hard Block (nó chỉ
soi con số, không đụng văn xuôi), mà là kiến thức ngành bị cắt vì trùng lặp.

CÁCH GIẢI
Kiến thức không viết chết, mà SINH RA TỪ DỮ LIỆU của chính SKU: số pha,
dải công suất, dầu/khô, loại lõi, Po/Pk/Uk thật. Hai SKU khác dữ liệu ->
khác chữ, khác số, khác cả góc nhìn. Cùng một khuôn nhưng không trùng.

KỶ LUẬT SỐ LIỆU (quan trọng)
Khối này do CODE dựng nên KHÔNG đi qua Hard Block (`kiem_tra_bia` chỉ
chạy trên văn AI). Vì vậy trách nhiệm nằm ở đây:
  - Mọi con số phải đến từ record, hoặc từ tra_cuu_thibidi (có nguồn in
    kèm), hoặc là PHÉP TÍNH từ hai loại trên (ghi rõ công thức).
  - Thiếu dữ liệu -> KHÔNG viết khối đó, trả ''. Không đoán, không văn vẻ
    chung chung để lấp chỗ.
  - Số tra từ catalogue LUÔN in kèm nguồn + chữ "tối đa theo catalogue"
    để không bị hiểu là số đo của chính máy đó.

TỐN 0 TOKEN GEMINI — toàn bộ do code sinh.
"""
import re
import html
import hashlib as _hashlib
import unicodedata

import tra_cuu_thibidi as TC
from chuan_hoa import bo_dau as _bo_dau   # Ver 5.7 — gom 9 bản _bo_dau về 1 nguồn (xem chuan_hoa.py)

GIO_NAM = 8760          # giờ/năm, dùng cho phép tính điện năng tổn hao


def _st(khoa):
    """Mượn bảng style của render_phase2 để khối mới trông đồng bộ."""
    try:
        import render_phase2 as R
        return R._st(khoa)
    except Exception:
        return ''


def _so(v):
    m = re.search(r'\d+(?:[.,]\d+)?', str(v or ''))
    return float(m.group(0).replace(',', '.')) if m else None


def _p(noi_dung, style='khoi_chung'):
    return f'<p {_st(style)}>{noi_dung}</p>'


def _g(n):
    """Số đẹp kiểu Việt: 1234.0 -> '1.234'."""
    if n is None:
        return ''
    if float(n) == int(n):
        return f'{int(n):,}'.replace(',', '.')
    return f'{n:,.1f}'.replace(',', '@').replace('.', ',').replace('@', '.')


# ---------------------------------------------------------------- Ver 6.2: biến thể câu chữ
def _bien_the(row, n, muoi=''):
    """Chọn biến thể 0..n-1 ỔN ĐỊNH theo SKU.

    Vì sao không random: bài đã đăng render lại phải ra ĐÚNG chữ cũ. Random
    thì mỗi lần đăng lại đổi văn, WordPress ghi nhận sửa đổi liên tục, và
    không bao giờ đối chiếu được bài live với bài trong kho.

    `muoi` cho mỗi khối một chuỗi muối khác nhau -> hai khối trong CÙNG một
    bài không bị chọn trùng chỉ số, tránh cảnh cả bài rơi vào "biến thể 0".

    Đo trên 6 SKU dầu 3 pha 250-2000kVA: cùng SKU gọi 100 lần ra cùng chỉ số.
    """
    khoa = str(row.get('ma_goc') or row.get('sku') or row.get('ten_goc') or '') + '|' + muoi
    return int(_hashlib.md5(khoa.encode('utf-8')).hexdigest(), 16) % max(1, n)


# ---------------------------------------------------------------- đọc đặc trưng SKU
def dac_trung(row):
    """Bóc đặc trưng dùng chung cho mọi khối. Thiếu thì để None."""
    ten = row.get('ten_goc', '') or ''
    t = _bo_dau(ten)
    pha = 3 if re.search(r'\b3\s*pha\b|\b3p\b', t) else \
          1 if re.search(r'\b1\s*pha\b|\b1p\b', t) else None
    # Ver 3.2 — nhiều SKU (vd dòng KP) KHÔNG ghi số pha trong tên. Suy từ
    # CẤP ĐIỆN ÁP HẠ theo quy ước lưới phân phối VN: hạ áp 0,4kV là ba pha
    # (400V dây), 0,22-0,23kV là một pha. Đây là quy ước ngành, không phải
    # đoán mò — và chỉ dùng khi tên hàng không nói gì.
    ap = str(row.get('cap_dien_ap', '') or '') + ' ' + ten
    if pha is None:
        if re.search(r'/\s*0[.,]4\s*kv', _bo_dau(ap)):
            pha = 3
        elif re.search(r'/\s*0[.,]2[23]\s*kv', _bo_dau(ap)):
            pha = 1
    # Ver 6.1 — nới từ tối đa 1 chữ đệm lên 3. Tên thật có dạng "Máy biến áp
    # CẤP NGUỒN Dầu 1 pha..." (2 chữ đệm) nên regex cũ trượt. VẪN neo vào
    # "biến áp"/"MBA" — bỏ neo là "đầu cáp" (bỏ dấu -> "dau cap") bị nhận
    # nhầm thành máy dầu. Đo trên MASTER thật (174 dòng MBA): 139 -> 141
    # dòng nhận diện được, 0 dòng đổi kết quả so với regex cũ.
    m = re.search(r'(?:bien\s*ap|mba)\s+(?:\w+\s+){0,3}?(dau|kho)\b', t)
    loai = m.group(1) if m else None
    loi = 'amorphous' if 'amorphous' in t else 'silic' if 'silic' in t else None
    kva = _so(row.get('cong_suat')) or (
        float(re.search(r'(\d+(?:[.,]\d+)?)\s*kva', t).group(1).replace(',', '.'))
        if re.search(r'(\d+(?:[.,]\d+)?)\s*kva', t) else None)
    # vật liệu cuộn dây in trong tên: (Cu/Cu), (Al/Cu)...
    mvl = re.search(r'\((cu|al)\s*/\s*(cu|al)\)', t)
    vat_lieu = f'{mvl.group(1)}/{mvl.group(2)}' if mvl else None
    map_ap = re.search(r'(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)\s*kv', _bo_dau(ap))
    cap_ap = f'{map_ap.group(1)}/{map_ap.group(2)}kV'.replace(',', '.') if map_ap else None
    return {'kva': kva, 'pha': pha, 'loai': loai, 'loi': loi, 'vat_lieu': vat_lieu,
            'cap_ap': cap_ap, 'hang': row.get('thuong_hieu', '') or '', 'ten': ten}


def _dai(kva):
    """Phân dải công suất — quyết định ngữ cảnh sử dụng."""
    if kva is None:
        return None
    if kva < 50:
        return 'rat_nho'
    if kva < 250:
        return 'nho'
    if kva < 800:
        return 'vua'
    if kva < 2000:
        return 'lon'
    return 'rat_lon'


# ---------------------------------------------------------------- KHỐI 1: ứng dụng
_UNG_DUNG = {
    (1, 'rat_nho'): ('cấp điện cho một hộ hoặc cụm vài hộ dân ở khu vực nông thôn, '
                     'miền núi — nơi lưới hạ áp kéo dài và phụ tải phân tán',
                     'treo trực tiếp trên trụ điện, không cần nền móng'),
    (1, 'nho'): ('cấp điện cho cụm dân cư nhỏ, trạm bơm nông nghiệp, hoặc phụ tải '
                 'một pha tập trung ở cuối tuyến',
                 'treo trụ hoặc đặt trên bệ, tuỳ mặt bằng tuyến'),
    (3, 'rat_nho'): ('cấp điện cho phụ tải ba pha công suất thấp: trạm bơm, xưởng '
                     'cơ khí nhỏ, hệ thống chiếu sáng công cộng',
                     'thường treo trụ hoặc đặt trạm giàn'),
    (3, 'nho'): ('cấp điện cho khu dân cư, cửa hàng, nhà xưởng quy mô nhỏ và vừa, '
                 'trạm biến áp khu vực',
                 'lắp trạm giàn, trạm treo hoặc trạm nền tuỳ mặt bằng'),
    (3, 'vua'): ('cấp điện cho nhà xưởng sản xuất, toà nhà thương mại, khách sạn, '
                 'trung tâm dữ liệu quy mô vừa',
                 'lắp trạm nền hoặc trạm kios, cần bố trí hành lang an toàn'),
    (3, 'lon'): ('cấp điện cho nhà máy sản xuất, khu công nghiệp, phụ tải công '
                 'nghiệp liên tục',
                 'lắp trạm nền có móng bê tông, cần đường vào cho xe cẩu'),
    (3, 'rat_lon'): ('cấp điện cho nhà máy công suất lớn, dây chuyền sản xuất liên '
                     'tục, phụ tải nền của cả khu công nghiệp',
                     'lắp trạm nền kiên cố, phải tính trước phương án vận chuyển và cẩu lắp'),
}


def khoi_ung_dung(row):
    """Ứng dụng điển hình — biến thiên theo (số pha × dải công suất × dầu/khô)."""
    d = dac_trung(row)
    khoa = (d['pha'], _dai(d['kva']))
    if khoa not in _UNG_DUNG:
        return ''
    dung, lap = _UNG_DUNG[khoa]
    ap_txt = f" ở cấp điện áp {d['cap_ap']}" if d['cap_ap'] else ''
    # Ver 6.2 — 4 khung câu cho cùng cặp (ứng dụng, cách lắp).
    bt = _bien_the(row, 4, 'ung_dung')
    if bt == 0:
        cau = (f"Ở mức {_g(d['kva'])}kVA{ap_txt}, máy thường được dùng để {dung}. "
               f"Về lắp đặt, cấu hình này {lap}.")
    elif bt == 1:
        cau = (f"Phụ tải điển hình của bản {_g(d['kva'])}kVA{ap_txt} là {dung}. "
               f"Phương án lắp thường thấy: {lap}.")
    elif bt == 2:
        cau = (f"Cấu hình này {lap}, và ở dung lượng {_g(d['kva'])}kVA{ap_txt} thì công "
               f"năng chính là {dung}.")
    else:
        cau = (f"Với {_g(d['kva'])}kVA{ap_txt}, đây là mức máy hay gặp ở các công trình "
               f"cần {dung}. Khâu lắp đặt tương ứng: {lap}.")
    if d['loai'] == 'kho':
        cau += (' Vì là máy khô, không dùng dầu cách điện, máy đặt được trong nhà, '
                'tầng hầm hoặc gần khu vực có yêu cầu phòng cháy nghiêm ngặt — nơi '
                'máy dầu bị hạn chế.')
    elif d['loai'] == 'dau':
        cau += (' Vì là máy dầu, vị trí đặt cần tính tới hố thu dầu sự cố và khoảng '
                'cách an toàn phòng cháy theo quy định.')
    if d['vat_lieu']:
        ten_vl = {'cu/cu': 'đồng cả cuộn cao áp lẫn hạ áp',
                  'al/al': 'nhôm cả hai cuộn',
                  'al/cu': 'nhôm cuộn cao áp và đồng cuộn hạ áp',
                  'cu/al': 'đồng cuộn cao áp và nhôm cuộn hạ áp'}.get(d['vat_lieu'])
        if ten_vl:
            cau += (f' Cấu hình này dùng dây quấn {ten_vl}, thông tin cần lưu ý khi so '
                    f'sánh báo giá giữa các phương án.')
    return _p(html.escape(cau).replace('&lt;', '<').replace('&gt;', '>'))


def _so_kt(v):
    if v is None:
        return None
    m = re.search(r'\d+(?:[.,]\d+)?', str(v).replace(',', '.'))
    return float(m.group()) if m else None


def _po_cua_record(row):
    """Lấy Po (W) từ chính record: cột khai cứng hoặc cột động."""
    v = row.get('ton_hao_khong_tai')
    if v not in (None, '', '-'):
        n = _so_kt(v)
        if n:
            return n
    dong = row.get('thong_so_dong') or {}
    if isinstance(dong, dict):
        for k, gt in dong.items():
            if re.search(r'tổn hao không tải|\bpo\b', str(k), re.I):
                if re.match(r'^\s*[\d.,]+\s*$', str(gt)):
                    return _so_kt(gt)
    return None


def _po_anh_em_khac_loi(row, anh_em):
    """Po của SKU cùng hãng, cùng kVA, cùng cấp điện áp, KHÁC loại lõi.

    Ver 3.6.4 — trước đây khối này CHỈ tra tra_cuu_thibidi.py, một bảng
    viết cứng chỉ có dữ liệu THIBIDI. Máy MBT tra ra None nên 86 SKU MBT
    không bao giờ có biểu đồ so sánh lõi, trong khi MASTER Ver7 đã có đủ
    Po cho cả bản Silic lẫn bản Amorphous của MBT. Đây là nguồn hình sinh
    tự động, 0 lượt AI, không phải chụp tay.
    """
    if not anh_em:
        return None, None
    kva = _so_kt(row.get('cong_suat'))
    hang = str(row.get('thuong_hieu') or '').strip().lower()
    cap = str(row.get('cap_dien_ap') or '').strip()
    loi_minh = 'amorphous' if 'morphous' in str(row.get('ten_goc') or '').lower() else 'silic'
    for r in anh_em:
        ten = str(r.get('ten_goc') or '').lower()
        loi_no = 'amorphous' if 'morphous' in ten else 'silic'
        if loi_no == loi_minh:
            continue
        if str(r.get('thuong_hieu') or '').strip().lower() != hang:
            continue
        if _so_kt(r.get('cong_suat')) != kva:
            continue
        if str(r.get('cap_dien_ap') or '').strip() != cap:
            continue
        po = _po_cua_record(r)
        if po:
            return po, loi_no
    return None, None


# ---------------------------------------------------------------- KHỐI 2: so sánh lõi
def khoi_so_sanh_loi(row, anh_em=None):
    """So sánh lõi Silic vs Amorphous BẰNG SỐ THẬT tại đúng mức kVA này.

    Hai nguồn, thử theo thứ tự:
      1. Bảng tra catalogue THIBIDI (tra_cuu_thibidi.py) - có sẵn cả 2 lõi
      2. Ver 3.6.4: Po của SKU anh em khác lõi trong CHÍNH dataset - mở
         khối này cho MBT và mọi hãng khác có đủ cặp Silic/Amorphous

    Thiếu cả hai -> trả '' (không viết chay).
    """
    d = dac_trung(row)
    b = TC.tra(d['kva'], d['pha'], d['loai'], d['hang'])
    nguon_txt = 'catalogue THIBIDI'
    noi_suy = False
    if b and b['loai'] == 'dau' and b['po_silic'] and b['po_amorphous']:
        po_s, po_a = b['po_silic'], b['po_amorphous']
        noi_suy = b['noi_suy']
        kva_hien = b['kva']
    else:
        po_khac, loi_khac = _po_anh_em_khac_loi(row, anh_em)
        po_minh = _po_cua_record(row)
        if not (po_khac and po_minh):
            return ''
        po_s, po_a = ((po_khac, po_minh) if loi_khac == 'silic'
                      else (po_minh, po_khac))
        kva_hien = _so_kt(row.get('cong_suat'))
        nguon_txt = f'dữ liệu {row.get("thuong_hieu") or "hãng"}'
    if not (po_s and po_a and po_s > po_a):
        return ''
    giam_pct = round((po_s - po_a) / po_s * 100)
    kwh_nam = round((po_s - po_a) * GIO_NAM / 1000)
    delta = po_s - po_a
    loi_txt = ('Máy này dùng lõi Amorphous' if d['loi'] == 'amorphous' else
               'Máy này dùng lõi thép Silic' if d['loi'] == 'silic' else
               'Tuỳ chọn lõi')
    # Ver 6.2 — 4 CÁCH DIỄN ĐẠT cho cùng một bộ số. Con số y hệt nhau, chỉ
    # khác cấu trúc câu và thứ tự thông tin. Trước 6.2 khối này chỉ có 1 câu
    # mẫu -> hai SKU khác kVA ra văn giống nhau 95,4% (đo thật).
    kv = _g(kva_hien)
    bt = _bien_the(row, 4, 'so_sanh_loi')
    # Ver 6.2 — CÔNG THỨC PHẢI IN RA Ở MỌI BIẾN THỂ. Kỷ luật số liệu của
    # module (xem docstring đầu file): số nào là PHÉP TÍNH thì phải ghi rõ
    # công thức để người đọc kiểm lại được. Bản nháp 6.2 từng bỏ công thức ở
    # biến thể 2-3 cho gọn -> FAIL tests/test_v32_tang3.py mục 6. Đa dạng hoá
    # ở câu dẫn, KHÔNG ở phần công thức.
    ct = f"({_g(delta)}W x {_g(GIO_NAM)}h : 1.000)"
    if bt == 0:
        cau = (f"Cùng mức {kv}kVA, {nguon_txt} ghi tổn hao không tải tối đa của lõi thép "
               f"Silic là {_g(po_s)}W, còn lõi Amorphous là {_g(po_a)}W, thấp hơn khoảng "
               f"{giam_pct}%. Tổn hao không tải tồn tại suốt thời gian máy đóng điện, kể "
               f"cả khi không có tải, nên chênh lệch {_g(delta)}W tương đương khoảng "
               f"{_g(kwh_nam)} kWh mỗi năm nếu máy vận hành liên tục {ct}. {loi_txt}.")
    elif bt == 1:
        cau = (f"{loi_txt}. Đặt cạnh bản còn lại ở cùng {kv}kVA thì khoảng cách là "
               f"{_g(delta)}W không tải: {_g(po_s)}W cho lõi thép Silic, {_g(po_a)}W cho "
               f"lõi Amorphous, ít hơn chừng {giam_pct}%. Phần hao này không phụ thuộc "
               f"tải, máy đóng điện là nó chạy, nên dồn cả năm vào khoảng {_g(kwh_nam)} "
               f"kWh {ct}.")
    elif bt == 2:
        cau = (f"Về tổn hao không tải ở mức {kv}kVA, {nguon_txt} đưa ra hai con số cho "
               f"hai loại lõi: {_g(po_s)}W với thép Silic và {_g(po_a)}W với Amorphous — "
               f"chênh nhau {giam_pct}%. Đây là phần điện mất liên tục do từ hoá lõi, "
               f"không liên quan tới việc máy đang mang bao nhiêu tải, nên {_g(delta)}W "
               f"khác biệt quy ra chừng {_g(kwh_nam)} kWh sau một năm vận hành {ct}. "
               f"{loi_txt}.")
    else:
        cau = (f"Ở {kv}kVA, hai phương án lõi cho tổn hao không tải khác nhau {giam_pct}%: "
               f"thép Silic {_g(po_s)}W so với Amorphous {_g(po_a)}W (nguồn: {nguon_txt}). "
               f"Quy đổi mức chênh {_g(delta)}W sang điện năng, nếu máy đóng điện quanh năm "
               f"thì khoảng {_g(kwh_nam)} kWh {ct} — con số đáng cân nhắc khi so tổng chi "
               f"phí vòng đời chứ không chỉ giá mua ban đầu. {loi_txt}.")
    if noi_suy:
        cau += (' Lưu ý: catalogue ghi rõ số liệu Amorphous ở mức công suất này là '
                'giá trị nội suy tuyến tính theo TCCS 10:2021/EVN.')
    # Ver 3.6.4 — nguồn lấy theo nhánh đã dùng, không giả định luôn có `b`
    nguon_ghi = (b['nguon'] if b and b.get('nguon')
                 else 'MASTER — số quy chuẩn/catalogue đã đối chiếu')
    cau += f" (Nguồn: {nguon_ghi}.)"
    return _p(cau)


# ---------------------------------------------------------------- KHỐI 3: đọc hiểu thông số
def khoi_doc_hieu_thong_so(row):
    """Giải thích Po / Pk / Uk BẰNG CHÍNH SỐ CỦA MÁY NÀY (tra catalogue).

    Không có số -> không viết. Đây là khối cho kỹ sư đang cân nhắc mua."""
    d = dac_trung(row)
    b = TC.tra(d['kva'], d['pha'], d['loai'], d['hang'])
    if not b:
        return ''
    y = []
    if b['loai'] == 'dau':
        po = b['po_amorphous'] if d['loi'] == 'amorphous' else b['po_silic']
        pk, uk = b['pk'], b['uk']
        if po:
            y.append(f"tổn hao không tải tối đa <strong>{_g(po)}W</strong> — phần điện "
                     f"mất đi liên tục do từ hoá lõi thép, có mặt cả khi máy chạy không tải")
        if pk:
            y.append(f"tổn hao có tải tối đa <strong>{_g(pk)}W</strong> ở chế độ định mức "
                     f"— phần mất trên cuộn dây, tăng theo bình phương dòng tải")
    else:
        po, pk, uk = b['po_24kv'], b['pk_24kv'], b['uk']
        if po:
            y.append(f"tổn hao không tải tối đa <strong>{_g(po)}W</strong> (cấp 24kV)")
        if pk:
            y.append(f"tổn hao ngắn mạch tối đa <strong>{_g(pk)}W</strong> ở 120°C (cấp 24kV)")
        if b.get('hieu_suat'):
            y.append(f"hiệu suất năng lượng tối thiểu <strong>{b['hieu_suat']}%</strong>")
    if uk:
        y.append(f"điện áp ngắn mạch <strong>Uk {_g(uk)}%</strong> — trị số này quyết định "
                 f"dòng ngắn mạch phía hạ áp, là căn cứ chọn thiết bị bảo vệ và tính khả "
                 f"năng vận hành song song với máy khác")
    if not y:
        return ''
    # Ver 6.2 — 4 khung câu. Danh sách `y` (các mệnh đề số liệu) giữ NGUYÊN,
    # chỉ đổi câu dẫn, thứ tự mệnh đề và câu miễn trừ. Khối này dài nhất
    # trong 5 khối (627 ký tự TB) nên là chỗ đóng góp trùng lặp lớn nhất.
    bt = _bien_the(row, 4, 'doc_hieu')
    kv = _g(b['kva'])
    # Ver 6.2 — CỤM BẮT BUỘC, MỌI BIẾN THỂ ĐỀU PHẢI CÓ, không được diễn đạt
    # lại: 'tối đa theo catalogue' + 'không phải kết quả đo'. Đây là câu
    # chống mạo nhận số catalogue thành số đo của máy — tests/test_v32_tang3.py
    # mục 4 canh đúng hai cụm này. Ver 6.2 bản nháp từng thay bằng "ngưỡng
    # tối đa"/"mức trần catalogue" cho đỡ trùng và làm FAIL 2 assertion.
    # Đa dạng hoá được phép ở PHẦN ĐUÔI câu, không phải ở cụm bắt buộc.
    _loi_hua = ('Đây là giá trị <em>tối đa theo catalogue</em> cho cả dòng sản phẩm, '
                'không phải kết quả đo của từng máy')
    duoi = {
        0: ' — biên bản thí nghiệm xuất xưởng của máy cụ thể thường cho số tốt hơn.',
        1: '; muốn biết số thật của đúng máy được giao thì căn cứ biên bản thí nghiệm '
           'xuất xưởng đi kèm.',
        2: '. Máy giao thực tế thường đo được thấp hơn ngưỡng này, chênh bao nhiêu thì '
           'tuỳ lô sản xuất.',
        3: ', nên khi so sánh giữa các hãng phải so cùng loại số — catalogue với '
           'catalogue, biên bản với biên bản.',
    }[bt]
    mien_tru = _loi_hua + duoi
    if bt == 0:
        cau = (f"Theo catalogue của hãng, cấu hình {kv}kVA này có: " + '; '.join(y) +
               f". {mien_tru} (Nguồn: {b['nguon']}.)")
    elif bt == 1:
        cau = (f"Mấy con số kỹ thuật của bản {kv}kVA nên đọc thế này — " +
               '; '.join(reversed(y)) + f". {mien_tru} (Nguồn: {b['nguon']}.)")
    elif bt == 2:
        cau = (f"Bản {kv}kVA được catalogue công bố các trị số sau: " + '; '.join(y) +
               f". {mien_tru} (Nguồn: {b['nguon']}.)")
    else:
        cau = ('; '.join(y).capitalize() + f" — đó là bộ thông số catalogue cho cấu hình "
               f"{kv}kVA. {mien_tru} (Nguồn: {b['nguon']}.)")
    return _p(cau)


# ---------------------------------------------------------------- KHỐI 4: lắp đặt & vận chuyển
def khoi_lap_dat_van_chuyen(row):
    """Lưu ý lắp đặt — biến thiên theo dải công suất và dầu/khô."""
    d = dac_trung(row)
    dai = _dai(d['kva'])
    if not dai or not d['loai']:
        return ''
    theo_dai = {
        'rat_nho': 'Ở dải công suất này máy đủ nhẹ để lắp bằng tời hoặc xe cẩu nhỏ, '
                   'thi công gọn trong ngày.',
        'nho': 'Ở dải này việc lắp đặt thường cần xe cẩu cỡ trung và một tổ thi công; '
               'nên khảo sát trước đường vào và bán kính quay của cẩu.',
        'vua': 'Ở dải này khối lượng máy đã đáng kể — cần nền móng tính toán riêng, '
               'xe cẩu phù hợp và phương án hạ máy vào vị trí.',
        'lon': 'Ở dải công suất lớn, vận chuyển và cẩu lắp là hạng mục cần lên phương án '
               'từ giai đoạn thiết kế: tải trọng đường, cao độ tĩnh không, vị trí đặt cẩu.',
        'rat_lon': 'Ở dải công suất rất lớn, việc vận chuyển thường phải xin phép tuyến '
                   'đường và bố trí cẩu chuyên dụng; nền móng và hệ thống thoát nhiệt '
                   'phải được thiết kế đồng bộ với trạm.',
    }[dai]
    theo_loai = (
        'Máy dầu cần hố thu dầu sự cố, kiểm tra mức dầu và silicagel định kỳ, '
        'và lấy mẫu dầu thử nghiệm theo chu kỳ bảo trì.'
        if d['loai'] == 'dau' else
        'Máy khô không có dầu nên bỏ được hố thu dầu, nhưng bù lại phải bảo đảm thông '
        'gió cho phòng đặt máy và vệ sinh bụi bám trên cuộn dây định kỳ.')
    dau_cau = f"Với cấu hình {_g(d['kva'])}kVA"
    if d['hang']:
        dau_cau += f" của {html.escape(str(d['hang']).split('/')[0].strip())}"
    # Ver 6.2 — 4 khung câu, cùng cặp (lưu ý theo dải, lưu ý theo dầu/khô).
    bt = _bien_the(row, 4, 'lap_dat')
    thap = theo_dai[0].lower() + theo_dai[1:]
    if bt == 0:
        return _p(f'{dau_cau}: {thap} {theo_loai}')
    if bt == 1:
        return _p(f'{theo_loai} Còn về thi công, {thap.rstrip(".")} — điểm cần tính khi '
                  f'lên phương án cho bản {_g(d["kva"])}kVA.')
    if bt == 2:
        return _p(f'{theo_dai} Đi kèm đó, {theo_loai[0].lower() + theo_loai[1:]}')
    return _p(f'Khâu chuẩn bị mặt bằng và bảo trì cho {dau_cau.lower().replace("với ", "")} '
              f'gồm hai phần. {theo_dai} {theo_loai}')


# ---------------------------------------------------------------- KHỐI 5: chọn công suất
def khoi_chon_cong_suat(row):
    """Đối chiếu với mức lân cận trong cùng dải — giúp người mua tự cân nhắc."""
    d = dac_trung(row)
    if not d['kva'] or not d['loai'] or not d['pha']:
        return ''
    duoi, tren = TC.muc_lan_can(d['kva'], d['pha'], d['loai'])
    if duoi is None and tren is None:
        return ''
    ve = []
    b = TC.tra(d['kva'], d['pha'], d['loai'], d['hang'])
    for muc, nhan in ((duoi, 'thấp hơn'), (tren, 'cao hơn')):
        if muc is None:
            continue
        bm = TC.tra(muc, d['pha'], d['loai'], d['hang'])
        if b and bm:
            po_key = ('po_amorphous' if (d['loi'] == 'amorphous' and b['loai'] == 'dau')
                      else 'po_silic' if b['loai'] == 'dau' else 'po_24kv')
            if b.get(po_key) and bm.get(po_key):
                ve.append(f"mức {nhan} liền kề là {_g(muc)}kVA (tổn hao không tải "
                          f"{_g(bm[po_key])}W so với {_g(b[po_key])}W của mức này)")
                continue
        ve.append(f'mức {nhan} liền kề là {_g(muc)}kVA')
    if not ve:
        return ''
    # Ver 6.2 — 4 khung câu, cùng bộ số liệu mức lân cận.
    bt = _bien_the(row, 4, 'chon_cs')
    if bt == 0:
        cau = (f"Trong dải sản phẩm cùng loại, {' và '.join(ve)}. Chọn công suất nên căn "
               f"cứ phụ tải tính toán cộng dự phòng phát triển, thay vì chọn sát mép: máy "
               f"chạy non tải kéo dài thì tổn hao không tải chiếm tỉ trọng lớn, còn chọn "
               f"thiếu thì phải thay máy khi phụ tải tăng.")
    elif bt == 1:
        cau = (f"Nếu đang phân vân giữa các mức: {' và '.join(ve)}. Căn cứ nên là phụ tải "
               f"tính toán cộng phần dự phòng cho vài năm tới. Chọn sát quá thì hết đường "
               f"mở rộng, chọn dư quá thì máy chạy non tải và phần tổn hao không tải trở "
               f"nên đáng kể so với điện thực dùng.")
    elif bt == 2:
        cau = (f"Bài toán chọn mức công suất ở đây khá rõ: {' và '.join(ve)}. Cách làm an "
               f"toàn là lấy phụ tải tính toán, cộng dự phòng phát triển, rồi mới đối "
               f"chiếu sang mức máy — chứ không lấy công suất đặt hiện tại làm chuẩn. Máy "
               f"non tải lâu dài tốn tổn hao không tải; máy thiếu thì sớm phải thay.")
    else:
        cau = (f"Hai hướng cân nhắc: {' và '.join(ve)}. Điểm cần chốt trước là phụ tải "
               f"tính toán của công trình cộng biên dự phòng — có con số đó rồi thì việc "
               f"chọn mức nào chỉ còn là đối chiếu. Lưu ý máy chạy non tải kéo dài khiến "
               f"tổn hao không tải chiếm tỉ trọng lớn trong hoá đơn, còn chọn thiếu thì "
               f"phải thay máy khi phụ tải tăng.")
    return _p(cau)


# ---------------------------------------------------------------- gom
DANH_SACH_KHOI = [khoi_ung_dung, khoi_so_sanh_loi, khoi_doc_hieu_thong_so,
                  khoi_lap_dat_van_chuyen, khoi_chon_cong_suat]


def tat_ca_khoi(row, tieu_de='', anh_em=None):   # tieu_de giữ cho tương thích ngược
    """Trả HTML gộp mọi khối dựng được cho SKU này. Không có khối nào -> ''.

    Ver 3.6.4 — `anh_em`: danh sách SKU cùng dataset, truyền xuống
    khoi_so_sanh_loi() để nó lấy được Po của bản khác lõi khi bảng tra
    THIBIDI không có hãng đó (mở biểu đồ cho 86 SKU MBT)."""
    if row.get('outline_id') != 'outline_may_bien_ap':
        return ''
    # Ver 3.2 — PHỤ KIỆN của MBA (vỏ, nắp che, giá treo...) có tên chứa
    # 'MBA 560kVA' nên từng lọt vào đây và được gán kiến thức máy biến áp.
    # Dùng chung đúng luật với enrich_tcvn_mba.la_phu_kien().
    try:
        import enrich_tcvn_mba as _E
        if _E.la_phu_kien(row.get('ten_goc', '')):
            return ''
    except Exception:
        pass
    phan = []
    for f in DANH_SACH_KHOI:
        # chỉ khoi_so_sanh_loi nhận thêm `anh_em`; các khối khác giữ nguyên
        # chữ ký cũ để không phải sửa lan.
        phan.append(f(row, anh_em) if f is khoi_so_sanh_loi else f(row))
    phan = [p for p in phan if p]
    if not phan:
        return ''
    # Ver 6.2 — XÁO THỨ TỰ KHỐI theo SKU, ổn định (cùng SKU luôn cùng thứ tự).
    # Hai bài cạnh nhau không còn đi đúng một mạch 1-2-3-4-5. Giữ khối ứng
    # dụng luôn đứng đầu — đó là thứ người đọc cần trước, không xáo lên xuống.
    if len(phan) > 2:
        dau, con_lai = phan[0], phan[1:]
        k = _bien_the(row, len(con_lai), 'thu_tu')
        phan = [dau] + con_lai[k:] + con_lai[:k]
    # Ver 3.3 — KHÔNG tự thêm <h2>: bố cục 2.5 đã mở section "Kiến thức
    # kỹ thuật liên quan" bao ngoài, thêm nữa thành 2 tiêu đề trùng khít
    # (thấy rõ trên bài thật TBD3P250). Chỉ trả nội dung.
    return ''.join(phan)
