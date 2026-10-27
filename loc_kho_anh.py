# -*- coding: utf-8 -*-
"""SONEALEO 4.0 — lọc kho ảnh tầng 1, không AI, không xoá file gốc."""
from tkinter import Tk, filedialog, messagebox
import xu_ly_anh as X


def main():
    root = Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title='Chọn KHO ẢNH cần lọc (tool không xoá file gốc)')
    if not folder:
        root.destroy()
        return
    try:
        kq = X.loc_kho_anh(folder)
        loai = kq['loai']
        messagebox.showinfo(
            'Lọc kho ảnh — hoàn tất',
            f"Tổng file: {kq['tong_file']}\n"
            f"Ảnh hợp lệ đầu vào: {kq['anh_hop_le_dau_vao']}\n"
            f"Giữ lại: {kq['giu_lai']}\n\n"
            f"Loại trùng byte: {loai['trung_byte']}\n"
            f"Loại ảnh nhỏ: {loai['anh_nho']}\n"
            f"Loại ảnh mờ: {loai['anh_mo']}\n"
            f"Không phải ảnh: {loai['khong_phai_anh']}\n\n"
            f"Ngưỡng mờ Laplacian variance: {kq['nguong_mo_laplacian_variance']}\n"
            f"Kết quả: {kq['dich']}\nBáo cáo: {kq['bao_cao']}")
    except Exception as e:
        messagebox.showerror('Lọc kho ảnh', f'{type(e).__name__}: {e}')
    finally:
        root.destroy()


if __name__ == '__main__':
    main()
