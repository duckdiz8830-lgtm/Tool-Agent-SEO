# -*- coding: utf-8 -*-
"""
SONEALEO ULTRA 4.4.1.5 — DỌN RÁC BÀI ĐÃ ĐĂNG.

VẤN ĐỀ NÓ GIẢI:
  Bài sinh trước Ver 4.4 có chèn "chỗ chờ ảnh" (div.snl-cho-anh) — ô nhắc
  việc nội bộ ghi rõ chụp ảnh gì, tỷ lệ bao nhiêu. Ver 4.4 đã tắt việc
  sinh ô này, NHƯNG bài cũ trong WordPress vẫn còn.

  xu_ly_anh.chen_anh_vao_bai() chỉ xoá ô đó khi role tương ứng CÓ ảnh thật
  (_thay_slot_legacy chỉ chạy khi fig != ''). Role nào thiếu file thì ô ở
  nguyên -> khách đọc được hướng dẫn chụp ảnh nội bộ.

NGUYÊN TẮC:
  1. CHỈ XOÁ, không bao giờ viết thêm. Không gọi AI, không tốn quota.
  2. Mọi mẫu rác khai báo trong MAU_RAC — thêm rác mới = thêm 1 dòng,
     không phải sửa logic.
  3. don_rac_bai() là hàm THUẦN: vào chuỗi, ra chuỗi + danh sách đã xoá.
     Test được không cần mạng, không cần WordPress.
  4. Batch mặc định CHẠY THỬ (chi_thu=True) — không ghi gì lên WordPress
     cho tới khi gọi rõ chi_thu=False.
"""
import re

# ---------------------------------------------------------------- mẫu rác
# (mã, mô tả cho log, regex)
#
# LƯU Ý div.snl-cho-anh: bên trong nó CÓ div lồng (div.snl-cho-anh-ten),
# nên '.*?</div>' sẽ cắt sai chỗ — dừng ở </div> của div con. Phải neo
# theo <p class="snl-cho-anh-kt"> là thẻ cuối cùng trước </div> ngoài.
# Cùng cách neo mà _thay_slot_legacy trong xu_ly_anh.py đang dùng.
MAU_RAC = [
    ('cho_anh',
     'Ô chờ ảnh nội bộ (hướng dẫn chụp lộ ra cho khách)',
     re.compile(
         r'<div\s+class=["\']snl-cho-anh["\']>.*?'
         r'<p\s+class=["\']snl-cho-anh-kt["\']>.*?</p>\s*</div>'
         r'(?:\s*<p\s+class=["\']snl-anh-caption["\']>.*?</p>)?',
         re.I | re.S)),

    ('caption_mo_coi',
     'Chú thích ảnh không còn ảnh đi kèm',
     re.compile(
         r'(?<!</figure>)\s*<p\s+class=["\']snl-anh-caption["\']>.*?</p>',
         re.I | re.S)),

    ('marker_slot',
     'Marker chèn ảnh chưa được thay',
     re.compile(r'<!--\s*SNL_IMAGE_SLOT:[a-z_]+\s*-->', re.I)),

    ('comment_url_anh',
     'Comment hướng dẫn URL_ANH đời cũ',
     re.compile(r'<!--(?:(?!-->).)*URL_ANH(?:(?!-->).)*-->', re.I | re.S)),

    # Ver 4.6.2 — GIÁ LIST LOTECH lộ ra HTML công khai.
    # phu_kien_di_kem.py đọc thẳng gia_list nên đi vòng qua hàng rào
    # FIELD_CAM_TUYET_DOI -> chuỗi ' · 82.650.000 ₫' in ra trong khối
    # "Lắp cho máy biến áp nào" trên các bài đã đăng. 4.5 đã chặn ở tầng
    # sinh; luật này dọn phần ĐÃ ĐĂNG.
    # Neo rất chặt: phải nằm ngay trước </small>, đúng dạng ' · <số> ₫'.
    ('gia_list_lo',
     'Giá list Lotech lộ trong khối phụ kiện',
     re.compile(r'\s*·\s*[\d.,]+\s*₫(?=\s*</small>)', re.I)),

    # Ver 4.6.2 — caveat A2608: câu rào đón nội bộ lọt ra bài bán hàng.
    # Chỉ xoá đúng câu, không đụng phần còn lại của đoạn.
    ('caveat_a2608',
     'Câu caveat nội bộ A2608 / quyết định EVN lọt ra ngoài',
     re.compile(
         r'\s*<p[^>]*>(?:(?!</p>).)*?(?:A2608|2608/QĐ-EVN)'
         r'(?:(?!</p>).)*?</p>', re.I | re.S)),
]


