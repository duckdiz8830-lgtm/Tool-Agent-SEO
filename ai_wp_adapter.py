# -*- coding: utf-8 -*-
"""
AI/WordPress adapter — Round 2/Gate 2: mock. Gate "Draft thật": thêm đường
GỌI THẬT (goi_ai_that, dang_wp_that, kiem_tra_ket_noi_wp), giữ nguyên đường
mock (goi_ai_mock, dang_wp_mock) cho tab Sinh & Đăng khi chọn chế độ Mock/Test.

  - goi_ai_mock()  : mô phỏng AI trả JSON đúng schema outline, CHỈ dùng dữ
                      liệu có thật trong record.
  - dang_wp_mock() : mô phỏng đăng WordPress, idempotent theo
                      (dataset_id, record_id, site, mau).
  - goi_ai_that()  : gọi Gemini thật, đúng 1 record (không batch).
  - dang_wp_that() : đăng Draft thật lên WordPress, idempotent + không
                      retry mù (dò lại slug trước khi thử lại sau lỗi mạng).
  - kiem_tra_ket_noi_wp() : xác thực REST API, KHÔNG tạo bài.
  - kiem_tra_bia_toan_bo(): Hard Block E2E — mọi field AI trả, không chỉ 4
                      field văn xuôi.

Tái sử dụng máy móc đã có trong autopost.py qua IMPORT, không copy code:
  - autopost.go_json / doc_429           : parse & xử lý lỗi Gemini, generic
  - autopost.thong_tin_wp / _auth        : đọc cấu hình WP theo mã site, generic
  - autopost.tim_bai_theo_slug           : chống đẻ slug -2, generic
  - autopost.UA / HEADERS                : header HTTP dùng chung
  - autopost.do_model()                  : dò model Gemini chạy được (gọi
                                            trực tiếp từ giao-dien.py, không
                                            viết lại ở đây)
Các hàm trên KHÔNG có phụ thuộc gì vào schema RMU (không đọc DL.*, chỉ nhận
tham số ma_site/slug) nên dùng lại được nguyên vẹn cho nhánh Phase 2 — đúng
yêu cầu "không copy autopost.py thành nhánh phần mềm thứ hai".

KHÔNG BAO GIỜ log/in ra API key hay Application Password — mọi hàm ở đây chỉ
đưa 2 giá trị đó vào URL/header của request, không print/log nơi nào khác.
"""
import hashlib
import json
import os
import random
import re
import time
from datetime import datetime, timezone

import profiles as P
import prompts_phase2 as PR
import render_phase2 as R


# ============================================================ AI — mock
def goi_ai_mock(row, mau='chuan', do_tre_gia_lap=0.0):
    """Mô phỏng gọi AI: trả (data: dict, usage: dict) giống hình dạng trả về
    của goi_gemini() thật (data, usage) để chỗ gọi không cần biết đang chạy
    mock hay thật. CHỈ dùng field có thật trong effective_cot_ai(row) —
    không bịa thêm, tự nhiên lọt qua Hard Block như AI thật tuân thủ đúng.

    Gate 2 Task 3: tôn trọng mau — bỏ đúng field theo
    prompts_phase2.MAU_BIEN_THE (không trả huong_dan_chon_html/faq cho
    'ngan_gon'), để HTML cuối cùng khác nhau có chủ đích, không phải giả bộ
    khác tên mẫu suông.
    """
    if do_tre_gia_lap:
        time.sleep(do_tre_gia_lap)

    outline_id = row['outline_id']
    cfg = PR.OUTLINE_NOI_DUNG[outline_id]
    mcfg = PR._mau(mau)
    ten = row.get('ten_goc', '') or 'Sản phẩm'
    thuong_hieu = row.get('thuong_hieu', '')

    manh_dac_diem = []
    for k, nhan in [('thuong_hieu', 'thương hiệu ' + thuong_hieu if thuong_hieu else ''),
                    ('tiet_dien', f'tiết diện {row.get("tiet_dien","")}' if row.get('tiet_dien') else ''),
                    ('cap_dien_ap', f'cấp điện áp {row.get("cap_dien_ap","")}' if row.get('cap_dien_ap') else ''),
                    ('vat_lieu_ruot', f'vật liệu ruột {row.get("vat_lieu_ruot","")}' if row.get('vat_lieu_ruot') else ''),
                    ('cong_suat', f'công suất {row.get("cong_suat","")}' if row.get('cong_suat') else ''),
                    ('quy_cach', f'quy cách {row.get("quy_cach","")}' if row.get('quy_cach') else '')]:
        if nhan:
            manh_dac_diem.append(nhan)
    # ngan_gon: chỉ giữ tối đa 2 đặc điểm đầu, đúng tinh thần súc tích
    if mau == 'ngan_gon':
        manh_dac_diem = manh_dac_diem[:2]

    data = {
        'meta_title': R.rut_gon_an_toan(ten, 60),
        'meta_description': R.rut_gon_an_toan(
            f'{ten} — {cfg["nhan_outline"]} chính hãng'
            + (f', {thuong_hieu}' if thuong_hieu else '')
            + '. Liên hệ để được tư vấn và báo giá.', 160),
        'intro_html': f'<p>{ten} là {cfg["nhan_outline"].lower()} '
                      f'{"của " + thuong_hieu if thuong_hieu else "chính hãng"}.</p>',
        'dac_diem_html': ('<p>Sản phẩm có ' + ', '.join(manh_dac_diem) + '.</p>'
                          if manh_dac_diem else '<p>Thông tin chi tiết vui lòng liên hệ tư vấn.</p>'),
        'ung_dung_html': f'<p>Phù hợp ứng dụng trong hệ thống điện liên quan đến '
                         f'{cfg["nhan_outline"].lower()}.</p>',
    }
    if 'huong_dan_chon_html' not in mcfg['bo_qua_section']:
        data['huong_dan_chon_html'] = ('<p>Liên hệ đội ngũ kỹ thuật để được tư vấn lựa chọn phù hợp '
                                       'với nhu cầu thực tế.</p>')
    if cfg['co_faq'] and not mcfg['bo_qua_faq']:
        # Task 1 (Ver 3.6): dùng NGUYÊN tên sản phẩm ở FAQ thay vì cắt —
        # cách work order gợi ý, né hẳn rủi ro cắt giữa token thay vì phải
        # tính lại giới hạn an toàn cho câu hỏi ngắn.
        data['faq'] = [{'q': f'{ten} có sẵn hàng không?',
                        'a': 'Vui lòng liên hệ để kiểm tra tồn kho và thời gian giao hàng.'}]

    usage = {'input_tokens': len(PR.nguoi_dung(row, outline_id, mau=mau)) // 4,
             'output_tokens': sum(len(str(v)) for v in data.values()) // 4,
             'mock': True}
    return data, usage


# ============================================================ WordPress — mock
_WP_MOCK_DB = {}  # tiến trình hiện tại, KHÔNG lưu đĩa — chỉ để mô phỏng nội bộ 1 phiên chạy


def dang_wp_mock(site, dataset_id, record_id, mau, title, slug, html_content):
    """Mô phỏng POST /wp/v2/posts — trả (wp_id, url) ổn định theo
    (dataset_id, record_id, site, mau): gọi lại nhiều lần với đúng khoá này
    trả lại CÙNG wp_id (giống hành vi 'cập nhật bài đã có' của dang_wp() thật
    — không đẻ bài mới mỗi lần chạy lại)."""
    khoa = (dataset_id, record_id, site, mau)
    if khoa in _WP_MOCK_DB:
        wp_id = _WP_MOCK_DB[khoa]
    else:
        wp_id = str(1000 + len(_WP_MOCK_DB) + 1)
        _WP_MOCK_DB[khoa] = wp_id
    url = f'https://{site}.mock/{slug}/'
    return wp_id, url


def reset_wp_mock():
    """Chỉ dùng cho test — xoá sạch trạng thái mock giữa các lần test độc lập."""
    _WP_MOCK_DB.clear()


# ============================================================ luồng 1 record (mock, đủ bước)
def sinh_va_dang_mock(con, dataset_id, record_id, site, site_cfg, mau='chuan'):
    """1 hàm gói trọn luồng cho 1 (record, site, mẫu): lấy record từ DB ->
    prompt -> AI mock -> render HTML -> sanitize (đã nằm trong render) ->
    Hard Block -> đăng WP mock -> ghi DB. Dùng cho Integration Test (T2-10)
    và cho UI (giao-dien.py gọi hàm này ở tab 'Chạy' khi chưa bật AI thật).
    """
    import db_phase2 as DB

    row = DB.lay_san_pham(con, dataset_id, record_id)
    if row is None:
        raise ValueError(f'Không tìm thấy record {record_id} trong dataset {dataset_id}')
    row = R.bo_sung_may_tuong_thich(row)

    DB.upsert_bai_viet_khoi_tao(con, dataset_id, record_id, site, mau)
    try:
        ai_data, usage = goi_ai_mock(row, mau=mau)
        bai = R.dung_bai_html(row, ai_data, site_cfg, mau=mau)

        # Ver 3.5 — GỘP Hard Block: dùng ĐÚNG kiem_tra_bia_toan_bo() (định
        # nghĩa bên dưới), CÙNG hàm luồng thật (_v3_viec_dang_draft_that ở
        # giao-dien.py) đang gọi. Trước đây Mock tự kiểm 1 đoạn RIÊNG (chỉ
        # 4 field văn xuôi + faq.a, THIẾU meta_title/meta_description/faq.q)
        # -> Mock/Preview có thể báo xanh dù dữ liệu bịa vẫn còn trong
        # meta_title/meta_description/faq.q, sang Real mới bị chặn — đúng lỗ
        # hổng GPT phát hiện bằng cách tiêm IP65 vào meta_title. Xoá hẳn
        # đoạn kiểm riêng, không giữ 2 đường logic cùng làm 1 việc.
        ai_data, vi_pham, flags = _xu_ly_vi_pham_phu(ai_data, row)
        if vi_pham:
            chi_tiet = '; '.join(f'{f}: {v}' for f, v in vi_pham.items())
            DB.cap_nhat_bai_viet(con, dataset_id, record_id, site, mau,
                                 trang_thai='loi', loi=f'Hard Block chặn: {chi_tiet}')
            return {'ok': False, 'loi': f'Hard Block chặn: {chi_tiet}'}
        # Nếu fallback meta có hiệu lực, render lại bằng data đã sửa.
        if flags:
            bai = R.dung_bai_html(row, ai_data, site_cfg, mau=mau)

        wp_id, url = dang_wp_mock(site, dataset_id, record_id, mau, bai['title'], bai['slug'], bai['html'])
        ngay = datetime.now(timezone.utc).isoformat()
        # Ver 4.3 production hotfix: Mock vẫn ghi nội dung/trạng thái để Dashboard
        # và regression cũ hoạt động, nhưng TUYỆT ĐỐI không ghi wp_id/wp_url giả
        # vào state mà đường WordPress thật sẽ đọc. Real thấy wp_id=NULL -> CREATE.
        DB.cap_nhat_bai_viet(con, dataset_id, record_id, site, mau,
                             slug=bai['slug'], title=bai['title'],
                             meta_description=bai['meta_description'], html=bai['html'],
                             trang_thai='da_dang', loi=flags.get('canh_bao_meta', ''),
                             wp_id=None, wp_url=None, ngay_dang=ngay)
        return {'ok': True, 'wp_id': wp_id, 'wp_url': url, 'usage': usage}
    except Exception as e:
        DB.cap_nhat_bai_viet(con, dataset_id, record_id, site, mau,
                             trang_thai='loi', loi=str(e))
        return {'ok': False, 'loi': str(e)}


