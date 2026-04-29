from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape

import feedparser
import httpx

from app.config import get_settings
from app.models.news import NewsSource

settings = get_settings()


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
            normalized_title = " ".join(self.title.split()).strip().lower()
            normalized_pub_time = self.pub_time
            if normalized_pub_time.tzinfo is not None:
                normalized_pub_time = normalized_pub_time.astimezone(timezone.utc).replace(tzinfo=None)
            normalized_pub_time = normalized_pub_time.replace(microsecond=0).isoformat()
            self.guid = hashlib.sha256(
                f"{normalized_title}|{normalized_pub_time}".encode("utf-8")
            ).hexdigest()[:64]


class BaseCollector(ABC):
    source: NewsSource = NewsSource.UNKNOWN
    feed_urls: list[str] = []

    @abstractmethod
    async def fetch(self) -> list[RawNewsItem]: ...

    def _parse_time(self, time_struct=None, raw_time: str | None = None) -> datetime:
        if time_struct:
            return datetime(*time_struct[:6])
        if raw_time:
            try:
                parsed = parsedate_to_datetime(raw_time)
                if parsed.tzinfo is not None:
                    parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
                return parsed
            except (TypeError, ValueError, IndexError):
                pass
        return datetime.utcnow()


class RSSCollector(BaseCollector):
    client_timeout: int = 15
    follow_redirects: bool = True

    async def fetch(self) -> list[RawNewsItem]:
        items: list[RawNewsItem] = []
        async with httpx.AsyncClient(
            timeout=self.client_timeout,
            follow_redirects=self.follow_redirects,
            headers={"User-Agent": "finai-flash/0.1"},
        ) as client:
            for url in self.feed_urls:
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    feed = feedparser.parse(response.text)
                    for entry in feed.entries:
                        title = entry.get("title", "").strip()
                        if not title:
                            continue
                        items.append(
                            RawNewsItem(
                                title=title,
                                content=self._extract_content(entry, title),
                                url=entry.get("link", url),
                                pub_time=self._parse_time(
                                    entry.get("published_parsed") or entry.get("updated_parsed"),
                                    entry.get("published") or entry.get("updated"),
                                ),
                                source=self.source,
                            )
                        )
                except Exception as exc:
                    print(f"[{self.__class__.__name__}] fetch error {url}: {exc}")
        return items

    @staticmethod
    def _extract_content(entry, fallback_title: str) -> str:
        raw = (
            entry.get("summary")
            or entry.get("description")
            or fallback_title
        )
        return clean_feed_text(raw)


def clean_feed_text(value: str) -> str:
    text = unescape(str(value or ""))
    text = re.sub(r"<img\b[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_rsshub_url(path: str) -> str:
    normalized_path = path if path.startswith("/") else f"/{path}"
    return f"{settings.normalized_rsshub_base_url()}{normalized_path}"
