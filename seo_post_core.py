# -*- coding: utf-8 -*-
"""Ver 5.5 — LÕI module SEO POST.

Làm 5 việc, theo đúng thứ tự luồng:
    1. nap_tu_khoa_*   : nhận từ khoá (gõ tay / dán list / import GSC)
    2. gop_sku         : N record -> 1 dict dữ liệu đã gộp thành DẢI
    3. sinh_bai        : gọi Gemini qua transport có sẵn của ai_wp_adapter
    4. render_bai      : lắp HTML (hero + AI đã sanitize + bảng + CTA + FAQ)
    5. dang_bai        : đẩy lên WP dạng post HOẶC product

KHÔNG tự viết lại thứ đã có:
    - sanitize HTML  -> render_phase2.sanitize_html()
    - schema Gemini  -> ai_wp_adapter._sang_gemini_schema()
    - HTTP + 429     -> requests, cùng cách goi_ai_that() đang làm
    - đăng WP/Woo    -> ai_wp_adapter.dang_wp_that() / dang_woo_that()
"""
import html as _html
import json
import os
import re
import time
import unicodedata
from datetime import datetime

import prompts_seo_post as P
import db_seo_post as DB


# ============================================================ 1. nạp từ khoá

def nap_tu_khoa_go_tay(cum):
    """1 cụm từ khoá gõ tay -> list 1 phần tử."""
    cum = (cum or '').strip()
    return [{'tu_khoa': cum, 'impression': None, 'diem': None}] if cum else []


def nap_tu_khoa_dan_list(khoi_text):
    """Dán nhiều dòng. Mỗi dòng 1 từ khoá. Bỏ dòng trống và trùng lặp,
    giữ nguyên thứ tự người dán (đó là thứ tự ưu tiên của họ)."""
    da_co, ra = set(), []
    for dong in (khoi_text or '').splitlines():
        kw = dong.strip().strip('-•*').strip()
        if not kw or kw.lower() in da_co:
            continue
        da_co.add(kw.lower())
        ra.append({'tu_khoa': kw, 'impression': None, 'diem': None})
    return ra


def nap_tu_khoa_gsc(duong_dan_file, nguong_impression=50):
    """Đọc thẳng 1 file .xlsx export từ Google Search Console.

    GSC hard-cap export ở 1.000 dòng — không có cách nào lấy hơn qua giao
    diện. Không cố vòng, chỉ báo cho người dùng biết khi chạm trần.
    """
    try:
        import pandas as pd
    except ImportError:
        raise RuntimeError('Cần pandas để đọc file GSC. Chạy: pip install pandas openpyxl')

    q = pd.read_excel(duong_dan_file, sheet_name='Queries')
    q.columns = [str(c).strip() for c in q.columns]
    cot_kw = q.columns[0]
    ra = []
    for _, r in q.iterrows():
        impr = float(r.get('Impressions', 0) or 0)
        if impr < nguong_impression:
            continue
        ra.append({
            'tu_khoa': str(r[cot_kw]).strip(),
            'impression': impr,
            'clicks': float(r.get('Clicks', 0) or 0),
            'ctr': float(r.get('CTR', 0) or 0),
            'position': float(r.get('Position', 0) or 0),
            'diem': None,
        })
    cham_tran = len(q) >= 1000
    return ra, cham_tran


def de_xuat(danh_sach_kw):
    """Gắn content type + tiêu đề gợi ý cho từng từ khoá.

    Đây là bước "giống ChatGPT": đưa từ khoá vào, tool nói nên viết dạng gì.
    Người dùng vẫn sửa lại được — đây là GỢI Ý, không phải quyết định.
    """
    ra = []
    for m in danh_sach_kw:
        kw = m['tu_khoa']
        tid, tin_cay, ly_do = P.doan_content_type(kw)
        ra.append({
            **m,
            'content_type': tid,
            'nhan_type': P.CONTENT_TYPE[tid]['nhan'],
            'do_tin_cay': tin_cay,
            'ly_do': ly_do,
            'can_sku': P.can_sku(tid),
            'tieu_de_goi_y': goi_y_tieu_de(tid, kw),
        })
    return ra


