"""
executor.py - Executor Agent
Thực thi action dựa trên intent từ Planner.
"""

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_chroma import Chroma
from src.agents.planner import get_llm
from src.rag.retriever import retrieve, format_context, get_citations
from src.config import FAITHFULNESS_THRESHOLD

EXECUTOR_SYSTEM_PROMPT = """Bạn là trợ lý kế toán thông minh cho doanh nghiệp Việt Nam.
Trả lời bằng tiếng Việt, chính xác, dựa trên context được cung cấp.
Nếu không tìm thấy thông tin trong context, hãy nói rõ thay vì đoán.
Luôn trích dẫn nguồn tài liệu khi trả lời."""


def make_executor(vector_store: Chroma):
    """
    Factory function tạo executor_node với vector_store đã được bind.
    Dùng closure để truyền vector_store vào node mà không vi phạm
    signature (state: dict) -> dict của LangGraph.
    """

    def executor_node(state: dict) -> dict:
        """
        Node function cho Executor Agent.
        Đọc intent từ state, thực thi action phù hợp,
        trả về dict update state.
        """
        intent = state.get("intent", "general")
        messages = state.get("messages", [])

        # Lấy câu hỏi cuối của user
        last_message = messages[-1].content if messages else ""

        print(f"⚙️ Executor xử lý intent: {intent}")

        # -----------------------------------------------
        # Routing dựa trên intent
        # -----------------------------------------------
        if intent == "stop":
            answer = "Tôi đã xử lý quá nhiều bước. Vui lòng thử lại với câu hỏi cụ thể hơn."
            return {
                "messages": [AIMessage(content=answer)],
                "tool_output": answer,
            }

        elif intent == "general":
            # TODO: gọi LLM trực tiếp không cần context
            # llm.invoke([SystemMessage(...), HumanMessage(content=last_message)])
            # Trả về {"messages": [AIMessage(content=response.content)]}
            llm = get_llm()
            response = llm.invoke([
                SystemMessage(content=EXECUTOR_SYSTEM_PROMPT),
                HumanMessage(content=last_message)
            ])
            return {"messages": [AIMessage(content=response.content)]}

        elif intent == "retrieve":
            docs = retrieve(vector_store, last_message, k=5)
            context = format_context(docs)
            citations = get_citations(docs)

            # Gộp context vào 1 message duy nhất, có hướng dẫn trích dẫn
            prompt = f"""Dựa vào các tài liệu sau, trả lời câu hỏi bằng tiếng Việt.
            Trích dẫn số thứ tự [1], [2]... khi dùng thông tin từ tài liệu đó.
            Nếu không tìm thấy thông tin, hãy nói rõ thay vì đoán.

            {context}

            Câu hỏi: {last_message}"""

            llm = get_llm()
            response = llm.invoke([HumanMessage(content=prompt)])
    
            return {
                "messages": [AIMessage(content=response.content)],
                "context": [context],   # list[str] không phải str
                "citations": citations,
            }


        elif intent == "invoice_summary":
            from src.tools.invoice_summary import invoice_summary_tool
            result = invoice_summary_tool(last_message, vector_store)
            return {"messages": [AIMessage(content=result)], "tool_output": result}

        elif intent == "email_draft":
            from src.tools.email_draft import email_draft_tool
            result = email_draft_tool(last_message, vector_store)
            return {"messages": [AIMessage(content=result)], "tool_output": result}

        elif intent == "web_search":
            # TODO: import và gọi web_search_tool(last_message)
            pass

        elif intent == "compare":
            # TODO: import và gọi compare_tool(last_message, vector_store)
            pass

        # Fallback nếu intent không khớp case nào
        answer = "Xin lỗi, tôi không thể xử lý yêu cầu này."
        return {"messages": [AIMessage(content=answer)]}

    return executor_node