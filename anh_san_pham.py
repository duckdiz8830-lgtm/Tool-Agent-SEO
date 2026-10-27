# -*- coding: utf-8 -*-
"""
SONEALEO ULTRA 3.0 — ẢNH SẢN PHẨM: quét thư mục ảnh trên máy, ghép với
SKU bằng TÊN FILE + ĐƯỜNG DẪN THƯ MỤC, tối ưu WebP, upload WordPress
Media và đặt ảnh đại diện.

VER 3.0 — ĐƯỜNG DẪN THƯ MỤC LÀ METADATA:
  Kho Drive thật của Lotech: file tên vô nghĩa ('z4395168565850_0.jpg')
  nhưng nằm trong 'MBA/320/' — người chụp ĐÃ phân loại bằng thư mục.
  3.0 đọc cả path: folder 'MBA' -> ngữ cảnh máy biến áp, folder '320'
  -> 320kVA, folder 'HBT'/'SHIHLIN' -> hãng, folder 'bienmay' -> ảnh
  biển máy (nguồn dữ liệu, không phải ảnh bán hàng). Tên file vẫn ưu
  tiên hơn; thư mục chỉ ĐIỀN CHỖ TRỐNG. Folder nhiều số ('1250 - 250')
  -> KHÔNG đoán, ghi cảnh báo để gán tay.

VER 2.9 — 3 vá từ sự cố batch 245 bài thật (05/08/2026):
  1. PHÂN BIỆT DẦU/KHÔ: ảnh MBA dầu THIBIDI 4000kVA từng bị gắn vào bài
     MBA KHÔ KP 4000kVA vì thuật toán chỉ khớp số kVA. Giờ dầu/khô là
     tiêu chí LOẠI HẲN (như số pha): ảnh ghi 'dau' không bao giờ ghép
     row 'kho' và ngược lại.
  2. GHÉP MƠ HỒ KHÔNG CÒN BÁO 'cao': trước đây 1 ảnh khớp đều 7 SKU vẫn
     hiện độ tin cậy 'cao' + tự tick chọn + tự gắn sao đại diện — cảnh
     báo chỉ nằm cuối cột lý do (bị cắt trên UI). Giờ ghép mơ hồ hạ
     xuống 'vua', KHÔNG tự tick — người dùng phải chủ động xác nhận.
  3. TÊN FILE NHIỀU MỨC CÔNG SUẤT ('mba 250kva 320kva.jpg'): trước lấy
     số đầu trong im lặng. Giờ vẫn lấy số đầu nhưng hạ tin cậy + ghi rõ
     cảnh báo vào lý do.

VÌ SAO
Trang sản phẩm B2B không có ảnh thì mất tin tưởng ngay. Lotech có sẵn
kho ảnh thật (chụp tại kho, lúc giao hàng, lúc cẩu lắp) trên Google
Drive — giá trị hơn ảnh catalogue vì đó là bằng chứng đã bán/đã lắp.
Việc còn thiếu chỉ là đường nối: tên file -> SKU -> WordPress.

NGUYÊN TẮC
  - Tên file KHÔNG parse được -> KHÔNG đoán, để người dùng gán tay.
  - Không tải ảnh từ Internet, không sinh ảnh. Chỉ dùng ảnh trong thư
    mục người dùng chỉ định.
  - Luôn có bước xem trước; upload là hành động riêng, không tự động.
  - Đổi tên file + alt text theo SKU -> mở cửa Google Images (ảnh gốc
    tên kiểu 'z7247219391950_47.jpg' vô nghĩa với SEO).
"""
import io
import os
import re
import unicodedata
from chuan_hoa import bo_dau as _bo_dau   # Ver 5.7 — gom 9 bản _bo_dau về 1 nguồn (xem chuan_hoa.py)

DUOI_ANH = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')


