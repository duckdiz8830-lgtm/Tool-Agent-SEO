# -*- coding: utf-8 -*-
"""Test Ver 3.7 — workspace ảnh theo bài, xử lý và đăng."""
import os, sys, tempfile, json
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import workspace_anh as WS
import xu_ly_anh as X

P = F = 0
def kt(t, dk):
    global P, F
    if dk: P += 1; print('  PASS ', t)
    else:  F += 1; print('  FAIL ', t)

from PIL import Image
D = Path(tempfile.mkdtemp())
ROW = {'ma_goc': 'TBD3P250', 'ten_goc': 'Máy biến áp dầu 3Pha 250KVA',
       'profile_id': 'may_bien_ap_do_luong', 'record_id': 'r42'}
TIEU_DE = 'Báo giá máy biến áp dầu THIBIDI 250kVA 3 pha 22/0,4kV (lõi Silic)'
SLUG = 'may-bien-ap-dau-thibidi-250kva-3-pha-silic'

def anh(ten, mau, kt_=(3000, 2000)):
    p = D / ten
    Image.new('RGB', kt_, mau).save(p, quality=95)
    return p

print('== 1. vai trò theo profile, KHÔNG đoán ==')
kt('máy biến áp khai đủ 5 ô', len(WS.ma_vai_tro('may_bien_ap_do_luong')) == 5)
kt('cáp điện CHƯA khai -> rỗng, không bịa vai trò', WS.vai_tro_cua('cap_dien') == [])
kt('tủ đóng cắt chưa khai -> rỗng', WS.vai_tro_cua('tu_va_thiet_bi_dong_cat') == [])
kt('profile lạ -> rỗng, không ném lỗi', WS.vai_tro_cua('khong_ton_tai') == [])
import khoi_anh as KA
# Ver 4.4.1.5 — O_ANH đã xoá; workspace_anh là nguồn sự thật duy nhất.
kt('khoi_anh KHÔNG còn dict O_ANH', not hasattr(KA, 'O_ANH'))
kt('workspace vẫn khai đủ 5 ô',
   sorted(WS.ma_vai_tro('may_bien_ap_do_luong'))
   == ['bien_may', 'can_canh', 'giao_hang', 'hero', 'lap_dat'])

print('== 2. thư mục + meta.json ==')
tm = WS.tao_workspace(D, '03_May_Bien_Ap_Do_Luong', 42, ROW,
                      wp_post_id=1264, title=TIEU_DE, slug=SLUG)
kt('tên thư mục: số dòng - tên đọc được - SKU',
   tm.name.startswith('042 - ') and tm.name.endswith(' - TBD3P250'))
kt('tên thư mục bỏ dấu (an toàn cho Windows)', 'ế' not in tm.name and 'á' not in tm.name)
kt('có meta.json', (tm / 'meta.json').is_file())
m = WS.doc_meta(tm)
kt('meta ghi đủ sku/wp_post_id/slug/profile',
   m['sku'] == 'TBD3P250' and m['wp_post_id'] == 1264 and m['slug'] == SLUG
   and m['profile'] == 'may_bien_ap_do_luong')
kt('gọi lại KHÔNG tạo thư mục trùng',
   WS.tao_workspace(D, '03_May_Bien_Ap_Do_Luong', 42, ROW, title=TIEU_DE) == tm)

print('== 3. rename thư mục KHÔNG làm mồ côi ảnh ==')
kt('tìm được bằng SKU', WS.tim_workspace(D, '03_May_Bien_Ap_Do_Luong', 'TBD3P250') == tm)
moi = tm.parent / 'ten do nguoi dung tu dat hoan toan'
tm.rename(moi); tm = moi
kt('sau khi rename vẫn tìm được (đọc meta.json, không đọc tên thư mục)',
   WS.tim_workspace(D, '03_May_Bien_Ap_Do_Luong', 'TBD3P250') == tm)
kt('SKU không tồn tại -> None',
   WS.tim_workspace(D, '03_May_Bien_Ap_Do_Luong', 'KHONG_CO') is None)

print('== 4. gán ảnh — KHÔNG bắt đổi tên tay ==')
WS.gan_anh(tm, anh('IMG_3827.jpg', (150, 60, 40)), 'hero')
WS.gan_anh(tm, anh('zalo-abc-xyz.jpg', (60, 90, 150)), 'bien_may')
q = WS.quet(tm)
kt('nhận file tên vô nghĩa IMG_3827.jpg', q['o']['hero']['ten_tren_dia'] == 'IMG_3827.jpg')
kt('nhận file tên zalo', q['o']['bien_may']['ten_tren_dia'] == 'zalo-abc-xyz.jpg')
kt('3 ô còn lại vẫn trống', q['thieu'] == ['can_canh', 'lap_dat', 'giao_hang'])
kt('trạng thái đếm đúng', WS.trang_thai_bai(tm)[0] == '2/5')
WS.doi_o(tm, 'hero', 'bien_may')
q = WS.quet(tm)
kt('đổi ảnh giữa 2 ô', q['o']['hero']['ten_tren_dia'] == 'zalo-abc-xyz.jpg')
WS.bo_anh(tm, 'hero')
kt('gỡ ảnh khỏi ô', WS.quet(tm)['o']['hero'] is None)
kt('gỡ KHÔNG xoá file trên đĩa (không tự xoá dữ liệu người dùng)',
   (tm / 'zalo-abc-xyz.jpg').is_file())
