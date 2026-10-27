# -*- coding: utf-8 -*-
"""Test Ver 3.6 — khối sản phẩm đi kèm (vỏ / giá treo <-> máy biến áp)."""
import sys, os, html
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import phu_kien_di_kem as PK

P = F = 0
def kt(t, dk):
    global P, F
    if dk: P += 1; print('  PASS ', t)
    else:  F += 1; print('  FAIL ', t)

def R(ma, ten, kva='', kv='', hang='MBT', gia='', rid=None):
    return {'ma_goc': ma, 'ten_goc': ten, 'cong_suat': kva, 'cap_dien_ap': kv,
            'thuong_hieu': hang, 'gia_list': gia, 'record_id': rid or ma}

may   = R('MBT1P15',    'Máy biến áp dầu 1Pha 15KVA 12.7/0.23KV Loại Silic', '15 kVA', '12.7/0.23 kV', 'MBT', '27950000')
mayA  = R('MBT1P15A107','Máy biến áp dầu 1Pha 15KVA 12.7/0.23KV Loại Amorphous', '15 kVA', '12.7/0.23 kV', 'MBT', '38241000')
vo    = R('MBTVMK1P15', 'Vỏ mạ kẽm nhúng nóng MBA 1P 15KVA 12,7/0,23KV-  MBT', '15 kVA', '12.7/0.23 kV', 'MBT', '980000')
vo_tb = R('TBDVO1P15',  'Vỏ mạ kẽm nhúng nóng MBA 1P 15KVA 12,7/0,23KV - TBD', '15 kVA', '12.7/0.23 kV', 'THIBIDI')
may_tb= R('TBD1P15',    'Máy biến áp dầu 1Pha 15KVA 12.7/0.23KV Loại Silic - TBD', '15 kVA', '12.7/0.23 kV', 'THIBIDI')
may25 = R('MBT1P25',    'Máy biến áp dầu 1Pha 25KVA 12.7/0.23KV Loại Silic', '25 kVA', '12.7/0.23 kV', 'MBT')
gt    = R('KNGTMBA125', 'Giá treo MBT 1x25', '', '', 'VN', '280000')
kho = [may, mayA, vo, vo_tb, may_tb, may25, gt]

print('== 1. phân loại ==')
kt('nhận ra máy biến áp', PK.phan_loai(may) == PK.MAY)
kt('nhận ra vỏ', PK.phan_loai(vo) == PK.VO)
kt('nhận ra giá treo', PK.phan_loai(gt) == PK.GIA_TREO)
kt('không phải 3 loại trên -> None',
   PK.phan_loai(R('EMVOL', 'Đồng hồ Vol CCX2.5 DT96 - EMIC')) is None)

print('== 2. khoá ghép lấy từ CỘT, không từ mã hàng ==')
kt('khoá máy = (pha, kVA, cấp áp)', PK.khoa(may)[0] == (1, 15.0, '12.7/0.23'))
kt('vỏ cùng máy ra cùng khoá', PK.khoa(vo)[0] == PK.khoa(may)[0])
kt('khoá không suy từ tên khi cột đủ dữ liệu', PK.khoa(vo)[1] is False)
kt('"12,7/0,23 kV" và "12.7/0.23 kV" ra cùng khoá',
   PK.khoa(R('X', 'Vỏ MBA 1P 15KVA', '15 kVA', '12,7/0,23kV'))[0] == PK.khoa(vo)[0])

print('== 3. giá treo: suy từ tên, PHẢI gắn cờ ==')
k, suy = PK.khoa(gt)
kt('đọc được "1x25" thành 1 pha 25 kVA', k == (1, 25.0, '12.7/0.23'))
kt('có gắn cờ suy_tu_ten', suy is True)
kt('giá treo không đọc được tên -> None',
   PK.khoa(R('X', 'Giá treo MBT', '', '', 'VN'))[0] is None)

print('== 4. ràng buộc hãng: vỏ là chi tiết cơ khí ==')
ds_vo = PK.tim_di_kem(vo, kho)
kt('vỏ MBT KHÔNG ghép sang máy THIBIDI',
   all(x['ma'] != 'TBD1P15' for x in ds_vo))
kt('vỏ MBT ghép đúng 2 máy MBT cùng 15 kVA',
   sorted(x['ma'] for x in ds_vo) == ['MBT1P15', 'MBT1P15A107'])
kt('vỏ THIBIDI ghép sang máy THIBIDI',
   [x['ma'] for x in PK.tim_di_kem(vo_tb, kho)] == ['TBD1P15'])
kt('giá treo KHÔNG ràng buộc hãng (kết cấu bắt vào cột)',
   'MBT1P25' in [x['ma'] for x in PK.tim_di_kem(gt, kho)])

print('== 5. hai chiều ==')
kt('trang máy thấy vỏ của nó', 'MBTVMK1P15' in [x['ma'] for x in PK.tim_di_kem(may, kho)])
kt('trang vỏ thấy máy của nó', 'MBT1P15' in [x['ma'] for x in ds_vo])
kt('không tự ghép chính nó', all(x['ma'] != 'MBT1P15' for x in PK.tim_di_kem(may, kho)))
kt('lệch kVA thì không ghép', all(x['ma'] != 'MBT1P25' for x in PK.tim_di_kem(may, kho)))

print('== 6. dựng HTML ==')
_st = lambda k: f'class="snl-{k}"'
h_may = PK.khoi_html(may, PK.tim_di_kem(may, kho), _st, html.escape)
h_vo = PK.khoi_html(vo, ds_vo, _st, html.escape)
kt('trang máy: tiêu đề nói về vỏ/giá treo', 'Vỏ và giá treo' in h_may)
kt('trang phụ kiện: tiêu đề nói về máy', 'Lắp cho máy biến áp' in h_vo)
kt('dùng class snl-* của tool, không đẻ CSS riêng',
   'snl-lien_quan_card' in h_vo and '<style' not in h_vo)
# Ver 5.7 — ĐẢO ASSERT. Test cũ đòi khối phụ kiện PHẢI in giá ra HTML.
# Nhưng Ver 4.5 đã cố ý bỏ hẳn việc đọc gia_list ở đây
# (phu_kien_di_kem.py: "BỎ 'gia'. gia_list nằm trong FIELD_CAM_TUYET_DOI"),
# và Ver 4.6.2 phải thêm luật sweep_rac 'gia_list_lo' để đi DỌN giá đã
# lỡ đăng ra ngoài. Nói cách khác test này đang bảo vệ đúng cái lỗ rò
# giá list Lotech. Từ nay assert ngược lại: giá TUYỆT ĐỐI không được ra HTML.
kt('KHÔNG lộ giá list ra HTML (FIELD_CAM_TUYET_DOI)',
   '27.950.000' not in h_vo and '₫' not in h_vo)
kt('danh sách rỗng -> không hiện khối', PK.khoi_html(may, [], _st, html.escape) == '')
kt('SKU không phải máy/vỏ/giá treo -> không hiện khối',
   PK.khoi_html(R('E', 'Đồng hồ Vol'), [], _st, html.escape) == '')

print('== 7. cờ soát lại ==')
kt('liệt kê đúng mã ghép bằng cách đọc tên',
   PK.canh_bao_suy_tu_ten(PK.tim_di_kem(may25, kho)) == ['KNGTMBA125'])
kt('ghép sạch thì không có cờ', PK.canh_bao_suy_tu_ten(ds_vo) == [])

print(f'\n===== KẾT QUẢ: PASS {P} / FAIL {F} =====')
