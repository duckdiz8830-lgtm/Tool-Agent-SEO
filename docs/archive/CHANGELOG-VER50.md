# CHANGELOG-VER50.md

Bản mới nhất ở đầu file. Xem `CHANGELOG-VER499.md` cho lịch sử trước đó.

---

## LOTECH AUTOPOST VER 5.0 CLAUDE — Vá lỗi MAX_TOKENS + hoàn thiện UX trang sản phẩm — 30/07/2026

Từ ảnh chụp + log production thật (30/07/2026, batch 50 sản phẩm máy biến
áp): 6 góp ý UX trên trang thật + 1 bug thật nghiêm trọng (bài bị cắt giữa
chừng, tốn quota).

### 1. VÁ BUG THẬT — "Bài bị cắt vì vượt giới hạn token"

**Chẩn đoán (đọc code + đối chiếu log console kiểm tra model):** console
log liệt kê MỌI model khả dụng đều ghi "có suy nghĩ ngầm" (Gemini 3.x có
tính năng thinking/suy luận nội bộ BẬT MẶC ĐỊNH). Đọc `ai_wp_adapter.py::
goi_ai_that()` xác nhận: request gửi Google **KHÔNG có `thinkingConfig`**
— nghĩa là phần suy nghĩ ngầm được dùng KHÔNG GIỚI HẠN, và phần này tính
CHUNG vào `maxOutputTokens` (24000) với câu trả lời JSON thật. Nếu suy
nghĩ ngầm ăn hết phần lớn ngân sách, JSON trả lời bị cắt cụt giữa chừng →
`finishReason: MAX_TOKENS`.

**Bằng chứng gián tiếp từ log thật:** 4/5 sản phẩm đầu batch phải đổi cặp
key/model mới thành công (tỷ lệ bất thường cao) — ngay cả bài "thành
công" cũng đang né tránh bị cắt bằng cách đổi model, không phải model dư
sức thật. Nghi ngờ chính đáng: Delta Context (Ver 4.9.9) bắt AI phải SO
SÁNH/suy luận (phức tạp hơn mô tả đơn thuần) — nhiều khả năng khiến model
"nghĩ" nhiều hơn, tăng đúng lúc bản đó ra mắt.

**Vá theo cả 2 hướng (Thịnh chọn):**
1. `thinkingConfig.thinkingBudget = 6000` — trần cứng cho suy nghĩ ngầm,
   đủ để model suy luận Delta Context nhưng không ăn hết ngân sách.
2. `maxOutputTokens` nâng 24000 → 48000 (model hỗ trợ tới 65536 theo log
   kiểm tra — 48000 chừa khoảng cách an toàn, không sát trần tối đa).

### 2. Title bỏ mã hàng, thêm "Báo Giá"

Ver 4.9.9 nhét cả mã hàng vào title ("...MBT1P15A2608 (Lõi Amorphous)") —
Thịnh xem thật trên site thấy "ngốc nghếch". Mã hàng vẫn hiện đầy đủ ở
Hero/bảng thông số/SKU WooCommerce, không mất thông tin, chỉ không lặp
lại trong H1. Đồng thời sửa lỗi làm SÓT cụm "Báo Giá" (yêu cầu gốc từ đầu
đã có, Ver 4.9.9 quên) — nhận lỗi, đã thêm.

Công thức mới: `[Loại máy] [Dầu/Khô] [Thương hiệu] [Công suất]kVA
([Đặc tính lõi]) - Báo Giá`.

### 3. CTA nổi bật hơn — KHÔNG animation

Thịnh muốn CTA "Liên Hệ Báo Giá" có chút động để không đứng yên. Đã cân
nhắc: animation CSS (pulse/nhấp nháy) BẮT BUỘC cần `@keyframes`, mà
`@keyframes` chỉ hoạt động trong `<style>` block hoặc file CSS — không
thể nhét vào thuộc tính `style=""` trên 1 thẻ (giới hạn kỹ thuật thật của
inline style, không phải chưa cố làm). Thịnh chọn: bỏ animation, tăng độ
nổi bật bằng thị giác tĩnh — nút "Yêu cầu báo giá" tăng cỡ chữ 14px→16px,
padding lớn hơn, thêm `box-shadow` màu cam nhẹ tạo cảm giác nổi khối.

