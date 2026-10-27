# -*- coding: utf-8 -*-
"""
Danh tính từng site + cấu hình bảng. Sửa file này khi thêm tên miền mới.
KHÔNG chứa API key, không chứa mật khẩu. Mấy thứ đó nằm trong cau-hinh.env.
"""
import os
import re
from pathlib import Path

BASE = Path(__file__).parent

# ---------------------------------------------------------------- các site
# Thêm site mới: chép nguyên 1 khối, đổi khoá và nội dung.
# Khoá 'site2' phải khớp với biến môi trường WP_SITE2_URL / _USER / _APP_PW.
SITES = {
    'site1': {
        'ten': 'Biến Áp THIBIDI',
        'hotline': '0358506151',
        'zalo': '0358506151',
        'dia_chi': 'TP. Hồ Chí Minh',
        'khu_vuc': 'TP.HCM, Bình Dương, Đồng Nai, Long An, Bà Rịa Vũng Tàu '
                   'và các tỉnh phía Nam',
        'cam_ket': 'Báo giá trong 15 phút giờ hành chính. Hàng chính hãng, có sẵn kho, '
                   'giao đúng tiến độ công trình.',
        'hang_duoc_nhac': ['THIBIDI'],       # AI chỉ được nhắc tên hãng trong danh sách này
        'mau_mac_dinh': 'bao_gia',
        'tu_cam_them': [],                   # từ cấm riêng của site này
        'danh_muc': [],                      # ngành hàng site này bán, [] = tất cả
    },
    'site2': {
        'ten': 'Tủ Trung Thế RMU',
        'hotline': '0358506151',
        'zalo': '0358506151',
        'dia_chi': 'TP. Hồ Chí Minh',
        'khu_vuc': 'TP.HCM và các tỉnh phía Nam',
        'cam_ket': 'Báo giá kèm cấu hình ngăn trong ngày. Có sẵn hàng, hỗ trợ kỹ thuật '
                   'chọn cấu hình theo sơ đồ một sợi.',
        'hang_duoc_nhac': ['Schneider', 'ABB', 'Siemens', 'Ormazabal', 'Lucy', 'TaeYoung'],
        'mau_mac_dinh': 'bao_gia',
        'tu_cam_them': [],
        'danh_muc': [],
    },
}

# ---------------------------------------------------------------- chặn rò rỉ danh tính
# Bài chứa 1 trong các chuỗi này thì BỊ CHẶN, không đăng. Áp dụng cho MỌI site.
# Đây là hàng rào duy nhất ngăn hệ vệ tinh bị nối về công ty mẹ.
TU_CAM_CHUNG = [
    'lotech', '0938416566', '0317337852', 'bình tân', 'binh tan', 'vihan',
    'cadivi-vn.vn', 'tutrungthe.vn', 'muabandien.vn', 'capls.vn',
    'lqs.com.vn', 'daucap.vn', 'shihlin.com.vn', 'lotech.com.vn',
]


def lay_site(ma_site):
    ds = tat_ca_site()
    if ma_site not in ds:
        raise SystemExit(f'Không có site "{ma_site}". Đang có: {", ".join(ds)}. '
                         f'Thêm site mới ở tab Cấu hình trong phần mềm, hoặc sửa cauhinh.py.')
    return ds[ma_site]


def tu_cam(ma_site):
    """Từ cấm chung + riêng, nhưng bỏ đi số hotline của chính site đó."""
    s = lay_site(ma_site)
    ds = [t.lower() for t in TU_CAM_CHUNG + list(s.get('tu_cam_them', []))]
    cua_minh = {str(s.get('hotline', '')).lower(), str(s.get('zalo', '')).lower()}
    return sorted({t for t in ds if t and t not in cua_minh})


# ---------------------------------------------------------------- site thêm qua giao diện
# SITES ở trên là site mẫu/demo, sửa trong code. Site thêm bằng tay ở tab Cấu hình
# lưu riêng ra file này, KHÔNG đụng vào SITES, để cập nhật phần mềm không đè mất.
_FILE_SITE_THEM = None


def _duong_dan_site_them():
    global _FILE_SITE_THEM
    if _FILE_SITE_THEM is None:
        from pathlib import Path
        _FILE_SITE_THEM = Path(__file__).parent / 'sites-them.json'
    return _FILE_SITE_THEM


