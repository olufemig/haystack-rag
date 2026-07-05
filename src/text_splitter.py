from dataclasses import dataclass
import re

from haystack import Document

from src.wiki_loader import WikiSource


@dataclass(frozen=True)
class ChunkStats:
    sources: int
    chunks: int


def split_wiki_source(source: WikiSource, chunk_size: int, chunk_overlap: int) -> tuple[list[Document], ChunkStats]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    text = re.sub(r"\s+", " ", source.text).strip()
    documents: list[Document] = []
    step = chunk_size - chunk_overlap
    slug = _slugify(source.title)

    for chunk_number, start in enumerate(range(0, len(text), step), start=1):
        content = text[start : start + chunk_size].strip()
        if not content:
            continue

        chunk_id = f"{slug}-wiki-c{chunk_number}"
        documents.append(
            Document(
                id=chunk_id,
                content=content,
                meta={
                    "source": source.url,
                    "title": source.title,
                    "chunk_id": chunk_id,
                },
            )
        )

    return documents, ChunkStats(sources=1, chunks=len(documents))


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "wiki"
