# -*- coding: utf-8 -*-
"""Ver 4.6 — cổng chặn bài MỎNG và bài TRÙNG, chạy TRƯỚC khi render.

VÌ SAO
  Bài học đắt nhất của dự án: hai SKU anh em (CXV/DSTA 3x4 vs 3x6) trùng
  99,96% văn bản hiển thị — phát hiện SAU khi đã đăng 245 bài. Và 336 dòng
  máy biến áp mới chỉ điền được 5/17 dòng bảng thông số nhưng vẫn render
  được bình thường.

  Cả hai lỗi đều ĐO ĐƯỢC TRƯỚC khi tốn một token AI nào. Module này biến
  bài học đó thành hàng rào tự động: thấy vấn đề ở SKU thứ 3, không phải
  sau SKU thứ 245.

NGUYÊN TẮC
  - Chỉ ĐO và BÁO. Không tự sửa dữ liệu, không tự bỏ SKU.
  - Đo trên VĂN BẢN HIỂN THỊ (đã bóc thẻ HTML), không đo trên HTML thô —
    thẻ và class giống nhau sẽ thổi phồng độ giống.
  - So với SKU ANH EM: cùng mã cáp / cùng hãng+loại, vì đó mới là cặp thật
    sự cạnh tranh nhau trên SERP.
"""
import difflib
import re
from collections import defaultdict

NGUONG_TRUNG = 0.90        # >= 90% văn bản giống nhau -> cảnh báo
TOI_THIEU_DONG_BANG = 6    # bảng thông số dưới 6 dòng -> bài mỏng
TOI_THIEU_KY_TU = 1200     # văn bản hiển thị quá ngắn -> bài mỏng


def van_ban_hien_thi(html):
    """Bóc thẻ, gộp khoảng trắng. Đo trên cái người đọc thấy."""
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', str(html or ''),
               flags=re.S | re.I)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = re.sub(r'&[a-z]+;', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def _khoa_anh_em(row):
    """Nhóm SKU cạnh tranh nhau: cùng mã cáp, hoặc cùng hãng + outline."""
    ma = str(row.get('ma_cap_catalogue') or '').strip()
    if ma:
        return 'ma:' + ma
    return 'ho:{}|{}'.format(row.get('thuong_hieu') or '',
                             row.get('outline_id') or '')


def dem_dong_bang(html):
    """Số dòng thật sự in ra trong bảng thông số."""
    return len(re.findall(r'<tr\b', str(html or ''), re.I))


def soat(bo_bai):
    """bo_bai: list dict {record_id, ten_goc, html, row}.

    Trả về (bao_cao, canh_bao) — canh_bao là list dict để hiện lên UI/log.
    """
    canh_bao = []
    nhom = defaultdict(list)

    for b in bo_bai:
        vb = van_ban_hien_thi(b['html'])
        b['_vb'] = vb
        n_dong = dem_dong_bang(b['html'])

        ly = []
        if n_dong < TOI_THIEU_DONG_BANG:
            ly.append(f'bảng thông số chỉ {n_dong} dòng '
                      f'(tối thiểu {TOI_THIEU_DONG_BANG})')
        if len(vb) < TOI_THIEU_KY_TU:
            ly.append(f'văn bản hiển thị chỉ {len(vb)} ký tự '
                      f'(tối thiểu {TOI_THIEU_KY_TU})')
        if ly:
            canh_bao.append({'loai': 'MONG', 'record_id': b['record_id'],
                             'ten': b['ten_goc'], 'chi_tiet': '; '.join(ly)})
        nhom[_khoa_anh_em(b.get('row') or {})].append(b)

    # --- trùng lặp trong từng nhóm anh em ---
    for khoa, ds in nhom.items():
        if len(ds) < 2:
            continue
        for i in range(len(ds)):
            for j in range(i + 1, len(ds)):
                a, b = ds[i], ds[j]
                if not a['_vb'] or not b['_vb']:
                    continue
                ty = difflib.SequenceMatcher(None, a['_vb'], b['_vb']).ratio()
                if ty >= NGUONG_TRUNG:
                    canh_bao.append({
                        'loai': 'TRUNG', 'record_id': a['record_id'],
                        'ten': a['ten_goc'],
                        'chi_tiet': f'giống {100 * ty:.1f}% với "{b["ten_goc"][:45]}" '
                                    f'(ngưỡng {100 * NGUONG_TRUNG:.0f}%)'})

    bc = {
        'tong_bai': len(bo_bai),
        'so_mong': sum(1 for c in canh_bao if c['loai'] == 'MONG'),
        'so_trung': sum(1 for c in canh_bao if c['loai'] == 'TRUNG'),
        'do_dai_tb': (round(sum(len(b['_vb']) for b in bo_bai) / len(bo_bai))
                      if bo_bai else 0),
    }
    return bc, canh_bao


def in_bao_cao(bc, canh_bao, gioi_han=15):
    print(f"Soát {bc['tong_bai']} bài · dài trung bình {bc['do_dai_tb']} ký tự")
    print(f"  MỎNG : {bc['so_mong']}")
    print(f"  TRÙNG: {bc['so_trung']}")
    for c in canh_bao[:gioi_han]:
        print(f"   [{c['loai']}] {str(c['ten'])[:45]} — {c['chi_tiet']}")
    if len(canh_bao) > gioi_han:
        print(f"   ... còn {len(canh_bao) - gioi_han} cảnh báo nữa")
