# -*- coding: utf-8 -*-
"""Ver 3.1 — test 4 vá V1 + fallback rule. Không gọi mạng thật.

Chạy: python tests/test_v31_va_loi.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import vision_chung as V
import enrich_tcvn_mba as E
import doc_catalogue_pdf as C

PASS = FAIL = 0


def kiem(dk, ten):
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if dk else (PASS, FAIL + 1)
    print(f'  {"PASS" if dk else "FAIL"}  {ten}')


class _FakeResp:
    def __init__(self, code, payload):
        self.status_code = code
        self._p = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._p


def _resp_text(t):
    return _FakeResp(200, {'candidates': [{'finishReason': 'STOP',
                                           'content': {'parts': [{'text': t}]}}]})


RESP_HET_TOKEN = _FakeResp(200, {'candidates': [{'finishReason': 'MAX_TOKENS',
                                                 'content': {}}]})   # KHÔNG có 'parts'

CH = {'keys': ['k1'], 'model': 'test-model'}

print("== 1. goi_vision — lỗi 'parts' (model suy nghĩ ăn hết token) ==")


class _RQ1:
    """Lần 1 trả MAX_TOKENS không parts; lần 2 (ngân sách x4) trả JSON tốt."""
    def __init__(self):
        self.goi = []

    def post(self, url, json=None, timeout=0):
        self.goi.append(json['generationConfig']['maxOutputTokens'])
        return RESP_HET_TOKEN if len(self.goi) == 1 else _resp_text('{"a": 1}')


rq = _RQ1()
kq = V.goi_vision(b'x', 'image/jpeg', 'p', cau_hinh=CH, max_tokens=1200, _requests=rq)
kiem(kq['ok'] and kq['json'] == {'a': 1}, "thiếu token -> retry tự động -> thành công")
kiem(rq.goi == [1200, 4800], f'ngân sách retry gấp 4 ({rq.goi})')
kiem(V.goi_vision(b'x', 'image/jpeg', 'p', cau_hinh=CH, max_tokens=100,
                  _requests=_RQ1())['ok'], 'max_tokens=100 bị nâng sàn 1000, không chết như 3.0')

print('== 2. goi_vision — JSON hỏng: retry 1 lần rồi lưu raw ==')


class _RQ2:
    def __init__(self, roi_tot=False):
        self.n = 0
        self.roi_tot = roi_tot

    def post(self, url, json=None, timeout=0):
        self.n += 1
        if self.roi_tot and self.n >= 2:
            return _resp_text('{"b": 2}')
        return _resp_text('day khong phai json dau nhe')


with tempfile.TemporaryDirectory() as tmp:
    cwd = os.getcwd()
    os.chdir(tmp)
    try:
        kq = V.goi_vision(b'x', 'image/jpeg', 'p', cau_hinh=CH, _requests=_RQ2(roi_tot=True))
        kiem(kq['ok'] and kq['json'] == {'b': 2}, 'JSON hỏng lần 1 -> retry -> lần 2 OK')
        rq2 = _RQ2()
        kq = V.goi_vision(b'x', 'image/jpeg', 'p', cau_hinh=CH, _requests=rq2)
        kiem(not kq['ok'] and 'raw' in kq['loi'], 'hỏng cả 2 lần -> báo lỗi kèm đường dẫn raw')
        raw_dir = os.path.join(V.VISION_CACHE, 'raw-loi')
        kiem(os.path.isdir(raw_dir) and len(os.listdir(raw_dir)) >= 1,
             'raw response được LƯU lại để soi')
    finally:
        os.chdir(cwd)

print('== 3. Cache theo cả prompt + model ==')
with tempfile.TemporaryDirectory() as tmp:
    cwd = os.getcwd()
    os.chdir(tmp)
    try:
        f = os.path.join(tmp, 'anh.jpg')
        open(f, 'wb').write(b'anh')
        V.ghi_cache(f, 'phanloai', {'v': 1}, them='model-A prompt cũ')
        kiem(V.doc_cache(f, 'phanloai', them='model-A prompt cũ') == {'v': 1},
             'cùng prompt -> ăn cache')
        kiem(V.doc_cache(f, 'phanloai', them='model-A prompt MỚI') is None,
             'ĐỔI PROMPT -> cache miss, buộc đọc lại (vá lỗi GPT bắt)')
        kiem(V.doc_cache(f, 'phanloai', them='model-B prompt cũ') is None,
             'đổi model -> cache miss')
    finally:
        os.chdir(cwd)

print('== 4. Vỏ mạ kẽm không còn là Pokémon điện ==')
kiem(E.la_phu_kien('Vỏ mạ kẽm nhúng nóng MBA 3P 560kVA (loại lớn)') is True,
     'vỏ mạ kẽm -> phụ kiện')
kiem(E.la_phu_kien('Giá treo MBA 1P 50kVA') is True, 'giá treo -> phụ kiện')
kiem(E.la_phu_kien('Máy biến áp dầu 3Pha 560KVA MBT') is False,
     'máy biến áp thật KHÔNG bị chặn oan')
kiem(E.la_phu_kien('Báo Giá Máy biến áp Khô KP/Hàn Quốc 4000kVA') is False,
     "'Báo Giá Máy biến áp...' không bị chặn oan")

print('== 5. Bảng khô: 250kVA = 98,46 theo catalogue THIBIDI thật ==')
kiem(E.meps_tcvn(250, 3, 'kho', (22, 0.4)) == 98.46, 'khô 250 -> 98.46 (sửa từ 98.49)')
kiem(E.meps_tcvn(1000, 3, 'kho', (22, 0.4)) == 98.92, 'khô 1000 giữ nguyên (catalogue xác nhận)')
kiem(E.meps_tcvn(2500, 3, 'kho', (22, 0.4)) == 99.09, 'khô 2500 giữ nguyên (catalogue xác nhận)')

print('== 6. PDF — AI phân loại chết thì fallback rule theo text layer ==')
with tempfile.TemporaryDirectory() as tmp:
    cwd = os.getcwd()
    os.chdir(tmp)
    try:
        import fitz
        doc = fitz.open()
        t = doc.new_page()
        t.insert_text((50, 60), 'Thong so ky thuat kVA Po Pk Uk ton hao khoi luong '
                                'kich thuoc 100 250 320 400 560 630 750 800 1000 1250 Dyn11 22/0.4')
        doc.save('cat.pdf')
        doc.close()

        def mock_pl_chet(anh_bytes, mime, prompt, cau_hinh=None, max_tokens=0, **kw):
            if 'co_bang_thong_so' in prompt:
                return {'ok': False, 'loi': 'mock: AI chết'}
            return {'ok': True, 'json': {'hang': 'MBT', 'loai_may': 'dau',
                                         'dien_ap': None, 'do_ro': 'cao',
                                         'cac_dong': [{'cong_suat_kva': 250, 'po_w': 440}]}}

        kq, n = C.doc_mot_pdf('cat.pdf', 99, goi_vision=mock_pl_chet)
        kiem(len(kq) == 1 and kq[0]['po_w'] == 440,
             'AI phân loại chết -> rule text layer cứu -> vẫn đọc được bảng')
    finally:
        os.chdir(cwd)

print(f'\n===== KẾT QUẢ: PASS {PASS} / FAIL {FAIL} =====')
sys.exit(1 if FAIL else 0)
