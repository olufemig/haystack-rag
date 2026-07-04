import chainlit as cl

from src.config import Settings, load_settings
from src.document_store import get_document_store
from src.llm import generate_text
from src.rag import FALLBACK_ANSWER, retrieve


def answer_question(question: str, settings: Settings) -> str:
    retrieval = retrieve(question, settings)
    if retrieval.used_fallback or not retrieval.prompt:
        return FALLBACK_ANSWER

    return generate_text(retrieval.prompt, settings)


@cl.on_chat_start
async def on_chat_start() -> None:
    settings = load_settings()
    cl.user_session.set("settings", settings)

    try:
        document_count = get_document_store(settings).count_documents()
    except Exception as exc:
        await cl.Message(content=f"ChromaDB is not ready: {exc}").send()
        return

    if document_count == 0:
        await cl.Message(
            content="No PDF chunks are available yet. Run ingestion before asking questions."
        ).send()
        return

    await cl.Message(
        content=(
            f"Ready. Loaded {document_count} PDF chunks from the knowledge base. "
            "Ask a question about the indexed documents."
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    settings = cl.user_session.get("settings") or load_settings()

    try:
        answer = await cl.make_async(answer_question)(message.content, settings)
    except Exception as exc:
        answer = f"I could not answer that question: {exc}"

    await cl.Message(content=answer).send()
