# -*- coding: utf-8 -*-
"""
Round 2 — R2-01 bước 1 "Database và migration", R2-02, R2-03, R2-04.

Schema mới, đa site + đa mẫu, tách rõ 3 bảng:
  - dataset            : metadata 1 dòng / lần xác nhận dataset (R2-04)
  - san_pham_phase2    : 1 dòng / record, khoá (dataset_id, record_id)   (R2-02)
  - bai_viet_phase2    : 1 dòng / (record, site, mẫu) bài đã/đang sinh   (R2-02)

Import lại CÙNG dataset (R2-03): UPSERT san_pham_phase2 (cập nhật
du_lieu_json/profile_id/outline_id/content_type/pipeline_version, GIỮ
NGUYÊN selected — cột không có trong SET của DO UPDATE thì SQLite tự giữ
nguyên, không phải code tự xử lý riêng). KHÔNG bao giờ đụng bai_viet_phase2
khi ghi san_pham_phase2 — 2 bảng độc lập hoàn toàn, không có thao tác nào xoá
hàng loạt bai_viet_phase2 theo dataset_id trong file này.

Không đụng `du-lieu.db` của nhánh RMU cũ (dulieu.py) — DB riêng
`phase2-du-lieu.db`, không tạo sẵn trong gói giao (R2-12: app tự tạo rỗng
lúc chạy lần đầu).
"""
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PIPELINE_VERSION = 'phase2-lite-r2'

BASE = Path(__file__).parent

# Ver 4.4.1.6 — DB ra %APPDATA%\SONEALEO\, ngoài thư mục version.
# Trước bản này DB nằm cạnh file .py nên mỗi lần lên version phải copy tay;
# quên copy = tưởng mất sạch bài đã đăng, copy ngược = đè bản mới bằng bản
# cũ mà không có cảnh báo nào. Fail-soft: thư mục chung hỏng thì về BASE.
try:
    import thu_muc_du_lieu as _TM
    _TM.chuan_bi(BASE)
    DB_PATH = _TM.duong_dan_db()
except Exception:
    DB_PATH = BASE / 'phase2-du-lieu.db'


def ket_noi(db_path=None):
    con = sqlite3.connect(db_path or DB_PATH)
    con.execute('PRAGMA foreign_keys=ON')
    # Ver 4.2 audit debt: desktop app có nhiều worker; WAL + busy_timeout
    # giảm lỗi `database is locked` mà không đổi transaction/business logic.
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA busy_timeout=5000')
    _tao_schema(con)
    return con


def _tao_schema(con):
    con.execute('''CREATE TABLE IF NOT EXISTS dataset (
        dataset_id TEXT PRIMARY KEY,
        profile_id TEXT NOT NULL,
        source_file TEXT,
        file_checksum TEXT NOT NULL,
        data_checksum TEXT NOT NULL,
        row_count INTEGER NOT NULL,
        column_structure TEXT NOT NULL,
        pipeline_version TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    )''')
    con.execute('''CREATE TABLE IF NOT EXISTS san_pham_phase2 (
        dataset_id TEXT NOT NULL,
        record_id TEXT NOT NULL,
        profile_id TEXT NOT NULL,
        outline_id TEXT NOT NULL,
        content_type TEXT NOT NULL,
        du_lieu_json TEXT NOT NULL,
        selected INTEGER NOT NULL DEFAULT 0,
        pipeline_version TEXT NOT NULL,
        PRIMARY KEY (dataset_id, record_id),
        FOREIGN KEY (dataset_id) REFERENCES dataset(dataset_id)
    )''')
    con.execute('''CREATE TABLE IF NOT EXISTS bai_viet_phase2 (
        dataset_id TEXT NOT NULL,
        record_id TEXT NOT NULL,
        site TEXT NOT NULL,
        mau TEXT NOT NULL,
        slug TEXT,
        title TEXT,
        meta_description TEXT,
        html TEXT,
        trang_thai TEXT NOT NULL DEFAULT 'chua_sinh',
        loi TEXT,
        wp_id TEXT,
        wp_url TEXT,
        ngay_dang TEXT,
        thoi_luong_giay REAL,
        PRIMARY KEY (dataset_id, record_id, site, mau),
        FOREIGN KEY (dataset_id, record_id) REFERENCES san_pham_phase2(dataset_id, record_id)
    )''')
    # Migration an toàn cho DB đã tạo TRƯỚC KHI có cột thoi_luong_giay (Gate
    # Draft thật) — CREATE TABLE IF NOT EXISTS không tự thêm cột thiếu vào
    # bảng đã tồn tại, phải ALTER TABLE riêng. Bọc try/except vì SQLite
    # không có "ADD COLUMN IF NOT EXISTS" — lỗi "duplicate column" nghĩa là
    # đã chạy migration này trước đó rồi, bỏ qua an toàn.
    try:
        con.execute('ALTER TABLE bai_viet_phase2 ADD COLUMN thoi_luong_giay REAL')
    except sqlite3.OperationalError:
        pass

    # Ver 3.9 — Article Jobs: 1 sản phẩm có thể có NHIỀU bài (job), mỗi job
    # outline riêng, đăng riêng, trạng thái riêng. Bảng RIÊNG, KHÔNG dùng lại
    # bai_viet_phase2 — bảng đó khoá theo (dataset_id, record_id, site, mau),
    # không đủ chỗ cho nhiều job cùng site/mẫu của 1 record. job_id là khoá
    # thật duy nhất.
    con.execute('''CREATE TABLE IF NOT EXISTS article_jobs (
        job_id TEXT PRIMARY KEY,
        dataset_id TEXT NOT NULL,
        record_id TEXT NOT NULL,
        site TEXT NOT NULL,
        mau TEXT NOT NULL,
        outline_id TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        trang_thai TEXT NOT NULL DEFAULT 'PENDING',
        slug TEXT,
        title TEXT,
        meta_description TEXT,
        html TEXT,
        wp_id TEXT,
        wp_url TEXT,
        loi TEXT,
        thoi_luong_giay REAL,
        ngay_dang TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (dataset_id, record_id) REFERENCES san_pham_phase2(dataset_id, record_id)
    )''')
    # SONEALEO Ver 1.2 — chống Enhance lặp insight giữa các SKU CÙNG NHÓM
    # (VD chạy Enhance cho 50 máy biến áp dầu 3 pha khác công suất -> nếu
    # không nhớ lại, insight rút ra dễ na ná nhau, tái tạo đúng lỗi
    # boilerplate Ver 5.3 đã bị vá — chỉ khác là lần này do Enhance sinh
    # ra chứ không phải code cố định). `nhom_khoa` = ten_loai_san_pham đã
    # chuẩn hoá (lower, bỏ khoảng trắng thừa) — KHÔNG theo record_id, vì
    # mục đích là chống lặp GIỮA CÁC SKU CÙNG NHÓM, không phải theo dõi
    # riêng từng SKU.
    con.execute('''CREATE TABLE IF NOT EXISTS enhance_lich_su_insight (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nhom_khoa TEXT NOT NULL,
        truong TEXT NOT NULL,
        noi_dung TEXT NOT NULL,
        record_id_da_dung TEXT NOT NULL,
        created_at TEXT NOT NULL
    )''')
    con.execute('''CREATE INDEX IF NOT EXISTS idx_enhance_lich_su_nhom
        ON enhance_lich_su_insight(nhom_khoa)''')
    con.commit()


