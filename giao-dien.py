#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Giao diện phần mềm. Bấm đúp PHAN-MEM.bat, hoặc: python giao-dien.py
Chỉ dùng tkinter có sẵn trong Python.

Giao diện KHÔNG chứa logic sinh bài. Mọi việc gọi vào autopost.sinh_mot_bai().
"""
import csv
import phien_ban as PB   # Ver 4.5 — nguồn duy nhất chuỗi phiên bản
import io
import os
import queue
import re
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

import cauhinh as C          # noqa: E402
import dulieu as D           # noqa: E402
import autopost as A         # noqa: E402  (import sớm để autopost.nap_env() đọc cau-hinh.env trước khi UI Ver 3 hiển thị)

NAVY, GREEN, AMBER, RED = '#1F3864', '#2E7D32', '#BF8F00', '#C00000'
XAM, XAM_NHAT, TRANG = '#5A5A5A', '#F4F5F7', '#FFFFFF'
CHU = 'Segoe UI'

# ---------------------------------------------------------------- palette Ver 3 (UI Gate)
# Riêng cho các tab Ver 3 — KHÔNG đụng NAVY/GREEN/AMBER/RED/XAM/XAM_NHAT/TRANG
# ở trên (đó là màu RMU cũ, giữ nguyên 100% để không ảnh hưởng giao diện
# rollback). Ver 1.6 SONEALEO — đổi sang DARK MODE theo yêu cầu Thịnh
# ("đỡ mỏi mắt khi ngồi lâu").
# Ver 2.6 — ĐỔI SANG LIGHT MODE, palette "C — Trung tính xám" (Thịnh
# chọn từ 3 bản preview: nền xám-xanh rất nhạt, card trắng nổi lên, accent
# teal). Dark mode Ver 1.6 bị chê "xấu hơn bản cũ" — bỏ hẳn, không giữ lại
# làm tuỳ chọn (không đáng công bảo trì 2 theme cho 1 người dùng).
V3_NAVY = '#0F766E'      # thanh header — teal đậm làm dải màu thương hiệu (giữ tên biến cũ
                         # để đỡ sửa nhiều chỗ, nhưng giờ mang màu teal, không phải navy nữa)
V3_HEADING = '#0F172A'   # chữ tiêu đề/heading — than đậm, đọc rõ trên nền trắng/xám nhạt
V3_TEAL = '#0F766E'      # màu nhấn / nút chính / tab đang chọn
V3_BG = '#F8FAFC'        # nền chính (xám-xanh rất nhạt)
V3_CARD = '#FFFFFF'      # nền khối/card (trắng, nổi lên trên nền xám)
V3_BORDER = '#E2E8F0'    # viền
V3_TEXT = '#1E293B'      # chữ chính (than đậm)
V3_MUTED = '#64748B'     # chữ phụ/ghi chú
V3_OK = '#16A34A'        # thành công
V3_WARN = '#D97706'      # cảnh báo
V3_ERR = '#DC2626'       # lỗi
V3_TAB_MO = '#F1F5F9'    # nền tab chưa chọn

CHE_DO = [('thu', 'Chạy thử   (không gọi AI, không tốn lượt)'),
          ('sinh', 'Sinh bài   (gọi AI, lưu ra file, chưa đăng)'),
          ('nhap', 'Đăng nháp   (lên web, khách không thấy)'),
          ('dang', 'Đăng thật   (hiện ra ngoài ngay)')]


class ChuyenHuongIn(io.TextIOBase):
    """Router stdout theo thread: worker nào đăng ký queue nào thì print
    của thread đó đi đúng queue; thread khác vẫn dùng stdout gốc.
    """

    def __init__(self, stdout_goc):
        self.stdout_goc = stdout_goc
        self._theo_thread = {}
        self._lock = threading.RLock()

    def gan_thread(self, hang_doi):
        with self._lock:
            self._theo_thread[threading.get_ident()] = hang_doi

    def bo_thread(self):
        with self._lock:
            self._theo_thread.pop(threading.get_ident(), None)

    def con_thread(self):
        with self._lock:
            return bool(self._theo_thread)

    def write(self, s):
        if not s:
            return 0
        with self._lock:
            q = self._theo_thread.get(threading.get_ident())
        if q is not None:
            q.put(s)
            return len(s)
        # Windows chạy bằng pythonw có thể có sys.stdout/sys.__stdout__ = None.
        # Router vẫn phải nuốt log an toàn thay vì gọi .write() lên None/stream đã đóng.
        if self.stdout_goc is None:
            return len(s)
        try:
            return self.stdout_goc.write(s)
        except (AttributeError, ValueError, OSError):
            return len(s)

    def flush(self):
        if self.stdout_goc is None:
            return None
        try:
            return self.stdout_goc.flush()
        except (AttributeError, ValueError, OSError):
            return None


_STDOUT_ROUTER_LOCK = threading.RLock()
_STDOUT_ROUTER = None

def _bat_stdout_worker(hang_doi):
    """Đăng ký stdout cho thread hiện tại mà không giành sys.stdout giữa worker."""
    global _STDOUT_ROUTER
    with _STDOUT_ROUTER_LOCK:
        if _STDOUT_ROUTER is None or sys.stdout is not _STDOUT_ROUTER:
            _STDOUT_ROUTER = ChuyenHuongIn(sys.stdout)
            sys.stdout = _STDOUT_ROUTER
        router = _STDOUT_ROUTER
        router.gan_thread(hang_doi)
        return router


def _tat_stdout_worker(router):
    global _STDOUT_ROUTER
    with _STDOUT_ROUTER_LOCK:
        router.bo_thread()
        if not router.con_thread() and sys.stdout is router:
            sys.stdout = router.stdout_goc
            if _STDOUT_ROUTER is router:
                _STDOUT_ROUTER = None


class PhanMem(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(PB.NHAN_DAY_DU)
        self.geometry('1280x800')
        self.minsize(1024, 700)
        self.configure(bg=V3_BG)
        self.q = queue.Queue()
        self.dung_lai = threading.Event()
        self.dang_chay = False
        self.san_pham = []
        self.che_do_rmu = False   # False = đang ở Ver 3 (mặc định), True = đang ở RMU rollback

        self._kieu()
        self._bat_copy_context()
        self._menu()
        self._dau_trang()
        # Ver 1.6 SONEALEO — đổi từ orient='vertical' (nhật ký xếp CHỒNG dưới
        # tab, chiếm hết chiều ngang) sang 'horizontal' (nhật ký nằm BÊN
        # PHẢI, ~40% chiều rộng — Thịnh yêu cầu, xem nhật ký + làm việc ở
        # tab cùng lúc không phải cuộn xuống). Vị trí sash đặt ở
        # _dat_ti_le_chia_man() sau khi cửa sổ có kích thước thật.
        self.chia_man = tk.PanedWindow(self, orient='horizontal', sashwidth=9,
                                       bg=V3_BORDER, bd=0, sashrelief='raised')
        self.chia_man.pack(fill='both', expand=True, padx=14, pady=(8, 0))

        # Khung chứa DUY NHẤT được add vào chia_man — bên trong chứa CẢ 2
        # notebook (Ver 3 + RMU), chỉ 1 trong 2 được pack() hiện ra tại một
        # thời điểm (pack_forget() cái kia). Cả 2 notebook dựng widget đúng
        # 1 LẦN lúc khởi động — chuyển qua lại chỉ pack/pack_forget, không
        # bao giờ tạo lại widget -> không nhân đôi dù đổi chế độ nhiều lần.
        self.khung_noi_dung = tk.Frame(self.chia_man, bg=V3_BG)
        self.chia_man.add(self.khung_noi_dung, stretch='always', minsize=420)

        # ---- notebook RMU (Ver 1/Ver 2) — dựng đủ 6 tab như cũ, KHÔNG pack mặc định
        self.tab = ttk.Notebook(self.khung_noi_dung)
        self._tab_tong_quan()
        self._tab_nhap()
        self._tab_cau_hinh()
        self._tab_san_pham()
        self._tab_thu_mot_bai()
        self._tab_chay()

        # ---- notebook Ver 3 — 5 tab chính, mặc định hiện ra
        self.v_phase2_dataset = tk.StringVar()   # dùng chung Tab 2 (bộ lọc) + Tab 4 (hiển thị)
        self.v3_active_record_id = None          # record đang active/focus, dùng cho Xem prompt/HTML (Task 1.2)
        self.v3_dung_lai = threading.Event()      # cờ Force Stop riêng cho luồng chạy Ver 3
        self.jobs_dung_lai = threading.Event()    # Ver 3.9 — cờ Force Stop RIÊNG cho luồng Article Jobs, tách hẳn khỏi v3_dung_lai (2 luồng độc lập, không đụng nút của nhau)
        self.tab_ver3 = ttk.Notebook(self.khung_noi_dung, style='V3.TNotebook')
        # Ver 2.6 — GOM 8 TAB THÀNH 3 NHÓM (Thịnh: "UI rườm rà, nhức đầu").
        # Dùng notebook LỒNG: 3 tab cha, mỗi tab cha chứa 1 notebook con.
        # Các hàm _v3_tab_* KHÔNG phải sửa — _v3_tab_cuon() tự tra bảng
        # _NHOM_TAB để add vào đúng notebook con.
        self._v3_nhom_nb = {}
        for ma_nhom, nhan_nhom in (('du_lieu', '  1. DỮ LIỆU  '),
                                   ('san_xuat', '  2. SẢN XUẤT  '),
                                   ('he_thong', '  3. CẤU HÌNH & LOG  ')):
            khung = ttk.Frame(self.tab_ver3, style='V3.TFrame')
            self.tab_ver3.add(khung, text=nhan_nhom)
            nb_con = ttk.Notebook(khung, style='V3.TNotebook')
            nb_con.pack(fill='both', expand=True)
            self._v3_nhom_nb[ma_nhom] = nb_con

        # Ver 2.6 — bỏ tab "0. Bắt đầu" (Thịnh yêu cầu, không cần) —
        # hàm _v3_tab_0_bat_dau() vẫn còn định nghĩa trong code, chỉ không
        # gọi nữa, để nếu sau này đổi ý thì gọi lại dễ.
        self._v3_tab_3_cau_hinh()
        self._v3_tab_1_nhap_du_lieu()
        self._v3_tab_2_san_pham()
        self._v3_tab_4_sinh_dang()
        self._v3_tab_5_theo_doi()
        self._v3_tab_6_outline_studio()
        self._v3_tab_7_article_jobs()
        self._v3_tab_8_enhance()
        # Ver 3.9 — ẨN tab ảnh legacy khỏi UI; giữ nguyên toàn bộ hàm/code để rollback.
        # self._v3_tab_9_anh()
        self._v3_tab_10_vision()
        # Ver 5.5 — Tab SEO Post. Bọc try để module mới lỗi cũng KHÔNG
        # làm sập app: 10 tab cũ vẫn chạy, chỉ mất tab mới + in lỗi ra log.
        # Ver 5.8 — Tab SEO Post nay cắm qua HỢP ĐỒNG giac_cam.py thay vì
        # nhận thẳng `self`. Trước đây module này nhét 15 thuộc tính
        # app._sp_* vào vỏ ứng dụng và với vào app 57 lượt — bẩn nhất hệ.
        # Nay nó tự giữ state trong class TabSeoPost, vỏ không biết nó có
        # bao nhiêu widget. GiacCam chặn cứng: với ra ngoài 5 chân là ném
        # LoiViPhamGiac nêu đích danh, không âm thầm hỏng.
        # Giữ try/except: module mới lỗi cũng KHÔNG làm sập app, chỉ mất
        # đúng tab đó và in lỗi ra log.
        try:
            import giac_cam
            import tab_seo_post
            tab_seo_post.gan_vao(self._v3_nhom_nb['san_xuat'],
                                 giac_cam.GiacCam(self, 'tab_seo_post'))
        except Exception as _e:
            print(f'!! Tab SEO Post không dựng được: {type(_e).__name__}: {_e}')

        # Ver 5.9 — màn hình "Hôm nay": làm gì tiếp, cái gì đang chặn.
        # Đặt ở nhóm 'du_lieu' và CHÈN LÊN ĐẦU (index 0) vì đây là thứ nên
        # nhìn trước tiên khi mở tool. Module này viết SAU giac_cam.py và
        # không sửa hợp đồng dòng nào — đó là phép thử xem hợp đồng có thật
        # sự dùng được để ráp tính năng mới hay không.
        try:
            import giac_cam as _gc
            import tab_hom_nay
            _t = tab_hom_nay.gan_vao(self._v3_nhom_nb['du_lieu'],
                                     _gc.GiacCam(self, 'tab_hom_nay'))
            self._v3_nhom_nb['du_lieu'].insert(0, _t.ngoai)
            self._v3_nhom_nb['du_lieu'].select(0)
        except Exception as _e:
            print(f'!! Tab Hôm nay không dựng được: {type(_e).__name__}: {_e}')
        # Ver 3.1 — 2 tab con mới (Làm giàu dữ liệu / Xem dữ liệu) nằm ở
        # FILE RIÊNG man_hinh_du_lieu.py — God Class chỉ thêm mấy dòng này.
        try:
            import man_hinh_du_lieu as _mhdl
            _mhdl.gan_vao(self._v3_nhom_nb['du_lieu'], self)
        except Exception as _e:
            print(f'[Ver 3.1] Không nạp được màn hình dữ liệu mới: {_e}')
        # Ver 3.5 — tab HÀNG ĐỢI: màn hình trạng thái lô SKU (file riêng
        # hang_doi.py). Đặt ở nhóm 'san_xuat' vì đây là chỗ chọn việc để
        # chạy, không phải chỗ xem dữ liệu. Lỗi ở đây KHÔNG được làm chết
        # tool -> bọc try, nhưng báo rõ chứ không im lặng.
        try:
            import hang_doi as _hd
            _hd.gan_vao(self._v3_nhom_nb['san_xuat'], self)
        except Exception as _e:
            print(f'[Ver 3.5] Không nạp được tab Hàng đợi: {_e}')
        # Ver 3.7 — tab ẢNH BÀI VIẾT (file riêng tab_anh.py). Đặt ở nhóm
        # 'san_xuat' vì nó nằm trên cùng dòng chảy với Sinh & Đăng.
        # KHÔNG gọi AI, không phụ thuộc tkinterdnd2.
        try:
            import giac_cam as _gc2
            import tab_anh as _ta
            self._tab_anh_37 = _ta.gan_vao(self._v3_nhom_nb['san_xuat'],
                                           _gc2.GiacCam(self, 'tab_anh'))
        except Exception as _e:
            print(f'[Ver 3.7] Không nạp được tab Ảnh bài viết: {_e}')
        self.tab_ver3.pack(fill='both', expand=True)   # Ver 3 hiện mặc định, RMU (self.tab) chưa pack

        self._nhat_ky()
        self.tt = tk.Label(self, text=PB.NHAN_SAN_SANG, bg=XAM_NHAT, fg=XAM,
                           font=(CHU, 9), anchor='w', padx=14)
        self.tt.pack(fill='x', side='bottom', ipady=5)

        # Ver 1.6 — đặt sash chia_man ở ~60/40 (tab/nhật ký). update_idletasks()
        # BẮT BUỘC trước — ép Tk tính layout thật ngay lập tức (đồng bộ),
        # không dùng self.after(...) hẹn giờ cho LẦN ĐẦU (đã thử, timing
        # không ổn định — có lúc sash rơi về minsize thay vì 60% thật).
        self.update_idletasks()
        self._dat_ti_le_chia_man(ep=True)
        # VÁ THÊM — bind <Configure> để sash TỰ CÂN LẠI mỗi khi cửa sổ đổi
        # kích thước thật (resize tay, maximize, đổi màn hình...) — không
        # thì sash là pixel cố định, cửa sổ to ra là tỉ lệ bị lệch hẳn
        # (log nuốt gần hết màn hình — lỗi thật Thịnh gặp trên máy).
        self.bind('<Configure>', self._khi_resize_cua_so)

        self._kiem_thu_vien()
        self.doc_cau_hinh()
        self.nap_san_pham()
        self.nap_kien_thuc_bang()
        self.nap_dashboard()
        self._nap_sp_thu()
        self._phase2_nap_dataset()
        self._v3_di_chuyen_du_lieu_khoa_cu()   # Ver 3.5: tự dò dữ liệu bản cũ khoá theo tên lúc khởi động
        self._v3_nap_danh_sach_dataset()
        self._v3_nap_dashboard()
        # Task 1.3 (Ver 3.4 UI) — nhật ký mặc định ~35% chiều cao, tính trên
        # winfo_height() CỦA self.chia_man (đã loại trừ header/status bar
        # đóng gói ở ngoài PanedWindow) thay vì self.winfo_height() (bao gồm
        # cả 2 khối đó) — công thức cũ lệch vì cộng nhầm phần header/status
        # vào phép tính %, khiến nhật ký hiện ra thấp hơn 35% thật sự trên
        # màn hình có header/status bar cao (DPI khác nhau trên Windows).
        def _dat_sash():
            self.chia_man.update_idletasks()
            tong = self.chia_man.winfo_height()
            log_h = max(180, int(tong * 0.35))
            vi_tri = max(300, tong - log_h)
            self.chia_man.sash_place(0, 0, vi_tri)
        self.after(150, _dat_sash)
        self._boc_hang_doi_job = self.after(80, self._boc_hang_doi)
        self.protocol('WM_DELETE_WINDOW', self._dong)

    # ------------------------------------------------------------ Ver 4.4 D1 — Copy context
    def _copy_clipboard(self, text):
        text = str(text or '')
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update_idletasks()

    def _hien_menu_copy(self, event, text):
        if text is None or str(text) == '':
            return
        m = tk.Menu(self, tearoff=0)
        m.add_command(label='Copy', command=lambda t=str(text): self._copy_clipboard(t))
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()

    def _menu_copy_label(self, event):
        w = event.widget
        text = ''
        try:
            tv = w.cget('textvariable')
            if tv:
                text = w.getvar(tv)
        except Exception:
            pass
        if not text:
            try:
                text = w.cget('text')
            except Exception:
                text = ''
        self._hien_menu_copy(event, text)
        return 'break'

    def _menu_copy_tree(self, event):
        tree = event.widget
        iid = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        if not iid or not col:
            return
        tree.focus(iid)
        if iid not in tree.selection():
            tree.selection_set(iid)
        vals = tree.item(iid, 'values') or ()
        try:
            idx = int(col[1:]) - 1
            text = vals[idx] if 0 <= idx < len(vals) else ''
        except Exception:
            text = ''
        self._hien_menu_copy(event, text)
        return 'break'

    def _bat_copy_context(self):
        # Bind theo class nên áp dụng cho mọi bảng/nhãn được tạo sau đó, kể cả
        # tab_anh.py và các tab plugin. Ít nhất mã hàng/tên/URL đều copy được.
        self.bind_class('TLabel', '<Button-3>', self._menu_copy_label, add='+')
        self.bind_class('Label', '<Button-3>', self._menu_copy_label, add='+')
        self.bind_class('Treeview', '<Button-3>', self._menu_copy_tree, add='+')

    # ------------------------------------------------------------ khung
    def _kieu(self):
        s = ttk.Style(self)
        try:
            s.theme_use('clam')
        except tk.TclError:
            pass
        s.configure('TNotebook', background=TRANG, borderwidth=0)
        s.configure('TNotebook.Tab', font=(CHU, 10, 'bold'), padding=(18, 9))
        s.map('TNotebook.Tab', background=[('selected', TRANG)],
              foreground=[('selected', NAVY)])
        s.configure('TFrame', background=TRANG)
        s.configure('TLabel', background=TRANG, font=(CHU, 10))
        s.configure('Mo.TLabel', foreground=XAM, font=(CHU, 9))
        s.configure('Dam.TLabel', font=(CHU, 11, 'bold'), foreground=NAVY)
        s.configure('TButton', font=(CHU, 10), padding=(12, 7))
        s.configure('Chinh.TButton', font=(CHU, 11, 'bold'), padding=(16, 10))
        s.configure('TEntry', padding=5)
        s.configure('Treeview', font=(CHU, 9), rowheight=24)
        s.configure('Treeview.Heading', font=(CHU, 9, 'bold'))
        s.configure('TCombobox', padding=5)

        # ---------------------------------------------------------- style riêng Ver 3
        s.configure('V3.TNotebook', background=V3_BG, borderwidth=0)
        s.configure('V3.TNotebook.Tab', font=(CHU, 10, 'bold'), padding=(20, 10),
                   background=V3_TAB_MO, foreground=V3_TEXT)
        s.map('V3.TNotebook.Tab', background=[('selected', V3_TEAL)],
             foreground=[('selected', TRANG)])
        s.configure('V3.TFrame', background=V3_BG)
        s.configure('V3Card.TFrame', background=V3_CARD, relief='solid', borderwidth=1)
        s.configure('V3.TLabel', background=V3_BG, foreground=V3_TEXT, font=(CHU, 10))
        s.configure('V3Card.TLabel', background=V3_CARD, foreground=V3_TEXT, font=(CHU, 10))
        s.configure('V3Tieu.TLabel', background=V3_BG, foreground=V3_HEADING, font=(CHU, 13, 'bold'))
        s.configure('V3CardTieu.TLabel', background=V3_CARD, foreground=V3_HEADING, font=(CHU, 12, 'bold'))
        s.configure('V3Mo.TLabel', background=V3_BG, foreground=V3_MUTED, font=(CHU, 9))
        s.configure('V3CardMo.TLabel', background=V3_CARD, foreground=V3_MUTED, font=(CHU, 9))
        s.configure('V3Ghi.TLabel', background=V3_CARD, foreground=V3_WARN, font=(CHU, 9, 'italic'))
        s.configure('V3.TButton', font=(CHU, 10), padding=(12, 7))
        s.configure('V3Chinh.TButton', font=(CHU, 11, 'bold'), padding=(18, 10))
        s.map('V3Chinh.TButton', background=[('!disabled', V3_TEAL)])
        s.configure('V3Xoa.TButton', font=(CHU, 10), padding=(12, 7))
        s.map('V3Xoa.TButton', foreground=[('!disabled', V3_ERR)])
        s.configure('V3.TLabelframe', background=V3_CARD, borderwidth=1, relief='solid')
        s.configure('V3.TLabelframe.Label', background=V3_CARD, foreground=V3_HEADING,
                   font=(CHU, 11, 'bold'))
        # Thanh tiến trình nổi bật — dày hơn mặc định (22px vs ~10px), màu
        # teal nhấn mạnh, để thấy rõ đang chạy giữa 1 màn hình nhiều khối.
        s.configure('V3.Horizontal.TProgressbar', thickness=24, troughcolor=V3_TAB_MO,
                   background=V3_TEAL, bordercolor=V3_BORDER, lightcolor=V3_TEAL,
                   darkcolor=V3_TEAL)
        s.configure('V3Dung.TButton', font=(CHU, 11, 'bold'), padding=(18, 10))
        s.map('V3Dung.TButton', foreground=[('!disabled', TRANG)],
             background=[('!disabled', V3_ERR), ('disabled', V3_TAB_MO)])

    def _dau_trang(self):
        h = tk.Frame(self, bg=V3_NAVY, height=48)
        h.pack(fill='x')
        h.pack_propagate(False)
        tk.Label(h, text=PB.NHAN_DAY_DU, bg=V3_NAVY, fg=TRANG,
                 font=(CHU, 16, 'bold')).pack(side='left', padx=16)

    def _menu(self):
        """Menu 'Công cụ' — DUY NHẤT cách vào chế độ RMU rollback (không đặt
        nút trên màn hình chính, không phím tắt, đúng work order UI)."""
        thanh = tk.Menu(self)
        self.config(menu=thanh)
        self.menu_cong_cu = tk.Menu(thanh, tearoff=0)
        thanh.add_cascade(label='Công cụ', menu=self.menu_cong_cu)
        self.menu_cong_cu.add_command(label='Chế độ RMU (rollback)', command=self._chuyen_che_do_rmu)

    def _chuyen_che_do_rmu(self):
        if not messagebox.askyesno(
                'Chế độ RMU (rollback)',
                'Chuyển sang giao diện RMU cũ (Ver 1/Ver 2)?\n\n'
                'Đây là chế độ dự phòng, không phải luồng chính. Dữ liệu Ver 3 '
                '(MASTER 4-Profile) không bị ảnh hưởng khi chuyển qua lại.'):
            return
        self.tab_ver3.pack_forget()
        self.tab.pack(fill='both', expand=True)
        self.che_do_rmu = True
        self.menu_cong_cu.entryconfig(0, label='Trở về LOTECH VER 3', command=self._chuyen_ve_ver3)
        self.tt.config(text='Đang ở chế độ RMU (rollback) — Ver 1/Ver 2')

    def _chuyen_ve_ver3(self):
        self.tab.pack_forget()
        self.tab_ver3.pack(fill='both', expand=True)
        self.che_do_rmu = False
        self.menu_cong_cu.entryconfig(0, label='Chế độ RMU (rollback)', command=self._chuyen_che_do_rmu)
        self.tt.config(text='Sẵn sàng · ' + PB.NHAN_AUTOPOST)

    def _o(self, cha, nhan, mo_ta='', an=False):
        k = ttk.Frame(cha)
        k.pack(fill='x', pady=(9, 0))
        ttk.Label(k, text=nhan, width=26).pack(side='left', anchor='w')
        v = tk.StringVar()
        e = ttk.Entry(k, textvariable=v, show='*' if an else '')
        e.pack(side='left', fill='x', expand=True)
        if an:
            ttk.Button(k, text='Hiện', width=6,
                       command=lambda: e.config(show='' if e.cget('show') else '*')
                       ).pack(side='left', padx=(6, 0))
        if mo_ta:
            ttk.Label(cha, text='      ' + mo_ta, style='Mo.TLabel').pack(anchor='w')
        return v

    # ------------------------------------------------------------ tab tổng quan
    O_SO = [('tong', 'Tổng bài cần làm', NAVY), ('dang', 'Đã đăng', GREEN),
            ('sinh', 'Đã sinh chưa đăng', '#2E5C8A'), ('chan', 'Bị chặn', RED),
            ('loi', 'Lỗi', '#8B0000'), ('con', 'Còn lại', XAM),
            ('chon_sp', 'SKU đang chọn viết', '#6B4F00')]

    COT_BANG_BAI = [('site', 'Site', 60), ('sku', 'SKU', 170), ('ten', 'Tên sản phẩm', 250),
                    ('mau', 'Loại bài', 110), ('du_lieu', 'Dữ liệu', 60),
                    ('anh', 'Ảnh', 45), ('so_tu', 'Số từ', 55),
                    ('kiem_tra', 'Kiểm tra', 80), ('wp', 'WP', 65),
                    ('trang_thai', 'Trạng thái', 90), ('ghi_chu', 'Ghi chú / Lý do chặn', 260)]

    def _tab_cuon(self, tieu_de, padding=14):
        """Bọc nội dung tab trong khung cuộn được.

        Dùng cho tab xếp chồng nhiều ô nhập liệu (Nhập Excel, Cấu hình, Chạy) —
        không có Treeview để tự co giãn, nên cửa sổ thấp hơn nội dung là nút Lưu
        bị đẩy khuất, không cuộn tới được. Đây đúng là lỗi trong ảnh chụp màn hình.
        """
        ngoai = ttk.Frame(self.tab)
        self.tab.add(ngoai, text=tieu_de)
        canvas = tk.Canvas(ngoai, bg=TRANG, highlightthickness=0)
        sb = ttk.Scrollbar(ngoai, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        trong = ttk.Frame(canvas, padding=padding)
        cua_so = canvas.create_window((0, 0), window=trong, anchor='nw')

        def _cap_nhat_vung(event=None):
            canvas.configure(scrollregion=canvas.bbox('all'))
        trong.bind('<Configure>', _cap_nhat_vung)

        def _khop_rong(event):
            canvas.itemconfig(cua_so, width=event.width)
        canvas.bind('<Configure>', _khop_rong)

        def _cuon(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        canvas.bind('<Enter>', lambda e: canvas.bind_all('<MouseWheel>', _cuon))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all('<MouseWheel>'))
        return trong

    def _tab_tong_quan(self):
        f = ttk.Frame(self.tab, padding=14)
        self.tab.add(f, text='  0. Tổng quan  ')

        o = ttk.Frame(f)
        o.pack(fill='x')
        self.o_so = {}
        for ma, nhan, mau in self.O_SO:
            hop = tk.Frame(o, bg=XAM_NHAT, bd=1, relief='solid')
            hop.pack(side='left', fill='x', expand=True, padx=(0, 8))
            lb = tk.Label(hop, text='0', bg=XAM_NHAT, fg=mau, font=(CHU, 24, 'bold'))
            lb.pack(pady=(10, 0))
            tk.Label(hop, text=nhan, bg=XAM_NHAT, fg=XAM,
                     font=(CHU, 9)).pack(pady=(0, 10))
            self.o_so[ma] = lb

        l = ttk.Frame(f)
        l.pack(fill='x', pady=(14, 6))
        ttk.Label(l, text='Site').pack(side='left')
        self.v_loc_site = tk.StringVar(value='tất cả')
        ttk.Combobox(l, textvariable=self.v_loc_site, width=12, state='readonly',
                     values=['tất cả'] + list(C.tat_ca_site())).pack(side='left', padx=(6, 16))
        ttk.Label(l, text='Trạng thái').pack(side='left')
        self.v_loc_tt = tk.StringVar(value='tất cả')
        ttk.Combobox(l, textvariable=self.v_loc_tt, width=14, state='readonly',
                     values=['tất cả', 'Chưa làm', 'Đã sinh', 'Đã đăng',
                             'Bị chặn']).pack(side='left', padx=(6, 16))
        ttk.Label(l, text='Tìm').pack(side='left')
        self.v_tim = tk.StringVar()
        e = ttk.Entry(l, textvariable=self.v_tim, width=24)
        e.pack(side='left', padx=6)
        e.bind('<Return>', lambda ev: self.nap_dashboard())
        ttk.Button(l, text='Lọc', command=self.nap_dashboard).pack(side='left')
        ttk.Button(l, text='Xuất Excel', style='Chinh.TButton',
                   command=self.xuat_excel).pack(side='right')
        ttk.Button(l, text='Tải lại', command=self.nap_dashboard).pack(side='right', padx=6)

        k = ttk.Frame(f)
        k.pack(fill='both', expand=True)
        self.bang_bai = ttk.Treeview(k, columns=[c for c, _, _ in self.COT_BANG_BAI],
                                     show='headings', height=11)
        for c, n, w in self.COT_BANG_BAI:
            self.bang_bai.heading(c, text=n)
            self.bang_bai.column(c, width=w,
                                 anchor='w' if c in ('sku', 'ten', 'ghi_chu', 'mau')
                                 else 'center')
        sb = ttk.Scrollbar(k, orient='vertical', command=self.bang_bai.yview)
        self.bang_bai.configure(yscrollcommand=sb.set)
        self.bang_bai.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        for ten, mau in [('dang', GREEN), ('sinh', '#2E5C8A'), ('chan', RED),
                         ('loi', '#8B0000'), ('chua', XAM)]:
            self.bang_bai.tag_configure(ten, foreground=mau)
        self.bang_bai.bind('<Double-1>', self._mo_bai)
        self.bang_bai.bind('<<TreeviewSelect>>', self._cap_nhat_xem_truoc)
        self.dashboard_row_map = {}

        ttk.Label(f, text='Chọn một dòng để xem trước tiêu đề/meta bên dưới. '
                          'Bấm đúp để mở file HTML.',
                  style='Mo.TLabel').pack(anchor='w', pady=(6, 8))

        # khung xem trước kiểu kết quả tìm kiếm Google: title xanh, link xanh lá, mô tả xám
        xt = tk.Frame(f, bg='#FFFFFF', bd=1, relief='solid')
        xt.pack(fill='x')
        trong = tk.Frame(xt, bg='#FFFFFF', padx=14, pady=10)
        trong.pack(fill='x')
        self.v_xt_nguon = tk.StringVar(value='Chưa chọn bài nào')
        tk.Label(trong, textvariable=self.v_xt_nguon, bg='#FFFFFF', fg='#5F6368',
                 font=(CHU, 9), anchor='w').pack(fill='x')
        self.v_xt_url = tk.StringVar(value='')
        tk.Label(trong, textvariable=self.v_xt_url, bg='#FFFFFF', fg='#006621',
                 font=(CHU, 9), anchor='w').pack(fill='x', pady=(2, 0))
        self.v_xt_title = tk.StringVar(value='')
        tk.Label(trong, textvariable=self.v_xt_title, bg='#FFFFFF', fg='#1A0DAB',
                 font=(CHU, 14), anchor='w', justify='left', wraplength=900
                 ).pack(fill='x', pady=(2, 2))
        self.v_xt_mo_ta = tk.StringVar(value='')
        tk.Label(trong, textvariable=self.v_xt_mo_ta, bg='#FFFFFF', fg='#4D5156',
                 font=(CHU, 10), anchor='w', justify='left', wraplength=900
                 ).pack(fill='x')
        nut = ttk.Frame(trong)
        nut.pack(fill='x', pady=(8, 0))
        self.btn_xt_file = ttk.Button(nut, text='Mở file HTML', state='disabled',
                                      command=self._mo_bai)
        self.btn_xt_file.pack(side='left')
        self.btn_xt_link = ttk.Button(nut, text='Mở link đã đăng', state='disabled',
                                      command=self._mo_link_da_dang)
        self.btn_xt_link.pack(side='left', padx=8)

    def _cap_nhat_xem_truoc(self, event=None):
        sel = self.bang_bai.selection()
        if not sel:
            return
        r = self.dashboard_row_map.get(sel[0])
        if not r:
            return
        self._xt_row = r
        if r['trang_thai'] == 'Đã đăng' and r['link']:
            self.v_xt_nguon.set(f'{r["site"]}  ·  {r["mau"]}  ·  Đã đăng')
            self.v_xt_url.set(r['link'])
        else:
            self.v_xt_nguon.set(f'{r["site"]}  ·  {r["mau"]}  ·  {r["trang_thai"]} '
                                '(chưa đăng, đây là xem trước từ file HTML)')
            self.v_xt_url.set(f'output/{r["site"]}__{r["slug"]}.html' if r['slug'] else '')
        tieu = r['meta_title'] or r['tieu_de'] or r['ten'] or '(chưa có tiêu đề)'
        self.v_xt_title.set(tieu)
        self.v_xt_mo_ta.set(r['meta_description'] or '(chưa có meta description — bài chưa sinh '
                            'hoặc bị chặn trước khi AI trả kết quả)')
        co_file = bool(r['slug']) and (BASE / 'output' / f'{r["site"]}__{r["slug"]}.html').exists()
        self.btn_xt_file.config(state='normal' if co_file else 'disabled')
        self.btn_xt_link.config(state='normal' if r['link'] else 'disabled')

    def _mo_link_da_dang(self):
        r = getattr(self, '_xt_row', None)
        if r and r.get('link'):
            import webbrowser
            webbrowser.open(r['link'])

    def nap_dashboard(self):
        import baocao
        for i in self.bang_bai.get_children():
            self.bang_bai.delete(i)
        self.dashboard_row_map = {}
        try:
            dong, sp = baocao.gom_du_lieu()
        except Exception as e:
            self.log('Không dựng được tổng quan: ' + str(e), 'loi')
            return
        loc_s, loc_t = self.v_loc_site.get(), self.v_loc_tt.get()
        tim = self.v_tim.get().strip().lower()
        dem = {'tong': 0, 'dang': 0, 'sinh': 0, 'chan': 0, 'loi': 0, 'con': 0,
               'chon_sp': sum(1 for r in sp if r['chon'] == 'Có'
                             and (loc_s == 'tất cả' or r['site'] == loc_s))}
        khoa = {'Đã đăng': 'dang', 'Đã sinh': 'sinh', 'Bị chặn': 'chan',
               'Lỗi': 'loi', 'Chưa làm': 'con'}
        tag = {'Đã đăng': 'dang', 'Đã sinh': 'sinh', 'Bị chặn': 'chan',
              'Lỗi': 'loi', 'Chưa làm': 'chua'}
        for i, r in enumerate(dong):
            # KPI chỉ tính bài của sản phẩm đang bật "chọn viết", và đúng site
            # đang lọc — trước đây đếm cả site khác + cả sản phẩm đã bỏ chọn,
            # số hiện ra không khớp cái mình thật sự sắp chạy.
            if (loc_s == 'tất cả' or r['site'] == loc_s) and r.get('chon') == 'Có':
                dem['tong'] += 1
                dem[khoa.get(r['trang_thai'], 'con')] += 1
            if loc_s != 'tất cả' and r['site'] != loc_s:
                continue
            if loc_t != 'tất cả' and r['trang_thai'] != loc_t:
                continue
            if tim and tim not in (r['sku'] + ' ' + r['ten']).lower():
                continue
            iid = f'{r["site"]}::{r["sku"]}::{i}'
            self.dashboard_row_map[iid] = r
            self.bang_bai.insert('', 'end', iid=iid, tags=(tag.get(r['trang_thai'], ''),),
                                 values=(r['site'], r['sku'], r['ten'], r['mau'],
                                         r['du_lieu'], r['anh'], r['so_tu'] or '',
                                         r['kiem_tra'], r['wp'], r['trang_thai'],
                                         r['ghi_chu']))
        for ma, lb in self.o_so.items():
            lb.config(text=str(dem[ma]))
        self.tt.config(text=f'Tổng quan: {dem["tong"]} bài cần làm, '
                            f'{dem["dang"]} đã đăng, {dem["con"]} còn lại')

    def _mo_bai(self, ev=None):
        sel = self.bang_bai.selection()
        if not sel:
            return
        r = self.dashboard_row_map.get(sel[0])
        if not r or not r.get('slug'):
            messagebox.showinfo('Chưa có file', 'Bài này chưa được sinh ra file HTML.')
            return
        f = BASE / 'output' / f'{r["site"]}__{r["slug"]}.html'
        if f.exists():
            self.mo(f)
        else:
            messagebox.showinfo('Chưa có file', 'Bài này chưa được sinh ra file HTML.')

    def xuat_excel(self):
        import baocao
        try:
            f, nb, ns = baocao.xuat()
        except Exception as e:
            messagebox.showerror('Không xuất được', str(e)[:500])
            return
        self.log(f'Đã xuất {f.name}: {nb} dòng bài viết, {ns} dòng sản phẩm', 'ok')
        self.mo(f)

    # ------------------------------------------------------------ tab nhập Excel
    def _tab_nhap(self):
        f = self._tab_cuon('  1. Nhập Excel  ', padding=18)
        ttk.Label(f, text='Nhập file Excel của sếp', style='Dam.TLabel').pack(anchor='w')
        ttk.Label(f, text='Đọc mọi sheet, gộp mã trùng, bỏ mã lỗi, tách sẵn điện áp, dòng, '
                          'rơ le, số ngăn. Bảo đảm slug không trùng.',
                  style='Mo.TLabel').pack(anchor='w', pady=(2, 10))
        k = ttk.Frame(f)
        k.pack(fill='x')
        ttk.Label(k, text='File Excel', width=14).pack(side='left')
        self.v_excel = tk.StringVar()
        e = ttk.Entry(k, textvariable=self.v_excel)
        e.pack(side='left', fill='x', expand=True)
        e.bind('<Return>', lambda ev: self._xem_excel())
        ttk.Button(k, text='Chọn file...', command=self._chon_excel).pack(side='left', padx=6)

        dm = ttk.Frame(f)
        dm.pack(fill='x', pady=(9, 0))
        ttk.Label(dm, text='Ngành hàng', width=14).pack(side='left')
        self.v_danh_muc = tk.StringVar()
        ttk.Entry(dm, textvariable=self.v_danh_muc, width=28).pack(side='left')
        ttk.Label(dm, text='   Ngăn kho theo ngành. Nạp file cáp điện đè lên tủ trung thế '
                           'mà không ngăn thì số liệu hai ngành trộn vào nhau, bộ chặn bịa '
                           'số yếu đi.', style='Mo.TLabel').pack(side='left')

        n = ttk.Frame(f)
        n.pack(fill='x', pady=(16, 0))
        ttk.Button(n, text='Xem thử, chưa ghi', command=self._xem_excel).pack(side='left')
        ttk.Button(n, text='NHẬP VÀO KHO DỮ LIỆU', style='Chinh.TButton',
                   command=self._nhap_excel).pack(side='left', padx=8)
        ttk.Button(n, text='Xuất products.csv', command=self._xuat_csv).pack(side='left')

        ttk.Separator(f).pack(fill='x', pady=16)
        ttk.Label(f, text='Kho kiến thức theo dòng sản phẩm', style='Dam.TLabel').pack(anchor='w')
        ttk.Label(f, text='Mục nào chưa đối chiếu catalogue thì phần mềm KHÔNG đưa cho AI dùng. '
                          'Mở file trong thư mục kienthuc, sửa da_kiem_chung thành true sau khi '
                          'đã kiểm tra. Cột "Chưa kiểm chứng" về 0 thì bài mới dày.',
                  style='Mo.TLabel').pack(anchor='w', pady=(2, 8))
        kk = ttk.Frame(f)
        kk.pack(fill='both', expand=True)
        self.bang_kt = ttk.Treeview(kk, columns=('f', 'h', 's', 't', 'c'),
                                    show='headings', height=7)
        for c, nn, w in [('f', 'File', 240), ('h', 'Hãng', 110), ('s', 'Dòng', 170),
                         ('t', 'Tổng mục', 90), ('c', 'Chưa kiểm chứng', 140)]:
            self.bang_kt.heading(c, text=nn)
            self.bang_kt.column(c, width=w, anchor='w' if c in 'fhs' else 'center')
        self.bang_kt.pack(side='left', fill='both', expand=True)
        self.bang_kt.tag_configure('thieu', foreground=AMBER)

        b = ttk.Frame(f)
        b.pack(fill='x', pady=(8, 0))
        ttk.Button(b, text='Tải lại', command=self.nap_kien_thuc_bang).pack(side='left')
        ttk.Button(b, text='Mở thư mục kienthuc',
                   command=lambda: self.mo(BASE / 'kienthuc')).pack(side='left', padx=6)
        ttk.Button(b, text='Mở thư mục ảnh',
                   command=lambda: self.mo(BASE / 'anh')).pack(side='left')

    def _chon_excel(self):
        p = filedialog.askopenfilename(title='Chọn file Excel',
                                       filetypes=[('Excel', '*.xlsx *.xlsm'), ('Tất cả', '*.*')])
        if p:
            self.v_excel.set(p)
            if not self.v_danh_muc.get().strip():
                self.v_danh_muc.set(D.goi_y_danh_muc(p))

    def _doc_excel(self):
        p = self.v_excel.get().strip().strip('"')
        if not p:
            messagebox.showwarning('Chưa chọn file', 'Bấm "Chọn file..." trước.')
            return None, None
        if not Path(p).exists():
            messagebox.showwarning('Không thấy file', f'Không tìm thấy:\n{p}')
            return None, None
        self.tt.config(text='Đang đọc ' + Path(p).name + ' ...')
        self.update_idletasks()
        try:
            return D.nhap_excel(p, danh_muc=self.v_danh_muc.get().strip() or None)
        except Exception as e:
            self.log('Không đọc được file Excel: ' + str(e), 'loi')
            messagebox.showerror('Không đọc được file Excel', str(e)[:700])
            return None, None
        finally:
            self.tt.config(text='Sẵn sàng')

    def _xem_excel(self):
        ds, bc = self._doc_excel()
        if ds is None:
            return
        self.log('== XEM THỬ, CHƯA GHI ==', 'nhan')
        for d in D.tom_tat_bao_cao(bc).splitlines():
            self.log(d, 'canh' if ('trùng' in d or 'lỗi' in d) else None)

    def _nhap_excel(self):
        ds, bc = self._doc_excel()
        if ds is None:
            return
        for d in D.tom_tat_bao_cao(bc).splitlines():
            self.log(d)
        dm = bc.get('danh_muc', 'chung')
        self.v_danh_muc.set(dm)
        self.log(f'Đã ghi {D.luu_san_pham(ds, dm)} sản phẩm vào du-lieu.db '
                 f'(ngành hàng: {dm})', 'ok')
        ba = D.bao_cao_anh(ds)
        self.log(f'Ảnh: {ba["tong_anh_trong_thu_muc"]} file trong thư mục anh, '
                 f'{ba["san_pham_co_anh"]} sản phẩm có ảnh, '
                 f'{ba["san_pham_thieu_anh"]} sản phẩm CHƯA có ảnh',
                 'canh' if ba['san_pham_thieu_anh'] else 'ok')
        self.nap_san_pham()
        self.nap_kien_thuc_bang()
        self.nap_dashboard()
        self._nap_sp_thu()

    def _xuat_csv(self):
        ds = D.doc_san_pham_db()
        if not ds:
            messagebox.showinfo('Trống', 'Chưa có sản phẩm nào. Nhập Excel trước.')
            return
        with open(BASE / 'products.csv', 'w', newline='', encoding='utf-8-sig') as fh:
            w = csv.DictWriter(fh, fieldnames=list(ds[0].keys()))
            w.writeheader()
            w.writerows(ds)
        self.log(f'Đã xuất products.csv ({len(ds)} dòng) để mở bằng Excel', 'ok')
        self.mo(BASE / 'products.csv')

    def nap_kien_thuc_bang(self):
        D.xoa_cache_kien_thuc()
        for i in self.bang_kt.get_children():
            self.bang_kt.delete(i)
        for r in D.trang_thai_kien_thuc():
            self.bang_kt.insert('', 'end', values=(r['file'], r['hang'], r['series'],
                                                   r['tong_muc'], r['chua_kiem_chung']),
                                tags=('thieu',) if r['chua_kiem_chung'] else ())

    # ------------------------------------------------------------ tab 1
    def _tab_cau_hinh(self):
        f = self._tab_cuon('  2. Cấu hình  ', padding=18)
        ttk.Label(f, text='Chìa khoá AI', style='Dam.TLabel').pack(anchor='w')
        self.v_key = self._o(f, 'Google API key',
                             'Lấy miễn phí ở aistudio.google.com, mục Get API key', an=True)
        k = ttk.Frame(f)
        k.pack(fill='x', pady=(9, 0))
        ttk.Label(k, text='Model', width=26).pack(side='left')
        self.v_model = tk.StringVar()
        self.cb_model = ttk.Combobox(k, textvariable=self.v_model, width=40)
        self.cb_model.pack(side='left')
        self.cb_model.bind('<<ComboboxSelected>>', lambda e: self._cap_nhat_dung_luong())
        ttk.Button(k, text='Dò model chạy được',
                   command=lambda: self.chay_nen(self.viec_do_model)).pack(side='left', padx=6)
        self.v_dung_luong = tk.StringVar(value='')
        ttk.Label(f, textvariable=self.v_dung_luong, style='Mo.TLabel').pack(anchor='w')
        ttk.Label(f, text='      Google đổi tên model liên tục. Bấm nút dò để biết key của bạn '
                          'dùng được cái nào và dung lượng thật (vào/ra bao nhiêu token, có '
                          'suy nghĩ ngầm hay không). Tránh model có chữ "gemma", không ép '
                          'được JSON.', style='Mo.TLabel').pack(anchor='w')

        ttk.Separator(f).pack(fill='x', pady=16)
        ttk.Label(f, text='Website WordPress', style='Dam.TLabel').pack(anchor='w')
        s = ttk.Frame(f)
        s.pack(fill='x', pady=(9, 0))
        ttk.Label(s, text='Site đang cấu hình', width=26).pack(side='left')
        self.v_site = tk.StringVar(value=list(C.tat_ca_site())[0])
        self.cb_site = ttk.Combobox(s, textvariable=self.v_site, width=20, state='readonly',
                                    values=list(C.tat_ca_site()))
        self.cb_site.pack(side='left')
        self.cb_site.bind('<<ComboboxSelected>>', lambda e: self.doc_cau_hinh(giu_site=True))
        ttk.Button(s, text='+ Site mới', command=self._hop_thoai_them_site
                  ).pack(side='left', padx=(8, 0))
        self.btn_xoa_site = ttk.Button(s, text='Xoá site này', command=self._xoa_site_hien_tai)
        self.btn_xoa_site.pack(side='left', padx=(6, 0))
        self.lb_site = ttk.Label(s, text='', style='Mo.TLabel')
        self.lb_site.pack(side='left', padx=10)
        ttk.Label(f, text='      Mỗi website WordPress của mày là một site riêng: mỗi cái có '
                          'tên, hotline, URL, tài khoản đăng và ngành hàng riêng. Bấm "+ Site '
                          'mới" để thêm, không cần sửa file cauhinh.py.',
                  style='Mo.TLabel').pack(anchor='w')

        self.v_url = self._o(f, 'Địa chỉ web', 'Ví dụ https://bienapthibidi.vn, không có / cuối')
        self.v_user = self._o(f, 'Tên đăng nhập')
        self.v_pw = self._o(f, 'Application Password',
                            'KHÔNG phải mật khẩu đăng nhập. Users > Profile > '
                            'Application Passwords', an=True)

        n = ttk.Frame(f)
        n.pack(fill='x', pady=(20, 0))
        ttk.Button(n, text='Lưu cấu hình', style='Chinh.TButton',
                   command=self.luu_cau_hinh).pack(side='left')
        ttk.Button(n, text='Kiểm tra kết nối WordPress',
                   command=lambda: self.chay_nen(self.viec_kiem_tra_wp)).pack(side='left', padx=8)
        ttk.Button(n, text='Mở thư mục chương trình',
                   command=lambda: self.mo(BASE)).pack(side='left')
        ttk.Label(f, text='      Kiểm tra kết nối thử 6 khâu: mở trang, REST API, đăng nhập, '
                          'đăng chữ thuần, đăng HTML, đăng bài đầy đủ. Chết ở khâu nào nó chỉ ra '
                          'khâu đó. Bài test nằm ở Bản nháp, nhớ xoá.',
                  style='Mo.TLabel').pack(anchor='w', pady=(8, 0))

    # ------------------------------------------------------------ tab 2
    def _tab_san_pham(self):
        f = ttk.Frame(self.tab, padding=14)
        self.tab.add(f, text='  3. Sản phẩm  ')
        t = ttk.Frame(f)
        t.pack(fill='x')
        self.lb_sp = ttk.Label(t, text='', style='Dam.TLabel')
        self.lb_sp.pack(side='left')
        ttk.Button(t, text='Mở products.csv bằng Excel',
                   command=lambda: self.mo(BASE / 'products.csv')).pack(side='right')
        ttk.Button(t, text='Tải lại', command=self.nap_san_pham).pack(side='right', padx=6)
        ttk.Button(t, text='Bỏ chọn hiện trên bảng',
                   command=lambda: self._chon_hang_loat(False)).pack(side='right', padx=6)
        ttk.Button(t, text='Chọn hiện trên bảng',
                   command=lambda: self._chon_hang_loat(True)).pack(side='right')
        ttk.Label(f, text='Bấm đúp vào cột Viết để bật/tắt riêng từng dòng. Chỉ dòng đang bật '
                          'mới được đưa vào hàng đợi sinh bài ở tab 4; dòng tắt vẫn nằm trong '
                          'bảng giá và liên kết nội bộ của các bài khác.',
                  style='Mo.TLabel').pack(anchor='w', pady=(2, 8))

        k = ttk.Frame(f)
        k.pack(fill='both', expand=True)
        self.bang = ttk.Treeview(k, columns=('stt', 'viet', 'sku', 'ten', 'day_du'),
                                 show='headings', height=14)
        for c, n, w in [('stt', 'STT', 42), ('viet', 'Viết', 46), ('sku', 'Mã', 160),
                        ('ten', 'Tên sản phẩm', 400), ('day_du', 'Dữ liệu đã điền', 130)]:
            self.bang.heading(c, text=n)
            self.bang.column(c, width=w, anchor='w' if c in ('sku', 'ten') else 'center')
        sb = ttk.Scrollbar(k, orient='vertical', command=self.bang.yview)
        self.bang.configure(yscrollcommand=sb.set)
        self.bang.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        self.bang.bind('<Double-1>', self._doi_chon_san_pham)
        self.bang.tag_configure('thieu', foreground=RED)
        self.bang.tag_configure('du', foreground=GREEN)

    # ------------------------------------------------------------ tab 3
    def _tab_thu_mot_bai(self):
        f = self._tab_cuon('  4. Thử 1 bài  ', padding=18)
        ttk.Label(f, text='Xem trước 1 bài trước khi chạy hàng loạt', style='Dam.TLabel'
                 ).pack(anchor='w')
        ttk.Label(f, text='Xem prompt thật gửi cho AI, dữ liệu nào giữ nguyên từ Excel, dữ liệu '
                          'nào AI viết, và bài ra sao — kết quả in ở khung Nhật ký bên dưới.',
                  style='Mo.TLabel').pack(anchor='w', pady=(2, 12))

        h = ttk.Frame(f)
        h.pack(fill='x')
        c0 = ttk.Frame(h)
        c0.pack(side='left', padx=(0, 24))
        ttk.Label(c0, text='Site', style='Dam.TLabel').pack(anchor='w')
        self.v_thu_site = tk.StringVar(value=list(C.tat_ca_site())[0])
        cb_site = ttk.Combobox(c0, textvariable=self.v_thu_site, width=14, state='readonly',
                               values=list(C.tat_ca_site()))
        cb_site.pack(anchor='w', pady=(6, 0))
        cb_site.bind('<<ComboboxSelected>>', lambda e: self._nap_sp_thu())

        c1 = ttk.Frame(h)
        c1.pack(side='left', padx=(0, 24))
        ttk.Label(c1, text='Sản phẩm', style='Dam.TLabel').pack(anchor='w')
        self.v_thu_sp = tk.StringVar()
        self.cb_thu_sp = ttk.Combobox(c1, textvariable=self.v_thu_sp, width=52, state='readonly')
        self.cb_thu_sp.pack(anchor='w', pady=(6, 0))

        c2 = ttk.Frame(h)
        c2.pack(side='left')
        ttk.Label(c2, text='Outline', style='Dam.TLabel').pack(anchor='w')
        self.v_thu_mau = tk.StringVar()
        self.cb_thu_mau = ttk.Combobox(c2, textvariable=self.v_thu_mau, width=20,
                                       state='readonly')
        self.cb_thu_mau.pack(anchor='w', pady=(6, 0))

        n = ttk.Frame(f)
        n.pack(fill='x', pady=(18, 0))
        ttk.Button(n, text='Xem prompt (miễn phí, không gọi AI)',
                   command=self._xem_prompt_thu).pack(side='left')
        ttk.Button(n, text='Chạy thật 1 bài (gọi AI, tốn phí)', style='Chinh.TButton',
                   command=self._chay_thu_mot_bai).pack(side='left', padx=8)
        self.btn_mo_ket_qua = ttk.Button(n, text='Mở file kết quả', state='disabled',
                                         command=lambda: self.mo(self._file_thu_gan_nhat)
                                         if getattr(self, '_file_thu_gan_nhat', None) else None)
        self.btn_mo_ket_qua.pack(side='left')
        ttk.Label(f, text='Kết quả in ở khung Nhật ký phía dưới màn hình — kéo thanh chia để '
                          'xem rộng hơn nếu cần.', style='Mo.TLabel').pack(anchor='w', pady=(8, 0))

    def _nap_sp_thu(self):
        try:
            A = self._ap_cau_hinh()
            ds = A.doc_san_pham(None, self.v_thu_site.get())
        except Exception as e:
            self.log('Không nạp được sản phẩm: ' + str(e), 'loi')
            ds = []
        self._sp_thu_map = {f'{r.get("ma_goc", r["sku"])}  —  {r["ten_san_pham"][:60]}': r
                            for r in ds}
        self.cb_thu_sp['values'] = list(self._sp_thu_map)
        if self._sp_thu_map and self.v_thu_sp.get() not in self._sp_thu_map:
            self.v_thu_sp.set(next(iter(self._sp_thu_map)))
        import prompts as P
        self.cb_thu_mau['values'] = list(P.MAU)
        if self.v_thu_mau.get() not in P.MAU and P.MAU:
            self.v_thu_mau.set(list(P.MAU)[0])

    def _san_pham_dang_chon_thu(self):
        if not getattr(self, '_sp_thu_map', None):
            self._nap_sp_thu()
        r = self._sp_thu_map.get(self.v_thu_sp.get())
        if not r:
            messagebox.showwarning('Chưa có sản phẩm', 'Vào tab 0 nhập Excel trước, hoặc chọn '
                                   'lại site/sản phẩm.')
        return r

    def _xem_prompt_thu(self):
        row = self._san_pham_dang_chon_thu()
        if not row:
            return
        A = self._ap_cau_hinh()
        import cauhinh as C2
        site = C2.lay_site(self.v_thu_site.get())
        mau = self.v_thu_mau.get()
        self.log('=' * 70, 'nhan')
        self.log(f'PROMPT THẬT — sản phẩm {row.get("ma_goc", row["sku"])}, outline "{mau}"'
                 f' (không tốn phí, chưa gọi AI)', 'nhan')
        self.log('--- SYSTEM (vai trò + luật cấm bịa) ---')
        self.log(A.dung_system(site))
        self.log('--- NGƯỜI DÙNG (dữ liệu sản phẩm + yêu cầu bài) ---')
        self.log(A.dung_prompt(row, mau))
        self.log('=' * 70, 'nhan')

    def _chay_thu_mot_bai(self):
        row = self._san_pham_dang_chon_thu()
        if not row:
            return
        self._ap_cau_hinh()
        if not os.environ.get('GOOGLE_API_KEY'):
            messagebox.showwarning('Thiếu API key', 'Điền Google API key ở tab 2 rồi bấm Lưu.')
            return
        self.chay_nen(lambda: self.viec_chay_thu_mot_bai(
            self.v_thu_site.get(), dict(row), self.v_thu_mau.get()))

    def viec_chay_thu_mot_bai(self, ma_site, row, mau_key):
        A = self._ap_cau_hinh()
        import cauhinh as C2, prompts as P
        tat_ca = A.doc_san_pham(None, ma_site)
        print('=' * 70)
        print(f'CHẠY THẬT 1 BÀI — {row.get("ma_goc", row["sku"])}, outline "{mau_key}", '
             f'site {ma_site}. Đang gọi AI...')
        kq = A.sinh_mot_bai(row, ma_site, mau_key, tat_ca, 'sinh', A.tao_client())

        print('\n--- 1. DỮ LIỆU GIỮ NGUYÊN TỪ EXCEL (AI không được đổi) ---')
        for k, nhan in C2.COT_BANG:
            v = (row.get(k) or '').strip()
            if v:
                print(f'    {nhan:24} : {v}')

        noi_dung_file = kq['file'].read_text(encoding='utf-8') if kq['file'].exists() else ''
        print(f'\n--- 2. AI VIẾT (outline "{P.MAU[mau_key]["ten"]}") ---')
        print(f'    Trạng thái kiểm tra : {kq["kiem_tra"]}')
        if kq['ghi_chu']:
            print(f'    Ghi chú             : {kq["ghi_chu"]}')
        print(f'    Số từ AI viết       : {kq["so_tu"]}')
        print(f'    Số ảnh gắn được     : {kq["so_anh"]}')

        print('\n--- 3. CẤU TRÚC OUTPUT (khung HTML ghép ra, xem đủ trong file) ---')
        for dong in noi_dung_file.splitlines()[:3]:
            print('    ' + dong)
        print(f'    ... ({len(noi_dung_file):,} ký tự, xem đủ trong file kết quả)')
        print(f'\nFile kết quả: {kq["file"]}')
        print('=' * 70)
        self._file_thu_gan_nhat = kq['file']
        self.ui(lambda: self.btn_mo_ket_qua.config(state='normal'))
        self.ui(self.nap_dashboard)

    def _tab_chay(self):
        f = self._tab_cuon('  5. Chạy  ', padding=18)
        h = ttk.Frame(f)
        h.pack(fill='x')

        c0 = ttk.Frame(h)
        c0.pack(side='left', padx=(0, 34))
        ttk.Label(c0, text='Site', style='Dam.TLabel').pack(anchor='w')
        self.v_site_chay = tk.StringVar(value=list(C.tat_ca_site())[0])
        ttk.Combobox(c0, textvariable=self.v_site_chay, width=14, state='readonly',
                     values=list(C.tat_ca_site())).pack(anchor='w', pady=(6, 0))

        c1 = ttk.Frame(h)
        c1.pack(side='left', padx=(0, 34))
        ttk.Label(c1, text='Loại bài', style='Dam.TLabel').pack(anchor='w')
        self.v_mau = tk.StringVar()
        self.cb_mau = ttk.Combobox(c1, textvariable=self.v_mau, width=22, state='readonly')
        self.cb_mau.pack(anchor='w', pady=(6, 0))

        c2 = ttk.Frame(h)
        c2.pack(side='left', padx=(0, 34))
        ttk.Label(c2, text='Số bài', style='Dam.TLabel').pack(anchor='w')
        self.v_so = tk.StringVar(value='3')
        ttk.Spinbox(c2, from_=1, to=999, textvariable=self.v_so, width=8).pack(anchor='w',
                                                                              pady=(6, 0))
        ttk.Label(c2, text='Bỏ qua', style='Mo.TLabel').pack(anchor='w', pady=(8, 0))
        self.v_bo_qua = tk.StringVar(value='0')
        ttk.Spinbox(c2, from_=0, to=9999, textvariable=self.v_bo_qua, width=8).pack(anchor='w')

        c3 = ttk.Frame(h)
        c3.pack(side='left')
        ttk.Label(c3, text='Chế độ', style='Dam.TLabel').pack(anchor='w')
        self.v_che_do = tk.StringVar(value='sinh')
        for gt, nhan in CHE_DO:
            ttk.Radiobutton(c3, text=nhan, value=gt,
                            variable=self.v_che_do).pack(anchor='w', pady=1)

        d = ttk.Frame(f)
        d.pack(fill='x', pady=(18, 0))
        ttk.Label(d, text='Nghỉ giữa 2 bài (giây)').pack(side='left')
        self.v_nghi = tk.StringVar(value='30')
        ttk.Spinbox(d, from_=0, to=300, textvariable=self.v_nghi, width=8).pack(side='left',
                                                                               padx=8)
        ttk.Label(d, text='Bản miễn phí của Google nên để 30 trở lên cho khỏi bị chặn tốc độ.',
                  style='Mo.TLabel').pack(side='left')
        self.v_tiep = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text='Bỏ qua sản phẩm đã sinh bài rồi (chạy tiếp sau khi tắt máy)',
                        variable=self.v_tiep).pack(anchor='w', pady=(10, 0))

        n = ttk.Frame(f)
        n.pack(fill='x', pady=(22, 0))
        self.nut_chay = ttk.Button(n, text='BẮT ĐẦU', style='Chinh.TButton',
                                   command=self.bat_dau_sinh)
        self.nut_chay.pack(side='left')
        self.nut_dung = ttk.Button(n, text='Dừng', command=self.yeu_cau_dung, state='disabled')
        self.nut_dung.pack(side='left', padx=8)
        ttk.Button(n, text='Mở thư mục kết quả',
                   command=lambda: self.mo(BASE / 'output')).pack(side='left')

        self.tien_do = ttk.Progressbar(f, mode='determinate')
        self.tien_do.pack(fill='x', pady=(18, 4))
        self.lb_tien_do = ttk.Label(f, text='Chưa chạy', style='Mo.TLabel')
        self.lb_tien_do.pack(anchor='w')

    # ============================================================ UI VER 3 — 5 tab chính
    # Ver 2.6 — bản đồ tab -> nhóm. Tab nào không có trong bảng này sẽ rơi
    # về nhóm 'he_thong' (an toàn: tab mới thêm sau vẫn hiện ra, không mất).
    _NHOM_TAB = {
        '2. Nhập dữ liệu': 'du_lieu',
        '3. Sản phẩm': 'du_lieu',
        '4. Sinh & Đăng': 'san_xuat',
        '5. Theo dõi': 'san_xuat',
        '8. Enhance': 'san_xuat',
        '9. Ảnh sản phẩm': 'du_lieu',
        '10. Đọc thông số (AI)': 'du_lieu',
        '7. Article Jobs': 'san_xuat',
        '11. SEO Post': 'san_xuat',          # Ver 5.5 — module bài chủ đề, không neo SKU
        '1. Cấu hình': 'he_thong',
        '6. Outline Studio': 'he_thong',
    }

    def _v3_tab_cuon(self, tieu_de, padding=16):
        """Giống _tab_cuon nhưng thêm vào notebook con theo nhóm (Ver 2.6)
        và dùng style/màu riêng Ver 3."""
        nhom = self._NHOM_TAB.get(tieu_de.strip(), 'he_thong')
        nb = getattr(self, '_v3_nhom_nb', {}).get(nhom) or self.tab_ver3
        # bỏ tiền tố số ở nhãn con cho gọn (đã có nhóm cha phân biệt)
        nhan = re.sub(r'^\s*\d+\.\s*', '', tieu_de).strip()
        ngoai = ttk.Frame(nb, style='V3.TFrame')
        nb.add(ngoai, text=f'  {nhan}  ')
        canvas = tk.Canvas(ngoai, bg=V3_BG, highlightthickness=0)
        sb = ttk.Scrollbar(ngoai, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        trong = ttk.Frame(canvas, padding=padding, style='V3.TFrame')
        cua_so = canvas.create_window((0, 0), window=trong, anchor='nw')

        def _cap_nhat_vung(event=None):
            canvas.configure(scrollregion=canvas.bbox('all'))
        trong.bind('<Configure>', _cap_nhat_vung)

        def _khop_rong(event):
            canvas.itemconfig(cua_so, width=event.width)
        canvas.bind('<Configure>', _khop_rong)

        def _cuon(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        canvas.bind('<Enter>', lambda e: canvas.bind_all('<MouseWheel>', _cuon))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all('<MouseWheel>'))
        return trong

    @staticmethod
    def _v3_the(cha, tieu_de):
        """1 khối 'card' viền/nền trắng theo palette Ver 3, dùng lặp lại ở
        mọi tab cho đồng nhất bố cục."""
        khung = ttk.LabelFrame(cha, text=tieu_de, style='V3.TLabelframe', padding=14)
        khung.pack(fill='x', pady=(0, 14))
        return khung

    # ---------------------------------------------------------- Tab 1: Nhập dữ liệu
    def _v3_tab_1_nhap_du_lieu(self):
        f = self._v3_tab_cuon('2. Nhập dữ liệu')
        ttk.Label(f, text='Nhập dữ liệu sản phẩm', style='V3Tieu.TLabel').pack(anchor='w', pady=(0, 4))
        ttk.Label(f, text='Nhập file MASTER (gộp 4 profile) hoặc 1 file profile con. Nhập lại '
                          'cùng dữ liệu không tạo dataset mới; dữ liệu đổi thật sẽ hỏi xác nhận.',
                  style='V3Mo.TLabel', wraplength=900).pack(anchor='w', pady=(0, 14))

        kA = self._v3_the(f, 'Chọn file')
        hang = ttk.Frame(kA, style='V3Card.TFrame')
        hang.pack(fill='x')
        self.v3_duong_dan_file = tk.StringVar(value='(chưa chọn file)')
        ttk.Entry(hang, textvariable=self.v3_duong_dan_file, state='readonly', width=68
                 ).pack(side='left', fill='x', expand=True)
        ttk.Button(hang, text='Chọn file MASTER...', style='V3.TButton',
                  command=self._v3_chon_file).pack(side='left', padx=(10, 6))
        self.nut_v3_nhap = ttk.Button(hang, text='Nhập dữ liệu', style='V3Chinh.TButton',
                                      command=self._v3_nhap_du_lieu, state='disabled')
        self.nut_v3_nhap.pack(side='left')

        # ---------------------------------------------------- Ver 4.7 — Chuẩn hoá MASTER
        kD = self._v3_the(f, 'Chuẩn hoá MASTER (tuỳ chọn — làm giàu dữ liệu trước khi nhập)')
        ttk.Label(kD, text='Chọn 1 file MASTER (gộp 4 sheet) — trích thêm thông số kỹ thuật từ tên hàng '
                           'bằng RULE CỐ ĐỊNH (KHÔNG suy đoán, KHÔNG gọi AI), đánh dấu CONFIRMED/CAN_KIEM '
                           'để tự soát trong Excel. KHÔNG tự động áp dụng — mở file ra kiểm tra/sửa tay '
                           'rồi tự chọn "Chọn file MASTER..." ở trên để nhập bản đã soát.',
                  style='V3CardMo.TLabel', wraplength=900).pack(anchor='w', pady=(0, 8))
        hangD = ttk.Frame(kD, style='V3Card.TFrame')
        hangD.pack(fill='x')
        ttk.Button(hangD, text='Chuẩn hoá MASTER...', style='V3.TButton',
                  command=self._v3_chuan_hoa_master).pack(side='left')
        self.lb_v3_chuan_hoa = ttk.Label(kD, text='', style='V3CardMo.TLabel', wraplength=900)
        self.lb_v3_chuan_hoa.pack(anchor='w', pady=(8, 0))

        kB = self._v3_the(f, 'Báo cáo import')
        self.bang_v3_baocao = ttk.Treeview(
            kB, columns=('profile', 'dataset', 'tong', 'loi'), show='headings', height=4)
        for c, n, w in [('profile', 'Profile', 190), ('dataset', 'Dataset ID', 170),
                        ('tong', 'Tổng record', 110), ('loi', 'Số dòng lỗi', 110)]:
            self.bang_v3_baocao.heading(c, text=n)
            self.bang_v3_baocao.column(c, width=w, anchor='w')
        self.bang_v3_baocao.pack(fill='x')

        kC = self._v3_the(f, 'Danh sách dataset đã nhập')
        hangC = ttk.Frame(kC, style='V3Card.TFrame')
        hangC.pack(fill='x', pady=(0, 8))
        ttk.Button(hangC, text='Tải lại danh sách dataset', style='V3.TButton',
                  command=self._v3_nap_danh_sach_dataset).pack(side='left')
        self.bang_v3_dataset = ttk.Treeview(
            kC, columns=('dataset', 'profile', 'so_dong', 'cap_nhat'), show='headings', height=6)
        for c, n, w in [('dataset', 'Dataset ID', 180), ('profile', 'Profile', 180),
                        ('so_dong', 'Số record', 100), ('cap_nhat', 'Cập nhật lúc', 190)]:
            self.bang_v3_dataset.heading(c, text=n)
            self.bang_v3_dataset.column(c, width=w, anchor='w')
        self.bang_v3_dataset.pack(fill='both', expand=True)

    def _v3_chon_file(self):
        p = filedialog.askopenfilename(filetypes=[('Excel', '*.xlsx')])
        if not p:
            return
        self.v3_duong_dan_file.set(p)
        self.nut_v3_nhap.config(state='normal')

    def _v3_chuan_hoa_master(self):
        """Ver 4.8 — SỬA theo góp ý Thịnh: trước đây bắt chọn THƯ MỤC
        (du_lieu_goc chứa 4 file rời), gây khó hiểu vì Thịnh thực tế luôn
        làm việc với 1 FILE MASTER gộp sẵn 4 sheet. Giờ hỏi chọn FILE —
        chuan_hoa_master._nap_du_lieu_nguon() đã tự nhận diện được cả 2
        kiểu (file gộp HOẶC thư mục), không cần sửa gì ở lõi logic, không
        viết lại — vẫn gọi ĐÚNG 1 nguồn code chuan_hoa_master.chuan_hoa()."""
        import chuan_hoa_master as CHM
        nguon = filedialog.askopenfilename(
            title='Chọn file MASTER (gộp 4 sheet, VD MASTER_4_PROFILE_SAN_PHAM.xlsx)',
            filetypes=[('Excel', '*.xlsx')])
        if not nguon:
            return
        duong_dan_ra = filedialog.asksaveasfilename(
            title='Lưu file MASTER đã chuẩn hoá', defaultextension='.xlsx',
            filetypes=[('Excel', '*.xlsx')], initialfile='MASTER_ENRICHED.xlsx')
        if not duong_dan_ra:
            return
        self.lb_v3_chuan_hoa.config(text='Đang chuẩn hoá...')
        self.update()
        try:
            CHM.chuan_hoa(nguon, duong_dan_ra)
        except Exception as e:
            self.lb_v3_chuan_hoa.config(text=f'LỖI: {type(e).__name__}: {e}')
            messagebox.showerror('Chuẩn hoá thất bại', str(e))
            return
        self.lb_v3_chuan_hoa.config(
            text=f'✓ Đã tạo: {duong_dan_ra}\n'
                f'Mở Excel để soát cột "Trạng Thái Kiểm Duyệt" (CAN_KIEM cần xem lại), '
                f'"Nghi Ngờ Phân Loại Sai" và "Trùng Mã/Tên" trước khi nhập.')
        messagebox.showinfo('Đã chuẩn hoá xong',
                           f'Đã tạo file:\n{duong_dan_ra}\n\n'
                           f'Mở Excel kiểm tra/sửa tay trước, sau đó bấm "Chọn file MASTER..." '
                           f'phía trên để nhập file này.')

    def _v3_nhap_du_lieu(self):
        p = self.v3_duong_dan_file.get()
        if not p or p == '(chưa chọn file)':
            return
        self.nut_v3_nhap.config(state='disabled')
        self.chay_nen_phase2(lambda: self._v3_viec_nhap(p))

    def _v3_viec_nhap(self, duong_dan):
        self._phase2_lam_import(duong_dan)   # tái sử dụng nguyên logic import Round 2/Gate 2
        self.ui(lambda: self.nut_v3_nhap.config(state='normal'))

    def _v3_cap_nhat_bao_cao(self):
        self.bang_v3_baocao.delete(*self.bang_v3_baocao.get_children())
        rpt = getattr(self, '_v3_bao_cao_gan_nhat', None)
        if not rpt or rpt.get('loai_nguon') != '4_profile':
            return
        for pid, m in rpt.get('ket_qua_theo_profile', {}).items():
            bc = m.get('bao_cao_import', {}) or {}
            self.bang_v3_baocao.insert(
                '', 'end', values=(pid, m.get('dataset_id', ''), m.get('so_dong', 0),
                                   bc.get('thieu_ma', 0)))

    def _v3_nap_danh_sach_dataset(self):
        import db_phase2 as DB
        con = self._con_phase2()
        try:
            ds = DB.liet_ke_dataset(con)
        finally:
            con.close()
        self.bang_v3_dataset.delete(*self.bang_v3_dataset.get_children())
        for d in ds:
            self.bang_v3_dataset.insert(
                '', 'end', values=(d['dataset_id'], d['profile_id'], d['row_count'], d['updated_at']))
        self._phase2_nap_dataset()   # cập nhật lại dropdown dataset dùng chung tab 2/4 (Round 2, không đổi)

    # ---------------------------------------------------------- Tab 2: Sản phẩm
    def _v3_tab_2_san_pham(self):
        f = self._v3_tab_cuon('3. Sản phẩm')
        ttk.Label(f, text='Sản phẩm', style='V3Tieu.TLabel').pack(anchor='w', pady=(0, 10))

        kloc = self._v3_the(f, 'Bộ lọc')
        hang = ttk.Frame(kloc, style='V3Card.TFrame')
        hang.pack(fill='x')
        ttk.Label(hang, text='Dataset', style='V3CardMo.TLabel').pack(side='left')
        self.cb_phase2_dataset = ttk.Combobox(hang, textvariable=self.v_phase2_dataset,
                                              width=24, state='readonly')
        self.cb_phase2_dataset.pack(side='left', padx=(6, 16))
        self.cb_phase2_dataset.bind('<<ComboboxSelected>>', lambda e: self._v3_loc_san_pham())

        ttk.Label(hang, text='Outline', style='V3CardMo.TLabel').pack(side='left')
        self.v3_loc_outline = tk.StringVar(value='(tất cả)')
        self.cb_v3_loc_outline = ttk.Combobox(hang, textvariable=self.v3_loc_outline, width=20,
                                              state='readonly', values=['(tất cả)'])
        self.cb_v3_loc_outline.pack(side='left', padx=(6, 16))
        self.cb_v3_loc_outline.bind('<<ComboboxSelected>>', lambda e: self._v3_loc_san_pham())

        ttk.Label(hang, text='Tìm (tên/mã/record_id)', style='V3CardMo.TLabel').pack(side='left')
        self.v3_tim_kiem = tk.StringVar()
        e_tim = ttk.Entry(hang, textvariable=self.v3_tim_kiem, width=22)
        e_tim.pack(side='left', padx=(6, 0))
        e_tim.bind('<KeyRelease>', lambda e: self._v3_loc_san_pham())

        hang2 = ttk.Frame(kloc, style='V3Card.TFrame')
        hang2.pack(fill='x', pady=(10, 0))
        ttk.Button(hang2, text='Chọn dòng đang hiển thị', style='V3.TButton',
                  command=lambda: self._phase2_chon_hang_loat(True)).pack(side='left')
        ttk.Button(hang2, text='Bỏ chọn dòng đang hiển thị', style='V3.TButton',
                  command=lambda: self._phase2_chon_hang_loat(False)).pack(side='left', padx=8)

        hang3 = ttk.Frame(kloc, style='V3Card.TFrame')
        hang3.pack(fill='x', pady=(8, 0))
        ttk.Button(hang3, text='Đánh dấu viết cho dòng bôi đen', style='V3Chinh.TButton',
                  command=lambda: self._v3_dat_chon_boi_den(True)).pack(side='left')
        ttk.Button(hang3, text='Bỏ đánh dấu viết cho dòng bôi đen', style='V3.TButton',
                  command=lambda: self._v3_dat_chon_boi_den(False)).pack(side='left', padx=8)

        ttk.Label(kloc, text='Bấm 1 dòng để xem/chỉnh (dòng active, dùng cho Xem prompt/HTML). '
                             'Giữ Shift/Ctrl để bôi đen nhiều dòng rồi bấm 2 nút phía trên. '
                             'Bấm đúp 1 dòng để bật/tắt chọn viết bài riêng dòng đó.',
                  style='V3CardMo.TLabel', wraplength=1000).pack(anchor='w', pady=(8, 0))

        thongke = ttk.Frame(f, style='V3.TFrame')
        thongke.pack(fill='x', pady=(0, 8))
        self.lb_v3_tong = ttk.Label(thongke, text='Tổng sản phẩm: -', style='V3.TLabel')
        self.lb_v3_tong.pack(side='left', padx=(0, 24))
        self.lb_v3_hien_thi = ttk.Label(thongke, text='Đang hiển thị: -', style='V3.TLabel')
        self.lb_v3_hien_thi.pack(side='left', padx=(0, 24))
        self.lb_v3_da_chon = ttk.Label(thongke, text='Đã chọn: -', style='V3.TLabel')
        self.lb_v3_da_chon.pack(side='left')

        khung_bang = ttk.Frame(f, style='V3Card.TFrame')
        khung_bang.pack(fill='both', expand=True)
        self.bang_phase2 = ttk.Treeview(
            khung_bang, columns=('chon', 'record_id', 'profile', 'outline', 'ten'),
            show='headings', height=16, selectmode='extended')
        for c, n, w in [('chon', 'Chọn', 50), ('record_id', 'record_id', 240),
                        ('profile', 'Profile', 140), ('outline', 'Outline', 150),
                        ('ten', 'Tên hàng', 320)]:
            self.bang_phase2.heading(c, text=n)
            self.bang_phase2.column(c, width=w, anchor='center' if c == 'chon' else 'w')
        sb = ttk.Scrollbar(khung_bang, orient='vertical', command=self.bang_phase2.yview)
        self.bang_phase2.configure(yscrollcommand=sb.set)
        self.bang_phase2.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        self.bang_phase2.bind('<Double-1>', self._phase2_doi_chon)
        self.bang_phase2.bind('<<TreeviewSelect>>', self._v3_ghi_nho_active)
        self.bang_phase2.tag_configure('da_chon', foreground=V3_OK)

    def _v3_loc_san_pham(self):
        """Nạp bảng sản phẩm CÓ áp bộ lọc Outline + tìm kiếm (lọc phía
        Python trên dữ liệu đã lấy về — không đụng pipeline import/DB, chỉ
        lọc hiển thị). Cũng cập nhật 3 số thống kê."""
        import db_phase2 as DB
        did = self._phase2_dataset_id_dang_chon()
        self.bang_phase2.delete(*self.bang_phase2.get_children())
        if not did:
            self.lb_v3_tong.config(text='Tổng sản phẩm: -')
            self.lb_v3_hien_thi.config(text='Đang hiển thị: -')
            self.lb_v3_da_chon.config(text='Đã chọn: -')
            return
        con = self._con_phase2()
        try:
            sp_full = DB.liet_ke_san_pham(con, dataset_id=did)
            tong = DB.dem_san_pham(con, dataset_id=did)
        finally:
            con.close()

        gia_tri_outline = ['(tất cả)'] + sorted({x['outline_id'] for x in sp_full})
        if list(self.cb_v3_loc_outline['values']) != gia_tri_outline:
            self.cb_v3_loc_outline['values'] = gia_tri_outline

        sp = sp_full
        outline_loc = self.v3_loc_outline.get()
        if outline_loc and outline_loc != '(tất cả)':
            sp = [x for x in sp if x['outline_id'] == outline_loc]
        tu_khoa = (self.v3_tim_kiem.get() or '').strip().lower()
        if tu_khoa:
            sp = [x for x in sp if tu_khoa in
                 (x.get('ten_goc', '') + x.get('ma_goc', '') + x['record_id']).lower()]

        for row in sp:
            the = 'da_chon' if row.get('selected') else ''
            self.bang_phase2.insert(
                '', 'end', iid=row['record_id'],
                values=('✓' if row.get('selected') else '', row['record_id'], row['profile_id'],
                        row['outline_id'], row.get('ten_goc', '')),
                tags=(the,))

        # Task 1.2 (Ver 3.4 UI) — BUG THẬT trên Windows: bảng bị xoá-dựng-lại
        # (delete + insert) mỗi lần lọc/refresh làm MẤT focus/selection, dù
        # dataset vẫn báo đủ 245 sản phẩm đã chọn. Khôi phục lại active row
        # (đã ghi nhớ qua _v3_ghi_nho_active, bind <<TreeviewSelect>>) nếu
        # record đó còn tồn tại trong danh sách vừa lọc.
        if getattr(self, 'v3_active_record_id', None) and self.bang_phase2.exists(self.v3_active_record_id):
            self.bang_phase2.focus(self.v3_active_record_id)
            if not self.bang_phase2.selection():
                self.bang_phase2.selection_set(self.v3_active_record_id)

        da_chon = sum(1 for x in sp_full if x.get('selected'))
        self.lb_v3_tong.config(text=f'Tổng sản phẩm: {tong}')
        self.lb_v3_hien_thi.config(text=f'Đang hiển thị: {len(sp)}')
        self.lb_v3_da_chon.config(text=f'Đã chọn: {da_chon}')

    def _v3_ghi_nho_active(self, event=None):
        """Ghi nhớ record đang active (focus) mỗi khi selection Treeview đổi
        (click, Ctrl/Shift-click, phím mũi tên) — dùng để khôi phục lại sau
        khi bảng bị xoá-dựng-lại lúc lọc/refresh (Task 1.2, sửa bug thật)."""
        iid = self.bang_phase2.focus()
        if iid:
            self.v3_active_record_id = iid

    def _v3_dat_chon_boi_den(self, chon):
        """Task 1.1 — CHỈ tác động các dòng đang BÔI ĐEN (Treeview
        selection() qua Shift/Ctrl-click), khác với 'Chọn dòng đang hiển
        thị' (tác động TOÀN BỘ dòng đang lọc ra, không cần bôi đen)."""
        import db_phase2 as DB
        did = self._phase2_dataset_id_dang_chon()
        ids = list(self.bang_phase2.selection())
        if not did or not ids:
            messagebox.showinfo('Chưa bôi đen dòng nào',
                                'Bôi đen ít nhất 1 dòng trong bảng (click, hoặc giữ Shift/Ctrl '
                                'để chọn nhiều dòng) rồi bấm nút này.')
            return
        con = self._con_phase2()
        try:
            DB.dat_chon(con, did, ids, chon=chon)
        finally:
            con.close()
        self._v3_loc_san_pham()


    # ---------------------------------------------------------- Tab 3: Cấu hình
    def _v3_tab_0_bat_dau(self):
        """Ver 1.6 SONEALEO — tab ĐẦU TIÊN, chỉ để định hướng. Không có
        logic nghiệp vụ nào ở đây — chỉ giải thích thứ tự làm việc + nút
        nhảy thẳng tới đúng tab. Feedback thật từ Thịnh: "lẫn giữa quá
        nhiều tab, không biết bấm tab nào trước" — đây là câu trả lời."""
        f = self._v3_tab_cuon('0. Bắt đầu')
        ttk.Label(f, text='Bắt đầu từ đâu?', style='V3Tieu.TLabel').pack(anchor='w', pady=(0, 4))
        ttk.Label(f, text='8 tab bên trên chia làm 2 nhóm — LÀM 1 LẦN (setup) và LÀM MỖI LẦN '
                          '(vòng lặp hàng ngày). Bấm nút bên dưới để nhảy thẳng tới đúng tab.',
                  style='V3Mo.TLabel', wraplength=850).pack(anchor='w', pady=(0, 16))

        k1 = self._v3_the(f, 'LÀM 1 LẦN — thiết lập ban đầu (bỏ qua nếu đã làm rồi)')
        for so, ten, mo_ta, idx in [
            ('1', 'Cấu hình', 'Nhập API key Gemini + thông tin website WordPress.', 1),
            ('2', 'Nhập dữ liệu', 'Nhập file MASTER Excel — chỉ cần làm lại khi Excel có SKU mới.', 2),
        ]:
            hang = ttk.Frame(k1, style='V3Card.TFrame')
            hang.pack(fill='x', pady=4)
            ttk.Label(hang, text=f'Bước {so}', style='V3CardTieu.TLabel', width=10).pack(side='left', padx=(0, 10))
            ttk.Label(hang, text=f'{ten} — {mo_ta}', style='V3CardMo.TLabel', wraplength=560
                     ).pack(side='left', fill='x', expand=True)
            ttk.Button(hang, text=f'Đi tới tab {so}. {ten}', style='V3.TButton',
                      command=lambda i=idx: self.tab_ver3.select(i)).pack(side='right')

        k2 = self._v3_the(f, 'LÀM MỖI LẦN — vòng lặp chính hàng ngày')
        for so, ten, mo_ta, idx in [
            ('3', 'Sản phẩm', 'Chọn (bấm đúp) những SKU muốn đăng bài hôm nay.', 3),
            ('4', 'Sinh & Đăng', 'Bấm 1 nút — AI viết bài + đăng lên WordPress cho SKU đã chọn.', 4),
            ('5', 'Theo dõi', 'Xem lại đã đăng bao nhiêu bài, còn lại bao nhiêu, có lỗi không.', 5),
        ]:
            hang = ttk.Frame(k2, style='V3Card.TFrame')
            hang.pack(fill='x', pady=4)
            ttk.Label(hang, text=f'Bước {so}', style='V3CardTieu.TLabel', width=10).pack(side='left', padx=(0, 10))
            ttk.Label(hang, text=f'{ten} — {mo_ta}', style='V3CardMo.TLabel', wraplength=560
                     ).pack(side='left', fill='x', expand=True)
            ttk.Button(hang, text=f'Đi tới tab {so}. {ten}', style='V3Chinh.TButton',
                      command=lambda i=idx: self.tab_ver3.select(i)).pack(side='right')

        k3 = self._v3_the(f, 'NÂNG CAO / TUỲ CHỌN — không bắt buộc mỗi lần')
        for so, ten, mo_ta, idx in [
            ('6', 'Outline Studio', 'Chỉnh cấu trúc/mẫu nội dung — ít khi cần đụng tới.', 6),
            ('7', 'Article Jobs', 'Hàng đợi đăng bài kiểu khác — cách thay thế cho tab 4.', 7),
            ('8', 'Enhance', 'Làm dày nội dung bằng insight từ Google — bật tuỳ chọn.', 8),
        ]:
            hang = ttk.Frame(k3, style='V3Card.TFrame')
            hang.pack(fill='x', pady=4)
            ttk.Label(hang, text=f'Bước {so}', style='V3CardTieu.TLabel', width=10).pack(side='left', padx=(0, 10))
            ttk.Label(hang, text=f'{ten} — {mo_ta}', style='V3CardMo.TLabel', wraplength=560
                     ).pack(side='left', fill='x', expand=True)
            ttk.Button(hang, text=f'Đi tới tab {so}. {ten}', style='V3.TButton',
                      command=lambda i=idx: self.tab_ver3.select(i)).pack(side='right')

    def _v3_tab_3_cau_hinh(self):
        f = self._v3_tab_cuon('1. Cấu hình')
        ttk.Label(f, text='Cấu hình', style='V3Tieu.TLabel').pack(anchor='w', pady=(0, 10))

        # ---------------------------------------------------- AI (Task 2.1)
        gc = C.doc_gemini()
        kAI = self._v3_the(f, 'AI — Google Gemini')
        hangKey = ttk.Frame(kAI, style='V3Card.TFrame')
        hangKey.pack(fill='x', pady=3)
        ttk.Label(hangKey, text='Google API key', width=26, style='V3CardMo.TLabel').pack(side='left')
        self.v3_gemini_key = tk.StringVar(value=gc['api_key'])
        ttk.Entry(hangKey, textvariable=self.v3_gemini_key, width=44, show='*').pack(side='left')

        hangNghi = ttk.Frame(kAI, style='V3Card.TFrame')
        hangNghi.pack(fill='x', pady=3)
        ttk.Label(hangNghi, text='Nghỉ giữa 2 bài (giây)', width=26, style='V3CardMo.TLabel').pack(side='left')
        self.v3_nghi_giua_bai = tk.StringVar(value='5')
        ttk.Entry(hangNghi, textvariable=self.v3_nghi_giua_bai, width=10).pack(side='left')

        hangKiemTra = ttk.Frame(kAI, style='V3Card.TFrame')
        hangKiemTra.pack(fill='x', pady=(10, 4))
        self.nut_v3_kiem_tra_key = ttk.Button(hangKiemTra, text='Kiểm tra API key và model',
                                              style='V3Chinh.TButton', command=self._v3_kiem_tra_gemini)
        self.nut_v3_kiem_tra_key.pack(side='left')

        hangModel = ttk.Frame(kAI, style='V3Card.TFrame')
        hangModel.pack(fill='x', pady=(8, 3))
        ttk.Label(hangModel, text='Model đang chọn', width=26, style='V3CardMo.TLabel').pack(side='left')
        self.v3_gemini_model = tk.StringVar(value=gc['model'])
        self.cb_v3_gemini_model = ttk.Combobox(hangModel, textvariable=self.v3_gemini_model, width=30,
                                               state='readonly',
                                               values=[gc['model']] if gc['model'] else [])
        self.cb_v3_gemini_model.pack(side='left')
        self.cb_v3_gemini_model.bind('<<ComboboxSelected>>', self._v3_doi_gemini_model)
        self.lb_v3_gemini_trang_thai = ttk.Label(
            kAI, text=('Đã có model đã lưu trước đó: ' + gc['model'] if gc['model']
                      else 'Chưa kiểm tra — nhập API key rồi bấm nút phía trên.'),
            style='V3CardMo.TLabel')
        self.lb_v3_gemini_trang_thai.pack(anchor='w', pady=(6, 0))

        # ---------------------------------------------------- Ver 4.7 — Key/Model dự phòng
        kDuPhong = self._v3_the(f, 'Dự phòng (thử tự động khi lỗi — không bắt buộc)')
        ttk.Label(kDuPhong, text='Model dự phòng: dùng khi model chính bị cắt token/sinh nội dung rác. '
                                 'API key dự phòng: dùng khi key chính hết quota trong ngày. '
                                 'Mỗi dòng 1 giá trị, để trống nếu không cần.',
                  style='V3CardMo.TLabel', wraplength=900).pack(anchor='w', pady=(0, 8))
        hangDP = ttk.Frame(kDuPhong, style='V3Card.TFrame')
        hangDP.pack(fill='x')
        khungModel = ttk.Frame(hangDP, style='V3Card.TFrame')
        khungModel.pack(side='left', padx=(0, 20))
        ttk.Label(khungModel, text='Model dự phòng', style='V3CardMo.TLabel').pack(anchor='w')
        self.txt_v3_model_du_phong = tk.Text(khungModel, height=3, width=30)
        self.txt_v3_model_du_phong.insert('end', '\n'.join(gc.get('model_du_phong') or []))
        self.txt_v3_model_du_phong.pack()
        khungKey = ttk.Frame(hangDP, style='V3Card.TFrame')
        khungKey.pack(side='left')
        ttk.Label(khungKey, text='API key dự phòng', style='V3CardMo.TLabel').pack(anchor='w')
        self.txt_v3_key_du_phong = tk.Text(khungKey, height=3, width=44)
        self.txt_v3_key_du_phong.insert('end', '\n'.join(gc.get('api_key_du_phong') or []))
        self.txt_v3_key_du_phong.pack()
        ttk.Button(kDuPhong, text='Lưu dự phòng', command=self._v3_luu_du_phong
                  ).pack(anchor='w', pady=(8, 0))

        # ---------------------------------------------------- Website (Task 3.1)
        wc = C.doc_website()
        # Ver 2.6 — CSS ra ngoài: đo thật lúc audit Ver 2.6 cho thấy inline
        # CSS chiếm 55,9% độ dài mỗi bài và giống hệt nhau giữa mọi SKU.
        # Bật chế độ class + dán 1 file CSS lên site -> giảm ~36% độ dài bài.
        kCss = self._v3_the(f, 'CSS bài viết (Ver 2.6)')
        self.v3_css_class_mode = tk.BooleanVar(value=C.doc_css_class_mode())
        ttk.Checkbutton(kCss, text='Dùng CSS class thay vì inline style (giảm ~36% độ dài mỗi bài)',
                       variable=self.v3_css_class_mode,
                       command=self._v3_luu_css_mode).pack(anchor='w')
        ttk.Label(kCss, text='CHỈ bật SAU KHI đã dán file CSS lên website (Code Snippets / '
                            'Appearance > Additional CSS). Bật mà chưa dán -> bài mất định dạng.',
                  style='V3CardMo.TLabel', wraplength=820).pack(anchor='w', pady=(4, 8))
        self.v3_giao_dien_2_5 = tk.BooleanVar(value=C.doc_giao_dien_2_5())
        ttk.Checkbutton(kCss, text='Dùng BỐ CỤC CAO CẤP 2.5 (hero 2 cột, chip, mục lục neo, '
                                   'FAQ gập, CTA) — cần dán CSS mới trước',
                       variable=self.v3_giao_dien_2_5,
                       command=self._v3_luu_giao_dien_25).pack(anchor='w', pady=(8, 8))
        ttk.Button(kCss, text='Xuất file CSS để dán lên WordPress', style='V3.TButton',
                  command=self._v3_xuat_css).pack(anchor='w')

        # Ver 2.6 — 2 công tắc bỏ khối thừa, xác nhận qua ảnh trang thật
        _ht = C.doc_hien_thi_bai()
        kHt = self._v3_the(f, 'Khối thừa trong bài (Ver 2.6)')
        self.v3_bo_cta_cuoi = tk.BooleanVar(value=_ht['bo_cta_cuoi'])
        ttk.Checkbutton(kHt, text='Bỏ khối "Liên hệ báo giá" cuối bài (bật nếu theme đã có CTA riêng)',
                       variable=self.v3_bo_cta_cuoi, command=self._v3_luu_hien_thi).pack(anchor='w')
        # Ver 4.4 A1 — bỏ công tắc placeholder khỏi UI. Ô ảnh trống luôn ẩn
        # mặc định; giữ biến True chỉ để _v3_luu_hien_thi() tương thích API cũ.
        self.v3_bo_anh_placeholder = tk.BooleanVar(value=True)
        ttk.Label(kHt, text='Ô ảnh trống luôn được ẩn khỏi bài. Không còn công tắc bật/tắt placeholder.',
                  style='V3CardMo.TLabel', wraplength=820).pack(anchor='w', pady=(6, 0))

        kWeb = self._v3_the(f, 'Website WordPress')
        self.v3_web_ten = tk.StringVar(value=(wc or {}).get('ten', ''))
        self.v3_web_url = tk.StringVar(value=(wc or {}).get('url', ''))
        self.v3_web_hotline = tk.StringVar(value=(wc or {}).get('hotline', ''))
        self.v3_web_user = tk.StringVar(value=(wc or {}).get('user', ''))
        self.v3_web_pw = tk.StringVar(value=(wc or {}).get('app_pw', ''))
        self.v3_o_website = []
        for nhan, var, an in [('Tên website', self.v3_web_ten, False),
                              ('URL WordPress', self.v3_web_url, False),
                              ('Hotline watermark', self.v3_web_hotline, False),
                              ('Username', self.v3_web_user, False),
                              ('Application Password', self.v3_web_pw, True)]:
            hang = ttk.Frame(kWeb, style='V3Card.TFrame')
            hang.pack(fill='x', pady=3)
            ttk.Label(hang, text=nhan, width=26, style='V3CardMo.TLabel').pack(side='left')
            o = ttk.Entry(hang, textvariable=var, width=44, show='*' if an else '')
            o.pack(side='left')
            self.v3_o_website.append(o)

        # Ver 4.6 — chọn nơi đăng: Post WordPress thường (mặc định, mọi site
        # cũ) hay Product WooCommerce (site chạy Flatsome+Woo, VD
        # maybienapvn.vn). Theo TỪNG site, không phải cấu hình toàn cục —
        # Lotech có nhiều site, phần lớn vẫn là WordPress thường.
        self._v3_che_do_dang_nhan = {'Bài viết (Post — WordPress thường)': 'post',
                                     'Sản phẩm (WooCommerce)': 'woo_product'}
        self._v3_che_do_dang_nhan_nguoc = {v: k for k, v in self._v3_che_do_dang_nhan.items()}
        self.v3_web_che_do_dang = tk.StringVar(
            value=self._v3_che_do_dang_nhan_nguoc.get((wc or {}).get('che_do_dang', 'post')))
        hangCD = ttk.Frame(kWeb, style='V3Card.TFrame')
        hangCD.pack(fill='x', pady=3)
        ttk.Label(hangCD, text='Loại đăng', width=26, style='V3CardMo.TLabel').pack(side='left')
        self.cb_v3_web_che_do_dang = ttk.Combobox(hangCD, textvariable=self.v3_web_che_do_dang, width=42,
                                                  state='readonly', values=list(self._v3_che_do_dang_nhan.keys()))
        self.cb_v3_web_che_do_dang.pack(side='left')
        self.v3_o_website.append(self.cb_v3_web_che_do_dang)

        hangTT = ttk.Frame(kWeb, style='V3Card.TFrame')
        hangTT.pack(fill='x', pady=3)
        ttk.Label(hangTT, text='Trạng thái đăng', width=26, style='V3CardMo.TLabel').pack(side='left')
        ttk.Label(hangTT, text='Draft (cố định — không có lựa chọn Publish)',
                 style='V3CardMo.TLabel').pack(side='left')

        hangNut = ttk.Frame(kWeb, style='V3Card.TFrame')
        hangNut.pack(fill='x', pady=(10, 2))
        self.nut_v3_web_luu = ttk.Button(hangNut, text='Lưu cấu hình', style='V3Chinh.TButton',
                                         command=self._v3_luu_website)
        self.nut_v3_web_luu.pack(side='left')
        self.nut_v3_web_sua = ttk.Button(hangNut, text='Sửa', style='V3.TButton',
                                         command=self._v3_sua_website)
        self.nut_v3_web_sua.pack(side='left', padx=6)
        self.nut_v3_web_xoa = ttk.Button(hangNut, text='Xoá', style='V3Xoa.TButton',
                                         command=self._v3_xoa_website)
        self.nut_v3_web_xoa.pack(side='left')
        self.nut_v3_web_test = ttk.Button(hangNut, text='Kiểm tra kết nối', style='V3.TButton',
                                          command=self._v3_kiem_tra_ket_noi_website)
        self.nut_v3_web_test.pack(side='left', padx=6)
        self.lb_v3_web_trang_thai = ttk.Label(kWeb, text='', style='V3CardMo.TLabel', wraplength=900)
        self.lb_v3_web_trang_thai.pack(anchor='w', pady=(6, 0))
        self._v3_ap_dung_khoa_website(da_luu=bool(wc))

    def _v3_kiem_tra_gemini(self):
        """Task 2.1 — lưu API key vào cau-hinh.env rồi dò model THẬT qua
        autopost.do_model() (hàm có sẵn, đã chạy thật ở nhánh RMU — tái sử
        dụng nguyên vẹn, không viết lại). do_model() tự print() tiến trình,
        chạy trong luồng nền nên tự động chảy vào khung Nhật ký."""
        key = self.v3_gemini_key.get().strip()
        if not key:
            messagebox.showwarning('Thiếu API key', 'Nhập Google API key trước.')
            return
        C.luu_gemini(key, self.v3_gemini_model.get().strip())   # lưu trước để do_model() đọc đúng key qua os.environ
        self.nut_v3_kiem_tra_key.config(state='disabled')
        self.lb_v3_gemini_trang_thai.config(text='Đang kiểm tra API key + dò model (gọi Gemini thật, có thể mất '
                                                  'khoảng 1 phút)...')
        self.chay_nen_phase2(self._v3_viec_kiem_tra_gemini)

    def _v3_viec_kiem_tra_gemini(self):
        import autopost as A
        # Ver 5.7 — BUG THẬT đã tái hiện được: Python 3 XOÁ tên biến của
        # `except ... as e` ngay khi thoát khối except. self.ui() chỉ ĐẨY
        # lambda vào queue, _boc_hang_doi() chạy nó SAU đó ở luồng chính ->
        # lúc chạy thì `e` không còn tồn tại:
        #     NameError: cannot access free variable 'e' where it is not
        #                associated with a value in enclosing scope
        # _boc_hang_doi() nuốt NameError vào nhánh 'LỖI UI callback', nên
        # _v3_ket_qua_kiem_tra_gemini() KHÔNG BAO GIỜ được gọi khi kiểm tra
        # key thất bại -> nút "Kiểm tra key" kẹt disabled vĩnh viễn, label
        # kẹt ở "Đang kiểm tra...", và lỗi API thật không bao giờ hiện ra.
        # Sửa: hoá giá trị lỗi thành CHUỖI ngay trong khối except, rồi bắt
        # chuỗi đó bằng default-arg (không phải free variable) để lambda giữ
        # được giá trị kể cả khi chạy trễ.
        try:
            chay_duoc = A.do_model()
        except SystemExit as e:
            tin_loi = str(e)
            self.ui(lambda t=tin_loi: self._v3_ket_qua_kiem_tra_gemini(None, t))
            return
        except Exception as e:
            tin_loi = f'{type(e).__name__}: {e}'
            self.ui(lambda t=tin_loi: self._v3_ket_qua_kiem_tra_gemini(None, t))
            return
        self.ui(lambda kq=chay_duoc: self._v3_ket_qua_kiem_tra_gemini(kq, None))

    def _v3_ket_qua_kiem_tra_gemini(self, chay_duoc, loi):
        self.nut_v3_kiem_tra_key.config(state='normal')
        if loi:
            self.lb_v3_gemini_trang_thai.config(text=f'LỖI: {loi}')
            messagebox.showerror('Kiểm tra API key thất bại', loi)
            return
        if not chay_duoc:
            self.lb_v3_gemini_trang_thai.config(
                text='API key hợp lệ nhưng KHÔNG có model nào chạy được — xem chi tiết ở Nhật ký.')
            return
        ten_models = [t['ten'] for t in chay_duoc]
        self.cb_v3_gemini_model['values'] = ten_models
        self.v3_gemini_model.set(ten_models[0])
        C.luu_gemini(self.v3_gemini_key.get().strip(), ten_models[0])
        self.lb_v3_gemini_trang_thai.config(
            text=f'OK — {len(ten_models)} model chạy được, đã chọn "{ten_models[0]}" (đề xuất đầu danh sách).')

    def _v3_doi_gemini_model(self, event=None):
        model = self.v3_gemini_model.get().strip()
        if model:
            C.luu_gemini(self.v3_gemini_key.get().strip(), model)

    def _v3_luu_du_phong(self):
        """Ver 4.7 — lưu danh sách model/API key dự phòng, mỗi dòng 1 giá
        trị (Text widget, không phải Entry — cho nhập nhiều dòng thoải mái).
        Dòng trống bị bỏ qua tự động (cauhinh._tach_danh_sach khi đọc lại,
        ở đây tách trước khi lưu cho sạch dữ liệu ngay từ đầu)."""
        model_dp = [d.strip() for d in self.txt_v3_model_du_phong.get('1.0', 'end').split('\n') if d.strip()]
        key_dp = [d.strip() for d in self.txt_v3_key_du_phong.get('1.0', 'end').split('\n') if d.strip()]
        C.luu_gemini_du_phong(key_dp, model_dp)
        messagebox.showinfo('Đã lưu', f'Đã lưu {len(model_dp)} model dự phòng và {len(key_dp)} API key dự phòng.')

    def _v3_ap_dung_khoa_website(self, da_luu):
        """Đã lưu -> khoá ô nhập (state='disabled'), chỉ mở lại qua nút Sửa.
        Chưa lưu -> mở ô nhập, nút Sửa/Xoá tắt.

        Ver 4.6 — combobox "Loại đăng" là dropdown, mở ra phải là 'readonly'
        (chỉ chọn trong danh sách), không phải 'normal' (gõ tay tự do) như
        các Entry văn bản khác."""
        trang_thai_o = 'disabled' if da_luu else 'normal'
        for o in self.v3_o_website:
            if o is getattr(self, 'cb_v3_web_che_do_dang', None):
                o.config(state='disabled' if da_luu else 'readonly')
            else:
                o.config(state=trang_thai_o)
        self.nut_v3_web_luu.config(state='disabled' if da_luu else 'normal')
        self.nut_v3_web_sua.config(state='normal' if da_luu else 'disabled')
        self.nut_v3_web_xoa.config(state='normal' if da_luu else 'disabled')
        self.nut_v3_web_test.config(state='normal' if da_luu else 'disabled')

    def _v3_luu_website(self):
        ten = self.v3_web_ten.get().strip()
        url = self.v3_web_url.get().strip()
        user = self.v3_web_user.get().strip()
        pw = self.v3_web_pw.get()
        hotline_var = getattr(self, 'v3_web_hotline', None)
        hotline = hotline_var.get().strip() if hotline_var is not None else ''
        che_do_dang = self._v3_che_do_dang_nhan.get(self.v3_web_che_do_dang.get(), 'post')
        if not url or not user or not pw:
            messagebox.showwarning('Thiếu thông tin', 'Cần đủ URL, Username và Application Password.')
            return
        ten_cu_truoc_khi_luu = C.doc_website()   # để dò dữ liệu cũ có khoá theo tên (bản < 3.5) cần di chuyển
        C.luu_website(ten, url, user, pw, che_do_dang, hotline=hotline)
        self._v3_di_chuyen_du_lieu_khoa_cu((ten_cu_truoc_khi_luu or {}).get('ten'))
        self._v3_ap_dung_khoa_website(da_luu=True)
        self._v3_cap_nhat_site_hien_thi()
        self._v3_cap_nhat_kha_dung_che_do_that()
        self.lb_v3_web_trang_thai.config(text=f'Đã lưu cấu hình cho "{ten or url}". '
                                              f'Bấm "Kiểm tra kết nối" trước khi đăng bài thật.')
        print(f'== Đã lưu cấu hình website: {ten or url} ({url}) ==')

    def _v3_di_chuyen_du_lieu_khoa_cu(self, ten_cu_bo_sung=None):
        """Ver 3.5 — bản < 3.5 lưu bài viết theo khoá TÊN hiển thị (đã sửa
        thành khoá URL chuẩn hoá). Tự dò và di chuyển dữ liệu cũ, GIỮ NGUYÊN
        wp_id/wp_url/trạng thái/thời lượng (chỉ đổi 1 cột `site`, không xoá-
        tạo-lại dòng nào — xem db_phase2.doi_khoa_site).

        Luôn kiểm tra TÊN đang cấu hình hiện tại (trường hợp phổ biến nhất:
        mở app bản 3.5 lần đầu sau khi nâng cấp từ 3.4, tên chưa đổi gì).
        `ten_cu_bo_sung`: thêm tên VỪA bị thay thế nếu người dùng vừa đổi
        tên trong cùng thao tác Lưu — không đoán mò các giá trị `site` lạ
        khác, chỉ nhắm đúng 2 trường hợp đã biết chắc chắn."""
        import db_phase2 as DB
        wc = C.doc_website()
        if not wc:
            return
        site_key_moi = wc['site_key']
        con = self._con_phase2()
        try:
            ung_vien = set(DB.liet_ke_site_dang_dung(con))
            for ten_cu in filter(None, {wc.get('ten'), ten_cu_bo_sung}):
                if ten_cu in ung_vien and ten_cu != site_key_moi:
                    so = DB.doi_khoa_site(con, ten_cu, site_key_moi)
                    if so:
                        print(f'== Di chuyển {so} bài viết từ khoá cũ "{ten_cu}" sang khoá URL '
                             f'"{site_key_moi}" (giữ nguyên WP ID/URL/trạng thái) ==')
        finally:
            con.close()

    def _v3_sua_website(self):
        self._v3_ap_dung_khoa_website(da_luu=False)
        self.lb_v3_web_trang_thai.config(text='Đang chỉnh sửa — bấm "Lưu cấu hình" để áp dụng.')

    def _v3_xoa_website(self):
        if not messagebox.askyesno('Xoá cấu hình website',
                                   'Xoá toàn bộ cấu hình website hiện tại (URL/Username/Application '
                                   'Password)? Không xoá được bài đã đăng, chỉ xoá cấu hình kết nối.'):
            return
        C.xoa_website()
        self.v3_web_ten.set(''); self.v3_web_url.set('')
        self.v3_web_user.set(''); self.v3_web_pw.set('')
        self.v3_web_che_do_dang.set(self._v3_che_do_dang_nhan_nguoc.get('post'))
        self._v3_ap_dung_khoa_website(da_luu=False)
        self._v3_cap_nhat_site_hien_thi()
        self._v3_cap_nhat_kha_dung_che_do_that()
        self.lb_v3_web_trang_thai.config(text='Đã xoá cấu hình website.')
        print('== Đã xoá cấu hình website ==')

    def _v3_kiem_tra_ket_noi_website(self):
        self.nut_v3_web_test.config(state='disabled')
        self.lb_v3_web_trang_thai.config(text='Đang kiểm tra kết nối...')
        self.chay_nen_phase2(self._v3_viec_kiem_tra_ket_noi)

    def _v3_viec_kiem_tra_ket_noi(self):
        import ai_wp_adapter as AWP
        kq = AWP.kiem_tra_ket_noi_wp()
        self.ui(lambda: self._v3_ket_qua_kiem_tra_ket_noi(kq))

    def _v3_ket_qua_kiem_tra_ket_noi(self, kq):
        self.nut_v3_web_test.config(state='normal')
        if kq['ok']:
            self.lb_v3_web_trang_thai.config(text=f'✓ {kq["thong_diep"]}')
            print(f'== Kiểm tra kết nối OK: {kq["thong_diep"]} ==')
        else:
            self.lb_v3_web_trang_thai.config(text=f'✗ {kq["loi"]}')
            print(f'== Kiểm tra kết nối LỖI: {kq["loi"]} ==')
            messagebox.showerror('Kết nối thất bại', kq['loi'])

    # ---------------------------------------------------------- Tab 4: Sinh & Đăng
    def _v3_tab_4_sinh_dang(self):
        f = self._v3_tab_cuon('4. Sinh & Đăng')
        ttk.Label(f, text='Sinh & Đăng', style='V3Tieu.TLabel').pack(anchor='w', pady=(0, 10))

        kTT = self._v3_the(f, 'Trạng thái lựa chọn')
        hang = ttk.Frame(kTT, style='V3Card.TFrame')
        hang.pack(fill='x')
        ttk.Label(hang, text='Dataset đang chọn:', style='V3CardMo.TLabel').pack(side='left')
        ttk.Label(hang, textvariable=self.v_phase2_dataset, style='V3CardTieu.TLabel'
                 ).pack(side='left', padx=(6, 24))
        self.lb_v3_so_da_chon_sd = ttk.Label(hang, text='Số sản phẩm đã chọn: -', style='V3CardMo.TLabel')
        self.lb_v3_so_da_chon_sd.pack(side='left')
        ttk.Button(kTT, text='Cập nhật số đã chọn', style='V3.TButton',
                  command=self._v3_cap_nhat_so_da_chon).pack(anchor='w', pady=(8, 0))

        kCH = self._v3_the(f, 'Mẫu, website và chế độ')
        hangM = ttk.Frame(kCH, style='V3Card.TFrame')
        hangM.pack(fill='x')
        ttk.Label(hangM, text='Mẫu', style='V3CardMo.TLabel').pack(side='left')
        self.v_phase2_mau = tk.StringVar(value='chuan')
        ttk.Combobox(hangM, textvariable=self.v_phase2_mau, width=14, state='readonly',
                    values=['chuan', 'ngan_gon']).pack(side='left', padx=(6, 24))
        # Task 3: KHÔNG hiển thị site1/site2 — Ver 3 chỉ có 1 website đã cấu
        # hình ở tab "3. Cấu hình", dùng luôn tên đó cho cả chế độ Mock lẫn
        # WordPress thật (không phải dropdown chọn site nữa).
        ttk.Label(hangM, text='Website:', style='V3CardMo.TLabel').pack(side='left')
        self.v_phase2_site = tk.StringVar()
        ttk.Label(hangM, textvariable=self.v_phase2_site, style='V3CardTieu.TLabel').pack(side='left', padx=(6, 0))
        self._v3_cap_nhat_site_hien_thi()

        hangCD = ttk.Frame(kCH, style='V3Card.TFrame')
        hangCD.pack(fill='x', pady=(10, 0))
        ttk.Label(hangCD, text='Chế độ:', style='V3CardMo.TLabel').pack(side='left')
        self.v3_che_do = tk.StringVar(value='mock')
        self.v3_che_do.trace_add('write', self._v3_doi_che_do)
        ttk.Radiobutton(hangCD, text='Mock / Test', value='mock', variable=self.v3_che_do
                       ).pack(side='left', padx=(8, 16))
        self.rb_v3_that = ttk.Radiobutton(hangCD, text='WordPress thật', value='that',
                                          variable=self.v3_che_do)
        self.rb_v3_that.pack(side='left')
        ttk.Button(hangCD, text='Dọn state .mock', style='V3.TButton',
                   command=self._v3_don_state_mock).pack(side='right')
        self.lb_v3_ghi_chu_che_do = ttk.Label(kCH, text='', style='V3Ghi.TLabel')
        self.lb_v3_ghi_chu_che_do.pack(anchor='w', pady=(4, 0))
        self._v3_cap_nhat_kha_dung_che_do_that()

        kXem = self._v3_the(f, 'Xem trước')
        hangX = ttk.Frame(kXem, style='V3Card.TFrame')
        hangX.pack(fill='x')
        ttk.Button(hangX, text='Xem prompt', style='V3.TButton',
                  command=self._phase2_xem_prompt).pack(side='left')
        ttk.Button(hangX, text='Xem trước HTML', style='V3.TButton',
                  command=self._phase2_chay_thu).pack(side='left', padx=8)
        ttk.Button(hangX, text='Mở trong trình duyệt', style='V3.TButton',
                  command=self._phase2_mo_trinh_duyet).pack(side='left', padx=8)
        ttk.Label(kXem, text='(dùng sản phẩm đang chọn ở tab 2. Sản phẩm — luôn dùng chế độ Mock để '
                             'xem trước, không tốn quota Gemini thật)',
                  style='V3CardMo.TLabel').pack(anchor='w', pady=(2, 6))
        self.txt_phase2_thu = tk.Text(kXem, height=12, wrap='word', font=('Consolas', 9))
        self.txt_phase2_thu.pack(fill='both', expand=True)

        kChay = self._v3_the(f, 'Sinh bài')
        self.tien_do_v3 = ttk.Progressbar(kChay, style='V3.Horizontal.TProgressbar',
                                          mode='determinate')
        self.tien_do_v3.pack(fill='x', pady=(0, 6))
        self.lb_v3_tien_do = ttk.Label(kChay, text='Chưa chạy', style='V3CardTieu.TLabel')
        self.lb_v3_tien_do.pack(anchor='w', pady=(0, 10))

        hangChay = ttk.Frame(kChay, style='V3Card.TFrame')
        hangChay.pack(fill='x')
        self.nut_v3_sinh_bai = ttk.Button(hangChay, text='Sinh bài Mock', style='V3Chinh.TButton',
                                          command=self._v3_bam_sinh_bai)
        self.nut_v3_sinh_bai.pack(side='left')
        self.nut_v3_dung = ttk.Button(hangChay, text='⏹ Dừng khẩn cấp (Force Stop)',
                                      style='V3Dung.TButton', command=self._v3_force_stop,
                                      state='disabled')
        self.nut_v3_dung.pack(side='left', padx=(10, 0))
        self.nut_v3_tiep_tuc = ttk.Button(hangChay, text='Tiếp tục từ chỗ dừng', style='V3.TButton',
                                          command=self._v3_tiep_tuc_tu_cho_dung)
        self.nut_v3_tiep_tuc.pack(side='left', padx=(10, 0))
        # Ver 5.3 — VÁ LỖ HỔNG THẬT: trước đây bài đã có wp_id bị BỎ QUA
        # VĨNH VIỄN ở mọi bản sau — mọi cải tiến content/UI từ Ver 5.0 trở
        # đi KHÔNG BAO GIỜ hiện trên bài đã đăng trước đó (đã gây hiểu lầm
        # thật với Thịnh — tưởng bản vá không chạy, thực ra là do bài chưa
        # từng được sinh lại). Mặc định TẮT (an toàn — hành vi cũ không đổi
        # nếu không bật) — bật lên thì bài đã đăng KHÔNG bị bỏ qua nữa, sinh
        # lại nội dung mới rồi UPDATE đúng bài WordPress/WooCommerce cũ
        # (dang_woo_that/dang_wp_that đã tự tra wp_id/SKU cũ để update, đọc
        # code xác nhận — không cần sửa gì ở tầng đó).
        self.v3_cho_phep_cap_nhat = tk.BooleanVar(value=False)
        ttk.Checkbutton(hangChay, text='Cho phép cập nhật lại bài ĐÃ ĐĂNG (ghi đè nội dung cũ)',
                       variable=self.v3_cho_phep_cap_nhat).pack(side='left', padx=(16, 0))
        # Ver 3.9 C6 — nút riêng: title/slug/Rank Math, KHÔNG sinh lại bài, KHÔNG gọi AI.
        self.nut_v3_cap_nhat_seo = ttk.Button(hangChay, text='Cập nhật SEO (không AI)',
                                              command=self._v3_bam_cap_nhat_seo)
        self.nut_v3_cap_nhat_seo.pack(side='left', padx=(10, 0))
        ttk.Label(kChay, text='Chế độ Mock chạy HÀNG LOẠT cho mọi sản phẩm đã chọn. Chế độ WordPress '
                             'thật chỉ chạy ĐÚNG 1 record đang active (không batch trong Gate này). '
                             'Nhật ký chạy hiện ở khung "Nhật ký" phía dưới màn hình.',
                  style='V3CardMo.TLabel', wraplength=1000).pack(anchor='w', pady=(8, 0))

    def _v3_cap_nhat_site_hien_thi(self):
        wc = C.doc_website()
        self.v_phase2_site.set((wc.get('ten') or wc.get('url')) if wc else '(chưa cấu hình — vào tab "3. Cấu hình")')

    def _v3_site_key(self):
        """KHOÁ lưu trữ thật trong DB (URL đã chuẩn hoá) — KHÔNG BAO GIỜ
        dùng tên hiển thị làm khoá (Task idempotency Ver 3.5: đổi tên không
        đổi khoá, đổi domain mới coi là site khác). Có giá trị cố định dự
        phòng khi chưa cấu hình, để luồng Mock vẫn chạy được (không bắt
        buộc phải cấu hình website thật mới test được Mock)."""
        wc = C.doc_website()
        return wc['site_key'] if wc else 'chua-cau-hinh-website'

    def _v3_site_cfg(self):
        """site_cfg dùng cho khoi_cta() — Ver 3 chỉ có Tên/URL (không có
        hotline/zalo như site1/site2 RMU cũ), khoi_cta() tự có nhánh dự
        phòng khi thiếu hotline (xem render_phase2.khoi_cta), không crash."""
        wc = C.doc_website()
        return {'ten': (wc.get('ten') or wc.get('url')) if wc else 'website'}

    def _v3_cap_nhat_kha_dung_che_do_that(self):
        wc = C.doc_website()
        if wc:
            self.rb_v3_that.config(state='normal')
            self.lb_v3_ghi_chu_che_do.config(text='')
        else:
            if self.v3_che_do.get() == 'that':
                self.v3_che_do.set('mock')
            self.rb_v3_that.config(state='disabled')
            self.lb_v3_ghi_chu_che_do.config(
                text='Chưa cấu hình website ở tab "3. Cấu hình" — chưa chọn được chế độ WordPress thật.')

    def _v3_doi_che_do(self, *args):
        if self.v3_che_do.get() == 'that':
            self.nut_v3_sinh_bai.config(text='Đăng Draft lên WordPress')
        else:
            self.nut_v3_sinh_bai.config(text='Sinh bài Mock')

    def _v3_bam_sinh_bai(self):
        if self.v3_che_do.get() == 'that':
            self._v3_dang_draft_that()
        else:
            self._phase2_chay_hang_loat()

    def _v3_bam_cap_nhat_seo(self):
        """Ver 3.9 C6 — batch metadata-only; main thread snapshot toàn bộ Tk state."""
        import db_phase2 as DB
        import render_phase2 as R
        did = self._phase2_dataset_id_dang_chon()
        if not did:
            messagebox.showinfo('Chưa chọn dataset', 'Chọn dataset trước.')
            return
        wc = C.doc_website()
        if not wc or wc.get('che_do_dang') != 'woo_product':
            messagebox.showwarning('Chưa phải WooCommerce',
                                   'Cập nhật SEO 3.9 chỉ chạy cho site cấu hình Sản phẩm (WooCommerce).')
            return
        mau = self._phase2_mau_dang_chon()
        site = wc['site_key']
        con = self._con_phase2()
        try:
            sp = DB.liet_ke_san_pham(con, dataset_id=did, chi_da_chon=True)
            danh_sach = []
            for row in sp:
                # Ver 4.1 BUG-02: SEO-only cùng invariant validation với Save Draft.
                if row.get('nghi_van_dien_ap') is True:
                    continue
                if not R.dung_goi_cap_nhat_seo(row, mau=mau):
                    continue
                bv = DB.lay_bai_viet(con, did, row['record_id'], site, mau)
                if bv and bv.get('wp_id'):
                    danh_sach.append((dict(row), str(bv['wp_id'])))
        finally:
            con.close()
        if not danh_sach:
            messagebox.showinfo('Không có bài đủ điều kiện',
                                'Không có máy biến áp/MOF đã đăng có wp_id trong các sản phẩm đang chọn.')
            return
        if not messagebox.askyesno(
                'Cập nhật SEO không AI',
                f'Sẽ cập nhật {len(danh_sach)} sản phẩm trên WooCommerce.\n\n'
                'CHỈ ghi: tên sản phẩm, slug, 3 meta Rank Math.\n'
                'KHÔNG render lại nội dung, KHÔNG gọi Gemini.\n\nTiếp tục?'):
            return
        self.v3_dung_lai.clear()
        self.nut_v3_cap_nhat_seo.config(state='disabled')
        self.nut_v3_sinh_bai.config(state='disabled')
        self.nut_v3_dung.config(state='normal')
        self.tien_do_v3.config(value=0, maximum=max(len(danh_sach), 1))
        self.lb_v3_tien_do.config(text='Bắt đầu cập nhật SEO...')
        self.chay_nen_phase2(lambda: self._v3_cap_nhat_seo_worker(danh_sach, did, site, mau))

    def _v3_cap_nhat_seo_worker(self, danh_sach, did, site, mau):
        """Worker pure-Python/Tk-safe: dữ liệu Tk đã snapshot trước khi vào thread."""
        import ai_wp_adapter as AWP
        import db_phase2 as DB
        import render_phase2 as R
        con = self._con_phase2()
        ok = loi = 0
        try:
            tong = len(danh_sach)
            for i, (row, wp_id) in enumerate(danh_sach, 1):
                if self.v3_dung_lai.is_set():
                    break
                try:
                    # Defense-in-depth: danh_sach có thể được gọi test/trực tiếp.
                    # Block trước mọi WordPress transport, SEO path không gọi AI.
                    if row.get('nghi_van_dien_ap') is True:
                        print(f'   [SEO {i}/{tong}] BLOCKED {row.get("record_id")}: nghi_van_dien_ap=True')
                        continue
                    goi = R.dung_goi_cap_nhat_seo(row, mau=mau)
                    if not goi:
                        continue
                    kq = AWP.cap_nhat_seo_woo_that(
                        wp_id, goi['title'], goi['slug'], goi['meta_rank_math'])
                    if not kq.get('ok'):
                        loi += 1
                        print(f'   [SEO {i}/{tong}] LỖI {row["record_id"]}: {kq.get("loi", "không rõ")}')
                    else:
                        ok += 1
                        cap = {'title': goi['title'], 'slug': goi['slug']}
                        if goi.get('canh_bao_meta'):
                            cap['loi'] = goi['canh_bao_meta']
                            print(f'   [SEO {i}/{tong}] {goi["canh_bao_meta"]}')
                        DB.cap_nhat_bai_viet(con, did, row['record_id'], site, mau, **cap)
                        print(f'   [SEO {i}/{tong}] OK {row["record_id"]} -> WP ID={wp_id}')
                except Exception as e:
                    loi += 1
                    print(f'   [SEO {i}/{tong}] LỖI {row.get("record_id")}: {type(e).__name__}: {e}')
                self.ui(lambda i=i, tong=tong: self._v3_cap_nhat_tien_do(i, tong))
        finally:
            con.close()
            thong_bao = f'Cập nhật SEO xong: {ok} OK, {loi} lỗi.'
            self.ui(lambda: self._v3_ket_thuc_chay(thong_bao))
            self.ui(lambda: self.nut_v3_cap_nhat_seo.config(state='normal'))

    def _v3_dang_draft_that(self):
        """Ver 3.7 — Save Draft THẬT cho TOÀN BỘ sản phẩm đang được CHỌN
        (selected=1, khối "2. Sản phẩm"), không chỉ 1 record active như
        trước Ver 3.6. Record đã 'da_dang' (có wp_id) được bỏ qua, không gọi
        lại Gemini/WordPress — an toàn để bấm lại nhiều lần hoặc tiếp tục
        sau khi Dừng khẩn cấp giữa batch. Xác nhận tay trước khi bắn — đây
        là request THẬT lên website thật."""
        import db_phase2 as DB
        did = self._phase2_dataset_id_dang_chon()
        if not did:
            messagebox.showinfo('Chưa chọn dataset', 'Chọn dataset ở khối "1. Nhập dữ liệu" trước.')
            return
        wc = C.doc_website()
        if not wc:
            messagebox.showwarning('Chưa cấu hình website', 'Vào tab "3. Cấu hình" nhập đủ URL/'
                                   'Username/Application Password và Lưu trước.')
            return
        gc = C.doc_gemini()
        if not gc['api_key'] or not gc['model']:
            messagebox.showwarning('Chưa cấu hình AI', 'Vào tab "3. Cấu hình" nhập API key và bấm '
                                   '"Kiểm tra API key và model" trước.')
            return
        mau = self._phase2_mau_dang_chon()
        con = self._con_phase2()
        try:
            sp = DB.liet_ke_san_pham(con, dataset_id=did, chi_da_chon=True)
        finally:
            con.close()
        if not sp:
            messagebox.showinfo('Chưa chọn sản phẩm',
                                'Bấm đúp ở bảng "2. Sản phẩm" để chọn ít nhất 1 sản phẩm trước.')
            return
        cho_phep_cap_nhat = self.v3_cho_phep_cap_nhat.get()   # Ver 5.3 — đọc trên luồng chính
        nhan_che_do = 'Sản phẩm (WooCommerce)' if wc.get('che_do_dang') == 'woo_product' else 'Bài viết (Post)'
        dong_canh_bao_cap_nhat = (
            '\n⚠️ ĐANG BẬT "Cho phép cập nhật lại bài ĐÃ ĐĂNG" — sản phẩm đã đăng trước đó '
            'sẽ bị GHI ĐÈ nội dung mới, không còn được bỏ qua.\n'
            if cho_phep_cap_nhat else
            '\nSản phẩm đã đăng THÀNH CÔNG từ trước sẽ được bỏ qua (không gọi lại Gemini/WordPress).\n'
        )
        if not messagebox.askyesno(
                'Đăng Draft THẬT lên WordPress',
                f'Sắp gọi Gemini THẬT rồi đăng bài THẬT (trạng thái Draft, KHÔNG Publish) lên:\n\n'
                f'  Website: {wc["ten"] or wc["url"]}\n'
                f'  Loại đăng: {nhan_che_do}\n'
                f'  Số sản phẩm đã chọn: {len(sp)}\n'
                f'  Mẫu: {mau}\n'
                f'{dong_canh_bao_cap_nhat}\n'
                f'Việc này tốn quota Gemini thật. Tiếp tục?'):
            return
        self.nut_v3_sinh_bai.config(state='disabled')
        self.nut_v3_tiep_tuc.config(state='disabled')
        self.nut_v3_dung.config(state='normal')   # Ver 3.7: batch nhiều record -> Force Stop áp dụng, giống Mock
        self.v3_dung_lai.clear()
        self.tien_do_v3.config(value=0, maximum=max(len(sp), 1))
        self.lb_v3_tien_do.config(text='Bắt đầu...')
        danh_sach_thu = self._v3_danh_sach_key_model_du_phong(gc)
        nghi_giua_bai = self._v3_nghi_giua_bai_giay()   # Ver 5.1 — đọc trên luồng chính, KHÔNG đọc StringVar trong luồng nền
        enhance_cfg = {
            'bat': bool(getattr(self, 'v3_enhance_bat', None) and self.v3_enhance_bat.get()),
            'serper_key': self.v3_serper_key.get().strip() if hasattr(self, 'v3_serper_key') else '',
            'cong_dong': bool(getattr(self, 'v3_enhance_cong_dong', None) and self.v3_enhance_cong_dong.get()),
        }
        site_cfg = self._v3_site_cfg()
        image_root = ''
        if getattr(self, '_tab_anh_37', None):
            image_root = self._tab_anh_37.v_goc.get().strip()
        self.chay_nen_phase2(
            lambda: self._v3_viec_dang_draft_that_hang_loat(sp, mau, danh_sach_thu, wc, nghi_giua_bai,
                                                            cho_phep_cap_nhat, enhance_cfg, site_cfg, image_root))

    def _v3_tiep_tuc_tu_cho_dung(self):
        """Ver 4.4.1.2 — tiếp tục batch thật chỉ với record CHƯA có WP ID.

        Không bật cho_phep_cap_nhat, nên bài đã có WP ID tuyệt đối không bị đụng.
        """
        import db_phase2 as DB
        if self.v3_che_do.get() != 'that':
            messagebox.showinfo('Tiếp tục từ chỗ dừng', 'Chuyển sang chế độ WordPress thật trước.')
            return
        did = self._phase2_dataset_id_dang_chon()
        if not did:
            messagebox.showinfo('Chưa chọn dataset', 'Chọn dataset trước.')
            return
        wc = C.doc_website()
        if not wc:
            messagebox.showwarning('Chưa cấu hình website', 'Chưa có cấu hình WordPress.')
            return
        gc = C.doc_gemini()
        if not gc.get('api_key') or not gc.get('model'):
            messagebox.showwarning('Chưa cấu hình AI', 'Chưa có API key/model Gemini.')
            return
        mau = self._phase2_mau_dang_chon()
        site = wc['site_key']
        con = self._con_phase2()
        try:
            sp = DB.liet_ke_san_pham(con, dataset_id=did, chi_da_chon=True)
            con_lai = []
            for row in sp:
                bv = DB.lay_bai_viet(con, did, row['record_id'], site, mau)
                if not (bv and bv.get('wp_id')):
                    con_lai.append(row)
        finally:
            con.close()
        if not con_lai:
            messagebox.showinfo('Tiếp tục từ chỗ dừng', 'Không còn record nào chưa có WP ID.')
            return
        if not messagebox.askyesno(
                'Tiếp tục từ chỗ dừng',
                f'Còn {len(con_lai)} record chưa có WP ID.\n\n'
                'Chỉ chạy các record này; bài đã có WP ID sẽ không bị cập nhật. Tiếp tục?'):
            return
        danh_sach_thu = self._v3_danh_sach_key_model_du_phong(gc)
        nghi_giua_bai = self._v3_nghi_giua_bai_giay()
        enhance_cfg = {
            'bat': bool(getattr(self, 'v3_enhance_bat', None) and self.v3_enhance_bat.get()),
            'serper_key': self.v3_serper_key.get().strip() if hasattr(self, 'v3_serper_key') else '',
            'cong_dong': bool(getattr(self, 'v3_enhance_cong_dong', None) and self.v3_enhance_cong_dong.get()),
        }
        site_cfg = self._v3_site_cfg()
        image_root = self._tab_anh_37.v_goc.get().strip() if getattr(self, '_tab_anh_37', None) else ''
        self.v3_dung_lai.clear()
        self.nut_v3_sinh_bai.config(state='disabled')
        self.nut_v3_tiep_tuc.config(state='disabled')
        self.nut_v3_dung.config(state='normal')
        self.tien_do_v3.config(value=0, maximum=max(len(con_lai), 1))
        self.lb_v3_tien_do.config(text=f'Tiếp tục {len(con_lai)} record chưa có WP ID...')
        self.chay_nen_phase2(
            lambda: self._v3_viec_dang_draft_that_hang_loat(
                con_lai, mau, danh_sach_thu, wc, nghi_giua_bai, False,
                enhance_cfg, site_cfg, image_root))

    def _v3_nghi_giua_bai_giay(self):
        """Ver 5.1 — VÁ: ô "Nghỉ giữa 2 bài" có trên giao diện từ lâu nhưng
        CHƯA BAO GIỜ được đọc ở đâu cả (grep xác nhận: biến chỉ xuất hiện ở
        chỗ khai báo UI, không .get() nào khác trong toàn bộ code, không
        time.sleep() nào dùng nó) — phát hiện thật khi audit lại tool, xem
        Audit-Checklist-Ver5.0.xlsx mục Tool #6. Đọc + validate ở LUỒNG
        CHÍNH (an toàn với Tkinter, giống cách `mau` được validate trước
        khi vào luồng nền), trả về số giây hợp lệ. Giá trị âm/không phải số
        -> về 0 (không nghỉ), KHÔNG raise lỗi chặn cả batch chỉ vì gõ sai 1
        ô nhập liệu phụ."""
        try:
            giay = float(self.v3_nghi_giua_bai.get().strip().replace(',', '.'))
            return max(0.0, giay)
        except (ValueError, AttributeError):
            return 0.0

    def _v3_danh_sach_key_model_du_phong(self, gc):
        """Ver 4.7 — dựng danh sách (api_key, model) để thử lần lượt: cặp
        CHÍNH trước, rồi đổi MODEL (giữ nguyên key chính — rẻ, không tốn
        quota key khác, hợp lý khi lỗi là model tự cắt/sinh rác), rồi mới
        đổi KEY (hợp lý khi lỗi là hết quota trong ngày của key chính).

        Ver 5.1 — VÁ: ma trận cũ CHỈ có (key_chính×model_phụ) và
        (key_phụ×model_chính), THIẾU hẳn tổ hợp (key_phụ×model_phụ) —
        phát hiện khi audit lại tool (Audit-Checklist-Ver5.0.xlsx mục Tool
        #7). Nếu key chính hết quota TRONG NGÀY VÀ model chính đang lỗi
        cùng lúc, tổ hợp duy nhất còn cứu được batch lại chưa từng được
        thử. Bổ sung đủ ma trận: mọi (key, model) trong 2 danh sách, trừ
        cặp CHÍNH đã có ở đầu (tránh thử trùng lần đầu)."""
        danh_sach = [(gc['api_key'], gc['model'])]
        for m in gc.get('model_du_phong') or []:
            if m != gc['model']:
                danh_sach.append((gc['api_key'], m))
        for k in gc.get('api_key_du_phong') or []:
            if k != gc['api_key']:
                danh_sach.append((k, gc['model']))
        # Ver 5.1 — tổ hợp còn thiếu: MỌI key phụ × MỌI model phụ
        for k in gc.get('api_key_du_phong') or []:
            if k == gc['api_key']:
                continue
            for m in gc.get('model_du_phong') or []:
                if m == gc['model']:
                    continue
                cap = (k, m)
                if cap not in danh_sach:
                    danh_sach.append(cap)
        return danh_sach

    def _v3_viec_dang_draft_that_hang_loat(self, rows, mau, danh_sach_thu, wc, nghi_giua_bai=0.0,
                                          cho_phep_cap_nhat=False, enhance_cfg=None, site_cfg=None,
                                          image_root=''):
        """Ver 3.7 — vòng lặp Đăng Draft THẬT qua toàn bộ record đã chọn.
        Tái dùng ĐÚNG 3 bước Gemini/Hard Block/WordPress mà bản 1-record cũ
        đã dùng (goi_ai_that/kiem_tra_bia_toan_bo/dang_wp_that — cả 2 hàm
        AI/WP đã tự có retry + chống đẻ slug-2 từ Ver 3.4/3.5, KHÔNG viết lại
        retry ở đây). Chỉ thêm: vòng lặp qua nhiều record, bỏ qua record đã
        'da_dang', 1 record lỗi không dừng batch, dừng an toàn theo cờ
        self.v3_dung_lai (kiểm tra ở ĐẦU mỗi record — giống hệt cơ chế Force
        Stop của _phase2_viec_chay_hang_loat bên Mock, không phải cơ chế
        mới)."""
        import ai_wp_adapter as AWP
        import render_phase2 as R
        import db_phase2 as DB

        site = wc['site_key']   # KHOÁ lưu trữ = URL chuẩn hoá, KHÔNG dùng tên hiển thị (Ver 3.5)
        enhance_cfg = enhance_cfg or {'bat': False, 'serper_key': '', 'cong_dong': False}
        site_cfg = site_cfg or {'ten': wc.get('ten') or wc.get('url') or 'website'}
        con = self._con_phase2()
        tong = len(rows)
        ok, loi, bo_qua, bi_dung = 0, 0, 0, False
        thong_bao = 'Batch dừng bất thường — xem console để biết chi tiết.'  # giá trị an toàn mặc định
        try:
            self.ui(lambda: self._v3_cap_nhat_tien_do_that(0, tong, 0, 0))
            for i, row in enumerate(rows, 1):
                if self.v3_dung_lai.is_set():
                    bi_dung = True
                    print(f'== Đã dừng theo yêu cầu, còn lại {tong - i + 1} sản phẩm chưa chạy ==')
                    break
                if i > 1 and nghi_giua_bai > 0:   # Ver 3.9 — wait cho phép Force Stop ngắt ngay
                    if self.v3_dung_lai.wait(nghi_giua_bai):
                        bi_dung = True
                        print(f'== Đã dừng trong lúc nghỉ, còn lại {tong - i + 1} sản phẩm chưa chạy ==')
                        break

                did, rid = row['dataset_id'], row['record_id']
                t0 = time.time()
                try:
                    if row.get('nghi_van_dien_ap') is True:
                        loi += 1
                        ly_do_block = 'BLOCKED: nghi_van_dien_ap=True — cần kiểm tra dữ liệu điện áp trước khi sinh/đăng.'
                        DB.upsert_bai_viet_khoi_tao(con, did, rid, site, mau)
                        DB.cap_nhat_bai_viet(con, did, rid, site, mau, trang_thai='loi', loi=ly_do_block,
                                             thoi_luong_giay=time.time() - t0)
                        print(f'  [{i}/{tong}] {ly_do_block} {rid}')
                        self.ui(lambda i=i, tong=tong, ok=ok, loi=loi: self._v3_cap_nhat_tien_do_that(i, tong, ok, loi))
                        continue
                    bv_truoc = DB.lay_bai_viet(con, did, rid, site, mau)
                    da_dang_truoc = bool(bv_truoc and bv_truoc.get('trang_thai') == 'da_dang' and bv_truoc.get('wp_id'))
                    if da_dang_truoc and not cho_phep_cap_nhat:
                        ok += 1
                        bo_qua += 1
                        print(f'  [{i}/{tong}] [bỏ qua — đã đăng] {rid} -> '
                             f'wp_id={bv_truoc["wp_id"]} {bv_truoc.get("wp_url", "")}')
                        self.ui(lambda i=i, tong=tong, ok=ok, loi=loi: self._v3_cap_nhat_tien_do_that(i, tong, ok, loi))
                        continue
                    if da_dang_truoc and cho_phep_cap_nhat:
                        # Ver 5.3 — KHÔNG skip, sinh lại nội dung + gọi
                        # dang_woo_that()/dang_wp_that() như bình thường.
                        # 2 hàm này TỰ tra wp_id/SKU cũ (DB.lay_bai_viet ở
                        # trong chính hàm đó) để làm UPDATE (PUT) thay vì
                        # tạo bài mới — đã đọc code xác nhận trước khi làm,
                        # không cần truyền thêm tham số nào ở đây.
                        print(f'  [{i}/{tong}] [CẬP NHẬT LẠI] {rid} -> wp_id cũ={bv_truoc["wp_id"]}')

                    DB.upsert_bai_viet_khoi_tao(con, did, rid, site, mau)
                    # Ver 4.9.9 — tính tier/delta/tải ƯỚC TÍNH bằng CODE
                    # TRƯỚC khi gọi AI, gộp vào row để AI THẤY số liệu này
                    # (không tự tính giữa chừng — dễ sai/bịa hơn code, và
                    # Hard Block sẽ chặn nhầm số AI tự suy ra không khớp
                    # nguồn nếu không làm vậy).
                    cung_dong = DB.tim_san_pham_cung_dong(con, did, rid, site=site)   # Ver 5.0 — site để bảng so sánh ra link đúng
                    row_ai = R.bo_sung_may_tuong_thich(dict(row, **R.tinh_delta_context(row, cung_dong)))
                    print(f'== [{i}/{tong}] Gọi Gemini thật cho {rid} '
                         f'(model chính={danh_sach_thu[0][1]}, {len(danh_sach_thu)} cặp key/model sẵn sàng thử, mẫu={mau}) ==')
                    t_ai = time.perf_counter()
                    kq_ai, vi_pham = AWP.goi_ai_co_du_phong(row_ai, mau, danh_sach_thu, site_cfg=site_cfg, timeout=AWP.TIMEOUT_GEMINI)
                    tg_ai = time.perf_counter() - t_ai
                    for tcap in kq_ai.get('timing_pairs', []):
                        nhan = 'OK' if tcap.get('ok') else 'LỖI'
                        print(f'   [TIME] AI thử #{tcap.get("thu")} {tcap.get("model")}: {tcap.get("giay", 0):.1f}s -> {nhan}')
                    print(f'   [TIME] AI tổng: {tg_ai:.1f}s')
                    if not kq_ai['ok']:
                        loi += 1
                        print(f'   LỖI (đã thử {kq_ai.get("da_thu", "?")} cặp key/model): {kq_ai["loi"]}')
                        for dong in kq_ai.get('lich_su', []):
                            print(f'     - {dong}')
                        DB.cap_nhat_bai_viet(con, did, rid, site, mau, trang_thai='loi', loi=kq_ai['loi'],
                                             thoi_luong_giay=time.time() - t0)
                        self.ui(lambda i=i, tong=tong, ok=ok, loi=loi: self._v3_cap_nhat_tien_do_that(i, tong, ok, loi))
                        continue
                    ai_data = kq_ai['data']
                    model_ok = kq_ai.get('model_da_dung')
                    if model_ok and model_ok != os.environ.get('MODEL_GEMINI', ''):
                        C.luu_gemini('', model_ok)
                        print(f'   [MODEL] Đã nhớ MODEL_GEMINI={model_ok} vào cau-hinh.env; lượt sau ưu tiên model này.')
                    if kq_ai.get('da_thu', 1) > 1:
                        print(f'   (thành công sau khi đổi cặp key/model, thử lần {kq_ai["da_thu"]}; cặp thắng đã được đưa lên đầu cho bài kế)')
                    if kq_ai.get('faq_bi_bo'):
                        print('   (đã bỏ FAQ vì nội dung bất thường — bài vẫn đăng bình thường không có FAQ)')
                    if kq_ai.get('canh_bao_meta'):
                        print(f'   [CẢNH BÁO META] {kq_ai["canh_bao_meta"]}')

                    # SONEALEO Ver 1.1 — Enhance (tab 8): CHỈ chạy nếu bật
                    # checkbox, lỗi Enhance KHÔNG được chặn luồng đăng bài
                    # chính — coi như tính năng phụ, hỏng thì dùng ai_data
                    # gốc, không dừng cả batch vì 1 sản phẩm Enhance lỗi.
                    if enhance_cfg.get('bat'):
                        try:
                            import enhance as E
                            serper_key = enhance_cfg.get('serper_key', '') or C.doc_serper().get('api_key', '')
                            ten_loai = row.get('nhom_nguon') or row.get('thuong_hieu') or row.get('ten_goc', '')[:40]
                            kq_enh = E.enhance_1_san_pham(row_ai, ai_data, ten_loai, serper_key,
                                                          danh_sach_thu[0][1], danh_sach_thu[0][0], con=con,
                                                          bat_nguon_cong_dong=enhance_cfg.get('cong_dong', False))
                            if kq_enh.get('ok'):
                                if kq_enh['canh_bao']:
                                    print(f'   [Enhance] CẢNH BÁO Hard Block bắt số lạ, GIỮ ai_data gốc: {kq_enh["canh_bao"]}')
                                else:
                                    ai_data = kq_enh['ai_data_moi']
                                    print(f'   [Enhance] OK — fetch {kq_enh["so_url_fetch_duoc"]} URL, '
                                         f'bỏ {kq_enh["so_y_da_bo_vi_co_so"]} ý có số lọt qua, đã chèn insight sạch.')
                            else:
                                print(f'   [Enhance] Lỗi ({kq_enh["loi"]}) — dùng ai_data gốc, không chặn đăng bài.')
                        except Exception as e:
                            print(f'   [Enhance] Lỗi bất thường ({e}) — dùng ai_data gốc, không chặn đăng bài.')

                    t_render = time.perf_counter()
                    lien_quan = DB.tim_san_pham_lien_quan(con, did, rid, site)
                    bai = R.dung_bai_html(row, ai_data, site_cfg, mau=mau, san_pham_lien_quan=lien_quan,
                                         cung_dong=cung_dong)
                    tg_render = time.perf_counter() - t_render
                    print(f'   [TIME] Render HTML: {tg_render:.1f}s')

                    # Ver 4.4.1.2 — marker ảnh được renderer đặt đúng vị trí.
                    # Dù không có ảnh, cuối block vẫn gọi chen_anh_vao_bai([]) để
                    # xóa sạch marker/placeholder trước khi gửi WordPress.
                    import xu_ly_anh as X
                    anh_kq = None
                    t_anh = time.perf_counter()
                    if image_root:
                        import autopost as AP
                        import workspace_anh as WS
                        phan_rid = str(rid).split('::')
                        sheet_anh = phan_rid[1] if len(phan_rid) >= 2 else row.get('profile_id', '')
                        sku_anh = row.get('publish_sku') or row.get('ma_goc') or ''
                        thu_muc_anh = WS.tim_workspace(image_root, sheet_anh, sku_anh) if sku_anh else None
                        thu_muc_ho = WS.tim_workspace_ho(image_root, sheet_anh, row)
                        if thu_muc_anh or thu_muc_ho:
                            def _upload_anh(duong_dan, ten, mime, alt='', tieu_de=''):
                                # Ver 4.1 BUG-06: production path phải delivery alt/title
                                # sau khi tạo Media. Cache vẫn do autopost quản theo site+hash.
                                media_id, media_url = AP._url_anh_tren_wp(
                                    C.MA_SITE_VER3, duong_dan, tra_media_id=True)
                                if media_id and (alt or tieu_de):
                                    kq_meta = AWP.cap_nhat_meta_anh_media(media_id, alt, tieu_de or alt)
                                    if not kq_meta.get('ok'):
                                        print(f'  [CẢNH BÁO ảnh] Media {media_id} đã upload nhưng alt/title lỗi: {kq_meta.get("loi", "không rõ")}')
                                return media_id, media_url
                            anh_kq = X.dang_anh_hieu_luc(
                                image_root, sheet_anh, thu_muc_anh, row, C.MA_SITE_VER3,
                                tieu_de=bai['title'], slug=bai['slug'],
                                upload=_upload_anh, ghi_log=print)
                            # 4.4.1.4 HF1 BUG-E: một slot ảnh lỗi không được chặn
                            # 4 slot tốt. Chỉ hard-fail khi không còn ảnh hiệu
                            # lực nào để đưa vào bài.
                            if anh_kq.get('loi') and not anh_kq.get('anh'):
                                raise RuntimeError('Ảnh lỗi: ' + '; '.join(anh_kq['loi'][:3]))
                            if anh_kq.get('loi'):
                                print('   [CẢNH BÁO ảnh PARTIAL] ' + '; '.join(anh_kq['loi'][:3]))
                            for _cb in anh_kq.get('canh_bao', [])[:3]:
                                print('   [CẢNH BÁO ảnh fallback] ' + _cb)
                    bai['html'] = X.chen_anh_vao_bai(
                        bai['html'], (anh_kq or {}).get('anh') or [])

                    tg_anh = time.perf_counter() - t_anh
                    print(f'   [TIME] Ảnh/upload media: {tg_anh:.1f}s')
                    t_wp = time.perf_counter()

                    # Ver 4.6 — Woo trở thành luồng đăng CHÍNH cho site nào đã
                    # chọn "Sản phẩm (WooCommerce)" ở tab Cấu hình; site khác
                    # (đa số vẫn WordPress thường) không đổi hành vi cũ 1 chút
                    # nào — nhánh mặc định vẫn gọi dang_wp_that() y hệt trước.
                    canh_bao_rank_math = ''
                    meta_rank_math = None
                    if wc.get('che_do_dang') == 'woo_product':
                        meta_rank_math, canh_bao_rank_math = R.dung_rank_math(
                            row, bai, tra_canh_bao=True)
                        if canh_bao_rank_math:
                            print('   [CẢNH BÁO META] ' + canh_bao_rank_math)
                        # Ver 2.6 — short_description: ưu tiên khối HERO do bố
                        # cục 2.5 tách ra (chip + thông số nhanh + giá + CTA),
                        # rơi về meta_description nếu bố cục cũ không có.
                        # WooCommerce hiện short_description ngay cạnh ảnh và
                        # nút mua ở ĐẦU trang -> đây là chỗ ăn tiền nhất.
                        mo_ta_ngan = bai.get('short_description') or ai_data.get('meta_description', '')
                        kq_wp = AWP.dang_woo_that(did, rid, site, mau, bai['title'], bai['slug'], bai['html'],
                                                  mo_ta_ngan,
                                                  ma_hang=row.get('publish_sku', row.get('ma_goc')),
                                                  danh_muc=R.dung_danh_muc(row),
                                                  meta_rank_math=meta_rank_math,
                                                  schema=bai.get('schema'),
                                                  faq_schema=bai.get('faq_schema'))
                    else:
                        kq_wp = AWP.dang_wp_that(did, rid, site, mau, bai['title'], bai['slug'], bai['html'],
                                                 ai_data.get('meta_description', ''))
                    tg_wp = time.perf_counter() - t_wp
                    print(f'   [TIME] POST/PUT WordPress: {tg_wp:.1f}s')
                    if not kq_wp['ok']:
                        loi += 1
                        print(f'   LỖI đăng bài: {kq_wp["loi"]}')
                        DB.cap_nhat_bai_viet(con, did, rid, site, mau, trang_thai='loi', loi=kq_wp['loi'],
                                             thoi_luong_giay=kq_wp.get('thoi_luong_giay', time.time() - t0))
                        self.ui(lambda i=i, tong=tong, ok=ok, loi=loi: self._v3_cap_nhat_tien_do_that(i, tong, ok, loi))
                        continue

                    if anh_kq and anh_kq.get('anh'):
                        media_ids = [a.get('wp_media_id') for a in anh_kq['anh'] if a.get('wp_media_id')]
                        if media_ids:
                            kq_gan_anh = AWP.gan_anh_vao_san_pham(
                                kq_wp['wp_id'], media_ids, la_woo=(wc.get('che_do_dang') == 'woo_product'))
                            stale_ids = {str(x) for x in (kq_gan_anh.get('invalid_media_ids') or [])}
                            if not kq_gan_anh.get('ok') and stale_ids:
                                # Local/cache có media ID đã bị xoá trên WP.
                                # Loại đúng slot stale, purge cache, retry 1 lần
                                # với phần còn sống thay vì làm chết cả lô.
                                import dulieu as DL
                                stale_anh = [a for a in anh_kq['anh'] if str(a.get('wp_media_id')) in stale_ids]
                                anh_con = [a for a in anh_kq['anh'] if str(a.get('wp_media_id')) not in stale_ids]
                                try:
                                    WS.vo_hieu_delivery_media(image_root, sheet_anh, row, thu_muc_anh,
                                                              C.MA_SITE_VER3, stale_anh)
                                except Exception as _e:
                                    print(f'   [CẢNH BÁO] Không xoá được state media stale: {_e}')
                                for _mid in stale_ids:
                                    try:
                                        DL.xoa_cache_anh_wp_theo_media(C.MA_SITE_VER3, _mid)
                                    except Exception:
                                        pass
                                if anh_con:
                                    media_ids = [a.get('wp_media_id') for a in anh_con if a.get('wp_media_id')]
                                    kq_gan_anh = AWP.gan_anh_vao_san_pham(
                                        kq_wp['wp_id'], media_ids,
                                        la_woo=(wc.get('che_do_dang') == 'woo_product'))
                                    if kq_gan_anh.get('ok'):
                                        anh_kq['anh'] = anh_con
                                        # Bài vừa POST có thể đang chứa URL stale;
                                        # chèn lại body chỉ bằng ảnh còn hợp lệ.
                                        bai['html'] = X.chen_anh_vao_bai(bai['html'], anh_con)
                                        kq_body_fix = AWP.cap_nhat_noi_dung_bai_that(
                                            kq_wp['wp_id'], bai['html'],
                                            la_woo=(wc.get('che_do_dang') == 'woo_product'))
                                        if not kq_body_fix.get('ok'):
                                            kq_gan_anh = {'ok': False, 'loi': 'Gallery đã repair nhưng body repair lỗi: ' + kq_body_fix.get('loi','không rõ')}
                                        else:
                                            print('   [Ảnh PARTIAL] Đã loại media stale ' + ','.join(sorted(stale_ids)) + '; slot đó sẽ upload lại ở lần sau.')
                                else:
                                    # Tất cả ID stale: bài vừa POST đã chứa các URL ảnh cũ.
                                    # Bóc toàn bộ figure do SONEALEO quản lý khỏi body để
                                    # không để body hiển thị URL chết trong khi gallery fail.
                                    html_sach = X.chen_anh_vao_bai(bai['html'], [])
                                    kq_body_clean = AWP.cap_nhat_noi_dung_bai_that(
                                        kq_wp['wp_id'], html_sach,
                                        la_woo=(wc.get('che_do_dang') == 'woo_product'))
                                    if kq_body_clean.get('ok'):
                                        bai['html'] = html_sach
                                        kq_gan_anh = {'ok': False, 'loi': 'Tất cả media ID đều stale; state/cache đã xoá và body đã bỏ URL stale, cần chạy lại ảnh.'}
                                    else:
                                        kq_gan_anh = {'ok': False, 'loi': 'Tất cả media ID đều stale; state/cache đã xoá nhưng cleanup body lỗi: ' + kq_body_clean.get('loi', 'không rõ')}
                            if not kq_gan_anh.get('ok'):
                                loi += 1
                                loi_anh = 'Gắn ảnh vào bài lỗi: ' + kq_gan_anh.get('loi', 'không rõ lỗi')
                                print(f'   LỖI: {loi_anh}')
                                DB.cap_nhat_bai_viet(con, did, rid, site, mau, trang_thai='loi', loi=loi_anh,
                                                     thoi_luong_giay=time.time() - t0)
                                self.ui(lambda i=i, tong=tong, ok=ok, loi=loi: self._v3_cap_nhat_tien_do_that(i, tong, ok, loi))
                                continue
                            try:
                                WS.danh_dau_da_gan_vao_bai(image_root, sheet_anh, row, thu_muc_anh,
                                                           C.MA_SITE_VER3, kq_wp['wp_id'], anh_kq['anh'])
                            except Exception as _e:
                                print(f'   [CẢNH BÁO ảnh] WP đã gắn ảnh nhưng local state chưa ghi được: {_e}')

                    ok += 1
                    ngay = datetime.now(timezone.utc).isoformat()
                    thoi_luong = time.time() - t0
                    canh_bao_sau = '; '.join(x for x in (kq_ai.get('canh_bao_meta', ''), canh_bao_rank_math) if x)
                    DB.cap_nhat_bai_viet(con, did, rid, site, mau, slug=bai['slug'], title=bai['title'],
                                         meta_description=bai['meta_description'], html=bai['html'],
                                         trang_thai='da_dang', loi=canh_bao_sau,
                                         wp_id=str(kq_wp['wp_id']), wp_url=kq_wp['wp_url'],
                                         ngay_dang=ngay, thoi_luong_giay=thoi_luong)
                    print(f'   [TIME] TỔNG bài: {thoi_luong:.1f}s | AI={tg_ai:.1f}s | render={tg_render:.1f}s | ảnh={tg_anh:.1f}s | WP={tg_wp:.1f}s')
                    print(f'   [{i}/{tong}] THÀNH CÔNG — WP ID={kq_wp["wp_id"]}, URL={kq_wp["wp_url"]}, '
                         f'mất {thoi_luong:.1f}s')
                    self.ui(lambda i=i, tong=tong, ok=ok, loi=loi: self._v3_cap_nhat_tien_do_that(i, tong, ok, loi))
                except Exception as e:
                    # Ver 3.7.1 — GPT phát hiện: exception ngoài dự kiến (không
                    # phải {'ok': False} mà crash thật, VD dữ liệu hỏng khiến
                    # renderer/DB ném lỗi) làm chết cả batch trước bản vá này.
                    # Giờ CHỈ record này bị đánh dấu lỗi, batch chạy tiếp record
                    # kế — không phụ thuộc goi_ai_that()/dang_wp_that() có trả
                    # đúng {'ok': False} hay không.
                    loi += 1
                    print(f'   LỖI KHÔNG LƯỜNG TRƯỚC ({type(e).__name__}): {e}')
                    try:
                        DB.cap_nhat_bai_viet(con, did, rid, site, mau, trang_thai='loi',
                                             loi=f'Lỗi không lường trước: {type(e).__name__}: {e}',
                                             thoi_luong_giay=time.time() - t0)
                    except Exception as e2:
                        print(f'   (không ghi được lỗi vào DB: {e2}) — vẫn tiếp tục record kế')
                    self.ui(lambda i=i, tong=tong, ok=ok, loi=loi: self._v3_cap_nhat_tien_do_that(i, tong, ok, loi))

            moi = max(0, ok - bo_qua)
            if not bi_dung:
                print(f'== Xong: tạo/cập nhật {moi}, bỏ qua {bo_qua}, lỗi {loi} (tổng {tong}) ==')
            thong_bao = (f'Đã dừng ở {ok + loi}/{tong} (tạo/cập nhật {moi}, bỏ qua {bo_qua}, lỗi {loi})' if bi_dung
                        else f'Xong: tạo/cập nhật {moi}, bỏ qua {bo_qua}, lỗi {loi} (tổng {tong})')
        finally:
            con.close()
            # Ver 3.7.1 — GPT phát hiện: trước đây 2 dòng dưới nằm NGOÀI
            # try/finally, nên nếu có exception thoát khỏi toàn bộ hàm (dù giờ
            # rất khó xảy ra nhờ try/except từng record ở trên), nút Sinh/Đăng
            # kẹt disabled và nút Dừng kẹt enabled vĩnh viễn. Chuyển vào finally
            # để LUÔN chạy dù có lỗi gì xảy ra ở tầng nào.
            self.ui(self._v3_nap_dashboard)
            self.ui(lambda: self._v3_ket_thuc_chay(thong_bao))

    def _v3_cap_nhat_tien_do_that(self, da_xong, tong, ok, loi):
        """Ver 3.7 — hiển thị tối thiểu theo work order: đã chạy/tổng, số
        thành công, số lỗi. Record hiện tại đang chạy được in ra console
        (đủ cho Thịnh theo dõi lúc chạy tay), không cần thêm widget mới."""
        self.tien_do_v3.config(value=da_xong, maximum=max(tong, 1))
        phan_tram = int(da_xong / tong * 100) if tong else 0
        self.lb_v3_tien_do.config(
            text=f'Đang chạy {da_xong}/{tong} ({phan_tram}%) — thành công {ok}, lỗi {loi}')

    def _v3_cap_nhat_so_da_chon(self):
        import db_phase2 as DB
        did = self._phase2_dataset_id_dang_chon()
        if not did:
            self.lb_v3_so_da_chon_sd.config(text='Số sản phẩm đã chọn: -')
            return
        con = self._con_phase2()
        try:
            n = len(DB.liet_ke_san_pham(con, dataset_id=did, chi_da_chon=True))
        finally:
            con.close()
        self.lb_v3_so_da_chon_sd.config(text=f'Số sản phẩm đã chọn: {n}')

    # ---------------------------------------------------------- Tab 5: Theo dõi
    def _v3_tab_5_theo_doi(self):
        f = self._v3_tab_cuon('5. Theo dõi')
        ttk.Label(f, text='Theo dõi', style='V3Tieu.TLabel').pack(anchor='w', pady=(0, 10))

        kloc = self._v3_the(f, 'Bộ lọc')
        hang = ttk.Frame(kloc, style='V3Card.TFrame')
        hang.pack(fill='x')
        ttk.Label(hang, text='Dataset', style='V3CardMo.TLabel').pack(side='left')
        self.v3_dash_dataset = tk.StringVar(value='(tất cả)')
        self.cb_v3_dash_dataset = ttk.Combobox(hang, textvariable=self.v3_dash_dataset, width=22,
                                               state='readonly', values=['(tất cả)'])
        self.cb_v3_dash_dataset.pack(side='left', padx=(6, 16))
        self.cb_v3_dash_dataset.bind('<<ComboboxSelected>>', lambda e: self._v3_nap_dashboard())

        ttk.Label(hang, text='Website', style='V3CardMo.TLabel').pack(side='left')
        self.v_phase2_dash_site = tk.StringVar(value='(tất cả)')
        wc_hien_tai = C.doc_website()
        # Dropdown HIỂN THỊ tên đẹp (wc['ten']), nhưng khi lọc sẽ dịch sang
        # site_key (URL chuẩn hoá) — xem _v3_nap_dashboard(). Ver 3 chỉ có 1
        # website nên "chọn khác (tất cả)" luôn nghĩa là "website đang cấu
        # hình", không cần ánh xạ nhiều-chiều phức tạp.
        gia_tri_site_loc = ['(tất cả)'] + ([wc_hien_tai['ten'] or wc_hien_tai['url']] if wc_hien_tai else [])
        self.cb_v3_dash_site = ttk.Combobox(hang, textvariable=self.v_phase2_dash_site, width=14,
                                            state='readonly', values=gia_tri_site_loc)
        self.cb_v3_dash_site.pack(side='left', padx=(6, 16))
        self.cb_v3_dash_site.bind('<<ComboboxSelected>>', lambda e: self._v3_nap_dashboard())

        ttk.Label(hang, text='Mẫu', style='V3CardMo.TLabel').pack(side='left')
        self.v3_dash_mau = tk.StringVar(value='(tất cả)')
        cb_mau = ttk.Combobox(hang, textvariable=self.v3_dash_mau, width=12, state='readonly',
                              values=['(tất cả)', 'chuan', 'ngan_gon'])
        cb_mau.pack(side='left', padx=(6, 16))
        cb_mau.bind('<<ComboboxSelected>>', lambda e: self._v3_nap_dashboard())

        ttk.Label(hang, text='Trạng thái', style='V3CardMo.TLabel').pack(side='left')
        self.v3_dash_trang_thai = tk.StringVar(value='(tất cả)')
        cb_tt = ttk.Combobox(hang, textvariable=self.v3_dash_trang_thai, width=14, state='readonly',
                             values=['(tất cả)', 'CHƯA CHẠY', 'chua_sinh', 'da_dang', 'loi', 'da_go'])
        cb_tt.pack(side='left', padx=(6, 0))
        cb_tt.bind('<<ComboboxSelected>>', lambda e: self._v3_nap_dashboard())

        # Ver 4.4 C1/C3/C5 — tìm realtime + lọc họ trên bảng Theo dõi.
        hang2 = ttk.Frame(kloc, style='V3Card.TFrame')
        hang2.pack(fill='x', pady=(8, 0))
        ttk.Label(hang2, text='Tìm mã/tên', style='V3CardMo.TLabel').pack(side='left')
        self.v3_dash_tim = tk.StringVar()
        self.o_v3_dash_tim = ttk.Entry(hang2, textvariable=self.v3_dash_tim, width=28)
        self.o_v3_dash_tim.pack(side='left', padx=(6, 16))
        self.v3_dash_tim.trace_add('write', lambda *_: self._v3_nap_dashboard())
        ttk.Label(hang2, text='Họ sản phẩm', style='V3CardMo.TLabel').pack(side='left')
        self.v3_dash_ho = tk.StringVar(value='(tất cả)')
        self.cb_v3_dash_ho = ttk.Combobox(hang2, textvariable=self.v3_dash_ho, width=34,
                                         state='readonly', values=['(tất cả)'])
        self.cb_v3_dash_ho.pack(side='left', padx=(6, 16))
        self.cb_v3_dash_ho.bind('<<ComboboxSelected>>', lambda _e: self._v3_nap_dashboard())
        self.lb_v3_dash_dong = ttk.Label(hang2, text='dòng 0/0', style='V3CardMo.TLabel')
        self.lb_v3_dash_dong.pack(side='right')

        hangNut = ttk.Frame(f, style='V3.TFrame')
        hangNut.pack(fill='x', pady=(0, 8))
        ttk.Button(hangNut, text='Tải lại', style='V3Chinh.TButton',
                  command=self._v3_nap_dashboard).pack(side='left')
        ttk.Button(hangNut, text='Mở URL', style='V3.TButton',
                  command=self._v3_mo_url).pack(side='left', padx=8)
        ttk.Button(hangNut, text='Xem lỗi', style='V3.TButton',
                  command=self._v3_xem_loi_chi_tiet).pack(side='left')
        ttk.Button(hangNut, text='Đăng lại bài lỗi đã chọn', style='V3Chinh.TButton',
                  command=self._v3_dang_lai_bai_loi_da_chon).pack(side='left', padx=8)
        # Audit 3.7 mục 47: feature tracker chưa có implementation production;
        # ẩn nút disabled khỏi release UI thay vì để một control chết gây nhiễu.
        # Ver 2.6 — GỠ BÀI HÀNG LOẠT (rollback). Trước Ver 2.6 tool chỉ có
        # đường đăng, không có đường lùi: phát hiện dữ liệu nguồn sai sau
        # khi đã đăng vài trăm bài thì phải vào WP xoá tay từng bài.
        ttk.Button(hangNut, text='⟲ Gỡ bài hàng loạt', style='V3Dung.TButton',
                  command=self._v3_go_bai_hang_loat).pack(side='right')
        # Ver 4.4.1.5 — DỌN RÁC. Không sinh lại bài, không gọi AI, không tốn
        # quota: đọc HTML thật trên WP -> cắt mẫu rác -> ghi lại nếu đổi.
        ttk.Button(hangNut, text='🧹 Dọn rác bài đã đăng', style='V3.TButton',
                  command=self._v3_don_rac_hang_loat).pack(side='right', padx=8)

        khung_bang = ttk.Frame(f, style='V3Card.TFrame')
        khung_bang.pack(fill='both', expand=True)
        self._v3_dash_sort_col = 'stt'
        self._v3_dash_sort_desc = False
        self._v3_dash_iid_map = {}
        self._v3_dash_rows = []
        cot = ('stt', 'dataset', 'record_id', 'ten', 'profile', 'site', 'mau', 'trang_thai',
              'wp_id', 'url', 'thoi_gian', 'thoi_luong', 'loi')
        self.bang_phase2_dash = ttk.Treeview(khung_bang, columns=cot, show='headings', height=14,
                                            selectmode='extended')
        for c, n, w in [('stt', 'STT', 46), ('dataset', 'Dataset', 100), ('record_id', 'Record ID', 180),
                        ('ten', 'Tên sản phẩm', 220), ('profile', 'Profile', 105),
                        ('site', 'Website', 90), ('mau', 'Mẫu', 65),
                        ('trang_thai', 'Trạng thái', 90), ('wp_id', 'WP ID', 65),
                        ('url', 'URL', 190), ('thoi_gian', 'Thời gian', 110),
                        ('thoi_luong', 'Thời lượng', 85), ('loi', 'Lỗi', 220)]:
            self.bang_phase2_dash.heading(c, text=n, command=lambda cc=c: self._v3_sort_dashboard(cc))
            self.bang_phase2_dash.column(c, width=w, anchor='center' if c in ('stt','wp_id') else 'w')
        sb = ttk.Scrollbar(khung_bang, orient='vertical', command=self.bang_phase2_dash.yview)
        self.bang_phase2_dash.configure(yscrollcommand=sb.set)
        self.bang_phase2_dash.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        self.bang_phase2_dash.tag_configure('ok', foreground=V3_OK)
        self.bang_phase2_dash.tag_configure('loi', foreground=V3_ERR)
        self.bang_phase2_dash.bind('<<TreeviewSelect>>', self._v3_chon_dashboard)
        self.bang_phase2_dash.bind('<Control-f>', self._v3_focus_tim_dashboard)

    def _v3_luu_css_mode(self):
        bat = self.v3_css_class_mode.get()
        C.luu_css_class_mode(bat)
        import os
        os.environ['CSS_CLASS_MODE'] = '1' if bat else '0'   # có hiệu lực ngay, không cần khởi động lại
        print(f'== [CSS] Chế độ {"CLASS (cần đã dán CSS lên site)" if bat else "INLINE (mặc định cũ)"} ==')

    def _v3_luu_hien_thi(self):
        import os
        bo_cta = self.v3_bo_cta_cuoi.get()
        bo_anh = self.v3_bo_anh_placeholder.get()
        C.luu_hien_thi_bai(bo_cta, bo_anh)
        os.environ['BO_CTA_CUOI'] = '1' if bo_cta else '0'
        os.environ['BO_ANH_PLACEHOLDER'] = '1' if bo_anh else '0'
        print(f'== [Hiển thị] Bỏ CTA cuối: {"CÓ" if bo_cta else "không"} | '
             f'Bỏ ô ảnh placeholder: {"CÓ" if bo_anh else "không"} ==')

    def _v3_luu_giao_dien_25(self):
        import os
        bat = self.v3_giao_dien_2_5.get()
        C.luu_giao_dien_2_5(bat)
        os.environ['GIAO_DIEN_2_5'] = '1' if bat else '0'
        if bat and not self.v3_css_class_mode.get():
            messagebox.showwarning('Nhớ bật CSS class',
                                   'Bố cục 2.5 cần chế độ "Dùng CSS class" bật cùng, '
                                   'và file CSS mới đã dán lên WordPress.\n\n'
                                   'Chưa dán CSS -> bài sẽ mất định dạng.')
        print(f'== [Giao diện] Bố cục 2.5: {"BẬT" if bat else "tắt"} ==')

    def _v3_xuat_css(self):
        import render_phase2 as R
        duong_dan = filedialog.asksaveasfilename(
            defaultextension='.css', initialfile='sonealeo-style.css',
            filetypes=[('CSS', '*.css')])
        if not duong_dan:
            return
        with open(duong_dan, 'w', encoding='utf-8') as fh:
            fh.write(R.xuat_file_css())
        messagebox.showinfo('Đã xuất CSS',
                            f'Đã lưu: {duong_dan}\n\n'
                            f'BƯỚC TIẾP THEO:\n'
                            f'1. Mở nội dung file, copy toàn bộ.\n'
                            f'2. WordPress > Code Snippets (hoặc Appearance > Customize > '
                            f'Additional CSS) > dán vào, lưu lại.\n'
                            f'3. Quay lại đây tick ô "Dùng CSS class".\n'
                            f'4. Đăng thử 1 bài, mở xem có đúng định dạng không rồi mới chạy batch.')

    def _v3_go_bai_hang_loat(self):
        """Ver 2.6 — gỡ bài đã đăng khỏi WordPress, theo đúng BỘ LỌC đang
        chọn ở trên (dataset/website/mẫu) — không phải gỡ mù toàn bộ.

        AN TOÀN 2 LỚP: (1) hỏi xác nhận có kèm SỐ LƯỢNG thật + vài mã hàng
        mẫu để Thịnh thấy rõ sắp gỡ cái gì; (2) mặc định chuyển vào THÙNG
        RÁC WordPress (khôi phục được), KHÔNG xoá vĩnh viễn — muốn xoá hẳn
        phải tick thêm ô riêng trong hộp thoại thứ hai."""
        import db_phase2 as DB
        import ai_wp_adapter as AWP

        did = self.v3_dash_dataset.get()
        did = None if did in ('', '(tất cả)') else did
        con = self._con_phase2()
        try:
            danh_sach = DB.liet_ke_bai_da_dang(con, dataset_id=did)
        finally:
            con.close()
        if not danh_sach:
            messagebox.showinfo('Không có bài nào', 'Không tìm thấy bài nào đã đăng (có WP ID) '
                                'khớp bộ lọc hiện tại.')
            return

        mau_ma = ', '.join(b['record_id'].split('::')[-1] for b in danh_sach[:5])
        if not messagebox.askyesno(
                'XÁC NHẬN GỠ BÀI',
                f'Sắp gỡ {len(danh_sach)} bài khỏi WordPress.\n\n'
                f'Ví dụ: {mau_ma}{"..." if len(danh_sach) > 5 else ""}\n\n'
                f'Bài sẽ được chuyển vào THÙNG RÁC của WordPress '
                f'(khôi phục được từ giao diện WP).\n\nTiếp tục?'):
            return

        wc = C.doc_website() or {}
        la_woo = wc.get('che_do_dang') == 'woo_product'
        self.chay_nen_phase2(lambda: self._v3_go_bai_viec_chay(danh_sach, la_woo))

    def _v3_go_bai_viec_chay(self, danh_sach, la_woo):
        import ai_wp_adapter as AWP
        print(f'== [Gỡ bài] Bắt đầu gỡ {len(danh_sach)} bài '
             f'({"WooCommerce" if la_woo else "WordPress"}) -> Thùng rác ==')

        def tien_do(i, tong, ok, loi):
            print(f'   [{i}/{tong}] đã gỡ OK={ok}, lỗi={loi}')

        kq = AWP.go_bai_hang_loat(danh_sach, la_woo=la_woo, vinh_vien=False,
                                  goi_lai_tien_do=tien_do, co_dung=self.v3_dung_lai)
        print(f'== [Gỡ bài] XONG: {kq["ok"]} thành công, {kq["loi"]} lỗi ==')
        for ct in kq['chi_tiet']:
            if not ct['ok']:
                print(f'   LỖI wp_id={ct.get("wp_id")}: {ct.get("loi")}')
        self.ui(self._v3_nap_dashboard)

    # ============================================================ Ver 4.4.1.5 — Dọn rác
    def _v3_don_rac_hang_loat(self):
        """Ver 4.4.1.5 — dọn rác HTML trên bài ĐÃ ĐĂNG, theo bộ lọc dataset
        đang chọn. Không render lại, không gọi AI, không tốn quota Gemini.

        LUỒNG 2 BƯỚC BẮT BUỘC — không cho ghi thẳng:
          B1 CHẠY THỬ: đọc hết, đếm bài bẩn, KHÔNG ghi gì.
          B2 GHI THẬT: chỉ chạy sau khi Thịnh xem số ở B1 và đồng ý.
        Lý do: PUT đè body production không undo được bằng tool, và bài nào
        có người sửa tay trên WP sau khi đăng thì phần sửa tay đó mất.
        """
        import db_phase2 as DB

        did = self.v3_dash_dataset.get()
        did = None if did in ('', '(tất cả)') else did
        con = self._con_phase2()
        try:
            danh_sach = DB.liet_ke_bai_da_dang(con, dataset_id=did)
        finally:
            con.close()
        if not danh_sach:
            messagebox.showinfo('Không có bài nào',
                                'Không tìm thấy bài đã đăng (có WP ID) khớp bộ lọc.')
            return

        if not messagebox.askyesno(
                'Dọn rác — bước 1: CHẠY THỬ',
                f'Sắp ĐỌC {len(danh_sach)} bài từ WordPress để xem bài nào còn rác.\n\n'
                f'Bước này CHỈ ĐỌC, không sửa gì trên site.\n'
                f'Xem kết quả xong mới hỏi có ghi thật hay không.\n\nTiếp tục?'):
            return

        wc = C.doc_website() or {}
        la_woo = wc.get('che_do_dang') == 'woo_product'
        self.chay_nen_phase2(lambda: self._v3_don_rac_viec_chay(danh_sach, la_woo, True))

    def _v3_don_rac_viec_chay(self, danh_sach, la_woo, chi_thu):
        import sweep_rac as SR
        nhan = 'CHẠY THỬ' if chi_thu else 'GHI THẬT'
        print(f'== [Dọn rác] {nhan} trên {len(danh_sach)} bài '
              f'({"WooCommerce" if la_woo else "WordPress"}) ==')

        def tien_do(i, tong, da_don, sach_san, loi):
            if i % 10 == 0 or i == tong:
                print(f'   [{i}/{tong}] có rác={da_don}, đã sạch={sach_san}, lỗi={loi}')

        kq = SR.quet_hang_loat(danh_sach, la_woo=la_woo, chi_thu=chi_thu,
                               goi_lai_tien_do=tien_do, co_dung=self.v3_dung_lai)

        print(f'== [Dọn rác] {nhan} XONG: {kq["da_don"]} bài có rác, '
              f'{kq["sach_san"]} bài vốn đã sạch, {kq["loi"]} lỗi ==')
        for ma, n in sorted(kq['tong_theo_ma'].items()):
            print(f'   • {SR.mo_ta_rac(ma)}: {n} chỗ')
        for ct in kq['chi_tiet']:
            if not ct['ok']:
                print(f'   LỖI wp_id={ct.get("wp_id")}: {ct.get("loi")}')

        if chi_thu and kq['da_don']:
            vd = ', '.join(str(c.get('record_id') or c.get('wp_id'))
                           for c in kq['chi_tiet'] if c.get('thay_doi'))[:200]
            self.ui(lambda: self._v3_don_rac_hoi_ghi_that(danh_sach, la_woo, kq, vd))
        elif chi_thu:
            self.ui(lambda: messagebox.showinfo(
                'Không có gì để dọn',
                f'Đã kiểm {kq["tong"]} bài, tất cả đều sạch. Không cần ghi gì.'))
        else:
            self.ui(self._v3_nap_dashboard)

    def _v3_don_rac_hoi_ghi_that(self, danh_sach, la_woo, kq, vd):
        chi_tiet = '\n'.join(f'   • {__import__("sweep_rac").mo_ta_rac(m)}: {n} chỗ'
                             for m, n in sorted(kq['tong_theo_ma'].items()))
        if not messagebox.askyesno(
                'Dọn rác — bước 2: GHI THẬT',
                f'{kq["da_don"]}/{kq["tong"]} bài còn rác:\n\n{chi_tiet}\n\n'
                f'Ví dụ: {vd}...\n\n'
                f'GHI ĐÈ body {kq["da_don"]} bài này trên WordPress?\n'
                f'Thao tác này KHÔNG hoàn tác được bằng tool. Nếu có ai sửa tay '
                f'bài trên WP sau khi đăng thì phần sửa tay sẽ mất.\n\nGhi thật?'):
            print('== [Dọn rác] Thịnh huỷ ở bước ghi thật. Site không bị đụng. ==')
            return
        chi_ban = [b for b in danh_sach
                   if any(c.get('wp_id') == b.get('wp_id') and c.get('thay_doi')
                          for c in kq['chi_tiet'])]
        self.chay_nen_phase2(lambda: self._v3_don_rac_viec_chay(chi_ban, la_woo, False))

    # ============================================================ Ver 3.8 — Outline Studio
    def _v3_tab_6_outline_studio(self):
        """Ver 3.8 — chỉnh phần "AI viết" của mỗi outline (góc nhìn + hướng
        dẫn 4 mục + ghi chú riêng) mà không cần sửa code. KHÔNG hiện field
        dữ liệu/bảng thông số/Schema — những thứ đó khoá cứng trong
        render_phase2.py, không thuộc phạm vi tab này (đúng yêu cầu Work
        Order: quản lý block AI, không cho sửa block DATA/CODE/SCHEMA)."""
        import prompts_phase2 as PR

        f = self._v3_tab_cuon('6. Outline Studio')
        ttk.Label(f, text='Outline Studio — chỉnh CÁCH AI VIẾT từng loại outline',
                  style='Dam.TLabel').pack(anchor='w')
        ttk.Label(f, text='Chỉ sửa được: góc nhìn + hướng dẫn viết 4 mục + ghi chú riêng. '
                          'KHÔNG sửa được ở đây: field dữ liệu lấy từ Excel, bảng thông số kỹ thuật, '
                          'Schema.org, luật chống bịa số — các phần đó khoá cứng trong code.',
                  style='V3Mo.TLabel', wraplength=780, justify='left').pack(anchor='w', pady=(2, 14))

        hang = ttk.Frame(f)
        hang.pack(fill='x')
        ttk.Label(hang, text='Outline', style='Dam.TLabel').pack(side='left')
        self._os_outline_map = {f'{cfg["nhan_outline"]} ({oid})': oid
                                for oid, cfg in PR.OUTLINE_NOI_DUNG.items()}
        self.v_os_outline = tk.StringVar()
        self.cb_os_outline = ttk.Combobox(hang, textvariable=self.v_os_outline, width=42, state='readonly',
                                          values=list(self._os_outline_map.keys()))
        self.cb_os_outline.pack(side='left', padx=(8, 0))
        self.cb_os_outline.bind('<<ComboboxSelected>>', lambda e: self._os_nap())
        self.lb_os_trang_thai = ttk.Label(hang, text='', style='V3Mo.TLabel')
        self.lb_os_trang_thai.pack(side='left', padx=(16, 0))

        ttk.Label(f, text='Góc nhìn (đối tượng đọc / định hướng giọng văn)', style='Dam.TLabel'
                 ).pack(anchor='w', pady=(14, 2))
        self.txt_os_goc_nhin = tk.Text(f, height=2, width=95, wrap='word')
        self.txt_os_goc_nhin.pack(anchor='w')

        self.txt_os_section = {}
        for key, nhan in [('intro_html', 'Giới thiệu (intro_html)'),
                          ('dac_diem_html', 'Đặc điểm (dac_diem_html)'),
                          ('ung_dung_html', 'Ứng dụng (ung_dung_html)'),
                          ('huong_dan_chon_html', 'Hướng dẫn lựa chọn (huong_dan_chon_html)')]:
            ttk.Label(f, text=nhan, style='Dam.TLabel').pack(anchor='w', pady=(10, 2))
            t = tk.Text(f, height=3, width=95, wrap='word')
            t.pack(anchor='w')
            self.txt_os_section[key] = t

        ttk.Label(f, text='Ghi chú riêng outline (tuỳ chọn)', style='Dam.TLabel').pack(anchor='w', pady=(10, 2))
        self.txt_os_ghi_chu = tk.Text(f, height=2, width=95, wrap='word')
        self.txt_os_ghi_chu.pack(anchor='w')

        n = ttk.Frame(f)
        n.pack(fill='x', pady=(16, 0))
        ttk.Button(n, text='Lưu', style='Chinh.TButton', command=self._os_luu).pack(side='left')
        ttk.Button(n, text='Khôi phục mặc định', command=self._os_khoi_phuc).pack(side='left', padx=8)
        ttk.Button(n, text='Xem trước prompt gửi Gemini', command=self._os_xem_truoc).pack(side='left', padx=8)

        ttk.Label(f, text='Xem trước (prompt THẬT SẼ gửi cho Gemini, dùng 1 sản phẩm mẫu thuộc đúng '
                          'outline này trong dataset đang chọn ở khối "2. Nhập dữ liệu")',
                  style='Dam.TLabel').pack(anchor='w', pady=(18, 2))
        self.txt_os_xem_truoc = tk.Text(f, height=16, width=95, wrap='word')
        self.txt_os_xem_truoc.pack(anchor='w')

        if self._os_outline_map:
            self.cb_os_outline.current(0)
            self._os_nap()

    def _os_outline_id_dang_chon(self):
        return self._os_outline_map.get(self.v_os_outline.get())

    def _os_nap(self):
        """Đổ dữ liệu (đã tuỳ chỉnh nếu có, hoặc mặc định gốc) lên các ô nhập
        khi chọn outline khác — không tự lưu gì, chỉ hiển thị."""
        import prompts_phase2 as PR
        import outline_studio as OS
        oid = self._os_outline_id_dang_chon()
        if not oid:
            return
        cfg = OS.cfg_hieu_luc(oid, PR.OUTLINE_NOI_DUNG[oid])
        self.txt_os_goc_nhin.delete('1.0', 'end')
        self.txt_os_goc_nhin.insert('end', cfg.get('goc_nhin', ''))
        for key, widget in self.txt_os_section.items():
            widget.delete('1.0', 'end')
            widget.insert('end', cfg.get('sections', {}).get(key, ''))
        self.txt_os_ghi_chu.delete('1.0', 'end')
        self.txt_os_ghi_chu.insert('end', cfg.get('ghi_chu_bo_qua', '') or '')
        da_tuy_chinh = OS.doc_1(oid) is not None
        self.lb_os_trang_thai.config(text='(đã tuỳ chỉnh)' if da_tuy_chinh else '(đang dùng mặc định gốc)')
        self.txt_os_xem_truoc.delete('1.0', 'end')

    def _os_lay_input(self):
        return (self.txt_os_goc_nhin.get('1.0', 'end').strip(),
                {k: w.get('1.0', 'end').strip() for k, w in self.txt_os_section.items()},
                self.txt_os_ghi_chu.get('1.0', 'end').strip())

    def _os_luu(self):
        import outline_studio as OS
        oid = self._os_outline_id_dang_chon()
        if not oid:
            return
        goc_nhin, sections, ghi_chu = self._os_lay_input()
        OS.luu(oid, goc_nhin, sections, ghi_chu)
        self.lb_os_trang_thai.config(text='(đã tuỳ chỉnh)')
        messagebox.showinfo('Đã lưu', 'Đã lưu tuỳ chỉnh outline. Áp dụng ngay cho lần sinh bài kế tiếp '
                                      '(Mock lẫn WordPress thật) — không cần khởi động lại app.')

    def _os_khoi_phuc(self):
        import outline_studio as OS
        oid = self._os_outline_id_dang_chon()
        if not oid:
            return
        if not messagebox.askyesno('Khôi phục mặc định',
                                   'Xoá tuỳ chỉnh hiện tại của outline này, quay về đúng bản gốc trong code?'):
            return
        OS.khoi_phuc_mac_dinh(oid)
        self._os_nap()

    def _os_xem_truoc(self):
        """Lưu tuỳ chỉnh (an toàn/khôi phục được) rồi dựng THẬT prompt sẽ
        gửi Gemini bằng 1 record mẫu thuộc đúng outline đang sửa — cho thấy
        đúng hiệu quả của việc sửa, không phải bản mock giả lập (goi_ai_mock
        không đọc mô tả section nên không phản ánh được thay đổi ở đây)."""
        import db_phase2 as DB
        import prompts_phase2 as PR
        oid = self._os_outline_id_dang_chon()
        if not oid:
            return
        self._os_luu()
        did = self._phase2_dataset_id_dang_chon()
        if not did:
            messagebox.showinfo('Chưa chọn dataset',
                                'Chọn 1 dataset ở khối "2. Nhập dữ liệu" để có sản phẩm mẫu xem trước.')
            return
        con = self._con_phase2()
        try:
            ung_vien = DB.liet_ke_san_pham(con, dataset_id=did, outline_id=oid)
        finally:
            con.close()
        if not ung_vien:
            messagebox.showinfo('Không có sản phẩm mẫu',
                                f'Dataset đang chọn không có sản phẩm nào thuộc outline "{oid}".')
            return
        row = ung_vien[0]
        mau = self._phase2_mau_dang_chon()
        he_thong, nguoi_dung, _schema = PR.xay_prompt(row, self._v3_site_cfg(), mau=mau)
        self.txt_os_xem_truoc.delete('1.0', 'end')
        self.txt_os_xem_truoc.insert(
            'end',
            f'[Sản phẩm mẫu: {row.get("ten_goc", row["record_id"])}] [Mẫu: {mau}]\n\n'
            f'=== SYSTEM (đã áp dụng tuỳ chỉnh vừa lưu) ===\n{he_thong}\n\n'
            f'=== USER ===\n{nguoi_dung}')

    # ============================================================ Ver 3.9 — Article Jobs
    def _v3_tab_10_vision(self):
        """Ver 3.0 — ĐỌC THÔNG SỐ BẰNG AI VISION.

        Gộp 4 script rời (doc_bien_may, doc_catalogue_pdf, ghep_vao_master,
        enrich_tcvn_mba) vào 1 tab, chạy nền có tiến độ, không phải mở
        dòng lệnh.

        Thứ tự đúng: 1 tính TCVN (0 quota) -> 2 đọc biển máy -> 3 đọc
        catalogue PDF -> 4 soát Excel -> 5 ghép vào MASTER.
        """
        f = self._v3_tab_cuon('10. Đọc thông số (AI)')
        ttk.Label(f, text='Đọc thông số kỹ thuật từ ảnh biển máy & catalogue PDF',
                  style='V3Tieu.TLabel').pack(anchor='w', pady=(0, 4))
        ttk.Label(f, text='Làm theo thứ tự 1 → 5. Bước 1 KHÔNG tốn lượt AI. Bước 2, 3 tốn '
                          'lượt Gemini — chạy thử số nhỏ trước, soát kết quả rồi mới chạy nhiều.',
                  style='V3Mo.TLabel', wraplength=900).pack(anchor='w', pady=(0, 14))

        # --- Bước 1: TCVN (0 quota)
        k1 = self._v3_the(f, 'Bước 1 — Tính sẵn từ công thức & tiêu chuẩn (KHÔNG tốn lượt AI)')
        ttk.Label(k1, text='Tính dòng điện danh định 2 phía từ công thức, tra hiệu suất tối thiểu '
                          'TCVN 8525:2015. Xuất file _TCVN.xlsx, KHÔNG ghi đè file gốc.',
                  style='V3CardMo.TLabel', wraplength=860).pack(anchor='w', pady=(0, 8))
        ttk.Button(k1, text='Chọn MASTER và tính', style='V3Chinh.TButton',
                  command=self._v3_vision_tcvn).pack(anchor='w')

        # --- Bước 2: biển máy
        k2 = self._v3_the(f, 'Bước 2 — Đọc ảnh biển máy (tốn lượt AI)')
        ttk.Label(k2, text='Quét thư mục ảnh, tự lọc ảnh biển máy (bảng thông số gắn trên thân '
                          'máy) rồi đọc Po/Pk/Uk/tổ đấu dây/khối lượng. Kết quả có cột "Cần kiểm" '
                          '— dòng tô vàng là chỗ số liệu mâu thuẫn, phải soát tay.',
                  style='V3CardMo.TLabel', wraplength=860).pack(anchor='w', pady=(0, 8))
        h2 = ttk.Frame(k2, style='V3Card.TFrame'); h2.pack(fill='x')
        self.v3_vision_thu_muc = tk.StringVar()
        ttk.Entry(h2, textvariable=self.v3_vision_thu_muc, width=46).pack(side='left', fill='x', expand=True)
        ttk.Button(h2, text='Chọn...', style='V3.TButton',
                  command=lambda: self._v3_vision_chon_thu_muc(self.v3_vision_thu_muc)).pack(side='left', padx=(8, 0))
        h2b = ttk.Frame(k2, style='V3Card.TFrame'); h2b.pack(fill='x', pady=(8, 0))
        ttk.Label(h2b, text='Giới hạn số ảnh đọc lần này:', style='V3CardMo.TLabel').pack(side='left')
        self.v3_vision_gh_anh = tk.StringVar(value='25')
        ttk.Entry(h2b, textvariable=self.v3_vision_gh_anh, width=6).pack(side='left', padx=(8, 12))
        ttk.Button(h2b, text='Đọc biển máy', style='V3Chinh.TButton',
                  command=self._v3_vision_bien_may).pack(side='left')

        # --- Bước 3: catalogue PDF
        k3 = self._v3_the(f, 'Bước 3 — Đọc catalogue PDF (tốn lượt AI)')
        ttk.Label(k3, text='Bung PDF thành trang, lọc trang có bảng thông số bằng chữ trong PDF '
                          'trước (0 lượt), chỉ trang khả nghi mới hỏi AI. Mỗi dòng ghi rõ lấy từ '
                          'file nào, trang mấy.',
                  style='V3CardMo.TLabel', wraplength=860).pack(anchor='w', pady=(0, 8))
        h3 = ttk.Frame(k3, style='V3Card.TFrame'); h3.pack(fill='x')
        self.v3_vision_pdf = tk.StringVar()
        ttk.Entry(h3, textvariable=self.v3_vision_pdf, width=46).pack(side='left', fill='x', expand=True)
        ttk.Button(h3, text='Chọn...', style='V3.TButton',
                  command=lambda: self._v3_vision_chon_thu_muc(self.v3_vision_pdf)).pack(side='left', padx=(8, 0))
        h3b = ttk.Frame(k3, style='V3Card.TFrame'); h3b.pack(fill='x', pady=(8, 0))
        ttk.Label(h3b, text='Giới hạn số trang đọc lần này:', style='V3CardMo.TLabel').pack(side='left')
        self.v3_vision_gh_pdf = tk.StringVar(value='20')
        ttk.Entry(h3b, textvariable=self.v3_vision_gh_pdf, width=6).pack(side='left', padx=(8, 12))
        ttk.Button(h3b, text='Đọc catalogue', style='V3Chinh.TButton',
                  command=self._v3_vision_pdf_chay).pack(side='left')

        # --- Bước 5: ghép
        k5 = self._v3_the(f, 'Bước 5 — Ghép kết quả đã soát vào MASTER')
        ttk.Label(k5, text='CHỈ chạy SAU KHI đã mở 2 file kết quả và soát các dòng "Cần kiểm". '
                          'Không ghi đè ô đã có dữ liệu; số liệu lệch nhau đưa vào sheet DoiChieu '
                          'chờ bạn quyết. Xuất file _VISION.xlsx, MASTER gốc giữ nguyên.',
                  style='V3CardMo.TLabel', wraplength=860).pack(anchor='w', pady=(0, 8))
        ttk.Button(k5, text='Chọn MASTER + file kết quả rồi ghép', style='V3Chinh.TButton',
                  command=self._v3_vision_ghep).pack(anchor='w')

        self.tien_do_v3_vision = ttk.Progressbar(f, style='V3.Horizontal.TProgressbar',
                                                 mode='indeterminate')
        self.tien_do_v3_vision.pack(fill='x', pady=(14, 6))
        self.lb_v3_vision = ttk.Label(f, text='Chưa chạy', style='V3CardTieu.TLabel')
        self.lb_v3_vision.pack(anchor='w')

    def _v3_vision_chon_thu_muc(self, bien):
        d = filedialog.askdirectory()
        if d:
            bien.set(d)

    def _v3_vision_bao(self, chu):
        self.ui(lambda: self.lb_v3_vision.config(text=chu))

    def _v3_vision_tcvn(self):
        p = filedialog.askopenfilename(title='Chọn file MASTER', filetypes=[('Excel', '*.xlsx')])
        if not p:
            return
        def chay():
            import enrich_tcvn_mba as E
            self._v3_vision_bao('Đang tính dòng điện & tra TCVN...')
            try:
                ra = E.enrich_file(p)
                print(f'== [Vision] Bước 1 xong -> {ra} ==')
                self._v3_vision_bao(f'Xong. File mới: {ra}')
                self.ui(lambda: messagebox.showinfo(
                    'Xong bước 1', f'Đã tạo:\n{ra}\n\nNhập file này ở tab "Nhập dữ liệu" '
                    f'là bài tự dày lên (Dynamic Schema tự nhận cột mới).'))
            except Exception as e:
                print(f'   LỖI bước 1: {e}')
                self._v3_vision_bao(f'Lỗi: {e}')
        self.chay_nen_phase2(chay)

    def _v3_vision_bien_may(self):
        goc = self.v3_vision_thu_muc.get().strip()
        if not goc:
            messagebox.showinfo('Chưa chọn thư mục', 'Chọn thư mục ảnh trước.')
            return
        try:
            gh = int(self.v3_vision_gh_anh.get() or 25)
        except ValueError:
            gh = 25
        if not messagebox.askyesno('Xác nhận',
                                   f'Sắp đọc tối đa {gh} ảnh biển máy bằng AI.\n\n'
                                   f'Mỗi ảnh tốn 1 lượt Gemini. Ảnh đã đọc lần trước được '
                                   f'lấy từ bộ nhớ đệm, không tốn thêm.\n\nTiếp tục?'):
            return
        def chay():
            import doc_bien_may as D
            self.ui(lambda: self.tien_do_v3_vision.start(12))
            self._v3_vision_bao(f'Đang quét & đọc tối đa {gh} ảnh biển máy...')
            try:
                # Ver 3.1 — quet_va_doc trả (danh_sách, thống_kê), KHÔNG phải
                # 1 list. Bản 3.0 unpack thiếu -> AttributeError khi xuất
                # Excel (lỗi P0 #1, GPT bắt được).
                kq, dem = D.quet_va_doc(goc, gioi_han=gh)
                ra = D.xuat_excel(kq) if kq else None
                print(f'== [Vision] Bước 2 xong: {len(kq)} dòng '
                      f'(quét {dem["anh"]} ảnh, {dem["goi_ai"]} lượt AI, '
                      f'cache đỡ {dem["bo_cache"]}, lỗi {dem["loi"]}) -> {ra} ==')
                if ra:
                    self._v3_vision_bao(f'Xong {len(kq)} dòng. File: {ra}')
                    self.ui(lambda: messagebox.showinfo(
                        'Xong bước 2', f'Đã tạo: {ra}\n\nMỞ FILE và soát các dòng tô vàng '
                        f'(cột "Cần kiểm") TRƯỚC KHI ghép ở bước 5.'))
                else:
                    self._v3_vision_bao('Không đọc được biển máy nào (xem Nhật ký).')
                    self.ui(lambda: messagebox.showinfo(
                        'Bước 2', 'Không đọc được biển máy nào — hết giới hạn lượt, '
                        'hoặc thư mục không có ảnh biển máy.'))
            except Exception as e:
                print(f'   LỖI bước 2: {e}')
                self._v3_vision_bao(f'Lỗi: {e}')
            finally:
                self.ui(lambda: self.tien_do_v3_vision.stop())
        self.chay_nen_phase2(chay)

    def _v3_vision_pdf_chay(self):
        goc = self.v3_vision_pdf.get().strip()
        if not goc:
            messagebox.showinfo('Chưa chọn thư mục', 'Chọn thư mục chứa file PDF trước.')
            return
        try:
            gh = int(self.v3_vision_gh_pdf.get() or 20)
        except ValueError:
            gh = 20
        if not messagebox.askyesno('Xác nhận',
                                   f'Sắp đọc tối đa {gh} trang PDF bằng AI.\n\n'
                                   f'Chỉ trang CÓ BẢNG THÔNG SỐ mới tốn lượt.\n\nTiếp tục?'):
            return
        def chay():
            import doc_catalogue_pdf as D
            import os as _os
            self.ui(lambda: self.tien_do_v3_vision.start(12))
            self._v3_vision_bao(f'Đang đọc catalogue PDF (tối đa {gh} trang)...')
            try:
                # Ver 3.1 — doc_mot_pdf trả (danh_sách_dòng, số_lượt_AI).
                # Bản 3.0 extend cả tuple vào list + trừ quota bằng số DÒNG
                # thay vì số LƯỢT AI (lỗi P0 #2).
                tat_ca, con_lai = [], gh
                for ten in sorted(_os.listdir(goc)):
                    if not ten.lower().endswith('.pdf') or con_lai <= 0:
                        continue
                    kq, n_goi = D.doc_mot_pdf(_os.path.join(goc, ten), con_lai)
                    tat_ca.extend(kq)
                    con_lai -= n_goi
                    print(f'   {ten}: {len(kq)} dòng ({n_goi} lượt AI)')
                ra = D.xuat_excel(tat_ca) if tat_ca else None
                print(f'== [Vision] Bước 3 xong: {len(tat_ca)} dòng -> {ra} ==')
                if ra:
                    self._v3_vision_bao(f'Xong {len(tat_ca)} dòng. File: {ra}')
                    self.ui(lambda: messagebox.showinfo('Xong bước 3',
                                                        f'Đã tạo: {ra}\n\nSoát rồi ghép ở bước 5.'))
                else:
                    self._v3_vision_bao('Không đọc được bảng nào (xem Nhật ký).')
                    self.ui(lambda: messagebox.showinfo(
                        'Bước 3', 'Không đọc được bảng thông số nào từ các PDF này.'))
            except Exception as e:
                print(f'   LỖI bước 3: {e}')
                self._v3_vision_bao(f'Lỗi: {e}')
            finally:
                self.ui(lambda: self.tien_do_v3_vision.stop())
        self.chay_nen_phase2(chay)

    def _v3_vision_ghep(self):
        master = filedialog.askopenfilename(title='Chọn file MASTER cần ghép vào',
                                            filetypes=[('Excel', '*.xlsx')])
        if not master:
            return
        files = filedialog.askopenfilenames(
            title='Chọn file kết quả đã soát (chọn được nhiều)',
            filetypes=[('Excel', '*.xlsx')])
        if not files:
            return
        def chay():
            import ghep_vao_master as G
            import os as _os
            self._v3_vision_bao('Đang ghép...')
            try:
                # Ver 3.1 — G.ghep cần [(đường_dẫn, ưu_tiên)], KHÔNG phải
                # list đường dẫn trần (lỗi P0 #3). Ưu tiên 0 = biển máy
                # (máy thật, tin hơn), 1 = catalogue.
                cap = [(f, 0 if 'bien' in _os.path.basename(f).lower() else 1)
                       for f in files]
                ra = G.ghep(master, cap)
                if not ra:
                    self._v3_vision_bao('Không có dòng nào dùng được để ghép.')
                    self.ui(lambda: messagebox.showinfo(
                        'Bước 5', 'Không ghép được dòng nào — kiểm tra file kết quả:\n'
                        '- Mọi dòng còn dấu X ở cột "Cần kiểm" đều bị bỏ qua\n'
                        '- Dòng thiếu công suất (kVA) cũng bị bỏ qua'))
                    return
                print(f'== [Vision] Bước 5 xong -> {ra} ==')
                self._v3_vision_bao(f'Xong. File mới: {ra}')
                self.ui(lambda: messagebox.showinfo(
                    'Xong bước 5', f'Đã tạo:\n{ra}\n\nMASTER gốc KHÔNG bị sửa.\n'
                    f'Xem sheet "DoiChieu" nếu có số liệu lệch nhau.\n\n'
                    f'Nhập file này ở tab "Nhập dữ liệu" rồi chạy lại batch.'))
            except Exception as e:
                print(f'   LỖI bước 5: {e}')
                self._v3_vision_bao(f'Lỗi: {e}')
        self.chay_nen_phase2(chay)

    def _v3_tab_9_anh(self):
        """Ver 3.0 ULTRA — tab Ảnh sản phẩm: quét thư mục ảnh trên máy,
        ghép với SKU bằng tên file, tối ưu WebP, upload lên WordPress và
        đặt ảnh đại diện.

        Thiết kế theo đúng yêu cầu Thịnh: có bước XEM TRƯỚC riêng, sửa
        được mã hàng bằng tay, chọn được ảnh đại diện, và upload là hành
        động tách bạch — không bao giờ tự động chạy."""
        f = self._v3_tab_cuon('9. Ảnh sản phẩm')
        ttk.Label(f, text='Ảnh sản phẩm — ghép theo tên file', style='V3Tieu.TLabel'
                 ).pack(anchor='w', pady=(0, 4))
        ttk.Label(f, text='Đặt tên file dạng "mba mbt 3p 250kva.jpg" (hãng + pha + công suất) '
                          'thì tool tự ghép với mã hàng. Tên không đọc được sẽ để trống cho '
                          'bạn gán tay — tool KHÔNG đoán bừa.',
                  style='V3Mo.TLabel', wraplength=900).pack(anchor='w', pady=(0, 14))

        kTM = self._v3_the(f, 'Thư mục ảnh trên máy')
        hang = ttk.Frame(kTM, style='V3Card.TFrame')
        hang.pack(fill='x')
        self.v3_anh_thu_muc = tk.StringVar()
        ttk.Entry(hang, textvariable=self.v3_anh_thu_muc, width=54).pack(side='left', fill='x', expand=True)
        ttk.Button(hang, text='Chọn...', style='V3.TButton',
                  command=self._v3_anh_chon_thu_muc).pack(side='left', padx=(8, 0))
        ttk.Button(hang, text='Quét', style='V3Chinh.TButton',
                  command=self._v3_anh_quet).pack(side='left', padx=(8, 0))

        kTuy = self._v3_the(f, 'Tuỳ chọn xử lý')
        self.v3_anh_webp = tk.BooleanVar(value=True)
        self.v3_anh_doi_ten = tk.BooleanVar(value=True)
        self.v3_anh_alt = tk.BooleanVar(value=True)
        self.v3_anh_dai_dien = tk.BooleanVar(value=True)
        for bien, nhan in ((self.v3_anh_webp, 'Chuyển sang WebP (giảm dung lượng ~80%)'),
                           (self.v3_anh_doi_ten, 'Đổi tên file theo SEO (thay tên kiểu z724721...)'),
                           (self.v3_anh_alt, 'Tự sinh alt text từ tên sản phẩm'),
                           (self.v3_anh_dai_dien, 'Đặt ảnh đầu tiên làm ảnh đại diện')):
            ttk.Checkbutton(kTuy, text=nhan, variable=bien).pack(anchor='w')
        hang2 = ttk.Frame(kTuy, style='V3Card.TFrame')
        hang2.pack(fill='x', pady=(8, 0))
        ttk.Label(hang2, text='Chiều rộng tối đa (px):', style='V3CardMo.TLabel').pack(side='left')
        self.v3_anh_rong = tk.StringVar(value='1200')
        ttk.Entry(hang2, textvariable=self.v3_anh_rong, width=8).pack(side='left', padx=(8, 0))

        kKQ = self._v3_the(f, 'Kết quả quét — sửa mã hàng bằng cách bấm đúp vào dòng')
        cot = ('ten_file', 'ma_goc', 'tin_cay', 'dai_dien', 'ly_do')
        self.bang_anh = ttk.Treeview(kKQ, columns=cot, show='headings', height=13)
        for c_, nhan, rong in (('ten_file', 'Tên file', 240), ('ma_goc', 'Mã hàng', 150),
                               ('tin_cay', 'Tin cậy', 70), ('dai_dien', 'Ảnh 1', 55),
                               ('ly_do', 'Lý do ghép / ghi chú', 300)):
            self.bang_anh.heading(c_, text=nhan)
            self.bang_anh.column(c_, width=rong, anchor='w')
        self.bang_anh.pack(fill='both', expand=True)
        self.bang_anh.bind('<Double-1>', self._v3_anh_sua_dong)
        self.v3_anh_du_lieu = []

        self.tien_do_v3_anh = ttk.Progressbar(kKQ, style='V3.Horizontal.TProgressbar',
                                              mode='determinate')
        self.tien_do_v3_anh.pack(fill='x', pady=(10, 6))
        self.lb_v3_anh = ttk.Label(kKQ, text='Chưa quét', style='V3CardTieu.TLabel')
        self.lb_v3_anh.pack(anchor='w')

        hangNut = ttk.Frame(kKQ, style='V3Card.TFrame')
        hangNut.pack(fill='x', pady=(10, 0))
        ttk.Button(hangNut, text='Xem trước (không upload)', style='V3.TButton',
                  command=self._v3_anh_xem_truoc).pack(side='left')
        self.nut_v3_anh_upload = ttk.Button(hangNut, text='Upload lên WordPress',
                                            style='V3Chinh.TButton',
                                            command=self._v3_anh_upload)
        self.nut_v3_anh_upload.pack(side='left', padx=(10, 0))

    def _v3_anh_chon_thu_muc(self):
        d = filedialog.askdirectory(title='Chọn thư mục chứa ảnh sản phẩm')
        if d:
            self.v3_anh_thu_muc.set(d)

    def _v3_anh_quet(self):
        import anh_san_pham as ASP
        import db_phase2 as DB
        did = self._phase2_dataset_id_dang_chon()
        if not did:
            messagebox.showinfo('Chưa chọn dataset', 'Chọn dataset ở tab "Nhập dữ liệu" trước.')
            return
        con = self._con_phase2()
        try:
            rows = DB.liet_ke_san_pham(con, dataset_id=did)
        finally:
            con.close()
        kq = ASP.quet_thu_muc(self.v3_anh_thu_muc.get().strip(), rows)
        if not kq.get('ok'):
            messagebox.showwarning('Không quét được', kq.get('loi', ''))
            return
        self.v3_anh_du_lieu = kq['danh_sach']
        self._v3_anh_ve_bang()
        ghep = sum(1 for d in self.v3_anh_du_lieu if d['ma_goc'])
        tong = len(self.v3_anh_du_lieu)
        self.lb_v3_anh.config(
            text=f'Tìm thấy {tong} ảnh · ghép được {ghep} · cần gán tay {tong - ghep}')
        print(f'== [Ảnh] Quét {tong} ảnh, ghép được {ghep}, cần gán tay {tong - ghep} ==')

    def _v3_anh_ve_bang(self):
        for i in self.bang_anh.get_children():
            self.bang_anh.delete(i)
        for idx, d in enumerate(self.v3_anh_du_lieu):
            self.bang_anh.insert('', 'end', iid=str(idx), values=(
                d['ten_file'][:44], d['ma_goc'] or '— chưa gán —',
                d['do_tin_cay'], '★' if d.get('anh_dai_dien') else '',
                d['ly_do'][:60]))

    def _v3_anh_sua_dong(self, _e=None):
        """Bấm đúp để gán mã hàng bằng tay / bỏ chọn / đổi ảnh đại diện."""
        sel = self.bang_anh.selection()
        if not sel:
            return
        idx = int(sel[0])
        d = self.v3_anh_du_lieu[idx]
        from tkinter import simpledialog
        ma = simpledialog.askstring(
            'Gán mã hàng',
            f'Ảnh: {d["ten_file"]}\n\nNhập MÃ HÀNG cần gắn ảnh này.\n'
            f'Để TRỐNG = bỏ qua ảnh này.\n'
            f'Gõ dấu * ở cuối = đặt làm ảnh đại diện (VD: MBT3P250A2608*)',
            initialvalue=d['ma_goc'])
        if ma is None:
            return
        ma = ma.strip()
        d['anh_dai_dien'] = ma.endswith('*')
        ma = ma.rstrip('*').strip()
        d['ma_goc'] = ma
        d['chon'] = bool(ma)
        d['ly_do'] = 'Gán tay' if ma else 'Bỏ qua'
        d['do_tin_cay'] = 'tay' if ma else 'khong'
        if ma:
            import db_phase2 as DB
            con = self._con_phase2()
            try:
                for r in DB.liet_ke_san_pham(con, dataset_id=self._phase2_dataset_id_dang_chon()):
                    if str(r.get('ma_goc', '')).strip().lower() == ma.lower():
                        d['record_id'] = r['record_id']
                        d['ten_san_pham'] = r.get('ten_goc', '')
                        break
                else:
                    d['ly_do'] = 'CẢNH BÁO: không tìm thấy mã này trong dataset'
            finally:
                con.close()
        self._v3_anh_ve_bang()

    def _v3_anh_xem_truoc(self):
        """Xuất danh sách ghép ra Excel để soi kỹ trước khi upload."""
        import anh_san_pham as ASP
        if not self.v3_anh_du_lieu:
            messagebox.showinfo('Chưa có dữ liệu', 'Bấm Quét trước.')
            return
        duong_dan = filedialog.asksaveasfilename(
            defaultextension='.xlsx', initialfile='xem-truoc-anh.xlsx',
            filetypes=[('Excel', '*.xlsx')])
        if not duong_dan:
            return
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Ghep anh'
        ws.append(['Tên file', 'Dung lượng (KB)', 'Mã hàng', 'Tên sản phẩm',
                   'Độ tin cậy', 'Ảnh đại diện', 'Tên file SEO sẽ dùng', 'Lý do'])
        for d in self.v3_anh_du_lieu:
            ten_seo = ''
            if d['ma_goc']:
                ten_seo = ASP.ten_file_seo({'ten_goc': d.get('ten_san_pham', ''),
                                            'ma_goc': d['ma_goc']})
            ws.append([d['ten_file'], d['kich_thuoc_kb'], d['ma_goc'],
                       d.get('ten_san_pham', ''), d['do_tin_cay'],
                       'X' if d.get('anh_dai_dien') else '', ten_seo, d['ly_do']])
        wb.save(duong_dan)
        messagebox.showinfo('Đã xuất', f'Đã lưu: {duong_dan}\n\n'
                                       'Soi kỹ cột "Mã hàng" rồi quay lại bấm Upload.')

    def _v3_anh_upload(self):
        can_up = [d for d in self.v3_anh_du_lieu if d.get('chon') and d.get('ma_goc')]
        if not can_up:
            messagebox.showinfo('Không có ảnh nào', 'Chưa ảnh nào được ghép mã hàng.')
            return
        if not messagebox.askyesno(
                'Xác nhận upload',
                f'Sắp upload {len(can_up)} ảnh lên WordPress Media và gắn vào sản phẩm.\n\n'
                f'Ảnh sẽ được tối ưu trước khi upload. Tiếp tục?'):
            return
        self.nut_v3_anh_upload.config(state='disabled')
        try:
            rong = int(self.v3_anh_rong.get() or 1200)
        except ValueError:
            rong = 1200
        cfg_anh = {
            'rong': rong,
            'webp': self.v3_anh_webp.get(),
            'doi_ten': self.v3_anh_doi_ten.get(),
            'dung_alt': self.v3_anh_alt.get(),
            'gan_dai_dien': self.v3_anh_dai_dien.get(),
            'dataset_id': self._phase2_dataset_id_dang_chon(),
            'website': C.doc_website() or {},
        }
        self.chay_nen_phase2(lambda: self._v3_anh_upload_chay(can_up, cfg_anh))

    def _v3_anh_upload_chay(self, can_up, cfg_anh):
        import anh_san_pham as ASP
        import ai_wp_adapter as AWP
        import db_phase2 as DB

        rong = cfg_anh['rong']
        webp = cfg_anh['webp']
        doi_ten = cfg_anh['doi_ten']
        dung_alt = cfg_anh['dung_alt']
        gan_dai_dien = cfg_anh['gan_dai_dien']

        # gom ảnh theo mã hàng — 1 sản phẩm có thể nhiều ảnh
        theo_ma = {}
        for d in can_up:
            theo_ma.setdefault(d['ma_goc'], []).append(d)
        for ds in theo_ma.values():   # ảnh đại diện lên đầu
            ds.sort(key=lambda x: not x.get('anh_dai_dien'))

        con = self._con_phase2()
        did = cfg_anh['dataset_id']
        wc = cfg_anh['website']
        la_woo = wc.get('che_do_dang') == 'woo_product'
        tong = len(can_up)
        i = ok = loi = 0
        print(f'== [Ảnh] Bắt đầu upload {tong} ảnh cho {len(theo_ma)} sản phẩm ==')
        try:
            for ma, ds in theo_ma.items():
                media_ids = []
                for thu_tu, d in enumerate(ds, 1):
                    i += 1
                    if self.v3_dung_lai.is_set():
                        print(f'== [Ảnh] ĐÃ DỪNG — còn {tong - i + 1} ảnh chưa xử lý ==')
                        return
                    du_lieu, duoi = ASP.toi_uu_anh(d['duong_dan'], rong_toi_da=rong,
                                                   sang_webp=webp)
                    if du_lieu is None:
                        loi += 1
                        print(f'   [{i}/{tong}] LỖI tối ưu {d["ten_file"]}: {duoi}')
                        continue
                    row_gia = {'ten_goc': d.get('ten_san_pham', ''), 'ma_goc': ma}
                    ten_up = (ASP.ten_file_seo(row_gia, thu_tu, duoi) if doi_ten
                              else d['ten_file'])
                    alt = ASP.alt_text(row_gia, thu_tu) if dung_alt else ''
                    kq = AWP.upload_anh_media(du_lieu, ten_up, alt=alt, tieu_de=alt)
                    if kq.get('ok'):
                        ok += 1
                        media_ids.append(kq['id'])
                        print(f'   [{i}/{tong}] OK {ten_up} '
                             f'({d["kich_thuoc_kb"]}KB -> {len(du_lieu)//1024}KB)')
                    else:
                        loi += 1
                        print(f'   [{i}/{tong}] LỖI upload {ten_up}: {kq["loi"]}')
                    self.ui(lambda i=i, tong=tong, ok=ok, loi=loi:
                            (self.tien_do_v3_anh.config(value=i, maximum=max(tong, 1)),
                             self.lb_v3_anh.config(text=f'Đang upload {i}/{tong} — OK {ok}, lỗi {loi}')))

                # gắn vào sản phẩm nếu đã đăng
                if media_ids and gan_dai_dien:
                    bai = None
                    for d in ds:
                        if d.get('record_id'):
                            bai = DB.lay_bai_viet(con, did, d['record_id'],
                                                  wc.get('ma_site', 'site1'), 'chuan')
                            break
                    if bai and bai.get('wp_id'):
                        kq_gan = AWP.gan_anh_vao_san_pham(bai['wp_id'], media_ids, la_woo=la_woo)
                        print(f'   -> {ma}: {"đã gắn ảnh vào sản phẩm" if kq_gan.get("ok") else "LỖI gắn: " + kq_gan.get("loi", "")}')
                    else:
                        print(f'   -> {ma}: ảnh đã lên Media nhưng sản phẩm CHƯA ĐĂNG, '
                             f'chưa gắn được (đăng bài xong chạy lại bước này)')
        finally:
            con.close()
            self.ui(lambda: self.nut_v3_anh_upload.config(state='normal'))
        print(f'== [Ảnh] XONG: {ok} thành công, {loi} lỗi ==')

    def _v3_tab_8_enhance(self):
        """SONEALEO Ver 1.1 — tab Enhance: bật/tắt + cấu hình Serper key,
        đọc bởi vòng lặp sinh bài ở '_v3_bam_sinh_bai_that' (nếu bật, chèn
        insight cấu trúc vào ai_data TRƯỚC khi render_phase2.dung_bai_html
        chạy — không đụng bảng thông số, không đụng luồng Article Jobs
        (tab 7), CHƯA wiring — chỉ luồng chính tab 4).

        Tự chứa (self-contained) — không đụng doc_cau_hinh()/luu tab Ver1/2
        cũ, đọc/ghi riêng qua cauhinh.doc_serper()/luu_serper()."""
        import enhance as E

        f = self._v3_tab_cuon('8. Enhance')
        ttk.Label(f, text='Enhance — làm dày content bằng insight từ SERP', style='V3Tieu.TLabel'
                 ).pack(anchor='w', pady=(0, 4))
        ttk.Label(f, text='CHỈ rút góc nhìn/cấu trúc/câu hỏi từ top Google — TUYỆT ĐỐI không '
                          'rút số liệu kỹ thuật (2 lớp chặn: lọc số + Hard Block chạy lại lần '
                          'cuối). Bảng thông số không bị đụng, luôn 100% từ MASTER.',
                  style='V3Mo.TLabel', wraplength=900).pack(anchor='w', pady=(0, 14))

        kKey = self._v3_the(f, 'Serper.dev API key')
        hangK = ttk.Frame(kKey, style='V3Card.TFrame')
        hangK.pack(fill='x')
        self.v3_serper_key = tk.StringVar(value=C.doc_serper().get('api_key', ''))
        ttk.Entry(hangK, textvariable=self.v3_serper_key, width=50, show='*'
                 ).pack(side='left', fill='x', expand=True)
        ttk.Button(hangK, text='Lưu', style='V3.TButton', command=self._v3_luu_serper_key
                 ).pack(side='left', padx=(8, 0))
        ttk.Label(kKey, text='Lấy key free (2.500 query) tại serper.dev — không cần thẻ tín dụng.',
                  style='V3CardMo.TLabel').pack(anchor='w', pady=(6, 0))

        kBat = self._v3_the(f, 'Bật cho lần Sinh bài tiếp theo')
        self.v3_enhance_bat = tk.BooleanVar(value=False)
        ttk.Checkbutton(kBat, text='Bật Enhance khi Sinh bài ở tab "4. Sinh & Đăng" (chỉ luồng '
                                   'chính, CHƯA áp dụng cho Article Jobs)',
                       variable=self.v3_enhance_bat).pack(anchor='w')
        ttk.Label(kBat, text='Tắt = hành vi y hệt trước giờ, không gọi Serper/thêm insight gì cả.',
                  style='V3CardMo.TLabel').pack(anchor='w', pady=(4, 0))
        self.v3_enhance_cong_dong = tk.BooleanVar(value=False)
        ttk.Checkbutton(kBat, text='Đợt 4 — thêm nguồn cộng đồng/diễn đàn kỹ thuật (rủi ro cao hơn '
                                   'SERP thường, đã có lớp chặn từ khoá khiếu nại/sự cố, MẶC ĐỊNH TẮT)',
                       variable=self.v3_enhance_cong_dong).pack(anchor='w', pady=(8, 0))
        ttk.Label(kBat, text=f'Diễn đàn dùng: {", ".join(__import__("enhance").DANH_SACH_DIEN_DAN)} '
                             '— sửa enhance.DANH_SACH_DIEN_DAN nếu cần đổi danh sách.',
                  style='V3CardMo.TLabel').pack(anchor='w', pady=(4, 0))

        kTest = self._v3_the(f, 'Test thử 1 sản phẩm (không tốn Gemini, chỉ tốn 1 credit Serper)')
        ttk.Button(kTest, text='Test Enhance cho sản phẩm đang xem (tab 3)', style='V3Chinh.TButton',
                  command=self._v3_test_enhance).pack(anchor='w')
        self.txt_v3_enhance_ket_qua = tk.Text(kTest, height=14, wrap='word', font=('Consolas', 9))
        self.txt_v3_enhance_ket_qua.pack(fill='both', expand=True, pady=(10, 0))

        kBatch = self._v3_the(f, 'Chạy thử cho CẢ NHÓM đã chọn (Đợt 2 — mock ai_data, KHÔNG tốn '
                                 'Gemini viết bài, nhưng TỐN 1 credit Serper + 1 lượt gọi Gemini rút '
                                 'insight cho mỗi sản phẩm)')
        ttk.Label(kBatch, text='Dùng để xem trước Enhance chạy ổn trên cả nhóm không (đặc biệt: '
                              'chống lặp Đợt 1 có hoạt động đúng giữa nhiều SKU cùng nhóm không) '
                              'TRƯỚC KHI bật checkbox ở trên và chạy thật với Gemini viết bài đầy đủ.',
                  style='V3CardMo.TLabel', wraplength=900).pack(anchor='w', pady=(0, 10))
        self.tien_do_v3_enhance = ttk.Progressbar(kBatch, style='V3.Horizontal.TProgressbar',
                                                   mode='determinate')
        self.tien_do_v3_enhance.pack(fill='x', pady=(0, 6))
        self.lb_v3_enhance_tien_do = ttk.Label(kBatch, text='Chưa chạy', style='V3CardTieu.TLabel')
        self.lb_v3_enhance_tien_do.pack(anchor='w', pady=(0, 10))
        hangBatch = ttk.Frame(kBatch, style='V3Card.TFrame')
        hangBatch.pack(fill='x')
        self.nut_v3_enhance_batch = ttk.Button(hangBatch, text='Chạy Enhance cho nhóm đã chọn (tab 2)',
                                               style='V3Chinh.TButton', command=self._v3_enhance_batch_bam)
        self.nut_v3_enhance_batch.pack(side='left')
        self.v3_enhance_batch_dung = threading.Event()
        self.nut_v3_enhance_batch_dung = ttk.Button(hangBatch, text='⏹ Dừng', style='V3Dung.TButton',
                                                     command=self._v3_enhance_batch_force_stop,
                                                     state='disabled')
        self.nut_v3_enhance_batch_dung.pack(side='left', padx=(10, 0))

    def _v3_luu_serper_key(self):
        C.luu_serper(self.v3_serper_key.get().strip())
        messagebox.showinfo('Đã lưu', 'Đã lưu Serper API key.')

    def _v3_enhance_batch_force_stop(self):
        self.v3_enhance_batch_dung.set()
        self.nut_v3_enhance_batch_dung.config(state='disabled')
        print('== [Enhance batch] Đã nhấn Dừng — dừng sau khi xong sản phẩm đang xử lý... ==')

    def _v3_enhance_batch_cap_nhat_tien_do(self, da_xong, tong, ok, loi):
        self.tien_do_v3_enhance.config(value=da_xong, maximum=max(tong, 1))
        phan_tram = int(da_xong / tong * 100) if tong else 0
        self.lb_v3_enhance_tien_do.config(
            text=f'Đang chạy {da_xong}/{tong} ({phan_tram}%) — OK {ok}, lỗi {loi}')

    def _v3_enhance_batch_bam(self):
        """Đợt 2 — chạy Enhance (mock ai_data) cho TOÀN BỘ sản phẩm đang
        CHỌN (selected=1) ở tab '2. Sản phẩm', dùng chung dataset đang
        chọn. Chạy nền qua chay_nen_phase2() (không đụng thread của luồng
        Sinh bài chính — 2 cờ dừng riêng)."""
        import db_phase2 as DB
        did = self._phase2_dataset_id_dang_chon()
        if not did:
            messagebox.showinfo('Chưa chọn dataset', 'Chọn dataset ở khối "1. Nhập dữ liệu" trước.')
            return
        serper_key = self.v3_serper_key.get().strip() or C.doc_serper().get('api_key', '')
        if not serper_key:
            messagebox.showwarning('Chưa có Serper key', 'Nhập + Lưu Serper API key ở trên trước.')
            return
        cfg_gemini = C.doc_gemini()
        if not cfg_gemini.get('api_key') or not cfg_gemini.get('model'):
            messagebox.showwarning('Chưa cấu hình Gemini', 'Vào tab "1. Cấu hình" nhập API key Gemini trước '
                                   '(Enhance vẫn cần Gemini để rút insight, dù không viết bài).')
            return
        con = self._con_phase2()
        try:
            sp = DB.liet_ke_san_pham(con, dataset_id=did, chi_da_chon=True)
        finally:
            con.close()
        if not sp:
            messagebox.showinfo('Chưa chọn sản phẩm', 'Bấm đúp ở bảng "2. Sản phẩm" để chọn ít nhất 1 '
                                'sản phẩm trước.')
            return
        if not messagebox.askyesno(
                'Chạy Enhance hàng loạt (mock)',
                f'Sắp chạy Enhance cho {len(sp)} sản phẩm đã chọn.\n\n'
                f'Không tốn Gemini viết bài (dùng ai_data mock), nhưng TỐN:\n'
                f'  - {len(sp)} credit Serper\n'
                f'  - {len(sp)} lượt gọi Gemini (rút insight, nhẹ hơn viết bài nhiều)\n\n'
                f'Tiếp tục?'):
            return

        self.v3_enhance_batch_dung.clear()
        self.nut_v3_enhance_batch.config(state='disabled')
        self.nut_v3_enhance_batch_dung.config(state='normal')
        self.tien_do_v3_enhance.config(value=0, maximum=len(sp))
        self.lb_v3_enhance_tien_do.config(text='Đang chuẩn bị...')
        bat_nguon_cong_dong = self.v3_enhance_cong_dong.get()
        self.chay_nen_phase2(lambda: self._v3_enhance_batch_viec_chay(
            did, sp, serper_key, cfg_gemini, bat_nguon_cong_dong))

    def _v3_enhance_batch_viec_chay(self, did, sp, serper_key, cfg_gemini, bat_nguon_cong_dong):
        import db_phase2 as DB
        import enhance as E
        import ai_wp_adapter as AWP

        con = self._con_phase2()
        tong = len(sp)
        ok = loi = 0
        tong_bo_so = 0
        tong_canh_bao = 0
        try:
            for i, row_tom_tat in enumerate(sp, 1):
                if self.v3_enhance_batch_dung.is_set():
                    print(f'== [Enhance batch] Đã dừng theo yêu cầu, còn lại {tong - i + 1} sản phẩm chưa chạy ==')
                    break
                rid = row_tom_tat['record_id']
                row = DB.lay_san_pham(con, did, rid)
                if not row:
                    loi += 1
                    print(f'  [{i}/{tong}] LỖI: không đọc được record {rid}')
                    self.ui(lambda i=i, tong=tong, ok=ok, loi=loi: self._v3_enhance_batch_cap_nhat_tien_do(i, tong, ok, loi))
                    continue
                ten_loai = row.get('nhom_nguon') or row.get('thuong_hieu') or row.get('ten_goc', '')[:40]
                ai_data_mock, _u = AWP.goi_ai_mock(row, mau='chuan')
                print(f'== [{i}/{tong}] Enhance (mock) cho {rid} — nhóm "{ten_loai}" ==')
                kq = E.enhance_1_san_pham(row, ai_data_mock, ten_loai, serper_key,
                                          cfg_gemini.get('model', ''), cfg_gemini.get('api_key', ''), con=con,
                                          bat_nguon_cong_dong=bat_nguon_cong_dong)
                if kq.get('ok'):
                    ok += 1
                    tong_bo_so += kq.get('so_y_da_bo_vi_co_so', 0)
                    if kq.get('canh_bao'):
                        tong_canh_bao += 1
                        print(f'   CẢNH BÁO Hard Block: {kq["canh_bao"]}')
                    else:
                        print(f'   OK — {kq["so_url_fetch_duoc"]} URL, bỏ {kq["so_y_da_bo_vi_co_so"]} ý có số.')
                else:
                    loi += 1
                    print(f'   LỖI: {kq["loi"]}')
                self.ui(lambda i=i, tong=tong, ok=ok, loi=loi: self._v3_enhance_batch_cap_nhat_tien_do(i, tong, ok, loi))
        finally:
            con.close()
            self.ui(lambda: (self.nut_v3_enhance_batch.config(state='normal'),
                             self.nut_v3_enhance_batch_dung.config(state='disabled')))
        print(f'== [Enhance batch] Xong: {ok}/{tong} OK, {loi} lỗi, '
             f'{tong_bo_so} ý có số bị bộ lọc bỏ tổng cộng, {tong_canh_bao} sản phẩm bị Hard Block cảnh báo ==')

    def _v3_test_enhance(self):
        """Test tay 1 record — DÙNG ai_data MOCK (không gọi Gemini thật),
        chỉ để xác nhận nhánh Serper + lọc số + Hard Block chạy đúng trên
        record thật đang chọn, không tốn quota Gemini cho việc test."""
        import enhance as E
        import ai_wp_adapter as AWP
        import json

        if not self.v3_active_record_id:
            messagebox.showinfo('Chưa chọn sản phẩm', 'Bấm đúp 1 dòng ở tab "2. Sản phẩm" trước.')
            return
        did = self._phase2_dataset_id_dang_chon()
        con = self._con_phase2()
        try:
            import db_phase2 as DB
            row = DB.lay_san_pham(con, did, self.v3_active_record_id)
            if not row:
                messagebox.showwarning('Không tìm thấy', 'Không lấy được dữ liệu sản phẩm này.')
                return

            serper_key = self.v3_serper_key.get().strip() or C.doc_serper().get('api_key', '')
            ten_loai = row.get('nhom_nguon') or row.get('thuong_hieu') or row.get('ten_goc', '')[:40]
            ai_data_mock, _usage_mock = AWP.goi_ai_mock(row, mau='chuan')

            self.txt_v3_enhance_ket_qua.delete('1.0', 'end')
            self.txt_v3_enhance_ket_qua.insert('end', f'Đang test Enhance cho: {ten_loai}...\n')
            self.update_idletasks()

            cfg_gemini = C.doc_gemini()
            kq = E.enhance_1_san_pham(row, ai_data_mock, ten_loai, serper_key,
                                      cfg_gemini.get('model', ''), cfg_gemini.get('api_key', ''), con=con,
                                      bat_nguon_cong_dong=self.v3_enhance_cong_dong.get())
        finally:
            con.close()

        self.txt_v3_enhance_ket_qua.delete('1.0', 'end')
        if not kq.get('ok'):
            self.txt_v3_enhance_ket_qua.insert('end', f'LỖI: {kq["loi"]}\n')
            return
        self.txt_v3_enhance_ket_qua.insert('end', f'OK — fetch được {kq["so_url_fetch_duoc"]} URL, '
                                           f'bỏ {kq["so_y_da_bo_vi_co_so"]} ý có số lọt qua.\n')
        if kq['canh_bao']:
            self.txt_v3_enhance_ket_qua.insert('end', f'\nCẢNH BÁO (Hard Block bắt số lạ):\n{kq["canh_bao"]}\n')
        else:
            self.txt_v3_enhance_ket_qua.insert('end', '\nHard Block lớp cuối: sạch, không có số lạ.\n')
        self.txt_v3_enhance_ket_qua.insert('end', '\n--- Insight rút được ---\n')
        self.txt_v3_enhance_ket_qua.insert('end', json.dumps(kq['insight_dung'], ensure_ascii=False, indent=2))

    def _v3_tab_7_article_jobs(self):
        """Ver 3.9 — 1 sản phẩm có thể có NHIỀU bài (job), mỗi job chọn
        outline riêng, đăng riêng, trạng thái riêng. Tab RIÊNG (không chung
        với tab 4) để không đụng luồng 'Đăng Draft lên WordPress' (1
        bài/sản phẩm) đã test kỹ từ Ver 3.7 — 2 luồng độc lập hoàn toàn,
        dùng nút/cờ Dừng riêng."""
        import prompts_phase2 as PR

        f = self._v3_tab_cuon('7. Article Jobs')
        ttk.Label(f, text='Article Jobs — nhiều bài cho 1 sản phẩm', style='Dam.TLabel').pack(anchor='w')
        ttk.Label(f, text='Mặc định 1 sản phẩm = 1 job (1 bài). Cần nhiều bài/góc nhìn khác nhau cho '
                          'cùng 1 sản phẩm thì bấm "+ Thêm job" và chọn outline khác cho job đó.',
                  style='V3Mo.TLabel', wraplength=780, justify='left').pack(anchor='w', pady=(2, 12))

        hangTao = ttk.Frame(f)
        hangTao.pack(fill='x')
        ttk.Button(hangTao, text='Tạo job mặc định cho sản phẩm đã chọn (tab 3)',
                  command=self._jobs_tao_mac_dinh).pack(side='left')
        ttk.Button(hangTao, text='Nạp lại danh sách', command=self._jobs_nap).pack(side='left', padx=8)
        self.lb_jobs_dem = ttk.Label(hangTao, text='', style='V3Mo.TLabel')
        self.lb_jobs_dem.pack(side='left', padx=(16, 0))

        cot = ('record', 'outline', 'seq', 'trang_thai', 'wp_id', 'wp_url', 'loi')
        self.bang_jobs = ttk.Treeview(f, columns=cot, show='headings', height=12)
        for c, n, w in [('record', 'Sản phẩm', 260), ('outline', 'Outline', 170), ('seq', '#', 30),
                        ('trang_thai', 'Trạng thái', 90), ('wp_id', 'WP ID', 60),
                        ('wp_url', 'URL', 220), ('loi', 'Lỗi', 200)]:
            self.bang_jobs.heading(c, text=n)
            self.bang_jobs.column(c, width=w, anchor='w')
        self.bang_jobs.pack(fill='both', expand=True, pady=(8, 0))
        self.bang_jobs.tag_configure('SUCCESS', foreground=V3_OK)
        self.bang_jobs.tag_configure('ERROR', foreground=V3_ERR)
        self._jobs_map = {}   # iid Treeview -> job_id thật

        hangSua = ttk.Frame(f)
        hangSua.pack(fill='x', pady=(10, 0))
        ttk.Label(hangSua, text='Outline cho job đã chọn:', style='Dam.TLabel').pack(side='left')
        self.v_jobs_outline = tk.StringVar()
        self._jobs_outline_map = {f'{cfg["nhan_outline"]} ({oid})': oid
                                  for oid, cfg in PR.OUTLINE_NOI_DUNG.items()}
        self.cb_jobs_outline = ttk.Combobox(hangSua, textvariable=self.v_jobs_outline, width=38,
                                            state='readonly', values=list(self._jobs_outline_map.keys()))
        self.cb_jobs_outline.pack(side='left', padx=(8, 8))
        ttk.Button(hangSua, text='Đổi outline (job chưa chạy)', command=self._jobs_doi_outline
                  ).pack(side='left')

        hangNut = ttk.Frame(f)
        hangNut.pack(fill='x', pady=(10, 0))
        ttk.Button(hangNut, text='+ Thêm job cho sản phẩm của dòng đang chọn',
                  command=self._jobs_them).pack(side='left')
        ttk.Button(hangNut, text='- Xoá job đã chọn (chỉ khi chưa chạy)',
                  command=self._jobs_xoa).pack(side='left', padx=8)

        kChay = self._v3_the(f, 'Đăng toàn bộ job PENDING')
        self.tien_do_jobs = ttk.Progressbar(kChay, style='V3.Horizontal.TProgressbar', mode='determinate')
        self.tien_do_jobs.pack(fill='x', pady=(0, 6))
        self.lb_jobs_tien_do = ttk.Label(kChay, text='Chưa chạy', style='V3CardTieu.TLabel')
        self.lb_jobs_tien_do.pack(anchor='w', pady=(0, 10))
        hangChayJobs = ttk.Frame(kChay, style='V3Card.TFrame')
        hangChayJobs.pack(fill='x')
        self.nut_jobs_dang = ttk.Button(hangChayJobs, text='Đăng Draft THẬT toàn bộ job PENDING',
                                        style='V3Chinh.TButton', command=self._jobs_dang_that)
        self.nut_jobs_dang.pack(side='left')
        self.nut_jobs_dung = ttk.Button(hangChayJobs, text='⏹ Dừng khẩn cấp (Force Stop)',
                                        style='V3Dung.TButton', command=self._jobs_force_stop,
                                        state='disabled')
        self.nut_jobs_dung.pack(side='left', padx=(10, 0))
        ttk.Label(kChay, text='Luồng RIÊNG, độc lập với nút "Đăng Draft lên WordPress" ở tab 4 — '
                             'chạy job nào không đụng tới bài đã đăng qua tab 4 và ngược lại. '
                             'Chỉ chạy chế độ THẬT (Gemini + WordPress thật) — job không có chế độ Mock.',
                  style='V3CardMo.TLabel', wraplength=1000).pack(anchor='w', pady=(8, 0))

    def _jobs_tao_mac_dinh(self):
        import db_phase2 as DB
        did = self._phase2_dataset_id_dang_chon()
        if not did:
            messagebox.showinfo('Chưa chọn dataset', 'Chọn dataset ở khối "2. Nhập dữ liệu" trước.')
            return
        wc = C.doc_website()
        if not wc:
            messagebox.showwarning('Chưa cấu hình website',
                                   'Vào tab "1. Cấu hình" nhập website trước — job cần biết đăng lên site nào.')
            return
        site = wc['site_key']
        mau = self._phase2_mau_dang_chon()
        con = self._con_phase2()
        try:
            sp = DB.liet_ke_san_pham(con, dataset_id=did, chi_da_chon=True)
            if not sp:
                messagebox.showinfo('Chưa chọn sản phẩm',
                                    'Bấm đúp ở bảng "2. Sản phẩm" (tab 3) để chọn ít nhất 1 sản phẩm trước.')
                return
            record_ids = [r['record_id'] for r in sp]
            tao_moi = DB.dam_bao_job_mac_dinh(con, did, record_ids, site, mau)
        finally:
            con.close()
        print(f'== Đã tạo {len(tao_moi)} job mặc định mới ({len(record_ids) - len(tao_moi)} '
             f'sản phẩm đã có job từ trước, không tạo trùng) ==')
        self._jobs_nap()

    def _jobs_nap(self):
        import db_phase2 as DB
        did = self._phase2_dataset_id_dang_chon()
        self.bang_jobs.delete(*self.bang_jobs.get_children())
        self._jobs_map = {}
        if not did:
            self.lb_jobs_dem.config(text='')
            return
        con = self._con_phase2()
        try:
            jobs = DB.liet_ke_jobs(con, dataset_id=did)
            ten_cache = {}
            for j in jobs:
                if j['record_id'] not in ten_cache:
                    sp = DB.lay_san_pham(con, did, j['record_id'])
                    ten_cache[j['record_id']] = (sp.get('ten_goc', j['record_id']) if sp else j['record_id'])
        finally:
            con.close()
        dem = {'PENDING': 0, 'SUCCESS': 0, 'ERROR': 0}
        for j in jobs:
            dem[j['trang_thai']] = dem.get(j['trang_thai'], 0) + 1
            nhan_outline = self._jobs_outline_map_nguoc().get(j['outline_id'], j['outline_id'])
            iid = self.bang_jobs.insert('', 'end', values=(
                ten_cache.get(j['record_id'], j['record_id']), nhan_outline, j['sequence'],
                j['trang_thai'], j['wp_id'] or '', j['wp_url'] or '', j['loi'] or ''),
                tags=(j['trang_thai'],))
            self._jobs_map[iid] = j['job_id']
        self.lb_jobs_dem.config(
            text=f'Tổng {len(jobs)} job — PENDING {dem.get("PENDING",0)}, '
                f'SUCCESS {dem.get("SUCCESS",0)}, ERROR {dem.get("ERROR",0)}')

    def _jobs_outline_map_nguoc(self):
        return {v: k for k, v in self._jobs_outline_map.items()}

    def _jobs_job_dang_chon(self):
        import db_phase2 as DB
        iid = self.bang_jobs.focus()
        job_id = self._jobs_map.get(iid)
        if not job_id:
            messagebox.showinfo('Chưa chọn', 'Bấm chọn 1 dòng job trong bảng trước.')
            return None
        con = self._con_phase2()
        try:
            return DB.lay_job(con, job_id)
        finally:
            con.close()

    def _jobs_doi_outline(self):
        import db_phase2 as DB
        job = self._jobs_job_dang_chon()
        if not job:
            return
        oid_moi = self._jobs_outline_map.get(self.v_jobs_outline.get())
        if not oid_moi:
            messagebox.showinfo('Chưa chọn outline', 'Chọn 1 outline trong dropdown trước.')
            return
        con = self._con_phase2()
        try:
            ok = DB.doi_outline_job(con, job['job_id'], oid_moi)
        finally:
            con.close()
        if not ok:
            messagebox.showwarning('Không đổi được',
                                   f'Job này đang ở trạng thái "{job["trang_thai"]}" — chỉ đổi outline '
                                   f'được khi job còn PENDING (chưa chạy).')
        self._jobs_nap()

    def _jobs_them(self):
        import db_phase2 as DB
        job = self._jobs_job_dang_chon()
        if not job:
            return
        oid_moi = self._jobs_outline_map.get(self.v_jobs_outline.get()) or job['outline_id']
        con = self._con_phase2()
        try:
            job_id_moi = DB.tao_job(con, job['dataset_id'], job['record_id'], job['site'], job['mau'], oid_moi)
        finally:
            con.close()
        print(f'== Đã thêm job mới {job_id_moi} cho record {job["record_id"]} ==')
        self._jobs_nap()

    def _jobs_xoa(self):
        import db_phase2 as DB
        job = self._jobs_job_dang_chon()
        if not job:
            return
        if not messagebox.askyesno('Xoá job', f'Xoá job #{job["sequence"]} của sản phẩm này? '
                                              f'(chỉ xoá được nếu job chưa chạy)'):
            return
        con = self._con_phase2()
        try:
            ok = DB.xoa_job(con, job['job_id'])
        finally:
            con.close()
        if not ok:
            messagebox.showwarning('Không xoá được',
                                   f'Job này đang ở trạng thái "{job["trang_thai"]}" — chỉ xoá được job PENDING.')
        self._jobs_nap()

    def _jobs_force_stop(self):
        self.jobs_dung_lai.set()
        self.nut_jobs_dung.config(state='disabled')
        print('== Article Jobs: đã nhấn Dừng khẩn cấp — dừng sau khi xong job đang xử lý... ==')

    def _jobs_dang_that(self):
        """Ver 3.9 REQ-POST-01: Sinh & Đăng đọc TOÀN BỘ article_jobs PENDING
        của dataset đang chọn, đăng THẬT tuần tự — không giới hạn 1 job/lần
        như luồng record cũ."""
        import db_phase2 as DB
        did = self._phase2_dataset_id_dang_chon()
        if not did:
            messagebox.showinfo('Chưa chọn dataset', 'Chọn dataset ở khối "2. Nhập dữ liệu" trước.')
            return
        wc = C.doc_website()
        if not wc:
            messagebox.showwarning('Chưa cấu hình website', 'Vào tab "1. Cấu hình" nhập website trước.')
            return
        gc = C.doc_gemini()
        if not gc['api_key'] or not gc['model']:
            messagebox.showwarning('Chưa cấu hình AI', 'Vào tab "1. Cấu hình" nhập API key Gemini trước.')
            return
        con = self._con_phase2()
        try:
            jobs = DB.liet_ke_jobs(con, dataset_id=did, trang_thai='PENDING')
        finally:
            con.close()
        if not jobs:
            messagebox.showinfo('Không có job', 'Không có job nào ở trạng thái PENDING để chạy. '
                                                'Bấm "Tạo job mặc định" trước.')
            return
        if not messagebox.askyesno(
                'Đăng Draft THẬT toàn bộ Article Jobs',
                f'Sắp gọi Gemini THẬT rồi đăng bài THẬT (Draft, KHÔNG Publish) cho {len(jobs)} job.\n\n'
                f'Việc này tốn quota Gemini thật. Tiếp tục?'):
            return
        self.nut_jobs_dang.config(state='disabled')
        self.nut_jobs_dung.config(state='normal')
        self.jobs_dung_lai.clear()
        self.tien_do_jobs.config(value=0, maximum=max(len(jobs), 1))
        self.lb_jobs_tien_do.config(text='Bắt đầu...')
        danh_sach_thu = self._v3_danh_sach_key_model_du_phong(gc)
        nghi_giua_bai = self._v3_nghi_giua_bai_giay()   # Ver 5.1
        self.chay_nen_phase2(
            lambda: self._jobs_viec_dang_hang_loat(jobs, danh_sach_thu, wc, nghi_giua_bai))

    def _jobs_viec_dang_hang_loat(self, jobs, danh_sach_thu, wc, nghi_giua_bai=0.0):
        """Ver 3.9 — vòng lặp qua article_jobs (KHÔNG phải record). Mỗi job
        override outline_id riêng của record trước khi dựng prompt/render
        (row['outline_id'] = job['outline_id']) -> job khác outline thì
        prompt/FAQ/schema đều theo đúng outline của JOB đó, không phải
        outline mặc định của sản phẩm. Job thứ 2 trở đi của cùng 1 record
        được gắn hậu tố slug riêng (hau_to_slug) để không đè slug/bài của
        job khác — job đầu tiên (sequence=1) giữ NGUYÊN slug như luồng cũ,
        không phá bài đã đăng thật từ trước. Mỗi job bọc try/except riêng
        (bài học từ Bug 1 vá ở Ver 3.7.1 — áp dụng ngay từ đầu, không đợi
        review lần 2 mới vá)."""
        import ai_wp_adapter as AWP
        import render_phase2 as R
        import db_phase2 as DB

        site_cfg = self._v3_site_cfg()
        con = self._con_phase2()
        tong = len(jobs)
        ok, loi, bi_dung = 0, 0, False
        thong_bao = 'Batch Jobs dừng bất thường — xem console để biết chi tiết.'
        try:
            self.ui(lambda: self._jobs_cap_nhat_tien_do(0, tong, 0, 0))
            for i, job in enumerate(jobs, 1):
                if self.jobs_dung_lai.is_set():
                    bi_dung = True
                    print(f'== Article Jobs: đã dừng theo yêu cầu, còn lại {tong - i + 1} job chưa chạy ==')
                    break
                if i > 1 and nghi_giua_bai > 0:   # Ver 3.9 — wait cho phép Force Stop ngắt ngay
                    if self.jobs_dung_lai.wait(nghi_giua_bai):
                        bi_dung = True
                        print(f'== Article Jobs: đã dừng trong lúc nghỉ, còn lại {tong - i + 1} job chưa chạy ==')
                        break

                job_id = job['job_id']
                t0 = time.time()
                try:
                    row_goc = DB.lay_san_pham(con, job['dataset_id'], job['record_id'])
                    if row_goc is None:
                        raise ValueError(f'Không tìm thấy sản phẩm gốc cho job {job_id} (dữ liệu có thể đã bị xoá).')
                    row = dict(row_goc)
                    row['outline_id'] = job['outline_id']   # job có thể dùng outline KHÁC outline mặc định của record

                    cung_dong = DB.tim_san_pham_cung_dong(con, job['dataset_id'], job['record_id'], site=job['site'])   # Ver 5.0
                    row_ai = dict(row, **R.tinh_delta_context(row, cung_dong))
                    print(f'== [{i}/{tong}] Job {job_id}: gọi Gemini thật (outline={job["outline_id"]}, '
                         f'model chính={danh_sach_thu[0][1]}, {len(danh_sach_thu)} cặp key/model sẵn sàng thử) ==')
                    kq_ai, vi_pham = AWP.goi_ai_co_du_phong(row_ai, job['mau'], danh_sach_thu, site_cfg=site_cfg)
                    if not kq_ai['ok']:
                        loi += 1
                        DB.cap_nhat_job(con, job_id, trang_thai='ERROR', loi=kq_ai['loi'],
                                       thoi_luong_giay=time.time() - t0)
                        print(f'   LỖI (đã thử {kq_ai.get("da_thu", "?")} cặp key/model): {kq_ai["loi"]}')
                        for dong in kq_ai.get('lich_su', []):
                            print(f'     - {dong}')
                        self.ui(lambda i=i, tong=tong, ok=ok, loi=loi: self._jobs_cap_nhat_tien_do(i, tong, ok, loi))
                        continue
                    ai_data = kq_ai['data']
                    if kq_ai.get('da_thu', 1) > 1:
                        print(f'   (thành công sau khi đổi cặp key/model, thử lần {kq_ai["da_thu"]})')
                    if kq_ai.get('faq_bi_bo'):
                        print('   (đã bỏ FAQ vì nội dung bất thường — bài vẫn đăng bình thường không có FAQ)')

                    hau_to = f'b{job["sequence"]}' if job['sequence'] > 1 else ''
                    lien_quan = DB.tim_san_pham_lien_quan(con, job['dataset_id'], job['record_id'], job['site'])
                    bai = R.dung_bai_html(row, ai_data, site_cfg, mau=job['mau'], hau_to_slug=hau_to,
                                          san_pham_lien_quan=lien_quan, cung_dong=cung_dong)
                    kq_wp = AWP.dang_wp_that(job['dataset_id'], job['record_id'], job['site'], job['mau'],
                                             bai['title'], bai['slug'], bai['html'],
                                             ai_data.get('meta_description', ''),
                                             da_co_wp_id=job.get('wp_id'))
                    if not kq_wp['ok']:
                        loi += 1
                        DB.cap_nhat_job(con, job_id, trang_thai='ERROR', loi=kq_wp['loi'],
                                       thoi_luong_giay=kq_wp.get('thoi_luong_giay', time.time() - t0))
                        print(f'   LỖI WordPress: {kq_wp["loi"]}')
                        self.ui(lambda i=i, tong=tong, ok=ok, loi=loi: self._jobs_cap_nhat_tien_do(i, tong, ok, loi))
                        continue

                    ok += 1
                    ngay = datetime.now(timezone.utc).isoformat()
                    thoi_luong = time.time() - t0
                    DB.cap_nhat_job(con, job_id, trang_thai='SUCCESS', slug=bai['slug'], title=bai['title'],
                                   meta_description=bai['meta_description'], html=bai['html'],
                                   wp_id=str(kq_wp['wp_id']), wp_url=kq_wp['wp_url'], ngay_dang=ngay,
                                   thoi_luong_giay=thoi_luong)
                    print(f'   [{i}/{tong}] THÀNH CÔNG — WP ID={kq_wp["wp_id"]}, {thoi_luong:.1f}s')
                    self.ui(lambda i=i, tong=tong, ok=ok, loi=loi: self._jobs_cap_nhat_tien_do(i, tong, ok, loi))
                except Exception as e:
                    loi += 1
                    print(f'   LỖI KHÔNG LƯỜNG TRƯỚC ({type(e).__name__}): {e}')
                    try:
                        DB.cap_nhat_job(con, job_id, trang_thai='ERROR',
                                       loi=f'Lỗi không lường trước: {type(e).__name__}: {e}',
                                       thoi_luong_giay=time.time() - t0)
                    except Exception as e2:
                        print(f'   (không ghi được lỗi vào DB: {e2}) — vẫn tiếp tục job kế')
                    self.ui(lambda i=i, tong=tong, ok=ok, loi=loi: self._jobs_cap_nhat_tien_do(i, tong, ok, loi))

            if not bi_dung:
                print(f'== Article Jobs xong: {ok} thành công, {loi} lỗi ==')
            thong_bao = (f'Đã dừng ở {ok + loi}/{tong} (thành công {ok}, lỗi {loi})' if bi_dung
                        else f'Xong: {ok}/{tong} job thành công, {loi} lỗi')
        finally:
            con.close()
            self.ui(self._jobs_nap)
            self.ui(self._v3_nap_dashboard)
            self.ui(lambda: self._jobs_ket_thuc_chay(thong_bao))

    def _jobs_cap_nhat_tien_do(self, da_xong, tong, ok, loi):
        self.tien_do_jobs.config(value=da_xong, maximum=max(tong, 1))
        phan_tram = int(da_xong / tong * 100) if tong else 0
        self.lb_jobs_tien_do.config(text=f'Đang chạy {da_xong}/{tong} ({phan_tram}%) — thành công {ok}, lỗi {loi}')

    def _jobs_ket_thuc_chay(self, thong_bao):
        self.nut_jobs_dang.config(state='normal')
        self.nut_jobs_dung.config(state='disabled')
        self.lb_jobs_tien_do.config(text=thong_bao)

    def _v3_focus_tim_dashboard(self, _e=None):
        self.o_v3_dash_tim.focus_set()
        self.o_v3_dash_tim.selection_range(0, 'end')
        return 'break'

    def _v3_sort_dashboard(self, cot):
        if self._v3_dash_sort_col == cot:
            self._v3_dash_sort_desc = not self._v3_dash_sort_desc
        else:
            self._v3_dash_sort_col, self._v3_dash_sort_desc = cot, False
        self._v3_nap_dashboard()

    def _v3_chon_dashboard(self, _e=None):
        iid = self.bang_phase2_dash.focus()
        if not iid:
            return
        try:
            n = self.bang_phase2_dash.index(iid) + 1
        except Exception:
            n = 0
        self.lb_v3_dash_dong.config(text=f'dòng {n}/{getattr(self, "_v3_dash_total", len(self._v3_dash_rows))}')

    def _v3_xem_loi_chi_tiet(self):
        iid = self.bang_phase2_dash.focus()
        d = self._v3_dash_iid_map.get(iid) if iid else None
        if not d:
            messagebox.showinfo('Lỗi', 'Chọn một dòng trước.')
            return
        loi = str(d.get('loi') or '').strip()
        if not loi:
            messagebox.showinfo('Lỗi', 'Dòng này không có nội dung lỗi.')
            return
        messagebox.showinfo('Chi tiết lỗi', loi)

    def _v3_dang_lai_bai_loi_da_chon(self):
        """Ver 4.4 C6 — retry đúng các dòng lỗi đang chọn trên dashboard.

        Tái dùng nguyên worker đăng thật hiện có; không sửa Hard Block/anti-dup.
        Chỉ nhận dòng site hiện tại, trạng thái `loi`, rồi nhóm theo mẫu.
        """
        iids = list(self.bang_phase2_dash.selection())
        ds = [self._v3_dash_iid_map[i] for i in iids if i in self._v3_dash_iid_map]
        ds = [d for d in ds if d.get('trang_thai') == 'loi']
        if not ds:
            messagebox.showinfo('Đăng lại bài lỗi', 'Chọn một hoặc nhiều dòng có trạng thái lỗi trước.')
            return
        wc = C.doc_website()
        if not wc:
            messagebox.showwarning('Đăng lại bài lỗi', 'Chưa cấu hình WordPress.')
            return
        ds = [d for d in ds if d.get('site') == wc.get('site_key')]
        if not ds:
            messagebox.showwarning('Đăng lại bài lỗi', 'Các dòng đã chọn không thuộc website đang cấu hình.')
            return
        gc = C.doc_gemini()
        if not gc.get('api_key') or not gc.get('model'):
            messagebox.showwarning('Đăng lại bài lỗi', 'Chưa cấu hình Gemini.')
            return
        if not messagebox.askyesno('Đăng lại bài lỗi',
                                   f'Đăng lại {len(ds)} bài lỗi đã chọn lên WordPress thật ở trạng thái Draft?'):
            return

        import db_phase2 as DB
        con = self._con_phase2()
        try:
            cache = {}
            rows_theo_mau = {}
            for d in ds:
                did = d['dataset_id']
                if did not in cache:
                    cache[did] = {r['record_id']: r for r in DB.liet_ke_san_pham(con, dataset_id=did)}
                row = cache[did].get(d['record_id'])
                if row:
                    rows_theo_mau.setdefault(d.get('mau') or 'chuan', []).append(row)
        finally:
            con.close()
        if not rows_theo_mau:
            messagebox.showerror('Đăng lại bài lỗi', 'Không tìm lại được record nguồn tương ứng.')
            return

        danh_sach_thu = self._v3_danh_sach_key_model_du_phong(gc)
        enhance_cfg = {
            'bat': bool(getattr(self, 'v3_enhance_bat', None) and self.v3_enhance_bat.get()),
            'serper_key': self.v3_serper_key.get().strip() if hasattr(self, 'v3_serper_key') else '',
            'cong_dong': bool(getattr(self, 'v3_enhance_cong_dong', None) and self.v3_enhance_cong_dong.get()),
        }
        site_cfg = self._v3_site_cfg()
        image_root = self._tab_anh_37.v_goc.get().strip() if getattr(self, '_tab_anh_37', None) else ''
        self.v3_dung_lai.clear()
        self.nut_v3_dung.config(state='normal')

        def viec():
            for mau, rows in rows_theo_mau.items():
                if self.v3_dung_lai.is_set():
                    break
                self._v3_viec_dang_draft_that_hang_loat(rows, mau, danh_sach_thu, wc, 0.0,
                                                       False, enhance_cfg, site_cfg, image_root)
        self.chay_nen_phase2(viec)

    def _v3_nap_dashboard(self):
        import db_phase2 as DB
        import workspace_anh as WS
        con = self._con_phase2()
        try:
            ds_list = DB.liet_ke_dataset(con)
            gia_tri_ds = ['(tất cả)'] + [d['dataset_id'] for d in ds_list]
            if list(self.cb_v3_dash_dataset['values']) != gia_tri_ds:
                self.cb_v3_dash_dataset['values'] = gia_tri_ds

            wc_hien_tai = C.doc_website()
            gia_tri_site_loc = ['(tất cả)'] + ([wc_hien_tai['ten'] or wc_hien_tai['url']] if wc_hien_tai else [])
            if list(self.cb_v3_dash_site['values']) != gia_tri_site_loc:
                self.cb_v3_dash_site['values'] = gia_tri_site_loc

            did = self.v3_dash_dataset.get()
            did = None if did in ('', '(tất cả)') else did
            site_hien_thi_loc = self.v_phase2_dash_site.get()
            site = None if site_hien_thi_loc in ('', '(tất cả)') else (
                wc_hien_tai['site_key'] if wc_hien_tai else None)
            trang_thai_ui = self.v3_dash_trang_thai.get()
            loc_chua_chay = (trang_thai_ui == 'CHƯA CHẠY')
            trang_thai = None if trang_thai_ui in ('', '(tất cả)', 'CHƯA CHẠY') else trang_thai_ui

            dash = DB.dashboard(con, dataset_id=did, site=site, trang_thai=trang_thai)
            mau_loc = self.v3_dash_mau.get()
            if mau_loc and mau_loc != '(tất cả)':
                dash = [d for d in dash if d['mau'] == mau_loc]

            ten_cache, row_cache = {}, {}
            for d in dash:
                if d['dataset_id'] not in row_cache:
                    sp_list = DB.liet_ke_san_pham(con, dataset_id=d['dataset_id'])
                    row_cache[d['dataset_id']] = {x['record_id']: x for x in sp_list}
                    ten_cache[d['dataset_id']] = {x['record_id']: x.get('ten_goc', '') for x in sp_list}
                row = row_cache[d['dataset_id']].get(d['record_id']) or {}
                bv = DB.lay_bai_viet(con, d['dataset_id'], d['record_id'], d['site'], d['mau'])
                d['ten_san_pham'] = ten_cache[d['dataset_id']].get(d['record_id'], '')
                d['loi'] = (bv or {}).get('loi') or ''
                d['site_hien_thi'] = (wc_hien_tai['ten'] or wc_hien_tai['url']) \
                    if wc_hien_tai and d['site'] == wc_hien_tai['site_key'] else d['site']
                d['sku_hien_thi'] = row.get('publish_sku') or row.get('ma_goc') or d['record_id'].split('::')[-1]
                d['thuong_hieu'] = row.get('thuong_hieu') or ''
                ho = WS.ho_san_pham(row) or {}
                d['ho_nhan'] = ho.get('nhan', '')

            # C8 + C5: lấy tập sản phẩm nguồn đã chọn độc lập dashboard state.
            # KPI và danh sách Họ phải vẫn đầy đủ ngay cả khi bài chưa từng chạy
            # nên chưa có dòng trong bai_viet_phase2.
            if did:
                sp_tong = DB.liet_ke_san_pham(con, dataset_id=did, chi_da_chon=True)
            else:
                sp_tong = []
                for x in ds_list:
                    sp_tong.extend(DB.liet_ke_san_pham(con, dataset_id=x['dataset_id'], chi_da_chon=True))
            tong_can_lam = len(sp_tong)
            ho_values_nguon = sorted({(WS.ho_san_pham(r) or {}).get('nhan', '') for r in sp_tong
                                      if (WS.ho_san_pham(r) or {}).get('nhan')}, key=str.casefold)

            # Ver 4.4.1.2 — CHƯA CHẠY nghĩa là record nguồn chưa có WP ID trên
            # site/mẫu đang xét. Phải synthesize cả record chưa từng có dòng
            # bai_viet_phase2, không thể chỉ filter bảng dashboard hiện hữu.
            if loc_chua_chay:
                site_check = site or (wc_hien_tai.get('site_key') if wc_hien_tai else None)
                da_co = DB.dashboard(con, dataset_id=did, site=site_check) if site_check else DB.dashboard(con, dataset_id=did)
                if mau_loc and mau_loc != '(tất cả)':
                    da_co = [x for x in da_co if x.get('mau') == mau_loc]
                co_wp = {(x['dataset_id'], x['record_id']) for x in da_co if x.get('wp_id')}
                mau_hien = mau_loc if mau_loc and mau_loc != '(tất cả)' else self._phase2_mau_dang_chon()
                dash = []
                for r in sp_tong:
                    key_r = (r.get('dataset_id') or did, r['record_id'])
                    # `liet_ke_san_pham` luôn có dataset_id trong record normalized;
                    # fallback did chỉ dùng cho fixture cũ.
                    dataset_r = r.get('dataset_id') or did
                    if (dataset_r, r['record_id']) in co_wp:
                        continue
                    ho = WS.ho_san_pham(r) or {}
                    dash.append({
                        'dataset_id': dataset_r, 'record_id': r['record_id'],
                        'profile_id': r.get('profile_id',''), 'outline_id': r.get('outline_id',''),
                        'content_type': r.get('content_type',''), 'site': site_check or '',
                        'mau': mau_hien, 'trang_thai': 'CHƯA CHẠY', 'wp_id': None, 'wp_url': '',
                        'ngay_dang': None, 'thoi_luong_giay': None, 'ten_san_pham': r.get('ten_goc',''),
                        'loi': '', 'site_hien_thi': (wc_hien_tai.get('ten') or wc_hien_tai.get('url')) if wc_hien_tai else (site_check or ''),
                        'sku_hien_thi': r.get('publish_sku') or r.get('ma_goc') or r['record_id'].split('::')[-1],
                        'thuong_hieu': r.get('thuong_hieu') or '', 'ho_nhan': ho.get('nhan','')})
        finally:
            con.close()

        dash_goc = list(dash)
        self.cb_v3_dash_ho['values'] = ['(tất cả)'] + ho_values_nguon
        if self.v3_dash_ho.get() not in self.cb_v3_dash_ho['values']:
            self.v3_dash_ho.set('(tất cả)')

        tim = self.v3_dash_tim.get().strip().casefold()
        if tim:
            dash = [d for d in dash if tim in (' '.join([d.get('sku_hien_thi',''), d.get('record_id',''),
                                                         d.get('ten_san_pham',''), d.get('thuong_hieu','')])).casefold()]
        ho_loc = self.v3_dash_ho.get()
        if ho_loc and ho_loc != '(tất cả)':
            dash = [d for d in dash if d.get('ho_nhan') == ho_loc]

        for n, d in enumerate(dash):
            d['_ord'] = n
        col = self._v3_dash_sort_col
        def key(d):
            if col == 'stt': return d.get('_ord', 0)
            map_key = {
                'dataset':'dataset_id','record_id':'record_id','ten':'ten_san_pham','profile':'profile_id',
                'site':'site_hien_thi','mau':'mau','trang_thai':'trang_thai','wp_id':'wp_id',
                'url':'wp_url','thoi_gian':'ngay_dang','thoi_luong':'thoi_luong_giay','loi':'loi'
            }
            v = d.get(map_key.get(col, col))
            if col in ('wp_id','thoi_luong'):
                try: return float(v or 0)
                except Exception: return 0
            return str(v or '').casefold()
        dash.sort(key=key, reverse=self._v3_dash_sort_desc)
        self._v3_dash_rows = dash
        self._v3_dash_total = len(dash_goc)

        self.bang_phase2_dash.delete(*self.bang_phase2_dash.get_children())
        self._v3_dash_iid_map = {}
        for n, d in enumerate(dash, 1):
            the = 'ok' if d['trang_thai'] == 'da_dang' else ('loi' if d['trang_thai'] == 'loi' else '')
            iid = f'dash_{n}'
            self._v3_dash_iid_map[iid] = d
            self.bang_phase2_dash.insert(
                '', 'end', iid=iid, values=(n, d['dataset_id'], d['record_id'], d['ten_san_pham'],
                                   d['profile_id'], d['site_hien_thi'], d['mau'], d['trang_thai'],
                                   d['wp_id'] or '', d['wp_url'] or '',
                                   DB.dinh_dang_thoi_gian(d['ngay_dang']),
                                   DB.dinh_dang_thoi_luong(d['thoi_luong_giay']),
                                   d['loi']), tags=(the,))
        self.lb_v3_dash_dong.config(text=f'dòng 0/{len(dash_goc)}')

        # C8 — summary KHÔNG phụ thuộc filter Trạng thái/Mẫu/Tìm kiếm đang xem.
        # Đếm record đã đăng ít nhất một bài trên site hiện hành trong dataset.
        # Chọn filter "Lỗi" không được làm thanh tổng quan tụt về 0 đã đăng.
        con2 = self._con_phase2()
        try:
            if did:
                dash_tong = DB.dashboard(con2, dataset_id=did, site=site)
            else:
                dash_tong = DB.dashboard(con2, site=site)
            da_dang_ids = {d['record_id'] for d in dash_tong
                           if d.get('trang_thai') == 'da_dang' and d.get('wp_id')}
        finally:
            con2.close()
        da_dang = len(da_dang_ids)
        con_lai = max(0, tong_can_lam - da_dang)
        self.tt.config(text=f'Tổng quan: {tong_can_lam} bài cần làm, {da_dang} đã đăng, {con_lai} còn lại')

    # Ver 3.5: 2 hàm định dạng đã chuyển sang db_phase2.py (dinh_dang_thoi_gian/
    # dinh_dang_thoi_luong) để dùng CHUNG với công cụ CLI
    # (cong_cu_kiem_tra_ket_qua.py) — không giữ 2 bản trùng logic ở đây nữa.

    def _v3_mo_url(self):
        iid = self.bang_phase2_dash.focus()
        if not iid:
            messagebox.showinfo('Chưa chọn', 'Bấm chọn 1 dòng ở bảng trước.')
            return
        vals = self.bang_phase2_dash.item(iid, 'values')
        url = vals[8] if len(vals) > 8 else ''
        if not url:
            messagebox.showinfo('Chưa có URL', 'Dòng này chưa có URL (chưa đăng, hoặc lỗi).')
            return
        import webbrowser
        webbrowser.open(url)

    def _con_phase2(self):
        import db_phase2 as DB
        return DB.ket_noi()

    def _phase2_chon_file(self):
        p = filedialog.askopenfilename(filetypes=[('Excel', '*.xlsx')])
        if not p:
            return
        self.chay_nen_phase2(lambda: self._phase2_lam_import(p))

    def chay_nen_phase2(self, ham):
        """Bản chạy nền RIÊNG cho tab Phase 2 — không dùng chay_nen() chung vì
        hàm đó khoá cứng theo nut_chay/nut_dung của tab 5 (RMU), 2 luồng chạy
        độc lập không được đụng nút của nhau."""
        def boc():
            router = _bat_stdout_worker(self.q)
            try:
                ham()
            except Exception:
                print('LỖI (Phase 2):\n' + traceback.format_exc())
            finally:
                _tat_stdout_worker(router)
        threading.Thread(target=boc, daemon=True).start()

    def _phase2_lam_import(self, duong_dan):
        import nhap_phase2 as N
        import db_phase2 as DB
        print(f'== Đang nhập {duong_dan} ...')
        rpt = N.import_phase2_pipeline(duong_dan)
        self._v3_bao_cao_gan_nhat = rpt   # UI Ver 3 đọc lại để hiện bảng báo cáo, không đổi hành vi cũ
        if rpt['loai_nguon'] == 'rmu_legacy':
            print('File này là dữ liệu RMU cũ — dùng "Công cụ → Chế độ RMU (rollback)" để nhập.')
            self.ui(self._v3_cap_nhat_bao_cao)
            return
        dong_canh_bao = []
        doi_cau_truc = []   # Ver 4.5.1
        for pid, m in rpt['ket_qua_theo_profile'].items():
            if m.get('ok'):
                print(f'  {pid}: OK -> dataset_id={m["dataset_id"]} ({m["trang_thai_dataset"]}), '
                     f'{m["so_dong"]} dòng')
                # Ver 4.4.1.7 — dataset mới thì PHẢI nói ra bài đã đăng đi đâu.
                # Trước đây bước này không tồn tại và bài mồ côi trong im lặng.
                cb2 = m.get('chuyen_bai')
                if cb2 and (cb2.get('bai_chuyen') or cb2.get('mo_coi')
                            or cb2.get('trung_khoa') or cb2.get('loi')):
                    print(f'     [dataset mới] kéo bài đã đăng từ '
                          f'{cb2.get("dataset_cu")} sang: '
                          f'{cb2.get("bai_chuyen", 0)} bài, '
                          f'{cb2.get("job_chuyen", 0)} job.')
                    if cb2.get('mo_coi'):
                        co_wp = [x for x in cb2['mo_coi'] if x.get('wp_id')]
                        print(f'     CẢNH BÁO: {len(cb2["mo_coi"])} bài KHÔNG khớp '
                              f'record_id (thường do sửa SKU hoặc đổi số dòng) — '
                              f'giữ nguyên ở dataset cũ, KHÔNG xoá.')
                        if co_wp:
                            print(f'     Trong đó {len(co_wp)} bài CÓ wp_id, tức bài '
                                  f'thật trên WordPress sẽ mất liên kết. Kiểm tay: '
                                  + ', '.join(str(x["record_id"]) for x in co_wp[:5])
                                  + (' …' if len(co_wp) > 5 else ''))
                    if cb2.get('trung_khoa'):
                        print(f'     {len(cb2["trung_khoa"])} bài đã tồn tại sẵn ở '
                              f'dataset mới — bỏ qua, không ghi đè.')
                    if cb2.get('loi'):
                        print(f'     LỖI khi kéo bài: {cb2["loi"]}')
            else:
                cb = m.get('canh_bao') or {}
                print(f'  {pid}: DỪNG — {cb.get("loai","")}: {cb.get("thong_diep","")}')
                if cb.get('loai') == 'CanhBaoDatasetDoi':
                    dong_canh_bao.append(pid)
                elif cb.get('loai') == 'CanhBaoCauTrucDoi':
                    # Ver 4.5.1 — chỉ THÊM cột thì cho đi tiếp sau xác nhận.
                    # Có BỚT cột thì để nguyên đường cũ (chặn cứng, mất dữ liệu).
                    if cb.get('cot_them') and not cb.get('cot_bot'):
                        doi_cau_truc.append(
                            f'{pid}: thêm cột ' + ', '.join(cb['cot_them']))
        if doi_cau_truc:
            ct = '\n'.join(doi_cau_truc)
            self.ui(lambda: self._phase2_hoi_doi_cau_truc(duong_dan, ct))
        if dong_canh_bao:
            self.ui(lambda: self._phase2_hoi_xac_nhan_dataset(duong_dan, dong_canh_bao))
        self.ui(self._phase2_nap_dataset)
        self.ui(self._v3_cap_nhat_bao_cao)
        self.ui(self._v3_nap_danh_sach_dataset)

    def _phase2_hoi_doi_cau_truc(self, duong_dan, chi_tiet):
        """Ver 4.5.1 — MASTER thêm cột mới. Cho phép đi tiếp sau khi người
        dùng nhìn thấy đúng cột nào được thêm."""
        hoi = messagebox.askyesno(
            'MASTER có thêm cột mới',
            chi_tiet + '\n\nTạo dataset MỚI với cấu trúc này?\n'
            'Bài viết/WP ID của dataset CŨ được chuyển sang, không mất gì.')
        if hoi:
            self.chay_nen_phase2(
                lambda: self._phase2_lam_import_xac_nhan(duong_dan, doi_cau_truc=True))

    def _phase2_hoi_xac_nhan_dataset(self, duong_dan, danh_sach_profile):
        import nhap_phase2 as N
        hoi = messagebox.askyesno(
            'Dataset đã đổi',
            f'Dữ liệu của {", ".join(danh_sach_profile)} khác với lần nhập trước '
            f'(data_checksum khác), nhưng cấu trúc cột vẫn giống.\n\n'
            f'Xác nhận đây là dataset MỚI (không phải sửa nhầm file)? '
            f'Bài viết/WP ID của dataset CŨ sẽ được giữ nguyên, không mất.')
        if hoi:
            self.chay_nen_phase2(lambda: self._phase2_lam_import_xac_nhan(duong_dan))

    def _phase2_lam_import_xac_nhan(self, duong_dan, doi_cau_truc=False):
        import nhap_phase2 as N
        rpt = N.import_phase2_pipeline(duong_dan, confirm_new_dataset=True,
                                       confirm_doi_cau_truc=doi_cau_truc)
        self._v3_bao_cao_gan_nhat = rpt
        for pid, m in rpt['ket_qua_theo_profile'].items():
            print(f'  {pid}: {"OK" if m.get("ok") else "LỖI"} -> {m.get("dataset_id","")} '
                 f'({m.get("trang_thai_dataset","")})')
        self.ui(self._phase2_nap_dataset)
        self.ui(self._v3_cap_nhat_bao_cao)
        self.ui(self._v3_nap_danh_sach_dataset)

    def _phase2_nap_dataset(self):
        import db_phase2 as DB
        con = self._con_phase2()
        try:
            ds = DB.liet_ke_dataset(con)
        finally:
            con.close()
        gia_tri = [f'{d["dataset_id"]} ({d["profile_id"]}, {d["row_count"]} dòng)' for d in ds]
        self.cb_phase2_dataset['values'] = gia_tri
        if gia_tri and not self.v_phase2_dataset.get():
            self.v_phase2_dataset.set(gia_tri[0])
        self._v3_loc_san_pham()   # UI Ver 3: refresh bảng sản phẩm tab 2 khi danh sách dataset đổi

    def _phase2_dataset_id_dang_chon(self):
        gt = self.v_phase2_dataset.get()
        return gt.split(' ')[0] if gt else None

    def _phase2_nap_danh_sach(self):
        import db_phase2 as DB
        did = self._phase2_dataset_id_dang_chon()
        self.bang_phase2.delete(*self.bang_phase2.get_children())
        if not did:
            return
        con = self._con_phase2()
        try:
            sp = DB.liet_ke_san_pham(con, dataset_id=did)
        finally:
            con.close()
        for row in sp:
            the = 'da_chon' if row.get('selected') else ''
            self.bang_phase2.insert('', 'end', iid=row['record_id'],
                                    values=('✓' if row.get('selected') else '',
                                            row['record_id'], row['profile_id'],
                                            row['outline_id'], row.get('ten_goc', '')),
                                    tags=(the,))

    def _phase2_doi_chon(self, event=None):
        """Bấm đúp để bật/tắt chọn viết bài. BUG THẬT đã sửa: refresh lại
        bảng (xoá hết + chèn lại) làm MẤT focus/selection của Treeview —
        nếu không khôi phục, thao tác bấm nút kế tiếp (Xem prompt/Chạy thử)
        sẽ không tìm thấy dòng đang chọn dù mắt thường vẫn thấy nó có vẻ
        đang được tô sáng. Giữ lại iid, focus/select lại đúng dòng đó."""
        import db_phase2 as DB
        iid = self.bang_phase2.focus()
        if not iid:
            return
        did = self._phase2_dataset_id_dang_chon()
        con = self._con_phase2()
        try:
            sp = DB.lay_san_pham(con, did, iid)
            moi = not sp.get('selected')
            DB.dat_chon(con, did, [iid], chon=moi)
        finally:
            con.close()
        self._v3_loc_san_pham()   # UI Ver 3: refresh có áp bộ lọc + cập nhật thống kê, thay _phase2_nap_danh_sach cũ
        if self.bang_phase2.exists(iid):
            self.bang_phase2.focus(iid)
            self.bang_phase2.selection_set(iid)

    def _phase2_chon_hang_loat(self, chon):
        import db_phase2 as DB
        did = self._phase2_dataset_id_dang_chon()
        if not did:
            return
        ids = list(self.bang_phase2.get_children())
        con = self._con_phase2()
        try:
            DB.dat_chon(con, did, ids, chon=chon)
        finally:
            con.close()
        self._v3_loc_san_pham()

    def _phase2_dong_dang_chon(self):
        """record đang active để Xem prompt/Xem trước HTML dùng (Task 1.2).
        Thứ tự ưu tiên: focus() hiện tại -> dòng đầu của selection() hiện
        tại -> v3_active_record_id đã ghi nhớ từ trước (bền qua các lần
        bảng bị xoá-dựng-lại lúc lọc/refresh — đây là chỗ sửa bug thật:
        trước kia chỉ có 2 lớp đầu, nếu bảng vừa refresh xong mà chưa kịp
        click lại thì cả focus() lẫn selection() đều rỗng dù dữ liệu đã
        chọn đủ 245 sản phẩm, gây báo sai 'Bấm chọn 1 dòng'.
        """
        import db_phase2 as DB
        iid = (self.bang_phase2.focus()
               or (self.bang_phase2.selection() or (None,))[0]
               or (self.v3_active_record_id if self.bang_phase2.exists(self.v3_active_record_id or '') else None))
        did = self._phase2_dataset_id_dang_chon()
        if not iid or not did:
            messagebox.showinfo('Chưa chọn', 'Bấm chọn 1 dòng ở bảng "2. Sản phẩm" trước.')
            return None
        self.v3_active_record_id = iid
        con = self._con_phase2()
        try:
            return DB.lay_san_pham(con, did, iid)
        finally:
            con.close()

    def dang_chon(self):
        """Ver 5.9 — CUNG CẤP chân thứ 6 của hợp đồng giac_cam.py.

        Module tách ra khỏi God Class cần biết người dùng đang làm việc trên
        dataset/mẫu/site nào. Ba ô chọn đó nằm ở tab khác, thuộc vỏ ứng
        dụng. Không có hàm này thì mỗi module phải tự dựng ô chọn riêng ->
        mỗi tab một dataset, đúng loại lỗi khó tìm nhất.

        Bọc try từng phần: một ô chưa dựng (tab chưa mở) KHÔNG được làm chết
        cả hàm — trả None cho ô đó là đủ.
        """
        d = {'dataset_id': None, 'mau': None, 'site': None}
        try:
            d['dataset_id'] = self._phase2_dataset_id_dang_chon()
        except Exception:
            pass
        try:
            d['mau'] = self._phase2_mau_dang_chon()
        except Exception:
            pass
        try:
            cfg = self._v3_site_cfg()
            d['site'] = cfg.get('ma') if isinstance(cfg, dict) else cfg
        except Exception:
            pass
        return d

    def _phase2_mau_dang_chon(self):
        """Đọc ô 'Mẫu' đã có sẵn ở khối D (Round 2) — dùng chung cho cả khối
        C (Thử 1 bài) và D (Chạy hàng loạt), không thêm widget mới. Mặc định
        'chuan' nếu ô trống hoặc gõ sai tên mẫu chưa hỗ trợ."""
        import prompts_phase2 as PR
        mau = (self.v_phase2_mau.get() or 'chuan').strip()
        if mau not in PR.MAU_BIEN_THE:
            messagebox.showwarning(
                'Mẫu chưa hỗ trợ',
                f'Mẫu "{mau}" chưa có prompt. Đang hỗ trợ: {", ".join(PR.MAU_BIEN_THE)}. '
                f'Dùng tạm "chuan".')
            return 'chuan'
        return mau

    def _phase2_xem_prompt(self):
        import prompts_phase2 as PR
        row = self._phase2_dong_dang_chon()
        if row is None:
            return
        mau = self._phase2_mau_dang_chon()
        import render_phase2 as R
        row = R.bo_sung_may_tuong_thich(row)
        he_thong, nguoi_dung, schema = PR.xay_prompt(row, self._v3_site_cfg(), mau=mau)
        self.txt_phase2_thu.delete('1.0', 'end')
        self.txt_phase2_thu.insert(
            'end', f'[Mẫu: {mau}]\n\n=== SYSTEM ===\n{he_thong}\n\n=== USER ===\n{nguoi_dung}')

    def _phase2_chay_thu(self):
        import ai_wp_adapter as AWP
        import db_phase2 as DB
        import render_phase2 as R
        row = self._phase2_dong_dang_chon()
        if row is None:
            return
        mau = self._phase2_mau_dang_chon()
        site_cfg = self._v3_site_cfg()
        con = self._con_phase2()   # Ver 4.9.8 — lấy cung_dong cho preview giống luồng thật
        cung_dong = DB.tim_san_pham_cung_dong(con, row['dataset_id'], row['record_id'])
        row_ai = R.bo_sung_may_tuong_thich(dict(row, **R.tinh_delta_context(row, cung_dong)))   # Ver 4.3.1
        ai_data, usage = AWP.goi_ai_mock(row_ai, mau=mau)
        bai = R.dung_bai_html(row, ai_data, site_cfg, mau=mau, cung_dong=cung_dong)
        # Ver 3.5: dùng ĐÚNG hàm kiem_tra_bia_toan_bo() mà luồng Real dùng —
        # trước đây preview tự kiểm 1 đoạn hẹp khác (4 field văn xuôi), có
        # thể báo "không chặn gì" dù meta_title/meta_description/faq.q vẫn
        # còn số bịa, sang Real mới lộ ra. Preview phải phản ánh ĐÚNG những
        # gì Real sẽ chặn, không phải 1 phiên bản dễ dãi hơn.
        vi_pham = AWP.kiem_tra_bia_toan_bo(ai_data, row_ai)
        chi_tiet_chan = '; '.join(f'{f}: {v}' for f, v in vi_pham.items())
        self.txt_phase2_thu.delete('1.0', 'end')
        self.txt_phase2_thu.insert(
            'end',
            f'[Mẫu: {mau}]\n'
            f'Title: {bai["title"]}\nMeta: {bai["meta_description"]}\nSlug: {bai["slug"]}\n'
            f'Hard Block: {"CHẶN — " + chi_tiet_chan if vi_pham else "không có gì bị chặn"}\n\n'
            f'--- HTML ---\n{bai["html"]}')

    def _phase2_mo_trinh_duyet(self):
        """Ver 5.0 — theo yêu cầu Thịnh: đọc HTML thô trong ô Text khó hình
        dung layout thật. Dựng CÙNG bài (Mock, không tốn quota) rồi ghi ra
        1 file .html tạm, mở bằng trình duyệt MẶC ĐỊNH của máy
        (webbrowser.open — có sẵn trong Python, không cần cài thêm gì) —
        nhìn gần đúng layout thật trên site (đã style INLINE từ Ver 4.9.9
        nên hiện màu/nút đúng ngay cả khi mở file rời, không qua WordPress)."""
        import html
        import os
        import tempfile
        import webbrowser

        import ai_wp_adapter as AWP
        import db_phase2 as DB
        import render_phase2 as R

        row = self._phase2_dong_dang_chon()
        if row is None:
            return
        mau = self._phase2_mau_dang_chon()
        site_cfg = self._v3_site_cfg()
        con = self._con_phase2()
        cung_dong = DB.tim_san_pham_cung_dong(con, row['dataset_id'], row['record_id'])
        row_ai = dict(row, **R.tinh_delta_context(row, cung_dong))
        ai_data, usage = AWP.goi_ai_mock(row_ai, mau=mau)
        bai = R.dung_bai_html(row, ai_data, site_cfg, mau=mau, cung_dong=cung_dong)

        trang = (f'<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8">'
                f'<title>{html.escape(bai["title"])}</title>'
                f'<style>body{{font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif;'
                f'max-width:820px;margin:0 auto;padding:24px;line-height:1.6;}}'
                f'h1{{font-size:22px;}} h2{{font-size:18px;border-bottom:2px solid #eee;'
                f'padding-bottom:6px;margin-top:28px;}}</style></head><body>'
                f'<div style="background:#1a1a2e;color:#fff;padding:10px 16px;border-radius:8px;'
                f'margin-bottom:20px;font-size:13px;">🧪 XEM TRƯỚC (Mock, không phải bài đã đăng) — '
                f'Slug dự kiến: {html.escape(bai["slug"])}</div>'
                f'<h1>{html.escape(bai["title"])}</h1>{bai["html"]}</body></html>')

        duong_dan = os.path.join(tempfile.gettempdir(), f'lotech_xem_truoc_{row.get("ma_goc", "sp")}.html')
        with open(duong_dan, 'w', encoding='utf-8') as f:
            f.write(trang)
        webbrowser.open('file://' + duong_dan)

    def _phase2_chay_hang_loat(self):
        """Validate mau ở LUỒNG CHÍNH trước khi vào luồng nền — Tkinter
        (messagebox trong _phase2_mau_dang_chon) không an toàn khi gọi từ
        luồng nền. Truyền mau đã hợp lệ vào hàm chạy nền qua tham số, hàm
        chạy nền không tự đọc/validate lại widget."""
        mau = self._phase2_mau_dang_chon()
        did = self._phase2_dataset_id_dang_chon()
        site = self._v3_site_key()
        site_cfg = self._v3_site_cfg()
        self.v3_dung_lai.clear()
        self.nut_v3_sinh_bai.config(state='disabled')
        self.nut_v3_dung.config(state='normal')
        self.tien_do_v3.config(value=0, maximum=1)
        self.lb_v3_tien_do.config(text='Đang chuẩn bị...')
        self.chay_nen_phase2(lambda: self._phase2_viec_chay_hang_loat(mau, did, site, site_cfg))

    def _v3_don_state_mock(self):
        """Ver 4.3.1: dọn duy nhất các bài có wp_url chứa '.mock' khỏi state production."""
        import db_phase2 as DB
        con = self._con_phase2()
        try:
            n = con.execute(
                "SELECT COUNT(*) FROM bai_viet_phase2 "
                "WHERE instr(lower(COALESCE(wp_url,'')), '.mock') > 0").fetchone()[0]
            if not n:
                messagebox.showinfo('Dọn state .mock', 'Không có bản ghi .mock nào trong DB.')
                return
            if not messagebox.askyesno(
                    'Dọn state .mock',
                    f'Tìm thấy {n} bản ghi Mock trong trạng thái đăng.\n\n'
                    'Chỉ xoá các dòng có URL chứa ".mock"; dữ liệu sản phẩm và bài thật không bị đụng.\n'
                    'Tiếp tục?'):
                return
            da_xoa = DB.don_bai_viet_mock(con)
        finally:
            con.close()
        self._v3_nap_dashboard()
        print(f'== [MOCK STATE] Đã dọn {da_xoa} bản ghi có URL .mock ==')
        messagebox.showinfo('Dọn state .mock', f'Đã dọn {da_xoa} bản ghi .mock.')

    def _v3_force_stop(self):
        """Nút Dừng khẩn cấp — chỉ BÁO hiệu dừng (Event), không kill thread
        thô bạo giữa chừng 1 record đang xử lý (tránh ghi dở dữ liệu). Vòng
        lặp tự kiểm tra cờ này ở ĐẦU mỗi record, dừng gọn giữa 2 record."""
        self.v3_dung_lai.set()
        self.nut_v3_dung.config(state='disabled')
        print('== Đã nhấn Dừng khẩn cấp — dừng sau khi xong record đang xử lý... ==')

    def _v3_cap_nhat_tien_do(self, da_xong, tong):
        self.tien_do_v3.config(value=da_xong, maximum=max(tong, 1))
        phan_tram = int(da_xong / tong * 100) if tong else 0
        self.lb_v3_tien_do.config(text=f'Đang chạy {da_xong}/{tong} ({phan_tram}%)')

    def _v3_ket_thuc_chay(self, thong_bao):
        self.nut_v3_sinh_bai.config(state='normal')
        if hasattr(self, 'nut_v3_tiep_tuc'):
            self.nut_v3_tiep_tuc.config(state='normal')
        self.nut_v3_dung.config(state='disabled')
        self.lb_v3_tien_do.config(text=thong_bao)

    def _phase2_viec_chay_hang_loat(self, mau, did, site, site_cfg):
        import db_phase2 as DB
        import ai_wp_adapter as AWP
        if not did:
            print('Chưa chọn dataset.')
            self.ui(lambda: self._v3_ket_thuc_chay('Chưa chọn dataset.'))
            return
        con = self._con_phase2()
        thong_bao = 'Batch mock dừng bất thường — xem console để biết chi tiết.'
        try:
            sp = DB.liet_ke_san_pham(con, dataset_id=did, chi_da_chon=True)
            if not sp:
                print('Không có sản phẩm nào đang chọn (bấm đúp ở bảng "2. Sản phẩm" để chọn).')
                thong_bao = 'Chưa có sản phẩm nào được chọn.'
                return
            tong = len(sp)
            print(f'== Chạy {tong} sản phẩm đã chọn, site={site}, mẫu={mau} (AI mock) ==')
            self.ui(lambda: self._v3_cap_nhat_tien_do(0, tong))
            ok, loi, bi_dung = 0, 0, False
            for i, row in enumerate(sp, 1):
                if self.v3_dung_lai.is_set():
                    bi_dung = True
                    print(f'== Đã dừng theo yêu cầu, còn lại {tong - i + 1} sản phẩm chưa chạy ==')
                    break
                try:
                    kq = AWP.sinh_va_dang_mock(con, did, row['record_id'], site, site_cfg, mau=mau)
                    if kq['ok']:
                        ok += 1
                        print(f'  [da_dang] {row["record_id"]} -> wp_id={kq["wp_id"]} {kq["wp_url"]}')
                    else:
                        loi += 1
                        print(f'  [loi] {row["record_id"]} -> {kq["loi"]}')
                except Exception as e:
                    loi += 1
                    print(f'  [loi] {row["record_id"]} -> {type(e).__name__}: {e}')
                self.ui(lambda i=i, tong=tong: self._v3_cap_nhat_tien_do(i, tong))
            if not bi_dung:
                print(f'== Xong: {ok} thành công, {loi} lỗi ==')
            thong_bao = (f'Đã dừng ở {ok + loi}/{tong} (thành công {ok}, lỗi {loi})' if bi_dung
                        else f'Xong: {ok}/{tong} thành công, {loi} lỗi')
        finally:
            con.close()
            self.ui(self._v3_nap_dashboard)
            self.ui(lambda tb=thong_bao: self._v3_ket_thuc_chay(tb))

    def _phase2_nap_dashboard(self):
        """Round 2 giữ tên hàm này cho tương thích ngược (test cũ gọi trực
        tiếp) — UI Ver 3 dùng bảng dashboard 11 cột mới, alias thẳng sang
        _v3_nap_dashboard() thay vì duy trì 2 bản logic riêng."""
        self._v3_nap_dashboard()

    def _nhat_ky(self):
        k = ttk.Frame(self.chia_man, padding=(14, 10, 14, 8), style='V3.TFrame')
        self.chia_man.add(k, stretch='always', minsize=280)
        t = ttk.Frame(k, style='V3.TFrame')
        t.pack(fill='x')
        ttk.Label(t, text='Nhật ký', style='V3Tieu.TLabel').pack(side='left')
        ttk.Button(t, text='Xoá', width=8, style='V3.TButton', command=self._xoa_log).pack(side='right')
        # Ver 2.6 — ô log CỐ TÌNH giữ tối kiểu terminal, KHÔNG đổi theo
        # V3_CARD (giờ đã là trắng) — quy ước phổ biến: khung UI sáng,
        # riêng vùng log/console giữ nền tối để phân biệt "vùng output"
        # với "vùng điều khiển". Đúng thiết kế gốc trước khi có dark mode
        # toàn app ở Ver 1.6.
        self.log_o = tk.Text(k, height=11, bg='#1E1E1E', fg='#E4E9ED', bd=0,
                             font=('Consolas', 9), wrap='word', state='disabled',
                             insertbackground='#E4E9ED', highlightthickness=1,
                             highlightbackground=V3_BORDER, highlightcolor=V3_BORDER)
        sb = ttk.Scrollbar(k, orient='vertical', command=self.log_o.yview)
        self.log_o.configure(yscrollcommand=sb.set)
        self.log_o.pack(side='left', fill='both', expand=True, pady=(6, 0))
        sb.pack(side='right', fill='y', pady=(6, 0))
        for ten, mau in [('ok', '#6FCF6F'), ('loi', '#FF7B7B'),
                         ('canh', '#F2C14E'), ('nhan', '#7FB3FF')]:
            self.log_o.tag_configure(ten, foreground=mau)

    def _khi_resize_cua_so(self, event):
        """VÁ THÊM — <Configure> nổ ra cho MỌI widget con (bubble), không
        chỉ cửa sổ gốc, và bắn liên tục nhiều lần với chiều rộng TRUNG GIAN
        khi đang kéo/maximize — nếu tính sash ngay trên từng event thì
        chốt nhầm theo 1 giá trị giữa chừng (đây chính là lý do lần vá
        trước vẫn sai: 21.9% thay vì 60%, vì bắt trúng event của widget
        con lúc window mới bắt đầu đổi kích thước). Sửa đúng cách: CHỈ
        nhận event của self (cửa sổ gốc, không phải widget con), và
        DEBOUNCE — huỷ hẹn giờ cũ, đặt hẹn giờ mới, chỉ thực sự tính khi
        không còn event nào bắn thêm trong 150ms (nghĩa là resize đã
        xong hẳn, không phải giữa chừng)."""
        if event.widget is not self:
            return
        job = getattr(self, '_resize_debounce_job', None)
        if job is not None:
            try:
                self.after_cancel(job)
            except Exception:
                pass
        self._resize_debounce_job = self.after(150, lambda: self._dat_ti_le_chia_man(ep=True))

    def _dat_ti_le_chia_man(self, ep=False):
        """Đặt sash chia_man ở đúng 60% chiều rộng cửa sổ THẬT tại thời
        điểm gọi. Gọi lúc mở app (ep=True, bỏ qua threshold) và mỗi khi
        `_khi_resize_cua_so` xác nhận resize đã settle (cũng ep=True — đến
        đây rồi thì luôn muốn tính lại, không cần threshold nữa)."""
        try:
            rong = self.winfo_width()
            if rong < 100:
                self.after(50, lambda: self._dat_ti_le_chia_man(ep=True))
                return
            self.chia_man.sash_place(0, int(rong * 0.6), 0)
        except tk.TclError:
            pass   # cửa sổ có thể đã đóng trước khi callback chạy tới, bỏ qua an toàn

    def _xoa_log(self):
        self.log_o.config(state='normal')
        self.log_o.delete('1.0', 'end')
        self.log_o.config(state='disabled')

    # ------------------------------------------------------------ tiện ích
    def report_callback_exception(self, kieu, gt, vet):
        """Chạy bằng pythonw thì không có console, nút lỗi trông như chết. Ghi vào nhật ký."""
        chi_tiet = ''.join(traceback.format_exception(kieu, gt, vet))
        try:
            self.log('LỖI: ' + str(gt), 'loi')
            for d in chi_tiet.strip().splitlines()[-6:]:
                self.log('   ' + d, 'loi')
            messagebox.showerror('Lỗi', str(gt)[:700])
        except Exception:
            pass

    def _kiem_thu_vien(self):
        thieu = [g for g in ('requests', 'openpyxl', 'bleach', 'fitz')
                 if not self._co(g)]
        if thieu:
            self.log('THIẾU THƯ VIỆN: ' + ', '.join(thieu), 'loi')
            self.log('Mở Command Prompt gõ:  python -m pip install ' + ' '.join(thieu), 'canh')
            if 'bleach' in thieu:
                self.log('  (bleach dùng để lọc HTML an toàn cho nhánh Phase 2 — '
                        'tab "6. Phase 2" sẽ báo lỗi nếu thiếu.)', 'canh')
        else:
            self.log('Thư viện đầy đủ. Sẵn sàng.', 'ok')

    @staticmethod
    def _co(ten):
        try:
            __import__(ten)
            return True
        except ImportError:
            return False

    def log(self, s, tag=None):
        self.log_o.config(state='normal')
        self.log_o.insert('end', s if s.endswith('\n') else s + '\n', tag)
        self.log_o.see('end')
        self.log_o.config(state='disabled')

    def ui(self, ham):
        """Nhờ luồng chính chạy giúp. Luồng nền TUYỆT ĐỐI không đụng vào tkinter."""
        self.q.put(('ui', ham))

    def _boc_hang_doi(self):
        try:
            while True:
                s = self.q.get_nowait()
                if isinstance(s, tuple) and s and s[0] == 'ui':
                    try:
                        s[1]()
                    except Exception:
                        self.log('LỖI UI callback:\n' + traceback.format_exc(), 'loi')
                    continue
                for d in s.splitlines():
                    if d.strip():
                        self.log(d, self._mau_dong(d))
        except queue.Empty:
            pass
        self._boc_hang_doi_job = self.after(80, self._boc_hang_doi)

    @staticmethod
    def _mau_dong(d):
        l = d.lower()
        if 'da_dang' in l or 'da_sinh' in l or '[ ok ]' in l or 'tất cả đều chạy' in l:
            return 'ok'
        if 'lỗi' in l or 'bi_chan' in l or '[ x' in l or 'hết lượt' in l:
            return 'loi'
        if 'cảnh báo' in l or 'chờ' in l or 'nhắc số' in l:
            return 'canh'
        if d.startswith('==') or d.startswith('=>'):
            return 'nhan'
        return None

    def mo(self, p):
        p = Path(p)
        if not p.exists():
            if p.suffix == '':
                p.mkdir(parents=True, exist_ok=True)
            else:
                messagebox.showwarning('Chưa có', f'Không tìm thấy:\n{p}')
                return
        try:
            if os.name == 'nt':
                os.startfile(str(p))
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(p)])
            else:
                subprocess.run(['xdg-open', str(p)])
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    # ------------------------------------------------------------ cấu hình
    def _doc_env(self):
        f = BASE / 'cau-hinh.env'
        d = {}
        if f.exists():
            for dong in f.read_text(encoding='utf-8-sig').splitlines():
                dong = dong.strip()
                if dong and not dong.startswith('#') and '=' in dong:
                    k, v = dong.split('=', 1)
                    d[k.strip()] = v.split('#')[0].strip().strip('"').strip("'")
        return d

    def doc_cau_hinh(self, giu_site=False):
        d = self._doc_env()
        ma = self.v_site.get()
        self.v_key.set(d.get('GOOGLE_API_KEY', ''))
        self.v_model.set(d.get('MODEL_GEMINI', 'gemini-3.6-flash'))
        pre = f'WP_{ma.upper()}'
        self.v_url.set(d.get(f'{pre}_URL', ''))
        self.v_user.set(d.get(f'{pre}_USER', ''))
        self.v_pw.set(d.get(f'{pre}_APP_PW', ''))
        self.lb_site.config(text=C.tat_ca_site()[ma]['ten'] + '  |  hotline ' + C.tat_ca_site()[ma]['hotline'])
        self.btn_xoa_site.config(state='disabled' if ma in C.SITES else 'normal')
        if not giu_site:
            self.tt.config(text='Đã đọc cau-hinh.env' if (BASE / 'cau-hinh.env').exists()
                           else 'Chưa có cau-hinh.env, điền rồi bấm Lưu')
        self._nap_mau()

    def _hop_thoai_them_site(self):
        top = tk.Toplevel(self)
        top.title('Thêm site mới')
        top.transient(self)
        top.grab_set()
        f = ttk.Frame(top, padding=16)
        f.pack(fill='both', expand=True)
        vien = {}

        def dong(nhan, mac_dinh='', mo_ta=''):
            ttk.Label(f, text=nhan).pack(anchor='w', pady=(8, 0))
            v = tk.StringVar(value=mac_dinh)
            ttk.Entry(f, textvariable=v, width=44).pack(anchor='w')
            if mo_ta:
                ttk.Label(f, text=mo_ta, style='Mo.TLabel').pack(anchor='w')
            return v

        vien['ma'] = dong('Mã site (viết liền, không dấu)', 'site3',
                          'Dùng nội bộ, ví dụ site3, cadivi, capls...')
        vien['ten'] = dong('Tên hiển thị', '', 'Ví dụ: CADIVI Việt Nam')
        vien['hotline'] = dong('Hotline', '')
        vien['dia_chi'] = dong('Địa chỉ (tuỳ chọn)', '')
        vien['khu_vuc'] = dong('Khu vực phục vụ (tuỳ chọn)', '')

        def luu():
            try:
                ma = vien['ma'].get().strip()
                C.them_site(ma, vien['ten'].get(), vien['hotline'].get(),
                           dia_chi=vien['dia_chi'].get(), khu_vuc=vien['khu_vuc'].get())
            except Exception as e:
                messagebox.showerror('Không thêm được', str(e))
                return
            self.cb_site['values'] = list(C.tat_ca_site())
            self.v_site.set(ma)
            self.doc_cau_hinh(giu_site=True)
            self.log(f'Đã thêm site "{ma}". Điền URL/tài khoản WordPress rồi bấm Lưu cấu hình.',
                     'ok')
            top.destroy()

        n = ttk.Frame(f)
        n.pack(fill='x', pady=(16, 0))
        ttk.Button(n, text='Thêm', style='Chinh.TButton', command=luu).pack(side='left')
        ttk.Button(n, text='Huỷ', command=top.destroy).pack(side='left', padx=8)

    def _xoa_site_hien_tai(self):
        ma = self.v_site.get()
        if ma in C.SITES:
            messagebox.showinfo('Không xoá được', f'"{ma}" là site mẫu có sẵn, không xoá được.')
            return
        if not messagebox.askyesno('Xác nhận', f'Xoá cấu hình site "{ma}"?\n\n'
                                    'Sản phẩm và bài viết đã sinh cho site này KHÔNG bị xoá, '
                                    'chỉ mất phần cấu hình (tên, hotline, WordPress).'):
            return
        C.xoa_site_them(ma)
        self.cb_site['values'] = list(C.tat_ca_site())
        self.v_site.set(list(C.tat_ca_site())[0])
        self.doc_cau_hinh(giu_site=True)
        self.log(f'Đã xoá site "{ma}".', 'ok')

    def _nap_mau(self):
        try:
            import prompts as P
            ds = list(P.MAU)
            self.cb_mau['values'] = ds
            if self.v_mau.get() not in ds and ds:
                self.v_mau.set(ds[0])
        except Exception:
            pass

    def luu_cau_hinh(self):
        """Giữ nguyên cấu hình của các site khác, chỉ ghi đè site đang chọn."""
        d = self._doc_env()
        ma = self.v_site.get()
        d['NHA_CUNG_CAP'] = d.get('NHA_CUNG_CAP', 'gemini')
        d['GOOGLE_API_KEY'] = self.v_key.get().strip()
        d['MODEL_GEMINI'] = self.v_model.get().strip()
        d[f'WP_{ma.upper()}_URL'] = self.v_url.get().strip().rstrip('/')
        d[f'WP_{ma.upper()}_USER'] = self.v_user.get().strip()
        d[f'WP_{ma.upper()}_APP_PW'] = self.v_pw.get().strip()
        noi_dung = ('# Sinh bởi giao diện Lotech Autopost. File này chỉ nằm trên máy bạn.\n'
                    '# KHÔNG gửi file này cho ai, không nén chung khi gửi phần mềm.\n'
                    + '\n'.join(f'{k}={v}' for k, v in d.items()) + '\n')
        (BASE / 'cau-hinh.env').write_text(noi_dung, encoding='utf-8')
        self._ap_cau_hinh()
        self.log(f'Đã lưu cau-hinh.env cho {ma}', 'ok')
        self.tt.config(text='Đã lưu cấu hình lúc ' + time.strftime('%H:%M:%S'))

    def _ap_cau_hinh(self):
        import autopost as A
        A.nap_env()
        A.MODEL_GEMINI = os.environ.get('MODEL_GEMINI', A.MODEL_GEMINI)
        A.NHA_CUNG_CAP = os.environ.get('NHA_CUNG_CAP', 'gemini').lower()
        return A

    # ------------------------------------------------------------ sản phẩm
    def nap_san_pham(self):
        for i in self.bang.get_children():
            self.bang.delete(i)
        self.san_pham = self._ap_cau_hinh().doc_san_pham()   # tất cả ngành hàng
        if not self.san_pham:
            self.lb_sp.config(text='Kho dữ liệu trống. Vào tab 0 nhập file Excel trước.')
            return
        du = chon = 0
        for i, r in enumerate(self.san_pham, 1):
            co, tong_cot = C.cham_du_lieu(r)
            tag = 'du' if co >= 7 else ('thieu' if co <= 2 else '')
            du += 1 if co >= 7 else 0
            dang_chon = int(r.get('chon', 1) or 0) == 1
            chon += 1 if dang_chon else 0
            # iid ghép danh_muc + sku: hai ngành trùng SKU vẫn phải là hai dòng riêng
            iid = f'{r.get("danh_muc", "chung")}::{r["sku"]}'
            self.bang.insert('', 'end', iid=iid, tags=(tag,),
                             values=(i, '✓' if dang_chon else '—', r['sku'],
                                     r['ten_san_pham'], f'{co}/{tong_cot}'))
        self.lb_sp.config(text=f'{len(self.san_pham)} sản phẩm  |  {chon} đang chọn viết  |  '
                               f'{du} dòng đã điền tương đối đủ')

    @staticmethod
    def _tach_khoa(iid):
        dm, _, sku = iid.partition('::')
        return dm, sku

    def _doi_chon_san_pham(self, event=None):
        iid = self.bang.focus()
        if not iid:
            return
        dm, sku = self._tach_khoa(iid)
        chon = D.dao_chon(dm, sku)
        v = list(self.bang.item(iid)['values'])
        v[1] = '✓' if chon else '—'
        self.bang.item(iid, values=v)
        self.lb_sp.config(text=self.lb_sp.cget('text').split('  |  ')[0] + '  |  '
                          + str(sum(1 for i in self.bang.get_children()
                                   if self.bang.item(i)['values'][1] == '✓')) + ' đang chọn viết')

    def _chon_hang_loat(self, chon):
        ds = list(self.bang.get_children())    # đúng những dòng đang hiện trên bảng
        if not ds:
            return
        D.dat_chon([self._tach_khoa(iid) for iid in ds], chon)
        for iid in ds:
            v = list(self.bang.item(iid)['values'])
            v[1] = '✓' if chon else '—'
            self.bang.item(iid, values=v)
        self.log(f'Đã {"chọn" if chon else "bỏ chọn"} {len(ds)} sản phẩm.', 'ok')
        self.nap_san_pham()

    # ------------------------------------------------------------ chạy nền
    def chay_nen(self, ham):
        if self.dang_chay:
            messagebox.showwarning('Đang bận', 'Đang có việc chạy. Chờ xong hoặc bấm Dừng.')
            return
        self.dang_chay = True
        self.dung_lai.clear()
        self.nut_chay.config(state='disabled')
        self.nut_dung.config(state='normal')

        def boc():
            router = _bat_stdout_worker(self.q)
            try:
                ham()
            except SystemExit as e:
                print(str(e))
            except Exception:
                print('LỖI:\n' + traceback.format_exc())
            finally:
                _tat_stdout_worker(router)
                self.ui(self._xong)

        threading.Thread(target=boc, daemon=True).start()

    def _xong(self):
        self.dang_chay = False
        self.nut_chay.config(state='normal')
        self.nut_dung.config(state='disabled')
        self.tt.config(text='Xong')

    def yeu_cau_dung(self):
        self.dung_lai.set()
        self.log('Đã yêu cầu dừng, đợi bài hiện tại xong...', 'canh')

    # ------------------------------------------------------------ các việc
    def viec_do_model(self):
        A = self._ap_cau_hinh()
        if not os.environ.get('GOOGLE_API_KEY'):
            print('Chưa có Google API key. Điền ở tab Cấu hình rồi bấm Lưu.')
            return
        print('== DÒ MODEL ==')
        ds = A.do_model()
        if ds:
            self.ui(lambda: self._chon_model(ds))

    def _chon_model(self, ds):
        self._model_dung_luong = {d['ten']: d for d in ds}
        self.cb_model['values'] = [d['ten'] for d in ds]
        if self.v_model.get() not in self._model_dung_luong:
            self.v_model.set(ds[0]['ten'])
            self.log(f'Đã chọn sẵn model {ds[0]["ten"]}. Nhớ bấm Lưu cấu hình.', 'ok')
        self._cap_nhat_dung_luong()

    def _cap_nhat_dung_luong(self):
        dl = getattr(self, '_model_dung_luong', {}).get(self.v_model.get())
        if not dl:
            self.v_dung_luong.set('')
            return
        nghi = '  |  có suy nghĩ ngầm (cần MAX_TOKENS cao hơn)' if dl['nghi'] else ''
        self.v_dung_luong.set(f'Dung lượng: vào {dl["vao"]:,} token  |  '
                              f'ra {dl["ra"]:,} token{nghi}')

    def viec_kiem_tra_wp(self):
        A = self._ap_cau_hinh()
        ma = self.v_site.get()
        print(f'== KIỂM TRA WORDPRESS: {ma} ==')
        A.kiem_tra_wp(ma, A.doc_san_pham(None, ma))

    def bat_dau_sinh(self):
        """Chạy ở LUỒNG CHÍNH: đọc hết dữ liệu giao diện rồi mới giao cho luồng nền."""
        if self.dang_chay:
            messagebox.showwarning('Đang bận', 'Đang có việc chạy.')
            return
        try:
            cfg = {'ma_site': self.v_site_chay.get(), 'mau_key': self.v_mau.get(),
                   'che_do': self.v_che_do.get(), 'so': int(self.v_so.get() or 1),
                   'bo_qua': int(self.v_bo_qua.get() or 0),
                   'nghi': float(self.v_nghi.get() or 0), 'tiep': bool(self.v_tiep.get())}
        except ValueError:
            messagebox.showerror('Sai số', 'Số bài, bỏ qua, nghỉ phải là số.')
            return
        self._ap_cau_hinh()
        if cfg['che_do'] in ('nhap', 'dang'):
            if not os.environ.get(f'WP_{cfg["ma_site"].upper()}_URL'):
                messagebox.showwarning('Thiếu', f'Chưa cấu hình WordPress cho '
                                                f'{cfg["ma_site"]} ở tab Cấu hình.')
                return
        if cfg['che_do'] == 'dang' and not messagebox.askyesno(
                'Xác nhận', 'Bài sẽ hiện ra ngoài cho khách thấy NGAY LẬP TỨC.\n\n'
                            'Chắc chắn chưa?'):
            return
        self.chay_nen(lambda: self.viec_sinh_bai(cfg))

    def viec_sinh_bai(self, cfg):
        A = self._ap_cau_hinh()
        import prompts as P
        ma_site, mau_key, che_do = cfg['ma_site'], cfg['mau_key'], cfg['che_do']
        tat_ca = A.doc_san_pham(None, ma_site)
        if not tat_ca:
            print('Kho dữ liệu trống. Vào tab 0 nhập Excel trước.')
            return
        rows = A.chon_dong(tat_ca, ma_site, mau_key, cfg['so'], cfg['bo_qua'], cfg['tiep'])
        if not rows:
            print('Không có sản phẩm nào trong khoảng đã chọn.')
            return

        print(f'== BẮT ĐẦU: {len(rows)} bài | site {ma_site} | '
              f'mẫu "{P.MAU[mau_key]["ten"]}" | chế độ {che_do} ==')
        self.ui(lambda: self.tien_do.config(maximum=len(rows), value=0))
        client = A.tao_client() if che_do != 'thu' else None
        dem = {'DA_DANG': 0, 'DA_SINH': 0, 'BI_CHAN': 0, 'LOI': 0}

        for i, row in enumerate(rows, 1):
            if self.dung_lai.is_set():
                print('Đã dừng theo yêu cầu.')
                break
            self.ui(lambda i=i, s=row['sku'], n=len(rows): (
                self.tien_do.config(value=i),
                self.lb_tien_do.config(text=f'Bài {i}/{n}: {s}')))
            try:
                kq = A.sinh_mot_bai(row, ma_site, mau_key, tat_ca, che_do, client)
                dem[kq['trang_thai']] += 1
                gc = f'  ({kq["ghi_chu"]})' if kq['ghi_chu'] else ''
                print(f'  [{i}/{len(rows)}] {kq["trang_thai"]} {kq["sku"]}{gc} '
                      f'{kq["link"]}'.rstrip())
            except SystemExit as e:
                print(str(e))
                break
            except Exception as e:
                dem['LOI'] += 1
                print(f'  [{i}/{len(rows)}] LỖI {row["sku"]}: {e}')
                A.ghi_bai_loi(row, ma_site, mau_key, e)
            if i < len(rows) and che_do != 'thu' and cfg['nghi']:
                self.dung_lai.wait(cfg['nghi'])

        tom = (f'Đăng {dem["DA_DANG"]} | sinh {dem["DA_SINH"]} | '
               f'chặn {dem["BI_CHAN"]} | lỗi {dem["LOI"]}')
        print(f'== XONG. {tom} ==')
        print(f'   File nằm ở: {BASE / "output"}')
        self.ui(lambda: (self.lb_tien_do.config(text='Xong. ' + tom),
                         self.nap_dashboard()))

    def _dong(self):
        if self.dang_chay and not messagebox.askyesno(
                'Đang chạy', 'Đang có việc chạy dở. Thoát luôn?'):
            return
        self.dung_lai.set()
        self.v3_dung_lai.set()   # Ver 3.5: báo dừng cả luồng Ver 3 đang chạy dở (nếu có)
        # Ver 4.2 audit debt: đóng app phải báo dừng mọi worker event đã tồn tại.
        for ten_event in ('jobs_dung_lai', 'v3_enhance_batch_dung'):
            ev = getattr(self, ten_event, None)
            if ev is not None:
                ev.set()
        # Ver 1.7 — VÁ TỔNG QUÁT thay vì huỷ đúng 1 job cố định: bản cũ chỉ
        # huỷ `_boc_hang_doi_job`, không đụng tới các after() job KHÁC đang
        # chờ (VD job debounce resize mới thêm Ver 1.6, hoặc bất kỳ after()
        # nào rải rác trong code) — job nào lỡ còn treo lúc destroy() thì
        # vẫn có thể bắn "invalid command name .../main thread is not in
        # main loop" y hệt lỗi GPT chỉ ra (test_v37_batch_real.py), chỉ là
        # xảy ra ở CHỖ KHÁC ngoài _boc_hang_doi. Dùng `after info` của Tcl
        # để liệt kê + huỷ MỌI job đang chờ trên cửa sổ này, không cần biết
        # trước tên/biến lưu job đó.
        try:
            for job_id in self.tk.eval('after info').split():
                try:
                    self.after_cancel(job_id)
                except Exception:
                    pass
        except Exception:
            pass
        self.destroy()


if __name__ == '__main__':
    PhanMem().mainloop()
