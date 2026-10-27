# -*- coding: utf-8 -*-
"""Ver 5.5 — MODULE SEO POST. Nguồn prompt cho bài viết chủ đề (post), TÁCH
HẲN khỏi prompts_phase2.py (bài mô tả sản phẩm).

VÌ SAO TÁCH FILE, KHÔNG NHÉT THÊM OUTLINE VÀO prompts_phase2:
    prompts_phase2 dựng prompt từ MỘT record sản phẩm — hàm nguoi_dung() nhận
    `row` và đọc row['profile_id'], row['ten_goc'], row['ma_goc']. Toàn bộ
    QUY_TAC_CHUNG ở đó xây trên giả định "chỉ được dùng dữ liệu trong DỮ LIỆU
    SẢN PHẨM". Giả định đó ĐÚNG cho bài sản phẩm và SAI cho bài chủ đề:
    một bài "Máy biến áp khô là gì" không có record nào để bám, áp luật 1 của
    QUY_TAC_CHUNG vào là bài không viết được dòng nào.

    Nên bản post cần MỘT BỘ LUẬT KHÁC, không phải bộ luật cũ nới lỏng. Xem
    QUY_TAC_KHONG_SKU bên dưới: vẫn cấm bịa, nhưng cấm theo cách khác — cấm
    con số cụ thể gán cho sản phẩm cụ thể, không cấm kiến thức ngành phổ thông.

QUAN HỆ VỚI SKU:
    Bài post KHÔNG có FK bắt buộc tới san_pham_phase2 (đó là ràng buộc của
    bảng article_jobs cũ, module này không dùng bảng đó). SKU là NGUỒN SỐ
    TUỲ CHỌN:
        sku='BAT_BUOC' -> không gắn SKU thì không cho sinh
        sku='TUY_CHON' -> có thì dùng, không thì viết chay
        sku='KHONG'    -> không đọc SKU kể cả khi có
    Khi CÓ SKU: bật QUY_TAC_CO_SKU, mọi con số phải truy được về ô Excel.
    Khi KHÔNG: bật QUY_TAC_KHONG_SKU, cấm mọi con số dạng thông số sản phẩm.

FILE NÀY KHÔNG LÀM GÌ NGOÀI DỰNG CHUỖI PROMPT:
    - Không gọi API (ai_wp_adapter lo)
    - Không đọc DB (db_seo_post lo)
    - Không gộp/tính dữ liệu SKU (seo_post_core lo, đưa vào đây dạng dict đã tính sẵn)
    - Không render HTML (seo_post_core lo)
"""
import json
import re
import unicodedata
from chuan_hoa import bo_dau as _bo_dau   # Ver 5.7 — gom 9 bản _bo_dau về 1 nguồn (xem chuan_hoa.py)

# ============================================================ hằng số dùng chung

# Field AI luôn phải trả, mọi content type.
TRUONG_CHUNG = ['meta_title', 'meta_description']

GIOI_HAN_DO_DAI = {
    'meta_title': '55-60 ký tự, PHẢI chứa từ khoá chính',
    'meta_description': '140-160 ký tự, chứa từ khoá chính, có yếu tố mời hành động',
    'intro_html': '3-4 câu (70-110 từ), câu đầu PHẢI chứa từ khoá chính',
    'faq': 'tối đa 4 câu hỏi, mỗi câu hỏi DƯỚI 15 từ, mỗi câu trả lời 40-80 từ',
    '_mac_dinh': '100-180 từ, chia 2-3 đoạn <p> hoặc <ul><li> nếu liệt kê từ 3 ý',
}

# Mức độ phụ thuộc SKU
SKU_BAT_BUOC = 'BAT_BUOC'
SKU_TUY_CHON = 'TUY_CHON'
SKU_KHONG = 'KHONG'

# Chế độ đăng — quyết định endpoint + schema, KHÔNG quyết định nội dung.
# Đặt hằng ở đây để 4 file của module dùng chung 1 chuỗi, không gõ tay lặp lại.
DANG_POST = 'post'
DANG_PRODUCT = 'product'


# ============================================================ luật nền — mọi bài post

QUY_TAC_NEN = """QUY TẮC NỀN — ÁP DỤNG MỌI BÀI, KHÔNG NGOẠI LỆ:
N1. Chỉ trả đúng các field trong "OUTPUT JSON SCHEMA", không thêm field, không thêm chữ nào ngoài JSON.
N2. KHÔNG tự viết Schema.org / JSON-LD. Phần mềm tự dựng.
N3. KHÔNG tự dựng bảng thông số kỹ thuật dạng <table>. Phần mềm tự dựng từ dữ liệu nguồn. Bạn chỉ viết văn.
N4. KHÔNG viết khối CTA, không viết "liên hệ hotline...", không chèn số điện thoại/email/địa chỉ. Phần mềm lắp CTA ở 3 vị trí cố định.
N5. KHÔNG bịa tên khách hàng, tên dự án, số liệu doanh thu, giải thưởng, chứng nhận, năm thành lập của bất kỳ doanh nghiệp nào — kể cả doanh nghiệp chủ website.
N6. KHÔNG viết câu quảng cáo rỗng: "chất lượng hàng đầu", "uy tín số 1", "giá tốt nhất thị trường", "cam kết chính hãng 100%". Người đọc là dân kỹ thuật và thu mua, loại câu này làm giảm độ tin cậy.
N7. Viết tiếng Việt kỹ thuật chuẩn ngành điện. Dùng đúng thuật ngữ (cấp điện áp, dòng định mức, tiết diện, tổ đấu dây...). Không dịch máy, không văn phong dịch.
N8. ĐỊNH DẠNG DỄ ĐỌC: mục nào liệt kê từ 3 ý trở lên thì dùng <ul><li>. In đậm <strong> 1-3 cụm từ khoá/thông số quan trọng mỗi đoạn để người đọc lướt vẫn nắm ý. Không in đậm cả câu.
N9. TỪ KHOÁ CHÍNH phải xuất hiện tự nhiên trong: meta_title, meta_description, câu đầu intro. Các mục còn lại dùng biến thể/đồng nghĩa, KHÔNG nhồi lặp nguyên văn từ khoá — nhồi từ khoá làm bài xấu đi, không tốt lên.
N10. Chỉ dùng thẻ HTML: <p> <ul> <ol> <li> <strong> <em> <h3> <br>. KHÔNG dùng <h1> <h2> (phần mềm tự đặt heading cấp trên), không dùng <table>, <script>, <style>, <div>, <span>, thuộc tính style."""


