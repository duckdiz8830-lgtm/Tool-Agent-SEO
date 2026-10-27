import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import importlib.util, json, os, sys, time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ver 5.1 -- test o tests/, du lieu/module chinh o thu muc goc (len 1 cap)
spec = importlib.util.spec_from_file_location('giao_dien', os.path.join(BASE, 'giao-dien.py'))
gd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gd)

import outline_studio as OS
import prompts_phase2 as PR
import db_phase2 as DB

KQ = []


def test(ma, mota, ok):
    KQ.append((ma, mota, bool(ok)))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}')


FILE_TC = os.path.join(BASE, 'outline-tuy-chinh.json')
if os.path.exists(FILE_TC):
    os.remove(FILE_TC)

OID = 'outline_cap_dien'
CFG_GOC = json.loads(json.dumps(PR.OUTLINE_NOI_DUNG[OID]))  # snapshot sâu để so sánh sau này

# ============================================================
# NHÓM A — module outline_studio.py thuần (không cần UI)
# ============================================================
test('OS-A1', 'Chưa có file tuỳ chỉnh -> doc_1() trả None (dùng mặc định gốc)',
     OS.doc_1(OID) is None)

test('OS-A2', 'cfg_hieu_luc() khi chưa tuỳ chỉnh trả ĐÚNG bản gốc (không đổi 1 ký tự)',
     OS.cfg_hieu_luc(OID, PR.OUTLINE_NOI_DUNG[OID]) == CFG_GOC)

OS.luu(OID, 'Góc nhìn MỚI để test', {
    'intro_html': 'Huong dan intro MOI',
    'dac_diem_html': 'Huong dan dac diem MOI',
    'ung_dung_html': 'Huong dan ung dung MOI',
    'huong_dan_chon_html': 'Huong dan chon MOI',
}, ghi_chu_bo_qua='Ghi chu rieng MOI')

cfg_sau_luu = OS.cfg_hieu_luc(OID, PR.OUTLINE_NOI_DUNG[OID])
test('OS-A3', f'Sau khi lưu, cfg_hieu_luc() trả ĐÚNG bản đã sửa: {cfg_sau_luu["goc_nhin"]}',
     cfg_sau_luu['goc_nhin'] == 'Góc nhìn MỚI để test'
     and cfg_sau_luu['sections']['dac_diem_html'] == 'Huong dan dac diem MOI'
     and cfg_sau_luu['ghi_chu_bo_qua'] == 'Ghi chu rieng MOI')

test('OS-A4', 'OUTLINE_NOI_DUNG gốc trong code KHÔNG bị sửa (bất biến, chỉ đọc)',
     PR.OUTLINE_NOI_DUNG[OID] == CFG_GOC)

test('OS-A5', 'co_faq KHÔNG đổi được qua Outline Studio (chỉ lấy từ cfg gốc, không đọc từ file)',
     cfg_sau_luu['co_faq'] == CFG_GOC['co_faq'])

test('OS-A6', "nhan_outline KHÔNG đổi được qua Outline Studio (không nằm trong TRUONG_SECTION_CHO_SUA)",
     cfg_sau_luu['nhan_outline'] == CFG_GOC['nhan_outline'])

OS.khoi_phuc_mac_dinh(OID)
test('OS-A7', 'Khôi phục mặc định -> cfg_hieu_luc() trả lại ĐÚNG bản gốc',
     OS.cfg_hieu_luc(OID, PR.OUTLINE_NOI_DUNG[OID]) == CFG_GOC)

# ---- key lạ/field không cho phép trong sections bị bỏ qua, không lưu ----
OS.luu(OID, 'test key la', {'intro_html': 'ok', 'field_khong_ton_tai': 'KHONG DUOC LUU'})
tc = OS.doc_1(OID)
test('OS-A8', f'Field lạ không nằm trong 4 field cho phép bị bỏ qua khi lưu: {tc["sections"]}',
     'field_khong_ton_tai' not in tc['sections'])
OS.khoi_phuc_mac_dinh(OID)

# ---- file JSON hỏng (tay sửa sai) không được làm crash ----
with open(FILE_TC, 'w', encoding='utf-8') as f:
    f.write('{ day la json hong khong parse duoc ]')
test('OS-A9', 'File outline-tuy-chinh.json hỏng -> doc_tat_ca() trả {} an toàn, không raise',
     OS.doc_tat_ca() == {})
test('OS-A10', 'File hỏng -> cfg_hieu_luc() vẫn trả cfg gốc bình thường, không crash',
     OS.cfg_hieu_luc(OID, PR.OUTLINE_NOI_DUNG[OID]) == CFG_GOC)
os.remove(FILE_TC)

# ============================================================
# NHÓM B — xay_prompt() thật sự đọc override (không phải chỉ cfg_hieu_luc suông)
# ============================================================
app = gd.PhanMem()
app.geometry('1366x768+0+0')
app.update()
app._phase2_lam_import(os.path.join(BASE, 'du_lieu_goc', 'MASTER_4_PROFILE_SAN_PHAM.xlsx'))
app._boc_hang_doi()
gt = [g for g in app.cb_phase2_dataset['values'] if g.startswith('ds_cap_dien')][0]
app.v_phase2_dataset.set(gt)
app._v3_loc_san_pham()
app.update()
did = app._phase2_dataset_id_dang_chon()
con = app._con_phase2()
row_cap = DB.liet_ke_san_pham(con, dataset_id=did, outline_id=OID)[0]
con.close()

