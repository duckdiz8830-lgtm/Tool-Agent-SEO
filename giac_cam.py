# -*- coding: utf-8 -*-
r"""Ver 5.8 — GIẮC CẮM: hợp đồng giữa vỏ ứng dụng và các module tính năng.

TẠI SAO CÓ FILE NÀY
    Đo ngày 22/08/2026 trên 5 module tính năng đang chạy:

        tab_anh.py            1508 dòng —  2 điểm chạm vào app
        hang_doi.py            436 dòng —  0
        man_hinh_du_lieu.py    492 dòng —  0
        giao_dien_2_5.py       587 dòng —  0
        tab_seo_post.py        410 dòng — 14

    3.023 dòng đã gần như tự lập. Nhưng **0 thứ được từ 2 module trở lên
    cùng dùng** — không có chuẩn chung nào cả. Mỗi module tự chế chấu riêng:
    tab_anh gọi app.ui + app.chay_nen_phase2, hang_doi dùng print(),
    tab_seo_post tự đẻ 14 thuộc tính app._sp_*, giao_dien_2_5 không có cả
    điểm vào chuẩn.

    Ráp vào thì được. Ráp ra thì phải đọc code mới biết gỡ dây nào.

BA MÂU THUẪN FILE NÀY SINH RA ĐỂ GIẢI

    1. API AN TOÀN TRÔNG NHƯ HACK, API TRÔNG CHUẨN THÌ KHÔNG AN TOÀN.
       print() từ luồng nền là HỢP LỆ — ChuyenHuongIn là router stdout theo
       từng thread, worker đăng ký queue nào thì print() đi đúng queue đó,
       marshal về luồng chính an toàn. Ngược lại app.log() ghi THẲNG vào
       widget self.log_o, không marshal gì cả -> gọi từ luồng nền là đúng
       loại bug đã vá ở tab_seo_post.py Ver 5.7.
       -> giac.log() tự nhận biết luồng, chọn đúng đường.

    2. HAI RUNNER NỀN, CÁI TÊN "CHUNG" MỚI LÀ CÁI HỎNG.
       chay_nen()        khoá cứng self.nut_chay / self.nut_dung — 2 nút của
                         tab 5 RMU, tức UI manager=NONE không bao giờ hiện.
       chay_nen_phase2() không dính widget nào, là bản tab_anh.py đang dùng.
       Tên nói ngược thực tế. Ai đọc code rồi chọn chay_nen() vì "nó là bản
       chung" đều dính.
       -> giac.chay_nen() trỏ về bản SẠCH.

    3. 18 CHỖ GỌI ket_noi(), KHÔNG KỶ LUẬT LUỒNG.
       sqlite3 mặc định check_same_thread=True. Ver 5.7 đã vá tab_seo_post
       (mỗi luồng một kết nối) nhưng chỉ vá tại chỗ đó.
       -> giac.db() phổ quát hoá cách vá ấy.

NĂM CHÂN CẮM — module tính năng CHỈ được dùng đúng 5 thứ này

    giac.log(msg, muc='')        in ra khung log chung, an toàn mọi luồng
    giac.ui(fn)                  nhờ luồng chính chạy fn
    giac.chay_nen(fn, ten='')    chạy fn ở luồng nền
    giac.db()                    kết nối SQLite của ĐÚNG luồng hiện tại
    giac.cau_hinh(ten, md=None)  đọc cấu hình đã nạp
    giac.dang_chon()             người dùng đang làm việc trên dataset/mẫu nào

    Ngoài 5 thứ này, module KHÔNG được với vào vỏ ứng dụng. Khung cố ý
    KHÔNG cho with tới: chạm thuộc tính lạ là ném LoiViPhamGiac nêu đích
    danh tên thuộc tính và nhắc dùng chân nào.

ĐIỂM VÀO CHUẨN

    def gan_vao(parent, giac):
        '''parent = widget cha (Notebook/Frame). Trả về tên tab, hoặc None.'''

    Bỏ dung_tab / dung / mo / tao. Một tên duy nhất.

CỬA THOÁT HIỂM — CÓ CHỦ Ý, VÀ ĐẾM ĐƯỢC

    giac.thoat_hiem('lý do')  trả về đối tượng app thô.

    Không thể ép 5 module đang chạy sạch trong một bước. Cửa này cho phép
    chuyển dần, ĐỔI LẠI mọi chỗ dùng đều grep ra được và bị
    test_v58_ranh_gioi.py đếm. Con số đó CHỈ ĐƯỢC GIẢM, không được tăng.
    Đây là cái thước, không phải cái cớ.

LỢI ÍCH KÉO THEO (thật ra là lý do lớn nhất)
    giac_cam.py KHÔNG import tkinter. Dựng được GiacCamGia() không cần giao diện
    -> module tính năng test được headless, không cần Xvfb, không cần dựng
    cả app 787 widget. Với người định ráp nhiều tính năng thì đây mới là
    thứ đáng giá nhất, hơn cả việc chia file.
"""
import os
import sqlite3
import threading

