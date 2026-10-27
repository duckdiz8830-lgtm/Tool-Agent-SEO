# -*- coding: utf-8 -*-
"""
panel_anh.py — Ver 6.3. Giao diện đề xuất ảnh từ kho ảnh gốc công ty.

CẶP VỚI: kho_anh_nguon.py (module lõi, chỉ đọc)

NGUYÊN TẮC GIỮ NGUYÊN:
  - CHỈ ĐỀ XUẤT. Bấm "Chọn ảnh này" chỉ bắn callback + copy đường dẫn.
    Không tự gắn ảnh vào SKU, không ghi DB, không gọi WooCommerce.
  - Mắt người duyệt, tool chỉ rút ngắn đường đi.

ĐANG ĐƯỢC GỌI TỪ: tab_anh.py -> nút "Kho ảnh công ty", cạnh nút "Google Images".

      import kho_anh_nguon as KAN
      from panel_anh import mo_cua_so_anh
      mo_cua_so_anh(cha, goc_anh=KAN.goc_kho(), **KAN.tu_row(row),
                    khi_chon=lambda dd: ...)

CHẠY THỬ ĐỘC LẬP:
      python panel_anh.py "D:\\W-ANH GOC" "EMIC-250" "bien ap" "EMIC"
"""

from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable

from kho_anh_nguon import KhoAnh, UngVien

try:
    from PIL import Image, ImageTk
    CO_PIL = True
except ImportError:
    CO_PIL = False

# --- giao diện ---
CAO_THUMB = 150
RONG_THUMB = 180
SO_COT = 4
MAU_NEN = "#f5f5f5"
MAU_O = "#ffffff"
MAU_CHON = "#2d7ff9"
MAU_DA_DUNG = "#d94b4b"
MAU_CHU_PHU = "#777777"


