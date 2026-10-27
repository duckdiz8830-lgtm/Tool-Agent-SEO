# -*- coding: utf-8 -*-
"""
Phase 2 Lite — Bảng thông số, schema, sanitize_html, chống bịa Hard Block,
và (Round 2) hàm dựng HTML hoàn chỉnh R2-06.

Prompt cho AI đã CHUYỂN sang prompts_phase2.py (R2-05, xay_prompt()) — hàm
dung_prompt() cũ ở đây đã xoá, không còn dùng.

Không đụng prompts.py/autopost.py cũ (nhánh RMU vẫn dùng nguyên bộ đó).
"""
import html
import re

import bleach

import profiles as P
import khoi_chiu_tai as KCT   # Ver 4.6

NHAN_COT = {
    'ten_goc': 'Tên hàng', 'thuong_hieu': 'Thương hiệu', 'quy_cach': 'Quy cách',
    'dvt': 'Đơn vị tính', 'tiet_dien': 'Tiết diện', 'cap_dien_ap': 'Cấp điện áp',
    'vat_lieu_ruot': 'Vật liệu ruột', 'cong_suat': 'Công suất',
    # Ver 4.9.5 — 6 field enrich catalogue đầu cáp/hộp nối (không dùng ở
    # đây vì bang_thong_so() lấy nhãn từ effective_cot_bang() — profiles.py
    # đã có sẵn (field, nhãn) — nhưng vẫn khai báo để nhất quán, phòng chỗ
    # nào khác trong code đọc trực tiếp NHAN_COT thay vì cot_bang).
    'duong_kinh_cach_dien': 'Đường kính cách điện áp dụng (mm)',
    'kich_thuoc_i': 'Kích thước lắp đặt I (mm)', 'kich_thuoc_l': 'Kích thước lắp đặt L (mm)',
    'duong_ro_ngoai_troi': 'Chiều dài đường rò - ngoài trời (mm)',
    'tieu_chuan_catalogue': 'Tiêu chuẩn áp dụng', 'test_dien': 'Kết quả test điện',
}


# ============================================================ Ver 4.9.9 — style INLINE, không phụ thuộc CSS ngoài
# Vá theo yêu cầu Thịnh: (1) không rành CSS, không muốn thao tác tay dán
# CSS vào Theme -> chuyển hết sang style="" ngay trên từng thẻ, tool tự lo
# hết; (2) không muốn để lại "dấu vân tay" tên tool/domain trong source
# code site -> bỏ hẳn prefix "lotech-", không đặt tên riêng theo domain
# nào (đổi qua site khác không cần sửa gì). Không dùng thẻ <style> block —
# WordPress kses xử lý <style> giống <script> (xoá thẻ, giữ text) — ĐÃ xác
# nhận qua bug schema thật (CHANGELOG-VER496.md), không lặp lại lỗi đó.
ST = {
    'hero': 'background:#f8fafc;border-radius:10px;padding:18px 22px;margin-bottom:20px;',
    'hero_meta': 'font-size:14px;color:#444;margin:0 0 10px;',
    'hero_specs': 'list-style:none;padding:0;margin:0 0 12px;font-size:14px;',
    'specs_table': 'width:100%;border-collapse:collapse;margin:14px 0;font-size:14px;',
    'specs_th': 'border:1px solid #e5e7eb;padding:9px 14px;text-align:left;background:#f1f5f9;width:40%;font-weight:600;',
    'specs_td': 'border:1px solid #e5e7eb;padding:9px 14px;text-align:left;',
    'so_sanh_table': 'width:100%;border-collapse:collapse;margin:14px 0;font-size:13px;',
    'so_sanh_th': 'border:1px solid #e5e7eb;padding:8px 12px;text-align:center;background:#f1f5f9;font-weight:600;',
    'so_sanh_td': 'border:1px solid #e5e7eb;padding:8px 12px;text-align:center;',
    'so_sanh_td_hien_tai': 'border:1px solid #e5e7eb;padding:8px 12px;text-align:center;background:#fef3c7;font-weight:700;',
    'btn_goi': 'display:inline-block;padding:9px 18px;border-radius:6px;text-decoration:none;font-size:14px;font-weight:600;margin:0 8px 6px 0;background:#16a34a;color:#fff;',
    'btn_zalo': 'display:inline-block;padding:9px 18px;border-radius:6px;text-decoration:none;font-size:14px;font-weight:600;margin:0 8px 6px 0;background:#0ea5e9;color:#fff;',
    'btn_baogia': 'display:inline-block;padding:12px 26px;border-radius:8px;text-decoration:none;font-size:16px;font-weight:700;margin:0 8px 6px 0;background:#ea580c;color:#fff;box-shadow:0 2px 6px rgba(234,88,12,0.4);',
    'cta_cuoi': 'background:#fffbeb;border-radius:10px;padding:20px 22px;margin-top:30px;',
    'khoi_chung': 'background:#fffbeb;border-radius:10px;padding:14px 18px;margin:20px 0;font-size:14px;',
    'khoi_thuong_hieu': 'background:#f8fafc;border-radius:10px;padding:14px 18px;margin:16px 0;font-size:14px;',
    'anh_placeholder': 'border:2px dashed #f97316;border-radius:10px;padding:24px;margin:16px 0;text-align:center;color:#c2410c;font-size:14px;font-weight:600;background:#fff7ed;',
    'lien_quan': 'list-style:none;padding:0;margin:0;',
    'lien_quan_li': 'padding:6px 0;border-bottom:1px dashed #e5e7eb;',
    'lien_quan_grid': 'display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin:14px 0;',
    'lien_quan_card': 'display:block;padding:14px 16px;border:1px solid #e5e7eb;border-radius:8px;text-decoration:none;color:#1a1a1a;font-size:14px;font-weight:600;line-height:1.4;transition:border-color .15s ease;',
    'btn_catalogue': 'display:inline-block;padding:9px 18px;border-radius:6px;text-decoration:none;font-size:14px;font-weight:600;margin:0 8px 6px 0;background:#0f172a;color:#fff;',
}

# ============================================================ Ver 2.1 — CSS ra ngoài (class thay inline)
# LÝ DO (đo thật lúc audit Ver 2.0): inline CSS chiếm 55,9% độ dài mỗi
# bài, và giống hệt nhau giữa mọi SKU -> code-to-text ratio tệ, nhân
# 5.264 trang. Chuyển sang class + 1 file CSS dán 1 lần vào WordPress
# (Code Snippets/theme) thì phần rác này biến mất khỏi từng bài.
#
# AN TOÀN NGƯỢC: mặc định TẮT (giữ inline y như Ver 2.0). Chỉ bật khi đã
# dán CSS lên site — nếu bật mà chưa dán, bài sẽ mất định dạng. Bật bằng
# biến môi trường CSS_CLASS_MODE=1 trong cau-hinh.env (hoặc checkbox tab
# Cấu hình).
CLS = {k: f'snl-{k.replace("_", "-")}' for k in ST}


def _dung_class_css():
    """Đọc mỗi lần gọi (không cache) để đổi cấu hình xong là có hiệu lực
    ngay, không cần khởi động lại app."""
    import os
    return str(os.environ.get('CSS_CLASS_MODE', '0')).strip().lower() in ('1', 'true', 'yes', 'on')


def _bo_cta_cuoi():
    """Ver 2.2 — theme WordPress (Flatsome) đã có sẵn khối CTA riêng ngay
    dưới nội dung (xác nhận bằng ảnh trang thật: khối xanh đậm 3 nút Nhận
    báo giá / Zalo / Hotline). Khối "Liên hệ báo giá" do tool sinh ra ở
    cuối bài là TRÙNG LẶP -> bật cờ này để bỏ, tránh 2 CTA sát nhau làm
    loãng. Mặc định TẮT (giữ hành vi cũ, an toàn cho site chưa có CTA theme)."""
    import os
    return str(os.environ.get('BO_CTA_CUOI', '0')).strip().lower() in ('1', 'true', 'yes', 'on')


def _bo_anh_placeholder():
    """Ver 2.2 — ô 'CHỖ CHÈN ẢNH SẢN PHẨM' viền cam trông như lỗi hiển thị
    với khách (xác nhận qua ảnh trang thật). Chừng nào chưa có ảnh thật,
    KHÔNG hiện gì còn hơn hiện ô báo thiếu. Mặc định TẮT (giữ hành vi cũ —
    ai đang dùng placeholder làm dấu nhắc chèn ảnh tay thì không bị mất)."""
    import os
    return str(os.environ.get('BO_ANH_PLACEHOLDER', '0')).strip().lower() in ('1', 'true', 'yes', 'on')


def _st(khoa):
    """Trả về attribute HTML hoàn chỉnh: class="snl-xxx" (chế độ mới) hoặc
    style="..." (chế độ cũ, mặc định). Dùng thay cho style="{ST[...]}"."""
    if _dung_class_css():
        return f'class="{CLS[khoa]}"'
    return f'style="{ST[khoa]}"'


def xuat_file_css():
    """Sinh nội dung CSS đầy đủ để dán vào WordPress (Code Snippets plugin,
    hoặc Appearance > Customize > Additional CSS). Sinh TỪ CHÍNH ST dict —
    không viết tay lần 2, nên không bao giờ lệch với code render."""
    # Ver 2.5 — GỘP cả bộ khối cao cấp (giao_dien_2_5.STYLE_2_5) vào cùng
    # 1 file, để Thịnh chỉ phải dán MỘT lần lên WordPress thay vì 2 file.
    try:
        import giao_dien_2_5 as G2
        css_2_5 = '\n' + G2.xuat_css_2_5()
    except Exception:
        css_2_5 = ''

    dong = ['/* SONEALEO — CSS cho bài sản phẩm. Dán 1 lần vào WordPress.',
            '   Sinh tự động từ render_phase2.ST — không sửa tay ở đây,',
            '   sửa ST rồi xuất lại. */', '']
    for khoa, css in ST.items():
        thuoc_tinh = '; '.join(x.strip() for x in css.split(';') if x.strip())
        dong.append(f'.{CLS[khoa]} {{ {thuoc_tinh}; }}')
    return '\n'.join(dong) + '\n' + css_2_5


# ============================================================ mục 6.1 — bảng thông số

# Ver 3.3 — nhãn cột Excel là ngôn ngữ NỘI BỘ, không phải ngôn ngữ khách
# hàng. "Loại lõi (trích từ tên)" hiện lên bảng cho khách xem là lộ cách
# tool hoạt động (Thịnh + GPT cùng bắt trên bài thật). Bỏ phần chú thích
# trong ngoặc CHỈ khi nó là ghi chú nội bộ; đơn vị đo thì GIỮ.
_NGOAC_NOI_BO = re.compile(
    r'\s*\((?:[^()]*(?:trích từ tên|suy ra|tự tính|nội bộ|tạm tính|ước tính)[^()]*)\)',
    re.IGNORECASE)
_NGOAC_NGUON = re.compile(r'\s*\(([^()]*?),\s*(catalogue[^()]*)\)', re.IGNORECASE)


def _nhan_hien_thi(ten):
    """Dọn nhãn cột trước khi in ra bảng cho khách."""
    t = str(ten or '')
    t = _NGOAC_NOI_BO.sub('', t)
    # "Tổn hao Po (W, catalogue THIBIDI)" -> "Tổn hao Po (W)" + nguồn đã
    # ghi ở badge/chân bảng, không lặp lại trong từng dòng.
    t = _NGOAC_NGUON.sub(lambda m: f' ({m.group(1).strip()})', t)
    return t.strip()


# Ver 3.6.4 — GỠ Uk khỏi danh sách gắn dấu ≤.
# Bảng TCCS 10:2021/EVN (Điều 20/38/56) ghi tiêu đề cột nguyên văn là
# "Điện áp ngắn mạch NHỎ NHẤT (Uk) (%)" — Uk là giá trị SÀN, không phải
# trần. In "≤ 2" là ngược dấu. Và về vật lý: Po/Pk thấp hơn trần là tốt,
# còn Uk thấp hơn thiết kế thì dòng ngắn mạch CAO hơn, tức xấu đi.
# Kỹ sư dùng Uk để tính dòng ngắn mạch chọn máy cắt và để kiểm điều kiện
# vận hành song song — cả hai đều cần trị số xác định, không phải ngưỡng.
# Nên Uk in TRẦN, không dấu. Io cũng không nằm trong danh sách này.
_RE_TON_HAO_QC = re.compile(r'tổn hao|ton hao|\bpo\b|\bpk\b', re.IGNORECASE)

# Nhãn cột trong MASTER ghi cứng "cực đại theo tiêu chuẩn EVN" cho mọi
# dòng. Nhưng 8 SKU KP có số THẬT từ catalogue hãng (IEC 60726) — dán nhãn
# quy chuẩn EVN lên số của hãng là tự hạ giá trị dữ liệu mình có.
_RE_NHAN_EVN = re.compile(r'\s*cực đại theo tiêu chuẩn EVN\s*', re.IGNORECASE)


def _nhan_theo_nguon(ten, loai_nguon):
    """Đổi nhãn cột khi số là của catalogue hãng, không phải quy chuẩn EVN."""
    if loai_nguon != 'catalogue_hang':
        return ten
    if not _RE_NHAN_EVN.search(str(ten)):
        return ten
    return _RE_NHAN_EVN.sub(' ', str(ten)).replace('  ', ' ').strip() \
        .replace('(W)', '(W, catalogue hãng)')


def _dong_bang_thong_so_dong(row):
    """Ver 2.8 — dựng thêm dòng bảng từ cột quét động, đặt SAU các cột đã
    khai báo. Giữ nguyên thứ tự xuất hiện trong Excel.

    Ver 3.6.1 — in dấu `≤` cho Po/Pk/Uk khi số là MỨC QUY CHUẨN EVN.
    Po/Pk/Uk trùng khít giữa THIBIDI và MBT vì cả hai in lại cùng bảng quy
    chuẩn EVN — đó là mức TRẦN cho phép, không phải số đo của từng máy.
    In dấu `=` cho số đó là sai sự thật với người mua là kỹ sư, và máy thật
    thường tốt hơn mức trần.

    Ký hiệu lấy từ cột `Nguồn - Ký hiệu hiển thị Po/Pk` của MASTER (Ver5
    trở đi) qua field `nguon_ky_hieu`: `≤` cho mức quy chuẩn, `=` cho số
    catalogue hãng công bố. Không có cột đó -> giữ nguyên như cũ.
    """
    dong = row.get('thong_so_dong') or {}
    if not dong:
        return ''
    ky_hieu = str(row.get('nguon_ky_hieu') or '').strip()
    loai_nguon = str(row.get('nguon_loai_so_lieu') or '').strip()
    ra = []
    for ten, gt in dong.items():
        ten = _nhan_theo_nguon(_nhan_hien_thi(ten), loai_nguon)
        v = str(gt)
        # chỉ thêm dấu cho đúng nhóm Po/Pk/Uk, và chỉ khi giá trị bắt đầu
        # bằng số (không thêm vào chuỗi mô tả)
        if (ky_hieu == '≤' and _RE_TON_HAO_QC.search(str(ten))
                and re.match(r'^\s*[\d.,]+\s*$', v)):
            v = f'≤ {v.strip()}'
        ra.append(f'<tr><th {_st("specs_th")}>{html.escape(str(ten))}</th>'
                  f'<td {_st("specs_td")}>{html.escape(v)}</td></tr>')
    return ''.join(ra)


def bang_thong_so(row):
    """Đọc effective_cot_bang(profile_id, outline_id). Giá trị đã normalize
    từ lúc import (profiles.normalize_cell) — không .strip() lại lần nữa
    trên dữ liệu pandas thô (đúng quyết định #5 vòng duyệt 2).

    Ver 4.9.9 — style INLINE (ST['specs_th']/['specs_td']), bỏ class
    "specs-table" cũ — xem khối ST đầu file."""
    profile_id, outline_id = row['profile_id'], row['outline_id']
    cot_bang = P.effective_cot_bang(profile_id, outline_id)
    tr = [f'<tr><th {_st("specs_th")}>{html.escape(nhan)}</th>'
          f'<td {_st("specs_td")}>{html.escape(v)}</td></tr>'
          for k, nhan in cot_bang
          if (v := row.get(k, ''))]
    if not tr:
        return '<p><em>Đang cập nhật thông số kỹ thuật.</em></p>'
    # Ver 2.8 — nối thêm dòng từ cột quét động (Dynamic Schema)
    bang = (f'<table {_st("specs_table")}><tbody>\n' + '\n'.join(tr)
            + _dong_bang_thong_so_dong(row) + '\n</tbody></table>')
    # Ver 3.9 C3 — A2608 có cờ nguồn/citation riêng trong MASTER Ver8.
    # In đúng citation đã import, không tự suy diễn QĐ 2608 là nguồn số liệu.
    sku = str(row.get('ma_goc') or '').upper()
    vien_dan = str(row.get('nguon_tieu_chuan_vien_dan') or '').strip()
    if 'A2608' in sku and vien_dan:
        bang += (f'<p><em>Nguồn số liệu: {html.escape(vien_dan)}.</em></p>')
    return bang


# ============================================================ mục 6.2 — sanitize_html
ALLOWED_TAGS = ['h2', 'h3', 'h4', 'p', 'ul', 'ol', 'li',
                 'table', 'thead', 'tbody', 'tr', 'th', 'td',
                 'a', 'strong', 'em', 'b', 'i', 'br']

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'target'],
    'table': ['class'],
    'td': ['colspan', 'rowspan', 'class'],
    'th': ['colspan', 'rowspan', 'class'],
}

ALLOWED_PROTOCOLS = ['http', 'https', 'tel']

CLASS_CHO_PHEP = {'specs-table', 'bg-cta', 'bg-specs'}


def _loc_class(html_str):
    """bleach không tự giới hạn GIÁ TRỊ của class, chỉ giới hạn class được
    phép xuất hiện trên tag nào — lọc thêm 1 bước: value nào không nằm trong
    whitelist thì xoá khỏi thuộc tính class."""
    def thay(m):
        gia_tri = [c for c in m.group(1).split() if c in CLASS_CHO_PHEP]
        return f'class="{" ".join(gia_tri)}"' if gia_tri else ''
    return re.sub(r'class="([^"]*)"', thay, html_str)


_XOA_KHOI_SCRIPT_STYLE = re.compile(r'<(script|style)\b[^>]*>.*?</\1>', re.IGNORECASE | re.DOTALL)


def sanitize_html(html_str):
    """Sanitize HTML do AI trả về TRƯỚC KHI ghép vào template và trước khi
    lưu/đăng WordPress. KHÔNG chạy hàm này lên HTML do bang_thong_so() dựng
    (code tự kiểm soát 100%, đã html.escape từng ô) — chạy lần 2 có nguy cơ
    xén mất class="specs-table"/colspan/rowspan (mục 6.2 kiến trúc)."""
    if not html_str:
        return ''
    # Xoá cả tag lẫn nội dung bên trong <script>/<style> trước — bleach mặc
    # định chỉ xoá tag lạ, giữ lại text bên trong, không đủ sạch cho 2 tag này.
    khong_script = _XOA_KHOI_SCRIPT_STYLE.sub('', html_str)
    sach = bleach.clean(
        khong_script,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )
    return _loc_class(sach)


# ============================================================ mục 8 — schema builder
def dung_schema(row, description=None):
    if not _bat_schema():
        return None            # Ver 4.5 — nhường Rank Math
    ct = row.get('content_type', 'product')
    if ct == 'service':
        return None
    profile_id, outline_id = row['profile_id'], row['outline_id']
    cot_bang = P.effective_cot_bang(profile_id, outline_id)
    schema = {
        '@context': 'https://schema.org', '@type': 'Product',
        'name': row.get('ten_goc'), 'sku': row.get('publish_sku') or row.get('ma_goc'),
        'brand': {'@type': 'Brand', 'name': row.get('thuong_hieu')} if row.get('thuong_hieu') else None,
        'description': description if description is not None else row.get('meta_description', ''),
        'additionalProperty': [
            {'@type': 'PropertyValue', 'name': nhan, 'value': row[k]}
            for k, nhan in cot_bang if row.get(k)
        ],
    }
    # KHÔNG nhánh nào tạo 'offers'/'price' — quyết định có chủ đích (không
    # phải thiếu sót): Offer theo schema.org BẮT BUỘC có price hoặc
    # priceSpecification, mà Lotech không công khai giá list (gia_list là
    # field nội bộ tuyệt đối) -> nhét Offer thiếu price còn SAI chuẩn hơn là
    # không có Offer. test_gate2.py::D1 test rõ "không có Offer hoặc giá",
    # đừng đổi lại nếu không có lý do mới.
    return {k: v for k, v in schema.items() if v}


