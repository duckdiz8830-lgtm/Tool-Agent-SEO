# -*- coding: utf-8 -*-
"""
Phase 2 Lite — Profile Registry + Outline Registry.

Không tạo class Python cho từng profile — dùng dict theo đúng chốt kiến trúc
(ARCHITECTURE-DRAFT-4-PROFILES.md mục 2). File này KHÔNG đụng gì tới
dulieu.py/autopost.py/prompts.py/cauhinh.py cũ — đó vẫn là nhánh RMU cũ, chạy
nguyên vẹn qua import_rmu_legacy() (xem nhap_phase2.py).

Bốn profile CỐ ĐỊNH cho Phase 2 Lite, không tự thêm/đoán profile mới:
    cap_dien, tu_va_thiet_bi_dong_cat, may_bien_ap_do_luong, phu_kien_va_khac
"""
import re
import math
from chuan_hoa import bo_dau as _bo_dau   # Ver 6.0 — nguồn bỏ dấu duy nhất (xem chuan_hoa.py)

# ============================================================ normalize_cell
def normalize_cell(v):
    """Chuẩn hoá 1 ô dữ liệu đọc từ Excel (pandas/openpyxl), chạy NGAY LÚC
    IMPORT, một lần duy nhất (ARCHITECTURE mục 1.1).

    - None / NaN (float)   -> ''
    - số (int/float)       -> chuỗi chuẩn, không có '.0' thừa nếu là số nguyên
    - text                 -> strip khoảng trắng 2 đầu

    Sau bước này, mọi nơi khác trong code (prompt, bảng HTML, schema,
    validator) CHỈ đọc giá trị đã qua hàm này — không tự gọi lại
    `(row.get(k) or '').strip()` trên dữ liệu pandas thô.
    """
    if v is None:
        return ''
    if isinstance(v, float) and math.isnan(v):
        return ''
    if isinstance(v, bool):
        # bool là subclass của int trong Python, phải chặn trước nhánh int/float
        return 'Đúng' if v else 'Sai'
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else str(v)
    return str(v).strip()


# ============================================================ Ver 2.8 — Dynamic Schema
# Cột NỘI BỘ / KIỂM DUYỆT — TUYỆT ĐỐI không được lọt vào bài viết. Đây là
# lớp chặn cho cơ chế quét động: thêm cột mới vào Excel thì tool tự đọc,
# nên phải chặn theo DANH SÁCH LOẠI TRỪ chứ không phải danh sách cho phép.
# Nếu không có lớp này, AI sẽ viết ra "sản phẩm này bị nghi ngờ phân loại
# sai" hay giá vốn lên trang bán hàng.
_TU_KHOA_COT_NOI_BO = [
    'giá', 'gia list', 'ghi chú', 'ghi chu', 'kiểm duyệt', 'kiem duyet',
    'nghi ngờ', 'nghi ngo', 'trùng mã', 'trung ma', 'độ tin cậy', 'do tin cay',
    'trạng thái', 'trang thai', 'nguồn', 'nguon', 'nhóm nguồn', 'nhom nguon',
    'internal', 'note', 'reviewer', 'audit', 'delta', 'changelog',
    'binding', 'claim id', 'source row', 'match', 'issue', 'coverage',
    'evidence', 'confidence', 'status', 'sku trùng', 'publish_sku',
    # Ver 2.8 — metadata do tool enrich bên ngoài sinh ra (phát hiện khi
    # chạy thật trên MASTER Ver7: 245/245 SKU có 7 cột kiểu này, toàn
    # metadata chứ không phải thông số kỹ thuật).
    'catalog ', 'catalog_', 'product id', 'product_id', 'row hash',
    'schema version', 'last enriched', 'profile ids', ' count',
    'hash', 'version', 'enriched', 'grade', 'timestamp', 'updated at',
]


def _la_cot_noi_bo(ten_cot):
    t = str(ten_cot or '').strip().lower()
    return any(k in t for k in _TU_KHOA_COT_NOI_BO)


def quet_cot_dong(raw_row, cot_import):
    """Ver 2.8 — quét MỌI cột Excel có giá trị mà CHƯA được khai báo trong
    cot_import, trả dict {tên cột: giá trị} để đưa cho AI.

    VÌ SAO: trước 2.8 danh sách cột khai CỨNG trong PROFILES — enrich Excel
    thêm 20 cột mới thì tool vẫn chỉ đọc đúng cột đã khai, data nằm chết
    trong file. Giờ thêm cột nào là bài dùng được cột đó, không cần sửa code.

    HAI LỚP CHẶN:
      1. Bỏ cột nội bộ/kiểm duyệt (_la_cot_noi_bo) — không để giá vốn hay
         ghi chú audit lọt lên trang bán hàng.
      2. Bỏ giá trị quá dài (>200 ký tự) — thường là ghi chú tự do, không
         phải thông số kỹ thuật.
    """
    da_khai = set(cot_import.keys())
    ra = {}
    for ten_cot, gia_tri in (raw_row or {}).items():
        if ten_cot in da_khai or _la_cot_noi_bo(ten_cot):
            continue
        v = normalize_cell(gia_tri)
        if not v or len(v) > 200:
            continue
        ra[str(ten_cot).strip()] = v
    return ra


