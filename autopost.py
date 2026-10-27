#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Engine: dữ liệu sản phẩm -> AI viết văn xuôi -> ghép HTML -> WordPress.

Giao diện (giao-dien.py) và dòng lệnh đều gọi CHUNG hàm sinh_mot_bai().
Sửa logic ở đây là cả hai đường cùng đổi.

Dòng lệnh:
    python autopost.py --site site1 --so 3 --che-do thu       # không gọi AI
    python autopost.py --site site1 --so 10 --che-do sinh     # gọi AI, chỉ ghi file
    python autopost.py --site site1 --so 10 --che-do nhap     # đăng dạng nháp
    python autopost.py --site site1 --do-model                # dò model Gemini dùng được
    python autopost.py --site site1 --kiem-tra-wp             # dò WordPress chết ở đâu
"""
import argparse
import csv
import html
import json
import os
import random
import re
import sys
import time
from pathlib import Path

import cauhinh as C
import prompts as P
import dulieu as DL

BASE = Path(__file__).parent
CSV_PATH = BASE / 'products.csv'
OUT_DIR = BASE / 'output'
LOG_PATH = BASE / 'log.csv'


# ============================================================ cấu hình chạy
def nap_env():
    """Đọc cau-hinh.env và nạp vào biến môi trường. File cấu hình thắng biến hệ thống."""
    # Ver 4.4.1.6 — ưu tiên %APPDATA%\SONEALEO\cau-hinh.env; không có thì
    # dùng bản cạnh mã nguồn như cũ (không phá cài đặt đang chạy).
    f = None
    try:
        import thu_muc_du_lieu as _TM
        _TM.chuan_bi(BASE)
        ung_vien = _TM.duong_dan_env()
        if ung_vien.exists():
            f = ung_vien
    except Exception:
        f = None
    if f is None:
        f = BASE / 'cau-hinh.env'
    if not f.exists():
        return
    for line in f.read_text(encoding='utf-8-sig').splitlines():   # utf-8-sig: bỏ BOM Notepad
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        v = v.split('#')[0].strip().strip('"').strip("'")
        v = v.replace('\u200b', '').replace('\xa0', ' ').strip()  # ký tự ẩn khi copy
        os.environ[k.strip()] = v


nap_env()

NHA_CUNG_CAP = os.environ.get('NHA_CUNG_CAP', 'gemini').strip().lower()
MODEL_GEMINI = os.environ.get('MODEL_GEMINI', 'gemini-3.6-flash')
MODEL_CLAUDE = os.environ.get('MODEL_CLAUDE', 'claude-haiku-4-5')
MAX_TOKENS = 8192
# Model có "suy nghĩ ngầm" ăn token vào phần suy nghĩ trước khi viết, tính chung
# vào maxOutputTokens. Không bù thêm thì JSON bị cắt giữa chừng đúng như log
# thật ngày 24/07 (gemini-3.5-flash). Đây là ngân sách dành riêng cho model đó.
MAX_TOKENS_SUY_NGHI = 24576
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta'

_NHO_THINKING = {}    # tra 1 lần mỗi model trong phiên chạy, khỏi gọi API mỗi bài
_MODEL_404_TRONG_PHIEN = set()  # Ver 3.9 A2: model đã 404 thì không thử lại trong cùng process


def _co_suy_nghi_ngam(model, key):
    """Model này có bật suy nghĩ ngầm không, theo đúng field API trả về (không đoán
    theo tên). Tra không được thì coi như không, dùng ngân sách token thường."""
    if model in _NHO_THINKING:
        return _NHO_THINKING[model]
    import requests
    nghi = False
    try:
        r = requests.get(f'{GEMINI_URL}/models/{model}', params={'key': key}, timeout=30)
        if r.status_code == 200:
            nghi = bool(r.json().get('thinking', False))
    except Exception:
        pass
    _NHO_THINKING[model] = nghi
    return nghi


# ============================================================ bộ canh bịa số
# Đơn vị bị canh. Xếp dài trước ngắn sau để "1000kVA" không bị đọc thành "1000kV".
DON_VI = r'(?:kVA|MVA|kV|kA|kW|Hz|IP\d{2}|mm|kg|°C|A|V|W|%)'
SO_DON_VI = re.compile(r'(\d+(?:[.,]\d+)?)\s*(' + DON_VI + r')\b', re.I)
MA_KT = re.compile(r'\b(VIP\s?\d+|REJ\s?\d+|REF\s?\d+|SEPAM\s?\w+|VAMP\s?\d+|8DJH[\w-]*|'
                   r'RM6[\w-]*|SM6[\w-]*|CGM[\w-]*)\b', re.I)


def chuan(s):
    """Chuẩn hoá để SO KHỚP con số.

    Dấu phẩy thập phân đổi thành dấu chấm, nếu không '0,4kV' trong dữ liệu sẽ
    không khớp với '0.4kV' do AI viết, và bài bị chặn oan.
    """
    s = str(s or '').lower()
    s = re.sub(r'(\d)[,](\d)', r'\1.\2', s)      # 0,4kv -> 0.4kv
    s = re.sub(r'(\d)\.0+\b', r'\1', s)          # 22.0kv -> 22kv
    return re.sub(r'[\s,]', '', s)


def mo_rong_gia_tri(v):
    """Tách giá trị ghép thành các con số hợp lệ.

    '22/0,4kV'            -> 22kV, 0,4kV, 22/0,4kV
    '1500 x 900 x 1600mm' -> 1500mm, 900mm, 1600mm
    '20kA/1s'             -> 20kA, 1s
    """
    v = str(v or '').strip()
    if not v:
        return set()
    out = {v}
    m = re.match(r'^([\d.,/x×\s]+?)\s*([a-zA-Z°]+\d*)$', v)
    if m:
        phan, dv = m.group(1), m.group(2)
        for p in re.split(r'[/x×]', phan):
            if p.strip():
                out.add(p.strip() + dv)
    for so, dv in SO_DON_VI.findall(v):
        out.add(so + dv)
    return out


def _kho_cua_dong(row):
    kho = set()
    for v in row.values():
        for x in mo_rong_gia_tri(v):
            kho.add(chuan(x))
    return kho


_KHO_CHUNG = {}


def kho_toan_bo(tat_ca):
    """Mọi giá trị hợp lệ có trong TOÀN BỘ kho sản phẩm.

    AI được phép nhắc con số tồn tại ở dòng khác (ví dụ nói dải sản phẩm có 22kV
    và 35kV). Chỉ chặn con số không có ở bất kỳ đâu.
    Cache theo số dòng để nhập lại Excel là tự tính lại, không dùng số cũ.
    """
    khoa = len(tat_ca)
    if khoa not in _KHO_CHUNG:
        _KHO_CHUNG.clear()
        kho = set()
        for r in tat_ca:
            kho |= _kho_cua_dong(r)
        _KHO_CHUNG[khoa] = kho
    return _KHO_CHUNG[khoa]


def _kho_kien_thuc(row):
    """Con số nằm trong kho kiến thức ĐÃ KIỂM CHỨNG của dòng này.

    Không cho vào đây thì bật kiến thức lên là bài bị chặn oan, vì AI nhắc lại
    đúng con số mình vừa đưa cho nó.
    """
    kt = DL.kien_thuc_thanh_chu(
        DL.nap_kien_thuc(row.get('series') or row.get('dong_san_pham'), row.get('hang')))
    kho = set()
    for so, dv in SO_DON_VI.findall(kt):
        kho.add(chuan(so + dv))
    for ma in MA_KT.findall(kt):
        kho.add(chuan(ma))
    return kho


def kiem_tra_bia(text, row, tat_ca):
    """Chặn con số AI bịa. Trả (chan, canh_bao).

    chan     : con số không có ở bất kỳ đâu trong kho -> KHÔNG đăng
    canh_bao : con số của dòng khác hoặc của kho kiến thức -> vẫn đăng, chỉ ghi log
    """
    rieng = _kho_cua_dong(row)
    chung = kho_toan_bo(tat_ca) | _kho_kien_thuc(row)
    chan, canh = [], []
    for so, dv in SO_DON_VI.findall(text or ''):
        t = chuan(so + dv)
        if t not in rieng:
            (canh if t in chung else chan).append(f'{so}{dv}')
    for ma in MA_KT.findall(text or ''):
        t = chuan(ma)
        if t not in rieng:
            (canh if t in chung else chan).append(ma)
    return sorted(set(chan)), sorted(set(canh))


def kiem_tra_ro_ri(text, ma_site):
    """Từ cấm xuất hiện trong bài -> lộ danh tính công ty mẹ -> chặn."""
    low = (text or '').lower()
    return sorted({t for t in C.tu_cam(ma_site) if t in low})


NGUONG_TRUNG_VAN = 0.75   # >= mức này thì cảnh báo. Chỉ cảnh báo, không chặn.


def _chuan_hoa_so_sanh(t):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t or '')).strip().lower()


def kiem_tra_trung_van(van_xuoi, ma_site, sku_hien_tai):
    """So phần văn AI viết với các bài đã sinh trước đó CÙNG SITE. Chỉ so văn
    biên tập (đã tách riêng khỏi bảng thông số/cấu hình từ trước), không so
    nguyên bài — sản phẩm cùng dòng được phép giống nhau ở phần thông số.
    Trả (tỷ lệ cao nhất, sku giống nhất) hoặc (0, None) nếu không có gì để so.
    """
    import difflib
    a = _chuan_hoa_so_sanh(van_xuoi)
    if not a:
        return 0.0, None
    cao_nhat, sku_giong = 0.0, None
    for sku, van_cu in DL.van_ban_cac_bai(ma_site, tru_sku=sku_hien_tai):
        b = _chuan_hoa_so_sanh(van_cu)
        if not b:
            continue
        # quick_ratio trước cho nhanh, chỉ tính ratio() chính xác khi có khả năng cao
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        if sm.quick_ratio() < NGUONG_TRUNG_VAN - 0.1:
            continue
        ty_le = sm.ratio()
        if ty_le > cao_nhat:
            cao_nhat, sku_giong = ty_le, sku
    return cao_nhat, sku_giong


# ============================================================ ghép HTML
class ThieuThiRong(dict):
    """Thiếu biến thì trả chuỗi rỗng, không nổ KeyError."""

    def __missing__(self, key):
        print(f'      (cảnh báo: mẫu dùng biến "{key}" nhưng không có dữ liệu)')
        return ''


def dien_bien(mau_chuoi, *nguon):
    gop = {}
    for n in nguon:
        gop.update({k: ('' if v is None else v) for k, v in n.items()})
    return mau_chuoi.format_map(ThieuThiRong(gop))


def bang_thong_so(row):
    tr = [f'<tr><th>{html.escape(nhan)}</th><td>{html.escape((row.get(k) or "").strip())}</td></tr>'
          for k, nhan in C.COT_BANG if (row.get(k) or '').strip()]
    if not tr:
        return '<p><em>Đang cập nhật thông số kỹ thuật.</em></p>'
    return '<table class="bg-specs"><tbody>\n' + '\n'.join(tr) + '\n</tbody></table>'


def _sap_xep_gia(r):
    """Xếp bảng giá theo số ngăn rồi tới cấp điện áp, cái nào không có thì đẩy xuống."""
    def so(v):
        m = re.search(r'(\d+(?:[.,]\d+)?)', str(v or ''))
        return float(m.group(1).replace(',', '.')) if m else 9999
    return (so(r.get('so_ngan')), so(r.get('cap_dien_ap')), str(r.get('ma_goc') or ''))


def bang_gia(row, tat_ca, site):
    """Bảng giá liệt kê các cấu hình cùng dòng, cùng cấp điện áp."""
    anh_em = [r for r in tat_ca
              if all(r.get(k) == row.get(k) for k in C.COT_GOM_BANG_GIA)
              and (r.get('gia_tham_khao') or '').strip()]
    if not anh_em:
        if not (row.get('gia_tham_khao') or '').strip():
            return ('<p>Giá bán thay đổi theo thời điểm và cấu hình. Vui lòng gọi '
                    f'<a href="tel:{site["hotline"]}">{site["hotline"]}</a> '
                    'để nhận báo giá chính thức.</p>')
        anh_em = [row]
    if all(r.get('sku') != row.get('sku') for r in anh_em):
        anh_em = anh_em + [row]

    anh_em = sorted(anh_em, key=_sap_xep_gia)
    th = ''.join(f'<th>{html.escape(n)}</th>' for _, n in C.COT_GIA)
    dong = []
    for i, r in enumerate(anh_em, 1):
        tds = ''.join(f'<td>{html.escape((r.get(k) or "").strip())}</td>' for k, _ in C.COT_GIA)
        dam = ' class="bg-hien-tai"' if r.get('sku') == row.get('sku') else ''
        dong.append(f'<tr{dam}><td>{i}</td>{tds}</tr>')
    return ('<table class="bg-price"><thead><tr><th>STT</th>' + th + '</tr></thead><tbody>\n'
            + '\n'.join(dong) + '\n</tbody></table>\n' + dien_bien(P.LUU_Y_GIA, site))


def khoi_phu_kien(row):
    pk = [x.strip() for x in (row.get('phu_kien_di_kem') or '').split(';') if x.strip()]
    if not pk:
        return ''
    li = '\n'.join(f'<li>{html.escape(x)}</li>' for x in pk)
    return f'<p><strong>Phụ kiện đi kèm khi giao hàng:</strong></p>\n<ul>\n{li}\n</ul>'


def anh_cua_san_pham(row, ma_site=None, tai_len=False):
    """Gộp ảnh từ 2 nguồn: link trong dữ liệu, và file trong thư mục anh/.

    tai_len=True (khi thật sự đăng bài): file trong máy được tải lên thư viện
    WordPress và dùng URL thật. Không có bước này thì HTML chứa file:///C:/...
    và ảnh sẽ vỡ hết trên web.
    """
    ds = []
    for i in (1, 2, 3):
        u = (row.get(f'anh_{i}_url') or '').strip()
        if u:
            ds.append((u, (row.get(f'anh_{i}_caption') or row.get('ten_san_pham', '')).strip()))
    for f in DL.gan_anh(row):
        u = None
        if tai_len and ma_site:
            try:
                u = _url_anh_tren_wp(ma_site, f)
            except Exception as e:
                print(f'      (không tải được ảnh {f.name}: {str(e)[:80]})')
                continue
        else:
            u = f.as_uri()
        if u and all(u != x[0] for x in ds):
            ds.append((u, row.get('ten_san_pham', '')))
    return ds[:3]


def khoi_anh(ds_anh, so_luong, bat_dau=1):
    out = []
    for i in range(bat_dau, min(bat_dau + so_luong, len(ds_anh) + 1)):
        u, cap = ds_anh[i - 1]
        out.append(f'<figure><img src="{html.escape(u)}" alt="{html.escape(cap)}" '
                   f'loading="lazy"><figcaption><em>{html.escape(cap)}</em></figcaption></figure>')
    return '\n'.join(out)


def khoi_lien_quan(row, tat_ca, base_url='', toi_da=20):
    """Liên kết nội bộ dày, chia 3 nhóm: cùng cấu hình, cùng dòng, cùng hãng."""
    def nhan(r):
        return r.get('series') or r.get('dong_san_pham') or ''

    sku, ngan = row.get('sku'), row.get('so_ngan')
    khac = [r for r in tat_ca if r.get('sku') != sku and r.get('slug')]
    g1 = [r for r in khac if nhan(r) == nhan(row) and ngan and r.get('so_ngan') == ngan]
    da_dung = {r['sku'] for r in g1}
    g2 = [r for r in khac if nhan(r) == nhan(row) and r['sku'] not in da_dung]
    da_dung |= {r['sku'] for r in g2}
    g3 = [r for r in khac if r.get('hang') == row.get('hang') and r['sku'] not in da_dung]

    nhom = [(f'Cùng cấu hình {ngan} ngăn' if ngan else 'Sản phẩm cùng loại', g1[:8]),
            (f'Khác trong dòng {nhan(row)}', g2[:8]),
            (f'Dòng khác của {row.get("hang", "")}'.strip(), g3[:6])]
    ra, dem = [], 0
    for tieu_de, ds in nhom:
        if not ds or dem >= toi_da:
            continue
        ds = ds[:toi_da - dem]
        dem += len(ds)
        li = '\n'.join(
            f'<li><a href="{base_url}/{r["slug"]}/">{html.escape(r["ten_san_pham"])}</a></li>'
            for r in ds)
        ra.append(f'<h3>{html.escape(tieu_de)}</h3>\n<ul class="bg-lienquan">\n{li}\n</ul>')
    return ('<h2>Sản phẩm liên quan</h2>\n' + '\n'.join(ra)) if ra else ''


def dung_bai(row, data, tat_ca, site, base_url='', ds_anh=None):
    if ds_anh is None:
        ds_anh = []
    faq = '\n'.join(f'<h3>{html.escape(q["q"])}</h3>\n<p>{q["a"]}</p>'
                    for q in data.get('faq', []) if q.get('q'))
    khoi = {
        'ten_goi_khac': data.get('ten_goi_khac_html', ''),
        'intro': data.get('intro_html', ''),
        'cau_tao': data.get('cau_tao_html', ''),
        'ung_dung': data.get('ung_dung_html', ''),
        'chon_mua': data.get('chon_mua_html', ''),
        'ket_luan': data.get('ket_luan_html', ''),
        'faq': faq,
        'anh_chinh': khoi_anh(ds_anh, 1, 1),
        'anh_phu': khoi_anh(ds_anh, 2, 2),
        'ten_san_pham': html.escape(row['ten_san_pham']),
        'bang_gia': bang_gia(row, tat_ca, site),
        'bang_thong_so': bang_thong_so(row),
        'khoi_phu_kien': khoi_phu_kien(row),
        'khoi_lien_quan': khoi_lien_quan(row, tat_ca, base_url),
    }
    for i in range(3):
        tieu_de = dien_bien(P.CTA_TIEU_DE[i % len(P.CTA_TIEU_DE)], row)
        khoi[f'khoi_cta_{i + 1}'] = dien_bien(P.CTA, site, {'tieu_de_cta': tieu_de})
    # chấp nhận cả tên có đuôi _html lẫn không, khỏi lệch tên biến trong prompts.py
    khoi.update({k + '_html': v for k, v in list(khoi.items())})
    return re.sub(r'\n{3,}', '\n\n', dien_bien(P.HTML, khoi))


# ============================================================ gọi AI
def dung_prompt(row, mau_key):
    mau = P.MAU[mau_key]
    co = [(nhan, row[k]) for k, nhan in C.COT_BANG if (row.get(k) or '').strip()]
    thieu = [nhan for k, nhan in C.COT_BANG if not (row.get(k) or '').strip()]
    du_lieu = '\n'.join(f'- {nhan}: {v}' for nhan, v in co)
    if row.get('cau_hinh_goc'):
        du_lieu += f"\n- Cấu hình đầy đủ theo catalogue: {row['cau_hinh_goc']}"

    kt = DL.kien_thuc_thanh_chu(
        DL.nap_kien_thuc(row.get('series') or row.get('dong_san_pham'), row.get('hang')))
    if kt:
        du_lieu += ('\n\nKIẾN THỨC CHUNG VỀ DÒNG SẢN PHẨM (đã đối chiếu tài liệu, dùng để '
                    'giải thích, NHƯNG KHÔNG được biến thành thông số riêng của model này):\n'
                    + kt)
    if thieu:
        du_lieu += ('\n\nDỮ LIỆU KHÔNG CÓ, TUYỆT ĐỐI KHÔNG ĐƯỢC NHẮC TỚI VÀ KHÔNG ĐƯỢC '
                    'SUY ĐOÁN:\n' + ', '.join(thieu))

    return f"""DỮ LIỆU SẢN PHẨM (chỉ được dùng đúng những gì ở đây):
{du_lieu}

