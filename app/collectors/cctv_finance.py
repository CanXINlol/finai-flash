from __future__ import annotations

from app.collectors.base import RSSCollector, build_rsshub_url
from app.models.news import NewsSource


class CCTVFinanceCollector(RSSCollector):
    source = NewsSource.CCTV_FINANCE
    feed_urls = [
        build_rsshub_url("/cctv/lm/jjbxs"),
    ]
