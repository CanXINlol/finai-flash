from __future__ import annotations
import feedparser
import httpx
from datetime import datetime
from app.collectors.base import BaseCollector, RawNewsItem
from app.models.news import NewsSource


class Jin10Collector(BaseCollector):
    """金十数据 RSS 采集器 (via RSSHub public instance)."""
    source = NewsSource.JIN10
    feed_urls = [
        "https://rsshub.app/jin10",
        "https://rsshub.app/jin10/flash",
    ]

    async def fetch(self) -> list[RawNewsItem]:
        items: list[RawNewsItem] = []
        async with httpx.AsyncClient(timeout=15) as client:
            for url in self.feed_urls:
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries:
                        items.append(RawNewsItem(
                            title=entry.get("title", "").strip(),
                            content=entry.get("summary", entry.get("title", "")),
                            url=entry.get("link", url),
                            pub_time=self._parse_time(entry.get("published_parsed")),
                            source=self.source,
                        ))
                except Exception as e:
                    print(f"[Jin10] fetch error {url}: {e}")
        return items
