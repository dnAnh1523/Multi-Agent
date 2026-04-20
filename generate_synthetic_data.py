"""
generate_synthetic_data.py
Tạo dữ liệu hóa đơn và báo cáo tài chính giả (synthetic) để test RAG pipeline.
Chạy: python generate_synthetic_data.py

Output: data/sample_invoices/
  - hoadon_001.pdf  (Hóa đơn GTGT - Công ty A bán cho Công ty B)
  - hoadon_002.pdf  (Hóa đơn GTGT - Công ty C bán cho Công ty D)
  - hoadon_003.pdf  (Hóa đơn GTGT - giá trị lớn, nhiều mặt hàng)
  - bao_cao_tai_chinh_q1.pdf (Báo cáo tài chính Q1/2026)
"""

import os
from pathlib import Path
from fpdf import FPDF

# --- Config ---
OUTPUT_DIR = Path("data/sample_invoices")
FONT_PATH = "E:\\Multi_Agent_RAG\\accounting-agent\\fonts\\dejavu_sans\\DejaVu_Sans\\DejaVuSansCondensed.ttf"
FONT_BOLD_PATH = "E:\\Multi_Agent_RAG\\accounting-agent\\fonts\\dejavu_sans\\DejaVu_Sans\\DejaVuSansCondensed-Bold.ttf"

# Màu sắc
COLOR_HEADER = (41, 128, 185)    # xanh dương
COLOR_TABLE_HEADER = (52, 73, 94) # xanh đậm
COLOR_ROW_ALT = (236, 240, 241)   # xám nhạt
COLOR_BORDER = (189, 195, 199)    # xám viền
COLOR_TOTAL = (231, 76, 60)       # đỏ cho tổng tiền


def make_pdf(landscape=False) -> FPDF:
    """Tạo FPDF instance đã config font tiếng Việt."""
    orientation = "L" if landscape else "P"
    pdf = FPDF(orientation=orientation, unit="mm", format="A4")
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("DejaVu", style="", fname=FONT_PATH)
    pdf.add_font("DejaVu", style="B", fname=FONT_BOLD_PATH)
    return pdf


def draw_header_box(pdf: FPDF, so_hd: str, ngay: str, mau_so: str, ky_hieu: str):
    """Vẽ phần header của hóa đơn GTGT."""
    # Tiêu đề chính
    pdf.set_font("DejaVu", style="B", size=16)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 10, "HÓA ĐƠN GIÁ TRỊ GIA TĂNG", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", style="", size=10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"(VAT INVOICE)", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)

    # Mẫu số và ký hiệu
    pdf.set_font("DejaVu", style="", size=9)
    pdf.set_text_color(0, 0, 0)
    effective_width = pdf.w - pdf.l_margin - pdf.r_margin
    col = effective_width / 3

    pdf.cell(col, 6, f"Mẫu số: {mau_so}", align="L")
    pdf.cell(col, 6, f"Ký hiệu: {ky_hieu}", align="C")
    pdf.cell(col, 6, f"Số: {so_hd}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.cell(0, 6, f"Ngày {ngay}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Đường kẻ ngang
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)


