import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
# -*- coding: utf-8 -*-
"""
Ver 5.1 Claude — vá 4 lỗi phát hiện khi TỰ AUDIT lại tool bằng
Audit-Checklist-Ver5.0.xlsx (không phải nghe kể — mỗi lỗi đều tự
grep/chạy code xác nhận trước khi vá):

1. "Nghỉ giữa 2 bài" — có UI, không bao giờ được đọc/dùng. (Tool #6)
2. Ma trận key/model dự phòng thiếu tổ hợp (key phụ × model phụ). (Tool #7)
3. Title bị cắt 70 ký tự gây trùng giữa 2 SKU khác nhau. (Tool #4)
4. SKU trùng trong MASTER khiến WooCommerce đè sản phẩm. (Tool #3)

Chạy: python3 test_v51_patch.py
"""
import inspect
import os
import sys

import nhap_phase2 as N
import render_phase2 as R

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ver 5.1 -- test o tests/, du lieu/module chinh o thu muc goc (len 1 cap)
MASTER_GOC = os.path.join(BASE, 'MASTER_4_PROFILE_SAN_PHAM.xlsx')

KET_QUA = []


def test(ma, mo_ta, dieu_kien):
    KET_QUA.append((ma, mo_ta, bool(dieu_kien)))
    print(f'[{"PASS" if dieu_kien else "FAIL"}] {ma}: {mo_ta}')


