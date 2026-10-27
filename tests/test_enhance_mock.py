# -*- coding: utf-8 -*-
"""Test mock cho enhance.py (SONEALEO Ver 1.1) — KHÔNG gọi Google/Gemini
thật (cần API key thật, Thịnh tự chạy tay 1 lần trên máy có key để xác
nhận phần network — xem HUONG-DAN-TEST-ENHANCE.md).

Trọng tâm test: bộ lọc số (loc_bo_muc_co_so) và Hard Block lớp cuối
(enhance_1_san_pham gọi lại render_phase2.kiem_tra_bia) — đây là 2 lớp
phòng thủ chống bịa số, PHẢI test kỹ hơn phần network (network chỉ cần
đúng cú pháp request, không phải rủi ro an toàn dữ liệu).

Chạy: python3 tests/test_enhance_mock.py (từ thư mục gốc)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import enhance as E
import render_phase2 as R

so_pass = 0
so_fail = 0


def kt(ten, dieu_kien):
    global so_pass, so_fail
    if dieu_kien:
        so_pass += 1
        print(f'[PASS] {ten}')
    else:
        so_fail += 1
        print(f'[FAIL] {ten}')


# ---------- Test 1: loc_bo_muc_co_so phải bỏ ý có số, giữ ý không số ----------
insight_ban_dau = {
    'khoang_trong_noi_dung': [
        'Thiếu mục bảo hành và chính sách vận chuyển',          # sạch, giữ
        'Công suất 630kVA phù hợp nhà máy vừa',                  # có số, phải bỏ
    ],
    'cau_hoi_thuong_gap': [
        'Máy biến áp dầu và máy biến áp khô khác nhau thế nào',  # sạch, giữ
        'Tổn hao không tải 780W có cao không',                   # có số, phải bỏ
    ],
    'goc_nhin_bundle_cheo': [
        'Gợi ý kèm tủ RMU và thiết bị đóng cắt trung thế',       # sạch, giữ
    ],
}
sach, so_bo = E.loc_bo_muc_co_so(insight_ban_dau)
kt('loc_bo_muc_co_so bỏ đúng 2 ý có số', so_bo == 2)
kt('loc_bo_muc_co_so giữ đúng 3 ý sạch',
   len(sach['khoang_trong_noi_dung']) == 1 and
   len(sach['cau_hoi_thuong_gap']) == 1 and
   len(sach['goc_nhin_bundle_cheo']) == 1)
kt('ý có số "630kVA" bị loại khỏi khoang_trong_noi_dung',
   'Công suất 630kVA phù hợp nhà máy vừa' not in sach['khoang_trong_noi_dung'])
kt('ý có số "780W" bị loại khỏi cau_hoi_thuong_gap',
   'Tổn hao không tải 780W có cao không' not in sach['cau_hoi_thuong_gap'])

# ---------- Test 2: cụm kỹ thuật kiểu "0.6/1kV" cũng phải bị bắt (không chỉ số đơn) ----------
insight_cum = {
    'khoang_trong_noi_dung': ['Phù hợp lưới 22/0.4kV khu công nghiệp'],
    'cau_hoi_thuong_gap': [],
    'goc_nhin_bundle_cheo': [],
}
sach2, so_bo2 = E.loc_bo_muc_co_so(insight_cum)
kt('cụm kỹ thuật "22/0.4kV" cũng bị bắt (không chỉ số đơn lẻ)', so_bo2 == 1)

# ---------- Test 3: merge_insight_vao_bai không đụng bảng thông số ----------
ai_data_goc = {
    'intro_html': '<p>Máy biến áp dầu 3 pha.</p>',
    'dac_diem_html': '<p>Đặc điểm gốc.</p>',
    'ung_dung_html': '<p>Ứng dụng gốc.</p>',
    'huong_dan_chon_html': '<p>Hướng dẫn gốc.</p>',
    'faq': [{'q': 'Câu hỏi gốc?', 'a': 'Trả lời gốc.'}],
}
insight_test = {
    'khoang_trong_noi_dung': ['Thiếu mục bảo hành'],
    'cau_hoi_thuong_gap': ['Bảo hành bao lâu'],
    'goc_nhin_bundle_cheo': ['Kèm tủ RMU'],
}
ai_data_moi = E.merge_insight_vao_bai(ai_data_goc, insight_test)
kt('merge KHÔNG có key "bang_thong_so" hay "cot_bang" nào bị chèn vào ai_data',
   'bang_thong_so' not in ai_data_moi and 'cot_bang' not in ai_data_moi)
kt('merge giữ nguyên intro_html gốc (không đụng phần không liên quan)',
   ai_data_moi['intro_html'] == ai_data_goc['intro_html'])
kt('merge thêm bullet vào huong_dan_chon_html',
   'Thiếu mục bảo hành' in ai_data_moi['huong_dan_chon_html'])
# Ver 3.5 — SỬA KỲ VỌNG: trước đây bundle chéo bị chèn vào ung_dung_html
# VÀ dựng lại trong goc_nhin_thi_truong_html -> in ra 2 lần trên 1 trang.
# Nay chỉ còn 1 chỗ. Test cũ khoá đúng cái lỗi đó nên phải đổi.
kt('bundle chéo vào ĐÚNG khối Góc nhìn thị trường, KHÔNG vào ung_dung_html',
   'Kèm tủ RMU' in (ai_data_moi.get('goc_nhin_thi_truong_html') or '') and
   'Kèm tủ RMU' not in (ai_data_moi.get('ung_dung_html') or ''))
kt('merge thêm câu hỏi mới vào faq, GIỮ câu hỏi gốc, KHÔNG tự bịa câu trả lời',
   len(ai_data_moi['faq']) == 2 and ai_data_moi['faq'][1]['a'] == '' and
   ai_data_moi['faq'][1].get('_can_ai_viet_lai_bang_data_that') is True)
kt('ai_data_goc KHÔNG bị sửa tại chỗ (merge trả dict mới)',
   ai_data_goc['huong_dan_chon_html'] == '<p>Hướng dẫn gốc.</p>')

# ---------- Test 4: Hard Block lớp cuối — số liệu lạ (không có trong row) phải bị bắt ----------
row_gia_lap = {
    'profile_id': 'may_bien_ap_do_luong', 'outline_id': 'outline_may_bien_ap',
    'ma_goc': 'MBT3P250', 'ten_goc': 'Máy biến áp dầu 3Pha 250KVA 22/0.4KV Loại Silic',
    'thuong_hieu': 'MBT', 'dvt': 'Máy', 'cong_suat': '250 kVA', 'cap_dien_ap': '22/0.4 kV',
}
# giả lập trường hợp bước lọc số bị lọt (VD AI viết số dạng chữ "hai trăm"
# rồi Gemini tự đổi lại thành số khi trả JSON, hoặc lọt qua kẽ regex nào
# đó) — Hard Block CHÍNH phải bắt được, đây là lý do bắt buộc phải chạy
# kiem_tra_bia() lại ở bước cuối, không chỉ dựa loc_bo_muc_co_so.
text_gia_lap_lot = '<ul><li>Phù hợp tải 500kVA trở lên</li></ul>'  # 500kVA không có trong row_gia_lap (row có 250kVA)
chan = R.kiem_tra_bia(text_gia_lap_lot, row_gia_lap)
kt('Hard Block chính bắt được số lạ "500kVA" (không khớp record)', len(chan) > 0)

text_dung = '<ul><li>Phù hợp tải 250kVA trở lên</li></ul>'  # khớp đúng công suất record
chan2 = R.kiem_tra_bia(text_dung, row_gia_lap)
kt('Hard Block chính KHÔNG chặn nhầm số ĐÚNG có trong record', len(chan2) == 0)

# ---------- Test 5: enhance_1_san_pham — lỗi thiếu API key phải báo rõ, không crash ----------
kq = E.enhance_1_san_pham(row_gia_lap, ai_data_goc, 'máy biến áp dầu 3 pha',
                          serper_api_key='', gemini_model='gemini-3.6-flash',
                          gemini_api_key='fake')
kt('enhance_1_san_pham báo lỗi rõ ràng khi thiếu Serper API key (không crash)',
   kq.get('ok') is False and 'Serper' in kq.get('loi', ''))

print(f'\n=== KẾT QUẢ (trước phần Ver 1.2): {so_pass} PASS / {so_fail} FAIL ===')


# ---------- Test 6 (Ver 1.2): chống lặp insight qua DB thật ----------
import tempfile, os as _os
import db_phase2 as DB

_tmp_db = tempfile.mktemp(suffix='.db')
con_test = DB.ket_noi(_tmp_db)

# Lần 1: ghi lịch sử insight cho nhóm "máy biến áp dầu 3 pha"
insight_lan1 = {
    'khoang_trong_noi_dung': ['Thiếu mục bảo hành và chính sách vận chuyển'],
    'cau_hoi_thuong_gap': ['Máy biến áp dầu và máy biến áp khô khác nhau thế nào'],
    'goc_nhin_bundle_cheo': ['Gợi ý kèm tủ RMU và thiết bị đóng cắt trung thế'],
}
so_ghi = DB.ghi_lich_su_insight(con_test, 'máy biến áp dầu 3 pha', 'MBT3P250', insight_lan1)
kt('ghi_lich_su_insight ghi đúng 3 dòng (3 ý insight)', so_ghi == 3)

# Lần 2: SKU khác cùng nhóm -> phải đọc lại được đúng 3 ý vừa ghi
lich_su = DB.lay_lich_su_insight(con_test, 'máy biến áp dầu 3 pha')
kt('lay_lich_su_insight đọc lại đúng 3 ý đã ghi', len(lich_su) == 3 and
   'Thiếu mục bảo hành và chính sách vận chuyển' in lich_su)

# Nhóm KHÁC (VD "cáp điện") -> không được lẫn lịch sử của nhóm máy biến áp
lich_su_nhom_khac = DB.lay_lich_su_insight(con_test, 'cáp điện trung thế')
kt('lay_lich_su_insight KHÔNG lẫn lịch sử giữa 2 nhóm khác nhau', len(lich_su_nhom_khac) == 0)

# Prompt phải chứa đúng câu dặn chống lặp khi có da_dung_truoc
_he_thong, _nguoi_dung, _schema = E.xay_prompt_insight('máy biến áp dầu 3 pha', ['nội dung giả lập'],
                                                        da_dung_truoc=lich_su)
kt('prompt insight có nhét câu dặn CHỐNG LẶP khi có lịch sử',
   'CHỐNG LẶP' in _nguoi_dung and 'Thiếu mục bảo hành và chính sách vận chuyển' in _nguoi_dung)

# enhance_1_san_pham với con=None (mặc định) -> KHÔNG đụng DB, không lỗi (backward compatible Ver 1.1)
kq_khong_con = E.enhance_1_san_pham(row_gia_lap, ai_data_goc, 'máy biến áp dầu 3 pha',
                                    serper_api_key='', gemini_model='gemini-3.6-flash',
                                    gemini_api_key='fake', con=None)
kt('enhance_1_san_pham con=None vẫn chạy bình thường (backward compatible), báo lỗi thiếu Serper key',
   kq_khong_con.get('ok') is False and 'Serper' in kq_khong_con.get('loi', ''))

# ---------- Test 7 (Ver 1.4 — Đợt 3): field boi_canh_su_dung ----------
insight_co_boi_canh = {
    'khoang_trong_noi_dung': [],
    'cau_hoi_thuong_gap': [],
    'goc_nhin_bundle_cheo': [],
    'boi_canh_su_dung': [
        'Phù hợp nhà xưởng vận hành liên tục, cần độ ổn định cao trong thời gian dài',
        'Phù hợp công trình dân dụng quy mô nhỏ, ưu tiên chi phí đầu tư ban đầu thấp',
        'Nhà xưởng B có công suất 500kVA nên chọn dòng này',   # CÓ SỐ — phải bị lọc bỏ
    ],
}
sach3, so_bo3 = E.loc_bo_muc_co_so(insight_co_boi_canh)
kt('loc_bo_muc_co_so áp dụng đúng cho field boi_canh_su_dung (bỏ ý có số)',
   so_bo3 == 1 and len(sach3['boi_canh_su_dung']) == 2)

ai_data_bc = E.merge_insight_vao_bai(
    {'ung_dung_html': '<p>Ứng dụng gốc.</p>'},
    {'boi_canh_su_dung': ['Phù hợp nhà xưởng vận hành liên tục']})
kt('bối cảnh sử dụng chỉ xuất hiện MỘT lần, ở khối Góc nhìn thị trường',
   (ai_data_bc.get('goc_nhin_thi_truong_html') or '').count('Phù hợp nhà xưởng vận hành liên tục') == 1 and
   'Phù hợp nhà xưởng vận hành liên tục' not in (ai_data_bc.get('ung_dung_html') or ''))

# ---------- Test 8 (Ver 1.5 — Đợt 4): lớp chặn từ khoá rủi ro uy tín/khiếu nại ----------
insight_rui_ro = {
    'khoang_trong_noi_dung': ['Thiếu mục bảo hành và chính sách vận chuyển'],  # sạch, giữ
    'cau_hoi_thuong_gap': ['Hãng X dùng có bị cháy nổ không'],                  # rủi ro, phải bỏ
    'goc_nhin_bundle_cheo': ['Nhiều người phản ánh hàng kém chất lượng'],       # rủi ro, phải bỏ
    'boi_canh_su_dung': ['Tránh mua loại rẻ tiền vì hay hỏng vặt'],             # rủi ro, phải bỏ
}
sach4, so_bo4 = E.loc_bo_muc_co_so(insight_rui_ro)
kt('lớp chặn từ khoá rủi ro bỏ đúng 3 ý dính khiếu nại/sự cố, giữ 1 ý sạch',
   so_bo4 == 3 and len(sach4['khoang_trong_noi_dung']) == 1 and
   len(sach4['cau_hoi_thuong_gap']) == 0 and len(sach4['goc_nhin_bundle_cheo']) == 0 and
   len(sach4['boi_canh_su_dung']) == 0)

# prompt phải gắn nhãn [Nguồn cộng đồng] riêng khi có noi_dung_cong_dong
_he_thong2, _nguoi_dung2, _schema2 = E.xay_prompt_insight(
    'máy biến áp dầu 3 pha', ['nội dung thương mại giả lập'],
    noi_dung_cong_dong=['nội dung diễn đàn giả lập'])
kt('prompt gắn nhãn [Nguồn cộng đồng] riêng khi có noi_dung_cong_dong',
   'Nguồn cộng đồng' in _nguoi_dung2 and 'nội dung diễn đàn giả lập' in _nguoi_dung2)
kt('QUY_TAC_INSIGHT có quy tắc 7 về nguồn cộng đồng (không trích than phiền)',
   'Nguồn cộng đồng' in E.QUY_TAC_INSIGHT and 'than phiền' in E.QUY_TAC_INSIGHT)

# tim_kiem_dien_dan phải trả lỗi rõ ràng khi thiếu key (không crash), và
# tự thêm site: filter đúng danh sách diễn đàn cấu hình sẵn
kq_dd = E.tim_kiem_dien_dan('máy biến áp dầu 3 pha', api_key='')
kt('tim_kiem_dien_dan báo lỗi rõ khi thiếu Serper key (không crash)',
   kq_dd.get('ok') is False and 'Serper' in kq_dd.get('loi', ''))

# enhance_1_san_pham với bat_nguon_cong_dong=False (mặc định) -> KHÔNG
# gọi tim_kiem_dien_dan (kiểm bằng cách monkeypatch tạm để đếm số lần gọi)
_dem_goi_dien_dan = {'n': 0}
_goc_tim_dien_dan = E.tim_kiem_dien_dan
def _dem(*a, **kw):
    _dem_goi_dien_dan['n'] += 1
    return _goc_tim_dien_dan(*a, **kw)
E.tim_kiem_dien_dan = _dem
kq_mac_dinh = E.enhance_1_san_pham(row_gia_lap, ai_data_goc, 'máy biến áp dầu 3 pha',
                                   serper_api_key='', gemini_model='gemini-3.6-flash',
                                   gemini_api_key='fake')   # bat_nguon_cong_dong mặc định False
E.tim_kiem_dien_dan = _goc_tim_dien_dan
kt('enhance_1_san_pham KHÔNG gọi tim_kiem_dien_dan khi bat_nguon_cong_dong=False (mặc định, đúng thiết kế opt-in)',
   _dem_goi_dien_dan['n'] == 0)

con_test.close()
_os.remove(_tmp_db)

print(f'\n=== KẾT QUẢ CUỐI CÙNG (gồm Ver 1.2 + 1.4 + 1.5): {so_pass} PASS / {so_fail} FAIL ===')
sys.exit(1 if so_fail else 0)
