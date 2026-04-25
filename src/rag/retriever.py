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
    Tự động chọn hybrid hoặc semantic tùy vào filter.
    """
    # CHẶN BM25 KHI CÓ FILTER: Chỉ dùng Semantic (Chroma)
    if metadata_filter is not None:
        retriever = get_retriever(vector_store, k, metadata_filter)
        print(f"🔍 Dùng Semantic Retrieval (vì có filter: {metadata_filter})")
        
    # NẾU KHÔNG CÓ FILTER: Cho phép chạy Hybrid (BM25 + Semantic) bình thường
    elif bm25_retriever is not None:
        retriever = get_hybrid_retriever(
            vector_store, bm25_retriever, k, metadata_filter=None
        )
        print("🔀 Dùng Hybrid Retrieval (BM25 + Semantic)")
        
    # FALLBACK Cuối cùng
    else:
        retriever = get_retriever(vector_store, k, metadata_filter=None)
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
# METADATA FILTER EXTRACTION (DYNAMIC ENTITY MAPPING)
# -----------------------------------------------

def get_valid_sources(vector_store: Chroma) -> list[str]:
    """Tự động quét Vector DB để lấy danh sách tất cả các tên file hiện có."""
    try:
        metadatas = vector_store.get()["metadatas"]
        if metadatas:
            # Dùng set để loại bỏ các tên file trùng lặp
            return list(set(m.get("source") for m in metadatas if m.get("source")))
    except Exception as e:
        print(f"⚠️ Lỗi khi lấy danh sách source từ Chroma: {e}")
    return []

def extract_metadata_filter(query: str, vector_store: Chroma) -> dict | None:
    # 1. Lấy danh sách file thực tế đang có trong DB
    valid_sources = get_valid_sources(vector_store)
    if not valid_sources:
        return None
    
    # 2. Tạo chuỗi danh sách để nhét vào prompt
    sources_str = "\n".join([f"- {s}" for s in valid_sources])

    # 3. Định nghĩa Pydantic Model ĐỘNG (nằm ngay trong hàm)
    class DocumentFilterParams(BaseModel):
        exact_source: Optional[str] = Field(
            description=f"""Ánh xạ yêu cầu của người dùng thành tên file chính xác.
CHỈ ĐƯỢC PHÉP trả về 1 trong các giá trị sau đây:
{sources_str}
Nếu người dùng không nhắc đến tài liệu cụ thể nào trong danh sách trên, trả về null.""",
            default=None,
        )

    llm = get_llm()
    structured_llm = llm.with_structured_output(DocumentFilterParams)
    try:
        result = structured_llm.invoke(query)
        if result and result.exact_source:
            print(f"🎯 LLM đã map thành công sang source: {result.exact_source}")
            return {"source": {"$eq": result.exact_source}}
    except Exception as e:
        print(f"⚠️ Lỗi trích xuất filter: {e}")
    return None

def extract_compare_filters(query: str, vector_store: Chroma) -> dict | None:
    valid_sources = get_valid_sources(vector_store)
    if not valid_sources:
        return None
        
    sources_str = "\n".join([f"- {s}" for s in valid_sources])

    class CompareFilterParams(BaseModel):
        exact_sources: List[str] = Field(
            description=f"""Danh sách tên các tài liệu cần so sánh.
CHỈ ĐƯỢC PHÉP chọn từ các giá trị sau:
{sources_str}
Trả về danh sách rỗng [] nếu không xác định được tài liệu.""",
            default_factory=list,
        )

    llm = get_llm()
    structured_llm = llm.with_structured_output(CompareFilterParams)
    try:
        result = structured_llm.invoke(query)
        if result and len(result.exact_sources) > 0:
            filters = [{"source": {"$eq": src}} for src in result.exact_sources]
            if len(filters) >= 2:
                return {"$or": filters}
            elif len(filters) == 1:
                return filters[0]
    except Exception as e:
        print(f"⚠️ Lỗi trích xuất filter so sánh: {e}")
    return None