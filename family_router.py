# -*- coding: utf-8 -*-
"""
SONEALEO Ver 2.4 — FAMILY ROUTER: nhận diện HỌ SẢN PHẨM từ tên hàng và
kiểm tra chéo với outline mà profiles.py gán.

VÌ SAO CÓ MODULE NÀY
Router cũ (profiles.xac_dinh_outline_id) tin vào profile_id + nhóm nguồn
lấy từ Excel. Nếu Excel xếp nhầm sheet, hoặc nhóm nguồn ghi sai, SKU sẽ
được viết bài như một loại sản phẩm KHÁC HẲN — sai bản chất, không phải
sai câu chữ. Đây là lỗi nặng nhất có thể xảy ra với content kỹ thuật:
đầu cáp bị viết như máy biến áp, vỏ thép bị gọi là máy biến áp...

Router cũ đã vá theo TỪNG CA phát hiện được ("vỏ mạ kẽm", "giá treo") —
kiểu bịt lỗ, không phải nhận diện có hệ thống. Module này bổ sung lớp
KIỂM TRA CHÉO độc lập: đọc TÊN sản phẩm (nguồn đáng tin nhất, do người
nhập viết), suy ra họ sản phẩm, so với outline đang gán.

NGUYÊN TẮC
  - Chỉ CẢNH BÁO + đề xuất, KHÔNG tự ý đổi outline khi không chắc chắn.
    Sai lệch có thể do tên hàng viết tắt lạ, không phải lúc nào Excel
    cũng sai.
  - Chỉ tự sửa khi độ tin cậy CAO và mâu thuẫn rõ ràng (VD tên ghi rõ
    "đầu cáp" mà lại gán outline máy biến áp).
  - Không nhận diện được -> trả None, KHÔNG đoán.
"""
import re
import unicodedata
from chuan_hoa import bo_dau as _bo_dau   # Ver 5.7 — gom 9 bản _bo_dau về 1 nguồn (xem chuan_hoa.py)


# Mỗi họ: (từ khoá BẮT BUỘC có, từ khoá LOẠI TRỪ, outline hợp lệ)
# Thứ tự QUAN TRỌNG: họ hẹp/đặc thù đặt TRƯỚC họ rộng, vì "đầu cáp" chứa
# chữ "cáp" — nếu để họ "cáp điện" trước thì đầu cáp bị nuốt.
# Ver 2.4 — TỪ KHOÁ PHỤ TRỢ: tên chứa các cụm này nghĩa là sản phẩm chỉ
# DÙNG CHO thiết bị kia, KHÔNG PHẢI thiết bị đó. Phát hiện khi quét thật
# 5.264 SKU: "Nắp chụp sứ MBA" bị nhận nhầm là máy biến áp chỉ vì có chữ
# "MBA". Kiểm cụm này TRƯỚC mọi họ khác.
_PHU_TRO = [
    # Ver 3.6.4 — thêm 'nắp che': "Nắp che loại tole cho MBA 320kVA" từng
    # bị nhận là MÁY BIẾN ÁP chỉ vì có chữ MBA (_PHU_TRO có 'nắp chụp'
    # nhưng thiếu 'nắp che').
    r'\bnap\s*chup\b', r'\bnap\s*che\b', r'\bnap\s*day\b',
    r'\bgia\s*treo\b', r'\bgia\s*do\b',
    r'\bke\s*do\b', r'\bgong\b', r'\bbulong\b', r'\boc\b', r'\bday\s*neo\b',
    r'\bphu\s*kien\b', r'\bhop\s*che\b',   # 'vỏ mạ kẽm' ĐÃ có họ riêng chi tiết hơn (vo_may_bien_ap), không gom vào đây
    r'\bthanh\s*(cai|dan)\b', r'\bkep\b', r'\bmoc\b',
]

# Dịch vụ: nhận diện TRƯỚC tất cả — "Thí nghiệm máy biến áp 250kVA" là
# DỊCH VỤ, không phải máy biến áp (phát hiện khi quét thật: 27 ca).
# Ver 3.6.4 — VÁ: "kiểm định" NẰM TRONG NGOẶC là THUỘC TÍNH đi kèm sản
# phẩm ("Công tơ điện tử ... (Đã bao gồm kiểm định)"), không phải dịch vụ.
# Chỉ coi là dịch vụ khi từ khoá đứng NGOÀI ngoặc.
_DICH_VU = [
    r'\bthi\s*nghiem\b', r'\bkiem\s*dinh\b', r'\bsua\s*chua\b',
    r'\bbao\s*duong\b', r'\bbao\s*tri\b', r'\blap\s*dat\b', r'\bdich\s*vu\b',
    r'\bvan\s*chuyen\b', r'\bcong\s*lap\b',
]