# ============================================================ THẬT — Gate "Draft thật"
# Ver 3 chỉ quản lý 1 website — khoá cố định 'website' (cauhinh.MA_SITE_VER3),
# khớp namespace autopost.thong_tin_wp()/_auth(): WP_WEBSITE_URL/_USER/_APP_PW.

GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta'


def _sang_gemini_schema(schema_don_gian):
    """Ver 4.1 — chuyển schema đơn giản (prompts_phase2._json_schema(), dạng
    {field: 'string'} hoặc {field: [{'q':'string','a':'string'}]}) sang đúng
    định dạng responseSchema của Gemini (OpenAPI subset: type/properties).

    Lý do thêm: log thật (26/07) cho thấy 6/10 batch thật lỗi "JSON hỏng,
    thường do bài quá dài bị cắt giữa chừng" dù maxOutputTokens=8192 đủ rộng
    — nghi vấn hàng đầu là request trước đó CHƯA ép Gemini theo đúng schema
    (chỉ có responseMimeType='application/json', không có responseSchema),
    khiến mô hình tự do hơn về cấu trúc, dễ lệch. Thêm responseSchema là
    cách rẻ nhất, đúng API, không phải đoán mò."""
    thuoc_tinh = {}
    bat_buoc = []
    for k, v in schema_don_gian.items():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            thuoc_tinh_con = {ik: {'type': 'STRING'} for ik in v[0].keys()}
            thuoc_tinh[k] = {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'properties': thuoc_tinh_con}}
            # faq: mảng có thể rỗng -> KHÔNG đưa vào required
        else:
            thuoc_tinh[k] = {'type': 'STRING'}
            bat_buoc.append(k)
    return {'type': 'OBJECT', 'properties': thuoc_tinh, 'required': bat_buoc}


# Ver 5.6 — timeout gọi Gemini: 45s -> 20s. Đo trên batch thật: mỗi SKU mất
# ~100s CHỈ để chờ 2 lần timeout của cặp key/model chết trước khi tới cặp
# sống. Gemini trả bài đạt trong khoảng 6-12s; 45s không cứu được request
# nào mà chỉ kéo dài thời gian chết. 20s vẫn dư gấp đôi biên an toàn.
# Đặt thành HẰNG SỐ để UI và adapter không lệch nhau (đúng bài học phien_ban).
TIMEOUT_GEMINI = 20


def goi_ai_that(row, mau, model, site_cfg=None, timeout=TIMEOUT_GEMINI, api_key=None):
    """Gọi Gemini THẬT cho ĐÚNG 1 record (Task 2.2 — không batch trong Gate
    này). Tái sử dụng autopost.go_json()/doc_429() (parse & xử lý lỗi 429,
    đã chạy thật trong RMU) qua import — không copy logic đó, chỉ không gọi
    thẳng autopost.goi_gemini() vì hàm đó tự dựng prompt theo
    dung_system()/dung_prompt() của nhánh RMU (prompts.py), không phải
    prompts_phase2.xay_prompt(). Cùng 1 kiểu retry/xử lý lỗi, khác nguồn prompt.

    Ver 4.7 — api_key: nếu truyền (không None), dùng ĐÚNG giá trị này thay
    vì đọc GOOGLE_API_KEY từ env — phục vụ goi_ai_co_du_phong() thử nhiều
    API key khác nhau mà KHÔNG cần đổi cấu hình toàn cục giữa các lần thử
    (đổi env giữa chừng 1 batch đang chạy nguy hiểm — nhiều luồng có thể
    đọc nhầm key của nhau). Không truyền (mặc định None) -> hành vi y hệt
    trước giờ, đọc từ env.

    Trả dict: {'ok': True, 'data': {...}, 'usage': {...}} hoặc
              {'ok': False, 'loi': '...'}
    KHÔNG BAO GIỜ log/in ra API key.
    """
    import requests
    import autopost as A
    import prompts_phase2 as PR

    key = (api_key if api_key is not None else os.environ.get('GOOGLE_API_KEY', '')).strip()
    if not key:
        return {'ok': False, 'loi': 'Chưa có GOOGLE_API_KEY — nhập ở tab "3. Cấu hình".'}
    if not model:
        return {'ok': False, 'loi': 'Chưa chọn model — bấm "Kiểm tra API key và model" ở tab "3. Cấu hình".'}

    he_thong, nguoi_dung, schema_don_gian = PR.xay_prompt(row, site_cfg, mau=mau)
    gs = _sang_gemini_schema(schema_don_gian)   # tính 1 lần, dùng cho cả request lẫn validate sau
    body = {
        'system_instruction': {'parts': [{'text': he_thong}]},
        'contents': [{'role': 'user', 'parts': [{'text': nguoi_dung}]}],
        'generationConfig': {'temperature': 0.6, 'maxOutputTokens': 48000,
                             'responseMimeType': 'application/json',
                             'responseSchema': gs,
                             # Ver 5.0 — VÁ LỖI THẬT (log production 30/07/2026, Thịnh
                             # gửi): model Gemini 3.x có "suy nghĩ ngầm" (thinking)
                             # BẬT MẶC ĐỊNH, KHÔNG giới hạn — phần suy nghĩ này tính
                             # CHUNG vào maxOutputTokens với câu trả lời JSON thật. Nếu
                             # không giới hạn, model tự do dùng bao nhiêu token tuỳ ý
                             # cho suy nghĩ, có thể ăn gần hết ngân sách, cắt cụt phần
                             # JSON trả lời -> finishReason=MAX_TOKENS ("Bài bị cắt vì
                             # vượt giới hạn token"). Ver 4.9.9 thêm Delta Context (yêu
                             # cầu AI SO SÁNH/suy luận, phức tạp hơn mô tả đơn thuần)
                             # nhiều khả năng khiến model "nghĩ" nhiều hơn, tăng tần
                             # suất bị cắt đúng lúc bản đó ra mắt.
                             #
                             # Vá theo cả 2 hướng cùng lúc (Thịnh chọn): (1) trần cứng
                             # cho thinking (6000 token — đủ để model suy luận delta
                             # context, không ăn hết ngân sách), (2) nâng
                             # maxOutputTokens 24000->48000 (model hỗ trợ tới 65536
                             # theo log kiểm tra model — 48000 chừa dư khoảng cách an
                             # toàn, không sát trần tối đa).
                             'thinkingConfig': {'thinkingBudget': 6000}},
    }
    url = f'{GEMINI_URL}/models/{model}:generateContent?key={key}'

    for lan in range(3):
        try:
            r = requests.post(url, json=body, timeout=timeout)
        except requests.exceptions.Timeout:
            # Ver 4.3 production hotfix: không giữ 1 cặp key/model chết tới 3 x timeout.
            # Fallback matrix ở goi_ai_co_du_phong() mới là nơi retry đúng cặp khác.
            return {'ok': False, 'loi': f'Timeout khi gọi Gemini sau {timeout}s — chuyển ngay sang cặp key/model kế tiếp.'}
        except requests.exceptions.RequestException as e:
            return {'ok': False, 'loi': f'Lỗi mạng khi gọi Gemini: {type(e).__name__}: {e}'}

        if r.status_code == 429:
            loai, msg, cho_google = A.doc_429(r)
            if loai == 'NGAY':
                return {'ok': False,
                       'loi': f'Hết lượt miễn phí trong ngày của model "{model}". '
                              f'Google nói: {msg}. Đổi model khác hoặc chờ reset (~14-15h VN).'}
            # Ver 4.3: rate-limit ngắn cũng nhường ngay cho cặp dự phòng; không ngủ
            # 20s rồi thử lại cùng cặp trong lúc đang render hàng loạt.
            return {'ok': False, 'loi': f'Bị chặn tốc độ (429): {msg} — chuyển cặp key/model kế tiếp.'}

        if r.status_code == 401 or r.status_code == 403:
            return {'ok': False, 'loi': f'API key bị từ chối (HTTP {r.status_code}). Kiểm tra lại key.'}
        if r.status_code == 404:
            return {'ok': False, 'loi': f'Model "{model}" không tồn tại hoặc không gọi được (HTTP 404). '
                                        f'Bấm "Kiểm tra API key và model" để dò lại.'}
        if r.status_code >= 300:
            return {'ok': False, 'loi': f'Gemini trả lỗi HTTP {r.status_code}: {r.text[:300]}'}

        try:
            j = r.json()
        except Exception:
            return {'ok': False, 'loi': 'Phản hồi Gemini không phải JSON hợp lệ.'}

        cands = j.get('candidates') or []
        if not cands:
            ly_do = j.get('promptFeedback', {}).get('blockReason', '')
            return {'ok': False, 'loi': 'Gemini không trả nội dung nào (candidates rỗng).'
                                        + (f' Lý do: {ly_do}' if ly_do else '')}
        c0 = cands[0]
        if c0.get('finishReason') in ('SAFETY', 'RECITATION', 'BLOCKLIST'):
            return {'ok': False, 'loi': f'Gemini chặn nội dung này (lý do {c0["finishReason"]}).'}
        if c0.get('finishReason') == 'MAX_TOKENS':
            return {'ok': False, 'loi': 'Bài bị cắt vì vượt giới hạn token — thử model khác hoặc rút gọn prompt.'}

        txt = ''.join(p.get('text', '') for p in c0.get('content', {}).get('parts', []))
        try:
            data = A.go_json(txt)   # tái sử dụng parser JSON đã chạy thật ở RMU (bóc ```json, cắt lề)
        except RuntimeError as e:
            # Ver 4.1 — thêm finishReason vào lỗi để chẩn đoán được có phải
            # do bị cắt (MAX_TOKENS đã bắt riêng ở trên rồi, nên nếu tới đây
            # vẫn lỗi parse thì finishReason thường là STOP — nghĩa là
            # Gemini TỰ NHẬN đã viết xong nhưng JSON vẫn sai cấu trúc, khác
            # hẳn nguyên nhân "bị cắt". Ghi rõ để không đoán nhầm hướng vá.
            return {'ok': False,
                   'loi': f'{e} (finishReason={c0.get("finishReason", "?")})'}

        um = j.get('usageMetadata', {})

        # Ver 4.6 — JSON parse được KHÔNG có nghĩa là đủ nội dung để đăng.
        # Trước đây nếu Gemini trả JSON hợp lệ nhưng THIẾU field bắt buộc
        # (VD thiếu hẳn dac_diem_html), hàm vẫn trả ok=True — bài ra mỏng
        # hơn nhưng không ai biết. Giờ kiểm đủ field bắt buộc theo ĐÚNG
        # schema đã gửi Gemini (gs['required'] — tái dùng, không tính lại),
        # thiếu field nào (rỗng/không có) thì FAILED thẳng, không âm thầm
        # đăng bài cụt.
        thieu = [f for f in gs['required'] if not str(data.get(f, '')).strip()]
        if thieu:
            return {'ok': False,
                   'loi': f'Gemini trả JSON hợp lệ nhưng THIẾU field bắt buộc: {", ".join(thieu)} '
                          f'(finishReason={c0.get("finishReason", "?")}) — không đăng bài thiếu nội dung.'}

        return {'ok': True, 'data': data,
               'usage': {'input_tokens': um.get('promptTokenCount', 0),
                         'output_tokens': um.get('candidatesTokenCount', 0)}}

    return {'ok': False, 'loi': 'Không gọi được Gemini sau nhiều lần thử.'}


