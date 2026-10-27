#!/usr/bin/env python3
"""
doc_schema.py — doc cau truc file MASTER Excel cua SONEALEO va in ra Markdown.

CHI DOC. Khong ghi de file MASTER trong moi truong hop.

Dung:
    python3 doc_schema.py <duong_dan_MASTER.xlsx>
    python3 doc_schema.py <duong_dan> --ra references/cot.md
    python3 doc_schema.py <duong_dan> --mau 8
"""

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("LOI: can pandas. Cai: pip install pandas openpyxl", file=sys.stderr)
    sys.exit(2)

SHEET_MONG_DOI = [
    "01_Cap_Dien",
    "02_Tu_Va_Thiet_Bi_Dong_Cat",
    "03_May_Bien_Ap_Do_Luong",
    "04_Phu_Kien_Va_Khac",
]

NGUONG_RONG = 0.90  # cot rong tren muc nay bi danh dau


def rut_gon(gia_tri, do_dai=40):
    s = str(gia_tri).replace("\n", " ").replace("|", "/").strip()
    return s[: do_dai - 1] + "…" if len(s) > do_dai else s


def mo_ta_cot(chuoi: "pd.Series", so_mau: int):
    tong = len(chuoi)
    so_trong = int(chuoi.isna().sum())
    ti_le_trong = so_trong / tong if tong else 0.0
    so_duy_nhat = int(chuoi.nunique(dropna=True))

    co_gia_tri = chuoi.dropna()
    mau = [rut_gon(v) for v in co_gia_tri.unique()[:so_mau]]

    return {
        "kieu": str(chuoi.dtype),
        "ti_le_trong": ti_le_trong,
        "so_duy_nhat": so_duy_nhat,
        "mau": mau,
        "canh_bao": ti_le_trong > NGUONG_RONG,
        "hang_so": so_duy_nhat == 1 and so_trong == 0,
    }


def xu_ly_sheet(ten: str, df: "pd.DataFrame", so_mau: int):
    dong = [f"\n## `{ten}`\n", f"- Số dòng: **{len(df):,}**", f"- Số cột: **{len(df.columns)}**\n"]
    dong.append("| # | Tên cột | Kiểu | % trống | Giá trị duy nhất | Mẫu |")
    dong.append("|---|---|---|---|---|---|")

    canh_bao = []
    for i, cot in enumerate(df.columns, 1):
        m = mo_ta_cot(df[cot], so_mau)
        co = ""
        if m["canh_bao"]:
            co = " ⚠️"
            canh_bao.append(f"`{cot}` trống {m['ti_le_trong']:.0%}")
        if m["hang_so"]:
            co += " 🔒"
            canh_bao.append(f"`{cot}` chỉ có 1 giá trị duy nhất")
        dong.append(
            f"| {i} | `{cot}`{co} | {m['kieu']} | {m['ti_le_trong']:.0%} | "
            f"{m['so_duy_nhat']:,} | {'; '.join(m['mau']) if m['mau'] else '—'} |"
        )

    if canh_bao:
        dong.append("\n**Cần chú ý:**\n")
        for c in canh_bao:
            dong.append(f"- {c}")

    return dong


def main():
    p = argparse.ArgumentParser(description="Doc schema MASTER Excel cua SONEALEO")
    p.add_argument("duong_dan", help="Duong dan toi file MASTER .xlsx")
    p.add_argument("--ra", default=None, help="Ghi ket qua Markdown ra file nay")
    p.add_argument("--mau", type=int, default=4, help="So gia tri mau moi cot (mac dinh 4)")
    args = p.parse_args()

    duong_dan = Path(args.duong_dan).expanduser().resolve()
    if not duong_dan.is_file():
        print(f"LOI: khong tim thay file: {duong_dan}", file=sys.stderr)
        return 2

    try:
        xl = pd.ExcelFile(duong_dan, engine="openpyxl")
    except Exception as e:
        print(f"LOI: khong mo duoc file: {e}", file=sys.stderr)
        return 2

    dong = [
        "# Cấu trúc MASTER",
        "",
        f"- File: `{duong_dan.name}`",
        f"- Số sheet: {len(xl.sheet_names)}",
        "",
        "> Sinh tự động bởi `doc_schema.py`. Chạy lại khi MASTER đổi cấu trúc.",
    ]

    thieu = [s for s in SHEET_MONG_DOI if s not in xl.sheet_names]
    thua = [s for s in xl.sheet_names if s not in SHEET_MONG_DOI]
    if thieu:
        dong.append(f"\n**⚠️ Thiếu sheet mong đợi:** {', '.join(f'`{s}`' for s in thieu)}")
    if thua:
        dong.append(f"\n**Sheet ngoài danh sách mong đợi:** {', '.join(f'`{s}`' for s in thua)}")

    tong_dong = 0
    for ten in xl.sheet_names:
        try:
            df = xl.parse(ten)
        except Exception as e:
            dong.append(f"\n## `{ten}`\n\n**LỖI đọc sheet:** {e}")
            continue
        tong_dong += len(df)
        dong.extend(xu_ly_sheet(ten, df, args.mau))

    dong.append(f"\n---\n\n**Tổng số dòng toàn file: {tong_dong:,}**")
    dong.append("\nChú thích: ⚠️ = cột trống >90% · 🔒 = cột chỉ có một giá trị duy nhất")

    ket_qua = "\n".join(dong)

    if args.ra:
        ra = Path(args.ra).expanduser().resolve()
        ra.parent.mkdir(parents=True, exist_ok=True)
        ra.write_text(ket_qua + "\n", encoding="utf-8")
        print(f"Da ghi: {ra}")
        print(f"Tong {tong_dong:,} dong tren {len(xl.sheet_names)} sheet.")
    else:
        print(ket_qua)

    return 0


if __name__ == "__main__":
    sys.exit(main())
