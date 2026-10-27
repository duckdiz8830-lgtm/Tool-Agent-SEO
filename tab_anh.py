# -*- coding: utf-8 -*-
"""TAB ẢNH BÀI VIẾT — Ver 3.7, đợt 1.

Ba cột:
  trái   — danh sách bài + trạng thái ảnh, lọc được
  giữa   — 5 ô vai trò của bài đang chọn, thumbnail hoặc viền trống
  phải   — thao tác: mở thư mục, đăng ảnh, ảnh chưa gán

KHÔNG phụ thuộc AI. Không phụ thuộc tkinterdnd2 (kéo thả từ Explorer để
đợt sau — đợt 1 dùng hộp thoại chọn file, một cú bấm là xong).

Tab này KHÔNG render bài, KHÔNG gọi Gemini. Nó chỉ đọc thư mục, ghi
meta.json và gọi xu_ly_anh khi bấm Đăng.
"""

import os
import subprocess
import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from urllib.parse import quote_plus

import workspace_anh as WS


def _gom_loi_anh(danh_sach_loi):
    """Ver 4.4.1.6 (UX) — gom lỗi upload theo LOẠI, không liệt kê từng dòng.

    12 ảnh cùng dính WAF thì người dùng cần đúng một câu 'bị chặn, bấm lại',
    không phải 12 khối HTML. Trả chuỗi ngắn để đưa vào hộp thoại.
    """
    import re as _re
    nhom = {}
    for d in danh_sach_loi or []:
        t = str(d)
        if _re.search(r'\b403\b', t):
            khoa = ('Bị chặn ở tầng server (403 — WAF/mod_security)',
                    'Do gửi quá nhanh chứ không phải sai quyền. '
                    'Bấm lại "Cập nhật ảnh lên WordPress" — slot lỗi vẫn giữ để thử lại.')
        elif _re.search(r'\b429\b', t):
            khoa = ('Bị giới hạn tốc độ (429)', 'Chờ vài phút rồi bấm lại.')
        elif _re.search(r'\b(500|502|503|504)\b', t):
            khoa = ('Máy chủ web lỗi/quá tải (5xx)', 'Thử lại sau ít phút.')
        elif _re.search(r'\b401\b', t):
            khoa = ('Sai thông tin đăng nhập (401)',
                    'Kiểm user + Application Password ở tab Cấu hình.')
        elif _re.search(r'\b413\b', t):
            khoa = ('Ảnh quá lớn so với giới hạn host (413)', 'Giảm kích thước ảnh.')
        elif _re.search(r'Timeout|ConnectionError|RequestException', t, _re.I):
            khoa = ('Mạng chập chờn / hết giờ chờ', 'Kiểm mạng rồi bấm lại.')
        else:
            khoa = ('Lỗi khác', 'Xem Nhật ký bên phải để biết chi tiết.')
        nhom.setdefault(khoa, 0)
        nhom[khoa] += 1

    dong = ['%d ảnh chưa lên được:' % sum(nhom.values())]
    for (ten, cach), n in sorted(nhom.items(), key=lambda x: -x[1]):
        dong.append('  • %s — %d ảnh' % (ten, n))
        dong.append('    %s' % cach)
    dong.append('\n(Chi tiết kỹ thuật đã ghi vào Nhật ký.)')
    return '\n'.join(dong)

# Ver 4.4 D2 — Pillow stock trên Windows không luôn có HEIC/AVIF decoder.
# Nếu pillow-heif đã được cài từ requirements.txt thì đăng ký opener một lần;
# thiếu dependency vẫn không làm chết tab JPG/PNG/WebP cũ.
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except Exception:
    pass

CAO_THUMB = 104
MAU_TRANG_THAI = {
    'CHƯA CÓ THƯ MỤC': '#8a8f98',
    'CHƯA CÓ ẢNH': '#8a8f98',
}
BO_LOC = [('tat_ca', 'Tất cả'), ('chua_anh', 'Chưa có ảnh'),
          ('lech', 'Lệch'), ('da_dang', 'Đã lên WP')]


