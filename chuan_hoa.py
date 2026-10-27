# -*- coding: utf-8 -*-
r"""Ver 5.7 — NGUỒN DUY NHẤT của việc bỏ dấu tiếng Việt.

VÌ SAO CÓ FILE NÀY
    Trước 5.7, `_bo_dau()` được định nghĩa lại ở 9 file với 6 thân hàm khác
    nhau (audit 22/08/2026):

        anh_san_pham.py, enrich_tcvn_mba.py, ghep_vao_master.py,
        kien_thuc_bien_thien.py   -> giống hệt nhau, CÓ .lower()
        family_router.py          -> CÓ .lower(), thêm `or ''`
        va_slug.py                -> CÓ .lower()
        prompts_seo_post.py       -> CÓ .lower() (gọi trước khi map đ)
        sinh_ma_noi_bo.py         -> KHÔNG .lower()
        workspace_anh.py          -> KHÔNG .lower(), NFD trước rồi mới map đ

    Cùng một cái tên, hai hành vi. So khớp từ khoá ra kết quả khác nhau tuỳ
    module đang đứng ở đâu — loại lỗi không bao giờ báo, chỉ âm thầm trượt.

BẪY ĐÃ VẤP THẬT (chép lại từ family_router.py và prompts_seo_post.py, đừng
để mất kiến thức này khi gom file):
    unicodedata NFD chỉ tách được dấu TỔ HỢP (á, ề, ộ...). Ký tự 'đ' là
    U+0111 — một ký tự ĐỘC LẬP, không phải 'd' + dấu gạch — nên NFD KHÔNG
    tách được. Hậu quả: 'điện' ra 'đien', 'Đầu cáp' ra 'đau cap', mọi regex
    viết r'\bdien\b' hay r'\bdau\s*cap\b' đều TRƯỢT trong im lặng. Phải map
    'đ'/'Đ' bằng tay TRƯỚC khi normalize.

DÙNG CÁI NÀO
    bo_dau(s)           -> có .lower(). Dùng cho so khớp từ khoá, routing,
                           slug. Đây là mặc định, 7/9 chỗ cũ dùng bản này.
    bo_dau_giu_hoa(s)   -> giữ nguyên hoa/thường. CHỈ dùng khi phần chữ hoa
                           mang ý nghĩa (sinh mã nội bộ, tên file workspace).

KHÔNG GOM `_so()` VÀO ĐÂY — đã cân nhắc và loại
    Audit ban đầu đề xuất gom luôn 6 bản `_so()`. Đọc kỹ thì SAI: 6 bản đó
    KHÔNG phải một hàm bị chép 6 lần, mà là 6 hàm KHÁC NHAU trùng tên riêng:
        enrich_tcvn_mba._so    float() trần, CỐ Ý ném lỗi khi dữ liệu bẩn
        hinh_ky_thuat._so      trả None nếu rỗng, bóc số đầu tiên
        khoi_chiu_tai._so      xử lý thêm sentinel 'nan'/'none'/'-'
        kien_thuc_bien_thien._so  bóc số đầu tiên, không lọc sentinel
        phu_kien_di_kem._so    thay ',' TRƯỚC khi bóc (khác thứ tự -> khác
                               kết quả với chuỗi kiểu '1.500,5')
        sinh_ma_noi_bo._so     trả CHUỖI, không phải float
    Gom lại là đổi hành vi thật ở 6 chỗ để đổi lấy cái đẹp mắt. Không làm.
"""
import unicodedata

__all__ = ['bo_dau', 'bo_dau_giu_hoa']


def _tach_dau(s):
    """Map 'đ'/'Đ' TRƯỚC (NFD không tách được), rồi mới bỏ dấu tổ hợp."""
    s = str(s if s is not None else '').replace('đ', 'd').replace('Đ', 'D')
    s = unicodedata.normalize('NFD', s)
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def bo_dau(s):
    """Bỏ dấu tiếng Việt + hạ chữ thường. Bản mặc định cho so khớp."""
    return _tach_dau(s).lower()


def bo_dau_giu_hoa(s):
    """Bỏ dấu tiếng Việt, GIỮ NGUYÊN hoa/thường."""
    return _tach_dau(s)


if __name__ == '__main__':
    mau = [
        ('Đầu cáp', 'dau cap'),
        ('điện áp', 'dien ap'),
        ('Máy biến áp THIBIDI', 'may bien ap thibidi'),
        ('Tủ trung thế RMU', 'tu trung the rmu'),
        ('', ''),
        (None, ''),
    ]
    sai = 0
    for vao, mong_doi in mau:
        ra = bo_dau(vao)
        dat = ra == mong_doi
        sai += 0 if dat else 1
        print(f'  {"OK  " if dat else "SAI "} bo_dau({vao!r}) = {ra!r}')
    ra = bo_dau_giu_hoa('Đầu cáp THIBIDI')
    dat = ra == 'Dau cap THIBIDI'
    sai += 0 if dat else 1
    print(f'  {"OK  " if dat else "SAI "} bo_dau_giu_hoa = {ra!r}')
    print(f'\nTONG SAI: {sai}')
    raise SystemExit(1 if sai else 0)