def normalize_row(raw_row, cot_import):
    """raw_row: dict {tên cột Excel: giá trị pandas thô}.
    cot_import: dict {tên cột Excel: field nội bộ} của 1 profile.
    Trả dict {field nội bộ: chuỗi đã normalize}.

    Ver 2.8 — thêm khoá `thong_so_dong`: mọi cột Excel CÓ GIÁ TRỊ mà chưa
    khai báo, đã lọc cột nội bộ. Cột đã khai vẫn đi đường cũ (có tên field
    ổn định để code khác dùng); cột lạ đi đường động.
    """
    ra = {field: normalize_cell(raw_row.get(ten_cot))
          for ten_cot, field in cot_import.items()}

    # Ver 3.6.4 — GỘP XUỐNG DÒNG trong Tên hàng thành một dòng.
    # Bug thật, chỉ lộ ra trên WordPress: 9 SKU MOF Young-hwa có tên 3 dòng
    #     Hợp bộ đo lường (MOF) 24kV
    #     Tỷ số biến dòng: 10-20/5A.
    #     Tỷ số biến áp: 22:√3/0,1:√3kV
    # WordPress lấy DÒNG ĐẦU làm tiêu đề, phần sau rơi rụng -> 7 sản phẩm
    # cùng một tên "Hợp bộ đo lường (MOF) 24kV", trong khi trong MASTER
    # chúng khác nhau hoàn toàn. Tool không sinh trùng, dữ liệu bị cắt cụt.
    # Gộp về một dòng thì tiêu đề, slug, meta, alt ảnh đều lấy được đủ.
    if ra.get('ten_goc'):
        ra['ten_goc'] = re.sub(r'\s*[\r\n]+\s*', ' · ', ra['ten_goc']).strip(' ·')
        ra['ten_goc'] = re.sub(r'\s{2,}', ' ', ra['ten_goc'])
    dong = quet_cot_dong(raw_row, cot_import)
    if dong:
        ra['thong_so_dong'] = dong
    return ra