def _now():
    return datetime.now(timezone.utc).isoformat()


# ============================================================ dataset metadata
def dataset_gan_nhat(con, profile_id):
    cur = con.execute(
        'SELECT dataset_id, data_checksum, column_structure FROM dataset '
        'WHERE profile_id=? AND active=1 ORDER BY rowid DESC LIMIT 1', (profile_id,))
    row = cur.fetchone()
    if row is None:
        return None
    return {'dataset_id': row[0], 'data_checksum': row[1], 'column_structure': row[2]}


def _dataset_id_moi(con, profile_id):
    n = con.execute('SELECT COUNT(*) FROM dataset WHERE profile_id=?', (profile_id,)).fetchone()[0]
    return f'ds_{profile_id}_{n + 1:03d}'


class CanhBaoDatasetDoi(Exception):
    def __init__(self, profile_id, dataset_cu, row_count_moi):
        self.profile_id = profile_id
        self.dataset_cu = dataset_cu
        self.row_count_moi = row_count_moi
        super().__init__(
            f'Dataset của "{profile_id}" đã đổi so với dataset_id={dataset_cu["dataset_id"]} '
            f'(data_checksum khác). Cần xác nhận (confirm_new_dataset=True) trước khi tạo '
            f'dataset_id mới.')


class CanhBaoCauTrucDoi(Exception):
    """Ver 4.5.1 — nói RÕ cột nào thêm/bớt, và có đường đi tiếp.

    Trước 4.5.1 exception này là ngõ cụt: thêm một cột hợp lệ vào profile là
    vĩnh viễn không import lại được (không có cờ bỏ qua). Sự cố 17/08/2026:
    thêm 'Hậu tố slug' + 'Slug chỉ định' -> sheet 03 bị chặn im, tool vẫn chạy
    dataset cũ 245 dòng mà giao diện không báo gì dễ thấy.
    """

    def __init__(self, profile_id, dataset_cu, cot_cu=None, cot_moi=None):
        self.profile_id = profile_id
        self.dataset_cu = dataset_cu
        self.cot_cu = list(cot_cu or [])
        self.cot_moi = list(cot_moi or [])
        self.them = [c for c in self.cot_moi if c not in self.cot_cu]
        self.bot = [c for c in self.cot_cu if c not in self.cot_moi]
        ct = []
        if self.them:
            ct.append('THÊM: ' + ', '.join(self.them))
        if self.bot:
            ct.append('BỚT: ' + ', '.join(self.bot))
        super().__init__(
            f'Cấu trúc cột của "{profile_id}" đã đổi so với dataset_id='
            f'{dataset_cu["dataset_id"]}. ' + ('; '.join(ct) + '. ' if ct else '') +
            'Chỉ BỚT cột là nguy hiểm (mất dữ liệu). Nếu chỉ THÊM cột thì xác '
            'nhận để tạo dataset mới, bài/WP ID cũ được chuyển sang, không mất.')


def xac_nhan_dataset(con, profile_id, source_file, file_checksum, data_checksum,
                      row_count, column_structure, confirm_new_dataset=False,
                      confirm_doi_cau_truc=False):
    """Trả dataset_id để dùng cho lần import này. Ghi/emit bảng `dataset`.

    Quy tắc (R2-04, kế thừa mục 3.2 kiến trúc):
      - Chưa có dataset nào cho profile -> tạo mới, không cần hỏi.
      - data_checksum giống dataset gần nhất -> dùng lại dataset_id cũ,
        CẬP NHẬT updated_at (đây là lần import lại cùng dataset, R2-03).
      - data_checksum khác, cấu trúc cột giống -> cần confirm_new_dataset=True,
        nếu không thì raise CanhBaoDatasetDoi.
      - Cấu trúc cột khác -> raise CanhBaoCauTrucDoi. Ver 4.5.1: có thể đi
        tiếp bằng confirm_doi_cau_truc=True (tạo dataset MỚI, chuyển bài cũ
        sang, không xoá gì). Vẫn CHẶN CỨNG nếu có cột bị BỚT — mất cột là mất
        dữ liệu, phải sửa profiles.py hoặc file MASTER cho đúng.
    """
    cau_truc_json = json.dumps(column_structure, ensure_ascii=False, sort_keys=True)
    ds_cu = dataset_gan_nhat(con, profile_id)

    if ds_cu is None:
        did = _dataset_id_moi(con, profile_id)
        con.execute(
            'INSERT INTO dataset (dataset_id, profile_id, source_file, file_checksum, '
            'data_checksum, row_count, column_structure, pipeline_version, created_at, updated_at) '
            'VALUES (?,?,?,?,?,?,?,?,?,?)',
            (did, profile_id, source_file, file_checksum, data_checksum, row_count,
             cau_truc_json, PIPELINE_VERSION, _now(), _now()))
        con.commit()
        return did, 'moi'

    if data_checksum == ds_cu['data_checksum']:
        con.execute('UPDATE dataset SET updated_at=?, row_count=?, source_file=? '
                    'WHERE dataset_id=?', (_now(), row_count, source_file, ds_cu['dataset_id']))
        con.commit()
        return ds_cu['dataset_id'], 'giong_het_import_lai'

    if cau_truc_json != ds_cu['column_structure']:
        try:
            cot_cu = json.loads(ds_cu['column_structure'])
        except Exception:
            cot_cu = []
        e = CanhBaoCauTrucDoi(profile_id, ds_cu, cot_cu, column_structure)
        # Bớt cột = mất dữ liệu -> KHÔNG có đường đi tiếp, kể cả có cờ.
        if e.bot or not confirm_doi_cau_truc:
            raise e
        confirm_new_dataset = True   # chỉ thêm cột + đã xác nhận -> dataset mới

    if not confirm_new_dataset:
        raise CanhBaoDatasetDoi(profile_id, ds_cu, row_count)

    did = _dataset_id_moi(con, profile_id)
    # Ver 3.9 — `active` là phiên bản hiện hành: dataset_gan_nhat() và
    # liet_ke_dataset() đều lọc active=1. Khi người dùng đã xác nhận tạo
    # version mới, tắt version cũ nhưng KHÔNG xoá lịch sử/bài đã đăng.
    con.execute('UPDATE dataset SET active=0 WHERE profile_id=? AND active=1', (profile_id,))
    con.execute(
        'INSERT INTO dataset (dataset_id, profile_id, source_file, file_checksum, '
        'data_checksum, row_count, column_structure, pipeline_version, created_at, updated_at) '
        'VALUES (?,?,?,?,?,?,?,?,?,?)',
        (did, profile_id, source_file, file_checksum, data_checksum, row_count,
         cau_truc_json, PIPELINE_VERSION, _now(), _now()))
    con.commit()
    return did, 'moi_da_xac_nhan'