def goi_y_tieu_de(content_type_id, tu_khoa, so_sku=None):
    chu_de = re.sub(
        r'^(báo giá|bảng giá|giá|catalogue|catalog|top \d+|so sánh|phân biệt|'
        r'cách chọn|cách tính|tìm hiểu)\s*', '', str(tu_khoa).strip(), flags=re.IGNORECASE)
    chu_de = re.sub(r'\s*(là gì|pdf|mới nhất|\d{4})\s*$', '', chu_de, flags=re.IGNORECASE).strip()
    chu_de = chu_de or str(tu_khoa)
    nay = datetime.now()
    mau = P.mau_tieu_de(content_type_id)[0]
    return (mau.replace('{chu_de}', chu_de)
               .replace('{nam}', str(nay.year)).replace('{thang}', f'{nay.month:02d}')
               .replace('{n}', '7').replace('{so_sku}', str(so_sku or 'nhiều'))
               .replace('{a}', chu_de).replace('{b}', '...')
               .replace('{loai_cong_trinh}', 'công trình'))


# ============================================================ 2. gộp SKU

_SO = re.compile(r'-?\d+(?:[.,]\d+)?')


def _so_dau_tien(v):
    m = _SO.search(str(v).replace(',', '.'))
    return float(m.group()) if m else None


def _fmt_so(x):
    """Bỏ .0 thừa nhưng KHÔNG dùng rstrip('0') — bug đã gặp: rstrip cắt
    360 thành 36. Chỉ cắt đúng phần thập phân bằng 0."""
    if x is None:
        return ''
    if float(x).is_integer():
        return str(int(x))
    return f'{x:g}'


def gop_sku(danh_sach_record, gioi_han_liet_ke=12):
    """N record -> (du_lieu_gop: dict, truong_thieu: list).

    Quy tắc gộp, cố ý đơn giản và kiểm chứng được:
      - Cột SỐ  -> dải min–max ("1.5 - 240 mm2"). 1 giá trị thì để nguyên.
      - Cột CHỮ -> liệt kê giá trị khác nhau, quá `gioi_han_liet_ke` thì
                   ghi "N giá trị khác nhau" thay vì đổ cả list vào prompt.
      - Cột nội bộ (gia_list, ghi_chu_ban_dau...) -> LOẠI TUYỆT ĐỐI.

    Đây là chỗ giải bài toán 2.171 SKU cáp trùng nội dung: gộp lại thành 1
    dải thay vì đẻ 2.171 bài khác nhau ~4 ký tự.
    """
    cam = {'gia_list', 'ghi_chu_ban_dau', 'nhom_nguon', 'nguon_catalogue'}
    try:
        import profiles as PF
        cam |= set(getattr(PF, 'FIELD_CAM_TUYET_DOI', set()))
    except Exception:
        pass
    cam |= {'dataset_id', 'record_id', 'profile_id', 'outline_id', 'content_type',
            'selected', 'pipeline_version', 'du_lieu_json', 'thong_so_dong'}

    NHAN = {
        'ten_goc': 'Tên hàng', 'ma_goc': 'Mã hàng', 'thuong_hieu': 'Thương hiệu',
        'quy_cach': 'Quy cách', 'dvt': 'Đơn vị tính', 'tiet_dien': 'Tiết diện',
        'cap_dien_ap': 'Cấp điện áp', 'vat_lieu_ruot': 'Vật liệu ruột',
        'cong_suat': 'Công suất', 'to_dau_day': 'Tổ đấu dây',
        'duong_kinh_cach_dien': 'Đường kính cách điện', 'tieu_chuan_catalogue': 'Tiêu chuẩn',
        'bao_hanh_thang': 'Bảo hành', 'chung_nhan': 'Chứng nhận',
    }

    if not danh_sach_record:
        return {}, []

    gom = {}
    for rec in danh_sach_record:
        nguon = dict(rec)
        nguon.update(rec.get('thong_so_dong') or {})
        for k, v in nguon.items():
            if k in cam or v in (None, '', 'nan'):
                continue
            gom.setdefault(k, []).append(v)

    ra = {'Số quy cách trong nhóm': str(len(danh_sach_record))}
    thieu = []
    for k, ds in sorted(gom.items()):
        nhan = NHAN.get(k, k.replace('_', ' ').strip().capitalize())
        sos = [_so_dau_tien(v) for v in ds]
        sos_sach = [s for s in sos if s is not None]

        # coi là cột số khi >=80% giá trị parse ra số VÀ có ít nhất 2 mốc khác nhau
        if len(sos_sach) >= max(1, int(0.8 * len(ds))) and len(set(sos_sach)) > 1:
            don_vi = re.sub(r'^[\d.,\s\-]+', '', str(ds[0])).strip()
            ra[nhan] = f'{_fmt_so(min(sos_sach))} - {_fmt_so(max(sos_sach))}' + (f' {don_vi}' if don_vi else '')
        else:
            gt = []
            for v in ds:
                s = str(v).strip()
                if s and s not in gt:
                    gt.append(s)
            ra[nhan] = gt[0] if len(gt) == 1 else (
                ', '.join(gt) if len(gt) <= gioi_han_liet_ke else f'{len(gt)} giá trị khác nhau')

    for k, nhan in NHAN.items():
        if nhan not in ra:
            thieu.append(nhan)
    return ra, thieu


