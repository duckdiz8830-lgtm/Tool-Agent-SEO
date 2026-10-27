import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
# -*- coding: utf-8 -*-
"""
Data Core regression test — CHỈ phần KHÔNG đổi giữa Round 1 và Round 2:
Profile/Outline Registry (normalize_cell, effective_cot_ai/bang) và
validator/regex (Bước 1 + Bước 3 của kiến trúc gốc). Phần DB (Bước 2) và
render/prompt (Bước 4) đã đổi thiết kế ở Round 2 (schema đa site/đa mẫu,
prompt Phase 2 thật) — xem test_round2_integration.py cho phần đó.

Lý do giữ file riêng: đúng nguyên tắc "không làm lại phần đã PASS nếu không
có test chứng minh lỗi" — Registry và regex không có lỗi nào bị phát hiện ở
Round 2, nên giữ nguyên logic, chỉ bỏ phần test DB cũ (kho_phase2.py đã xoá,
thay bằng db_phase2.py).

Chạy: python3 test_phase2_full.py
"""
import profiles as P
import nhap_phase2 as N
import validators as V

MASTER = 'du_lieu_goc/MASTER_4_PROFILE_SAN_PHAM.xlsx'
KY_VONG_SO_LUONG = {
    'cap_dien': 3387, 'tu_va_thiet_bi_dong_cat': 300,
    'may_bien_ap_do_luong': 245, 'phu_kien_va_khac': 1332,
}

KET_QUA = []


def test(so_thu_tu, mo_ta, dieu_kien, ghi_chu=''):
    ok = bool(dieu_kien)
    KET_QUA.append((so_thu_tu, mo_ta, ok, ghi_chu))
    print(f'[{"PASS" if ok else "FAIL"}] Test {so_thu_tu}: {mo_ta}'
          + (f'  ({ghi_chu})' if ghi_chu else ''))
    return ok