def chuyen_bai_sang_dataset_moi(con, profile_id, dataset_moi, dataset_cu=None):
    """Ver 4.4.1.7 — chuyển bài ĐÃ ĐĂNG sang dataset vừa tạo.

    VÌ SAO CẦN
        `xac_nhan_dataset()` tắt active của dataset cũ rồi tạo dataset mới,
        nhưng `bai_viet_phase2` và `article_jobs` vẫn trỏ dataset CŨ.
        `dashboard()` JOIN theo dataset_id nên trả rỗng -> site/mau/wp_id
        thành None -> mọi chức năng cần identity đều chết, và KHÔNG có
        cảnh báo nào. App chạy êm ru, chỉ lộ ra khi bấm đúng một nút.
        Sự cố thật 13/08/2026: 245 bài mồ côi, mất nửa ngày mới truy ra.

    VÌ SAO CHUYỂN ĐƯỢC
        record_id = profile::sheet::dòng::sku, KHÔNG chứa dataset_id.
        Nên phần lớn record giữ nguyên định danh qua các lần import; chỉ
        record nào bị sửa SKU hoặc đổi số dòng mới lệch.

    GỌI SAU `ghi_san_pham()` — trước đó dataset mới chưa có sản phẩm nào
    để đối chiếu record_id.

    AN TOÀN
        - CHỈ chuyển record_id CÓ trong san_pham_phase2 của dataset mới
          (không vi phạm khoá ngoại).
        - Record không khớp: ĐỂ NGUYÊN, không xoá, báo cáo ra ngoài.
        - Trùng khoá chính ở dataset mới: bỏ qua, báo cáo. Không ghi đè.
        - Chạy lại lần hai không làm gì thêm.

    Trả dict báo cáo, KHÔNG raise — import không được chết vì bước này.
    """
    bc = {'dataset_cu': None, 'dataset_moi': dataset_moi, 'bai_chuyen': 0,
          'job_chuyen': 0, 'mo_coi': [], 'trung_khoa': [], 'loi': ''}
    try:
        if dataset_cu is None:
            cur = con.execute(
                'SELECT dataset_id FROM dataset WHERE profile_id=? AND dataset_id<>? '
                'AND active=0 ORDER BY created_at DESC, rowid DESC LIMIT 1',
                (profile_id, dataset_moi))
            row = cur.fetchone()
            if row is None:
                return bc
            dataset_cu = row[0]
        bc['dataset_cu'] = dataset_cu

        rid_moi = {r[0] for r in con.execute(
            'SELECT record_id FROM san_pham_phase2 WHERE dataset_id=?', (dataset_moi,))}
        if not rid_moi:
            bc['loi'] = 'Dataset mới chưa có sản phẩm — gọi sai thứ tự.'
            return bc

        # Khoá chính bai_viet_phase2 = (dataset_id, record_id, site, mau).
        # Dataset mới đã có đúng bộ đó thì UPDATE sẽ vi phạm UNIQUE.
        da_co = {(r[0], r[1], r[2]) for r in con.execute(
            'SELECT record_id, site, mau FROM bai_viet_phase2 WHERE dataset_id=?',
            (dataset_moi,))}

        can_chuyen, mo_coi, trung = [], [], []
        for rid, site, mau, wp in con.execute(
                'SELECT record_id, site, mau, wp_id FROM bai_viet_phase2 '
                'WHERE dataset_id=?', (dataset_cu,)):
            if rid not in rid_moi:
                mo_coi.append({'record_id': rid, 'wp_id': wp})
            elif (rid, site, mau) in da_co:
                trung.append({'record_id': rid, 'wp_id': wp})
            else:
                can_chuyen.append((rid, site, mau))

        for rid, site, mau in can_chuyen:
            con.execute(
                'UPDATE bai_viet_phase2 SET dataset_id=? '
                'WHERE dataset_id=? AND record_id=? AND site=? AND mau=?',
                (dataset_moi, dataset_cu, rid, site, mau))
        bc['bai_chuyen'] = len(can_chuyen)

        n_job = con.execute(
            'UPDATE article_jobs SET dataset_id=? WHERE dataset_id=? AND record_id IN '
            '(SELECT record_id FROM san_pham_phase2 WHERE dataset_id=?)',
            (dataset_moi, dataset_cu, dataset_moi)).rowcount
        bc['job_chuyen'] = max(0, n_job or 0)
        bc['mo_coi'] = mo_coi
        bc['trung_khoa'] = trung
        con.commit()
    except Exception as e:
        try:
            con.rollback()
        except Exception:
            pass
        bc['loi'] = f'{type(e).__name__}: {e}'
    return bc


def lay_dataset(con, dataset_id):
    cur = con.execute(
        'SELECT dataset_id, profile_id, source_file, file_checksum, data_checksum, row_count, '
        'column_structure, pipeline_version, created_at, updated_at FROM dataset WHERE dataset_id=?',
        (dataset_id,))
    row = cur.fetchone()
    if row is None:
        return None
    cols = ['dataset_id', 'profile_id', 'source_file', 'file_checksum', 'data_checksum',
            'row_count', 'column_structure', 'pipeline_version', 'created_at', 'updated_at']
    return dict(zip(cols, row))


def liet_ke_dataset(con, profile_id=None):
    sql = 'SELECT dataset_id, profile_id, row_count, created_at, updated_at FROM dataset WHERE active=1'
    args = []
    if profile_id:
        sql += ' AND profile_id=?'
        args.append(profile_id)
    sql += ' ORDER BY rowid DESC'
    cur = con.execute(sql, args)
    cols = ['dataset_id', 'profile_id', 'row_count', 'created_at', 'updated_at']
    return [dict(zip(cols, r)) for r in cur.fetchall()]


# ============================================================ san_pham_phase2 (R2-03: UPSERT)
def ghi_san_pham(con, dataset_id, rows):
    """UPSERT — không dùng INSERT OR IGNORE mù quáng. Record đã có (cùng
    dataset_id, record_id) thì CẬP NHẬT du_lieu_json/profile_id/outline_id/
    content_type/pipeline_version, GIỮ NGUYÊN selected (không nằm trong SET
    nên SQLite tự không đụng tới)."""
    for r in rows:
        con.execute(
            '''INSERT INTO san_pham_phase2
               (dataset_id, record_id, profile_id, outline_id, content_type, du_lieu_json,
                selected, pipeline_version)
               VALUES (?,?,?,?,?,?,0,?)
               ON CONFLICT(dataset_id, record_id) DO UPDATE SET
                   profile_id=excluded.profile_id,
                   outline_id=excluded.outline_id,
                   content_type=excluded.content_type,
                   du_lieu_json=excluded.du_lieu_json,
                   pipeline_version=excluded.pipeline_version''',
            (dataset_id, r['record_id'], r['profile_id'], r['outline_id'], r['content_type'],
             json.dumps(r, ensure_ascii=False), PIPELINE_VERSION))
    con.commit()


