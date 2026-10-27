# -*- coding: utf-8 -*-
"""
SONEALEO Ver 4.2 — chạy TOÀN BỘ test bằng 1 lệnh: `python run_tests.py`

Vấn đề đang sửa (feedback thật, verify bằng tay trước khi viết file này):
mấy file test cũ (VD test_v498_patch.py) tìm fixture MASTER_4_PROFILE_
SAN_PHAM.xlsx SAI đường dẫn (tìm ở gốc thay vì du_lieu_goc/), khi không
thấy thì tự in "THIẾU... bỏ qua" rồi exit(0) — nhìn ngoài giống PASS
nhưng thực ra KHÔNG CHẠY GÌ CẢ. Script này tự phát hiện pattern đó, báo
riêng thành SKIP, không lẫn vào PASS.

Không sửa 33 file test cũ (rủi ro đụng vào test đang chạy đúng) — chỉ
làm 1 lớp điều phối BÊN NGOÀI, gọi từng file bằng subprocess, đọc
output + exit code, phân loại PASS/FAIL/SKIP.

Chạy: python run_tests.py       (không cần xvfb-run thủ công — script
                                  tự phát hiện Xvfb có sẵn không và tự
                                  bọc nếu có, bỏ qua nếu không)
"""
import subprocess
import sys
import os
import shutil
import time
import hashlib
import tempfile
import re
import threading
from pathlib import Path

BASE = Path(__file__).parent
TESTS_DIR = BASE / 'tests'

# Dấu hiệu nhận biết 1 file "bỏ qua vì thiếu fixture" — không phải PASS thật.
# Liệt kê tay từ việc đọc thật output của 33 file (Ver 1.7) — nếu về sau có
# test mới dùng câu khác, thêm vào list này.
DAU_HIEU_SKIP = [
    'THIẾU MASTER', 'THIẾU FILE TEST', 'bỏ qua test này',
    'thiếu MASTER_4_PROFILE_SAN_PHAM.xlsx',
]


def _co_xvfb():
    return shutil.which('xvfb-run') is not None


def _hash_file(duong_dan):
    """Hash file production để chứng minh test runner không sửa/xóa nó."""
    p = Path(duong_dan)
    if not p.exists():
        return '<MISSING>'
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _tao_sandbox_test(thu_muc_tam):
    """Copy code + fixture sang thư mục tạm; tuyệt đối không copy state production."""
    sandbox = Path(thu_muc_tam) / 'Sonealeo-Test-Sandbox'
    shutil.copytree(
        BASE,
        sandbox,
        ignore=shutil.ignore_patterns(
            'cau-hinh.env',
            'phase2-du-lieu.db',
            '__pycache__',
            '*.pyc',
        ),
    )
    return sandbox


def _env_sandbox(sandbox):
    """Ver 4.4.1.6 — CÔ LẬP thư mục dữ liệu cho từng test process.

    Từ 4.4.1.6 `phase2-du-lieu.db` và `cau-hinh.env` nằm ở %APPDATA%\\SONEALEO\\,
    KHÔNG còn nằm cạnh mã nguồn. Nghĩa là copy code sang sandbox tạm KHÔNG
    còn đủ để cách ly: mọi test sẽ trỏ chung vào DB THẬT của người dùng và
    ghi đè lên đó.

    Ép SONEALEO_DATA_DIR về trong sandbox để:
      1. Test không bao giờ chạm DB production.
      2. 4 worker song song không tranh nhau một file SQLite.
    """
    env = dict(os.environ)
    tm = Path(sandbox) / '_du-lieu-test'
    tm.mkdir(parents=True, exist_ok=True)
    env['SONEALEO_DATA_DIR'] = str(tm)
    return env