QUY_TAC_CO_SKU = """QUY TẮC KHI BÀI CÓ GẮN DỮ LIỆU SẢN PHẨM:
S1. Mọi CON SỐ và THÔNG SỐ KỸ THUẬT trong bài phải lấy đúng từ phần "DỮ LIỆU SẢN PHẨM ĐÃ GỘP" bên dưới. Không suy đoán, không quy đổi, không làm tròn, không nội suy giá trị nằm giữa hai mốc có sẵn.
S2. Trường nào nằm trong mục "DỮ LIỆU KHÔNG CÓ" thì TUYỆT ĐỐI không nhắc tới, không đoán giá trị.
S3. Khi dữ liệu cho DẢI giá trị (VD tiết diện từ 1.5 đến 240 mm2), viết đúng dạng dải, KHÔNG liệt kê thành từng mã cụ thể trừ khi dữ liệu liệt kê sẵn.
S4. KHÔNG viết mã hàng nội bộ vào câu văn. Gọi sản phẩm theo tên/quy cách.
S5. Nếu một nhận định kỹ thuật KHÔNG có số liệu chống lưng trong dữ liệu, viết ở mức định tính, không gắn số. Thà không có số còn hơn có số sai."""


QUY_TAC_KHONG_SKU = """QUY TẮC KHI BÀI KHÔNG GẮN DỮ LIỆU SẢN PHẨM:
K1. Được phép dùng KIẾN THỨC NGÀNH PHỔ THÔNG — nguyên lý hoạt động, cấu tạo chung, phân loại, cách thức vận hành. Đây là loại nội dung có trong mọi giáo trình kỹ thuật điện, không phải bịa.
K2. TUYỆT ĐỐI KHÔNG gán con số cụ thể cho sản phẩm cụ thể của bất kỳ hãng nào: không viết "máy biến áp Thibidi 250kVA có tổn hao không tải 480W", không viết giá, không viết mã hàng, không viết kích thước/khối lượng cụ thể. Bài này không có dữ liệu để chống lưng những con số đó.
K3. Được nhắc TÊN tiêu chuẩn (TCVN 8525:2015, IEC 60076, QCVN...) khi đúng ngữ cảnh, nhưng KHÔNG được trích số hiệu điều khoản, KHÔNG được trích giá trị ngưỡng cụ thể ghi trong tiêu chuẩn, KHÔNG khẳng định nội dung chi tiết của tiêu chuẩn.
K4. Công thức kỹ thuật phổ thông (VD S = P/cos-phi, I = S chia cho căn-3 nhân U) được phép viết vì đó là công thức sách giáo khoa. Ví dụ minh hoạ tính toán được phép, nhưng PHẢI ghi rõ là ví dụ minh hoạ.
K5. Khi không chắc chắn về một chi tiết kỹ thuật, viết ở mức khái quát hoặc bỏ hẳn ý đó. KHÔNG viết kiểu "thường vào khoảng X" để lách — đó vẫn là bịa số.
K6. KHÔNG so sánh hơn kém giữa các thương hiệu có thật. Được mô tả đặc điểm chung của từng nhóm sản phẩm, không xếp hạng hãng."""


