import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T2-11 + smoke test toàn bộ tab Phase 2 (A-E) qua giao-dien.py THẬT — không
phải gọi hàm logic trần, mà dựng đúng cửa sổ Tkinter thật rồi gọi các hàm xử
lý sự kiện y hệt khi người dùng bấm chuột.

Cần `python3-tk` (gói hệ thống, KHÔNG cài qua pip) và `xvfb` nếu chạy trên
máy không có màn hình (server/CI). Trên máy Windows của Thịnh có màn hình
thật thì bỏ `xvfb-run -a` chạy thẳng `python3 test_round2_ui_smoke.py` là đủ.

Chạy: xvfb-run -a python3 test_round2_ui_smoke.py    (Linux không màn hình)
      python3 test_round2_ui_smoke.py                 (Windows/máy có màn hình)
"""
import importlib.util
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ver 5.1 -- test o tests/, du lieu/module chinh o thu muc goc (len 1 cap)
DB_TEST = os.path.join(BASE, 'test_ui_smoke.db')

KET_QUA = []


def test(ma, mo_ta, dieu_kien):
    ok = bool(dieu_kien)
    KET_QUA.append((ma, mo_ta, ok))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mo_ta}')
    return ok


def main():
    if os.path.exists(DB_TEST):
        os.remove(DB_TEST)

    spec = importlib.util.spec_from_file_location('giao_dien', os.path.join(BASE, 'giao-dien.py'))
    gd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gd)

    app = gd.PhanMem()
    app.update()

    # -------------------------------------------------- T2-11: luồng RMU legacy còn nguyên
    # LƯU Ý (UI Gate): kể từ khi tách UI Ver 3 thành notebook riêng
    # (self.tab_ver3), notebook RMU (self.tab) chỉ còn đúng 6 tab gốc (0-5),
    # không còn tab "Phase 2" số 6 nữa (tab đó đã tách thành 5 tab Ver 3
    # riêng). Đây là thay đổi ĐÚNG Ý ĐỒ của UI Gate, không phải hồi quy.
    so_tab = app.tab.index('end')
    ten_tab = [app.tab.tab(i, 'text') for i in range(so_tab)]
    test('T2-11', f'Notebook RMU (self.tab) chỉ còn đúng 6 tab gốc (0-5), không lẫn tab Phase 2 — hiện có: {ten_tab}',
         so_tab == 6 and not any('Phase 2' in t for t in ten_tab))
    try:
        app.doc_cau_hinh()
        app.nap_san_pham()
        app.nap_kien_thuc_bang()
        app.nap_dashboard()
        app._nap_sp_thu()
        rmu_ok = True
    except Exception as e:
        rmu_ok = False
        print(f'   Lỗi RMU: {e}')
    test('T2-11', 'Toàn bộ hàm nạp dữ liệu RMU cũ (tab 0-5) chạy không crash', rmu_ok)

    # -------------------------------------------------- A. Nhập MASTER qua đúng hàm UI
    import db_phase2 as DB
    app._phase2_lam_import(os.path.join(BASE, 'du_lieu_goc', 'MASTER_4_PROFILE_SAN_PHAM.xlsx'))
    # _phase2_lam_import() gọi self.ui(...) để đẩy việc cập nhật dropdown về
    # luồng chính qua hàng đợi — trong ứng dụng thật, self.after(80,
    # self._boc_hang_doi) tự động rút hàng đợi mỗi 80ms nhờ mainloop() chạy
    # liên tục, không cần code gì thêm. Ở đây KHÔNG chạy mainloop() (test
    # không có người dùng thật để tương tác liên tục), nên rút hàng đợi tay
    # 1 lần cho chắc, mô phỏng đúng 1 nhịp timer sẽ tự xảy ra trong thực tế.
    app._boc_hang_doi()
    test('R2-10.A', 'Nút nhập Excel (dispatcher) chạy qua UI thật, ra đủ 4 dataset',
         len(app.cb_phase2_dataset['values']) == 4)

    # -------------------------------------------------- B. danh sách + chọn/bỏ chọn
    gt = [g for g in app.cb_phase2_dataset['values'] if 'may_bien_ap' in g][0]
    app.v_phase2_dataset.set(gt)
    app._phase2_nap_danh_sach()
    test('R2-10.B', 'Bảng sản phẩm hiện đủ 245 dòng của dataset máy biến áp',
         len(app.bang_phase2.get_children()) == 245)

    first_iid = app.bang_phase2.get_children()[0]
    app.bang_phase2.selection_set(first_iid)
    app.bang_phase2.focus(first_iid)
    app._phase2_doi_chon()
    giu_focus = app.bang_phase2.focus() == first_iid
    da_chon = app.bang_phase2.item(first_iid, 'values')[0] == '✓'
    test('R2-10.B', 'Bấm đúp chọn viết: cột Chọn hiện ✓, focus KHÔNG mất sau khi bảng refresh',
         da_chon and giu_focus)

    # -------------------------------------------------- C. Thử 1 bài — prompt Phase 2 thật
    app._phase2_xem_prompt()
    noi_dung_prompt = app.txt_phase2_thu.get('1.0', 'end')
    test('R2-10.C', 'Xem prompt hiện đủ SYSTEM + USER, không phải prompt RMU cũ',
         'SYSTEM' in noi_dung_prompt and 'USER' in noi_dung_prompt and
         'QUY TẮC BẮT BUỘC' in noi_dung_prompt)

    app._phase2_chay_thu()
    ket_qua_thu = app.txt_phase2_thu.get('1.0', 'end')
    test('R2-10.C', 'Chạy AI mock + dựng HTML hiện Title/Meta/Slug/Hard Block',
         all(k in ket_qua_thu for k in ('Title:', 'Meta:', 'Slug:', 'Hard Block:')))

    # -------------------------------------------------- D. Chạy hàng loạt (mock)
    app._phase2_viec_chay_hang_loat('chuan', app._phase2_dataset_id_dang_chon(), app._v3_site_key(), app._v3_site_cfg())
    test('R2-10.D', 'Chạy hàng loạt (mock) không lỗi', True)

    # -------------------------------------------------- E. Dashboard
    app._phase2_nap_dashboard()
    test('R2-10.E', 'Dashboard hiện >= 1 dòng sau khi chạy',
         len(app.bang_phase2_dash.get_children()) >= 1)

    app.destroy()
    if os.path.exists(DB_TEST):
        os.remove(DB_TEST)

    print()
    so_pass = sum(1 for _, _, ok in KET_QUA if ok)
    print(f'TỔNG UI SMOKE TEST: {so_pass}/{len(KET_QUA)} PASS')
    return KET_QUA


if __name__ == '__main__':
    kq = main()
    if any(not ok for _, _, ok in kq):
        sys.exit(1)