_LAP_KY_TU_RE = re.compile(r'(.)\1{9,}')   # 1 ký tự lặp liên tiếp >=10 lần — dấu hiệu output hỏng
_LAP_TU_RE = re.compile(r'\b(\w+)\b(?:\s+\1\b){4,}', re.IGNORECASE)   # 1 từ lặp liên tiếp >=5 lần
GIOI_HAN_DO_DAI_KIEM_TRA = {
    'meta_title': (5, 200), 'meta_description': (10, 400),
    'faq_q': (5, 150), 'faq_a': (5, 500),
}


def kiem_tra_chat_luong_text(gia_tri, nhan_gioi_han=None):
    """Ver 4.6 — chặn chuỗi rác lọt vào bài đăng: quá ngắn/quá dài bất
    thường, ký tự lặp liên tiếp (VD 'aaaaaaaaaa...'), từ lặp liên tục
    nhiều lần (VD 'tốt tốt tốt tốt tốt...') — dấu hiệu output AI hỏng mà
    Hard Block chống-bịa-số (kiem_tra_bia) không bắt được vì đây không
    phải số liệu, là vấn đề CHẤT LƯỢNG văn bản.

    `nhan_gioi_han`: khoá trong GIOI_HAN_DO_DAI_KIEM_TRA để áp giới hạn độ
    dài riêng (VD 'faq_q'). None -> chỉ kiểm lặp ký tự/từ, không kiểm độ
    dài (dùng cho field văn xuôi dài như dac_diem_html vốn không có giới
    hạn cố định).

    Trả list lỗi dạng chuỗi mô tả (rỗng = sạch)."""
    loi = []
    gia_tri = (gia_tri or '').strip()
    if nhan_gioi_han and nhan_gioi_han in GIOI_HAN_DO_DAI_KIEM_TRA:
        toi_thieu, toi_da = GIOI_HAN_DO_DAI_KIEM_TRA[nhan_gioi_han]
        if not (toi_thieu <= len(gia_tri) <= toi_da):
            loi.append(f'độ dài bất thường ({len(gia_tri)} ký tự, hợp lệ {toi_thieu}-{toi_da})')
    if _LAP_KY_TU_RE.search(gia_tri):
        loi.append('có ký tự lặp liên tiếp bất thường (nghi output hỏng)')
    if _LAP_TU_RE.search(gia_tri):
        loi.append('có từ lặp liên tục bất thường (nghi output hỏng)')
    return loi


_META_FIELDS_HARD_BLOCK = {'meta_title', 'meta_description'}


def _meta_rut_gon_an_toan(row):
    """Meta code-only, không số kỹ thuật, dùng khi CHỈ meta bị Hard Block.

    Không để meta trống. Không gọi AI lần nữa. Mục tiêu duy nhất là cho Draft
    sống để Thịnh sửa sau, trong khi thân bài vẫn giữ invariant Hard Block cũ.
    """
    brand = re.sub(r'\s+', ' ', str(row.get('thuong_hieu') or '')).strip()
    if row.get('outline_id') == 'outline_vo_may_bien_ap':
        goc = 'Vỏ mạ kẽm nhúng nóng'
    elif row.get('outline_id') == 'outline_phu_kien':
        goc = 'Phụ kiện thiết bị điện'
    else:
        goc = 'Sản phẩm thiết bị điện'
    if brand:
        goc = f'{goc} {brand}'
    return {
        'meta_title': goc,
        'meta_description': f'{goc}. Liên hệ báo giá và tư vấn kỹ thuật.'
    }


def _xu_ly_vi_pham_phu(ai_data, row):
    """Giữ Hard Block thân bài; hạ cấp FAQ và META thành fallback có cảnh báo.

    Trả (data_sach, vi_pham_con_lai, flags). Nếu vi_pham_con_lai còn field
    ngoài meta/FAQ thì caller PHẢI chặn cả bài như trước.
    """
    du_lieu = dict(ai_data or {})
    flags = {}
    vi_pham = kiem_tra_bia_toan_bo(du_lieu, row)
    if not vi_pham:
        return du_lieu, {}, flags

    # Giữ hành vi cũ: FAQ là phần phụ, bỏ cả FAQ rồi kiểm lại.
    if du_lieu.get('faq') and any(k.startswith('faq[') for k in vi_pham):
        du_lieu['faq'] = []
        flags['faq_bi_bo'] = True
        vi_pham = kiem_tra_bia_toan_bo(du_lieu, row)

    # LUẬT 4.3.1: chỉ khi phần còn lại TOÀN META mới được fallback.
    if vi_pham and all(k in _META_FIELDS_HARD_BLOCK for k in vi_pham):
        chi_tiet = '; '.join(f'{f}: {v}' for f, v in vi_pham.items())
        du_lieu.update(_meta_rut_gon_an_toan(row))
        vi_pham_sau = kiem_tra_bia_toan_bo(du_lieu, row)
        if not vi_pham_sau:
            flags['meta_bi_rut_gon'] = True
            flags['canh_bao_meta'] = f'CẢNH BÁO META: Hard Block chặn {chi_tiet}; đã dùng meta rút gọn an toàn.'
            return du_lieu, {}, flags
        vi_pham = vi_pham_sau

    return du_lieu, vi_pham, flags