# ============================================================ 3. sinh bài

def sinh_bai(con, bai_id, model=None, site_cfg=None, timeout=90, api_key=None):
    """Gọi Gemini sinh nội dung cho 1 bài. Trả (ok, thong_diep).

    Dùng lại transport của ai_wp_adapter (xử lý 429/thinkingConfig/schema),
    chỉ thay nguồn prompt sang prompts_seo_post.
    """
    import requests
    import ai_wp_adapter as AD

    bai = DB.lay_bai(con, bai_id)
    if not bai:
        return False, f'Không tìm thấy bài {bai_id}'

    recs = DB.sku_cua_bai(con, bai_id)
    du_lieu, thieu = gop_sku(recs)

    ok, ly_do = P.kiem_tra_du_dieu_kien(bai['content_type'], len(recs))
    if not ok:
        DB.cap_nhat(con, bai_id, trang_thai=DB.LOI, loi=ly_do)
        return False, ly_do

    try:
        he_thong, nguoi_dung, schema = P.xay_prompt_post(
            bai['content_type'], bai['tu_khoa_chinh'],
            tu_khoa_phu=bai['tu_khoa_phu'], du_lieu_sku=du_lieu or None,
            truong_thieu=thieu or None, site_cfg=site_cfg,
            che_do_gia=bai['che_do_gia'], ghi_chu_bien_tap=bai['ghi_chu_bien_tap'] or '')
    except ValueError as e:
        DB.cap_nhat(con, bai_id, trang_thai=DB.LOI, loi=str(e))
        return False, str(e)

    key = (api_key if api_key is not None else os.environ.get('GOOGLE_API_KEY', '')).strip()
    if not key:
        return False, 'Chưa có GOOGLE_API_KEY — nhập ở tab "1. Cấu hình".'
    model = model or getattr(AD, 'MODEL_GEMINI', 'gemini-3.6-flash')

    DB.cap_nhat(con, bai_id, trang_thai=DB.DANG_SINH, loi=None)
    body = {
        'system_instruction': {'parts': [{'text': he_thong}]},
        'contents': [{'role': 'user', 'parts': [{'text': nguoi_dung}]}],
        'generationConfig': {
            'temperature': 0.7, 'maxOutputTokens': 48000,
            'responseMimeType': 'application/json',
            'responseSchema': AD._sang_gemini_schema(schema),
            # Bài post dài hơn mô tả sản phẩm -> nới thinking so với 6000 của
            # luồng cũ, nhưng vẫn có TRẦN. Không giới hạn là phần suy nghĩ ăn
            # hết ngân sách, JSON bị cắt -> finishReason=MAX_TOKENS.
            'thinkingConfig': {'thinkingBudget': 8000},
        },
    }
    url = f'{getattr(AD, "GEMINI_URL", "https://generativelanguage.googleapis.com/v1beta")}/models/{model}:generateContent?key={key}'

    bat_dau = time.time()
    try:
        r = requests.post(url, json=body, timeout=timeout)
    except Exception as e:
        msg = f'Lỗi mạng khi gọi Gemini: {type(e).__name__}: {e}'
        DB.cap_nhat(con, bai_id, trang_thai=DB.LOI, loi=msg)
        return False, msg

    if r.status_code == 429:
        msg = ('Hết lượt / bị chặn tốc độ (429). Free tier Gemini là 20 request/ngày '
               'tính theo PROJECT, đổi key cùng project không ăn thua. Chờ reset (~14-15h VN) '
               'hoặc đổi model.')
        DB.cap_nhat(con, bai_id, trang_thai=DB.LOI, loi=msg)
        return False, msg
    if r.status_code != 200:
        msg = f'Gemini trả HTTP {r.status_code}: {r.text[:300]}'
        DB.cap_nhat(con, bai_id, trang_thai=DB.LOI, loi=msg)
        return False, msg

    try:
        goi = r.json()
        text = goi['candidates'][0]['content']['parts'][0]['text']
        data = json.loads(text)
    except Exception as e:
        msg = f'Không đọc được JSON Gemini trả về: {type(e).__name__}: {e}'
        DB.cap_nhat(con, bai_id, trang_thai=DB.LOI, loi=msg)
        return False, msg

    # chặn field lạ trước khi render
    cho_phep = set(P.truong_ai_duoc_tra(bai['content_type']))
    data = {k: v for k, v in data.items() if k in cho_phep}

    ok_bia, canh_bao = kiem_tra_bia_so(data, bai, du_lieu)

    html_bai = render_bai(bai, data, du_lieu, recs)
    title = (data.get('meta_title') or goi_y_tieu_de(bai['content_type'], bai['tu_khoa_chinh'])).strip()
    DB.cap_nhat(con, bai_id,
                trang_thai=DB.SINH_XONG,
                title=title,
                slug=tao_slug(title),
                meta_description=(data.get('meta_description') or '').strip(),
                html=html_bai,
                ai_json=json.dumps(data, ensure_ascii=False),
                loi=('; '.join(canh_bao) if canh_bao else None),
                thoi_luong_giay=round(time.time() - bat_dau, 1))
    tin = f'Sinh xong ({round(time.time() - bat_dau, 1)}s)'
    if canh_bao:
        tin += f' — CÓ {len(canh_bao)} CẢNH BÁO, đọc trước khi đăng'
    return True, tin


