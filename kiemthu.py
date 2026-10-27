#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bộ nghiệm thu. Chạy N bài rồi tự chấm 5 mốc đã chốt.

    python kiemthu.py --site site1 --so 30 --che-do sinh
    python kiemthu.py --site site1 --so 30 --che-do nhap    (đăng draft thật)

5 mốc:
    1. Không lỗi kết nối, không lỗi JSON
    2. Tỷ lệ bị chặn dưới 10%
    3. Không mất trạng thái: đủ N bản ghi trong kho dữ liệu
    4. Chạy lại không đẻ bài trùng, không đẻ slug -2
    5. Ngắt giữa chừng chạy tiếp được đúng chỗ

Mốc nào TRƯỢT thì in ngay nguyên nhân, khỏi đào log.
"""
import argparse
import re
import time

import autopost as A
import dulieu as DL
import prompts as P


class Mot:
    def __init__(self, ten):
        self.ten, self.dat, self.ly_do, self.so = ten, None, '', ''

    def cham(self, dat, so='', ly_do=''):
        self.dat, self.so, self.ly_do = dat, so, ly_do
        return self


def _phan_loai_loi(msg):
    m = msg.lower()
    if any(x in m for x in ('connection', 'remotedisconnected', 'timeout', 'ngắt kết nối',
                            'cắt kết nối', 'không nhận')):
        return 'KET_NOI'
    if 'json' in m:
        return 'JSON'
    if 'hết lượt' in m or '429' in m:
        return 'QUOTA'
    return 'KHAC'


def chay(ma_site, mau_key, so, che_do, nghi):
    """Chạy thật, gom số liệu thô."""
    tat_ca = A.doc_san_pham(None, ma_site)
    if not tat_ca:
        raise SystemExit('Kho dữ liệu trống. Nhập Excel trước.')
    rows = A.chon_dong(tat_ca, ma_site, mau_key, so, 0, bo_da_lam=True)
    if len(rows) < so:
        print(f'   (chỉ còn {len(rows)} sản phẩm chưa làm, chạy {len(rows)} bài)')
    if not rows:
        raise SystemExit('Không còn sản phẩm nào chưa làm. Xoá du-lieu.db để chạy lại từ đầu.')

    client = A.tao_client() if che_do != 'thu' else None
    kq = {'chay': len(rows), 'ok': 0, 'chan': 0, 'loi': {}, 'sku_loi': [],
          'giay': 0.0, 'so_tu': []}
    t0 = time.time()
    for i, row in enumerate(rows, 1):
        try:
            r = A.sinh_mot_bai(row, ma_site, mau_key, tat_ca, che_do, client)
            if r['trang_thai'] == 'BI_CHAN':
                kq['chan'] += 1
            else:
                kq['ok'] += 1
            kq['so_tu'].append(r['so_tu'])
            print(f'   [{i}/{len(rows)}] {r["trang_thai"]:8} {r["sku"][:34]:34} '
                  f'{r["so_tu"]:5} từ  {r["ghi_chu"][:44]}')
        except SystemExit as e:
            print(f'   [{i}/{len(rows)}] DỪNG: {e}')
            break
        except Exception as e:
            loai = _phan_loai_loi(str(e))
            kq['loi'][loai] = kq['loi'].get(loai, 0) + 1
            kq['sku_loi'].append((row['sku'], loai, str(e)[:120]))
            print(f'   [{i}/{len(rows)}] LỖI[{loai}] {row["sku"][:30]}: {str(e)[:70]}')
            A.ghi_bai_loi(row, ma_site, mau_key, e)
        if i < len(rows) and che_do != 'thu' and nghi:
            time.sleep(nghi)
    kq['giay'] = time.time() - t0
    return kq, rows


def cham_diem(ma_site, mau_key, kq, rows, che_do):
    ds = []
    n = kq['chay']

    # 1. lỗi kết nối / JSON
    ket_noi = kq['loi'].get('KET_NOI', 0)
    json_loi = kq['loi'].get('JSON', 0)
    m = Mot('1. Không lỗi kết nối, không lỗi JSON')
    if ket_noi or json_loi:
        m.cham(False, f'kết nối {ket_noi}, JSON {json_loi}',
               'Lỗi kết nối gần như luôn do ModSecurity hoặc plugin bảo mật trên web chặn '
               'bài có HTML. Chạy "Kiểm tra kết nối WordPress" ở tab 1.\n'
               '        Lỗi JSON là bài bị cắt giữa chừng: giảm tong_tu trong prompts.py '
               'hoặc đổi model.')
    else:
        m.cham(True, f'0/{n}')
    ds.append(m)

    # 2. tỷ lệ chặn
    ty = kq['chan'] / n if n else 0
    m = Mot('2. Tỷ lệ bị chặn dưới 10%')
    m.cham(ty < 0.10, f'{kq["chan"]}/{n} = {ty * 100:.0f}%',
           '' if ty < 0.10 else
           'Chặn nhiều nghĩa là AI bịa số. Hai nguyên nhân hay gặp: dữ liệu sản phẩm quá '
           'trống nên AI tự lấp, hoặc kho kiến thức bật mục chưa kiểm chứng.\n'
           '        Xem cột "Ghi chú / Lý do chặn" trong bang-dieu-khien.xlsx.')
    ds.append(m)

    # 3. không mất trạng thái
    ghi = {b['sku'] for b in DL.doc_bai_viet(ma_site) if b['mau'] == mau_key}
    thieu = [r['sku'] for r in rows if r['sku'] not in ghi]
    m = Mot('3. Đủ bản ghi trong kho dữ liệu, không mất trạng thái')
    m.cham(not thieu, f'{len(rows) - len(thieu)}/{len(rows)}',
           '' if not thieu else f'Thiếu bản ghi của: {", ".join(thieu[:6])}')
    ds.append(m)

    # 4. chạy lại không đẻ bài trùng
    tat_ca = A.doc_san_pham(None, ma_site)
    con_lai = A.chon_dong(tat_ca, ma_site, mau_key, 0, 0, bo_da_lam=True)
    lam_lai = [r['sku'] for r in con_lai if r['sku'] in ghi]
    trung = DL.slug_trung()
    m = Mot('4. Chạy lại không đẻ bài trùng, không trùng slug')
    if lam_lai or trung:
        m.cham(False, f'lặp {len(lam_lai)}, slug trùng {len(trung)}',
               'Bài đã xong vẫn lọt vào lượt chạy sau. Kiểm tra ô "Bỏ qua sản phẩm đã '
               'sinh bài rồi" và cột trang_thai trong du-lieu.db.')
    else:
        m.cham(True, f'{len(ghi)} bài đã xong đều được bỏ qua')
    ds.append(m)

    # 5. resume: mô phỏng tắt máy bằng cách đọc lại kho và xem còn đúng phần chưa làm
    tong_can = len(tat_ca)
    da_xong = len(DL.da_lam(ma_site, mau_key))
    m = Mot('5. Tắt máy chạy tiếp được đúng chỗ')
    m.cham(da_xong + len(con_lai) == tong_can,
           f'{da_xong} xong + {len(con_lai)} còn = {tong_can}',
           '' if da_xong + len(con_lai) == tong_can else
           'Số đã xong cộng số còn lại không khớp tổng. Kho dữ liệu bị lệch.')
    ds.append(m)
    return ds


def in_ket_qua(ds, kq, che_do):
    n = kq['chay']
    tu = kq['so_tu'] or [0]
    print('\n' + '=' * 74)
    print('BẢNG NGHIỆM THU')
    print('=' * 74)
    for m in ds:
        dau = ' ĐẠT  ' if m.dat else 'TRƯỢT '
        print(f'[{dau}] {m.ten:52} {m.so}')
        if m.ly_do:
            print(f'        {m.ly_do}')
    print('-' * 74)
    tb = kq['giay'] / n if n else 0
    print(f'Chạy {n} bài trong {kq["giay"] / 60:.1f} phút  |  {tb:.1f} giây/bài  '
          f'|  ước {int(3600 / tb) if tb else 0} bài/giờ')
    print(f'Số từ phần AI viết: thấp nhất {min(tu)}, trung bình {sum(tu) // len(tu)}, '
          f'cao nhất {max(tu)}')
    if kq['sku_loi']:
        print(f'\n{len(kq["sku_loi"])} bài lỗi:')
        for sku, loai, msg in kq['sku_loi'][:8]:
            print(f'   [{loai}] {sku}: {msg}')
    rot = [m for m in ds if not m.dat]
    print('=' * 74)
    if rot:
        print(f'KẾT LUẬN: TRƯỢT {len(rot)}/5 mốc. Chưa chạy sản lượng được.')
    elif che_do == 'thu':
        print('KẾT LUẬN: ĐẠT 5/5 nhưng đây là chế độ thử, chưa gọi AI và chưa đăng web.')
        print('          Chạy lại với --che-do nhap để nghiệm thu thật.')
    else:
        print('KẾT LUẬN: ĐẠT 5/5. Chạy sản lượng được.')
    print('=' * 74)
    return not rot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', default='site1')
    ap.add_argument('--mau')
    ap.add_argument('--so', type=int, default=30)
    ap.add_argument('--che-do', default='sinh', choices=A.CHE_DO)
    ap.add_argument('--nghi', type=float, default=30)
    a = ap.parse_args()

    import cauhinh as C
    mau_key = a.mau or C.lay_site(a.site).get('mau_mac_dinh', 'bao_gia')
    print('=' * 74)
    print(f'NGHIỆM THU  |  site {a.site}  |  mẫu {P.MAU[mau_key]["ten"]}  |  '
          f'{a.so} bài  |  chế độ {a.che_do}')
    if a.che_do != 'thu':
        print(f'AI: {A.NHA_CUNG_CAP} '
              f'({A.MODEL_CLAUDE if A.NHA_CUNG_CAP == "claude" else A.MODEL_GEMINI})'
              f'  |  nghỉ {a.nghi}s giữa 2 bài')
        print(f'Ước thời gian: {a.so * (a.nghi + 12) / 60:.0f} phút')
    print('=' * 74)

    kq, rows = chay(a.site, mau_key, a.so, a.che_do, a.nghi)
    ds = cham_diem(a.site, mau_key, kq, rows, a.che_do)
    ok = in_ket_qua(ds, kq, a.che_do)

    try:
        import baocao
        f, nb, ns = baocao.xuat(ma_site=a.site)
        print(f'\nĐã xuất báo cáo: {f}')
    except Exception as e:
        print(f'\n(không xuất được Excel: {e})')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
