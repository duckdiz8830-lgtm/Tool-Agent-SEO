# -*- coding: utf-8 -*-
"""Ver 5.5 — test cho prompts_seo_post.py.

Vá luôn nợ #2 trong bàn giao: Ver 5.4 KHÔNG có test (tests/ dừng ở
test_v53_patch.py). Module post có test ngay từ file đầu tiên.

Chạy: python -m pytest tests/test_seo_post_prompts.py -v
Hoặc chạy thẳng:  python tests/test_seo_post_prompts.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import prompts_seo_post as P


def test_doan_type_tu_khoa_that():
    """Từ khoá lấy từ GSC thật của 8 site, không phải mẫu bịa."""
    mong_doi = {
        'bảng giá dây điện cadivi mới nhất': 'bao_gia',
        'báo giá đầu cáp hộp nối 3M': 'bao_gia',
        'máy biến áp khô là gì': 'complete_guide',
        'so sánh máy biến áp dầu và khô': 'so_sanh',
        'cách chọn tiết diện dây dẫn': 'huong_dan_chon',
        'TCVN 8525:2015': 'tieu_chuan',
        'catalogue cadivi pdf': 'catalogue',
        'top 5 hãng máy biến áp': 'top_list',
        'dự án trạm biến áp 560kVA': 'du_an',
    }
    for kw, mong in mong_doi.items():
        tid, _, _ = P.doan_content_type(kw)
        assert tid == mong, f'"{kw}" -> {tid}, mong đợi {mong}'


def test_bo_dau_khong_gay_voi_chu_d():
    """NFD KHÔNG tách được 'đ' — phải map đ->d trước. Bug đã gặp thật."""
    assert 'dien' in P._bo_dau('điện')
    assert 'dau cap' in P._bo_dau('đầu cáp')
    # regex chứa 'dien' phải khớp được từ khoá có dấu
    tid, _, _ = P.doan_content_type('báo giá dây điện')
    assert tid == 'bao_gia'


def test_tu_khoa_ten_san_pham_khong_ep_thanh_post():
    """74% query toàn hệ là tên sản phẩm thuần — KHÔNG được ép thành bài
    post. Trả mặc định với độ tin cậy THẤP để giao diện cảnh báo."""
    tid, tin_cay, _ = P.doan_content_type('tủ rmu cooper eaton')
    assert tin_cay == 'thap'
    assert tid == 'complete_guide'


def test_chan_thieu_sku_bat_buoc():
    """Món du_lieu_bat_buoc — grep bản 4.x = 0 kết quả. Ở đây có thật."""
    ok, _ = P.kiem_tra_du_dieu_kien('bao_gia', 0)
    assert ok is False
    ok, _ = P.kiem_tra_du_dieu_kien('bao_gia', 212)
    assert ok is True
    # type không cần SKU thì 0 SKU vẫn qua
    ok, _ = P.kiem_tra_du_dieu_kien('complete_guide', 0)
    assert ok is True


def test_xay_prompt_raise_truoc_khi_ton_quota():
    """Free tier 20 request/ngày — phải chặn TRƯỚC khi gọi API."""
    try:
        P.xay_prompt_post('bao_gia', 'bảng giá cáp Cadivi')
        assert False, 'Phải raise ValueError khi thiếu SKU bắt buộc'
    except ValueError as e:
        assert 'BẮT BUỘC gắn SKU' in str(e)


def test_che_do_an_so_khong_ro_gia():
    """CHỐT CHẶN QUAN TRỌNG NHẤT: chế độ ẨN thì AI không được nhìn thấy
    một con số tiền nào, kể cả khi caller lỡ truyền gia_cong_khai vào."""
    gia = {'CVV 2x1.5': '12.500 d/m', 'CVV 2x2.5': '19.800 d/m'}
    _, u, _ = P.xay_prompt_post('bao_gia', 'bảng giá cáp',
                                du_lieu_sku={'Tiết diện': '1.5 - 240 mm2'},
                                che_do_gia='AN', gia_cong_khai=gia)
    assert '12.500' not in u
    assert '19.800' not in u
    # chế độ công khai thì thấy
    _, u2, _ = P.xay_prompt_post('bao_gia', 'bảng giá cáp',
                                 du_lieu_sku={'Tiết diện': '1.5 - 240 mm2'},
                                 che_do_gia='CONG_KHAI', gia_cong_khai=gia)
    assert '12.500' in u2


def test_luat_doi_theo_co_hay_khong_sku():
    """Có SKU -> luật S (truy về ô Excel). Không SKU -> luật K (cấm số cụ
    thể, cho phép kiến thức phổ thông). KHÔNG được bật cả hai."""
    h_co, _, _ = P.xay_prompt_post('top_list', 'top hãng cáp',
                                   du_lieu_sku={'Thương hiệu': 'Cadivi'})
    h_khong, _, _ = P.xay_prompt_post('top_list', 'top hãng cáp')
    assert 'S1.' in h_co and 'K1.' not in h_co
    assert 'K1.' in h_khong and 'S1.' not in h_khong


def test_schema_moi_type_chuyen_duoc_sang_gemini():
    """Schema phải đúng dạng ai_wp_adapter._sang_gemini_schema() hiểu được:
    giá trị là 'string' hoặc list-of-flat-dict. Không lồng sâu hơn."""
    for tid, _, _ in P.danh_sach_type():
        s = P._json_schema_post(tid)
        assert 'meta_title' in s and 'meta_description' in s
        for k, v in s.items():
            if isinstance(v, list):
                assert len(v) == 1 and isinstance(v[0], dict), f'{tid}.{k} sai dạng mảng'
                for ik, iv in v[0].items():
                    assert iv == 'string', f'{tid}.{k}.{ik} lồng quá sâu, Gemini không nhận'
            else:
                assert v == 'string', f'{tid}.{k} sai kiểu'


def test_du_8_type_va_khong_trung_nhan():
    ds = P.danh_sach_type()
    assert len(ds) == 8
    assert len({n for _, n, _ in ds}) == 8
    for _, _, sku in ds:
        assert sku in (P.SKU_BAT_BUOC, P.SKU_TUY_CHON, P.SKU_KHONG)


def test_canh_bao_product_khong_chan():
    """Cảnh báo chỉ trả chuỗi, KHÔNG raise — đăng product là quyết định
    nghiệp vụ đã chốt, tool không được tự chặn."""
    cb = P.canh_bao_che_do_dang('bao_gia', P.DANG_PRODUCT, 212)
    assert 'offers' in cb
    assert P.canh_bao_che_do_dang('bao_gia', P.DANG_POST, 212) == ''


def test_type_sai_bao_loi_ro_rang():
    ok, ly_do = P.kiem_tra_du_dieu_kien('khong_ton_tai', 5)
    assert ok is False and 'không hợp lệ' in ly_do


if __name__ == '__main__':
    ham = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    loi = 0
    for f in ham:
        try:
            f()
            print(f'  PASS  {f.__name__}')
        except AssertionError as e:
            loi += 1
            print(f'  FAIL  {f.__name__}: {e}')
    print(f'\n{len(ham) - loi}/{len(ham)} pass')
    sys.exit(1 if loi else 0)