# ---------------------------------------------------------------- parse tên file
_RE_CONG_SUAT = re.compile(r'(\d+(?:[.,]\d+)?)\s*k?va\b', re.IGNORECASE)
# "250k", "320kv" — CHỈ nhận là công suất khi số >= 50, vì lưới phân phối
# VN cao nhất 35kV nên "22kv"/"35kv" là ĐIỆN ÁP chứ không phải công suất.
_RE_CS_TRAN = re.compile(r'\b(\d{2,4})\s*k[v]?\b', re.IGNORECASE)
_RE_PHA = re.compile(r'\b([13])\s*p(?:ha)?\b', re.IGNORECASE)

# Thương hiệu nhận diện được — khớp theo token, không khớp chuỗi con.
# Ver 3.0: thêm 'hbt' (thấy trong cây thư mục Drive thật của Lotech).
_THUONG_HIEU = ['mbt', 'thibidi', 'shihlin', 'sanaky', 'emc', 'hem', 'abb',
                'kp', 'hbt', 'cadivi', 'ls vina', 'lsvina', 'taya', 'daphaco']


def phan_tich_ten_file(ten_file):
    """Bóc thông tin từ tên file ảnh.

    Trả dict {thuong_hieu, cong_suat, so_pha, loai_loi, do_tin_cay}.
    do_tin_cay: 'cao' (có hãng + công suất), 'vua' (chỉ 1 trong 2),
    'khong' (không có gì) — 'khong' nghĩa là phải gán tay.
    """
    goc = os.path.splitext(os.path.basename(ten_file))[0]
    t = ' ' + _bo_dau(goc).replace('_', ' ').replace('-', ' ') + ' '

    th = None
    for h in _THUONG_HIEU:
        if re.search(rf'\b{re.escape(h)}\b', t):
            th = h.upper()
            break

    cs = None
    m = _RE_CONG_SUAT.search(t)
    if m:
        cs = float(m.group(1).replace(',', '.'))
    else:
        m2 = _RE_CS_TRAN.search(t)
        if m2 and float(m2.group(1)) >= 50:
            cs = float(m2.group(1))

    pha = None
    mp = _RE_PHA.search(t)
    if mp:
        pha = int(mp.group(1))

    loi = None
    if 'amorphous' in t:
        loi = 'amorphous'
    elif 'silic' in t:
        loi = 'silic'

    # Ver 2.9 — dầu/khô. Chỉ nhận khi có ngữ cảnh máy biến áp ('mba' hoặc
    # 'bien ap') để 'đầu cáp' (bỏ dấu = 'dau cap') không bị nhận nhầm là
    # máy dầu. 'khong' (không) chứa 'kho' nhưng khớp token \b nên an toàn.
    loai_may = None
    if re.search(r'\bmba\b|bien\s*ap', t):
        if re.search(r'\bkho\b', t):
            loai_may = 'kho'
        elif re.search(r'\bdau\b', t):
            loai_may = 'dau'

    # Ver 2.9 — tên file có NHIỀU mức công suất khác nhau ('250kva
    # 320kva'): vẫn lấy số đầu (hành vi cũ) nhưng phải nói ra, không im
    # lặng nữa — người dùng từng dính đúng case này ở batch thật.
    canh_bao = None
    cac_cs = {m.group(1) for m in _RE_CONG_SUAT.finditer(t)}
    if len(cac_cs) > 1:
        canh_bao = (f'tên file có {len(cac_cs)} mức công suất '
                    f'({", ".join(sorted(cac_cs))}) — lấy số đầu, nên kiểm lại')

    if th and cs:
        tin = 'cao'
    elif th or cs:
        tin = 'vua'
    else:
        tin = 'khong'
    if canh_bao and tin == 'cao':
        tin = 'vua'

    return {'thuong_hieu': th, 'cong_suat': cs, 'so_pha': pha,
            'loai_loi': loi, 'loai_may': loai_may, 'canh_bao': canh_bao,
            'do_tin_cay': tin, 'ten_goc': goc}


