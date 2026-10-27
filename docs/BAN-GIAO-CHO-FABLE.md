# Bản giao cho Fable — Ver 3.5

Fable là bên tổng hợp giữa ba nhánh: Claude làm tool (Python), GPT làm
plugin giao diện WordPress (PHP/CSS), Fable ghép lại và lo phần đo hiệu
quả SEO. Tài liệu này viết cho Fable đọc trước khi làm bất cứ việc gì.

Giọng ở đây thẳng, không phải để công kích. Ba đứa AI không đọc được code
của nhau, nên chỗ nào từng vỡ thì phải ghi lại rõ, không thì vỡ tiếp.

---

## 1. Ranh giới ba bên — luật cứng

**Tool sinh HTML với class `snl-*`. Plugin chỉ được STYLE, không được đổi
cấu trúc.**

Đây là điểm va chạm duy nhất giữa Claude và GPT. Tool sinh khối hero,
bảng thông số, khối kiến thức với tiền tố class `snl-`. Plugin của GPT
viết CSS ăn theo các class đó. Nếu một bên đổi tên class hoặc đổi cấu trúc
thẻ, bên kia mất style **mà không ai báo** — không có test nào bắt được
chuyện đó, vì test của tool chỉ kiểm HTML, còn CSS nằm ở repo khác.

Hệ quả thực tế:
- Claude không đổi tên class `snl-*` mà không ghi vào `NHAT-KY-THAY-DOI.md`.
- GPT không thêm/bớt thẻ HTML trong plugin để "sửa layout" — muốn đổi cấu
  trúc thì đổi ở tool.
- Fable khi ghép hai nhánh: kiểm danh sách class `snl-*` hai bên có khớp
  không, trước khi kết luận "chạy được".

## 2. Bốn luật đóng gói — đã vi phạm một lần, đừng lặp lại

Bản 3.4 vi phạm cả bốn. Ghi lại nguyên văn để đối chiếu:

1. **ZIP không chứa `phase2-du-lieu.db`.** Bản 3.4 kèm file 7,5 MB. Giải
   nén đè lên thư mục đang chạy = xoá sạch dữ liệu thật (245 bài, wp_id,
   lịch sử đăng, log). Đây là mất dữ liệu, không phải bất tiện.
2. **ZIP không chứa `cau-hinh.env` thật.** Bản 3.4 kèm file đã bị ghi rác
   test: `GOOGLE_API_KEY=FAKE_KEY`, `WP_WEBSITE_URL=https://test37.vn`,
   `WP_WEBSITE_CHE_DO=post` (bản 3.3 là `woo_product`), và mất hai dòng
   `GOOGLE_API_KEY_DU_PHONG` / `MODEL_GEMINI_DU_PHONG`. Đè vào là mất key
   và tool đăng bài viết thường thay vì sản phẩm WooCommerce.
3. **Changelog phải ghi mọi phiên bản.** `NHAT-KY-THAY-DOI.md` của bản 3.4
   có mục mới nhất là **Ver 3.0** — toàn bộ thay đổi 3.1→3.4 không được
   ghi. Không ai biết 3.4 khác 3.3 chỗ nào, kể cả người viết ra nó.
4. **Đủ 4 tài liệu chuẩn**: `SPEC.md`, `NHAT-KY-THAY-DOI.md`,
   `KNOWN-ISSUES.md`, `TEST-REPORT.md`, cộng `TIEN-DO.md`. Bản 3.4 thiếu 3
   trong 4.

## 3. Ba lỗi kỹ thuật đã tìm ra, kèm bằng chứng

Ghi lại để Fable không "sửa lại" theo hướng cũ.

### 3.1 Ver 3.4 gần như không phải một phiên bản

Diff 3.3 → 3.4: `giao-dien.py` (4.457 dòng) **chỉ đổi 3 chuỗi
"Ver 3.3" → "Ver 3.4"**, không một dòng logic. Thay đổi thật chỉ có
`ban_do_du_lieu.py` (303 dòng) + 8 dòng nối trong `man_hinh_du_lieu.py`.

Bài học: đổi số phiên bản không phải là làm phiên bản. Changelog phải ghi
**diff thật**, không ghi ý định.

### 3.2 Lỗi lặp nội dung trên toàn bộ 245 bài

`enhance.merge_insight_vao_bai()`: Ver 2.6 tách `boi_canh_su_dung` +
`goc_nhin_bundle_cheo` ra khối riêng `goc_nhin_thi_truong_html` nhưng quên
xoá 2 lệnh cộng chuỗi cũ vào `ung_dung_html`. Cùng một bộ `<li>` in ra hai
lần mỗi bài, cách nhau ba màn hình.

Đây là **duplicate content do code tự sinh**. Ver 3.5 đã gỡ. Hai test cũ
(`test_enhance_mock.py`) đang khẳng định hành vi lặp là đúng — tức test
đang khoá cái lỗi. Đã sửa kỳ vọng, đừng khôi phục.

### 3.3 `man_hinh_du_lieu.gan_vao()` nuốt lỗi im lặng

Bọc `try/except` rồi chỉ `print` ra console. Máy nào thiếu `tksheet` thì
tab Bản đồ **biến mất không dấu vết**, người dùng tưởng chưa ai làm.

`hang_doi.py` ở Ver 3.5 không lặp lại: thiếu thư viện thì in thẳng lên
giao diện kèm câu lệnh cài. Áp dụng nguyên tắc này cho mọi tab sau.

