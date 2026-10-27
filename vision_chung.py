# -*- coding: utf-8 -*-
"""
SONEALEO ULTRA 3.0 — VISION CHUNG: gọi Gemini đọc ẢNH, trả JSON.

Dùng chung cho doc_bien_may.py (biển máy) và doc_catalogue_pdf.py
(trang catalogue). Nguyên tắc:
  - Đọc key/model từ CHÍNH cau-hinh.env của tool (GOOGLE_API_KEY,
    GOOGLE_API_KEY_DU_PHONG, MODEL_GEMINI) — không cấu hình mới.
  - CACHE kết quả theo hash file vào .vision-cache/ — chạy lại không
    đốt quota lần hai cho cùng một ảnh.
  - Hết lượt key này -> tự xoay sang key dự phòng (giống Ver 4.7 của
    ai_wp_adapter).
  - Ảnh downscale trước khi gửi (phân loại 512px, đọc chi tiết 1400px)
    — tiết kiệm token, biển máy chữ to nên 1400px đọc thoải mái.
  - AI CHỈ CHÉP LẠI những gì đọc được trên ảnh. Không thấy -> null.
    Đây là mắt xích Hard Block không với tới (số đi thẳng vào Excel),
    nên kỷ luật nằm ở prompt + bước NGƯỜI SOÁT file kết quả trước khi
    ghép vào master (ghep_vao_master.py không bao giờ tự ghi đè).
"""
import base64
import hashlib
import io
import json
import os
import re
import time

VISION_CACHE = '.vision-cache'
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta'


# ---------------------------------------------------------------- cấu hình
def _nap_env(duong_dan='cau-hinh.env'):
    """Đọc file env kiểu KEY=VALUE (không phụ thuộc python-dotenv)."""
    if not os.path.exists(duong_dan):
        return
    with open(duong_dan, encoding='utf-8') as f:
        for dong in f:
            dong = dong.strip()
            if not dong or dong.startswith('#') or '=' not in dong:
                continue
            k, _, v = dong.partition('=')
            os.environ.setdefault(k.strip(), v.strip())


def doc_cau_hinh():
    """Trả {'keys': [key chính, các key dự phòng...], 'model': ...}."""
    _nap_env()
    keys = []
    chinh = os.environ.get('GOOGLE_API_KEY', '').strip()
    if chinh:
        keys.append(chinh)
    for k in re.split(r'[,;\s]+', os.environ.get('GOOGLE_API_KEY_DU_PHONG', '')):
        k = k.strip()
        if k and k not in keys:
            keys.append(k)
    return {'keys': keys,
            'model': os.environ.get('MODEL_GEMINI', 'gemini-3.6-flash').strip()}


# ---------------------------------------------------------------- ảnh
def thu_nho_anh(duong_dan, rong_toi_da=1400, chat_luong=82):
    """Trả (bytes JPEG đã thu nhỏ, mime). Ảnh gốc KHÔNG bị sửa."""
    from PIL import Image
    with Image.open(duong_dan) as im:
        im = im.convert('RGB')
        if im.width > rong_toi_da:
            cao = round(im.height * rong_toi_da / im.width)
            im = im.resize((rong_toi_da, cao), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=chat_luong)
        return buf.getvalue(), 'image/jpeg'


# ---------------------------------------------------------------- cache
def _hash_file(duong_dan):
    h = hashlib.sha1()
    with open(duong_dan, 'rb') as f:
        for khoi in iter(lambda: f.read(1 << 20), b''):
            h.update(khoi)
    return h.hexdigest()[:16]


def _hash_chuoi(s):
    return hashlib.sha1(str(s).encode('utf-8', 'ignore')).hexdigest()[:8]


def doc_cache(duong_dan, nhan, them=''):
    """Ver 3.1 — `them`: chuỗi phụ (model + prompt) trộn vào khoá cache.
    Trước đây cache chỉ theo hash ảnh + nhãn -> sửa prompt xong chạy lại
    vẫn ăn kết quả cũ (lỗi GPT bắt được). Giờ đổi prompt/model là khoá
    đổi, tự đọc lại."""
    os.makedirs(VISION_CACHE, exist_ok=True)
    duoi = f'-{_hash_chuoi(them)}' if them else ''
    f = os.path.join(VISION_CACHE, f'{_hash_file(duong_dan)}-{nhan}{duoi}.json')
    if os.path.exists(f):
        try:
            with open(f, encoding='utf-8') as r:
                return json.load(r)
        except Exception:
            return None
    return None


