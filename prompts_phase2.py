# -*- coding: utf-8 -*-
"""
Round 2 — R2-05: Prompt Phase 2 THẬT, KHÔNG dùng prompts.py/MAU của nhánh
RMU cũ. Mỗi outline có cấu trúc nội dung riêng (OUTLINE_NOI_DUNG), nhưng
dùng CHUNG 1 hàm lắp ráp (xay_prompt) — tránh lặp 7 lần cùng 1 khối luật
"không bịa số"/"giữ nguyên đơn vị"/"JSON schema" (đó là luật CHUNG cho mọi
outline, không phải điểm khác biệt giữa các outline).

AI CHỈ được trả các field biên tập liệt kê ở TRUONG_AI_DUOC_TRA — không bao
giờ được tự dựng bảng thông số hay Product Schema (2 việc đó code tự làm ở
render_phase2.py).
"""
import json

import profiles as P

TRUONG_AI_DUOC_TRA_CHUAN = [
    'meta_title', 'meta_description', 'intro_html', 'dac_diem_html',
    'ung_dung_html', 'huong_dan_chon_html',
]
TRUONG_FAQ = 'faq'

GIOI_HAN_DO_DAI = {
    'meta_title': '55-60 ký tự',
    'meta_description': '140-160 ký tự',
    'intro_html': '2-3 câu (khoảng 40-70 từ)',
    'dac_diem_html': '80-150 từ, chia thành 2-3 đoạn <p> ngắn cho dễ đọc (hoặc <ul><li> nếu hợp lý hơn) — KHÔNG viết dồn thành 1 khối chữ dài liền mạch',
    'ung_dung_html': '60-120 từ',
    'huong_dan_chon_html': '60-120 từ',
    'faq': 'tối đa 3 câu hỏi, mỗi câu hỏi DƯỚI 15 từ (ngắn gọn, đúng trọng tâm), mỗi câu trả lời 30-60 từ',
}

# Gate 2 Task 3 — 2 mẫu bài THẬT SỰ khác nhau, không phải khác tên suông:
#   chuan    : đầy đủ mọi section outline cho phép, có FAQ nếu outline bật.
#   ngan_gon : bỏ hẳn mục "hướng dẫn lựa chọn" và FAQ (súc tích, chỉ còn
#              giới thiệu + đặc điểm + ứng dụng), độ dài mỗi mục rút còn ~
#              một nửa. Khác biệt này ở TẦNG PROMPT (không phải hy vọng AI
#              tự viết ngắn) — cả AI thật lẫn AI mock đều nhận đúng cấu trúc
#              đã rút gọn, nên HTML ra khác nhau có chủ đích, không phải
#              tình cờ do AI "cảm thấy" viết ngắn hơn.
MAU_BIEN_THE = {
    'chuan': {
        'nhan': 'Chuẩn — đầy đủ',
        'huong_dan_do_dai': 'Viết đầy đủ, chi tiết, đúng độ dài đã ghi ở mỗi mục.',
        'bo_qua_section': [],
        'bo_qua_faq': False,
        'he_so_do_dai': 1.0,
    },
    'ngan_gon': {
        'nhan': 'Ngắn gọn',
        'huong_dan_do_dai': ('Viết SÚC TÍCH, ngắn khoảng MỘT NỬA độ dài đã ghi ở mỗi mục. '
                             'Bỏ chi tiết phụ, giữ đúng ý chính.'),
        'bo_qua_section': ['huong_dan_chon_html'],
        'bo_qua_faq': True,
        'he_so_do_dai': 0.5,
    },
}


def _mau(mau):
    if mau not in MAU_BIEN_THE:
        raise ValueError(f'Mẫu không hợp lệ: "{mau}". Chỉ hỗ trợ: {list(MAU_BIEN_THE)}')
    return MAU_BIEN_THE[mau]

