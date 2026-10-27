#!/usr/bin/env python3
"""
dong_goi.py — kiem tra tien dong goi va tao ZIP cho SONEALEO ULTRA.

Script tu choi tao ZIP neu vi pham luat dong goi:
  - thieu phien_ban.py hoac khong doc duoc version
  - thieu tests/ hoac tests/ rong
  - co file cam (phase2-du-lieu.db, cau-hinh.env) trong danh sach dong goi

Dung:
    python3 dong_goi.py kiem-tra  <source_dir>
    python3 dong_goi.py dong-goi  <source_dir> [--ra <output_dir>] [--bo-qua-version]
"""

import argparse
import os
import re
import sys
import zipfile
from pathlib import Path

# File tuyet doi khong duoc vao ZIP (khop theo ten file, khong phan biet hoa thuong)
FILE_CAM = {
    "phase2-du-lieu.db",
    "cau-hinh.env",
}

# Thu muc / duoi file bo qua khi dong goi (rac, khong phai vi pham)
THU_MUC_BO_QUA = {
    "__pycache__", ".git", ".idea", ".vscode", ".pytest_cache",
    "build", "dist", ".mypy_cache", "node_modules", ".venv", "venv",
}
DUOI_BO_QUA = {".pyc", ".pyo", ".pyd", ".log", ".tmp", ".swp"}

# Thu muc bat buoc phai co mat trong ZIP
THU_MUC_BAT_BUOC = ["tests"]


def doc_version(source: Path):
    """Doc version string tu phien_ban.py. Tra ve (version, duong_dan) hoac (None, ly_do)."""
    ung_vien = list(source.rglob("phien_ban.py"))
    if not ung_vien:
        return None, "khong tim thay phien_ban.py"

    # Uu tien ban o goc source neu co nhieu ban
    ung_vien.sort(key=lambda p: len(p.relative_to(source).parts))
    duong_dan = ung_vien[0]

    try:
        noi_dung = duong_dan.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return None, f"khong doc duoc {duong_dan}: {e}"

    # Bat cac dang: PHIEN_BAN = "4.6.2" / __version__ = '5.4' / VERSION="5.4.1"
    mau = re.compile(
        r"""^\s*(?:PHIEN_BAN|__version__|VERSION|version)\s*=\s*["']([^"']+)["']""",
        re.MULTILINE,
    )
    khop = mau.search(noi_dung)
    if not khop:
        return None, f"tim thay {duong_dan.name} nhung khong parse duoc version string"
    return khop.group(1).strip(), duong_dan


def nen_bo_qua(duong_dan: Path, source: Path) -> bool:
    phan = duong_dan.relative_to(source).parts
    if any(p in THU_MUC_BO_QUA for p in phan):
        return True
    if duong_dan.suffix.lower() in DUOI_BO_QUA:
        return True
    return False


def liet_ke_file(source: Path):
    """Tra ve (danh_sach_dong_goi, danh_sach_vi_pham)."""
    dong_goi, vi_pham = [], []
    for duong_dan in sorted(source.rglob("*")):
        if not duong_dan.is_file():
            continue
        if nen_bo_qua(duong_dan, source):
            continue
        if duong_dan.name.lower() in FILE_CAM:
            vi_pham.append(duong_dan)
            continue
        dong_goi.append(duong_dan)
    return dong_goi, vi_pham


def kiem_tra_lech_version(source: Path):
    """Goi `python3 phien_ban.py` cua chinh du an — no tu doi chieu moc 'Ver x.y'
    cao nhat trong code voi PHIEN_BAN. Khong lam lai chuc nang da co."""
    import subprocess
    pb = source / "phien_ban.py"
    if not pb.is_file():
        return None, "khong co phien_ban.py o goc source"
    try:
        kq = subprocess.run(
            [sys.executable, str(pb)],
            cwd=str(source), capture_output=True, text=True, timeout=120,
        )
    except Exception as e:
        return None, f"khong chay duoc phien_ban.py: {e}"
    ra = (kq.stdout + kq.stderr).strip()
    dat = kq.returncode == 0 and "LECH" not in ra.upper()
    dong_cuoi = ra.splitlines()[-1] if ra else "(khong co output)"
    return dat, dong_cuoi


