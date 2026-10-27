# -*- coding: utf-8 -*-
"""Ver 5.8 — Tiện ích dựng giao diện dùng chung.

VÌ SAO TÁCH RIÊNG, KHÔNG NHÉT VÀO giac_cam.py

    Khi chuyển tab_seo_post sang hợp đồng, phát hiện một hồi quy thật:
    bản cũ gọi app._v3_tab_cuon() — hàm đó dựng Canvas + Scrollbar + bắt
    con lăn chuột rồi trả về frame bên trong. Bản viết lại dùng ttk.Frame
    trần nên tab 4 khối KHÔNG CUỘN ĐƯỢC, tràn khỏi cửa sổ là mất nút.

    Cách sai: thêm chân thứ 6 vào giac_cam ('tab_cuon').
    Vì sao sai: chân cắm là thứ module CẦN TỪ VỎ ỨNG DỤNG (log, luồng nền,
    DB, cấu hình). Khung cuộn không cần gì từ vỏ cả — nó là tkinter thuần.
    Nhét vào hợp đồng thì hợp đồng phình dần theo mỗi tiện ích mới, đúng
    cách God Class được nuôi lớn, chỉ khác chỗ đứng.

    QUY TẮC PHÂN LOẠI:
        Cần state/dịch vụ của vỏ  -> chân cắm trong giac_cam.py
        Chỉ cần tkinter           -> tiện ích ở đây, import thẳng

    Module tính năng import file này trực tiếp. Không đi qua giac.
"""
import tkinter as tk
from tkinter import ttk

NEN_MAC_DINH = '#F8FAFC'        # khớp V3_BG trong giao-dien.py


def khung_cuon(cha, padding=16, nen=NEN_MAC_DINH, style_frame='V3.TFrame'):
    """Trả (ngoai, trong): `ngoai` để add vào Notebook, `trong` để dựng nội dung.

    Chép nguyên hành vi của PhanMem._v3_tab_cuon: canvas cuộn dọc, thanh
    cuộn bên phải, nội dung khớp bề rộng, con lăn chuột chỉ ăn khi trỏ vào
    vùng này (bind khi <Enter>, gỡ khi <Leave> — nếu không thì cuộn ở tab
    này lại làm nhảy tab khác).
    """
    try:
        ngoai = ttk.Frame(cha, style=style_frame)
    except tk.TclError:
        ngoai = ttk.Frame(cha)

    canvas = tk.Canvas(ngoai, bg=nen, highlightthickness=0)
    sb = ttk.Scrollbar(ngoai, orient='vertical', command=canvas.yview)
    canvas.configure(yscrollcommand=sb.set)
    canvas.pack(side='left', fill='both', expand=True)
    sb.pack(side='right', fill='y')

    try:
        trong = ttk.Frame(canvas, padding=padding, style=style_frame)
    except tk.TclError:
        trong = ttk.Frame(canvas, padding=padding)
    cua_so = canvas.create_window((0, 0), window=trong, anchor='nw')

    trong.bind('<Configure>', lambda _e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>', lambda e: canvas.itemconfig(cua_so, width=e.width))

    def _cuon(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    canvas.bind('<Enter>', lambda _e: canvas.bind_all('<MouseWheel>', _cuon))
    canvas.bind('<Leave>', lambda _e: canvas.unbind_all('<MouseWheel>'))
    return ngoai, trong


def the(cha, tieu_de, padding=14, style_frame='V3.TLabelframe'):
    """Một khối 'card' viền/nền theo palette Ver 3, dùng lặp ở mọi tab.

    Chép từ PhanMem._v3_the — 7 lời gọi trong nhóm ui_anh sắp tách. Là
    tkinter thuần, không cần gì từ vỏ ứng dụng -> tiện ích, không phải chân.
    """
    try:
        khung = ttk.LabelFrame(cha, text=tieu_de, style=style_frame, padding=padding)
    except tk.TclError:
        khung = ttk.LabelFrame(cha, text=tieu_de, padding=padding)
    khung.pack(fill='x', pady=(0, 14))
    return khung