WS.gan_anh(tm, tm / 'zalo-abc-xyz.jpg', 'hero')

print('== 5. WebP dưới ngưỡng dung lượng ==')
b, tt = X.sang_webp(tm / 'IMG_3827.jpg')
kt('nén được', b is not None)
kt('rộng tối đa 1200px', tt['rong'] <= 1200)
kt('dưới 150KB', len(b) <= 150 * 1024)
kt('file lỗi -> trả lỗi, không ném exception', X.sang_webp(tm / 'meta.json')[0] is None)

print('== 6. tên file + alt ==')
kt('tên file theo slug + vai trò',
   X.ten_file(SLUG, 'bien_may') == f'{SLUG}-bien-may.webp')
alts = {v: X.alt_text(ROW, v, TIEU_DE) for v in WS.ma_vai_tro('may_bien_ap_do_luong')}
kt('mỗi vai trò một alt KHÁC NHAU (5 alt giống nhau là nhồi từ khoá)',
   len(set(alts.values())) == 5)
kt('alt bỏ chữ "Báo giá"', all(not a.startswith('Báo giá') for a in alts.values()))
kt('alt biển máy nói đúng ngữ cảnh', alts['bien_may'].startswith('Biển máy'))
kt('alt lắp đặt nói đúng ngữ cảnh', 'công trình' in alts['lap_dat'])
kt('record rỗng -> alt rỗng, không bịa', X.alt_text({}, 'hero', '') == '')

print('== 7. thẻ img đúng chuẩn ==')
h0 = X.the_img('u.webp', 'a', 1200, 800, dau_tien=True)
h1 = X.the_img('u.webp', 'a', 1200, 800, dau_tien=False)
kt('ảnh đầu (LCP) KHÔNG lazy-load', 'loading=' not in h0)
kt('ảnh sau CÓ lazy-load', 'loading="lazy"' in h1)
kt('luôn khai width/height (chống giật layout)',
   'width="1200"' in h0 and 'height="800"' in h0)

print('== 8. đăng: chống upload lặp, phát hiện thay ảnh ==')
dem = [0]
def up(p, ten, mime):
    dem[0] += 1
    return 3400 + dem[0], f'https://x.vn/wp/{ten}'
k1 = X.dang_anh_cua_bai(tm, ROW, 's', tieu_de=TIEU_DE, slug=SLUG, upload=up)
kt('lần 1 xử lý cả 2 ảnh', k1['da_xu_ly'] == 2 and k1['ok'])
kt('ảnh gốc chuyển vào _goc/, không xoá', len(list((tm / '_goc').iterdir())) == 2)
kt('trạng thái thành Đã lên Media', WS.trang_thai_bai(tm)[0].startswith('Đã lên Media'))
k2 = X.dang_anh_cua_bai(tm, ROW, 's', tieu_de=TIEU_DE, slug=SLUG, upload=up)
kt('bấm lần 2 KHÔNG upload lại', k2['da_xu_ly'] == 0 and k2['bo_qua'] == 2 and dem[0] == 2)
WS.gan_anh(tm, anh('ANH_MOI.jpg', (10, 200, 10), (2400, 1600)), 'hero')
kt('thay ảnh -> ô hết trạng thái đã lên Media', not WS.trang_thai_bai(tm)[0].startswith('Đã lên Media'))
k3 = X.dang_anh_cua_bai(tm, ROW, 's', tieu_de=TIEU_DE, slug=SLUG, upload=up)
kt('chỉ đăng lại ảnh vừa thay', k3['da_xu_ly'] == 1 and k3['bo_qua'] == 1 and dem[0] == 3)

print('== 9. HTML chèn vào NỘI DUNG bài ==')
html = X.khoi_anh_bai(k3['anh'])
kt('có thẻ figure', '<figure' in html)
kt('có đủ 2 ảnh', html.count('<img') == 2)
kt('rỗng -> không dựng khối', X.khoi_anh_bai([]) == '')

print('== 10. đếm dùng chung, KHÔNG chặn ==')
row2 = dict(ROW, ma_goc='TBD3P400', record_id='r43')
tm2 = WS.tao_workspace(D, '03_May_Bien_Ap_Do_Luong', 43, row2, title='Bài khác')
WS.gan_anh(tm2, D / 'IMG_3827.jpg', 'hero')
h = WS.quet(tm2)['o']['hero'].get('hash_goc')
kt('đếm được số bài khác dùng cùng tấm, KỂ CẢ khi bài kia đã xử lý sang webp',
   WS.dem_dung_chung(D, '03_May_Bien_Ap_Do_Luong', h) >= 1)
kt('vẫn CHO PHÉP gán (chỉ báo, không chặn)', WS.quet(tm2)['o']['hero'] is not None)

print('== 11. meta.json ghi nguyên tử ==')
kt('không để lại file tạm', not list(tm.glob('*.tam')))
kt('meta đọc lại được sau mọi thao tác', WS.doc_meta(tm) is not None)
kt('thư mục không có meta -> quét không ném lỗi',
   WS.doc_meta(D) is None and WS.trang_thai_bai(D / 'khong-ton-tai')[0] == 'CHƯA CÓ THƯ MỤC')

print(f'\n===== KẾT QUẢ: PASS {P} / FAIL {F} =====')