def dung_schema_script(row):
    """Task 1 Gate 2: gắn dung_schema() vào HTML dưới dạng
    <script type="application/ld+json">. Dịch vụ (content_type=service) ->
    dung_schema() trả None -> hàm này trả chuỗi rỗng, KHÔNG có script nào
    được chèn (đúng yêu cầu 'dịch vụ không có Product Schema').

    Escape '</script' bên trong JSON (phòng thủ, dù dữ liệu nguồn khó có
    chuỗi này) để không lỡ đóng sớm thẻ <script> bao ngoài.
    """
    import json
    schema = dung_schema(row)
    if not schema:
        return ''
    noi_dung = json.dumps(schema, ensure_ascii=False).replace('</script', '<\\/script')
    return f'<script type="application/ld+json">{noi_dung}</script>'


# ============================================================ R2-06 — dựng HTML hoàn chỉnh
_SLUG_XAU_RE = re.compile(r'[^a-z0-9]+')


# ============================================================ Ver 3.6 — rút gọn text an toàn
def rut_gon_an_toan(text, do_dai_toi_da):
    """Cắt chuỗi ở giới hạn `do_dai_toi_da` nhưng KHÔNG BAO GIỜ cắt giữa 1
    token (từ/số kỹ thuật dính liền không dấu cách — VD "22/0.4KV",
    "3x50+1x25mm²", mã hàng). Không tự sửa/bịa lại nội dung — chỉ cắt hoặc
    giữ nguyên.

    Ver 3.6 Task 1 — bug thật GPT phát hiện: `ten[:40]`/`ten[:60]` kiểu cắt
    thô cắt ngay giữa các cụm số như trên (VD "22/0.4K" thiếu chữ "V" cuối,
    nhìn như dữ liệu bịa/lỗi dù chỉ là bị cắt dở), khiến `sinh_va_dang_mock()`
    tự tạo ra chuỗi trông giống bịa số dù chưa từng bịa gì — Hard Block đôi
    khi vô tình chặn nhầm 1 mảnh cắt dở, đôi khi lọt qua nhưng vẫn sai chính
    tả/đơn vị so với record gốc.

    Thuật toán: lùi về khoảng trắng gần nhất TRƯỚC giới hạn. Nếu từ đầu tiên
    đã dài hơn cả giới hạn (không có khoảng trắng nào để lùi), THÀ DÀI HƠN
    MỘT CHÚT còn hơn cắt hỏng — tìm khoảng trắng gần nhất SAU giới hạn thay
    vì cắt giữa từ đó.
    """
    if not text:
        return ''
    if len(text) <= do_dai_toi_da:
        return text
    cat = text[:do_dai_toi_da]
    vi_tri_trang = cat.rfind(' ')
    if vi_tri_trang > 0:
        return cat[:vi_tri_trang].rstrip(' ,;:-')
    vi_tri_sau = text.find(' ', do_dai_toi_da)
    if vi_tri_sau == -1:
        return text   # không có khoảng trắng nào trong CẢ chuỗi -> trả nguyên, an toàn tuyệt đối
    return text[:vi_tri_sau].rstrip(' ,;:-')


def rut_gon_tieu_de_chong_trung(tieu_de, ma_goc, do_dai_toi_da=70):
    """Ver 5.1 — VÁ: phát hiện khi audit lại tool — 2 SKU có Tên hàng chỉ
    khác nhau ở PHẦN ĐUÔI (VD 'CVV 3x95+1x0mm2 (sc)' và 'CVV 3x95+1x0mm2
    (sc) - loại 2') bị `rut_gon_an_toan(..., 70)` cắt mất đúng phần khác
    biệt đó -> 2 title WordPress giống hệt nhau -> Google coi là duplicate
    title tag (hại SEO thật, KHÔNG phải giả thuyết — đã tự đếm ra 50 nhóm/
    120 dòng bị trùng trên MASTER thật, xem Audit-Checklist-Ver5.0.xlsx).

    Vá: khi câu GỐC dài hơn giới hạn (tức CHẮC CHẮN sẽ bị cắt), CHỪA sẵn
    chỗ cho ' · {ma_goc}' ở cuối trước khi cắt phần văn bản — mã hàng LUÔN
    duy nhất tuyệt đối trong MASTER (đã xác nhận, xem cot_import), nên 2
    title cắt từ 2 SKU khác nhau KHÔNG BAO GIỜ trùng nhau nữa, bất kể phần
    đầu giống nhau tới đâu. Câu GỐC đã đủ ngắn (không cần cắt) -> giữ
    NGUYÊN, không tự ý thêm mã hàng vào (tránh đổi hành vi không cần
    thiết cho phần lớn sản phẩm vốn không bị trùng)."""
    if not tieu_de:
        return tieu_de
    if len(tieu_de) <= do_dai_toi_da:
        return tieu_de   # không bị cắt -> không có rủi ro trùng, giữ nguyên hành vi cũ
    if not ma_goc:
        return rut_gon_an_toan(tieu_de, do_dai_toi_da)   # không có mã hàng để chống trùng -> hành vi cũ
    hau_to = f' · {ma_goc}'
    phan_van_ban = rut_gon_an_toan(tieu_de, max(do_dai_toi_da - len(hau_to), 10))
    return phan_van_ban + hau_to


def _thuong_hieu_gon(row):
    """Tên hãng ngắn lấy trực tiếp từ field thương hiệu, bỏ phần xuất xứ sau '/'."""
    hang = re.sub(r'\s+', ' ', str(row.get('thuong_hieu') or '')).strip()
    return hang.split('/', 1)[0].strip() if hang else ''


def _slug_mba_39(row, mau='chuan', hau_to=''):
    """Ver 3.9 C4 — slug transformer không chứa SKU/Cu-Cu/'chuan'.

    Công thức gốc: may-bien-ap-[dau|kho]-[hang]-[kVA]-[so-pha]-[loi].
    Hai discriminator nguồn được thêm CHỈ khi cần để không tái tạo collision
    đã đo trên MASTER Ver8 mà vẫn không đưa mã hàng trở lại URL:
      - QĐ 107/QĐ 2608 cho hai họ Amorphous;
      - cấp điện áp cho THIBIDI 1 pha Amorphous, vì cùng QĐ 107 nhưng có
        cả biến thể 12,7/0,23kV và 22/0,23kV.
    KP khô bỏ số pha và Cu/Cu đúng brief C4.
    """
    import dulieu as D
    loai = _phat_hien_loai_lam_mat(row.get('ten_goc', ''))
    hang = _thuong_hieu_gon(row)
    kva = _so_kva_tu_chuoi(row.get('cong_suat', ''))
    pha = _so_pha(row.get('ten_goc', ''))
    dac = _dac_tinh_loi(row.get('ten_goc', ''))
    loi = dac[4:].strip() if dac.lower().startswith('lõi ') else ''

    phan = ['may-bien-ap', loai, hang, f'{kva:g}kva' if kva is not None else '']
    la_kp_kho = (loai == 'kho' and hang.casefold() == 'kp')
    if pha and not la_kp_kho:
        phan.append(pha)
    if loi and not la_kp_kho:
        phan.append(loi)

    qd = _nhan_quyet_dinh(row)
    if qd:
        phan.append(qd)
    if (hang.casefold() == 'thibidi' and pha == '1 pha'
            and loi.casefold() == 'amorphous'):
        cap = _cap_ap_gon(row.get('cap_dien_ap'))
        if cap:
            phan.append(cap)

    slug = D.slugify('-'.join(str(x) for x in phan if x), dai=110)
    if mau and mau != 'chuan':
        mau_slug = D.slugify(str(mau), dai=24)
        if mau_slug:
            slug += '-' + mau_slug
    if hau_to:
        ht = D.slugify(str(hau_to), dai=24)
        if ht:
            slug += '-' + ht
    return slug


def dung_slug(row, mau='chuan', hau_to=''):
    """Sinh slug. Ver 3.9: máy biến áp dùng công thức C4; nhóm khác giữ đường cũ."""
    import dulieu as D

    # Ver 4.5 — Slug chỉ định: nếu MASTER có sẵn cột 'Slug chỉ định' thì DÙNG
    # NGUYÊN VĂN, không tính lại. tien_kiem_slug.py sinh cột này và bảo đảm
    # không trùng; bài đã đăng thì giữ nguyên slug cũ trong cột đó nên URL
    # không bao giờ tự đổi sau lưng. Excel thấy gì -> web ra đúng vậy.
    chi_dinh = str(row.get('slug_chi_dinh') or '').strip()
    if chi_dinh:
        s_cd = D.slugify(chi_dinh, dai=140)
        if s_cd:
            if mau and mau != 'chuan':
                ms = D.slugify(str(mau), dai=24)
                if ms:
                    s_cd += '-' + ms
            if hau_to:
                ht = D.slugify(str(hau_to), dai=24)
                if ht:
                    s_cd += '-' + ht
            return s_cd

    if row.get('outline_id') == 'outline_may_bien_ap':
        return _slug_mba_39(row, mau=mau,
                            hau_to=hau_to or row.get('hau_to_slug', ''))

    # Nhóm ngoài MBA giữ nguyên hành vi 3.8 để không mở blast-radius ngoài task C.
    if _slug_ngan():
        tieu_de = rut_gon_an_toan(dung_tieu_de(row), 95)
    else:
        tieu_de = rut_gon_an_toan(row.get('ten_goc', ''), 65)
    tieu_de_slug = D.slugify(tieu_de, dai=110) if tieu_de else ''

    ma = (row.get('ma_goc') or row.get('record_id') or '').lower()
    ma_slug = _SLUG_XAU_RE.sub('-', ma).strip('-') or 'san-pham'
    mau_slug = _SLUG_XAU_RE.sub('-', (mau or 'chuan').lower()).strip('-') or 'chuan'

    if _slug_ngan():
        phan = [tieu_de_slug] if len(tieu_de_slug) >= 20 else [tieu_de_slug, ma_slug]
        phan = [p for p in phan if p]
        if mau and mau != 'chuan':
            phan.append(mau_slug)
    else:
        phan = [p for p in (tieu_de_slug, ma_slug, mau_slug) if p]
    slug = '-'.join(phan)
    if hau_to:
        hau_to_slug = _SLUG_XAU_RE.sub('-', str(hau_to).lower()).strip('-')
        if hau_to_slug:
            slug += f'-{hau_to_slug}'
    return slug

def dung_danh_muc(row):
    """Cây danh mục WooCommerce suy từ dữ liệu, KHÔNG gọi AI.

    Ver 3.6.4 — trước đây payload không gửi 'categories' nên sản phẩm TẠO
    MỚI rơi vào "Chưa phân loại". Bài đã có thì không bị ảnh hưởng (Woo giữ
    nguyên danh mục khi PUT không kèm trường này), nhưng lô 250 bài sắp
    soạn đều là tạo mới.

    Trả list tên danh mục, cha trước con sau. Rỗng nếu không suy được —
    không đoán bừa.
    """
    outline = row.get('outline_id') or ''
    ten = str(row.get('ten_goc') or '').lower()

    if outline == 'outline_vo_may_bien_ap':
        return ['Phụ kiện máy biến áp', 'Vỏ bảo vệ máy biến áp']
    if 'giá treo' in ten:
        return ['Phụ kiện máy biến áp', 'Giá treo máy biến áp']
    if outline == 'outline_may_bien_ap':
        loai = _phat_hien_loai_lam_mat(row.get('ten_goc', ''))
        con = {'dau': 'Máy biến áp dầu', 'kho': 'Máy biến áp khô'}.get(loai)
        return ['Máy biến áp', con] if con else ['Máy biến áp']
    if outline == 'outline_do_luong':
        for khoa, nhan in (('mof', 'Hợp bộ đo lường MOF'),
                           ('công tơ', 'Công tơ điện'),
                           ('biến dòng', 'Biến dòng điện'),
                           ('đồng hồ', 'Đồng hồ đo điện')):
            if khoa in ten:
                return ['Thiết bị đo lường điện', nhan]
        return ['Thiết bị đo lường điện']
    return []


def _gia_tri_meta(row, field, mau_regex=''):
    v = str(row.get(field) or '').strip()
    if v:
        return v
    return _tim_trong_cot_dong(row, mau_regex) if mau_regex else ''


def _gan_don_vi_meta(v, don_vi):
    """Gắn đơn vị khi ô nguồn chỉ có số; không nhân đôi nếu nguồn đã có đơn vị."""
    s = re.sub(r'\s+', ' ', str(v or '')).strip()
    if not s:
        return ''
    if re.search(r'[A-Za-z%²]', s):
        return s
    return f'{s}{don_vi}'


def _gia_tri_meta_an_toan(row, nhan, field, mau_regex, don_vi):
    """Chọn số thật mà Hard Block hiện có xác minh được, không nới Hard Block."""
    ung_vien = []
    dong = _tim_trong_cot_dong(row, mau_regex) if mau_regex else ''
    if dong:
        ung_vien.append(dong)
    fixed = str(row.get(field) or '').strip()
    if fixed and fixed not in ung_vien:
        ung_vien.append(fixed)
    for v in ung_vien:
        co_dv = _gan_don_vi_meta(v, don_vi)
        if co_dv and not kiem_tra_bia(f'{nhan} {co_dv}', row):
            return co_dv
    return ''


def _rank_math_rut_gon_an_toan(row):
    """Meta code-only, không số kỹ thuật, dùng khi Hard Block chỉ chặn meta."""
    outline = str(row.get('outline_id') or '')
    brand = re.sub(r'\s+', ' ', str(row.get('thuong_hieu') or '')).strip()
    if outline == 'outline_vo_may_bien_ap':
        goc = 'Vỏ mạ kẽm nhúng nóng'
    elif outline == 'outline_may_bien_ap':
        goc = 'Máy biến áp'
    elif outline == 'outline_phu_kien':
        goc = 'Phụ kiện thiết bị điện'
    else:
        goc = 'Sản phẩm thiết bị điện'
    if brand:
        goc += ' ' + brand
    return {
        'rank_math_focus_keyword': rut_gon_an_toan(goc, 70),
        'rank_math_title': rut_gon_an_toan(goc + ' | MBA Việt Nam', 60),
        'rank_math_description': rut_gon_an_toan(goc + '. Liên hệ báo giá và tư vấn kỹ thuật.', 160),
    }


def _rank_math_fail_soft(row, meta, tra_canh_bao=False):
    """Ver 4.4.1 — mọi đường Rank Math dùng cùng luật META fail-soft.

    Không sửa Hard Block. Chỉ đổi hậu quả: meta vi phạm -> meta code-only
    không số + cảnh báo; thân bài vẫn do Hard Block core quyết định như cũ.
    """
    vi_pham = {}
    for k, v in (meta or {}).items():
        chan = kiem_tra_bia(str(v or ''), row)
        if chan:
            vi_pham[k] = chan
    canh_bao = ''
    if vi_pham:
        chi_tiet = '; '.join(f'{k}: {v}' for k, v in vi_pham.items())
        meta = _rank_math_rut_gon_an_toan(row)
        canh_bao = f'CẢNH BÁO META RANK MATH: Hard Block chặn {chi_tiet}; đã dùng meta rút gọn an toàn.'
    return (meta, canh_bao) if tra_canh_bao else meta


def dung_rank_math(row, bai, tra_canh_bao=False):
    """Ba trường Rank Math sinh bằng code; MBA Ver 3.9 theo bộ định danh C5."""
    if row.get('outline_id') == 'outline_may_bien_ap':
        loai = _phat_hien_loai_lam_mat(row.get('ten_goc', ''))
        nhan_loai = {'dau': 'dầu', 'kho': 'khô'}.get(loai, loai)
        hang = _thuong_hieu_gon(row)
        kva = _so_kva_tu_chuoi(row.get('cong_suat', ''))
        pha = _so_pha(row.get('ten_goc', ''))
        dac = _dac_tinh_loi(row.get('ten_goc', ''))
        loi = dac[4:].strip() if dac.lower().startswith('lõi ') else ''
        cap = _cap_ap_gon(row.get('cap_dien_ap'))

        # Focus keyword: chỉ ghép thành phần THẬT có trong record. KP không
        # ghi số pha/lõi trong MASTER thì không tự suy 3 pha hay coi Cu/Cu là lõi.
        qd = _nhan_quyet_dinh(row)
        focus_parts = ['máy biến áp', nhan_loai, hang,
                       f'{kva:g}kVA' if kva is not None else '', pha, loi, qd]
        # MASTER Ver8 chứng minh bộ cơ bản vẫn trùng 25 nhóm/50 dòng. Với
        # THIBIDI 1 pha Amorphous, cùng QĐ 107 nhưng khác cấp điện áp nên
        # thêm cấp áp thật để giữ focus keyword duy nhất, không dùng SKU.
        if (hang.casefold() == 'thibidi' and pha == '1 pha'
                and loi.casefold() == 'amorphous' and cap):
            focus_parts.append(cap)
        tu_khoa = re.sub(r'\s+', ' ', ' '.join(str(x) for x in focus_parts if x)).strip()
        tu_khoa = rut_gon_an_toan(tu_khoa, 90)

        title_parts = ['Báo giá Máy biến áp', nhan_loai, hang,
                       f'{kva:g}kVA' if kva is not None else '', cap, qd]
        title_core = re.sub(r'\s+', ' ', ' '.join(str(x) for x in title_parts if x)).strip()
        title_full = f'{title_core} | MBA Việt Nam'
        # Ưu tiên giữ đủ bộ định danh + cấp điện áp; nếu >60 thì bỏ brand site
        # trước, chỉ cắt core khi bản thân core vẫn vượt 60.
        seo_title = title_full if len(title_full) <= 60 else title_core
        if len(seo_title) > 60:
            seo_title = rut_gon_an_toan(seo_title, 60)

        # Description chỉ ghép số có thật. Không có mệnh đề "đang cập nhật",
        # không ước lượng, không hứa giá. Thêm từng mảnh nguyên vẹn để không
        # cắt dở số+đơn vị ở mốc 160 ký tự.
        desc_parts = ['Máy biến áp', nhan_loai, hang,
                      f'{kva:g}kVA' if kva is not None else '', pha, loi, qd]
        ident = re.sub(r'\s+', ' ', ' '.join(str(x) for x in desc_parts if x)).strip()
        cap_meta = _gan_don_vi_meta(row.get('cap_dien_ap'), 'kV')
        if cap_meta and cap_meta not in ident:
            ident += f' {cap_meta}'
        manh = [ident]
        specs = [
            ('Po', _gia_tri_meta_an_toan(row, 'Po', 'ton_hao_khong_tai', r'tổn hao không tải|\bpo\b', 'W')),
            ('Pk', _gia_tri_meta_an_toan(row, 'Pk', 'ton_hao_ngan_mach', r'tổn hao.*(?:có tải|ngắn mạch)|\bpk\b', 'W')),
            ('Uk', _gia_tri_meta_an_toan(row, 'Uk', 'dien_ap_ngan_mach', r'điện áp ngắn mạch|\buk\b', '%')),
            ('Io', _gia_tri_meta_an_toan(row, 'Io', 'dong_khong_tai', r'dòng điện không tải|\bio\b', '%')),
            ('Hiệu suất', _gia_tri_meta_an_toan(row, 'Hiệu suất', 'hieu_suat_e50', r'hiệu suất', '%')),
        ]
        for nhan, v in specs:
            if not v:
                continue
            ung_vien = ', '.join(manh + [f'{nhan} {v}']) + '.'
            if len(ung_vien) <= 160:
                manh.append(f'{nhan} {v}')
        mo_ta = ', '.join(manh) + '.'
        meta = {'rank_math_focus_keyword': tu_khoa,
                'rank_math_title': seo_title,
                'rank_math_description': mo_ta}
        return _rank_math_fail_soft(row, meta, tra_canh_bao)

    # Nhóm ngoài MBA giữ NGUYÊN logic 3.8 để task C không mở rộng phạm vi.
    tieu_de = bai.get('title') or dung_tieu_de(row)
    tieu_de = re.sub(r'\s+', ' ', str(tieu_de)).strip()
    tu_khoa = re.sub(r'^\s*Báo giá\s+', '', tieu_de, flags=re.I)
    tu_khoa = re.sub(r'\s*\([^)]*\)\s*$', '', tu_khoa).strip()
    tu_khoa = rut_gon_an_toan(tu_khoa, 70)

    ten_site = 'MBA Việt Nam'
    khong_ngoac = re.sub(r'\s*\([^)]*\)\s*$', '', tieu_de).strip()
    for ung_vien in (f'{tieu_de} | {ten_site}', tieu_de,
                     f'{khong_ngoac} | {ten_site}', khong_ngoac):
        if len(ung_vien) <= 60:
            seo_title = ung_vien
            break
    else:
        seo_title = rut_gon_an_toan(khong_ngoac, 60)

    manh = [tu_khoa]
    dac = _dac_tinh_loi(row.get('ten_goc', ''))
    if dac:
        manh.append(dac)
    po = row.get('ton_hao_khong_tai') or _tim_trong_cot_dong(row, r'tổn hao không tải|\bpo\b')
    if po:
        manh.append(f'tổn hao không tải {po}W')
    hs = row.get('hieu_suat_e50') or _tim_trong_cot_dong(row, r'hiệu suất')
    if hs:
        manh.append(f'hiệu suất {hs}%')
    mo_ta = ', '.join(manh) + '. Báo giá và tư vấn kỹ thuật trong giờ làm việc.'

    meta = {'rank_math_focus_keyword': tu_khoa,
            'rank_math_title': seo_title,
            'rank_math_description': rut_gon_an_toan(mo_ta, 160)}
    return _rank_math_fail_soft(row, meta, tra_canh_bao)

