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
    max_context_chars: int


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
        max_context_chars=int(os.getenv("MAX_CONTEXT_CHARS", "12000")),
    )