# Ver 5.5 — luật riêng cho type bao_gia. Tách khỏi QUY_TAC_CO_SKU vì đây là
# xung đột nghiệp vụ THẬT, không phải luật kỹ thuật:
#   Trang muốn ăn từ khoá "bảng giá X" nhưng Lotech KHÔNG công khai giá list
#   (gia_list nằm trong profiles.FIELD_CAM_TUYET_DOI, render_phase2.py:1678
#   ép price_display='Liên hệ'). Đây là quyết định kinh doanh, không phải bug.
# Cách xử lý: bài báo giá bán CẤU TRÚC GIÁ chứ không bán CON SỐ GIÁ —
# yếu tố cấu thành giá, cách đọc một bản báo giá, dải quy cách sẵn có, mốc
# thời gian cập nhật. Đây là nội dung có giá trị thật với người đi hỏi giá,
# và không rò gia_list.
QUY_TAC_BAO_GIA_AN_SO = """QUY TẮC RIÊNG BÀI BÁO GIÁ (chế độ ẨN SỐ — mặc định):
G1. TUYỆT ĐỐI KHÔNG viết bất kỳ con số tiền nào: không giá bán, không giá tham khảo, không khoảng giá, không "chỉ từ ... VND", không phần trăm chiết khấu.
G2. Thay vì con số, viết về CẤU TRÚC GIÁ: những yếu tố làm giá thay đổi (tiết diện, vật liệu ruột, cấp điện áp, số lượng đặt, thời điểm, quy cách đóng gói, điều kiện giao hàng).
G3. Viết phần "cách đọc một bản báo giá" thật sự hữu ích: bản báo giá gồm những mục gì, đã bao gồm VAT chưa, đơn vị tính là mét hay cuộn, thời hạn hiệu lực báo giá, chi phí vận chuyển tính riêng hay gộp.
G4. Nêu rõ giá vật tư điện biến động theo giá đồng/nhôm nguyên liệu, nên báo giá có thời hạn hiệu lực. Đây là sự thật ngành, viết được, nhưng KHÔNG kèm số liệu biến động cụ thể.
G5. KHÔNG hứa hẹn "giá tốt nhất", "rẻ hơn thị trường", "chiết khấu cao"."""

QUY_TAC_BAO_GIA_CONG_KHAI = """QUY TẮC RIÊNG BÀI BÁO GIÁ (chế độ CÔNG KHAI SỐ):
G1. CHỈ được dùng con số tiền xuất hiện trong mục "GIÁ CÔNG KHAI ĐƯỢC PHÉP DÙNG" bên dưới. Không có mục đó = quay về cấm tuyệt đối mọi con số tiền.
G2. Mỗi lần nêu giá PHẢI kèm mốc thời gian cập nhật và ghi rõ là giá tham khảo, chưa gồm VAT/vận chuyển trừ khi dữ liệu ghi khác.
G3. KHÔNG nội suy giá cho quy cách không có trong dữ liệu.
G4. Vẫn phải viết phần yếu tố cấu thành giá và cách đọc báo giá — con số không thay thế được phần này.
G5. KHÔNG hứa hẹn "giá tốt nhất", "rẻ hơn thị trường"."""


# ============================================================ 8 CONTENT TYPE
# Mỗi type khoá cứng: cấu trúc section + schema + mức phụ thuộc SKU.
# 'sections'    : field -> mô tả yêu cầu viết (field dạng chuỗi HTML)
# 'truong_mang' : field -> danh sách key của mỗi phần tử (field dạng mảng object)
# 'tin_hieu_kw' : regex nhận diện type từ từ khoá — rút từ phân tích 8.030 query
#                 GSC thật của 8 site (19/04-18/07/2026), không phải đoán.
# 'uu_tien'     : thứ tự ưu tiên khi 1 từ khoá khớp nhiều type (số nhỏ = ưu tiên cao)

