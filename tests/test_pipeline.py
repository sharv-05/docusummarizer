from docusummarizer.ingestion import clean_text, detect_speakers, validate_word_limit
from docusummarizer.chunking import chunk_transcript
from docusummarizer.pipeline import run_pipeline
from docusummarizer.export import extraction_json, extraction_pdf


def test_ingestion_and_speakers():
    text = clean_text("Maya: Agreed.\n\nJon: I will send the report.")
    assert detect_speakers(text) == ["Maya", "Jon"]
    assert validate_word_limit(text) == 8


def test_chunking_handles_long_transcript():
    text = "\n".join([f"Speaker {i % 3}: We discussed the launch and the risk." for i in range(200)])
    chunks = chunk_transcript(text, chunk_size=300, overlap=40)
    assert len(chunks) > 1 and all(chunk.words > 0 for chunk in chunks)


def test_chunking_rejects_invalid_overlap():
    try:
        chunk_transcript("A: hello", chunk_size=200, overlap=200)
    except ValueError as error:
        assert "overlap" in str(error)
    else:
        raise AssertionError("invalid overlap should fail")


def test_mock_pipeline_extracts_structured_fields():
    text = "Maya: We agreed to launch in April.\nJon: I will send the dashboard by Friday.\nMaya: A risk is mobile delay."
    result, ledger = run_pipeline(text, chunk_size=200, overlap=20)
    assert result.decisions and result.action_items and result.risks
    assert result.source_words > 0 and result.chunks > 0 and ledger.total_tokens > 0


def test_exports_are_bytes():
    result, ledger = run_pipeline("Alex: We decided to ship. Sam: I will prepare the runbook.")
    assert extraction_json(result, ledger).startswith(b"{")
    assert extraction_pdf(result, ledger).startswith(b"%PDF")


def test_extract_structured_entry_point_returns_pydantic_model():
    from docusummarizer.llm import TokenLedger, extract_structured
    result = extract_structured("Maya: We agreed to launch in April.", "Maya: We agreed to launch in April.", TokenLedger())
    assert result.executive_summary
    assert result.model == "mock"
