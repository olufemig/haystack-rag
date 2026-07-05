# Arsenal FC Wiki RAG Chatbot

Ask questions about the indexed Arsenal FC Wikipedia knowledge base.

This demo answers only from retrieved Arsenal FC wiki context. If the indexed source does not contain enough information, it returns:

```text
I don't know based on the available documents.
```

The interface is question-only. Wiki ingestion is handled separately with `ingest.py`.

Responses include the retrieved wiki source below the answer for transparency.