class TabAnh:
    # Ver 5.9 — chuyển sang hợp đồng giac_cam.py. Trước đây nhận thẳng `app`
    # và gọi app.ui / app.chay_nen_phase2 / app.log — 2 điểm chạm cuối cùng
    # của toàn hệ. Nay đi qua giắc cắm: cùng hành vi, nhưng module không còn
    # biết vỏ ứng dụng là cái gì, và chạy được với GiacCamGia headless.
    def __init__(self, nb, giac=None):
        self.giac = giac
        self.f = ttk.Frame(nb, padding=10)
        self.bai = []          # [dict] toàn bộ bài
        self.dang_hien = []
        self.chon = None       # bài đang xem
        self.thumb = {}        # giữ tham chiếu PhotoImage, không thì Tk xoá mất
        self._sort_anh_col = 'stt'
        self._sort_anh_desc = False
        self._iid_map = {}
        self._dung()
        self.nap()

    # -------------------------------------------------- giao diện
    def _dung(self):
        f = self.f
        thanh = ttk.Frame(f)
        thanh.pack(fill='x', pady=(0, 8))
        ttk.Label(thanh, text='Thư mục ảnh gốc:').pack(side='left')
        self.v_goc = tk.StringVar(value=self._goc_mac_dinh())
        ttk.Entry(thanh, textvariable=self.v_goc, width=46).pack(side='left', padx=6)
        ttk.Button(thanh, text='Chọn...', command=self._chon_goc).pack(side='left')
        ttk.Button(thanh, text='Nạp lại', command=self.nap).pack(side='left', padx=(12, 0))
        ttk.Button(thanh, text='Tạo thư mục cho toàn bộ bài đã đăng',
                   command=self._tao_hang_loat).pack(side='right')
        ttk.Button(thanh, text='Gán ảnh cho họ', command=self._mo_anh_ho).pack(side='right', padx=(0, 8))

        than = ttk.Frame(f)
        than.pack(fill='both', expand=True)

        # ---- cột trái: danh sách bài
        trai = ttk.Frame(than)
        trai.pack(side='left', fill='both', expand=True)
        loc = ttk.Frame(trai)
        loc.pack(fill='x')
        self.v_loc = tk.StringVar(value='tat_ca')
        for k, n in BO_LOC:
            ttk.Radiobutton(loc, text=n, value=k, variable=self.v_loc,
                            command=self._ap_loc).pack(side='left', padx=(0, 8))
        self.nhan_dem = ttk.Label(loc, text='')
        self.nhan_dem.pack(side='right')

        # Ver 4.4 C1/C3/C5 — tìm ngay khi gõ + lọc theo họ.
        loc2 = ttk.Frame(trai)
        loc2.pack(fill='x', pady=(5, 0))
        ttk.Label(loc2, text='Tìm').pack(side='left')
        self.v_tim_anh = tk.StringVar()
        self.o_tim_anh = ttk.Entry(loc2, textvariable=self.v_tim_anh, width=18)
        self.o_tim_anh.pack(side='left', padx=(5, 10))
        self.v_tim_anh.trace_add('write', lambda *_: self._ap_loc())
        ttk.Label(loc2, text='Họ').pack(side='left')
        self.v_ho_anh = tk.StringVar(value='(tất cả)')
        self.cb_ho_anh = ttk.Combobox(loc2, textvariable=self.v_ho_anh, width=22,
                                     state='readonly', values=['(tất cả)'])
        self.cb_ho_anh.pack(side='left', padx=(5, 8))
        self.cb_ho_anh.bind('<<ComboboxSelected>>', lambda _e: self._ap_loc())
        self.nhan_dong = ttk.Label(loc2, text='dòng 0/0')
        self.nhan_dong.pack(side='right')

        # Ver 4.4 C6 — thao tác nhiều dòng.
        bulk = ttk.Frame(trai)
        bulk.pack(fill='x', pady=(5, 0))
        ttk.Button(bulk, text='Gán ảnh chung…', command=self._gan_anh_chung).pack(side='left')
        ttk.Button(bulk, text='Đăng ảnh hàng loạt', command=self._dang_hang_loat).pack(side='left', padx=6)
        self.nut_dong_bo_wp_id = ttk.Button(bulk, text='ĐỒNG BỘ WP ID', command=self._dong_bo_wp_id)
        self.nut_dong_bo_wp_id.pack(side='left', padx=(2, 0))
        # Ver 5.5 — dọn ảnh hàng loạt. Mở cửa sổ riêng vì đây là nhóm thao
        # tác PHÁ HUỶ, không để lẫn nút với nhóm thao tác thường.
        ttk.Button(bulk, text='Dọn ảnh…', command=self._mo_don_anh).pack(side='right')

        cot = ('stt', 'ma', 'ten', 'anh', 'nguon', 'tt')
        self.bang = ttk.Treeview(trai, columns=cot, show='headings', height=18, selectmode='extended')
        for c, n, w in (('stt', 'STT', 46), ('ma', 'Mã hàng', 120), ('ten', 'Tên bài', 260),
                        ('anh', 'Ảnh', 60), ('nguon', 'Nguồn', 72), ('tt', 'Trạng thái', 130)):
            self.bang.heading(c, text=n, command=lambda cc=c: self._sap_xep_anh(cc))
            self.bang.column(c, width=w, anchor='center' if c in ('stt', 'anh') else 'w')
        self.bang.pack(fill='both', expand=True, pady=(6, 0))
        self.bang.bind('<<TreeviewSelect>>', self._bam_bai)
        self.bang.bind('<Control-f>', self._focus_tim_anh)

        # ---- cột phải: 5 ô. Ver 3.9: phần ô được cuộn dọc riêng;
        # cụm nút hành động nằm NGOÀI canvas nên luôn nhìn thấy ở đáy panel.
        phai = ttk.Frame(than, width=450, padding=(12, 0, 0, 0))
        phai.pack(side='left', fill='y')
        phai.pack_propagate(False)
        self.nhan_bai = ttk.Label(phai, text='Chọn một bài bên trái',
                                  font=('Segoe UI', 11, 'bold'), wraplength=410)
        self.nhan_bai.pack(anchor='w', fill='x')
        self.nhan_duong_dan = ttk.Label(phai, text='', foreground='#6b7789',
                                        wraplength=410)
        self.nhan_duong_dan.pack(anchor='w', fill='x', pady=(2, 8))

        # Ver 4.3 Windows hotfix: pack vùng action ở ĐÁY trước, rồi canvas
        # mới fill phần còn lại. Như vậy DPI/theme Windows không thể cho canvas
        # ăn mất parcel của nút.
        ha = ttk.Frame(phai)
        ha.pack(side='bottom', fill='x', pady=(8, 0))
        ttk.Button(ha, text='Mở thư mục', command=self._mo_thu_muc).pack(side='left')
        ttk.Button(ha, text='Google Images', command=self._mo_google_images).pack(side='left', padx=(6, 0))
        # Ver 6.3 — tra kho ảnh gốc công ty. Đặt cạnh Google Images vì cùng
        # một nhu cầu ("bài này thiếu ảnh, kiếm ở đâu"), khác nguồn: một cái
        # ra web, một cái vào kho nội bộ. Kho nội bộ nên đứng sau, vì nó chỉ
        # có ích khi đã cấu hình đường dẫn.
        ttk.Button(ha, text='Kho ảnh công ty',
                   command=self._mo_kho_anh_nguon).pack(side='left', padx=(6, 0))
        self.nut_dang = ttk.Button(ha, text='Cập nhật ảnh lên WordPress', command=self._dang)
        self.nut_dang.pack(side='left', padx=8)
        ttk.Label(phai, foreground='#6b7789', wraplength=410,
                  text='Ô trống thì ẩn trên web, không in chữ hướng dẫn cho khách. '
                       'Có 3 ảnh thì đăng 3, không đòi đủ 5.').pack(side='bottom', anchor='w', fill='x', pady=(6, 0))

        khung_cuon = ttk.Frame(phai)
        khung_cuon.pack(fill='both', expand=True)
        self.canvas_o = tk.Canvas(khung_cuon, highlightthickness=0, borderwidth=0)
        # tk.Scrollbar width cố định nhìn rõ hơn ttk theme trên Windows.
        self.cuon_doc = tk.Scrollbar(khung_cuon, orient='vertical', width=16, command=self.canvas_o.yview)
        self.canvas_o.configure(yscrollcommand=self.cuon_doc.set)
        self.canvas_o.pack(side='left', fill='both', expand=True)
        self.cuon_doc.pack(side='right', fill='y')
        self.khung_o = ttk.Frame(self.canvas_o)
        self._khung_o_window = self.canvas_o.create_window((0, 0), window=self.khung_o, anchor='nw')
        self.khung_o.bind('<Configure>', self._cap_nhat_vung_cuon)
        self.canvas_o.bind('<Configure>',
                           lambda e: self.canvas_o.itemconfigure(self._khung_o_window, width=e.width))
        # MouseWheel trên Windows đi tới widget con nằm dưới con trỏ (Label/Button),
        # không tự bubble về Canvas. Bind toàn app nhưng handler CHỈ ăn event nếu
        # con trỏ đang nằm trong canvas, nên không cướp scroll của bảng bên trái.
        self.canvas_o.bind_all('<MouseWheel>', self._cuon_chuot, add='+')
        self.canvas_o.bind('<Button-4>', lambda _e: self.canvas_o.yview_scroll(-1, 'units'))
        self.canvas_o.bind('<Button-5>', lambda _e: self.canvas_o.yview_scroll(1, 'units'))

    def _cap_nhat_vung_cuon(self, _e=None):
        self.canvas_o.configure(scrollregion=self.canvas_o.bbox('all'))

    def _cuon_chuot(self, e):
        """Windows: delta thường ±120. Chỉ scroll khi chuột nằm trong canvas ảnh."""
        try:
            px, py = self.canvas_o.winfo_pointerx(), self.canvas_o.winfo_pointery()
            x0, y0 = self.canvas_o.winfo_rootx(), self.canvas_o.winfo_rooty()
            if not (x0 <= px < x0 + self.canvas_o.winfo_width() and
                    y0 <= py < y0 + self.canvas_o.winfo_height()):
                return None
        except Exception:
            pass
        delta = int(getattr(e, 'delta', 0) or 0)
        if delta:
            buoc = -1 if delta > 0 else 1
            self.canvas_o.yview_scroll(buoc, 'units')
            return 'break'
        return None

    def _goc_mac_dinh(self):
        try:
            import cauhinh as C
            v = os.environ.get('THU_MUC_ANH') or getattr(C, 'THU_MUC_ANH', '')
            if v:
                return v
        except Exception:
            pass
        return str(Path.home() / 'LOTECH' / 'IMAGES')

    def _chon_goc(self):
        d = filedialog.askdirectory(title='Chọn thư mục ảnh gốc')
        if d:
            self.v_goc.set(d)
            self.nap()

    # -------------------------------------------------- nạp dữ liệu
    def nap(self):
        try:
            import db_phase2 as DB
            import render_phase2 as R
            import cauhinh as C
        except Exception as e:
            messagebox.showerror('Ảnh', f'Không nạp được cơ sở dữ liệu:\n{e}')
            return
        goc = self.v_goc.get().strip()
        self.bai = []
        try:
            con = DB.ket_noi()
            try:
                for dset in DB.liet_ke_dataset(con):
                    pid = dset['profile_id']
                    if not WS.ma_vai_tro(pid):
                        continue     # profile chưa khai vai trò -> bỏ qua, KHÔNG đoán
                    sp = DB.liet_ke_san_pham(con, dataset_id=dset['dataset_id'],
                                             profile_id=pid)
                    wc = C.doc_website() or {}
                    site_hien_tai = wc.get('site_key') or None
                    # Audit 3.7 mục 13: chỉ lấy bài của site hiện tại. Nếu một
                    # record có nhiều mẫu trên cùng site thì không tự chọn wp_id
                    # của mẫu nào — để None an toàn hơn gắn nhầm bài.
                    tt_theo_record = {}
                    for d in DB.dashboard(con, dataset_id=dset['dataset_id'],
                                          profile_id=pid, site=site_hien_tai):
                        tt_theo_record.setdefault(d['record_id'], []).append(d)
                    tt_bai = {rid: ds[0] for rid, ds in tt_theo_record.items() if len(ds) == 1}
                    for i, r in enumerate(sp, 1):
                        sku = r.get('publish_sku') or r.get('ma_goc') or ''
                        sheet = self._sheet_cua(r, dset)
                        tm = WS.tim_workspace(goc, sheet, sku) if goc and sku else None
                        bv_tt = tt_bai.get(r['record_id'], {})
                        tt, co, tong, nguon = WS.trang_thai_hieu_luc(
                            goc, sheet, r, tm, ma_site=C.MA_SITE_VER3, wp_post_id=bv_tt.get('wp_id'))
                        so_dong = int(r.get('source_row') or i)
                        slug = R.dung_slug(r)
                        ho = WS.ho_san_pham(r) or {}
                        self.bai.append({
                            'row': r, 'sku': sku, 'sheet': sheet, 'so_dong': so_dong,
                            'ten': str(r.get('ten_goc', '') or '').replace('\n', ' '),
                            'slug': slug, 'dataset_id': dset['dataset_id'], 'record_id': r['record_id'],
                            'site': bv_tt.get('site'), 'mau': bv_tt.get('mau'),
                            'wp_id': bv_tt.get('wp_id'),
                            'thu_muc': tm, 'tt': tt, 'co': co, 'tong': tong, 'nguon': nguon,
                            'ho_key': ho.get('key', ''), 'ho_nhan': ho.get('nhan', ''),
                        })
            finally:
                con.close()
        except Exception as e:
            messagebox.showerror('Ảnh', f'Lỗi đọc dữ liệu:\n{e}')
            return
        ho_values = sorted({b['ho_nhan'] for b in self.bai if b.get('ho_nhan')}, key=str.casefold)
        self.cb_ho_anh['values'] = ['(tất cả)'] + ho_values
        if self.v_ho_anh.get() not in self.cb_ho_anh['values']:
            self.v_ho_anh.set('(tất cả)')
        self._ap_loc()

    @staticmethod
    def _sheet_cua(row, dset):
        """Tên sheet dùng làm cấp thư mục trên. Ưu tiên record_id vì nó đã
        chứa tên sheet gốc; không có thì lùi về source_file, cuối cùng mới
        dùng profile_id."""
        rid = str(row.get('record_id') or '')
        if '::' in rid:
            phan = rid.split('::')
            if len(phan) >= 2 and phan[1]:
                return phan[1]
        return Path(str(dset.get('source_file') or '')).stem or row.get('profile_id', 'khac')

    def _focus_tim_anh(self, _e=None):
        self.o_tim_anh.focus_set()
        self.o_tim_anh.selection_range(0, 'end')
        return 'break'

    def _sap_xep_anh(self, cot):
        if self._sort_anh_col == cot:
            self._sort_anh_desc = not self._sort_anh_desc
        else:
            self._sort_anh_col, self._sort_anh_desc = cot, False
        self._ap_loc()

    def _ap_loc(self):
        k = self.v_loc.get()
        if k == 'tat_ca':
            ds = list(self.bai)
        elif k == 'chua_anh':
            ds = [b for b in self.bai if b['co'] == 0]
        elif k == 'lech':
            ds = [b for b in self.bai if b['tt'].startswith('LỆCH')]
        else:
            ds = [b for b in self.bai if b['tt'].startswith(('Đã lên Media', 'Đã gắn vào bài', 'ĐÃ ĐĂNG'))]

        tim = self.v_tim_anh.get().strip().casefold() if hasattr(self, 'v_tim_anh') else ''
        if tim:
            ds = [b for b in ds if tim in (' '.join([b.get('sku',''), b.get('ten',''),
                                                      str((b.get('row') or {}).get('thuong_hieu',''))])).casefold()]
        ho = self.v_ho_anh.get() if hasattr(self, 'v_ho_anh') else '(tất cả)'
        if ho and ho != '(tất cả)':
            ds = [b for b in ds if b.get('ho_nhan') == ho]

        col = self._sort_anh_col
        def key(b):
            if col == 'stt': return int(b.get('so_dong') or 0)
            if col == 'ma': return b.get('sku','').casefold()
            if col == 'ten': return b.get('ten','').casefold()
            if col == 'anh': return int(b.get('co') or 0)
            if col == 'nguon': return b.get('nguon','').casefold()
            if col == 'tt': return b.get('tt','').casefold()
            return 0
        ds.sort(key=key, reverse=self._sort_anh_desc)
        self.dang_hien = ds

        self.bang.delete(*self.bang.get_children())
        self._iid_map = {}
        for n, b in enumerate(self.dang_hien, 1):
            nhan_nguon = {'rieng': 'riêng', 'ho': 'họ', 'trong': 'trống'}.get(b.get('nguon'), 'trống')
            iid = f'anh_{n}'
            self._iid_map[iid] = b
            self.bang.insert('', 'end', iid=iid, values=(n, b['sku'], b['ten'][:70],
                                                        f"{b['co']}/{b['tong']}", nhan_nguon, b['tt']))
        thieu = sum(1 for b in self.bai if b['co'] == 0)
        lech = sum(1 for b in self.bai if b['tt'].startswith('LỆCH'))
        self.nhan_dem.config(text=f'{len(self.dang_hien)} bài · {thieu} chưa có ảnh · {lech} lệch')
        self.nhan_dong.config(text=f'dòng 0/{len(self.bai)}')

    # -------------------------------------------------- 5 ô
    def _bam_bai(self, _e=None):
        s = self.bang.selection()
        if not s:
            return
        iid = self.bang.focus() or s[0]
        b = self._iid_map.get(iid)
        if not b:
            return
        self.chon = b
        try:
            n = self.bang.index(iid) + 1
        except Exception:
            n = 0
        self.nhan_dong.config(text=f'dòng {n}/{len(self.bai)}')
        self._ve_o()

    def _bai_da_chon(self):
        return [self._iid_map[i] for i in self.bang.selection() if i in self._iid_map]

    @staticmethod
    def _downloads():
        d = Path.home() / 'Downloads'
        return str(d if d.exists() else Path.home())

    @staticmethod
    def _filetypes_anh():
        return [('Ảnh', '*.jpg *.jpeg *.jfif *.png *.webp *.heic *.bmp *.avif *.tif *.tiff'),
                ('Tất cả', '*.*')]

    def _gan_anh_chung(self):
        ds_bai = self._bai_da_chon()
        if not ds_bai:
            messagebox.showinfo('Ảnh', 'Chọn một hoặc nhiều dòng trước.')
            return
        vi_tri = simpledialog.askinteger('Gán ảnh chung', 'Gán vào ô số mấy (1–5)?',
                                        parent=self.f, minvalue=1, maxvalue=5)
        if not vi_tri:
            return
        p = filedialog.askopenfilename(title='Chọn một ảnh dùng chung', initialdir=self._downloads(),
                                       filetypes=self._filetypes_anh())
        if not p:
            return
        goc = self.v_goc.get().strip()
        ok, bo = 0, 0
        for b in ds_bai:
            roles = [v for v, _, _ in WS.vai_tro_cua((b.get('row') or {}).get('profile_id',''))]
            if vi_tri > len(roles):
                bo += 1
                continue
            tm = b.get('thu_muc') or WS.tao_workspace(goc, b['sheet'], b['so_dong'], b['row'],
                                                       wp_post_id=b.get('wp_id'), title=b['ten'], slug=b.get('slug'))
            b['thu_muc'] = tm
            WS.gan_anh(tm, p, roles[vi_tri - 1])
            ok += 1
        self.nap()
        messagebox.showinfo('Gán ảnh chung', f'Đã gán: {ok} bài. Ảnh dùng chung được phép reuse giữa nhiều SKU, không chặn.' + (f' Bỏ qua: {bo} bài không có ô số {vi_tri}.' if bo else ''))

    def _go_anh_hang_loat(self):
        """Ver 4.6.2 — gỡ ảnh của NHIỀU bài cùng lúc.

        Chỉ gỡ khỏi meta.json, KHÔNG xoá file ảnh (giữ đúng nguyên tắc của
        workspace_anh.bo_anh: tool không tự xoá dữ liệu người dùng).
        """
        ds_bai = self._bai_da_chon()
        if not ds_bai:
            messagebox.showinfo('Ảnh', 'Chọn một hoặc nhiều dòng trước.')
            return
        co_anh = [b for b in ds_bai if b.get('thu_muc') and b.get('co')]
        if not co_anh:
            messagebox.showinfo('Gỡ ảnh hàng loạt',
                                'Các dòng đang chọn không có ảnh nào để gỡ.')
            return
        vi_tri = simpledialog.askinteger(
            'Gỡ ảnh hàng loạt',
            f'{len(co_anh)} bài có ảnh.\n\n'
            f'Gỡ ô số mấy (1–5)?  Nhập 0 = gỡ TẤT CẢ các ô.',
            parent=self.f, minvalue=0, maxvalue=5)
        if vi_tri is None:
            return
        nhan = 'TẤT CẢ các ô' if vi_tri == 0 else f'ô số {vi_tri}'
        if not messagebox.askyesno(
                'Xác nhận gỡ ảnh',
                f'Gỡ {nhan} của {len(co_anh)} bài?\n\n'
                f'File ảnh KHÔNG bị xoá — chỉ bỏ gán khỏi bài. '
                f'Muốn xoá file thì tự xoá trong thư mục.',
                default='no'):
            return
        go, bo = 0, 0
        for b in co_anh:
            roles = [v for v, _, _ in WS.vai_tro_cua((b.get('row') or {}).get('profile_id', ''))]
            if vi_tri == 0:
                for r in roles:
                    WS.bo_anh(b['thu_muc'], r)
                go += 1
            elif vi_tri <= len(roles):
                WS.bo_anh(b['thu_muc'], roles[vi_tri - 1])
                go += 1
            else:
                bo += 1
        self.nap()
        messagebox.showinfo(
            'Gỡ ảnh hàng loạt',
            f'Đã gỡ {nhan} của {go} bài. File ảnh vẫn còn trong thư mục.'
            + (f' Bỏ qua {bo} bài không có ô số {vi_tri}.' if bo else ''))

    @staticmethod
    def _wp_id_khong_hop_le(loi):
        t = str(loi or '').lower()
        return ('rest_post_invalid_id' in t or 'woocommerce_rest_product_invalid_id' in t
                or 'invalid product id' in t or 'http 404' in t)

    def _resolve_wp_id_theo_sku(self, b, ghi_db=True):
        """BUG-C — DB thiếu/mất wp_id không có nghĩa bài không tồn tại.

        Dùng đúng resolver chống đăng trùng đã có: Woo GET products?sku=...
        Tìm thấy -> phục hồi wp_id vào bai_viet_phase2 rồi caller tiếp tục.
        Không tìm thấy và lỗi API là hai trạng thái KHÁC NHAU.
        """
        if b.get('wp_id'):
            return {'ok': True, 'wp_id': b.get('wp_id'), 'tu_db': True}
        did, rid, site, mau = b.get('dataset_id'), b.get('record_id'), b.get('site'), b.get('mau')
        sku = str(b.get('sku') or (b.get('row') or {}).get('publish_sku')
                  or (b.get('row') or {}).get('ma_goc') or '').strip()
        if not sku:
            return {'ok': False, 'loi': 'Record không có SKU để tra WordPress.', 'not_found': False}
        if not all((did, rid, site, mau)):
            return {'ok': False, 'loi': 'Thiếu identity DB (dataset/record/site/mẫu), không ghi WP ID để tránh gắn nhầm.',
                    'not_found': False}
        import autopost as A
        import cauhinh as C
        import db_phase2 as DB
        try:
            wp_id = A.tim_san_pham_woo_theo_sku(C.MA_SITE_VER3, sku)
        except (Exception, SystemExit) as e:
            return {'ok': False, 'loi': f'Không thể tra WP ID cho SKU {sku}: {type(e).__name__}: {e}',
                    'not_found': False}
        if not wp_id:
            return {'ok': False, 'loi': f'Bài chưa tồn tại trên WordPress (không tìm thấy SKU {sku}).',
                    'not_found': True}
        wp_id = str(wp_id)
        if ghi_db:
            con = DB.ket_noi()
            try:
                DB.cap_nhat_bai_viet(con, did, rid, site, mau, wp_id=wp_id)
            finally:
                con.close()
        b['wp_id'] = wp_id
        # Workspace riêng cũng cần biết post ID mới phục hồi để meta không còn lệch.
        if b.get('thu_muc'):
            try:
                meta = WS.doc_meta(b['thu_muc']) or {}
                meta['wp_post_id'] = wp_id
                WS.ghi_meta(b['thu_muc'], meta)
            except Exception:
                pass
        return {'ok': True, 'wp_id': wp_id, 'tu_db': False}

    def _gan_anh_vao_bai_ngay(self, b, kq):
        """Ver 4.4.1.3 — attach mọi ảnh HỢP LỆ, kể cả batch có slot lỗi.

        Một ảnh lỗi nén/upload không được phép biến 4 ảnh tốt thành orphan
        trong Media Library. Chỉ dùng item có cả URL + media_id; item lỗi giữ
        nguyên để lần sau retry riêng.
        """
        anh_hop_le = [a for a in (kq.get('anh') or [])
                      if a.get('url') and a.get('wp_media_id')]
        if not anh_hop_le:
            return {'ok': False, 'gan_bai': False, 'loi': 'Không có ảnh upload/reuse hợp lệ để gắn vào bài.',
                    'partial': bool(kq.get('loi'))}
        resolved = ({'ok': True, 'wp_id': b.get('wp_id'), 'tu_db': True}
                    if b.get('wp_id') else self._resolve_wp_id_theo_sku(b))
        if not resolved.get('ok'):
            return {'ok': False, 'gan_bai': False, 'loi': resolved.get('loi', 'Không tra được WP ID.'),
                    'not_found': resolved.get('not_found', False)}
        wp_id = resolved['wp_id']
        did, rid, site, mau = b.get('dataset_id'), b.get('record_id'), b.get('site'), b.get('mau')
        if not all((did, rid, site, mau)):
            return {'ok': False, 'gan_bai': False, 'loi': 'Thiếu identity bài (dataset/record/site/mẫu), không cập nhật để tránh gắn nhầm.'}
        import ai_wp_adapter as AWP
        import cauhinh as C
        import db_phase2 as DB
        import dulieu as DL
        import xu_ly_anh as X
        con = DB.ket_noi()
        try:
            bv = DB.lay_bai_viet(con, did, rid, site, mau)
            html_goc = (bv or {}).get('html') or ''
            nguon_html = 'DB'
            if not html_goc:
                # Ver 4.4.1.6 — DB rỗng html KHÔNG có nghĩa là bài không tồn
                # tại. Bài đăng từ đợt cũ (hoặc bằng công cụ khác) thì WordPress
                # có body, DB thì không. Trước bản này gặp trường hợp đó là
                # dừng hẳn với "không đoán vị trí ảnh" — trong khi bản THẬT
                # đang nằm sẵn trên WP, chỉ cần đọc về.
                #
                # Đọc content.raw chứ không phải rendered: rendered đã qua
                # wpautop/shortcode, PUT ngược lại là hỏng bài.
                wc0 = C.doc_website() or {}
                kq_doc = AWP.doc_noi_dung_bai_that(
                    wp_id, la_woo=(wc0.get('che_do_dang') == 'woo_product'))
                if kq_doc.get('ok') and (kq_doc.get('content') or '').strip():
                    html_goc = kq_doc['content']
                    nguon_html = 'WordPress'
                    # Lưu về DB để lần sau khỏi phải gọi mạng nữa.
                    try:
                        DB.cap_nhat_bai_viet(con, did, rid, site, mau, html=html_goc)
                    except Exception:
                        pass    # lưu hụt không sao, ảnh vẫn gắn được
                else:
                    return {'ok': False, 'gan_bai': False,
                            'loi': 'Không lấy được nội dung bài: DB chưa lưu HTML, '
                                   'và đọc từ WordPress cũng không được (%s). '
                                   'Ảnh đã lên Media, chỉ chưa chèn vào thân bài.'
                                   % (kq_doc.get('loi') or 'không rõ')}
            html_moi = X.chen_anh_vao_bai(html_goc, anh_hop_le)
            wc = C.doc_website() or {}
            la_woo = wc.get('che_do_dang') == 'woo_product'

            # C5: wp_id có nhưng đã chết -> invalidate -> lookup SKU -> retry đúng 1 lần.
            kq_body = AWP.cap_nhat_noi_dung_bai_that(wp_id, html_moi, la_woo=la_woo)
            if not kq_body.get('ok') and self._wp_id_khong_hop_le(kq_body.get('loi')):
                DB.cap_nhat_bai_viet(con, did, rid, site, mau, wp_id=None)
                b['wp_id'] = None
                resolved2 = self._resolve_wp_id_theo_sku(b)
                if not resolved2.get('ok'):
                    return {'ok': False, 'gan_bai': False,
                            'loi': 'WP ID cũ không hợp lệ; tra lại SKU thất bại: ' + resolved2.get('loi', '')}
                wp_id = resolved2['wp_id']
                kq_body = AWP.cap_nhat_noi_dung_bai_that(wp_id, html_moi, la_woo=la_woo)
            if not kq_body.get('ok'):
                return {'ok': False, 'gan_bai': False, 'body_ok': False, 'gallery_ok': False,
                        'loi': 'Cập nhật nội dung lỗi: ' + kq_body.get('loi', 'không rõ')}

            # Body đã thay đổi trên WordPress thì DB phải phản ánh NGAY, kể cả
            # request gallery phía sau thất bại. Không để remote/local lệch.
            DB.cap_nhat_bai_viet(con, did, rid, site, mau, html=html_moi, wp_id=wp_id)

            media_ids = []
            da_thay = set()
            for a in anh_hop_le:
                mid = a.get('wp_media_id')
                smid = str(mid)
                if smid not in da_thay:
                    da_thay.add(smid)
                    media_ids.append(mid)
            kq_gallery = AWP.gan_anh_vao_san_pham(wp_id, media_ids, la_woo=la_woo)
            stale_ids = {str(x) for x in (kq_gallery.get('invalid_media_ids') or [])}
            if not kq_gallery.get('ok') and stale_ids:
                # WordPress/Woo có thể đã xoá một attachment trong khi local
                # delivery/cache vẫn giữ ID cũ. Không để một ID chết kéo sập
                # cả gallery: vô hiệu đúng slot/site, purge cache upload,
                # loại ID stale rồi retry gallery đúng MỘT lần.
                stale_anh = [a for a in anh_hop_le if str(a.get('wp_media_id')) in stale_ids]
                anh_con = [a for a in anh_hop_le if str(a.get('wp_media_id')) not in stale_ids]
                try:
                    if b.get('sheet') and b.get('row'):
                        goc_anh = self.v_goc.get().strip() if hasattr(self, 'v_goc') else ''
                        WS.vo_hieu_delivery_media(goc_anh, b['sheet'], b['row'],
                                                  b.get('thu_muc'), C.MA_SITE_VER3, stale_anh)
                    for mid in stale_ids:
                        try:
                            DL.xoa_cache_anh_wp_theo_media(C.MA_SITE_VER3, mid)
                        except Exception:
                            pass
                except Exception:
                    pass

                if anh_con:
                    # Body lần đầu đã chứa URL stale. Render lại từ HTML gốc
                    # bằng CHỈ các ảnh còn hợp lệ rồi đồng bộ remote + DB.
                    html_moi = X.chen_anh_vao_bai(bv['html'], anh_con)
                    kq_body2 = AWP.cap_nhat_noi_dung_bai_that(wp_id, html_moi, la_woo=la_woo)
                    if not kq_body2.get('ok'):
                        return {'ok': False, 'gan_bai': False, 'body_ok': False, 'gallery_ok': False,
                                'stale_media_ids': sorted(stale_ids),
                                'loi': 'Đã phát hiện media stale nhưng cập nhật lại body lỗi: ' + kq_body2.get('loi', 'không rõ')}
                    DB.cap_nhat_bai_viet(con, did, rid, site, mau, html=html_moi, wp_id=wp_id)
                    media_ids = []
                    seen2 = set()
                    for a in anh_con:
                        mid = a.get('wp_media_id'); smid = str(mid)
                        if smid not in seen2:
                            seen2.add(smid); media_ids.append(mid)
                    kq_gallery = AWP.gan_anh_vao_san_pham(wp_id, media_ids, la_woo=la_woo)
                    if kq_gallery.get('ok'):
                        anh_hop_le = anh_con
                    else:
                        return {'ok': False, 'gan_bai': False, 'body_ok': True, 'gallery_ok': False,
                                'html': html_moi, 'wp_id': wp_id, 'stale_media_ids': sorted(stale_ids),
                                'loi': 'Đã loại media stale nhưng gallery retry vẫn lỗi: ' + kq_gallery.get('loi', 'không rõ')}
                else:
                    # Tất cả ID đều stale: khôi phục body gốc để không nhét URL
                    # chết vào bài. Slot đã được invalidate, lần bấm sau sẽ upload lại.
                    try:
                        AWP.cap_nhat_noi_dung_bai_that(wp_id, bv['html'], la_woo=la_woo)
                    except Exception:
                        pass
                    DB.cap_nhat_bai_viet(con, did, rid, site, mau, html=bv['html'], wp_id=wp_id)
                    return {'ok': False, 'gan_bai': False, 'body_ok': False, 'gallery_ok': False,
                            'wp_id': wp_id, 'stale_media_ids': sorted(stale_ids),
                            'loi': 'Tất cả media ID đều stale; đã xoá state/cache. Bấm cập nhật lại để upload lại ảnh.'}
            elif not kq_gallery.get('ok'):
                return {'ok': False, 'gan_bai': False, 'body_ok': True, 'gallery_ok': False,
                        'html': html_moi, 'wp_id': wp_id,
                        'loi': 'Body đã cập nhật nhưng gallery lỗi: ' + kq_gallery.get('loi', 'không rõ')}
            if b.get('sheet') and b.get('row'):
                try:
                    goc_anh = self.v_goc.get().strip() if hasattr(self, 'v_goc') else ''
                    WS.danh_dau_da_gan_vao_bai(goc_anh, b['sheet'], b['row'],
                                               b.get('thu_muc'), C.MA_SITE_VER3, wp_id, anh_hop_le)
                except Exception as e:
                    return {'ok': False, 'gan_bai': True, 'body_ok': True, 'gallery_ok': True,
                            'loi': f'Ảnh đã cập nhật WordPress nhưng không ghi được trạng thái local: {type(e).__name__}: {e}'}
            b['wp_id'] = wp_id
            return {'ok': True, 'gan_bai': True, 'body_ok': True, 'gallery_ok': True,
                    'partial': bool(kq.get('loi')) or bool(locals().get('stale_ids')),
                    'so_anh': len(anh_hop_le),
                    'stale_media_ids': sorted(locals().get('stale_ids', set())),
                    'html': html_moi, 'wp_id': wp_id,
                    'resolved': not resolved.get('tu_db', False)}
        finally:
            con.close()

    # ============================================================ Ver 5.5 — dọn ảnh
    def _mo_don_anh(self):
        """Cửa sổ dọn ảnh hàng loạt. Tách riêng vì đây là nhóm thao tác PHÁ
        HUỶ — không để nút xoá đứng cạnh nút đăng, bấm nhầm là mất ảnh.

        Ba tab theo mức độ không hồi lại được, xếp từ an toàn xuống nguy hiểm.
        """
        import threading
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog
        import don_anh as DA

        cs = tk.Toplevel(self)
        cs.title('Dọn ảnh hàng loạt')
        cs.geometry('900x620')

        ttk.Label(cs, text='Mọi thao tác mặc định CHẠY THỬ — xem báo cáo trước, '
                           'bỏ tick "Chạy thử" mới đụng thật.',
                  wraplength=860, foreground='#B00020').pack(anchor='w', padx=12, pady=(10, 6))

        nb = ttk.Notebook(cs)
        nb.pack(fill='both', expand=True, padx=12, pady=(0, 8))

        log = tk.Text(cs, height=9, wrap='word')
        log.pack(fill='both', expand=False, padx=12, pady=(0, 10))

        def ghi(t):
            log.insert('end', str(t) + '\n')
            log.see('end')
            cs.update_idletasks()

        def chay_nen(fn):
            threading.Thread(target=fn, daemon=True).start()

        # ---------------- Tab A: gỡ ảnh khỏi bài (hồi lại được) ----------------
        ta = ttk.Frame(nb, padding=12)
        nb.add(ta, text='  1. Gỡ khỏi bài (an toàn)  ')
        ttk.Label(ta, text='Bỏ ảnh khỏi sản phẩm/bài. File VẪN CÒN trong Media Library, '
                           'gắn lại lúc nào cũng được.', wraplength=830).pack(anchor='w')
        ha = ttk.Frame(ta)
        ha.pack(fill='x', pady=10)
        ttk.Label(ha, text='WP ID (cách nhau dấu phẩy):').pack(side='left')
        e_id = ttk.Entry(ha, width=40)
        e_id.pack(side='left', padx=6)
        ttk.Button(ha, text='Lấy từ dòng đang chọn ở bảng',
                   command=lambda: self._don_dien_wp_id(e_id)).pack(side='left')
        hb = ttk.Frame(ta)
        hb.pack(fill='x')
        ttk.Label(hb, text='Giữ lại N ảnh đầu:').pack(side='left')
        v_giu = tk.StringVar(value='1')
        ttk.Spinbox(hb, from_=0, to=10, width=5, textvariable=v_giu).pack(side='left', padx=6)
        ttk.Label(hb, text='(1 = giữ ảnh đại diện, gỡ hết gallery · 0 = gỡ sạch)').pack(side='left')
        v_thu_a = tk.BooleanVar(value=True)
        ttk.Checkbutton(ta, text='Chạy thử (chỉ xem, không đụng)', variable=v_thu_a).pack(anchor='w', pady=8)

        def _go():
            ids = [x.strip() for x in e_id.get().split(',') if x.strip().isdigit()]
            if not ids:
                messagebox.showwarning('Thiếu ID', 'Nhập ít nhất 1 WP ID.', parent=cs)
                return
            if not v_thu_a.get() and not messagebox.askyesno(
                    'Xác nhận', f'Gỡ ảnh khỏi {len(ids)} bài THẬT?', parent=cs):
                return

            def _w():
                ghi(f'--- Gỡ ảnh khỏi {len(ids)} bài (chạy thử={v_thu_a.get()}) ---')
                kq = DA.go_anh_khoi_bai(ids, la_woo=True, giu_lai_dau=int(v_giu.get() or 0),
                                        chay_thu=v_thu_a.get())
                if kq.get('loi'):
                    ghi('LỖI: ' + kq['loi'])
                    return
                for c in kq['chi_tiet']:
                    ghi(f"  #{c['wp_id']}: " + (
                        f"đang có {c.get('dang_co')} -> sẽ gỡ {c.get('se_go')}"
                        if c.get('chay_thu') else
                        (f"đã gỡ {c.get('da_go')}" if c['ok'] else 'LỖI ' + c.get('loi', ''))))
                ghi(f'Xong: {kq["so_xu_ly"]} bài.' + (f' Log: {kq["log"]}' if kq.get('log') else ''))
            chay_nen(_w)

        ttk.Button(ta, text='GỠ ẢNH', command=_go).pack(anchor='w')

        # ---------------- Tab B: xoá media WordPress ----------------
        tb = ttk.Frame(nb, padding=12)
        nb.add(tb, text='  2. Xoá media WordPress  ')
        ttk.Label(tb, text='Tìm media rồi xoá. Mặc định chỉ chuyển THÙNG RÁC (hồi được ~30 ngày) '
                           'và tự BỎ QUA ảnh đang gắn vào bài.', wraplength=830).pack(anchor='w')
        hc = ttk.Frame(tb)
        hc.pack(fill='x', pady=10)
        ttk.Label(hc, text='Tìm theo tên:').pack(side='left')
        e_tim = ttk.Entry(hc, width=26)
        e_tim.pack(side='left', padx=6)
        ttk.Label(hc, text='Upload trước ngày:').pack(side='left', padx=(10, 0))
        e_ngay = ttk.Entry(hc, width=12)
        e_ngay.insert(0, '')
        e_ngay.pack(side='left', padx=6)
        ttk.Label(hc, text='(YYYY-MM-DD, để trống = tất cả)').pack(side='left')

        bang_m = ttk.Treeview(tb, columns=('id', 'ten', 'ngay', 'gan'), show='headings',
                              height=8, selectmode='extended')
        for c, n, w in (('id', 'Media ID', 80), ('ten', 'Tên file', 380),
                        ('ngay', 'Ngày', 95), ('gan', 'Đang gắn vào bài', 150)):
            bang_m.heading(c, text=n)
            bang_m.column(c, width=w)
        bang_m.pack(fill='both', expand=True, pady=6)

        def _tim():
            def _w():
                ds, tong, loi = DA.liet_ke_media(e_tim.get().strip(), so_luong=100,
                                                 truoc_ngay=e_ngay.get().strip() or None)
                if loi:
                    ghi('LỖI: ' + loi)
                    return
                bang_m.delete(*bang_m.get_children())
                for m in ds:
                    bang_m.insert('', 'end', values=(m['id'], m['ten'], m['ngay'],
                                                     m['gan_vao'] or '— mồ côi —'))
                ghi(f'Tìm thấy {len(ds)} media (tổng {tong} trên site).')
            chay_nen(_w)

        def _tim_mo_coi():
            def _w():
                ghi('Đang quét media mồ côi (có thể mất 1-2 phút)...')
                ds, loi = DA.tim_anh_mo_coi(truoc_ngay=e_ngay.get().strip() or None)
                if loi:
                    ghi('LỖI: ' + loi)
                    return
                bang_m.delete(*bang_m.get_children())
                for m in ds:
                    bang_m.insert('', 'end', values=(m['id'], m['ten'], m['ngay'], '— mồ côi —'))
                ghi(f'{len(ds)} media KHÔNG gắn vào bài nào. Đây thường là rác của các lần '
                    f'upload lỗi — nhóm an toàn nhất để dọn.')
            chay_nen(_w)

        ttk.Button(hc, text='Tìm', command=_tim).pack(side='left', padx=(10, 0))
        ttk.Button(hc, text='Tìm ảnh MỒ CÔI', command=_tim_mo_coi).pack(side='left', padx=6)

        hd = ttk.Frame(tb)
        hd.pack(fill='x', pady=(4, 0))
        v_thu_b = tk.BooleanVar(value=True)
        v_force = tk.BooleanVar(value=False)
        ttk.Checkbutton(hd, text='Chạy thử', variable=v_thu_b).pack(side='left')
        ttk.Checkbutton(hd, text='XOÁ VĨNH VIỄN (không hồi được)',
                        variable=v_force).pack(side='left', padx=14)

        def _xoa():
            ids = [bang_m.item(i)['values'][0] for i in bang_m.selection()]
            if not ids:
                messagebox.showwarning('Chưa chọn', 'Chọn media trong bảng.', parent=cs)
                return
            xn = ''
            if v_force.get() and not v_thu_b.get():
                from tkinter import simpledialog
                xn = simpledialog.askstring(
                    'XOÁ VĨNH VIỄN',
                    f'Sắp xoá VĨNH VIỄN {len(ids)} ảnh. Không hồi lại được.\n'
                    f'Gõ đúng: {DA.XAC_NHAN_XOA}', parent=cs) or ''
                if xn != DA.XAC_NHAN_XOA:
                    ghi('Đã huỷ — chuỗi xác nhận không khớp.')
                    return

            def _w():
                ghi(f'--- Xoá {len(ids)} media (chạy thử={v_thu_b.get()}, '
                    f'vĩnh viễn={v_force.get()}) ---')
                kq = DA.xoa_media(ids, force=v_force.get(), chay_thu=v_thu_b.get(),
                                  xac_nhan=xn, bo_qua_dang_dung=True)
                if kq.get('loi'):
                    ghi('LỖI: ' + kq['loi'])
                    return
                for c in kq['chi_tiet']:
                    ghi(f"  media {c['media_id']}: " + (
                        'BỎ QUA — ' + c.get('ly_do', '') if c.get('bo_qua')
                        else (c.get('se') or ('OK' if c['ok'] else 'LỖI ' + c.get('loi', '')))))
                ghi(f'Xong: xoá {kq["so_xoa"]}, bỏ qua {kq["so_bo_qua"]}.'
                    + (f' Log: {kq["log"]}' if kq.get('log') else ''))
                if not v_thu_b.get():
                    _tim()
            chay_nen(_w)

        ttk.Button(hd, text='XOÁ ĐÃ CHỌN', command=_xoa).pack(side='right')

        # ---------------- Tab C: dọn file local ----------------
        tc = ttk.Frame(nb, padding=12)
        nb.add(tc, text='  3. Dọn file trên máy  ')
        ttk.Label(tc, text='Dọn ảnh trong thư mục local. Mặc định CHUYỂN sang thư mục '
                           '_da_xoa/ thay vì xoá thật — xoá file không có Undo.',
                  wraplength=830).pack(anchor='w')
        he = ttk.Frame(tc)
        he.pack(fill='x', pady=10)
        e_tm = ttk.Entry(he, width=52)
        e_tm.pack(side='left')
        ttk.Button(he, text='Chọn...',
                   command=lambda: (e_tm.delete(0, 'end'),
                                    e_tm.insert(0, filedialog.askdirectory(parent=cs) or ''))
                   ).pack(side='left', padx=6)
        hf = ttk.Frame(tc)
        hf.pack(fill='x')
        ttk.Label(hf, text='Chỉ file có tên chứa:').pack(side='left')
        e_mau = ttk.Entry(hf, width=22)
        e_mau.pack(side='left', padx=6)
        v_thu_c = tk.BooleanVar(value=True)
        v_rac = tk.BooleanVar(value=True)
        ttk.Checkbutton(tc, text='Chạy thử', variable=v_thu_c).pack(anchor='w', pady=(8, 0))
        ttk.Checkbutton(tc, text='Chuyển vào _da_xoa/ thay vì xoá hẳn (khuyên bật)',
                        variable=v_rac).pack(anchor='w')

        def _don_local():
            tm = e_tm.get().strip()
            if not tm:
                messagebox.showwarning('Thiếu', 'Chọn thư mục.', parent=cs)
                return
            if not v_thu_c.get() and not v_rac.get() and not messagebox.askyesno(
                    'Xác nhận', 'XOÁ HẲN file trên đĩa, không chuyển thùng rác. Chắc chưa?',
                    parent=cs):
                return

            def _w():
                kq = DA.xoa_anh_local(tm, e_mau.get().strip(), chay_thu=v_thu_c.get(),
                                      thung_rac=v_rac.get())
                if kq.get('loi'):
                    ghi('LỖI: ' + kq['loi'])
                    return
                ghi(f'{kq["so_file"]} file, {kq["tong_mb"]} MB'
                    + (' (chạy thử)' if kq.get('chay_thu') else
                       f' -> {kq.get("thung_rac") or "đã xoá hẳn"}'))
                for c in kq['chi_tiet'][:25]:
                    ghi(f'    {c["file"]}  {c["kb"]} KB')
                if len(kq['chi_tiet']) > 25:
                    ghi(f'    ... còn {len(kq["chi_tiet"]) - 25} file nữa')
            chay_nen(_w)

        ttk.Button(tc, text='DỌN', command=_don_local).pack(anchor='w', pady=8)

    def _don_dien_wp_id(self, entry):
        """Lấy wp_id của các dòng đang chọn ở bảng chính điền vào ô."""
        ids = []
        for i in getattr(self, 'bang', None).selection() if getattr(self, 'bang', None) else []:
            try:
                v = self.bang.item(i).get('values') or []
                for x in v:
                    if str(x).isdigit() and len(str(x)) >= 2:
                        ids.append(str(x))
                        break
            except Exception:
                pass
        entry.delete(0, 'end')
        entry.insert(0, ', '.join(dict.fromkeys(ids)))

    def _dong_bo_wp_id_core(self, ds_bai=None, ghi_log=print):
        """One-time repair DB <-> WordPress cho các row đang thiếu wp_id."""
        ds = list(ds_bai if ds_bai is not None else self.bai)
        seen = set()
        thong_ke = {'thieu': 0, 'tim_thay': 0, 'khong_tim_thay': 0, 'loi_api': 0, 'bo_qua_identity': 0}
        for b in ds:
            if b.get('wp_id'):
                continue
            key = (b.get('dataset_id'), b.get('record_id'), b.get('site'), b.get('mau'))
            if key in seen:
                continue
            seen.add(key)
            thong_ke['thieu'] += 1
            if not all(key):
                thong_ke['bo_qua_identity'] += 1
                ghi_log(f'[ĐỒNG BỘ WP ID] {b.get("sku")}: thiếu identity DB, bỏ qua an toàn.')
                continue
            kq = self._resolve_wp_id_theo_sku(b)
            if kq.get('ok'):
                thong_ke['tim_thay'] += 1
                ghi_log(f'[ĐỒNG BỘ WP ID] {b.get("sku")}: WP ID={kq.get("wp_id")}')
            elif kq.get('not_found'):
                thong_ke['khong_tim_thay'] += 1
                ghi_log(f'[ĐỒNG BỘ WP ID] {b.get("sku")}: KHÔNG TÌM THẤY')
            else:
                thong_ke['loi_api'] += 1
                ghi_log(f'[ĐỒNG BỘ WP ID] {b.get("sku")}: LỖI - {kq.get("loi")}')
        return thong_ke

    def _dong_bo_wp_id(self):
        ds = [b for b in self.bai if not b.get('wp_id')]
        if not ds:
            messagebox.showinfo('ĐỒNG BỘ WP ID', 'DB hiện không có record nào thiếu WP ID trong tab Ảnh.')
            return
        if not messagebox.askyesno('ĐỒNG BỘ WP ID',
                                   f'Tra WordPress theo SKU cho {len(ds)} record đang thiếu WP ID?\n\n'
                                   'Chỉ ghi lại ID tìm thấy; không tạo bài mới, không đăng lại nội dung.'):
            return
        def viec():
            kq = self._dong_bo_wp_id_core(ds, ghi_log=print)
            if self.giac:
                self.giac.ui(lambda k=kq: self._ket_thuc_dong_bo_wp_id(k))
            else:
                self._ket_thuc_dong_bo_wp_id(kq)
        if self.giac:
            self.giac.chay_nen(viec, ten='tab_anh')
        else:
            viec()

    def _ket_thuc_dong_bo_wp_id(self, kq):
        self.nap()
        messagebox.showinfo(
            'ĐỒNG BỘ WP ID',
            'Đồng bộ WP ID hoàn tất.\n\n'
            f"Thiếu trước khi chạy: {kq.get('thieu', 0)}\n"
            f"Tìm thấy: {kq.get('tim_thay', 0)}\n"
            f"Không tìm thấy: {kq.get('khong_tim_thay', 0)}\n"
            f"Lỗi API: {kq.get('loi_api', 0)}\n"
            f"Bỏ qua do thiếu identity: {kq.get('bo_qua_identity', 0)}")

    def _dang_hang_loat(self):
        ds_bai = list(self._bai_da_chon())
        if not ds_bai:
            messagebox.showinfo('Ảnh', 'Chọn một hoặc nhiều dòng trước.')
            return
        if not messagebox.askyesno('Đăng ảnh hàng loạt', f'Xử lý ảnh cho {len(ds_bai)} bài đã chọn?'):
            return
        goc = self.v_goc.get().strip()
        def viec():
            import xu_ly_anh as X
            import autopost as A
            import cauhinh as C
            def upload(duong_dan, ten, mime):
                return A._url_anh_tren_wp(C.MA_SITE_VER3, duong_dan, tra_media_id=True)
            ok = loi = partial = 0
            for b in ds_bai:
                try:
                    tm_ho = WS.tim_workspace_ho(goc, b['sheet'], b['row']) if goc else None
                    if not b.get('thu_muc') and not tm_ho:
                        continue
                    resolved = self._resolve_wp_id_theo_sku(b)
                    if not resolved.get('ok'):
                        raise RuntimeError(resolved.get('loi', 'Không tra được WP ID'))
                    kq = X.dang_anh_hieu_luc(goc, b['sheet'], b.get('thu_muc'), b['row'], C.MA_SITE_VER3,
                                        tieu_de=b['ten'], slug=b.get('slug',''), upload=upload,
                                        ghi_log=print)
                    # BUG-E: có slot lỗi vẫn attach các ảnh hợp lệ. Chỉ fail
                    # toàn bài khi không còn ảnh nào usable hoặc attach thật lỗi.
                    if not kq.get('anh'):
                        raise RuntimeError('; '.join(kq.get('loi', [])[:3]) or 'Không có ảnh hợp lệ để gắn.')
                    gan = self._gan_anh_vao_bai_ngay(b, kq)
                    if not gan.get('ok'):
                        raise RuntimeError(gan.get('loi', 'Không gắn được ảnh vào bài'))
                    if kq.get('loi') or gan.get('partial'):
                        partial += 1
                        ly_do = '; '.join(kq.get('loi', [])[:3])
                        if gan.get('stale_media_ids'):
                            ly_do += (('; ' if ly_do else '') +
                                      'media stale=' + ','.join(map(str, gan.get('stale_media_ids'))))
                        print(f'[Ảnh hàng loạt] {b.get("sku")}: PARTIAL - gắn {gan.get("so_anh", len(kq.get("anh", [])))} ảnh'
                              + (f'; {ly_do}' if ly_do else ''))
                    else:
                        ok += 1
                    for cb in kq.get('canh_bao', [])[:3]:
                        print(f'[Ảnh hàng loạt] {b.get("sku")}: cảnh báo fallback - {cb}')
                except Exception as e:
                    loi += 1
                    print(f'[Ảnh hàng loạt] {b.get("sku")}: {e}')
            if self.giac:
                self.giac.ui(lambda a=ok, b=loi, c=partial:
                             self._ket_thuc_dang_hang_loat(a, b, c))
            else:
                self._ket_thuc_dang_hang_loat(ok, loi, partial)
        if self.giac:
            self.giac.chay_nen(viec, ten='tab_anh')
        else:
            viec()

    def _ket_thuc_dang_hang_loat(self, ok, loi, partial=0):
        self.nap()
        messagebox.showinfo('Ảnh hàng loạt',
                            f'Xong: {ok} bài đầy đủ, {partial} bài một phần, lỗi {loi}.')

    def _mo_google_images(self):
        if not self.chon:
            messagebox.showinfo('Google Images', 'Chọn một bài trước.')
            return
        row = self.chon.get('row') or {}
        try:
            import kien_thuc_bien_thien as K
            d = K.dac_trung(row) or {}
        except Exception:
            d = {}
        # HF1 2026-08-11 — chỉ coi là máy biến áp khi router đã xác định đúng
        # outline_may_bien_ap. Profile may_bien_ap_do_luong còn chứa vỏ mạ kẽm,
        # đo lường và phụ kiện; kVA/profile không đủ để kết luận đây là MBA thật.
        la_mba = str(row.get('outline_id') or '') == 'outline_may_bien_ap'
        if la_mba:
            parts = ['máy biến áp']
            if d.get('loai') in ('dau', 'kho'):
                parts.append('dầu' if d['loai'] == 'dau' else 'khô')
            if d.get('hang'):
                parts.append(str(d['hang']))
            if d.get('kva') is not None:
                parts.append(f"{d['kva']:g}kVA")
            if d.get('pha'):
                parts.append(f"{d['pha']} pha")
        else:
            # Profile khác MBA chưa có bộ vai trò/query riêng ở task này: dùng
            # đúng tên sản phẩm hiện hữu thay vì gán nhầm tiền tố "máy biến áp".
            parts = [self.chon.get('ten') or self.chon.get('sku') or 'sản phẩm']
        q = ' '.join(parts)
        webbrowser.open('https://www.google.com/search?tbm=isch&q=' + quote_plus(q))

    def _mo_kho_anh_nguon(self):
        """Ver 6.3 — tra kho ảnh gốc công ty cho bài đang chọn.

        CHỈ ĐỀ XUẤT. Chọn xong chỉ copy đường dẫn vào clipboard; việc gán vào
        ô vai trò vẫn phải bấm "Chọn ảnh…" như cũ. Cố ý không tự gán: kho ảnh
        gốc chưa phân loại, tên folder chỉ nói được chủng loại + hãng chứ
        không nói được tấm này là mặt trước hay tem nhãn — máy đoán vai trò
        là đoán sai.
        """
        if not self.chon:
            messagebox.showinfo('Kho ảnh công ty', 'Chọn một bài trước.')
            return
        try:
            import kho_anh_nguon as KAN
            from panel_anh import mo_cua_so_anh
        except ImportError as e:
            messagebox.showerror('Kho ảnh công ty', f'Thiếu module: {e}')
            return

        goc = KAN.goc_kho()
        if not goc or not os.path.isdir(goc):
            messagebox.showinfo(
                'Kho ảnh công ty',
                'Chưa trỏ tới kho ảnh gốc.\n\n'
                'Chọn thư mục chứa toàn bộ ảnh chưa phân loại của công ty '
                '(thư mục có các folder con kiểu "BIEN AP TU EMIC", "DAU CAP 3M"…).')
            goc = filedialog.askdirectory(title='Chọn KHO ẢNH GỐC của công ty')
            if not goc:
                return
            try:
                import cauhinh as C
                C.ghi_env(KHO_ANH_NGUON=goc)
            except Exception:
                os.environ['KHO_ANH_NGUON'] = goc

        tham_so = KAN.tu_row(self.chon.get('row') or {})
        if not tham_so.get('sku'):
            tham_so['sku'] = self.chon.get('sku') or ''

        mo_cua_so_anh(self.f, goc_anh=goc, khi_chon=self._sau_khi_chon_kho,
                      lay_da_dung=self._anh_da_dung_trong_workspace, **tham_so)

    def _sau_khi_chon_kho(self, duong_dan):
        """Đã copy đường dẫn vào clipboard. Không gán — xem docstring trên."""
        messagebox.showinfo(
            'Kho ảnh công ty',
            'Đã copy đường dẫn:\n\n%s\n\n'
            'Bấm "Chọn ảnh…" ở ô muốn gán rồi dán vào ô File name.'
            % duong_dan)

    def _anh_da_dung_trong_workspace(self):
        """Tập `hash_goc` của mọi ảnh đã gán cho bất kỳ bài nào.

        Vì sao hash chứ không phải đường dẫn: WS.gan_anh() CHÉP ảnh vào thư mục
        bài và đổi tên khi trùng, nên đường dẫn nguồn không được lưu lại ở đâu
        cả. `hash_goc` là thứ duy nhất nối được tấm trong kho gốc với tấm đã
        gán — chính workspace_anh.dem_dung_chung() cũng so bằng khoá này.
        """
        ra = set()
        goc = self.v_goc.get().strip()
        if not goc or not os.path.isdir(goc):
            return ra
        try:
            for thu_muc_sheet in Path(goc).iterdir():
                if not thu_muc_sheet.is_dir():
                    continue
                for bai in thu_muc_sheet.iterdir():
                    if not bai.is_dir():
                        continue
                    m = WS.doc_meta(bai) or {}
                    for a in m.get('anh', []):
                        h = a.get('hash_goc') or a.get('hash')
                        if h:
                            ra.add(h)
        except OSError:
            pass
        return ra

    def _ve_o(self):
        for w in self.khung_o.winfo_children():
            w.destroy()
        self.thumb.clear()
        b = self.chon
        if not b:
            return
        self.nhan_bai.config(text=b['ten'])
        self.nhan_duong_dan.config(text=str(b['thu_muc'] or '(chưa có thư mục — bấm Tạo thư mục)'))

        pid = b['row'].get('profile_id', '')
        ds = WS.vai_tro_cua(pid)
        hieu_luc = WS.anh_hieu_luc(self.v_goc.get().strip(), b['sheet'], b['row'], b['thu_muc'])
        kq = {'o': hieu_luc['o']}

        for hang, (ma, nhan, huong_dan) in enumerate(ds):
            o = ttk.Frame(self.khung_o, relief='solid', borderwidth=1, padding=6)
            o.grid(row=hang, column=0, sticky='ew', pady=3)
            self.khung_o.columnconfigure(0, weight=1)
            a = kq['o'].get(ma)
            anh_lb = tk.Label(o, width=14, height=5, bg='#eef1f5',
                              text='(trống)' if not a else '')
            anh_lb.grid(row=0, column=0, rowspan=2, padx=(0, 8))
            if a:
                img = self._doc_thumb(a['duong_dan'])
                if img:
                    self.thumb[ma] = img
                    anh_lb.config(image=img, text='', width=0, height=0)
            ttk.Label(o, text=f'{hang + 1}. {nhan}',
                      font=('Segoe UI', 9, 'bold')).grid(row=0, column=1, sticky='w')
            nguon_o = hieu_luc.get('nguon_o', {}).get(ma, 'trong')
            nhan_nguon = 'RIÊNG' if nguon_o == 'rieng' else ('HỌ' if nguon_o == 'ho' else '')
            phu = ((f'[{nhan_nguon}] ' if nhan_nguon else '') + a.get('ten_tren_dia', '') +
                   '  ·  ' + a.get('trang_thai', '')) if a else huong_dan[:64]
            ttk.Label(o, text=phu, foreground='#6b7789',
                      wraplength=250).grid(row=1, column=1, sticky='w')
            nut = ttk.Frame(o)
            nut.grid(row=0, column=2, rowspan=2, sticky='e')
            ttk.Button(nut, text='Chọn ảnh…', width=11,
                       command=lambda m=ma: self._chon_anh(m)).pack()
            if a and nguon_o == 'rieng':
                ttk.Button(nut, text='Gỡ', width=11,
                           command=lambda m=ma: self._go(m)).pack(pady=(3, 0))
            o.columnconfigure(1, weight=1)

    def _doc_thumb(self, duong_dan):
        try:
            from PIL import Image, ImageTk
            with Image.open(duong_dan) as im:
                im = im.convert('RGB')
                r = CAO_THUMB / max(1, im.height)
                im = im.resize((max(1, int(im.width * r)), CAO_THUMB), Image.LANCZOS)
                return ImageTk.PhotoImage(im)
        except Exception:
            return None

    def _bao_dam_thu_muc(self):
        """Chưa có thư mục thì tạo ngay, khỏi bắt người dùng bấm hai lần."""
        b = self.chon
        if b['thu_muc']:
            return b['thu_muc']
        goc = self.v_goc.get().strip()
        if not goc:
            messagebox.showwarning('Ảnh', 'Chọn thư mục ảnh gốc trước.')
            return None
        tm = WS.tao_workspace(goc, b['sheet'], b['so_dong'], b['row'],
                              wp_post_id=b.get('wp_id'), title=b['ten'],
                              slug=b.get('slug'))
        b['thu_muc'] = tm
        return tm

    def _chon_anh(self, vai_tro):
        if not self.chon:
            return
        tm = self._bao_dam_thu_muc()
        if not tm:
            return
        ds = filedialog.askopenfilenames(
            title='Chọn ảnh', initialdir=self._downloads(), filetypes=self._filetypes_anh())
        if not ds:
            return
        vai_tro_all = [v for v, _, _ in WS.vai_tro_cua(self.chon['row'].get('profile_id', ''))]
        bat_dau = vai_tro_all.index(vai_tro) if vai_tro in vai_tro_all else 0
        if len(ds) == 1:
            dich = [vai_tro]
        else:
            # Ctrl-chọn nhiều: chỉ rót vào các ô đang TRỐNG từ ô được bấm trở đi,
            # rồi vòng về đầu nếu còn chỗ. Không ghi đè ảnh đang có ngoài ý muốn.
            hieu_luc = WS.anh_hieu_luc(self.v_goc.get().strip(), self.chon['sheet'],
                                       self.chon['row'], self.chon.get('thu_muc'))['o']
            thu_tu = vai_tro_all[bat_dau:] + vai_tro_all[:bat_dau]
            dich = [v for v in thu_tu if not hieu_luc.get(v)]
        for p, role in zip(ds, dich):
            try:
                WS.gan_anh(tm, p, role)
            except Exception as e:
                messagebox.showerror('Ảnh', f'{Path(p).name}: {e}')
                break
        self._lam_moi_bai()

    def _go(self, vai_tro):
        if self.chon and self.chon['thu_muc']:
            WS.bo_anh(self.chon['thu_muc'], vai_tro)
            self._lam_moi_bai()

    def _lam_moi_bai(self):
        b = self.chon
        if b:
            try:
                import cauhinh as C
                ma_site = C.MA_SITE_VER3
            except Exception:
                ma_site = None
            b['tt'], b['co'], b['tong'], b['nguon'] = WS.trang_thai_hieu_luc(
                self.v_goc.get().strip(), b['sheet'], b['row'], b.get('thu_muc'),
                ma_site=ma_site, wp_post_id=b.get('wp_id'))
        self._ve_o()
        self._ap_loc()

    def _mo_thu_muc(self):
        tm = self._bao_dam_thu_muc() if self.chon else None
        if not tm:
            return
        try:
            if sys.platform.startswith('win'):
                os.startfile(str(tm))
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', str(tm)])
            else:
                subprocess.Popen(['xdg-open', str(tm)])
        except Exception as e:
            messagebox.showerror('Ảnh', f'Không mở được thư mục:\n{e}')

    # -------------------------------------------------- hành động
    def _tao_hang_loat(self):
        goc = self.v_goc.get().strip()
        if not goc:
            messagebox.showwarning('Ảnh', 'Chọn thư mục ảnh gốc trước.')
            return
        if not messagebox.askyesno(
                'Tạo thư mục hàng loạt',
                f'Tạo thư mục + meta.json cho {len(self.bai)} bài?\n\n'
                'Thư mục đã có sẽ được giữ nguyên, chỉ cập nhật meta.'):
            return
        n = 0
        loi = []
        for b in self.bai:
            try:
                b['thu_muc'] = WS.tao_workspace(goc, b['sheet'], b['so_dong'],
                                                b['row'], wp_post_id=b.get('wp_id'),
                                                title=b['ten'], slug=b.get('slug'))
                n += 1
            except Exception as e:
                loi.append(f"{b['sku']}: {e}")
        self.nap()
        msg = f'Đã tạo/cập nhật {n} thư mục.'
        if loi:
            msg += f'\n\n{len(loi)} lỗi:\n' + '\n'.join(loi[:5])
        messagebox.showinfo('Ảnh', msg)

    def _mo_anh_ho(self):
        """Màn gán ảnh dùng chung theo họ; không gọi AI/WordPress."""
        CuaSoAnhHo(self)

    def _dang(self):
        if not self.chon:
            messagebox.showwarning('Ảnh', 'Chưa chọn bài.')
            return
        b = self.chon
        goc = self.v_goc.get().strip()
        tm_ho = WS.tim_workspace_ho(goc, b['sheet'], b['row']) if goc else None
        if not b.get('thu_muc') and not tm_ho:
            messagebox.showwarning('Ảnh', 'Bài này chưa có ảnh riêng và họ cũng chưa có ảnh.')
            return
        try:
            import xu_ly_anh as X
            import autopost as A
            import cauhinh as C
        except Exception as e:
            messagebox.showerror('Ảnh', f'Thiếu module:\n{e}')
            return

        resolved = self._resolve_wp_id_theo_sku(b)
        if not resolved.get('ok'):
            messagebox.showerror('Ảnh', resolved.get('loi', 'Không tra được WP ID.'))
            return

        def upload(duong_dan, ten, mime):
            return A._url_anh_tren_wp(C.MA_SITE_VER3, duong_dan, tra_media_id=True)

        meta = WS.doc_meta(b['thu_muc']) or {} if b.get('thu_muc') else {}
        kq = X.dang_anh_hieu_luc(goc, b['sheet'], b.get('thu_muc'), b['row'], C.MA_SITE_VER3,
                                 tieu_de=b['ten'], slug=meta.get('slug', ''),
                                 upload=upload,
                                 ghi_log=(self.giac.log if self.giac else (lambda *_: None)))
        # BUG-E: không dùng ``loi`` upload làm công tắc chặn attach. Nếu còn
        # ít nhất một ảnh hợp lệ, gắn phần tốt vào body/gallery ngay.
        gan = (self._gan_anh_vao_bai_ngay(b, kq)
               if kq.get('anh') else {'ok': False, 'loi': 'Không có ảnh hợp lệ để gắn.'})
        self._lam_moi_bai()
        msg = (f"Xử lý {kq['da_xu_ly']} ảnh, bỏ qua {kq['bo_qua']} ảnh đã có trên Media.")
        if gan.get('ok') and gan.get('gan_bai'):
            if kq.get('loi') or gan.get('partial'):
                msg += (f"\n\nĐã gắn {gan.get('so_anh', len(kq.get('anh', [])))} ảnh hợp lệ vào bài "
                        '(gallery + body). Các slot lỗi/stale giữ nguyên để retry.')
                if gan.get('stale_media_ids'):
                    msg += ('\nMedia ID stale đã được xoá state/cache: ' +
                            ', '.join(map(str, gan.get('stale_media_ids'))))
                    msg += '\nBấm Cập nhật ảnh lên WordPress lần nữa để upload lại đúng slot stale.'
            else:
                msg += '\n\nĐã gắn ảnh vào bài WordPress thật (gallery + vị trí body).'
        elif gan.get('body_ok') and not gan.get('gallery_ok'):
            msg += '\n\nCẢNH BÁO: body đã cập nhật nhưng gallery lỗi; có thể bấm lại để retry gallery.'
        else:
            msg += '\n\nLỗi gắn ảnh vào bài: ' + gan.get('loi', 'không rõ')
        # Ver 4.4.1.6 (UX) — trước bản này chỗ này đổ nguyên trang HTML chặn
        # vào hộp thoại: '<!DOCTYPE html><head><meta viewport…'. Người đọc
        # không rút ra được gì, mà thông tin thật thì bị cắt mất. Giờ gom
        # theo LOẠI lỗi, nói rõ làm gì tiếp; chi tiết kỹ thuật xuống Nhật ký.
        if kq.get('loi'):
            msg += '\n\n' + _gom_loi_anh(kq['loi'])
            ghi = self.giac.log if self.giac else None
            if ghi:
                ghi('--- [Ảnh] chi tiết lỗi upload ---')
                for d in kq['loi']:
                    ghi('   ' + str(d).replace('\n', '\n   '))
        if kq.get('canh_bao'):
            msg += '\n\nCảnh báo:\n' + '\n'.join(
                '  • ' + str(c).split('\n')[0][:160] for c in kq['canh_bao'][:5])
        messagebox.showinfo('Ảnh', msg)



