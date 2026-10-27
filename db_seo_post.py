# -*- coding: utf-8 -*-
"""Ver 5.5 — DB cho module SEO POST.

TÁCH BẢNG, KHÔNG DÙNG LẠI article_jobs:
    article_jobs có `FOREIGN KEY (dataset_id, record_id) REFERENCES
    san_pham_phase2(...)` với PRAGMA foreign_keys=ON (db_phase2.py:45) —
    tức MỌI dòng bắt buộc neo vào đúng 1 SKU. Bài chủ đề ("máy biến áp khô
    là gì") không có SKU nào để neo, nhét vào bảng đó là SQLite từ chối ghi.

    Nên module post dùng 2 bảng RIÊNG:
        bai_seo      — đứng độc lập, KHÔNG FK tới san_pham_phase2
        bai_seo_sku  — nối nhiều-nhiều, RỖNG cũng hợp lệ
    Luồng sản phẩm cũ không đụng tới, không có rủi ro hồi quy.

DÙNG CHUNG FILE DB với db_phase2 (cùng %APPDATA%\\SONEALEO\\) để 1 bài post
có thể JOIN sang san_pham_phase2 lấy thông số khi cần gộp SKU.
"""
import json
import sqlite3
import uuid
from datetime import datetime

# Trạng thái bài — cố ý giống article_jobs để người dùng không phải học 2 bộ từ
MOI = 'MOI'                # vừa tạo, chưa sinh nội dung
DANG_SINH = 'DANG_SINH'
SINH_XONG = 'SINH_XONG'    # có HTML, chưa đăng
DA_DANG = 'DA_DANG'
LOI = 'LOI'
BO_QUA = 'BO_QUA'          # người dùng quyết định không viết (VD trùng site khác)

MOI_TRANG_THAI = (MOI, DANG_SINH, SINH_XONG, DA_DANG, LOI, BO_QUA)


def _bay_gio():
    return datetime.now().isoformat(timespec='seconds')


def ket_noi(db_path=None):
    """Mở kết nối + tạo schema. Dùng lại db_phase2.ket_noi() khi có, để
    chắc chắn cùng 1 file DB và cùng PRAGMA."""
    try:
        import db_phase2 as DB
        con = DB.ket_noi(db_path)
    except Exception:
        con = sqlite3.connect(db_path or 'seo-post.db')
        con.execute('PRAGMA foreign_keys=ON')
        con.execute('PRAGMA journal_mode=WAL')
        con.execute('PRAGMA busy_timeout=5000')
    tao_schema(con)
    return con


def tao_schema(con):
    con.execute('''CREATE TABLE IF NOT EXISTS bai_seo (
        bai_id TEXT PRIMARY KEY,
        tu_khoa_chinh TEXT NOT NULL,
        tu_khoa_phu TEXT,
        content_type TEXT NOT NULL,
        site TEXT NOT NULL,
        che_do_dang TEXT NOT NULL DEFAULT 'post',
        che_do_gia TEXT NOT NULL DEFAULT 'AN',
        ghi_chu_bien_tap TEXT,
        trang_thai TEXT NOT NULL DEFAULT 'MOI',
        title TEXT,
        slug TEXT,
        meta_description TEXT,
        html TEXT,
        ai_json TEXT,
        wp_id TEXT,
        wp_url TEXT,
        loi TEXT,
        nguon TEXT,
        diem_uu_tien REAL,
        impression_goc REAL,
        thoi_luong_giay REAL,
        ngay_dang TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )''')
    # Nối nhiều-nhiều. KHÔNG khai FOREIGN KEY tới san_pham_phase2: dataset cũ
    # có thể bị xoá/thay khi import MASTER mới, mà bài đã đăng thì vẫn phải
    # giữ nguyên lịch sử. Ràng buộc chỉ tới bai_seo (ON DELETE CASCADE).
    con.execute('''CREATE TABLE IF NOT EXISTS bai_seo_sku (
        bai_id TEXT NOT NULL,
        dataset_id TEXT NOT NULL,
        record_id TEXT NOT NULL,
        PRIMARY KEY (bai_id, dataset_id, record_id),
        FOREIGN KEY (bai_id) REFERENCES bai_seo(bai_id) ON DELETE CASCADE
    )''')
    con.execute('CREATE INDEX IF NOT EXISTS ix_bai_seo_trang_thai ON bai_seo(trang_thai)')
    con.execute('CREATE INDEX IF NOT EXISTS ix_bai_seo_site ON bai_seo(site)')
    con.execute('CREATE INDEX IF NOT EXISTS ix_bai_seo_kw ON bai_seo(tu_khoa_chinh)')
    con.commit()


