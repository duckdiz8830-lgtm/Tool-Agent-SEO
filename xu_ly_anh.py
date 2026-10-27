# -*- coding: utf-8 -*-
"""XỬ LÝ ẢNH — Ver 3.7, đợt 1.

Nhận ảnh người dùng đã gán ô, làm nốt phần cơ khí:
  WebP -> đổi tên theo slug -> alt sinh từ dữ liệu -> upload WP Media ->
  chèn vào NỘI DUNG BÀI -> đặt ảnh đại diện -> ghi lại meta.json.

Đây đúng là phần tốn thời gian mà người làm SEO không nên phải làm tay.
Việc chọn ảnh vẫn là của mắt người.

KHÔNG GỌI AI. Toàn bộ file này chạy được khi mất mạng AI hoàn toàn.
"""

import io
import re
import html
import hashlib
import json
import os
import shutil
from pathlib import Path

import workspace_anh as WS

# Ver 4.4 D2 — HEIC/AVIF trên Windows qua pillow-heif.
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except Exception:
    pass

RONG_TOI_DA = 1200
KB_TOI_DA = 150
CHAT_LUONG_DAU = 82
CHAT_LUONG_MIN = 55


# ---------------------------------------------------------------- lọc kho ảnh tầng 1 (không AI)
NGUONG_MO_LAPLACIAN = 80.0
CANH_NGAN_TOI_THIEU = 800


def _nguong_canh_ngan():
    """Ver 5.7 — ngưỡng cạnh ngắn (px) cho cổng ảnh trên đường upload.

    Mặc định CANH_NGAN_TOI_THIEU (800). Cho phép đè bằng biến môi trường
    ANH_CANH_NGAN_TOI_THIEU vì hai lý do THẬT:

      1. Ngưỡng 800 là con số CHỌN, không phải hằng số vật lý. Kho ảnh mỗi
         hãng một khác; cần chỉnh thì chỉnh ở cấu hình, không phải sửa code
         rồi đóng gói lại.
      2. Đặt 0 = TẮT cổng. Cần khi chạy test cơ chế upload/watermark với
         ảnh fixture nhỏ, và khi phải đăng gấp một lô ảnh biết trước là
         dưới chuẩn (chấp nhận đánh đổi, có ý thức).

    Giá trị sai/âm -> quay về mặc định. 0 -> tắt hẳn.
    """
    import os as _os
    raw = _os.environ.get('ANH_CANH_NGAN_TOI_THIEU')
    if raw is None or str(raw).strip() == '':
        return CANH_NGAN_TOI_THIEU
    try:
        v = int(str(raw).strip())
    except (TypeError, ValueError):
        return CANH_NGAN_TOI_THIEU
    return v if v >= 0 else CANH_NGAN_TOI_THIEU


