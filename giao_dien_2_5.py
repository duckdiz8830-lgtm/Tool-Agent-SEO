# -*- coding: utf-8 -*-
"""
SONEALEO Ver 2.5 — GIAO DIỆN CAO CẤP (bộ khối mới).

MỤC TIÊU
Nâng trang sản phẩm từ "bảng thông số + vài đoạn văn" lên bố cục thương
mại đúng chuẩn B2B: hero 2 cột, thông số nhanh, chip đặc điểm, mục lục
neo, thẻ tóm tắt, FAQ gập, CTA cố định trên mobile.

VÌ SAO TÁCH FILE RIÊNG
`render_phase2.py` đã 1.400 dòng và giữ toàn bộ logic Hard Block + dữ
liệu. Bộ khối giao diện là thứ SẼ THAY ĐỔI NHIỀU (đổi màu, đổi bố cục,
thêm khối) — tách ra để sửa giao diện không đụng vào logic chống bịa số.

NGUYÊN TẮC GIỮ NGUYÊN TỪ Ver 2.1
- CSS nằm ở class, KHÔNG inline. Tất cả style tập trung ở STYLE_2_5 để
  `xuat_file_css()` sinh ra 1 file dán lên WordPress 1 lần.
- Đổi giao diện = sửa file CSS trên site, KHÔNG cần đăng lại 5.264 bài.
- Không dữ liệu thì không dựng khối (không hiện khung rỗng).
"""
import html
import re

# ---------------------------------------------------------------- bảng màu
MAU = {
    'navy': '#12233f',
    'red': '#d0342c',
    'line': '#e3e8ef',
    'soft': '#f5f7fa',
    'muted': '#6b7789',
    'ink': '#2a3648',
    'blue_soft': '#eaf2ff',
    'blue_ink': '#1b4f9c',
    'green': '#0f9d6f',
    'green_soft': '#eefaf5',
    'amber_soft': '#fff8e6',
    'amber_line': '#e8d191',
}

