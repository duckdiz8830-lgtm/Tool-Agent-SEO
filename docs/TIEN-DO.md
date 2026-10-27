# Tiến độ — SONEALEO ULTRA · Ver 5.4 · cập nhật 20/08/2026

> **File này là NGUỒN DUY NHẤT của roadmap.** Trước 20/08 roadmap nằm rải 3
> chỗ (`TIEN-DO.md`, phần "Vẫn còn" trong `NHAT-KY-THAY-DOI.md`,
> `KNOWN-ISSUES.md`) và **chửi nhau**: 2 việc bị liệt "còn nợ" trong khi
> code đã làm xong từ lâu. Từ nay việc "sẽ làm" chỉ ghi ở đây.
>
> Trạng thái mỗi mục có **mức tin cậy**. Mục nào chưa chạy thật để kiểm thì
> ghi thẳng *chưa tái kiểm* — không đoán.

---

## A. Đã đóng — trước đây bị ghi nhầm là "còn nợ"

Hai mục này đứng đầu danh sách ưu tiên trong nhật ký cũ suốt 1 tuần, thực tế
đã xong. Đây chính là cái giá của doc rot: **ưu tiên sai vì đọc doc thay vì đọc code.**

| Việc | Trạng thái thật | Bằng chứng | Tin cậy |
|---|---|---|---|
| `thinkingConfig` chưa vào request sinh bài thật | **XONG** — có cả fallback khi model trả 400 và tự bỏ `thinkingConfig` rồi thử lại | `autopost.py:496,509-523`; `ai_wp_adapter.py:273` (`thinkingBudget: 6000`) | cao |
| HTML từ AI chưa lọc thẻ an toàn | **XONG** — `bleach.clean`, xoá cả nội dung `<script>/<style>`, giới hạn giá trị `class` | `render_phase2.py:243-283`, gọi ở `:1668,1696,1700` | cao |
| `MODEL_GEMINI` mặc định là model đã chết | **XONG** — mặc định `gemini-3.6-flash` ở cả 3 nơi, không lệch | `autopost.py:68`; `cau-hinh.env.MAU:18`; `giao-dien.py:5003` | cao |
| Ảnh: WebP / featured image / alt | **CÓ CODE**, chưa tái kiểm chạy thật | 10 file có dấu vết (`xu_ly_anh.py`, `tab_anh.py`, `workspace_anh.py`...) | vừa |
| Gán chuyên mục / thẻ khi đăng WordPress | **CÓ CODE**, chưa tái kiểm | `ai_wp_adapter.py`, `render_phase2.py` | thấp |

## B. Còn nợ thật — theo thứ tự làm

1. **`du_lieu_bat_buoc` cho từng outline** — outline báo giá mà trống giá thì
   ĐỪNG SINH. Grep toàn source: **0 kết quả**, chưa làm dòng nào. Tin cậy: cao.
   *Liên quan trực tiếp tới chất lượng article — làm trước khi chạy lô lớn.*
2. **Vân tay thông số** — 2 SKU trùng cả 8 cột thì cảnh báo. Đo trên dữ liệu
   thật: **36/98 SKU đang trùng vân tay do CỘT TRỐNG**, không phải sản phẩm
   giống nhau thật. `cong_chat_luong.py` (Ver 4.6) đã chặn được MỎNG/TRÙNG ở
   mức bài — nhưng chưa chặn ở mức *dữ liệu nguồn*. Cần đo lại trên MASTER
   Ver16. Tin cậy con số 36/98: **thấp** (đo từ lâu, dataset đã đổi).
3. **Bếp trưởng bước 2** — sinh dàn ý RIÊNG cho từng hạng thay vì ép mọi SKU
   vào cùng khuôn 17 dòng. Đây là chỗ gỡ trần chất lượng ~6,5/10.
   `bep_truong.py` có phân hạng (bước 1, xong ở 3.5); bước 2 chưa.
4. **Cache `kho_toan_bo` không tự làm mới** khi sửa `products.csv` bằng tay
   rồi nhập lại → dễ đăng bài với danh sách trắng chống bịa số đã cũ.
5. **Nối 103 SKU có số vào Tầng 3** (`kien_thuc_bien_thien`) — tầng này đọc
   theo tên field cũ, phần lớn SKU vừa enrich chỉ có bảng, không có lời giải
   thích số. Chưa tái kiểm sau khi 5.4 đổi tên field. Tin cậy: **thấp**.
