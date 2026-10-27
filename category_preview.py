# -*- coding: utf-8 -*-
"""SONEALEO 4.0 — sinh preview HTML cho 9 danh mục Woo từ MASTER, không AI.

Không POST WordPress. Mọi số kỹ thuật mới đưa vào phần mô tả/bảng được
đối chiếu bằng Hard Block hiện có trên chính record nguồn sinh ra số đó.
"""
import html
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import nhap_phase2 as N
import render_phase2 as R

# dung_danh_muc() hiện sinh 11 tên từ MASTER Ver8. Hai tên dưới là category
# gốc/umbrella; bỏ hai root này còn đúng 9 landing category con cần preview.
DANH_MUC_GOC_KHONG_XUAT = {'Máy biến áp', 'Thiết bị đo lường điện'}


def _slug(s):
    s = unicodedata.normalize('NFD', str(s or ''))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('đ', 'd').replace('Đ', 'D').lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def _kva(row):
    v = str(row.get('cong_suat') or '')
    m = re.search(r'\d+(?:[.,]\d+)?', v)
    return float(m.group(0).replace(',', '.')) if m else None


def _fmt_num(v):
    return str(int(v)) if float(v).is_integer() else ('%g' % v)


def _dien_ap(row):
    return re.sub(r'\s+', ' ', str(row.get('cap_dien_ap') or '').strip())


def _link_san_pham(row):
    slug = R.dung_slug(row)
    sku = row.get('publish_sku') or row.get('ma_goc') or ''
    return f'<a href="/san-pham/{html.escape(slug, quote=True)}/">{html.escape(str(sku))}</a>'


def _assert_hard_block(token, row, context):
    """Không sửa/nới Hard Block: gọi thẳng kiem_tra_bia() hiện có.

    Token phải được kiểm trên CHÍNH record đã cung cấp giá trị đó. Nhờ vậy
    category-level summary không được phép mượn số từ record khác một cách
    mơ hồ và href/HTML markup không tạo false-positive.
    """
    chan = R.kiem_tra_bia(str(token), row)
    if chan:
        raise ValueError(f'Hard Block danh mục chặn {context}: token={token!r}, record={row.get("ma_goc")}, vi_pham={chan}')


def gom_danh_muc(master_path):
    rows = N.import_4_profile(str(master_path), chi_profile='may_bien_ap_do_luong')['may_bien_ap_do_luong']['rows']
    groups = defaultdict(list)
    all_names = set()
    for r in rows:
        for name in R.dung_danh_muc(r):
            all_names.add(name)
            if name not in DANH_MUC_GOC_KHONG_XUAT:
                groups[name].append(r)
    return dict(sorted(groups.items())), sorted(all_names)


def dung_html_danh_muc(name, rows):
    brands = sorted({str(r.get('thuong_hieu') or '').strip() for r in rows if str(r.get('thuong_hieu') or '').strip()})

    # Map value -> record nguồn để mỗi số được Hard Block xác minh đúng record.
    volt_map = {}
    kva_rows = defaultdict(list)
    for r in rows:
        # Ver 4.1 BUG-04: validation-blocked row không được tham gia aggregate.
        # Không sửa Hard Block; đây là pre-filter cùng invariant Save Draft.
        if r.get('nghi_van_dien_ap') is True:
            continue
        v = _dien_ap(r)
        # Hard Block hiện có là authority: field số tồn tại trong raw row nhưng
        # outline hiện tại không expose (VD vỏ máy mang theo cột điện áp của
        # MASTER) thì KHÔNG được đưa lên landing category.
        if v and not R.kiem_tra_bia(v, r) and v not in volt_map:
            volt_map[v] = r
        k = _kva(r)
        if k is not None:
            kva_token = f'{_fmt_num(k)}kVA'
            if not R.kiem_tra_bia(kva_token, r):
                kva_rows[k].append(r)

    parts = ['<section class="snl-category-description">',
             f'<h2>{html.escape(name)}</h2>']
    summary = [f'Danh mục hiện có <strong>{len(rows)} SKU</strong> trong MASTER Ver8.']

    if kva_rows:
        ks = sorted(kva_rows)
        lo_token = f'{_fmt_num(ks[0])}kVA'
        hi_token = f'{_fmt_num(ks[-1])}kVA'
        _assert_hard_block(lo_token, kva_rows[ks[0]][0], 'công suất nhỏ nhất')
        _assert_hard_block(hi_token, kva_rows[ks[-1]][0], 'công suất lớn nhất')
        summary.append(f'Dải công suất có dữ liệu từ <strong>{lo_token}</strong> đến <strong>{hi_token}</strong>.')

    if brands:
        summary.append('Hãng có mặt: <strong>' + html.escape(', '.join(brands)) + '</strong>.')

    if volt_map:
        volts = sorted(volt_map)
        for v in volts:
            _assert_hard_block(v, volt_map[v], 'cấp điện áp')
        summary.append('Cấp điện áp có dữ liệu: <strong>' + html.escape(', '.join(volts)) + '</strong>.')

    parts.append('<p>' + ' '.join(summary) + '</p>')
    parts.append('<p>Dữ liệu dưới đây được dựng trực tiếp từ MASTER; mục nào nguồn không có thì không tự bổ sung hoặc ước lượng.</p>')

    if kva_rows:
        parts.append('<h2>Mục lục theo công suất</h2>')
        parts.append('<table><thead><tr><th>Công suất</th><th>Sản phẩm</th></tr></thead><tbody>')
        for k in sorted(kva_rows):
            kva_token = f'{_fmt_num(k)}kVA'
            _assert_hard_block(kva_token, kva_rows[k][0], 'mục lục kVA')
            links = '<br>'.join(_link_san_pham(r) for r in sorted(kva_rows[k], key=lambda x: str(x.get('ma_goc') or '')))
            parts.append(f'<tr><td>{kva_token}</td><td>{links}</td></tr>')
        parts.append('</tbody></table>')
    else:
        parts.append('<p><strong>Mục lục kVA:</strong> MASTER không có trường công suất kVA cho các SKU trong danh mục này, nên không dựng bảng kVA giả.</p>')

    parts.append('</section>')
    return '\n'.join(parts)


def xuat_9_danh_muc(master_path, out_dir):
    groups, all_names = gom_danh_muc(master_path)
    if len(groups) != 9:
        raise ValueError(f'Kỳ vọng 9 danh mục sau khi bỏ 2 root, thực tế {len(groups)}: {list(groups)}; all={all_names}')
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = []
    for i, (name, rows) in enumerate(groups.items(), 1):
        body = dung_html_danh_muc(name, rows)
        p = out_dir / f'{i:02d}-{_slug(name)}.html'
        p.write_text(body, encoding='utf-8')
        result.append({'name': name, 'file': str(p), 'sku': len(rows),
                       'kva_levels': len({_kva(r) for r in rows if _kva(r) is not None})})
    return result, all_names


if __name__ == '__main__':
    base = Path(__file__).resolve().parent
    result, names = xuat_9_danh_muc(base / '8MASTER_ENRICHED_Ver8.xlsx', base / 'category-preview-4.0')
    print('ALL_CATEGORY_NAMES=' + ' | '.join(names))
    for x in result:
        print(f"{x['name']}: SKU={x['sku']}, KVA_LEVELS={x['kva_levels']}, FILE={x['file']}")
