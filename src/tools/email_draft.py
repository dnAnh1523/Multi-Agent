"""
email_draft.py - Tool soạn email chuyên nghiệp liên quan đến hóa đơn
"""

from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage
from src.rag.retriever import retrieve, format_context
from src.agents.planner import get_llm

EMAIL_DRAFT_PROMPT = """Bạn là chuyên gia kế toán Việt Nam, soạn email chuyên nghiệp.
Dựa vào thông tin hóa đơn dưới đây và yêu cầu của người dùng, hãy soạn một email hoàn chỉnh.

Email phải có đầy đủ:
- Tiêu đề (Subject)
- Lời chào
- Nội dung chính (đề cập số hóa đơn, số tiền, hạn thanh toán nếu có)
- Lời kết
- Chữ ký (Phòng Kế toán)

Yêu cầu:
- Ngôn ngữ: tiếng Việt, lịch sự, chuyên nghiệp
- Phong cách: đúng chuẩn nghiệp vụ kế toán Việt Nam
- Trình bày rõ ràng, dễ đọc

YÊU CẦU CỦA NGƯỜI DÙNG: {query}

THÔNG TIN HÓA ĐƠN:
{context}
"""


def email_draft_tool(query: str, vector_store: Chroma) -> str:
    """
    Soạn email chuyên nghiệp dựa trên thông tin hóa đơn.

    Args:
        query: yêu cầu của user (ví dụ: "soạn email nhắc nợ hóa đơn 001")
        vector_store: Chroma instance đã có documents

    Returns:
        str: email draft hoàn chỉnh
    """
    docs = retrieve(vector_store, query, k=3)

    if not docs:
        return "❌ Không tìm thấy thông tin hóa đơn để soạn email."

    context = format_context(docs)
    prompt = EMAIL_DRAFT_PROMPT.format(query=query, context=context)

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])

    return response.content