## 4. Vấn đề dữ liệu — quan trọng hơn cả phần code

### 4.1 Po/Pk/Uk KHÔNG phải thông số riêng của hãng

Po/Pk/Uk trùng khít 100% giữa catalogue THIBIDI và MBT vì cả hai in lại
**cùng một bảng quy chuẩn EVN**. Bảng của EVN Miền Bắc (QĐ 1011) ghi
50 kVA → Po 120 W, Pk 715 W, Io 2%, Uk 4÷6 — trùng dòng đầu bảng MBT.

Hệ quả cho SEO, và đây là chỗ Fable cần cân nhắc khi tính "hiệu quả":
**122 trang sẽ có cùng bộ số ở các cột Po/Pk/Uk/Io theo từng mức kVA.**
Cùng 250 kVA thì THIBIDI, MBT, EMC ra đúng một bộ số. Nhân lên 8 site thì
mức trùng nhân lên theo. Đây là cannibalization ở **tầng dữ liệu**, ma
trận góc nhìn không cứu được vì góc khác nhau nhưng bảng số vẫn y hệt.

Thứ khác nhau thật giữa các hãng: khối lượng dầu, tổng khối lượng, kích
thước W×D×H, tổ đấu dây, hiệu suất 100% tải, giá, xuất xứ. Cộng thêm thứ
catalogue không in: **Io và tổ đấu dây đọc từ biển máy thật**.

### 4.2 Trạng thái tiêu chuẩn — đã tra, có nguồn

- QĐ 96/QĐ-HĐTV ngày 05/9/2023 ban hành TCCS 01:2023/EVN. **QĐ 62/QĐ-EVN
  ngày 05/5/2017 đã hết hiệu lực.** Catalogue MBT 2024 vẫn in theo QĐ 62.
- Dung sai: Po được vượt đến 5%, Pk được vượt đến 3% so với bảng, với điều
  kiện hiệu suất E50% không giảm. **Cảnh báo:** điều khoản này thuộc quy
  định EVN **NPC (miền Bắc)**. Lotech bán ở địa bàn EVN SPC / EVNHCMC —
  chưa kiểm hai nơi này có quy định khác không.
- QĐ 107/QĐ-HĐTV ngày 21/9/2021 = tiêu chuẩn MBA phân phối **tổn hao
  thấp**. SKU lõi Amorphous ghi thẳng "QĐ 107/QĐ-HĐTV" trong cột Tên hàng,
  nên số của chúng lấy từ bảng này, không phải bảng Silic.

### 4.3 19 SKU Amorphous từng bị gán số của bản Silic

Phép kiểm: cùng kVA, Po(Amorphous)/Po(Silic) nằm trong dải 26,9–30,9% trên
25 cặp đối chiếu được. 19 dòng có tỷ lệ đúng 100% — tức chép nguyên bảng
Silic sang. Toàn bộ 17 SKU Amorphous của MBT + 2 của THIBIDI.

Nếu render ra: 19 bài nói máy lõi Amorphous có tổn hao không tải bằng đúng
máy lõi Silic — phủ định thẳng lý do tồn tại của Amorphous. Đã xoá ở MASTER
Ver5, để trống chờ bảng gốc QĐ 107.

**Nguyên tắc rút ra: để trống còn hơn để sai.**

## 5. Yêu cầu với Fable

1. **Đối chiếu code thật trước khi kết luận.** Ba lỗi ở mục 3 đều được
   tìm bằng cách đọc file, không phải bằng cách đọc báo cáo. Bản tóm tắt
   của phiên trước không phải bằng chứng.
2. **Không đề xuất lại những thứ đã thử và thất bại**: pipeline vision đọc
   catalogue PDF tự động (12 file 200 MB → chỉ ra 15/245 SKU, trong khi
   chụp màn hình tay ra 52/245); nhồi audit trail vào Excel (file 7 MB);
   SVG inline (`wp_kses` xoá thẻ); refactor kiến trúc nhiều tầng; Google
   Custom Search API (Google đã đóng).
3. **Schema JSON-LD trả qua key riêng, tuyệt đối không nhét vào HTML.**
   WordPress lọc thẻ `<script>` khi POST qua REST nhưng **giữ text bên
   trong** → nguyên khối JSON hiện thành chữ trên trang. Đã xảy ra thật.
4. **Về phần đo hiệu quả SEO**, hai lưu ý kỹ thuật đã kiểm:
   - WordPress **âm thầm bỏ qua** `rank_math_title` /
     `rank_math_description` khi POST qua REST — trả 201 thành công nhưng
     field vẫn rỗng. Phải `register_post_meta` hoặc cài plugin phụ mở
     endpoint riêng. Đây là chỗ hay tưởng chạy mà thực ra không ghi gì.
   - Vòng phản hồi GSC là 2–4 tuần cho mỗi thay đổi. Mọi cơ chế "tự
     chỉnh" nhanh hơn nhịp đó đều mất khả năng quy kết kết quả cho thay
     đổi nào. Đề xuất bản "phát hiện + đề xuất + người bấm duyệt" thay cho
     bản tự động hoàn toàn.
5. **Trạng thái quyền truy cập là ràng buộc lớn nhất**, không phải kỹ
   thuật. Toàn bộ kế hoạch nhân bản 8 site giả định có quyền trên 8 site.
   Hiện chưa có. Đừng lập kế hoạch bỏ qua điều đó.
