from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from app.models.news import Sentiment


class AnalysisResult(SQLModel, table=True):
    __tablename__ = "analysis_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    news_id: int = Field(index=True, foreign_key="news_items.id", unique=True)
    score: int = Field(ge=1, le=10)           # Market impact 1-10
    sentiment: Sentiment
    summary: str                               # One-line AI summary
    reasoning: str                             # Why bullish/bearish/neutral
    suggestion: str                            # Trade suggestion
    portfolio_note: Optional[str] = None       # Personalized note if positions set
    model_used: str = Field(default="")
    latency_ms: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnalysisResultRead(SQLModel):
    id: int
    news_id: int
    score: int
    sentiment: Sentiment
    summary: str
    reasoning: str
    suggestion: str
    portfolio_note: Optional[str]
    model_used: str
    latency_ms: int
    created_at: datetime