def dung_goi_cap_nhat_seo(row, mau='chuan'):
    """Ver 3.9 C6 — dữ liệu metadata-only cho đúng phạm vi C1-C5.

    Chỉ target máy biến áp (C1/C3/C4/C5) và MOF (C2). Nhóm khác trả {} để
    batch không ghi lại title/slug/meta ngoài phạm vi task.
    """
    outline = row.get('outline_id')
    la_mof = (outline == 'outline_do_luong'
              and re.search(r'\bMOF\b', str(row.get('ten_goc') or ''), re.I))
    if outline != 'outline_may_bien_ap' and not la_mof:
        return {}
    title = dung_tieu_de(row)
    slug = dung_slug(row, mau=mau)
    meta, canh_bao = dung_rank_math(row, {'title': title}, tra_canh_bao=True)
    goi = {'title': title, 'slug': slug, 'meta_rank_math': meta}
    if canh_bao:
        goi['canh_bao_meta'] = canh_bao
    return goi


def _tim_trong_cot_dong(row, mau_regex):
    """Lấy giá trị SỐ đầu tiên từ cột động khớp regex. Rỗng nếu không có —
    KHÔNG bịa, Hard Block áp cho meta y như áp cho nội dung."""
    dong = row.get('thong_so_dong') or {}
    if not isinstance(dong, dict):
        return ''
    for k, v in dong.items():
        if re.search(mau_regex, str(k), re.I) and re.match(r'^\s*[\d.,]+\s*$', str(v)):
            return str(v).strip()
    return ''


CHECKLIST_BAO_GIA = {
    'cap_dien': ['Mã hàng hoặc quy cách cần mua', 'Số mét cần đặt',
                'Địa điểm giao hàng', 'Thời gian cần hàng',
                'Có cần catalogue hoặc CO/CQ không'],
    'tu_va_thiet_bi_dong_cat': ['Mã thiết bị', 'Điện áp định mức', 'Dòng định mức',
                               'Số lượng', 'Có cần hồ sơ kỹ thuật không'],
    'may_bien_ap_do_luong': ['Mã thiết bị', 'Công suất (kVA)', 'Cấp điện áp',
                            'Số lượng', 'Có cần hồ sơ kỹ thuật không'],
    'phu_kien_va_khac': ['Mã hàng', 'Số lượng', 'Địa điểm giao hàng', 'Thời gian cần hàng'],
}


# ============================================================ Ver 4.9.7 — khối cố định "về máy biến áp nói chung"
# Thịnh duyệt hướng (demo HTML mẫu SKU MBT3P250A2608, 29/07/2026): tách sự
# thật ĐÚNG CHO CẢ DÒNG (nguyên lý làm mát, ứng dụng chung, tiêu chuẩn
# ngành, lưu ý lắp đặt) ra khối do CODE viết cứng — KHÔNG phải AI đoán mỗi
# lần. Máy biến áp DẦU và KHÔ khác nguyên lý làm mát HOÀN TOÀN (dầu ONAN
# tuần hoàn dầu, khô AN/AF không dầu) — nếu áp nhầm khối dầu cho SKU khô là
# bịa sai thông tin kỹ thuật thật. Phải tách 2 bản riêng, route theo loại
# phát hiện được từ Tên hàng — KHÔNG hiện khối nào nếu không nhận diện
# được loại (an toàn hơn hiện sai).
def _phat_hien_loai_lam_mat(ten_goc):
    """Trả 'dau' | 'kho' | None. Đọc trực tiếp Tên hàng — MASTER đặt tên
    nhất quán "Máy biến áp dầu ..."/"Máy biến áp khô ..." (đã kiểm tra thật
    245 dòng sheet 03_May_Bien_Ap_Do_Luong, không phải suy đoán mẫu)."""
    t = (ten_goc or '').lower()
    if 'khô' in t:
        return 'kho'
    if 'dầu' in t:
        return 'dau'
    return None


def _phat_hien_so_pha(ten_goc):
    """Trả '1' | '3' | None — đọc '1pha'/'3pha' (có/không khoảng trắng)
    trong Tên hàng, đúng định dạng MASTER đang dùng."""
    t = (ten_goc or '').lower().replace(' ', '')
    if '1pha' in t:
        return '1'
    if '3pha' in t:
        return '3'
    return None


_UNG_DUNG_THEO_PHA = {
    '1': 'thường dùng cho phụ tải phân tán, mật độ thấp — khu vực nông thôn, tuyến đường dây dài ít hộ dùng điện trên mỗi trạm.',
    '3': 'thường dùng cho phụ tải tập trung, mật độ cao — khu dân cư, khu công nghiệp, tòa nhà cần công suất lớn và cân bằng pha tốt.',
}


# ============================================================ Ver 4.9.9 — helper máy biến áp: tier/delta/tải ước tính/đặc tính lõi
_TIER_BAC = [
    (0, 250, 'nhỏ (dưới 250kVA)'),
    (250, 1000, 'trung (250-1000kVA)'),
    (1000, float('inf'), 'lớn (trên 1000kVA)'),
]


def _so_kva_tu_chuoi(s):
    """Ép chuỗi kiểu '160 kVA'/'160'/'12.7' về float. Không parse được ->
    None (an toàn, không crash, không suy đoán)."""
    if s is None:
        return None
    t = str(s)
    m = re.search(r'\d+(?:[.,]\d+)?', t)
    if not m:
        return None
    try:
        gt = float(m.group(0).replace(',', '.'))
    except ValueError:
        return None
    # Ver 4.5 — TRƯỚC ĐÂY đọc '25/40/63MVA' ra 25 kVA (sai 1.000 lần), ảnh
    # hưởng slug, tier công suất và delta context. Nhận đơn vị MVA và quy đổi.
    duoi = t[m.end():]
    m2 = re.match(r'^[\d./,\s()-]*?(mva|kva)\b', duoi, re.IGNORECASE)
    if m2 and m2.group(1).lower() == 'mva':
        gt *= 1000.0
    return gt


def _xac_dinh_tier(kva):
    """Trả nhãn tier (nhỏ/trung/lớn) theo mốc _TIER_BAC. kva=None -> ''."""
    if kva is None:
        return ''
    for lo, hi, nhan in _TIER_BAC:
        if lo <= kva < hi:
            return nhan
    return ''


def _so_pha(ten_goc):
    """'1Pha' / '3 pha' / '1P' -> '1 pha' | '3 pha' | ''. Đọc TÊN HÀNG,
    không đọc mã hàng (mã do người đặt, mỗi đợt một quy ước)."""
    t = str(ten_goc or '')
    if re.search(r'\b1\s*pha|\b1P\b', t, re.I):
        return '1 pha'
    if re.search(r'\b3\s*pha|\b3P\b', t, re.I):
        return '3 pha'
    return ''


def _cap_ap_gon(cap_dien_ap):
    """'12.7/0.23 kV' -> '12,7/0,23kV'. Rỗng nếu không có."""
    s = str(cap_dien_ap or '').strip()
    if not s:
        return ''
    s = re.sub(r'\s*kv\s*$', '', s, flags=re.I).strip()
    if not re.search(r'\d', s):
        return ''
    return s.replace('.', ',') + 'kV'


# Ver 3.6.4 — nhãn phân biệt hai họ Amorphous của MBT/THIBIDI.
# A107 theo QĐ 107/QĐ-HĐTV (TCCS 10:2021/EVN, EVN trung ương), A2608 theo
# QĐ 2608/QĐ-EVN SPC (tổng công ty miền Nam). Po/Pk hiện giống nhau nên
# không có nhãn kỹ thuật nào để phân biệt. Dùng số hiệu quyết định vì
# THIBIDI TỰ ghi "QĐ 107/QĐ-HĐTV" vào tên sản phẩm của họ — trong ngành
# này đó là cách phân biệt bình thường, không phải thuật ngữ khó hiểu.
def _nhan_quyet_dinh(row):
    t = (str(row.get('ten_goc') or '') + ' ' +
         str(row.get('quy_cach') or '') + ' ' +
         str(row.get('ma_goc') or '')).upper()
    if '2608' in t:
        return 'QĐ 2608'
    if '107' in t and 'A107' in t.replace(' ', '') or '107/QĐ' in t:
        return 'QĐ 107'
    return ''


def _dac_tinh_loi(ten_goc):
    """Bóc 1 cụm ngắn mô tả đặc tính lõi/vật liệu NẾU đã có sẵn trong Tên
    hàng — dùng cho tiêu đề SKU-first. Không tìm thấy -> '' (KHÔNG suy
    đoán loại lõi khi Tên hàng không ghi rõ)."""
    t = (ten_goc or '').lower()
    if 'cu/cu' in t or 'đồng/đồng' in t:
        return 'dây đồng Cu/Cu'
    if 'amorphous' in t:
        return 'lõi Amorphous'
    if 'silic' in t:
        return 'lõi Silic'
    return ''


# Ver 3.5.1 — VÁ theo Thịnh: title đang viết hoa loạn ("Báo Giá Máy biến áp
# Dầu THIBIDI 2500kVA (Lõi Silic)") vì mỗi mảnh ghép do một hàm khác nhau
# sinh ra, mỗi hàm tự quyết viết hoa. Nay MỌI mảnh đều chữ thường, chỉ hoa
# đúng một chữ đầu câu ở đây — trừ tên riêng.
#
# Tên riêng KHÔNG được hạ chữ hoa: thương hiệu lấy nguyên văn từ MASTER
# (THIBIDI, MBT, GELEX EMIC...), đơn vị kVA/kV, vật liệu theo cách
# catalogue viết (Silic, Amorphous, Cu/Cu). Vì vậy hàm này CHỈ đụng ký tự
# ĐẦU TIÊN, không dùng .capitalize() (nó sẽ hạ THIBIDI thành Thibidi).
def _hoa_dau_cau(s):
    s = (s or '').strip()
    return (s[0].upper() + s[1:]) if s else s


def _uoc_tinh_tai_kw(kva, he_so_cong_suat=0.8):
    """Ước tính dải tải kW tương ứng công suất kVA, GIẢ ĐỊNH cosφ cố định
    (mặc định 0.8 — hệ số phổ biến cho phụ tải hỗn hợp dân dụng/công
    nghiệp nhẹ, KHÔNG phải số đo thật của SKU). LUÔN trả kèm chú thích rõ
    đây là ước tính giả định — tuyệt đối không được dùng như số đo thật.
    kva=None -> '' (không suy đoán khi thiếu công suất).

    Ver 2.0 — VÁ LỖI THẬT (phát hiện lúc debug VNMBA1P1S, 1kVA): làm tròn
    số nguyên khiến máy công suất nhỏ ra khoảng "1-1 kW" (thấp=cao sau
    làm tròn, đọc kỳ cục, và nghi là nguồn gốc góp phần vào lỗi Hard Block
    chặn nhầm text AI viết cho SKU này — dù chưa tái hiện được chính xác
    nguyên nhân gốc, sửa luôn vì đây LÀ bug thật, độc lập đáng sửa).
    Nếu làm tròn ra trùng số, trả 1 số duy nhất, không hiện khoảng giả."""
    if kva is None:
        return ''
    tai = kva * he_so_cong_suat
    thap = round(tai * 0.9)
    cao = round(tai * 1.0)
    if thap == cao:
        return f'{cao} kW (ước tính, giả định cosφ={he_so_cong_suat})'
    return f'{thap}-{cao} kW (ước tính, giả định cosφ={he_so_cong_suat})'


def tinh_delta_context(row, cung_dong):
    """Ver 4.9.9 — tính TOÀN BỘ số liệu so sánh/tier/tải bằng CODE (không
    để AI tự tính) rồi trả dict field để CHÈN vào row trước khi build
    prompt — các field này phải được khai báo trong
    PROFILES['may_bien_ap_do_luong']['cot_ai'] và
    OUTLINES['outline_may_bien_ap']['cot_ai'] (profiles.py) thì Hard Block
    (_kho_cua_dong/_kho_mo_rong_cua_dong) mới nhận các số này là "có nguồn
    thật", không chặn nhầm là bịa.

    Lý do bắt buộc tính bằng code: để AI tự làm phép tính % chênh lệch/tải
    kW giữa các SKU sẽ bị Hard Block chặn (số AI tự suy ra không khớp
    chuỗi nguồn) — và quan trọng hơn, tự tính dễ sai/bịa hơn code thuần.

    Trả {} nếu record hiện tại không phải outline_may_bien_ap/outline_vo_
    may_bien_ap hoặc không có công suất hợp lệ — an toàn, không suy đoán.

    Ver 5.2 — mở rộng áp dụng cho outline_vo_may_bien_ap (Vỏ bảo vệ) —
    cỡ vỏ cũng có ý nghĩa so sánh thật (khớp đúng cỡ máy nào), không phải
    chỉ riêng máy biến áp thật mới cần."""
    if row.get('outline_id') not in ('outline_may_bien_ap', 'outline_vo_may_bien_ap'):
        return {}
    kva_hien_tai = _so_kva_tu_chuoi(row.get('cong_suat', ''))
    if kva_hien_tai is None:
        return {}

    ket_qua = {'tier_cong_suat': _xac_dinh_tier(kva_hien_tai)}
    # Ver 5.2 — VÁ: "tải ước tính (kW)" chỉ có nghĩa cho MÁY biến áp thật
    # (công suất tiêu thụ) — vỏ bảo vệ không tiêu thụ điện, tính "tải" cho
    # vỏ là vô nghĩa. Phát hiện khi tự test lại sau khi mở rộng hàm này.
    if row.get('outline_id') == 'outline_may_bien_ap':
        ket_qua['tai_uoc_tinh'] = _uoc_tinh_tai_kw(kva_hien_tai)

    if not cung_dong:
        return ket_qua

    # SKU liền kề nhỏ hơn/lớn hơn gần nhất trong danh sách cung_dong (đã
    # sort tăng dần theo công suất từ db_phase2.tim_san_pham_cung_dong).
    nho_hon = [s for s in cung_dong if (_so_kva_tu_chuoi(s.get('cong_suat')) or 1e18) < kva_hien_tai]
    lon_hon = [s for s in cung_dong if (_so_kva_tu_chuoi(s.get('cong_suat')) or -1) > kva_hien_tai]

    if nho_hon:
        sp = nho_hon[-1]
        kva_no = _so_kva_tu_chuoi(sp.get('cong_suat'))
        if kva_no:
            chenh = kva_hien_tai - kva_no
            pt = round(chenh / kva_no * 100, 1) if kva_no else 0
            # Ver 2.7 — BỎ MÃ SKU khỏi context (Thịnh nhắc lần thứ 3).
            # Trước đây chỉ DẶN prompt đừng nhắc mã, nhưng mã vẫn nằm trong
            # context nên AI vẫn dùng. Không đưa thì AI không nhắc được.
            ket_qua['sku_lien_ke_nho'] = f"phiên bản {kva_no:g}kVA"
            ket_qua['chenh_lech_nho'] = (
                f"+{chenh:g}kVA (bản này cao hơn {pt}% so với bản {kva_no:g}kVA)")

    if lon_hon:
        sp = lon_hon[0]
        kva_lo = _so_kva_tu_chuoi(sp.get('cong_suat'))
        if kva_lo:
            chenh = kva_lo - kva_hien_tai
            # Ver 2.7 — VÁ LỖI % 2 CHIỀU (bản đối chiếu phát hiện, đã verify):
            # 100 -> 160 là TĂNG 60% (mốc 100), nhưng 160 -> 100 là GIẢM
            # 37.5% (mốc 160). Bản cũ chỉ đưa 1 con số 37.5 mà không ghi rõ
            # mốc -> AI đảo chiều thành "160kVA cao hơn 37.5%" là SAI.
            # Giờ ghi rõ CẢ HAI chiều với mốc kèm theo, AI không đảo nhầm được.
            pt_giam = round(chenh / kva_lo * 100, 1) if kva_lo else 0
            pt_tang = round(chenh / kva_hien_tai * 100, 1) if kva_hien_tai else 0
            ket_qua['sku_lien_ke_lon'] = f"phiên bản {kva_lo:g}kVA"
            ket_qua['chenh_lech_lon'] = (
                f"-{chenh:g}kVA (bản này thấp hơn {pt_giam}% so với bản {kva_lo:g}kVA; "
                f"ngược lại bản {kva_lo:g}kVA cao hơn bản này {pt_tang}%)")

    return ket_qua