CONTENT_TYPE = {

    'bao_gia': {
        'nhan': 'Báo giá / Bảng giá',
        'muc_tieu': ('Nhóm từ khoá GIÁ-RỘNG: 758 từ khoá, 1.178 clicks, CTR 3,40% toàn hệ. '
                     'Đây là nhóm chuyển đổi mạnh nhất — 11/12 trang top toàn hệ mở đầu bằng '
                     '"Báo giá"/"Bảng giá".'),
        'sku': SKU_BAT_BUOC,
        'goc_nhin': ('Người đi hỏi giá vật tư điện cho công trình — có thể là thu mua, chủ thầu, '
                     'hoặc kỹ sư được giao dự toán. Họ cần biết giá phụ thuộc cái gì và bản báo '
                     'giá sẽ gồm những gì, trước khi gọi điện.'),
        'sections': {
            'intro_html': ('Xác nhận ngay đây là trang báo giá cho nhóm sản phẩm nào, phạm vi quy cách '
                           'nào, cập nhật thời điểm nào. Câu đầu chứa từ khoá chính. KHÔNG vòng vo.'),
            'yeu_to_gia_html': ('Những yếu tố làm giá thay đổi giữa các quy cách trong nhóm này. Bám vào '
                                'đúng các trường có trong dữ liệu đã gộp (tiết diện, vật liệu, cấp điện áp, '
                                'công suất...). Trình bày <ul><li>.'),
            'huong_dan_doc_bang_html': ('Cách đọc bảng quy cách bên dưới: cột nào nghĩa gì, đơn vị tính là gì, '
                                        'quy cách nào dùng cho ứng dụng nào. Giúp người đọc tự khoanh vùng '
                                        'được mã cần hỏi giá.'),
            'luu_y_bao_gia_html': ('Lưu ý thực tế khi lấy báo giá nhóm hàng này: thời hạn hiệu lực, VAT, '
                                   'đơn vị tính, số lượng tối thiểu, thời gian giao hàng, chi phí vận chuyển.'),
        },
        'truong_mang': {},
        'co_faq': True,
        'schema': ['Article', 'FAQPage'],
        'mau_tieu_de': [
            'Báo giá {chu_de} mới nhất {nam}',
            'Bảng giá {chu_de} {nam} — cập nhật {thang}/{nam}',
            'Báo giá {chu_de} — {so_sku} quy cách, giao toàn quốc',
        ],
        'tin_hieu_kw': r'báo giá|bảng giá|\bgiá\b|bao nhiêu tiền|chi phí|giá bao nhiêu',
        'uu_tien': 1,
    },

    'complete_guide': {
        'nhan': 'Complete Guide (X là gì — cấu tạo — nguyên lý)',
        'muc_tieu': ('Nhóm KIẾN THỨC: 213 từ khoá, CTR 3,72% (cao hơn trung bình hệ 2,90%). '
                     'Ăn top phễu, xây E-E-A-T, nuôi internal link cho các trang báo giá.'),
        'sku': SKU_KHONG,
        'goc_nhin': ('Người mới tiếp cận thiết bị này — sinh viên điện, kỹ sư trái ngành, chủ đầu tư '
                     'cần hiểu để ra quyết định. Cần đầy đủ nhưng không hàn lâm.'),
        'sections': {
            'intro_html': ('Trả lời thẳng "X là gì" ngay trong 2 câu đầu, dạng định nghĩa rõ ràng — đây là '
                           'đoạn Google hay lấy làm featured snippet. Câu đầu chứa từ khoá chính.'),
            'dinh_nghia_html': 'Định nghĩa mở rộng: vai trò của thiết bị này trong hệ thống điện, nó đứng ở đâu trong sơ đồ.',
            'cau_tao_html': 'Các bộ phận cấu thành và chức năng từng bộ phận. Trình bày <ul><li>.',
            'nguyen_ly_html': 'Nguyên lý hoạt động, giải thích theo trình tự dễ hiểu. Được dùng công thức phổ thông nếu cần.',
            'phan_loai_html': 'Các cách phân loại thường gặp (theo cấu tạo, theo cấp điện áp, theo ứng dụng...) và đặc điểm mỗi nhóm.',
            'ung_dung_html': 'Ứng dụng thực tế: loại công trình nào, vị trí nào trong lưới điện.',
        },
        'truong_mang': {},
        'co_faq': True,
        'schema': ['Article', 'FAQPage'],
        'mau_tieu_de': [
            '{chu_de} là gì? Cấu tạo, nguyên lý và ứng dụng',
            '{chu_de}: Tổng hợp kiến thức từ A đến Z',
            'Tìm hiểu {chu_de} — cấu tạo, phân loại, cách hoạt động',
        ],
        'tin_hieu_kw': r'là gì|nguyên lý|cấu tạo|khái niệm|tìm hiểu|tổng quan|kiến thức',
        'uu_tien': 3,
    },

    'top_list': {
        'nhan': 'Top List (Top N hãng / loại / model)',
        'muc_tieu': 'Ăn từ khoá dạng "top", "tốt nhất", "hãng nào". Giữ chân lâu, dễ đặt internal link ra các trang báo giá.',
        'sku': SKU_TUY_CHON,
        'goc_nhin': 'Người đang so bó đũa, chưa chốt được mua loại nào/hãng nào. Cần tiêu chí rõ để tự quyết.',
        'sections': {
            'intro_html': 'Nêu bài này xếp theo tiêu chí gì và dành cho ai. Câu đầu chứa từ khoá chính. KHÔNG hứa "tốt nhất".',
            'tieu_chi_html': ('Các tiêu chí dùng để đánh giá nhóm sản phẩm này, giải thích vì sao tiêu chí đó quan '
                              'trọng. Trình bày <ul><li>. Đây là phần tạo khác biệt với bài top list rác của đối thủ.'),
            'ket_luan_html': 'Tóm tắt: trường hợp nào nên chọn nhóm nào. KHÔNG xếp hạng hơn kém tuyệt đối.',
        },
        'truong_mang': {
            'danh_sach': ['ten', 'mo_ta', 'phu_hop_khi', 'can_luu_y'],
        },
        'co_faq': True,
        'schema': ['Article', 'ItemList'],
        'mau_tieu_de': [
            'Top {n} {chu_de} phổ biến nhất hiện nay',
            '{n} loại {chu_de} thường dùng và cách chọn',
            'Các dòng {chu_de} trên thị trường — so sánh và tiêu chí chọn',
        ],
        'tin_hieu_kw': r'\btop\b|tốt nhất|phổ biến|hãng nào|loại nào|nên mua|các loại|danh sách',
        'uu_tien': 2,
    },

    'so_sanh': {
        'nhan': 'So sánh A vs B',
        'muc_tieu': 'Ăn từ khoá "phân biệt", "khác nhau", "A hay B". Ý định gần chuyển đổi, người đọc sắp chốt.',
        'sku': SKU_TUY_CHON,
        'goc_nhin': 'Người đã khoanh vùng còn 2 lựa chọn, cần một bảng đối chiếu thẳng thắn để chốt.',
        'sections': {
            'intro_html': 'Nêu 2 đối tượng đem so và vì sao người ta hay phân vân giữa chúng. Câu đầu chứa từ khoá chính.',
            'tong_quan_a_html': 'Giới thiệu đối tượng A: bản chất, đặc điểm nổi bật.',
            'tong_quan_b_html': 'Giới thiệu đối tượng B: bản chất, đặc điểm nổi bật.',
            'nen_chon_khi_nao_html': ('Kết luận thực dụng: hoàn cảnh nào chọn A, hoàn cảnh nào chọn B. PHẢI có '
                                      'cả hai chiều, không được nghiêng hẳn một bên nếu dữ liệu không cho phép.'),
        },
        'truong_mang': {
            'bang_so_sanh': ['tieu_chi', 'ben_a', 'ben_b'],
        },
        'co_faq': True,
        'schema': ['Article', 'FAQPage'],
        'mau_tieu_de': [
            'So sánh {a} và {b}: nên chọn loại nào?',
            'Phân biệt {a} và {b} — khác nhau ở đâu',
            '{a} hay {b}? Đối chiếu chi tiết theo {n} tiêu chí',
        ],
        'tin_hieu_kw': r'so sánh|phân biệt|khác nhau|khác gì|\bvs\b|hay là|nên chọn.*hay',
        'uu_tien': 2,
    },

    'huong_dan_chon': {
        'nhan': 'Hướng dẫn chọn / công thức tính',
        'muc_tieu': 'Ăn từ khoá "cách chọn", "cách tính", "công thức". Nội dung công cụ, người đọc quay lại nhiều lần.',
        'sku': SKU_KHONG,
        'goc_nhin': 'Kỹ sư hoặc thợ điện đang phải ra quyết định kỹ thuật cụ thể, cần quy trình từng bước.',
        'sections': {
            'intro_html': 'Nêu bài này giúp giải bài toán gì, cần biết trước thông tin gì. Câu đầu chứa từ khoá chính.',
            'cong_thuc_html': ('Công thức tính liên quan (nếu có) — chỉ dùng công thức phổ thông sách giáo khoa. '
                               'Giải thích từng ký hiệu. Nếu đưa ví dụ số, PHẢI ghi rõ "ví dụ minh hoạ".'),
            'loi_thuong_gap_html': 'Các lỗi hay mắc khi chọn/tính sai và hậu quả thực tế. Trình bày <ul><li>.',
        },
        'truong_mang': {
            'buoc': ['tieu_de', 'noi_dung'],
        },
        'co_faq': True,
        'schema': ['HowTo', 'FAQPage'],
        'mau_tieu_de': [
            'Cách chọn {chu_de} đúng chuẩn — hướng dẫn {n} bước',
            'Hướng dẫn tính {chu_de}: công thức và ví dụ',
            'Chọn {chu_de} thế nào cho đúng? {n} bước cần làm',
        ],
        'tin_hieu_kw': r'cách chọn|cách tính|công thức|hướng dẫn|tính toán|chọn.*sao|lựa chọn.*nào',
        'uu_tien': 2,
    },

    'tieu_chuan': {
        'nhan': 'Tiêu chuẩn / quy định',
        'muc_tieu': ('Ít traffic nhưng đối thủ gần như bỏ trống. Ăn trust và tín hiệu E-E-A-T cho toàn domain. '
                     'Rủi ro cao nhất về bịa số — luật K3 khoá chặt.'),
        'sku': SKU_KHONG,
        'goc_nhin': 'Người cần biết quy định nào chi phối thiết bị này và nó ảnh hưởng gì tới việc mua/nghiệm thu.',
        'sections': {
            'intro_html': 'Nêu tiêu chuẩn/quy định nào đang nói tới và nó áp dụng cho đối tượng nào. Câu đầu chứa từ khoá chính.',
            'pham_vi_html': 'Phạm vi điều chỉnh: áp dụng cho loại thiết bị nào, cấp điện áp nào, ai phải tuân thủ.',
            'noi_dung_chinh_html': ('Các nhóm nội dung mà tiêu chuẩn này điều chỉnh, mô tả ở mức KHÁI QUÁT. '
                                    'TUYỆT ĐỐI không trích số hiệu điều khoản hay giá trị ngưỡng cụ thể.'),
            'ap_dung_thuc_te_html': 'Ý nghĩa thực tế khi mua hàng và nghiệm thu: cần yêu cầu nhà cung cấp cung cấp gì, kiểm tra gì.',
        },
        'truong_mang': {},
        'co_faq': True,
        'schema': ['Article', 'FAQPage'],
        'mau_tieu_de': [
            '{chu_de}: phạm vi áp dụng và những điều cần biết',
            'Quy định về {chu_de} — tóm tắt cho người mua hàng',
            '{chu_de} áp dụng thế nào trong thực tế?',
        ],
        'tin_hieu_kw': r'tiêu chuẩn|tcvn|\biec\b|qcvn|quy định|quyết định \d+|nghị định|thông tư|chứng nhận|hợp quy',
        'uu_tien': 1,
    },

    'catalogue': {
        'nhan': 'Catalogue / tài liệu kỹ thuật',
        'muc_tieu': ('Nhóm TÀI LIỆU: 222 từ khoá, CTR 3,89% — CAO NHẤT toàn hệ. Đang gần như bỏ trống. '
                     'Rẻ nhất trong 8 type, làm trước được.'),
        'sku': SKU_TUY_CHON,
        'goc_nhin': 'Kỹ sư đang cần tra thông số để thiết kế/dự toán, muốn tải tài liệu gốc chứ không muốn đọc quảng cáo.',
        'sections': {
            'intro_html': 'Nêu tài liệu này của hãng nào, cho dòng sản phẩm nào, gồm những gì. Câu đầu chứa từ khoá chính.',
            'noi_dung_tai_lieu_html': 'Tài liệu gồm những nhóm thông tin nào, mỗi nhóm dùng để làm gì. Trình bày <ul><li>.',
            'huong_dan_tra_cuu_html': ('Cách tra nhanh: muốn tìm thông số X thì xem mục nào, đối chiếu với điều kiện '
                                       'công trình ra sao. Đây là phần đối thủ không có.'),
        },
        'truong_mang': {},
        'co_faq': True,
        'schema': ['Article', 'FAQPage'],
        'mau_tieu_de': [
            'Catalogue {chu_de} — tải bản PDF mới nhất',
            'Tài liệu kỹ thuật {chu_de}: thông số và cách tra cứu',
            'Bảng tra {chu_de} — hướng dẫn sử dụng catalogue',
        ],
        'tin_hieu_kw': r'catalogue|catalog|\bpdf\b|tài liệu|bảng tra|tra cứu|download|tải về|datasheet',
        'uu_tien': 1,
    },

    'du_an': {
        'nhan': 'Dự án / case study',
        'muc_tieu': 'Gần như không ăn search. Ăn CHUYỂN ĐỔI và E-E-A-T — người đã vào site cần bằng chứng năng lực.',
        'sku': SKU_TUY_CHON,
        'goc_nhin': 'Khách hàng doanh nghiệp đang cân nhắc nhà cung cấp, cần thấy đã làm được việc tương tự.',
        'sections': {
            'intro_html': 'Nêu loại công trình và phạm vi công việc. Câu đầu chứa từ khoá chính.',
            'boi_canh_html': ('Bài toán kỹ thuật đặt ra: yêu cầu về công suất/cấp điện áp/điều kiện lắp đặt. '
                              'CHỈ viết những gì có trong dữ liệu được cấp — KHÔNG bịa tên chủ đầu tư, địa điểm, thời gian.'),
            'giai_phap_html': 'Giải pháp và chủng loại thiết bị sử dụng, lý do chọn cấu hình đó.',
            'ket_qua_html': ('Kết quả bàn giao ở mức định tính. TUYỆT ĐỐI không bịa số liệu tiết kiệm, '
                             'không bịa lời khen của khách hàng.'),
        },
        'truong_mang': {},
        'co_faq': False,
        'schema': ['Article'],
        'mau_tieu_de': [
            'Dự án {chu_de} — giải pháp và thiết bị sử dụng',
            'Thi công {chu_de}: bài toán kỹ thuật và cách xử lý',
            'Cung cấp {chu_de} cho {loai_cong_trinh}',
        ],
        'tin_hieu_kw': r'dự án|thi công|lắp đặt thực tế|case study|công trình',
        'uu_tien': 4,
    },
}


