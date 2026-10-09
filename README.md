# DocuSummarizer — AI-Powered Meeting Intelligence

DocuSummarizer turns raw `.txt`, `.docx`, and `.pdf` meeting transcripts into a structured, reviewable intelligence packet: executive summary, speaker-attributed decisions, owner/deadline action items, topic clusters, and risk flags.

## Highlights

- Streamlit UI with upload, processing status, tabbed results, and exports
- Handles transcripts up to 50,000 words with speaker-aware recursive chunking and overlap
- LangChain `RecursiveCharacterTextSplitter` when installed, with a safe local fallback
- Pydantic structured output models and retry-safe parsing
- OpenAI-compatible live provider behind environment variables; deterministic mock mode by default
- Token budget and cost estimates tracked per pipeline step
- ReportLab PDF and JSON export
- ROUGE-1/2/L evaluation helpers and manual quality rubric
- Pytest suite using mocked/deterministic responses

## Quick start (demo mode, no API key)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the URL printed by Streamlit, upload a transcript, or click **Load sample transcript**. Demo mode (`LLM_PROVIDER=mock`) does not call external services.

## Live LLM mode

```bash
cp .env.example .env
# Set LLM_PROVIDER=openai and OPENAI_API_KEY in .env
streamlit run app.py
```

The API key is loaded only by the Python process and is never embedded in exported JSON, the browser, or source control. The default model is `gpt-4o-mini`; Gemini can be added behind the same provider boundary.

## Docker

```bash
docker build -t docusummarizer .
docker run --rm -p 8501:8501 --env-file .env docusummarizer
```

## Project layout

- `app.py` — Streamlit UI
- `docusummarizer/ingestion.py` — `.txt`, `.docx`, `.pdf` parsing and normalization
- `docusummarizer/chunking.py` — speaker-aware chunking and token estimates
- `docusummarizer/models.py` — Pydantic extraction schema
- `docusummarizer/prompts.py` — documented prompt templates and bias/safety guardrails
- `docusummarizer/llm.py` — mock/live provider boundary and retry-safe structured extraction
- `docusummarizer/pipeline.py` — end-to-end orchestration and cost ledger
- `docusummarizer/export.py` — JSON and branded ReportLab PDF
- `docusummarizer/evaluation.py` — ROUGE metrics and manual rubric
- `samples/` — five sample meeting transcripts
- `docs/` — architecture, prompt decisions, and demo walkthrough

## Evaluation

```bash
pytest -q
python -m docusummarizer.evaluation
```

The evaluator compares generated summaries to reference summaries with ROUGE-1/2/L and records a manual rubric for attribution, completeness, and actionability. See `docs/evaluation.md`.
