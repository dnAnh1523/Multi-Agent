# debug_chroma.py
import sys
sys.path.insert(0, '.')
from src.rag.embedder import get_embedding_model, get_vector_store

embedding = get_embedding_model()
vs = get_vector_store(embedding)

# Xem tổng số documents
print("Total docs:", vs._collection.count())

# Xem tất cả documents và metadata
results = vs._collection.get()
print("IDs:", results["ids"])
print("Metadatas:", results["metadatas"])