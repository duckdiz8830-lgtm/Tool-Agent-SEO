# Lotech Autopost — Claude v2.3

**Lần đầu:** bấm đúp `CAI-DAT-LAN-DAU.bat`, chờ vài phút, nó tải Python riêng về thư
mục `python\`. Từ đó về sau bấm `PHAN-MEM.bat` là chạy, không cần Python máy, không
cần mạng.

Máy công ty chặn python.org thì bỏ qua bước đó, `PHAN-MEM.bat` tự dùng Python cài sẵn
trên máy. Vẫn chạy bình thường.

Xem đã sửa gì so với bản trước: `NHAT-KY-THAY-DOI.md`.

---

## 1. Việc phải làm ngay, trước khi chạy bất cứ thứ gì

Bản V3 không kèm `cau-hinh.env`, chỉ có `cau-hinh.env.MAU`. Điền cấu hình qua
giao diện (tab 1) là nó tự ghi ra file.

**Đổi model.** Cấu hình cũ đang để `MODEL_GEMINI=gemma-4-26b-a4b-it`. Dòng Gemma
không nhận system prompt và không ép được đầu ra JSON, chạy sẽ hỏng bài. V3 có xử lý
đỡ cho trường hợp này nhưng chất lượng vẫn kém hơn hẳn. Vào tab 1 bấm
**Dò model chạy được**, chọn một model có chữ `gemini` và `flash`.

---

## 2. Sáu lỗi đã sửa

| Lỗi | Hậu quả trước đây | Đã sửa |
|---|---|---|
| Thư mục `kienthuc/` không tồn tại, 4 file JSON nằm ở gốc | Kho kiến thức **chưa bao giờ chạy**. Hàm nạp luôn trả về rỗng | Tự dọn file JSON vào `kienthuc/` khi khởi động |
| So khớp số xoá luôn dấu phẩy | `0,4kV` trong dữ liệu không khớp `0.4kV` do AI viết, bài bị chặn oan. Xem log cũ: `CANH_BAO 0.4kV` | Dấu phẩy thập phân đổi thành dấu chấm trước khi so |
| Bảng giá gom theo cột `dong_may` | Cột này không tồn tại trong dữ liệu, nên bảng giá **không bao giờ hiện**, luôn rơi vào câu "gọi để nhận báo giá" | Gom theo `series` + `cap_dien_ap`, xếp theo số ngăn |
| Ảnh trong thư mục `anh/` ghép vào bài dưới dạng `file:///C:/...` | Đăng lên web là **ảnh vỡ hết** | Khi đăng thật thì tự tải ảnh lên thư viện WordPress, dùng URL thật, có nhớ để không tải trùng |
| Hai đường sinh bài riêng (giao diện một kiểu, dòng lệnh một kiểu) | Sửa chỗ này quên chỗ kia. Giao diện không ghi meta_title, không ghi log.csv | Cả hai gọi chung `sinh_mot_bai()` |
| Bộ nhớ đệm kho số không bao giờ xoá | Nhập lại Excel giữa chừng vẫn dùng kho số cũ | Đệm theo số dòng, dữ liệu đổi là tính lại |

Thêm một thứ: con số nằm trong kho kiến thức **đã kiểm chứng** giờ được đưa vào danh
sách trắng. Không làm vậy thì bật kiến thức lên là bài bị chặn oan, vì AI nhắc lại
đúng con số mình vừa đưa cho nó.

---

## 3. Ba thứ mới

**Chạy được nhiều site.** Mở `cauhinh.py`, khối `SITES`. Chép nguyên một khối, đổi
khoá thành `site3`, đổi tên và hotline. Rồi vào tab 1 chọn site đó, điền WordPress,
bấm Lưu. Tab 3 có ô chọn site khi chạy.

Mỗi site có `hang_duoc_nhac` riêng: AI chỉ được nhắc tên hãng trong danh sách đó.
Site THIBIDI thì chỉ THIBIDI, site RMU thì Schneider/ABB/Siemens.