# ---------------------------------------------------------------- style
# Mỗi khoá -> 1 class CSS (.snl-<khoá gạch ngang>). Viết gọn, không dùng
# tính năng CSS lạ để tránh bị theme/plugin bảo mật lọc.
STYLE_2_5 = {
    # -- khung trang
    'page': 'max-width:1180px;margin:0 auto;color:#2a3648;'
            'font-size:16px;line-height:1.65',
    'breadcrumb': 'color:#6b7789;font-size:13px;margin:0 0 14px',

    # -- hero
    'hero': 'display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));'
            'gap:32px;padding:0 0 30px;border-bottom:1px solid #e3e8ef;margin:0 0 26px',
    'hero-visual': 'position:relative;background:linear-gradient(145deg,#f9fafb,#eef2f6);'
                   'border:1px solid #e3e8ef;border-radius:16px;padding:18px;'
                   'display:flex;align-items:center;justify-content:center;min-height:280px',
    'hero-info': 'min-width:0',
    'kicker': 'display:inline-block;color:#d0342c;font-weight:700;font-size:13px;'
              'text-transform:uppercase;letter-spacing:.08em;margin:0 0 8px',
    'lead': 'font-size:17px;color:#4f5c70;margin:0 0 20px',

    # -- chip đặc điểm
    'chip-row': 'display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px;padding:0;list-style:none',
    'chip': 'display:inline-block;border:1px solid #d9e1ec;background:#fff;'
            'border-radius:999px;padding:6px 12px;font-size:13px;font-weight:600;color:#31415d',
    'chip-nguon': 'display:inline-block;border:1px solid #cfe0ff;background:#eaf2ff;'
                  'border-radius:999px;padding:6px 12px;font-size:13px;font-weight:600;color:#1b4f9c',

    # -- bảng thông số nhanh (2 cột)
    'quick': 'display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));'
             'border:1px solid #e3e8ef;border-radius:14px;overflow:hidden;margin:0 0 18px',
    'quick-o': 'padding:13px 15px;border-bottom:1px solid #e3e8ef;border-right:1px solid #e3e8ef',
    'quick-nhan': 'display:block;color:#6b7789;font-size:12px;text-transform:uppercase;'
                  'letter-spacing:.05em;font-weight:700',
    'quick-gt': 'display:block;color:#12233f;font-size:17px;font-weight:700;margin-top:3px',

    # -- giá + nút
    'price': 'display:flex;align-items:baseline;justify-content:space-between;gap:14px;'
             'padding:14px 17px;background:#f5f7fa;border-radius:12px;margin:0 0 14px',
    'price-nhan': 'color:#6b7789;font-weight:700;font-size:14px',
    'price-gt': 'font-size:21px;font-weight:800;color:#d0342c',
    'actions': 'display:flex;flex-wrap:wrap;gap:10px;margin:0 0 14px',
    'btn': 'display:inline-flex;align-items:center;justify-content:center;gap:8px;'
           'text-decoration:none;border-radius:11px;padding:13px 20px;font-weight:700;'
           'font-size:15px;border:1px solid transparent',
    'btn-chinh': 'background:#d0342c;color:#fff',
    'btn-phu': 'background:#fff;border:1px solid #bdc8d8;color:#12233f',
    'proof': 'display:block;margin-top:14px;padding:11px 14px;border-left:3px solid #0f9d6f;'
             'background:#eefaf5;border-radius:8px;color:#2f5a4d;font-size:13px',

    # -- mục lục neo
    'nav': 'display:flex;flex-wrap:wrap;gap:6px;padding:10px 0;margin:0 0 22px;'
           'border-top:1px solid #e3e8ef;border-bottom:1px solid #e3e8ef',
    'nav-link': 'text-decoration:none;font-size:13px;font-weight:700;color:#53607a;'
                'padding:7px 12px;border-radius:9px;background:#f5f7fa',

    # -- section
    'section': 'margin:0 0 34px',
    'section-head': 'display:flex;justify-content:space-between;align-items:flex-end;'
                    'gap:20px;margin:0 0 16px;flex-wrap:wrap',
    'h2': 'font-size:26px;line-height:1.25;color:#12233f;margin:0',
    'section-intro': 'max-width:760px;color:#6b7789;margin:6px 0 0;font-size:15px',
    'nguon-badge': 'font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;'
                   'border:1px solid #cfe0ff;background:#eaf2ff;color:#1b4f9c;'
                   'border-radius:999px;padding:5px 10px;white-space:nowrap',

    # -- thẻ tóm tắt
    'summary-grid': 'display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px',
    'summary-card': 'border:1px solid #e3e8ef;border-radius:14px;padding:18px;background:#fff',
    'card-title': 'display:block;color:#12233f;font-size:17px;font-weight:700;margin:0 0 6px',
    'card-text': 'color:#4f5c70;margin:0;font-size:15px',

    # -- bảng thông số đầy đủ
    'spec-wrap': 'display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px',
    'table': 'width:100%;border-collapse:collapse;border:1px solid #e3e8ef;border-radius:14px;'
             'overflow:hidden;font-size:15px',
    'th': 'padding:13px 15px;text-align:left;border-bottom:1px solid #e3e8ef;background:#f8fafc;'
          'color:#4d5a6e;font-size:13px;text-transform:uppercase;letter-spacing:.03em;width:42%',
    'td': 'padding:13px 15px;text-align:left;border-bottom:1px solid #e3e8ef;color:#2a3648',
    'origin': 'display:inline-block;font-size:10px;padding:2px 6px;margin-left:6px;border-radius:5px;'
              'background:#eaf2ff;color:#1b4f9c;text-transform:uppercase;letter-spacing:.03em',

    # -- ghi chú vàng
    'note': 'border:1px solid #e8d191;background:#fff8e6;border-radius:14px;padding:17px;'
            'font-size:14px;color:#5c4a1e',
    'note-title': 'display:block;font-weight:700;color:#12233f;margin:0 0 7px;font-size:15px',

    # -- checklist
    'checklist': 'list-style:none;margin:0;padding:0;display:grid;gap:8px',
    'check-item': 'position:relative;padding-left:24px;color:#4f5c70;font-size:15px',

    # -- FAQ
    'faq': 'display:grid;gap:10px',
    'faq-item': 'border:1px solid #e3e8ef;border-radius:12px;padding:15px 17px;background:#fff',
    'faq-q': 'font-weight:700;color:#12233f;cursor:pointer;font-size:16px',
    'faq-a': 'margin:9px 0 0;color:#4f5c70;font-size:15px',

    # -- CTA
    'cta': 'background:#12233f;color:#fff;border-radius:18px;padding:28px;margin:30px 0 0',
    'cta-title': 'font-size:23px;font-weight:800;margin:0 0 8px;color:#fff',
    'cta-text': 'margin:0 0 18px;color:#c8d4e8;font-size:15px',
    'cta-actions': 'display:flex;flex-wrap:wrap;gap:10px',

    # -- CTA giữa bài (Ver 2.6)
    'cta-giua': 'display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;'
                'gap:14px;padding:18px 22px;margin:0 0 30px;background:#fff8e6;'
                'border:1px solid #e8d191;border-radius:14px',
    'cta-giua-text': 'margin:0;font-weight:700;color:#12233f;font-size:16px',

    # -- hình kỹ thuật
    'tech-card': 'border:1px solid #e3e8ef;border-radius:16px;padding:18px;background:#fff',
    'tech-note': 'margin:10px 0 0;color:#6b7789;font-size:13px',
}