def goi_ai_co_du_phong(row, mau, danh_sach_thu, site_cfg=None, timeout=TIMEOUT_GEMINI):
    """Ver 4.7 — thử LẦN LƯỢT nhiều cặp (api_key, model) cho ĐÚNG 1 record,
    dừng ở lần đầu tiên thành công. `danh_sach_thu`: list[(api_key, model)]
    — phần tử đầu là cặp CHÍNH (đã cấu hình ở tab Cấu hình), các phần tử
    sau là dự phòng (đổi model trước — rẻ, không tốn quota key khác — rồi
    mới đổi key).

    "Thành công" = CẢ 2 điều kiện: (1) goi_ai_that() trả ok=True, (2)
    kiem_tra_bia_toan_bo() trên kết quả đó KHÔNG có vi phạm NGOÀI FAQ. Nếu
    (2) chặn nội dung CỐT LÕI (VD dac_diem_html) — vẫn coi là thất bại của
    cặp này, thử cặp tiếp theo. Ver 4.9 — nếu vi phạm CHỈ nằm trong FAQ
    (field phụ theo outline), tự động bỏ FAQ và coi là thành công (xem
    'faq_bi_bo' trong kết quả trả về) — không đổi cặp key/model chỉ vì 1
    field phụ.

    Ver 5.3 — VÁ: Hard Block chặn nội dung CỐT LÕI giờ THẤT BẠI NGAY (không
    thử thêm cặp key/model khác cho SẢN PHẨM NÀY) — khác hẳn lỗi 429/mạng
    (vẫn thử tiếp như cũ). Lý do: đổi model không chắc sửa được lỗi bịa
    (thường do data mỏng, không phải lỗi ngẫu nhiên riêng 1 model) — tốn
    quota cho 1 sản phẩm cứng đầu trong khi dùng cho sản phẩm MỚI hiệu quả
    hơn. Sản phẩm lỗi không mất, batch sau tự thử lại (chỉ bỏ qua bài
    'da_dang', không bỏ qua bài 'loi').

    Trả (kq_ai, vi_pham): kq_ai['ok']=True kèm 'da_thu' (thử tới cặp thứ
    mấy mới thành công) và vi_pham={} nếu thành công; nếu hết danh sách mà
    vẫn lỗi, trả kq_ai/vi_pham của LẦN THỬ CUỐI CÙNG (để caller ghi log
    đúng lỗi gần nhất, không mất thông tin). Ver 4.8 — thêm 'lich_su': list
    mô tả ngắn từng lần thử (model + tóm tắt lỗi/thành công), để caller ghi
    log đủ thấy TẤT CẢ các lần đã thử, không chỉ lần cuối — cần thiết để
    chẩn đoán case dự phòng KHÔNG cứu được (VD cả 2 cặp cùng hết quota)."""
    # Ver 4.3.1 — runtime enrichment để DB cũ KHÔNG cần re-import: field
    # may_tuong_thich được bóc lại từ Tên hàng trước cả prompt lẫn Hard Block.
    row = R.bo_sung_may_tuong_thich(row)
    kq_cuoi, vi_pham_cuoi = {'ok': False, 'loi': 'Danh sách key/model dự phòng rỗng.'}, {}
    lich_su = []
    timing_pairs = []
    for i, (api_key, model) in enumerate(list(danh_sach_thu), 1):
        t_cap = time.perf_counter()
        kq = goi_ai_that(row, mau, model, site_cfg=site_cfg, timeout=timeout, api_key=api_key)
        mat = time.perf_counter() - t_cap
        timing_pairs.append({'thu': i, 'model': model, 'giay': mat, 'ok': bool(kq.get('ok')),
                             'loi': '' if kq.get('ok') else str(kq.get('loi', ''))[:180]})
        if not kq['ok']:
            lich_su.append(f'#{i} model={model}: {kq["loi"]}')
            kq_cuoi, vi_pham_cuoi = kq, {}
            continue
        du_lieu_sach, vi_pham, flags = _xu_ly_vi_pham_phu(kq['data'], row)
        if vi_pham:
            thong_diep = '; '.join(f'{f}: {v}' for f, v in vi_pham.items())
            lich_su.append(f'#{i} model={model}: Hard Block chặn: {thong_diep}')
            kq_cuoi = {'ok': False, 'loi': f'Hard Block chặn (thử #{i}/{len(danh_sach_thu)}, model={model}): {thong_diep}'}
            vi_pham_cuoi = vi_pham
            # Thân bài/cốt lõi vẫn FAIL NGAY như Ver 5.3. Không nới Hard Block.
            kq_cuoi['da_thu'] = i
            kq_cuoi['lich_su'] = lich_su
            kq_cuoi['timing_pairs'] = timing_pairs
            return kq_cuoi, vi_pham_cuoi

        if du_lieu_sach is not kq.get('data') or flags:
            kq = dict(kq)
            kq['data'] = du_lieu_sach
            kq.update(flags)
            if flags.get('faq_bi_bo'):
                lich_su.append(f'#{i} model={model}: FAQ bị bỏ do Hard Block/quality')
            if flags.get('meta_bi_rut_gon'):
                lich_su.append(f'#{i} model={model}: META bị rút gọn an toàn, bài vẫn được phép Draft')

        kq['da_thu'] = i
        kq['model_da_dung'] = model
        kq['cap_da_dung'] = i
        kq['timing_pairs'] = timing_pairs
        kq['lich_su'] = lich_su + [f'#{i} model={model}: THÀNH CÔNG']
        if i > 1 and isinstance(danh_sach_thu, list):
            cap_ok = danh_sach_thu.pop(i - 1)
            danh_sach_thu.insert(0, cap_ok)
        return kq, {}
    kq_cuoi = dict(kq_cuoi)
    kq_cuoi['da_thu'] = len(danh_sach_thu)
    kq_cuoi['lich_su'] = lich_su
    kq_cuoi['timing_pairs'] = timing_pairs
    return kq_cuoi, vi_pham_cuoi


def kiem_tra_bia_toan_bo(ai_data, row):
    """Task 2.3 — Hard Block E2E: kiểm TOÀN BỘ field AI trả, không chỉ 4
    field văn xuôi như luồng mock (Round 2/Gate 2) — thêm meta_title,
    meta_description, faq[].q, faq[].a. Dùng CHUNG 1 hàm chấm
    (render_phase2.kiem_tra_bia, đã có Composite Hard Block + cụm mở rộng từ
    Gate 2, không viết lại). Trả dict {field: [chuỗi bị chặn,...]} — RỖNG
    nghĩa là an toàn.

    Ver 4.6 — thêm kiểm CHẤT LƯỢNG văn bản (kiem_tra_chat_luong_text) song
    song với Hard Block chống bịa số — 2 loại lỗi khác nhau, gộp chung vào
    CÙNG dict trả về để chỉ cần 1 điểm kiểm tra duy nhất (giao-dien.py
    không cần sửa gì thêm, vi_pham khác rỗng là chặn y hệt trước giờ)."""
    import render_phase2 as R
    vi_pham = {}
    for field in ('meta_title', 'meta_description', 'intro_html', 'dac_diem_html',
                 'ung_dung_html', 'huong_dan_chon_html'):
        gia_tri = ai_data.get(field, '')
        if gia_tri:
            chan = R.kiem_tra_bia(gia_tri, row)
            nhan_gh = field if field in GIOI_HAN_DO_DAI_KIEM_TRA else None
            loi_chat_luong = kiem_tra_chat_luong_text(gia_tri, nhan_gh)
            if chan or loi_chat_luong:
                vi_pham[field] = chan + loi_chat_luong
    for i, cau in enumerate(ai_data.get('faq') or []):
        for phan, nhan_gh in (('q', 'faq_q'), ('a', 'faq_a')):
            gia_tri = cau.get(phan, '')
            if gia_tri:
                chan = R.kiem_tra_bia(gia_tri, row)
                loi_chat_luong = kiem_tra_chat_luong_text(gia_tri, nhan_gh)
                if chan or loi_chat_luong:
                    vi_pham[f'faq[{i}].{phan}'] = chan + loi_chat_luong
    return vi_pham


_KHONG_TRUYEN = object()   # sentinel: phân biệt "không truyền tham số" với "truyền None có ý nghĩa"


