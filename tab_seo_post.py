# -*- coding: utf-8 -*-
"""Ver 5.8 — Tab "SEO Post" (Tab 11). Bài chủ đề, không neo SKU.

Cắm vào giao-dien.py bằng 1 dòng:
    import tab_seo_post; tab_seo_post.gan_vao(nb, giac)

Luồng trên màn hình, trái sang phải, đúng thứ tự người dùng làm:
    [1] Nạp từ khoá -> [2] Duyệt đề xuất -> [3] Gắn SKU -> [4] Sinh -> [5] Đăng

Tab này CHỈ dựng giao diện và gọi seo_post_core. Không chứa logic nghiệp vụ.

---------------------------------------------------------------------------
Ver 5.8 — VIẾT LẠI THEO HỢP ĐỒNG giac_cam.py

VÌ SAO
    Đo ngày 22/08/2026, file này là module bẩn nhất hệ:
        57 lượt với vào app  (trên 14 tên khác nhau)
        15 thuộc tính NHÉT vào app  (app._sp_kw1, app._sp_bang, ...)
    Ba module tính năng còn lại: tab_anh 2 lượt, hang_doi 0, man_hinh_du_lieu 0.

    Đây chính là cách God Class được nuôi lớn: mỗi tab mới nhét thêm chục
    thuộc tính vào vỏ ứng dụng, ai đọc `app.` cũng không biết cái nào của ai.
    Gỡ tab này ra trước đây là phải đi tìm 15 thuộc tính rải rác.

CÁCH SỬA
    Gói toàn bộ state vào class TabSeoPost — y hệt TabHangDoi (hang_doi.py)
    và TabAnh (tab_anh.py) vốn đã sạch từ đầu. Widget thành self.*, không
    còn app.* nào. Vỏ ứng dụng không biết tab này có bao nhiêu widget.

    Mọi thứ cần từ vỏ đi qua đúng 5 chân của giac_cam.py:
        giac.db()          thay _con(app) — vẫn threading.local, nay dùng chung
        giac.log(msg)      thay print() rải rác
        giac.chay_nen(fn)  thay threading.Thread(...) tự dựng
        giac.ui(fn)        khi cần đụng widget từ luồng nền
        giac.cau_hinh(t)   thay hằng số cắm cứng

    Giữ nguyên 100% hành vi người dùng thấy: cùng bố cục, cùng nút, cùng
    thông báo. Đây là đổi CHỖ ĐỂ ĐỒ, không đổi tính năng.

BẪY GIỮ NGUYÊN TỪ Ver 5.7 — đừng làm lại
    1. sqlite3 check_same_thread=True: một Connection chỉ dùng được ở luồng
       tạo ra nó. Dùng chung 1 kết nối giữa luồng UI và luồng nền -> mọi
       bài ném ProgrammingError, except nuốt mất, hiện ra "0 thành công,
       N lỗi". giac.db() trả kết nối theo từng luồng nên hết bệnh.
    2. Luồng nền TUYỆT ĐỐI không đụng tkinter. Cập nhật tiến độ phải đi qua
       giac.ui(). Tkinter không thread-safe: treo/crash ngẫu nhiên, không
       tái hiện theo ý muốn được.
    3. Callback chạy TRỄ không được bắt biến của `except ... as e` — Python
       xoá tên đó khi thoát khối except. Hoá thành chuỗi trước, truyền bằng
       default-arg.
"""
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import prompts_seo_post as P
import db_seo_post as DB
import seo_post_core as C
import ui_tien_ich as UI

TEN_TAB = '11. SEO Post'
SITE_MAC_DINH = 'maybienapvn.vn'