def _esc(s):
    return html.escape(str(s or ''))


def _cls(khoa):
    return f'snl-{khoa}'


def _c(khoa):
    """Trả attribute class hoàn chỉnh."""
    return f'class="{_cls(khoa)}"'


def xuat_css_2_5():
    """Sinh CSS cho bộ khối 2.5 — sinh TỪ CHÍNH STYLE_2_5 nên không bao
    giờ lệch với HTML render ra."""
    dong = ['/* ===== SONEALEO 2.5 — bộ khối giao diện cao cấp ===== */']
    for khoa, css in STYLE_2_5.items():
        tt = '; '.join(x.strip() for x in css.split(';') if x.strip())
        dong.append(f'.{_cls(khoa)} {{ {tt}; }}')
    # vài quy tắc không map 1-1 với 1 khoá
    dong += [
        '.snl-check-item:before { content: "✓"; position: absolute; left: 0; top: 0;'
        ' color: #0f9d6f; font-weight: 800; }',
        '.snl-quick-o:nth-child(even) { border-right: 0; }',
        '.snl-nav-link:hover { background: #e9eef5; color: #12233f; }',
        '.snl-btn:hover { opacity: .92; }',
        '@media (max-width: 640px) {',
        '  .snl-hero { gap: 20px; }',
        '  .snl-h2 { font-size: 22px; }',
        '  .snl-cta { padding: 20px; }',
        '}',
    ]
    return '\n'.join(dong) + '\n'


# ============================================================ các khối
def _hero_hien_chip_quick():
    """Ver 3.6.2 — mặc định TẮT chip + bảng nhanh ở hero (xem dung_bai_2_5).
    Bật lại bằng HERO_HIEN_CHIP_QUICK=1 trong cau-hinh.env."""
    import os
    return str(os.environ.get('HERO_HIEN_CHIP_QUICK', '0')).strip().lower() \
        in ('1', 'true', 'yes', 'on')


def khoi_chip(danh_sach):
    """danh_sach: list (chu, la_nguon). Bỏ mục rỗng."""
    muc = [(c, n) for c, n in danh_sach if str(c or '').strip()]
    if not muc:
        return ''
    li = ''.join(f'<li {_c("chip-nguon") if n else _c("chip")}>{_esc(c)}</li>' for c, n in muc)
    return f'<ul {_c("chip-row")}>{li}</ul>'


def khoi_quick(cap_gia_tri):
    """cap_gia_tri: list (nhãn, giá trị). Bỏ cặp thiếu giá trị."""
    muc = [(n, v) for n, v in cap_gia_tri if str(v or '').strip()]
    if not muc:
        return ''
    o = ''.join(f'<div {_c("quick-o")}><span {_c("quick-nhan")}>{_esc(n)}</span>'
                f'<strong {_c("quick-gt")}>{_esc(v)}</strong></div>' for n, v in muc)
    return f'<div {_c("quick")}>{o}</div>'


