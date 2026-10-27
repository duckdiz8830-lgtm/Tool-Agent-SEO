# -*- coding: utf-8 -*-
"""BẾP TRƯỞNG — Ver 3.5, bước 1: phân hạng nguyên liệu.

VÌ SAO CÓ FILE NÀY
------------------
Trước đây mọi SKU đều bị ép vào cùng một dàn ý, bất kể nó có bao nhiêu dữ
liệu. SKU chỉ có mỗi cái tên vẫn phải điền đủ bảng 17 dòng + khối biểu đồ
+ khối so sánh -> ba phần tư nội dung là nói vòng vo. Đó là trần chất
lượng, không phải lỗi prompt.

Bếp trưởng đọc "tủ lạnh" của từng SKU trước, rồi mới quyết định nấu món
gì. Bước 1 (file này) chỉ làm phần PHÂN HẠNG. Bước 2 (sinh dàn ý riêng
cho từng hạng) làm sau, dùng lại đúng hàm này — KHÔNG viết lại logic phân
hạng ở chỗ khác, vì hai chỗ cùng tính một thứ là cách chắc chắn nhất để
chúng lệch nhau.

NGUYÊN TẮC
----------
* Thuần Python. KHÔNG gọi AI, KHÔNG đọc mạng, KHÔNG đọc file. Tốn 0 quota.
* Chỉ đọc dữ liệu ĐÃ CÓ trong record (du_lieu_json), không tự suy ra gì.
* Không bịa: thiếu dữ liệu thì hạ hạng, không "ước lượng cho đủ".
"""

import re

# ============================================================ Hạng nguyên liệu
DU = 'DU'        # có số kỹ thuật thật -> viết được trang tra cứu thông số
VUA = 'VUA'      # có định danh (công suất/cấp áp...) nhưng không có số kỹ thuật
DOI = 'DOI'      # gần như chỉ có tên hàng

NHAN_HANG = {
    DU:  ('Đủ',  'Có số kỹ thuật thật — viết được trang tra cứu thông số'),
    VUA: ('Vừa', 'Có định danh, thiếu số kỹ thuật — chuyển sang bài hướng dẫn chọn'),
    DOI: ('Đói', 'Gần như chỉ có tên — bài ngắn, trung thực, 1 CTA'),
}

# Thứ tự để sắp xếp/so sánh (cao hơn = nhiều nguyên liệu hơn)
THU_TU = {DOI: 0, VUA: 1, DU: 2}


