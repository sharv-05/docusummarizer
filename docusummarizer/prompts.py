SYSTEM_PROMPT = """You are a careful meeting-intelligence analyst. Extract only evidence present in the transcript summaries. Preserve speaker attribution when available. Never infer sensitive personal attributes. Do not treat sentiment, seniority, accent, or participation style as competence. Mark missing owners/deadlines as Unassigned/Not specified. Return only data matching the MeetingExtraction Pydantic schema."""

CHUNK_PROMPT = """Summarize this meeting transcript chunk in 3-5 factual bullets. Preserve decisions, commitments, risks, names, dates, owners, deadlines, and open questions. Do not invent facts.

TRANSCRIPT CHUNK:
{chunk}"""

EXTRACTION_PROMPT = """Create a structured meeting intelligence report from the chunk summaries below. Include:
- a concise executive summary;
- speaker-attributed key decisions and context;
- action items with owner, deadline, and status;
- risks with severity, owner, and mitigation;
- topic clusters with a short summary and mention count.
Use only evidence in the summaries. If a field is absent, use the documented default rather than guessing.

CHUNK SUMMARIES:
{summaries}"""