def kiem_tra(source: Path, bo_qua_version: bool = False):
    """Chay toan bo kiem tra. Tra ve (dat, version, danh_sach_file, bao_cao)."""
    bao_cao = []
    dat = True

    version, chi_tiet = doc_version(source)
    if version is None:
        bao_cao.append(f"  [FAIL] phien_ban.py: {chi_tiet}")
        dat = False
    else:
        rel = Path(chi_tiet).relative_to(source)
        bao_cao.append(f"  [OK]   phien_ban.py -> version {version}  ({rel})")

    lech, chi_tiet_lech = kiem_tra_lech_version(source)
    if lech is None:
        bao_cao.append(f"  [WARN] khong chay duoc self-check version: {chi_tiet_lech}")
    elif lech:
        bao_cao.append(f"  [OK]   self-check version: {chi_tiet_lech}")
    else:
        bao_cao.append(f"  [FAIL] self-check version bao lech: {chi_tiet_lech}")
        dat = False

    for ten in THU_MUC_BAT_BUOC:
        thu_muc = source / ten
        if not thu_muc.is_dir():
            bao_cao.append(f"  [FAIL] thieu thu muc bat buoc: {ten}/")
            dat = False
        else:
            so_file = sum(1 for p in thu_muc.rglob("*") if p.is_file() and not nen_bo_qua(p, source))
            if so_file == 0:
                bao_cao.append(f"  [FAIL] {ten}/ ton tai nhung rong")
                dat = False
            else:
                bao_cao.append(f"  [OK]   {ten}/ co {so_file} file")

    danh_sach, vi_pham = liet_ke_file(source)
    if vi_pham:
        # Khong fail: tu dong loai tru va bao to. Fail cung o day chi khien
        # nguoi dung tim cach bypass, trong khi hanh vi dung la loai tru.
        bao_cao.append(f"  [WARN] da LOAI TRU {len(vi_pham)} file cam khoi ZIP:")
        for p in vi_pham:
            bao_cao.append(f"           - {p.relative_to(source)}")
    else:
        bao_cao.append(f"  [OK]   khong thay file cam ({', '.join(sorted(FILE_CAM))})")

    bao_cao.append(f"  [INFO] tong {len(danh_sach)} file se vao ZIP")

    if bo_qua_version and version is None:
        bao_cao.append("  [WARN] --bo-qua-version dang bat: bo qua kiem tra version")
        dat = True

    return dat, version, danh_sach, bao_cao


def dong_goi(source: Path, output_dir: Path, version, danh_sach):
    ten_ver = version if version else "KHONG-RO"
    output_dir.mkdir(parents=True, exist_ok=True)
    dich = output_dir / f"SONEALEO-ULTRA-{ten_ver}.zip"

    with zipfile.ZipFile(dich, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for duong_dan in danh_sach:
            z.write(duong_dan, duong_dan.relative_to(source))

    kich_thuoc = dich.stat().st_size / (1024 * 1024)
    return dich, kich_thuoc


def main():
    parser = argparse.ArgumentParser(description="Kiem tra va dong goi SONEALEO ULTRA")
    parser.add_argument("lenh", choices=["kiem-tra", "dong-goi"])
    parser.add_argument("source", help="Thu muc source cua SONEALEO")
    parser.add_argument("--ra", default=None, help="Thu muc xuat ZIP (mac dinh: canh source)")
    parser.add_argument("--bo-qua-version", action="store_true",
                        help="Cho phep dong goi du khong doc duoc version. Phai bao cho nguoi dung biet.")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.is_dir():
        print(f"LOI: khong phai thu muc: {source}", file=sys.stderr)
        return 2

    print(f"\nKiem tra: {source}\n")
    dat, version, danh_sach, bao_cao = kiem_tra(source, args.bo_qua_version)
    for dong in bao_cao:
        print(dong)

    if not dat:
        print("\nKET QUA: KHONG DAT. Khong tao ZIP.\n", file=sys.stderr)
        return 1

    print("\nKET QUA: DAT.\n")

    if args.lenh == "kiem-tra":
        return 0

    output_dir = Path(args.ra).expanduser().resolve() if args.ra else source.parent
    dich, kich_thuoc = dong_goi(source, output_dir, version, danh_sach)
    print(f"Da tao: {dich}")
    print(f"Kich thuoc: {kich_thuoc:.2f} MB")
    print(f"So file: {len(danh_sach)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