### 4. Bảng so sánh công suất — SKU đã đăng thành link

`db_phase2.tim_san_pham_cung_dong()` thêm tham số `site` (optional): có
`site` → JOIN với `bai_viet_phase2` lấy URL cho SKU anh em ĐÃ ĐĂNG THẬT ở
ĐÚNG site đó. `render_phase2.khoi_so_sanh_cong_suat()` hiện SKU có URL
thành link bấm được; SKU chưa đăng vẫn hiện số liệu dạng text thường —
KHÔNG bịa/không tạo link chết. Không truyền `site` (hành vi cũ Ver 4.9.8)
→ mọi SKU đều là text, an toàn ngược 100%.

### 5. Placeholder chèn ảnh

`render_phase2.khoi_anh_placeholder()` — khối viền cam nét đứt, nổi bật
hẳn khỏi nội dung thật, chèn ngay sau Hero (vị trí ảnh sản phẩm chính).
Tool KHÔNG tự sinh/tải ảnh (rủi ro bản quyền + sai sản phẩm) — chỉ đánh
dấu rõ vị trí để Thịnh tự thêm tay, dòng chữ nhắc rõ "XOÁ DÒNG NÀY KHI
THAY ẢNH THẬT" để không bị quên sót khi lên bài chính thức.

### 6. "Đặc điểm" chia nhiều đoạn thay vì 1 khối

Ver 4.9.9 từng sửa theo hướng "1 đoạn liền mạch, không tách khối" — Thịnh
xem thật thấy đọc mỏi mắt ("viết thành 1 cục không được ngon mắt"). Sửa
lại: khuyến khích chia 2-3 đoạn `<p>` ngắn, mỗi đoạn 1 ý (VD kỹ thuật /
vận hành lâu dài), không bắt buộc đúng khuôn nếu dữ liệu không đủ.

### 7. Xem trước dạng trang HTML thật

Tab "Sinh & Đăng" thêm nút "Mở trong trình duyệt" — dựng bài (Mock, không
tốn quota) rồi ghi ra file `.html` tạm, mở bằng `webbrowser.open()` (module
chuẩn Python, không cần cài thêm) — nhìn gần đúng layout thật (đã style
INLINE từ Ver 4.9.9 nên hiện màu/nút đúng ngay cả khi mở file rời).

### File sửa

`ai_wp_adapter.py` (thinkingConfig + maxOutputTokens), `render_phase2.py`
(`dung_tieu_de` bỏ mã hàng+thêm Báo Giá, CTA nổi bật hơn,
`khoi_so_sanh_cong_suat` link, `khoi_anh_placeholder` mới, wire vào
`dung_bai_html`), `db_phase2.py` (`tim_san_pham_cung_dong` thêm tham số
`site`/url), `prompts_phase2.py` (guidance `dac_diem_html` chia đoạn),
`giao-dien.py` (nút + hàm mở trình duyệt, wire site vào 2 điểm gọi thật,
đổi tiêu đề bản), `test_v498_patch.py` + `test_v499_patch.py` (cập nhật
theo hành vi mới có chủ đích).

### File mới

`test_v50_patch.py` (22 test: thinkingConfig/maxOutputTokens đúng giá
trị, title đúng công thức mới, CTA nổi bật, bảng so sánh link đúng/an
toàn ngược khi không truyền site, placeholder ảnh, guidance chia đoạn,
hàm+nút mở trình duyệt tồn tại đúng).

### Không làm

- Chưa verify thinkingBudget=6000 là mức TỐI ƯU thật (chỉ là mức khởi
  điểm hợp lý) — cần Thịnh chạy thật, quan sát log MAX_TOKENS còn xảy ra
  không, điều chỉnh lại nếu cần.
- Chưa có animation CTA — giới hạn kỹ thuật thật của inline style, Thịnh
  đã đồng ý bỏ.
- Thông số kỹ thuật máy biến áp vẫn mỏng — ngoài phạm vi code, cần đợt
  enrich riêng (đã thống nhất từ trước).
- Pillar page dầu/khô, cơ chế Hard Block fail nhảy sản phẩm tiếp theo —
  vẫn treo từ các bản trước, chưa có xác nhận mới.
