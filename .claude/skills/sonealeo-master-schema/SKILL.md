---
name: sonealeo-master-schema
description: Cấu trúc file MASTER Excel của SONEALEO (9MASTER_Ver16_SACH_TEXT.xlsx, 4 sheet, ~5.264 SKU thiết bị điện) và luật xử lý dữ liệu thông số kỹ thuật. Dùng skill này BẤT CỨ KHI NÀO người dùng nhắc tới MASTER, file 9MASTER, sheet 01_Cap_Dien / 02_Tu_Va_Thiet_Bi_Dong_Cat / 03_May_Bien_Ap_Do_Luong / 04_Phu_Kien_Va_Khac, cột dữ liệu SKU, bảng thông số, điền/enrich dữ liệu sản phẩm, join catalogue, hay import MASTER vào tool — kể cả khi họ chỉ upload file Excel và bảo "xem giúp". Skill chứa luật cấm bịa số liệu, quy trình import, và script tự đọc schema.
---

# MASTER Excel — cấu trúc và luật xử lý

## Luật số 1: không bao giờ bịa số liệu kỹ thuật

Đây là luật quan trọng nhất trong toàn bộ skill này, và nó có lý do thương mại chứ không phải đạo đức suông.

Dữ liệu ở đây là thông số thiết bị điện trung/hạ thế: dòng định mức, cấp điện áp, tiết diện, tổ đấu dây. Một con số sai đi vào bài viết là một con số sai đi vào quyết định mua hàng của kỹ sư điện. Nó không dừng ở lỗi SEO.

Quy tắc:
- Mọi thông số phải truy được về **một trang catalogue có nguồn**. Không có nguồn thì không điền.
- Mục không chắc chắn → gắn cờ **`CAN_KIEM`**. Không bao giờ để một con số nghe hợp lý thay cho ô trống.
- Ô trống là trạng thái hợp lệ. Con số bịa thì không.

Khi được yêu cầu "điền cho đủ" hoặc "ước lượng đại đi" — từ chối phần không có nguồn, nói rõ dòng nào thiếu nguồn, và đề xuất cách lấy nguồn.

## Luật số 2: không gán dữ liệu chéo dòng sản phẩm hay cấp điện áp

Hai SKU trông giống nhau không có nghĩa thông số dùng chung được. Cáp 0,6/1kV và cáp 12/20kV có thể cùng tiết diện nhưng khác toàn bộ phần còn lại. Máy biến áp dầu và khô cùng công suất khác tổn hao, khác tổ đấu dây, khác tiêu chuẩn áp dụng.

Không nội suy, không "chắc cũng vậy". Có nguồn xác nhận cho đúng SKU đó thì mới gán.

## Cấu trúc file

File đang dùng: `9MASTER_Ver16_SACH_TEXT.xlsx`

Bốn sheet:

| Sheet | Nội dung |
|---|---|
| `01_Cap_Dien` | Cáp điện |
| `02_Tu_Va_Thiet_Bi_Dong_Cat` | Tủ và thiết bị đóng cắt |
| `03_May_Bien_Ap_Do_Luong` | Máy biến áp, thiết bị đo lường |
| `04_Phu_Kien_Va_Khac` | Phụ kiện và nhóm khác |

Tổng ~5.264 SKU.

**Các phiên bản MASTER cũ (Ver11–Ver15) đã bỏ.** Nếu người dùng nhắc tới chúng, hỏi lại — nhiều khả năng là nhầm file.

### Bản đồ cột

Xem **`references/cot.md`** — trích tự động từ `profiles.py`, dict `PROFILES`, trên bản 5.5. Mức tin cậy: **xác nhận từ code**.

Phân biệt hai thứ, đừng lẫn:

- `references/cot.md` = cột tool **chấp nhận**. Cột nào không khai trong `cot_import` thì **không có đường vào hệ thống**, dù Excel có cột đó. Đây là bẫy đã cắn một lần: `profiles.py` có ghi chú về cột catalogue tồn tại trong Excel nhưng không khai trong `cot_import` nên dữ liệu rơi im lặng.
- `scripts/doc_schema.py` = cột file Excel **thật sự có** và tỉ lệ trống của chúng.