def _sha256_day_du(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def laplacian_variance(duong_dan, canh_phan_tich=320):
    """Variance của Laplacian rời rạc trên ảnh xám thu nhỏ tối đa 320px.

    Dùng Pillow + Python thuần để không thêm dependency OpenCV/Numpy vào bộ
    cài. Thu nhỏ chỉ phục vụ đo độ nét, không sửa file gốc.
    """
    from PIL import Image, ImageOps
    with Image.open(duong_dan) as src:
        im = ImageOps.exif_transpose(src).convert('L')
        im.thumbnail((canh_phan_tich, canh_phan_tich), Image.LANCZOS)
        w, h = im.size
        if w < 3 or h < 3:
            return 0.0
        px = im.load()
        n = 0
        tong = 0.0
        tong_binh = 0.0
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                v = (4 * px[x, y] - px[x - 1, y] - px[x + 1, y]
                     - px[x, y - 1] - px[x, y + 1])
                n += 1
                tong += v
                tong_binh += v * v
        mean = tong / n
        return max(0.0, tong_binh / n - mean * mean)


def loc_kho_anh(thu_muc_nguon, thu_muc_ra=None,
                 canh_ngan_toi_thieu=CANH_NGAN_TOI_THIEU,
                 nguong_mo=NGUONG_MO_LAPLACIAN):
    """Lọc tầng 1, KHÔNG XOÁ file gốc, KHÔNG gọi AI.

    Thứ tự loại: file không phải ảnh -> trùng byte -> cạnh ngắn < ngưỡng ->
    Laplacian variance < ngưỡng mờ. Ảnh đạt được hardlink sang `_DA_LOC`
    nếu cùng filesystem, nếu hardlink không được thì copy2. Giữ cấu trúc
    thư mục con để tránh đụng tên file.
    """
    from PIL import Image, ImageOps
    src = Path(thu_muc_nguon).resolve()
    if not src.is_dir():
        raise NotADirectoryError(str(src))
    out = Path(thu_muc_ra).resolve() if thu_muc_ra else src / '_DA_LOC'
    out.mkdir(parents=True, exist_ok=True)

    bao = {
        'nguon': str(src), 'dich': str(out),
        'canh_ngan_toi_thieu_px': int(canh_ngan_toi_thieu),
        'nguong_mo_laplacian_variance': float(nguong_mo),
        'tong_file': 0, 'anh_hop_le_dau_vao': 0, 'giu_lai': 0,
        'loai': {'khong_phai_anh': 0, 'trung_byte': 0, 'anh_nho': 0, 'anh_mo': 0},
        'chi_tiet': [],
    }
    seen = {}
    files = []
    for root, dirs, names in os.walk(src):
        root_p = Path(root)
        # Không tự quét output của chính mình khi rerun.
        dirs[:] = [d for d in dirs if (root_p / d).resolve() != out]
        for name in names:
            p = root_p / name
            # report cũ trong source cũng là file rác theo nghĩa ảnh, nhưng bỏ
            # riêng report của tool để rerun không làm số input tăng giả.
            if p.resolve().is_relative_to(out):
                continue
            files.append(p)
    bao['tong_file'] = len(files)

    for p in files:
        rel = p.relative_to(src)
        rec = {'file': str(rel)}
        try:
            with Image.open(p) as im0:
                im = ImageOps.exif_transpose(im0)
                w, h = im.size
                # verify() không dùng ở đây vì cần đọc tiếp; load 1 điểm đủ bắt
                # phần lớn file giả extension/corrupt trước khi hash nặng hơn.
                im.getpixel((0, 0))
        except Exception as e:
            bao['loai']['khong_phai_anh'] += 1
            rec.update({'ket_qua': 'loai', 'ly_do': 'khong_phai_anh', 'loi': type(e).__name__})
            bao['chi_tiet'].append(rec)
            continue

        bao['anh_hop_le_dau_vao'] += 1
        hsh = _sha256_day_du(p)
        if hsh in seen:
            bao['loai']['trung_byte'] += 1
            rec.update({'ket_qua': 'loai', 'ly_do': 'trung_byte', 'trung_voi': seen[hsh], 'sha256': hsh})
            bao['chi_tiet'].append(rec)
            continue
        seen[hsh] = str(rel)

        if min(w, h) < int(canh_ngan_toi_thieu):
            bao['loai']['anh_nho'] += 1
            rec.update({'ket_qua': 'loai', 'ly_do': 'anh_nho', 'kich_thuoc': [w, h], 'sha256': hsh})
            bao['chi_tiet'].append(rec)
            continue

        lv = laplacian_variance(p)
        if lv < float(nguong_mo):
            bao['loai']['anh_mo'] += 1
            rec.update({'ket_qua': 'loai', 'ly_do': 'anh_mo', 'kich_thuoc': [w, h],
                        'laplacian_variance': round(lv, 3), 'sha256': hsh})
            bao['chi_tiet'].append(rec)
            continue

        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and _sha256_day_du(dest) != hsh:
            dest = dest.with_name(f'{dest.stem}_{hsh[:10]}{dest.suffix}')
        cach = 'da_co'
        if not dest.exists():
            try:
                os.link(p, dest)
                cach = 'hardlink'
            except OSError:
                shutil.copy2(p, dest)
                cach = 'copy'
        bao['giu_lai'] += 1
        rec.update({'ket_qua': 'giu', 'kich_thuoc': [w, h],
                    'laplacian_variance': round(lv, 3), 'sha256': hsh,
                    'dich': str(dest.relative_to(out)), 'cach': cach})
        bao['chi_tiet'].append(rec)

    report = out / 'bao-cao-loc-anh.json'
    report.write_text(json.dumps(bao, ensure_ascii=False, indent=2), encoding='utf-8')
    bao['bao_cao'] = str(report)
    return bao


# ---------------------------------------------------------------- WebP
def sang_webp(duong_dan, rong_toi_da=RONG_TOI_DA, kb_toi_da=KB_TOI_DA):
    """Resize + WebP tới khi đạt ngưỡng KB; nếu quality chạm đáy thì
    giảm tiếp kích thước. Ảnh điện thoại được sửa EXIF orientation trước.
    """
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return None, 'Thiếu thư viện Pillow — chạy lại CAI-DAT-LAN-DAU.bat.'
    try:
        with Image.open(duong_dan) as src:
            im = ImageOps.exif_transpose(src)
            w0, h0 = im.size
            # Audit 3.7 mục 31: PNG/WebP có alpha không được convert RGB trực
            # tiếp (pixel trong suốt có thể thành nền đen). Composite lên nền
            # trắng có chủ đích; ảnh không alpha giữ đường convert cũ.
            if im.mode in ('RGBA', 'LA') or 'transparency' in im.info:
                rgba = im.convert('RGBA')
                nen = Image.new('RGBA', rgba.size, (255, 255, 255, 255))
                nen.alpha_composite(rgba)
                im = nen.convert('RGB')
            else:
                im = im.convert('RGB')
            # Giới hạn cạnh dài, không chỉ width: ảnh dọc 1200x4000 trước đây lọt nguyên.
            canh_dai = max(im.width, im.height)
            if canh_dai > rong_toi_da:
                ty_le = rong_toi_da / canh_dai
                im = im.resize((max(1, round(im.width * ty_le)),
                                max(1, round(im.height * ty_le))), Image.LANCZOS)
            q = CHAT_LUONG_DAU
            while True:
                buf = io.BytesIO()
                im.save(buf, 'WEBP', quality=q, method=4)
                b = buf.getvalue()
                if len(b) <= kb_toi_da * 1024:
                    return b, {'rong': im.width, 'cao': im.height,
                               'kb': round(len(b) / 1024, 1), 'chat_luong': q,
                               'goc': f'{w0}x{h0}'}
                if q > CHAT_LUONG_MIN:
                    q = max(CHAT_LUONG_MIN, q - 7)
                    continue
                # Quality đã chạm đáy mà vẫn quá nặng: thu cả hai chiều rồi thử lại.
                if max(im.width, im.height) <= 320:
                    return None, (f'Không thể nén dưới {kb_toi_da}KB mà vẫn giữ cạnh dài >=320px; '
                                  f'kết quả cuối {round(len(b)/1024,1)}KB.')
                im = im.resize((max(1, round(im.width * 0.85)),
                                max(1, round(im.height * 0.85))), Image.LANCZOS)
                q = CHAT_LUONG_DAU
    except Exception as e:
        return None, f'{type(e).__name__}: {e}'


# ---------------------------------------------------------------- watermark upload-only

def _bool_env(ten, mac_dinh=True):
    v = os.environ.get(ten)
    if v is None:
        return bool(mac_dinh)
    return str(v).strip().lower() not in ('0', 'false', 'off', 'no', 'khong', 'không')


def _hotline_watermark(ma_site):
    """Lấy hotline cho watermark theo thứ tự an toàn, không đoán mò.

    1) WATERMARK_PHONE (override riêng cho ảnh)
    2) WP_WEBSITE_HOTLINE (nếu sau này config website có field này)
    3) hotline của site legacy nếu ``ma_site`` thực sự là mã site1/site2/...

    Ver 3 hiện dùng ``ma_site='website'`` nên nếu chưa có 1/2 thì trả rỗng;
    tuyệt đối không lấy đại hotline của site khác vì sẽ in sai số lên hàng loạt ảnh.
    """
    for key in ('WATERMARK_PHONE', 'WP_WEBSITE_HOTLINE'):
        v = str(os.environ.get(key, '') or '').strip()
        if v:
            return v
    try:
        import cauhinh as C
        cfg = (C.tat_ca_site() or {}).get(str(ma_site)) or {}
        v = str(cfg.get('hotline') or '').strip()
        if v:
            return v
    except Exception:
        pass
    return ''


def cau_hinh_watermark(ma_site):
    """Watermark chỉ áp lên BẢN UPLOAD, không ghi đè ảnh gốc/canonical.

    Mặc định bật. Nếu không override ``WATERMARK_TEXT`` thì watermark dùng
    DOMAIN của WP hiện tại + HOTLINE (nếu có cấu hình). Hotline KHÔNG được
    đoán từ site khác: đặt một lần bằng ``WATERMARK_PHONE`` trong env nếu
    Ver 3 chưa có field hotline riêng.

    Signature được lưu theo delivery site. Đổi domain/phone/opacity/position
    thì asset sẽ upload lại đúng một lần, sau đó tiếp tục idempotent.
    """
    from urllib.parse import urlparse
    bat = _bool_env('WATERMARK_ENABLED', True)

    url = str(os.environ.get(f'WP_{str(ma_site).upper()}_URL', '') or '').strip()
    try:
        domain = (urlparse(url if '://' in url else 'https://' + url).hostname or '').lower()
    except Exception:
        domain = ''
    if domain.startswith('www.'):
        domain = domain[4:]
    domain = domain or 'LOTECH'
    phone = _hotline_watermark(ma_site)

    custom = str(os.environ.get('WATERMARK_TEXT', '') or '').strip()
    if custom:
        # Cho phép template nhưng vẫn tương thích text cũ như "LOTECH-TEST".
        text = custom.replace('{domain}', domain).replace('{phone}', phone).replace('\\n', '\n').strip()
        lines = [x.strip() for x in text.split('\n') if x.strip()] or [text]
    else:
        lines = [domain] + ([phone] if phone else [])
        text = ' | '.join(lines)

    try:
        opacity = max(35, min(220, int(os.environ.get('WATERMARK_OPACITY', '82'))))
    except Exception:
        opacity = 82
    position = str(os.environ.get('WATERMARK_POSITION', 'bottom-right') or 'bottom-right').strip().lower()
    if position not in ('bottom-right', 'bottom-left', 'top-right', 'top-left'):
        position = 'bottom-right'
    try:
        scale = max(0.018, min(0.080, float(os.environ.get('WATERMARK_SCALE', '0.026'))))
    except Exception:
        scale = 0.026
    # Ver 5.5 — kiểu watermark. 'goc' = hành vi cũ (hộp đen 1 góc),
    # 'ket_hop' = mức B đã chốt: lặp chéo mờ chống crop + thanh chân trang
    # đọc được ở thumbnail. Mặc định 'ket_hop'.
    kieu = str(os.environ.get('WATERMARK_STYLE', 'ket_hop') or 'ket_hop').strip().lower()
    if kieu not in ('goc', 'ket_hop', 'thanh', 'cheo'):
        kieu = 'ket_hop'
    try:
        cheo_alpha = max(0, min(120, int(os.environ.get('WATERMARK_TILE_ALPHA', '52'))))
    except Exception:
        cheo_alpha = 52
    payload = json.dumps({'v': 3, 'on': bat, 'kieu': kieu, 'cheo_alpha': cheo_alpha,
                          'domain': domain, 'phone': phone,
                          'lines': lines, 'opacity': opacity,
                          'position': position, 'scale': round(scale, 4)},
                         sort_keys=True, ensure_ascii=False)
    sig = hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]
    return {'enabled': bat, 'text': text, 'lines': lines, 'domain': domain,
            'phone': phone, 'opacity': opacity, 'position': position,
            'scale': scale, 'kieu': kieu, 'cheo_alpha': cheo_alpha, 'sig': sig}

