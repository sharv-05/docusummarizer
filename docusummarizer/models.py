from pydantic import BaseModel, Field
from typing import Literal

class Decision(BaseModel):
    decision: str
    speaker: str = "Unknown"
    context: str = ""
    confidence: float = Field(default=0.7, ge=0, le=1)
class ActionItem(BaseModel):
    task: str
    owner: str = "Unassigned"
    deadline: str = "Not specified"
    status: Literal['open','blocked','done','unknown'] = 'open'
    confidence: float = Field(default=0.7, ge=0, le=1)
class RiskFlag(BaseModel):
    risk: str
    severity: Literal['low','medium','high'] = 'medium'
    owner: str = "Unassigned"
    mitigation: str = "Review with the meeting owner"
class TopicCluster(BaseModel):
    topic: str
    summary: str
    mentions: int = 1
class MeetingExtraction(BaseModel):
    title: str = "Meeting intelligence brief"
    date: str = "Not specified"
    executive_summary: str
    decisions: list[Decision] = []
    action_items: list[ActionItem] = []
    risks: list[RiskFlag] = []
    topics: list[TopicCluster] = []
    speakers: list[str] = []
    source_words: int = 0
    chunks: int = 0
    model: str = "mock"