def dat_chon(con, dataset_id, record_ids, chon=True):
    con.executemany(
        'UPDATE san_pham_phase2 SET selected=? WHERE dataset_id=? AND record_id=?',
        [(1 if chon else 0, dataset_id, rid) for rid in record_ids])
    con.commit()


def lay_san_pham(con, dataset_id, record_id):
    cur = con.execute(
        'SELECT dataset_id, record_id, profile_id, outline_id, content_type, du_lieu_json, '
        'selected, pipeline_version FROM san_pham_phase2 WHERE dataset_id=? AND record_id=?',
        (dataset_id, record_id))
    row = cur.fetchone()
    if row is None:
        return None
    return _row_san_pham(row)


def _row_san_pham(row):
    d = json.loads(row[5])
    d['dataset_id'], d['selected'] = row[0], bool(row[6])
    return d


def liet_ke_san_pham(con, dataset_id=None, profile_id=None, outline_id=None, chi_da_chon=False):
    sql = ('SELECT dataset_id, record_id, profile_id, outline_id, content_type, du_lieu_json, '
           'selected, pipeline_version FROM san_pham_phase2 WHERE 1=1')
    args = []
    for cot, gia_tri in [('dataset_id', dataset_id), ('profile_id', profile_id),
                          ('outline_id', outline_id)]:
        if gia_tri:
            sql += f' AND {cot}=?'
            args.append(gia_tri)
    if chi_da_chon:
        sql += ' AND selected=1'
    cur = con.execute(sql, args)
    return [_row_san_pham(r) for r in cur.fetchall()]


def dem_san_pham(con, dataset_id=None, profile_id=None):
    sql = 'SELECT COUNT(*) FROM san_pham_phase2 WHERE 1=1'
    args = []
    if dataset_id:
        sql += ' AND dataset_id=?'
        args.append(dataset_id)
    if profile_id:
        sql += ' AND profile_id=?'
        args.append(profile_id)
    return con.execute(sql, args).fetchone()[0]


# ============================================================ bai_viet_phase2
def upsert_bai_viet_khoi_tao(con, dataset_id, record_id, site, mau):
    """Tạo dòng bai_viet_phase2 ở trạng thái 'chua_sinh' nếu CHƯA có — không
    đụng nếu đã có (INSERT OR IGNORE ở đây là ĐÚNG, vì mục đích chỉ là đảm
    bảo tồn tại 1 dòng khung để cập nhật dần, khác với UPSERT ghi đè nội dung
    của san_pham_phase2)."""
    con.execute(
        'INSERT OR IGNORE INTO bai_viet_phase2 (dataset_id, record_id, site, mau, trang_thai) '
        'VALUES (?,?,?,?,\'chua_sinh\')', (dataset_id, record_id, site, mau))
    con.commit()


def cap_nhat_bai_viet(con, dataset_id, record_id, site, mau, **truong):
    """Cập nhật CHÍNH XÁC 1 bài — luôn khớp đủ 4 phần khoá, không suy diễn.
    Field cho phép: slug, title, meta_description, html, trang_thai, loi,
    wp_id, wp_url, ngay_dang, thoi_luong_giay."""
    cho_phep = {'slug', 'title', 'meta_description', 'html', 'trang_thai', 'loi',
                'wp_id', 'wp_url', 'ngay_dang', 'thoi_luong_giay'}
    truong = {k: v for k, v in truong.items() if k in cho_phep}
    if not truong:
        return False
    upsert_bai_viet_khoi_tao(con, dataset_id, record_id, site, mau)
    set_sql = ', '.join(f'{k}=?' for k in truong)
    con.execute(
        f'UPDATE bai_viet_phase2 SET {set_sql} '
        'WHERE dataset_id=? AND record_id=? AND site=? AND mau=?',
        list(truong.values()) + [dataset_id, record_id, site, mau])
    con.commit()
    return True


def don_bai_viet_mock(con):
    """Ver 4.3 hotfix: xoá CHỈ state Mock đã lỡ ghi vào bảng production.
    Nhận diện bằng wp_url chứa '.mock'; không đụng san_pham_phase2 hay bài thật.
    Trả số dòng đã xoá.
    """
    cur = con.execute(
        "DELETE FROM bai_viet_phase2 WHERE instr(lower(COALESCE(wp_url,'')), '.mock') > 0")
    con.commit()
    return max(0, int(cur.rowcount or 0))


def lay_bai_viet(con, dataset_id, record_id, site, mau):
    cur = con.execute(
        'SELECT dataset_id, record_id, site, mau, slug, title, meta_description, html, '
        'trang_thai, loi, wp_id, wp_url, ngay_dang, thoi_luong_giay FROM bai_viet_phase2 '
        'WHERE dataset_id=? AND record_id=? AND site=? AND mau=?',
        (dataset_id, record_id, site, mau))
    row = cur.fetchone()
    if row is None:
        return None
    return _row_bai_viet(row)


def _row_bai_viet(row):
    cols = ['dataset_id', 'record_id', 'site', 'mau', 'slug', 'title', 'meta_description',
            'html', 'trang_thai', 'loi', 'wp_id', 'wp_url', 'ngay_dang', 'thoi_luong_giay']
    return dict(zip(cols, row))


def doi_khoa_site(con, site_cu, site_moi):
    """Ver 3.5 — Task idempotency: đổi khoá `site` từ giá trị CŨ (VD tên
    hiển thị 3.4 trước đây) sang khoá MỚI (URL chuẩn hoá), GIỮ NGUYÊN
    wp_id/wp_url/trang_thai/ngay_dang/thoi_luong_giay — chỉ UPDATE 1 cột,
    không xoá-tạo-lại dòng nào. Bỏ qua êm nếu site_cu không có dòng nào
    (không phải lỗi — đa số trường hợp chưa từng đăng gì dưới khoá cũ).

    Nếu site_moi đã có sẵn 1 dòng trùng khoá (dataset_id, record_id,
    site_moi, mau) — giữ nguyên dòng site_moi đã có (coi là dữ liệu mới hơn,
    không ghi đè), KHÔNG xoá dòng site_cu (để không mất dấu vết, người dùng
    tự kiểm tra tay nếu cần).

    Trả số dòng đã đổi khoá thành công.
    """
    if not site_cu or not site_moi or site_cu == site_moi:
        return 0
    cur = con.execute('SELECT dataset_id, record_id, mau FROM bai_viet_phase2 WHERE site=?',
                      (site_cu,))
    hang_can_doi = cur.fetchall()
    da_doi = 0
    for dataset_id, record_id, mau in hang_can_doi:
        da_co = con.execute(
            'SELECT 1 FROM bai_viet_phase2 WHERE dataset_id=? AND record_id=? AND site=? AND mau=?',
            (dataset_id, record_id, site_moi, mau)).fetchone()
        if da_co:
            continue   # site_moi đã có dữ liệu riêng, không ghi đè, không xoá site_cu
        con.execute(
            'UPDATE bai_viet_phase2 SET site=? WHERE dataset_id=? AND record_id=? AND site=? AND mau=?',
            (site_moi, dataset_id, record_id, site_cu, mau))
        da_doi += 1
    con.commit()
    return da_doi