# ============================================================ đoán content type từ từ khoá

def doan_content_type(tu_khoa):
    """Đoán content type phù hợp nhất cho 1 từ khoá.

    Trả (type_id, do_tin_cay, ly_do) với do_tin_cay thuộc {'cao','vua','thap'}.

    Đây là GỢI Ý, không phải quyết định — giao diện luôn cho người sửa lại.
    Ngưỡng tin cậy:
        cao  : khớp tín hiệu của đúng 1 type
        vua  : khớp nhiều type, chọn theo 'uu_tien'
        thap : không khớp gì -> trả complete_guide làm mặc định an toàn
               (viết chay được, không cần SKU, không rủi ro bịa số)
    """
    kw = _bo_dau(tu_khoa)
    khop = []
    for tid, cfg in CONTENT_TYPE.items():
        mau = _bo_dau(cfg['tin_hieu_kw'])
        if re.search(mau, kw):
            khop.append((cfg['uu_tien'], tid))

    if not khop:
        return ('complete_guide', 'thap',
                'Không khớp tín hiệu nào — mặc định Complete Guide (viết được không cần SKU).')
    if len(khop) == 1:
        tid = khop[0][1]
        return (tid, 'cao', f'Khớp tín hiệu riêng của "{CONTENT_TYPE[tid]["nhan"]}".')

    khop.sort()
    tid = khop[0][1]
    ten_khac = ', '.join(CONTENT_TYPE[t]['nhan'] for _, t in khop[1:])
    return (tid, 'vua',
            f'Khớp nhiều type, chọn "{CONTENT_TYPE[tid]["nhan"]}" theo ưu tiên. Cân nhắc thêm: {ten_khac}.')


