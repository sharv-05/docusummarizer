"""Typed output contracts for the meeting-intelligence report."""
from typing import Literal

from pydantic import BaseModel, Field


class Decision(BaseModel):
    decision: str
    speaker: str = "Unknown"
    context: str = ""
    confidence: float = Field(default=0.7, ge=0, le=1)


class ActionItem(BaseModel):
    task: str
    owner: str = "Unassigned"
    deadline: str = "Not specified"
    status: Literal["open", "blocked", "done", "unknown"] = "open"
    confidence: float = Field(default=0.7, ge=0, le=1)


class RiskFlag(BaseModel):
    risk: str
    severity: Literal["low", "medium", "high"] = "medium"
    owner: str = "Unassigned"
    mitigation: str = "Review with the meeting owner"


class TopicCluster(BaseModel):
    topic: str
    summary: str
    mentions: int = Field(default=1, ge=0)


class MeetingExtraction(BaseModel):
    title: str = "Meeting intelligence brief"
    date: str = "Not specified"
    executive_summary: str
    decisions: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    risks: list[RiskFlag] = Field(default_factory=list)
    topics: list[TopicCluster] = Field(default_factory=list)
    speakers: list[str] = Field(default_factory=list)
    source_words: int = 0
    chunks: int = 0
    model: str = "mock"
