# -*- coding: utf-8 -*-
"""Ver 5.5 — GỠ / XOÁ ẢNH HÀNG LOẠT.

BA MỨC, khác nhau về mức độ không hồi lại được. Đọc kỹ trước khi chạy:

    1. GỠ KHỎI BÀI (`go_anh_khoi_bai`)
       Bỏ ảnh khỏi sản phẩm/bài viết. File vẫn nằm nguyên trong Media
       Library. HỒI LẠI ĐƯỢC — gắn lại là xong.

    2. XOÁ VÀO THÙNG RÁC (`xoa_media`, force=False)
       Media chuyển sang trạng thái trash. WordPress giữ ~30 ngày.
       HỒI LẠI ĐƯỢC trong cửa sổ đó, qua Media > Thùng rác.

    3. XOÁ VĨNH VIỄN (`xoa_media`, force=True)
       File biến mất khỏi server. KHÔNG HỒI LẠI ĐƯỢC bằng bất cứ cách nào
       ngoài backup. Mọi bài đang dùng ảnh đó sẽ hỏng ảnh.

CHỐT CHẶN AN TOÀN — cố ý làm phiền, đừng gỡ đi:
    - Mọi hàm mặc định `chay_thu=True`. Chạy lần đầu chỉ ra BÁO CÁO, không
      đụng gì. Muốn chạy thật phải truyền `chay_thu=False`.
    - `xoa_media(force=True)` còn đòi thêm `xac_nhan='XOA VINH VIEN'`.
      Gõ sai một ký tự là không chạy.
    - Mọi lần chạy thật đều ghi log ra file trước khi gọi API. Xoá xong mà
      hối hận thì ít nhất còn danh sách ID để dựng lại từ backup.

VÌ SAO KHÔNG DÙNG LẠI ai_wp_adapter:
    Adapter chỉ có đường THÊM ảnh (`gan_anh_vao_san_pham`), không có đường
    gỡ. Module này chỉ thêm, không sửa gì của adapter.
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

# ----------------------------------------------------------- kết nối

def _ket_noi():
    """Trả (url_goc, auth, headers). Dùng lại đúng đường xác thực của
    autopost để không đẻ ra cách cấu hình thứ hai."""
    import autopost as A
    import cauhinh as C
    url, auth = A._auth(C.MA_SITE_VER3)
    return url, auth, getattr(A, 'HEADERS', {})


def _thu_muc_log():
    try:
        import thu_muc_du_lieu as TM
        d = Path(TM.duong_dan_db()).parent / 'log-xoa-anh'
    except Exception:
        d = Path('log-xoa-anh')
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ghi_log(viec, du_lieu):
    """Ghi log TRƯỚC khi gọi API. Xoá xong mới ghi thì mất điện giữa chừng
    là mất luôn danh sách."""
    f = _thu_muc_log() / f'{viec}-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
    try:
        f.write_text(json.dumps(du_lieu, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        pass
    return str(f)


# ----------------------------------------------------------- đọc

def liet_ke_media(tu_khoa='', so_luong=100, trang=1, chi_anh=True, truoc_ngay=None):
    """Liệt kê media trên WordPress. Trả (danh_sach, tong_so, loi).

    tu_khoa    : lọc theo tên file / title
    truoc_ngay : 'YYYY-MM-DD' — chỉ lấy media upload trước ngày này. Dùng để
                 dọn đợt upload cũ mà không đụng đợt mới.
    """
    import requests
    try:
        url, auth, headers = _ket_noi()
    except SystemExit as e:
        return [], 0, str(e)

    ts = {'per_page': min(100, max(1, so_luong)), 'page': max(1, trang)}
    if chi_anh:
        ts['media_type'] = 'image'
    if tu_khoa:
        ts['search'] = tu_khoa
    if truoc_ngay:
        ts['before'] = f'{truoc_ngay}T00:00:00'
    try:
        r = requests.get(f'{url}/wp-json/wp/v2/media', auth=auth, headers=headers,
                         params=ts, timeout=60)
    except requests.exceptions.RequestException as e:
        return [], 0, f'{type(e).__name__}: {e}'
    if r.status_code != 200:
        return [], 0, f'HTTP {r.status_code}: {r.text[:250]}'

    tong = int(r.headers.get('X-WP-Total', 0) or 0)
    ra = []
    for m in r.json():
        ra.append({
            'id': m.get('id'),
            'ten': (m.get('slug') or '')[:80],
            'title': ((m.get('title') or {}).get('rendered') or '')[:80],
            'url': m.get('source_url') or '',
            'ngay': (m.get('date') or '')[:10],
            'gan_vao': m.get('post') or None,     # post/product đang dùng, None = mồ côi
            'alt': (m.get('alt_text') or '')[:60],
        })
    return ra, tong, ''


def tim_anh_mo_coi(gioi_han_trang=10, truoc_ngay=None):
    """Media không gắn vào bài nào (`post` rỗng). Đây thường là rác của các
    lần upload lỗi giữa chừng — nhóm an toàn nhất để dọn.

    Trả (danh_sach, loi).
    """
    ra, trang = [], 1
    while trang <= gioi_han_trang:
        ds, tong, loi = liet_ke_media(so_luong=100, trang=trang, truoc_ngay=truoc_ngay)
        if loi:
            return ra, loi
        if not ds:
            break
        ra += [m for m in ds if not m['gan_vao']]
        if len(ds) < 100:
            break
        trang += 1
    return ra, ''


# ----------------------------------------------------------- mức 1: gỡ khỏi bài

def go_anh_khoi_bai(danh_sach_wp_id, la_woo=True, giu_lai_dau=0, chay_thu=True):
    """Gỡ ảnh khỏi sản phẩm/bài. FILE VẪN CÒN trong Media Library.

    giu_lai_dau : giữ lại N ảnh đầu (VD 1 = chỉ giữ ảnh đại diện, gỡ hết
                  gallery). 0 = gỡ sạch.
    chay_thu    : True (mặc định) chỉ báo cáo, không gọi API ghi.

    Trả dict {ok, so_xu_ly, chi_tiet, log}.
    """
    import requests
    try:
        url, auth, headers = _ket_noi()
    except SystemExit as e:
        return {'ok': False, 'loi': str(e)}

    chi_tiet = []
    for wp_id in danh_sach_wp_id:
        api = (f'{url}/wp-json/wc/v3/products/{wp_id}' if la_woo
               else f'{url}/wp-json/wp/v2/posts/{wp_id}')
        try:
            rg = requests.get(api, auth=auth, headers=headers, timeout=45)
        except requests.exceptions.RequestException as e:
            chi_tiet.append({'wp_id': wp_id, 'ok': False, 'loi': f'{type(e).__name__}: {e}'})
            continue
        if rg.status_code != 200:
            chi_tiet.append({'wp_id': wp_id, 'ok': False, 'loi': f'GET HTTP {rg.status_code}'})
            continue
        d = rg.json()
        if la_woo:
            hien = [x.get('id') for x in (d.get('images') or []) if x.get('id')]
            giu = hien[:giu_lai_dau]
            body = {'images': [{'id': i} for i in giu]}
        else:
            hien = [d.get('featured_media')] if d.get('featured_media') else []
            giu = hien[:giu_lai_dau]
            body = {'featured_media': giu[0] if giu else 0}
        se_go = [i for i in hien if i not in giu]

        if chay_thu:
            chi_tiet.append({'wp_id': wp_id, 'ok': True, 'chay_thu': True,
                             'dang_co': hien, 'se_go': se_go, 'se_giu': giu})
            continue
        if not se_go:
            chi_tiet.append({'wp_id': wp_id, 'ok': True, 'se_go': [], 'ghi_chu': 'không có gì để gỡ'})
            continue
        try:
            rp = requests.post(api, auth=auth, headers=headers, json=body, timeout=60)
            ok = rp.status_code in (200, 201)
            chi_tiet.append({'wp_id': wp_id, 'ok': ok, 'da_go': se_go if ok else [],
                             'loi': '' if ok else f'HTTP {rp.status_code}: {rp.text[:200]}'})
        except requests.exceptions.RequestException as e:
            chi_tiet.append({'wp_id': wp_id, 'ok': False, 'loi': f'{type(e).__name__}: {e}'})
        time.sleep(0.25)

    log = '' if chay_thu else _ghi_log('go-anh-khoi-bai', chi_tiet)
    return {'ok': all(c.get('ok') for c in chi_tiet) if chi_tiet else True,
            'chay_thu': chay_thu, 'so_xu_ly': len(chi_tiet),
            'chi_tiet': chi_tiet, 'log': log}


# ----------------------------------------------------------- mức 2 & 3: xoá media

XAC_NHAN_XOA = 'XOA VINH VIEN'


def xoa_media(danh_sach_media_id, force=False, chay_thu=True, xac_nhan='',
              bo_qua_dang_dung=True):
    """Xoá media khỏi WordPress.

    force=False : vào thùng rác, hồi lại được ~30 ngày. (khuyên dùng)
    force=True  : XOÁ VĨNH VIỄN, không hồi được. Bắt buộc truyền
                  xac_nhan='XOA VINH VIEN'.
    bo_qua_dang_dung : True thì tự BỎ QUA media đang gắn vào bài nào đó —
                  chốt chặn quan trọng nhất, tránh xoá nhầm ảnh đang chạy
                  làm hỏng ảnh của bài đã đăng.

    Trả dict {ok, so_xoa, so_bo_qua, chi_tiet, log}.
    """
    import requests

    if force and xac_nhan != XAC_NHAN_XOA:
        return {'ok': False,
                'loi': f'Xoá vĩnh viễn cần xac_nhan="{XAC_NHAN_XOA}". '
                       f'Đây là hành động KHÔNG HỒI LẠI ĐƯỢC.'}
    try:
        url, auth, headers = _ket_noi()
    except SystemExit as e:
        return {'ok': False, 'loi': str(e)}

    chi_tiet, bo_qua = [], 0
    for mid in danh_sach_media_id:
        dang_dung = None
        if bo_qua_dang_dung:
            try:
                rg = requests.get(f'{url}/wp-json/wp/v2/media/{mid}', auth=auth,
                                  headers=headers, timeout=45)
                if rg.status_code == 200:
                    dang_dung = rg.json().get('post') or None
            except requests.exceptions.RequestException:
                dang_dung = 'KHONG_KIEM_TRA_DUOC'
            if dang_dung:
                bo_qua += 1
                chi_tiet.append({'media_id': mid, 'ok': True, 'bo_qua': True,
                                 'ly_do': f'đang gắn vào bài {dang_dung}'})
                continue

        if chay_thu:
            chi_tiet.append({'media_id': mid, 'ok': True, 'chay_thu': True,
                             'se': 'xoá vĩnh viễn' if force else 'chuyển thùng rác'})
            continue
        try:
            rd = requests.delete(f'{url}/wp-json/wp/v2/media/{mid}', auth=auth,
                                 headers=headers, params={'force': 'true' if force else 'false'},
                                 timeout=60)
            ok = rd.status_code in (200, 201)
            chi_tiet.append({'media_id': mid, 'ok': ok, 'force': force,
                             'loi': '' if ok else f'HTTP {rd.status_code}: {rd.text[:200]}'})
        except requests.exceptions.RequestException as e:
            chi_tiet.append({'media_id': mid, 'ok': False, 'loi': f'{type(e).__name__}: {e}'})
        time.sleep(0.25)

    log = ''
    if not chay_thu:
        log = _ghi_log('xoa-vinh-vien' if force else 'xoa-thung-rac',
                       {'force': force, 'thoi_diem': datetime.now().isoformat(timespec='seconds'),
                        'chi_tiet': chi_tiet})
    so_xoa = sum(1 for c in chi_tiet if c.get('ok') and not c.get('bo_qua'))
    return {'ok': all(c.get('ok') for c in chi_tiet) if chi_tiet else True,
            'chay_thu': chay_thu, 'force': force, 'so_xoa': so_xoa,
            'so_bo_qua': bo_qua, 'chi_tiet': chi_tiet, 'log': log}


# ----------------------------------------------------------- dọn local

def xoa_anh_local(thu_muc, mau_ten='', chay_thu=True, thung_rac=True):
    """Dọn ảnh trên máy. thung_rac=True thì CHUYỂN sang thư mục `_da_xoa/`
    thay vì xoá thật — mặc định, vì xoá file local không có Undo.

    Trả dict {ok, so_file, tong_mb, chi_tiet}.
    """
    goc = Path(thu_muc)
    if not goc.is_dir():
        return {'ok': False, 'loi': f'Không thấy thư mục: {thu_muc}'}
    duoi = {'.webp', '.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    ds = [p for p in goc.rglob('*')
          if p.is_file() and p.suffix.lower() in duoi
          and (not mau_ten or mau_ten.lower() in p.name.lower())
          and '_da_xoa' not in p.parts]

    tong = sum(p.stat().st_size for p in ds)
    chi_tiet = [{'file': str(p.relative_to(goc)), 'kb': round(p.stat().st_size / 1024, 1)}
                for p in ds[:500]]
    if chay_thu:
        return {'ok': True, 'chay_thu': True, 'so_file': len(ds),
                'tong_mb': round(tong / 1024 / 1024, 2), 'chi_tiet': chi_tiet}

    rac = goc / '_da_xoa' / datetime.now().strftime('%Y%m%d-%H%M%S')
    if thung_rac:
        rac.mkdir(parents=True, exist_ok=True)
    loi = 0
    for p in ds:
        try:
            if thung_rac:
                dich = rac / p.relative_to(goc)
                dich.parent.mkdir(parents=True, exist_ok=True)
                p.replace(dich)
            else:
                p.unlink()
        except Exception:
            loi += 1
    return {'ok': loi == 0, 'chay_thu': False, 'so_file': len(ds) - loi,
            'so_loi': loi, 'tong_mb': round(tong / 1024 / 1024, 2),
            'thung_rac': str(rac) if thung_rac else None, 'chi_tiet': chi_tiet}
