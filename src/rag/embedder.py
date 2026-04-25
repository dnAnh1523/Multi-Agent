"""
embedder.py - Embedding và Vector Store Management
Nhận Documents từ loader, tạo embeddings và lưu vào Chroma.
"""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import torch
from src.config import EMBEDDING_MODEL, CHROMA_PERSIST_DIR, CHROMA_MODE


def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Khởi tạo embedding model chạy local.
    Model sẽ tự download lần đầu (~130MB), cache lại cho lần sau.
    
    Returns:
        HuggingFaceEmbeddings: embedding model đã sẵn sàng
    """
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )


def get_vector_store(embedding: HuggingFaceEmbeddings) -> Chroma:
    """
    Load Chroma vector store từ disk nếu đã tồn tại.
    Tạo mới (rỗng) nếu chưa có.
    
    Args:
        embedding: embedding model đã khởi tạo
        
    Returns:
        Chroma: vector store sẵn sàng để add/search documents
    """
    if CHROMA_MODE == "memory":
        return Chroma(embedding_function=embedding, collection_name="accounting_docs")
        
    else:
        return Chroma(embedding_function=embedding, persist_directory=CHROMA_PERSIST_DIR, collection_name="accounting_docs")


def make_doc_id(source: str, page: int) -> str:
    return f"{source}::page_{page}"


def add_documents(vector_store: Chroma, documents: list[Document]) -> int:
    """
    Thêm documents vào vector store.
    
    Args:
        vector_store: Chroma instance
        documents: list Documents từ loader
        
    Returns:
        int: số documents đã thêm thành công
    """
    if not documents:
        print("⚠️ Không có documents để thêm vào vector store")
        return 0

    ids = [make_doc_id(doc.metadata["source"], doc.metadata["page"]) for doc in documents]

    vector_store.add_documents(documents, ids=ids)
    print(f"✅ Đã index {len(documents)} documents vào vector store")
    return len(documents)


def build_vector_store(documents: list[Document]) -> tuple[Chroma, list[Document]]:
    """
    Returns:
        tuple: (vector_store, documents) — documents dùng để build BM25
    """
    print(f"🔧 Khởi tạo embedding model: {EMBEDDING_MODEL}")
    embedding = get_embedding_model()

    print(f"🗄️ Kết nối vector store (mode: {CHROMA_MODE})")
    vector_store = get_vector_store(embedding)

    try:
        if vector_store._collection.count() == 0:
            print("📦 Vector DB trống, tiến hành index dữ liệu mẫu...")
            add_documents(vector_store, documents)
        else:
            print(f"⚡ Vector DB đã có {vector_store._collection.count()} chunks.")
    except Exception as e:
        print(f"⚠️ Lỗi khi check DB: {e}")
        add_documents(vector_store, documents)

    # Return cả vector_store lẫn documents để build BM25
    return vector_store, documents