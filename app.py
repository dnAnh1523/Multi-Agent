"""
app.py - Chainlit UI Entry Point
Accounting & Invoice Agent - Multi-Agent RAG System
"""

import chainlit as cl
from pathlib import Path
import re
import uuid

from src.rag.loader import load_pdfs
from src.rag.embedder import build_vector_store, get_embedding_model, get_vector_store, add_documents
from src.agents.graph import build_graph, chat
from src.config import validate_config, LANGGRAPH_THREAD_ID
from src.rag.retriever import build_bm25_retriever


# --- Đường dẫn PDF mẫu mặc định ---
DEFAULT_PDFS = [
    "data/sample_invoices/hoadon_001.pdf",
    "data/sample_invoices/hoadon_002.pdf",
    "data/sample_invoices/hoadon_003.pdf",
    "data/sample_invoices/bao_cao_tai_chinh_q1.pdf",
]


@cl.on_chat_start
async def on_chat_start():
    """
    Chạy khi user mở app lần đầu.
    Khởi tạo vector store, load PDF mẫu, build graph.
    """
    # Kiểm tra config
    warnings = validate_config()
    for w in warnings:
        print(f"⚠️ {w}")

    # Thông báo đang khởi tạo
    msg = cl.Message(content="⚙️ Đang khởi tạo hệ thống...")
    await msg.send()

    # Load PDF mẫu
    docs = load_pdfs(DEFAULT_PDFS)

    # Build vector store
    vector_store, documents = build_vector_store(docs)
    bm25_retriever = build_bm25_retriever(documents)
    graph = build_graph(vector_store, bm25_retriever)
    cl.user_session.set("bm25_retriever", bm25_retriever)

    # Lưu vào user_session để dùng ở on_message
    # cl.user_session.set() nhận key và value
    cl.user_session.set("graph", graph)
    cl.user_session.set("vector_store", vector_store)
    session_thread_id = str(uuid.uuid4())
    cl.user_session.set("documents", documents)
    cl.user_session.set("thread_id", session_thread_id)

    # Cập nhật thông báo thành công
    msg.content = """✅ Hệ thống đã sẵn sàng!

**Tôi có thể giúp bạn:**
- 📄 Trả lời câu hỏi về tài liệu kế toán
- 🔍 Tóm tắt chi tiết hóa đơn
- ✉️ Soạn email nhắc nợ chuyên nghiệp
- 🌐 Tra cứu luật thuế mới nhất
- 📊 So sánh 2 hóa đơn hoặc báo cáo

**Upload PDF** để thêm tài liệu mới, hoặc bắt đầu hỏi ngay!"""
    await msg.update()

def process_citations(answer: str, citation_map: dict) -> tuple[str, list[str]]:
    # Pass 1: collect tất cả valid IDs
    bracket_groups = re.findall(r'\[([^\]]+)\]', answer)
    found_ids = []
    for group in bracket_groups:
        for id in [i.strip() for i in group.split(',')]:
            if re.match(r'^(rag|web)_[a-z0-9_]+$', id) and id in citation_map:
                if id not in found_ids:
                    found_ids.append(id)

    if not found_ids:
        # Xóa các ngoặc rác không hợp lệ
        processed = answer
        for group in set(bracket_groups):
            ids = [i.strip() for i in group.split(',')]
            if not any(i in citation_map for i in ids):
                processed = processed.replace(f'[{group}]', '')
        return processed, []

    # Pass 2: sort và map số IEEE
    sorted_ids = sorted(set(found_ids))
    id_to_number = {id: i + 1 for i, id in enumerate(sorted_ids)}

    # Pass 3: replace trong text
    processed = answer
    for group in set(bracket_groups):
        ids_in_group = [i.strip() for i in group.split(',')]
        valid_ids = [i for i in ids_in_group
                     if re.match(r'^(rag|web)_[a-z0-9_]+$', i)
                     and i in citation_map]
        if valid_ids:
            numbers = sorted([id_to_number[i] for i in valid_ids])
            new_ref = " ".join([f"[{n}]" for n in numbers])
            processed = processed.replace(f'[{group}]', new_ref)
        else:
            processed = processed.replace(f'[{group}]', '')

    # Pass 4: tạo danh sách tham khảo IEEE
    references = []
    for raw_id in sorted_ids:
        num = id_to_number[raw_id]
        meta = citation_map[raw_id]
        if meta["type"] == "document":
            ref = f'[{num}] "{meta["source"]}," trang {meta["page"]}.'
        else:
            ref = (f'[{num}] {meta["org"]}, "{meta["title"]},"'
                   f' [Online]. Available: {meta["url"]}')
        references.append(ref)

    return processed, references


@cl.on_message
async def on_message(message: cl.Message):
    """
    Chạy mỗi khi user gửi message.
    Xử lý 2 trường hợp: upload file hoặc hỏi câu hỏi.
    """
    graph = cl.user_session.get("graph")
    vector_store = cl.user_session.get("vector_store")
    thread_id = cl.user_session.get("thread_id")

    # -----------------------------------------------
    # Trường hợp 1: User upload file PDF
    # -----------------------------------------------
    if message.elements:
        pdf_files = [
            el for el in message.elements
            if hasattr(el, 'path') and el.path.endswith('.pdf')
        ]

        if pdf_files:
            processing_msg = cl.Message(content=f"📄 Đang xử lý {len(pdf_files)} file PDF...")
            await processing_msg.send()

            # Load các file PDF vừa upload
            # pdf_files[i].path là đường dẫn file trên server
            file_paths = [el.path for el in pdf_files]
            new_docs = load_pdfs(file_paths)

            # Add vào vector store hiện tại
            count = add_documents(vector_store, new_docs)
            existing_docs = cl.user_session.get("documents", [])
            updated_docs = existing_docs + new_docs
            cl.user_session.set("documents", updated_docs)
            bm25_retriever = build_bm25_retriever(updated_docs)
            cl.user_session.set("bm25_retriever", bm25_retriever)
            graph = build_graph(vector_store, bm25_retriever)
            cl.user_session.set("graph", graph)
            processing_msg.content = f"✅ Đã index {count} trang từ {len(pdf_files)} file vào hệ thống!"
            await processing_msg.update()

            # Nếu message chỉ có file, không có text → dừng ở đây
            if not message.content.strip():
                return

    # -----------------------------------------------
    # Trường hợp 2: User hỏi câu hỏi
    # -----------------------------------------------
    if not message.content.strip():
        return

    # Hiển thị loading
    # Bằng đoạn này
    thinking_msg = cl.Message(content="🤔 Đang xử lý...")
    await thinking_msg.send()

    # Hiển thị tool step khi graph chạy
    async with cl.Step(name="🤖 Multi-Agent Processing", type="tool") as step:
        step.input = message.content
        result = chat(graph, message.content, thread_id)
        intent = result.get("intent", "unknown")
        step.output = f"Intent: {intent} | Hoàn thành"

    # Lấy câu trả lời từ kết quả
    answer = result["messages"][-1].content

    # Lấy citations nếu có
    # Thay đoạn format citations cũ
    citation_map = result.get("citation_map", {})
    if citation_map:
        processed_answer, references = process_citations(answer, citation_map)
        if references:
            refs_text = "\n".join(references)
            answer = f"{processed_answer}\n\n---\n**Tài liệu tham khảo:**\n{refs_text}"
        else:
            answer = processed_answer

    # Cập nhật message với câu trả lời thật
    thinking_msg.content = answer
    await thinking_msg.update()