def khoi_gia_va_nut(gia_hien_thi, nut):
    """nut: list (nhãn, href, la_chinh)."""
    ra = [f'<div {_c("price")}><span {_c("price-nhan")}>Giá</span>'
          f'<strong {_c("price-gt")}>{_esc(gia_hien_thi)}</strong></div>']
    nut = [(t, h, c) for t, h, c in nut if t and h]
    if nut:
        a = ''.join(
            f'<a href="{_esc(h)}" class="{_cls("btn")} {_cls("btn-chinh") if c else _cls("btn-phu")}">'
            f'{_esc(t)}</a>' for t, h, c in nut)
        ra.append(f'<div {_c("actions")}>{a}</div>')
    return ''.join(ra)


def khoi_muc_luc(muc):
    """muc: list (id_neo, nhãn). Dưới 2 mục thì không dựng (thừa)."""
    muc = [(i, n) for i, n in muc if i and n]
    if len(muc) < 2:
        return ''
    a = ''.join(f'<a href="#{_esc(i)}" {_c("nav-link")}>{_esc(n)}</a>' for i, n in muc)
    return f'<nav {_c("nav")}>{a}</nav>'


def mo_section(id_neo, tieu_de, gioi_thieu='', nhan_nguon=''):
    badge = f'<span {_c("nguon-badge")}>{_esc(nhan_nguon)}</span>' if nhan_nguon else ''
    intro = f'<p {_c("section-intro")}>{_esc(gioi_thieu)}</p>' if gioi_thieu else ''
    return (f'<section {_c("section")} id="{_esc(id_neo)}">'
            f'<div {_c("section-head")}><div><h2 {_c("h2")}>{_esc(tieu_de)}</h2>{intro}</div>'
            f'{badge}</div>')


def dong_section():
    return '</section>'


def khoi_the_tom_tat(the):
    """the: list (tiêu đề, nội dung)."""
    the = [(t, n) for t, n in the if t and n]
    if not the:
        return ''
    c = ''.join(f'<div {_c("summary-card")}><b {_c("card-title")}>{_esc(t)}</b>'
                f'<p {_c("card-text")}>{_esc(n)}</p></div>' for t, n in the)
    return f'<div {_c("summary-grid")}>{c}</div>'


def khoi_ghi_chu(tieu_de, noi_dung_html):
    if not noi_dung_html:
        return ''
    tt = f'<b {_c("note-title")}>{_esc(tieu_de)}</b>' if tieu_de else ''
    return f'<div {_c("note")}>{tt}{noi_dung_html}</div>'


def khoi_checklist(muc):
    muc = [m for m in muc if str(m or '').strip()]
    if not muc:
        return ''
    li = ''.join(f'<li {_c("check-item")}>{_esc(m)}</li>' for m in muc)
    return f'<ul {_c("checklist")}>{li}</ul>'


def khoi_faq(cau_hoi):
    """cau_hoi: list (hỏi, đáp). Dùng <details> để gập/mở — không cần JS,
    WordPress không lọc mất."""
    ch = [(q, a) for q, a in cau_hoi if str(q or '').strip() and str(a or '').strip()]
    if not ch:
        return ''
    it = ''.join(
        f'<details {_c("faq-item")}><summary {_c("faq-q")}>{_esc(q)}</summary>'
        f'<p {_c("faq-a")}>{_esc(a)}</p></details>' for q, a in ch)
    return f'<div {_c("faq")}>{it}</div>'


def khoi_cta(tieu_de, mo_ta, nut, id_neo='lien-he-bao-gia'):
    nut = [(t, h, c) for t, h, c in nut if t and h]
    a = ''.join(
        f'<a href="{_esc(h)}" class="{_cls("btn")} {_cls("btn-chinh") if c else _cls("btn-phu")}">'
        f'{_esc(t)}</a>' for t, h, c in nut)
    khoi_nut = f'<div {_c("cta-actions")}>{a}</div>' if a else ''
    return (f'<div {_c("cta")} id="{_esc(id_neo)}">'
            f'<div {_c("cta-title")}>{_esc(tieu_de)}</div>'
            f'<p {_c("cta-text")}>{_esc(mo_ta)}</p>{khoi_nut}</div>')


