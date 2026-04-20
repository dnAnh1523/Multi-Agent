"""
loader.py - PDF Loading và Chunking Pipeline
Dùng pymupdf4llm để extract PDF ra Markdown theo từng trang,
sau đó chunk và wrap thành LangChain Documents có metadata đầy đủ.
"""

import unicodedata
from pathlib import Path
from langchain_core.documents import Document
import pymupdf4llm


def normalize_vietnamese(text: str) -> str:
    """
    Chuẩn hóa encoding tiếng Việt về Unicode NFC.
    Giải quyết vấn đề font VNI/TCVN3 extract ra ký tự lạ.
    """
    return unicodedata.normalize("NFC", text)



def clean_text(text: str) -> str:
    """
    Làm sạch text sau khi extract:
    - Bỏ dòng trắng thừa (quá 2 dòng liên tiếp)
    - Strip khoảng trắng đầu/cuối mỗi dòng
    """
    # 1. Split theo "\n"
    # 2. Strip từng dòng
    # 3. Gộp lại, nhưng không để quá 2 dòng trắng liên tiếp
    lines = text.split("\n")
    cleaned_lines = [line.strip() for line in lines]
    # Remove consecutive empty lines
    i = 0
    while i < len(cleaned_lines):
        if not cleaned_lines[i]:
            j = i + 1
            while j < len(cleaned_lines) and not cleaned_lines[j]:
                j += 1
            if j - i > 2:
                cleaned_lines[i:j] = [""] * (j - i - 2)
            i = j
        else:
            i += 1
    return "\n".join(cleaned_lines)


def load_pdf(file_path: str) -> list[Document]:
    """
    Load một file PDF và trả về list Documents đã chunk.
    Mỗi Document chứa:
    - page_content: text của chunk (đã clean)
    - metadata: {source, page, chunk_index, total_pages}
    
    Args:
        file_path: đường dẫn tới file PDF
        
    Returns:
        list[Document]: các chunks đã sẵn sàng để embed
        
    Raises:
        FileNotFoundError: nếu file không tồn tại
        ValueError: nếu PDF không extract được text
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError("File not found: {}".format(file_path))
    
    page_chunks = pymupdf4llm.to_markdown(str(path), page_chunks=True)
    if not page_chunks:
        raise ValueError("No text extracted from PDF: {}".format(file_path))
    
    documents = []
    for page_data in page_chunks:
        text = page_data["text"]
        page_num = page_data["metadata"].get("page") or page_data["metadata"].get("page_number", 1)
        text = normalize_vietnamese(text)
        text = clean_text(text)
        if len(text) < 50:
            print(f"⚠️ Trang {page_num} của '{path.name}' không extract được text")
            continue
        doc = Document(
            page_content=text,
            metadata={
                "source": path.name,
                "page": page_num,
                "file_path": str(path),
            }
        )
        documents.append(doc)
    return documents


def load_pdfs(file_paths: list[str]) -> list[Document]:
    """
    Load nhiều file PDF, gộp tất cả Documents lại.
    Bỏ qua file lỗi thay vì crash toàn bộ pipeline.
    
    Args:
        file_paths: list đường dẫn PDF
        
    Returns:
        list[Document]: tất cả chunks từ tất cả files
    """
    all_documents = []
    errors = []
    
    for file_path in file_paths:
        try:
            docs = load_pdf(file_path)
            all_documents.extend(docs)
        except Exception as e:
            errors.append((file_path, str(e)))
    
    if errors:
        print(f"⚠️ Không load được {len(errors)} file: {errors}")
    
    return all_documents