"""
planner.py - Planner Agent
Phân tích intent từ câu hỏi của user, quyết định action tiếp theo.
"""

from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from src.utils.llm import get_llm


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

def planner_node(state: dict) -> dict:
    # ❌ XÓA BỎ HOÀN TOÀN đoạn check MAX_AGENT_ITERATIONS
    # current_steps = state.get("steps", 0) ...
    
    messages = state.get("messages", [])
    if not messages:
        return {"intent": "general"}
    
    last_message = messages[-1].content.strip()
    if not last_message:
        return {"intent": "general"}

    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=last_message)
    ])

    intent = response.content.strip().lower()
    valid_intents = {"retrieve", "invoice_summary", "email_draft", "web_search", "compare", "general", "stop"}
    
    if intent not in valid_intents:
        intent = "retrieve"

    print(f"🎯 Planner quyết định: {intent}")
    return {"intent": intent} # 👈 Không trả về steps nữa