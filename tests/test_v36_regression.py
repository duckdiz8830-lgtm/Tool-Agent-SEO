import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
# -*- coding: utf-8 -*-
"""
Ver 3.6 — Task 1/Task 2 regression: không cắt giữa token kỹ thuật + chứng
minh assertion batch mới (MOCK-3 trong test_v34_that_ui.py) thật sự bắt
được lỗi, không phải pass giả.

Chạy: python3 test_v36_regression.py
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ver 5.1 -- test o tests/, du lieu/module chinh o thu muc goc (len 1 cap)

KQ = []


def test(ma, mota, ok, gc=''):
    ok = bool(ok)
    KQ.append((ma, mota, ok))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}' + (f'  ({gc})' if gc else ''))
    return ok


def main():
    import render_phase2 as R
    import ai_wp_adapter as AWP
    import nhap_phase2 as N
    import validators as V
    import db_phase2 as DB

    # ============================================================ Task 1: token không bị cắt
    # Đúng các pattern work order liệt kê — kiểm rut_gon_an_toan() KHÔNG BAO
    # GIỜ trả về 1 mảnh cắt dở của các token này.
    cac_token_can_giu_nguyen = ['22/0.4KV', '12.7/0.23KV', '0.6/1kV', '3x50+1x25mm²']

    for gh in (20, 25, 30, 35, 40, 45, 50, 55, 60):
        for tok in cac_token_can_giu_nguyen:
            cau = f'Sản phẩm kỹ thuật {tok} loại cao cấp bền bỉ lâu dài'
            kq = R.rut_gon_an_toan(cau, gh)
            # nếu chuỗi kết quả có chứa 1 PHẦN của token (không phải toàn bộ
            # và không phải hoàn toàn không có) -> bị cắt dở, SAI
            bi_cat_do = False
            for i in range(1, len(tok)):
                manh = tok[:i]
                if kq.endswith(manh) and not kq.endswith(tok):
                    bi_cat_do = True
                    break
            if bi_cat_do:
                test('TOK', f'"{tok}" giới hạn {gh}: KHÔNG bị cắt dở (thực tế: {kq!r})', False)

    # gộp 1 dòng PASS tổng cho dễ đọc nếu không có FAIL nào ở trên
    if not any(ma == 'TOK' and not ok for ma, _, ok in KQ):
        test('TOK-ALL', f'Toàn bộ {len(cac_token_can_giu_nguyen)} token x 9 giới hạn khác nhau '
                        f'= {len(cac_token_can_giu_nguyen)*9} case: KHÔNG có case nào bị cắt dở', True)

    # tên/mã dài nằm SÁT giới hạn cắt (off-by-one quanh biên)
    ten_dai = 'Máy biến áp dầu 3 pha 22/0.4KV công suất 1000KVA loại kín Amorphous'
    for gh in range(55, 66):
        kq = R.rut_gon_an_toan(ten_dai, gh)
        test('TOK-BIEN', f'Giới hạn {gh} sát biên "22/0.4KV": không cắt dở (kq={kq!r})',
             '22/0.4K' not in kq or '22/0.4KV' in kq)

    # ============================================================ Task 1: batch thật 245 record
    if os.path.exists(os.path.join(BASE, 'test_batch_v36.db')):
        os.remove(os.path.join(BASE, 'test_batch_v36.db'))
    rpt = N.import_phase2_pipeline(os.path.join(BASE, 'du_lieu_goc', 'MASTER_4_PROFILE_SAN_PHAM.xlsx'),
                                   db_path=os.path.join(BASE, 'test_batch_v36.db'))
    con = DB.ket_noi(os.path.join(BASE, 'test_batch_v36.db'))
    did = rpt['ket_qua_theo_profile']['may_bien_ap_do_luong']['dataset_id']
    sp = DB.liet_ke_san_pham(con, dataset_id=did)
    ok_dem, loi_dem = 0, 0
    for row in sp:
        kq = AWP.sinh_va_dang_mock(con, did, row['record_id'], 'test.vn', {'ten': 'test'}, mau='chuan')
        if kq['ok']:
            ok_dem += 1
        else:
            loi_dem += 1
    test('BATCH-245', f'Batch Mock 245 sản phẩm máy biến áp: {ok_dem}/245 thành công, {loi_dem} lỗi',
         ok_dem == 245 and loi_dem == 0)
    con.close()
    os.remove(os.path.join(BASE, 'test_batch_v36.db'))

    # ============================================================ Task 2: chứng minh assertion MỚI có giá trị
    # Cố ý tạo 1 lỗi thật (không phải giả lập bằng cách gọi hàm test() sai)
    # -> chứng minh nếu dùng CÁCH KIỂM CŨ (chỉ tìm chữ "Xong" trong nhãn)
    # thì VẪN PASS dù có lỗi thật, còn CÁCH MỚI (đếm chính xác qua DB) sẽ
    # FAIL đúng như phải FAIL.
    if os.path.exists(os.path.join(BASE, 'test_batch_loi_v36.db')):
        os.remove(os.path.join(BASE, 'test_batch_loi_v36.db'))
    rpt2 = N.import_phase2_pipeline(os.path.join(BASE, 'du_lieu_goc', 'MASTER_4_PROFILE_SAN_PHAM.xlsx'),
                                    db_path=os.path.join(BASE, 'test_batch_loi_v36.db'))
    con2 = DB.ket_noi(os.path.join(BASE, 'test_batch_loi_v36.db'))
    did2 = rpt2['ket_qua_theo_profile']['may_bien_ap_do_luong']['dataset_id']
    sp2 = DB.liet_ke_san_pham(con2, dataset_id=did2)[:10]   # chỉ 10 record cho nhanh

    _goc = AWP.goi_ai_mock
    so_lan_goi = {'n': 0}

    def _gia_lap_bia_1_record(row, mau='chuan', do_tre_gia_lap=0.0):
        """Cố ý làm record ĐẦU TIÊN trả THÂN BÀI chứa số bịa.
        Ver 4.3.1 đổi policy: meta-only được fallback, nên proof test phải
        tiêm lỗi vào dac_diem_html để vẫn kiểm đúng invariant Hard Block core."""
        so_lan_goi['n'] += 1
        if so_lan_goi['n'] == 1:
            data, usage = _goc(row, mau=mau, do_tre_gia_lap=do_tre_gia_lap)
            data['dac_diem_html'] = (data.get('dac_diem_html') or '') + '<p>Chịu được 99kV bịa.</p>'
            return data, usage
        return _goc(row, mau=mau, do_tre_gia_lap=do_tre_gia_lap)

    AWP.goi_ai_mock = _gia_lap_bia_1_record
    try:
        ok3, loi3 = 0, 0
        nhan_cuoi = ''
        for row in sp2:
            kq = AWP.sinh_va_dang_mock(con2, did2, row['record_id'], 'test.vn', {'ten': 'test'}, mau='chuan')
            if kq['ok']:
                ok3 += 1
            else:
                loi3 += 1
        nhan_cuoi = f'Xong: {ok3}/{len(sp2)} thành công, {loi3} lỗi'
    finally:
        AWP.goi_ai_mock = _goc
        con2.close()
        os.remove(os.path.join(BASE, 'test_batch_loi_v36.db'))

    test('PROOF-1', f'Đã cố ý gây đúng 1 lỗi thật trong batch 10 record: {ok3}/{len(sp2)} thành công, '
                    f'{loi3} lỗi (kỳ vọng loi3=1)', loi3 == 1 and ok3 == len(sp2) - 1)

    cach_cu_pass = 'Xong' in nhan_cuoi   # cách kiểm CŨ (chỉ tìm chữ "Xong")
    cach_moi_pass = (ok3 == len(sp2) and loi3 == 0)   # cách kiểm MỚI (đếm chính xác)
    test('PROOF-2', f'Cách kiểm CŨ (chỉ tìm chữ "Xong" trong nhãn "{nhan_cuoi}") -> '
                    f'{"PASS SAI" if cach_cu_pass else "FAIL"} dù có lỗi thật '
                    f'(chứng minh cách cũ là pass giả)',
         cach_cu_pass is True)   # xác nhận ĐÚNG là cách cũ sẽ pass sai (để so sánh)
    test('PROOF-3', f'Cách kiểm MỚI (đếm chính xác qua DB) -> {"PASS" if cach_moi_pass else "FAIL ĐÚNG"} '
                    f'(phải FAIL vì có 1 lỗi thật — assertion mới có giá trị)',
         cach_moi_pass is False)   # xác nhận cách mới ĐÚNG LÀ PHẢI FAIL ở đây

    print()
    p = sum(1 for _, _, ok in KQ if ok)
    print(f'TỔNG: {p}/{len(KQ)} PASS')
    return KQ


if __name__ == '__main__':
    kq = main()
    if any(not ok for _, _, ok in kq):
        sys.exit(1)