# ============================================================ ghi

def tao_bai(con, tu_khoa_chinh, content_type, site, tu_khoa_phu=None,
            che_do_dang='post', che_do_gia='AN', ghi_chu_bien_tap='',
            nguon='tay', diem_uu_tien=None, impression_goc=None):
    """Tạo 1 bài mới. Trả bai_id.

    CHỐNG TRÙNG: cùng (tu_khoa_chinh, site) mà đã có bài chưa BO_QUA thì
    KHÔNG tạo thêm — trả bai_id cũ. Đây là chốt chặn cannibalization ở tầng
    dữ liệu: 1.802 từ khoá trong hệ đang bị >=2 site tranh, không chặn ở đây
    thì import 3 lần cùng 1 file GSC là ra 3 bài y hệt.
    """
    cu = con.execute(
        'SELECT bai_id FROM bai_seo WHERE tu_khoa_chinh=? AND site=? AND trang_thai<>? LIMIT 1',
        (tu_khoa_chinh.strip(), site, BO_QUA)).fetchone()
    if cu:
        return cu[0]

    bai_id = 'bai_' + uuid.uuid4().hex[:12]
    t = _bay_gio()
    con.execute(
        'INSERT INTO bai_seo (bai_id, tu_khoa_chinh, tu_khoa_phu, content_type, site, '
        'che_do_dang, che_do_gia, ghi_chu_bien_tap, trang_thai, nguon, diem_uu_tien, '
        'impression_goc, created_at, updated_at) '
        'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        (bai_id, tu_khoa_chinh.strip(), json.dumps(tu_khoa_phu or [], ensure_ascii=False),
         content_type, site, che_do_dang, che_do_gia, ghi_chu_bien_tap, MOI,
         nguon, diem_uu_tien, impression_goc, t, t))
    con.commit()
    return bai_id


def gan_sku(con, bai_id, danh_sach):
    """danh_sach = [(dataset_id, record_id), ...]. Ghi đè toàn bộ."""
    con.execute('DELETE FROM bai_seo_sku WHERE bai_id=?', (bai_id,))
    con.executemany('INSERT OR IGNORE INTO bai_seo_sku (bai_id, dataset_id, record_id) VALUES (?,?,?)',
                    [(bai_id, d, r) for d, r in danh_sach])
    con.execute('UPDATE bai_seo SET updated_at=? WHERE bai_id=?', (_bay_gio(), bai_id))
    con.commit()


def cap_nhat(con, bai_id, **truong):
    """Cập nhật field bất kỳ của bai_seo. Chặn field lạ để không âm thầm
    ghi nhầm vào cột không tồn tại."""
    hop_le = {'tu_khoa_chinh', 'tu_khoa_phu', 'content_type', 'site', 'che_do_dang',
              'che_do_gia', 'ghi_chu_bien_tap', 'trang_thai', 'title', 'slug',
              'meta_description', 'html', 'ai_json', 'wp_id', 'wp_url', 'loi',
              'diem_uu_tien', 'impression_goc', 'thoi_luong_giay', 'ngay_dang'}
    xau = set(truong) - hop_le
    if xau:
        raise ValueError(f'Field không có trong bai_seo: {sorted(xau)}')
    if 'trang_thai' in truong and truong['trang_thai'] not in MOI_TRANG_THAI:
        raise ValueError(f'Trạng thái không hợp lệ: {truong["trang_thai"]}')
    if not truong:
        return
    truong['updated_at'] = _bay_gio()
    set_sql = ', '.join(f'{k}=?' for k in truong)
    con.execute(f'UPDATE bai_seo SET {set_sql} WHERE bai_id=?',
                tuple(truong.values()) + (bai_id,))
    con.commit()


