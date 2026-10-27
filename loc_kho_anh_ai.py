# -*- coding: utf-8 -*-
"""SONEALEO 4.2 — lọc kho ảnh tầng 2 bằng Vision, chạy riêng và tùy chọn.

Không đoán công suất kVA. AI chỉ trả đúng 3 trục: dầu/khô, 1/3 pha, vai trò.
Không chắc ở bất kỳ trục nào -> chưa phân loại. Ảnh gốc và _DA_LOC không bị xoá.
"""
from pathlib import Path
import json, shutil
import vision_chung as V
import workspace_anh as WS

LOAI_OK = {'dau', 'kho'}
PHA_OK = {'1', '3'}
VAI_TRO_OK = {'san_pham', 'bien_may', 'lap_dat', 'giao_hang', 'khong_dung_duoc'}
PROMPT = '''Phân loại ảnh thiết bị điện. Chỉ trả JSON, không giải thích.
Trả đúng 3 câu hỏi sau, KHÔNG được đoán công suất kVA:
1) may: "dau" hoặc "kho" hoặc null nếu không chắc.
2) pha: "1" hoặc "3" hoặc null nếu không chắc.
3) vai_tro: "san_pham" | "bien_may" | "lap_dat" | "giao_hang" | "khong_dung_duoc" | null nếu không chắc.
JSON: {"may":...,"pha":...,"vai_tro":...}
Nếu ảnh không đủ bằng chứng, dùng null. Tuyệt đối không suy đoán kVA.'''


def _chuan(kq):
    j = (kq or {}).get('json') if isinstance(kq, dict) and 'json' in kq else kq
    j = j if isinstance(j, dict) else {}
    loai = str(j.get('may') or '').strip().lower()
    pha = str(j.get('pha') or '').strip().lower().replace(' pha', '')
    vt = str(j.get('vai_tro') or '').strip().lower()
    if loai not in LOAI_OK or pha not in PHA_OK or vt not in VAI_TRO_OK:
        return {'trang_thai':'chua_phan_loai','loai':loai or None,'pha':pha or None,'vai_tro':vt or None}
    return {'trang_thai':'ok','loai':loai,'pha':pha,'vai_tro':vt}


def phan_loai_anh(duong_dan, vision_func=None):
    fn = vision_func
    if fn is None:
        cfg = V.doc_cau_hinh()
        if not cfg.get('keys'):
            return {'trang_thai':'bo_qua_khong_ai','loi':'Chưa có GOOGLE_API_KEY; tầng 1 vẫn dùng bình thường.'}
        b, mime = V.thu_nho_anh(duong_dan, rong_toi_da=900, chat_luong=80)
        kq = V.goi_vision(b, mime, PROMPT, cau_hinh=cfg, max_tokens=1200, timeout=45)
    else:
        kq = fn(str(duong_dan), PROMPT)
    if not isinstance(kq, dict) or kq.get('ok') is False:
        return {'trang_thai':'chua_phan_loai','loi':str((kq or {}).get('loi','vision lỗi'))}
    return _chuan(kq)


def _family_candidates(image_root, sheet, loai, pha):
    base = Path(image_root) / WS.ten_an_toan(sheet, 80) / '_HO'
    out=[]
    if not base.is_dir(): return out
    for d in base.iterdir():
        if not d.is_dir() or d.name.startswith('_'): continue
        m=WS.doc_meta(d) or {}
        label=str(m.get('family_label') or '').lower()
        # meta 4.0 chưa lưu riêng loai/pha, family label/key có hai tín hiệu này.
        key=str(m.get('family_key') or d.name).lower()
        if loai in key and f'{pha}-pha' in key:
            out.append(d)
        elif (('dầu' in label if loai=='dau' else 'khô' in label) and f'{pha} pha' in label):
            out.append(d)
    return out


def chay_tang2(da_loc_dir, image_root, sheet='03_May_Bien_Ap_Do_Luong', vision_func=None):
    src=Path(da_loc_dir); root=Path(image_root)
    files=[p for p in src.rglob('*') if p.is_file() and WS.la_anh(p)]
    report={'tong_anh':len(files),'phan_loai_ok':0,'chua_phan_loai':0,'khong_dung_duoc':0,
            'gan_dung_1_ho':0,'khong_ai':0,'chi_tiet':[]}
    for p in files:
        r=phan_loai_anh(p, vision_func=vision_func)
        item={'file':str(p),**r}
        if r.get('trang_thai')=='bo_qua_khong_ai':
            report['khong_ai']+=1; report['chi_tiet'].append(item); continue
        if r.get('trang_thai')!='ok':
            report['chua_phan_loai']+=1
            dest=root/WS.ten_an_toan(sheet,80)/'_HO'/'_CHUA_PHAN_LOAI'; dest.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,dest/p.name); item['dich']=str(dest/p.name); report['chi_tiet'].append(item); continue
        report['phan_loai_ok']+=1
        if r['vai_tro']=='khong_dung_duoc':
            report['khong_dung_duoc']+=1
            dest=root/WS.ten_an_toan(sheet,80)/'_HO'/'_KHONG_DUNG_DUOC'; dest.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,dest/p.name); item['dich']=str(dest/p.name); report['chi_tiet'].append(item); continue
        cand=_family_candidates(root,sheet,r['loai'],r['pha'])
        if len(cand)==1:
            dest=cand[0]/'_AI_TANG2'/r['vai_tro']; dest.mkdir(parents=True,exist_ok=True); report['gan_dung_1_ho']+=1
        else:
            # Không hỏi hãng/lõi nên nếu >1 họ cùng dầu/khô+pha thì tuyệt đối không đoán.
            dest=root/WS.ten_an_toan(sheet,80)/'_HO'/'_CHUA_PHAN_LOAI'/f"{r['loai']}_{r['pha']}pha_{r['vai_tro']}"; dest.mkdir(parents=True,exist_ok=True)
            report['chua_phan_loai']+=1
        shutil.copy2(p,dest/p.name); item['dich']=str(dest/p.name); item['so_ho_khop']=len(cand); report['chi_tiet'].append(item)
    out=root/WS.ten_an_toan(sheet,80)/'_HO'/'BAO-CAO-TANG2.json'; out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8'); report['bao_cao']=str(out)
    return report


def main():
    from tkinter import Tk,filedialog,messagebox
    r=Tk(); r.withdraw()
    src=filedialog.askdirectory(title='Chọn thư mục _DA_LOC đã lọc tầng 1')
    if not src: r.destroy(); return
    root=filedialog.askdirectory(title='Chọn gốc workspace ảnh SONEALEO')
    if not root: r.destroy(); return
    try:
        kq=chay_tang2(src,root)
        messagebox.showinfo('Lọc ảnh AI tầng 2',f"Tổng: {kq['tong_anh']}\nAI OK: {kq['phan_loai_ok']}\nChưa phân loại: {kq['chua_phan_loai']}\nKhông dùng: {kq['khong_dung_duoc']}\nKhông AI: {kq['khong_ai']}\n\n{kq['bao_cao']}")
    except Exception as e: messagebox.showerror('Lọc ảnh AI tầng 2',f'{type(e).__name__}: {e}')
    finally: r.destroy()
if __name__=='__main__': main()
