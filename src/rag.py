from dataclasses import dataclass

from haystack import Document
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever

from src.config import Settings, load_settings
from src.document_store import get_document_store
from src.embeddings import embed_text


FALLBACK_ANSWER = "I don't know based on the available documents."


@dataclass(frozen=True)
class Source:
    source: str
    page: int | None
    score: float | None


@dataclass(frozen=True)
class RetrievalResult:
    answer: str
    documents: list[Document]
    sources: list[Source]
    used_fallback: bool


def retrieve(question: str, settings: Settings | None = None) -> RetrievalResult:
    settings = settings or load_settings()
    question = question.strip()
    if not question:
        return _fallback()

    document_store = get_document_store(settings)
    if document_store.count_documents() == 0:
        return _fallback()

    query_embedding = embed_text(question, settings)
    retriever = ChromaEmbeddingRetriever(document_store=document_store, top_k=settings.top_k)
    result = retriever.run(query_embedding=query_embedding, top_k=settings.top_k)
    documents = _filter_documents(result.get("documents", []), settings.min_relevance_score)

    if not documents:
        return _fallback()

    context = _build_context(documents, settings.max_context_chars)
    if context == FALLBACK_ANSWER:
        return _fallback()

    sources = _sources_from_documents(documents)

    return RetrievalResult(
        answer=context,
        documents=documents,
        sources=sources,
        used_fallback=False,
    )


def _filter_documents(documents: list[Document], min_relevance_score: float) -> list[Document]:
    filtered: list[Document] = []
    for document in documents:
        relevance = _relevance_score(document)
        if relevance is None or relevance >= min_relevance_score:
            filtered.append(document)
    return filtered


def _relevance_score(document: Document) -> float | None:
    if document.score is None:
        return None
    return 1 - document.score


def _build_context(documents: list[Document], max_chars: int) -> str:
    chunks: list[str] = []
    used_chars = 0

    for index, document in enumerate(documents, start=1):
        source = document.meta.get("source", "unknown")
        page = document.meta.get("page", "unknown")
        content = (document.content or "").strip()
        if not content:
            continue

        chunk = f"[{index}] Source: {source}, page {page}\n{content}"
        remaining = max_chars - used_chars
        if remaining <= 0:
            break
        if len(chunk) > remaining:
            chunk = chunk[:remaining].rstrip()

        chunks.append(chunk)
        used_chars += len(chunk)

    if not chunks:
        return FALLBACK_ANSWER

    return "\n\n".join(chunks)


def _sources_from_documents(documents: list[Document]) -> list[Source]:
    seen: set[tuple[str, int | None]] = set()
    sources: list[Source] = []

    for document in documents:
        source = str(document.meta.get("source", "unknown"))
        page = document.meta.get("page")
        if not isinstance(page, int):
            page = None
        key = (source, page)
        if key in seen:
            continue

        seen.add(key)
        sources.append(Source(source=source, page=page, score=_relevance_score(document)))

    return sources


def _fallback() -> RetrievalResult:
    return RetrievalResult(
        answer=FALLBACK_ANSWER,
        documents=[],
        sources=[],
        used_fallback=True,
    )
