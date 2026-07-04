from dataclasses import dataclass

from haystack import Document

from src.pdf_loader import PdfPage


@dataclass(frozen=True)
class ChunkStats:
    pages: int
    chunks: int


def split_pages(pages: list[PdfPage], chunk_size: int, chunk_overlap: int) -> tuple[list[Document], ChunkStats]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    documents: list[Document] = []
    step = chunk_size - chunk_overlap

    for page in pages:
        chunk_number = 1
        for start in range(0, len(page.text), step):
            content = page.text[start : start + chunk_size].strip()
            if not content:
                continue

            chunk_id = f"{page.source}-p{page.page}-c{chunk_number}"
            documents.append(
                Document(
                    id=chunk_id,
                    content=content,
                    meta={
                        "source": page.source,
                        "page": page.page,
                        "chunk_id": chunk_id,
                    },
                )
            )
            chunk_number += 1

    return documents, ChunkStats(pages=len(pages), chunks=len(documents))
