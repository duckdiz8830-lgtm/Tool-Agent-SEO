# -*- coding: utf-8 -*-
"""Ver 4.4.1.6b — TẦNG DÙNG CHUNG cho mọi lần upload ảnh lên WordPress.

VÌ SAO CÓ FILE NÀY
    Trước bản này có HAI hàm upload ảnh khác nhau, cùng gọi
    POST /wp-json/wp/v2/media, mà hành vi lỗi khác hẳn nhau:

      autopost._url_anh_tren_wp      -> raise RuntimeError, cắt log 200 ký tự,
                                        KHÔNG retry.   Bị gọi từ 4 nơi, trong
                                        đó có tab Ảnh (đường dùng nhiều nhất).
      ai_wp_adapter.upload_anh_media -> trả dict, KHÔNG retry. Bị gọi 1 nơi.

    Hệ quả thật, đo được: bản 4.4.1.6 thêm retry vào `upload_anh_media` —
    tức là thêm vào đúng đường ÍT dùng nhất. 403 mà người dùng gặp đi qua
    `_url_anh_tren_wp`, không hưởng gì. Sửa một sợi trong bó dây mà tưởng
    đã sửa cả bó.

    File này là SỢI DUY NHẤT chạm mạng. Hai hàm trên giữ nguyên chữ ký cũ
    (không phá caller nào) nhưng bên trong đều gọi xuống đây, nên retry,
    cách đọc lỗi và cách ghi log CHỈ CÒN MỘT bản.

KHÔNG import autopost hay ai_wp_adapter ở đây — cả hai import ngược lên,
vòng import là vỡ ngay lúc khởi động.
"""
import random
import re
import time

# Mã lỗi đáng thử lại. 401/403-thật/413 KHÔNG nằm đây: thử lại vô nghĩa,
# chỉ tổ đập server. Riêng 403 nằm đây vì trong thực tế phần lớn 403 ở
# WordPress shared-host là WAF chặn theo tốc độ, không phải sai quyền —
# phân biệt được vì sai quyền thì hỏng TOÀN BỘ, còn WAF thì lỗ chỗ.
MA_TAM_THOI = (403, 408, 429, 500, 502, 503, 504)

_HEADER_DAU_MOI = ('Server', 'CF-Ray', 'CF-Mitigated', 'X-Sucuri-ID',
                   'X-Powered-By', 'X-Mod-Security', 'Retry-After',
                   'X-LiteSpeed-Cache')


def tom_tat_loi(r, gioi_han=600):
    """Rút thông tin DÙNG ĐƯỢC từ response lỗi -> (ngắn_cho_người, đầy_đủ_cho_log).

    Phòng thủ với object response tối giản (test cũ chỉ có status_code/text):
    hàm này chạy trên ĐƯỜNG BÁO LỖI, vỡ ở đây là nuốt mất lỗi gốc.
    """
    ma = getattr(r, 'status_code', 0)
    hd = getattr(r, 'headers', None) or {}
    ct = (hd.get('Content-Type') or '').lower()
    than = getattr(r, 'text', '') or ''

    dau_moi = [f'{h}={hd[h]}' for h in _HEADER_DAU_MOI if hd.get(h)]

    nguon = ''
    if 'json' in ct:
        try:
            j = r.json()
            nguon = str(j.get('message') or j.get('code') or '')[:300]
        except Exception:
            nguon = than[:300]
    if not nguon:
        m = re.search(r'<title[^>]*>(.*?)</title>', than, re.I | re.S)
        if m:
            nguon = re.sub(r'\s+', ' ', m.group(1)).strip()[:200]
        mid = re.search(r'(mod_security|ModSecurity|Reference\s*#[\w.]+|'
                        r'incident ID[:\s]*[\w-]+)', than, re.I)
        if mid:
            dau_moi.append(mid.group(1).strip())
    if not nguon:
        nguon = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', than)).strip()[:200]

    if ma == 403 and 'json' not in ct:
        goi_y = ('Bị CHẶN Ở TẦNG SERVER (WAF/mod_security), chưa vào tới '
                 'WordPress. Thường do upload liên tiếp quá nhanh — tool đã '
                 'tự thử lại vài lần, bấm thử lại lần nữa thường là được. '
                 'Sai quyền thì hỏng TOÀN BỘ chứ không lỗ chỗ như thế này.')
    elif ma == 429:
        goi_y = 'Bị giới hạn tốc độ. Chờ rồi thử lại, giảm số ảnh mỗi lượt.'
    elif ma in (500, 502, 503, 504):
        goi_y = 'Máy chủ web đang lỗi/quá tải. Thử lại sau ít phút.'
    elif ma == 401:
        goi_y = 'Sai user hoặc Application Password. Kiểm tab Cấu hình.'
    elif ma == 413:
        goi_y = 'Ảnh vượt giới hạn upload của host. Giảm kích thước ảnh.'
    else:
        goi_y = ''

    ngan = f'HTTP {ma}' + (f' — {nguon}' if nguon else '')
    if goi_y:
        ngan += '\n' + goi_y
    day_du = (f'HTTP {ma} | Content-Type: {ct or "?"}'
              + (' | ' + ' ; '.join(dau_moi) if dau_moi else '')
              + f'\n--- thân phản hồi ({len(than)} ký tự, cắt {gioi_han}) ---\n'
              + than[:gioi_han])
    return ngan, day_du


def post_media(url, auth, du_lieu_bytes, ten_file, mime, headers_goc=None,
               timeout=90, so_lan_thu=4, ghi_log=None):
    """Upload 1 ảnh, tự thử lại khi lỗi tạm thời. ĐƯỜNG DUY NHẤT chạm mạng.

    Trả (response_thanh_cong, None) hoặc (None, dict_loi).
    dict_loi: {loi, chi_tiet, tam_thoi, so_lan}
    """
    import requests
    headers = dict(headers_goc or {})
    headers['Content-Type'] = mime
    headers['Content-Disposition'] = f'attachment; filename="{ten_file}"'

    loi = {'loi': 'Không rõ', 'chi_tiet': '', 'tam_thoi': False, 'so_lan': 0}
    for lan in range(1, max(1, so_lan_thu) + 1):
        try:
            r = requests.post(f'{url}/wp-json/wp/v2/media', auth=auth,
                              headers=headers, data=du_lieu_bytes, timeout=timeout)
        except requests.exceptions.RequestException as e:
            loi = {'loi': f'{type(e).__name__}: {e}',
                   'chi_tiet': f'{type(e).__name__}: {e}',
                   'tam_thoi': True, 'so_lan': lan}
        else:
            if r.status_code in (200, 201):
                return r, None
            ngan, day_du = tom_tat_loi(r)
            tam = r.status_code in MA_TAM_THOI
            loi = {'loi': ngan, 'chi_tiet': day_du, 'tam_thoi': tam,
                   'so_lan': lan, 'status_code': r.status_code}
            if not tam:
                return None, loi        # 401/413… dừng ngay

        if lan >= max(1, so_lan_thu):
            return None, loi
        # Nhiễu ngẫu nhiên: nhiều ảnh trượt cùng lúc mà thử lại cùng thời
        # điểm thì lại kích đúng cái WAF vừa chặn mình.
        cho = min(2 * (2 ** (lan - 1)), 12) + random.uniform(0, 1.5)
        if ghi_log:
            ghi_log('   [ảnh] %s: %s — thử lại %d/%d sau %.1fs'
                    % (ten_file, loi['loi'].splitlines()[0], lan + 1, so_lan_thu, cho))
        time.sleep(cho)
    return None, loi