def dang_woo_that(dataset_id, record_id, site, mau, title, slug, content, excerpt,
                  ma_hang=None, da_co_woo_id=_KHONG_TRUYEN,
                  danh_muc=None, meta_rank_math=None, schema=None, faq_schema=None):
    """Ver 4.6 — Save Draft THẬT vào WooCommerce (`/wc/v3/products`) thay vì
    WordPress Post (`/wp/v2/posts`) — dùng cho site chạy Flatsome+Woo (VD
    maybienapvn.vn). Cùng auth Application Password (Basic Auth) như
    dang_wp_that() — WooCommerce REST API chấp nhận auth này nếu tài
    khoản có quyền `manage_woocommerce`, KHÔNG cần Consumer Key/Secret
    riêng, KHÔNG thêm cấu hình mới cho Thịnh.

    status LUÔN ép cứng 'draft', type LUÔN ép cứng 'simple' — không đọc
    tham số ngoài, không có đường nào lỡ Publish/đổi loại sản phẩm.

    Idempotent theo SKU (mã hàng) — đáng tin hơn slug vì SKU là mã hàng
    thật, duy nhất theo thiết kế MASTER; dự phòng theo slug nếu record
    không có mã hàng. Giá (regular_price/sale_price) KHÔNG được set —
    đúng mô hình 'Liên hệ báo giá' đã chốt, không có price/cart/checkout
    (Thịnh đã ẩn các chức năng này trên site, đây chỉ là đổi NƠI đăng).

    Cùng kỷ luật chống đăng trùng học được từ dang_wp_that() (Ver 3.7.1):
    lỗi mạng/timeout giữa chừng KHÔNG retry mù — dò lại SKU trước khi thử
    lại; nếu lần đầu (chưa biết ID) mà CẢ POST lẫn bước dò lại đều lỗi
    mạng, dừng hẳn thay vì liều tạo sản phẩm mới (tránh đẻ trùng SKU).

    Trả dict: {'ok':True,'wp_id':...,'wp_url':...,'thoi_luong_giay':...}
              hoặc {'ok':False,'loi':...,'thoi_luong_giay':...}
    (Giữ tên field 'wp_id'/'wp_url' — KHÔNG đổi tên — để tái dùng nguyên
    db_phase2.cap_nhat_bai_viet()/cap_nhat_job() không cần sửa gì thêm.)
    """
    import requests
    import autopost as A
    import db_phase2 as DB
    import cauhinh as C

    t0 = time.time()
    wc = C.doc_website()
    if not wc:
        return {'ok': False, 'loi': 'Chưa cấu hình website.', 'thoi_luong_giay': 0}

    try:
        url, auth = A._auth(C.MA_SITE_VER3)
    except SystemExit as e:
        return {'ok': False, 'loi': str(e), 'thoi_luong_giay': time.time() - t0}

    goi = {'name': title, 'type': 'simple', 'status': 'draft',
          'description': content, 'short_description': excerpt}
    if ma_hang:
        goi['sku'] = ma_hang

    # Ver 3.6.4 — DANH MỤC + META RANK MATH + SCHEMA.
    # Trước đây payload chỉ có name/type/status/description/short_description/sku.
    #  - Không gửi categories -> sản phẩm TẠO MỚI rơi vào "Chưa phân loại".
    #    (Bài đã có không bị ảnh hưởng: Woo giữ nguyên danh mục khi PUT
    #    không kèm trường này — nên 245 bài đã sửa tay vẫn an toàn.)
    #  - Không gửi meta Rank Math -> Focus Keyword trống, Rank Math không
    #    chấm được gì, điểm SEO đứng ở 15/100.
    #  - render_phase2 sinh schema/faq_schema đàng hoàng nhưng KHÔNG AI GỬI
    #    ĐI — 245 bài đang không có Product Schema lẫn FAQPage Schema.
    if danh_muc:
        # Ver 3.8 Gate 7 — Woo product payload chỉ nhận category assignment
        # ổn định bằng ID. Tên chỉ dùng để tra cứu; KHÔNG tự tạo category mới.
        ds_cat = []
        for ten_cat in [str(t).strip() for t in danh_muc if str(t).strip()]:
            try:
                r_cat = requests.get(
                    f'{url}/wp-json/wc/v3/products/categories',
                    auth=auth, headers=A.HEADERS,
                    params={'search': ten_cat, 'per_page': 100}, timeout=30)
            except requests.exceptions.RequestException as e:
                return {'ok': False, 'loi': f'Không tra được Woo category "{ten_cat}": {type(e).__name__}: {e}',
                        'thoi_luong_giay': time.time() - t0}
            if r_cat.status_code >= 300:
                return {'ok': False, 'loi': f'Không tra được Woo category "{ten_cat}" (HTTP {r_cat.status_code}).',
                        'thoi_luong_giay': time.time() - t0}
            try:
                cat_rows = r_cat.json()
            except Exception:
                return {'ok': False, 'loi': f'Woo category "{ten_cat}" trả JSON không hợp lệ.',
                        'thoi_luong_giay': time.time() - t0}
            cat = next((x for x in cat_rows
                        if str(x.get('name', '')).strip().casefold() == ten_cat.casefold()
                        and x.get('id')), None)
            if not cat:
                return {'ok': False,
                        'loi': f'Không tìm thấy Woo category đúng tên "{ten_cat}" — tool không tự tạo category.',
                        'thoi_luong_giay': time.time() - t0}
            ds_cat.append({'id': int(cat['id'])})
        if ds_cat:
            goi['categories'] = ds_cat

    meta = []
    for k, v in (meta_rank_math or {}).items():
        if v:
            meta.append({'key': k, 'value': v})
    if schema:
        # JSON-LD đi qua meta riêng, TUYỆT ĐỐI không nhét vào description:
        # WordPress lọc thẻ <script> nhưng GIỮ text bên trong -> nguyên khối
        # JSON hiện thành chữ trên trang. Đã xảy ra thật.
        meta.append({'key': '_snl_schema_jsonld', 'value': schema})
    if faq_schema:
        # Ver 4.2: renderer đã sinh FAQPage schema từ trước nhưng production
        # không delivery. Giữ Product key cũ, thêm key riêng để WPCode in ra.
        meta.append({'key': '_snl_faq_schema_jsonld', 'value': faq_schema})
    if meta:
        goi['meta_data'] = meta

    con = DB.ket_noi()
    try:
        if da_co_woo_id is _KHONG_TRUYEN:
            bv = DB.lay_bai_viet(con, dataset_id, record_id, site, mau)
            da_co = bv['wp_id'] if bv and bv.get('wp_id') else None
        else:
            da_co = da_co_woo_id

        if da_co is None:
            try:
                da_co = (A.tim_san_pham_woo_theo_sku(C.MA_SITE_VER3, ma_hang) if ma_hang
                         else A.tim_san_pham_woo_theo_slug(C.MA_SITE_VER3, slug))
            except Exception as e:
                return {'ok': False, 'loi': f'Không kiểm tra được SKU trước khi đăng: {e}',
                       'thoi_luong_giay': time.time() - t0}

        # Ver 4.4 B1 — site đang noindex và Thịnh chủ động chốt công thức slug
        # mới trước khi index. Vì vậy UPDATE cũng PHẢI gửi slug; nếu không, title
        # đổi nhưng URL vẫn giữ công thức cũ chứa SKU/"chuan". Idempotency vẫn
        # dựa wp_id/SKU như cũ, chỉ payload update có thêm trường slug.
        if slug:
            goi['slug'] = slug

        loi_cuoi = ''
        khong_phuc_hoi_nua = False
        for lan in range(3):
            api = f'{url}/wp-json/wc/v3/products/{da_co}' if da_co else f'{url}/wp-json/wc/v3/products'
            r = None
            try:
                r = requests.post(api, auth=auth, headers=A.HEADERS,
                                  data=json.dumps(goi, ensure_ascii=False).encode('utf-8'),
                                  timeout=90)
            except requests.exceptions.Timeout:
                loi_cuoi = 'Timeout khi gọi WooCommerce'
            except requests.exceptions.RequestException as e:
                loi_cuoi = f'{type(e).__name__}: {e}'

            if r is not None and r.status_code < 300:
                try:
                    j = r.json()
                except Exception:
                    return {'ok': False, 'loi': 'WooCommerce trả 2xx nhưng không phải JSON hợp lệ.',
                           'thoi_luong_giay': time.time() - t0}
                return {'ok': True, 'wp_id': j.get('id'), 'wp_url': j.get('permalink', ''),
                       'thoi_luong_giay': time.time() - t0}

            if r is not None and r.status_code in (401, 403):
                return {'ok': False,
                       'loi': f'Xác thực thất bại (HTTP {r.status_code}) — kiểm tra Application Password '
                              f'có đủ quyền quản lý WooCommerce (manage_woocommerce) không.',
                       'thoi_luong_giay': time.time() - t0}
            if r is not None and 400 <= r.status_code < 500:
                # Ver 4.9 — nguyên nhân gốc THẬT đã xác nhận (không còn đoán
                # mò như Ver 4.8): tài liệu WooCommerce REST API v3 ghi rõ
                # `status` mặc định là 'publish' — tra SKU trước đây bỏ sót
                # sản phẩm draft (chính trạng thái mọi sản phẩm tool này
                # tạo ra). Đã vá tận gốc ở tim_san_pham_woo_theo_sku()
                # (status='any'). Khối này giờ là lớp phòng thủ THỨ 2, chỉ
                # còn xử lý đúng 1 case còn lại: SKU bị giữ bởi sản phẩm
                # NẰM TRONG THÙNG RÁC — 'any' theo đúng ngữ nghĩa WordPress
                # KHÔNG bao gồm trash (hành vi lõi WP, không phải do tool
                # này chọn). Có bằng chứng thật: Thịnh gửi ảnh chụp đúng
                # sản phẩm trùng SKU đang nằm ở post_status=trash.
                #
                # KHÔNG tự ý khôi phục hay xoá vĩnh viễn sản phẩm trong
                # thùng rác — đây là hành động ảnh hưởng dữ liệu, để Thịnh
                # tự quyết. Chỉ báo RÕ RÀNG đang vướng đúng trường hợp gì.
                if da_co is None and ma_hang and not khong_phuc_hoi_nua:
                    khong_phuc_hoi_nua = True
                    try:
                        da_co_khoi_phuc = A.tim_san_pham_woo_theo_sku(C.MA_SITE_VER3, ma_hang)
                    except Exception:
                        da_co_khoi_phuc = None
                    if da_co_khoi_phuc:
                        da_co = da_co_khoi_phuc
                        print(f'   (WooCommerce báo trùng SKU "{ma_hang}" — tra lại tìm thấy sản phẩm '
                             f'ID={da_co}, chuyển sang cập nhật thay vì tạo mới)')
                        continue
                    try:
                        da_co_trong_rac = A.tim_san_pham_woo_theo_sku(C.MA_SITE_VER3, ma_hang, trang_thai='trash')
                    except Exception:
                        da_co_trong_rac = None
                    if da_co_trong_rac:
                        return {'ok': False,
                               'loi': f'SKU "{ma_hang}" đang bị giữ bởi 1 sản phẩm NẰM TRONG THÙNG RÁC '
                                      f'(ID={da_co_trong_rac}) trên WooCommerce — WordPress không coi thùng '
                                      f'rác là "đã xoá hẳn" nên SKU vẫn bị khoá. Cần vào WordPress Admin > '
                                      f'Products > Trash, XOÁ VĨNH VIỄN (Delete Permanently) sản phẩm đó rồi '
                                      f'chạy lại — tool không tự xoá thùng rác.',
                               'thoi_luong_giay': time.time() - t0}
                return {'ok': False, 'loi': f'WooCommerce từ chối (HTTP {r.status_code}): {r.text[:300]}',
                       'thoi_luong_giay': time.time() - t0}

            if lan < 2:
                khong_chac_da_tao = (da_co is None and r is None)
                time.sleep(5)
                try:
                    da_co_kiem_lai = (A.tim_san_pham_woo_theo_sku(C.MA_SITE_VER3, ma_hang) if ma_hang
                                      else A.tim_san_pham_woo_theo_slug(C.MA_SITE_VER3, slug))
                    if da_co_kiem_lai:
                        da_co = da_co_kiem_lai
                except Exception as e:
                    if khong_chac_da_tao:
                        return {'ok': False,
                               'loi': f'Không xác định được sản phẩm đã tạo hay chưa (POST tạo mới lỗi mạng, '
                                      f'sau đó kiểm tra SKU cũng lỗi: {type(e).__name__}: {e}). '
                                      f'KHÔNG thử tạo lại để tránh đăng trùng — chạy lại sau.',
                               'thoi_luong_giay': time.time() - t0}
                    pass

        return {'ok': False, 'loi': f'Đăng WooCommerce thất bại sau 3 lần thử. {loi_cuoi}',
               'thoi_luong_giay': time.time() - t0}
    finally:
        con.close()


def cap_nhat_seo_woo_that(wp_id, title, slug, meta_rank_math, timeout=90):
    """Ver 3.9 C6 — UPDATE metadata-only cho 1 Woo product đã tồn tại.

    Payload cố ý CHỈ có name + slug + meta_data Rank Math. Không nhận content,
    excerpt, category, sku hay schema nên hàm này không có đường ghi đè nội dung
    bài và không gọi AI. Caller phải truyền wp_id đã biết; không tự create.
    """
    import requests
    import autopost as A
    import cauhinh as C

    if not wp_id:
        return {'ok': False, 'loi': 'Thiếu Woo product ID.'}
    try:
        url, auth = A._auth(C.MA_SITE_VER3)
    except SystemExit as e:
        return {'ok': False, 'loi': str(e)}

    meta = [{'key': k, 'value': v} for k, v in (meta_rank_math or {}).items() if v]
    goi = {'name': title, 'slug': slug, 'meta_data': meta}
    api = f'{url}/wp-json/wc/v3/products/{wp_id}'
    try:
        r = requests.post(api, auth=auth, headers=A.HEADERS,
                          data=json.dumps(goi, ensure_ascii=False).encode('utf-8'),
                          timeout=timeout)
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'loi': f'{type(e).__name__}: {e}'}
    if r.status_code >= 300:
        return {'ok': False, 'loi': f'WooCommerce từ chối metadata-only update '
                                      f'(HTTP {r.status_code}): {r.text[:300]}'}
    try:
        j = r.json()
    except Exception:
        return {'ok': False, 'loi': 'WooCommerce trả 2xx nhưng không phải JSON hợp lệ.'}
    return {'ok': True, 'wp_id': j.get('id', wp_id), 'wp_url': j.get('permalink', ''),
            'payload_keys': sorted(goi)}


