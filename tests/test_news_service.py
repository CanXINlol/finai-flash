from __future__ import annotations

from datetime import datetime

import pytest
from sqlmodel import select

from app.collectors.base import RawNewsItem
from app.models.news import NewsItem, NewsSource
from app.services.news_service import NewsService


@pytest.mark.asyncio
async def test_ingest_deduplicates_by_title_and_pub_time(session):
    service = NewsService(session)
    pub_time = datetime(2024, 1, 1, 12, 0, 0)

    first = RawNewsItem(
        title="OPEC announces new output target",
        content="First version",
        url="https://example.com/first",
        pub_time=pub_time,
        source=NewsSource.JIN10,
    )
    duplicate = RawNewsItem(
        title="OPEC announces new output target",
        content="Second version",
        url="https://example.com/second",
        pub_time=pub_time,
        source=NewsSource.CLS,
    )

    inserted = await service.ingest(first)
    skipped = await service.ingest(duplicate)
    result = await session.execute(select(NewsItem))

    assert inserted is not None
    assert skipped is None
    assert len(result.scalars().all()) == 1
