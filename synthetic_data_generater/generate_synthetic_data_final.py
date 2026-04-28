"""
generate_all_invoices.py
Tích hợp toàn bộ dữ liệu mẫu cho hệ thống kế toán.
- Dữ liệu cơ bản (synthetic) : 20 hóa đơn (12 đầu vào, 8 đầu ra) + báo cáo Q1 + tờ khai thuế tháng 3
- Bổ sung 17 hóa đơn (004-020) từ generate_more_invoices
- Edge cases (021-024) và báo cáo Q2 có lỗ

Chạy: python generate_all_invoices.py
Output: data/sample_invoices/*.pdf
"""

import os
import sys
import random
from pathlib import Path
from datetime import datetime
from fpdf import FPDF

# ======================== CẤU HÌNH CHUNG ========================
OUTPUT_DIR = Path("data/sample_invoices")
FONT_PATHS = [
    r"C:\Windows\\Fonts\\DejaVuSansCondensed.ttf",
    "fonts/dejavu_sans/DejaVu_Sans/DejaVuSansCondensed.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
]
FONT_BOLD_PATHS = [
    r"C:\Windows\\Fonts\\DejaVuSansCondensed-Bold.ttf",
    "fonts/dejavu_sans/DejaVu_Sans/DejaVuSansCondensed-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
]

def find_font(paths):
    for p in paths:
        if Path(p).exists():
            return p
    return None

FONT_PATH      = find_font(FONT_PATHS)
FONT_BOLD_PATH = find_font(FONT_BOLD_PATHS)

if not FONT_PATH or not FONT_BOLD_PATH:
    print("❌ Không tìm thấy font DejaVuSansCondensed.")
    print("   Vui lòng cài font hoặc điều chỉnh đường dẫn trong script.")
    sys.exit(1)

# Màu sắc thống nhất
COLOR_HEADER       = (41, 128, 185)
COLOR_TABLE_HEADER = (52, 73, 94)
COLOR_ROW_ALT      = (236, 240, 241)
COLOR_BORDER       = (189, 195, 199)
COLOR_WARNING      = (192, 57, 43)
COLOR_NEGATIVE     = (231, 76, 60)

# ======================== ĐỐI TƯỢNG CÔNG TY ========================
BINH_MINH = {
    "ten": "Công ty CP Sản Xuất Bình Minh",
    "mst": "0312345678",
    "dia_chi": "Lô B5, KCN Bình Dương, Tỉnh Bình Dương",
    "tk": "123456789012 - Ngân hàng Vietcombank",
}

# Nhà cung cấp (từ synthetic và more)
NHA_CUNG_CAP = [
    {"ten": "Công ty TNHH Nguyên Liệu Nhựa Đại Việt",      "mst": "0501234567", "dia_chi": "KCN Sóng Thần, Bình Dương",                                  "tk": "12300111222333 - BIDV CN Bình Dương"},
    {"ten": "Công ty CP Thép Miền Nam",                      "mst": "0302345678", "dia_chi": "Số 12, Đường D1, KCN Biên Hòa, Đồng Nai",                    "tk": "20100456789012 - Vietinbank CN Đồng Nai"},
    {"ten": "Công ty TNHH Bao Bì Xanh",                     "mst": "0603456789", "dia_chi": "Số 88, Đường Lê Lợi, TP. Thủ Dầu Một, Bình Dương",           "tk": "00701122334455 - Agribank CN Bình Dương"},
    {"ten": "Công ty CP Điện Cơ Việt Nam",                   "mst": "0104567890", "dia_chi": "Số 45, Phố Trung Kính, Quận Cầu Giấy, Hà Nội",               "tk": "19033344556677 - Techcombank CN Hà Nội"},
    {"ten": "Công ty TNHH Hóa Chất Đông Nam Á",             "mst": "0805678901", "dia_chi": "Số 23, Đường Cộng Hòa, Quận Tân Bình, TP.HCM",               "tk": "10500998877665 - MB Bank CN TP.HCM"},
    {"ten": "Công ty CP Vận Tải Logistics Toàn Cầu",         "mst": "0206789012", "dia_chi": "Số 100, Xa Lộ Hà Nội, TP. Thủ Đức, TP.HCM",                 "tk": "21100556677889 - Agribank CN TP.HCM"},
    {"ten": "Công ty TNHH Thiết Bị Công Nghiệp Phương Đông", "mst": "0507890123", "dia_chi": "Lô C3, KCN Nhơn Trạch, Đồng Nai",                           "tk": "00201345678901 - BIDV CN Đồng Nai"},
    {"ten": "Công ty CP Giấy Tân Mai",                       "mst": "0608901234", "dia_chi": "Số 1, Đường Tân Mai, TP. Biên Hòa, Đồng Nai",                "tk": "11300234567890 - Vietinbank CN Đồng Nai"},
    {"ten": "Công ty TNHH Dầu Nhớt Castrol Việt Nam",       "mst": "0109012345", "dia_chi": "Tầng 10, Tòa nhà PV GAS, Số 673 Nguyễn Hữu Thọ, TP.HCM",    "tk": "19035566778899 - Techcombank CN TP.HCM"},
    {"ten": "Công ty CP Phụ Tùng Cơ Khí Tiến Đạt",          "mst": "0310123456", "dia_chi": "Số 56, Đường 30/4, TP. Thủ Dầu Một, Bình Dương",             "tk": "10202233445566 - Vietcombank CN Bình Dương"},
]

KHACH_HANG = [
    {"ten": "Công ty CP Điện Tử Samsung Vina",     "mst": "0311234567", "dia_chi": "KCN Yên Phong, Tỉnh Bắc Ninh",                                     "tk": "10501234567890 - MB Bank CN Bắc Ninh"},
    {"ten": "Công ty TNHH LG Electronics Việt Nam","mst": "0412345678", "dia_chi": "KCN Tràng Duệ, Tỉnh Hải Phòng",                                    "tk": "11301234567890 - Vietinbank CN Hải Phòng"},
    {"ten": "Công ty CP Nhựa Tiền Phong",          "mst": "0113456789", "dia_chi": "Số 6, Đường Trần Phú, Quận Hải An, Hải Phòng",                     "tk": "00701234567890 - Agribank CN Hải Phòng"},
    {"ten": "Công ty TNHH Panasonic Việt Nam",     "mst": "0514567890", "dia_chi": "KCN Thăng Long, Hà Nội",                                           "tk": "19034567890123 - Techcombank CN Hà Nội"},
    {"ten": "Công ty CP Cơ Khí Chính Xác Hà Nội", "mst": "0115678901", "dia_chi": "Số 74, Đường Nguyễn Trãi, Quận Thanh Xuân, Hà Nội",               "tk": "20105678901234 - Vietinbank CN Hà Nội"},
    {"ten": "Công ty TNHH Fuji Xerox Việt Nam",   "mst": "0816789012", "dia_chi": "Tầng 8, Tòa nhà Hà Nội Tower, Số 49 Hai Bà Trưng, Hà Nội",        "tk": "00206789012345 - BIDV CN Hà Nội"},
    {"ten": "Tập đoàn Dệt May Việt Nam (VINATEX)", "mst": "0117890123", "dia_chi": "Số 25, Bà Triệu, Quận Hoàn Kiếm, Hà Nội",                         "tk": "10207890123456 - Vietcombank CN Hà Nội"},
]

# Các đối tượng phụ cho edge cases
NCC_THIET_BI = NHA_CUNG_CAP[6]  # Công ty TNHH Thiết Bị Công Nghiệp Phương Đông
SAMSUNG = KHACH_HANG[0]
NCC_SINGAPORE = {
    "ten": "ABC Industrial Supplies Co., Ltd",
    "mst": "S12345678A",
    "dia_chi": "10 Tuas Avenue 1, Singapore 639514",
    "tk": "SGD Account: 123-456-789 - DBS Bank Singapore",
}

