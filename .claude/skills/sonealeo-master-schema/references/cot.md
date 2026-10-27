# Cấu trúc MASTER — bản đồ cột

> **Nguồn: `profiles.py`, dict `PROFILES`.** Trích tự động từ code, không phải từ file Excel.
> Mức tin cậy: **xác nhận từ code**. Đây là cột tool *chấp nhận*, không đảm bảo
> file MASTER hiện tại có đủ. Muốn biết file thật có gì, chạy `scripts/doc_schema.py`.

Cột không khai trong `cot_import` thì **không có đường vào hệ thống**, dù Excel có cột đó.


## `01_Cap_Dien` — profile `cap_dien`

- Nhãn: Cáp điện
- Số cột nhận: **27**
- Outline mặc định: `outline_cap_dien`
- content_type: `product`

| Cột Excel | Field nội bộ | Bắt buộc | Đưa cho AI | Chỉ nội bộ |
|---|---|:-:|:-:|:-:|
| `Mã hàng` | `ma_goc` | ✓ |  |  |
| `Tên hàng` | `ten_goc` | ✓ | ✓ |  |
| `Nhãn Hiệu / Xuất Xứ` | `thuong_hieu` | ✓ | ✓ |  |
| `Quy Cách / Áp Lực` | `quy_cach` | ✓ | ✓ |  |
| `ĐVT` | `dvt` | ✓ | ✓ |  |
| `Giá List (VNĐ)` | `gia_list` | ✓ |  | ✓ |
| `Ghi Chú Ban Đầu` | `ghi_chu_ban_dau` | ✓ |  | ✓ |
| `Nhóm Nguồn` | `nhom_nguon` | ✓ |  | ✓ |
| `Tiết Diện (mm²)` | `tiet_dien` | ✓ | ✓ |  |
| `Cấp Điện Áp` | `cap_dien_ap` | ✓ | ✓ |  |
| `Vật Liệu Ruột` | `vat_lieu_ruot` | ✓ | ✓ |  |
| `Catalogue PDF URL` | `catalogue_pdf_url` |  |  |  |
| `Vật liệu ruột (giải mã)` | `vat_lieu_ruot_giai_ma` |  | ✓ |  |
| `Loại cách điện (giải mã)` | `loai_cach_dien_giai_ma` |  | ✓ |  |
| `Vỏ bọc (giải mã)` | `vo_boc_giai_ma` |  | ✓ |  |
| `Giáp bảo vệ (giải mã)` | `giap_bao_ve_giai_ma` |  | ✓ |  |
| `Đặc điểm khác (giải mã)` | `dac_diem_khac_giai_ma` |  | ✓ |  |
| `Độ tin cậy giải mã` | `do_tin_cay_giai_ma` |  |  | ✓ |
| `Nguồn giải mã` | `nguon_giai_ma` |  |  | ✓ |
| `Dong dien dinh muc (A) [catalogue]` | `dong_dien_dinh_muc_catalogue` |  | ✓ |  |
| `Kieu lap dat cua dong dinh muc [catalogue]` | `kieu_lap_dat_catalogue` |  | ✓ |  |
| `Do sut ap (mV/A/m) [catalogue]` | `do_sut_ap_catalogue` |  | ✓ |  |
| `Dieu kien quy chieu dong tai [catalogue]` | `dieu_kien_quy_chieu_catalogue` |  |  |  |
| `Dien tro DC toi da 20C (Ohm/km) [catalogue]` | `dien_tro_dc_catalogue` |  | ✓ |  |
| `Duong kinh ruot dan (mm) [catalogue]` | `duong_kinh_ruot_dan_catalogue` |  |  |  |
| `Nhom ruot dan [catalogue]` | `nhom_ruot_dan_catalogue` |  |  |  |
| `Nguon du lieu catalogue` | `nguon_du_lieu_catalogue` |  |  |  |

## `02_Tu_Va_Thiet_Bi_Dong_Cat` — profile `tu_va_thiet_bi_dong_cat`

- Nhãn: Tủ và thiết bị đóng cắt
- Số cột nhận: **9**
- Outline mặc định: `outline_tu_dong_cat`
- content_type: `product`

| Cột Excel | Field nội bộ | Bắt buộc | Đưa cho AI | Chỉ nội bộ |
|---|---|:-:|:-:|:-:|
| `Mã hàng` | `ma_goc` | ✓ |  |  |
| `Tên hàng` | `ten_goc` | ✓ | ✓ |  |
| `Nhãn Hiệu / Xuất Xứ` | `thuong_hieu` | ✓ | ✓ |  |
| `Quy Cách / Áp Lực` | `quy_cach` | ✓ | ✓ |  |
| `ĐVT` | `dvt` | ✓ | ✓ |  |
| `Giá List (VNĐ)` | `gia_list` | ✓ |  | ✓ |
| `Ghi Chú Ban Đầu` | `ghi_chu_ban_dau` | ✓ |  | ✓ |
| `Nhóm Nguồn` | `nhom_nguon` | ✓ |  | ✓ |
| `Catalogue PDF URL` | `catalogue_pdf_url` |  |  |  |

## `03_May_Bien_Ap_Do_Luong` — profile `may_bien_ap_do_luong`

- Nhãn: Máy biến áp & đo lường
- Số cột nhận: **31**
- Outline mặc định: `—`
- content_type: `product`