def kiem_tra_bia_so(ai_data, bai, du_lieu_gop):
    """Hậu kiểm chống bịa. Trả (ok, list cảnh báo).

    KHÔNG chặn cứng — bài post có kiến thức phổ thông hợp lệ, chặn cứng là
    chặn nhầm. Nhưng phải NÓI RA để người duyệt biết chỗ nào cần soi.
    """
    canh_bao = []
    toan_van = ' '.join(str(v) for v in ai_data.values() if isinstance(v, str))

    # 1. rò giá khi đang ở chế độ ẨN
    if bai['che_do_gia'] != 'CONG_KHAI':
        if re.search(r'\d[\d.,]{4,}\s*(vnđ|vnd|đồng|đ/|₫)', toan_van, re.IGNORECASE):
            canh_bao.append('Có chuỗi giống GIÁ TIỀN trong bài dù đang ở chế độ ẩn số — soi kỹ.')

    # 2. bài không gắn SKU mà lại có thông số kỹ thuật cụ thể
    if not du_lieu_gop:
        don_vi = r'(kva|kv|mm2|mm²|amp|\ba\b|\bw\b|kw|hz|kg)'
        if len(re.findall(r'\d+[\d.,]*\s*' + don_vi, toan_van, re.IGNORECASE)) >= 3:
            canh_bao.append('Bài KHÔNG gắn SKU nhưng có nhiều thông số kỹ thuật kèm số — '
                            'nguy cơ bịa số, đối chiếu trước khi đăng.')

    # 3. câu quảng cáo rỗng (luật N6)
    for cum in ('tốt nhất thị trường', 'uy tín số 1', 'hàng đầu việt nam', 'giá rẻ nhất'):
        if cum in toan_van.lower():
            canh_bao.append(f'Có câu quảng cáo rỗng: "{cum}".')

    # 4. thẻ HTML ngoài whitelist
    the_la = set(re.findall(r'<\s*(script|style|div|span|h1|h2|table|iframe)\b', toan_van, re.IGNORECASE))
    if the_la:
        canh_bao.append(f'AI trả thẻ không được phép: {", ".join(sorted(the_la))} (sẽ bị sanitize xoá).')

    return (not canh_bao), canh_bao


# ============================================================ 4. render

def tao_slug(text):
    s = str(text).lower().replace('đ', 'd').replace('Đ', 'd')
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return re.sub(r'-{2,}', '-', s)[:90].strip('-')


def _sach(h):
    try:
        import render_phase2 as R
        return R.sanitize_html(h or '')
    except Exception:
        return re.sub(r'<\s*(script|style)[^>]*>.*?<\s*/\s*\1\s*>', '', h or '',
                      flags=re.IGNORECASE | re.DOTALL)


