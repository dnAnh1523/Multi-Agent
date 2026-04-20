"""
config.py - Centralized configuration loader
Đọc tất cả settings từ .env, cung cấp defaults hợp lý
"""

import os
from dotenv import load_dotenv

load_dotenv()


# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# --- Web Search ---
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# --- Vector Store ---
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
CHROMA_MODE = os.getenv("CHROMA_MODE", "persist")  # "persist" | "memory"

# --- Embedding ---
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "intfloat/multilingual-e5-small"
)

# --- Agent Settings ---
LANGGRAPH_THREAD_ID = os.getenv("LANGGRAPH_THREAD_ID", "accounting-agent-thread")
MAX_AGENT_ITERATIONS = int(os.getenv("MAX_AGENT_ITERATIONS", "10"))
FAITHFULNESS_THRESHOLD = float(os.getenv("FAITHFULNESS_THRESHOLD", "0.75"))

# --- Validation (chạy khi import để phát hiện lỗi sớm) ---
def validate_config() -> list[str]:
    """Trả về danh sách các warnings nếu config thiếu."""
    warnings = []
    if not GROQ_API_KEY:
        warnings.append("GROQ_API_KEY chưa được set — sẽ dùng Ollama fallback")
    if not TAVILY_API_KEY:
        warnings.append("TAVILY_API_KEY chưa được set — Web Search sẽ không hoạt động")
    return warnings