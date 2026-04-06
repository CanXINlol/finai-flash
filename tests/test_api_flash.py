from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.models.analysis import AnalysisResult
from app.models.news import NewsItem, NewsSource, Sentiment


@pytest.mark.asyncio
async def test_flash_endpoint_returns_latest_10(client, session):
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    for index in range(12):
        item = NewsItem(
            guid=f"flash-guid-{index}",
            title=f"Flash {index}",
            content=f"Content {index}",
            source=NewsSource.CLS,
            pub_time=base_time + timedelta(minutes=index),
        )
        session.add(item)
        await session.flush()
        if index in (10, 11):
            session.add(
                AnalysisResult(
                    news_id=item.id,
                    score=8,
                    sentiment=Sentiment.BULLISH,
                    summary=f"Summary {index}",
                    reasoning=f"Reasoning {index}",
                    suggestion=f"Suggestion {index}",
                    portfolio_note=None,
                    model_used="qwen2.5:7b",
                    latency_ms=1234,
                )
            )
    await session.commit()

    response = await client.get("/api/flash")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10
    assert data[0]["title"] == "Flash 11"
    assert data[-1]["title"] == "Flash 2"
    assert data[0]["analysis"]["summary"] == "Summary 11"
    assert data[0]["analysis"]["sentiment"] == "bullish"
    assert data[1]["analysis"]["summary"] == "Summary 10"
    assert data[2]["analysis"] is None
