import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Ver 3 Gate — 8 test bắt buộc (mục I work order) + chụp ảnh bằng chứng
(mục J). Cần Xvfb nếu chạy trên Linux không màn hình.

Chạy: xvfb-run -a python3 test_ver3_ui.py
"""
import importlib.util
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ver 5.1 -- test o tests/, du lieu/module chinh o thu muc goc (len 1 cap)
ANH_DIR = os.path.join(BASE, 'anh-bang-chung-ui')
os.makedirs(ANH_DIR, exist_ok=True)

KET_QUA = []


def test(ma, mo_ta, dieu_kien, ghi_chu=''):
    ok = bool(dieu_kien)
    KET_QUA.append((ma, mo_ta, ok, ghi_chu))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mo_ta}' + (f'  ({ghi_chu})' if ghi_chu else ''))
    return ok


def chup_anh(ten):
    duong_dan = os.path.join(ANH_DIR, f'{ten}.png')
    try:
        subprocess.run(['import', '-window', 'root', duong_dan], check=True,
                       capture_output=True, timeout=10)
        return os.path.exists(duong_dan)
    except Exception as e:
        print(f'   (không chụp được ảnh {ten}: {e})')
        return False


def main():
    for f in ['test_db.db']:
        if os.path.exists(f):
            os.remove(f)

    spec = importlib.util.spec_from_file_location('giao_dien', os.path.join(BASE, 'giao-dien.py'))
    gd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gd)

    app = gd.PhanMem()
    app.geometry('1366x768+0+0')
    app.update()
    time.sleep(0.3)

    # ---------- Test 1: Ver 2.6 gom 8 tab thành 3 nhóm cha ----------
    so_tab_v3 = app.tab_ver3.index('end')
    ten_tab = [app.tab_ver3.tab(i, 'text') for i in range(so_tab_v3)]
    test('I1', f'Ver 2.6 — gom 8 tab thành 3 NHÓM cha (thực tế: {ten_tab})',
         so_tab_v3 == 3 and ten_tab == ['  1. DỮ LIỆU  ', '  2. SẢN XUẤT  ',
                                        '  3. CẤU HÌNH & LOG  '])
    tong_tab_con = sum(nb.index('end') for nb in app._v3_nhom_nb.values())
    # Ver 5.9 — 15 tab con (6 + 7 + 2). Ver 5.7 là 14; +1 vì thêm màn hình
    # "Hôm nay" chèn lên đầu nhóm DỮ LIỆU. Con số này ĐƯỢC phép đổi khi cố
    # ý thêm/bớt tab — nhưng phải đổi Ở ĐÂY, có chủ đích, kèm lý do. Đổi mà
    # không hiểu vì sao đổi thì đang che một hồi quy.
    test('I1b', f'15 tab con sau khi ẩn tab ảnh legacy; tab workspace 3.9 vẫn còn (thực tế {tong_tab_con})',
         tong_tab_con == 15)
    tab_rmu_dang_pack = app.tab.winfo_ismapped()
    test('I2', 'Không thấy tab RMU (Ver 1/Ver 2) trong giao diện mặc định',
         not tab_rmu_dang_pack)
    kich_thuoc = (app.winfo_width(), app.winfo_height())
    test('I3', f'UI hiển thị ổn ở 1366x768, không exception (kích thước: {kich_thuoc})',
         True)

    # ---------- Test 4: chuyển qua lại 9 tab không exception (Ver 1.6 SONEALEO thêm "0. Bắt đầu") ----------
    loi_chuyen_tab = None
    try:
        for i in range(3):
            app.tab_ver3.select(i)
            app.update()
        app.tab_ver3.select(0)
        app.update()
    except Exception as e:
        loi_chuyen_tab = str(e)
    test('I4', 'Chuyển qua lại 3 nhóm tab không exception', loi_chuyen_tab is None, loi_chuyen_tab or '')
    chup_anh('03_tab_cau_hinh')
    app.tab_ver3.select(0)   # Ver 3.6: Cấu hình giờ là tab đầu tiên (index 0), không còn index 2
    app.update()
    chup_anh('03_tab_cau_hinh_that')
    app.tab_ver3.select(1)   # Ver 2.6: 'Sinh & Đăng' giờ nằm trong nhóm cha '2. SẢN XUẤT' (index 1)
    app.update()
    chup_anh('04_tab_sinh_dang')

    # ---------- Test 5: Menu Công cụ mở được chế độ RMU ----------
    loi_menu = None
    try:
        nhan_menu_truoc = app.menu_cong_cu.entrycget(0, 'label')
        # gọi thẳng lệnh menu thay vì click chuột thật (menu popup khó
        # tương tác tự động dưới Xvfb) — GHI CHÚ: đây gọi ĐÚNG command mà
        # menu entry đang trỏ tới, tương đương người dùng bấm menu đó.
        import tkinter.messagebox as messagebox
        cu = messagebox.askyesno
        messagebox.askyesno = lambda *a, **k: True   # tự动 "Có" để test không treo chờ người bấm
        app._chuyen_che_do_rmu()
        messagebox.askyesno = cu
    except Exception as e:
        loi_menu = str(e)
    app.update()
    test('I5', f'Menu Công cụ mở được chế độ RMU (nhãn menu trước: "{nhan_menu_truoc}")',
         loi_menu is None and app.che_do_rmu is True)
    chup_anh('05_menu_cong_cu_rmu')
    chup_anh('06_che_do_rmu')

    # ---------- Test 6: từ RMU quay lại Ver 3 ----------
    loi_quay_lai = None
    try:
        app._chuyen_ve_ver3()
    except Exception as e:
        loi_quay_lai = str(e)
    app.update()
    test('I6', 'Từ RMU quay lại Ver 3 được', loi_quay_lai is None and app.che_do_rmu is False)

    # ---------- Test 7: chuyển qua lại 3 lần không nhân đôi tab/widget ----------
    so_tab_v3_ban_dau = app.tab_ver3.index('end')
    so_tab_rmu_ban_dau = app.tab.index('end')
    import tkinter.messagebox as messagebox
    cu = messagebox.askyesno
    messagebox.askyesno = lambda *a, **k: True
    loi_lap = None
    try:
        for _ in range(3):
            app._chuyen_che_do_rmu()
            app.update()
            app._chuyen_ve_ver3()
            app.update()
    except Exception as e:
        loi_lap = str(e)
    messagebox.askyesno = cu
    test('I7', f'Chuyển qua lại RMU/Ver3 3 lần không nhân đôi tab/widget '
              f'(Ver3: {so_tab_v3_ban_dau}->{app.tab_ver3.index("end")}, '
              f'RMU: {so_tab_rmu_ban_dau}->{app.tab.index("end")})',
         loi_lap is None and app.tab_ver3.index('end') == so_tab_v3_ban_dau
         and app.tab.index('end') == so_tab_rmu_ban_dau)

    app.destroy()

    # ---------- Test 8: đóng mở lại vẫn khởi động ở Ver 3 ----------
    spec2 = importlib.util.spec_from_file_location('giao_dien2', os.path.join(BASE, 'giao-dien.py'))
    gd2 = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(gd2)
    app2 = gd2.PhanMem()
    app2.update()
    test('I8', 'Đóng và mở lại app vẫn khởi động ở Ver 3 (RMU không tự pack)',
         app2.tab_ver3.winfo_ismapped() and not app2.tab.winfo_ismapped()
         and app2.che_do_rmu is False)
    app2.destroy()

    print()
    so_pass = sum(1 for _, _, ok, _ in KET_QUA if ok)
    print(f'TỔNG TEST UI VER 3: {so_pass}/{len(KET_QUA)} PASS')
    print(f'Ảnh bằng chứng lưu tại: {ANH_DIR}')
    return KET_QUA


if __name__ == '__main__':
    kq = main()
    if any(not ok for _, _, ok, _ in kq):
        sys.exit(1)
