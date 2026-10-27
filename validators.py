# -*- coding: utf-8 -*-
"""
Phase 2 Lite — Bước 3: validator riêng từng profile + regex fix
(ARCHITECTURE-DRAFT-4-PROFILES.md mục 4, quyết định #10 vòng duyệt 2).

Chạy 1 lần lúc import, sau khi record đã có outline_id (profiles.py đã gắn).
KHÔNG đụng dulieu.py/autopost.py cũ (nhánh RMU).

Mọi regex ở đây đã kiểm bằng dữ liệu thật (xem DATA-AUDIT-4-PROFILES.md mục 8
— snapshot 33 tên) trước khi đưa vào code, không phải case tự nghĩ.
"""
import re

# ============================================================ regex dùng chung
# Điện áp dạng cặp X/Y kV hoặc X/Y V — dùng cho máy biến áp (bug kVA/kV) và
# cho cáp điện (300/500V, 450/750V...). Yêu cầu chữ V bắt buộc, "k" tuỳ chọn.
_DIEN_AP_CAP_RE = re.compile(
    r'(\d+(?:[.,]\d+)?(?:\s*/\s*\d+(?:[.,]\d+)?)?)\s*([kK]?[vV])\b')

# Điện áp CẶP bắt buộc có dấu "/" — dùng riêng cho máy biến áp vì công suất
# kVA không bao giờ viết dạng "X/Y", chỉ điện áp sơ/thứ cấp mới có "/".
_DIEN_AP_CAP_BAT_BUOC_RE = re.compile(
    r'(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)\s*([kK]?[vV])\b')

# Tiết diện mm2 — bắt cả dạng đa lõi "NxM" (đã có sẵn ở dữ liệu gốc, không
# đụng) lẫn đơn lõi "M" (đang thiếu, cần bóc). Cho phép dấu "-" trước "mm2"
# (case cá biệt "240-mm2").
_TIET_DIEN_RE = re.compile(
    r'(\d+(?:[.,]\d+)?(?:\s*[xX]\s*\d+(?:[.,]\d+)?)?)\s*-?\s*mm[²2]')

_CU_AL_RE = re.compile(r'cu[\s\-/]*al', re.IGNORECASE)

# R2-07: nhãn bảng thông số của may_bien_ap_do_luong đã mang sẵn đơn vị
# ("Công suất (kVA)", "Cấp điện áp (kV)") — GIÁ TRỊ vì vậy phải bỏ hậu tố đơn
# vị để không lặp ("Công suất (kVA): 15 kVA" là sai, phải là "...: 15").
# Cột "Cấp Điện Áp" của cap_dien KHÔNG áp hậu tố này — nhãn cột đó không có
# đơn vị (đơn vị đổi giữa V/kV theo từng dòng), giá trị PHẢI giữ nguyên đơn
# vị embedded, không được strip (khác hẳn 2 cột của máy biến áp).
_DON_VI_HAU_TO_RE = re.compile(r'\s*(kva|kv|va|a)\s*$', re.IGNORECASE)


def _strip_don_vi_hau_to(gia_tri):
    return _DON_VI_HAU_TO_RE.sub('', gia_tri or '').strip()


def _khop_dau(m):
    """Ghép lại đúng định dạng gốc từ match object 2 hoặc 3 group."""
    return ''.join(g for g in m.groups() if g)


# ============================================================ validate_cap_dien
def validate_cap_dien(row):
    """row: dict đã normalize, đã có outline_id (profiles.xac_dinh_outline_id
    đã chạy). Sửa TẠI CHỖ (mutate), trả về row để tiện dùng trong pipeline.

    Chỉ bóc thêm tiet_dien/cap_dien_ap cho những dòng THẬT SỰ là cáp
    (outline_id == 'outline_cap_dien') — không bóc cho 185 dòng phụ kiện lẫn
    trong sheet, vì "11mm2" của 1 con ốc xiết không phải tiết diện cáp, dù
    regex vẫn kỹ thuật khớp được. Outline Registry (profiles.py) đã tự loại
    field này khỏi output cho 185 dòng đó, đây là lớp phòng thủ thứ 2 ở tầng
    dữ liệu gốc, không tạo dữ liệu sai lệch ngay từ đầu.
    """
    ten = row.get('ten_goc', '')

    if row.get('outline_id') == 'outline_cap_dien':
        if not row.get('tiet_dien'):
            m = _TIET_DIEN_RE.search(ten)
            if m:
                row['tiet_dien'] = m.group(1).strip()
                row['tiet_dien_tu_dong_boc'] = True

        if not row.get('cap_dien_ap'):
            m = _DIEN_AP_CAP_RE.search(ten)
            if m:
                row['cap_dien_ap'] = _khop_dau(m)
                row['cap_dien_ap_tu_dong_boc'] = True

    # Cu-Al: phòng thủ lớp 2 — dù dòng này lỡ chưa được route sang
    # outline_phu_kien (VD ghi_chu_ban_dau bị điền nhầm "Cáp điện" cho 1 dòng
    # cosse), vẫn không cho hiển thị "Đồng (Cu)" sai cho vật liệu lưỡng kim.
    if _CU_AL_RE.search(ten) and row.get('vat_lieu_ruot'):
        row['vat_lieu_ruot'] = ''
        row['vat_lieu_ruot_da_xoa_do_cu_al'] = True

    return row


