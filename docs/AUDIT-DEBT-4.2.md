# RÀ NỢ AUDIT 3.7 TRÊN RELEASE 4.2

Nguồn đối chiếu: bản audit 3.7, source release 4.2 và test/mocks cục bộ. Không POST site thật, không gọi Gemini thật.

| Mục audit 3.7 | Trạng thái 4.2 | Bằng chứng / lý do |
|---|---|---|
| 9. Uploader cũ nuốt lỗi update alt | ĐÃ XỬ LÝ | `ai_wp_adapter.py::cap_nhat_meta_anh_media()` kiểm HTTP >=300 và trả lỗi/warning; R41 mock PASS. |
| 10. Workspace thiếu slug | ĐÃ XỬ LÝ | `tab_anh.py` lấy `render_phase2.dung_slug(row)` và truyền khi tạo workspace. |
| 11. Workspace collision giữa dataset version | CHƯA LÀM ĐƯỢC | `workspace_anh.tim_workspace(goc, sheet, sku)` vẫn identity theo sheet+SKU. Đổi identity/migrate thư viện ảnh cũ là thay kiến trúc/state, vượt luật không refactor; không tô PASS. |
| 12. `so_dong` không phải source row | ĐÃ XỬ LÝ | `tab_anh.py` ưu tiên `source_row`, fallback index khi nguồn không có. |
| 13. Tab ảnh có thể lấy wp_id sai site/mẫu | ĐÃ XỬ LÝ MỘT CÁCH BẢO THỦ | dashboard ảnh lọc site hiện tại; chỉ nhận wp_id khi record có đúng một article trên site, không chọn ngẫu nhiên giữa nhiều mẫu. |
| 14. Hai hệ ảnh cùng active | HẾT HIỆU LỰC UI | call tab ảnh legacy đã ẩn/comment, code cũ giữ để rollback nhưng user-facing chỉ còn workspace mới. |
| 15. Tab ảnh cũ dùng `ma_site` sai key | HẾT HIỆU LỰC UI | cùng lý do mục 14: tab legacy không còn được khởi tạo. Không sửa dead code. |
| 16. Validation chỉ logger | ĐÃ XỬ LÝ TRƯỚC 4.2 | R54: record `nghi_van_dien_ap=True` cho AI=0, WP=0. |
| 17. Dataset cũ không deactivate | ĐÃ XỬ LÝ | `db_phase2.py` deactivate active version cũ cùng profile khi xác nhận dataset mới; list current lọc `active=1`. |
| 18. Woo category gửi name | ĐÃ XỬ LÝ TRƯỚC 4.2 | R55 local payload categories=`[{"id":123}]`. |
| 19. Product schema SKU lệch publish SKU | ĐÃ XỬ LÝ TRƯỚC 4.2 | R55 local built schema SKU=`SKU-B2`. |
| 20. Product schema description rỗng | ĐÃ XỬ LÝ TRƯỚC 4.2 | R55 local description=`Mô tả cuối.` từ final representation. |
| 21. FAQ schema sinh rồi bỏ | ĐÃ XỬ LÝ LOCAL 4.2 | production Woo truyền `faq_schema`, meta `_snl_faq_schema_jsonld`; WPCode đọc key này; local mock + `php -l` PASS. Site thật chưa verify. |
| 22. Product schema chưa chắc ra frontend | PARTIAL | snippet `WPCode-SCHEMA-SONEALEO.php` đọc Product + FAQ meta và PHP syntax sạch. Theo luật task không verify site thật; Thịnh phải View Source. |
| 23. Normal WordPress Post ít schema hơn | CHƯA LÀM ĐƯỢC | `dang_wp_that()` không có schema transport và WPCode hiện chỉ chạy `is_product()`. Tự thêm meta cho WP Post chưa chứng minh site đã register/expose meta và cần frontend policy riêng; không vá đoán. |
| 24. Global stdout race | ĐÃ XỬ LÝ | `ChuyenHuongIn` router map queue theo thread; worker đăng ký/hủy route thay vì mỗi worker swap stdout mù. Full suite + R59 sạch Tk/thread. |
| 25. UI callback lỗi `except: pass` | ĐÃ XỬ LÝ | callback queue log traceback `LỖI UI callback` thay vì nuốt lỗi. |
| 26. Đóng app không dừng hết worker | PARTIAL | `_dong()` set các stop event đang có và cancel `after`; chưa join worker vì code không có registry thread. Thêm registry/join là refactor vượt luật. |
| 27. Force Stop ngủ hết `sleep` | ĐÃ XỬ LÝ | real batch/article jobs dùng Event `.wait()` nên stop có thể ngắt khoảng nghỉ. |
| 28. Mock batch cleanup không chặt | ĐÃ XỬ LÝ | default message, per-record exception isolation, DB/UI cleanup trong `finally`. |
| 29. Counter success tính cả skipped | ĐÃ XỬ LÝ | summary production tách tạo/cập nhật, bỏ qua, lỗi. |
| 30. Nén ảnh không đảm bảo <150KB | ĐÃ XỬ LÝ | R38 fixture 1200x4000 -> 360x1200, 6.7KB. |
| 31. EXIF orientation + alpha | ĐÃ XỬ LÝ | R39 EXIF output 1200x800; alpha composite nền trắng và image-filter giữ PNG hợp lệ. |
| 32. HTML ảnh không escape | ĐÃ XỬ LÝ | R40 có `&amp;`, `&quot;`, `&lt;`. |
| 33. Corrupt meta bị coi như không có | ĐÃ XỬ LÝ | `doc_meta()` backup file corrupt rồi raise lỗi thay vì silently return None. |
| 34. Comment atomic replace quá lời | ĐÃ XỬ LÝ | comment hiện ghi `atomic visibility; không tuyên bố durability khi mất điện`. |
| 35. `tim_workspace()` O(N²) | ĐÃ XỬ LÝ | index workspace cache theo sheet, lookup O(1) sau lần scan. |
| 36. Reuse count stale | ĐÃ XỬ LÝ | reuse chỉ tính asset khi file vật lý còn tồn tại và hash hiện tại khớp. |
| 37. SQLite concurrency | ĐÃ XỬ LÝ MỨC DESKTOP | `WAL` + `busy_timeout=5000`; không dựng write service vì no-refactor/single-user. |
| 38. Installer Tk ABI + dependency drift | PARTIAL | dependency đã gom `requirements.txt`, cả embedded/fallback dùng chung; BAT vẫn copy Tk từ system Python nên ABI risk chỉ có thể verify trên Windows, môi trường audit Linux không đủ bằng chứng. |
| 39. Claude legacy thiếu `anthropic` | HẾT HIỆU LỰC VỚI UI 4.2 / LEGACY CÒN | `cauhinh.luu_gemini()` cố định `NHA_CUNG_CAP=gemini`; `autopost.py` vẫn giữ legacy CLI/env Claude. Không cài thêm dependency không dùng vào release. |
| 40. Basic Auth cho phép HTTP production | ĐÃ XỬ LÝ | `cauhinh.luu_website()` bắt HTTPS, chỉ cho HTTP localhost/127.0.0.1. |
| 41. Secret plaintext | CHẤP NHẬN RỦI RO / GIẢM PHƠI BÀY | config vẫn plaintext theo app single-user; `.gitignore` chặn env/DB và ZIP 4.2 loại runtime env/DB. Không tự thêm secret vault. |
| 42. Runner PASS/SKIP classification bug | ĐÃ XỬ LÝ | R06/R07 PASS; synthetic exit0 im lặng và output `FAIL 1` đều làm runner exit 1. |
| 43. Test PASS giả do fixture thiếu | ĐÃ XỬ LÝ CHO 3 LEGACY ĐÃ NÊU | R56/R57/R58 = 21/21, 17/17, 32/32; tksheet thiếu được SKIP 77 công khai, không PASS giả. |
| 44. Version traceability | ĐÃ XỬ LÝ CURRENT STRING; LỊCH SỬ GIỮ NGUYÊN | README/BAT/current GUI = 4.2; README test count=66; historical comments không rewrite. Không tạo version module mới vì no-refactor. |
| 45. `giao-dien.py` God Class | KHÔNG LÀM — BỊ CẤM | audit đề nghị tách controller, nhưng task cấm refactor/tách file/di chuyển hàm. |
| 46. `.snl-page` wrapper/class mode | HẾT LỖI | `giao_dien_2_5.py` emit `<div class="snl-page">` qua `_c("page")`. |
| 47. Tracker dead/disabled | ĐÃ XỬ LÝ | nút tracker disabled đã ẩn khỏi release UI, code khác không bị đụng. |

## Phần cố ý chưa ký PASS

- Dataset-version image workspace ownership: cần policy/migration riêng, không vá trong release stabilization.
- Schema frontend thật: cần WordPress staging/production View Source; local chỉ chứng minh payload + PHP syntax.
- Normal WordPress Post schema delivery: cần quyết định contract riêng với WordPress meta/frontend.
- Graceful close có `join()` worker: cần worker registry, bị cấm refactor trong task này.
- Windows embedded Tk ABI: chỉ Windows smoke/installer mới chứng minh được.