he_thong_truoc, nguoi_dung_truoc, _ = PR.xay_prompt(row_cap, {'ten': 'Test'}, mau='chuan')
test('OS-B1', 'TRƯỚC khi tuỳ chỉnh: prompt user KHÔNG chứa đoạn hướng dẫn mới (chưa lưu gì)',
     'CAU_DUY_NHAT_XYZ_DAC_DIEM' not in nguoi_dung_truoc)

OS.luu(OID, 'Goc nhin qua Outline Studio test B', {
    'intro_html': CFG_GOC['sections']['intro_html'],
    'dac_diem_html': 'CAU_DUY_NHAT_XYZ_DAC_DIEM — mo ta dac diem kieu moi',
    'ung_dung_html': CFG_GOC['sections']['ung_dung_html'],
    'huong_dan_chon_html': CFG_GOC['sections']['huong_dan_chon_html'],
})
he_thong_sau, nguoi_dung_sau, _ = PR.xay_prompt(row_cap, {'ten': 'Test'}, mau='chuan')
test('OS-B2', 'SAU khi tuỳ chỉnh: prompt user chứa ĐÚNG đoạn hướng dẫn mới vừa lưu',
     'CAU_DUY_NHAT_XYZ_DAC_DIEM' in nguoi_dung_sau)
test('OS-B3', 'System prompt cũng đổi theo goc_nhin mới',
     'Goc nhin qua Outline Studio test B' in he_thong_sau)

# ---- Hard Block / QUY_TAC_CHUNG / JSON schema KHÔNG bị ảnh hưởng bởi tuỳ chỉnh ----
_, _, schema_truoc = PR.xay_prompt(row_cap, {'ten': 'Test'}, mau='chuan')
test('OS-B4', 'QUY_TAC_CHUNG (luật chống bịa số) vẫn còn nguyên trong system prompt sau tuỳ chỉnh',
     'Không suy đoán' in he_thong_sau and 'KHÔNG tự dựng bảng thông số' in he_thong_sau)
test('OS-B5', 'JSON schema (danh sách field AI được trả) không đổi bởi Outline Studio',
     schema_truoc == PR._json_schema(OID, mau='chuan'))

OS.khoi_phuc_mac_dinh(OID)
he_thong_reset, nguoi_dung_reset, _ = PR.xay_prompt(row_cap, {'ten': 'Test'}, mau='chuan')
test('OS-B6', 'Khôi phục mặc định -> prompt trở lại y hệt bản TRƯỚC khi tuỳ chỉnh',
     nguoi_dung_reset == nguoi_dung_truoc and he_thong_reset == he_thong_truoc)

# ============================================================
# NHÓM C — UI: chọn outline, gõ, Lưu, Khôi phục, Xem trước
# ============================================================
app.cb_os_outline.set([k for k, v in app._os_outline_map.items() if v == OID][0])
app._os_nap()
app.update()
test('OS-C1', 'UI nạp đúng góc nhìn mặc định khi chọn outline',
     app.txt_os_goc_nhin.get('1.0', 'end').strip() == CFG_GOC['goc_nhin'])
test('OS-C2', 'Trạng thái hiển thị đúng "đang dùng mặc định gốc" khi chưa tuỳ chỉnh',
     'mặc định' in app.lb_os_trang_thai.cget('text'))

app.txt_os_goc_nhin.delete('1.0', 'end')
app.txt_os_goc_nhin.insert('end', 'Goc nhin tu UI test C')
app.txt_os_section['dac_diem_html'].delete('1.0', 'end')
app.txt_os_section['dac_diem_html'].insert('end', 'Dac diem tu UI test C')

import tkinter.messagebox as messagebox
_cu_info = messagebox.showinfo
messagebox.showinfo = lambda *a, **k: None
app._os_luu()

test('OS-C3', 'Sau khi bấm Lưu, trạng thái đổi thành "(đã tuỳ chỉnh)"',
     'đã tuỳ chỉnh' in app.lb_os_trang_thai.cget('text'))
test('OS-C4', 'File outline-tuy-chinh.json thật sự được ghi ra đĩa',
     os.path.exists(FILE_TC) and OS.doc_1(OID)['goc_nhin'] == 'Goc nhin tu UI test C')

app._os_xem_truoc()   # nội bộ cũng gọi _os_luu() -> showinfo, phải giữ nguyên bản đã patch
messagebox.showinfo = _cu_info
app.update()
xem_truoc_text = app.txt_os_xem_truoc.get('1.0', 'end')
test('OS-C5', 'Xem trước hiển thị ĐÚNG prompt thật (chứa đoạn vừa sửa), không phải bản mock giả',
     'Dac diem tu UI test C' in xem_truoc_text and 'SYSTEM' in xem_truoc_text and 'USER' in xem_truoc_text)

_cu_askyesno = messagebox.askyesno
messagebox.askyesno = lambda *a, **k: True
app._os_khoi_phuc()
messagebox.askyesno = _cu_askyesno

test('OS-C6', 'Sau Khôi phục mặc định, UI nạp lại đúng góc nhìn gốc',
     app.txt_os_goc_nhin.get('1.0', 'end').strip() == CFG_GOC['goc_nhin'])
test('OS-C7', 'Trạng thái trở lại "đang dùng mặc định gốc"',
     'mặc định' in app.lb_os_trang_thai.cget('text'))

app.destroy()

print()
p = sum(1 for _, _, ok in KQ if ok)
print(f'TONG VER 3.8 OUTLINE STUDIO: {p}/{len(KQ)} PASS')
if p != len(KQ):
    sys.exit(1)
