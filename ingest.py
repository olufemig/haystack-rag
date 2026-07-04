import argparse
import sys
from pathlib import Path

from haystack.document_stores.types import DuplicatePolicy

from src.config import load_settings
from src.document_store import get_document_store
from src.embeddings import embed_documents
from src.pdf_loader import load_pdf_pages
from src.text_splitter import split_pages


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest PDFs into the persisted ChromaDB index.")
    parser.add_argument("--pdf-dir", default="./pdfs", help="Directory containing PDF files.")
    parser.add_argument("--reset", action="store_true", help="Delete existing documents before ingesting.")
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    settings = load_settings()
    pdf_dir = Path(args.pdf_dir)

    pages, pdf_count, skipped_empty_pages = load_pdf_pages(pdf_dir)
    documents, chunk_stats = split_pages(pages, settings.chunk_size, settings.chunk_overlap)

    if not documents:
        raise RuntimeError("No extractable text chunks were created from the PDF files")

    embedded_documents = embed_documents(documents, settings)
    document_store = get_document_store(settings)

    if args.reset:
        document_store.delete_all_documents()

    written = document_store.write_documents(embedded_documents, policy=DuplicatePolicy.OVERWRITE)

    print("Ingestion complete")
    print(f"PDFs found: {pdf_count}")
    print(f"Pages extracted: {chunk_stats.pages}")
    print(f"Chunks written: {written}")
    print(f"Skipped empty pages: {skipped_empty_pages}")
    print(f"Collection: {settings.chroma_collection}")
    print(f"Path: {settings.chroma_path}")


def main() -> int:
    try:
        run()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
