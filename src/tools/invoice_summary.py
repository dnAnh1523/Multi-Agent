"""
invoice_summary.py - Tool tóm tắt chi tiết hóa đơn
Trích xuất các trường quan trọng từ hóa đơn và trả về dạng bảng Markdown.
"""

from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage
from src.rag.retriever import retrieve, format_context, extract_metadata_filter
from src.utils.llm import get_llm

INVOICE_SUMMARY_PROMPT = """Bạn là chuyên gia kế toán Việt Nam. 
Dựa vào nội dung hóa đơn dưới đây, hãy trích xuất và trình bày các thông tin sau dạng bảng Markdown:

| Trường | Giá trị |
|--------|---------|
| Số hóa đơn | ... |
| Ký hiệu mẫu số | ... |
| Ngày lập | ... |
| Đơn vị bán hàng | ... |
| Mã số thuế (bên bán) | ... |
| Đơn vị mua hàng | ... |
| Mã số thuế (bên mua) | ... |
| Tổng tiền hàng (chưa thuế) | ... |
| Thuế suất GTGT | ... |
| Tiền thuế GTGT | ... |
| Tổng thanh toán | ... |
| Hình thức thanh toán | ... |

Nếu không tìm thấy thông tin nào, ghi "Không có" vào cột Giá trị.
Chỉ trả về bảng Markdown, không giải thích thêm.

NỘI DUNG HÓA ĐƠN:
{context}
"""

def invoice_summary_tool(query: str, vector_store: Chroma, bm25_retriever=None) -> str:
    """
    Tóm tắt chi tiết một hóa đơn từ vector store.
    
    Args:
        query: câu hỏi/yêu cầu của user (ví dụ: "tóm tắt hóa đơn số 001")
        vector_store: Chroma instance đã có documents
        
    Returns:
        str: bảng Markdown tóm tắt hóa đơn
    """
    # 1. Trích xuất filter từ query
    my_filter = extract_metadata_filter(query)

    # 2. Truyền filter vào hàm retrieve
    docs = retrieve(vector_store, query, k=3, metadata_filter=my_filter, bm25_retriever=bm25_retriever)

    # 3. CƠ CHẾ FALLBACK: Nếu filter quá khắt khe, thử tìm lại không dùng filter
    if not docs and my_filter:
        print("⚠️ Filter quá chặt không tìm thấy tài liệu, đang tìm lại không dùng filter...")
        docs = retrieve(vector_store, query, k=3, metadata_filter=None, bm25_retriever=bm25_retriever)

    if not docs:
        return "❌ Không tìm thấy hóa đơn phù hợp trong tài liệu đã upload. Hãy chắc chắn bạn đã cung cấp mã hoặc tên tài liệu hợp lệ."
    
    # Sửa lỗi Unpack Tuple: format_context trả về 2 biến (string, dict)
    context, _ = format_context(docs)
    prompt = INVOICE_SUMMARY_PROMPT.format(context=context)

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])

    return response.content