def main():
    print('=' * 70)
    print('BƯỚC 1 — normalize_cell + Profile/Outline Registry')
    print('=' * 70)

    test(1, 'normalize_cell() xử lý đúng NaN/số/text từ dữ liệu pandas thật',
         P.normalize_cell(float('nan')) == '' and P.normalize_cell(None) == '' and
         P.normalize_cell(15.0) == '15' and P.normalize_cell(37.5) == '37.5' and
         P.normalize_cell('  Cadivi  ') == 'Cadivi')

    vi_pham = []
    for pid, cfg in P.PROFILES.items():
        cot_ai, cot_bang = set(cfg.get('cot_ai', [])), {k for k, _ in cfg.get('cot_bang', [])}
        if (cot_ai | cot_bang) & P.FIELD_CAM_TUYET_DOI:
            vi_pham.append(pid)
    for oid, cfg in P.OUTLINES.items():
        cot_ai, cot_bang = set(cfg.get('cot_ai', [])), set(cfg.get('cot_bang', []))
        if (cot_ai | cot_bang) & P.FIELD_CAM_TUYET_DOI:
            vi_pham.append(oid)
    test(2, 'gia_list/ghi_chu_ban_dau không có trong cot_ai/cot_bang của mọi profile/outline',
         len(vi_pham) == 0, f'vi phạm: {vi_pham}' if vi_pham else '')

    eff = {k for k, _ in P.effective_cot_bang('cap_dien', 'outline_phu_kien')}
    test(3, 'effective_cot_bang(cap_dien, outline_phu_kien) KHÔNG chứa field ngữ nghĩa cáp',
         not ({'vat_lieu_ruot', 'tiet_dien', 'cap_dien_ap'} & eff))

    test(3, 'outline_service đã tách riêng khỏi outline_phu_kien (Round 2, R2-05)',
         'outline_service' in P.OUTLINES)

    print()
    print('=' * 70)
    print('BƯỚC 3 — validator, regex, routing outline (không đổi so với Round 1)')
    print('=' * 70)

    r_master = N.import_4_profile(MASTER)
    tong = sum(len(r_master[pid]['rows']) for pid in r_master)
    test(4, f'Import số lượng đúng 3.387/300/245/1.332/tổng 5.264 (thực tế {tong})',
         all(len(r_master[pid]['rows']) == n for pid, n in KY_VONG_SO_LUONG.items()) and tong == 5264)

    for pid in r_master:
        r_master[pid]['rows'] = V.validate_rows(r_master[pid]['rows'])

    cd = r_master['cap_dien']['rows']
    mba = r_master['may_bien_ap_do_luong']['rows']
    test(10, f'Regex tiết diện đơn lõi tự bóc đúng 801 dòng cáp thật '
             f'(thực tế {sum(1 for x in cd if x.get("tiet_dien_tu_dong_boc"))})',
         sum(1 for x in cd if x.get('tiet_dien_tu_dong_boc')) == 801)
    test(10, f'Regex điện áp "V" thường tự bóc đúng 291 dòng cáp thật '
             f'(thực tế {sum(1 for x in cd if x.get("cap_dien_ap_tu_dong_boc"))})',
         sum(1 for x in cd if x.get('cap_dien_ap_tu_dong_boc')) == 291)
    test(10, f'Cu-Al: xoá đúng 48 giá trị vat_lieu_ruot sai '
             f'(thực tế {sum(1 for x in cd if x.get("vat_lieu_ruot_da_xoa_do_cu_al"))})',
         sum(1 for x in cd if x.get('vat_lieu_ruot_da_xoa_do_cu_al')) == 48)
    n_bug = sum(1 for x in mba if x.get('canh_bao_dien_ap'))
    n_sua = sum(1 for x in mba if x.get('cap_dien_ap_da_sua_bug'))
    n_flag = sum(1 for x in mba if x.get('cap_dien_ap_khong_the_tu_sua'))
    test(10, f'kVA/kV: 165 dòng bug, 164 tự sửa, 1 flag không suy đoán (thực tế {n_bug}/{n_sua}/{n_flag})',
         n_bug == 165 and n_sua == 164 and n_flag == 1)

    import subprocess
    duong_dan_snapshot = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'test_snapshot_regex.py')
    kq = subprocess.run(['python3', duong_dan_snapshot], capture_output=True, text=True)
    test(10, 'Unit test snapshot 33 tên thật (A=9,B=8,C=6,D=10)', kq.returncode == 0,
         kq.stdout.strip().splitlines()[-1] if kq.stdout else '')

    td = r_master['tu_va_thiet_bi_dong_cat']['rows']
    n_votu = sum(1 for x in td if x['outline_id'] == 'outline_vo_tu')
    n_pk_cd = sum(1 for x in cd if x['outline_id'] == 'outline_phu_kien')
    n_giatreo = sum(1 for x in mba if x['outline_id'] == 'outline_phu_kien')
    # Ver 6.0 — 14 -> 9 CÓ CHỦ ĐÍCH, không phải hồi quy.
    # Thêm định tuyến theo TÊN cho tu_va_thiet_bi_dong_cat (profiles.py) để
    # sửa 19 SKU mà Family Router báo SAI HỌ. 5 trong số đó có
    # nhom_nguon='10. Tủ Điện & Trung Thế' nên trước đây bị gom vào vỏ tủ:
    #     VNHNTC1P/1PC/1PLS/3P  "Hộp nguồn lắp đặt..."  -> outline_phu_kien
    #     SNDTDD                "Tủ đo đếm (TU,TI...)"  -> outline_do_luong
    # Hộp nguồn không phải vỏ tủ trung thế; tủ đo đếm thuộc họ đo lường.
    # Để nguyên thì bài viết mô tả sai bản chất và rank nhầm truy vấn.
    test(11, f'Routing: cap_dien->outline_phu_kien=185 ({n_pk_cd}), vỏ tủ->outline_vo_tu=9 ({n_votu}), '
             f'giá treo->outline_phu_kien=7 ({n_giatreo})',
         n_pk_cd == 185 and n_votu == 9 and n_giatreo == 7)

    pk = r_master['phu_kien_va_khac']['rows']
    n_service = sum(1 for x in pk if x['outline_id'] == 'outline_service')
    n_service_ct = sum(1 for x in pk if x['content_type'] == 'service')
    test(11, f'Round 2: 41 dòng dịch vụ route đúng outline_service (thực tế {n_service}, content_type=service: {n_service_ct})',
         n_service == 41 and n_service_ct == 41)

    print()
    so_pass = sum(1 for _, _, ok, _ in KET_QUA if ok)
    print(f'TỔNG: {so_pass}/{len(KET_QUA)} PASS')
    return KET_QUA


if __name__ == '__main__':
    kq = main()
    fail = [x for x in kq if not x[2]]
    if fail:
        print('\nFAIL:')
        for so, mo_ta, ok, gc in fail:
            print(f'  Test {so}: {mo_ta} ({gc})')
        raise SystemExit(1)
