from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class Sentiment(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class NewsSource(str, Enum):
    JIN10 = "jin10"
    CLS = "cls"
    CCTV_FINANCE = "cctv_finance"
    REUTERS = "reuters"
    BLOOMBERG = "bloomberg"
    UNKNOWN = "unknown"


class NewsItem(SQLModel, table=True):
    __tablename__ = "news_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    guid: str = Field(index=True, unique=True, max_length=512)
    title: str = Field(max_length=1024)
    content: Optional[str] = Field(default=None)
    source: NewsSource = Field(default=NewsSource.UNKNOWN)
    source_url: Optional[str] = Field(default=None, max_length=1024)
    pub_time: datetime = Field(index=True)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    is_analyzed: bool = Field(default=False)


class NewsItemRead(SQLModel):
    id: int
    guid: str
    title: str
    content: Optional[str]
    source: NewsSource
    source_url: Optional[str]
    pub_time: datetime
    fetched_at: datetime
    is_analyzed: bool


class NewsItemList(SQLModel):
    items: list[NewsItemRead]
    total: int


class FlashItemRead(SQLModel):
    id: int
    title: str
    content: Optional[str]
    source: NewsSource
    source_url: Optional[str]
    pub_time: datetime
    fetched_at: datetime
