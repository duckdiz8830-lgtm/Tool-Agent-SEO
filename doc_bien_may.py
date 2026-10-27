# -*- coding: utf-8 -*-
"""
SONEALEO ULTRA 3.0 — ĐỌC BIỂN MÁY: quét thư mục ảnh, tự nhận diện ảnh
biển máy (nameplate), đọc thông số trên biển thành file Excel để NGƯỜI
SOÁT trước khi ghép vào master.

VÌ SAO
12 catalogue PDF 200MB chỉ moi được 15/245 SKU. Trong khi Drive có sẵn
ảnh chụp BIỂN MÁY của máy thật đã bán — trên đó in đúng Po, Pk, Uk%,
tổ đấu dây, khối lượng... Đây là nguồn số chuẩn nhất có thể có.

VAI NGƯỜI - VAI MÁY (người dùng KHÔNG cần biết ngành điện):
  Máy: tìm ảnh biển máy trong đống ảnh, đọc số, xuất Excel kèm nguồn.
  Người: mở Excel kết quả, liếc cột 'Cần kiểm' — dòng nào bị đánh dấu
  thì mở ảnh gốc (đường dẫn ghi sẵn) so 2 con số bằng mắt.

KỶ LUẬT SỐ LIỆU
  - Prompt ép AI CHỈ CHÉP số đọc được trên ảnh, không thấy -> null.
  - Số kVA đọc từ biển KHÁC số kVA của thư mục chứa ảnh -> đánh dấu
    'Cần kiểm', không tin bên nào.
  - File này KHÔNG tự ghi vào master — ghép là bước riêng có đối chiếu
    (ghep_vao_master.py).

CÁCH DÙNG
    python doc_bien_may.py "duong/dan/thu/muc/anh" [gioi_han_anh]
    (mặc định tối đa 150 ảnh/lần chạy để giữ quota; chạy lại sẽ đọc
    tiếp phần chưa làm nhờ cache)
"""
import json
import os
import sys

import vision_chung as V
import anh_san_pham as A

DUOI_ANH = ('.jpg', '.jpeg', '.png', '.webp')

PROMPT_PHAN_LOAI = (
    'Ảnh này có phải ảnh chụp BIỂN THÔNG SỐ (nameplate) gắn trên thân máy '
    'biến áp không? Biển là tấm kim loại/decal in bảng chữ và số kỹ thuật. '
    'Ảnh chụp nguyên cả máy, máy trên xe tải, nhà xưởng, người... KHÔNG phải. '
    'Trả JSON đúng dạng: {"la_bien_may": true/false}'
)

PROMPT_DOC_BIEN = (
    'Đây là ảnh biển thông số máy biến áp. CHỈ CHÉP LẠI giá trị ĐỌC RÕ '
    'được trên biển. Không đọc rõ hoặc không có -> null. TUYỆT ĐỐI không '
    'suy đoán, không tính toán, không lấy kiến thức ngoài ảnh.\n'
    'Trả JSON đúng các khoá sau:\n'
    '{"thuong_hieu": "...", "loai_may": "dau|kho|null", "so_pha": 1|3|null,'
    ' "cong_suat_kva": số|null, "dien_ap": "vd 22/0.4 kV"|null,'
    ' "to_dau_day": "vd Dyn11"|null, "po_w": số|null, "pk_w": số|null,'
    ' "uk_pct": số|null, "io_pct": số|null, "khoi_luong_dau_kg": số|null,'
    ' "tong_khoi_luong_kg": số|null, "kich_thuoc_mm": "DxRxC"|null,'
    ' "tieu_chuan": "..."|null, "nam_sx": số|null,'
    ' "do_ro": "cao|vua|thap" (ảnh nét, đọc chắc -> cao; mờ/nghiêng -> thap)}'
)

COT_XUAT = [
    ('anh', 'Ảnh nguồn'), ('thuong_hieu', 'Hãng (đọc từ biển)'),
    ('loai_may', 'Dầu/Khô'), ('so_pha', 'Số pha'),
    ('cong_suat_kva', 'Công suất (kVA)'), ('dien_ap', 'Điện áp'),
    ('to_dau_day', 'Tổ đấu dây'), ('po_w', 'Tổn hao không tải Po (W)'),
    ('pk_w', 'Tổn hao ngắn mạch Pk (W)'), ('uk_pct', 'Điện áp ngắn mạch Uk (%)'),
    ('io_pct', 'Dòng không tải Io (%)'), ('khoi_luong_dau_kg', 'Khối lượng dầu (kg)'),
    ('tong_khoi_luong_kg', 'Tổng khối lượng (kg)'), ('kich_thuoc_mm', 'Kích thước (mm)'),
    ('tieu_chuan', 'Tiêu chuẩn'), ('nam_sx', 'Năm SX'),
    ('do_ro', 'Độ rõ ảnh'), ('can_kiem', 'Cần kiểm'), ('ly_do_kiem', 'Lý do'),
]