# ============================================================ cấu trúc nội dung riêng từng outline
# nhan_section: tên section hiển thị (để AI hiểu ngữ cảnh viết, không phải
# heading cứng — code renderer tự thêm <h2>/<h3> ở render_phase2.py).
# co_faq: outline có bật khối FAQ hay không.
# goc_nhin: câu định hướng giọng văn/đối tượng đọc, khác nhau theo outline.
OUTLINE_NOI_DUNG = {
    'outline_cap_dien': {
        'nhan_outline': 'Cáp điện',
        'goc_nhin': 'Kỹ sư điện hoặc người mua vật tư cần chọn đúng loại cáp theo thông số kỹ thuật.',
        'sections': {
            'intro_html': 'Giới thiệu ngắn sản phẩm là loại cáp gì, dùng cho mục đích chung nào.',
            'dac_diem_html': 'Cấu tạo và đặc điểm CHỈ dựa trên dữ liệu có thật (tiết diện, cấp điện áp, vật liệu ruột nếu có). KHÔNG mô tả ruột đồng/nhôm, lớp cách điện XLPE/PVC, khả năng chịu nhiệt nếu dữ liệu không có field đó.',
            'ung_dung_html': 'Phạm vi ứng dụng thường gặp của loại cáp này (dân dụng/công nghiệp/hạ thế/trung thế theo cấp điện áp nếu có).',
            'huong_dan_chon_html': 'Hướng dẫn lựa chọn: những yếu tố cần xem khi chọn cáp (tiết diện phù hợp tải, môi trường lắp đặt).',
        },
        'co_faq': True,
    },
    'outline_tu_dong_cat': {
        'nhan_outline': 'Tủ và thiết bị đóng cắt',
        'goc_nhin': 'Kỹ sư vận hành trạm điện cần hiểu chức năng thiết bị trong hệ thống.',
        'sections': {
            'intro_html': 'Tổng quan thiết bị: đây là loại thiết bị đóng cắt/tủ điện gì.',
            'dac_diem_html': 'Chức năng trong hệ thống điện — CHỈ nhắc điện áp, dòng định mức, dòng cắt, số cực, số ngăn hoặc loại thiết bị KHI record có dữ liệu tương ứng trong phần "DỮ LIỆU SẢN PHẨM".',
            'ung_dung_html': 'Phạm vi ứng dụng: trạm biến áp, tủ phân phối, lưới trung/hạ thế.',
            'huong_dan_chon_html': 'Lưu ý khi lựa chọn thiết bị đóng cắt phù hợp hệ thống.',
        },
        'co_faq': False,
    },
    'outline_vo_tu': {
        'nhan_outline': 'Vỏ tủ / tủ đo đếm',
        'goc_nhin': 'Người mua vật tư cần vỏ tủ/hộp kỹ thuật lắp đặt thiết bị đo đếm.',
        'sections': {
            'intro_html': 'Giới thiệu ngắn đây là loại vỏ tủ/hộp gì, dùng để chứa gì.',
            'dac_diem_html': 'Đặc điểm vật lý CHỈ dựa trên dữ liệu có (kích thước, chất liệu nếu có trong tên/quy cách). Đây là sản phẩm cơ khí, KHÔNG có thông số điện (dòng cắt, dòng định mức) — KHÔNG bịa các thông số đó.',
            'ung_dung_html': 'Phạm vi sử dụng: lắp đặt ngoài trời/trong nhà, vị trí lắp đặt điển hình.',
            'huong_dan_chon_html': '',  # bỏ qua nếu không đủ dữ liệu — xem ghi_chu_bo_qua
        },
        'co_faq': False,
        'ghi_chu_bo_qua': 'huong_dan_chon_html có thể để rỗng nếu dữ liệu chỉ có kích thước, không đủ để viết hướng dẫn chọn có ý nghĩa — KHÔNG viết chung chung để lấp chỗ trống.',
    },
    'outline_may_bien_ap': {
        'nhan_outline': 'Máy biến áp',
        'goc_nhin': 'Kỹ sư điện cần chọn máy biến áp đúng công suất và cấp điện áp.',
        'sections': {
            'intro_html': 'Giới thiệu đây là máy biến áp loại gì (dựa Tên hàng, không suy đoán thêm).',
            'dac_diem_html': 'Đặc điểm CHỈ dựa trên công suất, cấp điện áp có trong dữ liệu. KHÔNG bịa thêm loại máy (dầu/khô/silic...) nếu field đó không có trong dữ liệu được cấp — chỉ được lấy nếu đã nằm sẵn trong Tên hàng ở phần dữ liệu. '
                            'VIẾT THÀNH 2-3 ĐOẠN <p> NGẮN (Ver 5.0 — KHÔNG dồn thành 1 khối chữ liền mạch, khó đọc trên màn hình), mỗi đoạn 1 ý riêng — VD đoạn 1: khía cạnh kỹ thuật (điểm đáng chú ý khi thiết kế/thi công); đoạn 2: khía cạnh vận hành lâu dài (chi phí, độ bền, tổn hao...) nếu dữ liệu cho phép nói tới. Không bắt buộc đúng 2 khía cạnh này nếu dữ liệu không đủ — miễn là chia đoạn tự nhiên, không viết 1 câu dài dằng dặc. '
                            'QUAN TRỌNG — CHỐNG TRÙNG LẶP GIỮA CÁC SKU (Ver 4.9.9): nếu dữ liệu có "Mã liền kề nhỏ hơn"/"Mã liền kề lớn hơn"/"Chênh lệch...", PHẢI dùng thông tin này để giải thích VÌ SAO chọn đúng mức công suất này thay vì mã liền kề — đây là điểm khác biệt hoá chính giữa các bài cùng dòng sản phẩm, không phải chi tiết phụ. Nếu KHÔNG có dữ liệu này (record không có SKU anh em), bỏ qua, không tự bịa. '
                            'QUY TẮC CHỐNG LẶP Ý (Ver 2.7 — lỗi thật trên bài đã đăng): phần Đặc điểm và phần Chọn công suất phù hợp KHÔNG được nói cùng một ý. Đặc điểm nói về CẤU TẠO và TÍNH CHẤT của chính sản phẩm này (vật liệu, kiểu chế tạo, tiêu chuẩn áp dụng). Chọn công suất phù hợp nói về CÁCH RA QUYẾT ĐỊNH (đối chiếu phụ tải thực tế, khi nào nên lên bản lớn hơn, khi nào đủ dùng). Nếu đã nêu con số so sánh với phiên bản khác ở mục Đặc điểm thì mục Chọn công suất KHÔNG được nhắc lại con số đó, và ngược lại. Gọi các bản khác bằng "phiên bản X kVA", TUYỆT ĐỐI không viết mã hàng vào câu văn.',
            'ung_dung_html': 'Ứng dụng: trạm biến áp phân phối, cấp điện cho khu vực/phụ tải. '
                             'Nếu dữ liệu có "Phân khúc công suất" và/hoặc "Tải ước tính", dùng để mô tả CỤ THỂ loại công trình/quy mô phù hợp (VD phân khúc nhỏ → tòa nhà vài tầng, xưởng nhỏ; phân khúc lớn → nhà máy, khu công nghiệp) — nếu có "Tải ước tính", PHẢI giữ nguyên cụm "(ước tính, giả định cosφ=...)" đi kèm, KHÔNG được bỏ qua phần chú thích này hay viết như số đo thật của máy.',
            'huong_dan_chon_html': 'Lưu ý chọn máy biến áp theo đúng công suất và cấp điện áp hệ thống. '
                                   'Nếu có dữ liệu chênh lệch với mã liền kề, dùng để tư vấn bài toán chọn mức công suất — không mua dư thừa mã lớn hơn khi mã hiện tại đã đủ dùng, hoặc ngược lại. KHÔNG tự đưa ra con số tiết kiệm chi phí (%, VNĐ) — Lotech không công khai giá, mọi câu hỏi về giá dẫn về CTA liên hệ.',
        },
        'co_faq': True,
    },
    'outline_vo_may_bien_ap': {
        # Ver 5.2 — outline riêng cho "Vỏ mạ kẽm nhúng nóng MBA..." — VỎ
        # THÉP bảo vệ, KHÔNG PHẢI máy biến áp. Rule quan trọng nhất: cấm
        # tuyệt đối gọi sản phẩm là "máy biến áp" — đây là phụ kiện lắp
        # ngoài, dữ liệu công suất chỉ để biết vỏ này khớp cỡ máy nào.
        'nhan_outline': 'Vỏ bảo vệ máy biến áp',
        'goc_nhin': 'Người mua cần vỏ bảo vệ đúng cỡ, đúng vật liệu chống ăn mòn cho máy biến áp treo trụ/ngoài trời.',
        'sections': {
            'intro_html': 'Giới thiệu đây LÀ VỎ BẢO VỆ (không phải máy biến áp) — dùng đúng từ "vỏ"/"vỏ bảo vệ"/"vỏ mạ kẽm" xuyên suốt, KHÔNG được viết như thể sản phẩm là máy biến áp hoàn chỉnh. Nếu có trường "Máy biến áp tương thích", được phép dùng NGUYÊN thông tin pha + kVA + cấp điện áp trong trường đó; đây là thông số của MÁY phù hợp với vỏ, không phải thông số điện của cái vỏ.',
            'dac_diem_html': 'Đặc điểm CHỈ dựa trên: vật liệu mạ kẽm nhúng nóng (đặc tính chống ăn mòn/oxy hoá đây là kiến thức phổ thông về mạ kẽm, được phép nói chung — KHÔNG bịa thêm độ dày lớp mạ hay số liệu kỹ thuật cụ thể nào không có trong dữ liệu), cỡ máy biến áp tương thích (theo Công suất). '
                            'Nếu dữ liệu có "Mã liền kề nhỏ hơn"/"lớn hơn", dùng để nói về việc chọn đúng cỡ vỏ khớp đúng cỡ máy — KHÔNG dùng ngôn ngữ như đang so sánh CÔNG SUẤT VẬN HÀNH của máy biến áp (vỏ không vận hành, chỉ bảo vệ).',
            'ung_dung_html': 'Ứng dụng: bảo vệ máy biến áp lắp đặt ngoài trời (treo trụ, trạm biến áp lộ thiên) khỏi mưa nắng/ăn mòn. KHÔNG viết về "cấp điện", "tải tiêu thụ" — đó là chức năng của máy biến áp, không phải của vỏ.',
            'huong_dan_chon_html': 'Lưu ý chọn ĐÚNG CỠ vỏ khớp với công suất máy biến áp đã có/dự kiến lắp. Không tự đưa số tiết kiệm chi phí.',
        },
        'co_faq': False,
    },
    'outline_do_luong': {
        'nhan_outline': 'Thiết bị đo lường',
        'goc_nhin': 'Kỹ sư đo lường/bảo vệ rơ le cần thiết bị TI/TU/MOF đúng thông số.',
        'sections': {
            'intro_html': 'Giới thiệu đây là thiết bị đo lường loại gì (TI/TU/MOF theo Tên hàng).',
            'dac_diem_html': 'Đặc điểm CHỈ dựa trên cấp điện áp và dữ liệu thực tế có trong record — KHÔNG bịa tỷ số biến, dung lượng VA, cấp chính xác nếu không nằm trong dữ liệu được cấp.',
            'ung_dung_html': 'Ứng dụng trong hệ thống đo đếm/bảo vệ.',
            'huong_dan_chon_html': 'Lưu ý chọn thiết bị đo lường phù hợp hệ thống.',
        },
        'co_faq': False,
    },
    'outline_phu_kien': {
        'nhan_outline': 'Phụ kiện và khác',
        'goc_nhin': 'Người mua vật tư cần phụ kiện đi kèm hệ thống điện.',
        'sections': {
            'intro_html': 'Sản phẩm này là gì, dùng để làm gì — mô tả chung, KHÔNG cố bóc thông số kỹ thuật kiểu cáp hay máy biến áp.',
            'dac_diem_html': 'Thông tin nhận diện và quy cách CHỈ dựa trên dữ liệu có (thương hiệu, quy cách nếu có).',
            'ung_dung_html': 'Công dụng và phạm vi sử dụng.',
            'huong_dan_chon_html': 'Lưu ý khi đặt hàng (số lượng, đơn vị tính).',
        },
        'co_faq': False,
    },
    'outline_dau_cap_ky_thuat': {
        # Ver 4.9.5 — riêng cho đầu cáp/hộp nối co nguội/co nhiệt ĐÃ enrich
        # từ catalogue thật (ABB/3M, 90 SKU đợt đầu). Khác outline_phu_kien
        # ở chỗ CÓ dữ liệu kỹ thuật thật để viết đặc điểm/hướng dẫn lắp đặt
        # cụ thể, không chỉ mô tả chung chung.
        'nhan_outline': 'Đầu cáp / hộp nối trung thế (có dữ liệu catalogue)',
        'goc_nhin': 'Kỹ sư điện hoặc thợ lắp đặt cần chọn đúng bộ đầu cáp/hộp nối theo tiết diện và điều kiện lắp đặt (trong nhà/ngoài trời).',
        'sections': {
            'intro_html': 'Giới thiệu ngắn đây là loại đầu cáp/hộp nối gì (co nguội/co nhiệt, trong nhà/ngoài trời theo Tên hàng), dùng để làm gì.',
            'dac_diem_html': 'Đặc điểm kỹ thuật CHỈ dựa trên dữ liệu có thật (đường kính cách điện áp dụng, kích thước lắp đặt, chiều dài đường rò nếu là loại ngoài trời, tiêu chuẩn áp dụng). KHÔNG suy đoán thêm vật liệu/cấu tạo ngoài dữ liệu được cấp.',
            'ung_dung_html': 'Phạm vi ứng dụng: loại cáp trung thế nào phù hợp (dựa tiết diện/điện áp trong Quy cách nếu có), lắp trong nhà hay ngoài trời.',
            'huong_dan_chon_html': 'Hướng dẫn chọn: đối chiếu tiết diện cáp thực tế công trình với đường kính cách điện áp dụng ghi trong dữ liệu để chọn đúng bộ kit, lưu ý khác biệt trong nhà/ngoài trời nếu có đường rò.',
        },
        'co_faq': True,
    },
    'outline_service': {
        'nhan_outline': 'Dịch vụ thí nghiệm / kiểm định',
        'goc_nhin': 'Khách hàng cần đặt dịch vụ thí nghiệm/kiểm định thiết bị điện.',
        'sections': {
            'intro_html': 'Dịch vụ này là gì — mô tả chung dựa trên Tên hàng.',
            'dac_diem_html': 'Nội dung/phạm vi công việc thực hiện, CHỈ dựa trên dữ liệu có trong record — KHÔNG bịa quy trình kỹ thuật, tiêu chuẩn áp dụng, hay kết quả thí nghiệm cụ thể nếu không có trong dữ liệu.',
            'ung_dung_html': 'Phạm vi áp dụng: loại thiết bị/công trình cần dịch vụ này.',
            'huong_dan_chon_html': 'Lưu ý khi đặt dịch vụ (liên hệ trước để xác nhận phạm vi công việc).',
        },
        'co_faq': False,
    },
}