# ======================== CÁC HÀM VẼ PDF CHUNG ========================
def make_pdf():
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("DejaVu", style="",  fname=FONT_PATH)
    pdf.add_font("DejaVu", style="B", fname=FONT_BOLD_PATH)
    return pdf

def draw_header(pdf, so_hd, ngay, mau_so, ky_hieu, dieu_chinh_cho=None):
    color = COLOR_WARNING if dieu_chinh_cho else COLOR_HEADER
    pdf.set_font("DejaVu", style="B", size=14)
    pdf.set_text_color(*color)
    title = ("HÓA ĐƠN ĐIỀU CHỈNH - " if dieu_chinh_cho else "") + "HÓA ĐƠN GIÁ TRỊ GIA TĂNG"
    pdf.cell(0, 10, title, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", style="", size=9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "(VAT INVOICE)", align="C", new_x="LMARGIN", new_y="NEXT")
    if dieu_chinh_cho:
        pdf.set_text_color(*COLOR_WARNING)
        pdf.set_font("DejaVu", style="B", size=9)
        pdf.cell(0, 6, f"*** ĐIỀU CHỈNH CHO HOÁ ĐƠN SỐ {dieu_chinh_cho} ***",
                 align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_font("DejaVu", style="", size=9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(w/3, 5.5, f"Mẫu số: {mau_so}", align="L")
    pdf.cell(w/3, 5.5, f"Ký hiệu: {ky_hieu}", align="C")
    pdf.cell(w/3, 5.5, f"Số: {so_hd}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5.5, f"Ngày {ngay}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)

def draw_party(pdf, label, info):
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_text_color(*COLOR_TABLE_HEADER)
    pdf.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    for lbl, key, bold in [
        ("Đơn vị:", "ten", True),
        ("Mã số thuế:", "mst", False),
        ("Địa chỉ:", "dia_chi", False),
        ("Số TK:", "tk", False),
    ]:
        if info.get(key):
            pdf.set_font("DejaVu", style="", size=9)
            pdf.cell(35, 5.5, lbl)
            pdf.set_font("DejaVu", style="B" if bold else "", size=9)
            pdf.cell(0, 5.5, info[key], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

def draw_items_standard(pdf, items):
    w = pdf.w - pdf.l_margin - pdf.r_margin
    cols = {"stt": 10, "ten": w*0.36, "dvt": 16, "sl": 20, "dg": 33, "tt": 33}
    headers = ["STT", "Tên hàng hóa/dịch vụ", "DVT", "Số lượng", "Đơn giá", "Thành tiền"]
    rh = 7
    pdf.set_fill_color(*COLOR_TABLE_HEADER)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", style="B", size=8)
    for h, k in zip(headers, cols):
        pdf.cell(cols[k], rh, h, border=1, align="C", fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    tong = 0
    for i, item in enumerate(items):
        tt = item["sl"] * item["dg"]
        tong += tt
        fill = i % 2 == 1
        pdf.set_fill_color(*COLOR_ROW_ALT)
        pdf.set_font("DejaVu", style="", size=8)
        pdf.cell(cols["stt"], rh, str(item["stt"]), border=1, align="C", fill=fill)
        pdf.cell(cols["ten"], rh, item["ten"],       border=1, fill=fill)
        pdf.cell(cols["dvt"], rh, item["dvt"],       border=1, align="C", fill=fill)
        pdf.cell(cols["sl"],  rh, f'{item["sl"]:,}', border=1, align="R", fill=fill)
        pdf.cell(cols["dg"],  rh, f'{item["dg"]:,.0f}', border=1, align="R", fill=fill)
        pdf.cell(cols["tt"],  rh, f'{tt:,.0f}',      border=1, align="R", fill=fill)
        pdf.ln()
    return tong

def draw_totals_standard(pdf, tong, thue=0.10):
    w = pdf.w - pdf.l_margin - pdf.r_margin
    lw, vw = w * 0.65, w * 0.35
    rh = 7
    thue_tien  = int(tong * thue)
    thanh_toan = int(tong) + thue_tien
    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_fill_color(245, 245, 245)
    for lbl, val in [
        ("Cộng tiền hàng:", f"{int(tong):,} VND"),
        (f"Thuế suất GTGT: {int(thue*100)}%:", f"{thue_tien:,} VND"),
    ]:
        pdf.cell(lw, rh, lbl, border=1, align="R", fill=True)
        pdf.cell(vw, rh, val, border=1, align="R", fill=True)
        pdf.ln()
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_fill_color(*COLOR_HEADER)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(lw, rh+1, "TỔNG CỘNG TIỀN THANH TOÁN:", border=1, align="R", fill=True)
    pdf.cell(vw, rh+1, f"{thanh_toan:,} VND", border=1, align="R", fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("DejaVu", style="", size=8)
    pdf.ln(2)
    return thanh_toan

def draw_signatures(pdf):
    w = pdf.w - pdf.l_margin - pdf.r_margin
    col = w / 2
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.cell(col, 6, "NGƯỜI MUA HÀNG", align="C")
    pdf.cell(col, 6, "NGƯỜI BÁN HÀNG", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(col, 5, "(Ký, ghi rõ họ tên)", align="C")
    pdf.cell(col, 5, "(Ký, đóng dấu, ghi rõ họ tên)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(18)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("DejaVu", style="", size=9)
    pdf.cell(col, 5, "Nguyễn Văn Mua", align="C")
    pdf.cell(col, 5, "Trần Thị Bán",   align="C", new_x="LMARGIN", new_y="NEXT")

def footer_note(pdf, ht="Chuyển khoản ngân hàng", han="30 ngày kể từ ngày xuất hóa đơn", ghi_chu=""):
    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_text_color(100, 100, 100)
    text = f"Hình thức thanh toán: {ht}  |  Hạn thanh toán: {han}"
    if ghi_chu:
        text += f"\nGhi chú: {ghi_chu}"
    pdf.multi_cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

# ======================== PHẦN 1: DỮ LIỆU SYNTHETIC BAN ĐẦU ========================
def gen_synthetic_batch():
    """Tạo 12 hóa đơn đầu vào + 8 hóa đơn đầu ra + báo cáo Q1 + tờ khai thuế tháng 3"""
    random.seed(0)  # Đảm bảo kết quả lặp lại khi dùng random

    # Dữ liệu cơ sở cho synthetic
    suppliers_base = [
        {"ten": "Công ty TNHH Thép Việt", "mst": "0101234567", "dia_chi": "KCN Quang Minh, Hà Nội"},
        {"ten": "Tổng kho Hóa chất Miền Nam", "mst": "0309876543", "dia_chi": "Quận 7, TP.HCM"},
        {"ten": "Cơ khí Chính xác ABC", "mst": "3701234444", "dia_chi": "Thuận An, Bình Dương"},
        {"ten": "Năng lượng Xanh", "mst": "0105556667", "dia_chi": "Cầu Giấy, Hà Nội"}
    ]
    customers_base = [
        {"ten": "Công ty Bao bì Toàn Cầu", "mst": "0311223344", "dia_chi": "KCN Tân Bình, TP.HCM"},
        {"ten": "Nhựa Gia dụng Minh Phát", "mst": "3700112233", "dia_chi": "Dĩ An, Bình Dương"}
    ]

    input_vat_march = 0
    output_vat_march = 0

    # 12 hóa đơn đầu vào (Bình Minh mua)
    for i in range(1, 13):
        supplier = random.choice(suppliers_base)
        date = datetime(2026, random.randint(1, 6), random.randint(1, 28))
        ngay_str = date.strftime("%d/%m/%Y")

        items = [
            {"ten": "Nguyên liệu nhựa PP", "sl": random.randint(100, 500), "dvt": "kg", "don_gia": 45000, "stt": 1},
            {"ten": "Hóa chất phụ gia", "sl": random.randint(10, 50), "dvt": "lít", "don_gia": 120000, "stt": 2}
        ]
        # Chuyển đổi sang định dạng items chuẩn (dg, sl, ten, dvt)
        items_std = [{"stt": it["stt"], "ten": it["ten"], "dvt": it["dvt"], "sl": it["sl"], "dg": it["don_gia"]} for it in items]

        vat_rate = 10
        # Edge case nhỏ trong synthetic
        if i == 1:
            items_std.append({"stt": 3, "ten": "Chiết khấu thương mại", "dvt": "Lần", "sl": 1, "dg": -500000})
        if i == 2:
            vat_rate = 0
        if i == 3:
            vat_rate = 5
        if i == 4:
            vat_rate = 8
        if i == 5:
            # Thiếu MST người mua (sẽ xử lý trong vẽ)
            pass

        # Tạo PDF
        pdf = make_pdf()
        pdf.add_page()
        so_hd = f"{i:07d}"
        ky_hieu = "BM/26E"
        draw_header(pdf, so_hd, ngay_str, "1/001", ky_hieu)
        draw_party(pdf, "ĐƠN VỊ BÁN HÀNG:", supplier)
        # Nếu i == 5 thì xóa MST của người mua
        buyer = BINH_MINH.copy()
        if i == 5:
            buyer["mst"] = ""
        draw_party(pdf, "ĐƠN VỊ MUA HÀNG:", buyer)
        tong = draw_items_standard(pdf, items_std)
        draw_totals_standard(pdf, tong, vat_rate/100)
        footer_note(pdf)
        draw_signatures(pdf)
        pdf.output(str(OUTPUT_DIR / f"hoadon_input_{i:03d}.pdf"))
        print(f"✅ Synthetic input: hoadon_input_{i:03d}.pdf")

        # Tính VAT tháng 3
        if date.month == 3:
            subtotal = sum(it["sl"] * it["dg"] for it in items_std)
            input_vat_march += subtotal * (vat_rate / 100)

    # 8 hóa đơn đầu ra (Bình Minh bán)
    for i in range(1, 9):
        customer = random.choice(customers_base)
        date = datetime(2026, random.randint(1, 6), random.randint(1, 28))
        ngay_str = date.strftime("%d/%m/%Y")

        items = [
            {"ten": "Màng nhựa PE cuộn", "sl": random.randint(50, 100), "dvt": "Cuộn", "don_gia": 850000, "stt": 1},
            {"ten": "Túi nilon thực phẩm", "sl": random.randint(200, 500), "dvt": "kg", "don_gia": 35000, "stt": 2}
        ]
        items_std = [{"stt": it["stt"], "ten": it["ten"], "dvt": it["dvt"], "sl": it["sl"], "dg": it["don_gia"]} for it in items]

        pdf = make_pdf()
        pdf.add_page()
        so_hd = f"{i+100:07d}"
        ky_hieu = "BM/26P"
        draw_header(pdf, so_hd, ngay_str, "1/001", ky_hieu)
        draw_party(pdf, "ĐƠN VỊ BÁN HÀNG:", BINH_MINH)
        draw_party(pdf, "ĐƠN VỊ MUA HÀNG:", customer)
        tong = draw_items_standard(pdf, items_std)
        draw_totals_standard(pdf, tong, 0.10)
        footer_note(pdf)
        draw_signatures(pdf)
        pdf.output(str(OUTPUT_DIR / f"hoadon_output_{i:03d}.pdf"))
        print(f"✅ Synthetic output: hoadon_output_{i:03d}.pdf")

        if date.month == 3:
            subtotal = sum(it["sl"] * it["dg"] for it in items_std)
            output_vat_march += subtotal * 0.10

    # Báo cáo Q1
    # Sẽ tạo sau (dùng hàm riêng)
    # Báo cáo Q2 tạm (sẽ bị ghi đè bởi edge case)
    gen_financial_report_q1()
    gen_financial_report_q2_temp()
    gen_vat_declaration(input_vat_march, output_vat_march)

def gen_financial_report_q1():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("DejaVu", style="B", size=12)
    pdf.cell(0, 6, BINH_MINH['ten'], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", style="", size=10)
    pdf.cell(0, 5, f"Địa chỉ: {BINH_MINH['dia_chi']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("DejaVu", style="B", size=16)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 10, "BÁO CÁO TÀI CHÍNH QUÝ 1/2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    # Dữ liệu Q1
    data_2026 = {"revenue": 4850000000, "cost": 3120000000, "profit": 944000000}
    data_2025 = {"revenue": 3920000000, "cost": 2580000000, "profit": 705600000}
    _draw_financial_table(pdf, data_2026, data_2025, "1")
    pdf.output(str(OUTPUT_DIR / "bao_cao_tai_chinh_q1.pdf"))
    print("✅ Synthetic report: bao_cao_tai_chinh_q1.pdf")

def gen_financial_report_q2_temp():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("DejaVu", style="B", size=12)
    pdf.cell(0, 6, BINH_MINH['ten'], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", style="", size=10)
    pdf.cell(0, 5, f"Địa chỉ: {BINH_MINH['dia_chi']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("DejaVu", style="B", size=16)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 10, "BÁO CÁO TÀI CHÍNH QUÝ 2/2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    data_2026 = {"revenue": 5200000000, "cost": 3400000000, "profit": 1100000000}
    data_2025 = {"revenue": 4100000000, "cost": 2700000000, "profit": 850000000}
    _draw_financial_table(pdf, data_2026, data_2025, "2")
    pdf.output(str(OUTPUT_DIR / "bao_cao_tai_chinh_q2.pdf"))
    print("✅ Synthetic report (temporary): bao_cao_tai_chinh_q2.pdf")

def _draw_financial_table(pdf, data_curr, data_prev, quarter):
    col1, col2, col3 = 90, 45, 45
    pdf.set_font("DejaVu", style="B", size=10)
    pdf.set_text_color(*COLOR_TABLE_HEADER)
    pdf.cell(0, 8, "I. KẾT QUẢ KINH DOANH (VNĐ)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_fill_color(*COLOR_TABLE_HEADER)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(col1, 8, "Chỉ tiêu", border=1, fill=True)
    pdf.cell(col2, 8, f"Quý {quarter}/2026", border=1, align="C", fill=True)
    pdf.cell(col3, 8, f"Quý {quarter}/2025", border=1, align="C", fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    rows = [
        ("Doanh thu thuần", data_curr['revenue'], data_prev['revenue'], False),
        ("Giá vốn hàng bán", data_curr['cost'], data_prev['cost'], False),
        ("Lợi nhuận gộp", data_curr['revenue'] - data_curr['cost'], data_prev['revenue'] - data_prev['cost'], True),
        ("Lợi nhuận sau thuế", data_curr['profit'], data_prev['profit'], True),
    ]
    for i, (label, v26, v25, bold) in enumerate(rows):
        fill = i % 2 == 1
        pdf.set_fill_color(*COLOR_ROW_ALT)
        pdf.set_font("DejaVu", style="B" if bold else "", size=9)
        pdf.cell(col1, 7, f" {label}", border=1, fill=fill)
        pdf.cell(col2, 7, f"{v26:,.0f}", border=1, align="R", fill=fill)
        pdf.cell(col3, 7, f"{v25:,.0f}", border=1, align="R", fill=fill)
        pdf.ln()
    pdf.ln(5)

def gen_vat_declaration(input_vat, output_vat):
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("DejaVu", style="B", size=14)
    pdf.cell(0, 10, "TỜ KHAI THUẾ GTGT THÁNG 3/2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("DejaVu", style="", size=10)
    pdf.cell(0, 6, f"Người nộp thuế: {BINH_MINH['ten']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Mã số thuế: {BINH_MINH['mst']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    col1, col2 = 120, 60
    pdf.set_font("DejaVu", style="B", size=10)
    pdf.cell(col1, 8, "Chỉ tiêu", border=1, align="C")
    pdf.cell(col2, 8, "Giá trị (VNĐ)", border=1, align="C")
    pdf.ln()
    pdf.set_font("DejaVu", style="", size=10)
    rows = [
        ("Tổng thuế GTGT đầu vào được khấu trừ", input_vat),
        ("Tổng thuế GTGT đầu ra phát sinh", output_vat),
        ("Thuế GTGT còn phải nộp trong kỳ", max(0, output_vat - input_vat)),
        ("Thuế GTGT chưa khấu trừ hết chuyển kỳ sau", max(0, input_vat - output_vat))
    ]
    for label, val in rows:
        pdf.cell(col1, 8, f" {label}", border=1)
        pdf.cell(col2, 8, f"{val:,.0f}", border=1, align="R")
        pdf.ln()
    pdf.output(str(OUTPUT_DIR / "to_khai_thue_gtgt_thang3_2026.pdf"))
    print("✅ Synthetic declaration: to_khai_thue_gtgt_thang3_2026.pdf")

# ======================== PHẦN 2: THÊM 17 HÓA ĐƠN (MORE INVOICES) ========================
# Dữ liệu từ generate_more_invoices.py (đã được định nghĩa sẵn trong NHA_CUNG_CAP, KHACH_HANG)
# Các hóa đơn đầu vào (10 cái) và đầu ra (7 cái)

INVOICES_IN_MORE = [
    dict(so_hd="0000004", ngay="08 tháng 01 năm 2026", mau_so="01GTKT0/001", ky_hieu="DD/26E",
         ben_ban=NHA_CUNG_CAP[0], thue=0.10,
         items=[
             {"stt":1,"ten":"Hạt nhựa PP (Polypropylene) nguyên sinh","dvt":"Kg","sl":5000,"dg":28_000},
             {"stt":2,"ten":"Hạt nhựa HDPE tái chế","dvt":"Kg","sl":2000,"dg":22_000},
             {"stt":3,"ten":"Chất phụ gia ổn định nhiệt","dvt":"Kg","sl":200,"dg":85_000},
         ]),
    dict(so_hd="0000005", ngay="15 tháng 01 năm 2026", mau_so="01GTKT0/001", ky_hieu="EE/26E",
         ben_ban=NHA_CUNG_CAP[1], thue=0.08,
         items=[
             {"stt":1,"ten":"Thép tấm cán nguội (Cold Rolled) dày 2mm","dvt":"Tấn","sl":10,"dg":18_500_000},
             {"stt":2,"ten":"Thép hộp vuông 50x50x2mm","dvt":"Cây","sl":200,"dg":280_000},
             {"stt":3,"ten":"Bulong đai ốc M10 (hộp 100 cái)","dvt":"Hộp","sl":50,"dg":120_000},
         ]),
    dict(so_hd="0000006", ngay="03 tháng 02 năm 2026", mau_so="01GTKT0/001", ky_hieu="FF/26E",
         ben_ban=NHA_CUNG_CAP[2], thue=0.10,
         items=[
             {"stt":1,"ten":"Túi PE đóng gói sản phẩm (25x35cm)","dvt":"Cuộn","sl":500,"dg":180_000},
             {"stt":2,"ten":"Thùng carton 5 lớp (40x30x25cm)","dvt":"Cái","sl":2000,"dg":25_000},
             {"stt":3,"ten":"Băng keo đóng gói (48mm x 100m)","dvt":"Cuộn","sl":200,"dg":35_000},
             {"stt":4,"ten":"Nhãn dán sản phẩm (in màu 4 màu)","dvt":"Tờ","sl":10000,"dg":800},
         ]),
    dict(so_hd="0000007", ngay="18 tháng 02 năm 2026", mau_so="01GTKT0/001", ky_hieu="GG/26E",
         ben_ban=NHA_CUNG_CAP[3], thue=0.10,
         items=[
             {"stt":1,"ten":"Động cơ điện 3 pha 7.5kW (IE3)","dvt":"Cái","sl":2,"dg":12_500_000},
             {"stt":2,"ten":"Biến tần Siemens G120 7.5kW","dvt":"Cái","sl":2,"dg":18_000_000},
             {"stt":3,"ten":"Cáp điện 3x4mm2 (cuộn 100m)","dvt":"Cuộn","sl":5,"dg":2_800_000},
         ]),
    dict(so_hd="0000008", ngay="05 tháng 03 năm 2026", mau_so="01GTKT0/001", ky_hieu="HH/26E",
         ben_ban=NHA_CUNG_CAP[4], thue=0.10,
         items=[
             {"stt":1,"ten":"Dung môi MEK (Methyl Ethyl Ketone) thùng 180L","dvt":"Thùng","sl":10,"dg":8_500_000},
             {"stt":2,"ten":"Sơn chống rỉ epoxy 2 thành phần (20L)","dvt":"Thùng","sl":30,"dg":1_200_000},
             {"stt":3,"ten":"Chất tẩy rửa công nghiệp (can 25L)","dvt":"Can","sl":20,"dg":650_000},
         ]),
    dict(so_hd="0000009", ngay="20 tháng 03 năm 2026", mau_so="01GTKT0/001", ky_hieu="II/26E",
         ben_ban=NHA_CUNG_CAP[5], thue=0.10,
         items=[
             {"stt":1,"ten":"Vận chuyển hàng hóa TP.HCM - Bình Dương (xe 5 tấn)","dvt":"Chuyến","sl":15,"dg":2_200_000},
             {"stt":2,"ten":"Vận chuyển hàng hóa Đồng Nai - Bình Dương (xe 10 tấn)","dvt":"Chuyến","sl":8,"dg":3_500_000},
             {"stt":3,"ten":"Phí bốc xếp hàng hóa tại kho","dvt":"Tấn","sl":50,"dg":150_000},
         ]),
    dict(so_hd="0000010", ngay="07 tháng 04 năm 2026", mau_so="01GTKT0/001", ky_hieu="JJ/26E",
         ben_ban=NHA_CUNG_CAP[6], thue=0.10,
         items=[
             {"stt":1,"ten":"Máy nén khí trục vít 15kW (500L/phút)","dvt":"Cái","sl":1,"dg":85_000_000},
             {"stt":2,"ten":"Bộ lọc khí nén tổ hợp (0.01 micron)","dvt":"Bộ","sl":2,"dg":4_500_000},
             {"stt":3,"ten":"Ống dẫn khí nén DN25 (cuộn 50m)","dvt":"Cuộn","sl":10,"dg":1_200_000},
             {"stt":4,"ten":"Van điện từ khí nén 1/2 inch","dvt":"Cái","sl":20,"dg":850_000},
         ]),
    dict(so_hd="0000011", ngay="22 tháng 04 năm 2026", mau_so="01GTKT0/001", ky_hieu="KK/26E",
         ben_ban=NHA_CUNG_CAP[7], thue=0.10,
         items=[
             {"stt":1,"ten":"Giấy in A4 80gsm (thùng 5 ram)","dvt":"Thùng","sl":20,"dg":320_000},
             {"stt":2,"ten":"Giấy kraft cuộn 70cm (cuộn 100m)","dvt":"Cuộn","sl":50,"dg":180_000},
             {"stt":3,"ten":"Giấy decal trắng A4 (hộp 100 tờ)","dvt":"Hộp","sl":30,"dg":250_000},
         ]),
    dict(so_hd="0000012", ngay="06 tháng 05 năm 2026", mau_so="01GTKT0/001", ky_hieu="LL/26E",
         ben_ban=NHA_CUNG_CAP[8], thue=0.10,
         items=[
             {"stt":1,"ten":"Dầu thủy lực Castrol Hyspin AWS 46 (thùng 209L)","dvt":"Thùng","sl":3,"dg":9_800_000},
             {"stt":2,"ten":"Mỡ bôi trơn Castrol Molub-Alloy (hộp 18kg)","dvt":"Hộp","sl":5,"dg":2_200_000},
             {"stt":3,"ten":"Dầu cắt gọt gia công kim loại (can 20L)","dvt":"Can","sl":10,"dg":1_500_000},
         ]),
    dict(so_hd="0000013", ngay="20 tháng 05 năm 2026", mau_so="01GTKT0/001", ky_hieu="MM/26E",
         ben_ban=NHA_CUNG_CAP[9], thue=0.10,
         items=[
             {"stt":1,"ten":"Vòng bi SKF 6205 2RS (hộp 10 cái)","dvt":"Hộp","sl":20,"dg":850_000},
             {"stt":2,"ten":"Dây curoa Optibelt Z31 (bộ 5 cái)","dvt":"Bộ","sl":10,"dg":680_000},
             {"stt":3,"ten":"Khớp nối trục đàn hồi size 6","dvt":"Cái","sl":8,"dg":1_200_000},
             {"stt":4,"ten":"Xy lanh khí nén Ø50 stroke 200mm","dvt":"Cái","sl":6,"dg":2_800_000},
         ]),
]

INVOICES_OUT_MORE = [
    dict(so_hd="0000014", ngay="25 tháng 01 năm 2026", mau_so="01GTKT0/001", ky_hieu="NN/26E",
         ben_mua=KHACH_HANG[0], thue=0.10,
         items=[
             {"stt":1,"ten":"Vỏ nhựa TV 55 inch (màu đen mờ)","dvt":"Cái","sl":5000,"dg":85_000},
             {"stt":2,"ten":"Khung nhựa điều khiển từ xa","dvt":"Cái","sl":10000,"dg":12_000},
             {"stt":3,"ten":"Nắp pin nhựa (bộ 2 cái)","dvt":"Bộ","sl":10000,"dg":8_000},
         ]),
    dict(so_hd="0000015", ngay="10 tháng 02 năm 2026", mau_so="01GTKT0/001", ky_hieu="OO/26E",
         ben_mua=KHACH_HANG[1], thue=0.10,
         items=[
             {"stt":1,"ten":"Khung nhựa máy giặt cửa trước","dvt":"Cái","sl":3000,"dg":125_000},
             {"stt":2,"ten":"Nắp bộ lọc máy giặt","dvt":"Cái","sl":3000,"dg":45_000},
             {"stt":3,"ten":"Vỏ nhựa điều hòa không khí 1.5HP","dvt":"Bộ","sl":2000,"dg":180_000},
         ]),
    dict(so_hd="0000016", ngay="25 tháng 02 năm 2026", mau_so="01GTKT0/001", ky_hieu="PP/26E",
         ben_mua=KHACH_HANG[2], thue=0.08,
         items=[
             {"stt":1,"ten":"Ống nhựa PVC Ø90 dài 6m (PN10)","dvt":"Cây","sl":1000,"dg":185_000},
             {"stt":2,"ten":"Ống nhựa HDPE Ø110 dài 6m (PN10)","dvt":"Cây","sl":500,"dg":320_000},
             {"stt":3,"ten":"Co nối PVC 90 độ Ø90","dvt":"Cái","sl":500,"dg":35_000},
         ]),
    dict(so_hd="0000017", ngay="15 tháng 03 năm 2026", mau_so="01GTKT0/001", ky_hieu="QQ/26E",
         ben_mua=KHACH_HANG[3], thue=0.10,
         items=[
             {"stt":1,"ten":"Vỏ nhựa máy ảnh Lumix series (bộ 3 chi tiết)","dvt":"Bộ","sl":2000,"dg":220_000},
             {"stt":2,"ten":"Khung nhựa bếp từ Panasonic","dvt":"Cái","sl":3000,"dg":95_000},
             {"stt":3,"ten":"Nắp nhựa nồi cơm điện 1.8L","dvt":"Cái","sl":5000,"dg":42_000},
         ]),
    dict(so_hd="0000018", ngay="10 tháng 04 năm 2026", mau_so="01GTKT0/001", ky_hieu="RR/26E",
         ben_mua=KHACH_HANG[4], thue=0.10,
         items=[
             {"stt":1,"ten":"Tấm ốp nhựa ABS (600x400x3mm)","dvt":"Tấm","sl":500,"dg":185_000},
             {"stt":2,"ten":"Chi tiết nhựa kỹ thuật PA66 (phức tạp)","dvt":"Cái","sl":1000,"dg":320_000},
             {"stt":3,"ten":"Bánh răng nhựa POM module 2 (Z=40)","dvt":"Cái","sl":500,"dg":280_000},
         ]),
    dict(so_hd="0000019", ngay="22 tháng 04 năm 2026", mau_so="01GTKT0/001", ky_hieu="SS/26E",
         ben_mua=KHACH_HANG[5], thue=0.10,
         items=[
             {"stt":1,"ten":"Khung nhựa máy photocopy A3","dvt":"Cái","sl":1000,"dg":450_000},
             {"stt":2,"ten":"Nắp nhựa khay giấy máy in","dvt":"Cái","sl":2000,"dg":85_000},
             {"stt":3,"ten":"Bánh xe dẫn giấy nhựa (bộ 4 cái)","dvt":"Bộ","sl":2000,"dg":120_000},
         ]),
    dict(so_hd="0000020", ngay="15 tháng 05 năm 2026", mau_so="01GTKT0/001", ky_hieu="TT/26E",
         ben_mua=KHACH_HANG[6], thue=0.10,
         items=[
             {"stt":1,"ten":"Ống cuộn chỉ nhựa (Ø76mm x 200mm)","dvt":"Cái","sl":10000,"dg":18_000},
             {"stt":2,"ten":"Cone cuộn sợi nhựa (Ø60mm, cao 180mm)","dvt":"Cái","sl":20000,"dg":12_000},
             {"stt":3,"ten":"Lõi nhựa cuộn vải (Ø150mm x 1500mm)","dvt":"Cái","sl":500,"dg":185_000},
             {"stt":4,"ten":"Hộp nhựa đựng phụ kiện may (30x20x10cm)","dvt":"Cái","sl":2000,"dg":55_000},
         ]),
]

def gen_more_invoices_batch():
    """Tạo các hóa đơn 004-020"""
    # Đầu vào (10 cái)
    for i, inv in enumerate(INVOICES_IN_MORE):
        pdf = make_pdf()
        pdf.add_page()
        draw_header(pdf, inv["so_hd"], inv["ngay"], inv["mau_so"], inv["ky_hieu"])
        draw_party(pdf, "ĐƠN VỊ BÁN HÀNG:", inv["ben_ban"])
        draw_party(pdf, "ĐƠN VỊ MUA HÀNG:", BINH_MINH)
        tong = draw_items_standard(pdf, inv["items"])
        draw_totals_standard(pdf, tong, inv["thue"])
        footer_note(pdf)
        draw_signatures(pdf)
        fname = f"hoadon_{int(inv['so_hd']):03d}.pdf"
        pdf.output(str(OUTPUT_DIR / fname))
        print(f"✅ More input: {fname}")

    # Đầu ra (7 cái)
    for i, inv in enumerate(INVOICES_OUT_MORE):
        pdf = make_pdf()
        pdf.add_page()
        draw_header(pdf, inv["so_hd"], inv["ngay"], inv["mau_so"], inv["ky_hieu"])
        draw_party(pdf, "ĐƠN VỊ BÁN HÀNG:", BINH_MINH)
        draw_party(pdf, "ĐƠN VỊ MUA HÀNG:", inv["ben_mua"])
        tong = draw_items_standard(pdf, inv["items"])
        draw_totals_standard(pdf, tong, inv["thue"])
        footer_note(pdf)
        draw_signatures(pdf)
        fname = f"hoadon_{int(inv['so_hd']):03d}.pdf"
        pdf.output(str(OUTPUT_DIR / fname))
        print(f"✅ More output: {fname}")

# ======================== PHẦN 3: EDGE CASES ========================
def gen_edge_cases_batch():
    """Tạo hóa đơn 021,022,023,024 và báo cáo Q2 có lỗ (ghi đè)"""
    # EC-1: Hóa đơn gốc sai đơn giá
    pdf = make_pdf()
    pdf.add_page()
    draw_header(pdf, "0000021", "07 tháng 04 năm 2026", "01GTKT0/001", "UU/26E")
    draw_party(pdf, "ĐƠN VỊ BÁN HÀNG:", NCC_THIET_BI)
    draw_party(pdf, "ĐƠN VỊ MUA HÀNG:", BINH_MINH)
    items = [
        {"stt":1,"ten":"Máy nén khí trục vít 15kW (500L/phút)","dvt":"Cái","sl":1,"dg":75_000_000},
        {"stt":2,"ten":"Bộ lọc khí nén tổ hợp (0.01 micron)","dvt":"Bộ","sl":2,"dg":4_500_000},
        {"stt":3,"ten":"Ống dẫn khí nén DN25 (cuộn 50m)","dvt":"Cuộn","sl":10,"dg":1_200_000},
    ]
    tong = draw_items_standard(pdf, items)
    draw_totals_standard(pdf, tong, 0.10)
    footer_note(pdf, ghi_chu="*** HOÁ ĐƠN NÀY ĐÃ BỊ ĐIỀU CHỈNH - Xem HĐ số 0000022 ***")
    pdf.set_font("DejaVu", style="B", size=8)
    pdf.set_text_color(*COLOR_WARNING)
    pdf.cell(0, 6, "LƯU Ý: Hoá đơn này đã được điều chỉnh do sai đơn giá mặt hàng STT 1.",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0,0,0)
    draw_signatures(pdf)
    pdf.output(str(OUTPUT_DIR / "hoadon_021.pdf"))
    print("✅ Edge case: hoadon_021.pdf")

    # EC-2: Hóa đơn điều chỉnh
    pdf = make_pdf()
    pdf.add_page()
    draw_header(pdf, "0000022", "10 tháng 04 năm 2026", "01GTKT0/001", "VV/26E", dieu_chinh_cho="0000021")
    draw_party(pdf, "ĐƠN VỊ BÁN HÀNG:", NCC_THIET_BI)
    draw_party(pdf, "ĐƠN VỊ MUA HÀNG:", BINH_MINH)
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_text_color(*COLOR_WARNING)
    pdf.cell(0, 6, "LÝ DO ĐIỀU CHỈNH:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 5,
        "Hoá đơn số 0000021 ngày 07/04/2026 ghi sai đơn giá mặt hàng STT 1 "
        "(Máy nén khí trục vít 15kW): ghi 75,000,000 VND thay vì 85,000,000 VND dùng. "
        "Hoá đơn điều chỉnh này ghi nhận phần chênh lệch tăng thêm 10,000,000 VND.",
        new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    w = pdf.w - pdf.l_margin - pdf.r_margin
    cols = {"stt":9, "ten":w*0.42, "dvt":16, "sl":18, "dg_cu":30, "dg_moi":30, "cl":25}
    headers = ["STT", "Tên hàng hoá/dịch vụ", "DVT", "SL", "Đơn giá cũ", "Đơn giá mới", "Chênh lệch"]
    rh = 7
    pdf.set_fill_color(*COLOR_TABLE_HEADER)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", style="B", size=7.5)
    for h, k in zip(headers, cols):
        pdf.cell(cols[k], rh, h, border=1, align="C", fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("DejaVu", style="", size=7.5)
    pdf.set_fill_color(*COLOR_ROW_ALT)
    pdf.cell(cols["stt"],   rh, "1",                                     border=1, align="C", fill=True)
    pdf.cell(cols["ten"],   rh, "Máy nén khí trục vít 15kW (500L/phút)", border=1, fill=True)
    pdf.cell(cols["dvt"],   rh, "Cái",                                   border=1, align="C", fill=True)
    pdf.cell(cols["sl"],    rh, "1",                                      border=1, align="R", fill=True)
    pdf.cell(cols["dg_cu"], rh, "75,000,000",                            border=1, align="R", fill=True)
    pdf.cell(cols["dg_moi"],rh, "85,000,000",                            border=1, align="R", fill=True)
    pdf.set_text_color(*COLOR_WARNING)
    pdf.cell(cols["cl"],    rh, "+10,000,000",                           border=1, align="R", fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)
    w2 = pdf.w - pdf.l_margin - pdf.r_margin
    lw, vw = w2 * 0.65, w2 * 0.35
    rh2 = 7
    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(lw, rh2, "Tiền hàng điều chỉnh tăng thêm:", border=1, align="R", fill=True)
    pdf.cell(vw, rh2, "10,000,000 VND",                 border=1, align="R", fill=True)
    pdf.ln()
    pdf.cell(lw, rh2, "Thu GTGT 10% điều chỉnh tăng thêm:", border=1, align="R", fill=True)
    pdf.cell(vw, rh2, "1,000,000 VND",                       border=1, align="R", fill=True)
    pdf.ln()
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_fill_color(*COLOR_WARNING)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(lw, rh2+1, "TỔNG SỐ TIỀN ĐIỀU CHỈNH TĂNG THÊM:", border=1, align="R", fill=True)
    pdf.cell(vw, rh2+1, "11,000,000 VND",                     border=1, align="R", fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("DejaVu", style="", size=8)
    pdf.ln(3)
    footer_note(pdf, ghi_chu="Điều chỉnh tăng. Bên mua thanh toán thêm phần chênh lệch này.")
    draw_signatures(pdf)
    pdf.output(str(OUTPUT_DIR / "hoadon_022.pdf"))
    print("✅ Edge case: hoadon_022.pdf")

    # EC-3: Hóa đơn đa thuế suất
    pdf = make_pdf()
    pdf.add_page()
    draw_header(pdf, "0000023", "15 tháng 05 năm 2026", "01GTKT0/001", "WW/26E")
    draw_party(pdf, "ĐƠN VỊ BÁN HÀNG:", BINH_MINH)
    draw_party(pdf, "ĐƠN VỊ MUA HÀNG:", SAMSUNG)
    pdf.set_font("DejaVu", style="B", size=8)
    pdf.set_text_color(*COLOR_TABLE_HEADER)
    pdf.cell(0, 5, "Lưu ý: Hóa đơn này có nhiều mức thuế suất GTGT khác nhau (8% và 10%).",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # items đa thuế
    items_multi = [
        {"stt":1,"ten":"Vỏ nhựa TV 55 inch (màu đen mờ)","dvt":"Cái","sl":3000,"dg":85_000,"thue":0.10},
        {"stt":2,"ten":"Khung nhựa điều khiển từ xa","dvt":"Cái","sl":6000,"dg":12_000,"thue":0.10},
        {"stt":3,"ten":"Nắp pin nhựa (bộ 2 cái)","dvt":"Bộ", "sl":6000,"dg":8_000,"thue":0.10},
        {"stt":4,"ten":"Bo mạch nhựa bảo vệ PCB (giảm thuế 8%)","dvt":"Cái","sl":3000,"dg":45_000,"thue":0.08},
        {"stt":5,"ten":"Linh kiện nhựa tản nhiệt CPU","dvt":"Cái","sl":3000,"dg":62_000,"thue":0.08},
    ]
    # Vẽ bảng đa thuế
    w = pdf.w - pdf.l_margin - pdf.r_margin
    cols_multi = {"stt":9, "ten":w*0.30, "dvt":14, "sl":18, "dg":28, "ts":18, "tt":28}
    headers_multi = ["STT", "Tên hàng hóa/dịch vụ", "DVT", "Số lượng", "Đơn giá", "Thuế suất", "Thành tiền"]
    rh = 7
    pdf.set_fill_color(*COLOR_TABLE_HEADER)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", style="B", size=7.5)
    for h, k in zip(headers_multi, cols_multi):
        pdf.cell(cols_multi[k], rh, h, border=1, align="C", fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    tong_8 = tong_10 = 0
    for i, item in enumerate(items_multi):
        tt = item["sl"] * item["dg"]
        if item["thue"] == 0.08:
            tong_8 += tt
        else:
            tong_10 += tt
        fill = i % 2 == 1
        pdf.set_fill_color(*COLOR_ROW_ALT)
        pdf.set_font("DejaVu", style="", size=7.5)
        pdf.cell(cols_multi["stt"], rh, str(item["stt"]), border=1, align="C", fill=fill)
        pdf.cell(cols_multi["ten"], rh, item["ten"],       border=1, fill=fill)
        pdf.cell(cols_multi["dvt"], rh, item["dvt"],       border=1, align="C", fill=fill)
        pdf.cell(cols_multi["sl"],  rh, f'{item["sl"]:,}', border=1, align="R", fill=fill)
        pdf.cell(cols_multi["dg"],  rh, f'{item["dg"]:,.0f}', border=1, align="R", fill=fill)
        pdf.cell(cols_multi["ts"],  rh, f'{int(item["thue"]*100)}%', border=1, align="C", fill=fill)
        pdf.cell(cols_multi["tt"],  rh, f'{tt:,.0f}', border=1, align="R", fill=fill)
        pdf.ln()
    # Tổng đa thuế
    lw, vw = w * 0.65, w * 0.35
    thue_8  = int(tong_8  * 0.08)
    thue_10 = int(tong_10 * 0.10)
    thanh_toan = int(tong_8) + int(tong_10) + thue_8 + thue_10
    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_fill_color(245, 245, 245)
    rows_total = [
        ("Cộng tiền hàng (thuế suất 8%):", f"{int(tong_8):,} VND"),
        ("Thuế GTGT 8%:", f"{thue_8:,} VND"),
        ("Cộng tiền hàng (thuế suất 10%):", f"{int(tong_10):,} VND"),
        ("Thuế GTGT 10%:", f"{thue_10:,} VND"),
        ("Tổng thuế GTGT:", f"{thue_8+thue_10:,} VND"),
    ]
    for lbl, val in rows_total:
        pdf.cell(lw, rh, lbl, border=1, align="R", fill=True)
        pdf.cell(vw, rh, val, border=1, align="R", fill=True)
        pdf.ln()
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_fill_color(*COLOR_HEADER)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(lw, rh+1, "TỔNG CỘNG TIỀN THANH TOÁN:", border=1, align="R", fill=True)
    pdf.cell(vw, rh+1, f"{thanh_toan:,} VND", border=1, align="R", fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("DejaVu", style="", size=8)
    pdf.ln(2)
    footer_note(pdf, ghi_chu="Mặt hàng STT 4-5 áp dụng thuế suất 8% theo Nghị định giảm thuế GTGT năm 2026.")
    draw_signatures(pdf)
    pdf.output(str(OUTPUT_DIR / "hoadon_023.pdf"))
    print("✅ Edge case: hoadon_023.pdf")

    # EC-4: Hóa đơn ngoại tệ USD
    TY_GIA = 25_450
    pdf = make_pdf()
    pdf.add_page()
    draw_header(pdf, "0000024", "20 tháng 05 năm 2026", "01GTKT0/001", "XX/26E")
    draw_party(pdf, "ĐƠN VỊ BÁN HÀNG:", NCC_SINGAPORE)
    draw_party(pdf, "ĐƠN VỊ MUA HÀNG:", BINH_MINH)
    pdf.set_font("DejaVu", style="B", size=8)
    pdf.set_text_color(*COLOR_TABLE_HEADER)
    pdf.cell(0, 5, f"Tỷ giá quy đổi: 1 USD = {TY_GIA:,} VND (Theo tỷ giá NHTW ngày 20/05/2026)",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    w = pdf.w - pdf.l_margin - pdf.r_margin
    cols_usd = {"stt":9, "ten":w*0.34, "dvt":14, "sl":16, "dg_usd":26, "tt_usd":24, "tt_vnd":28}
    headers_usd = ["STT", "Tên hàng hóa", "DVT", "SL", "Đơn giá (USD)", "Thành tiền (USD)", "Thành tiền (VND)"]
    rh = 7
    pdf.set_fill_color(*COLOR_TABLE_HEADER)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", style="B", size=7.5)
    for h, k in zip(headers_usd, cols_usd):
        pdf.cell(cols_usd[k], rh, h, border=1, align="C", fill=True)
    pdf.ln()
    items_usd = [
        {"stt":1,"ten":"Precision Mold Steel NAK80 Block 300x200x100mm","dvt":"Block","sl":5, "dg_usd":1_200},
        {"stt":2,"ten":"Hot Runner System 8-cavity Complete Set",        "dvt":"Set",  "sl":2, "dg_usd":3_800},
        {"stt":3,"ten":"Mold Temperature Controller 9kW",               "dvt":"Unit", "sl":2, "dg_usd":950},
        {"stt":4,"ten":"Technical consulting & installation (on-site)",  "dvt":"Day",  "sl":3, "dg_usd":600},
    ]
    tong_usd = 0
    pdf.set_text_color(0, 0, 0)
    for i, item in enumerate(items_usd):
        tt_usd = item["sl"] * item["dg_usd"]
        tong_usd += tt_usd
        fill = i % 2 == 1
        pdf.set_fill_color(*COLOR_ROW_ALT)
        pdf.set_font("DejaVu", style="", size=7.5)
        pdf.cell(cols_usd["stt"],    rh, str(item["stt"]),          border=1, align="C", fill=fill)
        pdf.cell(cols_usd["ten"],    rh, item["ten"],                border=1, fill=fill)
        pdf.cell(cols_usd["dvt"],    rh, item["dvt"],                border=1, align="C", fill=fill)
        pdf.cell(cols_usd["sl"],     rh, str(item["sl"]),            border=1, align="R", fill=fill)
        pdf.cell(cols_usd["dg_usd"], rh, f'${item["dg_usd"]:,}',    border=1, align="R", fill=fill)
        pdf.cell(cols_usd["tt_usd"], rh, f'${tt_usd:,}',            border=1, align="R", fill=fill)
        pdf.cell(cols_usd["tt_vnd"], rh, f'{tt_usd*TY_GIA:,.0f}',   border=1, align="R", fill=fill)
        pdf.ln()
    tong_vnd    = int(tong_usd * TY_GIA)
    thue_vnd    = int(tong_vnd * 0.10)
    thanh_toan  = tong_vnd + thue_vnd
    pdf.ln(2)
    lw2 = w * 0.60
    vw2 = w * 0.40
    rh2 = 7
    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_fill_color(245, 245, 245)
    for lbl, val in [
        ("Tổng tiền hàng (USD):",    f"${tong_usd:,} USD"),
        (f"Quy đổi VND (x {TY_GIA:,}):", f"{tong_vnd:,} VND"),
        ("Thuế GTGT 10%:",           f"{thue_vnd:,} VND"),
    ]:
        pdf.cell(lw2, rh2, lbl, border=1, align="R", fill=True)
        pdf.cell(vw2, rh2, val, border=1, align="R", fill=True)
        pdf.ln()
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_fill_color(*COLOR_HEADER)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(lw2, rh2+1, "TỔNG TIỀN THANH TOÁN (VND):", border=1, align="R", fill=True)
    pdf.cell(vw2, rh2+1, f"{thanh_toan:,} VND",         border=1, align="R", fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("DejaVu", style="", size=8)
    pdf.ln(2)
    footer_note(pdf, ht="Chuyển khoản ngoại tệ (USD) hoặc VND quy đổi",
                han="45 ngày kể từ ngày xuất hóa đơn",
                ghi_chu=f"Tỷ giá thanh toán áp dụng tỷ giá NHTW ngày chuyển tiền thực tế.")
    draw_signatures(pdf)
    pdf.output(str(OUTPUT_DIR / "hoadon_024.pdf"))
    print("✅ Edge case: hoadon_024.pdf")

    # Báo cáo tài chính Q2 có lỗ (ghi đè file Q2 đã tạo ở synthetic)
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("DejaVu", style="B", size=13)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 8, "BÁO CÁO TÀI CHÍNH QUÝ II/2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", style="", size=10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, "Công ty CP Sản Xuất Bình Minh - MST: 0312345678", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Kỳ báo cáo: 01/04/2026 - 30/06/2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)

    # Dữ liệu lỗ
    def draw_table(title, rows):
        w = pdf.w - pdf.l_margin - pdf.r_margin
        c1, c2, c3 = w*0.55, w*0.225, w*0.225
        pdf.set_font("DejaVu", style="B", size=10)
        pdf.set_text_color(*COLOR_TABLE_HEADER)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", style="B", size=8)
        pdf.set_fill_color(*COLOR_TABLE_HEADER)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(c1, 7, "Chi tieu",  border=1, fill=True)
        pdf.cell(c2, 7, "Q2/2026",   border=1, align="R", fill=True)
        pdf.cell(c3, 7, "Q2/2025",   border=1, align="R", fill=True)
        pdf.ln()
        for i, (lbl, v26, v25, bold) in enumerate(rows):
            fill = i % 2 == 1
            pdf.set_fill_color(*COLOR_ROW_ALT)
            if isinstance(v26, (int,float)) and v26 < 0:
                pdf.set_text_color(*COLOR_NEGATIVE)
            else:
                pdf.set_text_color(0, 0, 0)
            pdf.set_font("DejaVu", style="B" if bold else "", size=8)
            if bold:
                pdf.set_fill_color(*COLOR_HEADER)
                pdf.set_text_color(255, 255, 255)
            pdf.cell(c1, 6.5, f"  {lbl}", border=1, fill=True)
            val26 = f"{v26:,.0f}" if isinstance(v26,(int,float)) else v26
            val25 = f"{v25:,.0f}" if isinstance(v25,(int,float)) else v25
            pdf.cell(c2, 6.5, val26, border=1, align="R", fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(c3, 6.5, val25, border=1, align="R", fill=True)
            pdf.ln()
        pdf.ln(4)

    draw_table("I. KẾT QUẢ HOẠT ĐỘNG KINH DOANH (Đơn vị: VND)", [
        ("Doanh thu thuần",                    3_120_000_000,  4_850_000_000, False),
        ("Giá vốn hàng bán",                   3_580_000_000,  3_120_000_000, False),
        ("Lợi nhuận gộp",                       -460_000_000,  1_730_000_000, True),
        ("Chi phí bán hàng",                     198_000_000,    245_000_000, False),
        ("Chi phí quản lý doanh nghiệp",         285_000_000,    312_000_000, False),
        ("Lợi nhuận từ HĐKD",                   -943_000_000,  1_173_000_000, True),
        ("Thu nhập khác",                          8_500_000,     15_000_000, False),
        ("Chi phí khác",                          12_000_000,      8_000_000, False),
        ("LỢI NHUẬN TRƯỚC THUẾ",                -946_500_000,  1_180_000_000, True),
        ("Thuế TNDN (20%)",                              0,      236_000_000, False),
        ("LỢI NHUẬN SAU THUẾ (LỖ)",             -946_500_000,    944_000_000, True),
    ])

    draw_table("II. TÌNH HÌNH CÔNG NỢ (Đơn vị: VND)", [
        ("Phải thu khách hàng",                1_820_000_000,  1_250_000_000, False),
        ("Trong đó: Quá hạn >30 ngày",           420_000_000,    180_000_000, False),
        ("Phải trả nhà cung cấp",                960_000_000,    870_000_000, False),
        ("Tổng dư nợ vay ngân hàng",           2_800_000_000,  2_500_000_000, True),
        ("Hệ số thanh toán hiện hành",              "1.42",        "1.85",    False),
        ("Hệ số thanh toán nhanh",                  "0.91",        "1.24",    False),
    ])

    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_text_color(*COLOR_TABLE_HEADER)
    pdf.cell(0, 6, "III. PHÂN TÍCH VÀ NHẬN XÉT", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_text_color(0, 0, 0)
    notes = [
        "1. Q2/2026 ghi nhận THUA LỖ 946,500,000 VND - giảm mạnh so với lợi nhuận 944tr của Q2/2025.",
        "2. Doanh thu giảm 35.7% do mất 2 khách hàng lớn (LG Electronics và Panasonic tạm ngừng đơn hàng).",
        "3. Giá vốn tăng do chi phí nguyên liệu nhựa PP tăng 28% và giá thép tăng 15% trong quý.",
        "4. Hệ số thanh toán nhanh giảm xuống 0.91 (<1.0) - cảnh báo rủi ro thanh khoản ngắn hạn.",
        "5. Nợ phải thu quá hạn tăng lên 420tr (23% tổng phải thu) - cần đẩy mạnh thu hồi công nợ.",
        "6. Ban lãnh đạo đã triển khai kế hoạch tái cơ cấu: cắt giảm chi phí, tìm kiếm khách hàng mới.",
        "7. Báo cáo được lập theo Chuẩn mực Kế toán Việt Nam (VAS) và Thông tư 200/2014/TT-BTC.",
    ]
    for note in notes:
        pdf.multi_cell(0, 5.5, note, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)
    w = pdf.w - pdf.l_margin - pdf.r_margin
    col = w / 3
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.cell(col, 6, "NGƯỜI LẬP BẢNG", align="C")
    pdf.cell(col, 6, "KẾ TOÁN TRƯỞNG", align="C")
    pdf.cell(col, 6, "GIÁM ĐỐC", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(col, 5, "(Ký, ghi rõ họ tên)", align="C")
    pdf.cell(col, 5, "(Ký, ghi rõ họ tên)", align="C")
    pdf.cell(col, 5, "(Ký, ghi rõ họ tên)", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(OUTPUT_DIR / "bao_cao_tai_chinh_q2.pdf"))
    print("✅ Edge case: bao_cao_tai_chinh_q2.pdf (ghi đè lên báo cáo Q2 cũ)")

# ======================== MAIN ========================
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("🚀 Bắt đầu tạo toàn bộ dữ liệu (synthetic + more invoices + edge cases)...\n")
    gen_synthetic_batch()
    print("\n--- Đã xong synthetic, tiếp tục with more invoices ---\n")
    gen_more_invoices_batch()
    print("\n--- Đã xong more invoices, tiếp tục edge cases ---\n")
    gen_edge_cases_batch()
    print(f"\n✅ Hoàn thành! Tổng số file PDF trong {OUTPUT_DIR}: {len(list(OUTPUT_DIR.glob('*.pdf')))}")

if __name__ == "__main__":
    main()