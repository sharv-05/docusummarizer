"""Speaker-aware recursive transcript chunking with a dependency-free fallback."""
from __future__ import annotations

import re
from dataclasses import dataclass

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except Exception:  # pragma: no cover - exercised when optional dependency is absent
    RecursiveCharacterTextSplitter = None


@dataclass
class Chunk:
    index: int
    text: str
    words: int
    estimated_tokens: int


def _speaker_boundaries(text: str) -> str:
    return re.sub(r"(?m)^(?=[A-Za-z][A-Za-z ._-]{1,40}:)", "\n", text)


def chunk_transcript(text: str, chunk_size: int = 1400, overlap: int = 180) -> list[Chunk]:
    if chunk_size < 100:
        raise ValueError("chunk_size must be at least 100 characters.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size.")
    prepared = _speaker_boundaries(text)
    if RecursiveCharacterTextSplitter:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", "? ", "! ", " "],
        )
        parts = splitter.split_text(prepared)
    else:
        parts = []
        start = 0
        while start < len(prepared):
            end = min(len(prepared), start + chunk_size)
            parts.append(prepared[start:end])
            if end == len(prepared):
                break
            start = end - overlap
    return [Chunk(i, part.strip(), len(part.split()), max(1, len(part.split()) * 4 // 3)) for i, part in enumerate(parts) if part.strip()]