def _doc_site_them():
    import json
    p = _duong_dan_site_them()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {}


def tat_ca_site():
    """SITES mẫu trong code + site thêm bằng tay qua giao diện, gộp lại."""
    return {**SITES, **_doc_site_them()}


def them_site(ma_site, ten, hotline, zalo=None, dia_chi='', khu_vuc='', cam_ket='',
             hang_duoc_nhac=None, mau_mac_dinh='bao_gia', danh_muc=None):
    """Thêm hoặc sửa 1 site qua giao diện, không phải sửa file .py."""
    import json
    ma_site = ma_site.strip()
    if not ma_site or not ten.strip():
        raise ValueError('Cần điền mã site và tên hiển thị.')
    if ma_site in SITES:
        raise ValueError(f'"{ma_site}" là site mẫu có sẵn trong cauhinh.py, đặt mã khác.')
    ds = _doc_site_them()
    ds[ma_site] = {
        'ten': ten.strip(), 'hotline': hotline.strip(), 'zalo': (zalo or hotline).strip(),
        'dia_chi': dia_chi.strip(), 'khu_vuc': khu_vuc.strip(), 'cam_ket': cam_ket.strip(),
        'hang_duoc_nhac': hang_duoc_nhac or [], 'mau_mac_dinh': mau_mac_dinh,
        'tu_cam_them': [], 'danh_muc': danh_muc or [],
    }
    _duong_dan_site_them().write_text(json.dumps(ds, ensure_ascii=False, indent=2),
                                      encoding='utf-8')
    return ds[ma_site]


def xoa_site_them(ma_site):
    import json
    ds = _doc_site_them()
    if ma_site in ds:
        del ds[ma_site]
        _duong_dan_site_them().write_text(json.dumps(ds, ensure_ascii=False, indent=2),
                                          encoding='utf-8')
        return True
    return False


# ---------------------------------------------------------------- bảng thông số
# (tên cột trong products.csv, nhãn hiện ra trên web)
COT_BANG = [
    ('ma_goc', 'Mã sản phẩm'),
    ('hang', 'Hãng sản xuất'),
    ('series', 'Dòng sản phẩm'),
    ('so_ngan', 'Số ngăn'),
    ('loai_ngan', 'Loại ngăn'),
    ('cap_dien_ap', 'Cấp điện áp'),
    ('dong_dinh_muc', 'Dòng định mức'),
    ('dong_ngan_mach', 'Dòng ngắn mạch'),
    ('ro_le', 'Rơ le bảo vệ'),
    ('cach_dien', 'Môi trường cách điện'),
    ('mo_rong', 'Khả năng mở rộng'),
    ('kich_thuoc', 'Kích thước (DxRxC)'),
    ('trong_luong', 'Trọng lượng'),
    ('tieu_chuan', 'Tiêu chuẩn áp dụng'),
    ('xuat_xu', 'Xuất xứ'),
    ('bao_hanh', 'Bảo hành'),
    ('tinh_trang_kho', 'Tình trạng kho'),
    ('gia_tham_khao', 'Giá tham khảo'),
]

# cột đưa vào bảng giá (bảng liệt kê nhiều cấu hình cùng dòng)
COT_GIA = [
    ('ma_goc', 'Mã'),
    ('so_ngan', 'Số ngăn'),
    ('cap_dien_ap', 'Cấp điện áp'),
    ('ro_le', 'Rơ le'),
    ('gia_tham_khao', 'Đơn giá tham khảo'),
]

# cột dùng để gom sản phẩm vào chung 1 bảng giá, xếp theo thứ tự ưu tiên
COT_GOM_BANG_GIA = ('series', 'cap_dien_ap')

# cột quyết định bài dày hay mỏng. Dashboard chấm "Dữ liệu x/10" theo danh sách này.
COT_QUAN_TRONG = ['cap_dien_ap', 'dong_dinh_muc', 'so_ngan', 'loai_ngan', 'ro_le',
                  'gia_tham_khao', 'tieu_chuan', 'kich_thuoc', 'bao_hanh', 'anh_1_url']


def cham_du_lieu(row):
    """Đếm số cột quan trọng đã điền. Trả (số đã điền, tổng)."""
    return sum(1 for c in COT_QUAN_TRONG if (row.get(c) or '').strip()), len(COT_QUAN_TRONG)


