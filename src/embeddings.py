from dataclasses import replace
from functools import lru_cache

from haystack import Document
from sentence_transformers import SentenceTransformer

from src.config import Settings


@lru_cache(maxsize=1)
def _load_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def embed_documents(documents: list[Document], settings: Settings) -> list[Document]:
    if not documents:
        return documents

    model = _load_model(settings.embedding_model)
    contents = [document.content or "" for document in documents]
    embeddings = model.encode(
        contents,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    return [
        replace(document, embedding=embedding.tolist())
        for document, embedding in zip(documents, embeddings, strict=True)
    ]


def embed_text(text: str, settings: Settings) -> list[float]:
    model = _load_model(settings.embedding_model)
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()