def _font_watermark(ImageFont, size):
    """Không đóng gói font riêng. Ưu tiên font hệ thống rồi fallback Pillow."""
    ds = [
        r'C:\Windows\Fonts\arialbd.ttf',
        r'C:\Windows\Fonts\segoeuib.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
    ]
    for f in ds:
        try:
            if Path(f).is_file():
                return ImageFont.truetype(f, size=size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _do_sang_trung_binh(im, hop=None):
    """Độ sáng trung bình 0-255 của ảnh (hoặc 1 vùng).

    Ver 5.5 — cần thiết vì watermark chữ TRẮNG trên ảnh nền TRẮNG là vô
    hình hoàn toàn. Ảnh catalogue nền trắng chiếm phần lớn kho, nên bản
    trước gần như không có watermark trên đúng nhóm ảnh đông nhất.
    """
    v = im.convert('L')
    if hop:
        v = v.crop(hop)
    v = v.resize((16, 16))
    px = list(v.tobytes())
    return sum(px) / max(1, len(px))


def _chu_co_vien(d, xy, text, font, mau_chu, mau_vien, day=3):
    """Vẽ chữ có viền. Viền là thứ giúp chữ đọc được mà KHÔNG cần hộp nền
    đè lên ảnh — đây là lý do bỏ được hộp đen của bản v2."""
    x, y = xy
    r2 = day * day
    for dx in range(-day, day + 1):
        for dy in range(-day, day + 1):
            if dx * dx + dy * dy <= r2:
                d.text((x + dx, y + dy), text, font=font, fill=mau_vien)
    d.text((x, y), text, font=font, fill=mau_chu)


def _lop_cheo(Image, ImageDraw, im, cfg, ImageFont):
    """Lớp chữ lặp chéo 30 độ phủ toàn ảnh — phần chống crop.

    Màu tự đảo theo độ sáng nền. Alpha mặc định 52 (mức B): nhìn thấy rõ,
    đủ làm nản người copy lười, nhưng không đè lên thân sản phẩm như kiểu
    chữ to giữa ảnh.
    """
    W, H = im.size
    sang = _do_sang_trung_binh(im)
    a = int(cfg.get('cheo_alpha', 52))
    mau = (255, 255, 255, a) if sang < 140 else (30, 38, 50, int(a * 0.9))
    lop = Image.new('RGBA', (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(lop)
    f = _font_watermark(ImageFont, max(11, round(W * 0.022)))
    txt = cfg.get('domain') or 'LOTECH'
    b = d.textbbox((0, 0), txt, font=f)
    bw, bh = max(1, b[2] - b[0]), max(1, b[3] - b[1])
    for r, y in enumerate(range(0, H * 2, bh * 5)):
        for x in range(-bw, W * 2, bw + round(W * 0.11)):
            d.text((x + (bw // 2 if r % 2 else 0), y), txt, font=f, fill=mau)
    lop = lop.rotate(30, resample=Image.BICUBIC, center=(W, H))
    lop = lop.crop((W // 2, H // 2, W // 2 + W, H // 2 + H))
    return Image.alpha_composite(im, lop)


def _lop_thanh_chan(Image, ImageDraw, im, cfg, ImageFont):
    """Thanh chân trang: dải mờ hết chiều ngang + domain trái, hotline phải.

    Đây là phần ĐỌC ĐƯỢC Ở THUMBNAIL. Watermark góc của bản v2 ở 200px
    (đúng cỡ Google Images hiển thị) không đọc ra số nào — đo trực tiếp.
    """
    W, H = im.size
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    hb = max(22, round(H * 0.082))
    d.rectangle((0, H - hb, W, H), fill=(12, 18, 28, 160))
    d.rectangle((0, H - hb, W, H - hb + max(2, round(hb * 0.04))),
                fill=(255, 186, 40, 230))
    f1 = _font_watermark(ImageFont, max(11, round(hb * 0.42)))
    f2 = _font_watermark(ImageFont, max(11, round(hb * 0.40)))
    pad = round(W * 0.022)
    dom = cfg.get('domain') or 'LOTECH'
    b1 = d.textbbox((0, 0), dom, font=f1)
    d.text((pad, H - hb + (hb - (b1[3] - b1[1])) / 2 - b1[1]), dom, font=f1,
           fill=(255, 255, 255, 248))
    phone = cfg.get('phone') or ''
    if phone:
        t2 = 'Hotline ' + phone
        b2 = d.textbbox((0, 0), t2, font=f2)
        d.text((W - pad - (b2[2] - b2[0]), H - hb + (hb - (b2[3] - b2[1])) / 2 - b2[1]),
               t2, font=f2, fill=(255, 200, 60, 250))
    return Image.alpha_composite(im, ov)


def _lop_goc_v2(Image, ImageDraw, im, cfg, ImageFont):
    """Kiểu cũ (v2): hộp đen bo góc + chữ trắng ở 1 góc. Giữ lại để quay về
    được nếu kiểu mới không hợp, KHÔNG xoá."""
    W, H = im.size
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    fs = max(14, min(72, round(W * cfg['scale'])))
    f = _font_watermark(ImageFont, fs)
    lines = list(cfg.get('lines') or [cfg.get('text') or 'LOTECH'])
    boxes = [d.textbbox((0, 0), l, font=f) for l in lines]
    widths = [max(1, b[2] - b[0]) for b in boxes]
    heights = [max(1, b[3] - b[1]) for b in boxes]
    gap = max(2, round(fs * 0.20)) if len(lines) > 1 else 0
    tw = max(widths) if widths else 1
    th = sum(heights) + gap * max(0, len(lines) - 1)
    px, py = max(6, round(fs * 0.38)), max(4, round(fs * 0.22))
    m = max(8, round(min(W, H) * 0.018))
    bw, bh = tw + px * 2, th + py * 2
    pos = cfg['position']
    x = m if pos.endswith('left') else max(m, W - bw - m)
    y = m if pos.startswith('top') else max(m, H - bh - m)
    bg_a = max(24, min(110, round(cfg['opacity'] * 0.62)))
    try:
        d.rounded_rectangle((x, y, x + bw, y + bh), radius=max(4, py), fill=(0, 0, 0, bg_a))
    except Exception:
        d.rectangle((x, y, x + bw, y + bh), fill=(0, 0, 0, bg_a))
    yy = y + py
    for l, b, hh in zip(lines, boxes, heights):
        ww = max(1, b[2] - b[0])
        tx = x + px if pos.endswith('left') else x + bw - px - ww
        d.text((tx, yy - b[1]), l, font=f, fill=(255, 255, 255, cfg['opacity']))
        yy += hh + gap
    return Image.alpha_composite(im, ov)


def them_watermark_webp(bytes_webp, ma_site, kb_toi_da=KB_TOI_DA):
    """Trả ``(bytes_upload, info)``. Canonical local vẫn là WebP sạch.

    Bản upload được watermark text bán trong suốt. Encode lại tới <= ngưỡng
    KB để watermark không phá budget ảnh. Không sửa file nguồn trên đĩa.
    """
    cfg = cau_hinh_watermark(ma_site)
    if not cfg['enabled']:
        return bytes_webp, dict(cfg, kb=round(len(bytes_webp) / 1024, 1))
    try:
        from PIL import Image, ImageDraw, ImageFont
        with Image.open(io.BytesIO(bytes_webp)) as src:
            im = src.convert('RGBA')

        # Ver 5.5 — dựng theo kiểu. 'ket_hop' (mặc định) = lặp chéo mờ chống
        # crop + thanh chân trang đọc được ở thumbnail. Cả hai lớp tự đảo màu
        # theo độ sáng nền, vì chữ trắng trên ảnh nền trắng là vô hình.
        kieu = cfg.get('kieu', 'ket_hop')
        if kieu == 'goc':
            out = _lop_goc_v2(Image, ImageDraw, im, cfg, ImageFont)
        elif kieu == 'cheo':
            out = _lop_cheo(Image, ImageDraw, im, cfg, ImageFont)
        elif kieu == 'thanh':
            out = _lop_thanh_chan(Image, ImageDraw, im, cfg, ImageFont)
        else:
            out = _lop_thanh_chan(Image, ImageDraw,
                                  _lop_cheo(Image, ImageDraw, im, cfg, ImageFont),
                                  cfg, ImageFont)
        out = out.convert('RGB')

        q = 80
        while True:
            buf = io.BytesIO()
            out.save(buf, 'WEBP', quality=q, method=4)
            b = buf.getvalue()
            if len(b) <= kb_toi_da * 1024:
                return b, dict(cfg, kb=round(len(b) / 1024, 1))
            if q > CHAT_LUONG_MIN:
                q = max(CHAT_LUONG_MIN, q - 6)
                continue
            if max(out.width, out.height) <= 320:
                # Không fail cả slot chỉ vì watermark làm tăng vài KB; giữ
                # bản encode cuối cùng nhưng báo đúng size trong info.
                return b, dict(cfg, kb=round(len(b) / 1024, 1), over_budget=True)
            out = out.resize((max(1, round(out.width * 0.90)),
                              max(1, round(out.height * 0.90))), Image.LANCZOS)
            q = 80
    except Exception as e:
        # Watermark là enhancement, không được làm chết upload ảnh. Fail-soft:
        # upload WebP sạch và trả warning để log/test nhìn thấy.
        return bytes_webp, dict(cfg, kb=round(len(bytes_webp) / 1024, 1),
                                warning=f'{type(e).__name__}: {e}')


# ---------------------------------------------------------------- tên + alt
def ten_file(slug, vai_tro, thu_tu=None):
    """`{slug}-{vai_tro}.webp`.

    Tên TRÊN ĐĨA khoá theo SKU (thư mục), tên TRÊN WEB khoá theo slug.
    Slug đổi thì chỉ chạy lại lượt upload, ảnh gốc không phải sờ tới.
    """
    s = re.sub(r'[^a-z0-9-]+', '-', str(slug or 'san-pham').lower()).strip('-')
    vt = str(vai_tro or '').replace('_', '-')
    duoi = f'-{thu_tu:02d}' if thu_tu else ''
    return f'{s}-{vt}{duoi}.webp'


_MO_TA_VAI_TRO = {
    'hero': '',
    'bien_may': 'Biển máy ',
    'can_canh': 'Cận cảnh ',
    'lap_dat': 'Lắp đặt ',
    'giao_hang': 'Giao hàng ',
}
_DUOI_VAI_TRO = {
    'hero': '',
    'bien_may': '',
    'can_canh': '',
    'lap_dat': ' tại công trình',
    'giao_hang': ' đến công trình',
}


def alt_text(row, vai_tro, tieu_de=''):
    """Alt sinh BẰNG CODE từ record + vai trò ô, không gọi AI.

    Hai ràng buộc:
      * Mỗi vai trò một câu KHÁC NHAU. Năm alt giống hệt nhau là nhồi từ
        khoá, Google coi đó là tín hiệu xấu chứ không phải tối ưu.
      * CHỈ chèn thông số có dữ liệu thật. Thiếu thì bỏ mệnh đề — Hard
        Block áp cho alt y như áp cho nội dung bài.
    """
    ten = str(tieu_de or row.get('ten_goc') or row.get('ma_goc') or '').strip()
    ten = re.sub(r'^\s*Báo giá\s+', '', ten, flags=re.I).strip()
    ten = re.sub(r'\s+', ' ', ten.replace('\n', ' '))
    if not ten:
        return ''
    truoc = _MO_TA_VAI_TRO.get(vai_tro, '')
    sau = _DUOI_VAI_TRO.get(vai_tro, '')
    cau = f'{truoc}{ten}{sau}'.strip()
    return cau[0].upper() + cau[1:] if cau else cau


# ---------------------------------------------------------------- HTML chèn bài
def the_img(url, alt, rong, cao, dau_tien=False):
    """Thẻ img đúng chuẩn:
      * ảnh đầu (LCP) KHÔNG lazy-load; từ ảnh thứ hai mới lazy
      * luôn khai width/height để trình duyệt chừa chỗ, khỏi giật layout
    """
    lazy = '' if dau_tien else ' loading="lazy" decoding="async"'
    return (f'<img src="{html.escape(str(url), quote=True)}" alt="{html.escape(str(alt), quote=True)}" width="{int(rong)}" height="{int(cao)}"'
            f'{lazy} class="snl-anh">')


def khoi_anh_bai(danh_sach):
    """Dựng HTML các ảnh để CHÈN VÀO NỘI DUNG BÀI.

    Phải nằm trong content chứ không chỉ gallery WooCommerce — Rank Math
    sinh image sitemap từ ảnh trong content.

    `danh_sach`: [{'url','alt','rong','cao','vai_tro','nhan'}...]
    """
    if not danh_sach:
        return ''
    ra = []
    for i, a in enumerate(danh_sach):
        cap = a.get('nhan') or ''
        fig = ['<figure class="snl-hinh">',
               the_img(a['url'], a['alt'], a['rong'], a['cao'], dau_tien=(i == 0))]
        if cap:
            fig.append(f'<figcaption>{html.escape(str(cap))}</figcaption>')
        fig.append('</figure>')
        ra.append(''.join(fig))
    return ''.join(ra)


def _figure_anh_noi_dung(a, vai_tro=''):
    """Một ảnh body, có marker role để re-run thay ảnh mà không nhân đôi."""
    if not a or not a.get('url'):
        return ''
    role = str(vai_tro or a.get('vai_tro') or '').strip()
    data_role = f' data-snl-role="{html.escape(role, quote=True)}"' if role else ''
    return ('<figure class="snl-hinh"' + data_role + '>' +
            the_img(a['url'], a.get('alt', ''), a.get('rong', 0), a.get('cao', 0), dau_tien=False) +
            '</figure>')


def _thay_slot_legacy(noi_dung, vai_tro, html_anh):
    """Thay/xóa placeholder Ver <=4.3 theo đúng số vai trò, kể cả comment cũ."""
    so = {'bien_may': '2', 'can_canh': '3', 'lap_dat': '4', 'giao_hang': '5'}.get(vai_tro)
    if not so:
        return noi_dung
    pat = re.compile(
        rf'<!--\s*ẢNH\s*{so}\b.*?-->\s*'
        rf'<div\s+class=["\']snl-cho-anh["\']>.*?'
        rf'<p\s+class=["\']snl-cho-anh-kt["\']>.*?</p>\s*</div>\s*'
        rf'<p\s+class=["\']snl-anh-caption["\']>.*?</p>',
        re.I | re.S)
    moi, n = pat.subn(html_anh, noi_dung, count=1)
    if n:
        return moi
    pat2 = re.compile(
        rf'<div\s+class=["\']snl-cho-anh["\']>\s*'
        rf'<span\s+class=["\']snl-cho-anh-nhan["\']>\s*Ảnh\s*{so}\s*</span>.*?'
        rf'<p\s+class=["\']snl-cho-anh-kt["\']>.*?</p>\s*</div>\s*'
        rf'<p\s+class=["\']snl-anh-caption["\']>.*?</p>',
        re.I | re.S)
    return pat2.sub(html_anh, noi_dung, count=1)


def _chen_truoc_dong_section(text, section_id, html_anh):
    """Chèn trước </section> của section id, không parse DOM để giữ dependency nhẹ."""
    if not html_anh or not section_id:
        return text, False
    pat = re.compile(
        rf'(<section\b[^>]*\bid=["\']{re.escape(section_id)}["\'][^>]*>.*?)(</section>)',
        re.I | re.S)
    moi, n = pat.subn(lambda m: m.group(1) + html_anh + m.group(2), text, count=1)
    return moi, bool(n)


def _chen_truoc_section_dau(text, html_anh):
    """Hero body: chèn ngay trước section nội dung đầu tiên, tức sau mục lục."""
    if not html_anh:
        return text, False
    pat = re.compile(r'(<section\b[^>]*class=["\'][^"\']*\bsnl-section\b[^"\']*["\'][^>]*>)', re.I)
    moi, n = pat.subn(lambda m: html_anh + m.group(1), text, count=1)
    if n:
        return moi, True
    # HTML cũ có section nhưng thiếu class snl-section.
    pat2 = re.compile(r'(<section\b[^>]*>)', re.I)
    moi, n = pat2.subn(lambda m: html_anh + m.group(1), text, count=1)
    return moi, bool(n)


def _chen_truoc_root_close(text, html_anh):
    """Fallback cuối: đặt ảnh trước </div> cuối cùng của content."""
    if not html_anh:
        return text, False
    pos = text.lower().rfind('</div>')
    if pos >= 0:
        return text[:pos] + html_anh + text[pos:], True
    return text + html_anh, True


def chen_anh_vao_bai(noi_dung, danh_sach):
    """Ver 4.4.1.2 — 5 ảnh xuất hiện ở CẢ Woo gallery VÀ body.

    Quy tắc body:
    - hero: trước section nội dung đầu tiên (sau mục lục nếu có)
    - bien_may: cuối section Thông số kỹ thuật
    - can_canh: cuối section Cấu tạo; nếu không có thì cuối Đặc điểm
    - lap_dat: cuối section Ứng dụng; nếu không có thì cuối Hướng dẫn chọn
    - giao_hang: cuối body

    Ưu tiên marker 4.4.1 / placeholder legacy. Nếu bài cũ trong DB không còn
    marker (case production đã đăng trước 4.4.1), tự tìm section semantic để
    chèn. Vì vậy không cần render lại bài và không gọi AI.
    """
    text = str(noi_dung or '')

    # 4.3 từng prepend toàn bộ figure trước root content. Bóc đúng cụm đó.
    text = re.sub(r'^\s*(?:<figure\s+class=["\']snl-hinh["\']>.*?</figure>\s*)+(?=<div\b)',
                  '', text, flags=re.I | re.S)
    # 4.4.1.2: re-run phải thay ảnh, không nhân đôi. Chỉ xóa figure do tool
    # mới chèn vì có data-snl-role, không đụng figure nội dung thủ công.
    text = re.sub(r'<figure\s+class=["\']snl-hinh["\'][^>]*\bdata-snl-role=["\'][^"\']+["\'][^>]*>.*?</figure>',
                  '', text, flags=re.I | re.S)

    theo_vai_tro = {str(a.get('vai_tro')): a for a in (danh_sach or []) if a and a.get('vai_tro')}
    da_chen = set()

    # 1) Marker hiện đại: giờ có cả hero.
    for vt in ('hero', 'bien_may', 'can_canh', 'lap_dat', 'giao_hang'):
        fig = _figure_anh_noi_dung(theo_vai_tro.get(vt), vt)
        marker = f'<!--SNL_IMAGE_SLOT:{vt}-->'
        if marker in text:
            text = text.replace(marker, fig, 1)
            if fig:
                da_chen.add(vt)

    # 2) Placeholder legacy cho role 2..5.
    for vt in ('bien_may', 'can_canh', 'lap_dat', 'giao_hang'):
        if vt in da_chen:
            continue
        fig = _figure_anh_noi_dung(theo_vai_tro.get(vt), vt)
        if not fig:
            continue
        before = text
        text = _thay_slot_legacy(text, vt, fig)
        if text != before:
            da_chen.add(vt)

    # 3) Bài production cũ không còn marker: fallback theo section semantic.
    if 'hero' not in da_chen:
        fig = _figure_anh_noi_dung(theo_vai_tro.get('hero'), 'hero')
        text, ok = _chen_truoc_section_dau(text, fig)
        if ok and fig:
            da_chen.add('hero')

    if 'bien_may' not in da_chen:
        fig = _figure_anh_noi_dung(theo_vai_tro.get('bien_may'), 'bien_may')
        text, ok = _chen_truoc_dong_section(text, 'thong-so', fig)
        if ok and fig:
            da_chen.add('bien_may')

    if 'can_canh' not in da_chen:
        fig = _figure_anh_noi_dung(theo_vai_tro.get('can_canh'), 'can_canh')
        ok = False
        for sec in ('cau-tao', 'dac-diem'):
            text, ok = _chen_truoc_dong_section(text, sec, fig)
            if ok:
                break
        if ok and fig:
            da_chen.add('can_canh')

    if 'lap_dat' not in da_chen:
        fig = _figure_anh_noi_dung(theo_vai_tro.get('lap_dat'), 'lap_dat')
        ok = False
        for sec in ('ung-dung', 'huong-dan'):
            text, ok = _chen_truoc_dong_section(text, sec, fig)
            if ok:
                break
        if ok and fig:
            da_chen.add('lap_dat')

    # Các role còn thiếu (kể cả giao_hang, hoặc section tương ứng không có)
    # được đưa xuống cuối body theo thứ tự chuẩn. Bảo đảm đủ 5 ảnh nếu đủ file.
    cuoi = []
    for vt in ('hero', 'bien_may', 'can_canh', 'lap_dat', 'giao_hang'):
        if vt not in da_chen:
            fig = _figure_anh_noi_dung(theo_vai_tro.get(vt), vt)
            if fig:
                cuoi.append(fig)
                da_chen.add(vt)
    if cuoi:
        text, _ = _chen_truoc_root_close(text, ''.join(cuoi))

    # Ver 4.4.1.5 — dọn rác cuối luồng, gom về sweep_rac.MAU_RAC.
    #
    # Trước 4.4.1.5 chỗ này chỉ xoá marker + comment URL_ANH, KHÔNG xoá
    # div.snl-cho-anh. Placeholder chỉ biến mất khi role đó có ảnh thật
    # (_thay_slot_legacy ở trên bị 'if not fig: continue' chặn), nên role
    # thiếu file thì hướng dẫn chụp ảnh nội bộ lọt ra trang khách.
    #
    # Đặt ở ĐÂY chứ không ở khoi_anh: giao-dien gọi chen_anh_vao_bai(html, [])
    # kể cả khi không có ảnh nào, nên mọi lần đăng/đăng lại đều đi qua đây.
    try:
        import sweep_rac as SR
        text, _ = SR.don_rac_bai(text)
    except Exception:
        # sweep_rac lỗi KHÔNG được làm hỏng luồng đăng ảnh; giữ hành vi cũ.
        text = re.sub(r'<!--SNL_IMAGE_SLOT:[a-z_]+-->', '', text, flags=re.I)
        text = re.sub(r'<!--(?:(?!-->).)*URL_ANH(?:(?!-->).)*-->', '', text, flags=re.I | re.S)
    return text


# ---------------------------------------------------------------- đăng
def dang_anh_cua_bai(thu_muc, row, ma_site, tieu_de='', slug='',
                     upload=None, ghi_log=None):
    """Xử lý + upload toàn bộ ảnh đã gán ô của một bài.

    `upload(duong_dan_tam, ten_file, mime) -> (media_id, url)` — tiêm từ
    ngoài để test được mà không cần WordPress thật.

    Bỏ qua ảnh đã `da_dang` và hash không đổi -> bấm lần hai KHÔNG upload
    thêm bản vô nghĩa. Ảnh `lech` (đã thay file) thì upload lại.

    Trả dict: {'ok', 'da_xu_ly', 'bo_qua', 'loi', 'anh': [...]}
    """
    log = ghi_log or (lambda *_: None)
    thu_muc = Path(thu_muc)
    kq = WS.quet(thu_muc)
    meta = kq['meta']
    slug = slug or meta.get('slug') or ''
    ds_vai_tro = WS.ma_vai_tro(meta.get('profile', ''))

    da_xu_ly, bo_qua, loi, ra = 0, 0, [], []
    bo_qua_nho = 0      # Ver 5.7 — số ảnh bị loại vì dưới ngưỡng CANH_NGAN_TOI_THIEU
    wm_cfg = cau_hinh_watermark(ma_site)
    # theo thứ tự vai trò khai trong profile, KHÔNG theo thứ tự người dùng gán
    for vt in ds_vai_tro:
        a = kq['o'].get(vt)
        if not a:
            continue
        # Ver 4.1 BUG-01: delivery state là theo SITE, không dùng chung
        # wp_media_id/url giữa 8 domain. Top-level fields vẫn giữ để tương thích
        # code cũ, nhưng quyết định skip chỉ dựa delivery_by_site[ma_site].
        delivery = (a.get('delivery_by_site') or {}).get(str(ma_site)) or {}
        wm_khop = (delivery.get('watermark_sig') == wm_cfg.get('sig'))
        # Delivery legacy chưa có watermark_sig: chỉ được reuse nếu watermark
        # hiện đang TẮT. Khi mặc định bật ở 4.4.1.3, ảnh cũ sẽ upload lại đúng
        # một lần để có watermark rồi các lần sau mới skip.
        if not wm_cfg.get('enabled') and not delivery.get('watermark_sig'):
            wm_khop = True
        if (a.get('trang_thai') == WS.DA_DANG and delivery.get('wp_media_id')
                and delivery.get('hash') == a.get('hash_hien_tai') and wm_khop):
            bo_qua += 1
            ra.append({'vai_tro': vt, 'url': delivery.get('media_url', ''),
                       'alt': a.get('alt', ''), 'rong': a.get('rong', 0),
                       'cao': a.get('cao', 0), 'wp_media_id': delivery.get('wp_media_id'),
                       'watermark_sig': delivery.get('watermark_sig'),
                       'da_co': True})
            continue

        # Ver 5.7 — CỔNG CHẤT LƯỢNG ẢNH, đặt ĐÚNG CHỖ.
        # CANH_NGAN_TOI_THIEU (800px) và laplacian_variance() đã có sẵn từ
        # lâu, NHƯNG chỉ được gọi từ loc_kho_anh() — mà loc_kho_anh() chỉ có
        # đúng 1 người gọi là script CLI loc_kho_anh.py (LOC-KHO-ANH.bat).
        # Đường upload THẬT (dang_anh_cua_bai -> sang_webp -> watermark)
        # KHÔNG hề kiểm kích thước hay độ mờ: sang_webp() chỉ THU NHỎ ảnh quá
        # to, không CHẶN ảnh quá nhỏ. Nghĩa là ngưỡng 800px trước bản này chỉ
        # có tác dụng nếu người dùng tự nhớ chạy file .bat — quên là ảnh mờ
        # lên site như cũ.
        # Nay chặn ngay tại nguồn: ảnh dưới ngưỡng KHÔNG upload, ô ảnh để
        # trống (bài tự ẩn ô trống từ Ver 4.4) thay vì đẩy ảnh vỡ lên site.
        nguong = _nguong_canh_ngan()
        try:
            _kt_w, _kt_h = int(a.get('rong') or 0), int(a.get('cao') or 0)
        except (TypeError, ValueError):
            _kt_w = _kt_h = 0
        if nguong and not (_kt_w and _kt_h):
            try:
                from PIL import Image as _Im
                with _Im.open(a['duong_dan']) as _im:
                    _kt_w, _kt_h = _im.size
            except Exception:
                _kt_w = _kt_h = 0
        if nguong and _kt_w and _kt_h and min(_kt_w, _kt_h) < nguong:
            bo_qua_nho += 1
            loi.append(f'{vt}: ảnh {_kt_w}x{_kt_h}px, cạnh ngắn < '
                       f'{nguong}px — bỏ qua, không upload')
            log(f'  [ảnh] {vt} BỎ QUA: {_kt_w}x{_kt_h}px dưới ngưỡng {nguong}px')
            continue

        b, tt = sang_webp(a['duong_dan'])
        if b is None:
            loi.append(f'{vt}: {tt}')
            log(f'  [ảnh] {vt} lỗi nén: {tt}')
            continue

        ten = ten_file(slug, vt)
        tam = thu_muc / ten
        # ``tam`` là canonical local SẠCH. Watermark chỉ áp trên bản upload
        # tạm để không phá ảnh nguồn và không bị đóng watermark lần hai khi
        # cùng workspace được dùng cho site khác.
        tam.write_bytes(b)
        b_upload, wm_info = them_watermark_webp(b, ma_site)
        safe_site = re.sub(r'[^a-z0-9._-]+', '-', str(ma_site).lower()).strip('-') or 'site'
        tm_upload = thu_muc / '.wp-upload' / safe_site
        tm_upload.mkdir(parents=True, exist_ok=True)
        tam_upload = tm_upload / ten
        tam_upload.write_bytes(b_upload)
        alt = alt_text(row, vt, tieu_de or meta.get('title', ''))
        try:
            # Uploader cũ chỉ nhận 3 tham số; uploader production 4.1 có thể
            # nhận thêm alt/title để delivery metadata WordPress Media.
            try:
                media_id, url = upload(str(tam_upload), ten, 'image/webp', alt=alt,
                                       tieu_de=tieu_de or meta.get('title', '') or alt)
            except TypeError:
                media_id, url = upload(str(tam_upload), ten, 'image/webp')
        except Exception as e:
            loi.append(f'{vt}: {type(e).__name__}: {e}')
            log(f'  [ảnh] {vt} lỗi upload: {e}')
            continue

        for m in meta['anh']:
            if m.get('vai_tro') == vt:
                m.update({'ten_sau_doi': ten, 'wp_media_id': media_id,
                          'media_url': url, 'alt': alt,
                          'rong': tt['rong'], 'cao': tt['cao'],
                          'trang_thai': WS.DA_DANG})
                # Delivery mới lên Media CHƯA đồng nghĩa đã gắn vào bài.
                # Không mang attached_wp_post_ids của delivery cũ sang ảnh mới.
                m.setdefault('delivery_by_site', {})[str(ma_site)] = {
                    'wp_media_id': media_id, 'media_url': url,
                    'hash': WS.hash_file(tam),
                    'watermark_sig': wm_info.get('sig'),
                    'watermark_text': wm_info.get('text') if wm_info.get('enabled') else '',
                    'attached_wp_post_ids': []}
                # Sau khi chuyển ảnh gốc vào _goc/, file đại diện cho ô này
                # trên đĩa CHÍNH LÀ bản .webp vừa tạo. Không cập nhật hai
                # trường dưới thì quét lần sau không thấy file -> ô hoá
                # trống, bấm Đăng lần hai lại upload lại từ đầu.
                m['ten_goc_luu'] = a['ten_tren_dia']
                m['ten_tren_dia'] = ten
                m['hash'] = WS.hash_file(tam)
        # Chỉ chuyển FILE GỐC vào _goc. Khi upload site thứ hai,
        # a['ten_tren_dia'] đã chính là WebP processed; chuyển nó đi sẽ làm
        # workspace mất ảnh sau lần delivery cross-site.
        if a.get('ten_tren_dia') != ten:
            WS.chuyen_vao_goc(thu_muc, a['ten_tren_dia'])
        da_xu_ly += 1
        ra.append({'vai_tro': vt, 'url': url, 'alt': alt,
                   'rong': tt['rong'], 'cao': tt['cao'], 'wp_media_id': media_id,
                   'watermark_sig': wm_info.get('sig'),
                   'watermark_text': wm_info.get('text') if wm_info.get('enabled') else '',
                   'da_co': False})
        wm_log = ''
        if wm_info.get('enabled'):
            wm_log = f', watermark={wm_info.get("text")} ({wm_info.get("kb", "?")}KB)'
        if wm_info.get('warning'):
            wm_log += f', WATERMARK WARNING={wm_info.get("warning")}'
        log(f'  [ảnh] {vt}: {tt["goc"]} -> {tt["rong"]}x{tt["cao"]}, '
            f'{tt["kb"]}KB, media_id={media_id}{wm_log}')
        # Upload thành công + meta sắp được ghi. Xoá asset tạm để workspace
        # không phình; nếu process chết trước đây thì file deterministic này
        # vẫn giúp cache upload path/hash tránh POST trùng ở lần chạy sau.
        try:
            tam_upload.unlink(missing_ok=True)
        except Exception:
            pass

    WS.ghi_meta(thu_muc, meta)
    return {'ok': not loi, 'partial': bool(loi and ra),
            'da_xu_ly': da_xu_ly, 'bo_qua': bo_qua,
            'bo_qua_nho': bo_qua_nho,   # Ver 5.7 — ảnh loại vì dưới ngưỡng px
            'loi': loi, 'anh': ra}


def dang_anh_hieu_luc(goc, sheet, thu_muc_rieng, row, ma_site,
                      tieu_de='', slug='', upload=None, ghi_log=None):
    """Ver 4.0 — upload + ghép ảnh RIÊNG/HỌ theo từng vai trò.

    Ảnh riêng thắng ảnh họ ở cùng vai trò; họ chỉ lấp ô còn thiếu. Workspace
    họ được upload một lần rồi tái dùng media_id cho mọi SKU cùng họ.
    Không gọi WordPress trực tiếp: uploader vẫn được tiêm từ ngoài như hàm
    ``dang_anh_cua_bai`` để test bằng mock.
    """
    log = ghi_log or (lambda *_: None)
    hieu_luc = WS.anh_hieu_luc(goc, sheet, row, thu_muc_rieng)
    tm_ho = hieu_luc.get('thu_muc_ho')

    kq_ho = {'ok': True, 'da_xu_ly': 0, 'bo_qua': 0, 'loi': [], 'anh': []}
    if tm_ho:
        meta_ho = WS.doc_meta(tm_ho) or {}
        kq_ho = dang_anh_cua_bai(
            tm_ho, row, ma_site,
            tieu_de=meta_ho.get('family_label') or meta_ho.get('title') or 'Họ sản phẩm',
            slug=meta_ho.get('slug') or ('ho-' + str((WS.ho_san_pham(row) or {}).get('key', 'san-pham'))),
            upload=upload, ghi_log=log)

    kq_rieng = {'ok': True, 'da_xu_ly': 0, 'bo_qua': 0, 'loi': [], 'anh': []}
    if thu_muc_rieng and Path(thu_muc_rieng).is_dir():
        kq_rieng = dang_anh_cua_bai(
            thu_muc_rieng, row, ma_site, tieu_de=tieu_de, slug=slug,
            upload=upload, ghi_log=log)

    theo_ho = {a.get('vai_tro'): a for a in kq_ho.get('anh', [])}
    theo_rieng = {a.get('vai_tro'): a for a in kq_rieng.get('anh', [])}
    ds = []
    nguon_o = {}
    for vt in WS.ma_vai_tro(row.get('profile_id', '')):
        a = theo_rieng.get(vt) or theo_ho.get(vt)
        if not a:
            continue
        b = dict(a)
        # Alt trong HTML phải đúng SKU hiện tại dù URL/media họ được tái dùng.
        b['alt'] = alt_text(row, vt, tieu_de)
        b['nguon'] = 'rieng' if vt in theo_rieng else 'ho'
        nguon_o[vt] = b['nguon']
        ds.append(b)

    co_rieng = any(v == 'rieng' for v in nguon_o.values())
    co_ho = any(v == 'ho' for v in nguon_o.values())
    nguon = 'rieng' if co_rieng else ('ho' if co_ho else 'trong')

    # BUG-E 4.4.1.3: lỗi ở nguồn HỌ/RIÊNG không được kéo chết cả bài nếu
    # vai trò đó đã có nguồn còn lại fallback thành công. Giữ lại thành
    # cảnh báo để người dùng biết asset riêng/họ có vấn đề, nhưng chỉ ``loi``
    # những vai trò THỰC SỰ không có ảnh hiệu lực để attach.
    tat_ca_loi = list(kq_ho.get('loi', [])) + list(kq_rieng.get('loi', []))
    role_ok = set(nguon_o)
    loi, canh_bao = [], []
    for e in tat_ca_loi:
        role = str(e).split(':', 1)[0].strip()
        (canh_bao if role in role_ok else loi).append(e)
    return {
        'ok': not loi, 'partial': bool(loi and ds),
        'da_xu_ly': kq_ho.get('da_xu_ly', 0) + kq_rieng.get('da_xu_ly', 0),
        'bo_qua': kq_ho.get('bo_qua', 0) + kq_rieng.get('bo_qua', 0),
        'bo_qua_nho': kq_ho.get('bo_qua_nho', 0) + kq_rieng.get('bo_qua_nho', 0),
        'loi': loi, 'canh_bao': canh_bao, 'anh': ds, 'nguon': nguon, 'nguon_o': nguon_o,
        'kq_ho': kq_ho, 'kq_rieng': kq_rieng,
    }