class TabSeoPost:
    """Toàn bộ state của tab nằm trong đây, không nhét gì vào vỏ ứng dụng."""

    def __init__(self, cha, giac):
        self.giac = giac
        self.de_xuat = []
        # Ver 5.8 — PHẢI là khung CUỘN. Bản viết lại đầu tiên dùng ttk.Frame
        # trần và mất tính năng cuộn của app._v3_tab_cuon() cũ: tab này có 4
        # khối, không cuộn thì tràn khỏi cửa sổ và mất luôn hàng nút cuối.
        # Bắt được nhờ dựng UI thật dưới Xvfb, không phải nhờ đọc code.
        self.ngoai, self.f = UI.khung_cuon(cha, padding=16)
        # Ver 5.8 — giac.db() chỉ trả KẾT NỐI, không tạo bảng riêng của
        # module. Trước đây db_seo_post.ket_noi() làm luôn cả hai. Không
        # gọi tao_schema ở đây thì với DB mới toanh, bảng bai_seo chưa tồn
        # tại -> liet_ke() ném lỗi -> cả tab không dựng được.
        DB.tao_schema(self.giac.db())
        self._dung_giao_dien()
        self.nap_bai()

    # ------------------------------------------------------------ giao diện
    def _dung_giao_dien(self):
        f = self.f
        ttk.Label(f, text='SEO Post — bài chủ đề, không neo SKU',
                  style='Dam.TLabel').pack(anchor='w')
        ttk.Label(f, text='Nhập từ khoá → tool đề xuất dạng bài + tiêu đề → gắn SKU nếu cần → '
                          'sinh → đăng. Đăng dạng post (mặc định) hoặc product, chọn từng bài.',
                  style='V3Mo.TLabel', wraplength=820,
                  justify='left').pack(anchor='w', pady=(2, 12))

        # ------------------------------------------------ [1] nạp từ khoá
        k1 = ttk.LabelFrame(f, text=' 1. Nạp từ khoá ', padding=10)
        k1.pack(fill='x', pady=(0, 10))

        h = ttk.Frame(k1)
        h.pack(fill='x')
        ttk.Label(h, text='Gõ 1 cụm:').pack(side='left')
        self.o_kw1 = ttk.Entry(h, width=42)
        self.o_kw1.pack(side='left', padx=6)
        ttk.Button(h, text='Thêm', command=self._them_go_tay).pack(side='left')
        ttk.Button(h, text='Import file GSC (.xlsx)...',
                   command=self._import_gsc).pack(side='left', padx=(18, 0))

        ttk.Label(k1, text='Hoặc dán nhiều dòng (mỗi dòng 1 từ khoá):',
                  style='V3Mo.TLabel').pack(anchor='w', pady=(8, 2))
        self.o_dan = tk.Text(k1, height=4, wrap='word')
        self.o_dan.pack(fill='x')
        ttk.Button(k1, text='Nạp danh sách đã dán',
                   command=self._them_dan_list).pack(anchor='w', pady=(6, 0))

        # ------------------------------------------------ [2] đề xuất
        k2 = ttk.LabelFrame(f, text=' 2. Đề xuất — sửa lại được, đây chỉ là gợi ý ',
                            padding=10)
        k2.pack(fill='both', expand=True, pady=(0, 10))

        cot = ('tu_khoa', 'nhan_type', 'can_sku', 'tin_cay', 'impr', 'tieu_de')
        self.bang = ttk.Treeview(k2, columns=cot, show='headings', height=9)
        for c, n, w in [('tu_khoa', 'Từ khoá', 230), ('nhan_type', 'Dạng bài', 175),
                        ('can_sku', 'Cần SKU', 80), ('tin_cay', 'Tin cậy', 65),
                        ('impr', 'Impr', 65), ('tieu_de', 'Tiêu đề gợi ý', 300)]:
            self.bang.heading(c, text=n)
            self.bang.column(c, width=w, anchor='w')
        self.bang.pack(fill='both', expand=True)
        self.bang.tag_configure('thap', foreground='#B00020')

        h2 = ttk.Frame(k2)
        h2.pack(fill='x', pady=(8, 0))
        ttk.Label(h2, text='Đổi dạng bài cho dòng đang chọn:').pack(side='left')
        self.o_doi_type = ttk.Combobox(h2, width=32, state='readonly',
                                       values=[n for _, n, _ in P.danh_sach_type()])
        self.o_doi_type.pack(side='left', padx=6)
        ttk.Button(h2, text='Áp dụng', command=self._doi_type).pack(side='left')
        ttk.Button(h2, text='Bỏ dòng', command=self._bo_dong).pack(side='left', padx=6)
        self.lb_dem = ttk.Label(h2, text='0 từ khoá', style='V3Mo.TLabel')
        self.lb_dem.pack(side='right')

        # ------------------------------------------------ [3] tuỳ chọn đăng
        k3 = ttk.LabelFrame(f, text=' 3. Tuỳ chọn đăng ', padding=10)
        k3.pack(fill='x', pady=(0, 10))

        h3 = ttk.Frame(k3)
        h3.pack(fill='x')
        ttk.Label(h3, text='Site:').pack(side='left')
        self.o_site = ttk.Entry(h3, width=22)
        # Ver 5.8 — site mặc định đi qua cấu hình thay vì cắm cứng trong code.
        self.o_site.insert(0, self.giac.cau_hinh('SEO_POST_SITE', SITE_MAC_DINH))
        self.o_site.pack(side='left', padx=(4, 16))

        ttk.Label(h3, text='Đăng dạng:').pack(side='left')
        self.v_che_do = tk.StringVar(value=P.DANG_POST)
        ttk.Radiobutton(h3, text='post (khuyên dùng)', value=P.DANG_POST,
                        variable=self.v_che_do).pack(side='left', padx=4)
        ttk.Radiobutton(h3, text='product (làm dày shop)', value=P.DANG_PRODUCT,
                        variable=self.v_che_do).pack(side='left', padx=4)

        ttk.Label(h3, text='   Giá:').pack(side='left')
        self.v_gia = tk.StringVar(value='AN')
        ttk.Radiobutton(h3, text='ẩn số', value='AN',
                        variable=self.v_gia).pack(side='left', padx=4)
        ttk.Radiobutton(h3, text='công khai', value='CONG_KHAI',
                        variable=self.v_gia).pack(side='left', padx=4)

        ttk.Button(k3, text='>> TẠO BÀI TỪ DANH SÁCH TRÊN', style='V3Chinh.TButton',
                   command=self._tao_bai).pack(anchor='w', pady=(10, 0))

        # ------------------------------------------------ [4] hàng đợi bài
        k4 = ttk.LabelFrame(f, text=' 4. Hàng đợi bài — sinh & đăng ', padding=10)
        k4.pack(fill='both', expand=True)

        cot2 = ('kw', 'type', 'site', 'dang', 'sku', 'tt', 'wp')
        self.bang2 = ttk.Treeview(k4, columns=cot2, show='headings', height=9)
        for c, n, w in [('kw', 'Từ khoá', 220), ('type', 'Dạng bài', 165),
                        ('site', 'Site', 120), ('dang', 'Đăng', 70), ('sku', 'SKU', 45),
                        ('tt', 'Trạng thái', 95), ('wp', 'WP / lỗi', 260)]:
            self.bang2.heading(c, text=n)
            self.bang2.column(c, width=w, anchor='w')
        self.bang2.pack(fill='both', expand=True)
        self.bang2.tag_configure('LOI', foreground='#B00020')
        self.bang2.tag_configure('DA_DANG', foreground='#0B7A28')

        h4 = ttk.Frame(k4)
        h4.pack(fill='x', pady=(8, 0))
        ttk.Button(h4, text='Nạp lại', command=self.nap_bai).pack(side='left')
        ttk.Button(h4, text='Gắn SKU cho bài đang chọn...',
                   command=self._gan_sku).pack(side='left', padx=6)
        ttk.Button(h4, text='Sinh nội dung (bài đang chọn)',
                   command=lambda: self._chay('sinh', False)).pack(side='left', padx=6)
        ttk.Button(h4, text='Đăng Draft (bài đang chọn)',
                   command=lambda: self._chay('dang', False)).pack(side='left', padx=6)
        ttk.Separator(h4, orient='vertical').pack(side='left', fill='y', padx=10)
        ttk.Button(h4, text='SINH HÀNG LOẠT', style='V3Chinh.TButton',
                   command=lambda: self._chay('sinh', True)).pack(side='left')
        ttk.Button(h4, text='ĐĂNG HÀNG LOẠT',
                   command=lambda: self._chay('dang', True)).pack(side='left', padx=6)

        self.lb_tt = ttk.Label(k4, text='', style='V3Mo.TLabel',
                               wraplength=820, justify='left')
        self.lb_tt.pack(anchor='w', pady=(8, 0))

    # ============================================================ [1] nạp
    def _them(self, ds):
        if not ds:
            return
        self.de_xuat.extend(C.de_xuat(ds))
        da, sach = set(), []
        for m in self.de_xuat:           # bỏ trùng theo từ khoá, giữ lần đầu
            k = m['tu_khoa'].lower()
            if k not in da:
                da.add(k)
                sach.append(m)
        self.de_xuat = sach
        self._ve_bang()

    def _them_go_tay(self):
        self._them(C.nap_tu_khoa_go_tay(self.o_kw1.get()))
        self.o_kw1.delete(0, 'end')

    def _them_dan_list(self):
        self._them(C.nap_tu_khoa_dan_list(self.o_dan.get('1.0', 'end')))
        self.o_dan.delete('1.0', 'end')

    def _import_gsc(self):
        duong = filedialog.askopenfilename(
            title='Chọn file GSC export (.xlsx)',
            filetypes=[('Excel', '*.xlsx'), ('Tất cả', '*.*')])
        if not duong:
            return
        try:
            ds, cham_tran = C.nap_tu_khoa_gsc(duong)
        except Exception as e:
            tin_loi = f'{type(e).__name__}: {e}'      # hoá chuỗi NGAY trong except
            messagebox.showerror('Lỗi', f'Không đọc được file:\n{tin_loi}')
            self.giac.log(f'[SEO Post] Import GSC lỗi: {tin_loi}')
            return
        self._them(ds)
        tin = f'Nạp {len(ds)} từ khoá (impression >= 50).'
        if cham_tran:
            tin += ('\n\nFile chạm trần 1.000 dòng — GSC không cho export hơn qua giao diện. '
                    'Muốn đủ thì tách theo trang/thư mục rồi export nhiều lần.')
        messagebox.showinfo('Xong', tin)

    # ============================================================ [2] bảng
    def _ve_bang(self):
        self.bang.delete(*self.bang.get_children())
        for i, m in enumerate(self.de_xuat):
            impr = f'{int(m["impression"]):,}' if m.get('impression') else ''
            self.bang.insert('', 'end', iid=str(i), values=(
                m['tu_khoa'], m['nhan_type'], m['can_sku'], m['do_tin_cay'],
                impr, m['tieu_de_goi_y']),
                tags=('thap',) if m['do_tin_cay'] == 'thap' else ())
        n_thap = sum(1 for m in self.de_xuat if m['do_tin_cay'] == 'thap')
        tin = f'{len(self.de_xuat)} từ khoá'
        if n_thap:
            tin += (f'  ({n_thap} dòng đỏ = tên sản phẩm thuần, nên để luồng SKU lo, '
                    f'sẽ bị bỏ khi tạo bài)')
        self.lb_dem.config(text=tin)

    @staticmethod
    def _dong_dang_chon(bang):
        ch = bang.selection()
        return ch[0] if ch else None

    def _doi_type(self):
        i = self._dong_dang_chon(self.bang)
        nhan = self.o_doi_type.get()
        if i is None or not nhan:
            return
        for tid, n, sku in P.danh_sach_type():
            if n == nhan:
                m = self.de_xuat[int(i)]
                m.update({'content_type': tid, 'nhan_type': n, 'can_sku': sku,
                          'do_tin_cay': 'cao',
                          'tieu_de_goi_y': C.goi_y_tieu_de(tid, m['tu_khoa'])})
                break
        self._ve_bang()

    def _bo_dong(self):
        i = self._dong_dang_chon(self.bang)
        if i is not None:
            self.de_xuat.pop(int(i))
            self._ve_bang()

    # ============================================================ [3] tạo bài
    def _tao_bai(self):
        if not self.de_xuat:
            messagebox.showwarning('Chưa có gì', 'Nạp từ khoá trước.')
            return
        site = self.o_site.get().strip()
        if not site:
            messagebox.showwarning('Thiếu site', 'Nhập tên site.')
            return
        moi, bo = C.tao_bai_tu_de_xuat(
            self.giac.db(), self.de_xuat, site,
            che_do_dang=self.v_che_do.get(), che_do_gia=self.v_gia.get())
        self.de_xuat = []
        self._ve_bang()
        self.nap_bai()
        self.giac.log(f'[SEO Post] Tạo mới {moi} bài, bỏ qua {bo}.')
        messagebox.showinfo(
            'Xong', f'Tạo mới {moi} bài.\nBỏ qua {bo} (trùng từ khoá đã có bài, '
                    f'hoặc là tên sản phẩm thuần).')

    # ============================================================ [4] hàng đợi
    def nap_bai(self):
        # Lỗi DB KHÔNG được kéo chết cả tab — hiện lên nhãn trạng thái để
        # người dùng đọc được, giống nguyên tắc "1 ảnh lỗi không kéo chết
        # cả bộ" ở xu_ly_anh.py.
        try:
            con = self.giac.db()
            self._nap_bai_that(con)
        except Exception as e:
            tin_loi = f'{type(e).__name__}: {e}'
            self.lb_tt.config(text=f'Không đọc được hàng đợi: {tin_loi}')
            self.giac.log(f'[SEO Post] nap_bai lỗi: {tin_loi}')

    def _nap_bai_that(self, con):
        self.bang2.delete(*self.bang2.get_children())
        for b in DB.liet_ke(con):
            wp = b.get('wp_url') or b.get('loi') or ''
            self.bang2.insert('', 'end', iid=b['bai_id'], values=(
                b['tu_khoa_chinh'],
                P.CONTENT_TYPE.get(b['content_type'], {}).get('nhan', b['content_type']),
                b['site'], b['che_do_dang'], b.get('so_sku', 0),
                b['trang_thai'], str(wp)[:120]),
                tags=(b['trang_thai'],))
        d = DB.dem_theo_trang_thai(con)
        self.lb_tt.config(
            text='  |  '.join(f'{k}: {v}' for k, v in sorted(d.items())) or 'Chưa có bài nào.')

    def _gan_sku(self):
        bai_id = self._dong_dang_chon(self.bang2)
        if not bai_id:
            messagebox.showwarning('Chưa chọn', 'Chọn 1 bài trong hàng đợi.')
            return
        bai = DB.lay_bai(self.giac.db(), bai_id)

        cs = tk.Toplevel(self.f)
        cs.title(f'Gắn SKU — {bai["tu_khoa_chinh"]}')
        cs.geometry('720x520')
        ttk.Label(cs, text='Lọc theo tên/mã sản phẩm rồi tick những SKU muốn gộp vào bài này:',
                  wraplength=690).pack(anchor='w', padx=12, pady=(12, 6))

        hloc = ttk.Frame(cs)
        hloc.pack(fill='x', padx=12)
        e = ttk.Entry(hloc, width=40)
        e.pack(side='left')
        bang = ttk.Treeview(cs, columns=('ds', 'rec', 'ten'), show='headings',
                            selectmode='extended', height=16)
        for c, n, w in [('ds', 'Dataset', 130), ('rec', 'Record', 130),
                        ('ten', 'Tên hàng', 420)]:
            bang.heading(c, text=n)
            bang.column(c, width=w)
        bang.pack(fill='both', expand=True, padx=12, pady=8)

        def _tim():
            bang.delete(*bang.get_children())
            tu = e.get().strip()
            try:
                sql = ('SELECT dataset_id, record_id, du_lieu_json FROM san_pham_phase2 '
                       + ('WHERE du_lieu_json LIKE ? ' if tu else '') + 'LIMIT 400')
                rows = self.giac.db().execute(sql, (f'%{tu}%',) if tu else ()).fetchall()
            except Exception as ex:
                tin_loi = f'{type(ex).__name__}: {ex}'
                messagebox.showerror('Lỗi', f'Chưa import MASTER nào?\n{tin_loi}', parent=cs)
                return
            for d, r, js in rows:
                try:
                    ten = json.loads(js).get('ten_goc', '')
                except Exception:
                    ten = ''
                bang.insert('', 'end', values=(d, r, ten))

        ttk.Button(hloc, text='Tìm', command=_tim).pack(side='left', padx=6)

        def _luu():
            ds = [(bang.item(i)['values'][0], str(bang.item(i)['values'][1]))
                  for i in bang.selection()]
            DB.gan_sku(self.giac.db(), bai_id, ds)
            self.nap_bai()
            cs.destroy()
            messagebox.showinfo('Xong', f'Đã gắn {len(ds)} SKU vào bài.')

        ttk.Button(cs, text='Lưu', command=_luu).pack(pady=(0, 12))
        _tim()

    # ============================================================ chạy nền
    def _chay(self, viec, hang_loat):
        """Sinh/đăng ở luồng nền — không đóng băng giao diện."""
        if hang_loat:
            tt = DB.MOI if viec == 'sinh' else DB.SINH_XONG
            ds = [b['bai_id'] for b in DB.liet_ke(self.giac.db(), trang_thai=tt)]
            if not ds:
                messagebox.showinfo('Không có gì', f'Không có bài nào ở trạng thái {tt}.')
                return
            gioi_han = self.giac.cau_hinh_int('GEMINI_QUOTA_NGAY', 20)
            if viec == 'sinh' and len(ds) > gioi_han:
                if not messagebox.askyesno(
                        'Cảnh báo quota',
                        f'{len(ds)} bài. Gemini free tier là {gioi_han} request/NGÀY tính '
                        f'theo project — quá {gioi_han} sẽ lỗi 429 hàng loạt.\n\nVẫn chạy?'):
                    return
        else:
            i = self._dong_dang_chon(self.bang2)
            if not i:
                messagebox.showwarning('Chưa chọn', 'Chọn 1 bài.')
                return
            ds = [i]

        giac = self.giac

        def _worker():
            # LUỒNG NỀN TUYỆT ĐỐI KHÔNG ĐỤNG TKINTER — mọi cập nhật đi qua
            # giac.ui(). Tkinter không thread-safe: treo/crash ngẫu nhiên.
            # giac.db() trả kết nối của CHÍNH luồng này (xem bẫy 1 ở đầu file).
            def _bao(text):
                giac.ui(lambda t=text: self.lb_tt.config(text=t))

            ok = loi = 0
            for n, bai_id in enumerate(ds, 1):
                _bao(f'[{n}/{len(ds)}] đang {viec}...')
                try:
                    con = giac.db()
                    t, tin = (C.sinh_bai(con, bai_id) if viec == 'sinh'
                              else C.dang_bai(con, bai_id))
                except Exception as ex:
                    t, tin = False, f'{type(ex).__name__}: {ex}'
                ok, loi = (ok + 1, loi) if t else (ok, loi + 1)
                giac.log(f'  [{n}/{len(ds)}] {bai_id}: {tin}')

            tong = f'Xong: {ok} thành công, {loi} lỗi. Xem chi tiết ở khung log.'
            giac.ui(lambda t=tong: (self.nap_bai(), self.lb_tt.config(text=t)))

        giac.chay_nen(_worker, ten='seo_post')


def gan_vao(nb_con, giac):
    """Điểm vào chuẩn. nb_con = Notebook cha. Trả về đối tượng tab."""
    t = TabSeoPost(nb_con, giac)
    # Nhãn giữ NGUYÊN như bản cũ. _v3_tab_cuon() cắt tiền tố số ('11. ')
    # trước khi hiện, nên đổi thành '11. SEO Post' là người dùng thấy khác.
    nb_con.add(t.ngoai, text='  SEO Post  ')
    return t
