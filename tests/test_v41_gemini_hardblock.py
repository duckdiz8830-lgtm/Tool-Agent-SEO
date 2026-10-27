import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import sys
import render_phase2 as R
import ai_wp_adapter as AWP
import prompts_phase2 as PR

KQ = []


def test(ma, mota, ok):
    KQ.append((ma, mota, bool(ok)))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}')


# ============================================================ NHÓM A — responseSchema
schema_don_gian = PR._json_schema('outline_may_bien_ap', mau='chuan')
gs = AWP._sang_gemini_schema(schema_don_gian)
test('SCHEMA-1', 'responseSchema có type OBJECT + properties đủ field',
     gs['type'] == 'OBJECT' and set(gs['properties']) == set(schema_don_gian))
test('SCHEMA-2', 'Field faq (mảng object) được chuyển đúng thành ARRAY of OBJECT',
     gs['properties']['faq']['type'] == 'ARRAY'
     and gs['properties']['faq']['items']['type'] == 'OBJECT'
     and set(gs['properties']['faq']['items']['properties']) == {'q', 'a'})
test('SCHEMA-3', 'faq KHÔNG nằm trong required (mảng có thể rỗng), field văn bản khác CÓ trong required',
     'faq' not in gs['required'] and 'meta_title' in gs['required'])

# ============================================================ NHÓM B — Hard Block lớp 4 (case thật từ log 26/07)
row_mba = {
    'profile_id': 'may_bien_ap_do_luong', 'outline_id': 'outline_may_bien_ap',
    'ten_goc': 'Máy biến áp dầu 1Pha 15KVA 12.7/0.23KV Loại Silic - TBD',
    'cap_dien_ap': '12.7/0.23', 'cong_suat': '15',
}

# case thật gây lỗi: AI viết "12.7KV" (tách nửa cặp sơ cấp) trong ung_dung_html
chan_1 = R.kiem_tra_bia('Sản phẩm phù hợp lưới điện 12.7KV khu vực nông thôn.', row_mba)
test('HB-1', f'"12.7KV" (nửa cặp điện áp sơ/thứ cấp thật, KHÔNG phải bịa) KHÔNG còn bị chặn nhầm — chan={chan_1}',
     chan_1 == [])

chan_2 = R.kiem_tra_bia('Vận hành ổn định ở cấp 0.23KV phía hạ áp.', row_mba)
test('HB-2', f'Nửa còn lại của cặp "0.23KV" cũng không bị chặn nhầm — chan={chan_2}',
     chan_2 == [])

# ============================================================ NHÓM C — đối chứng: KHÔNG được thủng
# C1: giá trị hoàn toàn không có trong record (bịa thật) vẫn phải bị chặn
chan_bia = R.kiem_tra_bia('Chịu được dòng ngắn mạch 99.9KV vượt trội.', row_mba)
test('HB-C1', f'Giá trị BỊA THẬT (99.9KV không nằm trong record) vẫn PHẢI bị chặn — chan={chan_bia}',
     '99.9KV' in chan_bia)

# C2: giá trị số khớp (12.7) nhưng đơn vị SAI HỌ (A - dòng điện, không phải điện áp)
# -> nguy cơ thủng nếu chỉ so giá trị mà không so họ đơn vị
chan_sai_ho = R.kiem_tra_bia('Dòng định mức đạt 12.7A theo thiết kế.', row_mba)
test('HB-C2', f'"12.7A" (đúng SỐ 12.7 nhưng SAI HỌ đơn vị — record chỉ có 12.7 ở field điện áp, '
             f'không phải dòng điện) PHẢI vẫn bị chặn, không được nới theo giá trị suông — chan={chan_sai_ho}',
     '12.7A' in chan_sai_ho)

# C3: giá trị số khớp nhưng lấy từ field khác không nằm trong _FIELD_HO_DON_VI
# (VD field công suất '15' không phải cặp ghép, layer 4 không áp dụng ở đây,
# nhưng '15' đã có trong kho token đơn lẻ qua field cong_suat rồi nên vẫn qua được bình thường)
row_mba_kva = dict(row_mba)
chan_congsuat = R.kiem_tra_bia('Công suất định mức 15KVA phù hợp phụ tải.', row_mba_kva)
test('HB-C3', f'"15KVA" khớp đúng field công suất có thật (không qua lớp 4, qua lớp 3 bình thường) — chan={chan_congsuat}',
     chan_congsuat == [])

# ============================================================ NHÓM D — regression: các case Hard Block cũ (Ver 3.4-3.9) không đổi hành vi
row_cap = {
    'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien',
    'ten_goc': 'Dây VCmd2x1.5mm2 (0.6/1kV) - Cadivi',
    'tiet_dien': '2x1.5', 'cap_dien_ap': '0.6/1',
}
chan_cu_1 = R.kiem_tra_bia('Cáp có tiết diện 2x1.5mm2, cấp điện áp 0.6/1kV.', row_cap)
test('HB-D1', f'Case cũ (số khớp đúng field, đúng như Ver 3.4-3.9 đã PASS) vẫn không bị chặn — chan={chan_cu_1}',
     chan_cu_1 == [])
chan_cu_2 = R.kiem_tra_bia('Cáp có tiết diện 9x99mm2 hoàn toàn khác.', row_cap)
test('HB-D2', f'Case cũ (cụm ghép bịa "9x99mm2") vẫn bị chặn như trước — chan={chan_cu_2}',
     '9x99mm2' in chan_cu_2)

print()
p = sum(1 for _, _, ok in KQ if ok)
print(f'TONG VER 4.1 GEMINI+HARDBLOCK: {p}/{len(KQ)} PASS')
if p != len(KQ):
    sys.exit(1)