def dung_tieu_de(row):
    """Ver 5.0 — VÁ theo Thịnh: bản Ver 4.9.9 nhét cả mã hàng vào title
    ("...MBT1P15A2608 (Lõi Amorphous)") — Thịnh xem thật trên site thấy
    "ngốc nghếch". Bỏ mã hàng khỏi title (mã hàng vẫn hiện đầy đủ trong
    Hero/bảng thông số/SKU WooCommerce, không mất thông tin).

    Ver 5.2 — VÁ 2 lỗi Thịnh phát hiện qua ảnh chụp site thật:
    (1) "Báo Giá" đưa lên ĐẦU câu (trước đây để cuối) — VD "Báo Giá Máy
    biến áp MBT 250kVA (Lõi Amorphous)" thay vì ngược lại.
    (2) THÊM NHÁNH RIÊNG cho outline_vo_may_bien_ap — trước đây hàm này
    CHỈ gate theo outline_id == 'outline_may_bien_ap', nên "Vỏ mạ kẽm
    nhúng nóng MBA..." (KHÔNG phải máy biến áp) vẫn lọt qua công thức
    "Máy biến áp [Thương hiệu] [X]kVA" — SAI SỰ THẬT (gọi vỏ thép thành
    máy biến áp). Đây là lỗi thật do thêm outline mới (Ver 5.0-5.1) mà
    không rà lại toàn bộ hàm dùng chung outline_may_bien_ap.
    """
    if row.get('outline_id') == 'outline_vo_may_bien_ap':
        thuong_hieu = row.get('thuong_hieu', '')
        kva = _so_kva_tu_chuoi(row.get('cong_suat', ''))
        phan = ['vỏ bảo vệ máy biến áp']
        if thuong_hieu:
            phan.append(thuong_hieu)
        if kva is not None:
            phan.append(f'{kva:g}kVA')
        # Ver 3.6.4 — vỏ cũng trùng tiêu đề vì thiếu số pha
        # (MBTVMK1P50 với MBTVMK3P50 cùng tên).
        pha = _so_pha(row.get('ten_goc', ''))
        if pha:
            phan.append(pha)
        cap = _cap_ap_gon(row.get('cap_dien_ap'))
        if cap:
            phan.append(cap)
        return _hoa_dau_cau('Báo giá ' + ' '.join(phan))
    if row.get('outline_id') != 'outline_may_bien_ap':
        ten_goc = re.sub(r'\s*[\r\n]+\s*', ' · ', str(row.get('ten_goc', '') or '')).strip()
        # Ver 3.9 C2 — MOF: không dùng meta_title AI chung chung. Tỷ số biến
        # dòng có thật trong Tên hàng là discriminator; đưa thẳng vào title.
        if row.get('outline_id') == 'outline_do_luong' and re.search(r'\bMOF\b', ten_goc, re.I):
            m = re.search(r'tỷ\s*số\s*biến\s*dòng\s*:\s*([^·\r\n]+)', ten_goc, re.I)
            ty_so = re.sub(r'[.\s]+$', '', m.group(1)).strip() if m else ''
            cap = _cap_ap_gon(row.get('cap_dien_ap'))
            hang_xuat_xu = re.sub(r'\s*/\s*', ' ', str(row.get('thuong_hieu') or '')).strip()
            hang_xuat_xu = re.sub(r'\s+', ' ', hang_xuat_xu)
            phan = ['Hợp bộ đo lường (MOF)', cap, hang_xuat_xu, ty_so, 'chính hãng']
            return re.sub(r'\s+', ' ', ' '.join(x for x in phan if x)).strip()

        # Ver 4.6.2 — CÁP ĐIỆN: trước đây lấy nguyên Tên hàng làm title
        # ("Dây CXV/DSTA3x95mm2 (0.6/1kV) - Cadivi"). GSC: CTR ở vị trí 1
        # mới 7,6% trong khi chuẩn 25-30% -> traffic mất ở tầng tiêu đề chứ
        # không phải tầng xếp hạng. Truy vấn cấp SKU (có tiết diện) CTR
        # 6,07% vs 2,74% -> tiết diện PHẢI nằm trong title.
        # Đưa thêm DÒNG TẢI vào title: vừa bắt đúng cụm "chịu tải bao nhiêu"
        # (41 truy vấn, vị trí TB 3,1, CTR 2,97%), vừa là con số KHÁC NHAU
        # giữa từng SKU nên không còn title na ná.
        if row.get('outline_id') == 'outline_cap_dien':
            lo = re.sub(r'^\s*(dây|cáp)\s+', '', ten_goc, flags=re.I)
            lo = re.sub(r'\s*-\s*[A-Za-zÀ-ỹ ]+$', '', lo).strip()   # bỏ đuôi "- Cadivi"
            hang = str(row.get('thuong_hieu') or '').strip()
            phan = ['Cáp ' + lo if lo else ten_goc]
            if hang and hang.lower() not in lo.lower():
                phan.append(hang)
            I = str(row.get('dong_dien_dinh_muc_catalogue') or '').strip()
            m_i = re.search(r'\d+(?:[.,]\d+)?', I)
            if m_i:
                # LƯU Ý: KHÔNG dùng rstrip('0') — '360' sẽ thành '36'.
                # Chỉ bỏ phần thập phân khi nó bằng 0 (315.0 -> 315).
                gt = float(m_i.group(0).replace(',', '.'))
                phan.append(f'{gt:g}A')
            tieu_de_cap = ' '.join(x for x in phan if x)
            duoi = ' — báo giá, thông số kỹ thuật'
            # Google cắt title quanh 60 ký tự; ưu tiên giữ phần định danh.
            if len(tieu_de_cap) + len(duoi) > 65:
                duoi = ' — báo giá'
            return re.sub(r'\s+', ' ', tieu_de_cap + duoi).strip()
        return ten_goc
    loai = _phat_hien_loai_lam_mat(row.get('ten_goc', ''))
    nhan_loai = {'dau': 'dầu', 'kho': 'khô'}.get(loai, '')
    kva = _so_kva_tu_chuoi(row.get('cong_suat', ''))
    dac_tinh = _dac_tinh_loi(row.get('ten_goc', ''))

    # Ver 3.6.4 — thêm SỐ PHA và CẤP ĐIỆN ÁP. Trước đây thiếu hai trường
    # này nên 30/35 nhóm tiêu đề bị trùng nguyên văn: TBD1P50 với TBD3P50
    # cùng tên (khác số pha), TBD1P50A107 với TBD1P5022A107 cùng tên
    # (khác cấp điện áp 12,7kV và 22kV). Trùng tiêu đề -> WordPress đẻ
    # slug -2, -3 -> nhiều URL gần giống nhau vĩnh viễn.
    phan = ['máy biến áp']
    if nhan_loai:
        phan.append(nhan_loai)
    if row.get('thuong_hieu'):
        phan.append(row['thuong_hieu'])
    if kva is not None:
        phan.append(f'{kva:g}kVA')
    pha = _so_pha(row.get('ten_goc', ''))
    if pha:
        phan.append(pha)
    cap = _cap_ap_gon(row.get('cap_dien_ap'))
    if cap:
        phan.append(cap)
    tieu_de = ' '.join(phan)

    trong_ngoac = [x for x in (dac_tinh, _nhan_quyet_dinh(row)) if x]
    if trong_ngoac:
        tieu_de += ' (' + ', '.join(trong_ngoac) + ')'
    return _hoa_dau_cau('Báo giá ' + tieu_de)


# ============================================================ Ver 4.9.9 — khối "Về thương hiệu" (data catalogue THẬT đã đọc, không bịa)
# Chỉ 2 brand đã có catalogue/hồ sơ năng lực THẬT đọc qua trước đó (MBT,
# THIBIDI) — brand khác (VD KP/Hàn Quốc) CHƯA có nguồn nào đọc được, để
# TRỐNG, không suy đoán/không bịa thông tin công ty.
THONG_TIN_THUONG_HIEU = {
    'mbt': ('MBT (Công ty CP Thiết bị điện MBT) sản xuất máy biến áp tại nhà máy Hà Nội, '
           'đạt chứng nhận ISO 9001:2015, sử dụng dây chuyền đúc chân không Hübers và '
           'máy quấn dây LAE Italy.'),
    'thibidi': ('THIBIDI (thành viên Tổng công ty Thiết bị điện GELEX) sản xuất tại nhà máy '
               'Biên Hòa, Đồng Nai, có hợp tác chuyển giao công nghệ lõi Amorphous từ '
               'Hitachi Metals (Nhật Bản).'),
}


def khoi_anh_placeholder(nhan='ảnh sản phẩm'):
    """Ver 4.4 A1 — không phát placeholder ảnh ra HTML production.

    Ảnh thật do workspace ảnh chèn. Bài thiếu ảnh phải sạch hoàn toàn thay vì
    hiện ô nhắc việc nội bộ cho khách hoặc để Rank Math nhặt URL giả.
    """
    return ''


def khoi_ve_thuong_hieu(row):
    """Trả khối ngắn (1 câu) giới thiệu thương hiệu — CHỈ hiện nếu brand
    của SKU khớp 1 trong các brand đã có data thật ở THONG_TIN_THUONG_HIEU
    (so khớp không dấu, không phân biệt hoa/thường). Không khớp -> trả ''
    (KHÔNG bịa thông tin công ty cho brand chưa có nguồn)."""
    hang = (row.get('thuong_hieu') or '').lower()
    for key, mota in THONG_TIN_THUONG_HIEU.items():
        if key in hang:
            return f'<div {_st("khoi_thuong_hieu")}><p>{html.escape(mota)}</p></div>'
    return ''


# ============================================================ mục X — bảng so sánh công suất trong dòng

def _don_vi_kva(v):
    """Ver 3.3 — chuẩn hoá hiển thị công suất: "250" -> "250 kVA".
    Đã có đơn vị thì giữ nguyên; rỗng/không phải số -> trả nguyên văn."""
    t = str(v or '').strip()
    if not t:
        return ''
    if re.search(r'kva', t, re.IGNORECASE):
        return re.sub(r'\s*kva', ' kVA', t, flags=re.IGNORECASE)
    return f'{t} kVA' if re.fullmatch(r'\d+(?:[.,]\d+)?', t) else t


def khoi_so_sanh_cong_suat(row, cung_dong):
    """Ver 4.9.8 — bảng so sánh công suất trong dòng, 100% CODE dựng từ
    data thật (db_phase2.tim_san_pham_cung_dong), KHÔNG qua AI — tránh mọi
    rủi ro AI viết sai số khi so sánh nhiều SKU cùng lúc. `cung_dong`:
    list[{'ma_goc','ten_goc','cong_suat','cap_dien_ap','url'}] đã tìm sẵn,
    rỗng/None -> hàm trả '' (không hiện block nếu không có SKU anh em nào).

    CHỈ hiện tên sản phẩm + công suất, KHÔNG hiện cấp điện áp trong bảng
    này — phát hiện thật khi build: cột "Cấp Điện Áp (kV)" trong MASTER bị
    lỗi dữ liệu ở nhiều dòng máy biến áp (giá trị trùng với công suất). Ẩn
    cột này ở bảng so sánh cho tới khi Thịnh xác nhận sửa lại MASTER.

    Ver 4.9.9 — style INLINE, bỏ class "lotech-so-sanh-table" cũ.

    Ver 5.0 — thêm link khi SKU anh em đã đăng thật (url có).

    Ver 5.2 — VÁ LỖI THẬT (Thịnh xem site thấy toàn mã "MBTVM3P50" —
    "người ta đéo biết đâu"): Ver 5.0 chỉ giải quyết "bấm được" (thêm
    link) nhưng KHÔNG giải quyết "đọc hiểu được" — mã hàng bấm được vẫn là
    mã hàng, khách vẫn không biết nó là gì. Giờ hiện TÊN SẢN PHẨM (rút gọn
    an toàn, không cắt giữa từ) làm chữ hiển thị, mã hàng KHÔNG còn hiện
    trong bảng này nữa (vẫn còn đầy đủ trong bảng thông số phía trên)."""
    if not cung_dong:
        return ''
    ten_hien_tai = rut_gon_an_toan(row.get('ten_goc', '') or row.get('ma_goc', ''), 55)
    # Ver 3.3 — cột công suất trước đây in SỐ TRẦN ("250") -> khách không
    # biết đơn vị (Thịnh phát hiện trên bài thật). Dùng chung _don_vi_kva()
    # để mọi dòng cùng định dạng.
    dong_hien_tai = (f'<tr><td {_st("so_sanh_td_hien_tai")}>{html.escape(ten_hien_tai)} (đang xem)</td>'
                     f'<td {_st("so_sanh_td_hien_tai")}>'
                     f'{html.escape(_don_vi_kva(row.get("cong_suat","")))}</td></tr>')
    dong_khac = []
    for sp in cung_dong:
        ten = rut_gon_an_toan(sp.get('ten_goc', '') or sp.get('ma_goc', ''), 55)
        if sp.get('url'):
            hien_thi = f'<a href="{html.escape(sp["url"])}">{html.escape(ten)}</a>'
        else:
            hien_thi = html.escape(ten)
        dong_khac.append(f'<tr><td {_st("so_sanh_td")}>{hien_thi}</td>'
                         f'<td {_st("so_sanh_td")}>'
                         f'{html.escape(_don_vi_kva(sp["cong_suat"]))}</td></tr>')
    return (
        # Ver 2.6 — h2 này CHỈ dùng cho bố cục CŨ. Bố cục 2.5 tự sinh h2 qua
        # mo_section() -> nếu giữ lại sẽ ra 2 tiêu đề giống hệt nhau liền
        # kề (Thịnh phát hiện trên bài thật). Bỏ khi đang chạy bố cục 2.5.
        ('' if _dung_giao_dien_2_5() else '<h2>So sánh công suất trong dòng</h2>')
        + f'<table {_st("so_sanh_table")}><thead><tr>'
        f'<th {_st("so_sanh_th")}>Sản phẩm</th><th {_st("so_sanh_th")}>Công suất</th>'
        f'</tr></thead><tbody>{dong_hien_tai}{"".join(dong_khac)}</tbody></table>'
    )


def _phat_hien_loai_loi(ten_goc):
    """Ver 5.3 — CHỈ nhận diện loại LÕI (Silic/Amorphous), KHÔNG lẫn với
    vật liệu dây quấn (Cu/Cu) như _dac_tinh_loi() đang gộp chung cho mục
    đích tiêu đề. Dùng riêng cho khoi_ve_loi() — 2 khái niệm khác nhau
    (lõi = mạch từ, dây quấn = cuộn dây), không được lẫn khi viết nội dung
    kỹ thuật (khác hẳn tiêu đề chỉ cần 1 cụm ngắn gọn nhất tìm thấy)."""
    t = (ten_goc or '').lower()
    if 'amorphous' in t:
        return 'amorphous'
    if 'silic' in t:
        return 'silic'
    return None


def khoi_ve_loi(row):
    """Ver 5.3 — khối kiến thức chung về loại LÕI (Silic/Amorphous), theo
    yêu cầu Thịnh mở rộng content (đối chiếu bài mẫu Gemini — phần "Lõi
    Thép Silic" của họ dùng được vì là kiến thức ngành chung, không phải
    số liệu bịa riêng SKU). CHỈ nói tính chất VẬT LÝ CHUNG đã được ngành
    công nhận rộng rãi (không có số % cụ thể nào — số % tổn hao khác nhau
    theo từng thiết kế thật, không có 1 số chung đúng cho mọi máy, tránh
    lặp lỗi "CAPEX giảm 30-40%" đã bị chặn ở bài Gemini trước).

    CHỈ áp dụng outline_may_bien_ap (không áp cho outline_vo_may_bien_ap —
    vỏ không có lõi). Trả '' nếu không nhận diện được loại lõi từ Tên hàng
    — KHÔNG đoán."""
    if row.get('outline_id') != 'outline_may_bien_ap':
        return ''
    loai = _phat_hien_loai_loi(row.get('ten_goc', ''))
    if loai is None:
        return ''
    if loai == 'silic':
        noi_dung = (
            '<h2>Về lõi thép Silic</h2>'
            '<p>Lõi thép Silic (tôn silic cán nguội, định hướng hạt) là vật liệu mạch từ phổ biến '
            'nhất trong ngành máy biến áp phân phối — được dùng rộng rãi từ nhiều thập kỷ, có nguồn '
            'cung ổn định và chi phí đầu tư ban đầu thấp hơn so với lõi Amorphous cùng công suất. '
            'Tổn hao không tải của lõi Silic cao hơn lõi Amorphous, nhưng vẫn đáp ứng đầy đủ các '
            'tiêu chuẩn hiệu suất năng lượng hiện hành tại Việt Nam (TCVN 8525).</p>'
        )
    else:
        noi_dung = (
            '<h2>Về lõi thép Amorphous</h2>'
            '<p>Lõi Amorphous (vật liệu từ tính vô định hình) là công nghệ mới hơn lõi Silic truyền '
            'thống, có tổn hao không tải thấp hơn đáng kể — phù hợp khi ưu tiên tiết kiệm chi phí '
            'điện năng trong suốt vòng đời vận hành, đổi lại chi phí đầu tư ban đầu thường cao hơn '
            'lõi Silic cùng công suất. Đây là lựa chọn phổ biến cho các công trình vận hành liên tục, '
            'nơi phần chênh lệch chi phí đầu tư có thể bù lại qua tiền điện tiết kiệm được.</p>'
        )
    return f'<div {_st("khoi_thuong_hieu")}>{noi_dung}</div>'


# ============================================================ SONEALEO 2.0 -- khoi kien thuc chung CAP DIEN
# Viet bang kien thuc nganh cong khai (TCVN 5935/6610, IEC 60227/60502 --
# cung nguon da verify luc giai ma ky hieu, xem NHAT-KY-THAY-DOI.md).
# KHONG co so lieu rieng 1 SKU nao -- chi noi tinh chat VAT LIEU CHUNG da
# duoc nganh cong nhan, dung nguyen tac y het khoi_ve_loi() cua may bien ap.
def khoi_ve_cach_dien_cap_dien(row):
    """Chi ap dung outline_cap_dien, chi hien khi da GIAI MA duoc (khong
    doan neu khong co du lieu -- dung field loai_cach_dien_giai_ma da noi
    vao profiles.py o buoc truoc)."""
    if row.get('outline_id') != 'outline_cap_dien':
        return ''
    cach_dien = row.get('loai_cach_dien_giai_ma', '')
    if not cach_dien:
        return ''
    if 'XLPE' in cach_dien:
        noi_dung = (
            '<h2>Về cách điện XLPE</h2>'
            '<p>Cách điện XLPE (Polyethylene liên kết ngang) là vật liệu cách điện cao cấp hơn PVC '
            'trong ngành cáp điện — chịu nhiệt độ vận hành và khả năng quá tải tốt hơn, phù hợp cho '
            'công trình yêu cầu độ bền cao hoặc điều kiện lắp đặt khắc nghiệt (ngầm, ngoài trời, tải '
            'nặng). Đổi lại, cáp XLPE thường có giá thành cao hơn cáp PVC cùng tiết diện. Cả 2 loại '
            'đều phải đáp ứng TCVN 5935/IEC 60502 (cáp lực) hoặc TCVN 6610/IEC 60227 (dây dẫn thông '
            'thường) tuỳ hạng mục sử dụng.</p>'
        )
    else:
        noi_dung = (
            '<h2>Về cách điện PVC</h2>'
            '<p>Cách điện PVC là vật liệu phổ biến nhất trong dây và cáp điện dân dụng/công nghiệp '
            'nhẹ — chi phí hợp lý, dễ thi công, đáp ứng đầy đủ yêu cầu an toàn điện cho phần lớn công '
            'trình lắp đặt trong nhà. Với công trình cần chịu nhiệt/quá tải cao hơn hoặc lắp đặt điều '
            'kiện khắc nghiệt, cáp cách điện XLPE thường được ưu tiên thay thế. Đáp ứng TCVN '
            '6610/IEC 60227 hoặc TCVN 5935/IEC 60502 tuỳ loại cáp.</p>'
        )
    return f'<div {_st("khoi_thuong_hieu")}>{noi_dung}</div>'


def khoi_giap_bao_ve_cap_dien(row):
    """Chỉ hiện khi record CÓ giáp bảo vệ (giải mã được) — không đoán cho
    record không có giáp."""
    if row.get('outline_id') != 'outline_cap_dien':
        return ''
    giap = row.get('giap_bao_ve_giai_ma', '')
    if not giap:
        return ''
    noi_dung = (
        '<h2>Về lớp giáp bảo vệ</h2>'
        '<p>Giáp bảo vệ (bằng thép hoặc nhôm, dạng băng/dải hoặc dạng sợi tuỳ thiết kế) là lớp gia '
        'cường cơ học bên ngoài cách điện, giúp cáp chịu được lực va đập, đè nén khi chôn ngầm trực '
        'tiếp dưới đất hoặc lắp đặt ở nơi có nguy cơ tổn thương cơ học — không phải yêu cầu bắt buộc '
        'cho mọi công trình, chỉ cần thiết khi tuyến cáp đi qua khu vực dễ bị tác động vật lý (đào '
        'đất, xe cộ qua lại, gặm nhấm...). Cáp không giáp phù hợp cho lắp đặt trong ống/máng cáp có '
        'bảo vệ sẵn.</p>'
    )
    return f'<div {_st("khoi_thuong_hieu")}>{noi_dung}</div>'


def khoi_chong_chay_cap_dien(row):
    """Chỉ hiện khi record CÓ đặc điểm chống cháy/LSHF giải mã được."""
    if row.get('outline_id') != 'outline_cap_dien':
        return ''
    dac_diem = row.get('dac_diem_khac_giai_ma', '') or ''
    if 'chống cháy' not in dac_diem.lower() and 'khói' not in dac_diem.lower() and 'halogen' not in dac_diem.lower():
        return ''
    noi_dung = (
        '<h2>Về khả năng chống cháy</h2>'
        '<p>Cáp chống cháy (FR) duy trì khả năng dẫn điện trong 1 khoảng thời gian nhất định khi có '
        'hoả hoạn — quan trọng cho hệ thống cần hoạt động liên tục trong sự cố (báo cháy, chiếu sáng '
        'sự cố, thang máy cứu hộ, bơm chữa cháy). Loại ít khói không halogen (LSHF/LSFH) khi cháy '
        'sinh ít khói độc và không khí ăn mòn — phù hợp không gian đông người hoặc kín (trung tâm '
        'thương mại, hầm, nhà ga) nơi an toàn thoát hiểm được ưu tiên hàng đầu.</p>'
    )
    return f'<div {_st("khoi_thuong_hieu")}>{noi_dung}</div>'


