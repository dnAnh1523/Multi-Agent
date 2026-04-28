"""
generate_edge_cases.py
Tạo các hóa đơn edge case và báo cáo tài chính Q2/2026.

Output: data/sample_invoices/
  hoadon_021.pdf  - Hóa đơn gốc (sai đơn giá, cần điều chỉnh)
  hoadon_022.pdf  - Hóa đơn ĐIỀU CHỈNH cho HĐ 021
  hoadon_023.pdf  - Hóa đơn đa thuế suất (8% và 10% trong cùng 1 HĐ)
  hoadon_024.pdf  - Hóa đơn ngoại tệ USD với quy đổi tỷ giá
  bao_cao_tai_chinh_q2.pdf - Báo cáo Q2/2026 (có lỗ)

Chạy: python generate_edge_cases.py
"""

import sys
from pathlib import Path
from fpdf import FPDF

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
    print("   Copy font vào fonts/dejavu_sans/DejaVu_Sans/")
    sys.exit(1)

print(f"✅ Font: {FONT_PATH}")

# Màu sắc
COLOR_HEADER       = (41, 128, 185)
COLOR_TABLE_HEADER = (52, 73, 94)
COLOR_ROW_ALT      = (236, 240, 241)
COLOR_BORDER       = (189, 195, 199)
COLOR_WARNING      = (192, 57, 43)
COLOR_NEGATIVE     = (231, 76, 60)

# Công ty Bình Minh
BINH_MINH = {
    "ten": "Công ty CP Sản Xuất Bình Minh",
    "mst": "0312345678",
    "dia_chi": "Lô B5, KCN Bình Dương, Tỉnh Bình Dương",
    "tk": "10203045678901 - Ngân hàng Vietcombank CN Bình Dương",
}

NCC_THIET_BI = {
    "ten": "Công ty TNHH Thiết Bị Công Nghiệp Phương Đông",
    "mst": "0507890123",
    "dia_chi": "Lô C3, KCN Nhơn Trạch, Đồng Nai",
    "tk": "00201345678901 - BIDV CN Đồng Nai",
}

SAMSUNG = {
    "ten": "Công ty CP Điện Tử Samsung Vina",
    "mst": "0311234567",
    "dia_chi": "KCN Yên Phong, Tỉnh Bắc Ninh",
    "tk": "10501234567890 - MB Bank CN Bắc Ninh",
}

NCC_SINGAPORE = {
    "ten": "ABC Industrial Supplies Co., Ltd",
    "mst": "S12345678A",
    "dia_chi": "10 Tuas Avenue 1, Singapore 639514",
    "tk": "SGD Account: 123-456-789 - DBS Bank Singapore",
}


