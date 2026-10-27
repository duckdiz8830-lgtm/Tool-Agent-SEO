# -*- coding: utf-8 -*-
"""Ver 5.5 — test watermark kiểu mới + chốt chặn an toàn của don_anh.

Chạy: python tests/test_v55_anh.py
"""
import io
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('WP_WEBSITE_URL', 'https://maybienapvn.vn')
os.environ.setdefault('WATERMARK_PHONE', '0358 506 151')

import xu_ly_anh as X
import don_anh as DA


def _anh(mau=(250, 250, 250), kt=(1200, 900)):
    from PIL import Image
    b = io.BytesIO()
    Image.new('RGB', kt, mau).save(b, 'WEBP', quality=82)
    return b.getvalue()


# ============================================================ watermark

def test_bon_kieu_deu_chay():
    goc = _anh()
    for kieu in ('ket_hop', 'goc', 'cheo', 'thanh'):
        os.environ['WATERMARK_STYLE'] = kieu
        out, info = X.them_watermark_webp(goc, 'website')
        assert 'warning' not in info, f'{kieu} lỗi: {info.get("warning")}'
        assert len(out) > 0
        assert info['kieu'] == kieu
    os.environ['WATERMARK_STYLE'] = 'ket_hop'


def test_mac_dinh_la_ket_hop():
    os.environ.pop('WATERMARK_STYLE', None)
    assert X.cau_hinh_watermark('website')['kieu'] == 'ket_hop'


def test_watermark_thuc_su_doi_pixel_tren_nen_trang():
    """Lỗi nặng nhất của bản v2: chữ trắng mờ trên ảnh nền trắng gần như
    vô hình. Ảnh catalogue nền trắng chiếm phần lớn kho, nên phải kiểm
    watermark có ĐỔI PIXEL thật không, không chỉ kiểm không crash."""
    from PIL import Image
    os.environ['WATERMARK_STYLE'] = 'ket_hop'
    goc = _anh((252, 252, 252))
    out, _ = X.them_watermark_webp(goc, 'website')
    a = Image.open(io.BytesIO(goc)).convert('L')
    b = Image.open(io.BytesIO(out)).convert('L')
    khac = sum(1 for x, y in zip(a.tobytes(), b.tobytes()) if abs(x - y) > 12)
    ty_le = khac / len(a.tobytes()) * 100
    assert ty_le > 1.5, f'Chỉ {ty_le:.2f}% pixel đổi — watermark quá mờ trên nền trắng'


def test_dao_mau_theo_do_sang_nen():
    """Nền sáng phải dùng chữ tối, nền tối dùng chữ sáng. Không đảo là một
    trong hai loại ảnh mất watermark."""
    assert X._do_sang_trung_binh(_pil(_anh((250, 250, 250)))) > 200
    assert X._do_sang_trung_binh(_pil(_anh((40, 44, 50)))) < 80


def _pil(b):
    from PIL import Image
    return Image.open(io.BytesIO(b))


def test_tat_watermark_tra_nguyen_bytes():
    os.environ['WATERMARK_ENABLED'] = '0'
    goc = _anh()
    out, _ = X.them_watermark_webp(goc, 'website')
    assert out is goc, 'Tắt watermark mà vẫn encode lại = phí CPU và giảm chất lượng'
    os.environ['WATERMARK_ENABLED'] = '1'


def test_sig_doi_khi_doi_kieu():
    """Signature phải đổi khi đổi kiểu, nếu không ảnh cũ không upload lại."""
    os.environ['WATERMARK_STYLE'] = 'goc'
    s1 = X.cau_hinh_watermark('website')['sig']
    os.environ['WATERMARK_STYLE'] = 'ket_hop'
    s2 = X.cau_hinh_watermark('website')['sig']
    assert s1 != s2


def test_watermark_khong_pha_ngan_sach_kb():
    os.environ['WATERMARK_STYLE'] = 'ket_hop'
    out, info = X.them_watermark_webp(_anh(), 'website', kb_toi_da=X.KB_TOI_DA)
    assert info['kb'] <= X.KB_TOI_DA or info.get('over_budget'), \
        f'{info["kb"]} KB vượt ngân sách mà không báo over_budget'


