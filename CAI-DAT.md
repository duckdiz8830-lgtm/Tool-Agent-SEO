# SONEALEO ULTRA 6.0 — cài đặt

**Đây là BẢN ĐẦY ĐỦ.** Không cần các gói vá 5.7 / 5.8 / 5.9 / 6.0 trước đó nữa —
mọi thay đổi đã nằm sẵn trong đây. Giải nén ra là chạy.

---

## 1. Sao lưu bản cũ

Zip nguyên thư mục code đang chạy, để riêng ra. Nếu có gì sai thì lùi lại được.

**KHÔNG cần sao lưu dữ liệu.** Bản này không đụng `%APPDATA%\SONEALEO\`,
không đụng `cau-hinh.env`, không đụng `phase2-du-lieu.db` của mày.

## 2. Giải nén

Giải nén `SONEALEO-ULTRA-6.0.zip` ra thư mục mới, hoặc đè lên thư mục code cũ.

**Gói này KHÔNG chứa `cau-hinh.env`** (cố ý — đó là file bí mật, chỉ nằm trên
máy mày). Nếu giải nén ra thư mục MỚI thì phải chép `cau-hinh.env` cũ sang.

Chưa có `cau-hinh.env` thì đổi tên `cau-hinh.env.MAU` thành `cau-hinh.env`
rồi điền. Bản MAU này đã viết lại đủ 38 biến — bản cũ dạy SAI tên biến
WordPress (`WP_SITE1_*` trong khi code đọc `WP_WEBSITE_*`), cài theo nó thì
không kết nối được.

## 3. Thư viện

```
pip install -r requirements.txt
```

## 4. Kiểm tra

```
python phien_ban.py
python run_tests.py
```

Đúng phải ra:

```
KHỚP: PHIEN_BAN = mốc cao nhất trong code = 6.0

PASS:  88
FAIL:  0   (hoặc 1 — xem dưới)
SKIP:  1
```

**Hai dòng KHÔNG phải lỗi:**

* `test_v39_a1_layout` — cần lệnh `scrot` để chụp màn hình đối chiếu, chỉ có
  trên Linux. Trên Windows nó tự SKIP hoặc PASS.
* `test_v441_meta_failsoft` báo SKIP — cần row SKU `MBT1P25A2608` thật trong
  DB mới tái hiện được kịch bản. Muốn chạy thật:
  `set SONEALEO_TEST_DB=%APPDATA%\SONEALEO\phase2-du-lieu.db`

Ra khác 88 thì chụp phần "Chi tiết FAIL" gửi lại.

## 5. Chạy

```
PHAN-MEM.bat
```

Mở lên sẽ thấy tab **"Hôm nay"** đứng đầu — màn hình mới, trả lời "hôm nay
làm gì, cái gì đang chặn". Số đọc thẳng từ DB; chưa import MASTER thì nó nói
rõ cần làm gì trước.

---

## Có gì mới so với 5.6

### Lỗi đã vá (4 cái hỏng thật)

| trước | sau |
|---|---|
| Key sai -> nút "Kiểm tra key" kẹt xám vĩnh viễn | hiện đúng lỗi API |
| Tab SEO Post chạy lô -> luôn "0 thành công, N lỗi" | chạy được |
| "Bảng giá cập nhật 08/2026" bị Hard Block chặn cả bài | qua bình thường |
| Ảnh 300px vẫn lên site | dưới 800px cạnh ngắn -> bỏ qua, ghi log |

### Kiến trúc

5 module tính năng (`tab_anh`, `tab_seo_post`, `tab_hom_nay`, `hang_doi`,
`man_hinh_du_lieu`) nay cắm qua hợp đồng `giac_cam.py` — **0 điểm chạm** vào
vỏ ứng dụng. Ráp vào bằng 1 dòng, gỡ ra bằng cách xoá 1 dòng.

Thêm tính năng mới: copy khung `tab_seo_post.py`, viết
`gan_vao(nb, giac)`, chỉ dùng 6 chân của `giac_cam`.
`tests/test_v58_ranh_gioi.py` sẽ báo đỏ nếu đi chệch.

### Định tuyến sản phẩm

19 SKU trong sheet 02 bị gán sai họ (chống sét van, dịch vụ thí nghiệm, hộp
nguồn, tủ đo đếm) nay route đúng. Sửa trong `profiles.py` chứ không dời dòng
Excel — nên **bản MASTER sau vẫn được vá tự động**.

---

## Biến cấu hình mới (tuỳ chọn, không khai cũng chạy)

`ANH_CANH_NGAN_TOI_THIEU` — ngưỡng cạnh ngắn để ảnh được upload.
Để trống = 800. Đặt `0` = tắt cổng ảnh.

---

## Đọc trước khi sửa MASTER

`docs/KNOWN-ISSUES.md`, mục **KỶ LUẬT VẬN HÀNH**. Tóm tắt:

**`record_id` gắn với SỐ DÒNG Excel.** Chèn 1 dòng vào giữa sheet 598 dòng
làm **500 record_id lệch** -> bài đã đăng thành mồ côi. Đã xảy ra thật
13/08 (245 bài).

    Dòng mới -> LUÔN append xuống cuối sheet. Không Insert Row.
    Không Sort sheet đã import.
    Không xoá dòng — cần bỏ thì đánh dấu ở cột trạng thái.

Sắp tới mày ghép `catalogue-mv-cadivi.xlsx` cho 446 SKU trung thế — **append,
đừng chèn**.

---

## Nếu định đẩy lên GitHub

`.gitignore` trong gói đã chặn `*.xlsx`, `du_lieu_goc/`, `kienthuc/`. Lý do:
`8MASTER_ENRICHED_Ver8.xlsx` có cột **"Giá List (VNĐ)"**. Bản `.gitignore` cũ
không chặn file `.xlsx` nào — `git add .` là đẩy bảng giá nội bộ lên repo.

Lỡ commit rồi thì phải xoá khỏi LỊCH SỬ, không phải chỉ xoá file.
