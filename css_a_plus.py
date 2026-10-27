# -*- coding: utf-8 -*-
"""SONEALEO 3.3 — CSS bố cục A+ (Thịnh chọn 06/08/2026).

Dán 1 lần vào WordPress > Code Snippets (loại CSS). Sửa file này rồi
chạy `python css_a_plus.py` để xuất ra css-a-plus.txt mà dán lại —
KHÔNG cần đăng lại bài nào, vì bài chỉ chứa class.

Phủ đủ 75/75 class của cả giao_dien_2_5.STYLE_2_5 lẫn render_phase2.ST.
"""

CSS = """
.snl-page{--m:#0f3d5c;--m2:#12557f;--do:#d0342c;--cam:#d1490f;--n:#1a2430;--n2:#5a6675;
  --vien:#dde3ea;--vien2:#eef1f5;--nen:#f6f8fa;
  max-width:1180px;margin:0 auto;color:var(--n);font-size:15.5px;line-height:1.65;
  font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.snl-page h1,.snl-page h2,.snl-page h3{font-weight:700;letter-spacing:-.01em}

/* ===== HERO — cột trái vuông 1:1 khớp Flatsome, cột phải gọn ===== */
.snl-hero{display:grid;grid-template-columns:minmax(300px,460px) 1fr;gap:34px;
  padding:0 0 26px;margin:0 0 24px;border-bottom:1px solid var(--vien)}
.snl-hero-visual{min-width:0}
.snl-anh-chinh{position:relative;width:100%;aspect-ratio:1/1;overflow:hidden;background:var(--nen);
  border:1px solid var(--vien);display:flex;align-items:center;justify-content:center}
.snl-anh-chinh img{width:100%;height:100%;object-fit:cover;display:block}
.snl-thumb-row{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:8px 0 0}
.snl-thumb{aspect-ratio:1/1;overflow:hidden;border:1px solid var(--vien);background:var(--nen);
  display:flex;align-items:center;justify-content:center;font-size:11px;color:#9aa4b2;cursor:pointer}
.snl-thumb img{width:100%;height:100%;object-fit:cover}
.snl-thumb-active{border:2px solid var(--do)}
.snl-hero-info{min-width:0}
.snl-breadcrumb{color:var(--n2);font-size:12.5px;margin:0 0 10px}
.snl-kicker{display:inline-block;background:var(--do);color:#fff;font-weight:700;font-size:11px;
  text-transform:uppercase;letter-spacing:.1em;padding:3px 9px;margin:0 0 10px}
.snl-h1{font-size:26px;line-height:1.28;margin:0 0 12px;color:var(--n)}
.snl-lead{font-size:15px;color:var(--n2);margin:0 0 18px}
.snl-chip-row{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 18px;padding:0;list-style:none}
.snl-chip{border:1px solid var(--vien);background:#fff;padding:5px 11px;font-size:12.5px;
  font-weight:600;color:var(--m2);font-variant-numeric:tabular-nums}
.snl-chip-nguon{background:var(--m);color:#fff;padding:5px 11px;font-size:12.5px;font-weight:700}

/* thông số nhanh kiểu Made-in-China: nhãn trái, giá trị phải, kẻ ngang mảnh */
.snl-quick{display:block;border-top:1px solid var(--vien);margin:0 0 18px}
.snl-quick-o{display:flex;justify-content:space-between;gap:16px;padding:9px 2px;
  border-bottom:1px solid var(--vien2)}
.snl-quick-nhan{font-size:13.5px;color:var(--n2);flex:none}
.snl-quick-gt{font-size:14.5px;font-weight:700;text-align:right;font-variant-numeric:tabular-nums}
.snl-price,.snl-price-nhan,.snl-price-gt{display:none}   /* bỏ dòng "Giá: Liên hệ" theo yêu cầu */
.snl-actions,.snl-cta-actions{display:flex;flex-wrap:wrap;gap:10px}
.snl-btn{display:inline-block;padding:12px 26px;text-decoration:none;font-size:14.5px;font-weight:700}
.snl-btn-chinh{background:var(--do);color:#fff}
.snl-btn-phu{background:#fff;color:var(--m);border:1.5px solid var(--m)}
.snl-btn:hover{opacity:.92}

/* ===== ĐIỀU HƯỚNG + SECTION ===== */
.snl-nav{display:flex;flex-wrap:wrap;border:1px solid var(--vien);background:var(--nen);margin:0 0 26px}
.snl-nav-link{padding:11px 16px;font-size:13.5px;font-weight:600;color:var(--m2);
  text-decoration:none;border-right:1px solid var(--vien)}
.snl-nav-link:hover{background:var(--m);color:#fff}
.snl-section{margin:0 0 30px;padding:0 0 26px;border-bottom:1px solid var(--vien)}
.snl-section-head{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;margin:0 0 16px}
.snl-h2{font-size:21px;color:var(--n);margin:0;padding:0 0 0 12px;border-left:4px solid var(--do)}
.snl-section-intro{font-size:13.5px;color:var(--n2);margin:8px 0 0 12px}
.snl-nguon-badge{flex:none;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;
  color:var(--n2);border:1px solid var(--vien);padding:4px 9px;background:#fff}

/* ===== BẢNG THÔNG SỐ kiểu Product Details ===== */
.snl-specs-table{width:100%;border-collapse:collapse;font-size:14.5px}
.snl-specs-th{padding:11px 16px 11px 0;text-align:left;width:54%;font-weight:400;color:var(--n2);
  border-bottom:1px solid var(--vien2);vertical-align:top}
.snl-specs-td{padding:11px 0;font-weight:700;border-bottom:1px solid var(--vien2);
  font-variant-numeric:tabular-nums}
.snl-specs-table tr:hover .snl-specs-th,.snl-specs-table tr:hover .snl-specs-td{background:var(--nen)}

/* ===== KHUNG ẢNH TRONG THÂN BÀI ===== */
.snl-anh-khung{width:100%;aspect-ratio:3/2;overflow:hidden;background:var(--nen);
  border:1px solid var(--vien);margin:16px 0 0}
.snl-anh-khung img{width:100%;height:100%;object-fit:cover;display:block}
.snl-anh-caption{font-size:12.5px;color:var(--n2);margin:8px 0 0;font-style:italic}

/* CHỖ CHỜ ẢNH — hiện rõ để tự chèn, nếu lỡ quên vẫn đọc được như câu trung thực */
.snl-cho-anh{border:1px dashed #b9c4d1;background:var(--nen);padding:26px 20px;margin:16px 0 0;
  text-align:center}
.snl-cho-anh-nhan{display:inline-block;background:var(--m);color:#fff;font-size:11px;font-weight:700;
  letter-spacing:.08em;text-transform:uppercase;padding:3px 9px;margin:0 0 10px}
.snl-cho-anh-ten{font-weight:700;color:var(--m);font-size:15px;margin:0 0 6px}
.snl-cho-anh-mo-ta{font-size:13px;color:var(--n2);margin:0 0 4px}
.snl-cho-anh-kt{font-size:12px;color:#8a93a5;margin:0;font-style:italic}

/* ===== KHỐI KIẾN THỨC — chia block ===== */
.snl-khoi-chung{background:#fff;border:1px solid var(--vien);border-left:3px solid var(--m2);
  padding:14px 18px;margin:0 0 12px;font-size:14.5px}
.snl-khoi-thuong-hieu{background:var(--nen);border:1px solid var(--vien);padding:16px 20px;
  margin:0 0 14px;font-size:14.5px}
.snl-khoi-thuong-hieu h2,.snl-khoi-thuong-hieu h3{font-size:16px;color:var(--m);margin:0 0 8px;
  padding:0;border:0}
.snl-khoi-chung p:last-child,.snl-khoi-thuong-hieu p:last-child{margin-bottom:0}
.snl-note{border:1px solid var(--vien);border-left:4px solid var(--do);background:var(--nen);
  padding:16px 20px;margin:18px 0}
.snl-note-title{font-weight:700;color:var(--m);margin:0 0 8px;font-size:15.5px}
.snl-origin{font-size:12.5px;color:var(--n2);margin:0}
.snl-summary-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));
  border:1px solid var(--vien)}
.snl-summary-card{padding:15px 17px;border-right:1px solid var(--vien)}
.snl-card-title{font-weight:700;color:var(--m);font-size:15px;margin:0 0 5px;
  font-variant-numeric:tabular-nums}
.snl-card-text{font-size:13.5px;color:var(--n2);margin:0}
.snl-so-sanh-table{width:100%;border-collapse:collapse;font-size:14px}
.snl-so-sanh-th{padding:10px 14px;background:var(--m);color:#fff;font-weight:700;font-size:12.5px;
  text-align:left;text-transform:uppercase;letter-spacing:.04em}
.snl-so-sanh-td{padding:10px 14px;border-bottom:1px solid var(--vien2);font-variant-numeric:tabular-nums}
.snl-so-sanh-td-hien-tai{padding:10px 14px;border-bottom:1px solid var(--vien2);background:#fff5f4;
  font-weight:700;color:var(--do);font-variant-numeric:tabular-nums}
.snl-checklist{list-style:none;padding:0;margin:14px 0}
.snl-check-item{position:relative;padding:0 0 0 24px;margin:0 0 9px;font-size:14.5px}
.snl-check-item:before{content:"▸";position:absolute;left:4px;color:var(--do);font-weight:700}
.snl-faq{border:1px solid var(--vien)}
.snl-faq-item{padding:15px 18px;border-bottom:1px solid var(--vien2)}
.snl-faq-q{font-weight:700;margin:0 0 6px;font-size:15px}
.snl-faq-a{margin:0;color:var(--n2);font-size:14.5px}
.snl-cta,.snl-cta-cuoi{background:var(--m);color:#fff;padding:26px;margin:28px 0 0}
.snl-cta-title{font-size:20px;font-weight:700;margin:0 0 6px}
.snl-cta-text{margin:0 0 18px;color:#cfe0ec;font-size:14.5px}
.snl-cta .snl-btn-phu{background:transparent;color:#fff;border-color:#fff}
.snl-cta-giua{background:var(--nen);border:1px solid var(--vien);border-left:4px solid var(--do);
  padding:16px 20px;margin:22px 0;display:flex;flex-wrap:wrap;align-items:center;
  justify-content:space-between;gap:14px}
.snl-cta-giua-text{margin:0;font-weight:600;font-size:15px}
.snl-tech-card{border:1px solid var(--vien);padding:16px;background:#fff;color:var(--n2)}
.snl-tech-note{margin:8px 0 0;font-size:12.5px}
.snl-lien-quan{list-style:none;padding:0;margin:0}
.snl-lien-quan-li{display:block;padding:9px 0;border-bottom:1px dashed var(--vien)}
.snl-lien-quan-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px}
.snl-lien-quan-card{display:block;padding:14px 16px;border:1px solid var(--vien);text-decoration:none;
  color:var(--n);font-size:14px;font-weight:600;line-height:1.45}
.snl-lien-quan-card:hover{border-color:var(--do);color:var(--do)}
.snl-anh-placeholder{display:none}
.snl-btn-goi,.snl-btn-zalo,.snl-btn-baogia,.snl-btn-catalogue{display:inline-block;padding:11px 22px;
  text-decoration:none;font-size:14.5px;font-weight:700;margin:0 8px 8px 0}
.snl-btn-baogia{background:var(--do);color:#fff}.snl-btn-goi{background:#16794a;color:#fff}
.snl-btn-zalo{background:#0b74c4;color:#fff}
.snl-btn-catalogue{background:#fff;color:var(--m);border:1.5px solid var(--m)}
.snl-hero-meta{font-size:14px;color:var(--n2);margin:0 0 10px}
.snl-hero-specs{list-style:none;padding:0;margin:0 0 12px;font-size:14px}
.snl-proof{font-size:12.5px;color:var(--n2);margin:10px 0 0}
.snl-spec-wrap{overflow-x:auto}
.snl-table{width:100%;border-collapse:collapse;font-size:14.5px}
.snl-th{padding:11px 16px 11px 0;text-align:left;width:54%;font-weight:400;color:var(--n2);
  border-bottom:1px solid var(--vien2)}
.snl-td{padding:11px 0;font-weight:700;border-bottom:1px solid var(--vien2)}
@media (max-width:900px){.snl-hero{grid-template-columns:1fr;gap:22px}}
@media (max-width:640px){.snl-page{font-size:15px}.snl-h1{font-size:22px}.snl-h2{font-size:19px}
  .snl-nav{overflow-x:auto;flex-wrap:nowrap}.snl-thumb-row{grid-template-columns:repeat(4,1fr)}}
"""


if __name__ == '__main__':
    open('css-a-plus.txt', 'w', encoding='utf-8').write(CSS)
    print(f'Đã xuất css-a-plus.txt — {len(CSS):,} ký tự')