# ============================================================ Profile Registry
PROFILES = {
    'cap_dien': {
        'nhan': 'Cáp điện',
        'cot_import': {
            'Mã hàng': 'ma_goc',
            'Tên hàng': 'ten_goc',
            'Nhãn Hiệu / Xuất Xứ': 'thuong_hieu',
            'Quy Cách / Áp Lực': 'quy_cach',
            'ĐVT': 'dvt',
            'Giá List (VNĐ)': 'gia_list',
            'Ghi Chú Ban Đầu': 'ghi_chu_ban_dau',
            'Nhóm Nguồn': 'nhom_nguon',
            'Tiết Diện (mm²)': 'tiet_dien',
            'Cấp Điện Áp': 'cap_dien_ap',
            'Vật Liệu Ruột': 'vat_lieu_ruot',
            # Ver 5.3 — cột nút "Tải Catalogue/Datasheet" (C10, xem đề xuất
            # DE-XUAT-TOAN-DIEN). KHÔNG BẮT BUỘC (xem cot_bat_buoc bên
            # dưới) — MASTER hiện CHƯA có cột này, để trống toàn bộ tới
            # khi Thịnh có file PDF thật; nút chỉ hiện khi field có giá
            # trị (khoi_nut_catalogue, render_phase2.py).
            'Catalogue PDF URL': 'catalogue_pdf_url',
            # Ver 2.0 — 7 field GIẢI MÃ ký hiệu cấu tạo từ Tên hàng (VD
            # "CXV/DSTA" -> ruột đồng/cách điện XLPE/giáp thép), theo quy
            # ước ngành công khai TCVN 5935/6610, IEC 60227/60502 — verify
            # qua 8 nguồn web độc lập (01/08/2026, xem NHAT-KY-THAY-DOI.md).
            # Chạy trên 3.387 dòng thật: 72.5% có ruột+cách điện (độ tin
            # cậy CAO), 17.7% thêm giáp bảo vệ, 33.3% thêm đặc điểm khác.
            # KHÔNG BẮT BUỘC (23% mã lạ, KHÔNG đoán, để trống đúng thiết
            # kế) — tên cột PHẢI khớp CHÍNH XÁC file
            # 5MASTER_ENRICHED_Ver5.xlsx (sheet 01_Cap_Dien, 7 cột cuối).
            'Vật liệu ruột (giải mã)': 'vat_lieu_ruot_giai_ma',
            'Loại cách điện (giải mã)': 'loai_cach_dien_giai_ma',
            'Vỏ bọc (giải mã)': 'vo_boc_giai_ma',
            'Giáp bảo vệ (giải mã)': 'giap_bao_ve_giai_ma',
            'Đặc điểm khác (giải mã)': 'dac_diem_khac_giai_ma',
            # 2 field CUỐI là METADATA về quá trình giải mã (độ tin cậy,
            # nguồn) — KHÔNG phải nội dung kỹ thuật, đưa vào cot_noi_bo
            # (không hiện bảng thông số, không đưa cho AI viết) đúng như
            # gia_list/ghi_chu_ban_dau.
            'Độ tin cậy giải mã': 'do_tin_cay_giai_ma',
            'Nguồn giải mã': 'nguon_giai_ma',
            # Ver 4.6 — thông số ĐIỆN bóc từ catalogue CADIVI hạ thế. Dữ liệu
            # này đã nằm trong MASTER (1.217 SKU có dòng định mức, 1.646 có
            # điện trở DC) nhưng cot_import không khai nên KHÔNG có đường vào
            # bài — nằm chết suốt từ lúc bóc catalogue.
            'Dong dien dinh muc (A) [catalogue]': 'dong_dien_dinh_muc_catalogue',
            'Kieu lap dat cua dong dinh muc [catalogue]': 'kieu_lap_dat_catalogue',
            'Do sut ap (mV/A/m) [catalogue]': 'do_sut_ap_catalogue',
            'Dieu kien quy chieu dong tai [catalogue]': 'dieu_kien_quy_chieu_catalogue',
            'Dien tro DC toi da 20C (Ohm/km) [catalogue]': 'dien_tro_dc_catalogue',
            'Duong kinh ruot dan (mm) [catalogue]': 'duong_kinh_ruot_dan_catalogue',
            'Nhom ruot dan [catalogue]': 'nhom_ruot_dan_catalogue',
            'Nguon du lieu catalogue': 'nguon_du_lieu_catalogue',
        },
        'cot_bat_buoc': [
            'Mã hàng', 'Tên hàng', 'Nhãn Hiệu / Xuất Xứ', 'Quy Cách / Áp Lực',
            'ĐVT', 'Giá List (VNĐ)', 'Ghi Chú Ban Đầu', 'Nhóm Nguồn',
            'Tiết Diện (mm²)', 'Cấp Điện Áp', 'Vật Liệu Ruột',
        ],
        'cot_noi_bo': ['gia_list', 'ghi_chu_ban_dau', 'nhom_nguon',
                       'do_tin_cay_giai_ma', 'nguon_giai_ma'],
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt',
                   'tiet_dien', 'cap_dien_ap', 'vat_lieu_ruot',
                   'vat_lieu_ruot_giai_ma', 'loai_cach_dien_giai_ma',
                   'vo_boc_giai_ma', 'giap_bao_ve_giai_ma', 'dac_diem_khac_giai_ma',
                   # Ver 4.6 — cho AI thấy thông số điện để viết mô tả bám số
                   # thật, thay vì viết chung chung giống nhau giữa các SKU.
                   'dong_dien_dinh_muc_catalogue', 'kieu_lap_dat_catalogue',
                   'do_sut_ap_catalogue', 'dien_tro_dc_catalogue'],
        'cot_bang': [
            ('ma_goc', 'Mã hàng'), ('thuong_hieu', 'Thương hiệu'),
            ('tiet_dien', 'Tiết diện (mm²)'), ('cap_dien_ap', 'Cấp điện áp'),
            ('vat_lieu_ruot', 'Vật liệu ruột'), ('quy_cach', 'Quy cách'),
            ('dvt', 'Đơn vị tính'),
            # Ver 2.0 — chỉ hiện khi có giải mã (bang_thong_so() tự bỏ
            # dòng trống, đúng pattern field catalogue máy biến áp Ver 5.4)
            ('vat_lieu_ruot_giai_ma', 'Vật liệu ruột (giải mã ký hiệu)'),
            ('loai_cach_dien_giai_ma', 'Loại cách điện (giải mã ký hiệu)'),
            ('vo_boc_giai_ma', 'Vỏ bọc (giải mã ký hiệu)'),
            ('giap_bao_ve_giai_ma', 'Giáp bảo vệ (giải mã ký hiệu)'),
            ('dac_diem_khac_giai_ma', 'Đặc điểm khác (giải mã ký hiệu)'),
            # Ver 4.6 — thông số ĐIỆN. Đây là thứ người mua tra, khác nhau
            # giữa từng SKU. 12 dòng cũ toàn nhận dạng và giải mã ký hiệu,
            # không dòng nào là thông số điện.
            ('dong_dien_dinh_muc_catalogue', 'Dòng điện định mức (A)'),
            ('kieu_lap_dat_catalogue', 'Kiểu lắp đặt của dòng định mức'),
            ('do_sut_ap_catalogue', 'Độ sụt áp (mV/A/m)'),
            ('dien_tro_dc_catalogue', 'Điện trở DC tối đa ở 20 °C (Ω/km)'),
            ('duong_kinh_ruot_dan_catalogue', 'Đường kính ruột dẫn (mm)'),
            ('nhom_ruot_dan_catalogue', 'Nhóm ruột dẫn'),
        ],
        'outline_id_mac_dinh': 'outline_cap_dien',
        'content_type': 'product',
    },
    'tu_va_thiet_bi_dong_cat': {
        'nhan': 'Tủ và thiết bị đóng cắt',
        'cot_import': {
            'Mã hàng': 'ma_goc',
            'Tên hàng': 'ten_goc',
            'Nhãn Hiệu / Xuất Xứ': 'thuong_hieu',
            'Quy Cách / Áp Lực': 'quy_cach',
            'ĐVT': 'dvt',
            'Giá List (VNĐ)': 'gia_list',
            'Ghi Chú Ban Đầu': 'ghi_chu_ban_dau',
            'Nhóm Nguồn': 'nhom_nguon',
            'Catalogue PDF URL': 'catalogue_pdf_url',   # Ver 5.3 — tuỳ chọn, xem ghi chú ở cap_dien
        },
        'cot_bat_buoc': [
            'Mã hàng', 'Tên hàng', 'Nhãn Hiệu / Xuất Xứ', 'Quy Cách / Áp Lực',
            'ĐVT', 'Giá List (VNĐ)', 'Ghi Chú Ban Đầu', 'Nhóm Nguồn',
        ],
        'cot_noi_bo': ['gia_list', 'ghi_chu_ban_dau', 'nhom_nguon'],
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
        'cot_bang': [('ma_goc', 'Mã hàng'), ('thuong_hieu', 'Thương hiệu'),
                     ('quy_cach', 'Quy cách'), ('dvt', 'Đơn vị tính')],
        'outline_id_mac_dinh': 'outline_tu_dong_cat',
        'content_type': 'product',
    },
    'may_bien_ap_do_luong': {
        'nhan': 'Máy biến áp & đo lường',
        'cot_import': {
            'Mã hàng': 'ma_goc',
            'Tên hàng': 'ten_goc',
            'Nhãn Hiệu / Xuất Xứ': 'thuong_hieu',
            'Quy Cách / Áp Lực': 'quy_cach',
            'ĐVT': 'dvt',
            'Giá List (VNĐ)': 'gia_list',
            'Ghi Chú Ban Đầu': 'ghi_chu_ban_dau',
            'Nhóm Nguồn': 'nhom_nguon',
            'Công Suất (kVA)': 'cong_suat',
            'Cấp Điện Áp (kV)': 'cap_dien_ap',
            'Catalogue PDF URL': 'catalogue_pdf_url',   # Ver 5.3 — tuỳ chọn, xem ghi chú ở cap_dien
            # Ver 5.4 — 10 cột enrich THẬT từ catalog_may_bien_ap_dau_mbt.pdf
            # (15 SKU MBT đợt đầu). KHÔNG bắt buộc — SKU chưa enrich vẫn import
            # bình thường, field trống, bang_thong_so() tự bỏ dòng trống.
            'Tổ đấu dây (catalogue)': 'to_dau_day',
            'Tổn hao không tải Po (W, catalogue)': 'ton_hao_khong_tai',
            'Tổn hao ngắn mạch Pk (W, catalogue)': 'ton_hao_ngan_mach',
            'Dòng điện không tải Io (%, catalogue)': 'dong_khong_tai',
            'Điện áp ngắn mạch Uk (%, catalogue)': 'dien_ap_ngan_mach',
            'Hiệu suất năng lượng tối thiểu E50 (catalogue)': 'hieu_suat_e50',
            'Kích thước A (mm, catalogue)': 'kich_thuoc_a',
            'Kích thước B (mm, catalogue)': 'kich_thuoc_b',
            'Kích thước C (mm, catalogue)': 'kich_thuoc_c',
            'Kích thước D (mm, catalogue)': 'kich_thuoc_d',
            'Khối lượng dầu (kg, catalogue)': 'khoi_luong_dau',
            'Tổng khối lượng (kg, catalogue)': 'tong_khoi_luong',
            # Ver 5.4 — Bảo hành/Chứng nhận: MASTER hiện CHƯA có cột này (0
            # dòng có dữ liệu) — khai báo sẵn để khi Thịnh xác nhận policy thật
            # và thêm cột, tool đọc ngay không cần sửa code lần 2. Tới lúc đó
            # field trống -> khoi_bao_hanh_chung_nhan() trả rỗng, không hiện
            # khối này (không bịa số tháng bảo hành/tên chứng nhận không nguồn).
            'Bảo hành (tháng)': 'bao_hanh_thang',
            'Chứng nhận (CO/CQ/Quatest)': 'chung_nhan',
            # Ver 3.5 — 3 cột phân loại nguồn số liệu (MASTER Ver5).
            # Phải KHAI ở đây chứ không để đi đường cột động, vì tên cột có
            # chữ 'Nguồn'/'Ghi chú' -> _la_cot_noi_bo() lọc bỏ, không tới
            # được du_lieu_json. Khai rồi thì bep_truong đọc được, mà vẫn
            # KHÔNG in ra bài (không nằm trong 'cot_bang').
            'Nguồn - Loại số liệu Po/Pk/Uk': 'nguon_loai_so_lieu',
            'Nguồn - Ký hiệu hiển thị Po/Pk': 'nguon_ky_hieu',
            # Ver 3.9 C3 — cột CÓ THẬT trong MASTER Ver8; giữ riêng để renderer
            # in đúng ghi chú nguồn A2608, không hard-code văn bản thay cho data.
            'Nguồn - Tiêu chuẩn viện dẫn': 'nguon_tieu_chuan_vien_dan',
            'Ghi chú - Cần kiểm lại': 'ghi_chu_can_kiem',
            # Ver 4.5 — hậu tố phân biệt slug, do tien_kiem_slug.py sinh ra cho
            # những dòng còn trùng URL. KHÔNG bắt buộc, để trống là bình thường.
            'Hậu tố slug': 'hau_to_slug',
            # Ver 4.5 — slug DÙNG NGUYÊN VĂN. tien_kiem_slug.py sinh ra, bảo đảm
            # không trùng và giữ nguyên slug của bài đã đăng. Trống -> tool tự
            # tính như cũ (hành vi 3.9 không đổi).
            'Slug chỉ định': 'slug_chi_dinh',
        },
        'cot_bat_buoc': [
            'Mã hàng', 'Tên hàng', 'Nhãn Hiệu / Xuất Xứ', 'Quy Cách / Áp Lực',
            'ĐVT', 'Giá List (VNĐ)', 'Ghi Chú Ban Đầu', 'Nhóm Nguồn',
            'Công Suất (kVA)', 'Cấp Điện Áp (kV)',
        ],
        'cot_noi_bo': ['gia_list', 'ghi_chu_ban_dau', 'nhom_nguon'],
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt', 'cong_suat', 'cap_dien_ap',
                   'to_dau_day', 'ton_hao_khong_tai', 'ton_hao_ngan_mach', 'dong_khong_tai',
                   'dien_ap_ngan_mach', 'hieu_suat_e50', 'kich_thuoc_a', 'kich_thuoc_b',
                   'kich_thuoc_c', 'kich_thuoc_d', 'khoi_luong_dau', 'tong_khoi_luong',
                   # Ver 4.9.9 — field TÍNH BẰNG CODE (tinh_delta_context() trong
                   # render_phase2.py), KHÔNG có trong Excel/cot_import — chỉ đưa
                   # vào prompt AI, KHÔNG đưa vào cot_bang (không phải cột bảng
                   # thông số). Đăng ký ở đây để Hard Block (_kho_cua_dong/
                   # _kho_mo_rong_cua_dong) nhận số trong các field này là 'có
                   # nguồn thật', không chặn nhầm.
                   'tier_cong_suat', 'sku_lien_ke_nho', 'sku_lien_ke_lon',
                   'chenh_lech_nho', 'chenh_lech_lon', 'tai_uoc_tinh',
                   # Ver 4.3.1 — field CODE bóc từ Tên hàng cho vỏ/phụ kiện MBA.
                   # Không có trong Excel; trống nếu tên không đủ pha+kVA+điện áp.
                   'may_tuong_thich'],
        'cot_bang': [('ma_goc', 'Mã hàng'), ('thuong_hieu', 'Thương hiệu'),
                     ('cong_suat', 'Công suất (kVA)'), ('cap_dien_ap', 'Cấp điện áp (kV)'),
                     ('dvt', 'Đơn vị tính'),
                     # Ver 5.4 — chỉ hiện khi SKU có enrich thật (bang_thong_so()
                     # tự bỏ dòng trống), theo đúng review Thịnh nhận: "bảng
                     # thông số quá sơ sài, thiếu tổ đấu dây/tổn hao/kích thước".
                     ('to_dau_day', 'Tổ đấu dây'),
                     ('ton_hao_khong_tai', 'Tổn hao không tải Po (W)'),
                     ('ton_hao_ngan_mach', 'Tổn hao ngắn mạch Pk (W)'),
                     ('dong_khong_tai', 'Dòng điện không tải Io (%)'),
                     ('dien_ap_ngan_mach', 'Điện áp ngắn mạch Uk (%)'),
                     ('hieu_suat_e50', 'Hiệu suất năng lượng tối thiểu (E50)'),
                     ('kich_thuoc_a', 'Kích thước A (mm)'), ('kich_thuoc_b', 'Kích thước B (mm)'),
                     ('kich_thuoc_c', 'Kích thước C (mm)'), ('kich_thuoc_d', 'Kích thước D (mm)'),
                     ('khoi_luong_dau', 'Khối lượng dầu (kg)'),
                     ('tong_khoi_luong', 'Tổng khối lượng (kg)'),
                     ('bao_hanh_thang', 'Bảo hành (tháng)'),
                     ('chung_nhan', 'Chứng nhận')],
        # outline mặc định phân theo Nhóm Nguồn -> đọc thẳng cột, không phải AI đoán
        'outline_id_theo_nhom_nguon': {
            '05. Máy Biến Áp': 'outline_may_bien_ap',
            '08. Đo Lường & Biến Dòng': 'outline_do_luong',
        },
        'content_type': 'product',
    },
    'phu_kien_va_khac': {
        'nhan': 'Phụ kiện và khác',
        'cot_import': {
            'Mã hàng': 'ma_goc',
            'Tên hàng': 'ten_goc',
            'Nhãn Hiệu / Xuất Xứ': 'thuong_hieu',
            'Quy Cách / Áp Lực': 'quy_cach',
            'ĐVT': 'dvt',
            'Giá List (VNĐ)': 'gia_list',
            'Ghi Chú Ban Đầu': 'ghi_chu_ban_dau',
            'Nhóm Nguồn': 'nhom_nguon',
            # Ver 4.9.5 — 6 cột enrich thật từ catalogue nhà sản xuất (đầu
            # cáp/hộp nối co nguội/co nhiệt ABB/3M, 90 SKU đợt đầu) + 1 cột
            # audit nội bộ. KHÔNG bắt buộc (xem 'cot_bat_buoc' bên dưới) —
            # MASTER chưa enrich (hoặc SKU chưa tới lượt enrich) vẫn import
            # bình thường, field này trống, routing rơi về outline_phu_kien
            # như cũ (xem xac_dinh_outline_id).
            'Đường kính cách điện áp dụng (mm)': 'duong_kinh_cach_dien',
            'Kích thước lắp đặt I (mm)': 'kich_thuoc_i',
            'Chiều dài lắp đặt L (mm)': 'kich_thuoc_l',
            'Chiều dài đường rò - ngoài trời (mm)': 'duong_ro_ngoai_troi',
            'Tiêu chuẩn (catalogue)': 'tieu_chuan_catalogue',
            'Test điện (catalogue)': 'test_dien',
            'Nguồn catalogue': 'nguon_catalogue',  # nội bộ — chỉ dùng routing/audit
            'Catalogue PDF URL': 'catalogue_pdf_url',   # Ver 5.3 — tuỳ chọn (đã có sẵn cot_bat_buoc, không cần thêm gì khác)
        },
        # 8 cột gốc — thiếu là lỗi dừng import (hành vi cũ, không đổi).
        # 7 cột enrich KHÔNG nằm trong danh sách này -> optional.
        'cot_bat_buoc': [
            'Mã hàng', 'Tên hàng', 'Nhãn Hiệu / Xuất Xứ', 'Quy Cách / Áp Lực',
            'ĐVT', 'Giá List (VNĐ)', 'Ghi Chú Ban Đầu', 'Nhóm Nguồn',
        ],
        'cot_noi_bo': ['gia_list', 'ghi_chu_ban_dau', 'nhom_nguon', 'nguon_catalogue'],
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt',
                   'duong_kinh_cach_dien', 'kich_thuoc_i', 'kich_thuoc_l',
                   'duong_ro_ngoai_troi', 'tieu_chuan_catalogue', 'test_dien'],
        'cot_bang': [('ma_goc', 'Mã hàng'), ('thuong_hieu', 'Thương hiệu'),
                     ('quy_cach', 'Quy cách'),
                     ('duong_kinh_cach_dien', 'Đường kính cách điện áp dụng (mm)'),
                     ('kich_thuoc_i', 'Kích thước lắp đặt I (mm)'),
                     ('kich_thuoc_l', 'Kích thước lắp đặt L (mm)'),
                     ('duong_ro_ngoai_troi', 'Chiều dài đường rò - ngoài trời (mm)'),
                     ('tieu_chuan_catalogue', 'Tiêu chuẩn áp dụng'),
                     ('dvt', 'Đơn vị tính')],
        'outline_id_mac_dinh': 'outline_phu_kien',
        'content_type_theo_nhom_nguon': {
            '09. Thí Nghiệm & Kiểm Định': 'service',
            '__default__': 'product',
        },
    },
}

