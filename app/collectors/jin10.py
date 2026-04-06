from __future__ import annotations

from app.collectors.base import RSSCollector, build_rsshub_url
from app.models.news import NewsSource


class Jin10Collector(RSSCollector):
    source = NewsSource.JIN10
    feed_urls = [
        build_rsshub_url("/jin10/telegraph"),
    ]
