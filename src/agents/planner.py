"""
planner.py - Planner Agent
Phân tích intent từ câu hỏi của user, quyết định action tiếp theo.
"""

from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from functools import lru_cache

from src.config import (
    GROQ_API_KEY, GROQ_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    MAX_AGENT_ITERATIONS,
)

# --- System prompt cho Planner ---
PLANNER_SYSTEM_PROMPT = """Bạn là Planner Agent của hệ thống kế toán thông minh.
Nhiệm vụ của bạn là phân tích câu hỏi của người dùng và quyết định action phù hợp.

Chỉ trả về MỘT trong các giá trị sau (không giải thích thêm):
- "retrieve": câu hỏi cần tìm thông tin từ tài liệu đã upload
- "invoice_summary": yêu cầu tóm tắt chi tiết một hóa đơn cụ thể
- "email_draft": yêu cầu soạn email liên quan đến hóa đơn
- "web_search": câu hỏi về luật thuế, chính sách mới nhất cần tìm trên web
- "compare": yêu cầu so sánh 2 hóa đơn hoặc 2 báo cáo
- "general": câu hỏi chung, chào hỏi, không cần tool hay retriever

Ví dụ:
- "Hóa đơn số 001 có tổng tiền bao nhiêu?" → retrieve
- "Tóm tắt hóa đơn số 002" → invoice_summary
- "Soạn email nhắc nợ cho hóa đơn 001" → email_draft
- "Nghị định 123 mới nhất về thuế GTGT?" → web_search
- "So sánh hóa đơn 001 và 002" → compare
- "Xin chào" → general
"""

@lru_cache(maxsize=1)
def get_llm():
    """
    Khởi tạo LLM với fallback Groq → Ollama.
    Returns ChatGroq nếu có API key, ngược lại trả ChatOllama.
    """
    llm = None
    if GROQ_API_KEY:
        llm = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=0)
    else:
        llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
    return llm


def planner_node(state: dict) -> dict:
    """
    Node function cho Planner Agent trong LangGraph.
    Nhận State, phân tích intent, trả về dict update State.

    Args:
        state: AgentState hiện tại

    Returns:
        dict: chỉ chứa các field muốn update {"intent": ..., "steps": ...}
    """
    # Kiểm tra giới hạn vòng lặp (R-02: tránh infinite loop)
    current_steps = state.get("steps", 0)
    if current_steps >= MAX_AGENT_ITERATIONS:
        print(f"⚠️ Đã đạt giới hạn {MAX_AGENT_ITERATIONS} bước, dừng agent")
        return {"intent": "stop", "steps": current_steps}

    # Lấy câu hỏi mới nhất của user từ messages
    messages = state.get("messages", [])
    if not messages:
        return {"intent": "general", "steps": current_steps + 1}
    last_message = messages[-1].content.strip()
    if not last_message:
        return {"intent": "general", "steps": current_steps + 1}

    # Gọi LLM để phân tích intent
    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=last_message)
    ])

    # Parse intent từ response
    # response.content là string, cần strip() và lower()
    intent = response.content.strip().lower()

    # Validate — nếu LLM trả về giá trị lạ thì fallback về "retrieve"
    valid_intents = {
        "retrieve", "invoice_summary", "email_draft",
        "web_search", "compare", "general", "stop"
    }
    if intent not in valid_intents:
        print(f"⚠️ Intent không hợp lệ '{intent}', fallback về 'retrieve'")
        intent = "retrieve"

    print(f"🎯 Planner quyết định: {intent}")
    return {"intent": intent, "steps": current_steps + 1}