# Field không bao giờ được xuất hiện trong cot_ai/cot_bang của bất kỳ profile
# hay outline nào — assert tĩnh chạy lúc khởi động (mục 10, test bước 1 #2).
FIELD_CAM_TUYET_DOI = {'gia_list', 'ghi_chu_ban_dau'}


# ============================================================ Outline Registry
OUTLINES = {
    'outline_cap_dien': {
        'nhan': 'Cáp điện (đầy đủ)',
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt',
                   'tiet_dien', 'cap_dien_ap', 'vat_lieu_ruot',
                   # Ver 2.0 — 5 field giải mã ký hiệu (khớp cot_ai profile
                   # cap_dien, effective_cot_ai lấy GIAO 2 danh sách này)
                   'vat_lieu_ruot_giai_ma', 'loai_cach_dien_giai_ma',
                   'vo_boc_giai_ma', 'giap_bao_ve_giai_ma', 'dac_diem_khac_giai_ma',
                   # Ver 4.6 — cho AI thấy thông số điện để viết mô tả bám số
                   # thật, thay vì viết chung chung giống nhau giữa các SKU.
                   'dong_dien_dinh_muc_catalogue', 'kieu_lap_dat_catalogue',
                   'do_sut_ap_catalogue', 'dien_tro_dc_catalogue'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'tiet_dien', 'cap_dien_ap',
                     'vat_lieu_ruot', 'quy_cach', 'dvt',
                     'vat_lieu_ruot_giai_ma', 'loai_cach_dien_giai_ma',
                     'vo_boc_giai_ma', 'giap_bao_ve_giai_ma', 'dac_diem_khac_giai_ma'],
    },
    'outline_phu_kien': {
        'nhan': 'Phụ kiện chung',
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt', 'may_tuong_thich'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
    },
    'outline_dau_cap_ky_thuat': {
        # Ver 4.9.5 — riêng cho SKU đầu cáp/hộp nối ĐÃ enrich từ catalogue
        # thật (có nguon_catalogue). Không dùng chung outline_phu_kien vì
        # field kỹ thuật (đường kính cách điện, kích thước lắp, test điện)
        # không có ý nghĩa cho phụ kiện khác (cosse, băng keo...) — đúng
        # nguyên tắc tách outline theo ngữ nghĩa field (mục 2.1 kiến trúc).
        'nhan': 'Đầu cáp / hộp nối trung thế (có dữ liệu catalogue)',
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt',
                   'duong_kinh_cach_dien', 'kich_thuoc_i', 'kich_thuoc_l',
                   'duong_ro_ngoai_troi', 'tieu_chuan_catalogue', 'test_dien'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'quy_cach',
                     'duong_kinh_cach_dien', 'kich_thuoc_i', 'kich_thuoc_l',
                     'duong_ro_ngoai_troi', 'tieu_chuan_catalogue', 'dvt'],
    },
    'outline_service': {
        'nhan': 'Dịch vụ thí nghiệm/kiểm định',
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
    },
    'outline_tu_dong_cat': {
        'nhan': 'Tủ và thiết bị đóng cắt',
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
    },
    'outline_vo_tu': {
        'nhan': 'Vỏ tủ / tủ đo đếm',
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'quy_cach', 'dvt'],
    },
    'outline_may_bien_ap': {
        'nhan': 'Máy biến áp',
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt', 'cong_suat', 'cap_dien_ap',
                   'tier_cong_suat', 'sku_lien_ke_nho', 'sku_lien_ke_lon',
                   'chenh_lech_nho', 'chenh_lech_lon', 'tai_uoc_tinh',
                   # Ver 5.4 — nối 10 field catalogue thật + 2 field bảo hành/
                   # chứng nhận (khai sẵn, rỗng tới khi có data thật) vào
                   # outline, khớp cot_ai của profile ở trên (effective_cot_ai
                   # lấy GIAO 2 danh sách này).
                   'to_dau_day', 'ton_hao_khong_tai', 'ton_hao_ngan_mach', 'dong_khong_tai',
                   'dien_ap_ngan_mach', 'hieu_suat_e50', 'kich_thuoc_a', 'kich_thuoc_b',
                   'kich_thuoc_c', 'kich_thuoc_d', 'khoi_luong_dau', 'tong_khoi_luong',
                   'bao_hanh_thang', 'chung_nhan'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'cong_suat', 'cap_dien_ap', 'dvt',
                     'to_dau_day', 'ton_hao_khong_tai', 'ton_hao_ngan_mach', 'dong_khong_tai',
                     'dien_ap_ngan_mach', 'hieu_suat_e50', 'kich_thuoc_a', 'kich_thuoc_b',
                     'kich_thuoc_c', 'kich_thuoc_d', 'khoi_luong_dau', 'tong_khoi_luong',
                     'bao_hanh_thang', 'chung_nhan'],
    },
    'outline_vo_may_bien_ap': {
        # Ver 5.2 — outline RIÊNG cho "Vỏ mạ kẽm nhúng nóng MBA..." — đây
        # là VỎ THÉP bảo vệ (phụ kiện lắp ngoài, KHÔNG phải máy biến áp),
        # tách khỏi outline_may_bien_ap để không bị gọi nhầm là "máy biến
        # áp" trong title/nội dung. Không đưa 'cap_dien_ap' vào — field
        # này vô nghĩa với vỏ (vỏ không có cấp điện áp riêng, và cột này
        # trong MASTER đang lỗi dữ liệu — xem ghi chú ở
        # tim_san_pham_cung_dong). 'cong_suat' GIỮ LẠI vì có ý nghĩa thật:
        # cỡ vỏ khớp đúng cỡ máy biến áp nào.
        'nhan': 'Vỏ bảo vệ máy biến áp',
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt', 'cong_suat',
                   'may_tuong_thich',
                   'tier_cong_suat', 'sku_lien_ke_nho', 'sku_lien_ke_lon',
                   'chenh_lech_nho', 'chenh_lech_lon'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'cong_suat', 'dvt'],
    },
    'outline_do_luong': {
        'nhan': 'Thiết bị đo lường',
        'cot_ai': ['ten_goc', 'thuong_hieu', 'quy_cach', 'dvt', 'cap_dien_ap'],
        'cot_bang': ['ma_goc', 'thuong_hieu', 'cap_dien_ap', 'dvt'],
    },
}


