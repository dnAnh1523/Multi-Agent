"""
app.py - Chainlit UI Entry Point
Accounting & Invoice Agent - Multi-Agent RAG System
"""

import chainlit as cl
from pathlib import Path
import re

from src.rag.loader import load_pdfs
from src.rag.embedder import build_vector_store, get_embedding_model, get_vector_store, add_documents
from src.agents.graph import build_graph, chat
from src.config import validate_config, LANGGRAPH_THREAD_ID

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
    vector_store = build_vector_store(docs)

    # Build graph
    graph = build_graph(vector_store)

    # Lưu vào user_session để dùng ở on_message
    # cl.user_session.set() nhận key và value
    cl.user_session.set("graph", graph)
    cl.user_session.set("vector_store", vector_store)
    cl.user_session.set("thread_id", LANGGRAPH_THREAD_ID)

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
    """
    Post-process câu trả lời của LLM:
    1. Tìm tất cả raw IDs xuất hiện trong answer
    2. Sort theo alphabet → thứ tự danh sách tham khảo IEEE
    3. Map raw_id → số IEEE [1],[2],...
    4. Thay thế trong text
    5. Tạo danh sách tham khảo IEEE

    Returns:
        tuple: (processed_answer, references_list)
    """
    # Tìm tất cả ngoặc vuông trong answer
    bracket_groups = re.findall(r'\[([^\]]+)\]', answer)

    # Extract tất cả raw IDs hợp lệ
    found_ids = []
    for group in bracket_groups:
        ids = [id.strip() for id in group.split(',')]
        for id in ids:
            if re.match(r'^(rag|web)_[a-z0-9_]+$', id) and id in citation_map:
                found_ids.append(id)

    if not found_ids:
        return answer, []

    # Sort theo alphabet → thứ tự danh sách tham khảo
    sorted_ids = sorted(set(found_ids))

    # Map raw_id → số IEEE
    id_to_number = {id: i + 1 for i, id in enumerate(sorted_ids)}

    # Thay thế trong text — xử lý cả single và multiple IDs
    processed = answer
    for group in set(re.findall(r'\[([^\]]+)\]', answer)):
        ids_in_group = [id.strip() for id in group.split(',')]
        valid_ids = [id for id in ids_in_group
                     if re.match(r'^(rag|web)_[a-z0-9_]+$', id)
                     and id in citation_map]
        if valid_ids:
            # Thay bằng số IEEE, sort theo số
            numbers = sorted([id_to_number[id] for id in valid_ids])
            new_ref = " ".join([f"[{n}]" for n in numbers])
            processed = processed.replace(f'[{group}]', new_ref)

    # Tạo danh sách tham khảo IEEE
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