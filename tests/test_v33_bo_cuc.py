# -*- coding: utf-8 -*-
"""Ver 3.3 — test bố cục A+: chỗ chờ ảnh, biểu đồ, đơn vị kVA, dọn nhãn,
mục lục FAQ, bỏ h2 lặp. Không gọi mạng, không gọi AI."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import khoi_anh as KA
import render_phase2 as R
import kien_thuc_bien_thien as K
import giao_dien_2_5 as G

PASS = FAIL = 0


def kiem(dk, ten):
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if dk else (PASS, FAIL + 1)
    print(f'  {"PASS" if dk else "FAIL"}  {ten}')


ROW = {'profile_id': 'may_bien_ap_do_luong', 'outline_id': 'outline_may_bien_ap',
       'ma_goc': 'TBD3P250', 'thuong_hieu': 'THIBIDI',
       'ten_goc': 'Máy biến áp dầu 3Pha 250KVA 22/0.4KV Loại Silic - TBD',
       'cong_suat': '250 kVA', 'cap_dien_ap': '22/0.4 kV', 'dvt': 'Máy',
       'thong_so_dong': {'Loại lõi (trích từ tên)': 'Silic',
                         'Tổn hao không tải Po (W, catalogue THIBIDI)': '340',
                         'Dòng điện danh định phía hạ áp (A)': '360.8'}}
AI = {'intro_html': '<p>Giới thiệu.</p>', 'dac_diem_html': '<p>Đặc điểm.</p>',
      'ung_dung_html': '<p>Ứng dụng.</p>', 'huong_dan_chon_html': '<p>Chọn công suất.</p>',
      'faq': [{'q': 'Câu hỏi 1?', 'a': 'Trả lời 1.'}]}

print('== 1. Ver 4.4: ô ảnh trống ẩn hoàn toàn ==')
for ma, _so in (('hero', '1'), ('bien_may', '2'), ('can_canh', '3'),
                 ('lap_dat', '4'), ('giao_hang', '5')):
    h = KA.cho_anh(ma)
    kiem(h == '', f'ô trống "{ma}" trả rỗng')
# Ver 4.4.1.5 — O_ANH đã bị XOÁ (chứa toàn văn hướng dẫn chụp ảnh nội bộ,
# code chết từ Ver 4.4). Test cũ so O_ANH với workspace giờ đảo ý: khẳng
# định dict KHÔNG được quay lại. Nguồn sự thật duy nhất về bộ vai trò ảnh
# bây giờ là workspace_anh.ma_vai_tro().
kiem(not hasattr(KA, 'O_ANH'),
     'khoi_anh KHÔNG còn dict O_ANH (hướng dẫn chụp ảnh không thể lọt ra bài)')
kiem(sorted(__import__('workspace_anh').ma_vai_tro('may_bien_ap_do_luong'))
     == ['bien_may', 'can_canh', 'giao_hang', 'hero', 'lap_dat'],
     'workspace_anh vẫn khai đủ bộ 5 vai trò ảnh')
kiem(KA.cho_anh('ma_la') == '', 'mã lạ -> trả rỗng, không dựng bừa')

print('== 2. Biểu đồ sinh từ số catalogue thật ==')
bd = KA.bieu_do_ton_hao(ROW)
kiem('<svg' in bd and '340' in bd, 'biểu đồ tổn hao có cột 340W của SKU này')
kiem('#d0342c' in bd, 'tô đỏ đúng mức đang xem')
kiem('180' in bd and '320' in bd, 'có cả mức lân cận 180 và 320 kVA')
bl = KA.bieu_do_loi(ROW)
kiem('340' in bl and '100' in bl, 'biểu đồ lõi: Silic 340W vs Amorphous 100W')
kiem('2.102' in bl and '8.760' in bl, 'ghi kèm phép tính kWh/năm')
kiem(KA.bieu_do_ton_hao(dict(ROW, thuong_hieu='MBT')) == '',
     'hãng KHÔNG tra được -> không vẽ (không mượn số THIBIDI)')
kiem(KA.bieu_do_loi(dict(ROW, cong_suat='275 kVA')) == '',
     'mức ngoài bảng -> không vẽ, không nội suy')

print('== 3. Đơn vị kVA trong bảng so sánh ==')
kiem(R._don_vi_kva('250') == '250 kVA', 'số trần -> thêm kVA')
kiem(R._don_vi_kva('250 kVA') == '250 kVA', 'đã có đơn vị -> giữ nguyên')
kiem(R._don_vi_kva('250kva') == '250 kVA', 'chuẩn hoá chữ hoa/thường')
kiem(R._don_vi_kva('') == '', 'rỗng -> rỗng')
kiem(R._don_vi_kva('theo yêu cầu') == 'theo yêu cầu', 'không phải số -> giữ nguyên')

print('== 4. Dọn nhãn nội bộ khỏi bảng thông số ==')
kiem(R._nhan_hien_thi('Loại lõi (trích từ tên)') == 'Loại lõi', 'bỏ "(trích từ tên)"')
kiem(R._nhan_hien_thi('Tổn hao không tải Po (W, catalogue THIBIDI)')
     == 'Tổn hao không tải Po (W)', 'giữ đơn vị, bỏ phần nguồn lặp')
kiem(R._nhan_hien_thi('Dòng điện danh định phía hạ áp (A)')
     == 'Dòng điện danh định phía hạ áp (A)', 'nhãn có ĐƠN VỊ giữ nguyên')
kiem(R._nhan_hien_thi('Cấp Điện Áp (kV)') == 'Cấp Điện Áp (kV)', 'không cắt nhầm đơn vị kV')

print('== 5. Khối kiến thức không còn h2 lặp ==')
h = K.tat_ca_khoi(ROW)
kiem(h and '<h2' not in h, 'tat_ca_khoi KHÔNG tự sinh <h2> nữa')
kiem('340W' in h or '340 W' in h.replace('\u00a0', ' '), 'vẫn giữ nội dung số thật')

print('== 6. Mục lục FAQ khớp với section FAQ ==')
bai = G.dung_bai_2_5(ROW, AI, {'hotline': '0903924986'}, bang_thong_so_html='<table></table>',
                     tach_hero=True)
htm = bai['than'] if isinstance(bai, dict) else str(bai)
kiem('id="faq"' in htm and 'Câu hỏi thường gặp' in htm, 'có FAQ -> có cả mục lục lẫn section')
ai_faq_hong = dict(AI, faq=[{'q': 'Hỏi mà thiếu đáp án?', 'a': ''}])
bai2 = G.dung_bai_2_5(ROW, ai_faq_hong, {}, bang_thong_so_html='<table></table>', tach_hero=True)
h2 = bai2['than'] if isinstance(bai2, dict) else str(bai2)
kiem('#faq' not in h2, 'FAQ thiếu đáp án -> mục lục KHÔNG còn link FAQ mồ côi')

print('== 7. Ảnh trống không để vết; ảnh thật chỉ hiện đúng số lượng ==')
kiem('snl-cho-anh' not in htm and 'URL_ANH' not in htm and 'THAY cả khối' not in htm,
     'bố cục 2.5 không còn placeholder/comment URL_ANH')
import xu_ly_anh as XA
real = XA.khoi_anh_bai([
    {'url':'https://x/1.webp','alt':'a','rong':1200,'cao':800,'nhan':'1'},
    {'url':'https://x/2.webp','alt':'b','rong':1200,'cao':800,'nhan':'2'},
    {'url':'https://x/3.webp','alt':'c','rong':1200,'cao':800,'nhan':'3'},
])
kiem(real.count('<figure') == 3 and 'snl-cho-anh' not in real, '3 ảnh thật -> đúng 3 figure, không có 2 ô trống')
kiem('Tổn hao không tải (W)' in htm, 'biểu đồ tổn hao được chèn')

print(f'\n===== KẾT QUẢ: PASS {PASS} / FAIL {FAIL} =====')
sys.exit(1 if FAIL else 0)
