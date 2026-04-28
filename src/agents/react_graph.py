# Toàn bộ file react_graph_thought.py (thay thế)
import logging
from typing import AsyncIterator, Literal, Any, Dict
from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, SystemMessage, BaseMessage
from langchain_core.runnables import RunnableConfig

from src.utils.llm import get_llm
from src.rag.retriever import retrieve, format_context
from src.tools.invoice_summary import invoice_summary_tool
from src.tools.email_draft import email_draft_tool
from src.tools.web_search import web_search_tool
from src.tools.compare import compare_tool
from src.config import LANGGRAPH_THREAD_ID

logger = logging.getLogger(__name__)

class ReActState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    thoughts: list[str]
    citation_map: dict

SYSTEM_PROMPT = """Bạn là Trợ lý AI Kế toán thông minh, chuyên nghiệp.

### Quy tắc xuất bước suy nghĩ (thought):
Trước KHI gọi một công cụ hoặc trả lời, bạn PHẢI ghi ra một dòng bắt đầu bằng "Thought: " (có dấu hai chấm và khoảng trắng). Dòng này sẽ được hiển thị cho người dùng thấy như một bước suy nghĩ. Nội dung sau "Thought: " giải thích bạn đang làm gì và tại sao.

Ví dụ:
Thought: Người dùng muốn tóm tắt hóa đơn 001, tôi sẽ gọi tom_tat_hoa_don.
<< sau đó gọi tool >>

Thought: Kết quả từ tool đã có, tôi sẽ trả về bảng.
<< sau đó trả lời >>

### Các công cụ có sẵn:
- tim_kiem_chung_tu(query): tìm kiếm nội dung trong tài liệu đã upload
- tom_tat_hoa_don(query): tóm tắt hóa đơn thành bảng
- soan_email_ke_toan(query): soạn email
- so_sanh_tai_lieu(query): so sánh hai tài liệu
- tra_cuu_luat_thue_internet(query): tra cứu luật thuế trên web

Hãy suy nghĩ step by step và thể hiện bằng các dòng "Thought: ".
"""

def build_react_graph(vector_store, bm25_retriever=None, checkpointer=None):
    llm = get_llm()
    tools = [
        {"name": "tim_kiem_chung_tu", "description": "Tìm kiếm thông tin trong chứng từ, hóa đơn đã upload.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
        {"name": "tom_tat_hoa_don", "description": "Tóm tắt chi tiết một tờ hóa đơn thành bảng.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
        {"name": "soan_email_ke_toan", "description": "Soạn email liên quan đến hóa đơn.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
        {"name": "so_sanh_tai_lieu", "description": "So sánh hai tài liệu/hóa đơn.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
        {"name": "tra_cuu_luat_thue_internet", "description": "Tra cứu luật thuế, thông tư trên internet.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    ]
    llm_with_tools = llm.bind_tools(tools)

    async def think_node(state: ReActState, config: RunnableConfig = None):
        messages = state["messages"]
        response = await llm_with_tools.ainvoke(
            [SystemMessage(content=SYSTEM_PROMPT)] + messages,
            config=config
        )
        content = response.content
        thought_lines = []
        clean_lines = []
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.lower().startswith('thought:'):
                thought_lines.append(stripped[8:].strip())
            else:
                clean_lines.append(line)
        clean_content = '\n'.join(clean_lines).strip()
        if not thought_lines and not response.tool_calls:
            thought_lines.append(content)
            clean_content = ""

        # Quan trọng: nếu có tool_calls, content sẽ rỗng để không hiển thị "Thought:" 
        final_content = "" if response.tool_calls else clean_content
        cleaned_message = AIMessage(
            content=final_content,
            tool_calls=response.tool_calls,
            response_metadata=response.response_metadata,
        )
        old_thoughts = state.get("thoughts", [])
        return {
            "messages": [cleaned_message],
            "thoughts": old_thoughts + thought_lines
        }

    async def call_tool(tool_name: str, tool_args: dict):
        query = tool_args["query"]
        if tool_name == "tim_kiem_chung_tu":
            docs = retrieve(vector_store, query, k=5, bm25_retriever=bm25_retriever)
            context, citation = format_context(docs)
            return context, citation
        elif tool_name == "tom_tat_hoa_don":
            return invoice_summary_tool(query, vector_store, bm25_retriever)
        elif tool_name == "soan_email_ke_toan":
            result = email_draft_tool(query, vector_store, bm25_retriever)
            return result, {}
        elif tool_name == "so_sanh_tai_lieu":
            return compare_tool(query, vector_store, bm25_retriever)
        elif tool_name == "tra_cuu_luat_thue_internet":
            return web_search_tool(query)
        else:
            return f"Tool {tool_name} không tồn tại.", {}

    async def act_node(state: ReActState):
        last_msg = state["messages"][-1]
        if not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
            return {"messages": []}
        tool_messages = []
        current_citation = state.get("citation_map", {}).copy()
        for tool_call in last_msg.tool_calls:
            content, new_citation = await call_tool(tool_call["name"], tool_call["args"])
            current_citation.update(new_citation)
            tool_messages.append(ToolMessage(content=content, tool_call_id=tool_call["id"]))
        return {"messages": tool_messages, "citation_map": current_citation}

    def should_continue(state: ReActState) -> Literal["act", "end"]:
        last_msg = state["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "act"
        return "end"

    builder = StateGraph(ReActState)
    builder.add_node("think", think_node)
    builder.add_node("act", act_node)
    builder.add_edge(START, "think")
    builder.add_conditional_edges("think", should_continue, {"act": "act", "end": END})
    builder.add_edge("act", "think")
    if checkpointer is None:
        checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)

async def chat_stream(graph, user_message: str, thread_id: str = LANGGRAPH_THREAD_ID):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        async for event in graph.astream_events(
            {"messages": [HumanMessage(content=user_message)]},
            config=config,
            version="v2"
        ):
            if event["event"] == "on_chain_stream" and event.get("name") == "think":
                chunk_data = event["data"]["chunk"]
                if "thoughts" in chunk_data and chunk_data["thoughts"]:
                    for thought in chunk_data["thoughts"]:
                        yield {"type": "thought", "content": thought}
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield {"type": "token", "content": chunk.content}
            if event["event"] == "on_chain_end" and event.get("name") == "LangGraph":
                state = event["data"]["output"]
                citation_map = state.get("citation_map", {})
                if citation_map:
                    yield {"type": "citation_map", "map": citation_map}
    except Exception as e:
        logger.error(f"Lỗi streaming: {e}")
        yield {"type": "token", "content": f"[Lỗi: {str(e)}]"}

def chat(graph, user_message: str, thread_id: str = LANGGRAPH_THREAD_ID) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke({"messages": [HumanMessage(content=user_message)]}, config=config)
    return {"messages": result["messages"], "citation_map": result.get("citation_map", {})}