__all__ = ['GiacCam', 'GiacCamGia', 'LoiViPhamGiac', 'CHAN_HOP_LE', 'DIEM_VAO']

# Đúng 5 chân. test_v58_ranh_gioi.py đọc trực tiếp danh sách này.
CHAN_HOP_LE = frozenset({'log', 'ui', 'chay_nen', 'db', 'cau_hinh', 'dang_chon'})

# Biến thể tiện dụng — KHÔNG phải năng lực mới, chỉ là đường tắt ép kiểu
# cho chân cau_hinh. Tách riêng để danh sách 5 chân ở trên giữ nguyên nghĩa
# "5 năng lực", đồng thời test không báo oan khi module dùng đường tắt.
# Thêm gì vào đây phải TRẢ LỜI ĐƯỢC: nó có mở thêm quyền truy cập nào không?
# Nếu có -> đó là chân thứ 6, phải bàn, không được lén nhét vào đây.
CHAN_TIEN_DUNG = frozenset({'cau_hinh_bool', 'cau_hinh_int'})

# Tên điểm vào chuẩn của module tính năng.
DIEM_VAO = 'gan_vao'


class LoiViPhamGiac(AttributeError):
    """Module tính năng với ra ngoài 5 chân cắm."""


class GiacCam:
    """Vỏ bọc quanh đối tượng app. Chỉ hở đúng 5 chân.

    Cố ý KHÔNG kế thừa và KHÔNG uỷ nhiệm tự động: uỷ nhiệm tự động thì
    module vẫn với tới mọi thứ của app và ta lại có God Class, chỉ khác là
    nằm ở nhiều file hơn.
    """

    __slots__ = ('_app', '_db_theo_luong', '_ten_module', '_da_thoat_hiem')

    def __init__(self, app, ten_module=''):
        object.__setattr__(self, '_app', app)
        object.__setattr__(self, '_db_theo_luong', threading.local())
        object.__setattr__(self, '_ten_module', ten_module or '(không tên)')
        object.__setattr__(self, '_da_thoat_hiem', [])

    # ---------------------------------------------------------------- 1. log
    def log(self, msg, muc=''):
        """In ra khung log chung. An toàn ở MỌI luồng.

        Luồng chính -> gọi thẳng app.log() (ghi widget, đang ở đúng luồng).
        Luồng nền   -> print(), để ChuyenHuongIn router đẩy qua queue.
        Không có app.log -> print() (chế độ headless/test).
        """
        s = str(msg)
        if threading.current_thread() is not threading.main_thread():
            print(s)
            return
        ham = getattr(self._app, 'log', None)
        if callable(ham):
            try:
                ham(s, muc) if muc else ham(s)
                return
            except TypeError:
                try:
                    ham(s)
                    return
                except Exception:
                    pass
            except Exception:
                pass
        print(s)

    # ----------------------------------------------------------------- 2. ui
    def ui(self, fn):
        """Nhờ luồng chính chạy fn. Luồng nền TUYỆT ĐỐI không đụng tkinter.

        CẢNH BÁO cho người viết module: fn chạy TRỄ. Đừng bắt biến của
        `except ... as e` vào fn — Python xoá tên đó khi thoát khối except,
        lúc fn chạy sẽ nổ NameError và bị nuốt. Hoá lỗi thành chuỗi trước,
        rồi truyền bằng default-arg. (Bug thật, vá ở Ver 5.7.)
        """
        ham = getattr(self._app, 'ui', None)
        if callable(ham):
            return ham(fn)
        return fn()          # headless: chạy luôn

    # ----------------------------------------------------------- 3. chay_nen
    def chay_nen(self, fn, ten=''):
        """Chạy fn ở luồng nền.

        Trỏ về chay_nen_phase2 — bản SẠCH, không dính widget. KHÔNG dùng
        chay_nen() của app vì bản đó khoá cứng nut_chay/nut_dung của tab 5
        RMU (UI manager=NONE, không bao giờ hiện).
        """
        ham = getattr(self._app, 'chay_nen_phase2', None)
        if callable(ham):
            return ham(fn)
        nhan = ten or self._ten_module
        t = threading.Thread(target=fn, name=f'giac:{nhan}', daemon=True)
        t.start()
        return t

    # ----------------------------------------------------------------- 4. db
    def db(self):
        """Kết nối SQLite của ĐÚNG luồng đang gọi.

        sqlite3 mặc định check_same_thread=True: một Connection chỉ dùng
        được ở luồng đã tạo ra nó. Dùng chung một kết nối giữa luồng UI và
        luồng nền -> ProgrammingError ở MỌI thao tác, và except Exception
        thường nuốt mất, hiện ra thành "0 thành công, N lỗi".
        Chi phí mở kết nối đo được 0,24 ms -> mở theo luồng là rẻ.

        GIỚI HẠN — ĐỌC KỸ, ĐÃ VẤP THẬT:
            Chân này chỉ trả KẾT NỐI. Nó KHÔNG tạo bảng riêng của module.
            Module nào có schema riêng thì phải tự gọi tao_schema() của
            mình MỘT LẦN sau khi lấy kết nối.

            Ver 5.8 vấp đúng chỗ này: tab_seo_post đổi từ
            db_seo_post.ket_noi() (= db_phase2.ket_noi() + tao_schema)
            sang giac.db() (chỉ có vế đầu). Trên máy dev có sẵn DB cũ nên
            KHÔNG lộ; chỉ lộ khi chạy với thư mục dữ liệu TRỐNG: bảng
            bai_seo chưa tồn tại -> liet_ke() ném lỗi -> tab không dựng
            được -> app còn 13 tab thay vì 14. Bắt được nhờ test_ver3_ui
            chạy trong sandbox sạch của run_tests.py.
        """
        con = getattr(self._db_theo_luong, 'con', None)
        if con is not None:
            return con
        mo = getattr(self._app, 'db_ket_noi', None)
        if callable(mo):
            con = mo()
        else:
            import db_phase2
            con = db_phase2.ket_noi()
        self._db_theo_luong.con = con
        return con

    # ----------------------------------------------------------- 5. cau_hinh
    def cau_hinh(self, ten, mac_dinh=None):
        """Đọc một giá trị cấu hình đã nạp.

        Hiện đọc os.environ (tool nạp cau-hinh.env vào đó lúc khởi động).
        Đi qua đây thay vì os.environ.get() rải rác để sau này đổi nguồn
        cấu hình chỉ phải sửa một chỗ.
        """
        ham = getattr(self._app, 'cau_hinh', None)
        if callable(ham):
            try:
                return ham(ten, mac_dinh)
            except TypeError:
                pass
        v = os.environ.get(ten)
        return mac_dinh if v is None or str(v).strip() == '' else v

    # ----------------------------------------------------- 6. dang_chon
    def dang_chon(self):
        """Người dùng đang làm việc trên dataset/mẫu/site nào.

        Trả dict: {'dataset_id': str|None, 'mau': str|None, 'site': str|None}

        VÌ SAO ĐÂY LÀ CHÂN THỨ 6, KHÔNG PHẢI TIỆN ÍCH — đã cân nhắc, không
        phải phình hợp đồng cho tiện:
            Đo ngày 22/08/2026 trên 4 nhóm method sắp tách khỏi God Class:
            38 lời gọi "ra ngoài nhóm" gom lại chỉ còn 6 hàm. 18 lời gọi đã
            có chỗ (db/cau_hinh), 10 là tiện ích tkinter thuần (khung_cuon,
            the) -> ui_tien_ich.py. Còn đúng 10 lời gọi là
            _phase2_dataset_id_dang_chon() + _phase2_mau_dang_chon().

            Hai hàm đó KHÔNG phải tiện ích: chúng đọc STATE CỦA VỎ ỨNG DỤNG
            (ô chọn dataset, ô nhập mẫu nằm ở tab khác). Đúng tiêu chí đã
            đặt ra: cần state/dịch vụ của vỏ -> chân cắm; chỉ cần tkinter ->
            tiện ích. Không có chân này thì mỗi module tách ra sẽ phải
            thoat_hiem() hoặc tự dựng ô chọn riêng -> mỗi tab một dataset,
            đúng loại lỗi khó tìm nhất.

        LƯU Ý: gọi TẠI LÚC DÙNG, đừng cache. Người dùng đổi dataset ở tab
        khác bất cứ lúc nào; giá trị cache là giá trị sai.
        """
        ham = getattr(self._app, 'dang_chon', None)
        if callable(ham):
            try:
                d = ham() or {}
                return {'dataset_id': d.get('dataset_id'), 'mau': d.get('mau'),
                        'site': d.get('site')}
            except Exception:
                pass
        return {'dataset_id': None, 'mau': None, 'site': None}

    def cau_hinh_bool(self, ten, mac_dinh=False):
        v = self.cau_hinh(ten, None)
        if v is None:
            return bool(mac_dinh)
        return str(v).strip().lower() in ('1', 'true', 'yes', 'y', 'on', 'co', 'có')

    def cau_hinh_int(self, ten, mac_dinh=0):
        v = self.cau_hinh(ten, None)
        try:
            return int(str(v).strip())
        except (TypeError, ValueError):
            return mac_dinh

    # ------------------------------------------------------- cửa thoát hiểm
    def thoat_hiem(self, ly_do):
        """Trả về app thô. MỖI lần dùng là một món nợ, và nó bị đếm.

        Chỉ dùng khi đang chuyển dần một module cũ và chưa gỡ hết dây.
        Bắt buộc nêu lý do bằng chữ — để người sau biết phải gỡ cái gì.
        test_v58_ranh_gioi.py đếm số lần xuất hiện trong source; con số đó
        CHỈ ĐƯỢC GIẢM.
        """
        if not ly_do or not str(ly_do).strip():
            raise LoiViPhamGiac(
                'thoat_hiem() bắt buộc nêu lý do bằng chữ, '
                'để người gỡ nợ sau này biết phải gỡ cái gì.')
        self._da_thoat_hiem.append(str(ly_do))
        return self._app

    def no_thoat_hiem(self):
        """Danh sách lý do đã dùng cửa thoát hiểm trong phiên chạy này."""
        return list(self._da_thoat_hiem)

    # ------------------------------------------------------------ chặn với
    def __getattr__(self, ten):
        raise LoiViPhamGiac(
            f'Module {self._ten_module!r} với tới `giac.{ten}` — không nằm '
            f'trong 5 chân cắm.\n'
            f'  Được phép: {", ".join(sorted(CHAN_HOP_LE))}\n'
            f'  Cần log       -> giac.log(msg)\n'
            f'  Cần chạy nền  -> giac.chay_nen(fn)\n'
            f'  Cần đụng UI   -> giac.ui(fn)\n'
            f'  Cần DB        -> giac.db()\n'
            f'  Cần cấu hình  -> giac.cau_hinh(ten)\n'
            f'  Thật sự cần thứ khác -> giac.thoat_hiem("lý do cụ thể"), '
            f'và ghi vào docs/KNOWN-ISSUES.md.')

    def __setattr__(self, ten, gia_tri):
        raise LoiViPhamGiac(
            f'Module {self._ten_module!r} gán `giac.{ten}` — cấm. '
            f'Module phải tự giữ state của mình, không nhét vào vỏ ứng dụng. '
            f'(Đây đúng là cách tab_seo_post.py đẻ ra 14 thuộc tính app._sp_*.)')

    def __repr__(self):
        return f'<GiacCam cho {self._ten_module!r}, {len(self._da_thoat_hiem)} lần thoát hiểm>'