QUY_TAC_CHUNG = """QUY TẮC BẮT BUỘC — KHÔNG NGOẠI LỆ:
1. CHỈ được dùng dữ liệu xuất hiện trong phần "DỮ LIỆU SẢN PHẨM" bên dưới. Không suy đoán, không bổ sung tiêu chuẩn IEC/TCVN/IP/CO/CQ/bảo hành/dòng tải/thông số kỹ thuật từ kiến thức bên ngoài.
2. Trường được liệt kê trong mục "DỮ LIỆU KHÔNG CÓ" — TUYỆT ĐỐI KHÔNG được nhắc tới, không suy đoán giá trị.
3. GIỮ NGUYÊN đơn vị và giá trị nguồn — không quy đổi, không làm tròn, không viết lại định dạng số.
4. KHÔNG được nhắc tới giá bán, giá tham khảo, "giá tốt nhất", khuyến mãi dưới bất kỳ hình thức nào — mọi câu hỏi về giá phải dẫn về CTA liên hệ.
5. KHÔNG tự dựng bảng thông số kỹ thuật dạng HTML — bảng đó do phần mềm tự render, không phải việc của bạn.
6. KHÔNG tự viết Schema.org hay JSON-LD — phần mềm tự dựng.
7. Chỉ trả đúng các field liệt kê trong "OUTPUT JSON SCHEMA" bên dưới, không thêm field khác, không thêm text ngoài JSON.
8. ĐA DẠNG HOÁ CÁCH VIẾT: mỗi sản phẩm phải có cách mở đầu và cấu trúc câu KHÁC với sản phẩm khác — có thể mở đầu bằng câu hỏi kỹ thuật, bằng ứng dụng thực tế, hoặc mô tả trực tiếp. TUYỆT ĐỐI không lặp lại một khuôn câu mở đầu cố định cho hàng loạt sản phẩm.
9. KHI DỮ LIỆU MỎNG (nhiều field quan trọng nằm trong "DỮ LIỆU KHÔNG CÓ" khiến 1 mục có nguy cơ bị cụt): chuyển hướng mục đó sang nói về công dụng chung của loại sản phẩm này hoặc lưu ý chung khi chọn mua — KHÔNG bỏ trống, KHÔNG viết 1 câu cụt ngủn cho có. Vẫn phải tuân thủ tuyệt đối quy tắc 1-2 ở trên, không được suy đoán số liệu không có để lấp chỗ trống.
10. Ở mục hướng dẫn lựa chọn, VIẾT TỰ NHIÊN như người có kinh nghiệm thực tế đang tư vấn — ưu tiên nói về công trình/ứng dụng nào phù hợp, tiêu chí kỹ thuật cần cân nhắc, điểm mạnh của sản phẩm khi chọn. TUYỆT ĐỐI KHÔNG dùng công thức cố định kiểu "Quý khách vui lòng gửi bản vẽ/thông số công trình để được tư vấn chính xác mã sản phẩm [mã hàng]" lặp lại y hệt cho nhiều sản phẩm — câu này đọc như mẫu soạn sẵn, không tự nhiên. Nếu THỰC SỰ hợp lý để gợi ý khách cung cấp thêm thông tin công trình, diễn đạt khác nhau mỗi lần, lồng ghép tự nhiên vào mạch văn, không tách thành câu kết luận cứng nhắc.\n11. ĐA DẠNG TỪ NGỮ (Ver 4.9.9): có thể dùng tự nhiên các từ đồng nghĩa cùng nghĩa với thuật ngữ chính khi phù hợp văn cảnh (VD "máy biến áp"/"biến thế"/"MBA", "công suất"/"dung lượng") — KHÔNG BẮT BUỘC, chỉ là lựa chọn tự nhiên khi viết, không cần cố nhét vào nếu câu văn không hợp. TUYỆT ĐỐI không đổi Ý NGHĨA hay giá trị số khi đổi từ.\n12. ĐỊNH DẠNG DỄ ĐỌC (Ver 5.3 — theo phản hồi thật: nội dung "bức tường chữ" dân kỹ thuật/thu mua không đọc hết): khi 1 mục liệt kê từ 3 Ý TRỞ LÊN (VD nhiều đặc điểm, nhiều tiêu chí lựa chọn, nhiều ứng dụng), ƯU TIÊN trình bày dạng <ul><li> thay vì viết liền thành 1 đoạn văn dài. In đậm (<strong>) các cụm từ khoá/thông số quan trọng xuất hiện trong câu (VD <strong>lõi Amorphous</strong>, <strong>cấp điện áp 22/0.4kV</strong>) để người đọc lướt nhanh vẫn nắm được ý chính — KHÔNG in đậm toàn bộ câu, chỉ 1-3 cụm từ ngắn mỗi đoạn. Không bắt buộc dùng <ul> nếu nội dung chỉ có 1-2 ý liền mạch tự nhiên hơn khi viết văn xuôi."""