def effective_cot_ai(profile_id, outline_id):
    """Giao giữa field profile cho phép và field outline cho phép. Giữ thứ
    tự theo cot_ai của profile."""
    p = PROFILES[profile_id]['cot_ai']
    o = set(OUTLINES[outline_id]['cot_ai'])
    return [f for f in p if f in o]


def effective_cot_bang(profile_id, outline_id):
    """Như trên nhưng cho bảng thông số/schema — giữ (field, nhãn), giữ thứ
    tự theo cot_bang của profile."""
    p = PROFILES[profile_id]['cot_bang']
    o = set(OUTLINES[outline_id]['cot_bang'])
    return [(k, nhan) for k, nhan in p if k in o]


# ============================================================ routing outline_id
def xac_dinh_outline_id(profile_id, row):
    """row: dict đã normalize, có đủ field cot_noi_bo (ghi_chu_ban_dau,
    nhom_nguon...). Trả outline_id đúng cho dòng này, theo routing rule của
    từng profile (ARCHITECTURE mục 4). KHÔNG đổi profile_id ở đây — hàm này
    chỉ quyết định outline.
    """
    if profile_id == 'cap_dien':
        # 185 dòng: ghi_chu_ban_dau khác "Cáp điện" (kể cả rỗng) -> phụ kiện
        if row.get('ghi_chu_ban_dau', '') != 'Cáp điện':
            return 'outline_phu_kien'
        return 'outline_cap_dien'

    if profile_id == 'tu_va_thiet_bi_dong_cat':
        # Ver 6.0 — ĐỊNH TUYẾN THEO TÊN, cùng cách đã dùng cho
        # may_bien_ap_do_luong ở dưới (vá Ver 5.2 "Vỏ mạ kẽm" bị gọi là máy
        # biến áp). Family Router phát hiện 19 SKU trong sheet 02 KHÔNG phải
        # thiết bị đóng cắt: chống sét van, dịch vụ thí nghiệm, sứ đỡ FCO,
        # hộp nguồn, tủ đo đếm. Để nguyên thì bài viết mô tả chống sét van
        # như thể nó là tủ đóng cắt — sai bản chất, và rank nhầm truy vấn.
        #
        # SỬA Ở ĐÂY chứ KHÔNG dời dòng sang sheet 04, vì
        # record_id = profile::sheet::SỐ DÒNG::sku — xoá dòng khỏi sheet 02
        # làm mọi dòng bên dưới đổi record_id và mồ côi bài đã đăng.
        # Sửa trong code còn có lợi: bản MASTER sau vẫn được vá, không phải
        # sửa tay lại từ đầu.
        _t = _bo_dau(row.get('ten_goc', ''))

        # Dịch vụ thí nghiệm/kiểm định — KHÔNG phải thiết bị bán ra.
        # family_router chấp nhận outline_service cho họ này (đúng bản chất
        # hơn outline_phu_kien).
        if 'thi nghiem' in _t or 'kiem dinh' in _t:
            return 'outline_service'

        # Tủ đo đếm: TU/TI/công tơ -> họ đo lường, không phải đóng cắt.
        if 'do dem' in _t or 'cong to' in _t:
            return 'outline_do_luong'

        # Chống sét van, sứ đỡ FCO, hộp nguồn -> phụ kiện.
        if ('chong set' in _t or 'su do' in _t or 'bass su' in _t
                or 'hop nguon' in _t):
            return 'outline_phu_kien'

        if row.get('nhom_nguon', '') == '10. Tủ Điện & Trung Thế':
            return 'outline_vo_tu'
        return 'outline_tu_dong_cat'

    if profile_id == 'may_bien_ap_do_luong':
        nhom = row.get('nhom_nguon', '')
        ten = row.get('ten_goc', '').strip().lower()
        # Ver 5.2 — VÁ LỖI THẬT (Thịnh xem site thấy "Vỏ mạ kẽm nhúng nóng
        # MBA 3P 1500KVA..." bị gọi thành "Máy biến áp MBT 1500kVA - Báo
        # Giá" — SAI SỰ THẬT, đây là VỎ THÉP bảo vệ, không phải máy biến
        # áp). Trước đây "Giá treo MBT" đã được tách ra outline_phu_kien
        # (dòng dưới), nhưng "Vỏ mạ kẽm" bị bỏ sót — vẫn dùng chung
        # outline_may_bien_ap nên dính đủ bộ title/so sánh công suất/delta
        # context viết như thể nó LÀ máy biến áp. Tách outline RIÊNG (theo
        # yêu cầu Thịnh) thay vì gộp vào outline_phu_kien chung chung — vỏ
        # có đặc thù riêng đáng nói (vật liệu mạ kẽm, chống ăn mòn, khớp
        # đúng cỡ máy) mà outline_phu_kien không có chỗ cho.
        if ten.startswith('vỏ mạ kẽm') or ten.startswith('vỏ mã kẽm'):
            return 'outline_vo_may_bien_ap'
        # 7 dòng "Giá treo MBT" lẫn trong nhóm 05 -> phụ kiện, không phải máy
        if 'giá treo' in ten:
            return 'outline_phu_kien'
        theo_nhom = PROFILES['may_bien_ap_do_luong']['outline_id_theo_nhom_nguon']
        if nhom in theo_nhom:
            return theo_nhom[nhom]
        return 'outline_phu_kien'   # nhóm lạ, chưa khai báo -> an toàn, không đoán bừa

    if profile_id == 'phu_kien_va_khac':
        # Dịch vụ (Nhóm Nguồn "09. Thí Nghiệm & Kiểm Định") dùng outline
        # RIÊNG (outline_service) — cấu trúc nội dung khác hẳn phụ kiện vật
        # lý (không có "quy cách kỹ thuật sản phẩm", có "quy trình thực
        # hiện"), và không dùng Product Schema (mục 6, dung_schema()).
        if row.get('nhom_nguon', '') == '09. Thí Nghiệm & Kiểm Định':
            return 'outline_service'
        # Ver 4.9.5 — SKU đã enrich từ catalogue thật (nguon_catalogue có
        # giá trị, field nội bộ ghi ở lúc build 5MASTER_ENRICHED) -> outline
        # kỹ thuật, có field đường kính/kích thước/test điện. SKU chưa
        # enrich (nguon_catalogue rỗng, kể cả MASTER cũ không có cột này
        # luôn) -> rơi về outline_phu_kien mặc định như cũ, không đoán.
        if row.get('nguon_catalogue', ''):
            return 'outline_dau_cap_ky_thuat'
        return PROFILES['phu_kien_va_khac']['outline_id_mac_dinh']

    raise ValueError(f'profile_id không hợp lệ: {profile_id}')