def khoi_ve_cau_tao_tu_dong_cat(row):
    """SONEALEO 2.0 -- khoi kien thuc chung TU DONG CAT/RMU. Viet bang
    kien thuc nganh cong khai (cau tao pho bien cua tu trung the hop bo),
    KHONG co so lieu rieng SKU nao (khong dong cat, khong Ir, khong Icu cu
    the). Ap dung outline_tu_dong_cat va outline_vo_tu -- hien LUON (khong
    can du lieu giai ma gi them, khac cap dien vi day la kien thuc chung
    cho ca nhom, khong phan nhanh theo bien the ky hieu)."""
    if row.get('outline_id') not in ('outline_tu_dong_cat', 'outline_vo_tu'):
        return ''
    noi_dung = (
        '<h2>Về cấu tạo tủ đóng cắt trung thế</h2>'
        '<p>Tủ đóng cắt trung thế (RMU — Ring Main Unit, hoặc tủ hợp bộ tương tự) thường gồm 3 '
        'thành phần chính: khoang chứa thiết bị đóng cắt (dao cách ly, cầu dao phụ tải hoặc máy '
        'cắt), khoang cáp/đấu nối, và hệ thống liên động cơ khí đảm bảo trình tự thao tác an toàn '
        '(không cho đóng nối đất khi dao chính đang đóng, và ngược lại). Vỏ tủ thường được thiết kế '
        'kín khí hoặc cách điện rắn (SF6, chân không, hoặc cách điện khí) tuỳ công nghệ nhà sản '
        'xuất, giúp thu gọn kích thước so với tủ đóng cắt kiểu hở truyền thống.</p>'
        '<p>Vai trò chính của thiết bị đóng cắt trung thế là phân đoạn lưới điện, cách ly sự cố và '
        'bảo vệ nhánh rẽ — lựa chọn đúng loại (dao cách ly tay công vs máy cắt tự động) phụ thuộc '
        'yêu cầu bảo vệ cụ thể của công trình, không chỉ dựa vào cấp điện áp.</p>'
    )
    return f'<div {_st("khoi_thuong_hieu")}>{noi_dung}</div>'


def khoi_cau_tao_phu_kien(row):
    """Ver 2.7 — khối "Cấu tạo & phụ kiện tiêu chuẩn" (đề xuất từ review
    chéo). Kiến thức ngành chung về BỘ PHẬN CẤU THÀNH của máy biến áp dầu
    phân phối — TCVN 6306/IEC 60076. KHÔNG phải thông số đo riêng SKU,
    nên an toàn: mọi máy dầu phân phối đều có các bộ phận này.

    Chỉ hiện cho outline_may_bien_ap VÀ chỉ khi nhận diện được máy DẦU từ
    tên (máy khô cấu tạo khác hẳn — không có dầu, không có bình dầu phụ)."""
    if row.get('outline_id') != 'outline_may_bien_ap':
        return ''
    ten = str(row.get('ten_goc', '')).lower()
    if 'khô' in ten or 'kho ' in ten:
        return ''
    if 'dầu' not in ten:
        return ''   # không chắc là máy dầu -> không nói
    noi_dung = (
        '<h2>Cấu tạo &amp; phụ kiện tiêu chuẩn</h2>'
        '<p>Máy biến áp dầu phân phối theo TCVN 6306 / IEC 60076 thường gồm các bộ phận chính '
        'sau — chi tiết cấu hình cụ thể tuỳ đơn hàng và nhà sản xuất:</p>'
        '<ul>'
        '<li><strong>Ruột máy</strong>: lõi thép và cuộn dây, ngâm trong dầu cách điện.</li>'
        '<li><strong>Vỏ thùng và cánh tản nhiệt</strong>: chứa dầu, đồng thời toả nhiệt sinh ra '
        'trong quá trình vận hành.</li>'
        '<li><strong>Sứ cách điện cao áp và hạ áp</strong>: điểm đấu nối dây vào và ra.</li>'
        '<li><strong>Bộ chuyển nấc điện áp</strong>: điều chỉnh điện áp đầu ra trong dải cho phép, '
        'thao tác khi máy đã cắt điện.</li>'
        '<li><strong>Van xả dầu và van lấy mẫu</strong>: phục vụ thay dầu và kiểm tra chất lượng '
        'dầu định kỳ.</li>'
        '<li><strong>Nhiệt kế và chỉ thị mức dầu</strong>: theo dõi trạng thái vận hành.</li>'
        '<li><strong>Móc cẩu và bánh xe</strong>: phục vụ vận chuyển và lắp đặt tại trạm.</li>'
        '</ul>'
        '<p>Các phụ kiện bảo vệ nâng cao (rơ-le hơi Buchholz, van an toàn áp lực, rơ-le nhiệt độ) '
        'thường được trang bị theo yêu cầu kỹ thuật của dự án hoặc theo dải công suất lớn.</p>'
    )
    return f'<div style="{ST["khoi_thuong_hieu"]}">{noi_dung}</div>'


def khoi_bao_tri_lap_dat(row):
    """Ver 5.3 — khối kiến thức chung về bảo trì & lắp đặt, tách riêng
    khỏi khoi_chung_may_bien_ap (đã rút gọn còn 1 câu từ Ver 4.9.9 để
    chống Boilerplate SEO — KHÔNG nhét lại nội dung dài vào đó, thay vào
    đó tách thành khối RIÊNG có thể tự thêm/rút mà không ảnh hưởng khối
    ONAN/AN-AF gốc). Nội dung là THỰC HÀNH BẢO TRÌ CHUNG của ngành (không
    phải cam kết bảo hành/chính sách riêng của Lotech — cái đó CẦN Thịnh
    xác nhận chính sách thật trước khi thêm, xem đề xuất DE-XUAT-TOAN-DIEN
    mục C13, CHƯA làm ở đây).

    CHỈ áp dụng outline_may_bien_ap. Trả '' nếu không nhận diện được loại
    dầu/khô — KHÔNG đoán bừa (giống khoi_chung_may_bien_ap)."""
    if row.get('outline_id') != 'outline_may_bien_ap':
        return ''
    loai = _phat_hien_loai_lam_mat(row.get('ten_goc', ''))
    if loai is None:
        return ''
    if loai == 'dau':
        muc = (
            '<li>Kiểm tra định kỳ chất lượng dầu cách điện (thử điện áp xuyên thủng) theo khuyến '
            'cáo của đơn vị bảo trì.</li>'
            '<li>Lắp đặt ngoài trời cần có rãnh/hố thu dầu sự cố và phương án phòng cháy chữa cháy '
            'phù hợp thiết bị chứa dầu.</li>'
            '<li>Với máy kiểu hở có bình dầu phụ, kiểm tra hạt hút ẩm (silicagel) định kỳ.</li>'
        )
    else:
        muc = (
            '<li>Vệ sinh bụi định kỳ bề mặt cuộn dây, đảm bảo không gian thông gió xung quanh không '
            'bị vật cản che kín.</li>'
            '<li>Phù hợp lắp trong phòng kỹ thuật điện có kiểm soát độ ẩm — không yêu cầu rãnh thu '
            'dầu sự cố như máy biến áp dầu.</li>'
            '<li>Với dòng có quạt làm mát hỗ trợ (AF), kiểm tra định kỳ hoạt động của quạt và nguồn '
            'cấp riêng cho hệ thống này.</li>'
        )
    return f'<div {_st("khoi_thuong_hieu")}><h2>Lưu ý bảo trì &amp; lắp đặt</h2><ul>{muc}</ul></div>'


def khoi_chung_may_bien_ap(row):
    """Ver 4.9.9 — VÁ theo review SEO (Gemini, qua Thịnh chuyển lại): bản
    cũ chép NGUYÊN VĂN 100% giữa mọi SKU cùng loại dầu/khô -> Google coi
    là Boilerplate Content, kéo điểm Site-wide Quality xuống khi có hàng
    chục URL cùng khối chữ dài giống hệt nhau. Rút còn 1 CÂU NGẮN + gợi ý
    xem thêm (chưa có link thật — pillar page dầu/khô CHƯA được viết, xem
    CHANGELOG-VER499.md mục 'Chưa làm'. Khi có URL thật, chỉ cần thêm href
    vào đây, không cần sửa gì khác).

    CHỈ áp dụng outline_may_bien_ap. Trả '' nếu không nhận diện được loại
    dầu/khô — KHÔNG đoán bừa để tránh gán nhầm nguyên lý làm mát."""
    if row.get('outline_id') != 'outline_may_bien_ap':
        return ''
    loai = _phat_hien_loai_lam_mat(row.get('ten_goc', ''))
    if loai is None:
        return ''
    if loai == 'dau':
        cau = ('Đây là máy biến áp DẦU (làm mát bằng dầu cách điện tuần hoàn tự nhiên — ONAN), '
              'tuân thủ TCVN 6306 và TCVN 8525.')
    else:
        cau = ('Đây là máy biến áp KHÔ (không dùng dầu, làm mát bằng không khí AN/AF), '
              'tuân thủ TCVN 6306-11, IEC 60076-11 và TCVN 8525.')
    return f'<p {_st("khoi_chung")}>{html.escape(cau)}</p>'


def khoi_checklist_bao_gia(profile_id):
    """Ver 4.5 — Block 5 chuẩn High-end Content: checklist rule-based theo
    profile, KHÔNG phải AI viết, KHÔNG phụ thuộc dữ liệu record (câu hỏi cố
    định, áp dụng mọi sản phẩm cùng profile). Profile không có trong bảng
    (chưa khai báo) -> trả rỗng, an toàn, không hiện block.

    Ver 4.9.6 — KHÔNG còn được gọi trong dung_bai_html() (Thịnh xác nhận
    làm giảm lead) — hàm GIỮ NGUYÊN định nghĩa phòng khi cần dùng lại."""
    items = CHECKLIST_BAO_GIA.get(profile_id)
    if not items:
        return ''
    li = ''.join(f'<li>{html.escape(x)}</li>' for x in items)
    return '<h2>Thông tin cần cung cấp để nhận báo giá</h2><ul>' + li + '</ul>'


def khoi_nut_catalogue(row):
    """Ver 5.3 — nút "Tải Catalogue/Datasheet (PDF)", theo phản hồi thật
    ("dân thu mua/kỹ sư cực kỳ cần file PDF, trang này chỉ có chữ").

    CHỈ hiện khi row có field 'catalogue_pdf_url' (đã đăng ký OPTIONAL ở
    cot_import của cả 4 profile, xem profiles.py) — MASTER hiện CHƯA có
    cột này, nên hàm này trả '' cho MỌI sản phẩm cho tới khi Thịnh có file
    PDF thật và điền link vào MASTER. KHÔNG tự tạo/suy đoán link — thiếu
    link thì không hiện nút, tuyệt đối không hiện nút rồi dẫn tới 404."""
    url = (row or {}).get('catalogue_pdf_url', '')
    if not url:
        return ''
    return f'<p><a href="{html.escape(url)}" target="_blank" rel="noopener" {_st("btn_catalogue")}>📄 Tải Catalogue / Datasheet (PDF)</a></p>'


def khoi_san_pham_lien_quan(danh_sach):
    """Ver 4.5 — Block 6 chuẩn High-end Content: sản phẩm liên quan. HÀM
    NÀY KHÔNG TỰ TRUY VẤN DB — chỉ dựng HTML từ danh sách đã được tầng gọi
    (giao-dien.py, qua db_phase2.tim_san_pham_lien_quan) tìm sẵn.

    `danh_sach`: list [{'ten':..., 'url':...}] — item thiếu 'ten' hoặc
    'url' bị bỏ qua. Rỗng/None -> trả '' (không hiện block).

    Ver 4.9.9 — style INLINE, bỏ class "lotech-lien-quan" cũ.

    Ver 5.3 — VÁ theo phản hồi thật ("vứt 1 chùm link dạng gạch đầu dòng
    thô ở giữa trang nhìn rất chắp vá"): đổi từ <ul><li> sang dạng GRID thẻ
    (CSS Grid, tự xuống dòng theo độ rộng màn hình) — mỗi sản phẩm 1 thẻ
    viền bo góc, dễ quét mắt hơn list text thuần."""
    if not danh_sach:
        return ''
    the = ''.join(
        f'<a href="{html.escape(sp["url"])}" {_st("lien_quan_card")}>{html.escape(sp["ten"])}</a>'
        for sp in danh_sach if sp.get('url') and sp.get('ten'))
    if not the:
        return ''
    return f'<h2>Sản phẩm liên quan</h2><div {_st("lien_quan_grid")}>' + the + '</div>'


def khoi_cta(site_cfg):
    """CTA do CODE dựng cứng, KHÔNG phải AI viết (R2-05: 'CTA lấy từ cấu
    hình website'). Dùng thẳng cauhinh.py qua site_cfg truyền vào.

    Ver 4.9.9 — style INLINE (ST['cta_cuoi']/['btn_goi']/['btn_zalo']),
    bỏ hẳn class "lotech-*"/"btn-*" cũ — không còn phụ thuộc CSS ngoài,
    không còn "dấu vân tay" tên riêng trong source HTML (đổi sang site
    khác không cần sửa gì, không lộ tên tool)."""
    # Ver 2.2 — theme đã có CTA riêng -> bỏ hẳn khối này để không lặp 2 CTA
    if _bo_cta_cuoi():
        return ''
    site_cfg = site_cfg or {}
    ten = html.escape(site_cfg.get('ten', ''))
    hotline = site_cfg.get('hotline', '')
    zalo = site_cfg.get('zalo', hotline)
    loi_dan = f'Liên hệ {ten} để được tư vấn và báo giá.' if ten else 'Liên hệ để được tư vấn và báo giá.'

    # Ver 4.5.1 P1 — id="lien-he-bao-gia" là đích neo thật cho nút "Yêu cầu
    # báo giá" ở khoi_cta_ngan() — GIỮ NGUYÊN, không đổi.
    if not hotline:
        return (f'<div {_st("cta_cuoi")}><h2 id="lien-he-bao-gia">Liên hệ báo giá</h2>'
                f'<p>{html.escape(loi_dan)}</p></div>')

    nut = [f'<a href="tel:{html.escape(hotline)}" {_st("btn_goi")}>Gọi {html.escape(hotline)}</a>']
    if zalo:
        nut.append(f'<a href="https://zalo.me/{html.escape(zalo)}" {_st("btn_zalo")}>Nhắn Zalo {html.escape(zalo)}</a>')
    return (f'<div {_st("cta_cuoi")}><h2 id="lien-he-bao-gia">Liên hệ báo giá</h2>'
            f'<p>{html.escape(loi_dan)}</p>'
            f'<p>{"".join(nut)}</p></div>')


def khoi_cta_ngan(site_cfg):
    """Ver 4.2 — CTA rút gọn dạng nút bấm, dùng ở Hero và ngay sau bảng
    thông số. KHÔNG lặp lại nguyên văn khoi_cta() đầy đủ.

    Ver 4.9.9 — style INLINE, bỏ class "lotech-cta-ngan"/"btn-*" cũ.

    Ver 5.2 — VÁ THEO YÊU CẦU THỊNH ("khách nhấn vào là bắt luôn, không
    cần jump link xuống dưới cùng"): nút "Yêu cầu báo giá" trước đây
    href="#lien-he-bao-gia" — CHỈ cuộn trang xuống khối CTA cuối, không
    hành động gì ngay. Giờ đổi thành hành động NGAY (gọi điện thẳng —
    cùng đích với nút "Gọi") khi có hotline. KHÔNG làm form nhập số điện
    thoại tại chỗ kiểu tutrungthe.vn — cần biết plugin/backend nhận lead
    thật của site, Thịnh xác nhận KHÔNG cần làm phần này."""
    site_cfg = site_cfg or {}
    hotline = site_cfg.get('hotline', '')
    zalo = site_cfg.get('zalo', hotline)
    if not hotline:
        # Ver 2.2 — nút này neo tới id="lien-he-bao-gia" nằm trong khoi_cta().
        # Nếu ĐÃ bỏ khối đó (theme có CTA riêng) mà vẫn render nút thì nút
        # trỏ vào hư không -> LINK CHẾT. Không có hotline + không có đích
        # neo => bỏ hẳn nút, để CTA của theme làm việc.
        if _bo_cta_cuoi():
            return ''
        return f'<p><a href="#lien-he-bao-gia" {_st("btn_baogia")}>Yêu cầu báo giá</a></p>'
    nut = [f'<a href="tel:{html.escape(hotline)}" {_st("btn_goi")}>Gọi {html.escape(hotline)}</a>']
    if zalo:
        nut.append(f'<a href="https://zalo.me/{html.escape(zalo)}" {_st("btn_zalo")}>Nhắn Zalo</a>')
    nut.append(f'<a href="tel:{html.escape(hotline)}" {_st("btn_baogia")}>Yêu cầu báo giá</a>')
    return '<p>' + ' '.join(nut) + '</p>'


def khoi_hero(row, site_cfg):
    """Ver 4.2 — Block Hero sản phẩm: mã hàng, thương hiệu, 3-6 thông số
    chính, giá Liên hệ, CTA gọn. 100% dựng từ dữ liệu đã có trong record.

    Ver 4.9.9 — style INLINE, bỏ class "lotech-hero*" cũ."""
    profile_id, outline_id = row['profile_id'], row['outline_id']
    dong = []
    meta = []
    if row.get('ma_goc'):
        meta.append(f"<strong>Mã hàng:</strong> {html.escape(row['ma_goc'])}")
    if row.get('thuong_hieu'):
        meta.append(f"<strong>Thương hiệu:</strong> {html.escape(row['thuong_hieu'])}")
    if meta:
        dong.append(f'<p {_st("hero_meta")}>' + ' &nbsp;|&nbsp; '.join(meta) + '</p>')

    cot_bang = P.effective_cot_bang(profile_id, outline_id)
    da_hien_o_meta = {'ma_goc', 'thuong_hieu'}
    dong_specs = [f'<li><strong>{html.escape(nhan)}:</strong> {html.escape(v)}</li>'
                 for k, nhan in cot_bang[:6] if k not in da_hien_o_meta and (v := row.get(k, ''))]
    if dong_specs:
        dong.append(f'<ul {_st("hero_specs")}>' + ''.join(dong_specs) + '</ul>')

    dong.append('<p><strong>Giá:</strong> Liên hệ</p>')
    dong.append(khoi_cta_ngan(site_cfg))
    return f'<div {_st("hero")}>' + ''.join(dong) + '</div>'


TRUONG_AI_CHO_PHEP = ['meta_title', 'meta_description', 'intro_html', 'dac_diem_html',
                      'ung_dung_html', 'huong_dan_chon_html', 'faq',
                       'goc_nhin_thi_truong_html']   # Ver 2.6 — khối Enhance riêng