def _cfg_hieu_luc(outline_id):
    """Ver 3.8 — cfg thật sự dùng để dựng prompt: bản gốc OUTLINE_NOI_DUNG
    trộn với tuỳ chỉnh Outline Studio (nếu có). CHỈ ảnh hưởng goc_nhin/
    sections/ghi_chu_bo_qua — co_faq, danh sách field, giới hạn độ dài,
    QUY_TAC_CHUNG không đi qua đây, không đổi được qua Outline Studio."""
    import outline_studio as OS
    return OS.cfg_hieu_luc(outline_id, OUTLINE_NOI_DUNG[outline_id])


def he_thong(outline_id, site_cfg=None, mau='chuan'):
    """System instruction — R2-05 'System instruction' + 'CTA lấy từ cấu
    hình website' (site_cfg cung cấp tên site/hotline để AI biết ngữ cảnh
    thương hiệu, KHÔNG phải để AI tự viết khối CTA — khối CTA do renderer
    lắp cứng, xem render_phase2.py).

    Gate 2 Task 3: mau quyết định câu hướng dẫn độ dài — đây là điểm khác
    biệt THẬT trong system prompt giữa 'chuan' và 'ngan_gon', không chỉ ở
    user prompt.
    """
    cfg = _cfg_hieu_luc(outline_id)
    mcfg = _mau(mau)
    ten_site = (site_cfg or {}).get('ten', 'website kỹ thuật điện')
    return (
        f'Bạn là biên tập viên kỹ thuật viết nội dung sản phẩm cho {ten_site}, '
        f'chuyên ngành thiết bị điện trung/hạ thế B2B.\n'
        f'Đối tượng đọc: {cfg["goc_nhin"]}\n'
        f'MẪU BÀI: {mcfg["nhan"]}. {mcfg["huong_dan_do_dai"]}\n\n'
        f'{QUY_TAC_CHUNG}'
    )