# ---------------------------------------------------------------- Ver 3.0: parse ĐƯỜNG DẪN
def phan_tich_duong_dan(duong_dan_anh, goc_thu_muc):
    """Ver 3.0 — bóc metadata từ CÂY THƯ MỤC giữa gốc quét và file.

    Kho Drive thật: 'MBA/320/z4395...jpg' — folder là phân loại của người
    chụp. Quy tắc:
      - folder 'mba'/'may bien ap'         -> ngữ cảnh máy biến áp
      - folder là 1 SỐ TRẦN 15..4000       -> công suất kVA (chỉ khi có
        ngữ cảnh mba, vì '320' trong folder cáp có thể là mét)
      - folder trùng tên hãng               -> thương hiệu
      - folder 'kho'/'dau'                  -> loại máy (cần ngữ cảnh mba)
      - folder chứa NHIỀU số ('1250 - 250') -> KHÔNG đoán, trả cảnh báo
      - folder 'bienmay'/'bien may'/'nameplate' -> ảnh biển máy (nguồn
        DỮ LIỆU cho vision đọc thông số, không phải ảnh bán hàng)
    """
    ra = {'thuong_hieu': None, 'cong_suat': None, 'loai_may': None,
          'la_mba': False, 'la_bien_may': False, 'canh_bao': None}
    try:
        rel = os.path.relpath(os.path.dirname(os.path.abspath(duong_dan_anh)),
                              os.path.abspath(goc_thu_muc))
    except ValueError:      # khác ổ đĩa trên Windows
        return ra
    if rel in ('.', ''):
        rel = ''
    phan = [_bo_dau(p).strip() for p in rel.replace('\\', '/').split('/') if p]
    # TÊN THƯ MỤC GỐC chỉ dùng làm NGỮ CẢNH (mba/bienmay), KHÔNG moi giá
    # trị từ nó: người dùng có thể trỏ tool vào 'MBA' (cần ngữ cảnh này)
    # nhưng cũng có thể trỏ vào 'LOTECH Files 2026' — số trong tên gốc
    # là rác, moi ra sẽ sinh cảnh báo nhảm (bug bắt được bằng test).
    goc_ten = _bo_dau(os.path.basename(os.path.abspath(goc_thu_muc))).strip()
    phan_ngu_canh = ([goc_ten] if goc_ten else []) + phan

    # lượt 1 — ngữ cảnh trước (mba có thể nằm ở folder cha bất kỳ)
    for p in phan_ngu_canh:
        if re.search(r'\bmba\b|may\s*bien\s*ap|bien\s*ap', p):
            ra['la_mba'] = True
        if re.search(r'bien\s*may|bienmay|nameplate', p):
            ra['la_bien_may'] = True

    # lượt 2 — giá trị
    for p in phan:
        for h in _THUONG_HIEU:
            if re.fullmatch(re.escape(h), p) or re.search(rf'\b{re.escape(h)}\b', p):
                ra['thuong_hieu'] = ra['thuong_hieu'] or h.upper()
                break
        if ra['la_mba']:
            if re.fullmatch(r'\bkho\b', p):
                ra['loai_may'] = ra['loai_may'] or 'kho'
            elif re.fullmatch(r'\bdau\b', p):
                ra['loai_may'] = ra['loai_may'] or 'dau'
        so_trong_folder = re.findall(r'\d+(?:[.,]\d+)?', p)
        if not so_trong_folder:
            continue
        if len(so_trong_folder) > 1:
            # '1250 - 250' — hai mức, không đoán mức nào
            ra['canh_bao'] = (f"thư mục '{p}' có {len(so_trong_folder)} số "
                              f"({', '.join(so_trong_folder)}) — không tự chọn, cần gán tay")
            continue
        so = float(so_trong_folder[0].replace(',', '.'))
        # chỉ nhận là kVA khi folder GẦN NHƯ chỉ là con số + có ngữ cảnh mba
        chi_la_so = re.fullmatch(r'[\d.,\s]*(kva)?', p)
        if ra['la_mba'] and chi_la_so and 15 <= so <= 4000:
            ra['cong_suat'] = so
    return ra