class PanelDeXuatAnh(ttk.Frame):
    """Lưới thumbnail ứng viên. Nhúng vào Frame/Toplevel bất kỳ."""

    def __init__(
        self,
        cha,
        goc_anh: str,
        khi_chon: Callable[[str], None] | None = None,
        lay_da_dung: Callable[[], set] | None = None,
        **kw,
    ):
        super().__init__(cha, **kw)
        self.goc_anh = goc_anh
        self.khi_chon = khi_chon
        self.lay_da_dung = lay_da_dung          # hàm -> set `hash_goc` đã gán cho bài khác
        self.kho = KhoAnh(goc_anh)

        self.ung_vien: list[UngVien] = []
        self.o_widget: list[tk.Frame] = []
        self.dang_chon: int | None = None
        self._anh_giu: dict[int, "ImageTk.PhotoImage"] = {}   # giữ ref chống GC
        self._hang_doi: queue.Queue = queue.Queue()
        self._the_he = 0                        # chống thumbnail của lượt cũ đè lượt mới

        self.sku = self.loai = self.hang = ""

        self._dung_giao_dien()
        self.after(120, self._bom_thumbnail)

    # ------------------------------------------------------------ giao diện

    def _dung_giao_dien(self) -> None:
        # thanh trên
        tren = ttk.Frame(self)
        tren.pack(fill="x", padx=8, pady=(8, 4))

        self.lb_tieu_de = ttk.Label(tren, text="Chưa chọn SKU", font=("Segoe UI", 10, "bold"))
        self.lb_tieu_de.pack(side="left")

        ttk.Button(tren, text="Quét lại kho", command=self.quet_lai, width=13).pack(side="right")
        ttk.Button(tren, text="Mở thư mục gốc", command=self._mo_goc, width=15).pack(side="right", padx=(0, 6))

        # thanh lọc
        loc = ttk.Frame(self)
        loc.pack(fill="x", padx=8, pady=(0, 6))

        ttk.Label(loc, text="Lọc tên:").pack(side="left")
        self.o_loc = ttk.Entry(loc, width=22)
        self.o_loc.pack(side="left", padx=(4, 12))
        self.o_loc.bind("<KeyRelease>", lambda e: self._ve_luoi())

        self.bien_px = tk.StringVar(value="0")
        ttk.Label(loc, text="Rộng tối thiểu:").pack(side="left")
        cb = ttk.Combobox(loc, textvariable=self.bien_px, width=7, state="readonly",
                          values=["0", "500", "600", "800", "1000", "1200"])
        cb.pack(side="left", padx=(4, 12))
        cb.bind("<<ComboboxSelected>>", lambda e: self.tai_lai())

        self.bien_an_da_dung = tk.BooleanVar(value=False)
        ttk.Checkbutton(loc, text="Ẩn ảnh đã dùng", variable=self.bien_an_da_dung,
                        command=self._ve_luoi).pack(side="left")

        self.lb_dem = ttk.Label(loc, text="", foreground=MAU_CHU_PHU)
        self.lb_dem.pack(side="right")

        # vùng cuộn
        bao = ttk.Frame(self)
        bao.pack(fill="both", expand=True, padx=8)

        self.canvas = tk.Canvas(bao, bg=MAU_NEN, highlightthickness=0)
        thanh = ttk.Scrollbar(bao, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=thanh.set)
        thanh.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.khung_luoi = tk.Frame(self.canvas, bg=MAU_NEN)
        self.cua_so_luoi = self.canvas.create_window((0, 0), window=self.khung_luoi, anchor="nw")
        self.khung_luoi.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind(
            "<Configure>", lambda e: self.canvas.itemconfig(self.cua_so_luoi, width=e.width)
        )
        for w in (self.canvas, self.khung_luoi):
            w.bind("<MouseWheel>", self._cuon)
            w.bind("<Button-4>", self._cuon)
            w.bind("<Button-5>", self._cuon)

        # thanh dưới
        duoi = ttk.Frame(self)
        duoi.pack(fill="x", padx=8, pady=8)

        self.lb_duong_dan = ttk.Label(duoi, text="—", foreground=MAU_CHU_PHU)
        self.lb_duong_dan.pack(side="left", fill="x", expand=True)

        self.nut_chon = ttk.Button(duoi, text="Chọn ảnh này", command=self._bam_chon,
                                   state="disabled", width=14)
        self.nut_chon.pack(side="right")
        self.nut_mo = ttk.Button(duoi, text="Mở trong Explorer", command=self._bam_mo,
                                 state="disabled", width=17)
        self.nut_mo.pack(side="right", padx=(0, 6))

    def _cuon(self, e) -> None:
        buoc = -1 if getattr(e, "delta", 0) > 0 or getattr(e, "num", 0) == 4 else 1
        self.canvas.yview_scroll(buoc, "units")

    # ------------------------------------------------------------ nạp dữ liệu

    def nap_kho(self, ep_quet_lai: bool = False) -> int:
        """Quét/đọc cache. Gọi một lần lúc mở app cho nhanh."""
        n = self.kho.nap_index(ep_quet_lai=ep_quet_lai)
        self.lb_dem.config(text=f"kho: {n} ảnh / {len(self.kho.index)} folder")
        return n

    def quet_lai(self) -> None:
        self.lb_dem.config(text="đang quét lại…")
        self.update_idletasks()
        self.nap_kho(ep_quet_lai=True)
        self.tai_lai()

    def tai_sku(self, sku: str, loai: str = "", hang: str = "") -> None:
        """Điểm vào chính: đổi SKU đang xem."""
        self.sku, self.loai, self.hang = sku, loai, hang
        nhan = f"{sku}"
        if loai or hang:
            nhan += f"   ({loai}{' · ' if loai and hang else ''}{hang})"
        self.lb_tieu_de.config(text=nhan)
        if not self.kho.index:
            self.nap_kho()
        self.tai_lai()

    def tai_lai(self) -> None:
        if not self.sku:
            return
        try:
            da_dung = self.lay_da_dung() if self.lay_da_dung else ()
        except Exception:
            da_dung = ()          # nguồn "đã dùng" hỏng thì mất nhãn, không mất panel
        try:
            nguong = int(self.bien_px.get())
        except ValueError:
            nguong = 0
        self.ung_vien = self.kho.de_xuat(
            sku=self.sku, loai=self.loai, hang=self.hang,
            hash_da_dung=da_dung, toi_thieu_px=nguong, gioi_han=48,
        )
        self._ve_luoi()

    # ------------------------------------------------------------ vẽ lưới

    def _loc_hien(self) -> list[tuple[int, UngVien]]:
        chu = self.o_loc.get().strip().lower()
        an = self.bien_an_da_dung.get()
        ra = []
        for i, uv in enumerate(self.ung_vien):
            if an and uv.da_dung:
                continue
            if chu and chu not in uv.ten_file.lower() and chu not in uv.thu_muc.lower():
                continue
            ra.append((i, uv))
        return ra

    def _ve_luoi(self) -> None:
        for w in self.khung_luoi.winfo_children():
            w.destroy()
        self.o_widget = []
        self._anh_giu.clear()
        self.dang_chon = None
        self._dat_nut(False)
        self.lb_duong_dan.config(text="—")
        self._the_he += 1
        the_he = self._the_he

        hien = self._loc_hien()
        if not hien:
            tk.Label(
                self.khung_luoi, bg=MAU_NEN, fg=MAU_CHU_PHU, justify="left",
                text=("Không có ứng viên nào.\n\n"
                      "Bấm 'Mở thư mục gốc' để tự tìm, hoặc hạ 'Rộng tối thiểu'."),
                font=("Segoe UI", 10), padx=20, pady=30,
            ).grid(row=0, column=0, sticky="w")
            self._goi_y_folder()
            return

        for vi_tri, (chi_so, uv) in enumerate(hien):
            o = self._ve_o(uv, chi_so)
            o.grid(row=vi_tri // SO_COT, column=vi_tri % SO_COT, padx=6, pady=6, sticky="n")
            self.o_widget.append(o)
            self._hang_doi.put((the_he, chi_so, uv.duong_dan))

        self.canvas.yview_moveto(0)

    def _ve_o(self, uv: UngVien, chi_so: int) -> tk.Frame:
        o = tk.Frame(self.khung_luoi, bg=MAU_O, bd=2, relief="flat",
                     highlightbackground="#dddddd", highlightthickness=1)
        o._chi_so = chi_so                                # type: ignore[attr-defined]

        anh = tk.Label(o, bg=MAU_O, width=RONG_THUMB, height=CAO_THUMB, text="…",
                       fg=MAU_CHU_PHU, compound="center")
        anh.pack(padx=4, pady=(4, 2))
        o.lb_anh = anh                                    # type: ignore[attr-defined]

        ten = uv.ten_file if len(uv.ten_file) <= 26 else uv.ten_file[:23] + "…"
        tk.Label(o, text=ten, bg=MAU_O, font=("Segoe UI", 8), width=24).pack()

        mo_ta = f"{uv.kich_thuoc}  ·  {uv.diem}đ"
        tk.Label(o, text=mo_ta, bg=MAU_O, fg=MAU_CHU_PHU, font=("Segoe UI", 8)).pack()

        tm = uv.thu_muc if len(uv.thu_muc) <= 26 else uv.thu_muc[:23] + "…"
        tk.Label(o, text=tm, bg=MAU_O, fg=MAU_CHU_PHU, font=("Segoe UI", 7)).pack(pady=(0, 2))

        if uv.da_dung:
            tk.Label(o, text="ĐÃ DÙNG", bg=MAU_DA_DUNG, fg="white",
                     font=("Segoe UI", 7, "bold"), padx=4).pack(pady=(0, 4))
        else:
            tk.Frame(o, bg=MAU_O, height=6).pack()

        for w in [o] + list(o.winfo_children()):
            w.bind("<Button-1>", lambda e, i=chi_so: self._chon_o(i))
            w.bind("<Double-Button-1>", lambda e, i=chi_so: (self._chon_o(i), self._bam_mo()))
            w.bind("<MouseWheel>", self._cuon)
            w.bind("<Button-4>", self._cuon)
            w.bind("<Button-5>", self._cuon)
        return o

    def _goi_y_folder(self) -> None:
        ds = self.kho.thu_muc_goi_y(self.loai, self.hang)[:5]
        if not ds:
            return
        khung = tk.Frame(self.khung_luoi, bg=MAU_NEN)
        khung.grid(row=1, column=0, sticky="w", padx=20)
        tk.Label(khung, text="Thư mục nên mở tay:", bg=MAU_NEN,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))
        for tm in ds:
            ttk.Button(khung, text=Path(tm).name,
                       command=lambda t=tm: self.kho.mo_thu_muc(t)).pack(anchor="w", pady=1)

    # ------------------------------------------------------------ thumbnail nền

    def _bom_thumbnail(self) -> None:
        """Kéo 1 job/lượt, load ở thread phụ, vẽ ở main thread."""
        try:
            the_he, chi_so, duong_dan = self._hang_doi.get_nowait()
        except queue.Empty:
            self.after(60, self._bom_thumbnail)
            return

        if the_he != self._the_he or not CO_PIL:
            self.after(1, self._bom_thumbnail)
            return

        def chay():
            im = None
            try:
                with Image.open(duong_dan) as g:
                    g.draft("RGB", (RONG_THUMB * 2, CAO_THUMB * 2))   # decode nhanh
                    g = g.convert("RGB")
                    g.thumbnail((RONG_THUMB, CAO_THUMB), Image.LANCZOS)
                    im = g.copy()
            except Exception:
                im = None
            self.after(0, lambda: self._gan_thumbnail(the_he, chi_so, im))

        threading.Thread(target=chay, daemon=True).start()

    def _gan_thumbnail(self, the_he: int, chi_so: int, im) -> None:
        if the_he == self._the_he:
            o = next((w for w in self.o_widget
                      if w.winfo_exists() and getattr(w, "_chi_so", None) == chi_so), None)
            if o is not None:
                lb = o.lb_anh                                  # type: ignore[attr-defined]
                if im is None:
                    lb.config(text="(lỗi ảnh)")
                else:
                    ph = ImageTk.PhotoImage(im)
                    self._anh_giu[chi_so] = ph
                    lb.config(image=ph, text="", width=RONG_THUMB, height=CAO_THUMB)
        self.after(1, self._bom_thumbnail)

    # ------------------------------------------------------------ tương tác

    def _chon_o(self, chi_so: int) -> None:
        muc_tieu = next((w for w in self.o_widget
                         if w.winfo_exists() and getattr(w, "_chi_so", None) == chi_so), None)
        if muc_tieu is None:
            return
        for o in self.o_widget:
            if o.winfo_exists():
                o.config(highlightbackground="#dddddd", highlightthickness=1)
        muc_tieu.config(highlightbackground=MAU_CHON, highlightthickness=2)
        self.dang_chon = chi_so
        uv = self.ung_vien[chi_so]
        self.lb_duong_dan.config(text=uv.duong_dan)
        self._dat_nut(True)

    def _dat_nut(self, bat: bool) -> None:
        tt = "normal" if bat else "disabled"
        self.nut_chon.config(state=tt)
        self.nut_mo.config(state=tt)

    def _bam_mo(self) -> None:
        if self.dang_chon is not None:
            self.kho.mo_thu_muc(self.ung_vien[self.dang_chon].duong_dan)

    def _bam_chon(self) -> None:
        """KHÔNG gắn ảnh. Chỉ copy đường dẫn + bắn callback."""
        if self.dang_chon is None:
            return
        dd = self.ung_vien[self.dang_chon].duong_dan
        try:
            self.clipboard_clear()
            self.clipboard_append(dd)
        except tk.TclError:
            pass
        self.lb_duong_dan.config(text=f"đã copy: {dd}")
        if self.khi_chon:
            self.khi_chon(dd)

    def _mo_goc(self) -> None:
        ds = self.kho.thu_muc_goi_y(self.loai, self.hang)
        self.kho.mo_thu_muc(ds[0] if ds else self.goc_anh)


