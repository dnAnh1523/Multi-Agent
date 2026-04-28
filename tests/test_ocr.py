# test_ocr.py
import pytesseract
import pymupdf4llm

# Config đường dẫn Tesseract mặc định trên Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Test extract file scan
result = pymupdf4llm.to_markdown(
    "data\\tax_documents\\78_2021_TT-BTC_477966.pdf",
    page_chunks=True,
)

print(f"Số trang extract được: {len(result)}")
print(f"\nText trang 1 (300 ký tự đầu):")
print(result[0]["text"][:300])
print(f"\nText trang 2 (300 ký tự đầu):")
print(result[1]["text"][:300] if len(result) > 1 else "Không có trang 2")