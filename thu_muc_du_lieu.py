# -*- coding: utf-8 -*-
"""Ver 4.4.1.6 — THƯ MỤC DỮ LIỆU DÙNG CHUNG.

VẤN ĐỀ NÓ GIẢI
    Trước bản này `phase2-du-lieu.db` và `cau-hinh.env` nằm NGAY TRONG thư
    mục phiên bản (…\\SONEALEO-ULTRA-4.4.1.5\\). Mỗi lần lên version phải
    copy tay 2 file sang thư mục mới. Hai kiểu chết:

      - Quên copy  -> mở app thấy DB trống, tưởng mất sạch bài đã đăng.
      - Copy ngược -> đè bản mới bằng bản cũ, mất trạng thái vừa làm,
        KHÔNG có thông báo nào, app chạy êm ru với dữ liệu cũ.

    Và một kiểu tệ hơn cả hai: mở app từ thư mục version CŨ thì nó ghi vào
    DB cũ nằm cạnh đó, trong khi mình tưởng đang dùng bản mới.

CÁCH GIẢI
    Cả hai file chuyển ra %APPDATA%\\SONEALEO\\ (Windows) hoặc
    ~/.local/share/SONEALEO (Linux/macOS). Ngoài mọi thư mục version, nên
    lên version chỉ còn giải nén và chạy.

DI CƯ TỰ ĐỘNG
    Lần đầu chạy: nếu thư mục chung CHƯA có file mà thư mục version CÓ,
    tự COPY sang (copy — KHÔNG di chuyển, KHÔNG xoá bản cũ).
    File cũ được đổi đuôi .da-chuyen-doi để lần sau không copy lại,
    nhưng nội dung vẫn còn nguyên nếu cần lùi.

    Đã có file ở thư mục chung thì TUYỆT ĐỐI không đụng — thư mục chung
    luôn thắng. Không bao giờ ghi đè dữ liệu đang sống bằng file cũ.

ÉP DÙNG ĐƯỜNG DẪN KHÁC
    Đặt biến môi trường SONEALEO_DATA_DIR trỏ tới thư mục mong muốn.
"""
import os
import shutil
import sys
from pathlib import Path

TEN_DB = 'phase2-du-lieu.db'
TEN_ENV = 'cau-hinh.env'

_nhat_ky_di_cu = []


def _thu_muc_mac_dinh():
    ep = os.environ.get('SONEALEO_DATA_DIR', '').strip()
    if ep:
        return Path(ep)
    if sys.platform == 'win32':
        goc = os.environ.get('APPDATA') or os.path.expanduser('~')
        return Path(goc) / 'SONEALEO'
    if sys.platform == 'darwin':
        return Path(os.path.expanduser('~/Library/Application Support/SONEALEO'))
    return Path(os.environ.get('XDG_DATA_HOME')
                or os.path.expanduser('~/.local/share')) / 'SONEALEO'


def thu_muc_du_lieu():
    """Trả Path thư mục dữ liệu chung, tạo nếu chưa có.

    Không tạo được (ổ chỉ đọc, thiếu quyền) thì lùi về thư mục mã nguồn —
    app vẫn chạy như bản cũ thay vì crash.
    """
    tm = _thu_muc_mac_dinh()
    try:
        tm.mkdir(parents=True, exist_ok=True)
        thu = tm / '.ghi-thu'
        thu.write_text('x', encoding='utf-8')
        thu.unlink()
        return tm
    except Exception as e:
        _nhat_ky_di_cu.append(
            f'CẢNH BÁO: không dùng được {tm} ({type(e).__name__}), '
            f'quay về thư mục mã nguồn.')
        return Path(__file__).parent


def _di_cu_1_file(ten, thu_muc_cu, thu_muc_moi, phu_kien=()):
    """Copy file từ thư mục version sang thư mục chung, MỘT LẦN duy nhất.

    phu_kien: các file đi kèm phải copy cùng (SQLite WAL: -wal, -shm).
    Bỏ sót -wal là mất giao dịch chưa checkpoint.
    """
    dich = thu_muc_moi / ten
    nguon = thu_muc_cu / ten
    if dich.exists():
        return          # thư mục chung LUÔN thắng, không bao giờ đè
    if not nguon.exists():
        return
    try:
        shutil.copy2(nguon, dich)
        for hau_to in phu_kien:
            p = thu_muc_cu / (ten + hau_to)
            if p.exists():
                shutil.copy2(p, thu_muc_moi / (ten + hau_to))
        _nhat_ky_di_cu.append(f'Đã chuyển {ten}: {nguon}  ->  {dich}')
        try:
            danh_dau = nguon.with_suffix(nguon.suffix + '.da-chuyen-doi')
            if not danh_dau.exists():
                nguon.rename(danh_dau)
                _nhat_ky_di_cu.append(
                    f'Bản cũ đổi tên thành {danh_dau.name} (nội dung còn nguyên).')
        except Exception:
            pass        # đổi tên hỏng không sao, bản chính đã copy xong
    except Exception as e:
        _nhat_ky_di_cu.append(f'LỖI chuyển {ten}: {type(e).__name__}: {e}')


def chuan_bi(thu_muc_cu=None):
    """Gọi MỘT LẦN lúc khởi động, TRƯỚC khi mở DB hay đọc env."""
    thu_muc_cu = Path(thu_muc_cu or Path(__file__).parent)
    moi = thu_muc_du_lieu()
    if moi.resolve() == thu_muc_cu.resolve():
        return moi
    _di_cu_1_file(TEN_DB, thu_muc_cu, moi, phu_kien=('-wal', '-shm'))
    _di_cu_1_file(TEN_ENV, thu_muc_cu, moi)
    return moi


def duong_dan_db():
    return thu_muc_du_lieu() / TEN_DB


def duong_dan_env():
    return thu_muc_du_lieu() / TEN_ENV


def nhat_ky():
    return list(_nhat_ky_di_cu)
