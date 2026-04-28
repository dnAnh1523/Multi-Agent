"""
generate_more_invoices.py
Tạo thêm 17 hóa đơn synthetic cho Công ty CP Sản Xuất Bình Minh.
- 10 hóa đơn đầu vào (mua hàng từ nhà cung cấp) tháng 1-5/2026
- 7 hóa đơn đầu ra (bán hàng cho khách) tháng 1-5/2026

Chạy: python generate_more_invoices.py
Output: data/sample_invoices/hoadon_004.pdf đến hoadon_020.pdf
"""

import os
import sys
from pathlib import Path
from fpdf import FPDF

# --- Config ---
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

FONT_PATH = find_font(FONT_PATHS)
FONT_BOLD_PATH = find_font(FONT_BOLD_PATHS)

if not FONT_PATH or not FONT_BOLD_PATH:
    print("❌ Không tìm thấy font DejaVuSansCondensed.")
    print("   Copy DejaVuSansCondensed.ttf và DejaVuSansCondensed-Bold.ttf")
    print("   vào thư mục fonts/dejavu_sans/DejaVu_Sans/ trong project.")
    sys.exit(1)

print(f"✅ Dùng font: {FONT_PATH}")

COLOR_HEADER       = (41, 128, 185)
COLOR_TABLE_HEADER = (52, 73, 94)
COLOR_ROW_ALT      = (236, 240, 241)
COLOR_BORDER       = (189, 195, 199)

BINH_MINH = {
    "ten": "Công ty CP Sản Xuất Bình Minh",
    "mst": "0312345678",
    "dia_chi": "Lô B5, KCN Bình Dương, Tỉnh Bình Dương",
    "tk": "10203045678901 - Ngân hàng Vietcombank CN Bình Dương",
}

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


def make_pdf():
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("DejaVu", style="",  fname=FONT_PATH)
    pdf.add_font("DejaVu", style="B", fname=FONT_BOLD_PATH)
    return pdf


def draw_header(pdf, so_hd, ngay, mau_so, ky_hieu):
    pdf.set_font("DejaVu", style="B", size=15)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 10, "HÓA ĐƠN GIÁ TRỊ GIA TĂNG", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", style="", size=9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "(VAT INVOICE)", align="C", new_x="LMARGIN", new_y="NEXT")
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


def draw_items(pdf, items):
    w = pdf.w - pdf.l_margin - pdf.r_margin
    cols = {"stt": 10, "ten": w*0.36, "dvt": 16, "sl": 20, "dg": 34, "tt": 34}
    headers = ["STT", "Tên hàng hóa/dịch vụ", "ĐVT", "Số lượng", "Đơn giá", "Thành tiền"]
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
        pdf.cell(cols["ten"], rh, item["ten"], border=1, fill=fill)
        pdf.cell(cols["dvt"], rh, item["dvt"], border=1, align="C", fill=fill)
        pdf.cell(cols["sl"],  rh, f'{item["sl"]:,}', border=1, align="R", fill=fill)
        pdf.cell(cols["dg"],  rh, f'{item["dg"]:,.0f}', border=1, align="R", fill=fill)
        pdf.cell(cols["tt"],  rh, f'{tt:,.0f}', border=1, align="R", fill=fill)
        pdf.ln()
    return tong


