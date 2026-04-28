"""
generate_synthetic_data.py
Refactored and upgraded script to generate a complete evaluation dataset of ~25 PDF documents.
- 20 Invoices (12 Input, 8 Output) for Công ty CP Sản Xuất Bình Minh.
- Financial Reports (Q1, Q2).
- VAT Declaration (Tháng 3/2026).
"""
import os
from pathlib import Path
from fpdf import FPDF
from datetime import datetime, timedelta
import random

# --- Config ---
OUTPUT_DIR = Path("data/sample_invoices")
# Using the absolute paths discovered in the environment
FONT_PATH = r"E:\Multi_Agent_RAG\accounting-agent\fonts\dejavu_sans\DejaVu_Sans\DejaVuSansCondensed.ttf"
FONT_BOLD_PATH = r"E:\Multi_Agent_RAG\accounting-agent\fonts\dejavu_sans\DejaVu_Sans\DejaVuSansCondensed-Bold.ttf"

# Colors
COLOR_HEADER = (41, 128, 185)    # Blue
COLOR_TABLE_HEADER = (52, 73, 94) # Dark Blue
COLOR_ROW_ALT = (236, 240, 241)   # Light Gray
COLOR_BORDER = (189, 195, 199)    # Gray border
COLOR_TOTAL = (231, 76, 60)       # Red for totals

# Central Entity
BINH_MINH = {
    "ten": "Công ty CP Sản Xuất Bình Minh",
    "mst": "0312345678",
    "dia_chi": "Lô B5, KCN Bình Dương, Tỉnh Bình Dương",
    "tai_khoan": "123456789012 - Ngân hàng Vietcombank"
}

def make_pdf(landscape=False) -> FPDF:
    """Create FPDF instance with Vietnamese font configuration."""
    orientation = "L" if landscape else "P"
    pdf = FPDF(orientation=orientation, unit="mm", format="A4")
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    # Check if fonts exist, otherwise use default
    if os.path.exists(FONT_PATH):
        pdf.add_font("DejaVu", style="", fname=FONT_PATH)
        pdf.add_font("DejaVu", style="B", fname=FONT_BOLD_PATH)
        pdf.set_font("DejaVu", size=10)
    else:
        pdf.set_font("Arial", size=10)
    return pdf

