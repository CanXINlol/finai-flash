from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class AlertLog(SQLModel, table=True):
    """Records every alert that was dispatched."""
    __tablename__ = "alert_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    news_id: int = Field(index=True)
    analysis_id: int
    channel: str = Field(max_length=32)    # "telegram" | "discord"
    status: str = Field(max_length=16)     # "sent" | "failed"
    error: Optional[str] = None
    sent_at: datetime = Field(default_factory=datetime.utcnow)


# all models exported for easy import
__all__ = ["AlertLog"]
