# -*- coding: utf-8 -*-
"""Test Ver 3.6.4 — đợt vá lớn: bếp trưởng 4 profile, Uk, nhãn KP, tiêu đề,
slug, meta Rank Math, danh mục, biểu đồ lõi cho mọi hãng, bảng cân hai
phía, Family Router, prompt Enhance."""
import os, sys, re, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import profiles as P
import bep_truong as B
import render_phase2 as R
import family_router as FR
import kien_thuc_bien_thien as KT
import enhance as E

Pn = Fn = 0
def kt(t, dk):
    global Pn, Fn
    if dk: Pn += 1; print('  PASS ', t)
    else:  Fn += 1; print('  FAIL ', t)

print('== 1. bep_truong: mọi trục phải TỒN TẠI trong profile ==')
bia = []
for pid, tr in B._TRUC.items():
    f = set(P.PROFILES[pid]['cot_import'].values())
    for nhom in ('dinh_danh', 'ky_thuat'):
        bia += [(pid, x) for x in tr[nhom] if x not in f]
kt('KHÔNG còn trục bịa tên (bản đầu có 12 trục không tồn tại)', bia == [])
kt('khai đủ 4 profile', set(B._TRUC) == set(P.PROFILES))

print('== 2. dấu ≤ chỉ cho Po/Pk, KHÔNG cho Uk/Io ==')
_ts = {'Tổn hao không tải Po cực đại theo tiêu chuẩn EVN (W)': '52',
       'Tổn hao có tải Pk cực đại theo tiêu chuẩn EVN (W)': '213',
       'Điện áp ngắn mạch Uk (%)': '2',
       'Dòng điện không tải Io (%)': '1'}
qc = R._dong_bang_thong_so_dong({'thong_so_dong': _ts, 'nguon_ky_hieu': '≤',
                                 'nguon_loai_so_lieu': 'quy_chuan_evn'})
kt('Po có dấu ≤', '≤ 52' in qc)
kt('Pk có dấu ≤', '≤ 213' in qc)
kt('Uk KHÔNG có dấu ≤ (bảng TCCS ghi "nhỏ nhất" — Uk là SÀN, không phải trần)',
   '≤ 2' not in qc.replace('≤ 213', ''))
kt('Io KHÔNG có dấu ≤', '≤ 1' not in qc)

print('== 3. nhãn cột theo nguồn ==')
kp = R._dong_bang_thong_so_dong({'thong_so_dong': _ts, 'nguon_ky_hieu': '=',
                                 'nguon_loai_so_lieu': 'catalogue_hang'})
kt('số catalogue hãng KHÔNG dán nhãn "theo tiêu chuẩn EVN"',
   'theo tiêu chuẩn EVN' not in kp)
kt('đổi thành nhãn catalogue hãng', 'catalogue hãng' in kp)
kt('dòng quy chuẩn EVN giữ nguyên nhãn', 'theo tiêu chuẩn EVN' in qc)

print('== 4. tiêu đề: số pha + cấp điện áp + nhãn quyết định ==')
def _r(ma, ten, kva, cap, hang='MBT', ol='outline_may_bien_ap'):
    return {'ma_goc': ma, 'ten_goc': ten, 'cong_suat': kva, 'cap_dien_ap': cap,
            'thuong_hieu': hang, 'outline_id': ol, 'profile_id': 'may_bien_ap_do_luong', 'content_type': 'product'}