HO_SAN_PHAM = [
    ('vo_may_bien_ap', {
        'bat_buoc': [r'\bvo\s*(ma|mz)\s*kem', r'\bvo\s*thung\b', r'\bvo\s*tram\b'],
        'loai_tru': [],
        'outline_hop_le': {'outline_vo_may_bien_ap', 'outline_phu_kien'},
        'nhan': 'Vỏ / thùng bảo vệ',
    }),
    ('dau_cap', {
        'bat_buoc': [r'\bdau\s*cap\b', r'\bhop\s*noi\b', r'\bmang\s*xong\b',
                     r'\bco\s*nhiet\b', r'\bdau\s*co\s*ngot\b'],
        'loai_tru': [],
        'outline_hop_le': {'outline_dau_cap_ky_thuat', 'outline_phu_kien'},
        'nhan': 'Đầu cáp / hộp nối',
    }),
    ('gia_do', {
        'bat_buoc': [r'\bgia\s*treo\b', r'\bgia\s*do\b', r'\bgong\b', r'\bke\s*do\b'],
        'loai_tru': [],
        'outline_hop_le': {'outline_phu_kien'},
        'nhan': 'Giá đỡ / phụ kiện cơ khí',
    }),
    ('may_bien_ap', {
        'bat_buoc': [r'\bmay\s*bien\s*ap\b', r'\bmba\b', r'\bbien\s*ap\s*(dau|kho)\b'],
        'loai_tru': [r'\bvo\b', r'\bgia\s*treo\b', r'\bdau\s*cap\b', r'\bbien\s*dong\b'],
        'outline_hop_le': {'outline_may_bien_ap'},
        'nhan': 'Máy biến áp',
    }),
    ('bien_dong_do_luong', {
        'bat_buoc': [r'\bbien\s*dong\b', r'\bbien\s*ap\s*do\s*luong\b', r'\bti\b', r'\bvt\b'],
        'loai_tru': [],
        'outline_hop_le': {'outline_do_luong', 'outline_phu_kien'},
        'nhan': 'Biến dòng / đo lường',
    }),
    ('tu_dong_cat', {
        'bat_buoc': [r'\btu\s*(dien|rmu|trung\s*the)\b', r'\brmu\b', r'\brecloser\b',
                     r'\blbs\b', r'\bmay\s*cat\b', r'\bdao\s*cach\s*ly\b', r'\bacb\b',
                     r'\bmccb\b', r'\bmcb\b'],
        'loai_tru': [],
        'outline_hop_le': {'outline_tu_dong_cat', 'outline_vo_tu', 'outline_phu_kien'},
        'nhan': 'Tủ / thiết bị đóng cắt',
    }),
    ('cap_dien', {
        'bat_buoc': [r'\bcap\b', r'\bday\b'],
        'loai_tru': [r'\bdau\s*cap\b', r'\bhop\s*noi\b', r'\bgia\s*treo\b',
                     r'\bkep\s*cap\b', r'\bmang\s*xong\b'],
        'outline_hop_le': {'outline_cap_dien', 'outline_phu_kien'},
        'nhan': 'Cáp điện / dây dẫn',
    }),
    ('su_cach_dien', {
        # Ver 3.6.4 — VÁ: r'\bsu\s*(...|dung|...)\b' bắt nhầm chữ "SỬ DỤNG".
        # Bỏ dấu xong "sử dụng" -> "su dung", trùng khít mẫu "sứ đứng".
        # Hậu quả thật: "Module PLC 1 pha (1 công tơ SỬ DỤNG 1 module)" bị
        # xếp thành sứ cách điện. Yêu cầu "sứ" và "đứng" LIỀN NHAU, không
        # cho khoảng trắng tuỳ ý, và loại trừ cụm "sử dụng".
        'bat_buoc': [r'\bsu\s?(cach\s*dien|dung|treo|do)\b', r'\bchong\s*set\b'],
        'cam_cum_co_dau': [r'sử\s+dụng'],
        'loai_tru': [],
        'outline_hop_le': {'outline_phu_kien'},
        'nhan': 'Sứ cách điện / chống sét',
    }),
]


