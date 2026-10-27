# -*- coding: utf-8 -*-
"""
Ver 3.8 — Outline Studio.

Cho phép chỉnh phần "AI viết" của mỗi outline (7 outline cố định trong
prompts_phase2.OUTLINE_NOI_DUNG) MÀ KHÔNG CẦN SỬA CODE — đúng yêu cầu Work
Order Ver 3.8: quản lý block DATA/CODE/AI/SCHEMA, KHÔNG cho AI sửa
specs/schema cố định.

Chỉ 3 trường được phép tuỳ chỉnh (đúng "block AI"):
  - goc_nhin           : câu định hướng giọng văn/đối tượng đọc
  - sections.*         : mô tả hướng dẫn AI viết 4 mục (intro/dac_diem/
                          ung_dung/huong_dan_chon)
  - ghi_chu_bo_qua      : ghi chú riêng (tuỳ chọn) của outline

TUYỆT ĐỐI KHÔNG cho sửa qua module này (khoá cứng, thuộc "block CODE/SCHEMA"):
  - TRUONG_AI_DUOC_TRA_CHUAN / GIOI_HAN_DO_DAI (danh sách field + độ dài)
  - QUY_TAC_CHUNG (luật Hard Block chống bịa số — bất biến)
  - co_faq (đổi field này đổi cả JSON schema + cách render, rủi ro cao,
    không thuộc phạm vi "sửa cách viết")
  - Bất cứ thứ gì trong render_phase2.py (bảng thông số, Schema.org JSON-LD)

Lưu vào 1 file JSON riêng (outline-tuy-chinh.json) cạnh code — không đổi
DB, không đổi schema bai_viet_phase2/san_pham_phase2. File hỏng/thiếu thì
coi như CHƯA CÓ tuỳ chỉnh (dùng nguyên bản gốc trong code), không crash.
"""
import json
from pathlib import Path

BASE = Path(__file__).parent
FILE_TUY_CHINH = BASE / 'outline-tuy-chinh.json'

TRUONG_SECTION_CHO_SUA = ('intro_html', 'dac_diem_html', 'ung_dung_html', 'huong_dan_chon_html')


def doc_tat_ca():
    """Trả dict {outline_id: {...}} toàn bộ tuỳ chỉnh đã lưu. File không
    tồn tại hoặc hỏng -> trả {} (an toàn, không raise)."""
    if not FILE_TUY_CHINH.exists():
        return {}
    try:
        with open(FILE_TUY_CHINH, 'r', encoding='utf-8') as f:
            du_lieu = json.load(f)
        return du_lieu if isinstance(du_lieu, dict) else {}
    except Exception:
        return {}


def doc_1(outline_id):
    return doc_tat_ca().get(outline_id)


def _ghi(du_lieu):
    with open(FILE_TUY_CHINH, 'w', encoding='utf-8') as f:
        json.dump(du_lieu, f, ensure_ascii=False, indent=2)


def luu(outline_id, goc_nhin, sections, ghi_chu_bo_qua=''):
    """sections: dict, CHỈ nhận đúng 4 key trong TRUONG_SECTION_CHO_SUA —
    key lạ bị bỏ qua, không lưu field không nằm trong danh sách cho phép."""
    du_lieu = doc_tat_ca()
    du_lieu[outline_id] = {
        'goc_nhin': (goc_nhin or '').strip(),
        'sections': {k: (sections.get(k) or '').strip() for k in TRUONG_SECTION_CHO_SUA},
        'ghi_chu_bo_qua': (ghi_chu_bo_qua or '').strip(),
    }
    _ghi(du_lieu)


def khoi_phuc_mac_dinh(outline_id):
    """Xoá tuỳ chỉnh của 1 outline — quay lại đúng bản gốc trong code. Trả
    True nếu có xoá, False nếu vốn chưa tuỳ chỉnh gì (không phải lỗi)."""
    du_lieu = doc_tat_ca()
    if outline_id in du_lieu:
        del du_lieu[outline_id]
        _ghi(du_lieu)
        return True
    return False


def cfg_hieu_luc(outline_id, cfg_goc):
    """Trộn tuỳ chỉnh (nếu có) LÊN TRÊN cfg gốc lấy từ
    prompts_phase2.OUTLINE_NOI_DUNG[outline_id]. cfg_goc không bị sửa (trả
    bản copy mới) — OUTLINE_NOI_DUNG trong code luôn giữ nguyên, khôi phục
    mặc định lúc nào cũng ra đúng bản gốc.

    Field không thuộc TRUONG_SECTION_CHO_SUA/goc_nhin/ghi_chu_bo_qua
    (co_faq, nhan_outline...) LUÔN lấy từ cfg_goc, tuyệt đối không đọc từ
    file tuỳ chỉnh dù file có chứa field đó (phòng file bị chỉnh tay sai)."""
    ket_qua = dict(cfg_goc)
    ket_qua['sections'] = dict(cfg_goc.get('sections', {}))

    tuy_chinh = doc_1(outline_id)
    if not tuy_chinh:
        return ket_qua

    if tuy_chinh.get('goc_nhin'):
        ket_qua['goc_nhin'] = tuy_chinh['goc_nhin']

    for k, v in (tuy_chinh.get('sections') or {}).items():
        if k in TRUONG_SECTION_CHO_SUA and k in ket_qua['sections'] and v:
            ket_qua['sections'][k] = v

    if tuy_chinh.get('ghi_chu_bo_qua'):
        ket_qua['ghi_chu_bo_qua'] = tuy_chinh['ghi_chu_bo_qua']

    return ket_qua
