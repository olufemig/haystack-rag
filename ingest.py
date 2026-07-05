import argparse
import sys

from haystack.document_stores.types import DuplicatePolicy

from src.config import load_settings
from src.document_store import get_document_store
from src.embeddings import embed_documents
from src.text_splitter import split_wiki_source
from src.wiki_loader import load_wiki_source


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest the Arsenal FC Wikipedia page into ChromaDB.")
    parser.add_argument("--url", help="Wiki URL to ingest. Defaults to WIKI_URL.")
    parser.add_argument("--reset", action="store_true", help="Delete existing documents before ingesting.")
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    settings = load_settings()

    wiki_url = args.url or settings.wiki_url
    source = load_wiki_source(wiki_url, settings.wiki_title)
    documents, chunk_stats = split_wiki_source(source, settings.chunk_size, settings.chunk_overlap)

    if not documents:
        raise RuntimeError("No extractable text chunks were created from the wiki source")

    embedded_documents = embed_documents(documents, settings)
    document_store = get_document_store(settings)

    if args.reset:
        document_store.delete_all_documents()

    written = document_store.write_documents(embedded_documents, policy=DuplicatePolicy.OVERWRITE)

    print("Ingestion complete")
    print(f"Source: {source.title}")
    print(f"URL: {source.url}")
    print(f"Chunks written: {written}")
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