# ============================================================ Ver 3 — ghi lại cau-hinh.env
# Gate "Website Configuration + Save Draft thật". Tái sử dụng ĐÚNG format
# cau-hinh.env đã có (autopost.nap_env() đọc file này lúc khởi động) — chỉ
# thêm hàm GHI, chưa ai viết hàm ghi trước đây (trước giờ người dùng tự sửa
# tay file .env). Giữ nguyên comment/thứ tự dòng, chỉ thay giá trị sau "=".

# Ver 4.4.1.6 — ghi cấu hình vào thư mục chung, không vào thư mục version.
try:
    import thu_muc_du_lieu as _TM
    ENV_PATH = _TM.duong_dan_env()
except Exception:
    ENV_PATH = BASE / 'cau-hinh.env'

# Ver 3 chỉ quản lý 1 website — cố định khoá 'website' (không phải site1/
# site2), khớp đúng namespace autopost.thong_tin_wp()/_auth() đang đọc:
# WP_{MA_SITE.upper()}_* -> WP_WEBSITE_URL / WP_WEBSITE_USER / WP_WEBSITE_APP_PW
MA_SITE_VER3 = 'website'


def _doc_dong_env():
    if not ENV_PATH.exists():
        mau = BASE / 'cau-hinh.env.MAU'
        return mau.read_text(encoding='utf-8-sig').splitlines() if mau.exists() else []
    return ENV_PATH.read_text(encoding='utf-8-sig').splitlines()


def ghi_env(**kv):
    """Cập nhật/thêm mới các khoá trong cau-hinh.env, GIỮ NGUYÊN mọi dòng
    khác (comment, khoá khác) — không ghi đè cả file. Cập nhật luôn
    os.environ để áp dụng ngay, không cần khởi động lại app.

    KHÔNG bao giờ gọi hàm này với giá trị cần giấu (Application Password)
    theo cách sẽ bị log lại — nơi gọi tự chịu trách nhiệm không print(kv).
    """
    dong = _doc_dong_env()
    con_thieu = dict(kv)
    ra = []
    for d in dong:
        s = d.strip()
        if s and not s.startswith('#') and '=' in s:
            k = s.split('=', 1)[0].strip()
            if k in con_thieu:
                ra.append(f'{k}={con_thieu.pop(k)}')
                continue
        ra.append(d)
    for k, v in con_thieu.items():
        ra.append(f'{k}={v}')
    ENV_PATH.write_text('\n'.join(ra) + '\n', encoding='utf-8')
    for k, v in kv.items():
        os.environ[k] = v


def chuan_hoa_url(url):
    """URL chuẩn hoá dùng làm KHOÁ định danh website — bỏ scheme (http/https
    coi như cùng 1 site), bỏ 'www.', hạ thường, bỏ dấu '/' cuối. Đây là điểm
    mấu chốt của Task idempotency: đổi TÊN hiển thị không đổi khoá (khoá lấy
    từ URL, không lấy từ tên), đổi DOMAIN thì khoá đổi -> coi là website
    khác — đúng yêu cầu, không cần code riêng cho 2 case đó, tự nhiên đúng
    nhờ định nghĩa khoá theo URL.
    """
    if not url:
        return ''
    u = url.strip().lower()
    u = re.sub(r'^https?://', '', u)
    u = re.sub(r'^www\.', '', u)
    u = u.rstrip('/')
    return u


def site_key():
    """Khoá định danh website Ver 3 hiện tại (URL đã chuẩn hoá) — dùng làm
    giá trị cột `site` trong db_phase2.bai_viet_phase2 (KHÔNG dùng tên hiển
    thị nữa, xem chuan_hoa_url). Trả '' nếu chưa cấu hình."""
    url = os.environ.get('WP_WEBSITE_URL', '').strip()
    return chuan_hoa_url(url) if url else ''


