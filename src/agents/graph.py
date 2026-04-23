"""
graph.py - LangGraph StateGraph cho Multi-Agent System
Định nghĩa AgentState, build graph với Planner + Executor nodes.
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import BaseMessage
from langchain_chroma import Chroma

from src.agents.planner import planner_node
from src.agents.executor import make_executor
from src.config import LANGGRAPH_THREAD_ID


# -----------------------------------------------
# 1. Định nghĩa AgentState
# -----------------------------------------------
class AgentState(TypedDict):
    messages:    Annotated[list[BaseMessage], add_messages]
    intent:      str
    context:     list[str]
    citations:   list[dict]
    tool_output: str
    steps:       int


# -----------------------------------------------
# 2. Routing function — quyết định sau Planner đi đâu
# -----------------------------------------------
def route_after_planner(state: AgentState) -> str:
    """
    Đọc intent từ state, trả về key để conditional edge routing.
    "stop"     → kết thúc graph
    "continue" → chạy tiếp executor
    """
    if state["intent"] == "stop":
        return "stop"
    else:        
        return "continue"


# -----------------------------------------------
# 3. Build graph
# -----------------------------------------------
def build_graph(vector_store: Chroma):
    """
    Tạo và compile StateGraph với:
    - Node "planner": phân tích intent
    - Node "executor": thực thi action
    - InMemorySaver checkpointer: lưu conversation history

    Args:
        vector_store: Chroma instance đã có documents

    Returns:
        CompiledGraph: graph đã compile, sẵn sàng để invoke
    """
    executor_node = make_executor(vector_store)

    builder = StateGraph(AgentState)

    builder.add_node("planner", planner_node)
    builder.add_node("executor", executor_node)

    builder.add_edge(START, "planner")

    builder.add_conditional_edges(
        "planner",
        route_after_planner,
        {"stop": END, "continue": "executor"}
    )

    builder.add_edge("executor", END)

    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


# -----------------------------------------------
# 4. Helper để invoke graph
# -----------------------------------------------
def chat(graph, user_message: str, thread_id: str = LANGGRAPH_THREAD_ID) -> dict:
    """
    Gửi message vào graph và nhận kết quả.

    Args:
        graph: CompiledGraph từ build_graph()
        user_message: câu hỏi của user
        thread_id: ID của conversation (dùng cho checkpointer)

    Returns:
        dict: AgentState cuối cùng sau khi graph chạy xong
    """
    from langchain_core.messages import HumanMessage

    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(
        {"messages": [HumanMessage(content=user_message)]},
        config=config,
    )
    return result