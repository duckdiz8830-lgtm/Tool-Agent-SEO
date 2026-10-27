# -*- coding: utf-8 -*-
"""Test Ver 3.6.1 — cụm nợ vặt: dấu ≤, bộ lọc dấu vết AI, bảng tra 3200."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import render_phase2 as R
import tra_cuu_thibidi as TC

P = F = 0
def kt(t, dk):
    global P, F
    if dk: P += 1; print('  PASS ', t)
    else:  F += 1; print('  FAIL ', t)

print('== 1. dấu ≤ cho mức quy chuẩn EVN ==')
_ts = {'Tổn hao không tải Po cực đại theo tiêu chuẩn EVN (W)': '52',
       'Điện áp ngắn mạch Uk (%)': '2',
       'Tổng khối lượng (kg)': '195'}
qc = R._dong_bang_thong_so_dong({'thong_so_dong': _ts, 'nguon_ky_hieu': '≤'})
cat = R._dong_bang_thong_so_dong({'thong_so_dong': _ts, 'nguon_ky_hieu': '='})
khong = R._dong_bang_thong_so_dong({'thong_so_dong': _ts})
kt('mức quy chuẩn EVN in "≤ 52"', '≤ 52' in qc)
kt('Uk KHÔNG được gắn dấu ≤', '≤ 2' not in qc)
kt('KHÔNG gắn dấu vào khối lượng (không phải Po/Pk/Uk)', '≤ 195' not in qc)
kt('số catalogue hãng giữ nguyên, không có ≤', '≤' not in cat)
kt('MASTER cũ chưa có cột ký hiệu -> giữ nguyên hành vi cũ', '≤' not in khong)

print('== 2. bộ lọc dấu vết AI ==')
kt('thay — bằng dấu phẩy',
   R._bo_gach_dai('Amorphous là 554W — thấp hơn 30%') == 'Amorphous là 554W, thấp hơn 30%')
kt('KHÔNG đụng gạch ngắn – (dải số là đúng chính tả)',
   R._bo_gach_dai('dải 15–100 kVA') == 'dải 15–100 kVA')
kt('không đẻ dấu phẩy kép', ',,' not in R._bo_gach_dai('a —, b'))
s = ('<p>Cần giải pháp hạ thế nguồn điện công suất lớn cho công trình trung áp? '
     'Máy biến áp dầu 3Pha 2500KVA 22/0.4KV do THIBIDI chế tạo, đáp ứng 96/QĐ-HĐTV.</p>')
r = R._bo_cau_hoi_mo_bai(s)
kt('cắt câu hỏi tu từ mở bài', 'Cần giải pháp' not in r)
kt('giữ lại phần nội dung thật', 'THIBIDI chế tạo' in r)
kt('giữ thẻ <p> mở đầu', r.startswith('<p>'))
kt('KHÔNG cắt nếu phần còn lại quá ngắn (không để đoạn rỗng)',
   R._bo_cau_hoi_mo_bai('<p>Ngắn quá?</p>') == '<p>Ngắn quá?</p>')
kt('câu thường (không phải câu hỏi) giữ nguyên',
   R._bo_cau_hoi_mo_bai('<p>Máy biến áp dầu 250kVA dùng cho trạm.</p>').startswith('<p>Máy'))
kt('chuỗi rỗng không lỗi', R.loc_dau_vet_ai('') == '')

print('== 3. bảng tra THIBIDI — mức 3200 kVA ==')
b32 = TC.tra(3200, 3, 'dau', 'THIBIDI')
b25 = TC.tra(2500, 3, 'dau', 'THIBIDI')
kt('3200 KHÔNG còn Po Amorphous 554W', b32['po_amorphous'] is None)
kt('3200 vẫn giữ Po Silic thật', b32['po_silic'] == 2340)
kt('2500 giữ nguyên (catalogue có in, đã ghi rõ nội suy)', b25['po_amorphous'] == 554)
kt('2500 vẫn được đánh dấu nội suy', b25['noi_suy'] is True)
kt('mức bình thường không bị ảnh hưởng', TC.tra(250, 3, 'dau', 'THIBIDI')['po_amorphous'] == 100)

print('== 4. khối so sánh lõi không dựng khi thiếu số ==')
import kien_thuc_bien_thien as KT
row32 = {'ten_goc': 'Máy biến áp dầu 3Pha 3200KVA 22/0.4KV Loại Silic - TBD',
         'thuong_hieu': 'THIBIDI', 'cong_suat': '3200', 'cap_dien_ap': '22/0.4'}
kt('SKU 3200 kVA: không vẽ so sánh Silic/Amorphous nữa (thiếu số, không bịa)',
   KT.khoi_so_sanh_loi(row32) == '')

print(f'\n===== KẾT QUẢ: PASS {P} / FAIL {F} =====')

print('== 5. Ver 3.6.2 — hero bỏ chip + bảng nhanh (góp ý sếp) ==')
import giao_dien_2_5 as G
_row = {'ma_goc': 'MBT1P15A2608', 'ten_goc': 'Máy biến áp dầu 1Pha 15KVA 12.7/0.23KV Loại Amorphous',
        'thuong_hieu': 'MBT', 'cong_suat': '15', 'cap_dien_ap': '12.7/0.23', 'dvt': 'Máy',
        'profile_id': 'may_bien_ap_do_luong', 'outline_id': 'outline_may_bien_ap'}
_ai = {'intro_html': '<p>Máy biến áp dầu 1Pha 15kVA do MBT sản xuất.</p>'}
def _hero(co):
    os.environ['HERO_HIEN_CHIP_QUICK'] = co
    return G.dung_bai_2_5(_row, _ai, {'ten': 'x', 'url': 'https://x.vn'}, tach_hero=True)['hero']
_tat, _bat = _hero('0'), _hero('1')
kt('MẶC ĐỊNH tắt: hero không còn chip', 'chip' not in _tat)
kt('MẶC ĐỊNH tắt: hero không còn bảng nhanh', 'quick' not in _tat)
kt('vẫn giữ đoạn văn mở đầu', 'MBT sản xuất' in _tat)
kt('vẫn giữ dòng giá', 'Liên hệ' in _tat)
kt('hero ngắn đi rõ rệt', len(_tat) < len(_bat) / 2)
kt('bật cờ thì hiện lại được', 'chip' in _bat and 'quick' in _bat)
os.environ.pop('HERO_HIEN_CHIP_QUICK', None)

print(f'\n===== KẾT QUẢ CUỐI: PASS {P} / FAIL {F} =====')

print('== 6. Ver 3.6.3 — vá 2 lỗi lọt lên bài thật ==')
os.environ['GIAO_DIEN_2_5'] = '1'
_r = {'ma_goc': 'MBT1P15A2608', 'ten_goc': 'Máy biến áp dầu 1Pha 15KVA 12.7/0.23KV Loại Amorphous',
      'thuong_hieu': 'MBT', 'cong_suat': '15', 'cap_dien_ap': '12.7/0.23',
      'profile_id': 'may_bien_ap_do_luong', 'outline_id': 'outline_may_bien_ap'}
_a = {'intro_html': '<p>Bạn đang tìm giải pháp truyền tải điện hiệu quả cho lưới điện một pha? '
                    '**Máy biến áp dầu 1Pha 15KVA 12.7/0.23KV** hiệu MBT dùng **lõi Amorphous** '
                    'siêu giảm hao, thiết kế kiểu kín với sứ gốm bền bỉ.</p>',
      'dac_diem_html': '<ul><li>Dùng **lõi Amorphous** giảm tổn hao</li></ul>',
      'meta_description': 'Bạn cần máy biến áp 15kVA? **MBT 15kVA** chính hãng, giao toàn quốc, bảo hành dài hạn.',
      'faq': []}
_k = R.dung_bai_html(_r, _a, {'ten': 'x', 'url': 'https://x.vn'})
_sd, _h, _m = _k['short_description'], _k['html'], _k['meta_description']
kt('hero KHÔNG còn dấu ** (Markdown lọt lên trang)', '**' not in _sd)
kt('hero đổi **đậm** thành <strong>', '<strong>' in _sd)
kt('thân bài KHÔNG còn dấu **', '**' not in _h)
kt('CẮT ĐƯỢC câu hỏi tu từ mở bài dù bị 4 tầng thẻ bọc ngoài',
   'Bạn đang tìm' not in _sd)
kt('giữ nguyên nội dung thật sau câu hỏi', 'lõi Amorphous' in _sd)
kt('meta là CHỮ TRẦN, không có thẻ HTML', '<' not in _m and '**' not in _m)
kt('meta cũng cắt câu hỏi mở đầu', 'Bạn cần' not in _m)
kt('dấu sao ĐƠN giữ nguyên (có thể là dấu nhân)',
   R._doi_markdown_dam('công thức a * b') == 'công thức a * b')
kt('không cắt khi phần còn lại quá ngắn',
   R._bo_cau_hoi_mo_bai('<div><p>Ngắn quá?</p></div>').count('Ngắn quá') == 1)
os.environ.pop('GIAO_DIEN_2_5', None)

print(f'\n===== KẾT QUẢ CUỐI: PASS {P} / FAIL {F} =====')
