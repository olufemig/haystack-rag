# PDF RAG Chatbot

Ask questions about the indexed PDF knowledge base.

This demo answers only from retrieved PDF context. If the documents do not contain enough information, it returns:

```text
I don't know based on the available documents.
```

The interface is question-only. PDF ingestion is handled separately with `ingest.py`.
