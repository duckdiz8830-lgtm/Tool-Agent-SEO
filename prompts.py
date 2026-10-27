# -*- coding: utf-8 -*-
"""
Khung viết bài. KHÔNG chứa danh tính site nữa, danh tính nằm ở cauhinh.py.

NGUYÊN TẮC BẤT DI BẤT DỊCH:
    AI chỉ viết VĂN XUÔI. Mọi con số (kVA, kV, A, mm, giá) do engine ghép thẳng
    từ dữ liệu. autopost.py có bộ chặn AI bịa số. Cột nào trống thì khối đó
    không hiện ra, KHÔNG bịa vào.
"""

# ---------------------------------------------------------------- system prompt
# {ten}, {hang_liet_ke} do engine điền theo site đang chạy.
SYSTEM = """Bạn là kỹ sư điện kiêm người viết nội dung cho một nhà phân phối thiết bị
điện trung thế tại Việt Nam. Website tên là {ten}.

QUY TẮC BẮT BUỘC, VI PHẠM LÀ BÀI BỊ CHẶN KHÔNG ĐĂNG:
1. TUYỆT ĐỐI KHÔNG tự nghĩ ra con số nào. Chỉ được nhắc lại con số đã có trong phần
   DỮ LIỆU SẢN PHẨM. Không có tổn hao thì không viết tổn hao. Không có kích thước thì
   không viết kích thước. Không có giá thì không viết giá.
2. Không bịa tiêu chuẩn, chứng chỉ, giấy uỷ quyền, tên dự án, tên khách hàng.
3. Không bịa thời gian giao hàng cụ thể.
4. KHÔNG nhắc tên bất kỳ công ty nào khác ngoài {ten} và các hãng: {hang_liet_ke}.
   Không nhắc mã số thuế, địa chỉ văn phòng, tên người, tên website khác.
5. Thiếu dữ liệu cho mục nào thì trả chuỗi rỗng cho mục đó, không lấp bằng câu chữ chung chung.
6. Được dùng KIẾN THỨC CHUNG VỀ DÒNG SẢN PHẨM để giải thích ký hiệu cấu hình và nói về
   ứng dụng. Nhưng KHÔNG được biến thông số chung của dòng thành thông số riêng của model.
7. Viết tiếng Việt kỹ thuật đúng cách gọi của thợ điện Việt Nam: "máy biến áp", "tủ RMU",
   "ngăn cầu dao phụ tải", "ngăn máy cắt", "cáp đến", "cáp đi", "trạm biến áp",
   "đầu cáp elbow", "rơ le bảo vệ".
8. Không dùng dấu gạch ngang dài. Không mở bài kiểu "Trong thời đại ngày nay" hay
   "Ngày nay, cùng với sự phát triển".
9. Không quảng cáo rỗng: "chất lượng hàng đầu", "uy tín số 1", "giá rẻ nhất thị trường".
   Viết như một người bán hàng kỹ thuật thật đang tư vấn.

ĐẦU RA: chỉ trả JSON hợp lệ. Không giải thích. Không dấu ```."""

# ---------------------------------------------------------------- yêu cầu JSON
JSON_SPEC = """Trả về JSON đúng cấu trúc sau:
{{
  "meta_title": "toi da 60 ky tu, co thong so chinh va ten hang",
  "meta_description": "toi da 155 ky tu, ket bang loi keu goi goi hotline",
  "h1": "tieu de trang",
  "ten_goi_khac_html": "1 doan <p> 30 den 50 tu, liet ke cac cach goi khac cua san pham ma khach hay go khi tim kiem. Chi dung cach goi co trong du lieu hoac bien the hien nhien cua ten san pham.",
  "intro_html": "1 doan <p> mo bai 70 den 100 tu. Noi ngay san pham la gi, dung o dau, ai mua. Khong vong vo.",
  "cau_tao_html": "{cau_tao}",
  "ung_dung_html": "{ung_dung}",
  "chon_mua_html": "{chon_mua}",
  "faq": [
    {{"q": "cau hoi khach that su hay hoi khi mua", "a": "tra loi 50 den 90 tu, thang vao viec"}}
  ],
  "ket_luan_html": "1 doan <p> 40 den 60 tu chot lai va dan toi goi hotline"
}}
Số câu FAQ: {so_faq}. Mỗi mục thân bài dùng thẻ <h3> cho tiêu đề con, <p> hoặc <ul> cho nội dung.
Tổng toàn bài khoảng {tong_tu} từ."""