def liet_ke_site_dang_dung(con):
    """Toàn bộ giá trị `site` khác nhau đang có trong bai_viet_phase2 — dùng
    để phát hiện dữ liệu cũ còn khoá theo tên hiển thị (trước Ver 3.5) cần
    di chuyển sang khoá URL chuẩn hoá."""
    cur = con.execute('SELECT DISTINCT site FROM bai_viet_phase2')
    return [r[0] for r in cur.fetchall()]


# ============================================================ định dạng hiển thị dùng chung (Ver 3.5)
# Trích từ giao-dien.py — KHÔNG phụ thuộc Tkinter, để cả GUI lẫn công cụ
# dòng lệnh (cong_cu_kiem_tra_ket_qua.py, gọi qua 5-KIEM-TRA-KET-QUA.bat)
# dùng CHUNG, không viết 2 bản logic định dạng khác nhau cho cùng 1 dữ liệu.
def dinh_dang_thoi_gian(iso_hoac_rong):
    """Hiển thị 'dd/mm HH:MM' (VD '25/07 10:51') — lưu trong DB vẫn là ISO
    UTC đầy đủ (không đổi định dạng lưu trữ, chỉ đổi cách HIỂN THỊ). Đổi
    sang giờ địa phương máy đang chạy."""
    if not iso_hoac_rong:
        return ''
    try:
        dt = datetime.fromisoformat(iso_hoac_rong)
        return dt.astimezone().strftime('%d/%m %H:%M')
    except Exception:
        return iso_hoac_rong


def dinh_dang_thoi_luong(giay):
    """Hiển thị 'HH:MM:SS' (VD '00:01:24')."""
    if giay is None:
        return ''
    try:
        giay = int(round(float(giay)))
        gio, du = divmod(giay, 3600)
        phut, giay = divmod(du, 60)
        return f'{gio:02d}:{phut:02d}:{giay:02d}'
    except Exception:
        return ''


def dashboard(con, dataset_id=None, site=None, profile_id=None, trang_thai=None):
    """Join san_pham_phase2 + bai_viet_phase2 để dashboard lọc theo dataset,
    site, profile, trạng thái cùng lúc (R2-10)."""
    sql = ('SELECT bv.dataset_id, bv.record_id, sp.profile_id, sp.outline_id, sp.content_type, '
           'bv.site, bv.mau, bv.trang_thai, bv.wp_id, bv.wp_url, bv.ngay_dang, bv.thoi_luong_giay '
           'FROM bai_viet_phase2 bv JOIN san_pham_phase2 sp '
           'ON bv.dataset_id=sp.dataset_id AND bv.record_id=sp.record_id WHERE 1=1')
    args = []
    for cot, gia_tri, bang in [('dataset_id', dataset_id, 'bv'), ('site', site, 'bv'),
                                ('profile_id', profile_id, 'sp'), ('trang_thai', trang_thai, 'bv')]:
        if gia_tri:
            sql += f' AND {bang}.{cot}=?'
            args.append(gia_tri)
    cur = con.execute(sql, args)
    cols = ['dataset_id', 'record_id', 'profile_id', 'outline_id', 'content_type',
            'site', 'mau', 'trang_thai', 'wp_id', 'wp_url', 'ngay_dang', 'thoi_luong_giay']
    return [dict(zip(cols, r)) for r in cur.fetchall()]


# ============================================================ Ver 3.9 — article_jobs
_JOB_COT = ['job_id', 'dataset_id', 'record_id', 'site', 'mau', 'outline_id', 'sequence',
           'trang_thai', 'slug', 'title', 'meta_description', 'html', 'wp_id', 'wp_url',
           'loi', 'thoi_luong_giay', 'ngay_dang']


def _row_job(row):
    return dict(zip(_JOB_COT, row))


_RE_CONG_SUAT_TRONG_TEN = re.compile(r'\d+(?:[.,]\d+)?\s*kva', re.IGNORECASE)


def _ho_may_bien_ap(ten_goc):
    """Ver 4.9.8 — khoá 'họ sản phẩm' để nhóm các SKU CÙNG DÒNG, khác công
    suất: thay số+KVA trong Tên hàng bằng token cố định rồi chuẩn hoá
    khoảng trắng/chữ hoa-thường. VD 'Máy biến áp dầu 3Pha 250KVA
    22/0.4KV Loại Amorphous...' và '...320KVA...' cùng ra 1 khoá — đúng vì
    đây LÀ cùng 1 dòng sản phẩm, chỉ khác mức công suất."""
    if not ten_goc:
        return ''
    t = _RE_CONG_SUAT_TRONG_TEN.sub('#KVA', ten_goc.lower())
    return re.sub(r'\s+', ' ', t).strip()


def _so_kva(cong_suat):
    """Ép cong_suat về float để sort.

    Ver 2.2 — VÁ BUG ẨN NGHIÊM TRỌNG: bản cũ chỉ làm float(str) trần, nên
    với dữ liệu THẬT trong MASTER ('15 kVA', '250 kVA' — CÓ đơn vị) nó trả
    None cho MỌI SKU. Hệ quả: bảng "So sánh công suất trong dòng" chưa bao
    giờ thực sự được sắp xếp theo công suất — mọi record rơi vào nhánh
    "None -> đẩy xuống cuối", giữ nguyên thứ tự đọc từ DB. Triệu chứng bị
    CHE vì thứ tự trong file Excel vốn đã tăng dần sẵn, nhìn ngoài tưởng
    sort đúng. Phát hiện khi test khử trùng mức công suất (Ver 2.2).

    Giờ bóc số đầu tiên trong chuỗi, chấp nhận cả '250', '250 kVA',
    '37.5kVA', '1.000 kVA'. Không parse được -> None (giữ hành vi cũ)."""
    if cong_suat is None:
        return None
    m = re.search(r'\d+(?:[.,]\d+)?', str(cong_suat).replace('.', '', 0))
    if not m:
        return None
    try:
        return float(m.group(0).replace(',', '.'))
    except ValueError:
        return None


_OUTLINE_CO_SO_SANH_CONG_SUAT = ('outline_may_bien_ap', 'outline_vo_may_bien_ap')


