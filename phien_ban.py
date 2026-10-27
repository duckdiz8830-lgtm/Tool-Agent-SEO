# -*- coding: utf-8 -*-
"""Ver 4.5 — NGUỒN DUY NHẤT của chuỗi phiên bản.

Trước 4.5, chuỗi phiên bản nằm rải rác và ĐÃ LỆCH NHAU:
    giao-dien.py       -> 'Ver 4.4.1.4 HF1'  (3 chỗ)
    thu_muc_du_lieu.py -> 'Ver 4.4.1.6'
    tên file zip       -> '4_4_1_7'
Ba con số khác nhau cho cùng một bản build. Không ai biết đang chạy cái gì.

Từ nay: sửa DUY NHẤT ở đây, mọi nơi khác import.

--- 20/08/2026: file này đã tự phản bội mục đích của nó ---
PHIEN_BAN nằm im ở '4.6.2' suốt 5 đợt phát triển, trong khi code thật đi
tới 5.4. Bằng chứng đếm được trong source: 15 mốc 'Ver 5.0', 65 'Ver 5.1',
15 'Ver 5.2', 24 'Ver 5.3', 10 'Ver 5.4' + 4 file test tests/test_v5{0..3}_patch.py.
Một hằng số duy nhất vẫn lệch được nếu KHÔNG AI SỬA NÓ.

QUY TRÌNH BẮT BUỘC khi đóng gói bản mới, làm ĐỦ 3 bước, không được bỏ bước:
  1. Sửa PHIEN_BAN ở dòng dưới.
  2. Thêm mục vào docs/NHAT-KY-THAY-DOI.md (viết LÚC làm, không viết sau).
  3. Chạy `python phien_ban.py` — script tự đối chiếu mốc 'Ver x.y' cao
     nhất trong code với PHIEN_BAN, lệch thì báo đỏ.
"""

PHIEN_BAN = '6.3'
TEN_APP = 'SONEALEO ULTRA'
NHAN_DAY_DU = f'{TEN_APP} · Ver {PHIEN_BAN}'
NHAN_SAN_SANG = f'Sẵn sàng · {NHAN_DAY_DU}'
NHAN_AUTOPOST = f'LOTECH AUTOPOST VER {PHIEN_BAN}'


def moc_cao_nhat_trong_code(thu_muc=None):
    """Quét mọi file .py (trừ tests/) tìm mốc 'Ver x.y[.z]' cao nhất được
    ghi trong comment. Trả tuple (chuoi, danh_sach_file) hoặc (None, [])."""
    import os
    import re
    goc = thu_muc or os.path.dirname(os.path.abspath(__file__))
    mau = re.compile(r'Ver (\d+)\.(\d+)(?:\.(\d+))?')
    cao, o_dau = None, []
    for goc_con, thu_muc_con, ten_files in os.walk(goc):
        thu_muc_con[:] = [d for d in thu_muc_con
                          if d not in ('tests', 'qa', 'docs', '__pycache__', '.git')]
        for ten in ten_files:
            if not ten.endswith('.py'):
                continue
            duong_dan = os.path.join(goc_con, ten)
            try:
                with open(duong_dan, 'r', encoding='utf-8', errors='replace') as f:
                    noi_dung = f.read()
            except OSError:
                continue
            for m in mau.finditer(noi_dung):
                bo = tuple(int(x) if x else 0 for x in m.groups())
                if cao is None or bo > cao:
                    cao, o_dau = bo, [ten]
                elif bo == cao and ten not in o_dau:
                    o_dau.append(ten)
    if cao is None:
        return None, []
    chuoi = f'{cao[0]}.{cao[1]}' + (f'.{cao[2]}' if cao[2] else '')
    return chuoi, o_dau


def kiem_tra_lech():
    """Trả (khop: bool, thong_diep: str). Dùng được trong test/CI."""
    trong_code, o_dau = moc_cao_nhat_trong_code()
    if trong_code is None:
        return True, 'Không tìm thấy mốc "Ver x.y" nào trong code — bỏ qua.'
    if trong_code == PHIEN_BAN:
        return True, f'KHỚP: PHIEN_BAN = mốc cao nhất trong code = {PHIEN_BAN}'
    return False, (
        f'LỆCH PHIÊN BẢN:\n'
        f'  phien_ban.PHIEN_BAN   = {PHIEN_BAN}\n'
        f'  mốc cao nhất trong code   = {trong_code}  (ở: {", ".join(o_dau[:5])})\n'
        f'  -> Sửa PHIEN_BAN, HOẶC xoá mốc ghi nhầm trong code.\n'
        f'  -> Và ghi mục mới vào docs/NHAT-KY-THAY-DOI.md.')


if __name__ == '__main__':
    import sys
    khop, tin = kiem_tra_lech()
    print(tin)
    sys.exit(0 if khop else 1)