def xac_dinh_content_type(profile_id, row):
    if profile_id == 'phu_kien_va_khac':
        nhom = row.get('nhom_nguon', '')
        theo_nhom = PROFILES['phu_kien_va_khac']['content_type_theo_nhom_nguon']
        return theo_nhom.get(nhom, theo_nhom['__default__'])
    return PROFILES[profile_id].get('content_type', 'product')


# ============================================================ assert tĩnh — chạy lúc import module
def _kiem_tra_registry():
    for pid, p in PROFILES.items():
        cot_ai = set(p.get('cot_ai', []))
        cot_bang = {k for k, _ in p.get('cot_bang', [])}
        vi_pham = (cot_ai | cot_bang) & FIELD_CAM_TUYET_DOI
        if vi_pham:
            raise AssertionError(
                f'PROFILES["{pid}"]: field cấm tuyệt đối lọt vào cot_ai/cot_bang: {vi_pham}')
    for oid, o in OUTLINES.items():
        cot_ai = set(o.get('cot_ai', []))
        cot_bang = set(o.get('cot_bang', []))
        vi_pham = (cot_ai | cot_bang) & FIELD_CAM_TUYET_DOI
        if vi_pham:
            raise AssertionError(
                f'OUTLINES["{oid}"]: field cấm tuyệt đối lọt vào cot_ai/cot_bang: {vi_pham}')


_kiem_tra_registry()