def can_sku(content_type_id):
    """Trả mức phụ thuộc SKU của 1 type — dùng để giao diện bật/tắt nút gắn SKU."""
    return CONTENT_TYPE[content_type_id]['sku']


def kiem_tra_du_dieu_kien(content_type_id, so_sku_da_gan):
    """Chặn TRƯỚC khi tốn quota AI. Trả (ok: bool, ly_do: str).

    Ver 5.5 — đây chính là món `du_lieu_bat_buoc` mà bản 4.x ghi trong doc
    suốt nhiều đợt nhưng KHÔNG có dòng code nào (grep toàn source = 0 kết
    quả, chỉ có trong NHAT-KY-THAY-DOI.md và archive/KNOWN-ISSUES.md). Ở
    module post nó có thật ngay từ bản đầu.
    """
    if content_type_id not in CONTENT_TYPE:
        return False, f'Content type không hợp lệ: "{content_type_id}". Hợp lệ: {list(CONTENT_TYPE)}'
    muc = CONTENT_TYPE[content_type_id]['sku']
    if muc == SKU_BAT_BUOC and so_sku_da_gan <= 0:
        return False, (f'Type "{CONTENT_TYPE[content_type_id]["nhan"]}" BẮT BUỘC gắn SKU. '
                       f'Đang gắn 0 SKU — bài sẽ không có dữ liệu để dựng bảng quy cách. '
                       f'Gắn SKU rồi sinh lại.')
    return True, 'Đủ điều kiện sinh bài.'


