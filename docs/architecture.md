# Architecture and data flow

```mermaid
flowchart LR
  Upload[TXT / DOCX / PDF] --> Ingest[Normalize text + detect speakers]
  Ingest --> Chunk[Recursive speaker-aware chunking]
  Chunk --> Summaries[Chunk summaries]
  Summaries --> Merge[Global context / prompt chain]
  Merge --> Parse[Pydantic structured parser + retry boundary]
  Parse --> UI[Streamlit tabs]
  Parse --> JSON[JSON export]
  Parse --> PDF[ReportLab PDF]
  Chunk --> Ledger[Token/cost ledger]
  Merge --> Ledger
```

The default provider is deterministic mock mode so the demo works without a paid key. When `LLM_PROVIDER=openai` and `OPENAI_API_KEY` are set, the provider boundary uses LangChain structured output support. Parse/provider failures fall back to the local extraction path rather than crashing the UI.