def khoi_cta_giua(nut):
    """Ver 2.6 — CTA chèn GIỮA bài (sau mục Ứng dụng). Trước 2.6 chỉ có
    CTA ở hero và cuối trang; bài dài nên khúc giữa mất hút, khách đọc
    tới đoạn thấy hợp nhu cầu thì không có nút nào để bấm."""
    nut = [(t, h, ch) for t, h, ch in (nut or []) if t and h]
    if not nut:
        return ''
    a = ''.join(
        f'<a href="{_esc(h)}" class="{_cls("btn")} {_cls("btn-chinh") if ch else _cls("btn-phu")}">'
        f'{_esc(t)}</a>' for t, h, ch in nut[:2])
    return (f'<div {_c("cta-giua")}>'
            f'<p {_c("cta-giua-text")}>Cần tư vấn cấu hình cho công trình cụ thể?</p>'
            f'<div {_c("cta-actions")}>{a}</div></div>')


def khoi_hinh_ky_thuat(svg_html, ghi_chu=''):
    if not svg_html:
        return ''
    gc = f'<p {_c("tech-note")}>{_esc(ghi_chu)}</p>' if ghi_chu else ''
    return f'<div {_c("tech-card")}>{svg_html}{gc}</div>'


# ============================================================ ráp bài hoàn chỉnh
# Ver 2.6 — đơn vị mặc định cho từng field. Dữ liệu MASTER có chỗ ghi
# "15 kVA", có chỗ chỉ "15" -> chip/quick hiện số trơ trọi, khó đọc
# (Thịnh phản hồi). Chỉ thêm khi giá trị CHƯA có đơn vị, không nhân đôi.
_DON_VI = {'cong_suat': 'kVA', 'cap_dien_ap': 'kV', 'tiet_dien': 'mm²'}


def _them_don_vi(khoa, gia_tri):
    v = str(gia_tri or '').strip()
    if not v:
        return v
    dv = _DON_VI.get(khoa)
    if not dv:
        return v
    # đã có đơn vị (bất kỳ chữ cái nào ngoài số/dấu) -> giữ nguyên
    if re.search(r'[A-Za-zΩ²]', v):
        return v
    return f'{v} {dv}'


def _chip_tu_row(row):
    """Rút 3-5 đặc điểm ngắn từ dữ liệu THẬT của record để làm chip.
    Không có thì bỏ, không bịa."""
    ra = []
    for k in ('cong_suat', 'cap_dien_ap', 'tiet_dien'):
        v = _them_don_vi(k, row.get(k))
        if v:
            ra.append((v, False))
    ten = str(row.get('ten_goc', '')).lower()
    for tu, nhan in (('amorphous', 'Lõi Amorphous'), ('silic', 'Lõi Silic'),
                     ('kiểu kín', 'Kiểu kín'), ('khô', 'Máy khô'),
                     ('xlpe', 'Cách điện XLPE')):
        if tu in ten:
            ra.append((nhan, False))
    for k, nhan in (('vat_lieu_ruot_giai_ma', None), ('loai_cach_dien_giai_ma', None),
                    ('giap_bao_ve_giai_ma', 'Có giáp bảo vệ')):
        v = row.get(k)
        if v:
            ra.append((nhan or v, False))
    if row.get('thuong_hieu'):
        ra.append((row['thuong_hieu'], False))
    # bỏ trùng, giữ thứ tự, tối đa 6
    da, kq = set(), []
    for c, n in ra:
        if c not in da:
            da.add(c)
            kq.append((c, n))
    return kq[:6]



# ============================================================ Ver 3.3 — ảnh & biểu đồ
def _cho_anh(ma):
    """Gọi khoi_anh.cho_anh, lỗi thì trả '' — không để hỏng cả bài."""
    try:
        import khoi_anh as KA
        return KA.cho_anh(ma)
    except Exception as e:
        print(f'[Ver 3.3] Bỏ qua chỗ chờ ảnh "{ma}": {e}')
        return ''