# ============================================================ dựng prompt

def _mo_ta_do_dai(truong):
    return GIOI_HAN_DO_DAI.get(truong, GIOI_HAN_DO_DAI['_mac_dinh'])


def _json_schema_post(content_type_id):
    """Schema đơn giản {field: 'string'} / {field: [{k:'string'}]} —
    ai_wp_adapter._sang_gemini_schema() đã biết chuyển dạng này sang
    responseSchema của Gemini, KHÔNG viết lại hàm chuyển đổi ở đây.
    """
    cfg = CONTENT_TYPE[content_type_id]
    schema = {k: 'string' for k in TRUONG_CHUNG}
    for truong in cfg['sections']:
        schema[truong] = 'string'
    for truong, khoa_con in cfg['truong_mang'].items():
        schema[truong] = [{k: 'string' for k in khoa_con}]
    if cfg['co_faq']:
        schema['faq'] = [{'q': 'string', 'a': 'string'}]
    return schema


def truong_ai_duoc_tra(content_type_id):
    """Danh sách field AI được phép trả — dùng để validate output, chặn
    field lạ trước khi render."""
    return list(_json_schema_post(content_type_id).keys())


def he_thong_post(content_type_id, co_sku, site_cfg=None, che_do_gia='AN'):
    """System instruction cho bài post.

    co_sku      : True nếu bài có gắn ít nhất 1 SKU
    che_do_gia  : 'AN' (mặc định, không nêu số tiền) | 'CONG_KHAI'
                  Chỉ có tác dụng với type bao_gia.
    """
    if content_type_id not in CONTENT_TYPE:
        raise ValueError(f'Content type không hợp lệ: "{content_type_id}"')
    cfg = CONTENT_TYPE[content_type_id]
    ten_site = (site_cfg or {}).get('ten', 'website kỹ thuật điện')

    khoi_luat = [QUY_TAC_NEN, QUY_TAC_CO_SKU if co_sku else QUY_TAC_KHONG_SKU]
    if content_type_id == 'bao_gia':
        khoi_luat.append(QUY_TAC_BAO_GIA_CONG_KHAI if che_do_gia == 'CONG_KHAI'
                         else QUY_TAC_BAO_GIA_AN_SO)

    return (
        f'Bạn là biên tập viên kỹ thuật của {ten_site}, chuyên ngành thiết bị điện '
        f'trung/hạ thế B2B tại Việt Nam.\n'
        f'DẠNG BÀI: {cfg["nhan"]}.\n'
        f'ĐỐI TƯỢNG ĐỌC: {cfg["goc_nhin"]}\n\n'
        + '\n\n'.join(khoi_luat)
    )


def nguoi_dung_post(content_type_id, tu_khoa_chinh, tu_khoa_phu=None,
                    du_lieu_sku=None, truong_thieu=None, gia_cong_khai=None,
                    ghi_chu_bien_tap=''):
    """User prompt cho bài post.

    tu_khoa_chinh    : chuỗi, từ khoá đích của bài
    tu_khoa_phu      : list chuỗi, cụm từ khoá phụ cùng ý định (từ GSC)
    du_lieu_sku      : dict ĐÃ GỘP SẴN do seo_post_core tính, dạng
                       {'Tiết diện': '1.5 - 240 mm2', 'Số quy cách': '212', ...}
                       File này KHÔNG tự tính gộp.
    truong_thieu     : list nhãn trường không có dữ liệu -> đưa vào mục cấm nhắc
    gia_cong_khai    : dict {quy_cach: gia} — CHỈ truyền khi che_do_gia='CONG_KHAI'.
                       Không truyền = AI không thấy con số nào, không có gì để rò.
    ghi_chu_bien_tap : chỉ dẫn thêm người dùng gõ ở giao diện
    """
    cfg = CONTENT_TYPE[content_type_id]
    phan = []

    phan.append(f'TỪ KHOÁ CHÍNH: {tu_khoa_chinh}')
    if tu_khoa_phu:
        phan.append('TỪ KHOÁ PHỤ (dùng tự nhiên trong bài, không nhồi):\n'
                    + '\n'.join(f'- {t}' for t in tu_khoa_phu))

    if du_lieu_sku:
        dong = '\n'.join(f'- {nhan}: {gt}' for nhan, gt in du_lieu_sku.items() if gt not in (None, ''))
        phan.append('DỮ LIỆU SẢN PHẨM ĐÃ GỘP (chỉ được dùng đúng những gì ở đây):\n' + dong)
    else:
        phan.append('DỮ LIỆU SẢN PHẨM: KHÔNG CÓ. Bài này viết bằng kiến thức ngành phổ thông '
                    'theo quy tắc K1-K6. Không được gán con số cụ thể cho sản phẩm cụ thể.')

    if gia_cong_khai:
        dong_gia = '\n'.join(f'- {qc}: {g}' for qc, g in gia_cong_khai.items())
        phan.append('GIÁ CÔNG KHAI ĐƯỢC PHÉP DÙNG (chỉ đúng những dòng này, không nội suy):\n' + dong_gia)

    if truong_thieu:
        phan.append('DỮ LIỆU KHÔNG CÓ, TUYỆT ĐỐI KHÔNG NHẮC TỚI:\n' + ', '.join(truong_thieu))

    # cấu trúc cần viết
    dong_ct = []
    for truong, mo_ta in cfg['sections'].items():
        dong_ct.append(f'- {truong} ({_mo_ta_do_dai(truong)}): {mo_ta}')
    for truong, khoa_con in cfg['truong_mang'].items():
        dong_ct.append(f'- {truong} (mảng, 3-7 phần tử; mỗi phần tử gồm: {", ".join(khoa_con)}): '
                       f'mỗi trường con 1-3 câu, KHÔNG chứa thẻ HTML.')
    if cfg['co_faq']:
        dong_ct.append(f'- faq ({GIOI_HAN_DO_DAI["faq"]}): câu hỏi người mua thật sự hay hỏi về chủ đề này, '
                       f'không phải câu hỏi tự đặt cho có. Mảng rỗng được nếu không có gì đáng hỏi.')
    phan.append('CẤU TRÚC NỘI DUNG CẦN VIẾT (mỗi mục là 1 field trong JSON trả về):\n' + '\n'.join(dong_ct))

    if ghi_chu_bien_tap:
        phan.append('CHỈ DẪN THÊM TỪ BIÊN TẬP VIÊN:\n' + ghi_chu_bien_tap)

    phan.append('OUTPUT JSON SCHEMA BẮT BUỘC (chỉ trả đúng JSON, không thêm chữ nào khác):\n'
                + json.dumps(_json_schema_post(content_type_id), ensure_ascii=False, indent=2))

    return '\n\n'.join(phan)