def dung_bai_html(row, ai_data, site_cfg=None, mau='chuan', hau_to_slug='', san_pham_lien_quan=None, cung_dong=None):
    """Ghép Hero (code) + AI editorial (đã sanitize) + bảng thông số code tự
    dựng (KHÔNG sanitize, xem mục 6.2) + CTA code tự dựng (3 vị trí: Hero /
    sau bảng specs / cuối trang) + Checklist báo giá + Sản phẩm liên quan +
    Schema JSON-LD thành 1 bài hoàn chỉnh.

    Ver 4.2 — tách vật lý theo chuẩn High-end Content đã chốt với Thịnh:
    Block 1 Hero (khoi_hero, code-only) -> AI intro -> Block 2 bảng thông số
    + CTA gọn -> AI đặc điểm/ứng dụng/hướng dẫn -> FAQ -> CTA đầy đủ cuối
    trang (khoi_cta, giữ NGUYÊN như Ver 3.4-4.1, không đổi hành vi) -> Schema.

    Ver 4.5 — thêm Block 5 (Checklist báo giá, rule theo profile) và Block 6
    (Sản phẩm liên quan) chen giữa nội dung AI và FAQ. `san_pham_lien_quan`:
    list đã tìm sẵn qua db_phase2.tim_san_pham_lien_quan() — mặc định None
    = không hiện block, KHÔNG đổi hành vi cũ nếu caller chưa truyền.

    R2-06: giá List không xuất hiện — vì ai_data chỉ chứa field trong
    TRUONG_AI_CHO_PHEP (lọc cứng ở đây, phòng thủ lớp 2 dù prompt đã không
    đưa gia_list cho AI thấy từ đầu), price_display cố định 'Liên hệ'.

    Gate 2 Task 1: Schema (`dung_schema_script`) gắn ở CUỐI HTML — sản phẩm
    có đúng 1 khối `<script type="application/ld+json">`, dịch vụ không có
    khối nào (dung_schema_script trả rỗng cho content_type=service).

    Ver 3.9 — hau_to_slug: xem dung_slug(), mặc định rỗng = không đổi hành
    vi cũ."""
    import prompts_phase2 as PR

    ai_data = {k: v for k, v in (ai_data or {}).items() if k in TRUONG_AI_CHO_PHEP}

    # Ver 3.6.3 — lọc dấu vết AI NGAY TẠI ĐÂY, trước mọi khâu ghép.
    # Ver 3.6.1 lọc ở khâu cuối nên không bao giờ chạy: lúc đó chuỗi đã là
    # '<div class="snl-page">...<div class="snl-kicker">MBT</div>...<p>Bạn
    # đang tìm...?' — chữ "MBT" của khối thương hiệu chen vào giữa, chuỗi
    # thẻ mở không còn liền mạch, regex neo đầu chuỗi trượt.
    # Lọc ở đây thì mỗi trường văn xuôi còn nguyên vẹn, chưa bị bọc gì.
    ai_data = _loc_ai_data(ai_data)

    outline_id = row['outline_id']
    cfg = PR.OUTLINE_NOI_DUNG[outline_id]

    # Ver 2.5 — BỐ CỤC CAO CẤP (giao_dien_2_5.py): hero 2 cột, chip, thông
    # số nhanh, mục lục neo, FAQ gập, CTA. Bật bằng GIAO_DIEN_2_5=1.
    # MẶC ĐỊNH TẮT -> bố cục cũ giữ nguyên 100%, không ảnh hưởng bài đã đăng.
    # Cần dán file CSS mới lên site trước khi bật (tab 1 > Xuất file CSS).
    if _dung_giao_dien_2_5():
        try:
            return _dung_bai_2_5_wrapper(row, ai_data, site_cfg, mau, hau_to_slug,
                                         san_pham_lien_quan, cung_dong)
        except Exception as e:
            # Bố cục mới hỏng KHÔNG được làm chết cả batch -> rơi về bố cục cũ
            print(f'   [Giao diện 2.5] Lỗi ({e}) — dùng bố cục cũ cho record này.')

    khoi = [khoi_hero(row, site_cfg)]
    # Ver 2.3 (Mốc 2) — HÌNH KỸ THUẬT vẽ từ dữ liệu, đặt ngay dưới Hero,
    # đúng vị trí mắt tìm ảnh sản phẩm. Vẽ bằng code (hinh_ky_thuat.py) từ
    # field có thật -> không AI sinh ảnh, không tải ảnh ngoài, thiếu dữ
    # liệu thì KHÔNG vẽ. Có hình rồi thì bỏ luôn ô placeholder (2 thứ cùng
    # chỗ là thừa).
    try:
        import hinh_ky_thuat as HKT
        hinh = HKT.hinh_cho_row(row)
    except Exception:
        hinh = ''   # lỗi vẽ hình KHÔNG được làm hỏng cả bài
    if hinh:
        khoi.append(hinh)
    else:
        khoi.append(khoi_anh_placeholder('ảnh sản phẩm chính'))   # Ver 5.0
    if ai_data.get('intro_html'):
        khoi.append(sanitize_html(ai_data['intro_html']))

    # Ver 4.9.9 — Block "Về thương hiệu" — CODE, data catalogue thật, chỉ
    # hiện cho brand đã có nguồn (xem khoi_ve_thuong_hieu/THONG_TIN_THUONG_HIEU).
    thuong_hieu_html = khoi_ve_thuong_hieu(row)
    if thuong_hieu_html:
        khoi.append(thuong_hieu_html)

    khoi.append('<h2>Thông số kỹ thuật</h2>')
    khoi.append(bang_thong_so(row))
    khoi.append('<p><strong>Giá:</strong> Liên hệ</p>')  # price_display cố định, không đọc gia_list
    khoi.append(khoi_cta_ngan(site_cfg))   # Ver 4.2 — CTA #2: ngay sau bảng thông số

    # Ver 5.3 — nút Tải Catalogue/Datasheet, chỉ hiện khi có link PDF thật
    # (row['catalogue_pdf_url']) — MASTER hiện chưa có cột này nên trả rỗng
    # cho mọi sản phẩm tới khi Thịnh bổ sung.
    nut_catalogue = khoi_nut_catalogue(row)
    if nut_catalogue:
        khoi.append(nut_catalogue)

    # Ver 4.9.8 — Block so sánh công suất trong dòng, CODE dựng từ
    # cung_dong (db_phase2.tim_san_pham_cung_dong), KHÔNG qua AI.
    ss = khoi_so_sanh_cong_suat(row, cung_dong)
    if ss:
        khoi.append(ss)

    if ai_data.get('dac_diem_html'):
        khoi.append('<h2>Đặc điểm</h2>')
        khoi.append(sanitize_html(ai_data['dac_diem_html']))

    if ai_data.get('ung_dung_html'):
        khoi.append('<h2>Ứng dụng</h2>')
        khoi.append(sanitize_html(ai_data['ung_dung_html']))

    if ai_data.get('huong_dan_chon_html'):
        khoi.append('<h2>Hướng dẫn lựa chọn</h2>')
        khoi.append(sanitize_html(ai_data['huong_dan_chon_html']))

    # Ver 4.9.6 — VÁ: bỏ hẳn Block 5 "Thông tin cần cung cấp để nhận báo
    # giá" (Thịnh xác nhận LẦN THỨ HAI — đã nhắc ở phiên trước nhưng bị
    # miss, lần này ghi rõ vào code để không lặp lại): khối checklist rào
    # cản làm khách ngại điền, giảm lead thay vì tăng — Lotech muốn khách
    # GỌI THẲNG, không muốn tạo cảm giác "phải chuẩn bị đủ thông tin mới
    # được hỏi giá". Hàm khoi_checklist_bao_gia() GIỮ NGUYÊN định nghĩa
    # (không xoá code) phòng khi cần dùng lại dạng khác sau này, chỉ KHÔNG
    # GỌI trong luồng dựng bài nữa.
    lq = khoi_san_pham_lien_quan(san_pham_lien_quan)   # Ver 4.5 — Block 6
    if lq:
        khoi.append(lq)

    if cfg['co_faq'] and ai_data.get('faq'):
        cau = []
        for q in ai_data['faq']:
            if not q.get('q'):
                continue
            cau.append(f'<h3>{html.escape(q["q"])}</h3><p>{sanitize_html(q.get("a", ""))}</p>')
        if cau:
            khoi.append('<h2>Câu hỏi thường gặp</h2>')
            khoi.extend(cau)

    # Ver 6.2 — GỠ 3 KHỐI KIẾN THỨC VIẾT CHẾT khỏi luồng dựng bài:
    #   khoi_chung_may_bien_ap (111 ký tự) / khoi_ve_loi (423) /
    #   khoi_bao_tri_lap_dat  (314)
    # Đo trên 6 SKU dầu 3 pha 250-2000kVA: cả 3 trả văn GIỐNG NHAU 100,0%.
    # Tổng 848 ký tự boilerplate byte-identical trên MỌI bài — chiếm 25%
    # khối lượng chữ do code sinh, và là phần kéo tỷ lệ trùng lên cao nhất
    # sau khi đã vá các khối biến thiên.
    # Nội dung của chúng nay ĐÃ CÓ bản biến thiên tương ứng, sinh từ dữ liệu
    # thật của chính SKU: ve_loi -> khoi_so_sanh_loi (Po thật của 2 lõi),
    # bao_tri_lap_dat -> khoi_lap_dat_van_chuyen (theo dải kVA + dầu/khô),
    # chung_may_bien_ap -> khoi_ung_dung. Giữ cả hai là nói hai lần cùng ý.
    # HÀM GIỮ NGUYÊN ĐỊNH NGHĨA (không xoá code) — chỉ không gọi nữa.
    # Bật lại bằng biến môi trường SNL_KHOI_KIEN_THUC_CU=1.
    import os as _os_kt
    if str(_os_kt.environ.get('SNL_KHOI_KIEN_THUC_CU', '0')).strip().lower() in ('1', 'true', 'on'):
        for _f_kt in (khoi_chung_may_bien_ap, khoi_ve_loi, khoi_bao_tri_lap_dat):
            _h_kt = _f_kt(row)
            if _h_kt:
                khoi.append(_h_kt)

    # Ver 6.1 — TẦNG 3 BIẾN THIÊN, NAY CHẠY CẢ Ở BỐ CỤC CŨ.
    #
    # Trước 6.1, kien_thuc_bien_thien CHỈ được gọi trong
    # _dung_bai_2_5_wrapper(), tức chỉ chạy khi GIAO_DIEN_2_5=1 — mà cờ đó
    # mặc định '0' (cau-hinh.env.MAU dòng 143). Hệ quả đo được, không phải
    # suy đoán: trong bố cục đang chạy thật, 3 khối kiến thức duy nhất là
    # khoi_chung_may_bien_ap / khoi_ve_loi / khoi_bao_tri_lap_dat — cả 3
    # viết CHẾT, trả CÙNG MỘT chuỗi cho mọi SKU cùng dầu/khô. Đo trên 5 SKU
    # khác nhau (25kVA -> 1600kVA): khoi_chung ra đúng 2 biến thể,
    # khoi_bao_tri ra đúng 2 biến thể, 250kVA và 1600kVA byte-identical.
    # Đó chính xác là cái "cùng một khuôn" người đọc nhìn thấy.
    #
    # Khối biến thiên sinh chữ từ kVA/số pha/dầu-khô/lõi/hãng của chính SKU
    # và Po/Pk/Uk tra catalogue. TỐN 0 TOKEN GEMINI — toàn bộ do code sinh.
    # Bọc try để lỗi ở đây KHÔNG làm hỏng bài (giữ đúng kỷ luật của nhánh 2.5).
    try:
        import kien_thuc_bien_thien as _KTBT
        _bien_thien = _KTBT.tat_ca_khoi(row, anh_em=_PK_kho_row(row))
        if _bien_thien:
            khoi.append(_bien_thien)
    except Exception as _e:
        print(f'[Ver 6.1] Bỏ qua khối kiến thức biến thiên: {_e}')

    # SONEALEO 2.0 -- 3 khoi kien thuc chung CAP DIEN, cung nguyen tac
    # (code viet cung, kien thuc nganh chung, KHONG phai AI doan rieng
    # SKU) -- chi hien khi field giai ma ky hieu (Viec 3/9 hom nay) THAT
    # SU co gia tri, tu an neu khong giai ma duoc, khong doan.
    # Ver 4.6 — khối "chịu tải bao nhiêu" đặt TRƯỚC các khối kiến thức
    # chung: GSC cho thấy đây là câu người mua gõ (41 truy vấn, vị trí TB
    # 3,1 nhưng CTR 2,97%), phải nằm cao trong bài chứ không nhét cuối.
    chiu_tai = KCT.khoi_chiu_tai(row, _st, lambda v: html.escape(str(v)))
    if chiu_tai:
        khoi.append(chiu_tai)

    ve_cach_dien_cd = khoi_ve_cach_dien_cap_dien(row)
    if ve_cach_dien_cd:
        khoi.append(ve_cach_dien_cd)
    giap_cd = khoi_giap_bao_ve_cap_dien(row)
    if giap_cd:
        khoi.append(giap_cd)
    chong_chay_cd = khoi_chong_chay_cap_dien(row)
    if chong_chay_cd:
        khoi.append(chong_chay_cd)

    # SONEALEO 2.0 -- khoi kien thuc chung TU DONG CAT/RMU (Viec 5)
    ve_tu_dong_cat = khoi_ve_cau_tao_tu_dong_cat(row)
    if ve_tu_dong_cat:
        khoi.append(ve_tu_dong_cat)

    khoi.append(khoi_cta(site_cfg))

    # Ver 4.9.6 — VÁ LỖI THẬT (ảnh chụp production 29/07/2026, Thịnh gửi):
    # dung_schema_script() trả đúng HTML <script type="application/ld+json">
    # ...</script> — TỰ NÓ không sai. Nhưng khi field 'description' này
    # được POST qua WooCommerce REST API (ai_wp_adapter.py::dang_woo_that),
    # WordPress lọc nội dung post (wp_kses) XOÁ thẻ <script>/<style> khỏi
    # danh sách tag được phép nhưng CHỈ xoá cặp thẻ, GIỮ NGUYÊN text bên
    # trong — kết quả: nguyên khối JSON hiện ra thành CHỮ THẬT trên trang
    # (đúng như ảnh chụp). Nhét <script> vào post_content KHÔNG BAO GIỜ
    # sống sót qua REST API trừ khi user có quyền unfiltered_html (không
    # kiểm chứng được từ code, phụ thuộc cấu hình WordPress phía Thịnh).
    #
    # Vá: KHÔNG còn nhét schema vào 'html' (nội dung thật gửi đi) nữa —
    # trả riêng qua key 'schema' (dict, không phải string) để nơi gọi
    # (ai_wp_adapter.py) tự quyết định đường đi khác an toàn hơn sau này
    # (VD ghi vào custom field cho Rank Math đọc — plugin này đã cài sẵn
    # trên site theo ảnh chụp, nhưng cần xác nhận tên meta key thật trước
    # khi code, không đoán mù). Trước mắt: KHÔNG có Product Schema nào
    # được đăng, còn hơn đăng JSON lộ ra thành chữ như hiện tại.
    schema = dung_schema(row)

    # Ver 4.9.9 — Title/H1 SKU-FIRST, CODE dựng CỐ ĐỊNH theo công thức đã
    # chốt — không còn tin vào ai_data['meta_title'] tự do (AI không đảm
    # bảo đúng định dạng mỗi lần). Ngoài outline_may_bien_ap, giữ hành vi
    # cũ (Tên hàng/meta_title AI) — CHƯA áp công thức SKU-first cho profile
    # khác (chưa được yêu cầu, tránh đổi hành vi ngoài phạm vi đã duyệt).
    if outline_id == 'outline_may_bien_ap':
        tieu_de = dung_tieu_de(row)
    else:
        tieu_de = ai_data.get('meta_title') or row.get('ten_goc', '')

    if outline_id == 'outline_may_bien_ap':
        # Thịnh đã quyết KHÔNG muốn mã hàng trong title máy biến áp (Ver
        # 5.0) — KHÔNG áp fallback thêm mã hàng ở đây dù bị cắt, chỉ cắt an
        # toàn thường (thực tế dung_tieu_de() luôn ngắn, hiếm khi cần cắt).
        title_cuoi = rut_gon_an_toan(tieu_de, 70)
    else:
        title_cuoi = rut_gon_tieu_de_chong_trung(tieu_de, row.get('ma_goc', ''), 70)

    return {
        'title': title_cuoi,
        'meta_description': rut_gon_an_toan(ai_data.get('meta_description', '') or '', 160),
        'html': re.sub(r'\n{3,}', '\n\n', '\n'.join(khoi)),
        'slug': dung_slug(row, mau, hau_to=hau_to_slug),
        'schema': schema,
    }


# ============================================================ mục 7 — chống bịa Hard Block
_SO_DON_VI = re.compile(
    # Ver 2.8 — thêm W/kW/dB/kg/Hz/%: cột QUÉT ĐỘNG hay mang các đơn vị
    # này (tổn hao W, độ ồn dB, khối lượng kg). Thiếu thì Hard Block bỏ qua
    # luôn số đó — không chặn nhầm nhưng cũng không bảo vệ.
    # Ver 5.6 — thêm mA/cm (yêu cầu mở rộng danh sách đơn vị). CỐ Ý KHÔNG
    # thêm đơn vị `m` TRẦN: "cuộn 100 m", "dài 500m" là văn nói bình thường
    # trong bài cáp, mà KHÔNG field nào của Profile Registry hiện có nhãn
    # "(m)" -> thêm vào đây sẽ đẻ ra đúng họ false-positive mà bản này đang
    # đi sửa. `°C` cũng không thêm ở đây vì _CUM_MO_RONG_RE đã bắt sẵn.
    r'(\d+(?:[.,]\d+)?)\s*(kVA|kV|kA|kW|kg|mm2|mm²|mm|mA|cm|dB|Hz|VA|W|A|V|%)\b', re.IGNORECASE)

# R2-08: cụm kỹ thuật hoàn chỉnh — bắt cả chuỗi số nối nhau bằng x/+// (VD
# "0.6/1kV", "3x50mm²", "3x50+1x25mm²", "100/5A"), không chỉ 1 số + 1 đơn vị
# đơn lẻ. Bắt buộc có ÍT NHẤT 1 dấu nối (x, + hoặc /) mới coi là "cụm" — số
# đơn lẻ có đơn vị (VD "22kV") vẫn do _SO_DON_VI xử lý như cũ, không đổi.
_CUM_KY_THUAT_RE = re.compile(
    r'\d+(?:[.,]\d+)?(?:\s*[x+/]\s*\d+(?:[.,]\d+)?){1,}\s*(?:kVA|kV|kA|mm2|mm²|mm|VA|V|A)?',
    re.IGNORECASE)

# Ver 5.7 — VÁ FALSE-POSITIVE THẬT: phần đơn vị của _CUM_KY_THUAT_RE là
# OPTIONAL, nên NGÀY THÁNG cũng khớp dạng "cụm kỹ thuật":
#     "cập nhật ngày 22/08/2026"  -> chặn '22/08/2026'
#     "Bảng giá tháng 8/2026"     -> chặn '8/2026'
#     "áp dụng từ 01/09/2026"     -> chặn '01/09/2026'
# kiem_tra_bia_toan_bo() là CỔNG CỨNG: dính 1 field là chặn CẢ BÀI (kể cả
# FAQ). Mà framing "Bảng giá/Báo giá cập nhật tháng X" chính là dạng tiêu đề
# đang chạy tốt nhất cho nhóm truy vấn báo giá -> Hard Block đang chặn oan
# đúng nhóm bài quan trọng nhất.
#
# Sửa ĐÚNG PHẠM VI: chỉ bỏ qua chuỗi có HÌNH DẠNG NGÀY và KHÔNG mang đơn vị
# kỹ thuật. Không nới bất kỳ số kỹ thuật nào — "22/0,4kV" vẫn qua Hard Block
# như cũ vì có đơn vị, "3x50mm²" vẫn qua vì có đơn vị, "22/0,4" trần vẫn bị
# xét như cũ vì năm phải có 4 chữ số và phải nằm ở vế cuối.
#   dd/mm/yyyy | d/m/yyyy | mm/yyyy | m/yyyy   (yyyy = 19xx..20xx)
_NGAY_THANG_RE = re.compile(
    r'^(?:(?:0?[1-9]|[12]\d|3[01])\s*/\s*)?(?:0?[1-9]|1[0-2])\s*/\s*(?:19|20)\d{2}$')


def _la_ngay_thang(cum):
    """True nếu `cum` chỉ là ngày/tháng-năm, KHÔNG phải thông số kỹ thuật.

    Điều kiện chặt, cả 3 phải đúng:
      1. Không có đơn vị kỹ thuật đi kèm (có kV/A/mm... -> là thông số).
      2. Khớp trọn vẹn khuôn ngày ở trên.
      3. Không chứa dấu thập phân — "22/0,4" hay "1.5/3" không bao giờ là ngày.
    """
    s = str(cum).strip()
    if _DON_VI_CUOI_RE.search(s):
        return False
    if ',' in s or '.' in s:
        return False
    return bool(_NGAY_THANG_RE.match(s))


_DON_VI_CUOI_RE = re.compile(r'(kVA|kV|kA|mm2|mm²|mm|VA|V|A)\s*$', re.IGNORECASE)


# Ver 4.3.1 — dữ liệu tương thích của PHỤ KIỆN vỏ máy biến áp được bóc
# CHỈ từ Tên hàng thật. Không suy từ mã SKU và không đoán nếu tên không đủ
# cả 3 thành phần: số pha + kVA + cặp điện áp. Mục đích: cho prompt/Hard
# Block biết "22/0,4kV" là thông tin của MÁY mà vỏ tương thích, không phải
# cấp điện áp riêng của cái vỏ.
_MAY_TUONG_THICH_RE = re.compile(
    r'\b([13])\s*P(?:HA)?\b.*?(\d+(?:[.,]\d+)?)\s*KVA\b.*?'
    r'(\d+(?:[.,]\d+)?\s*/\s*\d+(?:[.,]\d+)?)\s*KV\b', re.IGNORECASE)


