# -*- coding: utf-8 -*-
"""Ver 5.9 — Màn hình "HÔM NAY": làm gì tiếp, cái gì đang chặn.

VÌ SAO CÓ MÀN HÌNH NÀY
    Tool đang có 23 tab con. Chúng được bồi thêm theo từng version, không
    phải theo cách một người làm SEO đi hết một ngày. Không tab nào trả lời
    được câu hỏi mở tool ra là hỏi đầu tiên:

        "Hôm nay làm gì? Cái gì đang chặn?"

    Muốn biết còn bao nhiêu SKU chưa sinh -> mở tab Hàng đợi, bấm lọc.
    Muốn biết hôm nay đã đốt bao nhiêu quota -> đếm tay trong log.
    Muốn biết bài nào lỗi -> mở tab Theo dõi, kéo tìm.
    Ba câu hỏi, ba tab, không câu nào có sẵn số.

    Sắp xếp lại 23 tab thành 5 nhóm khác vẫn là 23 tab. Cái thiếu là một
    màn hình TỔNG HỢP, nên làm cái đó trước khi bàn chuyện bày biện.

ĐÂY CŨNG LÀ PHÉP THỬ HỢP ĐỒNG
    Module này viết SAU giac_cam.py và KHÔNG được sửa giac_cam.py dòng nào.
    Nếu ráp một tính năng mới mà phải nới hợp đồng thì hợp đồng sai. Nó chỉ
    dùng đúng 5 chân + ui_tien_ich, không với vào vỏ ứng dụng lần nào.

NGUYÊN TẮC SỐ LIỆU — QUAN TRỌNG
    Chỉ hiện số ĐỌC ĐƯỢC TỪ DB. Cái nào chưa đo được thì ghi thẳng
    "chưa đo được" kèm lý do, KHÔNG ước lượng, KHÔNG bịa.
    Màn hình mà bịa một con số là mất giá trị cả màn hình.
"""
import datetime
import sqlite3
import tkinter as tk
from tkinter import ttk

import ui_tien_ich as UI

TEN_TAB = 'Hôm nay'

# Trạng thái trong bai_viet_phase2 (xem db_phase2._tao_schema)
CHUA_SINH = 'chua_sinh'
DA_DANG = 'da_dang'
LOI = 'loi'
DA_GO = 'da_go'


def _hom_nay():
    return datetime.date.today().isoformat()


def doc_so_lieu(con, quota_ngay=20):
    """Đọc mọi con số từ DB. Tách khỏi giao diện để test được headless.

    Trả dict. Khoá nào không đo được thì giá trị là None — bên vẽ sẽ hiện
    'chưa đo được' thay vì số 0 (0 và 'không biết' là hai chuyện khác nhau,
    lẫn lộn hai cái đó là cách bảng số liệu mất uy tín).
    """
    so = {'loi_doc': None, 'tong_sku': None, 'chua_sinh': None, 'da_dang': None,
          'bai_loi': None, 'da_go': None, 'dang_hom_nay': None,
          'quota_ngay': quota_ngay, 'quota_con': None, 'theo_profile': {},
          'site_dang_dung': []}

    def _hoi(sql, args=()):
        try:
            return con.execute(sql, args).fetchall()
        except sqlite3.Error:
            return None

    r = _hoi('SELECT COUNT(*) FROM san_pham_phase2')
    if r is None:
        so['loi_doc'] = ('Chưa có bảng dữ liệu nào. Vào tab "Nhập dữ liệu" '
                         'import file MASTER trước.')
        return so
    so['tong_sku'] = r[0][0]

    r = _hoi('SELECT trang_thai, COUNT(*) FROM bai_viet_phase2 GROUP BY trang_thai')
    dem = {row[0]: row[1] for row in (r or [])}
    so['da_dang'] = dem.get(DA_DANG, 0)
    so['bai_loi'] = dem.get(LOI, 0)
    so['da_go'] = dem.get(DA_GO, 0)

    # Chưa sinh = SKU chưa có dòng bài viết nào, CỘNG dòng còn ở 'chua_sinh'.
    r = _hoi('SELECT COUNT(*) FROM san_pham_phase2 sp WHERE NOT EXISTS ('
             '  SELECT 1 FROM bai_viet_phase2 bv'
             '  WHERE bv.dataset_id=sp.dataset_id AND bv.record_id=sp.record_id)')
    chua_co_dong = r[0][0] if r else 0
    so['chua_sinh'] = chua_co_dong + dem.get(CHUA_SINH, 0)

    # Quota: đếm bài ĐĂNG trong ngày hôm nay. ngay_dang lưu dạng ISO nên
    # so bằng tiền tố ngày là đủ, không cần parse.
    r = _hoi("SELECT COUNT(*) FROM bai_viet_phase2 "
             "WHERE ngay_dang IS NOT NULL AND substr(ngay_dang,1,10)=?", (_hom_nay(),))
    if r is not None:
        so['dang_hom_nay'] = r[0][0]
        so['quota_con'] = max(0, quota_ngay - r[0][0])

    r = _hoi('SELECT sp.profile_id, COUNT(*) FROM san_pham_phase2 sp '
             'GROUP BY sp.profile_id ORDER BY COUNT(*) DESC')
    so['theo_profile'] = {row[0]: row[1] for row in (r or [])}

    r = _hoi('SELECT DISTINCT site FROM bai_viet_phase2 WHERE site IS NOT NULL')
    so['site_dang_dung'] = sorted(row[0] for row in (r or []) if row[0])
    return so