def xay_prompt_post(content_type_id, tu_khoa_chinh, tu_khoa_phu=None,
                    du_lieu_sku=None, truong_thieu=None, site_cfg=None,
                    che_do_gia='AN', gia_cong_khai=None, ghi_chu_bien_tap=''):
    """Hàm tổng — trả (system_text, user_text, json_schema).

    Đây là hàm DUY NHẤT seo_post_core / ai_wp_adapter gọi để lấy prompt bài
    post. Không ghép chuỗi prompt ở nơi khác (cùng tinh thần prompts_phase2).

    Raise ValueError sớm nếu type sai hoặc thiếu SKU bắt buộc — chặn trước
    khi tốn 1 request Gemini (free tier chỉ 20 request/ngày/project).
    """
    so_sku = len(du_lieu_sku) if du_lieu_sku else 0
    ok, ly_do = kiem_tra_du_dieu_kien(content_type_id, so_sku)
    if not ok:
        raise ValueError(ly_do)

    co_sku = bool(du_lieu_sku)
    if che_do_gia != 'CONG_KHAI':
        gia_cong_khai = None   # chốt chặn: chế độ ẨN thì AI không bao giờ thấy số tiền

    return (
        he_thong_post(content_type_id, co_sku, site_cfg, che_do_gia),
        nguoi_dung_post(content_type_id, tu_khoa_chinh, tu_khoa_phu,
                        du_lieu_sku, truong_thieu, gia_cong_khai, ghi_chu_bien_tap),
        _json_schema_post(content_type_id),
    )


# ============================================================ tiện ích cho giao diện

def danh_sach_type():
    """Trả list (type_id, nhãn, mức SKU) để đổ vào combobox Tab 8."""
    return [(tid, cfg['nhan'], cfg['sku']) for tid, cfg in CONTENT_TYPE.items()]


def mau_tieu_de(content_type_id):
    return list(CONTENT_TYPE[content_type_id]['mau_tieu_de'])


def schema_cua_type(content_type_id):
    """Loại JSON-LD phần mềm sẽ dựng cho type này. Trả list.

    Ver 5.5 — LƯU Ý khi đăng dạng `product`: Rank Math tự sinh schema Product
    cho mọi WooCommerce product và schema đó cần `offers`. Bài post gộp nhiều
    SKU không có `offers` -> Rank Math đẻ lỗi schema. Đăng dạng `post` không
    dính. seo_post_core phải cảnh báo khi người dùng chọn `product` cho type
    có nhiều SKU.
    """
    return list(CONTENT_TYPE[content_type_id]['schema'])


def canh_bao_che_do_dang(content_type_id, che_do_dang, so_sku):
    """Trả chuỗi cảnh báo (rỗng nếu không có vấn đề gì).

    KHÔNG CHẶN — Thịnh chốt đăng product để làm dày nội lực site, đó là quyết
    định nghiệp vụ. Chỉ nói cho biết cái giá phải trả.
    """
    if che_do_dang != DANG_PRODUCT:
        return ''
    if so_sku > 1:
        return (f'Đăng dạng product với {so_sku} SKU gộp: Rank Math sẽ tự sinh schema Product '
                f'thiếu `offers` -> Search Console báo lỗi. Cân nhắc tắt schema Product của '
                f'Rank Math cho bài này, hoặc đăng dạng post.')
    if content_type_id in ('complete_guide', 'huong_dan_chon', 'tieu_chuan'):
        return (f'Type "{CONTENT_TYPE[content_type_id]["nhan"]}" là bài kiến thức, đăng dạng product '
                f'sẽ hiện nút "Thêm vào giỏ" trên trang không bán gì. Cân nhắc đăng dạng post.')
    return ''