class GiacCamGia(GiacCam):
    """Giắc cắm không cần giao diện — để test module tính năng headless.

    log  -> gom vào list, đọc bằng .da_in()
    ui   -> chạy ngay
    nền  -> chạy ĐỒNG BỘ (test tất định, không phải chờ thread)
    db   -> sqlite in-memory, tự tạo schema nếu có db_phase2
    """

    __slots__ = ('_dong_log', '_cau_hinh_gia', '_con_gia', '_chon_gia')

    def __init__(self, cau_hinh=None, ten_module='test', dang_chon=None):
        super().__init__(app=None, ten_module=ten_module)
        object.__setattr__(self, '_dong_log', [])
        object.__setattr__(self, '_cau_hinh_gia', dict(cau_hinh or {}))
        object.__setattr__(self, '_con_gia', None)
        object.__setattr__(self, '_chon_gia',
                           dict(dang_chon or {'dataset_id': None, 'mau': None, 'site': None}))

    def dang_chon(self):
        return dict(self._chon_gia)

    def log(self, msg, muc=''):
        self._dong_log.append(str(msg))

    def da_in(self):
        return list(self._dong_log)

    def ui(self, fn):
        return fn()

    def chay_nen(self, fn, ten=''):
        return fn()          # đồng bộ: test tất định

    def db(self):
        if self._con_gia is None:
            con = sqlite3.connect(':memory:', check_same_thread=False)
            con.row_factory = sqlite3.Row
            try:
                import db_phase2
                tao = getattr(db_phase2, '_tao_schema', None)
                if callable(tao):
                    tao(con)
            except Exception:
                pass
            object.__setattr__(self, '_con_gia', con)
        return self._con_gia

    def cau_hinh(self, ten, mac_dinh=None):
        if ten in self._cau_hinh_gia:
            return self._cau_hinh_gia[ten]
        return super().cau_hinh(ten, mac_dinh)


