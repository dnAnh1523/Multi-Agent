"""
llm.py - Centralized LLM factory
Tránh circular import giữa planner, executor, retriever và các tools.
"""

from functools import lru_cache
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from src.config import (
    GROQ_API_KEY, GROQ_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
)


@lru_cache(maxsize=1)
def get_llm():
    """
    Khởi tạo LLM với fallback Groq → Ollama.
    Dùng lru_cache để chỉ tạo 1 instance duy nhất.
    """
    if GROQ_API_KEY:
        return ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=0)
    return ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)