def _chay_1_file(duong_dan, dung_xvfb):
    lenh = (['xvfb-run', '-a', sys.executable, str(duong_dan)] if dung_xvfb
           else [sys.executable, str(duong_dan)])
    try:
        goc_sandbox = Path(duong_dan).parent.parent
        kq = subprocess.run(lenh, capture_output=True, text=True, timeout=90,
                            cwd=str(goc_sandbox), env=_env_sandbox(goc_sandbox))
        return kq.returncode, kq.stdout + kq.stderr
    except subprocess.TimeoutExpired:
        return -1, '[TIMEOUT sau 90s]'


_IN_LOCK = threading.Lock()

def _log_runner(msg):
    with _IN_LOCK:
        print(msg, flush=True)

def _chay_nhom_test(ten_tests, dung_xvfb):
    """Một worker chạy tuần tự danh sách test, NHƯNG mỗi test có sandbox riêng.

    Ver 4.2: sandbox theo NHÓM làm các test stateful nhìn thấy DB/config/file do
    test trước để lại. Giữ 4 worker song song, chỉ đổi ranh giới isolation về
    đúng từng file test; không giảm test, không đổi regression record.
    """
    ket = {}
    for ten_test in ten_tests:
        _t = time.time()
        _log_runner(f'  [RUN ] {ten_test}')
        with tempfile.TemporaryDirectory(prefix='sonealeo-test-one-') as td:
            _t_copy = time.time()
            sandbox = _tao_sandbox_test(td)
            _log_runner(f'  [COPY] {ten_test} {time.time() - _t_copy:.2f}s')
            _t_exec = time.time()
            ket[ten_test] = _chay_1_file(sandbox / 'tests' / ten_test, dung_xvfb)
            _log_runner(f'  [EXEC] {ten_test} {time.time() - _t_exec:.2f}s exit={ket[ten_test][0]}')
            _log_runner(f'  [CLEAN] {ten_test} begin')
        _log_runner(f'  [DONE] {ten_test} {time.time() - _t:.2f}s exit={ket[ten_test][0]}')
    return ket




def _chay_song_song_main(ten_file, dung_xvfb, so_luong=4):
    """Chạy tối đa ``so_luong`` subprocess cùng lúc, scheduler ở MAIN THREAD.

    Không dùng ThreadPool/ProcessPool để bọc ``subprocess``. Diagnostic Ver 4.2
    đã chứng minh executor wrapper có thể treo dù chính test chạy riêng hoàn tất.
    Output ghi vào file thay vì PIPE để loại deadlock do pipe/backpressure.
    """
    cho = list(ten_file)
    dang_chay = {}
    ket = {}
    while cho or dang_chay:
        while cho and len(dang_chay) < so_luong:
            ten_test = cho.pop(0)
            t0 = time.time()
            _log_runner(f'  [RUN ] {ten_test}')
            td_obj = tempfile.TemporaryDirectory(prefix='sonealeo-test-one-')
            t_copy = time.time()
            sandbox = _tao_sandbox_test(td_obj.name)
            _log_runner(f'  [COPY] {ten_test} {time.time() - t_copy:.2f}s')
            duong_test = sandbox / 'tests' / ten_test
            lenh = (['xvfb-run', '-a', sys.executable, str(duong_test)] if dung_xvfb
                    else [sys.executable, str(duong_test)])
            log_path = Path(td_obj.name) / 'subprocess-output.log'
            log_f = log_path.open('w+', encoding='utf-8')
            p_test = subprocess.Popen(
                lenh, stdout=log_f, stderr=subprocess.STDOUT,
                cwd=str(sandbox), text=True, env=_env_sandbox(sandbox),
            )
            _log_runner(f'  [PID ] {ten_test} pid={p_test.pid}')
            dang_chay[p_test.pid] = {
                'name': ten_test, 'p': p_test, 'td': td_obj, 'log': log_f,
                'start': time.time(), 'all_start': t0,
            }

        time.sleep(0.05)
        for pid, job in list(dang_chay.items()):
            p_test = job['p']
            rc = p_test.poll()
            elapsed = time.time() - job['start']
            timed_out = rc is None and elapsed > 90
            if timed_out:
                p_test.kill()
                try:
                    p_test.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
                rc = -1
            if rc is None:
                continue

            job['log'].flush()
            job['log'].seek(0)
            out = job['log'].read()
            job['log'].close()
            if timed_out:
                out += '\n[TIMEOUT sau 90s]'
            ket[job['name']] = (rc, out)
            _log_runner(f'  [EXEC] {job["name"]} {elapsed:.2f}s exit={rc}')
            _log_runner(f'  [CLEAN] {job["name"]} begin')
            job['td'].cleanup()
            _log_runner(f'  [DONE] {job["name"]} {time.time() - job["all_start"]:.2f}s exit={rc}')
            del dang_chay[pid]
    return ket

