"""
compare.py - Tool so sánh dữ liệu giữa 2 hóa đơn hoặc 2 báo cáo
"""

import re
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage
from src.rag.retriever import retrieve, format_context, extract_compare_filters
from src.utils.llm import get_llm

COMPARE_PROMPT = """Bạn là chuyên gia kế toán Việt Nam.
Dựa vào nội dung các tài liệu dưới đây, hãy so sánh và trình bày kết quả dưới dạng bảng Markdown.

Bảng so sánh phải có các cột: Tiêu chí | Tài liệu 1 | Tài liệu 2
Các tiêu chí cần so sánh (nếu có):
- Số hóa đơn / Tên tài liệu
- Ngày lập
- Đơn vị bán / lập
- Đơn vị mua
- Tổng tiền hàng
- Thuế suất GTGT
- Tiền thuế GTGT
- Tổng thanh toán
- Hình thức thanh toán

Nếu không tìm thấy thông tin nào, ghi "Không có" vào ô tương ứng.
Sau bảng, thêm phần NHẬN XÉT ngắn gọn về sự khác biệt chính.

YÊU CẦU CỦA NGƯỜI DÙNG: {query}

NỘI DUNG TÀI LIỆU:
{context}
"""


def compare_tool(query: str, vector_store: Chroma, bm25_retriever=None) -> str:
    multi_filter = extract_compare_filters(query, vector_store)
    
    # Kéo k=6 chunk để đảm bảo đủ dữ liệu từ 2 file
    docs = retrieve(vector_store, query, k=6, metadata_filter=multi_filter, bm25_retriever=bm25_retriever)

    # THÊM FALLBACK MỚI: Nếu filter quá khắt khe không tìm thấy doc nào, bỏ filter đi tìm lại
    if not docs and multi_filter:
        print("⚠️ Filter quá chặt không tìm thấy tài liệu, đang tìm lại không dùng filter...")
        docs = retrieve(vector_store, query, k=6, metadata_filter=None, bm25_retriever=bm25_retriever)

    if not docs:
        return "❌ Không tìm thấy tài liệu phù hợp để so sánh. Hãy chắc chắn bạn đã cung cấp mã hóa đơn hoặc tên tệp chính xác."

    sources = list(set(doc.metadata.get("source", "") for doc in docs))
    
    if len(sources) < 2:
        return f"❌ Hệ thống chỉ tìm thấy thông tin từ một nguồn: {sources[0] if sources else 'không xác định'}. Vui lòng kiểm tra lại mã số các tài liệu cần so sánh."

    context, _ = format_context(docs) # Chỉ lấy context text, bỏ qua citation map ở tool con
    prompt = COMPARE_PROMPT.format(query=query, context=context)

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])

    used_sources = []
    for doc in docs:
        source = doc.metadata.get("source", "")
        invoice_numbers = re.findall(r'\d{7}', doc.page_content)
        for num in invoice_numbers:
            if num in response.content and source not in used_sources:
                used_sources.append(source)

    display_sources = used_sources if used_sources else sources
    sources_text = "\n".join([f"- {s}" for s in display_sources])
    
    return f"{response.content}\n\n---\n**Tài liệu được phân tích:**\n{sources_text}"