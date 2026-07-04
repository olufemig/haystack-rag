from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    chroma_path: str
    chroma_collection: str
    gemini_api_key: str | None
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    min_relevance_score: float
    max_question_chars: int
    max_context_chars: int
    llm_provider: str
    ollama_base_url: str
    ollama_model: str
    gemini_model: str


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        chroma_path=os.getenv("CHROMA_PATH", "./data/chroma"),
        chroma_collection=os.getenv("CHROMA_COLLECTION", "pdf_knowledge_base"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "2000")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "100")),
        top_k=int(os.getenv("TOP_K", "5")),
        min_relevance_score=float(os.getenv("MIN_RELEVANCE_SCORE", "0.7")),
        max_question_chars=int(os.getenv("MAX_QUESTION_CHARS", "1000")),
        max_context_chars=int(os.getenv("MAX_CONTEXT_CHARS", "12000")),
        llm_provider=os.getenv("LLM_PROVIDER", "ollama").lower(),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
    )