def draw_header_box(pdf: FPDF, so_hd: str, ngay: str, mau_so: str, ky_hieu: str):
    """Draw VAT invoice header."""
    pdf.set_font("DejaVu", style="B", size=16)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 10, "HÓA ĐƠN GIÁ TRỊ GIA TĂNG", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", style="", size=10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "(VAT INVOICE)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    pdf.set_font("DejaVu", style="", size=9)
    pdf.set_text_color(0, 0, 0)
    effective_width = pdf.w - pdf.l_margin - pdf.r_margin
    col = effective_width / 3
    pdf.cell(col, 6, f"Mẫu số: {mau_so}", align="L")
    pdf.cell(col, 6, f"Ký hiệu: {ky_hieu}", align="C")
    pdf.cell(col, 6, f"Số: {so_hd}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Ngày {ngay}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)

def draw_party_info(pdf: FPDF, label: str, ten: str, mst: str, dia_chi: str, tai_khoan: str = ""):
    """Draw Buyer/Seller information."""
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_text_color(*COLOR_TABLE_HEADER)
    pdf.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", style="", size=9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(35, 5.5, "Đơn vị:")
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

def generate_dynamic_invoice(data: dict, output_path: Path):
    """Generic function to generate an invoice PDF from a data dictionary."""
    pdf = make_pdf()
    pdf.add_page()
    
    # Header
    draw_header_box(pdf, data['so_hd'], data['ngay'], data['mau_so'], data['ky_hieu'])
    
    # Seller & Buyer
    draw_party_info(pdf, "ĐƠN VỊ BÁN HÀNG (SELLER)", **data['seller'])
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.set_line_width(0.2)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(2)
    draw_party_info(pdf, "ĐƠN VỊ MUA HÀNG (BUYER)", **data['buyer'])
    
    # Items Table
    pdf.set_font("DejaVu", style="B", size=9)
    pdf.set_fill_color(*COLOR_TABLE_HEADER)
    pdf.set_text_color(255, 255, 255)
    
    cols = [10, 70, 15, 20, 30, 35] # STT, Ten, DVT, SL, Don Gia, Thanh Tien
    headers = ["STT", "Tên hàng hóa, dịch vụ", "ĐVT", "SL", "Đơn giá", "Thành tiền"]
    for w, h in zip(cols, headers):
        pdf.cell(w, 8, h, border=1, align="C", fill=True)
    pdf.ln()
    
    pdf.set_font("DejaVu", style="", size=9)
    pdf.set_text_color(0, 0, 0)
    
    subtotal = 0
    for i, item in enumerate(data['items'], 1):
        thanh_tien = item['sl'] * item['don_gia']
        subtotal += thanh_tien
        
        # Zebra striping
        fill = i % 2 == 0
        pdf.set_fill_color(*COLOR_ROW_ALT)
        
        pdf.cell(cols[0], 7, str(i), border=1, align="C", fill=fill)
        pdf.cell(cols[1], 7, item['ten'], border=1, fill=fill)
        pdf.cell(cols[2], 7, item['dvt'], border=1, align="C", fill=fill)
        pdf.cell(cols[3], 7, f"{item['sl']:,}", border=1, align="R", fill=fill)
        
        price_str = f"{item['don_gia']:,}"
        if 'currency' in data and data['currency'] == 'USD':
            price_str = f"${item['don_gia']:,.2f}"
        pdf.cell(cols[4], 7, price_str, border=1, align="R", fill=fill)
        
        total_str = f"{thanh_tien:,.0f}"
        if 'currency' in data and data['currency'] == 'USD':
            total_str = f"${thanh_tien:,.2f}"
        pdf.cell(cols[5], 7, total_str, border=1, align="R", fill=fill)
        pdf.ln()

    # Totals
    pdf.set_font("DejaVu", style="B", size=9)
    currency_symbol = "VNĐ" if data.get('currency', 'VND') == 'VND' else "USD"
    
    # VAT calculation
    vat_rate = data.get('vat_rate', 10)
    vat_amount = subtotal * (vat_rate / 100)
    total_payment = subtotal + vat_amount
    
    def draw_total_row(label, value):
        pdf.cell(sum(cols[:-1]), 7, label, border=1, align="R")
        val_str = f"{value:,.0f}" if currency_symbol == "VNĐ" else f"${value:,.2f}"
        pdf.cell(cols[-1], 7, val_str, border=1, align="R")
        pdf.ln()

    draw_total_row("Cộng tiền hàng (Subtotal):", subtotal)
    draw_total_row(f"Thuế suất GTGT (VAT Rate): {vat_rate}%", vat_amount)
    
    pdf.set_text_color(*COLOR_TOTAL)
    draw_total_row("Tổng cộng tiền thanh toán (Total):", total_payment)
    
    # Currency Note
    if data.get('currency') == 'USD':
        pdf.set_font("DejaVu", style="", size=8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, f"* Tỷ giá quy đổi: 1 USD = {data.get('exchange_rate', '25,450')} VNĐ", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    # Signatures
    effective_width = pdf.w - pdf.l_margin - pdf.r_margin
    col_w = effective_width / 2
    pdf.set_font("DejaVu", style="B", size=10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(col_w, 6, "NGƯỜI MUA HÀNG", align="C")
    pdf.cell(col_w, 6, "NGƯỜI BÁN HÀNG", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", style="", size=8)
    pdf.cell(col_w, 5, "(Ký, ghi rõ họ tên)", align="C")
    pdf.cell(col_w, 5, "(Ký, đóng dấu)", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.output(str(output_path))
    print(f"✅ Generated: {output_path}")

def generate_financial_report(output_path: Path, quarter: str, year: int, data_2026: dict, data_2025: dict):
    """Generate a financial report PDF."""
    pdf = make_pdf()
    pdf.add_page()
    
    # Header
    pdf.set_font("DejaVu", style="B", size=12)
    pdf.cell(0, 6, BINH_MINH['ten'], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", style="", size=10)
    pdf.cell(0, 5, f"Địa chỉ: {BINH_MINH['dia_chi']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font("DejaVu", style="B", size=16)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 10, f"BÁO CÁO TÀI CHÍNH QUÝ {quarter}/{year}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    def draw_table(title, rows):
        pdf.set_font("DejaVu", style="B", size=10)
        pdf.set_text_color(*COLOR_TABLE_HEADER)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        
        col1, col2, col3 = 90, 45, 45
        pdf.set_fill_color(*COLOR_TABLE_HEADER)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(col1, 8, "Chỉ tiêu", border=1, fill=True)
        pdf.cell(col2, 8, f"Quý {quarter}/{year}", border=1, align="C", fill=True)
        pdf.cell(col3, 8, f"Quý {quarter}/{year-1}", border=1, align="C", fill=True)
        pdf.ln()
        
        pdf.set_text_color(0, 0, 0)
        for i, (label, val_curr, val_prev, is_bold) in enumerate(rows):
            fill = i % 2 == 1
            pdf.set_fill_color(*COLOR_ROW_ALT)
            if is_bold:
                pdf.set_font("DejaVu", style="B", size=9)
            else:
                pdf.set_font("DejaVu", style="", size=9)
            
            pdf.cell(col1, 7, f" {label}", border=1, fill=fill)
            pdf.cell(col2, 7, f"{val_curr:,.0f}", border=1, align="R", fill=fill)
            pdf.cell(col3, 7, f"{val_prev:,.0f}", border=1, align="R", fill=fill)
            pdf.ln()
        pdf.ln(5)

    report_rows = [
        ("Doanh thu thuần", data_2026['revenue'], data_2025['revenue'], False),
        ("Giá vốn hàng bán", data_2026['cost'], data_2025['cost'], False),
        ("Lợi nhuận gộp", data_2026['revenue'] - data_2026['cost'], data_2025['revenue'] - data_2025['cost'], True),
        ("Lợi nhuận sau thuế", data_2026['profit'], data_2025['profit'], True),
    ]
    draw_table("I. KẾT QUẢ KINH DOANH (VNĐ)", report_rows)
    
    pdf.output(str(output_path))
    print(f"✅ Generated: {output_path}")

def generate_vat_declaration(output_path: Path, month: int, year: int, input_vat: float, output_vat: float):
    """Generate a VAT declaration PDF."""
    pdf = make_pdf()
    pdf.add_page()
    
    pdf.set_font("DejaVu", style="B", size=14)
    pdf.cell(0, 10, f"TỜ KHAI THUẾ GTGT THÁNG {month}/{year}", align="C", new_x="LMARGIN", new_y="NEXT")
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
        
    pdf.output(str(output_path))
    print(f"✅ Generated: {output_path}")

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("🚀 Starting synthetic data generation...\n")
    
    # --- 12 INPUT INVOICES (Bình Minh is Buyer) ---
    suppliers = [
        {"ten": "Công ty TNHH Thép Việt", "mst": "0101234567", "dia_chi": "KCN Quang Minh, Hà Nội"},
        {"ten": "Tổng kho Hóa chất Miền Nam", "mst": "0309876543", "dia_chi": "Quận 7, TP.HCM"},
        {"ten": "Cơ khí Chính xác ABC", "mst": "3701234444", "dia_chi": "Thuận An, Bình Dương"},
        {"ten": "Năng lượng Xanh", "mst": "0105556667", "dia_chi": "Cầu Giấy, Hà Nội"}
    ]
    
    input_vat_total_march = 0
    
    for i in range(1, 13):
        supplier = random.choice(suppliers)
        date = datetime(2026, random.randint(1, 6), random.randint(1, 28))
        
        items = [
            {"ten": "Nguyên liệu nhựa PP", "sl": random.randint(100, 500), "dvt": "kg", "don_gia": 45000},
            {"ten": "Hóa chất phụ gia", "sl": random.randint(10, 50), "dvt": "lít", "don_gia": 120000}
        ]
        
        data = {
            "so_hd": f"{i:07d}",
            "ngay": date.strftime("%d/%m/%Y"),
            "mau_so": "1/001",
            "ky_hieu": "BM/26E",
            "seller": supplier,
            "buyer": BINH_MINH,
            "items": items,
            "vat_rate": 10
        }
        
        # Edge Case 1: Commercial Discount (Negative value)
        if i == 1:
            data['items'].append({"ten": "Chiết khấu thương mại", "sl": 1, "dvt": "Lần", "don_gia": -500000})
            
        # Edge Case 2: USD billing
        if i == 2:
            data['currency'] = 'USD'
            data['exchange_rate'] = '25,450'
            for item in data['items']:
                item['don_gia'] = round(item['don_gia'] / 25450, 2)
        
        # Edge Case 3: Missing Buyer MST
        if i == 3:
            data['buyer'] = BINH_MINH.copy()
            data['buyer']['mst'] = ""
            
        # Edge Case 4: Various VAT rates
        if i == 4: data['vat_rate'] = 0
        if i == 5: data['vat_rate'] = 5
        if i == 6: data['vat_rate'] = 8
        
        filename = f"hoadon_input_{i:03d}.pdf"
        generate_dynamic_invoice(data, OUTPUT_DIR / filename)
        
        # Track March VAT for declaration
        if date.month == 3:
            subtotal = sum(item['sl'] * item['don_gia'] for item in data['items'])
            if data.get('currency') == 'USD':
                subtotal *= 25450
            input_vat_total_march += subtotal * (data['vat_rate'] / 100)

    # --- 8 OUTPUT INVOICES (Bình Minh is Seller) ---
    customers = [
        {"ten": "Công ty Bao bì Toàn Cầu", "mst": "0311223344", "dia_chi": "KCN Tân Bình, TP.HCM"},
        {"ten": "Nhựa Gia dụng Minh Phát", "mst": "3700112233", "dia_chi": "Dĩ An, Bình Dương"}
    ]
    
    output_vat_total_march = 0
    
    for i in range(1, 9):
        customer = random.choice(customers)
        date = datetime(2026, random.randint(1, 6), random.randint(1, 28))
        
        items = [
            {"ten": "Màng nhựa PE cuộn", "sl": random.randint(50, 100), "dvt": "Cuộn", "don_gia": 850000},
            {"ten": "Túi nilon thực phẩm", "sl": random.randint(200, 500), "dvt": "kg", "don_gia": 35000}
        ]
        
        data = {
            "so_hd": f"{i+100:07d}",
            "ngay": date.strftime("%d/%m/%Y"),
            "mau_so": "1/001",
            "ky_hieu": "BM/26P",
            "seller": BINH_MINH,
            "buyer": customer,
            "items": items,
            "vat_rate": 10
        }
        
        filename = f"hoadon_output_{i:03d}.pdf"
        generate_dynamic_invoice(data, OUTPUT_DIR / filename)
        
        if date.month == 3:
            subtotal = sum(item['sl'] * item['don_gia'] for item in data['items'])
            output_vat_total_march += subtotal * (data['vat_rate'] / 100)

    # --- Additional Documents ---
    generate_financial_report(OUTPUT_DIR / "bao_cao_tai_chinh_q1.pdf", "1", 2026, 
                             {"revenue": 4850000000, "cost": 3120000000, "profit": 944000000},
                             {"revenue": 3920000000, "cost": 2580000000, "profit": 705600000})
    
    generate_financial_report(OUTPUT_DIR / "bao_cao_tai_chinh_q2.pdf", "2", 2026, 
                             {"revenue": 5200000000, "cost": 3400000000, "profit": 1100000000},
                             {"revenue": 4100000000, "cost": 2700000000, "profit": 850000000})
    
    generate_vat_declaration(OUTPUT_DIR / "to_khai_thue_gtgt_thang3_2026.pdf", 3, 2026, 
                            input_vat_total_march, output_vat_total_march)

    print(f"\n✅ Finished! Created {len(list(OUTPUT_DIR.glob('*.pdf')))} files in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