def phan_tich_anh(duong_dan_anh, goc_thu_muc=None):
    """Ver 3.0 — kết hợp TÊN FILE (ưu tiên) + ĐƯỜNG DẪN (điền chỗ trống).

    Tên file do người đặt có chủ đích -> tin hơn; thư mục là phân loại
    thô -> chỉ dùng khi tên file thiếu. Trả cùng cấu trúc
    phan_tich_ten_file, cộng thêm 'la_bien_may' và 'nguon_path' (ghi rõ
    trường nào lấy từ thư mục — hiện lên cột lý do cho người dùng soi).
    """
    tt = phan_tich_ten_file(os.path.basename(duong_dan_anh))
    tt['la_bien_may'] = False
    if not goc_thu_muc:
        return tt
    pd = phan_tich_duong_dan(duong_dan_anh, goc_thu_muc)
    tt['la_bien_may'] = pd['la_bien_may']
    tu_path = []
    if not tt.get('thuong_hieu') and pd['thuong_hieu']:
        tt['thuong_hieu'] = pd['thuong_hieu']
        tu_path.append(f"hãng {pd['thuong_hieu']} (thư mục)")
    if not tt.get('cong_suat') and pd['cong_suat']:
        tt['cong_suat'] = pd['cong_suat']
        tu_path.append(f"công suất {pd['cong_suat']:g}kVA (thư mục)")
    if not tt.get('loai_may') and pd['loai_may']:
        tt['loai_may'] = pd['loai_may']
        tu_path.append('loại ' + ('khô' if pd['loai_may'] == 'kho' else 'dầu') + ' (thư mục)')
    if pd['canh_bao']:
        tt['canh_bao'] = (f"{tt['canh_bao']} | {pd['canh_bao']}"
                          if tt.get('canh_bao') else pd['canh_bao'])
    tt['nguon_path'] = ', '.join(tu_path)
    # tính lại độ tin cậy sau khi thư mục điền chỗ trống. Thông tin từ
    # thư mục ÁP CHO CẢ FOLDER (không riêng ảnh này) nên trần là 'vua' —
    # đủ để tool đề xuất ghép, nhưng người dùng vẫn nên liếc lại.
    if tt['do_tin_cay'] == 'khong' and (tt.get('thuong_hieu') or tt.get('cong_suat')):
        tt['do_tin_cay'] = 'vua'
    if tt.get('canh_bao') and tt['do_tin_cay'] == 'cao':
        tt['do_tin_cay'] = 'vua'
    return tt


# ---------------------------------------------------------------- ghép với SKU
def _kva_cua_row(row):
    v = row.get('cong_suat') or ''
    m = re.search(r'\d+(?:[.,]\d+)?', str(v))
    return float(m.group(0).replace(',', '.')) if m else None


def _pha_cua_row(row):
    t = _bo_dau(row.get('ten_goc', ''))
    if re.search(r'\b3\s*pha\b|3p\b', t):
        return 3
    if re.search(r'\b1\s*pha\b|1p\b', t):
        return 1
    return None


def _loai_may_cua_row(row):
    """Ver 2.9 — dầu/khô của SKU, bắt theo CỤM 'biến áp dầu/khô' để tên
    hàng chứa 'đầu cáp', 'đầu cosse'... không bị nhận nhầm."""
    t = _bo_dau(row.get('ten_goc', ''))
    m = re.search(r'(?:bien\s*ap|mba)\s+(?:\w+\s+)?(dau|kho)\b', t)
    return m.group(1) if m else None