if __name__ == '__main__':
    sai = 0

    def kt(ten, dk):
        global sai
        dat = bool(dk)
        sai += 0 if dat else 1
        print(f'  {"OK  " if dat else "SAI "} {ten}')

    k = GiacCamGia({'MODEL_GEMINI': 'x-test'})
    k.log('dòng một')
    kt('log gom được', k.da_in() == ['dòng một'])
    kt('ui chạy ngay', k.ui(lambda: 7) == 7)
    kt('chay_nen chạy đồng bộ', k.chay_nen(lambda: 8) == 8)
    kt('cau_hinh đọc bản giả', k.cau_hinh('MODEL_GEMINI') == 'x-test')
    kt('cau_hinh trả mặc định', k.cau_hinh('KHONG_CO_DAU', 'md') == 'md')
    kt('cau_hinh_bool', k.cau_hinh_bool('KHONG_CO', True) is True)
    kt('cau_hinh_int rác -> mặc định', k.cau_hinh_int('KHONG_CO', 42) == 42)
    kt('db mở được', k.db() is not None)
    kt('db cùng luồng tái dùng', k.db() is k.db())

    try:
        k.nut_chay
        kt('chặn đọc thuộc tính lạ', False)
    except LoiViPhamGiac as e:
        kt('chặn đọc thuộc tính lạ', 'không nằm trong 5 chân' in str(e))
    try:
        k.abc = 1
        kt('chặn gán thuộc tính', False)
    except LoiViPhamGiac:
        kt('chặn gán thuộc tính', True)
    try:
        k.thoat_hiem('')
        kt('thoat_hiem đòi lý do', False)
    except LoiViPhamGiac:
        kt('thoat_hiem đòi lý do', True)
    kt('thoat_hiem có lý do thì ghi nợ',
       (k.thoat_hiem('đang chuyển dần tab X') is None) and k.no_thoat_hiem() == ['đang chuyển dần tab X'])
    kt('CHAN_HOP_LE đúng 6 chân', len(CHAN_HOP_LE) == 6)
    kt('dang_chon trả đủ 3 khoá',
       set(k.dang_chon()) == {'dataset_id', 'mau', 'site'})

    print(f'\nTONG SAI: {sai}')
    raise SystemExit(1 if sai else 0)
