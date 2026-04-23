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

# # Test 1: general intent
# print("\n=== Test 1: General ===")
# result = chat(graph, "Xin chào, bạn có thể giúp gì cho tôi?")
# print(result["messages"][-1].content)

# # Test 2: retrieve intent
# print("\n=== Test 2: Retrieve ===")
# result = chat(graph, "Hóa đơn số 0000001 có tổng tiền thanh toán là bao nhiêu?")
# print(result["messages"][-1].content)
# print("Citations:", result.get("citations"))

# # Test 3: follow-up (test memory)
# print("\n=== Test 3: Follow-up (memory) ===")
# result = chat(graph, "Thuế GTGT của hóa đơn đó là bao nhiêu phần trăm?")
# print(result["messages"][-1].content)

# # Test 4: invoice_summary
# print("\n=== Test 4: Invoice Summary ===")
# result = chat(graph, "Tóm tắt chi tiết hóa đơn số 0000001")
# print(result["messages"][-1].content)

# # Test 5: email_draft
# print("\n=== Test 5: Email Draft ===")
# result = chat(graph, "Soạn email nhắc nợ cho hóa đơn số 0000001")
# print(result["messages"][-1].content)

# # Test 6: web_search
# print("\n=== Test 6: Web Search ===")
# result = chat(graph, "Thuế suất GTGT hiện hành tại Việt Nam năm 2026 là bao nhiêu?")
# print(result["messages"][-1].content)

# Test 7: compare
print("\n=== Test 7: Compare ===")
result = chat(graph, "So sánh hóa đơn số 0000001 và hóa đơn số 0000002")
print(result["messages"][-1].content)