# ============================================================ Trục dữ liệu
# Mỗi profile khai 2 nhóm trục:
#   dinh_danh : thiếu -> tụt xuống ĐÓI (không đủ để nói bất cứ điều gì cụ thể)
#   ky_thuat  : có ít nhất 1 -> lên ĐỦ (có số thật để dựng bảng/biểu đồ)
#
# Ver 3.6.4 — KHAI LẠI TOÀN BỘ. Bản đầu tiên khai tên field BỊA
# ('so_loi', 'dien_ap_dinh_muc', 'dong_dinh_muc', 'cap_bao_ve'...) —
# không field nào tồn tại trong profiles.py, chỉ profile máy biến áp là
# khớp vì đó là profile duy nhất được mở ra đọc lúc viết. Hậu quả:
# 5.096/5.264 SKU bị chấm ĐÓI, và con số đó bị báo ra như tình trạng dữ
# liệu trong khi nó là tình trạng của chính đoạn khai báo này.
#
# Toàn bộ tên dưới đây đối chiếu trực tiếp với PROFILES[...]['cot_import'].
# Có test khoá lại: mọi trục phải tồn tại trong cot_import của profile.
_TRUC = {
    'may_bien_ap_do_luong': {
        'dinh_danh': ['cong_suat', 'cap_dien_ap'],
        'ky_thuat': ['ton_hao_khong_tai', 'ton_hao_ngan_mach', 'dien_ap_ngan_mach',
                     'dong_khong_tai', 'hieu_suat_e50', 'tong_khoi_luong',
                     'khoi_luong_dau', 'to_dau_day'],
    },
    'cap_dien': {
        # Tiết diện là thứ đầu tiên khách hỏi khi mua cáp; cấp điện áp
        # quyết định dòng cáp. Thiếu cả hai thì không nói được gì cụ thể.
        'dinh_danh': ['tiet_dien', 'cap_dien_ap'],
        'ky_thuat': ['vat_lieu_ruot', 'vat_lieu_ruot_giai_ma',
                     'loai_cach_dien_giai_ma', 'vo_boc_giai_ma',
                     'giap_bao_ve_giai_ma', 'dac_diem_khac_giai_ma'],
    },
    'tu_va_thiet_bi_dong_cat': {
        # Profile này CHƯA có cột kỹ thuật nào ngoài quy_cach — dòng cắt
        # ngắn mạch, số ngăn, cấp bảo vệ đều chưa được enrich. Khai đúng
        # hiện trạng: hạng ĐỦ của nhóm này chỉ đạt khi có quy cách chi tiết.
        'dinh_danh': ['thuong_hieu'],
        'ky_thuat': ['quy_cach'],
    },
    'phu_kien_va_khac': {
        # Phụ kiện đấu nối: kích thước và đường rò là thông số quyết định
        # lắp vừa hay không — đó mới là "nguyên liệu kỹ thuật" của nhóm này,
        # không phải Po/Pk.
        'dinh_danh': ['thuong_hieu'],
        'ky_thuat': ['duong_kinh_cach_dien', 'kich_thuoc_i', 'kich_thuoc_l',
                     'duong_ro_ngoai_troi', 'tieu_chuan_catalogue', 'test_dien'],
    },
}

# Fallback cho profile chưa khai (tab mới, profile thêm sau): chỉ dựa vào
# số cột động có giá trị. An toàn: không bao giờ ném lỗi vì thiếu khai báo.
_TRUC_MAC_DINH = {'dinh_danh': [], 'ky_thuat': []}

# Từ khoá nhận diện cột động mang SỐ KỸ THUẬT thật (Po/Pk/Uk/Io...).
# Cột enrich đợt sau hay đổi tên ('Po (W, catalogue)', 'Po cực đại theo
# tiêu chuẩn EVN (W)'...) nên bắt theo từ khoá thay vì khớp tên chính xác.
_KHOA_KY_THUAT = re.compile(
    r'tổn hao|ton hao|\bpo\b|\bpk\b|\buk\b|\bio\b|ngắn mạch|ngan mach|'
    r'không tải|khong tai|hiệu suất|hieu suat|khối lượng|khoi luong|'
    r'kích thước|kich thuoc|tổ đấu dây|to dau day|dòng điện danh định|'
    r'dong dien danh dinh',
    re.IGNORECASE)


def _co_gia_tri(v):
    """Ô có dữ liệu thật hay không. Chuỗi rỗng, '-', 'nan', None đều là trống."""
    if v is None:
        return False
    s = str(v).strip()
    return s not in ('', '-', '--', 'nan', 'None', 'N/A', 'n/a', '0')


def _dem_truc(row, ds_truc):
    return [t for t in ds_truc if _co_gia_tri(row.get(t))]


def _cot_dong_ky_thuat(row):
    """Các cột động mang số kỹ thuật (đường cột động của profiles.py).

    Cần thiết vì đợt enrich mới ghi vào cột tên khác với field khai cứng,
    nên nếu chỉ đọc field khai thì 103 SKU vừa enrich sẽ bị chấm là ĐÓI.
    """
    dong = row.get('thong_so_dong') or {}
    if not isinstance(dong, dict):
        return []
    return [k for k, v in dong.items()
            if _co_gia_tri(v) and _KHOA_KY_THUAT.search(str(k))]