def ghi_cache(duong_dan, nhan, du_lieu, them=''):
    os.makedirs(VISION_CACHE, exist_ok=True)
    duoi = f'-{_hash_chuoi(them)}' if them else ''
    f = os.path.join(VISION_CACHE, f'{_hash_file(duong_dan)}-{nhan}{duoi}.json')
    with open(f, 'w', encoding='utf-8') as w:
        json.dump(du_lieu, w, ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- gọi Gemini
def _doc_429(r):
    """Bóc thời gian chờ Google đề nghị từ body lỗi 429 (RetryInfo)."""
    try:
        chi_tiet = r.json().get('error', {}).get('details', [])
        for d in chi_tiet:
            if 'RetryInfo' in str(d.get('@type', '')):
                m = re.search(r'(\d+)', str(d.get('retryDelay', '')))
                if m:
                    return int(m.group(1))
        msg = r.json().get('error', {}).get('message', '')
        if 'per day' in msg.lower() or 'daily' in msg.lower():
            return -1          # hết lượt trong ngày -> đổi key, đừng chờ
    except Exception:
        pass
    return 20


def _luu_raw_loi(noi_dung, ly_do):
    """Ver 3.1 — parse hỏng thì LƯU NGUYÊN VĂN response để soi, thay vì
    vứt đi (yêu cầu GPT: 'log raw response khi parse thất bại')."""
    thu_muc = os.path.join(VISION_CACHE, 'raw-loi')
    os.makedirs(thu_muc, exist_ok=True)
    ten = os.path.join(thu_muc, f'{int(time.time() * 1000)}.txt')
    try:
        with open(ten, 'w', encoding='utf-8') as w:
            w.write(f'# {ly_do}\n{noi_dung}')
    except Exception:
        return None
    return ten


def _boc_text(r):
    """Bóc text từ response Gemini. Trả (text, ly_do_hong).

    Ver 3.1 — model Gemini 3.x có 'suy nghĩ nội bộ' ăn token TRƯỚC khi
    xuất chữ: maxOutputTokens thấp -> finishReason=MAX_TOKENS và content
    KHÔNG có 'parts' -> đây chính là lỗi \"'parts'\" tràn log hôm 06/08.
    """
    try:
        ung_vien = r.json().get('candidates') or []
        if not ung_vien:
            return None, 'response không có candidates'
        cand = ung_vien[0]
        ly_do_dung = cand.get('finishReason', '')
        parts = (cand.get('content') or {}).get('parts') or []
        text = ''.join(p.get('text', '') for p in parts).strip()
        if not text:
            if ly_do_dung == 'MAX_TOKENS':
                return None, 'HET_TOKEN'      # tín hiệu riêng -> retry ngân sách to hơn
            return None, f'response rỗng (finishReason={ly_do_dung or "?"})'
        return text, None
    except Exception as e:
        return None, f'không đọc được cấu trúc response: {e}'


def goi_vision(anh_bytes, mime, prompt, cau_hinh=None, max_tokens=4000,
               timeout=120, _requests=None):
    """Gửi 1 ảnh + prompt, ép trả JSON. Tự xoay key khi hết lượt ngày.

    Ver 3.1 — chống chết lãng nhách (7 lỗi/8 trang hôm 06/08):
      - Thiếu token vì model 'suy nghĩ' -> retry 1 lần với ngân sách x4.
      - JSON parse hỏng -> retry 1 lần; vẫn hỏng -> LƯU RAW để soi.
      - max_tokens tối thiểu 1000 (dưới mức đó model 3.x chưa kịp nói gì).

    Trả {'ok': True, 'json': ...} hoặc {'ok': False, 'loi': ...}.
    _requests: tiêm mock khi test — không đụng mạng thật.
    """
    import requests as _rq
    rq = _requests or _rq
    ch = cau_hinh or doc_cau_hinh()
    if not ch['keys']:
        return {'ok': False, 'loi': 'Chưa có GOOGLE_API_KEY trong cau-hinh.env.'}
    max_tokens = max(int(max_tokens), 1000)

    def _body(so_token):
        return {
            'contents': [{'parts': [
                {'text': prompt},
                {'inline_data': {'mime_type': mime,
                                 'data': base64.b64encode(anh_bytes).decode()}},
            ]}],
            'generationConfig': {'temperature': 0.1,
                                 'response_mime_type': 'application/json',
                                 'maxOutputTokens': so_token},
        }

    loi_cuoi = 'không rõ'
    for key in ch['keys']:
        url = f"{GEMINI_URL}/models/{ch['model']}:generateContent?key={key}"
        ngan_sach = max_tokens
        da_retry_parse = False
        lan = 0
        while lan < 4:
            lan += 1
            try:
                r = rq.post(url, json=_body(ngan_sach), timeout=timeout)
            except Exception as e:
                loi_cuoi = f'lỗi mạng: {e}'
                time.sleep(5)
                continue
            if r.status_code == 429:
                cho = _doc_429(r)
                if cho == -1:
                    loi_cuoi = f'key ...{key[-6:]} hết lượt trong ngày'
                    break              # sang key kế
                time.sleep(cho)
                continue
            if r.status_code in (500, 502, 503):
                loi_cuoi = f'HTTP {r.status_code} (máy chủ Google quá tải)'
                time.sleep(8)
                continue
            if r.status_code != 200:
                loi_cuoi = f'HTTP {r.status_code}: {r.text[:200]}'
                break
            text, hong = _boc_text(r)
            if hong == 'HET_TOKEN' and ngan_sach < max_tokens * 4:
                ngan_sach = max_tokens * 4     # model 'suy nghĩ' ăn hết — nới rồi thử lại
                continue
            if hong:
                loi_cuoi = hong
                _luu_raw_loi(r.text[:5000], hong)
                break
            text = re.sub(r'^```(?:json)?|```$', '', text.strip(),
                          flags=re.MULTILINE).strip()
            try:
                return {'ok': True, 'json': json.loads(text)}
            except Exception as e:
                if not da_retry_parse:
                    da_retry_parse = True      # thử lại đúng 1 lần
                    continue
                duong_raw = _luu_raw_loi(text[:5000], f'JSON hỏng: {e}')
                loi_cuoi = (f'không parse được JSON trả về: {e}'
                            + (f' (raw: {duong_raw})' if duong_raw else ''))
                break
    return {'ok': False, 'loi': loi_cuoi}