def ghep_anh_voi_sku(thong_tin_anh, danh_sach_row):
    """Tìm SKU khớp nhất với 1 ảnh.

    Bắt buộc khớp CÔNG SUẤT (nếu ảnh có). Thương hiệu, số pha, loại lõi
    là điểm cộng. Không có công suất trong tên -> không ghép tự động.

    Trả (row_khop, ly_do) hoặc (None, ly_do_khong_khop).
    """
    if not thong_tin_anh.get('cong_suat'):
        return None, 'Tên file không có công suất — cần gán tay'

    cs_anh = thong_tin_anh['cong_suat']
    ung_vien = []
    for r in danh_sach_row:
        if _kva_cua_row(r) != cs_anh:
            continue
        diem = 1
        ly_do = [f'công suất {cs_anh:g}kVA']
        th_anh = (thong_tin_anh.get('thuong_hieu') or '').lower()
        if th_anh and th_anh in _bo_dau(r.get('thuong_hieu', '') + ' ' + r.get('ten_goc', '')):
            diem += 2
            ly_do.append(f'hãng {th_anh.upper()}')
        if thong_tin_anh.get('so_pha') and _pha_cua_row(r) == thong_tin_anh['so_pha']:
            diem += 2
            ly_do.append(f"{thong_tin_anh['so_pha']} pha")
        elif thong_tin_anh.get('so_pha') and _pha_cua_row(r):
            continue   # số pha mâu thuẫn -> loại hẳn
        # Ver 2.9 — dầu/khô mâu thuẫn -> LOẠI HẲN (bài học batch 245:
        # ảnh MBA dầu THIBIDI từng gắn vào bài MBA khô KP vì chỉ so kVA).
        lm_anh, lm_row = thong_tin_anh.get('loai_may'), _loai_may_cua_row(r)
        if lm_anh and lm_row:
            if lm_anh != lm_row:
                continue
            diem += 2
            ly_do.append('máy ' + ('khô' if lm_anh == 'kho' else 'dầu'))
        if thong_tin_anh.get('loai_loi'):
            if thong_tin_anh['loai_loi'] in _bo_dau(r.get('ten_goc', '')):
                diem += 1
                ly_do.append(thong_tin_anh['loai_loi'])
        ung_vien.append((diem, r, ', '.join(ly_do)))

    if not ung_vien:
        return None, f'Không SKU nào có công suất {cs_anh:g}kVA'
    ung_vien.sort(key=lambda x: -x[0])
    if len(ung_vien) > 1 and ung_vien[0][0] == ung_vien[1][0]:
        return (ung_vien[0][1],
                f'{ung_vien[0][2]} (có {len(ung_vien)} SKU cùng khớp — nên kiểm lại)')
    return ung_vien[0][1], ung_vien[0][2]