**Từ cấm gom về một chỗ.** `cauhinh.py > TU_CAM_CHUNG`. Bài nào chứa một trong các
chuỗi đó là bị chặn, không đăng. Đây là hàng rào duy nhất ngăn hệ vệ tinh bị nối
về công ty mẹ. Hotline của chính site đang chạy được tự loại ra khỏi danh sách.

**Chuyển dữ liệu cũ tự động.** `du-lieu.db` của V2 thiếu cột `site`. Lần chạy đầu
nó tự chuyển toàn bộ lịch sử sang bảng mới, gán về `site1`. Không mất gì.

---

## 4. Thứ tự làm

```
Tab 1   chọn file Excel  >  điền Ngành hàng  >  Xem thử  >  NHẬP VÀO KHO
Tab 1   mở thư mục kienthuc, đối chiếu catalogue, sửa da_kiem_chung thành true
Tab 1   bỏ ảnh vào thư mục anh/, tên file chứa mã sản phẩm
Tab 2   điền API key, dò model, điền WordPress, Lưu, bấm Kiểm tra kết nối
Tab 3   bấm đúp cột "Viết" để bật/tắt sản phẩm cần sinh bài. Dòng tắt vẫn có mặt
        trong bảng giá và liên kết nội bộ của bài khác, chỉ là không tự sinh bài
Tab 3   xem dòng nào thiếu dữ liệu, xuất products.csv để điền giá rồi nhập lại

**products.csv không đi kèm bản này.** File đó chỉ sinh ra khi mày bấm "Xuất
products.csv" ở tab 3, dùng để điền giá/tình trạng kho rồi nhập lại — không
phải nguồn dữ liệu gốc. Dữ liệu thật LUÔN LUÔN import từ file Excel gốc ở
tab 1 (qua `nhap_excel`), vì chỉ đường đó mới giữ đúng các sản phẩm trùng
thành record riêng (từ v2.6). Nếu thấy `products.csv` cũ nằm sẵn trong thư
mục — xoá đi, đừng dùng, nó là dữ liệu demo cũ trước bản sửa lỗi trùng.
Tab 4   chạy thử 3 bài  >  đọc file trong output/  >  chỉnh prompts.py
        >  sinh thật  >  đăng nháp  >  đọc lại  >  đăng thật
Tab 0   theo dõi tiến độ, chọn 1 dòng để xem trước tiêu đề/meta bên dưới bảng,
        bấm Xuất Excel để gửi sếp hoặc giao người điền dữ liệu
```

**Ngành hàng** là ô quan trọng nhất ở tab 1. Nó ngăn kho theo ngành. Nạp file cáp điện
mà để chung ngành với tủ trung thế thì số liệu hai ngành trộn vào nhau, bộ chặn bịa số
yếu hẳn đi. Mặc định lấy theo tên file Excel, sửa tay được.

Khai site nào bán ngành nào ở `cauhinh.py`, khoá `danh_muc`. Để `[]` là lấy tất cả.

## 4b. Nghiệm thu trước khi chạy sản lượng

Bấm `KIEM-THU-30-BAI.bat`. Nó chạy 30 bài rồi tự chấm 5 mốc:

```
[ ĐẠT  ] 1. Không lỗi kết nối, không lỗi JSON
[ ĐẠT  ] 2. Tỷ lệ bị chặn dưới 10%
[ ĐẠT  ] 3. Đủ bản ghi trong kho dữ liệu, không mất trạng thái
[ ĐẠT  ] 4. Chạy lại không đẻ bài trùng, không trùng slug
[ ĐẠT  ] 5. Tắt máy chạy tiếp được đúng chỗ
```

Trượt mốc nào nó in luôn nguyên nhân và chỗ phải sửa. Đủ 5/5 ở chế độ `nhap` thì mới
chạy sản lượng. Chạy xong tự xuất luôn file Excel.

Bốn chế độ ở tab 3:

- **Chạy thử** — không gọi AI, không tốn lượt. Chỉ để xem khung HTML, bảng giá,
  liên kết nội bộ ra đúng chưa.
- **Sinh bài** — gọi AI thật, ghi ra `output/`, chưa đụng tới web.
- **Đăng nháp** — lên WordPress ở mục Bản nháp, khách không thấy.
- **Đăng thật** — hiện ra ngoài ngay. Có hỏi lại một lần.