def _json_schema(outline_id, mau='chuan'):
    cfg = OUTLINE_NOI_DUNG[outline_id]
    mcfg = _mau(mau)
    truong_can = [t for t in TRUONG_AI_DUOC_TRA_CHUAN if t not in mcfg['bo_qua_section']]
    truong = {k: 'string' for k in truong_can}
    if cfg['co_faq'] and not mcfg['bo_qua_faq']:
        truong[TRUONG_FAQ] = [{'q': 'string', 'a': 'string'}]
    return truong


def nguoi_dung(row, outline_id, site_cfg=None, mau='chuan'):
    """User prompt — dữ liệu sản phẩm (dùng effective_cot_ai, KHÔNG bao giờ
    có gia_list/ghi_chu_ban_dau) + cấu trúc nội dung riêng outline + JSON
    schema bắt buộc (R2-05).

    Gate 2 Task 3: mẫu 'ngan_gon' bỏ hẳn mục huong_dan_chon_html/faq khỏi
    CẤU TRÚC yêu cầu (không phải chỉ dặn AI viết ngắn) — nên cả prompt lẫn
    JSON schema đều khác NHAU THẬT giữa 2 mẫu, AI (kể cả mock) không có chỗ
    để trả những field đó, HTML ra tự nhiên khác nhau.
    """
    if outline_id not in OUTLINE_NOI_DUNG:
        raise ValueError(f'outline_id không có prompt Phase 2: {outline_id}')
    cfg = _cfg_hieu_luc(outline_id)
    mcfg = _mau(mau)
    profile_id = row['profile_id']

    fields = P.effective_cot_ai(profile_id, outline_id)
    nhan_cot = {'ten_goc': 'Tên hàng', 'thuong_hieu': 'Thương hiệu', 'quy_cach': 'Quy cách',
                'dvt': 'Đơn vị tính', 'tiet_dien': 'Tiết diện', 'cap_dien_ap': 'Cấp điện áp',
                'vat_lieu_ruot': 'Vật liệu ruột', 'cong_suat': 'Công suất',
                # Ver 4.9.9 — field delta-context tính bằng code (render_phase2.tinh_delta_context)
                'tier_cong_suat': 'Phân khúc công suất', 'sku_lien_ke_nho': 'Mã liền kề nhỏ hơn',
                'sku_lien_ke_lon': 'Mã liền kề lớn hơn', 'chenh_lech_nho': 'Chênh lệch so với mã nhỏ hơn',
                'chenh_lech_lon': 'Chênh lệch so với mã lớn hơn',
                'tai_uoc_tinh': 'Tải ước tính (tham khảo)',
                'may_tuong_thich': 'Máy biến áp tương thích',
                # Ver 4.9.5 — 6 field enrich catalogue đầu cáp/hộp nối
                'duong_kinh_cach_dien': 'Đường kính cách điện áp dụng',
                'kich_thuoc_i': 'Kích thước lắp đặt I', 'kich_thuoc_l': 'Kích thước lắp đặt L',
                'duong_ro_ngoai_troi': 'Chiều dài đường rò (ngoài trời)',
                'tieu_chuan_catalogue': 'Tiêu chuẩn áp dụng', 'test_dien': 'Kết quả test điện',
                # Ver 5.4 — 10 field catalogue máy biến áp + 2 field bảo hành/chứng nhận
                'to_dau_day': 'Tổ đấu dây', 'ton_hao_khong_tai': 'Tổn hao không tải (Po)',
                'ton_hao_ngan_mach': 'Tổn hao ngắn mạch (Pk)', 'dong_khong_tai': 'Dòng điện không tải (Io)',
                'dien_ap_ngan_mach': 'Điện áp ngắn mạch (Uk)', 'hieu_suat_e50': 'Hiệu suất năng lượng tối thiểu (E50)',
                'kich_thuoc_a': 'Kích thước A', 'kich_thuoc_b': 'Kích thước B',
                'kich_thuoc_c': 'Kích thước C', 'kich_thuoc_d': 'Kích thước D',
                'khoi_luong_dau': 'Khối lượng dầu', 'tong_khoi_luong': 'Tổng khối lượng',
                'bao_hanh_thang': 'Thời gian bảo hành', 'chung_nhan': 'Chứng nhận'}
    co = [(nhan_cot.get(k, k), row.get(k, '')) for k in fields if row.get(k, '')]
    thieu = [nhan_cot.get(k, k) for k in fields if not row.get(k, '')]

    du_lieu = '\n'.join(f'- {nhan}: {v}' for nhan, v in co)

    # Ver 2.8 — DYNAMIC SCHEMA: mọi cột Excel có giá trị mà chưa khai báo
    # trong PROFILES đều được đưa vào đây (đã lọc cột nội bộ ở
    # profiles.quet_cot_dong). Nhờ vậy enrich Excel thêm cột nào là AI
    # dùng được cột đó ngay, KHÔNG cần sửa code.
    dong = row.get('thong_so_dong') or {}
    if dong:
        them = '\n'.join(f'- {ten}: {gt}' for ten, gt in dong.items())
        # Ver 3.0 — CẢNH BÁO BẮT BUỘC cho cột hiệu suất TCVN: đó là MỨC SÀN
        # tiêu chuẩn quy định phải đạt, KHÔNG phải hiệu suất thực đo của máy.
        # Viết "máy có hiệu suất 98,2%" là SAI SỰ THẬT.
        if any('hiệu suất' in str(k).lower() and 'tối thiểu' in str(k).lower()
               for k in dong):
            them += ('\n\n[LƯU Ý BẮT BUỘC] Cột "Hiệu suất năng lượng tối thiểu '
                     'TCVN 8525:2015" là MỨC SÀN mà tiêu chuẩn quy định sản phẩm '
                     'phải đạt, KHÔNG phải hiệu suất thực đo của máy này. Chỉ được '
                     'viết dạng "đáp ứng mức hiệu suất tối thiểu ... theo TCVN '
                     '8525:2015". TUYỆT ĐỐI KHÔNG viết "máy có hiệu suất X%" hay '
                     '"hiệu suất đạt X%".')
        du_lieu += ('\n\nTHÔNG SỐ BỔ SUNG TỪ DỮ LIỆU NGUỒN (dùng được, '
                    'nhưng CHỈ dùng đúng con số ghi ở đây, không suy diễn thêm):\n' + them)

    if thieu:
        du_lieu += '\n\nDỮ LIỆU KHÔNG CÓ, TUYỆT ĐỐI KHÔNG ĐƯỢC NHẮC TỚI:\n' + ', '.join(thieu)

    sections_ap_dung = {k: v for k, v in cfg['sections'].items()
                        if k not in mcfg['bo_qua_section']}
    cau_truc = '\n'.join(
        f'- {truong} ({GIOI_HAN_DO_DAI.get(truong, "")}): {mo_ta}'
        for truong, mo_ta in sections_ap_dung.items())
    if cfg['co_faq'] and not mcfg['bo_qua_faq']:
        cau_truc += f'\n- faq ({GIOI_HAN_DO_DAI["faq"]}): 0-3 câu hỏi thường gặp dựa trên dữ liệu có, có thể để mảng rỗng nếu không có gì đáng hỏi.'

    ghi_chu_bo_qua = cfg.get('ghi_chu_bo_qua', '')

    return f"""DỮ LIỆU SẢN PHẨM (chỉ được dùng đúng những gì ở đây):
{du_lieu}

TÊN SẢN PHẨM: {row.get('ten_goc', '')}
MÃ SẢN PHẨM: {row.get('ma_goc', '')}
LOẠI NỘI DUNG: {cfg['nhan_outline']}
MẪU BÀI: {mcfg['nhan']} — {mcfg['huong_dan_do_dai']}

CẤU TRÚC NỘI DUNG CẦN VIẾT (mỗi mục là 1 field trong JSON trả về):
{cau_truc}
{('GHI CHÚ RIÊNG OUTLINE NÀY: ' + ghi_chu_bo_qua) if ghi_chu_bo_qua else ''}

OUTPUT JSON SCHEMA BẮT BUỘC (chỉ trả đúng JSON, không thêm chữ nào khác):
{json.dumps(_json_schema(outline_id, mau), ensure_ascii=False, indent=2)}"""


def xay_prompt(row, site_cfg=None, mau='chuan'):
    """Hàm tổng — trả (system_text, user_text, json_schema) cho 1 record +
    1 mẫu. Đây là hàm DUY NHẤT giao-dien.py / adapter gọi để lấy prompt
    Phase 2, không tự ghép chuỗi rời rạc ở nơi khác (cùng tinh thần R2-01).
    """
    _mau(mau)   # raise sớm nếu mau không hợp lệ, trước khi tốn công dựng prompt
    outline_id = row['outline_id']
    return (he_thong(outline_id, site_cfg, mau), nguoi_dung(row, outline_id, site_cfg, mau),
            _json_schema(outline_id, mau))


def truong_ai_duoc_tra(outline_id, mau='chuan'):
    cfg = OUTLINE_NOI_DUNG[outline_id]
    mcfg = _mau(mau)
    co_ban = [t for t in TRUONG_AI_DUOC_TRA_CHUAN if t not in mcfg['bo_qua_section']]
    return co_ban + ([TRUONG_FAQ] if cfg['co_faq'] and not mcfg['bo_qua_faq'] else [])
