import os as _os, sys as _sys  # Ver 5.1 -- gọn thư mục: test chuyển vào tests/, thêm đường dẫn về thư mục gốc để import các module chính
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import sys
import render_phase2 as R

# Ver 5.1 — RÀ LẠI file test này khi audit tool (Audit-Checklist-Ver5.0.xlsx
# mục Tool #9): file này đứng yên từ Ver 4.2, chưa từng chạy lại/cập nhật
# qua các đợt đổi CSS-inline (Ver 4.9.9) và tách schema khỏi html (Ver
# 4.9.6) — 5/12 test FAIL khi chạy lại thật vì kiểm tra hành vi CŨ đã bị
# thay đổi CÓ CHỦ ĐÍCH từ lâu. Cập nhật theo hành vi HIỆN TẠI, giữ nguyên
# Ý NGHĨA kiểm tra gốc (vị trí Hero/CTA/bảng, không phải tên class cụ thể).

KQ = []


def test(ma, mota, ok):
    KQ.append((ma, mota, bool(ok)))
    print(f'[{"PASS" if ok else "FAIL"}] {ma}: {mota}')


row = {
    'profile_id': 'cap_dien', 'outline_id': 'outline_cap_dien', 'ma_goc': 'CDVCMD21.5',
    'ten_goc': 'Dây VCmd2x1.5mm2 (0.6/1kV) - Cadivi', 'thuong_hieu': 'Cadivi',
    'tiet_dien': '2x1.5', 'cap_dien_ap': '0.6/1', 'dvt': 'M',
}
ai_data = {'meta_title': 'T', 'meta_description': 'M', 'intro_html': '<p>Gioi thieu</p>',
          'dac_diem_html': '<p>Dac diem</p>'}
site_cfg = {'ten': 'Lotech', 'hotline': '0909123456', 'zalo': '0909123456'}

bai = R.dung_bai_html(row, ai_data, site_cfg)
h = bai['html']

# ============================================================ NHÓM A — Hero block
test('HERO-1', 'HTML bắt đầu bằng khối Hero (Ver 5.1: div có style inline, không còn class)',
     h.startswith('<div style="'))
test('HERO-2', 'Hero có Mã hàng', 'CDVCMD21.5' in h.split('</div>')[0])
test('HERO-3', 'Hero có Thương hiệu', 'Cadivi' in h.split('</div>')[0])
test('HERO-4', 'Hero có Giá: Liên hệ', 'Giá:</strong> Liên hệ' in h.split('</div>')[0])
test('HERO-5', 'Hero KHÔNG qua AI — chỉ dựng từ row/site_cfg, đổi ai_data không ảnh hưởng Hero',
     R.khoi_hero(row, site_cfg) == R.dung_bai_html(row, {}, site_cfg)['html'].split('\n')[0])

# ============================================================ NHÓM B — CTA đúng vị trí (Ver 5.1: nhận diện qua nút "Yêu cầu báo giá", không qua class)
so_cta_ngan = h.count('Yêu cầu báo giá')
test('CTA-1', f'Nút "Yêu cầu báo giá" xuất hiện đúng 2 lần (Hero + sau bảng thông số): {so_cta_ngan}',
     so_cta_ngan == 2)
test('CTA-2', 'CTA đầy đủ (cuối trang) vẫn còn anchor id (giữ nguyên từ Ver 4.5.1, KHÔNG đổi)',
     '<h2 id="lien-he-bao-gia">Liên hệ báo giá</h2>' in h)
vi_tri_hero = h.find('Yêu cầu báo giá')
vi_tri_bang = h.find('Công suất' if 'Công suất' in h else '<table')
vi_tri_cta2 = h.find('Yêu cầu báo giá', vi_tri_hero + 1)
vi_tri_cta_cuoi = h.find('Liên hệ báo giá</h2>')
test('CTA-3', f'Thứ tự đúng: Hero({vi_tri_hero}) < bảng thông số({vi_tri_bang}) < CTA gọn #2({vi_tri_cta2}) < CTA cuối({vi_tri_cta_cuoi})',
     vi_tri_hero < vi_tri_bang < vi_tri_cta2 < vi_tri_cta_cuoi)

# ============================================================ NHÓM C — khoi_cta() vẫn giữ đúng nội dung/anchor (Ver 5.1: định dạng nút thay đổi, không so sánh chuỗi cứng nữa)
cta_full = R.khoi_cta(site_cfg)
test('CTA-4', 'khoi_cta() vẫn có id anchor + đúng hotline/zalo (nội dung, không so khớp định dạng CSS cụ thể)',
     'id="lien-he-bao-gia"' in cta_full and '0909123456' in cta_full and 'zalo.me/0909123456' in cta_full)

# ============================================================ NHÓM D — không hotline vẫn không crash
site_cfg_trong = {}
bai_trong = R.dung_bai_html(row, ai_data, site_cfg_trong)
test('CTA-5', 'Không có hotline: Hero + CTA vẫn render an toàn, không crash', bool(bai_trong['html']))

# ============================================================ NHÓM E — regression: schema (Ver 5.1: tách riêng khỏi html từ Ver 4.9.6, KHÔNG còn đếm JSON-LD trong html)
test('REG-1', 'Schema KHÔNG còn nhét vào html (đúng hành vi Ver 4.9.6 — tránh bug WordPress kses xoá <script>)',
     'application/ld+json' not in h)
test('REG-1B', "dung_bai_html() trả riêng key 'schema' (dict) đúng nội dung Product",
     isinstance(bai.get('schema'), dict) and bai['schema'].get('@type') == 'Product')
row_dv = dict(row, profile_id='phu_kien_va_khac', outline_id='outline_service', content_type='service')
bai_dv = R.dung_bai_html(row_dv, ai_data, site_cfg)
test('REG-2', 'Dịch vụ vẫn KHÔNG có schema (Hero không ảnh hưởng logic content_type)',
     bai_dv.get('schema') is None)

print()
p = sum(1 for _, _, ok in KQ if ok)
print(f'TONG VER 4.2 HERO+CTA (ra soat lai Ver 5.1): {p}/{len(KQ)} PASS')
if p != len(KQ):
    sys.exit(1)