def quet_thu_muc(duong_dan, danh_sach_row):
    """Quét thư mục ảnh, trả list dict đã ghép sẵn để hiển thị lên UI."""
    if not duong_dan or not os.path.isdir(duong_dan):
        return {'ok': False, 'loi': 'Thư mục không tồn tại.'}
    ket_qua = []
    for goc, _thu_muc, files in os.walk(duong_dan):
        for f in sorted(files):
            if not f.lower().endswith(DUOI_ANH):
                continue
            duong_dan_anh = os.path.join(goc, f)
            # Ver 3.0 — parse cả tên file lẫn đường dẫn thư mục
            tt = phan_tich_anh(duong_dan_anh, goc_thu_muc=duong_dan)
            if tt.get('la_bien_may'):
                # ảnh biển máy = NGUỒN DỮ LIỆU cho bước vision đọc thông
                # số, không phải ảnh bán hàng -> không ghép SKU, không
                # tick, hiện rõ lý do để người dùng biết vì sao bị bỏ qua.
                ket_qua.append({
                    'duong_dan': duong_dan_anh, 'ten_file': f,
                    'kich_thuoc_kb': round(os.path.getsize(duong_dan_anh) / 1024),
                    'phan_tich': tt, 'ma_goc': '', 'record_id': '',
                    'ten_san_pham': '', 'do_tin_cay': 'khong',
                    'ly_do': 'ảnh biển máy — dành cho bước đọc thông số, không đăng làm ảnh sản phẩm',
                    'chon': False, 'anh_dai_dien': False,
                })
                continue
            row, ly_do = ghep_anh_voi_sku(tt, danh_sach_row)
            # Ver 2.9 — mơ hồ (nhiều SKU đồng điểm) hoặc có cảnh báo tên
            # file: hạ 'cao' -> 'vua', KHÔNG tự tick chọn/đại diện. Trước
            # đây ghép 1/7 SKU vẫn hiện 'cao' + tự chọn, cảnh báo nằm cuối
            # cột lý do bị UI cắt cụt — người dùng không hề thấy.
            mo_ho = bool(row) and 'cùng khớp' in (ly_do or '')
            if tt.get('canh_bao'):
                ly_do = f"{ly_do} | {tt['canh_bao']}" if ly_do else tt['canh_bao']
            if tt.get('nguon_path'):
                ly_do = f"{ly_do} | {tt['nguon_path']}" if ly_do else tt['nguon_path']
            tin = tt['do_tin_cay'] if row else 'khong'
            if row and mo_ho and tin == 'cao':
                tin = 'vua'
            tu_chon = bool(row) and not mo_ho and tin == 'cao'
            ket_qua.append({
                'duong_dan': duong_dan_anh, 'ten_file': f,
                'kich_thuoc_kb': round(os.path.getsize(duong_dan_anh) / 1024),
                'phan_tich': tt, 'ma_goc': row.get('ma_goc') if row else '',
                'record_id': row.get('record_id') if row else '',
                'ten_san_pham': row.get('ten_goc') if row else '',
                'do_tin_cay': tin,
                'ly_do': ly_do, 'chon': tu_chon, 'anh_dai_dien': tu_chon,
            })
    return {'ok': True, 'danh_sach': ket_qua}


# ---------------------------------------------------------------- tối ưu ảnh
def toi_uu_anh(duong_dan, rong_toi_da=1200, chat_luong=82, sang_webp=True):
    """Resize + convert WebP trong bộ nhớ (không ghi đè file gốc).

    Trả (bytes, ten_duoi) hoặc (None, loi)."""
    try:
        from PIL import Image
    except ImportError:
        return None, 'Thiếu thư viện Pillow — chạy CAI-DAT-LAN-DAU.bat lại.'
    try:
        with Image.open(duong_dan) as im:
            im = im.convert('RGB')
            if im.width > rong_toi_da:
                cao = round(im.height * rong_toi_da / im.width)
                im = im.resize((rong_toi_da, cao), Image.LANCZOS)
            buf = io.BytesIO()
            if sang_webp:
                im.save(buf, 'WEBP', quality=chat_luong, method=4)
                return buf.getvalue(), 'webp'
            im.save(buf, 'JPEG', quality=chat_luong, optimize=True)
            return buf.getvalue(), 'jpg'
    except Exception as e:
        return None, f'{type(e).__name__}: {e}'


def ten_file_seo(row, thu_tu=1, duoi='webp'):
    """Đổi tên file theo SEO. Ảnh gốc tên 'z7247219391950_47.jpg' hoàn
    toàn vô nghĩa với Google Images."""
    import dulieu as D
    phan = [row.get('ten_goc', '') or row.get('ma_goc', '')]
    ten = D.slugify(' '.join(p for p in phan if p), dai=70) or 'san-pham'
    return f'{ten}-{thu_tu}.{duoi}' if thu_tu > 1 else f'{ten}.{duoi}'


def alt_text(row, thu_tu=1):
    ten = row.get('ten_goc', '') or row.get('ma_goc', '')
    duoi = ['', ' — ảnh thực tế', ' — ảnh lắp đặt tại công trình',
            ' — ảnh giao hàng']
    return f'{ten}{duoi[min(thu_tu - 1, len(duoi) - 1)]}'
