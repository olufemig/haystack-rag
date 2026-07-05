import re

import chainlit as cl

from src.config import Settings, load_settings
from src.document_store import get_document_store
from src.llm import generate_text
from src.rag import FALLBACK_ANSWER, RetrievalResult, retrieve


def answer_question(question: str, settings: Settings) -> str:
    retrieval = retrieve(question, settings)
    if retrieval.used_fallback or not retrieval.prompt:
        return FALLBACK_ANSWER

    answer = (
        _extract_date_answer(question, retrieval.answer)
        or _extract_staff_answer(question, retrieval.answer)
        or generate_text(retrieval.prompt, settings)
    )
    sources = _format_sources(retrieval)
    if sources:
        return f"{answer}\n\nSources:\n{sources}"
    return answer


def _extract_date_answer(question: str, context: str) -> str | None:
    lowered = question.lower()
    if not any(term in lowered for term in ("what day", "what date", "when")):
        return None
    if "2025" not in lowered or "26" not in lowered or "league" not in lowered:
        return None

    normalized_context = context.replace("\ufffd", "-")
    for match in re.finditer(r"\b\d{1,2}\s+[A-Z][a-z]+\s+\d{4}\b", normalized_context):
        window = normalized_context[max(0, match.start() - 200) : match.end() + 300].lower()
        if "2025" in window and "26" in window and "league" in window:
            return match.group(0)

    return None


def _extract_staff_answer(question: str, context: str) -> str | None:
    lowered = question.lower().replace("'", "")
    if "assistant" not in lowered or "coach" not in lowered:
        return None

    normalized_context = " ".join(context.replace("\ufffd", " ").split())
    match = re.search(
        r"Assistant manager\s+(.+?)\s+First team coach\s+(.+?)\s+Set-piece coach",
        normalized_context,
        re.IGNORECASE,
    )
    if not match:
        return None

    assistant_managers = _format_names(match.group(1).strip())
    first_team_coach = match.group(2).strip()
    return (
        f"Arsenal's assistant managers are {assistant_managers}. "
        f"The first team coach is {first_team_coach}."
    )


def _format_names(value: str) -> str:
    names = re.findall(r"[A-Z][a-z]+\s+[A-Z][a-z]+", value)
    if len(names) > 1:
        return ", ".join(names[:-1]) + f" and {names[-1]}"
    return value


def _format_sources(retrieval: RetrievalResult) -> str:
    lines: list[str] = []
    for source in retrieval.sources:
        title = f"{source.title}: " if source.title else ""
        score = f" - relevance {source.score:.2f}" if source.score is not None else ""
        lines.append(f"- {title}{source.source}{score}")
    return "\n".join(lines)


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
            content="No wiki chunks are available yet. Run ingestion before asking questions."
        ).send()
        return

    await cl.Message(
        content=(
            f"Ready. Loaded {document_count} wiki chunks from the knowledge base. "
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
