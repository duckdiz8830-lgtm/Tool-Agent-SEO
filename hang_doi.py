# -*- coding: utf-8 -*-
"""TAB HÀNG ĐỢI — Ver 3.5.

VÌ SAO CÓ FILE NÀY
------------------
10 tab cũ tổ chức theo TÍNH NĂNG: muốn làm gì phải nhớ tính năng đó nằm ở
tab số mấy. Nhưng 90% thời gian câu hỏi không phải "nút render ở đâu" mà là
"lô 245 SKU đang ở đâu, còn bao nhiêu chưa làm, cái nào không nên làm".
Không tab nào trả lời được câu đó trong một cái nhìn.

Tab này đảo lại: DANH SÁCH SKU là trung tâm, lọc được, chọn hàng loạt.
Hạng nguyên liệu (bep_truong) và cảnh báo dữ liệu (MASTER Ver5) là cột
hạng nhất, không giấu trong tab phụ hay trong nhật ký.

RANH GIỚI — QUAN TRỌNG
----------------------
Tab này KHÔNG render, KHÔNG đăng, KHÔNG gọi AI. Nó chỉ đọc DB và ghi đúng
một thứ: cờ `selected` của san_pham_phase2. Tab '4. Sinh & Đăng' đã đọc cờ
đó sẵn (liet_ke_san_pham(chi_da_chon=True)) nên không cần đụng vào luồng
render. Một nguồn sự thật cho "sắp làm cái nào", không nhân đôi pipeline.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import bep_truong as BT
import db_phase2 as DB

NHAN_TRANG_THAI = {
    '': 'Chưa render', 'chua_sinh': 'Chưa render', 'dang_sinh': 'Đang chạy',
    'da_sinh': 'Chờ duyệt', 'da_dang': 'Đã đăng', 'loi': 'Lỗi',
}

# Màu nền theo hạng — chỉ 3 mức, đủ để liếc mắt phân biệt, không thành cầu vồng
MAU_HANG = {BT.DU: '#E1F5EE', BT.VUA: '#FAEEDA', BT.DOI: '#F1EFE8'}
MAU_CANH_BAO = '#FAEEDA'

BO_LOC = [('tat_ca', 'Tất cả'), (BT.DU, 'Đủ'), (BT.VUA, 'Vừa'),
          (BT.DOI, 'Đói'), ('canh_bao', 'Có cảnh báo')]

# Ver 4.5.2 — LỌC THEO TRẠNG THÁI, trục thứ hai độc lập với hạng nguyên liệu.
# Trước 4.5.2 chỉ có trục hạng, nên KHÔNG cô lập được nhóm "chưa render":
# đo thật trên 581 dòng (245 đã đăng) — mọi bộ lọc đều lẫn bài đã đăng, và
# "Chọn hết" ôm luôn 245 bài đã đăng -> render lại, đốt quota, ghi đè bài live.
BO_LOC_TT = [('tt_tat_ca', 'Mọi trạng thái'), ('chua', 'Chưa render'),
             ('duyet', 'Chờ duyệt'), ('dang', 'Đã đăng'), ('loi', 'Lỗi')]


def _nhom_trang_thai(t):
    if t == 'da_dang':
        return 'dang'
    if t == 'da_sinh':
        return 'duyet'
    if t == 'loi':
        return 'loi'
    return 'chua'


class TabHangDoi:
    def __init__(self, nb, app=None):
        self.app = app
        self.f = ttk.Frame(nb, padding=12)
        self.dong = []          # [dict] toàn bộ SKU của profile đang xem
        self.dang_hien = []     # [dict] sau khi lọc
        self.loc = 'tat_ca'
        self.bang = None
        self._dung_giao_dien()
        self.nap()

    # -------------------------------------------------- dựng giao diện
    def _dung_giao_dien(self):
        f = self.f

        thanh = ttk.Frame(f)
        thanh.pack(fill='x', pady=(0, 8))
        ttk.Label(thanh, text='Nhóm sản phẩm:').pack(side='left')
        self.v_profile = tk.StringVar(value='may_bien_ap_do_luong')
        self.cb_profile = ttk.Combobox(thanh, textvariable=self.v_profile, width=26,
                                       state='readonly')
        self.cb_profile.pack(side='left', padx=(6, 12))
        self.cb_profile.bind('<<ComboboxSelected>>', lambda _e: self.nap())
        ttk.Button(thanh, text='Nạp lại', command=self.nap).pack(side='left')
        self.nhan_dataset = ttk.Label(thanh, text='', foreground='#6b7789')
        self.nhan_dataset.pack(side='right')

        # --- 4 ô đếm trạng thái
        o = ttk.Frame(f)
        o.pack(fill='x', pady=(0, 8))
        self.dem_nhan = {}
        for khoa, ten in [('chua', 'Chưa render'), ('duyet', 'Chờ duyệt'),
                          ('dang', 'Đã đăng'), ('kiem', 'Cần kiểm')]:
            khung = ttk.Frame(o, relief='solid', borderwidth=1, padding=8)
            khung.pack(side='left', fill='x', expand=True, padx=(0, 6))
            ttk.Label(khung, text=ten, foreground='#6b7789').pack(anchor='w')
            lb = ttk.Label(khung, text='0', font=('Segoe UI', 16))
            lb.pack(anchor='w')
            self.dem_nhan[khoa] = lb
            # Ver 4.5.2 — 4 ô này TRÔNG như nút lọc nhưng trước đây là nhãn
            # chết. Bấm vào không có gì xảy ra -> người dùng tưởng tool hỏng.
            # Nay bấm = lọc đúng nhóm đó.
            for w in (khung, *khung.winfo_children()):
                w.bind('<Button-1>', lambda _e, k=khoa: self._loc_tu_o_dem(k))
                try:
                    w.configure(cursor='hand2')
                except tk.TclError:
                    pass

        # --- bộ lọc theo hạng
        loc = ttk.Frame(f)
        loc.pack(fill='x', pady=(0, 6))
        self.v_loc = tk.StringVar(value='tat_ca')
        self.nut_loc = {}
        for khoa, ten in BO_LOC:
            r = ttk.Radiobutton(loc, text=ten, value=khoa, variable=self.v_loc,
                                command=self._ap_loc)
            r.pack(side='left', padx=(0, 10))
            self.nut_loc[khoa] = r
        self.nhan_chon = ttk.Label(loc, text='')
        self.nhan_chon.pack(side='right')

        # --- Ver 4.5.2: bộ lọc TRẠNG THÁI (trục 2)
        loc2 = ttk.Frame(f)
        loc2.pack(fill='x', pady=(0, 6))
        ttk.Label(loc2, text='Trạng thái:', foreground='#6b7789').pack(
            side='left', padx=(0, 8))
        self.v_loc_tt = tk.StringVar(value='tt_tat_ca')
        for khoa, ten in BO_LOC_TT:
            ttk.Radiobutton(loc2, text=ten, value=khoa, variable=self.v_loc_tt,
                            command=self._ap_loc).pack(side='left', padx=(0, 10))

        # --- bảng
        khung_bang = ttk.Frame(f)
        khung_bang.pack(fill='both', expand=True)
        try:
            from tksheet import Sheet
        except ImportError as e:
            # KHÔNG nuốt lỗi im lặng. Bản 3.4 bọc try/except rồi chỉ print ra
            # console -> máy thiếu thư viện thì tab biến mất, người dùng tưởng
            # chưa ai làm. Ở đây báo thẳng lên giao diện.
            ttk.Label(khung_bang, foreground='#A32D2D', justify='left',
                      text=('Thiếu thư viện tksheet nên không dựng được bảng.\n'
                            f'Chi tiết: {e}\n\n'
                            'Mở Command Prompt và chạy:  pip install tksheet\n'
                            'Rồi khởi động lại tool.')).pack(anchor='w', pady=20)
            return
        self.bang = Sheet(khung_bang, headers=['', 'Mã hàng', 'Tên hàng', 'Hạng',
                                               'Trạng thái', 'Cần kiểm'],
                          show_row_index=False, header_height=26)
        self.bang.enable_bindings(('single_select', 'row_select', 'drag_select',
                                   'column_width_resize', 'copy', 'arrowkeys'))
        self.bang.pack(fill='both', expand=True)
        self.bang.extra_bindings('cell_select', self._bam_o)
        self.bang.column_width(0, 34)
        self.bang.column_width(1, 130)
        self.bang.column_width(2, 380)
        self.bang.column_width(3, 60)
        self.bang.column_width(4, 100)

        # --- hành động
        ha = ttk.Frame(f)
        ha.pack(fill='x', pady=(8, 0))
        # Ver 4.5.2 — nút AN TOÀN đặt trước, đúng việc hay làm nhất: chọn
        # những SKU chưa từng render. Không bao giờ chạm bài đã đăng.
        ttk.Button(ha, text='Chọn các SKU CHƯA render',
                   command=self._chon_chua_render).pack(side='left')
        # Ver 4.6.2 — cổng chất lượng viết ở 4.6 nhưng chưa có đường bấm.
        # Đo TRƯỚC khi sinh, tốn 0 token AI.
        ttk.Button(ha, text='Soát mỏng/trùng…',
                   command=self._soat_chat_luong).pack(side='left', padx=6)
        ttk.Button(ha, text='Chọn hết (theo bộ lọc)',
                   command=lambda: self._chon_hang_loat(True)).pack(side='left', padx=6)
        ttk.Button(ha, text='Bỏ chọn hết',
                   command=lambda: self._chon_hang_loat(False)).pack(side='left', padx=6)
        ttk.Button(ha, text='Lưu lựa chọn vào hàng đợi',
                   command=self._luu).pack(side='left', padx=(18, 0))
        ttk.Label(ha, foreground='#6b7789',
                  text='  Lưu xong sang tab "Sinh & Đăng" để chạy.').pack(side='left')

    # -------------------------------------------------- nạp dữ liệu
    def nap(self):
        try:
            con = DB.ket_noi()
        except Exception as e:
            messagebox.showerror('Hàng đợi', f'Không mở được cơ sở dữ liệu:\n{e}')
            return
        try:
            ds = [d['profile_id'] for d in DB.liet_ke_dataset(con)]
            if ds:
                self.cb_profile['values'] = sorted(set(ds))
            profile = self.v_profile.get()
            dset = DB.dataset_gan_nhat(con, profile)
            if not dset:
                self.dong = []
                self.nhan_dataset.config(text=f'Chưa có dữ liệu nhập cho "{profile}"')
                self._ap_loc()
                return
            dsid = dset['dataset_id']
            self.nhan_dataset.config(
                text=f'{dset.get("source_file") or "?"} · {dset.get("row_count") or 0} dòng')

            sp = DB.liet_ke_san_pham(con, dataset_id=dsid, profile_id=profile)
            tt = {d['record_id']: d['trang_thai']
                  for d in DB.dashboard(con, dataset_id=dsid, profile_id=profile)}
        finally:
            con.close()

        self.dong = []
        for r in sp:
            k = BT.phan_hang(r)
            self.dong.append({
                'record_id': r.get('record_id', ''),
                'ma': r.get('ma_goc') or r.get('publish_sku') or '',
                'ten': (r.get('ten_goc') or '').replace('\n', ' ').strip(),
                'hang': k['hang'], 'nhan_hang': k['nhan'], 'ly_do': k['ly_do'],
                'trang_thai': tt.get(r.get('record_id'), ''),
                'canh_bao': BT.canh_bao(r),
                'chon': bool(r.get('selected')),
            })
        self._ap_loc()

    # -------------------------------------------------- lọc + vẽ
    def _loc_tu_o_dem(self, khoa):
        """Ver 4.5.2 — bấm ô đếm = lọc nhóm đó."""
        if khoa == 'kiem':
            self.v_loc.set('canh_bao')
            self.v_loc_tt.set('tt_tat_ca')
        else:
            self.v_loc.set('tat_ca')
            self.v_loc_tt.set(khoa)
        self._ap_loc()

    def _ap_loc(self):
        self.loc = self.v_loc.get()
        if self.loc == 'tat_ca':
            ds = list(self.dong)
        elif self.loc == 'canh_bao':
            ds = [d for d in self.dong if d['canh_bao']]
        else:
            ds = [d for d in self.dong if d['hang'] == self.loc]
        # Ver 4.5.2 — trục 2: trạng thái. Hai trục giao nhau (AND).
        tt = self.v_loc_tt.get() if hasattr(self, 'v_loc_tt') else 'tt_tat_ca'
        if tt != 'tt_tat_ca':
            ds = [d for d in ds if _nhom_trang_thai(d['trang_thai']) == tt]
        self.dang_hien = ds
        self._ve()
        self._dem()

    def _ve(self):
        if not self.bang:
            return
        data = [['✔' if d['chon'] else '', d['ma'], d['ten'], d['nhan_hang'],
                 NHAN_TRANG_THAI.get(d['trang_thai'], d['trang_thai']),
                 d['canh_bao'][:90]] for d in self.dang_hien]
        self.bang.set_sheet_data(data, reset_col_positions=False,
                                 reset_row_positions=True)
        for i, d in enumerate(self.dang_hien):
            self.bang.highlight_cells(row=i, column=3, bg=MAU_HANG.get(d['hang']),
                                      fg='#2C2C2A')
            if d['canh_bao']:
                self.bang.highlight_cells(row=i, column=5, bg=MAU_CANH_BAO,
                                          fg='#854F0B')

    def _dem(self):
        c = {'chua': 0, 'duyet': 0, 'dang': 0, 'kiem': 0}
        for d in self.dong:
            t = d['trang_thai']
            if t == 'da_dang':
                c['dang'] += 1
            elif t == 'da_sinh':
                c['duyet'] += 1
            else:
                c['chua'] += 1
            if d['canh_bao']:
                c['kiem'] += 1
        for k, lb in self.dem_nhan.items():
            lb.config(text=str(c[k]))
        n = sum(1 for d in self.dong if d['chon'])
        # Ver 4.5.2 — nói rõ trong lựa chọn có bao nhiêu bài ĐÃ ĐĂNG, để
        # không bấm Lưu rồi mới biết mình vừa xếp lịch render lại bài live.
        n_dang = sum(1 for d in self.dong
                     if d['chon'] and _nhom_trang_thai(d['trang_thai']) == 'dang')
        canh = f' (trong đó {n_dang} ĐÃ ĐĂNG)' if n_dang else ''
        self.nhan_chon.config(
            text=f'{len(self.dang_hien)} dòng đang hiện · {n} đã chọn{canh}')

    # -------------------------------------------------- tương tác
    def _bam_o(self, su_kien=None):
        """Bấm vào cột đầu = bật/tắt chọn dòng đó."""
        try:
            r, c = self.bang.get_currently_selected()[:2]
        except Exception:
            return
        if c != 0 or r is None or r >= len(self.dang_hien):
            return
        d = self.dang_hien[r]
        d['chon'] = not d['chon']
        self.bang.set_cell_data(r, 0, '✔' if d['chon'] else '')
        self._dem()

    def _soat_chat_luong(self):
        """Ver 4.6.2 — dựng thử bài của các SKU đang chọn rồi đo MỎNG/TRÙNG.

        Không gọi AI, không ghi gì. Chỉ dựng phần code sinh (bảng thông số +
        khối chịu tải) để biết TRƯỚC khi tốn quota là bài sẽ mỏng hay trùng.
        """
        import html as _html
        import cong_chat_luong as CG
        import render_phase2 as R
        try:
            import khoi_chiu_tai as KCT
        except ImportError:
            KCT = None

        chon = [d for d in self.dang_hien if d['chon']] or list(self.dang_hien)
        if not chon:
            messagebox.showinfo('Soát chất lượng', 'Không có dòng nào để soát.')
            return
        if len(chon) > 400:
            chon = chon[:400]

        with DB.ket_noi() as con:
            dsid = DB.dataset_gan_nhat(con, self.v_profile.get())["dataset_id"]
            sp = {r['record_id']: r for r in DB.liet_ke_san_pham(con, dataset_id=dsid)}

        _st = getattr(R, '_st', lambda k: '')
        _esc = lambda v: _html.escape(str(v))
        bo = []
        for d in chon:
            r = sp.get(d['record_id'])
            if not r:
                continue
            try:
                h = R.bang_thong_so(r)
                if KCT:
                    h += KCT.khoi_chiu_tai(r, _st, _esc)
            except Exception:
                continue
            bo.append({'record_id': d['record_id'], 'ten_goc': d.get('ten', ''),
                       'html': h, 'row': r})
        if not bo:
            messagebox.showinfo('Soát chất lượng', 'Không dựng được bài nào để đo.')
            return

        bc, cb = CG.soat(bo)
        print(f'--- Soát chất lượng {bc["tong_bai"]} SKU ---')
        CG.in_bao_cao(bc, cb, gioi_han=40)
        messagebox.showinfo(
            'Soát chất lượng',
            f'Đã soát {bc["tong_bai"]} SKU · dài trung bình {bc["do_dai_tb"]} ký tự\n\n'
            f'MỎNG : {bc["so_mong"]}\n'
            f'TRÙNG: {bc["so_trung"]}\n\n'
            f'Chi tiết từng dòng xem ở khung Nhật ký bên phải.\n'
            f'Bài mỏng/trùng vẫn sinh được — đây là cảnh báo, không phải chặn.')

    def _chon_chua_render(self):
        """Ver 4.5.2 — chọn mọi SKU chưa render TRONG bộ lọc đang xem.

        Đây là thao tác hay dùng nhất mà trước 4.5.2 không làm được: không có
        bộ lọc trạng thái nên muốn bỏ qua bài đã đăng phải tick tay từng dòng
        trên 581 dòng.
        """
        n = 0
        for d in self.dang_hien:
            if _nhom_trang_thai(d['trang_thai']) == 'chua':
                d['chon'] = True
                n += 1
        self._ve()
        self._dem()
        if n == 0:
            messagebox.showinfo(
                'Hàng đợi', 'Không có SKU nào ở trạng thái "Chưa render" '
                            'trong bộ lọc đang xem.')

    def _chon_hang_loat(self, bat):
        if bat:
            da_dang = [d for d in self.dang_hien
                       if _nhom_trang_thai(d['trang_thai']) == 'dang']
            if da_dang:
                # Ver 4.5.2 — chặn tai nạn: chọn hết ở "Tất cả" sẽ ôm cả bài
                # ĐÃ ĐĂNG -> render lại, đốt quota Gemini và ghi đè bài đang
                # có thứ hạng. Phải hỏi, và mặc định là KHÔNG.
                ok = messagebox.askyesno(
                    'Có bài ĐÃ ĐĂNG trong lựa chọn',
                    f'{len(da_dang)} SKU trong bộ lọc đang xem ĐÃ ĐĂNG lên site.\n\n'
                    f'Chọn hết sẽ render lại các bài này: tốn quota AI, và nội '
                    f'dung mới ghi đè bài đang có thứ hạng.\n\n'
                    f'Muốn bỏ qua chúng thì bấm No rồi dùng nút '
                    f'"Chọn các SKU CHƯA render".\n\nVẫn chọn cả bài đã đăng?',
                    default='no')
                if not ok:
                    return
        for d in self.dang_hien:
            d['chon'] = bat
        self._ve()
        self._dem()

    def _luu(self):
        chon = [d for d in self.dong if d['chon']]
        doi = [d for d in chon if d['hang'] == BT.DOI]
        if doi:
            # Hạng ĐÓI vẫn cho render (quyết định của Thịnh), nhưng phải hỏi
            # một lần — bài viết cho SKU chỉ có tên sẽ mỏng và nói vòng vo.
            ok = messagebox.askyesno(
                'Có SKU hạng Đói',
                f'{len(doi)} SKU trong lựa chọn thuộc hạng ĐÓI — gần như chỉ có '
                f'tên hàng, không có công suất/cấp điện áp.\n\n'
                f'Bài viết cho nhóm này sẽ mỏng và ít giá trị. Vẫn đưa vào hàng đợi?')
            if not ok:
                return
        try:
            con = DB.ket_noi()
            try:
                dset = DB.dataset_gan_nhat(con, self.v_profile.get())
                if not dset:
                    return
                dsid = dset['dataset_id']
                DB.dat_chon(con, dsid, [d['record_id'] for d in self.dong], chon=False)
                if chon:
                    DB.dat_chon(con, dsid, [d['record_id'] for d in chon], chon=True)
                con.commit()
            finally:
                con.close()
        except Exception as e:
            messagebox.showerror('Hàng đợi', f'Không lưu được lựa chọn:\n{e}')
            return
        messagebox.showinfo(
            'Hàng đợi',
            f'Đã đưa {len(chon)} SKU vào hàng đợi.\n\n'
            f'Sang tab "Sinh & Đăng" và bật "chỉ chạy mục đã chọn" để render.')


def gan_vao(nb_con, app=None):
    """giao-dien.py gọi đúng 1 dòng: hang_doi.gan_vao(nb, self)."""
    t = TabHangDoi(nb_con, app)
    nb_con.add(t.f, text='  Hàng đợi (3.5)  ')
    return t