CTA_MAC_DINH = ('<div class="bg-cta"><p><strong>Cần báo giá hoặc tư vấn kỹ thuật?</strong> '
                'Liên hệ để nhận bảng giá cập nhật và hỗ trợ chọn đúng chủng loại cho công trình.</p></div>')


def _bang_quy_cach(recs, gioi_han=40):
    """Bảng quy cách do CODE dựng, không phải AI (luật N3). Escape từng ô."""
    if not recs:
        return ''
    uu_tien = ['ten_goc', 'quy_cach', 'tiet_dien', 'cap_dien_ap', 'cong_suat',
               'vat_lieu_ruot', 'thuong_hieu', 'dvt']
    NHAN = {'ten_goc': 'Tên hàng', 'quy_cach': 'Quy cách', 'tiet_dien': 'Tiết diện',
            'cap_dien_ap': 'Cấp điện áp', 'cong_suat': 'Công suất',
            'vat_lieu_ruot': 'Vật liệu ruột', 'thuong_hieu': 'Thương hiệu', 'dvt': 'ĐVT'}
    cot = [c for c in uu_tien if any(str(r.get(c, '')).strip() for r in recs)]
    if not cot:
        return ''
    h = ['<table class="specs-table"><thead><tr>']
    h += [f'<th>{_html.escape(NHAN.get(c, c))}</th>' for c in cot]
    h.append('</tr></thead><tbody>')
    for r in recs[:gioi_han]:
        h.append('<tr>' + ''.join(
            f'<td>{_html.escape(str(r.get(c, "") or ""))}</td>' for c in cot) + '</tr>')
    h.append('</tbody></table>')
    if len(recs) > gioi_han:
        h.append(f'<p><em>Hiển thị {gioi_han}/{len(recs)} quy cách. '
                 f'Liên hệ để nhận danh mục đầy đủ.</em></p>')
    return ''.join(h)


def render_bai(bai, ai_data, du_lieu_gop, recs):
    """Lắp HTML hoàn chỉnh. Thứ tự cố định, không để AI quyết bố cục."""
    cfg = P.CONTENT_TYPE[bai['content_type']]
    kh = []

    intro = _sach(ai_data.get('intro_html', ''))
    if intro:
        kh.append(intro)
    kh.append(CTA_MAC_DINH)   # CTA vị trí 1 — ngay sau intro

    NHAN_H2 = {
        'yeu_to_gia_html': 'Yếu tố ảnh hưởng tới giá',
        'huong_dan_doc_bang_html': 'Cách đọc bảng quy cách',
        'luu_y_bao_gia_html': 'Lưu ý khi lấy báo giá',
        'dinh_nghia_html': 'Định nghĩa và vai trò',
        'cau_tao_html': 'Cấu tạo',
        'nguyen_ly_html': 'Nguyên lý hoạt động',
        'phan_loai_html': 'Phân loại',
        'ung_dung_html': 'Ứng dụng thực tế',
        'tieu_chi_html': 'Tiêu chí đánh giá',
        'ket_luan_html': 'Kết luận',
        'tong_quan_a_html': 'Tổng quan lựa chọn A',
        'tong_quan_b_html': 'Tổng quan lựa chọn B',
        'nen_chon_khi_nao_html': 'Nên chọn loại nào?',
        'cong_thuc_html': 'Công thức tính',
        'loi_thuong_gap_html': 'Lỗi thường gặp',
        'pham_vi_html': 'Phạm vi áp dụng',
        'noi_dung_chinh_html': 'Nội dung chính',
        'ap_dung_thuc_te_html': 'Áp dụng thực tế',
        'noi_dung_tai_lieu_html': 'Tài liệu gồm những gì',
        'huong_dan_tra_cuu_html': 'Hướng dẫn tra cứu',
        'boi_canh_html': 'Bối cảnh dự án',
        'giai_phap_html': 'Giải pháp',
        'ket_qua_html': 'Kết quả',
    }

    for truong in cfg['sections']:
        if truong == 'intro_html':
            continue
        noi = _sach(ai_data.get(truong, ''))
        if not noi:
            continue
        kh.append(f'<h2>{_html.escape(NHAN_H2.get(truong, truong))}</h2>')
        kh.append(noi)

    # bảng do AI trả dạng mảng -> code dựng <table>, AI không được tự dựng
    for truong, khoa in cfg['truong_mang'].items():
        muc = ai_data.get(truong) or []
        if not isinstance(muc, list) or not muc:
            continue
        if truong == 'danh_sach':
            kh.append('<h2>Danh sách</h2><ul>')
            for m in muc:
                kh.append(f'<li><strong>{_html.escape(str(m.get("ten", "")))}</strong> — '
                          f'{_html.escape(str(m.get("mo_ta", "")))} '
                          f'<em>Phù hợp khi:</em> {_html.escape(str(m.get("phu_hop_khi", "")))}</li>')
            kh.append('</ul>')
        elif truong == 'buoc':
            kh.append('<h2>Các bước thực hiện</h2><ol>')
            for m in muc:
                kh.append(f'<li><strong>{_html.escape(str(m.get("tieu_de", "")))}</strong>: '
                          f'{_html.escape(str(m.get("noi_dung", "")))}</li>')
            kh.append('</ol>')
        elif truong == 'bang_so_sanh':
            kh.append('<h2>Bảng đối chiếu</h2><table class="specs-table"><thead><tr>'
                      '<th>Tiêu chí</th><th>Lựa chọn A</th><th>Lựa chọn B</th></tr></thead><tbody>')
            for m in muc:
                kh.append(f'<tr><td>{_html.escape(str(m.get("tieu_chi", "")))}</td>'
                          f'<td>{_html.escape(str(m.get("ben_a", "")))}</td>'
                          f'<td>{_html.escape(str(m.get("ben_b", "")))}</td></tr>')
            kh.append('</tbody></table>')

    bang = _bang_quy_cach(recs)
    if bang:
        kh.append('<h2>Bảng quy cách</h2>')
        kh.append(bang)
        kh.append(CTA_MAC_DINH)   # CTA vị trí 2 — ngay dưới bảng, chỗ nóng nhất

    faq = ai_data.get('faq') or []
    if isinstance(faq, list) and faq:
        kh.append('<h2>Câu hỏi thường gặp</h2>')
        for m in faq:
            kh.append(f'<h3>{_html.escape(str(m.get("q", "")))}</h3>'
                      f'<p>{_html.escape(str(m.get("a", "")))}</p>')

    kh.append(CTA_MAC_DINH)       # CTA vị trí 3 — cuối bài
    return '\n'.join(kh)