def kiem_tra_ket_noi_wp():
    """Task 3.2 — xác thực WordPress REST API, KHÔNG tạo bài. Trả
    {'ok':True,'thong_diep':...} hoặc {'ok':False,'loi':...} phân biệt rõ
    HTTP status/auth/timeout/WAF."""
    import requests
    import autopost as A
    import cauhinh as C

    wc = C.doc_website()
    if not wc:
        return {'ok': False, 'loi': 'Chưa cấu hình website — điền đủ URL/Username/Application Password rồi Lưu.'}
    try:
        url, auth = A._auth(C.MA_SITE_VER3)
    except SystemExit as e:
        return {'ok': False, 'loi': str(e)}
    try:
        r = requests.get(f'{url}/wp-json/wp/v2/users/me', auth=auth,
                         headers={'User-Agent': A.UA, 'Accept': 'application/json'}, timeout=20)
    except requests.exceptions.Timeout:
        return {'ok': False, 'loi': 'Timeout khi kết nối WordPress (20s) — kiểm tra URL hoặc mạng.'}
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'loi': f'Lỗi kết nối: {type(e).__name__}: {e}'}

    if r.status_code == 200:
        try:
            j = r.json()
            return {'ok': True, 'thong_diep': f'Kết nối OK — đăng nhập là "{j.get("name", "?")}" '
                                              f'({", ".join(j.get("roles", []))})'}
        except Exception:
            return {'ok': False, 'loi': 'HTTP 200 nhưng phản hồi không phải JSON — có thể bị WAF/CDN chặn.'}
    if r.status_code in (401, 403):
        return {'ok': False, 'loi': f'Xác thực thất bại (HTTP {r.status_code}) — kiểm tra lại '
                                    f'Username/Application Password.'}
    if r.status_code == 404:
        return {'ok': False, 'loi': 'HTTP 404 — kiểm tra lại URL (thiếu /wp-json hay sai domain?).'}
    ct = r.headers.get('Content-Type', '')
    if 'json' not in ct.lower() and r.status_code in (503, 403, 429):
        return {'ok': False, 'loi': f'HTTP {r.status_code}, phản hồi không phải JSON — nhiều khả năng '
                                    f'bị WAF/Cloudflare chặn request.'}
    return {'ok': False, 'loi': f'HTTP {r.status_code}: {r.text[:200]}'}


def dang_wp_that(dataset_id, record_id, site, mau, title, slug, content, excerpt,
                  da_co_wp_id=_KHONG_TRUYEN):
    """Task 3.3 — Save Draft THẬT. status LUÔN ép cứng 'draft' (không đọc
    tham số ngoài — không có đường nào lỡ Publish). Idempotent: tra wp_id đã
    lưu trước, nếu chưa có thì tra theo slug (autopost.tim_bai_theo_slug,
    dùng lại nguyên, không copy). Lỗi mạng/timeout giữa chừng: KHÔNG retry mù
    — dò lại slug trước khi thử lại, để nếu request trước đã thành công phía
    server (chỉ client timeout) thì lần sau PUT cập nhật đúng bài đó, không
    tạo bài mới đẻ slug-2.

    Ver 3.9 — da_co_wp_id: nếu được TRUYỀN (kể cả None), dùng đúng giá trị
    này làm điểm bắt đầu, KHÔNG tự tra bai_viet_phase2. Lý do: bảng đó khoá
    theo (dataset_id, record_id, site, mau) — không phân biệt được nhiều
    Article Job của CÙNG record/site/mau, tra nhầm sẽ PUT đè job khác. Bộ
    gọi theo job (giao-dien.py) LUÔN truyền tham số này (lấy từ
    article_jobs.wp_id của chính job đang xử lý). Luồng cũ (1 bài/record,
    Ver 3.4-3.8) KHÔNG truyền -> hành vi y hệt trước đây, không đổi.

    Trả dict: {'ok':True,'wp_id':...,'wp_url':...,'thoi_luong_giay':...}
              hoặc {'ok':False,'loi':...,'thoi_luong_giay':...}
    """
    import requests
    import autopost as A
    import db_phase2 as DB
    import cauhinh as C

    t0 = time.time()
    wc = C.doc_website()
    if not wc:
        return {'ok': False, 'loi': 'Chưa cấu hình website.', 'thoi_luong_giay': 0}

    try:
        url, auth = A._auth(C.MA_SITE_VER3)
    except SystemExit as e:
        return {'ok': False, 'loi': str(e), 'thoi_luong_giay': time.time() - t0}

    goi = {'title': title, 'content': content, 'excerpt': excerpt, 'status': 'draft'}

    con = DB.ket_noi()
    try:
        if da_co_wp_id is _KHONG_TRUYEN:
            bv = DB.lay_bai_viet(con, dataset_id, record_id, site, mau)
            da_co = bv['wp_id'] if bv and bv.get('wp_id') else None
        else:
            da_co = da_co_wp_id

        if da_co is None:
            try:
                da_co = A.tim_bai_theo_slug(C.MA_SITE_VER3, slug)
            except Exception as e:
                return {'ok': False, 'loi': f'Không kiểm tra được slug trước khi đăng: {e}',
                       'thoi_luong_giay': time.time() - t0}

        # Ver 4.9.6 — VÁ cùng lý do dang_woo_that(): chỉ gửi 'slug' khi
        # THẬT SỰ tạo mới. LƯU Ý RIÊNG cho luồng này: tra theo slug ở TRÊN
        # (tim_bai_theo_slug) vẫn dùng `slug` MỚI truyền vào — nếu bài đã
        # đăng từ TRƯỚC Ver 4.9.6 (slug kiểu cũ, chỉ có mã hàng), tra bằng
        # slug mới sẽ KHÔNG tìm thấy, da_co vẫn None -> tạo bài trùng. Đây
        # là rủi ro đã biết, không tự sửa được ở tầng code vì phần mềm
        # không có cách nào tự suy ra slug CŨ của bài đã đăng nếu không lưu
        # lại — Thịnh cần tự kiểm tra thủ công 15 sản phẩm đã đăng trước
        # Ver 4.9.6 (site chạy WordPress Post, không phải WooCommerce) có
        # bị tạo trùng không sau khi chạy lại bằng bản này.
        if da_co is None:
            goi['slug'] = slug

        loi_cuoi = ''
        for lan in range(3):
            api = f'{url}/wp-json/wp/v2/posts/{da_co}' if da_co else f'{url}/wp-json/wp/v2/posts'
            r = None
            try:
                r = requests.post(api, auth=auth, headers=A.HEADERS,
                                  data=json.dumps(goi, ensure_ascii=False).encode('utf-8'),
                                  timeout=90)
            except requests.exceptions.Timeout:
                loi_cuoi = 'Timeout khi gọi WordPress'
            except requests.exceptions.RequestException as e:
                loi_cuoi = f'{type(e).__name__}: {e}'

            if r is not None and r.status_code < 300:
                try:
                    j = r.json()
                except Exception:
                    return {'ok': False, 'loi': 'WordPress trả 2xx nhưng không phải JSON hợp lệ.',
                           'thoi_luong_giay': time.time() - t0}
                return {'ok': True, 'wp_id': j.get('id'), 'wp_url': j.get('link', ''),
                       'thoi_luong_giay': time.time() - t0}

            if r is not None and r.status_code in (401, 403):
                return {'ok': False,
                       'loi': f'Xác thực thất bại (HTTP {r.status_code}) — kiểm tra Application Password.',
                       'thoi_luong_giay': time.time() - t0}
            if r is not None and 400 <= r.status_code < 500:
                return {'ok': False, 'loi': f'WordPress từ chối (HTTP {r.status_code}): {r.text[:300]}',
                       'thoi_luong_giay': time.time() - t0}

            # timeout / lỗi mạng / 5xx -> KHÔNG retry mù: dò lại slug trước
            if lan < 2:
                # Ver 3.7.1 — GPT phát hiện lỗ hổng: nếu da_co đang RỖNG (lần
                # đầu đăng record này, POST vừa rồi nhắm thẳng vào collection
                # endpoint để TẠO MỚI) và request đó KHÔNG có phản hồi nào
                # (timeout/lỗi mạng — r is None, khác với việc server trả 5xx
                # rõ ràng), thì không biết chắc WordPress đã tạo bài hay chưa.
                # Nếu bước dò slug ngay sau đó CŨNG lỗi mạng, tuyệt đối không
                # được thử POST tạo mới lần nữa — dễ đẻ slug-2. Phải dừng hẳn,
                # trả lỗi để chạy lại sau (lần sau da_co vẫn None nhưng sẽ dò
                # slug lại từ đầu hàm, có thể lúc đó mạng đã ổn định).
                khong_chac_da_tao = (da_co is None and r is None)
                time.sleep(5)
                try:
                    da_co_kiem_lai = A.tim_bai_theo_slug(C.MA_SITE_VER3, slug)
                    if da_co_kiem_lai:
                        da_co = da_co_kiem_lai
                except Exception as e:
                    if khong_chac_da_tao:
                        return {'ok': False,
                               'loi': f'Không xác định được bài đã tạo hay chưa (POST tạo mới lỗi mạng, '
                                      f'sau đó kiểm tra slug cũng lỗi: {type(e).__name__}: {e}). '
                                      f'KHÔNG thử tạo lại để tránh đăng trùng (slug-2) — chạy lại sau.',
                               'thoi_luong_giay': time.time() - t0}
                    pass   # da_co đã biết từ trước (chắc chắn có bài) -> lỗi dò lại chỉ tạm thời, vẫn an toàn để PUT ở vòng sau

        return {'ok': False, 'loi': f'Đăng thất bại sau 3 lần thử. {loi_cuoi}',
               'thoi_luong_giay': time.time() - t0}
    finally:
        con.close()


# ============================================================ Ver 2.1 — gỡ bài hàng loạt (rollback)
def go_1_bai(wp_id, la_woo=False, vinh_vien=False, timeout=30):
    """Gỡ 1 bài/sản phẩm khỏi WordPress.

    MẶC ĐỊNH `vinh_vien=False` -> chuyển vào THÙNG RÁC (khôi phục được từ
    giao diện WP). Chỉ khi truyền vinh_vien=True mới xoá hẳn (force=true).
    Chọn mặc định an toàn vì đây là thao tác hàng loạt — sai 1 lần là mất
    hàng trăm bài, không có đường lùi thứ hai.

    Trả {'ok': True, 'wp_id':...} hoặc {'ok': False, 'loi': ...}
    """
    import requests
    import autopost as A
    import cauhinh as C

    try:
        url, auth = A._auth(C.MA_SITE_VER3)
    except SystemExit as e:
        return {'ok': False, 'loi': str(e)}

    loai = 'wc/v3/products' if la_woo else 'wp/v2/posts'
    api = f'{url}/wp-json/{loai}/{wp_id}'
    tham_so = {'force': 'true'} if vinh_vien else {}
    try:
        r = requests.delete(api, auth=auth, headers=A.HEADERS, params=tham_so, timeout=timeout)
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'loi': f'{type(e).__name__}: {e}'}
    if r.status_code in (200, 410):
        return {'ok': True, 'wp_id': wp_id}
    if r.status_code == 404:
        # Bài không còn trên WP (đã bị xoá tay từ trước) — coi như ĐÃ GỠ,
        # không phải lỗi: mục đích cuối cùng (bài không còn tồn tại) đã đạt.
        return {'ok': True, 'wp_id': wp_id, 'ghi_chu': 'Không tìm thấy trên WP (có thể đã xoá trước đó)'}
    return {'ok': False, 'loi': f'HTTP {r.status_code}: {r.text[:200]}'}


