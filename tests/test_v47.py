import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import sys
from unittest.mock import patch

import ai_wp_adapter as AWP
import cauhinh as C
import prompts_phase2 as PR

KQ = []


def test(ma, mota, ok):
    KQ.append((ma, mota, bool(ok)))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}')


class FakeGeminiResp:
    def __init__(self, status_code, json_data):
        self.status_code, self._json = status_code, json_data

    def json(self):
        return self._json


def body_json(data_dict):
    import json
    return {
        'candidates': [{'finishReason': 'STOP',
                        'content': {'parts': [{'text': json.dumps(data_dict, ensure_ascii=False)}]}}],
        'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 10},
    }


ROW = {'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'ten_goc': 'Cap test', 'ma_goc': 'CD1'}
SCHEMA = PR._json_schema('outline_cap_dien', mau='chuan')
DATA_DU = {k: ('noi dung du dai qua nguong do dai kiem tra field nay' if isinstance(v, str) else [])
          for k, v in SCHEMA.items()}

# ============================================================ NHÓM A — cấu hình dự phòng
C.luu_gemini_du_phong(['key_phu_1', 'key_phu_2'], ['model_phu_1'])
gc = C.doc_gemini()
test('CFG-1', f'Đọc lại đúng model dự phòng: {gc["model_du_phong"]}', gc['model_du_phong'] == ['model_phu_1'])
test('CFG-2', f'Đọc lại đúng API key dự phòng: {gc["api_key_du_phong"]}',
     gc['api_key_du_phong'] == ['key_phu_1', 'key_phu_2'])

C.luu_gemini_du_phong([], [])
gc2 = C.doc_gemini()
test('CFG-3', f'Lưu rỗng -> đọc lại đúng rỗng, không lỗi: {gc2["model_du_phong"]}, {gc2["api_key_du_phong"]}',
     gc2['model_du_phong'] == [] and gc2['api_key_du_phong'] == [])

test('CFG-4', 'Tách danh sách nhận cả dấu phẩy lẫn xuống dòng, bỏ dòng trống',
     C._tach_danh_sach('a, b,\nc\n\n') == ['a', 'b', 'c'])

# ============================================================ NHÓM B — goi_ai_co_du_phong: thành công ngay lần đầu
C.luu_gemini('key_chinh', 'model_chinh')
with patch('requests.post', return_value=FakeGeminiResp(200, body_json(DATA_DU))):
    kq, vp = AWP.goi_ai_co_du_phong(ROW, 'chuan', [('key_chinh', 'model_chinh')], site_cfg={'ten': 'T'})
test('DP-1', f'Thành công ngay cặp đầu -> da_thu=1, vi_pham rỗng: {kq.get("da_thu")}, {vp}',
     kq['ok'] is True and kq.get('da_thu') == 1 and vp == {})

# ============================================================ NHÓM C — goi_ai_co_du_phong: model chính lỗi (MAX_TOKENS-kiểu), model dự phòng cứu được
goi_lan = {'n': 0}


def post_that_bai_lan_1(url, **kwargs):
    goi_lan['n'] += 1
    if 'model_chinh' in url:
        return FakeGeminiResp(200, {'candidates': [{'finishReason': 'MAX_TOKENS', 'content': {'parts': []}}],
                                    'usageMetadata': {}})
    return FakeGeminiResp(200, body_json(DATA_DU))


with patch('requests.post', side_effect=post_that_bai_lan_1):
    kq2, vp2 = AWP.goi_ai_co_du_phong(ROW, 'chuan', [('key_chinh', 'model_chinh'), ('key_chinh', 'model_phu')],
                                      site_cfg={'ten': 'T'})
test('DP-2', f'Model chính bị MAX_TOKENS -> tự chuyển model dự phòng, cứu được: da_thu={kq2.get("da_thu")}',
     kq2['ok'] is True and kq2.get('da_thu') == 2)

# ============================================================ NHÓM D — goi_ai_co_du_phong: Hard Block chặn field CỐT LÕI cũng kích hoạt đổi cặp
# (Ver 4.9: nếu vi phạm CHỈ ở FAQ thì tự bỏ FAQ thay vì đổi model — xem
# test_v49.py FAQ-DROP-*. Test này dùng vi phạm ở field CỐT LÕI
# (dac_diem_html) để đúng nghĩa "phải đổi model mới cứu được".)
DATA_RAC = dict(DATA_DU)
DATA_RAC['dac_diem_html'] = 'a' * 200   # ky tu lap bat thuong o field COT LOI, khong phai FAQ


def post_rac_lan_1(url, **kwargs):
    if 'model_chinh' in url:
        return FakeGeminiResp(200, body_json(DATA_RAC))
    return FakeGeminiResp(200, body_json(DATA_DU))


with patch('requests.post', side_effect=post_rac_lan_1):
    kq3, vp3 = AWP.goi_ai_co_du_phong(ROW, 'chuan', [('key_chinh', 'model_chinh'), ('key_chinh', 'model_phu')],
                                      site_cfg={'ten': 'T'})
# Ver 5.3 — ĐỔI Ý NGHĨA TEST có chủ đích: trước đây Hard Block chặn nội
# dung cốt lõi thì TỰ ĐỘNG chuyển model dự phòng (test cũ mong da_thu=2).
# Từ Ver 5.3, Hard Block chặn cốt lõi THẤT BẠI NGAY (không thử thêm cặp
# khác cho CÙNG sản phẩm — tốn quota vô ích khi đổi model không chắc sửa
# được lỗi do data mỏng). Xem CHANGELOG-VER53.md mục vá. Đây LÀ thay đổi
# hành vi có chủ đích, không phải hồi quy.
test('DP-3', f'Model chính sinh nội dung CỐT LÕI rác (Hard Block chặn) -> THẤT BẠI NGAY (Ver 5.3), '
             f'không đốt cặp dự phòng cho sản phẩm này: da_thu={kq3.get("da_thu")}, ok={kq3["ok"]}',
     kq3['ok'] is False and kq3.get('da_thu') == 1)

# ============================================================ NHÓM E — goi_ai_co_du_phong: hết sạch danh sách vẫn lỗi -> trả lỗi cuối cùng, không giấu
with patch('requests.post', return_value=FakeGeminiResp(200, {'candidates': [{'finishReason': 'MAX_TOKENS',
                                                                              'content': {'parts': []}}],
                                                              'usageMetadata': {}})):
    kq4, vp4 = AWP.goi_ai_co_du_phong(ROW, 'chuan', [('key_chinh', 'model_chinh'), ('key_chinh', 'model_phu')],
                                      site_cfg={'ten': 'T'})
test('DP-4', f'Hết sạch danh sách vẫn lỗi -> ok=False, da_thu=đúng số cặp đã thử: {kq4.get("da_thu")}',
     kq4['ok'] is False and kq4.get('da_thu') == 2 and 'token' in kq4['loi'].lower())

# ============================================================ NHÓM F — danh sách dự phòng rỗng vẫn an toàn
kq5, vp5 = AWP.goi_ai_co_du_phong(ROW, 'chuan', [], site_cfg={'ten': 'T'})
test('DP-5', f'Danh sách rỗng -> trả lỗi rõ ràng, không crash: {kq5}', kq5['ok'] is False)

# ============================================================ NHÓM G — api_key param override trên goi_ai_that
da_dung_key = {}


def post_ghi_lai_key(url, **kwargs):
    da_dung_key['url'] = url
    return FakeGeminiResp(200, body_json(DATA_DU))


with patch('requests.post', side_effect=post_ghi_lai_key):
    AWP.goi_ai_that(ROW, 'chuan', 'model_x', site_cfg={'ten': 'T'}, api_key='key_truyen_thang')
test('KEY-1', 'Truyền api_key trực tiếp -> dùng ĐÚNG key đó, không đọc env',
     'key_truyen_thang' in da_dung_key['url'])

# ============================================================ NHÓM H — prompt FAQ có giới hạn độ dài câu hỏi
_, nd, _ = PR.xay_prompt(ROW, {'ten': 'T'}, mau='chuan')
test('FAQ-PROMPT-1', 'Prompt user có nhắc giới hạn độ dài câu hỏi FAQ (không chỉ câu trả lời)',
     'câu hỏi' in nd.lower() and ('dưới 15' in nd or '15 từ' in nd))

# ============================================================ NHÓM I — token tăng
import inspect
test('TOKEN-1', 'maxOutputTokens đã tăng lên 24000', '24000' in inspect.getsource(AWP.goi_ai_that))

# ============================================================ NHÓM J — nút Chuẩn hoá MASTER gọi đúng module đã có, không viết lại logic
import chuan_hoa_master as CHM
test('CHM-WIRE-1', 'Module chuan_hoa_master có hàm chuan_hoa() sẵn sàng cho GUI gọi', hasattr(CHM, 'chuan_hoa'))

print()
p = sum(1 for _, _, ok in KQ if ok)
print(f'TONG VER 4.7: {p}/{len(KQ)} PASS')
if p != len(KQ):
    sys.exit(1)