def dung_schema_jsonld(bai, ai_data):
    """JSON-LD dựng bằng CODE, đi qua meta key riêng, KHÔNG nhúng vào HTML."""
    ra = []
    loai = P.schema_cua_type(bai['content_type'])
    if 'Article' in loai:
        ra.append({'@context': 'https://schema.org', '@type': 'Article',
                   'headline': bai.get('title') or ai_data.get('meta_title', ''),
                   'description': bai.get('meta_description') or ai_data.get('meta_description', ''),
                   'datePublished': datetime.now().strftime('%Y-%m-%d')})
    faq = ai_data.get('faq') or []
    if 'FAQPage' in loai and faq:
        ra.append({'@context': 'https://schema.org', '@type': 'FAQPage',
                   'mainEntity': [{'@type': 'Question', 'name': m.get('q', ''),
                                   'acceptedAnswer': {'@type': 'Answer', 'text': m.get('a', '')}}
                                  for m in faq]})
    return ra


# ============================================================ 5. đăng

def _doc_cau_hinh_wp():
    """Đọc URL + Application Password từ cauhinh.doc_website()."""
    import cauhinh as CH
    w = CH.doc_website() or {}
    url = (w.get('url') or '').rstrip('/')
    user = w.get('user') or ''
    pw = w.get('app_pw') or w.get('app_password') or ''
    if not (url and user and pw):
        raise RuntimeError('Chưa cấu hình WordPress — vào tab "1. Cấu hình" nhập URL + '
                           'Application Password trước.')
    return url, (user, pw)


