# -*- coding: utf-8 -*-
"""Ver 5.7 — test CỔNG CHẤT LƯỢNG ẢNH trên đường upload thật.

VÌ SAO CÓ FILE NÀY
    CANH_NGAN_TOI_THIEU = 800 tồn tại từ lâu nhưng CHỈ được gọi từ
    loc_kho_anh(), mà loc_kho_anh() chỉ có 1 người gọi là script CLI
    loc_kho_anh.py (LOC-KHO-ANH.bat). Đường upload thật —
    dang_anh_cua_bai() -> sang_webp() -> them_watermark_webp() — KHÔNG hề
    kiểm kích thước. Ngưỡng 800px trên thực tế là một bước thủ công tự nhớ:
    quên bấm .bat là ảnh mờ lên site như cũ.

    Ver 5.7 đưa cổng vào đúng đường upload. Test này khoá hành vi đó lại.
    Nếu ai gỡ cổng ra (hoặc vô tình đặt nhầm chỗ sau vòng refactor),
    test này phải ĐỎ.

Không gọi mạng — upload được thay bằng hàm giả đếm số lần được gọi.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image

import xu_ly_anh as X
import workspace_anh as WS

_sai = 0


def kt(ten, dieu_kien, ghi_chu=''):
    global _sai
    dat = bool(dieu_kien)
    _sai += 0 if dat else 1
    print(f'  {"PASS" if dat else "FAIL"}  {ten}{("  | " + str(ghi_chu)) if ghi_chu and not dat else ""}')


def _chay(kich_thuoc_theo_vai_tro, nguong_env=None):
    """Dựng workspace, gán ảnh theo kích thước cho trước, chạy upload giả."""
    D = Path(tempfile.mkdtemp())
    row = {'ma_goc': 'SKU-GATE', 'publish_sku': 'SKU-GATE', 'ten_goc': 'MBA',
           'profile_id': 'may_bien_ap_do_luong', 'record_id': 'r-gate'}
    tm = WS.tao_workspace(D, 'S', 1, row, title='MBA', slug='mba')
    vai_tro = WS.ma_vai_tro(row['profile_id'])

    for i, (w, h) in enumerate(kich_thuoc_theo_vai_tro):
        p = D / f'anh{i}.jpg'
        Image.new('RGB', (w, h), (120, 150, 180)).save(p, quality=92)
        WS.gan_anh(tm, p, vai_tro[i])

    da_upload = []

    def up(path, ten, mime, *a, **kw):
        da_upload.append(ten)
        return 900 + len(da_upload), f'https://img/{ten}'

    cu = os.environ.get('ANH_CANH_NGAN_TOI_THIEU')
    if nguong_env is None:
        os.environ.pop('ANH_CANH_NGAN_TOI_THIEU', None)
    else:
        os.environ['ANH_CANH_NGAN_TOI_THIEU'] = str(nguong_env)
    try:
        kq = X.dang_anh_cua_bai(tm, row, 'siteA', tieu_de='MBA', slug='mba', upload=up)
    finally:
        if cu is None:
            os.environ.pop('ANH_CANH_NGAN_TOI_THIEU', None)
        else:
            os.environ['ANH_CANH_NGAN_TOI_THIEU'] = cu
    return kq, da_upload


print('== A. ngưỡng mặc định ==')
kt('mặc định đúng 800px', X.CANH_NGAN_TOI_THIEU == 800, X.CANH_NGAN_TOI_THIEU)
os.environ.pop('ANH_CANH_NGAN_TOI_THIEU', None)
kt('_nguong_canh_ngan() trả 800 khi không set env', X._nguong_canh_ngan() == 800)

print('== B. ảnh DƯỚI ngưỡng bị chặn, KHÔNG upload ==')
kq, up = _chay([(640, 480)])
kt('không gọi upload lần nào', len(up) == 0, up)
kt('không có ảnh nào vào bài', len(kq['anh']) == 0, kq['anh'])
kt('bo_qua_nho đếm đúng 1', kq.get('bo_qua_nho') == 1, kq.get('bo_qua_nho'))
kt('thông báo lỗi nêu kích thước thật', any('640x480' in str(e) for e in kq['loi']), kq['loi'])
kt('thông báo lỗi nêu ngưỡng', any('800' in str(e) for e in kq['loi']), kq['loi'])

print('== C. CẠNH NGẮN mới tính, không phải diện tích ==')
kq, up = _chay([(3000, 500)])
kt('3000x500 (cạnh ngắn 500) bị chặn dù rất rộng', len(up) == 0, up)
kt('bo_qua_nho = 1', kq.get('bo_qua_nho') == 1)

print('== D. ảnh ĐÚNG chuẩn vẫn đi qua bình thường ==')
kq, up = _chay([(1000, 850)])
kt('có gọi upload', len(up) == 1, up)
kt('ảnh vào được bài', len(kq['anh']) == 1, kq['anh'])
kt('bo_qua_nho = 0', kq.get('bo_qua_nho') == 0, kq.get('bo_qua_nho'))

print('== E. đúng ngay TẠI ngưỡng thì cho qua (>=, không phải >) ==')
kq, up = _chay([(800, 800)])
kt('800x800 đi qua', len(up) == 1 and kq.get('bo_qua_nho') == 0, (up, kq.get('bo_qua_nho')))

print('== F. một ảnh xấu KHÔNG kéo chết ảnh tốt ==')
kq, up = _chay([(1000, 900), (300, 200)])
kt('ảnh tốt vẫn lên', len(up) == 1, up)
kt('ảnh xấu bị bỏ', kq.get('bo_qua_nho') == 1, kq.get('bo_qua_nho'))
kt('cờ partial được bật', kq.get('partial') is True, kq)

print('== G. env đè được ngưỡng ==')
kq, up = _chay([(640, 480)], nguong_env=400)
kt('hạ ngưỡng 400 -> 640x480 đi qua', len(up) == 1, up)
kq, up = _chay([(640, 480)], nguong_env=0)
kt('ngưỡng 0 = TẮT cổng -> đi qua', len(up) == 1, up)
kq, up = _chay([(1000, 900)], nguong_env=1500)
kt('nâng ngưỡng 1500 -> 1000x900 bị chặn', len(up) == 0, up)
kt('env rác quay về mặc định 800',
   (os.environ.update({'ANH_CANH_NGAN_TOI_THIEU': 'xyz'}) or X._nguong_canh_ngan()) == 800)
os.environ.pop('ANH_CANH_NGAN_TOI_THIEU', None)

print(f'\nTONG SAI: {_sai}')
raise SystemExit(1 if _sai else 0)