def dung_viec_can_lam(so):
    """Sinh danh sách việc theo thứ tự ưu tiên, TỪ SỐ LIỆU thật.

    Trả list (muc_do, tieu_de, giai_thich). muc_do: 'chan' | 'nen' | 'xong'.
    Không có việc nào thì trả list rỗng — bên vẽ hiện 'không có gì gấp'.
    """
    viec = []
    if so.get('loi_doc'):
        return [('chan', 'Chưa có dữ liệu', so['loi_doc'])]

    if so.get('bai_loi'):
        viec.append(('chan', f'{so["bai_loi"]} bài đang ở trạng thái LỖI',
                     'Mở tab "Theo dõi", lọc trạng thái lỗi, đọc cột lỗi. '
                     'Lỗi 429 là hết quota Gemini, lỗi HTTP là phía WordPress.'))

    con = so.get('quota_con')
    if con is not None:
        if con == 0:
            viec.append(('chan', 'Hết quota đăng trong ngày',
                         f'Đã đăng {so["dang_hom_nay"]}/{so["quota_ngay"]} hôm nay. '
                         'Quota Gemini free tier tính theo GOOGLE CLOUD PROJECT, '
                         'không theo key — thêm key cùng project không tăng hạn mức.'))
        elif con <= 5:
            viec.append(('nen', f'Còn {con} lượt đăng hôm nay',
                         'Sắp chạm trần. Ưu tiên lô quan trọng, đừng đốt vào bài thử.'))

    if so.get('chua_sinh'):
        viec.append(('nen', f'{so["chua_sinh"]} SKU chưa sinh bài',
                     'TRƯỚC KHI SINH: mở tab "Hàng đợi", bấm "Soát mỏng/trùng…". '
                     'Lô nào toàn MỎNG thì đừng sinh — sinh ra cũng là bài trùng.'))

    if so.get('da_go'):
        viec.append(('nen', f'{so["da_go"]} bài đã gỡ khỏi web',
                     'Kiểm tra xem gỡ có chủ đích không, hay do lỗi đồng bộ wp_id.'))

    if not viec:
        viec.append(('xong', 'Không có gì đang chặn',
                     'Số liệu sạch. Việc tiếp theo tuỳ mày chọn.'))
    return viec