t1 = R.dung_tieu_de(_r('TBD1P50', 'Máy biến áp dầu 1Pha 50KVA 12.7/0.23KV Loại Silic', '50', '12.7/0.23', 'THIBIDI'))
t3 = R.dung_tieu_de(_r('TBD3P50', 'Máy biến áp dầu 3Pha 50KVA 22/0.4KV Loại Silic', '50', '22/0.4', 'THIBIDI'))
kt('1 pha và 3 pha KHÔNG còn trùng tiêu đề', t1 != t3)
kt('tiêu đề có số pha', '1 pha' in t1 and '3 pha' in t3)
kt('tiêu đề có cấp điện áp', '12,7/0,23kV' in t1)
a107 = R.dung_tieu_de(_r('MBT3P100A107', 'Máy biến áp dầu 3Pha 100KVA 22/0.4KV Loại Amorphous QĐ 107/QĐ-HĐTV', '100', '22/0.4'))
a2608 = R.dung_tieu_de(_r('MBT3P100A2608', 'Máy biến áp dầu 3Pha 100KVA 22/0.4KV Loại Amorphous', '100', '22/0.4'))
a2608_qc = dict(_r('MBT3P100A2608', 'Máy biến áp dầu 3Pha 100KVA 22/0.4KV Loại Amorphous', '100', '22/0.4'))
a2608_qc['quy_cach'] = '2608/QĐ-EVN SPC'
kt('hai họ Amorphous phân biệt bằng số hiệu quyết định',
   R.dung_tieu_de(a2608_qc) != a107 and 'QĐ 2608' in R.dung_tieu_de(a2608_qc))
kt('vẫn là sentence case, thương hiệu giữ hoa', t1.startswith('Báo giá máy') and 'THIBIDI' in t1)

print('== 5. slug giữ được phần phân biệt ==')
os.environ['SLUG_NGAN'] = '1'
s1, s3 = R.dung_slug(_r('TBD1P50', 'Máy biến áp dầu 1Pha 50KVA 12.7/0.23KV Loại Silic', '50', '12.7/0.23', 'THIBIDI')), \
         R.dung_slug(_r('TBD3P50', 'Máy biến áp dầu 3Pha 50KVA 22/0.4KV Loại Silic', '50', '22/0.4', 'THIBIDI'))
kt('slug 1 pha khác slug 3 pha', s1 != s3)
kt('slug giữ được cụm "loi-silic" (Ver 2.6 cắt 55 ký tự làm mất)', 'silic' in s1)
kt('slug không quá dài', len(s1) <= 110)
os.environ.pop('SLUG_NGAN', None)

print('== 6. meta Rank Math + danh mục ==')
_row = _r('MBT1P15A2608', 'Máy biến áp dầu 1Pha 15KVA 12.7/0.23KV Loại Amorphous', '15', '12.7/0.23')
m = R.dung_rank_math(_row, {'title': R.dung_tieu_de(_row)})
kt('có đủ 3 trường Rank Math',
   set(m) == {'rank_math_focus_keyword', 'rank_math_title', 'rank_math_description'})
kt('SEO title <= 60 ký tự', len(m['rank_math_title']) <= 60)
kt('SEO title KHÔNG đứt giữa dấu ngoặc', not m['rank_math_title'].rstrip().endswith('(lõi'))
kt('meta description <= 160 ký tự', len(m['rank_math_description']) <= 160)
kt('focus keyword bỏ chữ "Báo giá"', not m['rank_math_focus_keyword'].lower().startswith('báo giá'))
kt('KHÔNG bịa số khi record không có Po',
   'tổn hao không tải' not in m['rank_math_description'])
m2 = R.dung_rank_math(dict(_row, ton_hao_khong_tai='14 W'), {'title': R.dung_tieu_de(_row)})
kt('CÓ chèn Po khi record có số thật', 'Po 14 W' in m2['rank_math_description'])
kt('danh mục máy biến áp dầu', R.dung_danh_muc(_row) == ['Máy biến áp', 'Máy biến áp dầu'])
kt('danh mục vỏ bảo vệ',
   R.dung_danh_muc({'outline_id': 'outline_vo_may_bien_ap', 'ten_goc': 'Vỏ mạ kẽm'})
   == ['Phụ kiện máy biến áp', 'Vỏ bảo vệ máy biến áp'])
kt('không suy được thì trả rỗng, KHÔNG đoán bừa',
   R.dung_danh_muc({'outline_id': 'outline_la', 'ten_goc': 'X'}) == [])