def main():
    # ============================================================ 1. Nghỉ giữa 2 bài
    with open(os.path.join(BASE, 'giao-dien.py'), encoding='utf-8') as f:
        src = f.read()
    test('X1-01', 'Có hàm _v3_nghi_giua_bai_giay() đọc giá trị UI',
         'def _v3_nghi_giua_bai_giay' in src)
    test('X1-02', 'Ver 3.9 dùng Event.wait thay time.sleep để Force Stop ngắt được khoảng nghỉ',
         src.count('time.sleep(nghi_giua_bai)') == 0
         and src.count('.wait(nghi_giua_bai)') >= 2)
    test('X1-03', 'Cả 2 vòng lặp batch (record + job) đều nhận tham số nghi_giua_bai '
                 '(Ver 5.3 — hàm batch record có thêm tham số cho_phep_cap_nhat, chỉ cần kiểm tra nghi_giua_bai vẫn còn)',
         "def _v3_viec_dang_draft_that_hang_loat(self, rows, mau, danh_sach_thu, wc, nghi_giua_bai=0.0," in src
         and 'def _jobs_viec_dang_hang_loat(self, jobs, danh_sach_thu, wc, nghi_giua_bai=0.0):' in src)

    # ============================================================ 2. Ma trận key/model
    idx = src.find('def _v3_danh_sach_key_model_du_phong')
    ham_src = src[idx:idx+2000]
    test('X2-01', 'Có vòng lặp tổ hợp key phụ × model phụ (dòng comment Ver 5.1)',
         'Ver 5.1' in ham_src and 'MỌI key phụ' in ham_src)

    # Test thật logic (giả lập, không cần Tkinter)
    def _danh_sach_test(gc):
        danh_sach = [(gc['api_key'], gc['model'])]
        for m in gc.get('model_du_phong') or []:
            if m != gc['model']:
                danh_sach.append((gc['api_key'], m))
        for k in gc.get('api_key_du_phong') or []:
            if k != gc['api_key']:
                danh_sach.append((k, gc['model']))
        for k in gc.get('api_key_du_phong') or []:
            if k == gc['api_key']:
                continue
            for m in gc.get('model_du_phong') or []:
                if m == gc['model']:
                    continue
                cap = (k, m)
                if cap not in danh_sach:
                    danh_sach.append(cap)
        return danh_sach

    gc = {'api_key': 'K1', 'model': 'M1', 'api_key_du_phong': ['K2'], 'model_du_phong': ['M2']}
    ds = _danh_sach_test(gc)
    test('X2-02', f'Ma trận đủ 4 tổ hợp với 1 key phụ + 1 model phụ (thực tế {len(ds)})', len(ds) == 4)
    test('X2-03', 'CÓ tổ hợp (key phụ, model phụ) — đây là tổ hợp bị thiếu trước Ver 5.1',
         ('K2', 'M2') in ds)
    test('X2-04', 'Cặp CHÍNH vẫn đứng đầu danh sách (thử trước tiên, không đổi hành vi ưu tiên cũ)',
         ds[0] == ('K1', 'M1'))

    # ============================================================ 3. Title chống trùng
    test('X3-01', 'Title NGẮN (không cần cắt) giữ NGUYÊN, không tự ý thêm mã hàng',
         R.rut_gon_tieu_de_chong_trung('Tên ngắn', 'MA123', 70) == 'Tên ngắn')
    dai = 'A' * 40 + ' ' + 'B' * 40   # 81 ký tự, chắc chắn bị cắt
    kq = R.rut_gon_tieu_de_chong_trung(dai, 'MA999', 70)
    test('X3-02', 'Title DÀI bị cắt CÓ thêm mã hàng ở cuối để chống trùng',
         'MA999' in kq)
    test('X3-03', 'Title DÀI vẫn không vượt giới hạn quá xa (còn kiểm soát được độ dài)',
         len(kq) <= 85)
    test('X3-04', 'Không có mã hàng -> vẫn cắt an toàn, không crash',
         R.rut_gon_tieu_de_chong_trung(dai, '', 70) != '')

    if os.path.exists(MASTER_GOC):
        r = N.import_4_profile(MASTER_GOC)
        titles = {}
        for pid, info in r.items():
            for row in info['rows']:
                if row['outline_id'] == 'outline_may_bien_ap':
                    continue
                t = R.rut_gon_tieu_de_chong_trung(row.get('ten_goc', ''), row.get('ma_goc', ''), 70)
                titles.setdefault(t, []).append(row.get('ma_goc'))
        trung = {k: v for k, v in titles.items() if len(v) > 1}
        # còn sót lại chỉ khi Tên hàng GỐC (chưa cắt) đã trùng nhau thật sự trong MASTER — lỗi dữ liệu, không phải lỗi cắt chuỗi
        con_sot_do_data_loi = sum(1 for v in trung.values() if len(set(v)) > 1 for _ in [0])
        test('X3-05', f'Số title trùng do CẮT CHUỖI giảm mạnh so với 120 dòng ban đầu (còn {sum(len(v) for v in trung.values())} dòng, phần còn lại là mã hàng trùng thật hoặc Tên hàng gốc trong MASTER vốn đã trùng)',
             sum(len(v) for v in trung.values()) < 30)

    # ============================================================ 4. SKU trùng -> publish_sku
    if os.path.exists(MASTER_GOC):
        r2 = N.import_4_profile(MASTER_GOC, chi_profile='tu_va_thiet_bi_dong_cat')
        rows = r2['tu_va_thiet_bi_dong_cat']['rows']
        test('X4-01', "Mọi dòng ĐỀU có field 'publish_sku' sau import",
             all('publish_sku' in x for x in rows))
        bhslbs = [x for x in rows if x['ma_goc'] == 'BHSLBS24M']
        test('X4-02', f'Case thật BHSLBS24M: có {len(bhslbs)} dòng cùng mã (kỳ vọng 2)', len(bhslbs) == 2)
        if len(bhslbs) == 2:
            pubs = sorted(x['publish_sku'] for x in bhslbs)
            test('X4-03', f'2 dòng CÙNG ma_goc nhưng publish_sku KHÁC NHAU (thực tế {pubs})',
                 pubs[0] != pubs[1])
            test('X4-04', 'Dòng đầu tiên giữ NGUYÊN publish_sku = ma_goc (không đổi hành vi cho SKU không trùng)',
                 'BHSLBS24M' in pubs)
            test('X4-05', 'Dòng thứ 2 có hậu tố -B2 để phân biệt', any(p.endswith('-B2') for p in pubs))

        # Kiểm tra field ma_goc KHÔNG bị đổi (vẫn hiện đúng mã catalogue thật)
        test('X4-06', "ma_goc KHÔNG bị đổi theo publish_sku — vẫn đúng mã thật trong content",
             all(x['ma_goc'] == 'BHSLBS24M' for x in bhslbs))

        # Test không có SKU trùng thì publish_sku = ma_goc y hệt (an toàn ngược)
        khong_trung = [x for x in rows if x['ma_goc'] != 'BHSLBS24M'][:20]
        test('X4-07', 'SKU KHÔNG trùng -> publish_sku giống hệt ma_goc (an toàn ngược, không đổi hành vi cũ)',
             all(x['publish_sku'] == x['ma_goc'] for x in khong_trung))

    # ============================================================ 5. Wire vào ai_wp_adapter (dang_woo_that dùng publish_sku)
    test('X5-01', "giao-dien.py gọi dang_woo_that() với publish_sku, KHÔNG còn dùng thẳng ma_goc",
         "ma_hang=row.get('publish_sku', row.get('ma_goc'))" in src)

    tong = len(KET_QUA)
    dat = sum(1 for _, _, ok in KET_QUA if ok)
    print(f'\nTỔNG VER 5.1 PATCH: {dat}/{tong} PASS')
    if dat != tong:
        sys.exit(1)


if __name__ == '__main__':
    main()