Hai cái lệch nhau chính là chỗ dữ liệu biến mất. Khi debug "sao điền rồi mà không ra", so hai cái này trước.

### Chênh lệch dữ liệu giữa 4 sheet

| Sheet | Số cột nhận | Cột thông số kỹ thuật |
|---|---:|---|
| `01_Cap_Dien` | 27 | nhiều (giải mã + catalogue) |
| `02_Tu_Va_Thiet_Bi_Dong_Cat` | 9 | **không có cột nào** |
| `03_May_Bien_Ap_Do_Luong` | 31 | nhiều nhất |
| `04_Phu_Kien_Va_Khac` | 16 | vừa |

Sheet tủ/thiết bị đóng cắt chỉ có 8 cột hành chính + 1 URL catalogue. **Không có một cột thông số kỹ thuật nào.** Nghĩa là mọi SKU tủ trung thế/RMU sinh ra nội dung chỉ khác nhau ở tên và giá — trùng lặp là chắc chắn, không phải rủi ro.

Đây là nhóm sếp Quân ưu tiên vì biên lợi nhuận cao. Nếu có kế hoạch generate hàng loạt nhóm này, nêu con số 9 cột ra trước.

## Quy trình import MASTER vào tool

Đúng thứ tự, không bỏ bước:

1. Load MASTER trong SONEALEO
2. Tool hỏi *"MASTER có thêm cột mới"* → chọn **Yes**
3. Sang tab **Hàng đợi**
4. Bấm **"Chọn các SKU CHƯA render"**
5. Bấm **Lưu**

Bước 3–5 bắt buộc vì bản ghi mới mặc định `selected=0`. Bỏ qua thì chúng nằm im trong DB và không bao giờ được render — trông như import hỏng, thực ra chỉ là chưa chọn.

Trước mỗi batch generate, chạy **"Soát mỏng/trùng…"** ở tab Hàng đợi. Batch nào toàn MỎNG thì bỏ qua, đừng đốt quota.

## Tình trạng dữ liệu hiện tại

Biết trước để khỏi phát hiện lại từ đầu:

- **336 dòng MBA mới**: mới điền 5/17 dòng bảng thông số
- **446 SKU trung thế**: chưa join `catalogue-mv-cadivi.xlsx`
- **1.216 SKU cáp có thông số dòng định mức** → nội dung unique ~66%, đáng generate
- **2.171 SKU cáp không có dữ liệu dòng** → nội dung trùng ~97%, **gộp vào trang danh mục, đừng generate riêng**
- **17 SKU trùng, 19 SKU sai outline** — đã hạ ưu tiên có chủ đích
- **Sheet tủ/đóng cắt: 0 cột thông số** — xem bảng chênh lệch ở trên

### Bài học đã trả giá: enrich dữ liệu một mình không cứu được trùng lặp

Hai SKU cáp anh em sinh ra HTML **giống nhau 99,96%**. Enrich thêm dữ liệu chỉ kéo xuống 99,9% — gần như không đổi. Phần trùng nằm ở boilerplate template, không nằm ở dữ liệu.

Muốn thật sự khác biệt cần đủ ba thứ cùng lúc: enrich dữ liệu **+** sửa boilerplate **+** dữ liệu catalogue. Thiếu một thì đừng kỳ vọng.

Hệ quả: khi có người đề xuất "cứ thêm dữ liệu vào rồi generate", nêu lại con số này.

## Script

```bash
python3 scripts/doc_schema.py /duong/dan/9MASTER_Ver16_SACH_TEXT.xlsx

# Xuat thang ra file de dan vao references/cot.md
python3 scripts/doc_schema.py MASTER.xlsx --ra references/cot.md

# Xem nhieu gia tri mau hon cho tung cot
python3 scripts/doc_schema.py MASTER.xlsx --mau 8
```

Script in ra mỗi sheet: số dòng, và với từng cột — kiểu dữ liệu, tỉ lệ ô trống, số giá trị duy nhất, vài giá trị mẫu. Cột trống >90% được đánh dấu riêng vì đó thường là cột đã bỏ hoặc chưa điền.

Script **chỉ đọc**, không sửa file.
