import os
import re
from typing import Any

from .models import MeetingExtraction
from .prompts import SYSTEM_PROMPT


class TokenLedger:
    def __init__(self):
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
        input_price = float(
            input_rate
            if input_rate is not None
            else os.getenv("COST_PER_1K_INPUT", "0.00015")
        )
        output_price = float(
            output_rate
            if output_rate is not None
            else os.getenv("COST_PER_1K_OUTPUT", "0.0006")
        )
        cost = input_tokens / 1000 * input_price + output_tokens / 1000 * output_price
        self.rows.append(
            {
                "step": step,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": round(cost, 6),
                "model": model,
            }
        )

    @property
    def total_tokens(self) -> int:
        return sum(row["input_tokens"] + row["output_tokens"] for row in self.rows)

    @property
    def total_cost(self) -> float:
        return round(sum(row["estimated_cost_usd"] for row in self.rows), 6)


def _mock_extract(text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    speakers: list[str] = []
    for line in lines:
        if ":" in line:
            speaker = line.split(":", 1)[0].strip()
            if len(speaker) < 40 and speaker not in speakers:
                speakers.append(speaker)

    sentences = re.split(r"(?<=[.!?])\s+", text)
    decisions: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []
    topics: list[dict[str, Any]] = []

    for sentence in sentences:
        if not sentence.strip():
            continue
        lower = sentence.lower()
        speaker = sentence.split(":", 1)[0].strip() if ":" in sentence else "Unknown"
        if any(word in lower for word in ("decide", "agreed", "approved", "will use", "chosen", "go with")):
            decisions.append(
                {
                    "decision": sentence,
                    "speaker": speaker,
                    "context": "Extracted from transcript",
                    "confidence": 0.86,
                }
            )
        if any(word in lower for word in ("action", "todo", "will ", "owner", "follow up", "send ", "prepare ", "schedule ")):
            owner = "Unassigned"
            owner_match = re.search(
                r"(?:owner|by|for)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)",
                sentence,
            )
            if owner_match:
                owner = owner_match.group(1)
            actions.append(
                {
                    "task": sentence,
                    "owner": owner,
                    "deadline": "Not specified",
                    "status": "open",
                    "confidence": 0.78,
                }
            )
        if any(word in lower for word in ("risk", "blocked", "concern", "delay", "issue", "dependency", "uncertain")):
            risks.append(
                {
                    "risk": sentence,
                    "severity": "high"
                    if any(word in lower for word in ("critical", "blocked", "security"))
                    else "medium",
                    "owner": "Unassigned",
                    "mitigation": "Review and assign a mitigation owner",
                }
            )

    keyword_groups = {
        "Product": ("product", "feature", "customer", "user"),
        "Engineering": ("api", "model", "data", "deploy", "system"),
        "Planning": ("timeline", "launch", "milestone", "budget"),
    }
    lower_text = text.lower()
    for topic, keywords in keyword_groups.items():
        mentions = sum(lower_text.count(keyword) for keyword in keywords)
        if mentions:
            topics.append(
                {
                    "topic": topic,
                    "summary": f"{topic} was discussed across the transcript.",
                    "mentions": mentions,
                }
            )

    summary = " ".join(sentence.strip() for sentence in sentences[:3]).strip()[:900]
    return {
        "title": "Meeting intelligence brief",
        "date": "Not specified",
        "executive_summary": summary or text[:900],
        "decisions": decisions[:12],
        "action_items": actions[:20],
        "risks": risks[:12],
        "topics": topics,
        "speakers": speakers,
        "model": "mock",
    }


def _live_extract(context: str) -> MeetingExtraction:
    """Call the configured LangChain provider and require a Pydantic result."""
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    structured_llm = llm.with_structured_output(MeetingExtraction)
    result = structured_llm.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=context)]
    )
    if isinstance(result, MeetingExtraction):
        return result
    return MeetingExtraction.model_validate(result)


def extract_structured(
    source_text: str,
    context: str,
    ledger: TokenLedger,
    model: str = "mock",
) -> MeetingExtraction:
    """Extract a typed meeting report, preferring the live provider when configured.

    The function always returns a valid ``MeetingExtraction``. Live provider or parsing
    failures are retried once, then safely fall back to deterministic extraction so a
    transient API error cannot take down the Streamlit workflow.
    """
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    input_tokens = max(1, len(context.split()) * 4)

    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        for attempt in range(2):
            try:
                live_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                result = _live_extract(context)
                output_tokens = max(1, len(result.model_dump_json().split()) * 4)
                ledger.add(
                    "structured_extraction",
                    input_tokens,
                    output_tokens,
                    model=live_model,
                )
                return result.model_copy(
                    update={
                        "source_words": len(source_text.split()),
                        "model": live_model,
                    }
                )
            except Exception:
                if attempt == 1:
                    break

    fallback = MeetingExtraction.model_validate(_mock_extract(source_text))
    ledger.add("structured_extraction", input_tokens, 350, model=model)
    return fallback.model_copy(
        update={"source_words": len(source_text.split()), "model": model}
    )