def tim_san_pham_cung_dong(con, dataset_id, record_id, site=None, gioi_han=6):
    """Ver 4.9.8 — tìm các SKU máy biến áp CÙNG DÒNG (cùng Tên hàng sau khi
    bỏ số công suất), KHÁC mức công suất, để dựng bảng so sánh công suất
    (khoi_so_sanh_cong_suat, render_phase2.py).

    Ver 5.2 — VÁ: trước đây CHỈ áp dụng outline_may_bien_ap. Từ khi tách
    outline_vo_may_bien_ap riêng cho "Vỏ mạ kẽm..." (không phải máy biến
    áp), hàm này PHẢI nhận CẢ 2 outline — nhưng LUÔN so sánh trong CÙNG 1
    outline với record đang xét (JOIN thêm điều kiện outline_id = outline
    của chính sp), để KHÔNG bao giờ đem 1 cái vỏ đi so công suất với 1
    máy biến áp thật (2 bản chất khác nhau, so sánh chéo vô nghĩa).

    Ver 5.0 — VÁ theo Thịnh xem thật thấy "mã hàng ai biết" (không có ý
    nghĩa với khách nếu không bấm được): thêm tham số `site` (optional,
    None = giữ hành vi cũ Ver 4.9.8, không có url). Có `site` -> JOIN với
    bai_viet_phase2 (cùng logic tim_san_pham_lien_quan) để lấy 'url' cho
    SKU anh em ĐÃ ĐĂNG THẬT ở ĐÚNG site đó — SKU chưa đăng vẫn hiện trong
    bảng (để so sánh số liệu) nhưng KHÔNG có url (không bịa link chết).

    Trả list[{'ma_goc','ten_goc','cong_suat','cap_dien_ap','url'}] — thêm
    'ten_goc' Ver 5.2 (Thịnh: "mã hàng ai biết đâu, phải nhập tên sản
    phẩm") để bảng so sánh hiện TÊN thay vì mã trơ trọi. (key 'url' luôn
    có mặt, giá trị '' nếu chưa đăng/không truyền site) đã sort theo công
    suất tăng dần, rỗng nếu record hiện tại không cùng dataset/không phải
    máy biến áp/vỏ máy biến áp, hoặc không tìm được SKU anh em nào."""
    sp = lay_san_pham(con, dataset_id, record_id)
    if sp is None or sp.get('outline_id') not in _OUTLINE_CO_SO_SANH_CONG_SUAT:
        return []
    outline_hien_tai = sp['outline_id']
    ho = _ho_may_bien_ap(sp.get('ten_goc', ''))
    if not ho:
        return []

    url_theo_record = {}
    if site:
        cur_url = con.execute(
            "SELECT record_id, wp_url FROM bai_viet_phase2 "
            "WHERE dataset_id = ? AND site = ? AND trang_thai = 'da_dang' "
            "AND wp_url IS NOT NULL AND wp_url != ''",
            (dataset_id, site))
        url_theo_record = dict(cur_url.fetchall())

    cur = con.execute(
        "SELECT du_lieu_json FROM san_pham_phase2 "
        "WHERE dataset_id = ? AND outline_id = ?",
        (dataset_id, outline_hien_tai))
    ung_vien = []
    for (dlj,) in cur.fetchall():
        try:
            r = json.loads(dlj)
        except (json.JSONDecodeError, TypeError):
            continue
        if r.get('record_id') == record_id:
            continue
        if _ho_may_bien_ap(r.get('ten_goc', '')) != ho:
            continue
        ung_vien.append({'ma_goc': r.get('ma_goc', ''), 'ten_goc': r.get('ten_goc', ''),
                         'cong_suat': r.get('cong_suat', ''),
                         'cap_dien_ap': r.get('cap_dien_ap', ''),
                         'url': url_theo_record.get(r.get('record_id'), '')})

    if not ung_vien:
        return []
    ung_vien.sort(key=lambda x: (_so_kva(x['cong_suat']) is None, _so_kva(x['cong_suat']) or 0))

    # Ver 2.2 — KHỬ TRÙNG THEO MỨC CÔNG SUẤT. Bug thật phát hiện khi Thịnh
    # xem trang đã đăng: bảng hiện 100 / 100 / 160 / 160 / 250 / 250 —
    # trùng đôi, vì nhiều SKU khác nhau (khác tiêu chuẩn EVN, khác mã QĐ)
    # có CÙNG mức kVA. Bảng này để so sánh giữa các MỨC công suất, hiện
    # trùng số làm nó vô dụng và trông như lỗi dữ liệu.
    #
    # Giữ 1 đại diện cho mỗi mức kVA, ưu tiên SKU ĐÃ ĐĂNG (có url) để bảng
    # bấm được — SKU chưa đăng chỉ dùng khi mức đó chưa có ai đăng.
    # Ver 2.7 — LOẠI mức kVA TRÙNG với chính record đang xem (bản đối chiếu
    # + Gemini cùng chỉ ra trên bài thật: bảng hiện "100 (đang xem)" rồi
    # ngay dưới lại "100"). Ver 2.2 mới khử trùng GIỮA các ứng viên, quên
    # so với record hiện tại.
    kva_dang_xem = _so_kva(sp.get("cong_suat")) if sp else None
    if kva_dang_xem is not None:
        ung_vien = [uv for uv in ung_vien if _so_kva(uv['cong_suat']) != kva_dang_xem]

    tot_nhat_theo_kva = {}
    for uv in ung_vien:
        kva = _so_kva(uv['cong_suat'])
        khoa = kva if kva is not None else f"_khong_so_{uv['ma_goc']}"
        cu = tot_nhat_theo_kva.get(khoa)
        if cu is None or (not cu.get('url') and uv.get('url')):
            tot_nhat_theo_kva[khoa] = uv
    da_khu_trung = sorted(
        tot_nhat_theo_kva.values(),
        key=lambda x: (_so_kva(x['cong_suat']) is None, _so_kva(x['cong_suat']) or 0))

    # Ver 3.6.4 — LẤY CÂN HAI PHÍA quanh mức đang xem, thay vì cắt 6 cái
    # đầu. Bug thật thấy trên bài KP 800kVA: bảng chỉ liệt kê 160-500 trong
    # khi mục sản phẩm liên quan ngay dưới có 1000-2000. Vì danh sách sort
    # tăng dần rồi `[:6]` nên SKU công suất lớn LUÔN chỉ thấy mức nhỏ hơn
    # mình — bảng so sánh mất một nửa ý nghĩa.
    if kva_dang_xem is None:
        return da_khu_trung[:gioi_han]
    duoi = [x for x in da_khu_trung
            if (_so_kva(x['cong_suat']) or 0) < kva_dang_xem]
    tren = [x for x in da_khu_trung
            if (_so_kva(x['cong_suat']) or 0) > kva_dang_xem]
    nua = gioi_han // 2
    # thiếu bên nào thì bù bằng bên kia, để luôn đủ `gioi_han` dòng
    lay_duoi = duoi[-min(nua, len(duoi)):] if duoi else []
    lay_tren = tren[:gioi_han - len(lay_duoi)]
    if len(lay_duoi) + len(lay_tren) < gioi_han and duoi:
        thieu = gioi_han - len(lay_duoi) - len(lay_tren)
        lay_duoi = duoi[-min(len(lay_duoi) + thieu, len(duoi)):]
    return sorted(lay_duoi + lay_tren,
                  key=lambda x: (_so_kva(x['cong_suat']) is None,
                                 _so_kva(x['cong_suat']) or 0))


