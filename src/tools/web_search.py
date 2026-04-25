"""
web_search.py - Tool tra cứu luật thuế và thông tin kế toán mới nhất
Dùng Tavily Search API để tìm thông tin real-time từ các nguồn đáng tin cậy.
"""

from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage
from src.agents.planner import get_llm
from src.config import TAVILY_API_KEY
from urllib.parse import urlparse
import re

def make_web_id(url: str, index: int) -> str:
    """
    Tạo descriptive raw ID từ domain + số thứ tự.
    Ví dụ: "https://thuvienphapluat.vn/..." + 1 → "web_thuvienphapluat_vn_01"
    """
    domain = urlparse(url).netloc.replace("www.", "")
    # Normalize domain: thay dấu chấm bằng underscore
    domain_id = re.sub(r'[^a-z0-9]', '_', domain.lower())
    domain_id = re.sub(r'_+', '_', domain_id).strip('_')
    return f"web_{domain_id}_{index:02d}"

DOMAIN_MAP = {
    "thuvienphapluat.vn": "Thư viện Pháp luật",
    "gdt.gov.vn": "Tổng cục Thuế",
    "mof.gov.vn": "Bộ Tài chính",
}

def web_search_tool(query: str) -> tuple[str, dict]:
    """
    Tìm kiếm thông tin luật thuế, chính sách kế toán mới nhất.

    Returns:
        tuple: (answer_str, citation_map)
    """
    if not TAVILY_API_KEY:
        return "❌ Chưa cấu hình TAVILY_API_KEY.", {}

    search = TavilySearch(
        max_results=5,
        topic="general",
        include_domains=["tongcucthuế.gov.vn", "thuvienphapluat.vn",
                         "mof.gov.vn", "gdt.gov.vn"]
    )

    raw_results = search.invoke({"query": query})
    results = raw_results.get("results", [])

    if not results:
        return "❌ Không tìm thấy thông tin liên quan trên web.", {}

    # --- THAY ĐỔI: dùng raw_id thay vì [1],[2] ---
    citation_map = {}
    formatted = []

    for i, r in enumerate(results, 1):
        title = r.get("title", "Không có tiêu đề")
        url = r.get("url", "")
        content = r.get("content", "")[:500]

        raw_id = make_web_id(url, i)
        domain = urlparse(url).netloc.replace("www.", "")
        org = DOMAIN_MAP.get(domain, domain)

        # Format context với raw_id làm label
        formatted.append(f"[{raw_id}] {title}\nNguồn: {url}\n{content}")

        # Build citation_map
        citation_map[raw_id] = {
            "title": title,
            "url": url,
            "org": org,
            "type": "web"
        }

    search_context = "\n\n".join(formatted)

    # --- THAY ĐỔI: prompt dùng raw_id thay vì số ---
    prompt = f"""Dựa vào các kết quả tìm kiếm sau, hãy trả lời câu hỏi bằng tiếng Việt.
Khi trích dẫn, dùng đúng ID trong ngoặc vuông như [web_thuvienphapluat_vn_01].
Nếu một câu dùng nhiều nguồn, liệt kê tất cả IDs trong cùng 1 ngoặc, phân cách bằng dấu phẩy.
Ví dụ: [web_thuvienphapluat_vn_01, web_gdt_gov_vn_02]
KHÔNG tạo ID mới ngoài danh sách trên.
Ưu tiên thông tin từ các nguồn chính thống (Tổng cục Thuế, Bộ Tài chính).

KẾT QUẢ TÌM KIẾM:
{search_context}

CÂU HỎI: {query}"""

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])

    # --- THAY ĐỔI: return tuple thay vì str ---
    return response.content, citation_map