def doc_mot_anh(duong_dan, goc=None, goi_vision=None, ch=None, dem=None):
    """Ver 3.1 — xử lý ĐÚNG 1 ảnh (tách từ quet_va_doc để GUI gọi lẻ).

    Trả dict kết quả (như 1 phần tử của quet_va_doc) hoặc None (không
    phải biển máy / lỗi / chưa gọi được AI). `dem` là dict thống kê dùng
    chung, truyền vào để cộng dồn."""
    goi = goi_vision or V.goi_vision
    ch = ch or V.doc_cau_hinh()
    dem = dem if dem is not None else {'goi_ai': 0, 'bien_may': 0,
                                       'bo_cache': 0, 'loi': 0}
    _k_pl = ch['model'] + PROMPT_PHAN_LOAI
    _k_doc = ch['model'] + PROMPT_DOC_BIEN
    pd = A.phan_tich_duong_dan(duong_dan, goc or os.path.dirname(duong_dan))

    pl = V.doc_cache(duong_dan, 'phanloai', them=_k_pl)
    if pl is None and pd['la_bien_may']:
        pl = {'la_bien_may': True}
    if pl is None:
        nho, mime = V.thu_nho_anh(duong_dan, rong_toi_da=512, chat_luong=60)
        kq = goi(nho, mime, PROMPT_PHAN_LOAI, cau_hinh=ch, max_tokens=1200)
        dem['goi_ai'] += 1
        if not kq['ok']:
            dem['loi'] += 1
            print(f'  [phân loại LỖI] {os.path.basename(duong_dan)}: {kq["loi"]}')
            return None
        pl = kq['json']
        V.ghi_cache(duong_dan, 'phanloai', pl, them=_k_pl)
    else:
        dem['bo_cache'] += 1
    if not pl.get('la_bien_may'):
        return None
    dem['bien_may'] += 1

    ds = V.doc_cache(duong_dan, 'docbien', them=_k_doc)
    if ds is None:
        nho, mime = V.thu_nho_anh(duong_dan, rong_toi_da=1400, chat_luong=85)
        kq = goi(nho, mime, PROMPT_DOC_BIEN, cau_hinh=ch, max_tokens=2500)
        dem['goi_ai'] += 1
        if not kq['ok']:
            dem['loi'] += 1
            print(f'  [đọc biển LỖI] {os.path.basename(duong_dan)}: {kq["loi"]}')
            return None
        ds = kq['json']
        V.ghi_cache(duong_dan, 'docbien', ds, them=_k_doc)

    can_kiem, ly_do = '', []
    kva_bien = ds.get('cong_suat_kva')
    if kva_bien and pd['cong_suat'] and float(kva_bien) != float(pd['cong_suat']):
        can_kiem = 'X'
        ly_do.append(f"biển ghi {kva_bien}kVA nhưng nằm trong thư mục {pd['cong_suat']:g}")
    th_bien = (ds.get('thuong_hieu') or '').lower()
    if th_bien and pd['thuong_hieu'] and pd['thuong_hieu'].lower() not in th_bien \
            and th_bien not in pd['thuong_hieu'].lower():
        can_kiem = 'X'
        ly_do.append(f"biển ghi hãng {ds['thuong_hieu']} nhưng thư mục là {pd['thuong_hieu']}")
    if ds.get('do_ro') == 'thap':
        can_kiem = 'X'
        ly_do.append('ảnh mờ — AI tự báo đọc không chắc')

    dong = {k: ds.get(k) for k, _n in COT_XUAT if k in ds}
    dong.update({'anh': os.path.relpath(duong_dan, goc) if goc else duong_dan,
                 'can_kiem': can_kiem, 'ly_do_kiem': '; '.join(ly_do)})
    print(f'  [OK] {os.path.basename(duong_dan)} -> {ds.get("thuong_hieu")} {kva_bien}kVA'
          f'{" (CẦN KIỂM)" if can_kiem else ""}')
    return dong


def quet_va_doc(goc, gioi_han=150, goi_vision=None):
    """Trả (danh_sach_ket_qua, thong_ke). goi_vision tiêm mock khi test.

    Ver 3.1 — thân vòng lặp tách ra doc_mot_anh() để GUI gọi lẻ từng
    file; hành vi và giới hạn lượt giữ nguyên như 3.0."""
    goi = goi_vision or V.goi_vision
    ch = V.doc_cau_hinh()
    ket_qua = []
    dem = {'anh': 0, 'goi_ai': 0, 'bien_may': 0, 'bo_cache': 0, 'loi': 0}
    for thu_muc, _d, files in os.walk(goc):
        for f in sorted(files):
            if not f.lower().endswith(DUOI_ANH):
                continue
            dem['anh'] += 1
            if dem['goi_ai'] >= gioi_han:
                continue
            dong = doc_mot_anh(os.path.join(thu_muc, f), goc=goc,
                               goi_vision=goi, ch=ch, dem=dem)
            if dong:
                ket_qua.append(dong)
    return ket_qua, dem


def xuat_excel(ket_qua, duong_dan_ra='bien-may-ket-qua.xlsx'):
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'BienMay'
    ws.append([nhan for _k, nhan in COT_XUAT])
    for c in ws[1]:
        c.font = Font(bold=True)
    do = PatternFill('solid', fgColor='FFF2CC')
    for d in ket_qua:
        ws.append([d.get(k, '') for k, _n in COT_XUAT])
        if d.get('can_kiem'):
            for c in ws[ws.max_row]:
                c.fill = do
    wb.save(duong_dan_ra)
    return duong_dan_ra


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Cách dùng: python doc_bien_may.py <thư mục ảnh> [giới hạn ảnh gọi AI]')
        sys.exit(1)
    goc = sys.argv[1]
    gioi_han = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    kq, dem = quet_va_doc(goc, gioi_han)
    ra = xuat_excel(kq) if kq else None
    print(f"\nẢnh đã quét: {dem['anh']} | lượt gọi AI: {dem['goi_ai']} "
          f"(cache đỡ {dem['bo_cache']}) | biển máy: {dem['bien_may']} | lỗi: {dem['loi']}")
    if ra:
        print(f'Kết quả: {ra} — MỞ FILE, soát các dòng tô vàng (cột "Cần kiểm") trước khi ghép.')
    else:
        print('Chưa đọc được biển máy nào (hết giới hạn lượt hoặc không có ảnh biển).')
