from haystack_integrations.document_stores.chroma import ChromaDocumentStore

from src.config import Settings, load_settings


def get_document_store(settings: Settings | None = None) -> ChromaDocumentStore:
    settings = settings or load_settings()

    return ChromaDocumentStore(
        collection_name=settings.chroma_collection,
        persist_path=settings.chroma_path,
        distance_function="cosine",
    )
