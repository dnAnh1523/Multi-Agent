"""
compare.py - Tool so sánh dữ liệu giữa 2 hóa đơn hoặc 2 báo cáo
"""

import re
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage
from src.rag.retriever import retrieve, format_context
from src.agents.planner import get_llm

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


def compare_tool(query: str, vector_store: Chroma) -> str:
    """
    So sánh dữ liệu giữa 2 hóa đơn hoặc 2 báo cáo.

    Args:
        query: yêu cầu so sánh (ví dụ: "so sánh hóa đơn 001 và 002")
        vector_store: Chroma instance đã có documents

    Returns:
        str: bảng so sánh Markdown kèm nhận xét
    """
    # k=4 để đảm bảo lấy được chunks từ cả 2 tài liệu
    docs = retrieve(vector_store, query, k=4)  # TODO: sửa k nếu cần thiết

    if not docs:
        return "❌ Không tìm thấy tài liệu phù hợp để so sánh."

    # Kiểm tra có đủ 2 nguồn khác nhau không
    sources = list(set(doc.metadata.get("source", "") for doc in docs))
    if len(sources) < 2:
        return f"❌ Chỉ tìm thấy 1 tài liệu ({sources[0]}). Cần ít nhất 2 tài liệu để so sánh."

    context = format_context(docs)
    prompt = COMPARE_PROMPT.format(query=query, context=context)

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])

    used_sources = []
    for doc in docs:
        source = doc.metadata.get("source", "")
        # Lấy số hóa đơn từ content của doc (ví dụ: 0000001, 0000002)
        # Nếu số đó xuất hiện trong response → doc này được dùng để so sánh
        invoice_numbers = re.findall(r'\d{7}', doc.page_content)
        for num in invoice_numbers:
            if num in response.content and source not in used_sources:
                used_sources.append(source)

    # Fallback nếu không detect được
    display_sources = used_sources if used_sources else sources
    sources_text = "\n".join([f"- {s}" for s in display_sources])
    return f"{response.content}\n\n---\n**Tài liệu được so sánh:**\n{sources_text}"