TÊN SẢN PHẨM: {row['ten_san_pham']}
LOẠI BÀI: {mau['ten']}
GÓC NHÌN NGƯỜI ĐỌC: {mau['goc_nhin']}

{dien_bien(P.JSON_SPEC, mau)}"""


def dung_system(site):
    return dien_bien(P.SYSTEM, site,
                     {'hang_liet_ke': ', '.join(site.get('hang_duoc_nhac', [])) or 'không có'})


def go_json(raw):
    goc = raw
    raw = re.sub(r'^```(?:json)?|```$', '', (raw or '').strip(), flags=re.M).strip()
    i, j = raw.find('{'), raw.rfind('}')
    if i >= 0 and j > i:
        raw = raw[i:j + 1]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        if not goc.strip():
            raise RuntimeError('AI trả về rỗng. Thường do model bị chặn hoặc hết lượt. '
                               'Đổi MODEL_GEMINI sang model khác.')
        raise RuntimeError(
            f'AI trả về JSON hỏng ({e}). Thường do bài quá dài bị cắt giữa chừng. '
            f'Cách xử lý: giảm tong_tu trong prompts.py, hoặc đổi model khác. '
            f'Đầu ra nhận được: {goc[:200]}...')


def doc_429(r):
    """Bóc phản hồi 429 của Google: hết lượt NGÀY hay chỉ bị chặn tốc độ PHÚT."""
    msg, cho, loai = '', None, 'PHUT'
    try:
        err = r.json().get('error', {})
        msg = err.get('message', '')
        for d in err.get('details', []):
            t = d.get('@type', '')
            if 'QuotaFailure' in t:
                for v in d.get('violations', []):
                    if 'PerDay' in (v.get('quotaId', '') + ' ' + v.get('quotaMetric', '')):
                        loai = 'NGAY'
                    msg = msg or v.get('quotaId', '')
            if 'RetryInfo' in t:
                m = re.match(r'(\d+(?:\.\d+)?)s', str(d.get('retryDelay', '')))
                if m:
                    cho = float(m.group(1)) + 2
    except Exception:
        msg = r.text[:200]
    if 'per day' in msg.lower() or 'PerDay' in msg:
        loai = 'NGAY'
    return loai, msg or 'không rõ lý do', cho


class Usage:
    def __init__(self, i=0, o=0):
        self.input_tokens, self.output_tokens = i, o


def goi_gemini(row, mau_key, site):
    import requests
    key = os.environ.get('GOOGLE_API_KEY')
    if not key:
        raise SystemExit('Thiếu GOOGLE_API_KEY trong cau-hinh.env. '
                         'Lấy miễn phí ở aistudio.google.com > Get API key')
    he_thong, nguoi_dung = dung_system(site), dung_prompt(row, mau_key)
    la_gemma = 'gemma' in MODEL_GEMINI.lower()
    # Gemma không có thinking, khỏi tốn 1 lượt gọi API đi tra.
    nghi = False if la_gemma else _co_suy_nghi_ngam(MODEL_GEMINI, key)
    cfg = {'temperature': 0.8, 'maxOutputTokens': MAX_TOKENS_SUY_NGHI if nghi else MAX_TOKENS}
    if nghi:
        # "low" là mức Google khuyên dùng mặc định cho việc viết/tool-calling,
        # đủ chất lượng mà không ăn hết ngân sách vào suy nghĩ.
        cfg['thinkingConfig'] = {'thinkingLevel': 'low'}
    if la_gemma:
        # Dòng Gemma không nhận system_instruction và không ép được JSON.
        body = {'contents': [{'role': 'user',
                              'parts': [{'text': he_thong + '\n\n' + nguoi_dung}]}],
                'generationConfig': cfg}
    else:
        cfg['responseMimeType'] = 'application/json'
        body = {'system_instruction': {'parts': [{'text': he_thong}]},
                'contents': [{'role': 'user', 'parts': [{'text': nguoi_dung}]}],
                'generationConfig': cfg}

    url = f'{GEMINI_URL}/models/{MODEL_GEMINI}:generateContent?key={key}'
    da_bo_thinking = False
    for lan in range(5):
        r = requests.post(url, json=body, timeout=120)
        if r.status_code == 400 and not da_bo_thinking and 'thinkingConfig' in body['generationConfig']:
            # Phòng khi field "thinking" API báo có nhưng model thực tế từ chối
            # tham số này (model cũ, hoặc field chưa chính xác cho model đó).
            try:
                msg = r.json().get('error', {}).get('message', '')
            except Exception:
                msg = ''
            if 'thinking' in msg.lower():
                print(f'      (model từ chối thinkingConfig, bỏ đi thử lại: {msg[:90]})')
                body['generationConfig'].pop('thinkingConfig', None)
                body['generationConfig']['maxOutputTokens'] = MAX_TOKENS
                da_bo_thinking = True
                continue
        if r.status_code == 429:
            loai, msg, cho_google = doc_429(r)
            if loai == 'NGAY':
                raise SystemExit(
                    f'HẾT LƯỢT MIỄN PHÍ TRONG NGÀY của model "{MODEL_GEMINI}".\n'
                    f'   Google nói: {msg}\n'
                    f'   Ba cách xử lý:\n'
                    f'     1. Đổi model khác, mỗi model một hạn mức riêng. '
                    f'Bấm "Dò model chạy được" ở tab Cấu hình.\n'
                    f'     2. Mai chạy tiếp, hạn mức reset khoảng 14-15h giờ Việt Nam.\n'
                    f'     3. Tạo key mới bằng tài khoản Google khác.')
            cho = cho_google or min(20 * (lan + 1), 65)
            print(f'      (chặn tốc độ, chờ {cho:.0f}s rồi thử lại. Google: {msg[:90]})')
            time.sleep(cho)
            continue
        if r.status_code == 404:
            try:
                tb = r.json().get('error', {}).get('message', r.text[:300])
            except Exception:
                tb = r.text[:300]
            raise SystemExit(f'Model "{MODEL_GEMINI}" gọi không được (404).\n'
                             f'   Google nói: {tb}\n'
                             f'   => Bấm "Dò model chạy được" ở tab Cấu hình.')
        if r.status_code >= 300:
            raise RuntimeError(f'Gemini {r.status_code}: {r.text[:300]}')

        j = r.json()
        cands = j.get('candidates') or []
        if not cands:
            raise RuntimeError(f'Gemini không trả nội dung. Phản hồi: {str(j)[:250]}')
        c0 = cands[0]
        if c0.get('finishReason') in ('SAFETY', 'RECITATION', 'BLOCKLIST'):
            raise RuntimeError(f'Gemini chặn bài này (lý do {c0["finishReason"]}). Bỏ qua.')
        if c0.get('finishReason') == 'MAX_TOKENS':
            raise RuntimeError('Bài bị cắt vì vượt giới hạn token. '
                               'Giảm tong_tu trong prompts.py hoặc tăng MAX_TOKENS.')
        txt = ''.join(p.get('text', '') for p in c0.get('content', {}).get('parts', []))
        um = j.get('usageMetadata', {})
        return go_json(txt), Usage(um.get('promptTokenCount', 0),
                                   um.get('candidatesTokenCount', 0))
    raise RuntimeError('Thử lại 5 lần vẫn bị chặn tốc độ. Tăng thời gian nghỉ lên 30-60 giây, '
                       'hoặc đổi model khác.')


def goi_claude(row, mau_key, site, client):
    resp = client.messages.create(
        model=MODEL_CLAUDE, max_tokens=MAX_TOKENS,
        system=[{'type': 'text', 'text': dung_system(site),
                 'cache_control': {'type': 'ephemeral'}}],
        messages=[{'role': 'user', 'content': dung_prompt(row, mau_key)}])
    return go_json(''.join(b.text for b in resp.content if b.type == 'text')), resp.usage


def goi_ai(row, mau_key, site, client=None):
    if NHA_CUNG_CAP == 'claude':
        return goi_claude(row, mau_key, site, client)
    return goi_gemini(row, mau_key, site)


def tao_client():
    """Chỉ Claude mới cần client. Gemini gọi thẳng HTTP."""
    if NHA_CUNG_CAP != 'claude':
        return None
    import anthropic
    return anthropic.Anthropic()


# ============================================================ WordPress
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')   # host VN hay chặn UA của requests
HEADERS = {'User-Agent': UA, 'Accept': 'application/json',
           'Content-Type': 'application/json; charset=utf-8'}


def thong_tin_wp(ma_site):
    pre = f'WP_{ma_site.upper()}'
    url, user, pw = (os.environ.get(f'{pre}_URL'), os.environ.get(f'{pre}_USER'),
                     os.environ.get(f'{pre}_APP_PW'))
    if not all([url, user, pw]):
        raise SystemExit(f'Thiếu {pre}_URL / {pre}_USER / {pre}_APP_PW trong cau-hinh.env')
    return url.rstrip('/'), user, pw


def _auth(ma_site):
    from requests.auth import HTTPBasicAuth
    url, user, pw = thong_tin_wp(ma_site)
    return url, HTTPBasicAuth(user, pw)


def tim_bai_theo_slug(ma_site, slug):
    """Trả post id nếu WordPress đã có bài dùng slug này (để cập nhật, không đẻ bài -2).

    KHÔNG nuốt lỗi mạng ở đây. Trước đây bắt Exception rồi trả None, nghĩa là
    lỗi mạng bị hiểu nhầm thành "chưa có bài" -> tạo bài mới -> đẻ slug -2 ngay
    trên chính những kết nối chập chờn dễ lỗi nhất. Lỗi thì để nơi gọi tự quyết.
    """
    import requests
    url, auth = _auth(ma_site)
    r = requests.get(f'{url}/wp-json/wp/v2/posts', params={'slug': slug, 'status': 'any'},
                     auth=auth, headers={'User-Agent': UA}, timeout=45)
    if r.status_code >= 300:
        raise RuntimeError(f'Kiểm tra slug lỗi {r.status_code}: {r.text[:200]}')
    d = r.json()
    return d[0].get('id') if isinstance(d, list) and d else None


def tim_san_pham_woo_theo_sku(ma_site, sku, trang_thai='any'):
    """Ver 4.6 — trả product id nếu WooCommerce đã có sản phẩm dùng SKU này
    (để cập nhật, không đẻ sản phẩm trùng). Cùng kỷ luật với
    tim_bai_theo_slug(): KHÔNG nuốt lỗi mạng — lỗi thì để nơi gọi tự quyết,
    không tự coi là 'chưa có sản phẩm' rồi tạo mới. SKU dùng làm khoá tra
    thay vì slug vì WooCommerce REST API hỗ trợ lọc chính xác theo `sku`,
    đáng tin hơn slug (sản phẩm có thể trùng slug do WordPress tự thêm hậu
    tố, nhưng SKU là mã hàng thật, duy nhất theo thiết kế MASTER).

    Ver 4.9 — BUG THẬT đã vá: tài liệu WooCommerce REST API v3 ghi rõ tham
    số `status` mặc định là 'publish' — nghĩa là trước đây hàm này CHỈ tìm
    trong sản phẩm đã publish, bỏ sót hoàn toàn sản phẩm ở trạng thái
    'draft' (chính là trạng thái MỌI sản phẩm tool này tạo ra, vì luôn ép
    cứng draft) — tự tool tạo bài xong không tìm lại được chính bài mình
    vừa tạo. Thêm `status='any'` để bao trùm draft/publish/pending/private.

    LƯU Ý: 'any' theo đúng ngữ nghĩa WP_Query KHÔNG bao gồm 'trash' (hành
    vi lõi WordPress, không phải chọn riêng của tool này) — sản phẩm đã bị
    xoá vào Thùng rác vẫn PHẢI tra riêng bằng trang_thai='trash' nếu cần
    (xem `_kiem_tra_sku_trong_thung_rac`)."""
    import requests
    url, auth = _auth(ma_site)
    r = requests.get(f'{url}/wp-json/wc/v3/products', params={'sku': sku, 'status': trang_thai},
                     auth=auth, headers={'User-Agent': UA}, timeout=45)
    if r.status_code >= 300:
        raise RuntimeError(f'Kiểm tra SKU WooCommerce lỗi {r.status_code}: {r.text[:200]}')
    d = r.json()
    return d[0].get('id') if isinstance(d, list) and d else None


def tim_san_pham_woo_theo_slug(ma_site, slug, trang_thai='any'):
    """Ver 4.6 — dự phòng khi sản phẩm không có SKU (hiếm, nhưng an toàn
    hơn là bỏ qua kiểm tra hoàn toàn). Cùng kỷ luật không nuốt lỗi mạng.
    Ver 4.9 — cùng vá `status='any'` như tim_san_pham_woo_theo_sku()."""
    import requests
    url, auth = _auth(ma_site)
    r = requests.get(f'{url}/wp-json/wc/v3/products', params={'slug': slug, 'status': trang_thai},
                     auth=auth, headers={'User-Agent': UA}, timeout=45)
    if r.status_code >= 300:
        raise RuntimeError(f'Kiểm tra slug WooCommerce lỗi {r.status_code}: {r.text[:200]}')
    d = r.json()
    return d[0].get('id') if isinstance(d, list) and d else None


def _url_anh_tren_wp(ma_site, duong_dan, tra_media_id=False):
    """Tải ảnh lên Media; cache chỉ hợp lệ khi cùng site + path + content hash."""
    import hashlib
    import mimetypes
    import requests
    p = Path(duong_dan)
    du_lieu = p.read_bytes()
    file_hash = hashlib.sha256(du_lieu).hexdigest()
    da_co = DL.nho_anh_wp(duong_dan, ma_site, file_hash=file_hash)
    if da_co:
        return da_co if tra_media_id else da_co[1]
    url, auth = _auth(ma_site)
    mime = mimetypes.guess_type(p.name)[0] or 'image/jpeg'
    # Ver 4.4.1.6b — đi qua tầng chung wp_http. TRƯỚC bản này đây là đường
    # KHÔNG có retry và cắt log ở 200 ký tự, trong khi nó mới là đường bị
    # gọi nhiều nhất (tab Ảnh 2 chỗ, giao-dien 1 chỗ, autopost 1 chỗ).
    # 4.4.1.6 thêm retry nhầm vào ai_wp_adapter.upload_anh_media — hàm chỉ
    # có 1 caller — nên 403 thực tế không hưởng gì. Đây là chỗ sửa đúng.
    import wp_http as WH
    r, loi = WH.post_media(url, auth, du_lieu, p.name, mime,
                           headers_goc={'User-Agent': UA}, timeout=180,
                           ghi_log=globals().get('_ghi_log_anh'))
    if r is None:
        # Giữ NGUYÊN kiểu ngoại lệ cũ: 4 caller đang bắt RuntimeError.
        # Đổi sang trả dict ở đây là phá cả 4 chỗ cùng lúc.
        raise RuntimeError('Tải ảnh lỗi: %s\n[chi tiết] %s'
                           % (loi.get('loi'), loi.get('chi_tiet', '')))
    j = r.json()
    media_id, media_url = j.get('id'), j.get('source_url', '')
    DL.luu_anh_wp(duong_dan, ma_site, media_id, media_url, file_hash=file_hash)
    return (media_id, media_url) if tra_media_id else media_url


def dang_wp(ma_site, sku, mau_key, title, slug, content, excerpt, status):
    """Đăng hoặc cập nhật bài, tránh đẻ trùng khi mạng chập chờn. Trả (link, wp_id).

    Thứ tự xác định bài đã tồn tại chưa, tin cậy giảm dần:
      1. wp_id đã lưu trong kho từ lần đăng trước cho đúng (site, sku, mẫu) này.
         Không phụ thuộc mạng ngay lúc này nên đáng tin nhất.
      2. Hỏi WordPress theo slug — chỉ khi (1) không có. Hỏi lỗi thì DỪNG hẳn,
         không đoán "chưa có bài" để tránh đẻ trùng.
    Sau một lần POST bị mất kết nối (không rõ WordPress đã tạo bài chưa), hỏi
    lại slug trước khi POST lần nữa, không bao giờ POST mù hai lần liên tiếp.
    """
    import requests
    url, auth = _auth(ma_site)
    goi = {'title': title, 'slug': slug, 'content': content, 'excerpt': excerpt, 'status': status}

    da_co = DL.wp_id_da_luu(ma_site, sku, mau_key)
    if da_co is None:
        da_co = tim_bai_theo_slug(ma_site, slug)   # lỗi thì raise thẳng, dừng ở đây

    loi_cuoi = ''
    for lan in range(3):
        api = f'{url}/wp-json/wp/v2/posts/{da_co}' if da_co else f'{url}/wp-json/wp/v2/posts'
        mat_ket_noi = False
        try:
            r = requests.post(api, auth=auth, headers=HEADERS,
                              data=json.dumps(goi, ensure_ascii=False).encode('utf-8'),
                              timeout=90)
        except Exception as e:
            loi_cuoi, r, mat_ket_noi = f'{type(e).__name__}: {e}', None, True
        if r is not None and r.status_code < 300:
            j = r.json()
            return j.get('link', '') + ('   (cập nhật bài đã có)' if da_co else ''), j.get('id')
        if r is not None and 400 <= r.status_code < 500:
            raise RuntimeError(f'WordPress trả về {r.status_code}: {r.text[:300]}')
        if r is not None:
            loi_cuoi = f'HTTP {r.status_code}: {r.text[:150]}'
        if lan < 2:
            if mat_ket_noi:
                # không rõ WordPress đã nhận POST vừa rồi chưa -> hỏi lại slug
                # trước khi thử tiếp, tuyệt đối không POST mù thêm lần nào.
                print('      (mất kết nối, kiểm tra lại WordPress trước khi thử tiếp...)')
                time.sleep(5)
                try:
                    kt = tim_bai_theo_slug(ma_site, slug)
                    if kt:
                        da_co = kt   # bài đã lên rồi, lần sau PUT cập nhật thay vì POST mới
                except Exception:
                    pass    # vẫn không hỏi được thì giữ nguyên da_co hiện có, không tệ hơn cũ
            else:
                print(f'      (web không nhận, thử lại lần {lan + 2} sau 5s...)')
                time.sleep(5)
    raise RuntimeError(
        f'Đăng thất bại sau 3 lần. {loi_cuoi}\n'
        f'      Gần như chắc chắn do tường lửa hoặc plugin bảo mật chặn bài có mã HTML.\n'
        f'      Chạy "Kiểm tra kết nối WordPress" ở tab 2 để biết chết ở khâu nào.')


# ============================================================ MỘT BÀI (dùng chung)
CHE_DO = ('thu', 'sinh', 'nhap', 'dang')

MAU_THU = {
    'meta_title': '[thử] meta title', 'meta_description': '[thử] meta description',
    'ten_goi_khac_html': '<p>[thử] cụm tên gọi khác</p>',
    'intro_html': '<p>[thử] đoạn mở bài</p>',
    'cau_tao_html': '<h3>[thử] Cấu tạo</h3><p>...</p>',
    'ung_dung_html': '<h3>[thử] Ứng dụng</h3><p>...</p>',
    'chon_mua_html': '<h3>[thử] Chọn mua</h3><p>...</p>',
    'faq': [{'q': '[thử] câu hỏi?', 'a': '...'}],
    'ket_luan_html': '<p>[thử] đoạn chốt</p>',
}


def sinh_mot_bai(row, ma_site, mau_key, tat_ca, che_do='sinh', client=None):
    """Sinh 1 bài từ đầu đến cuối. Giao diện và dòng lệnh đều gọi hàm này.

    Trả dict: trang_thai, sku, ghi_chu, link, file, usage.
    trang_thai: DA_DANG | DA_SINH | BI_CHAN
    """
    if che_do not in CHE_DO:
        raise ValueError(f'che_do phải là một trong {CHE_DO}')
    site = C.lay_site(ma_site)
    base_url = os.environ.get(f'WP_{ma_site.upper()}_URL', '').rstrip('/')
    dang_that = che_do in ('nhap', 'dang')

    if che_do == 'thu':
        data = dict(MAU_THU, h1=dien_bien(P.MAU[mau_key]['tieu_de'], row))
        usage = None
    else:
        data, usage = goi_ai(row, mau_key, site, client)

    van_xuoi = ' '.join(
        [data.get(k, '') for k in ('ten_goi_khac_html', 'intro_html', 'cau_tao_html',
                                   'ung_dung_html', 'chon_mua_html', 'ket_luan_html',
                                   'meta_title', 'meta_description')]
        + [q.get('q', '') + ' ' + q.get('a', '') for q in data.get('faq', [])])
    ro_ri = kiem_tra_ro_ri(van_xuoi, ma_site)
    bia, nhe = ([], []) if che_do == 'thu' else kiem_tra_bia(van_xuoi, row, tat_ca)
    bi_chan = bool(ro_ri or bia)

    # Trùng văn biên tập chỉ cảnh báo, không chặn — sản phẩm cùng dòng được phép
    # giống nhau ở thông số/cấu hình, đây chỉ canh phần AI tự viết (mở bài, ứng
    # dụng, FAQ...) bị lặp lại y chang giữa hai bài khác nhau.
    ty_le_trung, sku_trung = (0.0, None) if che_do == 'thu' or bi_chan \
        else kiem_tra_trung_van(van_xuoi, ma_site, row['sku'])

    ds_anh = anh_cua_san_pham(row, ma_site, tai_len=dang_that and not bi_chan)
    tieu_de = data.get('h1') or dien_bien(P.MAU[mau_key]['tieu_de'], row)
    slug = f"{row['slug']}-{mau_key.replace('_', '-')}"[:95]
    body = dung_bai(row, data, tat_ca, site, base_url, ds_anh)

    OUT_DIR.mkdir(exist_ok=True)
    f_out = OUT_DIR / f'{ma_site}__{slug}.html'
    f_out.write_text(f'<!-- meta_title: {data.get("meta_title", "")} -->\n'
                     f'<!-- meta_description: {data.get("meta_description", "")} -->\n'
                     f'<h1>{html.escape(tieu_de)}</h1>\n{body}', encoding='utf-8')

    link, wp_id, wp_tt = '', None, ''
    if bi_chan:
        trang_thai = 'BI_CHAN'
        ghi_chu = '; '.join((['lộ danh tính: ' + ', '.join(ro_ri)] if ro_ri else [])
                            + (['bịa số: ' + ', '.join(bia)] if bia else []))
    elif dang_that:
        wp_tt = 'draft' if che_do == 'nhap' else 'publish'
        link, wp_id = dang_wp(ma_site, row['sku'], mau_key, tieu_de, slug, body,
                              data.get('meta_description', ''), wp_tt)
        trang_thai, ghi_chu = 'DA_DANG', ''
    else:
        trang_thai, ghi_chu = 'DA_SINH', ''
    if nhe and not bi_chan:
        ghi_chu = (ghi_chu + ' | ' if ghi_chu else '') + 'nhắc số dòng khác: ' + ', '.join(nhe[:6])
    if ty_le_trung >= NGUONG_TRUNG_VAN:
        ghi_chu = (ghi_chu + ' | ' if ghi_chu else '') + \
            f'trùng văn {ty_le_trung * 100:.0f}% với {sku_trung}'

    # trạng thái từng chặng, để dashboard nhìn một dòng là biết chết ở đâu
    co, tong = C.cham_du_lieu(row)
    kt = 'CHAN' if bi_chan else ('CANH_BAO' if (nhe or ty_le_trung >= NGUONG_TRUNG_VAN) else 'DAT')
    chang = {'kiem_tra': kt,
             'wp_trang_thai': wp_tt,
             'so_tu': len(re.sub(r'<[^>]+>', ' ', van_xuoi).split()),
             'so_anh': len(ds_anh), 'du_lieu_day': f'{co}/{tong}',
             'danh_muc': row.get('danh_muc', '') or 'chung',
             'meta_title': data.get('meta_title', ''),
             'meta_description': data.get('meta_description', ''),
             'van_bien_tap': van_xuoi if not bi_chan else ''}

    DL.ghi_bai(ma_site, row['sku'], mau_key, slug, tieu_de, body,
               trang_thai, ghi_chu, wp_id, link, **chang)
    ghi_log(ma_site, mau_key, row['sku'], trang_thai, ghi_chu, link)
    return dict(chang, trang_thai=trang_thai, sku=row['sku'], ghi_chu=ghi_chu,
                link=link, file=f_out, usage=usage)


def ghi_log(ma_site, mau, sku, trang_thai, ghi_chu, link):
    moi = not LOG_PATH.exists() or LOG_PATH.stat().st_size == 0
    with open(LOG_PATH, 'a', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        if moi:
            w.writerow(['thoi_gian', 'site', 'mau', 'sku', 'trang_thai', 'ghi_chu', 'link'])
        w.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), ma_site, mau, sku,
                    trang_thai, ghi_chu, link])


def ghi_bai_loi(row, ma_site, mau_key, thong_diep):
    """Ghi bài LỖI vào cả log.csv lẫn SQLite.

    Trước đây lỗi chỉ vào log.csv, không vào bảng bai_viet, nên dashboard hiện
    "Chưa làm" cho SKU vừa nổ lỗi thay vì "Lỗi" — nhìn dashboard tưởng còn hàng
    để chạy tiếp, thật ra đang có bài đứng im chờ retry.
    """
    slug = f"{row.get('slug', row.get('sku', ''))}-{mau_key.replace('_', '-')}"[:95]
    co, tong = C.cham_du_lieu(row)
    DL.ghi_bai(ma_site, row.get('sku', ''), mau_key, slug,
               row.get('ten_san_pham', row.get('sku', '')), '', 'LOI', str(thong_diep)[:300],
               None, '', kiem_tra='', wp_trang_thai='', so_tu=0, so_anh=0,
               du_lieu_day=f'{co}/{tong}', danh_muc=row.get('danh_muc', '') or 'chung')
    ghi_log(ma_site, mau_key, row.get('sku', ''), 'LOI', str(thong_diep)[:200], '')


# ============================================================ nguồn dữ liệu
def doc_san_pham(danh_muc=None, ma_site=None, chi_da_chon=False):
    """Ưu tiên kho SQLite (do tab Nhập Excel ghi). Không có thì lùi về products.csv.

    danh_muc lọc theo ngành hàng. Không truyền thì lấy theo khai báo của site.
    chi_da_chon=True: chỉ lấy sản phẩm đang bấm chọn ở tab Sản phẩm.
    Mặc định là False vì kết quả hàm này còn dùng làm NGỮ CẢNH: danh sách trắng
    chống bịa số, gom bảng giá, dựng liên kết nội bộ. Sản phẩm chưa chọn viết vẫn
    phải có mặt ở đó, không thì bảng giá và liên kết related bị hụt. Việc lọc
    "chỉ sinh sản phẩm đã chọn" nằm ở chon_dong(), không nằm ở đây.
    QUAN TRỌNG: danh sách trả về vừa là nguồn sinh bài, vừa là danh sách trắng
    chống bịa số. Trộn cáp điện với tủ trung thế là bộ chặn yếu đi.
    """
    if danh_muc is None and ma_site:
        danh_muc = C.lay_site(ma_site).get('danh_muc') or None
    ds = DL.doc_san_pham_db(danh_muc, chi_lay_da_chon=chi_da_chon)
    if ds:
        return ds
    if danh_muc or chi_da_chon:      # đã lọc mà rỗng thì trả rỗng, không lùi về file dùng chung
        return []
    if not CSV_PATH.exists():
        return []
    with open(CSV_PATH, encoding='utf-8-sig') as f:
        return [r for r in csv.DictReader(f) if r.get('sku')]


def chon_dong(tat_ca, ma_site, mau_key, so=0, bo_qua=0, bo_da_lam=False, chi_da_chon=True):
    """Chọn các dòng sẽ thật sự sinh bài trong lượt chạy này.

    chi_da_chon=True (mặc định): bỏ những sản phẩm đang tắt ô chọn ở tab Sản phẩm.
    tat_ca vẫn giữ nguyên đầy đủ để làm ngữ cảnh (bảng giá, liên kết, chống bịa số).
    """
    ds = list(tat_ca)
    if chi_da_chon:
        ds = [r for r in ds if int(r.get('chon', 1) or 0) == 1]
    if bo_da_lam:
        da = DL.da_lam(ma_site, mau_key)
        ds = [r for r in ds if r['sku'] not in da]
    ds = ds[bo_qua:]
    return ds[:so] if so else ds


# ============================================================ công cụ dò
def _ung_vien_model(key):
    import requests
    r = requests.get(f'{GEMINI_URL}/models?key={key}&pageSize=200', timeout=60)
    r.raise_for_status()
    LOAI_BO = ('image', 'tts', 'robotics', 'embedding', 'aqa', 'lyria', 'veo',
               'computer-use', 'deep-research', 'nano-banana', 'antigravity', 'customtools')
    thong_tin = {}
    for m in r.json().get('models', []):
        ten = m['name'].replace('models/', '')
        if 'generateContent' not in m.get('supportedGenerationMethods', []):
            continue
        if any(x in ten.lower() for x in LOAI_BO):
            continue
        # dung lượng thật của model, lấy trực tiếp từ API, không phải đoán theo tên
        thong_tin[ten] = {'ten': ten,
                          'vao': m.get('inputTokenLimit', 0),
                          'ra': m.get('outputTokenLimit', 0),
                          'nghi': bool(m.get('thinking', False))}

    def diem(t):
        """Điểm càng thấp càng nên dùng."""
        m = re.search(r'gemini-(\d+(?:\.\d+)?)', t)
        d = -(float(m.group(1)) if m else 0) * 10     # bản mới ưu tiên
        if 'flash' in t: d -= 30                      # hạn mức miễn phí cao nhất
        if 'gemma' in t: d += 20                      # không ép được JSON, viết yếu
        if 'lite' in t: d += 8
        if 'preview' in t: d += 12
        if 'pro' in t: d += 25                        # hạn mức miễn phí rất thấp
        if re.search(r'-\d{3}$', t): d += 15          # bản đóng băng cũ kiểu -001
        return d

    return sorted(thong_tin.values(), key=lambda x: diem(x['ten']))


def thong_tin_model(ten, key=None):
    """Dung lượng của một model: input/output limit thật từ API, có bật thinking không."""
    key = key or os.environ.get('GOOGLE_API_KEY')
    for tt in _ung_vien_model(key):
        if tt['ten'] == ten:
            return tt
    return {'ten': ten, 'vao': 0, 'ra': 0, 'nghi': None}


def do_model():
    """Dò model Gemini bằng request thật, ưu tiên model đã chạy được lần trước.

    Ver 3.9 A2: mục tiêu của nút này là tìm NHANH một model dùng được, không
    quét hết catalogue Google mỗi lần. Model đã lưu trong cau-hinh.env được
    thử đầu tiên; nếu trả 200 thì dừng ngay và lưu lại. Model trả 404 được
    nhớ trong RAM để những lần dò sau của cùng phiên không thử lại. Mỗi probe
    có timeout riêng 12 giây để một model chết không giữ cả lượt dò quá lâu.
    """
    import requests
    key = os.environ.get('GOOGLE_API_KEY')
    if not key:
        raise SystemExit('Thiếu GOOGLE_API_KEY trong cau-hinh.env')
    ung_vien = [x for x in _ung_vien_model(key) if x['ten'] not in _MODEL_404_TRONG_PHIEN]

    # Model đã chứng minh chạy ở lượt trước đi trước hàng. Không bịa model mới:
    # chỉ ưu tiên nếu tên đó thật sự có trong danh sách API vừa trả về.
    da_nho = os.environ.get('MODEL_GEMINI', '').strip()
    if da_nho:
        ung_vien.sort(key=lambda x: (0 if x['ten'] == da_nho else 1))

    print(f'Thử gọi thật tối đa {len(ung_vien)} model (dừng khi có model chạy được).\n')
    chay_duoc = []
    tam_dung_duoc = []
    for tt in ung_vien:
        ten = tt['ten']
        body = {'contents': [{'role': 'user', 'parts': [{'text': 'Trả lời đúng 1 từ: ok'}]}],
                'generationConfig': {'maxOutputTokens': 2048}}
        dung_luong = (f"vào {tt['vao']:,} / ra {tt['ra']:,}"
                     + (' / có suy nghĩ ngầm' if tt['nghi'] else ''))
        try:
            rr = requests.post(f'{GEMINI_URL}/models/{ten}:generateContent?key={key}',
                               json=body, timeout=12)
        except Exception as e:
            print(f'   [LOI ] {ten:32} {str(e)[:50]}')
            continue
        if rr.status_code == 200:
            print(f'   [ OK ] {ten:32} {dung_luong}')
            chay_duoc.append(tt)
            C.luu_gemini(key, ten)
            break
        elif rr.status_code == 429:
            loai, _, _ = doc_429(rr)
            if loai == 'NGAY':
                print(f'   [HET ] {ten:32} hết lượt trong ngày')
            else:
                print(f'   [BAN ] {ten:32} chặn tốc độ, có thể dùng nếu chạy chậm')
                tam_dung_duoc.append(tt)
        elif rr.status_code == 404:
            _MODEL_404_TRONG_PHIEN.add(ten)
            try:
                msg = rr.json().get('error', {}).get('message', '')[:60]
            except Exception:
                msg = rr.text[:70]
            print(f'   [ 404] {ten:32} {msg}')
        else:
            try:
                msg = rr.json().get('error', {}).get('message', '')[:60]
            except Exception:
                msg = rr.text[:70]
            print(f'   [{rr.status_code:>4}] {ten:32} {msg}')

    if not chay_duoc and tam_dung_duoc:
        # Không có 200 nhưng có model chỉ bị rate-limit ngắn: giữ hành vi cũ là
        # coi model đó có khả năng dùng, nhưng KHÔNG ghi vào config như một
        # model đã xác nhận chạy thành công.
        chay_duoc.append(tam_dung_duoc[0])

    print()
    if chay_duoc:
        print('=> NÊN DÙNG:  MODEL_GEMINI=' + chay_duoc[0]['ten'])
    else:
        print('=> Không model nào chạy được. Nhiều khả năng key sai hoặc chưa bật API.')
    return chay_duoc

def kiem_tra_wp(ma_site, tat_ca):
    """Dò từng khâu để biết WordPress chết ở đâu."""
    import requests
    url, auth = _auth(ma_site)
    print(f'Kiểm tra {url}\n')

    def thu(ten, ham):
        try:
            r = ham()
            code = getattr(r, 'status_code', '?')
            print(f'   [{("OK  " if isinstance(code, int) and code < 300 else code):>4}] {ten}')
            return r
        except Exception as e:
            print(f'   [ X  ] {ten}  ->  {type(e).__name__}: {str(e)[:90]}')
            return None

    def ok(r):
        return r is not None and r.status_code < 300

    r1 = thu('1. Mở được trang chủ',
             lambda: requests.get(url, headers={'User-Agent': UA}, timeout=30))
    if r1 is None:
        print('\n=> Không vào được web. Kiểm tra lại địa chỉ, có http/https đúng chưa.')
        return
    r2 = thu('2. REST API còn sống (/wp-json)',
             lambda: requests.get(f'{url}/wp-json', headers={'User-Agent': UA}, timeout=30))
    if not ok(r2):
        print('\n=> REST API bị chặn. Nhờ bên quản trị tắt plugin bảo mật (Wordfence, '
              'iThemes, Really Simple SSL) hoặc bật lại REST API.')
        return
    r3 = thu('3. Đăng nhập bằng Application Password',
             lambda: requests.get(f'{url}/wp-json/wp/v2/users/me', auth=auth,
                                  headers={'User-Agent': UA}, timeout=30))
    if not ok(r3):
        print(f'\n=> Sai tài khoản hoặc Application Password. '
              f'Phản hồi: {getattr(r3, "text", "")[:200]}')
        return
    try:
        print(f'          đăng nhập với tên: {r3.json().get("name")}')
    except Exception:
        pass

    def post(noi_dung, tieu_de):
        return requests.post(
            f'{url}/wp-json/wp/v2/posts', auth=auth, headers=HEADERS,
            data=json.dumps({'title': tieu_de, 'content': noi_dung, 'status': 'draft'},
                            ensure_ascii=False).encode('utf-8'), timeout=90)

    ids = []
    r4 = thu('4. Đăng thử bài chữ thuần', lambda: post('Bai test.', 'TEST 1 autopost'))
    if ok(r4):
        ids.append(r4.json().get('id'))
    r5 = thu('5. Đăng thử bài có bảng và liên kết',
             lambda: post('<h2>Test</h2><table><tr><td>1</td></tr></table>'
                          '<p><a href="tel:0000000000">Goi</a></p>', 'TEST 2 autopost'))
    if ok(r5):
        ids.append(r5.json().get('id'))

    r6 = None
    if tat_ca:
        site = C.lay_site(ma_site)
        bai = dung_bai(tat_ca[0], dict(MAU_THU, h1='thử'), tat_ca, site)
        r6 = thu(f'6. Đăng thử bài đầy đủ ({len(bai):,} ký tự)',
                 lambda: post(bai, 'TEST 3 autopost bai day du'))
        if ok(r6):
            ids.append(r6.json().get('id'))

    print()
    if ok(r6):
        print('=> TẤT CẢ ĐỀU CHẠY. Bài test nằm ở mục Bản nháp, vào xoá đi.')
    elif ok(r4):
        print('=> Đăng chữ thuần thì được, đăng HTML thì chết.')
        print('   Nguyên nhân: ModSecurity hoặc plugin bảo mật chặn nội dung HTML.')
        print('   Cách xử lý, nói với bên quản trị web hoặc hosting:')
        print('     1. Tắt tạm plugin bảo mật (Wordfence, iThemes, All In One WP Security)')
        print('     2. Nhờ hosting tắt ModSecurity cho tên miền này')
        print('     3. Nếu qua Cloudflare: tắt WAF hoặc thêm luật bỏ qua /wp-json/')
    else:
        print('=> Không đăng được cả bài chữ thuần. REST API bị chặn ghi.')
        print('   Kiểm tra tài khoản có quyền Author trở lên không, và plugin bảo mật.')
    if ids:
        print(f'\n   Nhớ vào {url}/wp-admin/edit.php?post_status=draft xoá bài TEST: {ids}')


# ============================================================ dòng lệnh
def main():
    ap = argparse.ArgumentParser(description='Lotech autopost')
    ap.add_argument('--site', default='site1', help='khoá site trong cauhinh.py')
    ap.add_argument('--mau', help='mẫu bài, mặc định lấy theo site')
    ap.add_argument('--che-do', default='sinh', choices=CHE_DO)
    ap.add_argument('--so', type=int, default=0, help='số bài, 0 = tất cả')
    ap.add_argument('--bo-qua', type=int, default=0)
    ap.add_argument('--nghi', type=float, default=30, help='giây nghỉ giữa 2 bài')
    ap.add_argument('--tiep', action='store_true', help='bỏ qua sản phẩm đã sinh bài rồi')
    ap.add_argument('--danh-muc', help='lọc ngành hàng, mặc định theo khai báo site')
    ap.add_argument('--do-model', action='store_true')
    ap.add_argument('--kiem-tra-wp', action='store_true')
    a = ap.parse_args()

    if a.do_model:
        return do_model()
    if a.kiem_tra_wp:
        return kiem_tra_wp(a.site, doc_san_pham(a.danh_muc, a.site))

    site = C.lay_site(a.site)
    mau_key = a.mau or site.get('mau_mac_dinh', 'bao_gia')
    if mau_key not in P.MAU:
        raise SystemExit(f'Không có mẫu "{mau_key}". Đang có: {", ".join(P.MAU)}')

    tat_ca = doc_san_pham(a.danh_muc, a.site)
    if not tat_ca:
        raise SystemExit('Kho dữ liệu trống. Mở phần mềm, tab 0, nhập file Excel trước.')
    rows = chon_dong(tat_ca, a.site, mau_key, a.so, a.bo_qua, a.tiep)
    if not rows:
        raise SystemExit('Không có sản phẩm nào trong khoảng đã chọn.')

    print(f'Site {a.site} ({site["ten"]}) | mẫu {P.MAU[mau_key]["ten"]} | '
          f'{len(rows)} bài | chế độ {a.che_do}')
    if a.che_do != 'thu':
        print(f'AI: {NHA_CUNG_CAP} '
              f'({MODEL_CLAUDE if NHA_CUNG_CAP == "claude" else MODEL_GEMINI})')

    client = tao_client() if a.che_do != 'thu' else None
    dem = {'DA_DANG': 0, 'DA_SINH': 0, 'BI_CHAN': 0, 'LOI': 0}
    tok_in = tok_out = 0

    for i, row in enumerate(rows, 1):
        try:
            kq = sinh_mot_bai(row, a.site, mau_key, tat_ca, a.che_do, client)
            dem[kq['trang_thai']] += 1
            if kq['usage']:
                tok_in += kq['usage'].input_tokens
                tok_out += kq['usage'].output_tokens
            gc = f'  ({kq["ghi_chu"]})' if kq['ghi_chu'] else ''
            print(f'  [{i}/{len(rows)}] {kq["trang_thai"]} {kq["sku"]}{gc} '
                  f'{kq["link"]}'.rstrip())
        except SystemExit as e:
            print(str(e))
            break
        except Exception as e:
            dem['LOI'] += 1
            print(f'  [{i}/{len(rows)}] LỖI {row["sku"]}: {e}')
            ghi_bai_loi(row, a.site, mau_key, e)
        if i < len(rows) and a.che_do != 'thu' and a.nghi:
            time.sleep(a.nghi + random.uniform(0, a.nghi * 0.4))

    print(f'\nXong. Đăng {dem["DA_DANG"]} | sinh {dem["DA_SINH"]} | '
          f'chặn {dem["BI_CHAN"]} | lỗi {dem["LOI"]}')
    if tok_in or tok_out:
        if NHA_CUNG_CAP == 'claude':
            usd = tok_in / 1e6 * 1.0 + tok_out / 1e6 * 5.0
            print(f'Token vào {tok_in:,} | ra {tok_out:,} | ước {usd:.3f} USD, chưa trừ cache')
        else:
            print(f'Token vào {tok_in:,} | ra {tok_out:,} | chi phí 0 đồng (bản miễn phí)')
    print(f'File HTML nằm ở: {OUT_DIR}')


if __name__ == '__main__':
    sys.exit(main() and 0)
