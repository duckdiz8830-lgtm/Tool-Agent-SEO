# SONEALEO ULTRA 6.2 — cách chạy

## 1. Chép đè 3 file vào thư mục gốc SONEALEO

    kien_thuc_bien_thien.py
    render_phase2.py
    phien_ban.py

Backup 3 file cũ trước.

## 2. Kiểm tra trước khi đăng

    python kiem_tra_6_2.py

Phải ra `=> SẴN SÀNG CHẠY`. Nếu không, dừng, đừng đăng.

Sáu điều nó kiểm:
- 6 bài dựng được, không rỗng
- render 2 lần ra y hệt (đăng lại không đổi chữ)
- trùng lặp TB < 50%
- câu miễn trừ catalogue còn nguyên
- công thức tổn hao/năm còn in ra
- không có số bịa

## 3. Chạy thử 10 SKU trước

Chọn 10 SKU khác nhau (dầu / khô / amorphous / ≥1600kVA / ≤400kVA), render,
xem mắt. Đưa Quân xem. **Đừng chạy 580 phát một.**

## 4. Chạy thật

Backup HTML cũ trước khi đè. Không rollback được thì đừng chạy hàng loạt.

---

## Không tốn quota Gemini

Khối kiến thức do code sinh. Chỉ phần văn AI (mở bài / đặc điểm / ứng dụng /
hướng dẫn chọn) mới gọi Gemini — phần đó không đổi ở 6.2.

## Muốn quay lại khối kiến thức cũ

    SNL_KHOI_KIEN_THUC_CU=1

Hàm cũ vẫn còn nguyên trong code, chỉ không được gọi.

## Vẫn còn

SKU không có thông số riêng thì vẫn trùng. Đó là vấn đề dữ liệu, code không sửa được.