Ô **Bỏ qua sản phẩm đã sinh bài rồi** để mặc định bật. Tắt máy giữa chừng, mở lại
bấm BẮT ĐẦU là nó chạy tiếp từ chỗ dừng.

---

## 5. Kho kiến thức, việc còn phải làm bằng tay

Hiện trạng số mục **chưa đối chiếu catalogue**:

| File | Tổng mục | Chưa kiểm chứng |
|---|---|---|
| abb-safering-safeplus.json | 14 | 7 |
| schneider-rm6.json | 15 | 11 |
| schneider-sm6.json | 13 | 10 |
| siemens-8djh.json | 6 | 4 |

Mục nào `"da_kiem_chung": false` thì phần mềm **không đưa cho AI**. Nghĩa là kiến
thức chưa kiểm tra không bao giờ lọt vào bài, nhưng cũng nghĩa là bài đang mỏng hơn
mức có thể.

Mở catalogue Schneider và ABB, đối chiếu, sửa `false` thành `true`. Mỗi mục sửa
đúng là **toàn bộ sản phẩm cùng dòng** đều được hưởng. Đây là việc cho ra nhiều
kết quả nhất so với công bỏ ra, ước chừng nửa buổi cho cả 4 file.

Chỉ sửa `da_kiem_chung`, đừng đổi cấu trúc file. Sửa xong bấm **Tải lại** ở tab 0
để xem cột "Chưa kiểm chứng" tụt xuống.

---

## 6. Cấu trúc file

```
CAI-DAT-LAN-DAU.bat  tải Python riêng, chạy 1 lần
PHAN-MEM.bat         mở phần mềm
KIEM-THU-30-BAI.bat  nghiệm thu, tự chấm 5 mốc

cauhinh.py           danh tính từng site, ngành hàng, từ cấm, danh sách cột
prompts.py           khung prompt, mẫu bài, khung HTML. Sửa văn phong ở đây
autopost.py          engine: gọi AI, chặn bịa số, ghép HTML, đăng WordPress
dulieu.py            đọc Excel, kho kiến thức, quản ảnh, SQLite
baocao.py            dựng dashboard và xuất Excel
kiemthu.py           bộ nghiệm thu
giao-dien.py         giao diện, không chứa logic sinh bài

cau-hinh.env         khoá và mật khẩu. KHÔNG gửi cho ai
du-lieu.db           sản phẩm và lịch sử bài. KHÔNG gửi cho ai
bang-dieu-khien.xlsx báo cáo xuất ra, ghi đè mỗi lần xuất
kienthuc/*.json      kiến thức theo dòng sản phẩm
anh/                 ảnh, tên file chứa mã sản phẩm
output/              file HTML sinh ra
python/              Python riêng, có sau khi chạy CAI-DAT-LAN-DAU
log.csv              nhật ký, mở bằng Excel
```

Muốn đổi văn phong bài viết: sửa `prompts.py`, mục `MAU`. Muốn đổi bố cục
trang: sửa `HTML` trong cùng file. Không cần đụng vào hai file còn lại.

---

## 7. Còn thiếu, biết mà chưa làm

- Chưa đặt ảnh đại diện cho bài (`featured_media`). Ảnh đã lên thư viện WordPress
  rồi, còn thiếu bước gán.
- Chưa có trang danh mục và trang so sánh, mới có trang sản phẩm lẻ.
- Chưa gán chuyên mục và thẻ khi đăng, bài rơi hết vào Chưa phân loại.
- Chưa có schema Product/FAQPage. Bài có khối FAQ nhưng không có dữ liệu có cấu
  trúc, mất cơ hội hiện rich result.
- Bộ chặn bịa số chỉ canh **con số có đơn vị** và mã rơ le. Câu chữ bịa kiểu
  "được nhiều nhà thầu tin dùng" nó không bắt được. Vẫn phải đọc bài trước khi đăng.
- Mới có 2 mẫu bài (`bao_gia`, `thong_so`). Cả hệ dùng chung 2 mẫu thì dễ lộ
  dấu vết máy sinh, nên viết thêm mẫu thứ ba và thứ tư.