# ============================================================ dọn ảnh — chốt chặn

def test_xoa_vinh_vien_doi_chuoi_xac_nhan():
    """Chốt chặn quan trọng nhất: không có chuỗi xác nhận thì KHÔNG gọi API."""
    kq = DA.xoa_media([1, 2, 3], force=True, chay_thu=False, xac_nhan='')
    assert kq['ok'] is False
    assert DA.XAC_NHAN_XOA in kq['loi']
    kq = DA.xoa_media([1], force=True, chay_thu=False, xac_nhan='xoa vinh vien')
    assert kq['ok'] is False, 'Chuỗi sai hoa/thường vẫn phải chặn'


def test_mac_dinh_la_chay_thu():
    """Mọi hàm phá huỷ phải mặc định chạy thử. Đọc chữ ký hàm, không gọi API."""
    import inspect
    for ham in (DA.go_anh_khoi_bai, DA.xoa_media, DA.xoa_anh_local):
        p = inspect.signature(ham).parameters['chay_thu']
        assert p.default is True, f'{ham.__name__} không mặc định chạy thử'


def test_xoa_media_mac_dinh_khong_force():
    import inspect
    assert inspect.signature(DA.xoa_media).parameters['force'].default is False
    assert inspect.signature(DA.xoa_media).parameters['bo_qua_dang_dung'].default is True


def test_xoa_local_mac_dinh_vao_thung_rac():
    import inspect
    assert inspect.signature(DA.xoa_anh_local).parameters['thung_rac'].default is True


def test_don_local_chay_thu_khong_dung_file():
    tm = tempfile.mkdtemp()
    for i in range(4):
        Path(tm, f'anh-{i}.webp').write_bytes(b'x' * 1200)
    Path(tm, 'ghi-chu.txt').write_text('khong phai anh')
    kq = DA.xoa_anh_local(tm, chay_thu=True)
    assert kq['so_file'] == 4, 'Phải bỏ qua file không phải ảnh'
    assert len(list(Path(tm).glob('*.webp'))) == 4, 'Chạy thử mà mất file!'


def test_don_local_that_chuyen_vao_thung_rac():
    tm = tempfile.mkdtemp()
    for i in range(3):
        Path(tm, f'anh-{i}.webp').write_bytes(b'x' * 900)
    kq = DA.xoa_anh_local(tm, chay_thu=False, thung_rac=True)
    assert kq['so_file'] == 3
    assert len(list(Path(tm).glob('*.webp'))) == 0
    assert len(list(Path(kq['thung_rac']).rglob('*.webp'))) == 3, 'File phải còn trong _da_xoa'


def test_don_local_loc_theo_mau_ten():
    tm = tempfile.mkdtemp()
    Path(tm, 'may-bien-ap-1.webp').write_bytes(b'x' * 500)
    Path(tm, 'cap-dien-1.webp').write_bytes(b'x' * 500)
    kq = DA.xoa_anh_local(tm, mau_ten='may-bien-ap', chay_thu=True)
    assert kq['so_file'] == 1


def test_bo_qua_thu_muc_da_xoa():
    """Không được quét lại chính thùng rác của mình, nếu không chạy 2 lần
    là lồng thư mục vô tận."""
    tm = tempfile.mkdtemp()
    Path(tm, 'a.webp').write_bytes(b'x' * 500)
    DA.xoa_anh_local(tm, chay_thu=False, thung_rac=True)
    kq = DA.xoa_anh_local(tm, chay_thu=True)
    assert kq['so_file'] == 0, 'Đang quét lại file trong _da_xoa/'


if __name__ == '__main__':
    ham = [v for k, v in sorted(globals().items())
           if k.startswith('test_') and callable(v)]
    loi = 0
    for f in ham:
        try:
            f()
            print(f'  PASS  {f.__name__}')
        except AssertionError as e:
            loi += 1
            print(f'  FAIL  {f.__name__}: {e}')
        except Exception as e:
            loi += 1
            print(f'  ERR   {f.__name__}: {type(e).__name__}: {e}')
    print(f'\n{len(ham) - loi}/{len(ham)} pass')
    sys.exit(1 if loi else 0)