def bo_sung_may_tuong_thich(row):
    """Trả copy row có `may_tuong_thich` nếu bóc chắc chắn được từ Tên hàng.

    Chỉ áp cho outline vỏ MBA / phụ kiện. Không có đủ pattern thì giữ nguyên
    row và để field trống, tuyệt đối không suy luận từ SKU.
    """
    if not isinstance(row, dict):
        return row
    if row.get('may_tuong_thich'):
        return row
    if row.get('outline_id') not in ('outline_vo_may_bien_ap', 'outline_phu_kien'):
        return row
    m = _MAY_TUONG_THICH_RE.search(str(row.get('ten_goc') or ''))
    if not m:
        return row
    pha = '1 pha' if m.group(1) == '1' else '3 pha'
    kva = m.group(2).strip()
    cap = re.sub(r'\s+', '', m.group(3))
    ra = dict(row)
    ra['may_tuong_thich'] = f'{pha} {kva}kVA {cap}kV'
    return ra

# Ver 4.1 — Hard Block lớp 4 (chống false-positive giá trị tách từ cặp ghép).
# Bug thật đã gặp (26/07, batch thật): field cấp điện áp lưu cặp không đơn
# vị "12.7/0.23" (sơ cấp/thứ cấp máy biến áp). AI viết lại tự nhiên thành
# "12.7KV" (tách 1 nửa cặp, thêm đơn vị) — record CÓ số này thật, nhưng lớp
# 3 (token đơn lẻ) chưa từng thấy "12.7" đứng riêng kèm đơn vị trong nguồn
# nên chặn nhầm. CHỈ nới khi CẢ giá trị lẫn "họ đơn vị" đều khớp field gốc
# — không nới theo kiểu "thấy số xuất hiện là cho qua" (rủi ro thủng thật,
# GPT review đã cảnh báo đúng).
_FIELD_HO_DON_VI = {
    'cap_dien_ap': 'DIEN_AP',
    'tiet_dien': 'TIET_DIEN',
}
_DON_VI_SANG_HO = {
    'kv': 'DIEN_AP', 'v': 'DIEN_AP',
    'mm': 'TIET_DIEN', 'mm2': 'TIET_DIEN', 'mm²': 'TIET_DIEN',
}


def _kho_thanh_phan_cum_theo_field(row):
    """Trả set các tuple (số_con_đã_chuẩn_hoá, họ_đơn_vị) — số_con tách từ
    CỤM GHÉP (có dấu x/+/) của field trong _FIELD_HO_DON_VI, gắn đúng họ
    đơn vị của field đó. Số đơn lẻ (không dấu nối) KHÔNG vào kho này — lớp
    3 (_kho_cua_dong) đã xử lý số đơn lẻ đứng sẵn kèm đơn vị trong nguồn
    rồi, kho này CHỈ để bắt trường hợp AI tách 1 nửa cặp ghép ra viết riêng."""
    kho = set()
    for field, ho in _FIELD_HO_DON_VI.items():
        v = row.get(field, '')
        if not v:
            continue
        for m in _CUM_KY_THUAT_RE.finditer(v):
            cum_chuan = _chuan_cum(m.group(0))
            for so_con in re.split(r'[x+/]', cum_chuan):
                if so_con:
                    kho.add((so_con, ho))
    return kho

# Gate 2 Task 2 — cụm "mở rộng": các loại thông tin AI hay tự bịa mà KHÔNG
# field nào trong 4 profile hiện có (bảo hành, cấp bảo vệ IP, tiêu chuẩn
# IEC/TCVN, nhiệt độ, phần trăm). Vì không field nào của Profile Registry
# chứa loại dữ liệu này, những cụm này gần như LUÔN bị chặn trong thực tế —
# đúng ý đồ: AI không có cơ sở dữ liệu nào để nhắc, nên nhắc là bịa. Vẫn xây
# đúng cơ chế so khớp với record (không hard-code chặn cứng), để nếu sau này
# có profile/field mang loại dữ liệu này thì cơ chế tự nới đúng, không cần
# sửa lại logic.
_CUM_MO_RONG_RE = re.compile(
    r'(?:'
    r'\d+\s*(?:tháng|năm)'                              # bảo hành theo tháng/năm
    r'|IP[\s-]?\d{2}'                                    # cấp bảo vệ IPxx
    r'|(?:IEC|TCVN)[\s-]?\d+(?:[-.:]\d+)*'                # tiêu chuẩn kèm số
    r'|\d+(?:[.,]\d+)?\s*(?:°\s*C|độ\s*C)'                # nhiệt độ
    r'|\d+(?:[.,]\d+)?\s*%'                               # phần trăm
    r')', re.IGNORECASE)


# ============================================================ Ver 5.6 — chuẩn hoá đơn vị 2 PHÍA
# BUG THẬT (21/08, batch 14 SKU MBA khô THIBIDI, sheet 03 dòng 583-596):
# Hard Block chặn 5/5 dòng đầu với ['2950W','4%','740W'] — mọi số ĐỀU CÓ
# THẬT trong MASTER. Nguyên nhân xác nhận-từ-code:
#
#   MASTER lưu Po=740 (SỐ TRẦN), đơn vị nằm ở TÊN CỘT
#   "Tổn hao không tải Po (W, catalogue)" / nhãn bảng "Tổn hao không tải Po (W)".
#   _kho_cua_dong() chỉ chạy _SO_DON_VI.findall(giá_trị) — mà "740" không
#   có đơn vị dính kèm -> KHÔNG có gì vào kho. AI viết "740W" -> chặn.
#
# Nhánh `thong_so_dong` (cột quét động) ĐÃ có đúng cơ chế bóc đơn vị từ tên
# cột từ Ver 2.8. Nhánh field KHAI BÁO (cot_import/cot_bang) thì KHÔNG —
# thiếu sót thuần tuý, không phải quyết định thiết kế. Bản này bù đúng chỗ
# đó, KHÔNG nới bất kỳ luật so khớp nào khác.
#
# Vì sao "160 kVA" không dính: cột "Công Suất (kVA)" lưu nguyên chuỗi có
# đơn vị -> _SO_DON_VI bắt được. Vì sao 850/3959 lọt ở dòng 250kVA: lần đó
# AI viết số TRẦN, không kèm đơn vị -> _SO_DON_VI không bắt -> không kiểm
# tra luôn. (KHÔNG phải do dấu cách: _SO_DON_VI đã có `\s*`, "740 W" và
# "740W" bị chặn y hệt nhau — đã chạy thử xác nhận.)

# Đơn vị HỢP LỆ khi bóc từ nhãn cột. Dùng WHITELIST chứ không "mọi chữ cái
# trong ngoặc": nhãn thật trong Registry có "(E50)", "(catalogue)",
# "(giải mã)", "(CO/CQ/Quatest)", "(VNĐ)" — không phải đơn vị, bóc bừa thì
# kho số phình ra vô nghĩa. Khoá = dạng đã hạ chữ thường, bỏ khoảng trắng.
_DON_VI_TU_NHAN = {
    'w': 'W', 'kw': 'kW', 'kva': 'kVA', 'va': 'VA',
    'kv': 'kV', 'v': 'V', 'a': 'A', 'ka': 'kA', 'ma': 'mA',
    '%': '%', 'mm': 'mm', 'mm2': 'mm²', 'mm²': 'mm²', 'cm': 'cm', 'm': 'm',
    'kg': 'kg', 'hz': 'Hz', 'db': 'dB',
    '°c': '°C', 'độc': '°C', 'doc': '°C',
    'tháng': 'tháng', 'năm': 'năm',
    'mv/a/m': 'mV/A/m', 'ω/km': 'Ω/km', 'ohm/km': 'Ω/km',
}

# Đồng nhất các cách viết cùng 1 đơn vị về MỘT khoá so sánh duy nhất.
_DON_VI_DONG_NHAT = {'mm2': 'mm²', 'ohm/km': 'ω/km', '°c': 'doc', 'độc': 'doc'}

_SO_TRAN_RE = re.compile(r'\d+(?:[.,]\d+)?')
_NGOAC_RE = re.compile(r'[\(\[]([^\)\]]*)[\)\]]')


def _chuan_gia_tri_so(so):
    """Chuẩn hoá PHẦN SỐ về 1 dạng duy nhất, áp cho CẢ HAI PHÍA (kho lấy từ
    MASTER và chuỗi AI viết): bỏ khoảng trắng, dấu phẩy thập phân VN -> dấu
    chấm, cắt số 0 thừa cuối phần thập phân ("4.0" -> "4", "0.60" -> "0.6").

    KHÔNG làm tròn, KHÔNG bỏ chữ số có nghĩa: 745 vẫn khác 740."""
    s = str(so).strip().replace(' ', '').replace(',', '.')
    if not re.fullmatch(r'\d+(?:\.\d+)?', s):
        return s.lower()
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s or '0'


def _chuan_don_vi(dv):
    """Chuẩn hoá ĐƠN VỊ về 1 khoá so sánh: bỏ khoảng trắng, hạ chữ thường,
    gộp các cách viết đồng nghĩa (mm2 = mm², Ohm/km = Ω/km, °C = độ C)."""
    d = re.sub(r'\s+', '', str(dv or '')).lower()
    return _DON_VI_DONG_NHAT.get(d, d)


def _don_vi_tu_nhan(nhan):
    """Bóc danh sách đơn vị từ 1 nhãn cột / tên cột Excel.

    Chỉ đọc phần trong ngoặc `(...)` hoặc `[...]`, tách theo dấu phẩy/chấm
    phẩy (KHÔNG tách theo `/` vì mV/A/m và Ω/km là đơn vị ghép), rồi lọc
    qua whitelist _DON_VI_TU_NHAN.

        "Tổn hao không tải Po (W, catalogue)" -> ['W']
        "Điện áp ngắn mạch Uk (%, catalogue)" -> ['%']
        "Điện trở DC tối đa 20C (Ohm/km)"     -> ['Ω/km']
        "Hiệu suất năng lượng tối thiểu (E50)"-> []      (E50 không phải đơn vị)
        "Giá List (VNĐ)"                      -> []      (tiền, không phải thông số)
    """
    ra = []
    for trong_ngoac in _NGOAC_RE.findall(str(nhan or '')):
        for phan in re.split(r'[,;]', trong_ngoac):
            khoa = re.sub(r'\s+', '', phan).lower()
            dv = _DON_VI_TU_NHAN.get(khoa)
            if dv and dv not in ra:
                ra.append(dv)
    return ra


_CACHE_DON_VI_FIELD = {}


def _don_vi_theo_field(profile_id, outline_id):
    """Trả {field nội bộ: [đơn vị]} cho đúng cặp (profile, outline).

    Hai nguồn nhãn, gộp lại:
      1. `cot_bang` của Registry — (field, nhãn) sẵn có, VD ('ton_hao_khong_tai',
         'Tổn hao không tải Po (W)').
      2. TÊN CỘT EXCEL trong `cot_import` — phủ thêm field chỉ nằm trong
         cot_ai mà không lên bảng thông số.

    CHỈ lấy field nằm trong cot_ai/cot_bang hiệu lực — field nội bộ
    (gia_list, ghi_chu...) không bao giờ vào đây, y như 3 kho hiện có.

    Cache theo (profile_id, outline_id): render 245 bài không phải dựng lại
    map 245 lần."""
    khoa = (profile_id, outline_id)
    if khoa in _CACHE_DON_VI_FIELD:
        return _CACHE_DON_VI_FIELD[khoa]
    ra = {}
    try:
        cot_bang = P.effective_cot_bang(profile_id, outline_id)
        cho_phep = set(P.effective_cot_ai(profile_id, outline_id)) | {k for k, _ in cot_bang}
    except (KeyError, TypeError):
        _CACHE_DON_VI_FIELD[khoa] = ra
        return ra
    for field, nhan in cot_bang:
        for dv in _don_vi_tu_nhan(nhan):
            if dv not in ra.setdefault(field, []):
                ra[field].append(dv)
    for ten_cot, field in (P.PROFILES.get(profile_id, {}).get('cot_import') or {}).items():
        if field not in cho_phep:
            continue
        for dv in _don_vi_tu_nhan(ten_cot):
            if dv not in ra.setdefault(field, []):
                ra[field].append(dv)
    _CACHE_DON_VI_FIELD[khoa] = ra
    return ra


def _chuan_cum(s):
    """Chuẩn hoá 1 cụm kỹ thuật để so sánh: bỏ khoảng trắng, hạ chữ thường,
    BỎ hậu tố đơn vị cuối cùng. Lý do bỏ đơn vị: theo quy ước R2-07, nhiều
    field lưu giá trị KHÔNG kèm đơn vị (VD tiet_dien='3x50', đơn vị nằm ở
    nhãn "Tiết diện (mm²)"), trong khi AI viết văn xuôi tự nhiên sẽ kèm đơn
    vị ("3x50mm²"). Cái cần chống bịa là PHẦN SỐ (3x50 thật hay 9x50 giả),
    không phải có/không có chữ "mm²" theo sau — so sánh phần số sau khi bỏ
    đơn vị vẫn phát hiện đúng số giả (0.6/1 khác 99/1), không bị vướng lệch
    quy ước có/không đơn vị giữa các field."""
    s = re.sub(r'\s+', '', s).lower().replace(',', '.')
    s = _DON_VI_CUOI_RE.sub('', s).lower()
    # Ver 5.6 — chuẩn hoá NỐT phần số bên trong cụm, để "22/0.40" (MASTER)
    # và "22/0.4" (AI viết) là MỘT. Không đụng tới phần chữ.
    return _SO_TRAN_RE.sub(lambda m: _chuan_gia_tri_so(m.group(0)), s)


def _chuan_so(so, dv):
    # Ver 5.6 — chuẩn hoá 2 phần RIÊNG rồi mới ghép, thay vì ghép chuỗi thô.
    # Nhờ vậy "740W" / "740 W" / "740w" / "740.0W" ra cùng một khoá, còn
    # "745W" vẫn ra khoá khác -> vẫn chặn.
    return f'{_chuan_gia_tri_so(so)}{_chuan_don_vi(dv)}'


def _kho_cua_dong(row):
    """Mọi số hợp lệ có trong CHÍNH record này — chỉ tính field cot_ai/
    cot_bang (không tính gia_list dù nó có số, vì gia_list không phải dữ
    liệu kỹ thuật được phép nhắc)."""
    kho = set()
    profile_id, outline_id = row['profile_id'], row['outline_id']
    fields = set(P.effective_cot_ai(profile_id, outline_id)) | \
        {k for k, _ in P.effective_cot_bang(profile_id, outline_id)}
    nhan_dv = _don_vi_theo_field(profile_id, outline_id)
    for k in fields:
        v = row.get(k, '')
        for so, dv in _SO_DON_VI.findall(v):
            kho.add(_chuan_so(so, dv))
        # Ver 5.6 — VÁ LỖI THẬT: field khai báo lưu SỐ TRẦN, đơn vị nằm ở
        # TÊN CỘT ("Tổn hao không tải Po (W, catalogue)" = "740"). Ghép
        # lại đúng như nhánh cột quét động đã làm từ Ver 2.8. Field RỖNG
        # -> _SO_TRAN_RE không tìm được số nào -> KHÔNG thêm gì vào kho
        # (đây là chỗ giữ nguyên khả năng chặn bịa: cột trống thì AI viết
        # gì cũng chặn).
        for dv in nhan_dv.get(k, ()):
            for so in _SO_TRAN_RE.findall(str(v)):
                kho.add(_chuan_so(so, dv))
    # Ver 2.8 — cột QUÉT ĐỘNG cũng là dữ liệu THẬT của record, phải nằm
    # trong kho số hợp lệ. Nếu quên, Hard Block sẽ chặn nhầm chính số mà
    # tool vừa đưa cho AI — đúng họ lỗi row/row_ai từng mất 5 bản mới thấy.
    for ten_cot, v in (row.get('thong_so_dong') or {}).items():
        v = str(v)
        for so, dv in _SO_DON_VI.findall(v):
            kho.add(_chuan_so(so, dv))
        # Excel thường ghi đơn vị ở TÊN CỘT ("Tổn hao Po (W)") còn ô chỉ
        # có số trần ("340"). Bóc đơn vị trong ngoặc rồi ghép lại, nếu
        # không thì Hard Block sẽ chặn nhầm chính số tool vừa đưa cho AI.
        m_dv = re.search(r'\(([^)]*?)([A-Za-zΩ%²]+)[^)]*\)', str(ten_cot))
        if m_dv:
            dv_cot = m_dv.group(2)
            for so in re.findall(r'\d+(?:[.,]\d+)?', v):
                kho.add(_chuan_so(so, dv_cot))
        # Ver 5.6 — bổ sung (KHÔNG thay thế) bộ bóc theo whitelist: bắt
        # được nhãn nhiều đơn vị và nhãn dùng ngoặc vuông mà regex trên bỏ
        # sót. Thuần cộng thêm khoá -> không thể gây chặn nhầm mới.
        for dv in _don_vi_tu_nhan(ten_cot):
            for so in _SO_TRAN_RE.findall(v):
                kho.add(_chuan_so(so, dv))
    return kho


def _kho_cum_cua_dong(row):
    """Kho cụm kỹ thuật hoàn chỉnh (R2-08) — CHỈ những chuỗi có dấu nối
    x/+// mới tính, số đơn lẻ không vào kho này (đã có _kho_cua_dong lo)."""
    kho = set()
    profile_id, outline_id = row['profile_id'], row['outline_id']
    fields = set(P.effective_cot_ai(profile_id, outline_id)) | \
        {k for k, _ in P.effective_cot_bang(profile_id, outline_id)}
    for k in fields:
        v = row.get(k, '')
        for m in _CUM_KY_THUAT_RE.finditer(v):
            kho.add(_chuan_cum(m.group(0)))
    # Ver 3.2 — VÁ NỐT HỌ LỖI CỦA VER 2.8: hồi đó chỉ thêm cột quét động
    # vào _kho_cua_dong (số đơn lẻ), QUÊN 2 kho còn lại. Hậu quả: enrich
    # Excel thêm cột có giá trị dạng CỤM ("3x50mm²") thì Hard Block chặn
    # nhầm chính số tool vừa đưa cho AI.
    for v in (row.get('thong_so_dong') or {}).values():
        for m in _CUM_KY_THUAT_RE.finditer(str(v)):
            kho.add(_chuan_cum(m.group(0)))
    return kho


def _kho_mo_rong_cua_dong(row):
    """Gate 2 Task 2 — kho cụm mở rộng (bảo hành/IP/IEC-TCVN/nhiệt độ/%) có
    trong CHÍNH record này. Quét cùng field như 2 kho trên — nếu record nào
    đó sau này có field mang loại dữ liệu này (VD thêm cột 'Cấp bảo vệ' cho
    1 profile), giá trị thật của field đó sẽ tự động được phép nhắc."""
    kho = set()
    profile_id, outline_id = row['profile_id'], row['outline_id']
    fields = set(P.effective_cot_ai(profile_id, outline_id)) | \
        {k for k, _ in P.effective_cot_bang(profile_id, outline_id)}
    nhan_dv = _don_vi_theo_field(profile_id, outline_id)
    for k in fields:
        v = row.get(k, '')
        for m in _CUM_MO_RONG_RE.finditer(v):
            kho.add(_chuan_cum(m.group(0)))
        # Ver 5.6 — đây là chỗ làm chết cả batch MBA khô: cột "Điện áp ngắn
        # mạch Uk (%, catalogue)" lưu "4" (số trần), AI viết "4%" -> lớp 1
        # chặn vì kho mở rộng rỗng. Ghép số trần với đơn vị của nhãn rồi
        # mới quét, y hệt nhánh cột động. Cũng phủ luôn "(tháng)" cho
        # bao_hanh_thang và nhãn "(°C)" nếu sau này có.
        for dv in nhan_dv.get(k, ()):
            for so in _SO_TRAN_RE.findall(str(v)):
                for m in _CUM_MO_RONG_RE.finditer(f'{so}{dv}'):
                    kho.add(_chuan_cum(m.group(0)))
    # Ver 3.2 — cột quét động cũng phải vào kho MỞ RỘNG. Đây là chỗ làm
    # batch 5 bài 06/08 chết: cột "Tiêu chuẩn hiệu suất năng lượng áp
    # dụng" = "TCVN 8525:2015" và cột hiệu suất "(%)" nằm ở kho động,
    # nhưng kho mở rộng không quét tới -> chặn nhầm 'TCVN 8525:2015',
    # '99.1%', '4%' dù chúng CÓ THẬT trong record.
    for ten_cot, v in (row.get('thong_so_dong') or {}).items():
        v = str(v)
        for m in _CUM_MO_RONG_RE.finditer(v):
            kho.add(_chuan_cum(m.group(0)))
        # đơn vị nằm ở TÊN CỘT, ô chỉ có số trần -> ghép lại rồi mới quét
        m_dv = re.search(r'\(([^)]*?)([A-Za-zΩ%²]+)[^)]*\)', str(ten_cot))
        if m_dv:
            for so in re.findall(r'\d+(?:[.,]\d+)?', v):
                for m in _CUM_MO_RONG_RE.finditer(f'{so}{m_dv.group(2)}'):
                    kho.add(_chuan_cum(m.group(0)))
    return kho


