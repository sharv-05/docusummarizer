"""End-to-end ingestion, chunking, summarization, and extraction orchestration."""
from __future__ import annotations

import os

from .chunking import chunk_transcript
from .ingestion import detect_speakers, validate_word_limit
from .llm import TokenLedger, extract_structured, summarize_chunk


def run_pipeline(text: str, chunk_size: int = 1400, overlap: int = 180):
    """Process up to MAX_WORDS and return a validated report plus token ledger."""
    source_words = validate_word_limit(text, int(os.getenv("MAX_WORDS", "50000")))
    chunks = chunk_transcript(text, chunk_size, overlap)
    if not chunks:
        raise ValueError("No transcript chunks were produced.")

    ledger = TokenLedger()
    summaries = [summarize_chunk(chunk.text, chunk.index + 1, ledger) for chunk in chunks]
    context = "\n\n".join(f"Chunk {index + 1}: {summary}" for index, summary in enumerate(summaries))
    result = extract_structured(text, context, ledger)
    return result.model_copy(update={
        "chunks": len(chunks),
        "source_words": source_words,
        "speakers": detect_speakers(text) or result.speakers,
    }), ledger