def main():
    # Ver 3.9 A3 — chỉ khởi động Xvfb MỘT lần cho cả suite. Trước đây mỗi
    # file test gọi một `xvfb-run`, tốn ~0.5s startup × hàng chục file.
    # Khi đã có DISPLAY (Windows/Linux desktop hoặc lần re-exec dưới đây),
    # subprocess test dùng chung display và vẫn chạy tuần tự trong sandbox.
    if _co_xvfb() and not os.environ.get('SONEALEO_SUITE_XVFB_ONCE'):
        env = dict(os.environ)
        env['SONEALEO_SUITE_XVFB_ONCE'] = '1'
        rc = subprocess.call(['xvfb-run', '-a', sys.executable, str(Path(__file__).resolve())],
                             cwd=str(BASE), env=env)
        raise SystemExit(rc)
    dung_xvfb = False
    production_paths = [BASE / 'cau-hinh.env', BASE / 'phase2-du-lieu.db']
    hash_truoc = {str(p): _hash_file(p) for p in production_paths}
    ket_qua = {'PASS': [], 'FAIL': [], 'SKIP': []}
    t0 = time.time()

    ten_file = sorted(p.name for p in TESTS_DIR.glob('test_*.py'))
    print(f'Tìm thấy {len(ten_file)} file test. DISPLAY: {os.environ.get("DISPLAY", "none")}.', flush=True)
    print('4 worker chạy song song; MỖI file test có sandbox tạm riêng, không copy cau-hinh.env / phase2-du-lieu.db production.\n', flush=True)

    # Ver 4.2: scheduler MAIN THREAD giữ tối đa 4 subprocess song song.
    # Không bọc subprocess trong ThreadPool/ProcessPool: diagnostic đã tái hiện
    # executor hang độc lập với test cụ thể. Mỗi test vẫn có sandbox riêng.
    so_nhom = min(4, max(1, len(ten_file)))
    ket_raw = _chay_song_song_main(ten_file, dung_xvfb, so_luong=so_nhom)

    for ten in ten_file:
        exit_code, out = ket_raw[ten]
        bi_skip = any(dh in out for dh in DAU_HIEU_SKIP)
        co_tong_ket_pass = bool(re.search(
            r'(?im)^\s*(?:\[PASS\]|PASS(?:\b|[:_])|(?:TỔNG|TONG|TOTAL)\b.*\bPASS\b)', out))
        # Ver 5.7 — SỬA FALSE-FAIL THẬT (audit 22/08/2026).
        # Regex trên CHỈ nhận marker dạng "PASS". Test viết bằng unittest in
        # ra "Ran 10 tests in 0.001s / OK" — không có chữ PASS nào — nên bị
        # rơi xuống nhánh else và chấm FAIL dù exit=0 và test đậu sạch.
        # Test viết kiểu bộ đếm sai cũng vậy: "TONG SAI: 0" là ĐẬU nhưng
        # không có chữ PASS. 4 test bị chấm oan trước bản này:
        #     test_v4415_sweep_rac, test_v4416_ux_va_retry,
        #     test_v4417_chuyen_dataset, test_v46_patch
        # Hậu quả thật: bộ test báo 9 FAIL trong khi chỉ có 5 lỗi thật ->
        # người đọc quen với "lúc nào chả đỏ" rồi bỏ qua cả lỗi thật.
        # Nới marker ĐẬU (không đụng marker FAIL, nên không thể làm lọt lỗi):
        #   - unittest:  dòng chỉ có "OK", kèm/không kèm "(skipped=N)"
        #   - unittest:  "Ran N test(s) in ..." + không có FAILED/ERROR
        #   - bộ đếm:    "TONG SAI: 0" / "TỔNG SAI: 0"
        if not co_tong_ket_pass:
            unittest_ok = bool(re.search(r'(?m)^\s*OK\s*(?:\([^)]*\))?\s*$', out))
            unittest_ran = bool(re.search(r'(?im)^\s*Ran\s+\d+\s+tests?\s+in\b', out))
            unittest_hong = bool(re.search(r'(?im)^\s*(?:FAILED\b|ERROR\b)', out))
            dem_sai_0 = bool(re.search(r'(?im)^\s*(?:TỔNG|TONG)\s+SAI\s*[:=]?\s*0\b', out))
            co_tong_ket_pass = bool(
                (unittest_ok and unittest_ran and not unittest_hong) or dem_sai_0)
        # Ver 4.1 BUG-03: exit0 KHÔNG đủ để PASS. Phải có marker PASS thật
        # và không được có marker FAIL với bộ đếm >0 / [FAIL].
        co_fail_marker = bool(re.search(
            r'(?im)^\s*\[FAIL\]|\bFAIL\s*[:=]?\s*[1-9]\d*\b|\bFAIL\s+[1-9]\d*\b', out))
        if exit_code == 77:
            ket_qua['SKIP'].append((ten, out.strip().splitlines()[-1] if out.strip() else 'SKIP exit 77'))
            trang_thai = 'SKIP'
        elif exit_code == 0 and bi_skip and not co_tong_ket_pass:
            ket_qua['SKIP'].append((ten, out.strip().splitlines()[-1] if out.strip() else ''))
            trang_thai = 'SKIP'
        elif exit_code == 0 and co_tong_ket_pass and not co_fail_marker:
            ket_qua['PASS'].append(ten)
            trang_thai = 'PASS'
        else:
            dong_cuoi = out.strip().splitlines()[-3:] if out.strip() else ['(không có output)']
            ket_qua['FAIL'].append((ten, exit_code, dong_cuoi))
            trang_thai = 'FAIL'
        print(f'  [{trang_thai}] {ten}', flush=True)

    hash_sau = {str(p): _hash_file(p) for p in production_paths}
    production_nguyen_ven = hash_truoc == hash_sau
    if production_nguyen_ven:
        print('\n[PASS] TEST-SANDBOX: checksum production env/DB không đổi.')
    else:
        print('\n[FAIL] TEST-SANDBOX: production env/DB đã bị thay đổi.')
        for p in production_paths:
            k = str(p)
            print(f'  {p.name}: before={hash_truoc[k]} after={hash_sau[k]}')
        ket_qua['FAIL'].append(('TEST-SANDBOX', 2, ['checksum production env/DB thay đổi']))

    thoi_gian = time.time() - t0
    print(f'\n{"=" * 60}')
    print(f'PASS:  {len(ket_qua["PASS"])}')
    print(f'FAIL:  {len(ket_qua["FAIL"])}')
    print(f'SKIP:  {len(ket_qua["SKIP"])}  (dependency/fixture hoặc test chủ động SKIP — KHÔNG tính là pass thật)')
    print(f'Thời gian: {thoi_gian:.1f}s')
    print(f'{"=" * 60}')

    if ket_qua['SKIP']:
        print('\n--- Chi tiết SKIP (không tính là PASS) ---')
        for ten, dong in ket_qua['SKIP']:
            print(f'  {ten}: {dong}')

    if ket_qua['FAIL']:
        print('\n--- Chi tiết FAIL ---')
        for ten, code, dong_cuoi in ket_qua['FAIL']:
            print(f'  {ten} (exit={code}):')
            for d in dong_cuoi:
                print(f'      {d}')

    sys.exit(1 if ket_qua['FAIL'] else 0)


if __name__ == '__main__':
    main()
