# -*- coding: utf-8 -*-
"""
SONEALEO ULTRA 3.2 — BẢNG TRA CATALOGUE THIBIDI.

NGUỒN: Optimize-THIBIDI-Catalogue-TV-25112025.pdf (bản 25/11/2025)
  - Trang 10: MBA ngâm dầu 1 pha (6 mức) + 3 pha (17 mức)
  - Trang 13: MBA khô 3 pha (13 mức)

CÁCH LẤY: bóc bằng TOẠ ĐỘ chữ trong PDF (pymupdf), KHÔNG dùng AI, KHÔNG
đoán. Lý do phải dùng toạ độ: trích text thô cho ra thứ tự đọc bị đảo
(mức 3200kVA nhảy vào giữa danh sách) -> ghép sai kVA với thông số. Đây
đúng là lý do đợt nạp 12 catalogue PDF trước đây thất bại (15/245 SKU).
Dựng theo toạ độ thì cột thẳng hàng, số tăng đơn điệu đúng quy luật vật
lý, và đối chiếu khớp ảnh chụp trang 19 do Thịnh gửi.

Ý NGHĨA SỐ LIỆU — đọc kỹ trước khi dùng:
  - Đây là THÔNG SỐ CỰC ĐẠI THEO CATALOGUE của dòng sản phẩm THIBIDI,
    KHÔNG phải số đo của từng máy cụ thể đã bán. Máy thật thường tốt hơn.
  - Chỉ áp dụng cho SKU hãng THIBIDI. Hãng khác (MBT, EMC, HBT, KP,
    Shihlin) có bảng riêng — CHƯA CÓ, không được suy sang.
  - Ghi chú của chính catalogue: Po/Pk của máy Amorphous 3 pha mức 180kVA
    và 2500kVA là NỘI SUY TUYẾN TÍNH theo TCCS 10:2021/EVN, không phải đo.
"""

NGUON = 'Catalogue THIBIDI 25/11/2025'

# (kVA): (Po lõi Silic W, Po lõi Amorphous W, Pk W, Uk %)
DAU_1PHA = {
    15: (52, 14, 213, 2), 25: (67, 19, 333, 2), 37.5: (92, 26, 420, 2),
    50: (108, 31, 570, 2), 75: (148, 42, 933, 2), 100: (192, 54, 1305, 2),
}
DAU_3PHA = {
    100: (205, 60, 1250, 4), 160: (280, 76, 1940, 4), 180: (295, 81, 2090, 4),
    250: (340, 100, 2600, 4), 320: (385, 116, 3170, 4), 400: (433, 132, 3820, 4),
    560: (580, 176, 4810, 4), 630: (780, 216, 5570, 4), 750: (845, 232, 6540, 5),
    800: (880, 248, 6920, 5), 1000: (980, 280, 8550, 5), 1250: (1115, 336, 10690, 5),
    1500: (1223, 376, 12825, 6), 1600: (1305, 392, 13680, 6),
    2000: (1500, 464, 17100, 6), 2500: (1850, 554, 21000, 6),
    # Ver 3.6.1 — XOÁ Po Amorphous mức 3200: bảng cũ ghi 554W, TRÙNG ĐÚNG mức
    # 2500kVA. Máy 3.200kVA không thể có tổn hao không tải bằng máy 2.500kVA.
    # Đối chiếu TCCS 10:2021/EVN (QĐ 107/QĐ-HĐTV): bảng tiêu chuẩn DỪNG Ở
    # 2.000kVA, ghi chú cuối bảng chỉ cho phép NỘI suy giữa 2 mức có sẵn —
    # mức 3.200 là ngoại suy, không có cơ sở. Để None thay vì số sai.
    3200: (2340, None, 24460, 7),
}
# Mức nội suy theo ghi chú của chính catalogue — đánh dấu để bài ghi rõ.
NOI_SUY_3PHA = {180, 2500}

# (kVA): (Po 24kV, Po 35kV, Pk 24kV, Pk 35kV, hiệu suất tối thiểu %)
KHO_3PHA = {
    160: (740, 960, 2950, 3000, 98.15), 250: (850, 1300, 3959, 4370, 98.46),
    320: (1020, 1500, 4620, 4800, 98.59), 400: (1150, 1700, 5405, 5860, 98.66),
    560: (1610, 2200, 6900, 8000, 98.77), 630: (1700, 2200, 7130, 8000, 98.80),
    750: (2050, 2850, 7498, 9700, 98.85), 1000: (2400, 3100, 8211, 11500, 98.92),
    1250: (2850, 3700, 11914, 14000, 98.97), 1600: (3300, 4300, 13110, 17000, 99.02),
    2000: (4100, 5100, 14111, 21000, 99.06), 2500: (5150, 6400, 17411, 25000, 99.09),
    3200: (6050, 7500, 21505, 29000, 99.13),
}
# Uk% máy khô theo dải công suất (in gộp ô trên catalogue)
KHO_UK = [(630, 4.0), (1250, 5.0), (2500, 6.0), (3200, 7.0)]


def _uk_kho(kva):
    for tran, uk in KHO_UK:
        if kva <= tran:
            return uk
    return None


def tra(kva, pha, loai_may, thuong_hieu=''):
    """Tra bảng THIBIDI. Trả dict hoặc None nếu ngoài phạm vi.

    CHẶN CỨNG: chỉ trả số khi thương hiệu là THIBIDI (hoặc để trống —
    khi đó gọi bên ngoài tự chịu trách nhiệm). Không suy sang hãng khác.
    """
    th = str(thuong_hieu or '').upper()
    if th and 'THIBIDI' not in th and 'TBD' not in th:
        return None
    try:
        kva = float(kva)
    except (TypeError, ValueError):
        return None
    if loai_may == 'kho':
        if pha != 3 or kva not in KHO_3PHA:
            return None
        po24, po35, pk24, pk35, hs = KHO_3PHA[kva]
        return {'loai': 'kho', 'kva': kva, 'po_24kv': po24, 'po_35kv': po35,
                'pk_24kv': pk24, 'pk_35kv': pk35, 'hieu_suat': hs,
                'uk': _uk_kho(kva), 'nguon': NGUON, 'noi_suy': False}
    bang = DAU_1PHA if pha == 1 else DAU_3PHA if pha == 3 else None
    if bang is None or kva not in bang:
        return None
    po_s, po_a, pk, uk = bang[kva]
    return {'loai': 'dau', 'kva': kva, 'po_silic': po_s, 'po_amorphous': po_a,
            'pk': pk, 'uk': uk, 'nguon': NGUON,
            'noi_suy': pha == 3 and kva in NOI_SUY_3PHA}


def muc_lan_can(kva, pha, loai_may):
    """Trả (mức dưới, mức trên) trong cùng dải công suất — dùng cho khối
    'chọn công suất'. Không có thì trả None."""
    bang = (KHO_3PHA if loai_may == 'kho' else
            DAU_1PHA if pha == 1 else DAU_3PHA)
    ds = sorted(bang)
    try:
        kva = float(kva)
    except (TypeError, ValueError):
        return None, None
    duoi = max((k for k in ds if k < kva), default=None)
    tren = min((k for k in ds if k > kva), default=None)
    return duoi, tren