def phan_hang(row):
    """Chấm hạng nguyên liệu cho 1 record.

    row: dict du_lieu_json của san_pham_phase2 (hoặc dict đã normalize_row).
    Trả dict — KHÔNG trả chuỗi trần, vì chỗ gọi luôn cần biết VÌ SAO:

        {'hang': 'DU'|'VUA'|'DOI',
         'nhan': 'Đủ'|'Vừa'|'Đói',
         'mo_ta': '...',
         'truc_dinh_danh': [...],   # trục định danh CÓ dữ liệu
         'thieu_dinh_danh': [...],  # trục định danh THIẾU
         'truc_ky_thuat': [...],    # trục kỹ thuật CÓ dữ liệu (kể cả cột động)
         'so_o_co_du_lieu': int,
         'ly_do': 'câu giải thích ngắn, hiện thẳng trên giao diện'}
    """
    profile = (row.get('profile_id') or '').strip()
    truc = _TRUC.get(profile, _TRUC_MAC_DINH)

    co_dd = _dem_truc(row, truc['dinh_danh'])
    thieu_dd = [t for t in truc['dinh_danh'] if t not in co_dd]
    co_kt = _dem_truc(row, truc['ky_thuat']) + _cot_dong_ky_thuat(row)

    tong_o = sum(1 for v in row.values() if _co_gia_tri(v))

    if co_kt and not thieu_dd:
        hang = DU
        ly_do = f'{len(co_kt)} chỉ số kỹ thuật có dữ liệu'
    elif not thieu_dd:
        hang = VUA
        ly_do = 'có định danh nhưng chưa có chỉ số kỹ thuật nào'
    elif co_kt:
        # hiếm: có số kỹ thuật nhưng thiếu định danh -> vẫn chỉ VỪA, vì
        # không biết công suất/cấp áp thì không dựng được bảng so sánh.
        hang = VUA
        ly_do = f'có số kỹ thuật nhưng thiếu: {", ".join(thieu_dd)}'
    else:
        hang = DOI
        ly_do = 'thiếu ' + ', '.join(thieu_dd) if thieu_dd else 'gần như chỉ có tên hàng'

    nhan, mo_ta = NHAN_HANG[hang]
    return {'hang': hang, 'nhan': nhan, 'mo_ta': mo_ta,
            'truc_dinh_danh': co_dd, 'thieu_dinh_danh': thieu_dd,
            'truc_ky_thuat': co_kt, 'so_o_co_du_lieu': tong_o, 'ly_do': ly_do}


def canh_bao(row):
    """Cảnh báo cần người đọc, lấy từ cột 'Ghi chú - Cần kiểm lại' của MASTER.

    Cột này do đợt rà soát Ver 5 sinh ra (Po/Pk nội suy, số Amorphous bị
    chép nhầm từ bảng Silic, lệch công suất trong catalogue KP...). Nó phải
    hiện CẠNH DÒNG DỮ LIỆU, không phải nằm trong nhật ký — cảnh báo trong
    log thì không ai đọc.
    """
    v = row.get('ghi_chu_can_kiem')
    return str(v).strip() if _co_gia_tri(v) else ''


def ky_hieu_so_lieu(row):
    """'≤' nếu Po/Pk là mức quy chuẩn EVN, '=' nếu là số catalogue hãng.

    Po/Pk/Uk trùng khít giữa THIBIDI và MBT vì cả hai in lại cùng bảng quy
    chuẩn EVN — đó là mức TRẦN cho phép, không phải số đo của từng máy.
    In dấu '=' cho số đó là sai sự thật với người mua là kỹ sư.
    """
    v = row.get('nguon_ky_hieu')
    return str(v).strip() if _co_gia_tri(v) else ''


def thong_ke(danh_sach_row):
    """Đếm theo hạng cho thanh tổng quan. Trả dict {hang: số lượng}."""
    dem = {DU: 0, VUA: 0, DOI: 0}
    for r in danh_sach_row:
        dem[phan_hang(r)['hang']] += 1
    return dem