class TabHomNay:
    """Toàn bộ state nằm trong đây. Không nhét gì vào vỏ ứng dụng."""

    def __init__(self, cha, giac):
        self.giac = giac
        self.o_so = {}
        self.ngoai, self.f = UI.khung_cuon(cha, padding=16)
        self._dung_giao_dien()
        self.lam_moi()

    # ------------------------------------------------------------ giao diện
    def _dung_giao_dien(self):
        f = self.f
        dau = ttk.Frame(f)
        dau.pack(fill='x')
        ttk.Label(dau, text='Hôm nay', style='Dam.TLabel').pack(side='left')
        ttk.Button(dau, text='Làm mới', command=self.lam_moi).pack(side='right')
        self.lb_gio = ttk.Label(dau, text='', style='V3Mo.TLabel')
        self.lb_gio.pack(side='right', padx=10)

        ttk.Label(f, text='Mọi con số dưới đây đọc thẳng từ cơ sở dữ liệu. '
                          'Cái nào chưa đo được thì ghi rõ "chưa đo được" — không ước lượng.',
                  style='V3Mo.TLabel', wraplength=820,
                  justify='left').pack(anchor='w', pady=(2, 12))

        # ---------------------------------------------- hàng ô số
        khoi_so = ttk.Frame(f)
        khoi_so.pack(fill='x', pady=(0, 14))
        for khoa, nhan in [('tong_sku', 'SKU trong kho'),
                           ('chua_sinh', 'Chưa sinh bài'),
                           ('da_dang', 'Đã đăng'),
                           ('bai_loi', 'Đang lỗi'),
                           ('quota_con', 'Quota còn')]:
            o = ttk.Frame(khoi_so, relief='solid', borderwidth=1, padding=10)
            o.pack(side='left', fill='x', expand=True, padx=(0, 6))
            ttk.Label(o, text=nhan, style='V3Mo.TLabel').pack(anchor='w')
            lb = ttk.Label(o, text='—', font=('Segoe UI', 17))
            lb.pack(anchor='w')
            self.o_so[khoa] = lb

        # ---------------------------------------------- việc cần làm
        k1 = ttk.LabelFrame(f, text=' Việc cần làm — xếp theo mức chặn ', padding=10)
        k1.pack(fill='both', expand=True, pady=(0, 12))
        self.hop_viec = ttk.Frame(k1)
        self.hop_viec.pack(fill='both', expand=True)

        # ---------------------------------------------- kho hàng theo nhóm
        k2 = ttk.LabelFrame(f, text=' Kho hàng theo nhóm sản phẩm ', padding=10)
        k2.pack(fill='both', expand=True)
        self.bang_profile = ttk.Treeview(k2, columns=('profile', 'sl'),
                                         show='headings', height=5)
        self.bang_profile.heading('profile', text='Nhóm sản phẩm')
        self.bang_profile.heading('sl', text='Số SKU')
        self.bang_profile.column('profile', width=380, anchor='w')
        self.bang_profile.column('sl', width=90, anchor='e')
        self.bang_profile.pack(fill='both', expand=True)

        self.lb_site = ttk.Label(k2, text='', style='V3Mo.TLabel',
                                 wraplength=820, justify='left')
        self.lb_site.pack(anchor='w', pady=(8, 0))

    # ------------------------------------------------------------ số liệu
    def lam_moi(self):
        """Đọc DB ở LUỒNG NỀN, vẽ ở luồng chính. DB có thể chậm khi nhiều SKU."""
        giac = self.giac

        def _viec():
            try:
                quota = giac.cau_hinh_int('GEMINI_QUOTA_NGAY', 20)
                so = doc_so_lieu(giac.db(), quota)
            except Exception as e:
                tin_loi = f'{type(e).__name__}: {e}'      # hoá chuỗi trong except
                giac.log(f'[Hôm nay] đọc số liệu lỗi: {tin_loi}')
                so = {'loi_doc': f'Không đọc được dữ liệu: {tin_loi}'}
            giac.ui(lambda s=so: self._ve(s))

        giac.chay_nen(_viec, ten='hom_nay')

    def _ve(self, so):
        gio = datetime.datetime.now().strftime('%H:%M:%S')
        self.lb_gio.config(text=f'cập nhật {gio}')

        for khoa, lb in self.o_so.items():
            v = so.get(khoa)
            lb.config(text='—' if v is None else f'{v:,}')

        for w in self.hop_viec.winfo_children():
            w.destroy()
        mau = {'chan': '#B00020', 'nen': '#8A6D00', 'xong': '#0B7A28'}
        dau_dong = {'chan': 'CHẶN', 'nen': 'NÊN LÀM', 'xong': 'OK'}
        for muc, tieu_de, giai_thich in dung_viec_can_lam(so):
            hang = ttk.Frame(self.hop_viec)
            hang.pack(fill='x', pady=(0, 8))
            ttk.Label(hang, text=f'[{dau_dong[muc]}]  {tieu_de}',
                      foreground=mau[muc]).pack(anchor='w')
            ttk.Label(hang, text=giai_thich, style='V3Mo.TLabel',
                      wraplength=780, justify='left').pack(anchor='w', padx=(18, 0))

        self.bang_profile.delete(*self.bang_profile.get_children())
        for pid, n in (so.get('theo_profile') or {}).items():
            self.bang_profile.insert('', 'end', values=(pid, f'{n:,}'))

        ds = so.get('site_dang_dung') or []
        self.lb_site.config(
            text=('Site đang dùng: ' + ', '.join(ds)) if ds
            else 'Chưa có bài nào gắn site.')


def gan_vao(nb_con, giac):
    """Điểm vào chuẩn."""
    t = TabHomNay(nb_con, giac)
    nb_con.add(t.ngoai, text=f'  {TEN_TAB}  ')
    return t
