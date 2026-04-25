"""
retriever.py - Retrieval từ Vector Store
Nhận câu hỏi, tìm chunks liên quan, trả về kèm citation metadata.
"""

from langchain_chroma import Chroma
from langchain_core.documents import Document

from pydantic import BaseModel, Field
from typing import Optional, List
from src.agents.planner import get_llm

def get_retriever(vector_store: Chroma, k: int = 5, metadata_filter: dict = None):
    """
    Tạo retriever từ vector store.
    Dùng MMR để lấy kết quả đa dạng, tránh chunks lặp lại.

    Args:
        vector_store: Chroma instance đã có documents
        k: số chunks muốn lấy về (default 5)

    Returns:
        VectorStoreRetriever: retriever sẵn sàng để invoke
    """
    search_kwargs={"k": k, "fetch_k": k * 2}

    # Thêm filter nếu có truyền vào
    if metadata_filter:
        search_kwargs["filter"] = metadata_filter

    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs
    )
    return retriever


def retrieve(
    vector_store: Chroma,
    query: str,
    k: int = 5,
    metadata_filter: dict = None
) -> list[Document]:
    """
    Tìm kiếm chunks liên quan đến câu hỏi.

    Args:
        vector_store: Chroma instance
        query: câu hỏi của user
        k: số chunks muốn lấy

    Returns:
        list[Document]: chunks liên quan, mỗi chunk có metadata đầy đủ
    """
    retriever = get_retriever(vector_store, k, metadata_filter)
    return retriever.invoke(query)


def format_context(documents: list[Document]) -> tuple[str, dict]:
    """
    Format list Documents thành context string và citation_map.
    
    Returns:
        tuple: (context_str, citation_map)
        context_str: dùng raw_id làm label
        citation_map: {raw_id: {source, page, type}} để post-process
    """
    if not documents:
        return "Không tìm thấy thông tin liên quan.", {}

    context_parts = []
    citation_map = {}

    for doc in documents:
        raw_id = doc.metadata.get("raw_id", "rag_unknown")
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", 1)

        # Format context với raw_id làm label
        context_parts.append(
            f"[{raw_id}] ({source} - Trang {page}):\n{doc.page_content}"
        )

        # Build citation_map
        citation_map[raw_id] = {
            "source": source,
            "page": page,
            "type": "document"
        }

    return "\n\n".join(context_parts), citation_map


# Định nghĩa Schema cho LLM
class DocumentFilterParams(BaseModel):
    doc_id: Optional[str] = Field(
        description="Mã số hóa đơn, tên file, hoặc mã chứng từ trích xuất từ câu hỏi của user. Ví dụ: '001', '002', 'báo cáo tài chính'. Trả về null nếu không thấy con số hay tên cụ thể nào.",
        default=None
    )


def extract_metadata_filter(query: str) -> dict | None:
    """
    Dùng LLM để đọc câu hỏi và tạo metadata filter cho Chroma.
    """
    llm = get_llm()
    # Ép LLM trả về đúng schema DocumentFilterParams
    structured_llm = llm.with_structured_output(DocumentFilterParams)
    
    try:
        result = structured_llm.invoke(query)
        if result and result.doc_id:
            print(f"🎯 Đã trích xuất doc_id để lọc: {result.doc_id}")
            # Trả về dict filter đúng chuẩn của Chroma
            return {"source": {"$contains": result.doc_id}}
    except Exception as e:
        print(f"⚠️ Lỗi trích xuất filter: {e}")
        
    return None


class CompareFilterParams(BaseModel):
    doc_ids: List[str] = Field(
        description="Danh sách các mã hóa đơn, số chứng từ hoặc tên tài liệu cần được so sánh. Ví dụ: ['001', '002'].",
        default_factory=list
    )

def extract_compare_filters(query: str) -> dict | None:
    """
    Trích xuất danh sách ID và tạo filter $or cho Chroma.
    """
    llm = get_llm()
    structured_llm = llm.with_structured_output(CompareFilterParams)
    
    try:
        result = structured_llm.invoke(query)
        if result and len(result.doc_ids) >= 2:
            # Tạo toán tử $or để lấy được cả 2 (hoặc nhiều hơn) tài liệu
            # Cấu trúc của Chroma: {"$or": [{"field": {"$contains": "val1"}}, {"field": {"$contains": "val2"}}]}
            filters = []
            for d_id in result.doc_ids:
                filters.append({"source": {"$contains": d_id}})
            
            return {"$or": filters}
            
        elif result and len(result.doc_ids) == 1:
            # Nếu user chỉ nhắc 1 ID nhưng intent là compare, vẫn lọc theo ID đó
            return {"source": {"$contains": result.doc_ids[0]}}
            
    except Exception as e:
        print(f"⚠️ Lỗi trích xuất filter so sánh: {e}")
        
    return None