def nhan_dien_ho(ten_hang):
    """Trả (ma_ho, thong_tin_ho) hoặc (None, None) nếu không nhận diện được.

    Duyệt theo THỨ TỰ khai báo — họ hẹp trước họ rộng.

    Ver 2.4 — 2 lớp chặn nhầm ĐẶT TRƯỚC MỌI HỌ (phát hiện khi quét thật
    5.264 SKU, router bản đầu cho ~90 ca false positive):
      1. DỊCH VỤ ("Thí nghiệm máy biến áp 250kVA" là dịch vụ, không phải máy)
      2. PHỤ TRỢ ("Nắp chụp sứ MBA" là phụ kiện dùng CHO máy, không phải máy)
    """
    t = ' ' + _bo_dau(ten_hang) + ' '
    t_co_dau = ' ' + str(ten_hang or '').lower() + ' '

    # bỏ mọi cụm trong ngoặc trước khi dò dịch vụ — trong ngoặc là thuộc
    # tính ("Đã bao gồm kiểm định"), ngoài ngoặc mới là bản chất sản phẩm
    t_ngoai_ngoac = re.sub(r'\([^)]*\)', ' ', t)
    if any(re.search(p, t_ngoai_ngoac) for p in _DICH_VU):
        return 'dich_vu', {'nhan': 'Dịch vụ kỹ thuật',
                           'outline_hop_le': {'outline_service', 'outline_phu_kien'}}
    if any(re.search(p, t) for p in _PHU_TRO):
        return 'phu_tro', {'nhan': 'Phụ kiện / phụ trợ',
                           'outline_hop_le': {'outline_phu_kien', 'outline_vo_may_bien_ap',
                                              'outline_dau_cap_ky_thuat', 'outline_tu_dong_cat',
                                              'outline_do_luong'}}

    for ma_ho, tt in HO_SAN_PHAM:
        if any(re.search(p, t) for p in tt['loai_tru']):
            continue
        # Ver 3.6.4 — 'cam_cum_co_dau': dò trên bản CÒN DẤU.
        # 'sứ đứng' và 'sử dụng' bỏ dấu đều ra 'su dung' — không phân biệt
        # được nữa. Ca thật: "Module PLC ... 1 công tơ SỬ DỤNG 1 module" bị
        # xếp thành sứ cách điện. Chặn bằng bản có dấu thì 'Sứ đứng 24kV'
        # vẫn nhận đúng, chỉ 'sử dụng' bị loại.
        if any(re.search(p, t_co_dau) for p in tt.get('cam_cum_co_dau', [])):
            continue
        if any(re.search(p, t) for p in tt['bat_buoc']):
            return ma_ho, tt
    return None, None


def kiem_tra_cheo(ten_hang, outline_id_dang_gan):
    """Đối chiếu họ suy từ TÊN với outline đang gán.

    Trả dict:
      {'khop': True/False, 'ho': ..., 'nhan': ..., 'outline_de_xuat': ...,
       'muc_do': 'ok' | 'canh_bao' | 'nghiem_trong', 'ly_do': ...}

    - 'ok': khớp, hoặc không nhận diện được họ (không kết luận bừa).
    - 'canh_bao': lệch nhưng outline hiện tại vẫn nằm trong nhóm chấp
      nhận được (VD đầu cáp đang dùng outline_phu_kien — chưa tối ưu
      nhưng KHÔNG sai bản chất).
    - 'nghiem_trong': lệch hẳn họ (VD đầu cáp bị gán outline_may_bien_ap)
      -> bài sẽ viết sai bản chất sản phẩm, PHẢI sửa.
    """
    ma_ho, tt = nhan_dien_ho(ten_hang)
    if not ma_ho:
        return {'khop': True, 'ho': None, 'nhan': None,
                'outline_de_xuat': None, 'muc_do': 'ok',
                'ly_do': 'Không nhận diện được họ từ tên — không kết luận.'}

    if outline_id_dang_gan in tt['outline_hop_le']:
        return {'khop': True, 'ho': ma_ho, 'nhan': tt['nhan'],
                'outline_de_xuat': None, 'muc_do': 'ok', 'ly_do': ''}

    # Lệch: outline đang gán KHÔNG nằm trong nhóm hợp lệ của họ này
    de_xuat = sorted(tt['outline_hop_le'])[0]
    return {'khop': False, 'ho': ma_ho, 'nhan': tt['nhan'],
            'outline_de_xuat': de_xuat, 'muc_do': 'nghiem_trong',
            'ly_do': (f'Tên hàng cho thấy đây là "{tt["nhan"]}" nhưng đang gán '
                      f'outline "{outline_id_dang_gan}" — bài sẽ viết sai bản chất '
                      f'sản phẩm. Đề xuất: "{de_xuat}".')}


def quet_ca_dataset(rows):
    """Quét cả danh sách record, trả list các ca lệch để cảnh báo lúc
    import. KHÔNG tự sửa — người dùng quyết định."""
    lech = []
    for r in rows:
        kq = kiem_tra_cheo(r.get('ten_goc', ''), r.get('outline_id', ''))
        if not kq['khop']:
            lech.append({'ma_goc': r.get('ma_goc', ''), 'ten_goc': r.get('ten_goc', ''),
                         'outline_hien_tai': r.get('outline_id', ''), **kq})
    return lech