def _slot_anh(ma):
    """Ver 4.4.1.2 — marker NỘI BỘ để pipeline ảnh thay đúng vị trí.

    Cả 5 role đều có marker body; đồng thời Woo gallery vẫn giữ đủ 5 ảnh.
    Marker không chứa URL/hướng dẫn và bị xóa trước khi gửi WordPress.
    """
    if ma not in ('hero', 'bien_may', 'can_canh', 'lap_dat', 'giao_hang'):
        return ''
    return f'<!--SNL_IMAGE_SLOT:{ma}-->'


def _bieu_do(loai, row, anh_em=None):
    try:
        import khoi_anh as KA
        return KA.bieu_do_ton_hao(row, anh_em) if loai == 'ton_hao' else KA.bieu_do_loi(row, anh_em)
    except Exception as e:
        print(f'[Ver 3.3] Bỏ qua biểu đồ "{loai}": {e}')
        return ''


def dung_bai_2_5(row, ai_data, site_cfg, bang_thong_so_html='', so_sanh_html='',
                 lien_quan_html='', hinh_svg='', khoi_kien_thuc=(), tieu_de='',
                 cot_bang=(), tach_hero=False, anh_em=None):
    """Ráp bài theo bố cục cao cấp 2.5.

    Nhận HTML đã dựng sẵn từ render_phase2 (bảng thông số, so sánh, liên
    quan, hình) — module này CHỈ lo bố cục/giao diện, KHÔNG đụng dữ liệu
    hay Hard Block.
    """
    site_cfg = site_cfg or {}
    hotline = site_cfg.get('hotline', '')
    zalo = site_cfg.get('zalo', hotline)
    ten_site = site_cfg.get('ten', '')

    # ---- HERO
    # Ver 2.7 — SVG XUỐNG BODY (Thịnh yêu cầu): sơ đồ kỹ thuật ở hero dễ
    # bị Google Images index như ảnh sản phẩm chính, không mong muốn. Đưa
    # xuống mục "Cấu tạo" trong thân bài, đúng vai trò minh hoạ kỹ thuật.
    # Hero để trống chỗ ảnh -> WooCommerce tự hiện ảnh thật khi có.
    visual = ''

    # Ver 3.6.2 — TẮT chip + bảng nhanh ở hero theo góp ý của sếp Quân.
    # Lý do (Thịnh soát trên bài thật): H1 đã ghi đủ "Máy biến áp dầu MBT
    # 15kVA (lõi Amorphous)", rồi chip nhắc lại y hệt 4 thứ đó, rồi bảng
    # nhanh nhắc lần thứ ba, rồi bảng thông số đầy đủ phía dưới nhắc lần
    # thứ tư. Ba lần lặp trong 400px đầu, đẩy đoạn văn thật và nút báo giá
    # xuống dưới màn hình — trên điện thoại còn tệ hơn.
    #
    # MỘT cờ gom cả hai, không tách thành 2-3 cờ: chúng luôn đi cùng nhau,
    # tách ra là mở đầu cho một tab cấu hình 20 dòng mà sáu tháng nữa không
    # ai nhớ cái nào làm gì.
    #   HERO_HIEN_CHIP_QUICK=0  (mặc định) — chỉ lead + giá
    #   HERO_HIEN_CHIP_QUICK=1            — hiện lại, để so sánh khi cần
    if _hero_hien_chip_quick():
        chip = khoi_chip(_chip_tu_row(row))
        quick = khoi_quick([
            ('Mã hàng', row.get('ma_goc')),
            ('Thương hiệu', row.get('thuong_hieu')),
            ('Công suất', _them_don_vi('cong_suat', row.get('cong_suat'))),
            ('Cấp điện áp', _them_don_vi('cap_dien_ap', row.get('cap_dien_ap'))),
            ('Tiết diện', _them_don_vi('tiet_dien', row.get('tiet_dien'))),
            ('Đơn vị tính', row.get('dvt')),
        ])
    else:
        chip = quick = ''
    nut = []
    if hotline:
        nut.append((f'Gọi {hotline}', f'tel:{re.sub(r"[^0-9+]", "", hotline)}', True))
    if zalo:
        nut.append(('Chat Zalo', f'https://zalo.me/{re.sub(r"[^0-9]", "", zalo)}', False))
    if not nut:
        nut.append(('Yêu cầu báo giá', '#lien-he-bao-gia', True))
    # Ver 2.7 — BỎ nút CTA ở hero (Thịnh đã cài CTA riêng trên theme, 2 cái
    # sát nhau gây ngộp). Giữ dòng giá vì đó là thông tin, không phải CTA.
    gia_nut = (f'<div {_c("price")}><span {_c("price-nhan")}>Giá</span>'
               f'<strong {_c("price-gt")}>Liên hệ</strong></div>')

    lead = ''
    if ai_data.get('intro_html'):
        lead = f'<div {_c("lead")}>{ai_data["intro_html"]}</div>'

    hero = (f'<div {_c("hero")}>'
            f'<div {_c("hero-info")}>'
            f'<div {_c("kicker")}>{_esc(row.get("thuong_hieu", "Thiết bị điện"))}</div>'
            f'{lead}{chip}{quick}{gia_nut}</div></div>')

    # ---- MỤC LỤC (chỉ mục nào thật sự có nội dung)
    muc = []
    if bang_thong_so_html:
        muc.append(('thong-so', 'Thông số kỹ thuật'))
    if ai_data.get('dac_diem_html'):
        muc.append(('dac-diem', 'Đặc điểm'))
    if ai_data.get('ung_dung_html'):
        muc.append(('ung-dung', 'Ứng dụng'))
    if ai_data.get('huong_dan_chon_html'):
        muc.append(('huong-dan', 'Hướng dẫn chọn'))
    if ai_data.get('goc_nhin_thi_truong_html'):
        muc.append(('goc-nhin', 'Góc nhìn thị trường'))
    if so_sanh_html:
        muc.append(('so-sanh', 'So sánh trong dòng'))
    if hinh_svg:
        muc.append(('cau-tao', 'Sơ đồ cấu tạo'))
    if khoi_kien_thuc:
        muc.append(('kien-thuc', 'Kiến thức kỹ thuật'))
    # Ver 3.3 — VÁ: trước đây mục lục thêm "Câu hỏi thường gặp" chỉ cần
    # ai_data['faq'] khác rỗng, nhưng phần dựng section lại lọc thêm điều
    # kiện q VÀ a cùng có -> FAQ toàn câu thiếu đáp án thì mục lục có link
    # mà bài không có section (Thịnh phát hiện trên bài thật). Dùng CHUNG
    # một phép lọc cho cả hai chỗ.
    faq_dung = [(q.get('q'), q.get('a')) for q in (ai_data.get('faq') or [])
                if q.get('q') and q.get('a')]
    if faq_dung:
        muc.append(('faq', 'Câu hỏi thường gặp'))

    # Ver 2.6 — TÁCH HERO sang short_description (Thịnh phát hiện, đúng
    # chỗ ăn tiền nhất): WooCommerce hiện short_description NGAY CẠNH ảnh
    # và nút mua ở đầu trang, còn description bị đẩy xuống tab "Mô tả".
    # Trước 2.6 toàn bộ hero (chip + thông số nhanh + giá + CTA) nằm trong
    # description -> thứ quan trọng nhất lại ở chỗ ít người cuộn tới.
    if tach_hero:
        than = [f'<div {_c("page")}>', khoi_muc_luc(muc), _slot_anh('hero')]
    else:
        than = [f'<div {_c("page")}>', hero, khoi_muc_luc(muc), _slot_anh('hero')]
    phan = than

    # ---- THÔNG SỐ
    if bang_thong_so_html:
        # Ver 2.6 — bỏ câu "Số liệu lấy trực tiếp từ dữ liệu sản phẩm,
        # không suy đoán" (Thịnh phản hồi): đó là ngôn ngữ NỘI BỘ nói về
        # cách tool hoạt động, khách mua hàng không quan tâm — đúng lỗi
        # mà bản đối chiếu cũng mắc phải.
        phan += [mo_section('thong-so', 'Thông số kỹ thuật'),
                 bang_thong_so_html, _slot_anh('bien_may'), dong_section()]

    # ---- NỘI DUNG AI
    # Ver 2.6 — "Hướng dẫn lựa chọn" -> "Chọn công suất phù hợp": tên cũ
    # nghe như tài liệu kỹ thuật, tên mới đúng ngữ cảnh mua hàng hơn.
    # CTA GIỮA BÀI chèn ngay sau "Ứng dụng" — đúng lúc khách vừa xác nhận
    # sản phẩm hợp nhu cầu, trước khi phải cuộn hết trang mới thấy nút.
    for id_neo, tieu, khoa in (('dac-diem', 'Đặc điểm', 'dac_diem_html'),
                               ('ung-dung', 'Ứng dụng', 'ung_dung_html'),
                               ('huong-dan', 'Chọn công suất phù hợp', 'huong_dan_chon_html')):
        if ai_data.get(khoa):
            phan += [mo_section(id_neo, tieu), ai_data[khoa]]
            # Ver 3.3 — 2 biểu đồ sinh từ số catalogue, đặt đúng chỗ người
            # đọc đang cân nhắc mức công suất. Không tra được -> trả '',
            # không chèn gì.
            if khoa == 'huong_dan_chon_html':
                phan += [_bieu_do('ton_hao', row, anh_em), _bieu_do('loi', row, anh_em)]
            phan.append(dong_section())
            if khoa == 'ung_dung_html':
                phan.append(khoi_cta_giua(nut))

    # ---- GÓC NHÌN THỊ TRƯỜNG (Ver 2.6 — khối Enhance riêng, có nhãn)
    if ai_data.get('goc_nhin_thi_truong_html'):
        phan += [mo_section('goc-nhin', 'Góc nhìn từ thị trường',
                            'Tổng hợp từ nhu cầu và cách triển khai thực tế của công trình cùng loại.',
                            nhan_nguon='Khảo sát thị trường'),
                 ai_data['goc_nhin_thi_truong_html'], dong_section()]

    # ---- SO SÁNH
    if so_sanh_html:
        phan += [mo_section('so-sanh', 'So sánh công suất trong dòng'),
                 so_sanh_html, dong_section()]

    # ---- CẤU TẠO (Ver 2.7 — nơi mới của sơ đồ kỹ thuật SVG)
    if hinh_svg:
        phan += [mo_section('cau-tao', 'Sơ đồ cấu tạo',
                            'Sơ đồ minh hoạ nguyên lý, không theo tỷ lệ kích thước thật.'),
                 khoi_hinh_ky_thuat(hinh_svg), _slot_anh('can_canh'), dong_section()]

    # ---- KIẾN THỨC KỸ THUẬT (khối code viết cứng, có nguồn TCVN/IEC)
    if khoi_kien_thuc:
        phan.append(mo_section('kien-thuc', 'Kiến thức kỹ thuật liên quan',
                               nhan_nguon='TCVN / IEC'))
        phan.extend(k for k in khoi_kien_thuc if k)
        phan.append(dong_section())

    # ---- ẢNH LẮP ĐẶT (Ver 3.3 — ảnh chốt đơn, đặt trước khối liên hệ)
    # Ver 3.7 — đủ 5 ô, khớp workspace_anh.VAI_TRO. Trước chỉ có 3 ô nên
    # người quản trị không có chỗ nhắc ảnh đại diện và ảnh giao hàng.
    phan.append(_slot_anh('lap_dat'))
    phan.append(_slot_anh('giao_hang'))

    # ---- LIÊN QUAN
    if lien_quan_html:
        phan.append(lien_quan_html)

    # ---- FAQ
    if faq_dung:
        ch = faq_dung
        f = khoi_faq(ch)
        if f:
            phan += [mo_section('faq', 'Câu hỏi thường gặp'), f, dong_section()]

    # ---- CTA
    # Ver 2.7 — BỎ khối CTA cuối bài (theme đã có sẵn khối CTA ngay dưới,
    # 2 khối lớn sát nhau gây ngộp — Thịnh và bản đối chiếu đều chỉ ra).
    # Chỉ giữ CTA GIỮA BÀI, chỗ khách vừa xác nhận sản phẩm hợp nhu cầu.
    phan.append('</div>')
    than_html = ''.join(p for p in phan if p)
    if tach_hero:
        return {'hero': f'<div {_c("page")}>{hero}</div>', 'than': than_html}
    return than_html