def go_bai_hang_loat(danh_sach_bai, la_woo=False, vinh_vien=False,
                     goi_lai_tien_do=None, co_dung=None):
    """Gỡ nhiều bài. `danh_sach_bai`: list dict từ
    db_phase2.liet_ke_bai_da_dang().

    - Lỗi 1 bài KHÔNG dừng cả batch (giống vòng lặp đăng).
    - Ghi DB trạng thái 'da_go' NGAY sau mỗi bài gỡ xong -> dừng giữa
      chừng vẫn giữ đúng trạng thái, không mất dấu.
    - `co_dung`: threading.Event để bấm Dừng giữa chừng.
    - `goi_lai_tien_do(i, tong, ok, loi)`: callback cập nhật UI.

    Trả {'ok': int, 'loi': int, 'chi_tiet': [...]}
    """
    import db_phase2 as DB

    con = DB.ket_noi()
    ok = loi = 0
    chi_tiet = []
    tong = len(danh_sach_bai)
    try:
        for i, bai in enumerate(danh_sach_bai, 1):
            if co_dung is not None and co_dung.is_set():
                chi_tiet.append({'wp_id': None, 'ok': False, 'loi': f'ĐÃ DỪNG — còn {tong - i + 1} bài chưa gỡ'})
                break
            kq = go_1_bai(bai['wp_id'], la_woo=la_woo, vinh_vien=vinh_vien)
            if kq['ok']:
                ok += 1
                DB.danh_dau_da_go(con, bai['dataset_id'], bai['record_id'], bai['site'], bai['mau'],
                                  ghi_chu=kq.get('ghi_chu', ''))
            else:
                loi += 1
            chi_tiet.append({'wp_id': bai['wp_id'], 'record_id': bai['record_id'],
                             'ok': kq['ok'], 'loi': kq.get('loi', '')})
            if goi_lai_tien_do:
                goi_lai_tien_do(i, tong, ok, loi)
    finally:
        con.close()
    return {'ok': ok, 'loi': loi, 'chi_tiet': chi_tiet}


# ============================================================ Ver 2.7 — upload ảnh sản phẩm
# ==================================================== Ver 4.4.1.6 — lỗi HTTP
# Bug tồn đọng: log 403 bị cắt ở 200 ký tự, mà 200 ký tự đầu của một trang
# chặn toàn là '<!DOCTYPE html><head><meta viewport…' — vô dụng. Thông tin
# cần (ai chặn, luật nào) nằm ở HEADER và ở <title>, đều bị mất.
_MA_LOI_TAM_THOI = (403, 408, 429, 500, 502, 503, 504)


def tom_tat_loi_http(r, gioi_han=600):
    """Ver 4.4.1.6b — giữ tên cũ, thân đã chuyển sang wp_http.tom_tat_loi
    để chỉ còn MỘT bản logic đọc lỗi HTTP trong toàn dự án."""
    import wp_http as WH
    return WH.tom_tat_loi(r, gioi_han)


def _tom_tat_loi_http_cu(r, gioi_han=600):
    """Bản cũ, giữ lại để đối chiếu. Không còn ai gọi."""
    import re as _re
    # Phòng thủ: caller cũ (và test cũ) truyền vào object response tối giản
    # chỉ có status_code/text. Thiếu headers KHÔNG được phép ném lỗi — hàm
    # này chạy trên ĐƯỜNG BÁO LỖI, vỡ ở đây là nuốt mất lỗi gốc.
    ma = getattr(r, 'status_code', 0)
    _hd = getattr(r, 'headers', None) or {}
    ct = (_hd.get('Content-Type') or '').lower()
    than = getattr(r, 'text', '') or ''

    # Header nhận diện lớp chặn — cái này mới cho biết THỦ PHẠM
    dau_moi = []
    for h in ('Server', 'CF-Ray', 'CF-Mitigated', 'X-Sucuri-ID', 'X-Powered-By',
              'X-Mod-Security', 'Retry-After', 'X-LiteSpeed-Cache'):
        v = _hd.get(h)
        if v:
            dau_moi.append(f'{h}={v}')

    nguon = ''
    if 'json' in ct:
        try:
            j = r.json()
            nguon = str(j.get('message') or j.get('code') or '')[:300]
        except Exception:
            nguon = than[:300]
    else:
        # Trang HTML chặn: <title> là thứ duy nhất đáng đọc
        m = _re.search(r'<title[^>]*>(.*?)</title>', than, _re.I | _re.S)
        if m:
            nguon = _re.sub(r'\s+', ' ', m.group(1)).strip()[:200]
        mid = _re.search(r'(mod_security|ModSecurity|Reference\s*#[\w.]+|'
                         r'Error\s*code\s*\d+|incident ID[:\s]*[\w-]+)',
                         than, _re.I)
        if mid:
            dau_moi.append(mid.group(1).strip())
        if not nguon:
            nguon = _re.sub(r'<[^>]+>', ' ', than)
            nguon = _re.sub(r'\s+', ' ', nguon).strip()[:200]

    if ma == 403 and 'json' not in ct:
        goi_y = ('Bị CHẶN Ở TẦNG SERVER (WAF/mod_security), chưa vào tới '
                 'WordPress. Thường do upload liên tiếp quá nhanh — thử lại '
                 'thường là được. Sai quyền thì hỏng TOÀN BỘ chứ không lỗ chỗ.')
    elif ma in (429,):
        goi_y = 'Bị giới hạn tốc độ. Chờ rồi thử lại, giảm số ảnh mỗi lượt.'
    elif ma in (500, 502, 503, 504):
        goi_y = 'Máy chủ web đang lỗi/quá tải. Thử lại sau ít phút.'
    elif ma in (401,):
        goi_y = 'Sai user hoặc Application Password. Kiểm tab Cấu hình.'
    elif ma == 413:
        goi_y = 'Ảnh vượt giới hạn upload của host. Giảm kích thước ảnh.'
    else:
        goi_y = ''

    ngan = f'HTTP {ma}'
    if nguon:
        ngan += f' — {nguon}'
    if goi_y:
        ngan += f'\n{goi_y}'

    day_du = f'HTTP {ma} | Content-Type: {ct or "?"}'
    if dau_moi:
        day_du += ' | ' + ' ; '.join(dau_moi)
    day_du += f'\n--- thân phản hồi ({len(than)} ký tự, cắt {gioi_han}) ---\n'
    day_du += than[:gioi_han]
    return ngan, day_du


def upload_anh_media(du_lieu_bytes, ten_file, alt='', tieu_de='', timeout=90,
                     so_lan_thu=4, ghi_log=None):
    """Upload 1 ảnh lên WordPress Media Library qua REST API.

    Ver 4.4.1.6 — TỰ THỬ LẠI khi gặp lỗi tạm thời (403 WAF, 429, 5xx).
    Bằng chứng thực tế: trong cùng một lượt, media_id 2105-2108 lên OK,
    hero + bien_may ăn 403, rồi 2109-2111 lại OK. Lỗi lỗ chỗ như vậy là
    chặn theo TỐC ĐỘ, không phải sai quyền — nghỉ một nhịp rồi gửi lại là
    qua. Trước đây mỗi lần như thế đều bung lỗi ra tận mặt người dùng.

    Giãn cách tăng dần 2s -> 5s -> 11s (có nhiễu ngẫu nhiên để nhiều ảnh
    trượt cùng lúc không dội lại server cùng một thời điểm).

    Trả {'ok': True, 'id': ..., 'url': ...} hoặc
        {'ok': False, 'loi': ..., 'chi_tiet': ..., 'tam_thoi': bool, 'so_lan': n}
    """
    import random
    import time
    import requests
    import autopost as A
    import cauhinh as C

    try:
        url, auth = A._auth(C.MA_SITE_VER3)
    except SystemExit as e:
        return {'ok': False, 'loi': str(e), 'tam_thoi': False}

    kieu = 'image/webp' if ten_file.lower().endswith('.webp') else 'image/jpeg'
    headers = dict(A.HEADERS)
    headers['Content-Disposition'] = f'attachment; filename="{ten_file}"'
    headers['Content-Type'] = kieu

    # Ver 4.4.1.6b — dùng chung wp_http.post_media với autopost, không giữ
    # bản sao logic retry riêng. Trước đó hai đường upload có hành vi lỗi
    # khác hẳn nhau, sửa một bên tưởng đã sửa cả hai.
    import wp_http as WH
    r, loi = WH.post_media(url, auth, du_lieu_bytes, ten_file, kieu,
                           headers_goc=headers, timeout=timeout,
                           so_lan_thu=so_lan_thu, ghi_log=ghi_log)
    if r is None:
        loi['ok'] = False
        return loi
    kq = r.json()
    media_id = kq.get('id')

    # Cập nhật alt text + title (SEO ảnh) — bước riêng vì API upload
    # không nhận metadata cùng lúc với binary.
    warning = ''
    if media_id and (alt or tieu_de):
        try:
            r_meta = requests.post(f'{url}/wp-json/wp/v2/media/{media_id}', auth=auth,
                                   headers=A.HEADERS,
                                   json={'alt_text': alt, 'title': tieu_de or alt},
                                   timeout=30)
            if r_meta.status_code >= 300:
                warning = f'Ảnh upload OK nhưng alt/title lỗi HTTP {r_meta.status_code}'
        except requests.exceptions.RequestException as e:
            warning = f'Ảnh upload OK nhưng alt/title lỗi {type(e).__name__}: {e}'
    out = {'ok': True, 'id': media_id, 'url': kq.get('source_url', '')}
    if warning:
        out['warning'] = warning
    return out



