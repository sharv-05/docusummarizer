# Prompt and quality decisions

- **Evidence-only extraction:** the system prompt forbids invented facts and requires missing owners/deadlines to be explicit.
- **Separate concerns:** chunk summaries keep context bounded; the final structured extractor maps decisions, actions, risks, and topics into typed Pydantic fields.
- **Bias control:** prompts prohibit sensitive-attribute inference and explicitly reject sentiment, accent, seniority, or participation style as competence signals.
- **Retry-safe boundary:** the live provider is wrapped in an exception boundary; malformed/failed output falls back to the deterministic extractor and preserves the token ledger.
- **Cost awareness:** every chunk and extraction step records estimated input/output tokens and an estimated USD cost.
