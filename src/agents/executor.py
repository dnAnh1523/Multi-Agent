"""
executor.py - Executor Agent
Thực thi action dựa trên intent từ Planner.
Dùng resolved_query (đã rewrite) thay vì last_message thô.
Cập nhật working_memory sau mỗi lượt để Planner dùng cho lần sau.
"""

import re

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_chroma import Chroma
from src.utils.llm import get_llm
from src.rag.retriever import retrieve, format_context

EXECUTOR_SYSTEM_PROMPT = """Bạn là trợ lý kế toán thông minh cho doanh nghiệp Việt Nam.
Trả lời bằng tiếng Việt, chính xác, dựa trên context được cung cấp.
Nếu không tìm thấy thông tin trong context, hãy nói rõ thay vì đoán.
Luôn trích dẫn nguồn tài liệu khi trả lời."""


def _extract_invoice_number(text: str) -> str | None:
    """Trích xuất số hóa đơn 7 chữ số từ text nếu có."""
    nums = re.findall(r'\d{7}', text)
    return nums[0] if nums else None


def make_executor(vector_store: Chroma, bm25_retriever=None):
    """
    Factory function tạo executor_node với vector_store đã được bind.
    Dùng closure để truyền vector_store vào node mà không vi phạm
    signature (state: dict) -> dict của LangGraph.
    """

    def executor_node(state: dict) -> dict:
        intent         = state.get("intent", "general")
        messages       = state.get("messages", [])
        working_memory = state.get("working_memory", {})

        # last_message: nội dung thô của user (dùng cho general/web_search)
        last_message = messages[-1].content if messages else ""

        # resolved_query: đã được Planner rewrite dựa trên working_memory
        # Fallback về last_message nếu chưa có
        resolved_query = state.get("resolved_query") or last_message

        print(f"⚙️ Executor xử lý intent: {intent}")
        print(f"   resolved_query: {resolved_query}")

        # -----------------------------------------------
        # Routing dựa trên intent
        # -----------------------------------------------

        if intent == "stop":
            answer = "Tôi đã xử lý quá nhiều bước. Vui lòng thử lại với câu hỏi cụ thể hơn."
            return {
                "messages": [AIMessage(content=answer)],
                "tool_output": answer,
                "citation_map": {},
                "working_memory": working_memory,
            }

        elif intent == "general":
            llm = get_llm()
            response = llm.invoke([
                SystemMessage(content=EXECUTOR_SYSTEM_PROMPT),
                HumanMessage(content=last_message),
            ])
            return {
                "messages": [AIMessage(content=response.content)],
                "citation_map": {},
                "working_memory": working_memory,  # không thay đổi memory
            }

        elif intent == "retrieve":
            docs = retrieve(
                vector_store, resolved_query,
                k=5, bm25_retriever=bm25_retriever,
            )
            context, citation_map = format_context(docs)

            prompt_lines = [
                "Dựa vào các tài liệu sau, trả lời câu hỏi bằng tiếng Việt.",
                "Khi trích dẫn, dùng đúng ID trong ngoặc vuông như [rag_hoadon_001_p1].",
                "Nếu một câu dùng nhiều nguồn, liệt kê tất cả IDs trong cùng 1 ngoặc, phân cách bằng dấu phẩy.",
                "KHÔNG tạo ID mới ngoài danh sách trên.",
                "Nếu không tìm thấy thông tin, hãy nói rõ thay vì đoán.",
                "",
                context,
                "",
                f"Câu hỏi: {resolved_query}",
            ]
            prompt = "\n".join(prompt_lines)
            llm = get_llm()
            response = llm.invoke([HumanMessage(content=prompt)])

            new_memory = {**working_memory}
            new_memory["last_action"] = "retrieve"
            new_memory["last_query"]  = resolved_query

            return {
                "messages": [AIMessage(content=response.content)],
                "context": [context],
                "citation_map": citation_map,
                "working_memory": new_memory,
            }

        elif intent == "invoice_summary":
            from src.tools.invoice_summary import invoice_summary_tool
            result = invoice_summary_tool(resolved_query, vector_store, bm25_retriever)

            new_memory = {**working_memory}
            new_memory["last_action"] = "invoice_summary"
            new_memory["last_invoice_query"] = resolved_query
            inv_num = _extract_invoice_number(resolved_query)
            if inv_num:
                new_memory["current_invoice_number"] = inv_num

            return {
                "messages": [AIMessage(content=result)],
                "tool_output": result,
                "citation_map": {},
                "working_memory": new_memory,
            }

        elif intent == "email_draft":
            from src.tools.email_draft import email_draft_tool
            result = email_draft_tool(resolved_query, vector_store, bm25_retriever)

            new_memory = {**working_memory}
            new_memory["last_action"] = "email_draft"
            new_memory["last_email_query"] = resolved_query
            inv_num = _extract_invoice_number(resolved_query)
            if inv_num:
                new_memory["current_invoice_number"] = inv_num

            return {
                "messages": [AIMessage(content=result)],
                "tool_output": result,
                "citation_map": {},
                "working_memory": new_memory,
            }

        elif intent == "web_search":
            from src.tools.web_search import web_search_tool
            # web_search dùng last_message vì không cần context hóa đơn
            answer, citation_map = web_search_tool(last_message)

            new_memory = {**working_memory}
            new_memory["last_action"] = "web_search"
            new_memory["last_web_query"] = last_message

            return {
                "messages": [AIMessage(content=answer)],
                "tool_output": answer,
                "citation_map": citation_map,
                "working_memory": new_memory,
            }

        elif intent == "compare":
            from src.tools.compare import compare_tool
            result = compare_tool(resolved_query, vector_store, bm25_retriever)

            new_memory = {**working_memory}
            new_memory["last_action"] = "compare"
            new_memory["last_compare_query"] = resolved_query

            return {
                "messages": [AIMessage(content=result)],
                "tool_output": result,
                "citation_map": {},
                "working_memory": new_memory,
            }

        # Fallback
        answer = "Xin lỗi, tôi không thể xử lý yêu cầu này."
        return {
            "messages": [AIMessage(content=answer)],
            "working_memory": working_memory,
        }

    return executor_node