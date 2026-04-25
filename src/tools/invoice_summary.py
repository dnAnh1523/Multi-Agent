"""
invoice_summary.py - Tool tóm tắt chi tiết hóa đơn
Trích xuất các trường quan trọng từ hóa đơn và trả về dạng bảng Markdown.
"""

from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage
from src.rag.retriever import retrieve, format_context, extract_metadata_filter
from src.utils.llm import get_llm

INVOICE_SUMMARY_PROMPT = """Bạn là chuyên gia kế toán Việt Nam. 
Dựa vào nội dung hóa đơn dưới đây và yêu cầu của người dùng, hãy trích xuất và trình bày các thông tin sau dạng bảng Markdown:

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

YÊU CẦU CỦA NGƯỜI DÙNG: {query}

NỘI DUNG HÓA ĐƠN:
{context}
"""

def invoice_summary_tool(query: str, vector_store: Chroma, bm25_retriever=None) -> str:
    """
    Tóm tắt chi tiết một hóa đơn từ vector store.
    """
    # 1. Trích xuất filter từ query
    my_filter = extract_metadata_filter(query, vector_store)

    # 2. Truyền filter vào hàm retrieve
    docs = retrieve(vector_store, query, k=5, metadata_filter=my_filter, bm25_retriever=bm25_retriever)

    # 3. CƠ CHẾ FALLBACK: Nếu filter quá khắt khe, thử tìm lại không dùng filter
    if not docs and my_filter:
        print("⚠️ Filter quá chặt không tìm thấy tài liệu, đang tìm lại không dùng filter...")
        docs = retrieve(vector_store, query, k=5, metadata_filter=None, bm25_retriever=bm25_retriever)

    if not docs:
        return "❌ Không tìm thấy hóa đơn phù hợp trong tài liệu đã upload. Hãy chắc chắn bạn đã cung cấp mã hoặc tên tài liệu hợp lệ."
    
    context, _ = format_context(docs)
    
    # In ra Terminal để bạn dễ dàng kiểm soát dữ liệu
    print("=== DỮ LIỆU ĐƯỢC KÉO LÊN CHO LLM ĐỌC ===")
    print([doc.metadata for doc in docs])
    
    # Đưa cả query và context vào prompt
    prompt = INVOICE_SUMMARY_PROMPT.format(query=query, context=context)

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])

    return response.content