# ---------------------------------------------------------------- mẫu bài
MAU = {
    'bao_gia': {
        'ten': 'Báo giá',
        'tieu_de': 'Báo giá {ten_san_pham}',
        'so_faq': 6,
        'tong_tu': '900 đến 1100',
        'cau_tao': ('2 den 3 the <h3> kem <p>: san pham nay gom nhung bo phan chinh nao va '
                    'moi bo phan lam gi, vi sao cau tao do quan trong khi chon mua, nhung gi '
                    'di kem khi nhan hang. 250 den 320 tu.'),
        'ung_dung': ('2 the <h3> kem <p> hoac <ul>: loai cong trinh nao dung dung cau hinh '
                     'nay, no nam o dau trong mot tram bien ap hoan chinh. 220 den 300 tu.'),
        'chon_mua': ('3 the <h3> kem <p>: cach chon dung cau hinh, nhung loi hay gap khi dat '
                     'hang, can chuan bi gi truoc khi nhan va lap dat. 250 den 330 tu.'),
        'goc_nhin': ('Khách đang so giá và chuẩn bị đặt hàng: chủ đầu tư, nhà thầu điện, '
                     'ban quản lý dự án. Viết để họ yên tâm bấm gọi.'),
    },
    'thong_so': {
        'ten': 'Thông số kỹ thuật',
        'tieu_de': 'Thông số kỹ thuật {ten_san_pham}',
        'so_faq': 5,
        'tong_tu': '800 đến 1000',
        'cau_tao': ('3 the <h3> kem <p>: giai thich y nghia tung thong so co trong bang va anh '
                    'huong toi van hanh, cau tao ben trong, vat lieu va kieu lam mat. '
                    '300 den 380 tu.'),
        'ung_dung': ('2 the <h3> kem <p>: dieu kien lap dat va moi truong van hanh, cach doc '
                     'nhan may va kiem tra khi nghiem thu. 200 den 280 tu.'),
        'chon_mua': ('2 the <h3> kem <p>: so sanh cau hinh nay voi cau hinh lien ke de chon cho '
                     'dung, cac hang muc can thi nghiem truoc khi dong dien. 200 den 280 tu.'),
        'goc_nhin': 'Kỹ sư thiết kế hoặc kỹ thuật viên đang tra cứu trước khi hỏi giá.',
    },
}

# ---------------------------------------------------------------- khung HTML
HTML = """{ten_goi_khac}

{intro}

{anh_chinh}

{khoi_cta_1}

<h2>Bảng giá {ten_san_pham}</h2>
{bang_gia}

<h2>Thông số kỹ thuật {ten_san_pham}</h2>
{bang_thong_so}

<h2>Cấu tạo và phụ kiện đi kèm</h2>
{cau_tao}
{khoi_phu_kien}

<h2>Ứng dụng thực tế</h2>
{ung_dung}

{anh_phu}

{khoi_cta_2}

<h2>Hướng dẫn chọn mua</h2>
{chon_mua}

<h2>Câu hỏi thường gặp</h2>
{faq}

{ket_luan}

{khoi_lien_quan}

{khoi_cta_3}"""

CTA = """<div class="bg-cta">
  <p><strong>{tieu_de_cta}</strong></p>
  <p>{cam_ket}</p>
  <p><a href="tel:{hotline}">Gọi ngay {hotline}</a>
     &nbsp;|&nbsp; <a href="https://zalo.me/{zalo}">Chat Zalo {zalo}</a></p>
</div>"""

CTA_TIEU_DE = [
    'Nhận báo giá {ten_san_pham} kèm chiết khấu công trình',
    'Cần tư vấn chọn đúng cấu hình? Gọi kỹ thuật',
    'Báo giá chính thức và tình trạng kho hôm nay',
]

LUU_Y_GIA = ('<p><em>Lưu ý: bảng giá trên chỉ mang tính tham khảo. Giá bán thay đổi theo biến '
             'động nguyên vật liệu và tuỳ chọn cấu hình. Để có báo giá chính thức kèm chiết '
             'khấu cho công trình, quý khách vui lòng gọi '
             '<a href="tel:{hotline}">{hotline}</a>.</em></p>')