def don_rac_bai(noi_dung):
    """Xoá mọi mẫu rác khỏi HTML bài. Trả (html_sach, {ma_rac: so_lan}).

    Hàm thuần, không I/O. Không đụng ảnh thật (figure.snl-hinh), không đụng
    bảng thông số, không đụng nội dung AI.
    """
    text = str(noi_dung or '')
    da_xoa = {}
    for ma, _mo_ta, pat in MAU_RAC:
        text, n = pat.subn('', text)
        if n:
            da_xoa[ma] = n
    return text, da_xoa


def mo_ta_rac(ma):
    for m, mo_ta, _ in MAU_RAC:
        if m == ma:
            return mo_ta
    return ma


# ---------------------------------------------------------------- 1 bài
def quet_1_bai(wp_id, la_woo=True, chi_thu=True, timeout=60):
    """Đọc bài thật từ WordPress -> dọn -> ghi lại NẾU có thay đổi.

    chi_thu=True: chỉ đọc và báo cáo, KHÔNG ghi. Đây là mặc định có chủ ý —
    ghi đè body production là thao tác không undo được bằng tool.

    Trả dict {ok, wp_id, thay_doi, da_xoa, giam_ky_tu, loi}
    """
    import ai_wp_adapter as AWP
    kq_doc = AWP.doc_noi_dung_bai_that(wp_id, la_woo=la_woo, timeout=timeout)
    if not kq_doc.get('ok'):
        return {'ok': False, 'wp_id': wp_id, 'thay_doi': False,
                'da_xoa': {}, 'giam_ky_tu': 0,
                'loi': 'Đọc bài lỗi: ' + kq_doc.get('loi', 'không rõ')}

    goc = kq_doc.get('content') or ''
    sach, da_xoa = don_rac_bai(goc)
    if not da_xoa:
        return {'ok': True, 'wp_id': wp_id, 'thay_doi': False,
                'da_xoa': {}, 'giam_ky_tu': 0, 'loi': ''}

    giam = len(goc) - len(sach)
    if chi_thu:
        return {'ok': True, 'wp_id': wp_id, 'thay_doi': True,
                'da_xoa': da_xoa, 'giam_ky_tu': giam, 'loi': '(chạy thử)'}

    kq_ghi = AWP.cap_nhat_noi_dung_bai_that(wp_id, sach, la_woo=la_woo,
                                            timeout=timeout)
    if not kq_ghi.get('ok'):
        return {'ok': False, 'wp_id': wp_id, 'thay_doi': False,
                'da_xoa': da_xoa, 'giam_ky_tu': 0,
                'loi': 'Ghi bài lỗi: ' + kq_ghi.get('loi', 'không rõ')}
    return {'ok': True, 'wp_id': wp_id, 'thay_doi': True,
            'da_xoa': da_xoa, 'giam_ky_tu': giam, 'loi': ''}


# ---------------------------------------------------------------- hàng loạt
def quet_hang_loat(danh_sach_bai, la_woo=True, chi_thu=True,
                   goi_lai_tien_do=None, co_dung=None, timeout=60):
    """Quét nhiều bài. danh_sach_bai: list dict có khoá 'wp_id'.

    co_dung: object có .get() trả True khi Thịnh bấm Dừng (dùng chung cơ
    chế với gỡ bài hàng loạt).

    Trả {tong, sach_san, da_don, loi, chi_tiet, tong_theo_ma}
    """
    tong = len(danh_sach_bai or [])
    sach_san = 0        # bài vốn đã sạch
    da_don = 0          # bài có rác
    loi = 0
    chi_tiet = []
    tong_theo_ma = {}

    for i, b in enumerate(danh_sach_bai or [], 1):
        if co_dung is not None:
            try:
                if co_dung.get():
                    break
            except Exception:
                pass
        wp_id = b.get('wp_id')
        kq = quet_1_bai(wp_id, la_woo=la_woo, chi_thu=chi_thu, timeout=timeout)
        kq['record_id'] = b.get('record_id', '')
        kq['title'] = b.get('title', '')
        chi_tiet.append(kq)
        if not kq['ok']:
            loi += 1
        elif kq['thay_doi']:
            da_don += 1
            for ma, n in kq['da_xoa'].items():
                tong_theo_ma[ma] = tong_theo_ma.get(ma, 0) + n
        else:
            sach_san += 1
        if goi_lai_tien_do:
            goi_lai_tien_do(i, tong, da_don, sach_san, loi)

    return {'tong': tong, 'sach_san': sach_san, 'da_don': da_don,
            'loi': loi, 'chi_tiet': chi_tiet, 'tong_theo_ma': tong_theo_ma}
