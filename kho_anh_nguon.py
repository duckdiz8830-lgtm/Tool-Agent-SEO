# -*- coding: utf-8 -*-
"""
kho_anh_nguon.py — Ver 6.3. Lõi đề xuất ảnh từ KHO ẢNH GỐC của công ty.

PHÂN BIỆT VỚI CÁC MODULE ẢNH ĐÃ CÓ (đọc kỹ trước khi sửa):
    workspace_anh.py  — thư mục LÀM VIỆC của từng bài (_goc, meta.json, 5 vai trò).
    xu_ly_anh.py      — resize/watermark/lọc mờ, xử lý ảnh ĐÃ chọn.
    tab_anh.py        — UI gán ảnh vào 5 ô của bài.
    kho_anh_nguon.py  — module NÀY. Chỉ TRA CỨU kho ảnh gốc chưa phân loại
                        (vd D:\\W-ANH GOC) để gợi ý ứng viên. KHÔNG copy, KHÔNG
                        gán, KHÔNG sửa gì. Chọn xong vẫn đi qua WS.gan_anh().

NGUYÊN TẮC:
  - CHỈ ĐỌC. Không ghi DB, không đụng MASTER, không gọi WooCommerce.
  - Trả về danh sách ứng viên có xếp hạng. Người duyệt bằng mắt, tool không tự gắn.
  - Không phụ thuộc module nào của SONEALEO -> ghép vào bằng 3 dòng, gỡ ra cũng 3 dòng.

CÁCH DÙNG NHANH:
    import kho_anh_nguon as KAN
    kho = KAN.KhoAnh(KAN.goc_kho())       # đường dẫn lấy từ cau-hinh.env
    kho.nap_index()                       # lần đầu quét, sau đó đọc cache
    ds = kho.de_xuat(**KAN.tu_row(row))   # row = dòng MASTER của bài
    kho.mo_thu_muc(ds[0].duong_dan)       # bật Explorer, select sẵn file

CHẠY THỬ ĐỘC LẬP:
    python kho_anh_nguon.py                       # self-test
    python kho_anh_nguon.py "D:\\W-ANH GOC"        # liệt kê folder + loại nhận ra
    python kho_anh_nguon.py "D:\\W-ANH GOC" "EMIC-250" "máy biến áp" "EMIC"
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image
    CO_PIL = True
except ImportError:
    CO_PIL = False

# Giữ ĐỒNG BỘ với workspace_anh.DUOI_ANH — lệch thì kho gốc và workspace
# bất đồng ý kiến về "cái gì là ảnh".
DUOI_ANH = {".jpg", ".jpeg", ".jfif", ".png", ".webp", ".heic", ".bmp",
            ".avif", ".gif", ".tif", ".tiff"}


def hash_file(duong_dan: str) -> str:
    """SHA-256 rút gọn 16 ký tự — PHẢI khớp workspace_anh.hash_file().

    Đây là cách duy nhất biết một tấm trong kho gốc đã được gán cho bài nào
    chưa: workspace ghi `hash_goc`, không ghi đường dẫn nguồn. So theo tên
    file sẽ trượt (gan_anh đổi tên khi trùng), so theo hash thì không.
    """
    h = hashlib.sha256()
    try:
        with open(duong_dan, "rb") as fh:
            for khoi in iter(lambda: fh.read(1 << 20), b""):
                h.update(khoi)
    except OSError:
        return ""
    return h.hexdigest()[:16]

# Tên folder rác, bỏ qua khi quét
FOLDER_BO_QUA = {"thumbs", "__macosx", ".git", "node_modules", "cache", "temp", "tmp"}

# Từ khóa LOẠI, khớp prefix dài nhất trước.
# Trích từ cấu trúc thật của kho W-ANH GOC (LOẠI + HÃNG).
TU_KHOA_LOAI = [
    "bien dong ha the ct", "bien dong ti", "bien dong ha the",
    "cau dao dien di dong", "chong set cao the", "do bao ho dien",
    "dau cap te", "dau cap", "bien ap tu", "bien ap", "bien tan",
    "acb ocr tester", "contactor", "chi ong", "cong to", "cam bien",
    "cap mang", "acquy", "cap", "acb", "ats", "cb", "ds",
]
TU_KHOA_LOAI.sort(key=len, reverse=True)

# Ánh xạ cách gọi trong MASTER -> từ khóa LOẠI của tên folder.
# Sửa/thêm ở đây khi gặp SKU không khớp. Đây là chỗ duy nhất cần bảo trì tay.
ANH_XA_LOAI = {
    "may bien ap": "bien ap",
    "mba": "bien ap",
    "bien ap": "bien ap",
    "tram bien ap": "bien ap",
    "bien dong": "bien dong ti",
    "ct": "bien dong ti",
    "bien dong ti": "bien dong ti",
    "cap": "cap",
    "day cap": "cap",
    "cap dien": "cap",
    "cap trung the": "cap",
    "cap ha the": "cap",
    "dau cap": "dau cap",
    "dau cap co dan": "dau cap",
    "hop dau cap": "dau cap",
    "chi": "chi ong",
    "chi ong": "chi ong",
    "cau chi": "chi ong",
    "fco": "chi ong",
    "dao cach ly": "ds",
    "ds": "ds",
    "acb": "acb",
    "mccb": "cb",
    "mcb": "cb",
    "cb": "cb",
    "ats": "ats",
    "contactor": "contactor",
    "khoi dong tu": "contactor",
    "bien tan": "bien tan",
    "cam bien": "cam bien",
    "cong to": "cong to",
    "cong to dien": "cong to",
    "chong set": "chong set cao the",
    "acquy": "acquy",
}

# Ánh xạ tên hãng trong MASTER -> tên hãng trong folder (khi viết khác nhau).
ANH_XA_HANG = {
    "3m": "3m",
    "abb": "abb",
    "schneider electric": "schneider",
    "schneider": "schneider",
    "ls": "ls",
    "ls electric": "ls",
    "mitsubishi": "mitsu",
    "hyundai": "hyundai",
    "emic": "emic",
    "cadivi": "cadivi",
    "cadisun": "cadisun",
    "daphaco": "daphaco",
    "thipha": "thipha",
    "tayaa": "tayaa",
    "thang long": "thang long",
    "dai long": "dai long",
    "viet thai": "viet thai",
    "prysmian": "prysmian",
    "cellpack": "cellpack",
    "raychem": "raychem",
    "eti": "eti",
    "siba": "siba",
    "ec insulator": "ec insulator",
    "ab chance": "ab chance",
}


# ---------------------------------------------------------------- chuẩn hóa

def chuan_hoa(s: str) -> str:
    """Bỏ dấu tiếng Việt, về chữ thường, gộp khoảng trắng, bỏ ký tự lạ."""
    if not s:
        return ""
    s = str(s).replace("Đ", "D").replace("đ", "d")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tach_folder(ten_folder: str) -> tuple[str, str]:
    """'BIEN AP TU EMIC' -> ('bien ap tu', 'emic'). Không nhận ra loại -> ('', toàn bộ)."""
    t = chuan_hoa(ten_folder)
    for loai in TU_KHOA_LOAI:
        if t == loai:
            return loai, ""
        if t.startswith(loai + " "):
            return loai, t[len(loai):].strip()
    return "", t


def suy_loai_tu_ten(ten: str) -> str:
    """Suy LOẠI sản phẩm từ tên hàng trong MASTER.

    Vì sao không dùng kien_thuc_bien_thien.dac_trung(): hàm đó trả 'loai' là
    dầu/khô (kiểu MBA), không phải chủng loại sản phẩm. Ở đây cần 'máy biến áp'
    vs 'đầu cáp' vs 'cáp' để bắt sang tên folder.

    Neo vào cụm DÀI trước: 'dau cap' phải thắng 'cap', không thì đầu cáp bị
    nhận nhầm thành cáp và chỉ sang nhầm folder.
    """
    t = chuan_hoa(ten)
    if not t:
        return ""
    for khoa, loai in _NEO_TEN:
        if re.search(r"\b" + khoa + r"\b", t):
            return loai
    return ""


# (mẫu tìm trong tên hàng, LOẠI trả về) — xếp cụm dài trước, KHÔNG đổi thứ tự
_NEO_TEN = [
    (r"dau cap|dau noi cap|hop dau cap", "dau cap"),
    (r"may bien ap|bien ap|mba", "bien ap"),
    (r"bien dong|may bien dong", "bien dong ti"),
    (r"chi ong|cau chi|fco|lbfco", "chi ong"),
    (r"dao cach ly|cau dao", "ds"),
    (r"chong set|chong soc|lightning", "chong set cao the"),
    (r"cong to|dong ho dien", "cong to"),
    (r"khoi dong tu|contactor", "contactor"),
    (r"bien tan|inverter", "bien tan"),
    (r"cam bien|sensor", "cam bien"),
    (r"acquy|ac quy|binh dien", "acquy"),
    (r"\bacb\b", "acb"),
    (r"\bats\b", "ats"),
    (r"\bmccb\b|\bmcb\b|\bcb\b|aptomat", "cb"),
    (r"cap dien|day cap|\bcap\b|\bcvv\b|\bcxv\b", "cap"),
]


def tu_row(row: dict) -> dict:
    """Bóc (sku, loai, hang) từ một dòng MASTER -> đưa thẳng vào de_xuat().

    Không ném lỗi khi thiếu cột: thiếu tên thì loại rỗng, lúc đó việc so khớp
    rơi hết về hãng + tên file, vẫn ra kết quả chứ không chết.
    """
    row = row or {}
    ten = str(row.get("ten_goc") or row.get("ten") or "")
    sku = str(row.get("ma_goc") or row.get("sku") or row.get("ma") or "")
    hang = str(row.get("thuong_hieu") or row.get("hang") or "")
    return {"sku": sku, "loai": suy_loai_tu_ten(ten), "hang": hang}


def goc_kho() -> str:
    """Đường dẫn kho ảnh gốc, đọc từ cau-hinh.env (khoá KHO_ANH_NGUON).

    Chưa cấu hình thì trả chuỗi rỗng — nơi gọi tự bảo người dùng đi chọn,
    KHÔNG đoán bừa một thư mục nào đó rồi quét nhầm cả ổ đĩa.
    """
    return (os.environ.get("KHO_ANH_NGUON") or "").strip()


def token_sku(sku: str) -> list[str]:
    """Cắt SKU thành mảnh có ý nghĩa để dò trong tên file. Bỏ mảnh quá ngắn."""
    t = chuan_hoa(sku)
    return [x for x in t.split() if len(x) >= 3]


# ---------------------------------------------------------------- dữ liệu

@dataclass
class UngVien:
    duong_dan: str
    ten_file: str
    thu_muc: str
    rong: int = 0
    cao: int = 0
    dung_luong: int = 0
    diem: int = 0
    ly_do: list[str] = field(default_factory=list)
    da_dung: bool = False

    @property
    def kich_thuoc(self) -> str:
        return f"{self.rong}x{self.cao}" if self.rong else "?"


# ---------------------------------------------------------------- kho ảnh

class KhoAnh:
    """Index thư mục ảnh, tra cứu tức thời sau lần quét đầu."""

    PHIEN_BAN_INDEX = 2

    def __init__(self, goc: str, file_cache: str | None = None):
        self.goc = Path(goc)
        self.file_cache = Path(file_cache) if file_cache else self._cache_mac_dinh()
        self.index: dict[str, list[dict]] = {}   # key = tên folder đã chuẩn hóa
        self.thoi_diem_quet: float = 0.0

    def _cache_mac_dinh(self) -> Path:
        """Ghi vào %APPDATA%\\SONEALEO (chỗ chứa phase2-du-lieu.db), KHÔNG ghi cạnh
        thư mục ảnh — thư mục ảnh có thể nằm trên ổ mạng hoặc Drive read-only."""
        if sys.platform == "win32":
            goc_cache = Path(os.environ.get("APPDATA", Path.home())) / "SONEALEO"
        else:
            goc_cache = Path.home() / ".sonaleo"
        try:
            goc_cache.mkdir(parents=True, exist_ok=True)
        except OSError:
            goc_cache = Path.home()
        # mỗi thư mục gốc một cache riêng — md5 vì hash() đổi mỗi lần chạy process
        try:
            khoa = str(self.goc.resolve())
        except OSError:
            khoa = str(self.goc)
        dau = hashlib.md5(khoa.lower().encode("utf-8")).hexdigest()[:10]
        return goc_cache / f"index_anh_{dau}.json"

    # --- quét ---------------------------------------------------------

    def quet(self, doc_kich_thuoc: bool = True, in_tien_do: bool = True) -> int:
        """Đi hết cây thư mục, gom ảnh theo folder cha. Trả về số ảnh tìm được."""
        self.index = {}
        tong = 0
        for thu_muc, con, files in os.walk(self.goc):
            con[:] = [c for c in con if chuan_hoa(c) not in FOLDER_BO_QUA and not c.startswith(".")]
            anh = [f for f in files if Path(f).suffix.lower() in DUOI_ANH]
            if not anh:
                continue
            p = Path(thu_muc)
            khoa = chuan_hoa(p.name)
            muc = self.index.setdefault(khoa, [])
            for f in anh:
                dd = str(p / f)
                r = c_ = 0
                dl = 0
                try:
                    dl = os.path.getsize(dd)
                except OSError:
                    pass
                if doc_kich_thuoc and CO_PIL:
                    r, c_ = self._kich_thuoc(dd)
                muc.append({"dd": dd, "ten": f, "tm": p.name, "r": r, "c": c_, "dl": dl})
                tong += 1
            if in_tien_do and tong and tong % 500 == 0:
                print(f"  ... {tong} ảnh", flush=True)
        self.thoi_diem_quet = time.time()
        return tong

    @staticmethod
    def _kich_thuoc(duong_dan: str) -> tuple[int, int]:
        """Đọc header, không load pixel -> nhanh với thư mục lớn."""
        try:
            with Image.open(duong_dan) as im:
                return im.size
        except Exception:
            return (0, 0)

    # --- cache --------------------------------------------------------

    def luu_cache(self) -> None:
        """Ghi cache. Hỏng thì bỏ qua — mất cache chỉ tốn thêm 1 lần quét, không sập app."""
        goi = {
            "phien_ban": self.PHIEN_BAN_INDEX,
            "goc": str(self.goc),
            "thoi_diem": self.thoi_diem_quet,
            "index": self.index,
        }
        try:
            self.file_cache.parent.mkdir(parents=True, exist_ok=True)
            self.file_cache.write_text(json.dumps(goi, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def doc_cache(self) -> bool:
        if not self.file_cache.exists():
            return False
        try:
            goi = json.loads(self.file_cache.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False
        if goi.get("phien_ban") != self.PHIEN_BAN_INDEX or goi.get("goc") != str(self.goc):
            return False
        self.index = goi.get("index", {})
        self.thoi_diem_quet = goi.get("thoi_diem", 0.0)
        return bool(self.index)

    def nap_index(self, ep_quet_lai: bool = False) -> int:
        """Đọc cache nếu có, không thì quét. Gọi cái này lúc mở app."""
        if not ep_quet_lai and self.doc_cache():
            return sum(len(v) for v in self.index.values())
        n = self.quet()
        self.luu_cache()
        return n

    # --- tra cứu ------------------------------------------------------

    def de_xuat(
        self,
        sku: str,
        loai: str = "",
        hang: str = "",
        hash_da_dung: Iterable[str] = (),
        toi_thieu_px: int = 0,
        gioi_han: int = 40,
    ) -> list[UngVien]:
        """
        Trả về ứng viên đã xếp hạng. Điểm càng cao càng đáng xem.
          +100  tên file chứa nguyên SKU
          +90   tên file khớp mã SKU (dạng mã ngắn)
          +60   tên file chứa >=2 mảnh của SKU
          +30   tên file chứa 1 mảnh
          +40   folder khớp cả LOẠI và HÃNG
          +15   folder khớp LOẠI (folder không ghi hãng)
          +8/+4 ảnh lớn
          -25   ảnh đã dùng cho bài khác

        `hash_da_dung`: tập `hash_goc` lấy từ meta.json của workspace. Hash chỉ
        được tính cho các ứng viên LỌT TOP (mặc định 40 tấm), không tính cho cả
        kho — đọc 2,2 GB để tô một cái nhãn là không đáng.
        """
        hash_set = {x for x in hash_da_dung if x}
        sku_ch = chuan_hoa(sku)
        sku_lien = sku_ch.replace(" ", "")
        mang = token_sku(sku)

        loai_ch = ANH_XA_LOAI.get(chuan_hoa(loai), chuan_hoa(loai))
        hang_ch = ANH_XA_HANG.get(chuan_hoa(hang), chuan_hoa(hang))

        ket_qua: list[UngVien] = []
        for khoa, ds in self.index.items():
            f_loai, f_hang = tach_folder(khoa)

            diem_fol, ly_do_fol = 0, []
            if loai_ch and f_loai:
                khop_loai = loai_ch in f_loai or f_loai in loai_ch
            else:
                khop_loai = False

            if khop_loai and hang_ch and f_hang and (hang_ch in f_hang or f_hang in hang_ch):
                diem_fol, ly_do_fol = 40, ["folder khớp loại+hãng"]
            elif khop_loai and not f_hang:
                diem_fol, ly_do_fol = 15, ["folder khớp loại (chưa rõ hãng)"]
            elif khop_loai:
                diem_fol, ly_do_fol = 5, ["folder cùng loại, khác hãng"]
            elif hang_ch and f_hang and hang_ch in f_hang:
                diem_fol, ly_do_fol = 10, ["folder cùng hãng, khác loại"]

            for m in ds:
                if toi_thieu_px and m["r"] and m["r"] < toi_thieu_px:
                    continue

                ten_ch = chuan_hoa(Path(m["ten"]).stem)
                diem, ly_do = diem_fol, list(ly_do_fol)

                ten_lien = ten_ch.replace(" ", "")

                if sku_ch and sku_ch in ten_ch:
                    diem += 100
                    ly_do.append("tên file chứa SKU")
                elif sku_lien and len(sku_lien) >= 5 and sku_lien in ten_lien:
                    # bắt SKU dạng mã ngắn: '3M-92-EB-5-1' <-> '92-EB-5-1.jpg'
                    diem += 90
                    ly_do.append("tên file khớp mã SKU")
                elif sku_lien and len(sku_lien) >= 6 and ten_lien and ten_lien in sku_lien:
                    diem += 80
                    ly_do.append("mã SKU chứa tên file")
                else:
                    trung = [x for x in mang if x in ten_ch]
                    if len(trung) >= 2:
                        diem += 60
                        ly_do.append(f"tên file khớp {len(trung)} mảnh SKU")
                    elif trung:
                        diem += 30
                        ly_do.append("tên file khớp 1 mảnh SKU")

                if diem <= 0:
                    continue

                if m["r"] >= 1200:
                    diem += 8
                elif m["r"] >= 800:
                    diem += 4

                ket_qua.append(UngVien(
                    duong_dan=m["dd"], ten_file=m["ten"], thu_muc=m["tm"],
                    rong=m["r"], cao=m["c"], dung_luong=m["dl"],
                    diem=diem, ly_do=ly_do,
                ))

        ket_qua.sort(key=lambda x: (-x.diem, -x.rong, x.ten_file))
        ket_qua = ket_qua[:gioi_han]

        # Hash SAU khi cắt top: chỉ đọc <= gioi_han file thay vì cả kho.
        if hash_set:
            for uv in ket_qua:
                if hash_file(uv.duong_dan) in hash_set:
                    uv.da_dung = True
                    uv.diem -= 25
                    uv.ly_do.append("ĐÃ DÙNG cho bài khác")
            ket_qua.sort(key=lambda x: (-x.diem, -x.rong, x.ten_file))
        return ket_qua

    def thu_muc_goi_y(self, loai: str = "", hang: str = "") -> list[str]:
        """Khi không đề xuất được ảnh cụ thể: trả về folder đáng mở nhất."""
        loai_ch = ANH_XA_LOAI.get(chuan_hoa(loai), chuan_hoa(loai))
        hang_ch = ANH_XA_HANG.get(chuan_hoa(hang), chuan_hoa(hang))
        cham = []
        for khoa, ds in self.index.items():
            if not ds:
                continue
            f_loai, f_hang = tach_folder(khoa)
            d = 0
            if loai_ch and f_loai and (loai_ch in f_loai or f_loai in loai_ch):
                d += 10
                if hang_ch and f_hang and hang_ch in f_hang:
                    d += 10
                elif not f_hang:
                    d += 3
            elif hang_ch and f_hang and hang_ch in f_hang:
                d += 5
            if d:
                cham.append((d, str(Path(ds[0]["dd"]).parent)))
        cham.sort(reverse=True)
        return [tm for _, tm in cham]

    # --- mở Explorer --------------------------------------------------

    @staticmethod
    def mo_thu_muc(duong_dan: str) -> bool:
        """Bật Explorer. Trỏ vào file thì select sẵn file đó."""
        p = Path(duong_dan)
        if not p.exists():
            return False
        try:
            if sys.platform == "win32":
                if p.is_file():
                    subprocess.run(["explorer", "/select,", os.path.normpath(str(p))])
                else:
                    os.startfile(str(p))
            elif sys.platform == "darwin":
                subprocess.run(["open", "-R" if p.is_file() else "", str(p)])
            else:
                subprocess.run(["xdg-open", str(p if p.is_dir() else p.parent)])
            return True
        except Exception:
            return False


# ---------------------------------------------------------------- chạy thử

def _tu_kiem_tra() -> None:
    assert chuan_hoa("Máy Biến Áp  EMIC") == "may bien ap emic"
    assert chuan_hoa("Đầu cáp 3M") == "dau cap 3m"
    assert tach_folder("BIEN AP TU EMIC") == ("bien ap tu", "emic")
    assert tach_folder("DAU CAP 3M") == ("dau cap", "3m")
    assert tach_folder("Contactor Hyundai") == ("contactor", "hyundai")
    assert tach_folder("CHI ONG") == ("chi ong", "")
    assert tach_folder("CAP CADIVI") == ("cap", "cadivi")
    # "22" và "0.4" bị loại vì <3 ký tự -> mảnh ngắn match lung tung, gây nhiễu
    assert token_sku("EMIC-250-22/0.4") == ["emic", "250"]
    assert token_sku("3M-92-EB-5-1") == []          # SKU toàn mảnh ngắn -> chỉ dựa vào folder

    # suy loại: cụm dài phải thắng cụm ngắn
    assert suy_loai_tu_ten("Đầu cáp co nguội 3M 24kV") == "dau cap"
    assert suy_loai_tu_ten("Cáp ngầm CADIVI CXV 3x50") == "cap"
    assert suy_loai_tu_ten("Máy biến áp dầu EMIC 250kVA 22/0,4kV") == "bien ap"
    assert suy_loai_tu_ten("Máy biến dòng EMIC 100/5A") == "bien dong ti"
    assert suy_loai_tu_ten("Chì ống ABB 24kV") == "chi ong"
    assert suy_loai_tu_ten("") == ""

    # bóc từ dòng MASTER thật
    r = tu_row({"ten_goc": "Máy biến áp dầu 250kVA", "ma_goc": "MBA-250",
                "thuong_hieu": "EMIC"})
    assert r == {"sku": "MBA-250", "loai": "bien ap", "hang": "EMIC"}, r
    assert tu_row({})["loai"] == ""                 # thiếu cột -> không nổ

    print("✔ self-test qua hết")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _tu_kiem_tra()
        sys.exit(0)

    goc = sys.argv[1]
    sku = sys.argv[2] if len(sys.argv) > 2 else ""
    loai = sys.argv[3] if len(sys.argv) > 3 else ""
    hang = sys.argv[4] if len(sys.argv) > 4 else ""

    if not CO_PIL:
        print("! Chưa có Pillow -> không đọc được kích thước. pip install Pillow")

    kho = KhoAnh(goc)
    t0 = time.time()
    n = kho.nap_index()
    print(f"Index: {n} ảnh / {len(kho.index)} folder ({time.time()-t0:.1f}s)")

    if not sku:
        for k in sorted(kho.index)[:60]:
            l, h = tach_folder(k)
            print(f"  {k:<40} loại={l or '?':<20} hãng={h or '?'}")
        sys.exit(0)

    ds = kho.de_xuat(sku=sku, loai=loai, hang=hang)
    if not ds:
        print(f"\nKhông có ứng viên cho '{sku}'. Folder nên mở tay:")
        for tm in kho.thu_muc_goi_y(loai, hang)[:5]:
            print("  ", tm)
        sys.exit(0)

    print(f"\n{len(ds)} ứng viên cho '{sku}':\n")
    for uv in ds[:20]:
        co = " [ĐÃ DÙNG]" if uv.da_dung else ""
        print(f"  {uv.diem:>4}  {uv.kich_thuoc:>10}  {uv.thu_muc} / {uv.ten_file}{co}")
        print(f"        └ {', '.join(uv.ly_do)}")