# ============================================================
# HELPERS
# ============================================================

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
        pdf.cell(0, 6,
                 f"*** ĐIỀU CHỈNH CHO HOÁ ĐƠN SỐ {dieu_chinh_cho} ***",
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
    """Bảng hàng hóa thông thường — 1 mức thuế suất."""
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
        pdf.cell(cols["tt"],  rh, f'{tt:,.0f}', border=1, align="R", fill=fill)
        pdf.ln()
    return tong


def draw_items_multi_tax(pdf, items):
    """Bảng hàng hóa đa thuế suất — thêm cột Thuế suất."""
    w = pdf.w - pdf.l_margin - pdf.r_margin
    cols = {"stt": 9, "ten": w*0.30, "dvt": 14, "sl": 18, "dg": 28, "ts": 18, "tt": 28}
    headers = ["STT", "Tên hàng hóa/dịch vụ", "DVT", "Số lượng", "Đơn giá", "Thuế suất", "Thành tiền"]
    rh = 7
    pdf.set_fill_color(*COLOR_TABLE_HEADER)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", style="B", size=7.5)
    for h, k in zip(headers, cols):
        pdf.cell(cols[k], rh, h, border=1, align="C", fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    tong_8  = 0
    tong_10 = 0
    for i, item in enumerate(items):
        tt = item["sl"] * item["dg"]
        if item["thue"] == 0.08:
            tong_8 += tt
        else:
            tong_10 += tt
        fill = i % 2 == 1
        pdf.set_fill_color(*COLOR_ROW_ALT)
        pdf.set_font("DejaVu", style="", size=7.5)
        pdf.cell(cols["stt"], rh, str(item["stt"]), border=1, align="C", fill=fill)
        pdf.cell(cols["ten"], rh, item["ten"],       border=1, fill=fill)
        pdf.cell(cols["dvt"], rh, item["dvt"],       border=1, align="C", fill=fill)
        pdf.cell(cols["sl"],  rh, f'{item["sl"]:,}', border=1, align="R", fill=fill)
        pdf.cell(cols["dg"],  rh, f'{item["dg"]:,.0f}', border=1, align="R", fill=fill)
        pdf.cell(cols["ts"],  rh, f'{int(item["thue"]*100)}%', border=1, align="C", fill=fill)
        pdf.cell(cols["tt"],  rh, f'{tt:,.0f}', border=1, align="R", fill=fill)
        pdf.ln()
    return tong_8, tong_10


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


def draw_totals_multi_tax(pdf, tong_8, tong_10):
    w = pdf.w - pdf.l_margin - pdf.r_margin
    lw, vw = w * 0.65, w * 0.35
    rh = 7
    thue_8  = int(tong_8  * 0.08)
    thue_10 = int(tong_10 * 0.10)
    thanh_toan = int(tong_8) + int(tong_10) + thue_8 + thue_10
    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_fill_color(245, 245, 245)
    rows = [
        ("Cộng tiền hàng (thuế suất 8%):", f"{int(tong_8):,} VND"),
        ("Thuế GTGT 8%:", f"{thue_8:,} VND"),
        ("Cộng tiền hàng (thuế suất 10%):", f"{int(tong_10):,} VND"),
        ("Thuế GTGT 10%:", f"{thue_10:,} VND"),
        ("Tổng thuế GTGT:", f"{thue_8+thue_10:,} VND"),
    ]
    for lbl, val in rows:
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


def footer_note(pdf, ht="Chuyển khoản ngân hàng",
                han="30 ngày kể từ ngày xuất hóa đơn", ghi_chu=""):
    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_text_color(100, 100, 100)
    text = f"Hình thức thanh toán: {ht}  |  Hạn thanh toán: {han}"
    if ghi_chu:
        text += f"\nGhi chú: {ghi_chu}"
    pdf.multi_cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)


# ============================================================
# EC-1: HÓA ĐƠN GỐC (sai đơn giá máy nén khí)
# ============================================================
def gen_hoadon_021(out: Path):
    pdf = make_pdf()
    pdf.add_page()
    draw_header(pdf, "0000021", "07 tháng 04 năm 2026", "01GTKT0/001", "UU/26E")
    draw_party(pdf, "ĐƠN VỊ BÁN HÀNG:", NCC_THIET_BI)
    draw_party(pdf, "ĐƠN VỊ MUA HÀNG:", BINH_MINH)
    items = [
        {"stt":1,"ten":"Máy nén khí trục vít 15kW (500L/phút)","dvt":"Cái","sl":1,"dg":75_000_000},  # SAI: nen la 85tr
        {"stt":2,"ten":"Bộ lọc khí nén tổ hợp (0.01 micron)","dvt":"Bộ","sl":2,"dg":4_500_000},
        {"stt":3,"ten":"Ống dẫn khí nén DN25 (cuộn 50m)","dvt":"Cuộn","sl":10,"dg":1_200_000},
    ]
    tong = draw_items_standard(pdf, items)
    draw_totals_standard(pdf, tong, 0.10)
    footer_note(pdf,
        ghi_chu="*** HOÁ ĐƠN NÀY ĐÃ BỊ ĐIỀU CHỈNH - Xem HĐ số 0000022 ***")
    pdf.set_font("DejaVu", style="B", size=8)
    pdf.set_text_color(*COLOR_WARNING)
    pdf.cell(0, 6,
        "LƯU Ý: Hoá đơn này đã được điều chỉnh do sai đơn giá mặt hàng STT 1.",
        new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0,0,0)
    draw_signatures(pdf)
    pdf.output(str(out))
    print(f"✅ {out.name}")


# ============================================================
# EC-2: HÓA ĐƠN ĐIỀU CHỈNH cho HĐ 021
# ============================================================
def gen_hoadon_022(out: Path):
    pdf = make_pdf()
    pdf.add_page()
    draw_header(pdf, "0000022", "10 tháng 04 năm 2026", "01GTKT0/001", "VV/26E",
                dieu_chinh_cho="0000021")
    draw_party(pdf, "ĐƠN VỊ BÁN HÀNG:", NCC_THIET_BI)
    draw_party(pdf, "ĐƠN VỊ MUA HÀNG:", BINH_MINH)

    # Ghi chú lý do điều chỉnh
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

    # Bảng điều chỉnh — chỉ ghi dòng chênh lệch
    w = pdf.w - pdf.l_margin - pdf.r_margin
    cols = {"stt":9, "ten":w*0.42, "dvt":16, "sl":18, "dg_cu":30, "dg_moi":30, "cl":25}
    headers = ["STT", "Tên hàng hoá/dịch vụ", "DVT", "SL",
               "Đơn giá cũ", "Đơn giá mới", "Chênh lệch"]
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

    # Totals
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
    pdf.output(str(out))
    print(f"✅ {out.name}")


# ============================================================
# EC-3: HÓA ĐƠN ĐA THUẾ SUẤT (8% và 10%)
# ============================================================
def gen_hoadon_023(out: Path):
    pdf = make_pdf()
    pdf.add_page()
    draw_header(pdf, "0000023", "15 tháng 05 năm 2026", "01GTKT0/001", "WW/26E")
    draw_party(pdf, "ĐƠN VỊ BÁN HÀNG:", BINH_MINH)
    draw_party(pdf, "ĐƠN VỊ MUA HÀNG:", SAMSUNG)

    pdf.set_font("DejaVu", style="B", size=8)
    pdf.set_text_color(*COLOR_TABLE_HEADER)
    pdf.cell(0, 5,
        "Lưu ý: Hóa đơn này có nhiều mức thuế suất GTGT khác nhau (8% và 10%).",
        new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    items = [
        # Thuế 10% — sản phẩm thông thường
        {"stt":1,"ten":"Vỏ nhựa TV 55 inch (màu đen mờ)",        "dvt":"Cái","sl":3000,"dg":85_000,  "thue":0.10},
        {"stt":2,"ten":"Khung nhựa điều khiển từ xa",            "dvt":"Cái","sl":6000,"dg":12_000,  "thue":0.10},
        {"stt":3,"ten":"Nắp pin nhựa (bộ 2 cái)",                "dvt":"Bộ", "sl":6000,"dg":8_000,   "thue":0.10},
        # Thuế 8% — thiết bị điện tử theo NĐ giảm thuế
        {"stt":4,"ten":"Bo mạch nhựa bảo vệ PCB (giảm thuế 8%)", "dvt":"Cái","sl":3000,"dg":45_000,  "thue":0.08},
        {"stt":5,"ten":"Linh kiện nhựa tản nhiệt CPU",           "dvt":"Cái","sl":3000,"dg":62_000,  "thue":0.08},
    ]
    tong_8, tong_10 = draw_items_multi_tax(pdf, items)
    draw_totals_multi_tax(pdf, tong_8, tong_10)
    footer_note(pdf,
        ghi_chu="Mặt hàng STT 4-5 áp dụng thuế suất 8% theo Nghị định giảm thuế GTGT năm 2026.")
    draw_signatures(pdf)
    pdf.output(str(out))
    print(f"✅ {out.name}")


# ============================================================
# EC-4: HÓA ĐƠN NGOẠI TỆ USD
# ============================================================
def gen_hoadon_024(out: Path):
    TY_GIA = 25_450   # 1 USD = 25,450 VND (tỷ giá ngày lập hóa đơn)
    pdf = make_pdf()
    pdf.add_page()
    draw_header(pdf, "0000024", "20 tháng 05 năm 2026", "01GTKT0/001", "XX/26E")
    draw_party(pdf, "ĐƠN VỊ BÁN HÀNG:", NCC_SINGAPORE)
    draw_party(pdf, "ĐƠN VỊ MUA HÀNG:", BINH_MINH)

    # Ghi chú tỷ giá
    pdf.set_font("DejaVu", style="B", size=8)
    pdf.set_text_color(*COLOR_TABLE_HEADER)
    pdf.cell(0, 5,
        f"Tỷ giá quy đổi: 1 USD = {TY_GIA:,} VND (Theo tỷ giá NHTW ngày 20/05/2026)",
        new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # Bảng hàng hóa bằng USD
    w = pdf.w - pdf.l_margin - pdf.r_margin
    cols = {"stt":9, "ten":w*0.34, "dvt":14, "sl":16, "dg_usd":26, "tt_usd":24, "tt_vnd":28}
    headers = ["STT", "Tên hàng hóa", "DVT", "SL",
               "Đơn giá (USD)", "Thành tiền (USD)", "Thành tiền (VND)"]
    rh = 7

    pdf.set_fill_color(*COLOR_TABLE_HEADER)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", style="B", size=7.5)
    for h, k in zip(headers, cols):
        pdf.cell(cols[k], rh, h, border=1, align="C", fill=True)
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
        pdf.cell(cols["stt"],    rh, str(item["stt"]),          border=1, align="C", fill=fill)
        pdf.cell(cols["ten"],    rh, item["ten"],                border=1, fill=fill)
        pdf.cell(cols["dvt"],    rh, item["dvt"],                border=1, align="C", fill=fill)
        pdf.cell(cols["sl"],     rh, str(item["sl"]),            border=1, align="R", fill=fill)
        pdf.cell(cols["dg_usd"], rh, f'${item["dg_usd"]:,}',    border=1, align="R", fill=fill)
        pdf.cell(cols["tt_usd"], rh, f'${tt_usd:,}',            border=1, align="R", fill=fill)
        pdf.cell(cols["tt_vnd"], rh, f'{tt_usd*TY_GIA:,.0f}',   border=1, align="R", fill=fill)
        pdf.ln()

    tong_vnd    = int(tong_usd * TY_GIA)
    thue_vnd    = int(tong_vnd * 0.10)
    thanh_toan  = tong_vnd + thue_vnd

    pdf.ln(2)
    lw2 = (pdf.w - pdf.l_margin - pdf.r_margin) * 0.60
    vw2 = (pdf.w - pdf.l_margin - pdf.r_margin) * 0.40
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

    footer_note(pdf,
        ht="Chuyển khoản ngoại tệ (USD) hoặc VND quy đổi",
        han="45 ngày kể từ ngày xuất hóa đơn",
        ghi_chu=f"Tỷ giá thanh toán áp dụng tỷ giá NHTW ngày chuyển tiền thực tế.")
    draw_signatures(pdf)
    pdf.output(str(out))
    print(f"✅ {out.name}")


# ============================================================
# BAO CÁO TÀI CHÍNH Q2/2026 — có lỗ
# ============================================================
def gen_bao_cao_q2(out: Path):
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
            # Màu đỏ nếu số âm
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

    # Ghi chú phân tích
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

    pdf.output(str(out))
    print(f"✅ {out.name}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("🚀 Bat dau tao edge case data...\n")

    gen_hoadon_021(OUTPUT_DIR / "hoadon_021.pdf")
    gen_hoadon_022(OUTPUT_DIR / "hoadon_022.pdf")
    gen_hoadon_023(OUTPUT_DIR / "hoadon_023.pdf")
    gen_hoadon_024(OUTPUT_DIR / "hoadon_024.pdf")
    gen_bao_cao_q2(OUTPUT_DIR / "bao_cao_tai_chinh_q2.pdf")

    print(f"\n✅ Hoan thanh! Tong {len(list(OUTPUT_DIR.glob('*.pdf')))} file PDF trong {OUTPUT_DIR}/")
    print("\nDanh sach file moi:")
    for f in sorted(OUTPUT_DIR.glob("*.pdf")):
        if f.stem in ["hoadon_021","hoadon_022","hoadon_023","hoadon_024","bao_cao_tai_chinh_q2"]:
            print(f"  📄 {f.name} ({f.stat().st_size/1024:.1f} KB)")