def dang_bai(con, bai_id, trang_thai_wp='draft'):
    """Đăng lên WordPress. che_do_dang quyết định endpoint:
        post    -> /wp-json/wp/v2/posts
        product -> /wp-json/wc/v3/products

    KHÔNG mượn ai_wp_adapter.dang_wp_that(): hàm đó tra bảng `bai_viet` theo
    (dataset_id, record_id) của luồng sản phẩm. Bài post không có SKU nào để
    điền vào 2 khoá đó, nhét bừa 'seo_post' vào là ghi rác sang bảng của
    luồng cũ. Đường đăng riêng, idempotent bằng chính bai_seo.wp_id.

    Mặc định 'draft' — bài luôn qua mắt người trước khi publish.
    """
    import requests

    bai = DB.lay_bai(con, bai_id)
    if not bai:
        return False, f'Không tìm thấy bài {bai_id}'
    if not bai.get('html'):
        return False, 'Bài chưa có nội dung — sinh bài trước.'

    canh = P.canh_bao_che_do_dang(bai['content_type'], bai['che_do_dang'], len(bai['sku']))
    la_product = (bai['che_do_dang'] == P.DANG_PRODUCT)

    try:
        goc, auth = _doc_cau_hinh_wp()
    except RuntimeError as e:
        return False, str(e)

    if la_product:
        diem_cuoi = f'{goc}/wp-json/wc/v3/products'
        goi = {'name': bai['title'], 'slug': bai['slug'], 'type': 'simple',
               'description': bai['html'],
               'short_description': bai.get('meta_description') or '',
               'status': 'draft' if trang_thai_wp == 'draft' else 'publish',
               'catalog_visibility': 'visible'}
    else:
        diem_cuoi = f'{goc}/wp-json/wp/v2/posts'
        goi = {'title': bai['title'], 'slug': bai['slug'], 'content': bai['html'],
               'excerpt': bai.get('meta_description') or '',
               'status': 'draft' if trang_thai_wp == 'draft' else 'publish'}

    # Idempotent: đã có wp_id thì CẬP NHẬT, không tạo bài mới đẻ slug-2.
    wp_id_cu = (bai.get('wp_id') or '').strip()
    url = f'{diem_cuoi}/{wp_id_cu}' if wp_id_cu else diem_cuoi

    try:
        r = requests.post(url, json=goi, auth=auth, timeout=60)
    except Exception as e:
        msg = f'Lỗi mạng khi đăng: {type(e).__name__}: {e}'
        DB.cap_nhat(con, bai_id, trang_thai=DB.LOI, loi=msg)
        return False, msg

    if r.status_code in (401, 403):
        msg = f'Xác thực thất bại (HTTP {r.status_code}) — kiểm tra Application Password.'
        DB.cap_nhat(con, bai_id, trang_thai=DB.LOI, loi=msg)
        return False, msg
    if r.status_code >= 300:
        msg = f'WordPress từ chối (HTTP {r.status_code}): {r.text[:300]}'
        DB.cap_nhat(con, bai_id, trang_thai=DB.LOI, loi=msg)
        return False, msg

    try:
        kq = r.json()
    except ValueError:
        kq = {}
    wp_id = kq.get('id', '')
    wp_url = kq.get('link') or kq.get('permalink') or ''

    DB.cap_nhat(con, bai_id, trang_thai=DB.DA_DANG, wp_id=str(wp_id),
                wp_url=wp_url, ngay_dang=datetime.now().isoformat(timespec='seconds'),
                loi=canh or None)
    loai = 'product' if la_product else 'post'
    return True, (f'Đã đăng {loai} draft (#{wp_id}) — {wp_url or "chưa có URL"}'
                  + (f'\nCẢNH BÁO: {canh}' if canh else ''))


# ============================================================ tiện ích hàng loạt

def tao_bai_tu_de_xuat(con, danh_sach_de_xuat, site, che_do_dang='post', che_do_gia='AN'):
    """Đổ kết quả de_xuat() vào DB. Trả (so_tao_moi, so_bo_qua_vi_trung)."""
    moi = trung = 0
    for m in danh_sach_de_xuat:
        if m.get('do_tin_cay') == 'thap':
            trung += 1     # tên sản phẩm thuần — việc của luồng SKU, không tạo bài post
            continue
        truoc = DB.tim_trung_tu_khoa(con, m['tu_khoa'])
        bai_id = DB.tao_bai(
            con, m['tu_khoa'], m['content_type'], site,
            tu_khoa_phu=m.get('tu_khoa_phu'), che_do_dang=che_do_dang,
            che_do_gia=che_do_gia, nguon=m.get('nguon', 'gsc'),
            diem_uu_tien=m.get('diem'), impression_goc=m.get('impression'))
        if truoc:
            trung += 1
        else:
            moi += 1
        _ = bai_id
    return moi, trung
