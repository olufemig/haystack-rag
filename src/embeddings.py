from dataclasses import replace
import re
import time

from google import genai
from haystack import Document

from src.config import Settings


GEMINI_EMBEDDING_BATCH_SIZE = 100
GEMINI_EMBEDDING_MAX_RETRIES = 3


def embed_documents(documents: list[Document], settings: Settings) -> list[Document]:
    if not documents:
        return documents

    embeddings = _embed_contents([document.content or "" for document in documents], settings)
    return [
        replace(document, embedding=embedding)
        for document, embedding in zip(documents, embeddings, strict=True)
    ]


def embed_text(text: str, settings: Settings) -> list[float]:
    embeddings = _embed_contents([text], settings)
    return embeddings[0]


def _embed_contents(contents: list[str], settings: Settings) -> list[list[float]]:
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is required for Gemini embeddings")

    client = genai.Client(api_key=settings.gemini_api_key)
    all_embeddings: list[list[float]] = []

    for start in range(0, len(contents), GEMINI_EMBEDDING_BATCH_SIZE):
        batch = contents[start : start + GEMINI_EMBEDDING_BATCH_SIZE]
        response = _embed_batch(client, settings.embedding_model, batch)
        embeddings = getattr(response, "embeddings", None)
        if not embeddings or len(embeddings) != len(batch):
            raise RuntimeError("Gemini returned an unexpected embedding response")

        for embedding in embeddings:
            values = getattr(embedding, "values", None)
            if not values:
                raise RuntimeError("Gemini returned an empty embedding")
            all_embeddings.append(list(values))

    return all_embeddings


def _embed_batch(client: genai.Client, model: str, contents: list[str]):
    for attempt in range(GEMINI_EMBEDDING_MAX_RETRIES + 1):
        try:
            return client.models.embed_content(model=model, contents=contents)
        except Exception as exc:
            delay = _retry_delay_seconds(exc)
            if delay is None or attempt == GEMINI_EMBEDDING_MAX_RETRIES:
                raise
            print(f"Gemini embedding quota reached; retrying in {delay:.0f}s...")
            time.sleep(delay)

    raise RuntimeError("Gemini embedding retry loop exited unexpectedly")


def _retry_delay_seconds(error: Exception) -> float | None:
    message = str(error)
    match = re.search(r"retry(?: in|Delay'?: '?)(\d+(?:\.\d+)?)s", message, re.IGNORECASE)
    if match:
        return float(match.group(1)) + 1
    if "RESOURCE_EXHAUSTED" in message or "429" in message:
        return 60
    return None
