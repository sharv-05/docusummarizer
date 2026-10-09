# DocuSummarizer — AI-Powered Meeting Intelligence

DocuSummarizer turns raw `.txt`, `.docx`, and `.pdf` meeting transcripts into a structured, reviewable intelligence packet: executive summary, speaker-attributed decisions, owner/deadline action items, topic clusters, and risk flags.

This repository implements the **Code-A-Nova Internship Project Brief — Task 5**. It is intentionally a meeting-intelligence product; it is not the separate HireIQ interview-intelligence platform.

## Features mapped to the brief

- Streamlit upload/review UI for `.txt`, `.docx`, and `.pdf` transcripts
- Normalization and speaker-label detection with a 50,000-word safety limit
- LangChain `RecursiveCharacterTextSplitter` with speaker-aware separators and overlap
- Multi-step LangChain pipeline: chunk summarization → global structured extraction
- Pydantic models for decisions, action items, risks, topic clusters, and report metadata
- OpenAI GPT-4o-mini live mode through environment variables, with two-attempt retry and safe deterministic fallback
- Mock mode by default, so the demo and tests run without an API key or paid provider
- Per-step token estimates, model name, and configurable cost estimates in the UI and JSON export
- Tabbed Streamlit results for summary, decisions, actions, risks/topics, and token ledger
- Branded ReportLab PDF and complete JSON export
- ROUGE-1/2/L evaluation helper over five sample transcripts plus a manual rubric field
- Pytest regression suite covering ingestion, chunking validation, structured extraction, and exports

## Quick start (demo mode, no API key)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the URL printed by Streamlit, upload a transcript, or click **Load sample transcript**. Demo mode (`LLM_PROVIDER=mock`) uses bounded deterministic extraction and does not call external services.

## Live LLM mode

```bash
cp .env.example .env
# Set LLM_PROVIDER=openai and OPENAI_API_KEY in .env
streamlit run app.py
```

The API key is read only by the Python process and is never embedded in exported JSON, the browser, or source control. The default model is `gpt-4o-mini`; provider/model/cost settings are configurable through environment variables.

## Validation

```bash
pytest -q
python -m docusummarizer.evaluation
```

The evaluator runs against five supplied sample transcripts and emits ROUGE-1/2/L plus the rubric fields. Tests use mock mode and do not require network access.

## Docker

```bash
docker build -t docusummarizer .
docker run --rm -p 8501:8501 --env-file .env docusummarizer
```

## Project layout

- `app.py` — Streamlit UI and export controls
- `docusummarizer/ingestion.py` — `.txt`, `.docx`, `.pdf` parsing and normalization
- `docusummarizer/chunking.py` — speaker-aware recursive chunking and token estimates
- `docusummarizer/models.py` — Pydantic extraction schemas
- `docusummarizer/prompts.py` — documented prompt templates and guardrails
- `docusummarizer/llm.py` — LangChain provider boundary, retries, mock mode, and token ledger
- `docusummarizer/pipeline.py` — end-to-end orchestration
- `docusummarizer/export.py` — JSON and branded ReportLab PDF exports
- `docusummarizer/evaluation.py` — ROUGE metrics and rubric output
- `samples/` — five sample meeting transcripts
- `docs/` — architecture, prompt decisions, and demo walkthrough
- `tests/` — pytest regression suite

## Notes on reliability

The repaired `extract_structured` entry point always returns a validated `MeetingExtraction`. Live provider and structured-parser failures are retried once and then fall back to deterministic local extraction, so a transient API or malformed-response error cannot crash the Streamlit workflow.