6. **In dấu `≤`** trong bảng thông số cho 93 SKU dùng mức quy chuẩn EVN.
   *Bẫy đã biết:* **KHÔNG** khai cột Po/Pk EVN vào `cot_import` — field khai
   cứng chỉ chứa số trần ("640"), Hard Block không ghép được đơn vị và sẽ
   chặn nhầm chính số mình đưa cho AI. Phải sửa ở chỗ dựng bảng.
7. **Liên kết nội bộ** — thiếu hậu tố outline trong URL, có thể trỏ tới bài
   chưa đăng. (5.0 đã vá phần "chỉ link khi SKU anh em có URL thật" — phần
   hậu tố outline chưa rõ đã xong chưa. Tin cậy: **thấp**.)
8. **Ver 5.4 chưa có test.** `tests/` có `test_v50..v53_patch.py`, không có
   `test_v54`. Serper.dev + 10 cột catalogue MBA đang chạy không lưới. Tin cậy: cao.

## C. Nợ kiến trúc — đang phình, không giảm

| Món | Lúc ghi nợ (4.4.1.7) | Bây giờ | Xu hướng |
|---|---|---|---|
| `giao-dien.py` God Class | 4.457 dòng | **5.336 dòng** | ↑ +20% |
| 5 đường ghi nội dung lên WordPress | chưa gỡ | chưa gỡ | → |

Quyết định giữ nguyên từ 3.6.4: viết lại `giao-dien.py` rủi ro lớn hơn lợi
ích, mọi tab mới từ 3.1 nằm ở file riêng. **Nhưng nếu nó qua 6.000 dòng thì
phải xét lại** — đặt đó làm ngưỡng kích hoạt, không xét theo cảm tính.

## D. Việc KHÔNG code được — chỉ Thịnh làm

- [ ] Chạy thử **Dọn rác 3 bài** trên WP thật rồi mới chạy 245 — treo từ 13/08.
- [ ] Chạy `run_tests.py` **trên Windows** để kết luận 4 test fail (nghi là lỗi
      môi trường Tkinter/Xvfb, chưa xác nhận).
- [ ] Quyết **17 SKU trùng** (12 cáp, 1 tủ, 4 phụ kiện) — lỗi nhập liệu hay thật?
- [ ] Quyết **19 SKU gán sai họ sản phẩm** (VD `ABBLA12` chống sét van đang ở
      `outline_tu_dong_cat`). Nguy hơn lỗi văng: bài ra êm, chỉ là **sai bản chất**.
- [ ] Chốt **caveat QĐ 2608**: Po=31W/Pk=570W thuộc TCCS 10:2021 hay QĐ 2608?
- [ ] Hỏi công ty: **bảo hành bao nhiêu tháng, có CO/CQ không** — đang 0/245.
      5.4 đã khai sẵn field, chỉ thiếu số.
- [ ] Xin bảng gốc **QĐ 107/QĐ-HĐTV 2021** để phục hồi 19 SKU Amorphous.
- [ ] Hỏi KP: catalogue in công suất 1200 nhưng mã máy KPCE-1250/24.

## E. Đã quyết KHÔNG làm

- Việt hoá UI (trọng số 0,0163).
- Refactor kiến trúc nhiều tầng.
- Pipeline vision đọc catalogue PDF tự động.
- Điều khiển Gemini qua trình duyệt (Chrome CDP) — dễ gãy, rủi ro ToS.
- Gỡ nhánh RMU Ver 1/Ver 2 tuy không dùng — code chạy được thì để yên.

---

## Quy trình đóng gói — làm ĐỦ, không bỏ bước

Doc rot 4.5→5.4 xảy ra vì không có bước bắt buộc. Từ nay:

1. Sửa `phien_ban.PHIEN_BAN`.
2. Ghi mục mới vào `docs/NHAT-KY-THAY-DOI.md` **lúc đang làm**, không viết sau.
3. Chạy `python phien_ban.py` — tự đối chiếu mốc `Ver x.y` cao nhất trong
   code với `PHIEN_BAN`. Lệch thì exit code 1.
4. Cập nhật `docs/KNOWN-ISSUES.md` (ít nhất sửa dòng phiên bản ở header).
5. Nếu đụng `cot_import`: chạy `import_phase2_pipeline` trên MASTER THẬT
   trước khi đóng gói — `column_structure` guard sẽ chặn ngầm nếu không.
6. ZIP không kèm `.db` và `cau-hinh.env` thật.
