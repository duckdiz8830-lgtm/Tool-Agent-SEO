# Hướng dẫn dùng Ver 3.5 — cách chạy hiệu quả nhất

## Cài đặt

```
pip install tksheet
```

Giải nén ZIP vào **thư mục mới**, đừng đè lên thư mục đang chạy. ZIP này
không kèm `phase2-du-lieu.db` và không kèm `cau-hinh.env` thật — chép hai
file đó từ thư mục cũ sang. (Có `cau-hinh.env.mau` để tham khảo nếu làm
lại từ đầu.)

## Bước bắt buộc trước tiên: import MASTER Ver5

Tab Hàng đợi đọc hạng nguyên liệu từ dữ liệu đã import. Nếu vẫn đang chạy
MASTER cũ thì mọi SKU sẽ hiện hạng **Vừa** hoặc **Đói**, không có cái nào
**Đủ** — không phải tool sai, là dữ liệu trong DB chưa có số.

Vào tab `2. Nhập dữ liệu`, nhập `6MASTER_ENRICHED_Ver5.xlsx`. Sau khi
import, con số đúng phải là **150 Đủ / 15 Vừa / 80 Đói**. Thấy khác là
import chưa ăn.

---

## Quy trình chạy hằng ngày

Từ bản này trở đi, **mở tool là vào tab Hàng đợi trước**, không phải tab
Sinh & Đăng.

### 1. Liếc 4 ô đếm

Chưa render / Chờ duyệt / Đã đăng / Cần kiểm. Đây là câu trả lời cho "lô
245 đang ở đâu" mà trước kia phải mở hai ba tab mới ghép ra được.

Ô **Cần kiểm** là ô quan trọng nhất. Nó đếm số SKU có cảnh báo dữ liệu
lấy từ cột `Ghi chú - Cần kiểm lại` của MASTER Ver5 — Po/Pk nội suy, số
Amorphous nghi chép nhầm, lệch công suất trong catalogue KP. Ô này khác 0
thì đừng render nhóm đó vội.

### 2. Lọc theo hạng, làm từng hạng một

**Đừng chọn cả 245 rồi bấm chạy.** Làm theo hạng, vì mỗi hạng cần cách
kiểm khác nhau:

| Hạng | Số SKU | Làm gì |
|---|---|---|
| **Đủ** | 150 | Render trước. Đây là nhóm ra được bài tử tế. QA tay 10 bài **không phải THIBIDI** trước khi render cả lô — đường dữ liệu của THIBIDI khác 193 SKU còn lại, THIBIDI ổn không suy ra được nhóm khác ổn |
| **Vừa** | 15 | Render sau. Bài sẽ mỏng hơn, chấp nhận được |
| **Đói** | 80 | Để cuối cùng, hoặc bỏ hẳn. Tool có cho render nhưng sẽ hỏi lại một lần |
| **Có cảnh báo** | 22 | Xem trước khi động vào bất cứ hạng nào |

### 3. Chọn và lưu

Bấm vào ô vuông cột đầu để tick từng dòng, hoặc `Chọn hết (theo bộ lọc)`
để tick toàn bộ dòng đang hiện. Xong bấm **Lưu lựa chọn vào hàng đợi**.

Tab Hàng đợi **không render**. Nó chỉ ghi cờ "sắp làm cái này" vào cơ sở
dữ liệu. Sang tab `4. Sinh & Đăng`, bật *chỉ chạy mục đã chọn*, rồi bấm
chạy như cũ.

Tách vậy là cố ý: một chỗ quyết định làm gì, một chỗ thực thi. Đổi ý thì
quay lại tick lại, không cần cơ chế huỷ tác vụ phức tạp.

---

## Ba mẹo đáng tiền nhất

**Lọc "Có cảnh báo" mỗi lần sau khi enrich dữ liệu.** Mỗi đợt bổ sung
catalogue đều có khả năng sinh số sai. Lọc cảnh báo là cách rẻ nhất để bắt
trước khi nó thành bài viết.

**Chạy lô nhỏ 10–15 SKU, xem kết quả, rồi mới chạy tiếp.** Chạy 245 phát
một thì lỗi hệ thống sẽ nhân lên 245 lần trước khi ai kịp nhìn.

**Ô "Chưa render" giảm chậm hơn dự kiến là bình thường.** Nó tính cả SKU
lỗi và SKU chưa từng đụng tới. Muốn biết chính xác thì đối chiếu với tab
`5. Theo dõi`.

---

## Cái tab này CỐ Ý không làm

- Không render, không đăng, không gọi AI. Chỉ đọc và ghi đúng một cờ.
- Không sửa dữ liệu. Muốn sửa số thì sửa ở MASTER rồi import lại.
- Không thay thế 10 tab cũ. Chúng còn nguyên, chỉ là ngày thường không
  cần mở.

## Khi tab không hiện ra

Thiếu `tksheet` thì tab vẫn hiện nhưng chỗ bảng sẽ ghi rõ thiếu gì và
cách cài. Nếu tab biến mất hẳn, mở cửa sổ đen (console) xem dòng bắt đầu
bằng `[Ver 3.5]`.
