import sys
sys.path.insert(0, '.')

from src.rag.loader import load_pdfs
from src.rag.embedder import build_vector_store
from src.agents.graph import build_graph, chat

# Setup
print("📄 Loading documents...")
docs = load_pdfs([
    'data/sample_invoices/hoadon_001.pdf',
    'data/sample_invoices/hoadon_002.pdf',
    'data/sample_invoices/hoadon_003.pdf',
    'data/sample_invoices/bao_cao_tai_chinh_q1.pdf',
])
vs = build_vector_store(docs)

# Build graph
print("\n🔧 Building graph...")
graph = build_graph(vs)

# Test 1: general intent
print("\n=== Test 1: General ===")
result = chat(graph, "Xin chào, bạn có thể giúp gì cho tôi?")
print(result["messages"][-1].content)

# Test 2: retrieve intent
print("\n=== Test 2: Retrieve ===")
result = chat(graph, "Hóa đơn số 0000001 có tổng tiền thanh toán là bao nhiêu?")
print(result["messages"][-1].content)
print("Citations:", result.get("citations"))

# Test 3: follow-up (test memory)
print("\n=== Test 3: Follow-up (memory) ===")
result = chat(graph, "Thuế GTGT của hóa đơn đó là bao nhiêu phần trăm?")
print(result["messages"][-1].content)