def tim_san_pham_lien_quan(con, dataset_id, record_id, site, gioi_han=5):
    """Ver 4.5.1 — vá theo GPT review độc lập (5 điểm, xem CHANGELOG-VER46):

    P0: Đọc CẢ 2 nguồn bài đã đăng thật — `bai_viet_phase2` (luồng record)
    VÀ `article_jobs` (luồng job, CHỈ `trang_thai='SUCCESS'`). Trước đây
    chỉ đọc `bai_viet_phase2` nên bài đăng qua Article Jobs không bao giờ
    được gợi ý. Canonical khi 1 record có URL ở CẢ 2 nguồn: ưu tiên
    `bai_viet_phase2`; nếu chỉ có ở `article_jobs`, lấy job `sequence`
    NHỎ NHẤT.

    P1: Thêm tham số `site` bắt buộc — CHỈ trả URL thuộc ĐÚNG site đang
    đăng, tránh lẫn URL site khác khi 1 record đăng nhiều site.

    P1: CHỈ trả ứng viên điểm > 0 (cùng cấp điện áp: +2, cùng thương hiệu:
    +1), bắt buộc CÙNG `content_type`. Sort ổn định khi bằng điểm (theo
    tên rồi record_id).

    Trả list [{'ten':..., 'url':...}], rỗng nếu chưa có ứng viên đạt điều
    kiện — an toàn, không hiện block."""
    sp = lay_san_pham(con, dataset_id, record_id)
    if sp is None:
        return []
    profile_id = sp.get('profile_id')
    content_type = sp.get('content_type')
    cap = sp.get('cap_dien_ap')
    hang = sp.get('thuong_hieu')

    theo_record = {}   # record_id -> wp_url, nguồn bai_viet_phase2 ưu tiên
    cur = con.execute(
        'SELECT DISTINCT sp2.record_id, bv.wp_url '
        'FROM san_pham_phase2 sp2 '
        'JOIN bai_viet_phase2 bv ON bv.dataset_id = sp2.dataset_id AND bv.record_id = sp2.record_id '
        'WHERE sp2.dataset_id = ? AND sp2.profile_id = ? AND sp2.content_type = ? AND sp2.record_id != ? '
        "AND bv.site = ? AND bv.trang_thai = 'da_dang' AND bv.wp_url IS NOT NULL AND bv.wp_url != ''",
        (dataset_id, profile_id, content_type, record_id, site))
    for rid, wp_url in cur.fetchall():
        theo_record.setdefault(rid, wp_url)

    cur2 = con.execute(
        'SELECT DISTINCT sp2.record_id, aj.wp_url, aj.sequence '
        'FROM san_pham_phase2 sp2 '
        'JOIN article_jobs aj ON aj.dataset_id = sp2.dataset_id AND aj.record_id = sp2.record_id '
        'WHERE sp2.dataset_id = ? AND sp2.profile_id = ? AND sp2.content_type = ? AND sp2.record_id != ? '
        "AND aj.site = ? AND aj.trang_thai = 'SUCCESS' AND aj.wp_url IS NOT NULL AND aj.wp_url != ''",
        (dataset_id, profile_id, content_type, record_id, site))
    job_theo_record = {}
    for rid, wp_url, seq in cur2.fetchall():
        if rid in theo_record:
            continue
        if rid not in job_theo_record or seq < job_theo_record[rid][1]:
            job_theo_record[rid] = (wp_url, seq)
    for rid, (wp_url, _seq) in job_theo_record.items():
        theo_record[rid] = wp_url

    ung_vien = []
    for rid, wp_url in theo_record.items():
        sp2 = lay_san_pham(con, dataset_id, rid)
        if sp2 is None:
            continue
        diem = 0
        if cap and sp2.get('cap_dien_ap') == cap:
            diem += 2
        if hang and sp2.get('thuong_hieu') == hang:
            diem += 1
        if diem <= 0:
            continue
        ten = sp2.get('ten_goc', rid)
        ung_vien.append((diem, ten, rid, wp_url))

    ung_vien.sort(key=lambda x: (-x[0], x[1], x[2]))
    return [{'ten': ten, 'url': url} for _, ten, _, url in ung_vien[:gioi_han]]


def tao_job(con, dataset_id, record_id, site, mau, outline_id):
    """Tạo 1 job mới cho (record, site, mau) — sequence tự tăng, KHÔNG bao
    giờ đè job cũ (mỗi lần gọi luôn ra job_id mới). Trả job_id vừa tạo."""
    seq = con.execute(
        'SELECT COALESCE(MAX(sequence), 0) FROM article_jobs '
        'WHERE dataset_id=? AND record_id=? AND site=? AND mau=?',
        (dataset_id, record_id, site, mau)).fetchone()[0] + 1
    job_id = f'{dataset_id}:{record_id}:{site}:{mau}:{seq}'
    now = _now()
    con.execute(
        'INSERT INTO article_jobs (job_id, dataset_id, record_id, site, mau, outline_id, '
        'sequence, trang_thai, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)',
        (job_id, dataset_id, record_id, site, mau, outline_id, seq, 'PENDING', now, now))
    con.commit()
    return job_id


def dam_bao_job_mac_dinh(con, dataset_id, record_ids, site, mau):
    """Ver 3.9 REQ-PLAN-01: mỗi record ĐÃ CHỌN mà CHƯA có job nào (bất kỳ
    trạng thái) cho đúng (site, mau) này -> tạo đúng 1 job mặc định, outline
    lấy từ outline_id đã routing sẵn khi import (san_pham_phase2.outline_id).
    Idempotent — gọi lại nhiều lần trên cùng selection KHÔNG tạo thêm job
    (record đã có job rồi thì bỏ qua, không phải việc của hàm này để thêm
    job thứ 2 — đó là việc của nút '+ Thêm job' làm riêng, có chủ đích).
    Trả danh sách job_id vừa tạo mới (rỗng nếu record nào cũng đã có job)."""
    tao_moi = []
    for rid in record_ids:
        da_co = con.execute(
            'SELECT COUNT(*) FROM article_jobs WHERE dataset_id=? AND record_id=? '
            'AND site=? AND mau=?', (dataset_id, rid, site, mau)).fetchone()[0]
        if da_co:
            continue
        sp = lay_san_pham(con, dataset_id, rid)
        if sp is None:
            continue
        tao_moi.append(tao_job(con, dataset_id, rid, site, mau, sp['outline_id']))
    return tao_moi


def liet_ke_jobs(con, dataset_id=None, record_id=None, site=None, mau=None, trang_thai=None):
    sql = ('SELECT job_id, dataset_id, record_id, site, mau, outline_id, sequence, trang_thai, '
           'slug, title, meta_description, html, wp_id, wp_url, loi, thoi_luong_giay, ngay_dang '
           'FROM article_jobs WHERE 1=1')
    args = []
    for cot, gia_tri in [('dataset_id', dataset_id), ('record_id', record_id),
                          ('site', site), ('mau', mau), ('trang_thai', trang_thai)]:
        if gia_tri:
            sql += f' AND {cot}=?'
            args.append(gia_tri)
    sql += ' ORDER BY record_id, sequence'
    cur = con.execute(sql, args)
    return [_row_job(r) for r in cur.fetchall()]