class CuaSoAnhHo:
    """Cửa sổ gán 5 ô ảnh dùng chung cho từng họ máy biến áp."""
    def __init__(self, tab):
        self.tab = tab
        self.top = tk.Toplevel(tab.f)
        self.top.title('Gán ảnh cho họ sản phẩm')
        self.top.geometry('980x720')
        self.top.minsize(820, 600)
        self.thumb = {}
        self.chon = None
        self.ho = self._gom_ho()
        self._dung()
        self._nap_bang()

    def _gom_ho(self):
        gom = {}
        for b in self.tab.bai:
            ho = WS.ho_san_pham(b.get('row') or {})
            if not ho:
                continue
            k = ho['key']
            if k not in gom:
                gom[k] = {'ho': ho, 'bai': b, 'so_sku': 0}
            gom[k]['so_sku'] += 1
        return list(gom.values())

    def _dung(self):
        f = ttk.Frame(self.top, padding=10)
        f.pack(fill='both', expand=True)
        ttk.Label(f, text='Ảnh họ dùng làm mặc định; ảnh riêng của SKU luôn thắng ở cùng ô.',
                  foreground='#5f6368').pack(anchor='w', pady=(0, 8))
        than = ttk.Frame(f)
        than.pack(fill='both', expand=True)

        trai = ttk.Frame(than, width=330)
        trai.pack(side='left', fill='y')
        trai.pack_propagate(False)
        self.bang = ttk.Treeview(trai, columns=('ho', 'sku'), show='headings', height=22)
        self.bang.heading('ho', text='Họ sản phẩm')
        self.bang.heading('sku', text='SKU')
        self.bang.column('ho', width=255, anchor='w')
        self.bang.column('sku', width=48, anchor='center')
        self.bang.pack(fill='both', expand=True)
        self.bang.bind('<<TreeviewSelect>>', self._bam)

        phai = ttk.Frame(than, padding=(12, 0, 0, 0))
        phai.pack(side='left', fill='both', expand=True)
        self.nhan = ttk.Label(phai, text='Chọn một họ bên trái', font=('Segoe UI', 11, 'bold'), wraplength=570)
        self.nhan.pack(anchor='w', fill='x')
        self.duong_dan = ttk.Label(phai, text='', foreground='#6b7789', wraplength=570)
        self.duong_dan.pack(anchor='w', fill='x', pady=(2, 8))

        khung_cuon = ttk.Frame(phai)
        khung_cuon.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(khung_cuon, highlightthickness=0, borderwidth=0)
        sb = ttk.Scrollbar(khung_cuon, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        self.o = ttk.Frame(self.canvas)
        self.win = self.canvas.create_window((0, 0), window=self.o, anchor='nw')
        self.o.bind('<Configure>', lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(self.win, width=e.width))

        ha = ttk.Frame(phai)
        ha.pack(fill='x', pady=(8, 0))
        ttk.Button(ha, text='Mở thư mục họ', command=self._mo).pack(side='left')

    def _nap_bang(self):
        for x in self.bang.get_children():
            self.bang.delete(x)
        for x in self.ho:
            self.bang.insert('', 'end', values=(x['ho']['nhan'], x['so_sku']))
        if self.ho:
            first = self.bang.get_children()[0]
            self.bang.selection_set(first)
            self.bang.focus(first)
            self._bam()

    def _bam(self, _e=None):
        s = self.bang.selection()
        if not s:
            return
        i = self.bang.index(s[0])
        if i >= len(self.ho):
            return
        self.chon = self.ho[i]
        self._ve()

    def _tm(self, tao=False):
        if not self.chon:
            return None
        b = self.chon['bai']
        goc = self.tab.v_goc.get().strip()
        if not goc:
            return None
        return (WS.tao_workspace_ho(goc, b['sheet'], b['row']) if tao
                else WS.tim_workspace_ho(goc, b['sheet'], b['row']))

    def _ve(self):
        for w in self.o.winfo_children():
            w.destroy()
        self.thumb.clear()
        if not self.chon:
            return
        self.nhan.config(text=self.chon['ho']['nhan'] + f"  ·  {self.chon['so_sku']} SKU")
        tm = self._tm(False)
        self.duong_dan.config(text=str(tm or '(chưa có thư mục họ — chọn ảnh để tạo)'))
        kq = WS.quet(tm) if tm else {'o': {}}
        ds = WS.vai_tro_cua('may_bien_ap_do_luong')
        for hang, (ma, nhan, huong_dan) in enumerate(ds):
            box = ttk.Frame(self.o, relief='solid', borderwidth=1, padding=6)
            box.grid(row=hang, column=0, sticky='ew', pady=3)
            self.o.columnconfigure(0, weight=1)
            a = kq['o'].get(ma)
            lb = tk.Label(box, width=14, height=5, bg='#eef1f5', text='(trống)' if not a else '')
            lb.grid(row=0, column=0, rowspan=2, padx=(0, 8))
            if a:
                img = self.tab._doc_thumb(a['duong_dan'])
                if img:
                    self.thumb[ma] = img
                    lb.config(image=img, text='', width=0, height=0)
            ttk.Label(box, text=f'{hang + 1}. {nhan}', font=('Segoe UI', 9, 'bold')).grid(row=0, column=1, sticky='w')
            phu = (a.get('ten_tren_dia', '') + '  ·  ' + a.get('trang_thai', '')) if a else huong_dan
            ttk.Label(box, text=phu, foreground='#6b7789', wraplength=350).grid(row=1, column=1, sticky='w')
            nut = ttk.Frame(box)
            nut.grid(row=0, column=2, rowspan=2, sticky='e')
            ttk.Button(nut, text='Chọn ảnh…', width=11,
                       command=lambda m=ma: self._chon_anh(m)).pack()
            if a:
                ttk.Button(nut, text='Gỡ', width=11,
                           command=lambda m=ma: self._go(m)).pack(pady=(3, 0))
            box.columnconfigure(1, weight=1)

    def _chon_anh(self, vai_tro):
        tm = self._tm(True)
        if not tm:
            messagebox.showwarning('Ảnh họ', 'Chưa chọn thư mục ảnh gốc hoặc họ sản phẩm.')
            return
        ds = filedialog.askopenfilenames(
            title='Chọn ảnh cho họ sản phẩm', initialdir=self.tab._downloads(),
            filetypes=self.tab._filetypes_anh())
        if not ds:
            return
        roles = [v for v, _, _ in WS.vai_tro_cua('may_bien_ap_do_luong')]
        start = roles.index(vai_tro) if vai_tro in roles else 0
        for k, file in enumerate(ds):
            if start + k >= len(roles):
                break
            WS.gan_anh(tm, file, roles[start + k])
        self._ve()
        self.tab.nap()

    def _go(self, vai_tro):
        tm = self._tm(False)
        if tm:
            WS.bo_anh(tm, vai_tro)
            self._ve()
            self.tab.nap()

    def _mo(self):
        tm = self._tm(True)
        if not tm:
            return
        try:
            if sys.platform.startswith('win'):
                os.startfile(str(tm))
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', str(tm)])
            else:
                subprocess.Popen(['xdg-open', str(tm)])
        except Exception as e:
            messagebox.showerror('Ảnh họ', f'Không mở được thư mục:\n{e}')

def gan_vao(nb_con, giac=None):
    """Điểm vào chuẩn. giao-dien.py gọi 1 dòng với một GiacCam."""
    t = TabAnh(nb_con, giac)
    nb_con.add(t.f, text='  Ảnh bài viết (4.0)  ')
    return t
