# Roadmap

This roadmap reflects the current implementation plan for the Haystack RAG chatbot.

## Phase 1: Project Foundation

- Change Python requirement from `>=3.14` to a compatibility-focused range such as `>=3.11,<3.13`.
- Add core dependencies:
  - `haystack-ai`
  - `chroma-haystack`
  - `chromadb`
  - `chainlit`
  - `google-genai`
  - `guardrails-ai` for optional future output validation
  - `langwatch` for optional future observability
  - `python-dotenv`
  - `requests`
- Add dev dependencies:
  - `pytest`
  - `pytest-mock`
- Add optional HTTP mocking dependency after implementation details are known:
  - `responses` if using `requests`
  - `respx` if using `httpx`
- Add `.gitignore`.
- Add `.env.example`.
- Add base `README.md`.

## Phase 2: Shared Configuration

- Create `src/config.py`.
- Load configuration from environment variables.
- Support local and Railway settings.
- Include settings for:
  - ChromaDB path and collection.
  - Gemini API key.
  - Gemini embedding model.
  - LLM provider.
  - Ollama base URL and model.
  - Gemini LLM model.
  - retrieval limits.
  - chunking settings.
  - LangWatch settings.

## Phase 3: Ingestion CLI

- Create `ingest.py`.
- Default command:

```powershell
uv run python ingest.py --reset
```

- Create wiki loading utilities.
- Fetch the Arsenal FC Wikipedia page.
- Extract structured readable article text from paragraphs, lists, captions, and table cells.
- Split article text into overlapping chunks.
- Embed chunks with Gemini `gemini-embedding-001`.
- Persist chunks to ChromaDB through Haystack/Chroma.
- Store metadata for retrieval/debugging:
  - `source`
  - `title`
  - `chunk_id`
- Print an ingestion summary.

## Phase 4: Embedding And Vector Store Layer

- Create `src/embeddings.py`.
- Wrap Gemini `gemini-embedding-001` for document and query embeddings.
- Create `src/document_store.py`.
- Centralize ChromaDB persistent store setup.
- Ensure ingestion and retrieval use the same collection and embedding dimensions.

## Phase 5: RAG Pipeline

- Create `src/rag.py`.
- Build a Haystack-based retrieval flow:

```text
Question -> app guardrails -> Gemini query embedding -> Chroma retrieval
         -> retrieval threshold -> grounded prompt -> LLM provider
         -> answer with source metadata
```

- Enforce Arsenal FC wiki-only answers.
- Return fallback when retrieval is weak or missing.
- Keep source metadata and append the retrieved wiki source below Chainlit answers.

## Phase 6: LLM Provider Layer

- Create `src/llm.py`.
- Add provider switching with `LLM_PROVIDER`.
- Implement local Ollama generation:
  - model: `qwen2.5-coder:7b`
  - endpoint: `OLLAMA_BASE_URL`
- Implement Railway Gemini generation:
  - model: `gemini-2.5-flash-lite`
  - key: `GEMINI_API_KEY`
- Return clear errors when the configured provider is unavailable.

## Phase 7: Guardrails

- Create `src/guardrails.py`.
- Implement lightweight app guardrails for RAG logic:
  - query validation.
  - prompt injection blocking.
  - retrieval threshold checks.
  - context length limits.
  - fallback routing.
- Keep Guardrails AI as an installed dependency for later output validation if needed.
- Enforce the final answer contract:
  - answer from retrieved Arsenal FC wiki context only.
  - keep answer generation grounded and let the UI append source metadata separately.
  - use exact fallback when unsupported.
  - do not leak prompts or internal instructions.

## Phase 8: Chainlit App

- Create `app.py`.
- Make the UI question-only.
- Do not support uploads or ingestion in the UI.
- On startup, check that ChromaDB exists and has data.
- On each message:
  - validate question.
  - run RAG.
  - generate an answer from the grounded prompt.
  - render answer plus retrieved wiki source.
  - show clear user-facing errors for missing index or unavailable model provider.

## Phase 9: Observability And Evaluation

- Create `src/observability.py`.
- Make hosted LangWatch optional via `LANGWATCH_ENABLED`.
- If the dashboard must be self-hosted as part of the Railway deployment, replace LangWatch with Langfuse or Phoenix.
- Trace each RAG request.
- Log:
  - question.
  - provider and model.
  - retrieved documents and scores.
  - guardrail decisions.
  - final answer.
  - source metadata if observability is later wired in.
  - errors and latency.
- Add an optional evaluation dataset later at `eval/questions.jsonl`.
- Evaluate:
  - faithfulness.
  - context relevance.
  - answer relevance.
  - source-grounding correctness.
  - fallback correctness.
  - prompt-injection resistance.
  - provider parity between local Ollama and Railway Gemini.

## Phase 10: Minimal Unit Testing

- Create the minimal test folder structure:

```text
tests/
  unit/
    test_config.py
    test_text_splitter.py
    test_guardrails.py
    test_llm.py
    test_rag.py
  fixtures/
    retrieved_docs.json
```

- Use `pytest` as the test runner.
- Use `pytest-mock` to mock external services.
- Do not make live Gemini API calls in unit tests.
- Do not call a live Ollama server in unit tests.
- Do not require a live ChromaDB index in unit tests.
- Do not call Guardrails AI, LangWatch, Langfuse, Phoenix, or other observability services in unit tests.
- Cover only the core behavior needed for confidence:
  - configuration defaults and LLM provider switching.
  - chunk size and overlap behavior.
  - prompt-injection blocking.
  - weak retrieval fallback.
  - LLM provider selection for Ollama and Gemini with mocked calls.
  - RAG fallback behavior when no useful context is retrieved.
- Run tests with:

```powershell
uv run pytest
```

## Phase 11: Railway Deployment

- Use a Railway volume mounted at `/data`.
- Store ChromaDB at `/data/chroma`.
- Configure Railway environment variables:

```env
CHROMA_PATH=/data/chroma
CHROMA_COLLECTION=arsenal_wiki
EMBEDDING_MODEL=gemini-embedding-001
GEMINI_API_KEY=your_key_here
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash-lite
LANGWATCH_ENABLED=true
LANGWATCH_PROJECT=haystack-rag
```

- Use start command:

```powershell
uv run chainlit run app.py --host 0.0.0.0 --port $PORT
```

- Ensure the ChromaDB index is copied to the persistent disk before demo use.
- Alternatively, run ingestion once in Railway.
- Ensure `GEMINI_API_KEY` is set because both ingestion and query embeddings use Gemini.

## Phase 12: Verification

- Run dependency sync:

```powershell
uv sync
```

- Compile Python files:

```powershell
uv run python -m compileall app.py ingest.py src
```

- Run unit tests:

```powershell
uv run pytest
```

- Ingest the Arsenal FC Wikipedia source:

```powershell
uv run python ingest.py --reset
```

- Start local app:

```powershell
uv run chainlit run app.py -w
```

- Test:
  - answerable Arsenal FC question.
  - unanswerable question.
  - prompt-injection attempt.
  - overly long question.
  - missing ChromaDB index.
  - Ollama unavailable locally.
  - answers include the retrieved wiki source section.
  - LangWatch traces when enabled.

## Deferred Work

- Add Railway deployment notes or config after deployment settings are finalized.
- Add automated evaluation runner.
- Add Ragas as an optional offline evaluation framework if needed.
- Add authentication if the demo becomes public beyond controlled testing.
