from google import genai
import requests

from src.config import Settings, load_settings


def generate_text(prompt: str, settings: Settings | None = None) -> str:
    settings = settings or load_settings()
    provider = settings.llm_provider.lower()

    if provider == "ollama":
        return _generate_with_ollama(prompt, settings)
    if provider == "gemini":
        return _generate_with_gemini(prompt, settings)

    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")


def _generate_with_ollama(prompt: str, settings: Settings) -> str:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
    response = requests.post(
        url,
        json={
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()

    payload = response.json()
    answer = payload.get("response")
    if not answer:
        raise RuntimeError("Ollama returned an empty response")

    return answer.strip()


def _generate_with_gemini(prompt: str, settings: Settings) -> str:
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
    )

    answer = getattr(response, "text", None)
    if not answer:
        raise RuntimeError("Gemini returned an empty response")

    return answer.strip()