def draw_totals(pdf, tong, thue=0.10):
    w = pdf.w - pdf.l_margin - pdf.r_margin
    lw, vw = w * 0.65, w * 0.35
    rh = 7
    thue_tien  = int(tong * thue)
    thanh_toan = int(tong) + thue_tien
    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_fill_color(245, 245, 245)
    for lbl, val in [
        ("Cộng tiền hàng:", f"{int(tong):,} VNĐ"),
        (f"Thuế suất GTGT: {int(thue*100)}%:", f"{thue_tien:,} VNĐ"),
    ]:
        pdf.cell(lw, rh, lbl, border=1, align="R", fill=True)
        pdf.cell(vw, rh, val, border=1, align="R", fill=True)
        pdf.ln()
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_fill_color(*COLOR_HEADER)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(lw, rh+1, "TỔNG CỘNG TIỀN THANH TOÁN:", border=1, align="R", fill=True)
    pdf.cell(vw, rh+1, f"{thanh_toan:,} VNĐ", border=1, align="R", fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("DejaVu", style="", size=8)
    pdf.ln(2)
    return thanh_toan


def draw_signatures(pdf):
    w  = pdf.w - pdf.l_margin - pdf.r_margin
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
    pdf.cell(col, 5, "Trần Thị Bán", align="C", new_x="LMARGIN", new_y="NEXT")


def gen_hoadon(output_path, so_hd, ngay, mau_so, ky_hieu,
               ben_ban, ben_mua, items, thue=0.10,
               ht_thanh_toan="Chuyển khoản ngân hàng",
               han_tt="30 ngày kể từ ngày xuất hóa đơn",
               ghi_chu=""):
    pdf = make_pdf()
    pdf.add_page()
    draw_header(pdf, so_hd, ngay, mau_so, ky_hieu)
    draw_party(pdf, "ĐƠN VỊ BÁN HÀNG:", ben_ban)
    draw_party(pdf, "ĐƠN VỊ MUA HÀNG:", ben_mua)
    tong = draw_items(pdf, items)
    draw_totals(pdf, tong, thue)
    pdf.set_font("DejaVu", style="", size=8)
    pdf.set_text_color(100, 100, 100)
    footer = f"Hình thức thanh toán: {ht_thanh_toan}  |  Hạn thanh toán: {han_tt}"
    if ghi_chu:
        footer += f"  |  {ghi_chu}"
    pdf.multi_cell(0, 5, footer, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    draw_signatures(pdf)
    pdf.output(str(output_path))
    print(f"✅ {output_path.name}")


# ============================================================
# 10 HÓA ĐƠN ĐẦU VÀO (Bình Minh mua)
# ============================================================
INVOICES_IN = [
    dict(so_hd="0000004", ngay="08 tháng 01 năm 2026", mau_so="01GTKT0/001", ky_hieu="DD/26E",
         ben_ban=NHA_CUNG_CAP[0], ben_mua=BINH_MINH, thue=0.10,
         items=[
             {"stt":1,"ten":"Hạt nhựa PP (Polypropylene) nguyên sinh","dvt":"Kg","sl":5000,"dg":28_000},
             {"stt":2,"ten":"Hạt nhựa HDPE tái chế","dvt":"Kg","sl":2000,"dg":22_000},
             {"stt":3,"ten":"Chất phụ gia ổn định nhiệt","dvt":"Kg","sl":200,"dg":85_000},
         ]),
    dict(so_hd="0000005", ngay="15 tháng 01 năm 2026", mau_so="01GTKT0/001", ky_hieu="EE/26E",
         ben_ban=NHA_CUNG_CAP[1], ben_mua=BINH_MINH, thue=0.08,
         items=[
             {"stt":1,"ten":"Thép tấm cán nguội (Cold Rolled) dày 2mm","dvt":"Tấn","sl":10,"dg":18_500_000},
             {"stt":2,"ten":"Thép hộp vuông 50x50x2mm","dvt":"Cây","sl":200,"dg":280_000},
             {"stt":3,"ten":"Bulong đai ốc M10 (hộp 100 cái)","dvt":"Hộp","sl":50,"dg":120_000},
         ]),
    dict(so_hd="0000006", ngay="03 tháng 02 năm 2026", mau_so="01GTKT0/001", ky_hieu="FF/26E",
         ben_ban=NHA_CUNG_CAP[2], ben_mua=BINH_MINH, thue=0.10,
         items=[
             {"stt":1,"ten":"Túi PE đóng gói sản phẩm (25x35cm)","dvt":"Cuộn","sl":500,"dg":180_000},
             {"stt":2,"ten":"Thùng carton 5 lớp (40x30x25cm)","dvt":"Cái","sl":2000,"dg":25_000},
             {"stt":3,"ten":"Băng keo đóng gói (48mm x 100m)","dvt":"Cuộn","sl":200,"dg":35_000},
             {"stt":4,"ten":"Nhãn dán sản phẩm (in màu 4 màu)","dvt":"Tờ","sl":10000,"dg":800},
         ]),
    dict(so_hd="0000007", ngay="18 tháng 02 năm 2026", mau_so="01GTKT0/001", ky_hieu="GG/26E",
         ben_ban=NHA_CUNG_CAP[3], ben_mua=BINH_MINH, thue=0.10,
         items=[
             {"stt":1,"ten":"Động cơ điện 3 pha 7.5kW (IE3)","dvt":"Cái","sl":2,"dg":12_500_000},
             {"stt":2,"ten":"Biến tần Siemens G120 7.5kW","dvt":"Cái","sl":2,"dg":18_000_000},
             {"stt":3,"ten":"Cáp điện 3x4mm2 (cuộn 100m)","dvt":"Cuộn","sl":5,"dg":2_800_000},
         ]),
    dict(so_hd="0000008", ngay="05 tháng 03 năm 2026", mau_so="01GTKT0/001", ky_hieu="HH/26E",
         ben_ban=NHA_CUNG_CAP[4], ben_mua=BINH_MINH, thue=0.10,
         items=[
             {"stt":1,"ten":"Dung môi MEK (Methyl Ethyl Ketone) thùng 180L","dvt":"Thùng","sl":10,"dg":8_500_000},
             {"stt":2,"ten":"Sơn chống rỉ epoxy 2 thành phần (20L)","dvt":"Thùng","sl":30,"dg":1_200_000},
             {"stt":3,"ten":"Chất tẩy rửa công nghiệp (can 25L)","dvt":"Can","sl":20,"dg":650_000},
         ]),
    dict(so_hd="0000009", ngay="20 tháng 03 năm 2026", mau_so="01GTKT0/001", ky_hieu="II/26E",
         ben_ban=NHA_CUNG_CAP[5], ben_mua=BINH_MINH, thue=0.10,
         items=[
             {"stt":1,"ten":"Vận chuyển hàng hóa TP.HCM - Bình Dương (xe 5 tấn)","dvt":"Chuyến","sl":15,"dg":2_200_000},
             {"stt":2,"ten":"Vận chuyển hàng hóa Đồng Nai - Bình Dương (xe 10 tấn)","dvt":"Chuyến","sl":8,"dg":3_500_000},
             {"stt":3,"ten":"Phí bốc xếp hàng hóa tại kho","dvt":"Tấn","sl":50,"dg":150_000},
         ]),
    dict(so_hd="0000010", ngay="07 tháng 04 năm 2026", mau_so="01GTKT0/001", ky_hieu="JJ/26E",
         ben_ban=NHA_CUNG_CAP[6], ben_mua=BINH_MINH, thue=0.10,
         items=[
             {"stt":1,"ten":"Máy nén khí trục vít 15kW (500L/phút)","dvt":"Cái","sl":1,"dg":85_000_000},
             {"stt":2,"ten":"Bộ lọc khí nén tổ hợp (0.01 micron)","dvt":"Bộ","sl":2,"dg":4_500_000},
             {"stt":3,"ten":"Ống dẫn khí nén DN25 (cuộn 50m)","dvt":"Cuộn","sl":10,"dg":1_200_000},
             {"stt":4,"ten":"Van điện từ khí nén 1/2 inch","dvt":"Cái","sl":20,"dg":850_000},
         ]),
    dict(so_hd="0000011", ngay="22 tháng 04 năm 2026", mau_so="01GTKT0/001", ky_hieu="KK/26E",
         ben_ban=NHA_CUNG_CAP[7], ben_mua=BINH_MINH, thue=0.10,
         items=[
             {"stt":1,"ten":"Giấy in A4 80gsm (thùng 5 ram)","dvt":"Thùng","sl":20,"dg":320_000},
             {"stt":2,"ten":"Giấy kraft cuộn 70cm (cuộn 100m)","dvt":"Cuộn","sl":50,"dg":180_000},
             {"stt":3,"ten":"Giấy decal trắng A4 (hộp 100 tờ)","dvt":"Hộp","sl":30,"dg":250_000},
         ]),
    dict(so_hd="0000012", ngay="06 tháng 05 năm 2026", mau_so="01GTKT0/001", ky_hieu="LL/26E",
         ben_ban=NHA_CUNG_CAP[8], ben_mua=BINH_MINH, thue=0.10,
         items=[
             {"stt":1,"ten":"Dầu thủy lực Castrol Hyspin AWS 46 (thùng 209L)","dvt":"Thùng","sl":3,"dg":9_800_000},
             {"stt":2,"ten":"Mỡ bôi trơn Castrol Molub-Alloy (hộp 18kg)","dvt":"Hộp","sl":5,"dg":2_200_000},
             {"stt":3,"ten":"Dầu cắt gọt gia công kim loại (can 20L)","dvt":"Can","sl":10,"dg":1_500_000},
         ]),
    dict(so_hd="0000013", ngay="20 tháng 05 năm 2026", mau_so="01GTKT0/001", ky_hieu="MM/26E",
         ben_ban=NHA_CUNG_CAP[9], ben_mua=BINH_MINH, thue=0.10,
         items=[
             {"stt":1,"ten":"Vòng bi SKF 6205 2RS (hộp 10 cái)","dvt":"Hộp","sl":20,"dg":850_000},
             {"stt":2,"ten":"Dây curoa Optibelt Z31 (bộ 5 cái)","dvt":"Bộ","sl":10,"dg":680_000},
             {"stt":3,"ten":"Khớp nối trục đàn hồi size 6","dvt":"Cái","sl":8,"dg":1_200_000},
             {"stt":4,"ten":"Xy lanh khí nén Ø50 stroke 200mm","dvt":"Cái","sl":6,"dg":2_800_000},
         ]),
]

# ============================================================
# 7 HÓA ĐƠN ĐẦU RA (Bình Minh bán)
# ============================================================
INVOICES_OUT = [
    dict(so_hd="0000014", ngay="25 tháng 01 năm 2026", mau_so="01GTKT0/001", ky_hieu="NN/26E",
         ben_ban=BINH_MINH, ben_mua=KHACH_HANG[0], thue=0.10,
         items=[
             {"stt":1,"ten":"Vỏ nhựa TV 55 inch (màu đen mờ)","dvt":"Cái","sl":5000,"dg":85_000},
             {"stt":2,"ten":"Khung nhựa điều khiển từ xa","dvt":"Cái","sl":10000,"dg":12_000},
             {"stt":3,"ten":"Nắp pin nhựa (bộ 2 cái)","dvt":"Bộ","sl":10000,"dg":8_000},
         ]),
    dict(so_hd="0000015", ngay="10 tháng 02 năm 2026", mau_so="01GTKT0/001", ky_hieu="OO/26E",
         ben_ban=BINH_MINH, ben_mua=KHACH_HANG[1], thue=0.10,
         items=[
             {"stt":1,"ten":"Khung nhựa máy giặt cửa trước","dvt":"Cái","sl":3000,"dg":125_000},
             {"stt":2,"ten":"Nắp bộ lọc máy giặt","dvt":"Cái","sl":3000,"dg":45_000},
             {"stt":3,"ten":"Vỏ nhựa điều hòa không khí 1.5HP","dvt":"Bộ","sl":2000,"dg":180_000},
         ]),
    dict(so_hd="0000016", ngay="25 tháng 02 năm 2026", mau_so="01GTKT0/001", ky_hieu="PP/26E",
         ben_ban=BINH_MINH, ben_mua=KHACH_HANG[2], thue=0.08,
         items=[
             {"stt":1,"ten":"Ống nhựa PVC Ø90 dài 6m (PN10)","dvt":"Cây","sl":1000,"dg":185_000},
             {"stt":2,"ten":"Ống nhựa HDPE Ø110 dài 6m (PN10)","dvt":"Cây","sl":500,"dg":320_000},
             {"stt":3,"ten":"Co nối PVC 90 độ Ø90","dvt":"Cái","sl":500,"dg":35_000},
         ]),
    dict(so_hd="0000017", ngay="15 tháng 03 năm 2026", mau_so="01GTKT0/001", ky_hieu="QQ/26E",
         ben_ban=BINH_MINH, ben_mua=KHACH_HANG[3], thue=0.10,
         items=[
             {"stt":1,"ten":"Vỏ nhựa máy ảnh Lumix series (bộ 3 chi tiết)","dvt":"Bộ","sl":2000,"dg":220_000},
             {"stt":2,"ten":"Khung nhựa bếp từ Panasonic","dvt":"Cái","sl":3000,"dg":95_000},
             {"stt":3,"ten":"Nắp nhựa nồi cơm điện 1.8L","dvt":"Cái","sl":5000,"dg":42_000},
         ]),
    dict(so_hd="0000018", ngay="10 tháng 04 năm 2026", mau_so="01GTKT0/001", ky_hieu="RR/26E",
         ben_ban=BINH_MINH, ben_mua=KHACH_HANG[4], thue=0.10,
         items=[
             {"stt":1,"ten":"Tấm ốp nhựa ABS (600x400x3mm)","dvt":"Tấm","sl":500,"dg":185_000},
             {"stt":2,"ten":"Chi tiết nhựa kỹ thuật PA66 (phức tạp)","dvt":"Cái","sl":1000,"dg":320_000},
             {"stt":3,"ten":"Bánh răng nhựa POM module 2 (Z=40)","dvt":"Cái","sl":500,"dg":280_000},
         ]),
    dict(so_hd="0000019", ngay="22 tháng 04 năm 2026", mau_so="01GTKT0/001", ky_hieu="SS/26E",
         ben_ban=BINH_MINH, ben_mua=KHACH_HANG[5], thue=0.10,
         items=[
             {"stt":1,"ten":"Khung nhựa máy photocopy A3","dvt":"Cái","sl":1000,"dg":450_000},
             {"stt":2,"ten":"Nắp nhựa khay giấy máy in","dvt":"Cái","sl":2000,"dg":85_000},
             {"stt":3,"ten":"Bánh xe dẫn giấy nhựa (bộ 4 cái)","dvt":"Bộ","sl":2000,"dg":120_000},
         ]),
    dict(so_hd="0000020", ngay="15 tháng 05 năm 2026", mau_so="01GTKT0/001", ky_hieu="TT/26E",
         ben_ban=BINH_MINH, ben_mua=KHACH_HANG[6], thue=0.10,
         items=[
             {"stt":1,"ten":"Ống cuộn chỉ nhựa (Ø76mm x 200mm)","dvt":"Cái","sl":10000,"dg":18_000},
             {"stt":2,"ten":"Cone cuộn sợi nhựa (Ø60mm, cao 180mm)","dvt":"Cái","sl":20000,"dg":12_000},
             {"stt":3,"ten":"Lõi nhựa cuộn vải (Ø150mm x 1500mm)","dvt":"Cái","sl":500,"dg":185_000},
             {"stt":4,"ten":"Hộp nhựa đựng phụ kiện may (30x20x10cm)","dvt":"Cái","sl":2000,"dg":55_000},
         ]),
]


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total_planned = len(INVOICES_IN) + len(INVOICES_OUT)
    print(f"🚀 Bắt đầu tạo {total_planned} hóa đơn...\n")

    print("--- HÓA ĐƠN ĐẦU VÀO (Bình Minh mua) ---")
    for i, inv in enumerate(INVOICES_IN):
        fname = f"hoadon_{4+i:03d}.pdf"
        gen_hoadon(OUTPUT_DIR / fname, **inv)

    print("\n--- HÓA ĐƠN ĐẦU RA (Bình Minh bán) ---")
    for i, inv in enumerate(INVOICES_OUT):
        fname = f"hoadon_{14+i:03d}.pdf"
        gen_hoadon(OUTPUT_DIR / fname, **inv)

    total = len(list(OUTPUT_DIR.glob("*.pdf")))
    print(f"\n✅ Hoàn thành! Tổng {total} file PDF trong {OUTPUT_DIR}/")