def xoa_bai(con, bai_id):
    con.execute('DELETE FROM bai_seo WHERE bai_id=?', (bai_id,))
    con.commit()


# ============================================================ đọc

def lay_bai(con, bai_id):
    con.row_factory = sqlite3.Row
    r = con.execute('SELECT * FROM bai_seo WHERE bai_id=?', (bai_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d['tu_khoa_phu'] = json.loads(d.get('tu_khoa_phu') or '[]')
    d['sku'] = [(x[0], x[1]) for x in con.execute(
        'SELECT dataset_id, record_id FROM bai_seo_sku WHERE bai_id=?', (bai_id,))]
    return d


def liet_ke(con, trang_thai=None, site=None, content_type=None, gioi_han=500):
    con.row_factory = sqlite3.Row
    dk, tham = [], []
    if trang_thai:
        dk.append('b.trang_thai=?')
        tham.append(trang_thai)
    if site:
        dk.append('b.site=?')
        tham.append(site)
    if content_type:
        dk.append('b.content_type=?')
        tham.append(content_type)
    where = ('WHERE ' + ' AND '.join(dk)) if dk else ''
    sql = (f'SELECT b.*, (SELECT COUNT(*) FROM bai_seo_sku s WHERE s.bai_id=b.bai_id) AS so_sku '
           f'FROM bai_seo b {where} '
           f'ORDER BY CASE WHEN b.diem_uu_tien IS NULL THEN 1 ELSE 0 END, '
           f'b.diem_uu_tien DESC, b.created_at DESC LIMIT ?')
    return [dict(r) for r in con.execute(sql, tuple(tham) + (gioi_han,))]


def dem_theo_trang_thai(con):
    return {r[0]: r[1] for r in con.execute(
        'SELECT trang_thai, COUNT(*) FROM bai_seo GROUP BY trang_thai')}


def tim_trung_tu_khoa(con, tu_khoa, tru_bai_id=None):
    """Từ khoá này đã có bài ở site nào chưa. Dùng để cảnh báo cannibalization
    NGAY LÚC tạo bài, không đợi tới lúc đăng xong mới phát hiện."""
    sql = 'SELECT bai_id, site, trang_thai, wp_url FROM bai_seo WHERE tu_khoa_chinh=? AND trang_thai<>?'
    tham = [tu_khoa.strip(), BO_QUA]
    if tru_bai_id:
        sql += ' AND bai_id<>?'
        tham.append(tru_bai_id)
    return [{'bai_id': r[0], 'site': r[1], 'trang_thai': r[2], 'wp_url': r[3]}
            for r in con.execute(sql, tham)]


def sku_cua_bai(con, bai_id):
    """Trả list dict record đầy đủ từ san_pham_phase2 (JOIN sang bảng cũ).
    Trả [] nếu bảng đó không tồn tại — module post vẫn chạy được khi chưa
    import MASTER nào."""
    try:
        rows = con.execute(
            'SELECT sp.dataset_id, sp.record_id, sp.profile_id, sp.outline_id, sp.du_lieu_json '
            'FROM bai_seo_sku s JOIN san_pham_phase2 sp '
            '  ON sp.dataset_id=s.dataset_id AND sp.record_id=s.record_id '
            'WHERE s.bai_id=?', (bai_id,)).fetchall()
    except sqlite3.OperationalError:
        return []
    ra = []
    for d, r, p, o, js in rows:
        try:
            du_lieu = json.loads(js)
        except (ValueError, TypeError):
            du_lieu = {}
        du_lieu.update({'dataset_id': d, 'record_id': r, 'profile_id': p, 'outline_id': o})
        ra.append(du_lieu)
    return ra