def doc_website():
    """Đọc cấu hình website Ver 3 hiện tại (đã nạp vào os.environ lúc khởi
    động qua autopost.nap_env()). Trả None nếu chưa cấu hình gì.

    'site_key' = khoá định danh THẬT (URL chuẩn hoá) — dùng cho DB/idempotency.
    'ten'      = CHỈ để hiển thị, không được dùng làm khoá ở bất kỳ đâu.

    Ver 4.6 — 'che_do_dang': 'post' (mặc định, /wp/v2/posts như trước giờ)
    hoặc 'woo_product' (/wc/v3/products — site chạy Flatsome+WooCommerce).
    Theo site, không phải cấu hình toàn cục — Lotech có nhiều site, chỉ site
    nào thật sự chạy WooCommerce mới cần đổi."""
    url = os.environ.get('WP_WEBSITE_URL', '').strip()
    if not url:
        return None
    return {
        'ten': os.environ.get('WP_WEBSITE_TEN', '').strip(),
        'url': url,
        'site_key': chuan_hoa_url(url),
        'user': os.environ.get('WP_WEBSITE_USER', '').strip(),
        'app_pw': os.environ.get('WP_WEBSITE_APP_PW', ''),   # KHÔNG strip — Application Password có thể có khoảng trắng giữa các cụm, đúng định dạng Google/WordPress sinh ra
        'che_do_dang': os.environ.get('WP_WEBSITE_CHE_DO', 'post').strip() or 'post',
        'hotline': (os.environ.get('WP_WEBSITE_HOTLINE', '') or os.environ.get('WATERMARK_PHONE', '')).strip(),
    }


def luu_website(ten, url, user, app_pw, che_do_dang='post', hotline=''):
    u = url.strip().rstrip('/')
    # Ver 4.2 audit debt: Application Password chỉ được lưu cho HTTPS;
    # localhost/dev được phép HTTP để test cục bộ.
    low = u.lower()
    if low.startswith('http://') and not re.match(r'^http://(?:localhost|127\.0\.0\.1)(?::\d+)?(?:/|$)', low):
        raise ValueError('Website production phải dùng https:// để bảo vệ WordPress Application Password.')
    if u and not re.match(r'^https?://', low):
        raise ValueError('Địa chỉ website phải bắt đầu bằng https:// (hoặc http://localhost khi test).')
    ghi_env(WP_WEBSITE_TEN=ten.strip(), WP_WEBSITE_URL=u,
            WP_WEBSITE_USER=user.strip(), WP_WEBSITE_APP_PW=app_pw,
            WP_WEBSITE_CHE_DO=che_do_dang if che_do_dang in ('post', 'woo_product') else 'post',
            WP_WEBSITE_HOTLINE=str(hotline or '').strip())


def xoa_website():
    ghi_env(WP_WEBSITE_TEN='', WP_WEBSITE_URL='', WP_WEBSITE_USER='', WP_WEBSITE_APP_PW='',
            WP_WEBSITE_CHE_DO='', WP_WEBSITE_HOTLINE='')


def luu_gemini(api_key, model):
    """NHA_CUNG_CAP cố định 'gemini' cho Ver 3 (Task 2: không cho tự nhập
    Nhà cung cấp) — vẫn ghi khoá này để nhánh RMU cũ (autopost.py đọc
    NHA_CUNG_CAP) không bị vỡ nếu 2 nhánh dùng chung 1 file cau-hinh.env."""
    kv = {'NHA_CUNG_CAP': 'gemini'}
    if api_key:
        kv['GOOGLE_API_KEY'] = api_key
    if model:
        kv['MODEL_GEMINI'] = model
    ghi_env(**kv)


# Ver 5.6 — MODEL ĐÃ CHẾT: tên model KHÔNG tồn tại phía Google, mọi lần gọi
# trả HTTP 404 ngay lập tức. Vẫn nằm trong cau-hinh.env của máy Thịnh nên
# _v3_danh_sach_key_model_du_phong() vẫn ghép nó vào ma trận key×model và
# thử lại cho TỪNG SKU. Không sửa được bằng cách sửa file .env kèm bản
# đóng gói (cau-hinh.env cố ý KHÔNG nằm trong ZIP — là state của máy), nên
# lọc ở chỗ ĐỌC: mọi caller (giao-dien, seo_post_core, vision_chung) đều đi
# qua doc_gemini(), lọc 1 chỗ là sạch cả hệ.
#
# Chỉ liệt kê model đã XÁC NHẬN 404 bằng log thật. Không đoán, không lọc
# theo pattern tên — model mới ra mà bị lọc nhầm thì hỏng nặng hơn.
MODEL_CHET = {'gemini-5.0-flash'}


def _bo_model_chet(danh_sach):
    return [m for m in danh_sach if m.strip().lower() not in MODEL_CHET]


