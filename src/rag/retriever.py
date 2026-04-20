"""
retriever.py - Retrieval từ Vector Store
Nhận câu hỏi, tìm chunks liên quan, trả về kèm citation metadata.
"""

from langchain_chroma import Chroma
from langchain_core.documents import Document


def get_retriever(vector_store: Chroma, k: int = 5):
    """
    Tạo retriever từ vector store.
    Dùng MMR để lấy kết quả đa dạng, tránh chunks lặp lại.

    Args:
        vector_store: Chroma instance đã có documents
        k: số chunks muốn lấy về (default 5)

    Returns:
        VectorStoreRetriever: retriever sẵn sàng để invoke
    """
    # TODO: gọi vector_store.as_retriever() với:
    #   search_type = "mmr"
    #   search_kwargs = {"k": k, "fetch_k": k * 2}
    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": k * 2}
    )
    return retriever


def retrieve(
    vector_store: Chroma,
    query: str,
    k: int = 5,
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
    # TODO:
    # 1. Gọi get_retriever(vector_store, k)
    # 2. Gọi retriever.invoke(query)
    # 3. Return kết quả
    retriever = get_retriever(vector_store, k)
    return retriever.invoke(query)


def format_context(documents: list[Document]) -> str:
    """
    Format list Documents thành 1 string context để đưa vào LLM prompt.
    Mỗi chunk được đánh số và kèm citation.

    Args:
        documents: list Documents từ retrieve()

    Returns:
        str: context đã format, ví dụ:
            [1] (hoadon_001.pdf - Trang 1):
            Nội dung chunk...

            [2] (hoadon_002.pdf - Trang 2):
            Nội dung chunk...
    """
    if not documents:
        return "Không tìm thấy thông tin liên quan trong tài liệu đã upload."

    # TODO: dùng vòng lặp enumerate(documents, 1) để đánh số từ 1
    # Mỗi chunk format thành:
    #   f"[{i}] ({doc.metadata['source']} - Trang {doc.metadata['page']}):\n{doc.page_content}"
    # Các chunk cách nhau bằng "\n\n"
    # Gợi ý: dùng list comprehension rồi "\n\n".join(...)
    return "\n\n".join(
        f"[{i}] ({doc.metadata['source']} - Trang {doc.metadata['page']}):\n{doc.page_content}"
        for i, doc in enumerate(documents, 1)
    )


def get_citations(documents: list[Document]) -> list[dict]:
    """
    Trích xuất citation info từ list Documents.
    Dùng để hiển thị nguồn tham khảo trong UI.

    Args:
        documents: list Documents từ retrieve()

    Returns:
        list[dict]: ví dụ [{"source": "hoadon_001.pdf", "page": 1}, ...]
    """
    # TODO: dùng list comprehension
    # Mỗi phần tử là dict với key "source" và "page" từ doc.metadata
    # Dùng dict() để tránh duplicate nếu cùng source+page
    citations_dict = {
        (doc.metadata.get("source"), doc.metadata.get("page")): {
            "source": doc.metadata.get("source"),
            "page": doc.metadata.get("page")
        }
        for doc in documents
    }
    
    # Lấy toàn bộ values của dict và chuyển lại thành list
    return list(citations_dict.values())