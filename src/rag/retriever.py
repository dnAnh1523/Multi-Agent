"""
retriever.py - Retrieval từ Vector Store
Nhận câu hỏi, tìm chunks liên quan, trả về kèm citation metadata.
Hỗ trợ Hybrid Retrieval: BM25 (keyword) + Chroma MMR (semantic).
"""

import re
import unicodedata

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from pydantic import BaseModel, Field
from typing import Optional, List
from src.utils.llm import get_llm


# -----------------------------------------------
# SEMANTIC RETRIEVER (Chroma MMR)
# -----------------------------------------------

def get_retriever(vector_store: Chroma, k: int = 5, metadata_filter: dict = None):
    """
    Tạo semantic retriever từ Chroma vector store.
    Dùng MMR để lấy kết quả đa dạng, tránh chunks lặp lại.
    """
    search_kwargs = {"k": k, "fetch_k": k * 2}
    if metadata_filter:
        search_kwargs["filter"] = metadata_filter

    return vector_store.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs,
    )


# -----------------------------------------------
# BM25 RETRIEVER (Keyword)
# -----------------------------------------------

def build_bm25_retriever(documents: list[Document]) -> BM25Retriever:
    """
    Build BM25 index từ toàn bộ documents.
    Gọi 1 lần khi khởi động và rebuild khi có document mới.

    Args:
        documents: toàn bộ documents đã load

    Returns:
        BM25Retriever: retriever đã build index sẵn sàng để cache
    """
    retriever = BM25Retriever.from_documents(documents)
    return retriever


# -----------------------------------------------
# HYBRID RETRIEVER (BM25 + Semantic)
# -----------------------------------------------

def get_hybrid_retriever(
    vector_store: Chroma,
    bm25_retriever: BM25Retriever,
    k: int = 5,
    metadata_filter: dict = None,
    bm25_weight: float = 0.4,
    semantic_weight: float = 0.6,
) -> EnsembleRetriever:
    """
    Tạo hybrid retriever kết hợp BM25 + Chroma MMR.
    Dùng Reciprocal Rank Fusion (RRF) để merge kết quả.

    Args:
        vector_store: Chroma instance
        bm25_retriever: BM25Retriever đã build sẵn (từ cache)
        k: số chunks muốn lấy về
        metadata_filter: Chroma metadata filter nếu có
        bm25_weight: trọng số BM25 (default 0.4)
        semantic_weight: trọng số semantic (default 0.6)

    Returns:
        EnsembleRetriever: hybrid retriever sẵn sàng invoke
    """
    # Cập nhật k cho BM25
    bm25_retriever.k = k

    # Semantic retriever
    semantic_retriever = get_retriever(vector_store, k, metadata_filter)

    return EnsembleRetriever(
        retrievers=[bm25_retriever, semantic_retriever],
        weights=[bm25_weight, semantic_weight],
    )


# -----------------------------------------------
# RETRIEVE (entry point chính)
# -----------------------------------------------

def retrieve(
    vector_store: Chroma,
    query: str,
    k: int = 5,
    metadata_filter: dict = None,
    bm25_retriever: BM25Retriever = None,
) -> list[Document]:
    """
    Tìm kiếm chunks liên quan đến câu hỏi.
    Tự động chọn hybrid hoặc semantic tùy vào bm25_retriever.

    Args:
        vector_store: Chroma instance
        query: câu hỏi của user
        k: số chunks muốn lấy
        metadata_filter: filter theo metadata nếu có
        bm25_retriever: nếu có → dùng hybrid, không có → fallback semantic

    Returns:
        list[Document]: chunks liên quan có metadata đầy đủ
    """
    if bm25_retriever is not None:
        retriever = get_hybrid_retriever(
            vector_store, bm25_retriever, k, metadata_filter
        )
        print("🔀 Dùng Hybrid Retrieval (BM25 + Semantic)")
    else:
        retriever = get_retriever(vector_store, k, metadata_filter)
        print("🔍 Dùng Semantic Retrieval (fallback)")

    return retriever.invoke(query)


# -----------------------------------------------
# FORMAT CONTEXT & CITATION MAP
# -----------------------------------------------

def format_context(documents: list[Document]) -> tuple[str, dict]:
    """
    Format list Documents thành context string và citation_map.

    Returns:
        tuple: (context_str, citation_map)
        context_str: dùng raw_id làm label
        citation_map: {raw_id: {source, page, type}}
    """
    if not documents:
        return "Không tìm thấy thông tin liên quan.", {}

    context_parts = []
    citation_map = {}

    for doc in documents:
        raw_id = doc.metadata.get("raw_id", "rag_unknown")
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", 1)

        context_parts.append(
            f"[{raw_id}] ({source} - Trang {page}):\n{doc.page_content}"
        )
        citation_map[raw_id] = {
            "source": source,
            "page": page,
            "type": "document",
        }

    return "\n\n".join(context_parts), citation_map


# -----------------------------------------------
# METADATA FILTER EXTRACTION
# -----------------------------------------------

def clean_doc_id(text: str) -> str:
    """Chuẩn hóa chuỗi trích xuất từ LLM thành ID dùng để filter."""
    if not text:
        return ""
    numbers = re.findall(r'\d+', text)
    if numbers:
        return numbers[0]
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return normalized.lower().replace(" ", "_")


class DocumentFilterParams(BaseModel):
    doc_id: Optional[str] = Field(
        description="Mã số hoặc tên tài liệu cần trích xuất (ví dụ: '001', 'báo cáo tài chính').",
        default=None,
    )


def extract_metadata_filter(query: str) -> dict | None:
    llm = get_llm()
    structured_llm = llm.with_structured_output(DocumentFilterParams)
    try:
        result = structured_llm.invoke(query)
        if result and result.doc_id:
            cleaned_id = clean_doc_id(result.doc_id)
            if cleaned_id:
                print(f"🎯 Đã trích xuất doc_id để lọc: {cleaned_id}")
                return {"source": {"$contains": cleaned_id}}
    except Exception as e:
        print(f"⚠️ Lỗi trích xuất filter: {e}")
    return None


class CompareFilterParams(BaseModel):
    doc_ids: List[str] = Field(
        description="Danh sách mã hóa đơn hoặc tên chứng từ (ví dụ: ['001', '002']).",
        default_factory=list,
    )


def extract_compare_filters(query: str) -> dict | None:
    llm = get_llm()
    structured_llm = llm.with_structured_output(CompareFilterParams)
    try:
        result = structured_llm.invoke(query)
        if result and len(result.doc_ids) > 0:
            filters = []
            for d_id in result.doc_ids:
                cleaned_id = clean_doc_id(d_id)
                if cleaned_id:
                    filters.append({"source": {"$contains": cleaned_id}})
            if len(filters) >= 2:
                return {"$or": filters}
            elif len(filters) == 1:
                return filters[0]
    except Exception as e:
        print(f"⚠️ Lỗi trích xuất filter so sánh: {e}")
    return None