def lay_job(con, job_id):
    cur = con.execute(
        'SELECT job_id, dataset_id, record_id, site, mau, outline_id, sequence, trang_thai, '
        'slug, title, meta_description, html, wp_id, wp_url, loi, thoi_luong_giay, ngay_dang '
        'FROM article_jobs WHERE job_id=?', (job_id,))
    row = cur.fetchone()
    return _row_job(row) if row else None


def xoa_job(con, job_id):
    """Chỉ xoá được job CHƯA CHẠY (trang_thai='PENDING') — đúng acceptance
    'Nút - xóa job chưa chạy'. Trả True nếu xoá, False nếu job không tồn
    tại hoặc đã chạy rồi (không xoá, không phải lỗi)."""
    row = con.execute('SELECT trang_thai FROM article_jobs WHERE job_id=?', (job_id,)).fetchone()
    if not row or row[0] != 'PENDING':
        return False
    con.execute('DELETE FROM article_jobs WHERE job_id=?', (job_id,))
    con.commit()
    return True


def doi_outline_job(con, job_id, outline_id_moi):
    """Chỉ đổi được outline của job CHƯA CHẠY — job đã SUCCESS/ERROR giữ
    nguyên outline đã dùng để đăng, không sửa ngược lịch sử. Trả True/False."""
    row = con.execute('SELECT trang_thai FROM article_jobs WHERE job_id=?', (job_id,)).fetchone()
    if not row or row[0] != 'PENDING':
        return False
    con.execute('UPDATE article_jobs SET outline_id=?, updated_at=? WHERE job_id=?',
               (outline_id_moi, _now(), job_id))
    con.commit()
    return True


def cap_nhat_job(con, job_id, **truong):
    """Cập nhật kết quả xử lý 1 job — dùng bởi vòng lặp đăng THẬT (giao-dien.py).
    Field cho phép: trang_thai, slug, title, meta_description, html, wp_id,
    wp_url, loi, thoi_luong_giay, ngay_dang."""
    cho_phep = {'trang_thai', 'slug', 'title', 'meta_description', 'html', 'wp_id',
               'wp_url', 'loi', 'thoi_luong_giay', 'ngay_dang'}
    truong = {k: v for k, v in truong.items() if k in cho_phep}
    if not truong:
        return False
    truong['updated_at'] = _now()
    set_sql = ', '.join(f'{k}=?' for k in truong)
    con.execute(f'UPDATE article_jobs SET {set_sql} WHERE job_id=?',
               list(truong.values()) + [job_id])
    con.commit()
    return True


# ============================================================ SONEALEO Ver 1.2 — chống lặp insight Enhance
def chuan_hoa_nhom_khoa(ten_loai_san_pham):
    """Chuẩn hoá tên nhóm để so khớp lịch sử — lower + gộp khoảng trắng
    thừa, KHÔNG đụng dấu tiếng Việt (2 nhóm khác dấu vẫn nên tính khác
    nhau, tránh gộp nhầm 2 loại sản phẩm khác nhau)."""
    return ' '.join((ten_loai_san_pham or '').strip().lower().split())


def lay_lich_su_insight(con, ten_loai_san_pham, gioi_han=30):
    """Trả list các câu insight (mọi truong) đã dùng cho nhóm này ở các
    lần Enhance TRƯỚC — mới nhất trước. Dùng để nhét vào prompt AI dặn
    'đừng lặp lại các ý này' (xem enhance.xay_prompt_insight)."""
    nhom_khoa = chuan_hoa_nhom_khoa(ten_loai_san_pham)
    cur = con.execute(
        'SELECT noi_dung FROM enhance_lich_su_insight WHERE nhom_khoa=? '
        'ORDER BY id DESC LIMIT ?', (nhom_khoa, gioi_han))
    return [r[0] for r in cur.fetchall()]


def ghi_lich_su_insight(con, ten_loai_san_pham, record_id, insight_sach):
    """Lưu lại các ý insight VỪA DÙNG (sau khi đã lọc số + Hard Block, tức
    insight THẬT SỰ chèn vào bài) cho nhóm này, để lần Enhance sau (SKU
    khác cùng nhóm) biết mà tránh lặp. Gọi SAU khi enhance_1_san_pham
    trả ok=True, không gọi nếu Enhance lỗi hoặc bị chặn hoàn toàn."""
    nhom_khoa = chuan_hoa_nhom_khoa(ten_loai_san_pham)
    now = _now()
    hang = []
    for truong, danh_sach in (insight_sach or {}).items():
        for y in danh_sach:
            hang.append((nhom_khoa, truong, y, record_id, now))
    if not hang:
        return 0
    con.executemany(
        'INSERT INTO enhance_lich_su_insight (nhom_khoa, truong, noi_dung, record_id_da_dung, created_at) '
        'VALUES (?, ?, ?, ?, ?)', hang)
    con.commit()
    return len(hang)


# ============================================================ Ver 2.1 — gỡ bài hàng loạt (rollback)
def liet_ke_bai_da_dang(con, dataset_id=None, site=None, mau=None, gioi_han=None):
    """Ver 2.1 — liệt kê bài ĐÃ ĐĂNG THẬT (có wp_id) để phục vụ gỡ hàng
    loạt. Lý do có hàm này: trước Ver 2.1 tool CHỈ biết đăng, không có
    đường lùi — đăng nhầm 400 bài (VD phát hiện dữ liệu nguồn sai như vụ
    165 dòng điện áp) thì phải vào WordPress xoá tay từng bài.

    Trả list dict {dataset_id, record_id, site, mau, wp_id, wp_url, title,
    slug, ngay_dang} — sắp xếp mới nhất trước."""
    sql = ("SELECT dataset_id, record_id, site, mau, wp_id, wp_url, title, slug, ngay_dang "
           "FROM bai_viet_phase2 WHERE trang_thai='da_dang' AND wp_id IS NOT NULL AND wp_id != ''")
    args = []
    for cot, gia_tri in (('dataset_id', dataset_id), ('site', site), ('mau', mau)):
        if gia_tri:
            sql += f' AND {cot}=?'
            args.append(gia_tri)
    sql += ' ORDER BY ngay_dang DESC'
    if gioi_han:
        sql += f' LIMIT {int(gioi_han)}'
    cot_ten = ['dataset_id', 'record_id', 'site', 'mau', 'wp_id', 'wp_url',
               'title', 'slug', 'ngay_dang']
    return [dict(zip(cot_ten, r)) for r in con.execute(sql, args).fetchall()]


def danh_dau_da_go(con, dataset_id, record_id, site, mau, ghi_chu=''):
    """Đánh dấu bài đã bị gỡ khỏi WordPress. GIỮ NGUYÊN wp_id/wp_url (không
    xoá) — để còn truy vết được bài nào từng tồn tại ở đâu, và để nếu khôi
    phục từ Thùng rác WP thì khớp lại được."""
    return cap_nhat_bai_viet(con, dataset_id, record_id, site, mau,
                             trang_thai='da_go', loi=ghi_chu or 'Đã gỡ khỏi WordPress (Ver 2.1)')