def doc_gemini():
    model_chinh = os.environ.get('MODEL_GEMINI', '')
    du_phong = _bo_model_chet(_tach_danh_sach(os.environ.get('MODEL_GEMINI_DU_PHONG', '')))
    if model_chinh.strip().lower() in MODEL_CHET:
        # Model CHÍNH mà chết thì không thể trả rỗng (caller kiểm
        # `if not gc['model']` rồi báo "chưa cấu hình AI" và dừng batch).
        # Đôn model dự phòng đầu tiên lên làm chính; hết sạch thì mới để rỗng.
        model_chinh = du_phong.pop(0) if du_phong else ''
    return {'api_key': os.environ.get('GOOGLE_API_KEY', ''),
            'model': model_chinh,
            'api_key_du_phong': _tach_danh_sach(os.environ.get('GOOGLE_API_KEY_DU_PHONG', '')),
            'model_du_phong': du_phong}


def _tach_danh_sach(chuoi):
    """Tách chuỗi nhiều dòng/nhiều phẩy thành list, bỏ dòng trống, bỏ khoảng trắng thừa."""
    if not chuoi:
        return []
    thanh_phan = chuoi.replace(',', '\n').split('\n')
    return [x.strip() for x in thanh_phan if x.strip()]


def luu_gemini_du_phong(danh_sach_key, danh_sach_model):
    """Ver 4.7 — API key dự phòng: dùng khi key chính hết quota trong ngày.
    Model dự phòng: dùng khi model chính bị cắt token/sinh nội dung rác
    (Hard Block chặn độ dài bất thường) — 2 nguyên nhân khác nhau, 2 danh
    sách riêng, không gộp chung. `danh_sach_key`/`danh_sach_model`: list
    chuỗi, đã tách sẵn (UI tách trước khi gọi).

    LƯU Ý: ghi_env() lưu mỗi khoá 1 DÒNG DUY NHẤT — nối bằng dấu phẩy,
    KHÔNG được nối bằng '\\n' (sẽ phá định dạng file .env, đọc lại sai)."""
    ghi_env(GOOGLE_API_KEY_DU_PHONG=','.join(danh_sach_key),
            MODEL_GEMINI_DU_PHONG=','.join(danh_sach_model))


def luu_serper(api_key):
    """SONEALEO Ver 1.1 — tab Enhance: Serper.dev API key. Ver 5.4 đổi từ
    Google Custom Search (bị Google đóng cho project mới, 403 vĩnh viễn)
    sang Serper — chỉ cần 1 key, không có cx."""
    ghi_env(SERPER_API_KEY=api_key or '')


def doc_serper():
    return {'api_key': os.environ.get('SERPER_API_KEY', '')}


def luu_css_class_mode(bat):
    """Ver 2.1 — bật/tắt chế độ CSS class (thay cho inline style). Lưu vào
    cau-hinh.env để render_phase2._dung_class_css() đọc được."""
    ghi_env(CSS_CLASS_MODE='1' if bat else '0')


def doc_css_class_mode():
    return str(os.environ.get('CSS_CLASS_MODE', '0')).strip().lower() in ('1', 'true', 'yes', 'on')


def luu_hien_thi_bai(bo_cta_cuoi, bo_anh_placeholder):
    """Ver 2.2 — 2 công tắc hiển thị: bỏ khối CTA cuối (theme đã có CTA
    riêng) và bỏ ô placeholder ảnh (trông như lỗi với khách)."""
    ghi_env(BO_CTA_CUOI='1' if bo_cta_cuoi else '0',
            BO_ANH_PLACEHOLDER='1' if bo_anh_placeholder else '0')


def doc_hien_thi_bai():
    _bat = lambda k: str(os.environ.get(k, '0')).strip().lower() in ('1', 'true', 'yes', 'on')
    return {'bo_cta_cuoi': _bat('BO_CTA_CUOI'),
            'bo_anh_placeholder': _bat('BO_ANH_PLACEHOLDER')}


def luu_giao_dien_2_5(bat):
    """Ver 2.5 — bật/tắt bố cục cao cấp (hero 2 cột, chip, mục lục neo,
    FAQ gập, CTA). Cần dán CSS mới lên site trước khi bật."""
    ghi_env(GIAO_DIEN_2_5='1' if bat else '0')


def doc_giao_dien_2_5():
    return str(os.environ.get('GIAO_DIEN_2_5', '0')).strip().lower() in ('1', 'true', 'yes', 'on')