# ---------------------------------------------------------------- cửa sổ rời

def mo_cua_so_anh(
    cha,
    goc_anh: str,
    sku: str,
    loai: str = "",
    hang: str = "",
    khi_chon: Callable[[str], None] | None = None,
    lay_da_dung: Callable[[], set] | None = None,
) -> tk.Toplevel:
    """Mở cửa sổ đề xuất ảnh. Đây là hàm nút bấm trong SONEALEO nên gọi."""
    cs = tk.Toplevel(cha)
    cs.title(f"Đề xuất ảnh — {sku}")
    cs.geometry("860x680")
    cs.minsize(700, 480)

    p = PanelDeXuatAnh(cs, goc_anh=goc_anh, khi_chon=khi_chon, lay_da_dung=lay_da_dung)
    p.pack(fill="both", expand=True)
    p.tai_sku(sku=sku, loai=loai, hang=hang)

    cs.transient(cha)
    return cs


# ---------------------------------------------------------------- chạy thử

if __name__ == "__main__":
    import sys

    goc = sys.argv[1] if len(sys.argv) > 1 else "."
    sku = sys.argv[2] if len(sys.argv) > 2 else "EMIC-250-22/0.4"
    loai = sys.argv[3] if len(sys.argv) > 3 else "máy biến áp"
    hang = sys.argv[4] if len(sys.argv) > 4 else "EMIC"

    goc_root = tk.Tk()
    goc_root.withdraw()
    cs = mo_cua_so_anh(goc_root, goc_anh=goc, sku=sku, loai=loai, hang=hang,
                       khi_chon=lambda dd: print("CALLBACK chọn:", dd))
    cs.protocol("WM_DELETE_WINDOW", goc_root.destroy)
    goc_root.mainloop()