| Cột Excel | Field nội bộ | Bắt buộc | Đưa cho AI | Chỉ nội bộ |
|---|---|:-:|:-:|:-:|
| `Mã hàng` | `ma_goc` | ✓ |  |  |
| `Tên hàng` | `ten_goc` | ✓ | ✓ |  |
| `Nhãn Hiệu / Xuất Xứ` | `thuong_hieu` | ✓ | ✓ |  |
| `Quy Cách / Áp Lực` | `quy_cach` | ✓ | ✓ |  |
| `ĐVT` | `dvt` | ✓ | ✓ |  |
| `Giá List (VNĐ)` | `gia_list` | ✓ |  | ✓ |
| `Ghi Chú Ban Đầu` | `ghi_chu_ban_dau` | ✓ |  | ✓ |
| `Nhóm Nguồn` | `nhom_nguon` | ✓ |  | ✓ |
| `Công Suất (kVA)` | `cong_suat` | ✓ | ✓ |  |
| `Cấp Điện Áp (kV)` | `cap_dien_ap` | ✓ | ✓ |  |
| `Catalogue PDF URL` | `catalogue_pdf_url` |  |  |  |
| `Tổ đấu dây (catalogue)` | `to_dau_day` |  | ✓ |  |
| `Tổn hao không tải Po (W, catalogue)` | `ton_hao_khong_tai` |  | ✓ |  |
| `Tổn hao ngắn mạch Pk (W, catalogue)` | `ton_hao_ngan_mach` |  | ✓ |  |
| `Dòng điện không tải Io (%, catalogue)` | `dong_khong_tai` |  | ✓ |  |
| `Điện áp ngắn mạch Uk (%, catalogue)` | `dien_ap_ngan_mach` |  | ✓ |  |
| `Hiệu suất năng lượng tối thiểu E50 (catalogue)` | `hieu_suat_e50` |  | ✓ |  |
| `Kích thước A (mm, catalogue)` | `kich_thuoc_a` |  | ✓ |  |
| `Kích thước B (mm, catalogue)` | `kich_thuoc_b` |  | ✓ |  |
| `Kích thước C (mm, catalogue)` | `kich_thuoc_c` |  | ✓ |  |
| `Kích thước D (mm, catalogue)` | `kich_thuoc_d` |  | ✓ |  |
| `Khối lượng dầu (kg, catalogue)` | `khoi_luong_dau` |  | ✓ |  |
| `Tổng khối lượng (kg, catalogue)` | `tong_khoi_luong` |  | ✓ |  |
| `Bảo hành (tháng)` | `bao_hanh_thang` |  |  |  |
| `Chứng nhận (CO/CQ/Quatest)` | `chung_nhan` |  |  |  |
| `Nguồn - Loại số liệu Po/Pk/Uk` | `nguon_loai_so_lieu` |  |  |  |
| `Nguồn - Ký hiệu hiển thị Po/Pk` | `nguon_ky_hieu` |  |  |  |
| `Nguồn - Tiêu chuẩn viện dẫn` | `nguon_tieu_chuan_vien_dan` |  |  |  |
| `Ghi chú - Cần kiểm lại` | `ghi_chu_can_kiem` |  |  |  |
| `Hậu tố slug` | `hau_to_slug` |  |  |  |
| `Slug chỉ định` | `slug_chi_dinh` |  |  |  |

## `04_Phu_Kien_Va_Khac` — profile `phu_kien_va_khac`

- Nhãn: Phụ kiện và khác
- Số cột nhận: **16**
- Outline mặc định: `outline_phu_kien`
- content_type: `—`

| Cột Excel | Field nội bộ | Bắt buộc | Đưa cho AI | Chỉ nội bộ |
|---|---|:-:|:-:|:-:|
| `Mã hàng` | `ma_goc` | ✓ |  |  |
| `Tên hàng` | `ten_goc` | ✓ | ✓ |  |
| `Nhãn Hiệu / Xuất Xứ` | `thuong_hieu` | ✓ | ✓ |  |
| `Quy Cách / Áp Lực` | `quy_cach` | ✓ | ✓ |  |
| `ĐVT` | `dvt` | ✓ | ✓ |  |
| `Giá List (VNĐ)` | `gia_list` | ✓ |  | ✓ |
| `Ghi Chú Ban Đầu` | `ghi_chu_ban_dau` | ✓ |  | ✓ |
| `Nhóm Nguồn` | `nhom_nguon` | ✓ |  | ✓ |
| `Đường kính cách điện áp dụng (mm)` | `duong_kinh_cach_dien` |  | ✓ |  |
| `Kích thước lắp đặt I (mm)` | `kich_thuoc_i` |  | ✓ |  |
| `Chiều dài lắp đặt L (mm)` | `kich_thuoc_l` |  | ✓ |  |
| `Chiều dài đường rò - ngoài trời (mm)` | `duong_ro_ngoai_troi` |  | ✓ |  |
| `Tiêu chuẩn (catalogue)` | `tieu_chuan_catalogue` |  | ✓ |  |
| `Test điện (catalogue)` | `test_dien` |  | ✓ |  |
| `Nguồn catalogue` | `nguon_catalogue` |  |  | ✓ |
| `Catalogue PDF URL` | `catalogue_pdf_url` |  |  |  |