print('== 7. tên hàng nhiều dòng bị gộp (vụ MOF) ==')
r = P.normalize_row({'Tên hàng': 'Hợp bộ đo lường (MOF) 24kV\nTỷ số biến dòng: 10-20/5A.'},
                    {'Tên hàng': 'ten_goc'})
kt('gộp xuống dòng thành 1 dòng', '\n' not in r['ten_goc'])
kt('giữ đủ phần phân biệt sau xuống dòng', '10-20/5A' in r['ten_goc'])

print('== 8. biểu đồ so sánh lõi mở cho hãng ngoài THIBIDI ==')
mbt_a = {'ma_goc': 'MBT1P15A107', 'ten_goc': 'Máy biến áp dầu 1Pha 15KVA Loại Amorphous',
         'cong_suat': '15', 'cap_dien_ap': '12.7/0.23', 'thuong_hieu': 'MBT',
         'outline_id': 'outline_may_bien_ap', 'ton_hao_khong_tai': '14'}
mbt_s = dict(mbt_a, ma_goc='MBT1P15',
             ten_goc='Máy biến áp dầu 1Pha 15KVA Loại Silic', ton_hao_khong_tai='52')
kt('KHÔNG có anh em -> không dựng (giữ luật không viết chay)',
   KT.khoi_so_sanh_loi(mbt_a, None) == '')
out = KT.khoi_so_sanh_loi(mbt_a, [mbt_s])
kt('CÓ anh em khác lõi -> dựng được cho MBT', out != '')
kt('dùng đúng số thật 52W và 14W', '52' in out and '14' in out)
kt('không nhận nhầm nguồn là catalogue THIBIDI', 'catalogue THIBIDI' not in out)

print('== 9. Family Router — 3 dương tính giả ==')
kt('"sử dụng" KHÔNG bị nhận là sứ đứng',
   FR.nhan_dien_ho('Module PLC 1 pha (1 công tơ sử dụng 1 module)')[0] != 'su_cach_dien')
kt('"Sứ đứng" thật vẫn nhận đúng',
   FR.nhan_dien_ho('Sứ đứng 24kV')[0] == 'su_cach_dien')
kt('"kiểm định" trong ngoặc là thuộc tính, không phải dịch vụ',
   FR.nhan_dien_ho('Công tơ điện tử 3 pha (Đã bao gồm kiểm định)')[0] != 'dich_vu')
kt('"Thí nghiệm máy biến áp" ngoài ngoặc vẫn là dịch vụ',
   FR.nhan_dien_ho('Thí nghiệm máy biến áp 250kVA')[0] == 'dich_vu')
kt('"Nắp che cho MBA" là phụ trợ, không phải máy biến áp',
   FR.nhan_dien_ho('Nắp che loại tole cho MBA 320kva')[0] == 'phu_tro')
kt('"Giá treo MBT" vẫn là phụ trợ (không bị bản vá làm hỏng)',
   FR.nhan_dien_ho('Giá treo MBT 1 pha')[0] == 'phu_tro')

print('== 10. prompt Enhance nhận cỡ máy ==')
ch = E.mo_ta_cau_hinh(mbt_a)
kt('mô tả cấu hình có số pha và dải công suất', '1 pha' in ch and 'nhỏ' in ch)
kt('máy lớn ra dải khác',
   'lớn' in E.mo_ta_cau_hinh(dict(mbt_a, ten_goc='MBA 3Pha 2000KVA', cong_suat='2000')))
kt('record rỗng -> chuỗi rỗng, không bịa', E.mo_ta_cau_hinh({}) == '')
he, ng, _ = E.xay_prompt_insight('máy biến áp dầu', ['x'], cau_hinh=ch)
kt('quy tắc 5b có trong system prompt', '5b.' in he)
kt('cấu hình có trong user prompt', 'CẤU HÌNH ĐANG XÉT' in ng)
kt('vẫn giữ quy tắc 5 (không nhắc mã hàng)', 'không nhắc tên thương hiệu/mã hàng' in he)

print(f'\n===== KẾT QUẢ: PASS {Pn} / FAIL {Fn} =====')