def kiem_tra_bia(text, row):
    """Hard Block — CHỈ số/cụm có trong chính record này mới được phép. Số
    hoặc cụm chỉ tồn tại ở record khác (dù cùng hay khác profile) đều bị
    chặn, không có mức 'cảnh báo, vẫn cho đăng' (quyết định #2 Round 1).

    3 lớp, xét theo thứ tự CỤ THỂ NHẤT trước, CHUNG NHẤT sau — mỗi lớp cắt
    phần đã xét ra khỏi text trước khi lớp sau xử lý phần còn lại, để không
    báo trùng 2 lần cho cùng 1 chuỗi và không bị token con của 1 cụm hợp lệ
    làm sai lệch kết quả của cụm khác:

    1) Cụm MỞ RỘNG (Gate 2 Task 2) — bảo hành, IPxx, IEC/TCVN, nhiệt độ, %.
       Không profile nào hiện có field loại này -> gần như luôn bị chặn,
       đúng ý đồ (AI không có cơ sở để nhắc).
    2) Cụm KỸ THUẬT hoàn chỉnh (R2-08) — "0.6/1kV", "3x50mm²". Một token đơn
       lẻ trích từ TRONG cụm hợp lệ (VD "1kV" trích từ "0.6/1kV") không đủ để
       coi cả cụm khác "99/1kV" là hợp lệ.
    3) Token đơn lẻ (Round 1) — trên phần text chưa thuộc cụm nào ở trên.

    Trả list chuỗi bị chặn — rỗng thì bài được đăng.
    """
    text = text or ''
    chan = []

    # 1) cụm mở rộng trước tiên
    rieng_mo_rong = _kho_mo_rong_cua_dong(row)
    con_lai_1 = []
    vi_tri_cuoi = 0
    for m in _CUM_MO_RONG_RE.finditer(text):
        con_lai_1.append(text[vi_tri_cuoi:m.start()])
        vi_tri_cuoi = m.end()
        cum_goc = m.group(0)
        if _chuan_cum(cum_goc) not in rieng_mo_rong:
            chan.append(cum_goc.strip())
    con_lai_1.append(text[vi_tri_cuoi:])
    text_sau_mo_rong = ''.join(con_lai_1)

    # 2) cụm kỹ thuật hoàn chỉnh, trên phần chưa thuộc cụm mở rộng
    rieng_cum = _kho_cum_cua_dong(row)
    con_lai_2 = []
    vi_tri_cuoi = 0
    for m in _CUM_KY_THUAT_RE.finditer(text_sau_mo_rong):
        con_lai_2.append(text_sau_mo_rong[vi_tri_cuoi:m.start()])
        vi_tri_cuoi = m.end()
        cum_goc = m.group(0)
        # Ver 5.7 — ngày tháng không phải thông số kỹ thuật, không chặn.
        # Cắt khỏi text như mọi cụm đã xét khác để lớp 3 (token đơn lẻ)
        # không đem "2026" ra soi lại.
        if _la_ngay_thang(cum_goc):
            continue
        if _chuan_cum(cum_goc) not in rieng_cum:
            chan.append(cum_goc.strip())
        # cụm đã xét (dù chặn hay không) thì KHÔNG đưa phần bên trong vào
        # vòng kiểm token đơn nữa — tránh trùng lặp báo lỗi 2 lần cho cùng 1
        # chuỗi, và tránh false-positive khi 1 cụm hợp lệ có token con
        # (VD "1kV" trong "0.6/1kV" hợp lệ) bị đem so kiểu token đơn riêng lẻ.
    con_lai_2.append(text_sau_mo_rong[vi_tri_cuoi:])
    text_con_lai = ''.join(con_lai_2)

    # 3) token đơn lẻ trên phần text CHƯA thuộc cụm nào ở 2 bước trên
    rieng = _kho_cua_dong(row)
    kho_thanh_phan = _kho_thanh_phan_cum_theo_field(row)
    for so, dv in _SO_DON_VI.findall(text_con_lai):
        t = _chuan_so(so, dv)
        if t in rieng:
            continue
        # lớp 4 — chỉ nới khi giá trị là số con thật của 1 cụm ghép trong
        # CHÍNH record này VÀ đơn vị AI viết thuộc đúng họ đơn vị của field
        # sinh ra cụm đó (VD field cấp điện áp -> chỉ chấp nhận kV/V, không
        # chấp nhận A hay mm dù trùng giá trị số).
        # Ver 5.6 — dùng CÙNG hàm chuẩn hoá với _chuan_cum (kho thành phần
        # đi qua _chuan_cum), nếu không "0.40" và "0.4" lại lệch khoá.
        so_chuan_khong_dv = _chuan_gia_tri_so(so)
        ho_don_vi_ai_viet = _DON_VI_SANG_HO.get(dv.lower())
        if ho_don_vi_ai_viet and (so_chuan_khong_dv, ho_don_vi_ai_viet) in kho_thanh_phan:
            continue
        chan.append(f'{so}{dv}')

    return sorted(set(chan))


# ============================================================ Ver 2.5 — bố cục cao cấp
def dung_faq_schema(ai_data):
    """Ver 2.7 — FAQPage schema (đề xuất từ review chéo). Rank Math đã cài
    sẵn trên site nên schema này có cơ hội hiện rich snippet trong SERP.

    TRẢ RIÊNG, KHÔNG nhét vào html — cùng lý do với Product schema:
    WordPress lọc thẻ <script> khi POST REST API nhưng giữ text bên trong
    -> JSON lộ thành chữ trên trang (đã xảy ra thật).

    Không có FAQ -> trả None, không dựng schema rỗng."""
    if not _bat_schema():
        return None            # Ver 4.5 — nhường Rank Math
    faq = [q for q in (ai_data or {}).get('faq') or []
           if str(q.get('q', '')).strip() and str(q.get('a', '')).strip()]
    if not faq:
        return None
    return {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [{
            '@type': 'Question',
            'name': str(q['q']).strip(),
            'acceptedAnswer': {'@type': 'Answer',
                               'text': re.sub(r'<[^>]+>', ' ', str(q['a'])).strip()},
        } for q in faq],
    }


def _bat_schema():
    """Ver 4.5 — cờ nhường schema cho Rank Math.

    Rank Math + theme + SONEALEO đều có thể sinh Product/FAQPage -> trùng
    schema, GSC báo lỗi. Đặt SONEALEO_SCHEMA=0 để tool NGỪNG phát JSON-LD,
    để Rank Math lo. Mặc định BẬT (giữ nguyên hành vi cũ, an toàn cho site
    chưa cấu hình Rank Math schema).
    """
    import os
    return str(os.environ.get('SONEALEO_SCHEMA', '1')).strip().lower() \
        not in ('0', 'false', 'no', 'off')


def _slug_ngan():
    """Ver 2.6 — bật slug ngắn. Mặc định TẮT để bài cũ/quy trình cũ không
    đổi; bật cùng lúc với bố cục 2.5."""
    import os
    return str(os.environ.get('SLUG_NGAN', '0')).strip().lower() in ('1', 'true', 'yes', 'on')


def _PK_kho_row(row):
    """Danh sách SKU cùng dataset để module phụ kiện dò cặp.

    Đọc thẳng DB (chỉ 245 dòng của sheet máy biến áp, nhẹ). Có cache theo
    dataset_id để render 119 bài không phải truy vấn 119 lần.
    """
    import db_phase2 as DB
    ds = row.get('dataset_id') or ''
    if not hasattr(_PK_kho_row, '_cache'):
        _PK_kho_row._cache = {}
    if ds in _PK_kho_row._cache:
        return _PK_kho_row._cache[ds]
    con = DB.ket_noi()
    try:
        rows = DB.liet_ke_san_pham(con, dataset_id=ds or None,
                                   profile_id=row.get('profile_id'))
    finally:
        con.close()
    _PK_kho_row._cache[ds] = rows
    return rows


# ============================================================ Ver 3.6.1 — bộ lọc cuối
# Hai dấu vết làm bài đọc như AI viết, Thịnh phản hồi từ site thật:
#   1. gạch ngang dài "—" rải khắp bài
#   2. mở bài bằng câu hỏi tu từ ("Cần giải pháp hạ thế nguồn điện...?")
# Cả hai đến từ NHIỀU nguồn: AI viết, code tự sinh (kien_thuc_bien_thien có
# hơn 10 chỗ), và cột động. Nên lọc ở ĐIỂM NGHẼN CUỐI — chỗ mọi chuỗi đã
# ghép xong — thay vì đi sửa từng nguồn rồi vẫn sót.
#
# KHÔNG đụng gạch ngắn "–" (U+2013): nó dùng cho dải số ("15–100 kVA") là
# đúng chính tả, không phải dấu vết AI.
# Ver 3.6.3 — VÁ 2 lỗi Thịnh phát hiện trên bài thật:
#
# (a) Bộ lọc câu hỏi mở bài Ver 3.6.1 KHÔNG BAO GIỜ CHẠY. Nó neo vào đầu
#     chuỗi và chỉ cho phép tối đa MỘT thẻ <p> đứng trước. Nhưng chuỗi thật
#     là '<div class="snl-page"><div class="snl-hero">...<div class="snl-lead">
#     <p>Bạn đang tìm...?' — bốn tầng thẻ. Regex không khớp, câu hỏi vẫn lọt.
#     Nay bỏ qua MỌI thẻ mở đầu, không giới hạn số tầng.
#
# (b) AI trả về Markdown **in đậm**, không ai chuyển sang HTML nên dấu sao
#     hiện nguyên trên trang: '**Máy biến áp dầu 1Pha 15KVA**'. Chuyển
#     **...** thành <strong>. CHỈ xử dấu sao đôi — dấu sao đơn để nguyên vì
#     nó có thể là dấu nhân trong công thức.
_RE_HOI_MO_BAI = re.compile(
    r'^((?:\s*<[^>]+>\s*)*)([^.?!<>]{10,180}\?\s*)')
_RE_DAM = re.compile(r'\*\*(?=\S)(.+?)(?<=\S)\*\*', re.DOTALL)


def _bo_gach_dai(s):
    """'A — B' -> 'A, B'. Dấu — luôn có khoảng trắng hai bên trong văn xuôi
    tiếng Việt nên thay bằng dấu phẩy đọc trôi hơn gạch nối."""
    if not s:
        return s
    s = re.sub(r'\s*\u2014\s*', ', ', s)
    return re.sub(r',\s*,', ',', s)


def _doi_markdown_dam(s):
    """**đậm** -> <strong>đậm</strong>. Sót lại dấu sao lẻ thì xoá nốt."""
    if not s:
        return s
    s = _RE_DAM.sub(r'<strong>\1</strong>', s)
    return s.replace('**', '')


def _bo_cau_hoi_mo_bai(s, toi_thieu_con_lai=60):
    """Cắt câu hỏi tu từ mở đầu, bỏ qua mọi thẻ HTML bọc ngoài. Chỉ cắt khi
    phần còn lại vẫn đủ dài — không bao giờ để lại đoạn rỗng."""
    if not s:
        return s
    m = _RE_HOI_MO_BAI.match(s)
    if not m:
        return s
    the_mo = m.group(1)
    con_lai = s[m.end():]
    if len(re.sub(r'<[^>]+>', '', con_lai).strip()) < toi_thieu_con_lai:
        return s
    return the_mo + con_lai.lstrip()


def loc_dau_vet_ai(s):
    """Gọi ở điểm cuối, sau khi HTML đã ghép xong."""
    return _doi_markdown_dam(_bo_gach_dai(_bo_cau_hoi_mo_bai(s)))


# Trường nào được cắt câu hỏi mở bài: chỉ đoạn MỞ ĐẦU. Các mục khác
# (đặc điểm, ứng dụng, hướng dẫn chọn) có thể dùng câu hỏi giữa bài một
# cách hợp lệ, cắt vào là hỏng nghĩa.
_TRUONG_CAT_CAU_HOI = ('intro_html', 'meta_description')


def _loc_ai_data(ai_data):
    """Làm sạch từng trường văn xuôi AI trả về, TRƯỚC khi ghép vào bố cục.

    Áp cho mọi trường: bỏ gạch ngang dài, chuyển **đậm** sang <strong>.
    Riêng đoạn mở đầu: cắt thêm câu hỏi tu từ.
    """
    ra = {}
    for k, v in (ai_data or {}).items():
        if not isinstance(v, str):
            ra[k] = v
            continue
        v = _bo_gach_dai(v)
        if k == 'meta_description':
            # meta phải là CHỮ TRẦN: Google in nguyên văn thẻ nếu có.
            # Xoá dấu sao chứ không đổi thành <strong>.
            v = v.replace('**', '')
            v = _bo_cau_hoi_mo_bai(v, toi_thieu_con_lai=40)
        else:
            v = _doi_markdown_dam(v)
            if k in _TRUONG_CAT_CAU_HOI:
                v = _bo_cau_hoi_mo_bai(v)
        ra[k] = v
    return ra


def _dung_giao_dien_2_5():
    import os
    return str(os.environ.get('GIAO_DIEN_2_5', '0')).strip().lower() in ('1', 'true', 'yes', 'on')


def _dung_bai_2_5_wrapper(row, ai_data, site_cfg, mau, hau_to_slug,
                          san_pham_lien_quan, cung_dong):
    """Cầu nối: dựng sẵn các khối DỮ LIỆU bằng logic cũ (đã qua Hard Block,
    đã test kỹ), rồi giao cho giao_dien_2_5 lo BỐ CỤC.

    Tách rõ: dữ liệu do render_phase2 lo, giao diện do giao_dien_2_5 lo.
    Sửa giao diện không bao giờ đụng vào logic chống bịa số."""
    import giao_dien_2_5 as G2

    # --- các khối dữ liệu, dùng nguyên hàm cũ ---
    bang = bang_thong_so(row)
    ss = khoi_so_sanh_cong_suat(row, cung_dong)
    lq = khoi_san_pham_lien_quan(san_pham_lien_quan)
    try:
        import hinh_ky_thuat as HKT
        hinh = HKT.hinh_cho_row(row)
    except Exception:
        hinh = ''

    # --- khối kiến thức kỹ thuật (code viết cứng, nguồn TCVN/IEC) ---
    kien_thuc = [khoi_ve_thuong_hieu(row), khoi_chung_may_bien_ap(row),
                 khoi_ve_loi(row), khoi_cau_tao_phu_kien(row), khoi_bao_tri_lap_dat(row),
                 KCT.khoi_chiu_tai(row, _st, lambda v: html.escape(str(v))),
                 khoi_ve_cach_dien_cap_dien(row), khoi_giap_bao_ve_cap_dien(row),
                 khoi_chong_chay_cap_dien(row), khoi_ve_cau_tao_tu_dong_cat(row)]
    # Ver 3.2 — TẦNG 3 BIẾN THIÊN: kiến thức sinh từ dữ liệu của chính SKU
    # (dải công suất, số pha, dầu/khô, loại lõi, Po/Pk/Uk tra catalogue)
    # nên hai SKU khác dữ liệu ra hai bài khác chữ — thay cho khối viết
    # chết từng bị cắt còn 1 câu ở Ver 4.9.9 vì trùng lặp. Tốn 0 token AI.
    # Bọc try để lỗi ở đây KHÔNG làm hỏng bài (nhánh cũ vẫn chạy).
    try:
        import kien_thuc_bien_thien as _KTBT
        # Ver 3.6.4 — truyền danh sách SKU cùng dataset để khối so sánh lõi
        # lấy được Po của bản khác lõi khi bảng tra THIBIDI không có hãng
        # đó. Dùng chung cache với khối phụ kiện nên không thêm truy vấn DB.
        kien_thuc.append(_KTBT.tat_ca_khoi(row, anh_em=_PK_kho_row(row)))
    except Exception as _e:
        print(f'[Ver 3.2] Bỏ qua khối kiến thức biến thiên: {_e}')
    # Ver 3.6 — khối SẢN PHẨM ĐI KÈM (vỏ / giá treo <-> máy biến áp).
    # Ghép bằng (số pha, kVA, cấp điện áp) từ chính dữ liệu MASTER, 0 lượt
    # AI. Mục đích: trang phụ kiện đứng một mình quá mỏng (vỏ chỉ có 4 dòng
    # thông số), còn trang máy thì không nhắc gì tới vỏ -> mất cơ hội bán
    # kèm. KHÔNG gộp trang: 1 SKU vẫn 1 trang, đây chỉ là một khối liên kết.
    # Bọc try vì đây là khối THÊM — lỗi ở đây không được làm hỏng bài.
    try:
        import phu_kien_di_kem as _PK
        _ds = _PK.tim_di_kem(row, _PK_kho_row(row))
        _di_kem = _PK.khoi_html(row, _ds, _st, html.escape)
        if _di_kem:
            kien_thuc.append(_di_kem)
    except Exception as _e:
        print(f'[Ver 3.6] Bỏ qua khối phụ kiện đi kèm: {_e}')
    kien_thuc = [k for k in kien_thuc if k]

    # --- làm sạch HTML do AI trả (y như luồng cũ) ---
    ai_sach = dict(ai_data)
    for k in ('intro_html', 'dac_diem_html', 'ung_dung_html', 'huong_dan_chon_html'):
        if ai_sach.get(k):
            ai_sach[k] = sanitize_html(ai_sach[k])
    if ai_sach.get('faq'):
        ai_sach['faq'] = [{'q': q.get('q', ''), 'a': sanitize_html(q.get('a', ''))}
                          for q in ai_sach['faq'] if q.get('q')]

    # Ver 2.6 — tách hero sang short_description (WooCommerce hiện nó ngay
    # cạnh ảnh + nút mua ở ĐẦU trang; description bị đẩy xuống tab "Mô tả").
    ket_qua = G2.dung_bai_2_5(row, ai_sach, site_cfg,
                              bang_thong_so_html=bang, so_sanh_html=ss,
                              lien_quan_html=lq, hinh_svg=hinh,
                              khoi_kien_thuc=kien_thuc, tach_hero=True,
                              anh_em=_PK_kho_row(row))
    noi_dung = ket_qua['than']
    hero_html = ket_qua['hero']

    # --- schema: TRẢ RIÊNG, TUYỆT ĐỐI KHÔNG nhét vào 'html' ---
    # Ver 2.5 — suýt tái tạo lại lỗi đã vá: WordPress lọc thẻ <script> khi
    # POST qua REST API nhưng GIỮ text bên trong -> nguyên khối JSON-LD
    # hiện thành CHỮ THẬT trên trang (đã xảy ra thật, có ảnh chụp). Bản cũ
    # đã sửa bằng cách trả schema qua key riêng; bố cục mới phải theo
    # đúng như vậy, không được nhét lại vào html.
    la_mof = (row.get('outline_id') == 'outline_do_luong'
              and re.search(r'\bMOF\b', str(row.get('ten_goc') or ''), re.I))
    tieu_de = dung_tieu_de(row) if (row['outline_id'] == 'outline_may_bien_ap' or la_mof) else (
        ai_data.get('meta_title') or row.get('ten_goc', ''))
    meta_description = _doi_markdown_dam(
        _bo_gach_dai(ai_data.get('meta_description') or ''))[:300]
    return {
        'title': tieu_de,
        'slug': dung_slug(row, mau=mau, hau_to=hau_to_slug),
        'meta_description': meta_description,
        'html': _doi_markdown_dam(_bo_gach_dai(noi_dung)),
        'short_description': loc_dau_vet_ai(hero_html),
        'schema': dung_schema(row, description=meta_description),
        'faq_schema': dung_faq_schema(ai_data),   # Ver 2.7
    }
