# SONEALEO ULTRA — Ver 5.7
*(tên cũ: Lotech Autopost — đổi tên 31/07/2026, đọc lái "SEO Alone": SEO 1 mình từ Excel tới đăng bài, không đổi kiến trúc/logic bên trong)*


## Chạy phần mềm

Bấm đúp **`PHAN-MEM.bat`**. Lần đầu chưa có Python thì chạy
`CAI-DAT-LAN-DAU.bat` trước.

Muốn có icon riêng trên Desktop (không phải icon `cmd` mặc định của
Windows): chạy `TAO-SHORTCUT-CO-ICON.bat` **1 lần duy nhất** — tool tự tạo
shortcut "Lotech Autopost" trên Desktop, dùng icon trong thư mục `icon\`.
Từ sau chỉ cần bấm shortcut đó, không cần mở `PHAN-MEM.bat` nữa.

## 5.7 — cổng chất lượng ảnh + sửa 2 tab hỏng

- **Ảnh dưới 800px cạnh ngắn KHÔNG còn được upload.** Trước 5.7 ngưỡng này
  chỉ chạy khi tự nhớ bấm `LOC-KHO-ANH.bat`; nay nó nằm ngay trên đường
  upload thật, không bỏ sót được nữa. Ảnh dưới ngưỡng bị bỏ qua và ghi rõ
  kích thước vào log, ô ảnh để trống thay vì đẩy ảnh vỡ lên site.
- **Tab "SEO Post" chạy hàng loạt đã hoạt động trở lại.** Trước 5.7 mọi bài
  đều báo lỗi do dùng chung kết nối cơ sở dữ liệu giữa hai luồng.
- **Nút "Kiểm tra key" không còn kẹt** khi key sai — nay hiện đúng lỗi thật.
- **Bài có ngày tháng không còn bị chặn oan.** "Bảng giá cập nhật 08/2026"
  trước đây bị hàng rào chống bịa số hiểu nhầm là thông số kỹ thuật. Hàng
  rào với số kỹ thuật giữ nguyên độ chặt.
- `cau-hinh.env.MAU` viết lại đủ 38 biến. Bản cũ dạy sai tên biến
  WordPress — cài máy mới theo nó sẽ không kết nối được.

## 4.4.1.4 — ảnh production

- Watermark upload mặc định: **domain + hotline** (2 dòng), không sửa ảnh gốc.
- Hotline nhập một lần ở **Cấu hình → Website WordPress → Hotline watermark**.
- Cho phép **cùng một ảnh dùng cho nhiều SKU**; tool chỉ đếm/cảnh báo reuse, không chặn.
- Một slot ảnh lỗi không được kéo chết cả bộ; ảnh hợp lệ vẫn gắn vào gallery + body.

## Cấu trúc thư mục (chuẩn hoá từ Ver 5.1 cũ, hiện tại Ver 5.7)

```
├── PHAN-MEM.bat                  ← bấm để chạy phần mềm
├── CAI-DAT-LAN-DAU.bat           ← chạy 1 lần đầu tiên nếu chưa có Python
├── TAO-SHORTCUT-CO-ICON.bat      ← chạy 1 lần để có icon riêng trên Desktop
├── KIEM-THU-30-BAI.bat           ← test nhanh qua dòng lệnh, không cần mở giao diện
├── 5-KIEM-TRA-KET-QUA.bat        ← xem lại kết quả đã đăng
├── cau-hinh.env.MAU              ← đổi tên thành cau-hinh.env rồi điền API key
├── icon/                         ← icon cho shortcut
├── giao-dien.py, *.py            ← TOÀN BỘ code chính — GIỮ NGUYÊN Ở GỐC,
│                                    không di chuyển (tránh rủi ro vỡ import)
├── du_lieu_goc/                  ← file Excel mẫu đi kèm
├── kienthuc/                     ← dữ liệu tham khảo catalogue đã đọc trước đó
├── tests/                        ← TOÀN BỘ file test (86 file, gom lại từ đợt dọn Ver 5.1 cũ,
│                                    trước đây nằm lẫn ở gốc)
│   └── test_*.py                    Chạy: python3 tests/test_v51_patch.py
│                                    (chạy TỪ THƯ MỤC GỐC, không cd vào tests/ —
│                                    một số test đọc file Excel mẫu theo đường dẫn
│                                    tương đối tính từ thư mục gốc)
└── docs/                         ← TOÀN BỘ tài liệu (gom lại từ đợt dọn Ver 5.1 cũ)
    ├── NHAT-KY-THAY-DOI.md          Đổi gì qua từng bản — bản mới nhất ở đầu file
    ├── KNOWN-ISSUES.md               Lỗi/thiếu đã biết, chưa sửa
    ├── SPEC.md, HUONG-DAN*.md         Tài liệu kỹ thuật/hướng dẫn dùng
    ├── ARCHITECTURE-DRAFT-4-PROFILES.md, DATA-AUDIT-4-PROFILES.md
    └── lich-su-phien-ban/            CHANGELOG/TEST-REPORT/BAO-CAO-KHOI-LUONG
                                       của TỪNG BẢN (VER 3.6 → VER 5.1) — tài
                                       liệu lịch sử, ít khi cần đọc lại.
```

**Vì sao code Python KHÔNG bị gom vào thư mục con:** đã cân nhắc — chuyển
`giao-dien.py` và các file cùng cấp vào 1 thư mục riêng có rủi ro thật (cách
Python tìm module phụ thuộc vị trí file), trong khi lợi ích chỉ là thẩm mỹ.
Áp dụng đúng nguyên tắc đã thống nhất: *"code chạy được thì để yên"*.
Chỉ gom `.md` (tài liệu — không ảnh hưởng code) và `test_*.py` (đã tự kiểm
tra kỹ, sửa đường dẫn, chạy lại xác nhận không vỡ gì trước khi gom).

## Đọc gì trước

1. `docs/NHAT-KY-THAY-DOI.md` — biết bản mới nhất đổi gì.
2. `docs/lich-su-phien-ban/CHANGELOG-VER51.md` — chi tiết bản này.
3. `docs/KNOWN-ISSUES.md` — biết cái gì còn thiếu/chưa sửa trước khi dùng.