def draw_party_info(pdf: FPDF, label: str, ten: str, mst: str, dia_chi: str, tai_khoan: str = ""):
    """Vẽ thông tin bên mua / bên bán."""
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_text_color(*COLOR_TABLE_HEADER)
    pdf.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", style="", size=9)
    pdf.set_text_color(0, 0, 0)

    pdf.cell(35, 5.5, "Đơn vị:", )
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.cell(0, 5.5, ten, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", style="", size=9)
    pdf.cell(35, 5.5, "Mã số thuế:")
    pdf.cell(0, 5.5, mst, new_x="LMARGIN", new_y="NEXT")

    pdf.cell(35, 5.5, "Địa chỉ:")
    pdf.cell(0, 5.5, dia_chi, new_x="LMARGIN", new_y="NEXT")

    if tai_khoan:
        pdf.cell(35, 5.5, "Số TK:")
        pdf.cell(0, 5.5, tai_khoan, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)


def draw_items_table(pdf: FPDF, items: list[dict]):
    """
    Vẽ bảng hàng hóa/dịch vụ.
    items: list of dict với keys: stt, ten_hang, dvt, so_luong, don_gia, thanh_tien
    """
    effective_width = pdf.w - pdf.l_margin - pdf.r_margin
    col_widths = {
        "stt":        10,
        "ten_hang":   effective_width * 0.35,
        "dvt":        18,
        "so_luong":   22,
        "don_gia":    35,
        "thanh_tien": 35,
    }
    headers = ["STT", "Tên hàng hóa/dịch vụ", "ĐVT", "Số lượng", "Đơn giá", "Thành tiền"]
    row_h = 7

    # Header row
    pdf.set_fill_color(*COLOR_TABLE_HEADER)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", style="B", size=8)
    pdf.set_draw_color(*COLOR_BORDER)

    for header, key in zip(headers, col_widths.keys()):
        pdf.cell(col_widths[key], row_h, header, border=1, align="C", fill=True)
    pdf.ln()

    # Data rows
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("DejaVu", style="", size=8)
    tong_chua_thue = 0

    for i, item in enumerate(items):
        fill = i % 2 == 1
        pdf.set_fill_color(*COLOR_ROW_ALT)

        thanh_tien = item["so_luong"] * item["don_gia"]
        tong_chua_thue += thanh_tien

        pdf.cell(col_widths["stt"], row_h, str(item["stt"]), border=1, align="C", fill=fill)
        pdf.cell(col_widths["ten_hang"], row_h, item["ten_hang"], border=1, fill=fill)
        pdf.cell(col_widths["dvt"], row_h, item["dvt"], border=1, align="C", fill=fill)
        pdf.cell(col_widths["so_luong"], row_h, f'{item["so_luong"]:,}', border=1, align="R", fill=fill)
        pdf.cell(col_widths["don_gia"], row_h, f'{item["don_gia"]:,.0f}', border=1, align="R", fill=fill)
        pdf.cell(col_widths["thanh_tien"], row_h, f'{thanh_tien:,.0f}', border=1, align="R", fill=fill)
        pdf.ln()

    return tong_chua_thue


def draw_totals(pdf: FPDF, tong_chua_thue: float, thue_suat: float = 0.10):
    """Vẽ phần tổng tiền, thuế GTGT, tổng thanh toán."""
    effective_width = pdf.w - pdf.l_margin - pdf.r_margin
    label_w = effective_width * 0.65
    value_w = effective_width * 0.35
    row_h = 7

    thue_gtgt = tong_chua_thue * thue_suat
    tong_thanh_toan = tong_chua_thue + thue_gtgt

    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_text_color(0, 0, 0)

    # Cộng tiền hàng
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(label_w, row_h, "Cộng tiền hàng:", border=1, align="R", fill=True)
    pdf.cell(value_w, row_h, f'{tong_chua_thue:,.0f} VNĐ', border=1, align="R", fill=True)
    pdf.ln()

    # Thuế GTGT
    pdf.cell(label_w, row_h, f"Thuế suất GTGT: {int(thue_suat*100)}%:", border=1, align="R", fill=True)
    pdf.cell(value_w, row_h, f'{thue_gtgt:,.0f} VNĐ', border=1, align="R", fill=True)
    pdf.ln()

    # Tổng thanh toán
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_fill_color(*COLOR_HEADER)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(label_w, row_h + 1, "TỔNG CỘNG TIỀN THANH TOÁN:", border=1, align="R", fill=True)
    pdf.cell(value_w, row_h + 1, f'{tong_thanh_toan:,.0f} VNĐ', border=1, align="R", fill=True)
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("DejaVu", style="", size=8)
    pdf.ln(2)

    # Số tiền bằng chữ (đơn giản hóa)
    pdf.cell(0, 6, f"Số tiền viết bằng chữ: {so_tien_bang_chu(int(tong_thanh_toan))}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    return tong_thanh_toan


def so_tien_bang_chu(so: int) -> str:
    """Chuyển số tiền thành chữ (đơn giản hóa cho synthetic data)."""
    ty = so // 1_000_000_000
    trieu = (so % 1_000_000_000) // 1_000_000
    ngan = (so % 1_000_000) // 1_000
    don_vi = so % 1_000

    parts = []
    if ty: parts.append(f"{ty} tỷ")
    if trieu: parts.append(f"{trieu} triệu")
    if ngan: parts.append(f"{ngan} nghìn")
    if don_vi: parts.append(f"{don_vi}")

    return " ".join(parts) + " đồng" if parts else "Không đồng"


def draw_signatures(pdf: FPDF):
    """Vẽ phần ký tên."""
    effective_width = pdf.w - pdf.l_margin - pdf.r_margin
    col = effective_width / 2

    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(col, 6, "NGƯỜI MUA HÀNG", align="C")
    pdf.cell(col, 6, "NGƯỜI BÁN HÀNG", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(col, 5, "(Ký, ghi rõ họ tên)", align="C")
    pdf.cell(col, 5, "(Ký, đóng dấu, ghi rõ họ tên)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)

    # Placeholder chữ ký
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("DejaVu", style="", size=9)
    pdf.cell(col, 5, "Nguyễn Văn Mua", align="C")
    pdf.cell(col, 5, "Trần Thị Bán", align="C", new_x="LMARGIN", new_y="NEXT")


# ============================================================
# HÓA ĐƠN 001: Công ty phần mềm bán dịch vụ cho công ty SX
# ============================================================
def generate_hoadon_001(output_path: Path):
    pdf = make_pdf()
    pdf.add_page()

    draw_header_box(pdf,
        so_hd="0000001",
        ngay="05 tháng 01 năm 2026",
        mau_so="01GTKT0/001",
        ky_hieu="AA/26E"
    )

    draw_party_info(pdf,
        label="ĐƠN VỊ BÁN HÀNG:",
        ten="Công ty TNHH Phần Mềm Alpha",
        mst="0101234567",
        dia_chi="Số 10, Đường Láng Hạ, Quận Đống Đa, Hà Nội",
        tai_khoan="19034521687015 - Ngân hàng Techcombank CN Hà Nội"
    )

    draw_party_info(pdf,
        label="ĐƠN VỊ MUA HÀNG:",
        ten="Công ty CP Sản Xuất Bình Minh",
        mst="0312345678",
        dia_chi="Lô B5, KCN Bình Dương, Tỉnh Bình Dương",
        tai_khoan="10203045678901 - Ngân hàng Vietcombank CN Bình Dương"
    )

    items = [
        {"stt": 1, "ten_hang": "Phần mềm quản lý kho (giấy phép 1 năm)", "dvt": "Bộ", "so_luong": 1, "don_gia": 15_000_000},
        {"stt": 2, "ten_hang": "Dịch vụ cài đặt và cấu hình hệ thống", "dvt": "Lần", "so_luong": 1, "don_gia": 5_000_000},
        {"stt": 3, "ten_hang": "Đào tạo sử dụng phần mềm (8 giờ)", "dvt": "Giờ", "so_luong": 8, "don_gia": 500_000},
        {"stt": 4, "ten_hang": "Hỗ trợ kỹ thuật từ xa (6 tháng)", "dvt": "Tháng", "so_luong": 6, "don_gia": 1_200_000},
    ]

    tong = draw_items_table(pdf, items)
    draw_totals(pdf, tong, thue_suat=0.10)

    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "Hình thức thanh toán: Chuyển khoản ngân hàng  |  Hạn thanh toán: 30 ngày kể từ ngày xuất hóa đơn",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    draw_signatures(pdf)
    pdf.output(str(output_path))
    print(f"✅ Tạo xong: {output_path}")


# ============================================================
# HÓA ĐƠN 002: Nhà cung cấp vật tư bán cho công ty XD
# ============================================================
def generate_hoadon_002(output_path: Path):
    pdf = make_pdf()
    pdf.add_page()

    draw_header_box(pdf,
        so_hd="0000002",
        ngay="12 tháng 02 năm 2026",
        mau_so="01GTKT0/001",
        ky_hieu="BB/26E"
    )

    draw_party_info(pdf,
        label="ĐƠN VỊ BÁN HÀNG:",
        ten="Công ty TNHH Vật Tư Xây Dựng Đại Thành",
        mst="0201987654",
        dia_chi="Số 45, Đường Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh",
        tai_khoan="00701234567890 - Ngân hàng BIDV CN TP.HCM"
    )

    draw_party_info(pdf,
        label="ĐƠN VỊ MUA HÀNG:",
        ten="Công ty CP Xây Dựng Hoàng Long",
        mst="0400112233",
        dia_chi="Số 88, Đường Trần Phú, TP. Đà Nẵng",
        tai_khoan="21100000123456 - Ngân hàng Agribank CN Đà Nẵng"
    )

    items = [
        {"stt": 1, "ten_hang": "Xi măng PCB40 (bao 50kg)", "dvt": "Bao", "so_luong": 500, "don_gia": 95_000},
        {"stt": 2, "ten_hang": "Thép thanh D16 (cuộn 100kg)", "dvt": "Cuộn", "so_luong": 20, "don_gia": 4_200_000},
        {"stt": 3, "ten_hang": "Gạch ốp lát ceramic 60x60cm", "dvt": "m²", "so_luong": 200, "don_gia": 185_000},
        {"stt": 4, "ten_hang": "Cát vàng xây dựng", "dvt": "m³", "so_luong": 50, "don_gia": 280_000},
        {"stt": 5, "ten_hang": "Phí vận chuyển", "dvt": "Chuyến", "so_luong": 3, "don_gia": 1_500_000},
    ]

    tong = draw_items_table(pdf, items)
    draw_totals(pdf, tong, thue_suat=0.08)

    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "Hình thức thanh toán: Tiền mặt hoặc chuyển khoản  |  Ghi chú: Hàng đã kiểm tra chất lượng đạt tiêu chuẩn TCVN",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    draw_signatures(pdf)
    pdf.output(str(output_path))
    print(f"✅ Tạo xong: {output_path}")


# ============================================================
# HÓA ĐƠN 003: Dịch vụ tư vấn kế toán - giá trị lớn
# ============================================================
def generate_hoadon_003(output_path: Path):
    pdf = make_pdf()
    pdf.add_page()

    draw_header_box(pdf,
        so_hd="0000003",
        ngay="20 tháng 03 năm 2026",
        mau_so="01GTKT0/001",
        ky_hieu="CC/26E"
    )

    draw_party_info(pdf,
        label="ĐƠN VỊ BÁN HÀNG:",
        ten="Công ty TNHH Kiểm Toán và Tư Vấn Phương Nam",
        mst="0302468012",
        dia_chi="Tầng 15, Tòa nhà Landmark, Số 2 Tôn Đức Thắng, Quận 1, TP.HCM",
        tai_khoan="11300987654321 - Ngân hàng Vietinbank CN TP.HCM"
    )

    draw_party_info(pdf,
        label="ĐƠN VỊ MUA HÀNG:",
        ten="Tập đoàn Sản Xuất Toàn Cầu Việt Nam",
        mst="0100135791",
        dia_chi="Số 1, Phố Tràng Tiền, Quận Hoàn Kiếm, Hà Nội",
        tai_khoan="10102030405060 - Ngân hàng MB Bank CN Hà Nội"
    )

    items = [
        {"stt": 1, "ten_hang": "Dịch vụ kiểm toán báo cáo tài chính năm 2025", "dvt": "Hợp đồng", "so_luong": 1, "don_gia": 80_000_000},
        {"stt": 2, "ten_hang": "Tư vấn thuế TNDN và GTGT năm 2025", "dvt": "Hợp đồng", "so_luong": 1, "don_gia": 25_000_000},
        {"stt": 3, "ten_hang": "Lập và nộp báo cáo quyết toán thuế", "dvt": "Bộ hồ sơ", "so_luong": 2, "don_gia": 15_000_000},
        {"stt": 4, "ten_hang": "Tư vấn tái cơ cấu tài chính doanh nghiệp", "dvt": "Ngày công", "so_luong": 10, "don_gia": 5_000_000},
        {"stt": 5, "ten_hang": "Đào tạo nghiệp vụ kế toán nội bộ", "dvt": "Buổi", "so_luong": 4, "don_gia": 8_000_000},
        {"stt": 6, "ten_hang": "Phần mềm kế toán MISA SME (bản quyền)", "dvt": "Năm", "so_luong": 1, "don_gia": 12_000_000},
    ]

    tong = draw_items_table(pdf, items)
    draw_totals(pdf, tong, thue_suat=0.10)

    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5,
        "Hình thức thanh toán: Chuyển khoản ngân hàng, thanh toán 2 đợt:\n"
        "- Đợt 1 (50%): Trong vòng 7 ngày kể từ ngày ký hợp đồng\n"
        "- Đợt 2 (50%): Sau khi bàn giao đầy đủ hồ sơ và báo cáo",
        new_x="LMARGIN", new_y="NEXT"
    )
    pdf.ln(4)

    draw_signatures(pdf)
    pdf.output(str(output_path))
    print(f"✅ Tạo xong: {output_path}")


# ============================================================
# BÁO CÁO TÀI CHÍNH Q1/2026
# ============================================================
def generate_bao_cao_tai_chinh(output_path: Path):
    pdf = make_pdf()
    pdf.add_page()

    # Tiêu đề
    pdf.set_font("DejaVu", style="B", size=14)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 8, "BÁO CÁO TÀI CHÍNH QUÝ I/2026", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", style="", size=10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, "Công ty CP Sản Xuất Bình Minh - MST: 0312345678", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Kỳ báo cáo: 01/01/2026 - 31/03/2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Đường kẻ
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(5)

    def draw_financial_table(title: str, rows: list[tuple]):
        """Vẽ bảng số liệu tài chính."""
        effective_width = pdf.w - pdf.l_margin - pdf.r_margin

        pdf.set_font("DejaVu", style="B", size=10)
        pdf.set_text_color(*COLOR_TABLE_HEADER)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")

        col1 = effective_width * 0.55
        col2 = effective_width * 0.225
        col3 = effective_width * 0.225

        # Header
        pdf.set_font("DejaVu", style="B", size=8)
        pdf.set_fill_color(*COLOR_TABLE_HEADER)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(col1, 7, "Chỉ tiêu", border=1, fill=True)
        pdf.cell(col2, 7, "Q1/2026", border=1, align="R", fill=True)
        pdf.cell(col3, 7, "Q1/2025", border=1, align="R", fill=True)
        pdf.ln()

        # Rows
        pdf.set_text_color(0, 0, 0)
        for i, (label, val_2026, val_2025, is_bold) in enumerate(rows):
            fill = i % 2 == 1
            pdf.set_fill_color(*COLOR_ROW_ALT)
            if is_bold:
                pdf.set_font("DejaVu", style="B", size=8)
                pdf.set_fill_color(*COLOR_HEADER)
                pdf.set_text_color(255, 255, 255)
            else:
                pdf.set_font("DejaVu", style="", size=8)
                pdf.set_text_color(0, 0, 0)

            pdf.cell(col1, 6.5, f"  {label}", border=1, fill=True)
            pdf.cell(col2, 6.5, f"{val_2026:,.0f}" if isinstance(val_2026, (int, float)) else val_2026,
                     border=1, align="R", fill=True)
            pdf.cell(col3, 6.5, f"{val_2025:,.0f}" if isinstance(val_2025, (int, float)) else val_2025,
                     border=1, align="R", fill=True)
            pdf.ln()

        pdf.ln(4)

    # --- Kết quả kinh doanh ---
    draw_financial_table("I. KẾT QUẢ HOẠT ĐỘNG KINH DOANH (Đơn vị: VNĐ)", [
        ("Doanh thu thuần",              4_850_000_000, 3_920_000_000, False),
        ("Giá vốn hàng bán",             3_120_000_000, 2_580_000_000, False),
        ("Lợi nhuận gộp",                1_730_000_000, 1_340_000_000, True),
        ("Chi phí bán hàng",               245_000_000,   198_000_000, False),
        ("Chi phí quản lý doanh nghiệp",   312_000_000,   267_000_000, False),
        ("Lợi nhuận từ HĐKD",            1_173_000_000,   875_000_000, True),
        ("Thu nhập khác",                   15_000_000,    12_000_000, False),
        ("Chi phí khác",                     8_000_000,     5_000_000, False),
        ("LỢI NHUẬN TRƯỚC THUẾ",         1_180_000_000,   882_000_000, True),
        ("Thuế TNDN (20%)",                236_000_000,   176_400_000, False),
        ("LỢI NHUẬN SAU THUẾ",           944_000_000,   705_600_000, True),
    ])

    # --- Tình hình công nợ ---
    draw_financial_table("II. TÌNH HÌNH CÔNG NỢ (Đơn vị: VNĐ)", [
        ("Phải thu khách hàng",          1_250_000_000,   980_000_000, False),
        ("Trong đó: Quá hạn >30 ngày",     180_000_000,   145_000_000, False),
        ("Phải trả nhà cung cấp",          870_000_000,   720_000_000, False),
        ("Tổng dư nợ vay ngân hàng",     2_500_000_000, 2_800_000_000, True),
        ("Hệ số thanh toán hiện hành",           "1.85",       "1.72", False),
        ("Hệ số thanh toán nhanh",               "1.24",       "1.18", False),
    ])

    # --- Ghi chú ---
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_text_color(*COLOR_TABLE_HEADER)
    pdf.cell(0, 6, "III. GHI CHÚ VÀ NHẬN XÉT", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_text_color(0, 0, 0)
    notes = [
        "1. Doanh thu Q1/2026 tăng 23.7% so với cùng kỳ năm 2025, vượt kế hoạch 8.2%.",
        "2. Lợi nhuận sau thuế tăng 33.8% nhờ cải thiện hiệu quả quản lý chi phí sản xuất.",
        "3. Khoản phải thu quá hạn chiếm 14.4% tổng phải thu - cần đẩy mạnh thu hồi công nợ.",
        "4. Dư nợ vay ngân hàng giảm 10.7% so với Q1/2025, cải thiện cơ cấu vốn.",
        "5. Báo cáo được lập theo Chuẩn mực Kế toán Việt Nam (VAS) và Thông tư 200/2014/TT-BTC.",
    ]
    for note in notes:
        pdf.multi_cell(0, 5.5, note, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # Ký tên
    effective_width = pdf.w - pdf.l_margin - pdf.r_margin
    col = effective_width / 3
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(col, 6, "NGƯỜI LẬP BẢNG", align="C")
    pdf.cell(col, 6, "KẾ TOÁN TRƯỞNG", align="C")
    pdf.cell(col, 6, "GIÁM ĐỐC", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(col, 5, "(Ký, ghi rõ họ tên)", align="C")
    pdf.cell(col, 5, "(Ký, ghi rõ họ tên)", align="C")
    pdf.cell(col, 5, "(Ký, đóng dấu)", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(output_path))
    print(f"✅ Tạo xong: {output_path}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("🚀 Bắt đầu tạo synthetic data...\n")

    generate_hoadon_001(OUTPUT_DIR / "hoadon_001.pdf")
    generate_hoadon_002(OUTPUT_DIR / "hoadon_002.pdf")
    generate_hoadon_003(OUTPUT_DIR / "hoadon_003.pdf")
    generate_bao_cao_tai_chinh(OUTPUT_DIR / "bao_cao_tai_chinh_q1.pdf")

    print(f"\n✅ Hoàn thành! Đã tạo {len(list(OUTPUT_DIR.glob('*.pdf')))} file tại: {OUTPUT_DIR}/")
    print("\nDanh sách file:")
    for f in sorted(OUTPUT_DIR.glob("*.pdf")):
        size_kb = f.stat().st_size / 1024
        print(f"  📄 {f.name} ({size_kb:.1f} KB)")