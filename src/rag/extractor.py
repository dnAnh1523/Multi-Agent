from pydantic import BaseModel, Field
from typing import Optional
from src.agents.planner import get_llm

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