def cap_nhat_meta_anh_media(media_id, alt='', tieu_de='', timeout=30):
    """Ver 4.1 BUG-06 — cập nhật alt/title cho attachment đã upload.

    Hàm tách riêng để production image workflow đang dùng autopost cache vẫn
    giữ nguyên API/upload bytes cũ. Không POST nếu thiếu media_id.
    """
    import requests
    import autopost as A
    import cauhinh as C
    if not media_id:
        return {'ok': False, 'loi': 'Thiếu media_id'}
    try:
        url, auth = A._auth(C.MA_SITE_VER3)
        r = requests.post(f'{url}/wp-json/wp/v2/media/{media_id}', auth=auth,
                          headers=A.HEADERS,
                          json={'alt_text': alt or '', 'title': tieu_de or alt or ''},
                          timeout=timeout)
        if r.status_code >= 300:
            return {'ok': False, 'loi': f'HTTP {r.status_code}: {r.text[:200]}'}
        return {'ok': True}
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'loi': f'{type(e).__name__}: {e}'}

def cap_nhat_noi_dung_bai_that(wp_id, content, la_woo=True, timeout=60):
    """Ver 4.4.1 — cập nhật CHỈ body của bài/sản phẩm đã có.

    Dùng cho nút Đăng ảnh: không render lại, không gọi AI, không đổi title/slug/meta.
    """
    import requests
    import autopost as A
    import cauhinh as C
    if not wp_id:
        return {'ok': False, 'loi': 'Thiếu WP ID.'}
    try:
        url, auth = A._auth(C.MA_SITE_VER3)
    except SystemExit as e:
        return {'ok': False, 'loi': str(e)}
    if la_woo:
        api = f'{url}/wp-json/wc/v3/products/{wp_id}'
        body = {'description': content}
    else:
        api = f'{url}/wp-json/wp/v2/posts/{wp_id}'
        body = {'content': content}
    try:
        r = requests.post(api, auth=auth, headers=A.HEADERS, json=body, timeout=timeout)
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'loi': f'{type(e).__name__}: {e}'}
    if r.status_code not in (200, 201):
        return {'ok': False, 'loi': f'HTTP {r.status_code}: {r.text[:200]}'}
    return {'ok': True, 'wp_id': wp_id}


def doc_noi_dung_bai_that(wp_id, la_woo=True, timeout=60):
    """Ver 4.4.1.5 — ĐỌC body bài/sản phẩm đang sống trên WordPress.

    Trước bản này adapter chỉ có đường GHI (cap_nhat_noi_dung_bai_that),
    không có đường ĐỌC. Sweep rác bắt buộc phải đọc HTML THẬT trên WP chứ
    không lấy từ SQLite: DB có thể lệch với bản đang sống (đăng lại nhiều
    lần, sửa tay trên WP, ảnh chèn sau khi lưu DB). Dọn theo bản DB rồi PUT
    đè là ghi nhầm phiên bản.

    Trả {ok, wp_id, content, loi}
    """
    import requests
    import autopost as A
    import cauhinh as C
    if not wp_id:
        return {'ok': False, 'loi': 'Thiếu WP ID.', 'content': ''}
    try:
        url, auth = A._auth(C.MA_SITE_VER3)
    except SystemExit as e:
        return {'ok': False, 'loi': str(e), 'content': ''}
    if la_woo:
        api = f'{url}/wp-json/wc/v3/products/{wp_id}'
        khoa = 'description'
    else:
        api = f'{url}/wp-json/wp/v2/posts/{wp_id}?context=edit'
        khoa = 'content'
    try:
        r = requests.get(api, auth=auth, headers=A.HEADERS, timeout=timeout)
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'loi': f'{type(e).__name__}: {e}', 'content': ''}
    if r.status_code != 200:
        return {'ok': False, 'content': '',
                'loi': f'HTTP {r.status_code}: {r.text[:500]}'}
    try:
        data = r.json()
    except ValueError:
        return {'ok': False, 'content': '', 'loi': 'WP trả về không phải JSON.'}
    noi_dung = data.get(khoa, '')
    # WP REST bọc content trong {'raw':..,'rendered':..}; Woo trả chuỗi phẳng.
    # Phải lấy 'raw' — 'rendered' đã qua wpautop/shortcode, PUT lại là hỏng bài.
    if isinstance(noi_dung, dict):
        noi_dung = noi_dung.get('raw') or ''
        if not noi_dung:
            return {'ok': False, 'content': '',
                    'loi': 'WP không trả content.raw (thiếu quyền context=edit).'}
    return {'ok': True, 'wp_id': wp_id, 'content': noi_dung, 'loi': ''}


def gan_anh_vao_san_pham(wp_id, danh_sach_media_id, la_woo=True, timeout=60):
    """Gắn ảnh vào sản phẩm. Ảnh ĐẦU TIÊN trong danh sách thành ảnh đại
    diện (WooCommerce quy ước images[0] là featured)."""
    import requests
    import autopost as A
    import cauhinh as C

    if not danh_sach_media_id:
        return {'ok': False, 'loi': 'Không có ảnh nào để gắn.'}
    try:
        url, auth = A._auth(C.MA_SITE_VER3)
    except SystemExit as e:
        return {'ok': False, 'loi': str(e)}

    if la_woo:
        api = f'{url}/wp-json/wc/v3/products/{wp_id}'
        body = {'images': [{'id': mid} for mid in danh_sach_media_id]}
    else:
        api = f'{url}/wp-json/wp/v2/posts/{wp_id}'
        body = {'featured_media': danh_sach_media_id[0]}
    try:
        r = requests.post(api, auth=auth, headers=A.HEADERS, json=body, timeout=timeout)
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'loi': f'{type(e).__name__}: {e}'}
    if r.status_code not in (200, 201):
        # Woo trả 400 cho CẢ gallery nếu chỉ một attachment ID đã bị xoá/
        # không còn là image. Bóc ID lỗi để caller loại đúng slot, không để
        # một media stale kéo chết 4 ảnh tốt còn lại.
        invalid_ids = []
        try:
            j = r.json() if r.text else {}
        except Exception:
            j = {}
        data = j.get('data') if isinstance(j, dict) else {}
        if isinstance(data, dict):
            for k in ('resource_id', 'image_id', 'id'):
                v = data.get(k)
                if str(v or '').isdigit():
                    invalid_ids.append(str(v))
        import re as _re
        # Regex chỉ chạy trên message nếu JSON parse được, tránh nhặt nhầm
        # data.status=400 thành media ID vì code có chữ invalid_image_id.
        raw = (str(j.get('message') or '') if isinstance(j, dict) else '') or (r.text or '')[:1200]
        # Message thực tế Woo thường dạng '#1526 is an invalid image ID'
        # hoặc 'Invalid image id 1526'. Không lấy bừa HTTP 400 làm media ID.
        for pat in (r'#\s*(\d+)\s+is\s+(?:an?\s+)?(?:invalid|not\s+valid)',
                    r'(?:invalid|not\s+valid)[^0-9]{0,40}(?:image\s*)?(?:id)?[^0-9]{0,10}(\d+)',
                    r'(?:image\s*id)[^0-9]{0,10}(\d+)'):
            for m in _re.finditer(pat, raw, flags=_re.I):
                invalid_ids.append(m.group(1))
        invalid_ids = list(dict.fromkeys(x for x in invalid_ids if str(x).isdigit()))
        ngan, day_du = tom_tat_loi_http(r)
        return {'ok': False, 'loi': ngan, 'chi_tiet': day_du,
                'status_code': r.status_code, 'invalid_media_ids': invalid_ids}

    # ---- Ver 4.4.1.6 — ĐỌC LẠI ĐỂ XÁC NHẬN (bug tồn đọng #1) ----
    # HTTP 200 chỉ nói request được nhận, KHÔNG nói ảnh đã dính. Woo có thể
    # nuốt im lặng khi attachment thuộc post khác, khi plugin lọc, hoặc khi
    # cache tầng trên trả 200 mà chưa ghi. Trước bản này tool tin luôn 200 và
    # báo thành công — sai lệch chỉ lộ ra khi mở trang bằng mắt.
    #
    # Verify KHÔNG được phép biến thành công thành thất bại: gọi GET hỏng
    # (mạng, quyền đọc) thì vẫn trả ok=True, chỉ kèm cảnh báo.
    try:
        rg = requests.get(api, auth=auth, headers=A.HEADERS, timeout=timeout)
        if rg.status_code == 200:
            d = rg.json()
            if la_woo:
                that = [str(x.get('id')) for x in (d.get('images') or []) if x.get('id')]
                mong_doi = [str(x) for x in danh_sach_media_id]
                thieu = [x for x in mong_doi if x not in that]
                if thieu:
                    return {'ok': False, 'da_verify': True,
                            'loi': 'WordPress trả 200 nhưng đọc lại thì %d/%d ảnh '
                                   'KHÔNG có trên sản phẩm (thiếu media id: %s). '
                                   'Nhiều khả năng plugin/cache chặn.'
                                   % (len(thieu), len(mong_doi), ', '.join(thieu)),
                            'media_ids_thieu': thieu}
                if that and that[0] != mong_doi[0]:
                    # Ver 4.4.1.6 (bug tồn đọng #3) — ảnh đại diện KHÔNG đúng
                    # cái mình gửi. Trước đây tool âm thầm chấp nhận, nên hero
                    # upload lỗi là một ảnh khác lặng lẽ lên làm ảnh đại diện.
                    return {'ok': True, 'da_verify': True,
                            'canh_bao': 'Ảnh đại diện trên web là media %s, '
                                        'KHÔNG phải ảnh hero đã gửi (%s). '
                                        'Kiểm lại trang trước khi bỏ noindex.'
                                        % (that[0], mong_doi[0])}
            else:
                fm = str(d.get('featured_media') or '')
                if fm != str(danh_sach_media_id[0]):
                    return {'ok': False, 'da_verify': True,
                            'loi': 'WordPress trả 200 nhưng ảnh đại diện đọc lại '
                                   'là %s, không phải %s.'
                                   % (fm or 'trống', danh_sach_media_id[0])}
            return {'ok': True, 'da_verify': True}
        return {'ok': True, 'da_verify': False,
                'canh_bao': 'Gắn ảnh trả 200 nhưng không đọc lại kiểm chứng được '
                            '(HTTP %s khi GET).' % rg.status_code}
    except requests.exceptions.RequestException as e:
        return {'ok': True, 'da_verify': False,
                'canh_bao': 'Gắn ảnh trả 200 nhưng không đọc lại kiểm chứng được '
                            '(%s).' % type(e).__name__}
