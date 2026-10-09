"""LLM provider boundary, token accounting, and deterministic demo extraction."""
from __future__ import annotations

import os
import re
from typing import Any, Callable

from .models import MeetingExtraction
from .prompts import CHUNK_PROMPT, EXTRACTION_PROMPT, SYSTEM_PROMPT


class TokenLedger:
    """Per-call token and estimated cost accounting for the UI and exports."""

    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def add(
        self,
        step: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "mock",
        input_rate: float | None = None,
        output_rate: float | None = None,
    ) -> None:
        input_price = float(input_rate if input_rate is not None else os.getenv("COST_PER_1K_INPUT", "0.00015"))
        output_price = float(output_rate if output_rate is not None else os.getenv("COST_PER_1K_OUTPUT", "0.0006"))
        cost = input_tokens / 1000 * input_price + output_tokens / 1000 * output_price
        self.rows.append({
            "step": step,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "estimated_cost_usd": round(cost, 6),
            "model": model,
        })

    @property
    def total_tokens(self) -> int:
        return sum(row["input_tokens"] + row["output_tokens"] for row in self.rows)

    @property
    def total_cost(self) -> float:
        return round(sum(row["estimated_cost_usd"] for row in self.rows), 6)


def _word_tokens(value: str) -> int:
    return max(1, len(value.split()) * 4 // 3)


def _mock_chunk_summary(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    return " ".join(sentence for sentence in sentences[:5] if sentence).strip()[:900] or text[:900]


def _mock_extract(text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    speakers: list[str] = []
    for line in lines:
        if ":" in line:
            speaker = line.split(":", 1)[0].strip()
            if 1 < len(speaker) < 40 and speaker not in speakers:
                speakers.append(speaker)

    sentences = re.split(r"(?<=[.!?])\s+", text)
    decisions: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []
    topics: list[dict[str, Any]] = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        lower = sentence.lower()
        speaker = sentence.split(":", 1)[0].strip() if ":" in sentence else "Unknown"
        if any(word in lower for word in ("decide", "agreed", "approved", "will use", "chosen", "go with")):
            decisions.append({"decision": sentence, "speaker": speaker, "context": "Evidence from transcript", "confidence": 0.86})
        if any(word in lower for word in ("action", "todo", "will ", "owner", "follow up", "send ", "prepare ", "schedule ")):
            owner = "Unassigned"
            owner_match = re.search(r"(?:owner|by|for)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)", sentence)
            if owner_match:
                owner = owner_match.group(1)
            deadline_match = re.search(r"\b(?:by|before|on)\s+([^,.]+)", sentence, re.I)
            actions.append({"task": sentence, "owner": owner, "deadline": deadline_match.group(1).strip() if deadline_match else "Not specified", "status": "open", "confidence": 0.78})
        if any(word in lower for word in ("risk", "blocked", "concern", "delay", "issue", "dependency", "uncertain")):
            risks.append({"risk": sentence, "severity": "high" if any(word in lower for word in ("critical", "blocked", "security")) else "medium", "owner": "Unassigned", "mitigation": "Review and assign a mitigation owner"})

    keyword_groups = {
        "Product": ("product", "feature", "customer", "user"),
        "Engineering": ("api", "model", "data", "deploy", "system"),
        "Planning": ("timeline", "launch", "milestone", "budget"),
    }
    lower_text = text.lower()
    for topic, keywords in keyword_groups.items():
        mentions = sum(lower_text.count(keyword) for keyword in keywords)
        if mentions:
            topics.append({"topic": topic, "summary": f"{topic} was discussed across the transcript.", "mentions": mentions})

    summary = " ".join(sentence.strip() for sentence in sentences[:4]).strip()[:1000]
    return {
        "title": "Meeting intelligence brief",
        "date": "Not specified",
        "executive_summary": summary or text[:1000],
        "decisions": decisions[:12],
        "action_items": actions[:20],
        "risks": risks[:12],
        "topics": topics,
        "speakers": speakers,
        "model": "mock",
    }


def _openai_model():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)


def _invoke_with_retry(invoke: Callable[[], Any], attempts: int = 2) -> Any:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            return invoke()
        except Exception as error:  # provider and parser errors are recoverable at this boundary
            last_error = error
    raise RuntimeError("LLM request failed after retry") from last_error


def summarize_chunk(text: str, index: int, ledger: TokenLedger) -> str:
    """Summarize one chunk, or use a bounded deterministic summary in demo mode."""
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        from langchain_core.messages import HumanMessage, SystemMessage
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        result = _invoke_with_retry(lambda: _openai_model().invoke([
            SystemMessage(content="You summarize meeting transcript chunks factually. Preserve names, dates, decisions, risks, and commitments."),
            HumanMessage(content=CHUNK_PROMPT.format(chunk=text)),
        ]))
        summary = result.content if isinstance(result.content, str) else str(result.content)
        ledger.add(f"chunk_summary_{index}", _word_tokens(text), _word_tokens(summary), model=model)
        return summary.strip()
    summary = _mock_chunk_summary(text)
    ledger.add(f"chunk_summary_{index}", _word_tokens(text), _word_tokens(summary), model="mock")
    return summary


def extract_structured(source_text: str, context: str, ledger: TokenLedger, model: str = "mock") -> MeetingExtraction:
    """Return a validated extraction, retrying provider/parser failures before fallback."""
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    input_tokens = _word_tokens(context)
    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            live_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            structured_llm = _openai_model().with_structured_output(MeetingExtraction)
            result = _invoke_with_retry(lambda: structured_llm.invoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=EXTRACTION_PROMPT.format(summaries=context)),
            ]))
            parsed = result if isinstance(result, MeetingExtraction) else MeetingExtraction.model_validate(result)
            ledger.add("structured_extraction", input_tokens, _word_tokens(parsed.model_dump_json()), model=live_model)
            return parsed.model_copy(update={"source_words": len(source_text.split()), "model": live_model})
        except Exception:
            # A malformed response or transient provider error must not take down the UI.
            pass
    fallback = MeetingExtraction.model_validate(_mock_extract(source_text))
    ledger.add("structured_extraction", input_tokens, 350, model=model)
    return fallback.model_copy(update={"source_words": len(source_text.split()), "model": model})
