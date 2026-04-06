from __future__ import annotations
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass, field
from app.models.news import NewsSource


@dataclass
class RawNewsItem:
    title: str
    content: str
    url: str
    pub_time: datetime
    source: NewsSource
    guid: str = field(default="")

    def __post_init__(self):
        if not self.guid:
            self.guid = hashlib.sha256(
                f"{self.source}:{self.url}:{self.title}".encode()
            ).hexdigest()[:64]


class BaseCollector(ABC):
    source: NewsSource = NewsSource.UNKNOWN
    feed_urls: list[str] = []

    @abstractmethod
    async def fetch(self) -> list[RawNewsItem]: ...

    def _parse_time(self, time_struct) -> datetime:
        if time_struct:
            return datetime(*time_struct[:6])
        return datetime.utcnow()