# ============================================================ validate_tu_dong_cat
def validate_tu_dong_cat(row):
    """Không có bug dữ liệu bắt buộc sửa. routing outline_vo_tu đã làm ở
    profiles.py. Field nào trống (dòng cắt, dòng định mức...) thì để trống —
    không có field kỹ thuật riêng trong cot_import của profile này để mà ép,
    nên không cần code thêm ở đây."""
    return row


# ============================================================ validate_may_bien_ap
def validate_may_bien_ap(row):
    """Sửa bug kVA/kV CHỈ cho record THẬT SỰ là máy biến áp/vỏ máy biến áp
    (outline_id trong {'outline_may_bien_ap', 'outline_vo_may_bien_ap'}, đã
    loại 7 dòng "Giá treo MBT" ở bước routing). Bug: Cấp Điện Áp (kV) bị
    copy nhầm bằng đúng số Công Suất (kVA).

    Ver 5.3 — VÁ HỒI QUY THẬT: Ver 5.2 tách "Vỏ mạ kẽm..." ra outline
    RIÊNG (outline_vo_may_bien_ap, đúng — vỏ không phải máy biến áp thật)
    nhưng hàm này vẫn chỉ gate theo 'outline_may_bien_ap', nên ~24 dòng vỏ
    ĐANG bị bug kVA/kV lại bị BỎ SÓT không fix nữa (regex chỉ chạy nếu
    outline khớp) — tự phát hiện qua test_phase2_full.py Test 10 lệch số
    (165→141) khi chạy full regression trước khi đóng gói, không phải do
    review ngoài phát hiện. cap_dien_ap hiện KHÔNG được hiển thị ở outline
    vỏ (đã loại khỏi cot_ai/cot_bang khi tách outline — vỏ không có "cấp
    điện áp" thật) nên lỗi này KHÔNG ảnh hưởng nội dung hiển thị, nhưng vẫn
    nên fix đúng ở tầng dữ liệu, phòng dùng lại field này sau này.

    Bỏ hậu tố đơn vị (R2-07) áp dụng cho MỌI dòng của profile này bất kể
    outline — đặt cuối hàm qua _chuan_hoa_don_vi_may_bien_ap(), chạy trên cả
    2 nhánh thoát sớm bên dưới, không riêng nhánh bug.
    """
    if row.get('outline_id') not in ('outline_may_bien_ap', 'outline_vo_may_bien_ap'):
        return _chuan_hoa_don_vi_may_bien_ap(row)

    ten = row.get('ten_goc', '')
    cong_suat_so = re.sub(r'[^\d.,]', '', row.get('cong_suat', '') or '')
    cap_dien_ap_so = re.sub(r'[^\d.,]', '', row.get('cap_dien_ap', '') or '')

    la_bug = bool(cong_suat_so) and cong_suat_so == cap_dien_ap_so
    if not la_bug:
        return _chuan_hoa_don_vi_may_bien_ap(row)

    row['canh_bao_dien_ap'] = True
    m = _DIEN_AP_CAP_BAT_BUOC_RE.search(ten)
    if m:
        so1, so2, don_vi = m.groups()
        row['cap_dien_ap'] = f'{so1}/{so2}{don_vi}'
        row['cap_dien_ap_da_sua_bug'] = True
    else:
        # Không tách được điện áp thật từ tên (VD thiếu chữ "V" do lỗi đánh
        # máy nguồn, "22/0.4K" thay vì "22/0.4KV") -> KHÔNG suy đoán, xoá
        # hẳn giá trị sai thay vì giữ số kVA giả làm điện áp.
        row['cap_dien_ap'] = ''
        row['cap_dien_ap_khong_the_tu_sua'] = True

    return _chuan_hoa_don_vi_may_bien_ap(row)


def _chuan_hoa_don_vi_may_bien_ap(row):
    """R2-07: nhãn cot_bang của may_bien_ap_do_luong đã mang đơn vị trong
    tên nhãn ("Công suất (kVA)", "Cấp điện áp (kV)") -> giá trị phải bỏ hậu
    tố đơn vị lặp lại. Áp cho MỌI outline của profile này (kể cả
    outline_do_luong, outline_phu_kien của 7 dòng giá treo — rỗng thì strip
    cũng ra rỗng, an toàn)."""
    if row.get('profile_id') != 'may_bien_ap_do_luong':
        return row
    row['cong_suat'] = _strip_don_vi_hau_to(row.get('cong_suat', ''))
    row['cap_dien_ap'] = _strip_don_vi_hau_to(row.get('cap_dien_ap', ''))
    return row


# ============================================================ validate_phu_kien
def validate_phu_kien(row):
    """content_type=service đã gắn ở profiles.py (theo Nhóm Nguồn). Không có
    bug dữ liệu bắt buộc sửa thêm."""
    return row


VALIDATORS = {
    'cap_dien': validate_cap_dien,
    'tu_va_thiet_bi_dong_cat': validate_tu_dong_cat,
    'may_bien_ap_do_luong': validate_may_bien_ap,
    'phu_kien_va_khac': validate_phu_kien,
}


def validate_row(row):
    profile_id = row['profile_id']
    fn = VALIDATORS[profile_id]
    return fn(row)


def validate_rows(rows):
    return [validate_row(r) for r in rows]


# ============================================================ chuẩn hoá ĐVT + SKU trùng dùng chung
def chuan_hoa_dvt(rows):
    """.strip() lại lần nữa cho chắc (dữ liệu đã qua normalize_cell ở
    profiles.py rồi nên về lý thuyết đã sạch, đây là phòng thủ kép rẻ tiền)."""
    for r in rows:
        if 'dvt' in r:
            r['dvt'] = (r['dvt'] or '').strip()
    return rows
