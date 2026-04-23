"""
web_search.py - Tool tra cứu luật thuế và thông tin kế toán mới nhất
Dùng Tavily Search API để tìm thông tin real-time từ các nguồn đáng tin cậy.
"""

from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage
from src.agents.planner import get_llm
from src.config import TAVILY_API_KEY


def web_search_tool(query: str) -> str:
    """
    Tìm kiếm thông tin luật thuế, chính sách kế toán mới nhất.

    Args:
        query: câu hỏi của user về luật thuế/chính sách

    Returns:
        str: tổng hợp thông tin từ web kèm nguồn tham khảo
    """
    if not TAVILY_API_KEY:
        return "❌ Chưa cấu hình TAVILY_API_KEY. Vui lòng thêm vào file .env"

    # include_domains giúp ưu tiên nguồn đáng tin cậy về thuế VN
    search = TavilySearch(
        max_results=5,
        topic="general",
        include_domains=["tongcucthuế.gov.vn", "thuvienphapluat.vn",
                         "mof.gov.vn", "gdt.gov.vn"]
    )

    raw_results = search.invoke({"query": query})

    # Format kết quả thành string có nguồn rõ ràng
    results = raw_results.get("results", [])
    if not results:
        return "❌ Không tìm thấy thông tin liên quan trên web."

    # Format từng kết quả: tiêu đề + URL + nội dung
    formatted = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "Không có tiêu đề")
        url = r.get("url", "")
        content = r.get("content", "")[:500]  # giới hạn 500 ký tự mỗi kết quả
        formatted.append(f"[{i}] {title}\nNguồn: {url}\n{content}")

    search_context = "\n\n".join(formatted)

    prompt = f"""Dựa vào các kết quả tìm kiếm sau, hãy trả lời câu hỏi bằng tiếng Việt.
Trích dẫn số thứ tự nguồn [1], [2]... khi dùng thông tin đó.
Ưu tiên thông tin từ các nguồn chính thống (Tổng cục Thuế, Bộ Tài chính).

KẾT QUẢ TÌM KIẾM:
{search_context}

CÂU HỎI: {query}"""

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])

    # Tạo danh sách nguồn để append vào cuối câu trả lời
    source_list = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "Không có tiêu đề")
        url = r.get("url", "")
        source_list.append(f"[{i}] {title} — {url}")

    sources_text = "\n".join(source_list)

    return f"{response.content}\n\n---\n**Nguồn tham khảo:**\n{sources_text}"