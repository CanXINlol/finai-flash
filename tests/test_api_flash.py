from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.models.news import NewsItem, NewsSource


@pytest.mark.asyncio
async def test_flash_endpoint_returns_latest_10(client, session):
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    for index in range(12):
        session.add(
            NewsItem(
                guid=f"flash-guid-{index}",
                title=f"Flash {index}",
                content=f"Content {index}",
                source=NewsSource.CLS,
                pub_time=base_time + timedelta(minutes=index),
            )
        )
    await session.commit()

    response = await client.get("/api/flash")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10
    assert data[0]["title"] == "Flash 11"
    assert data[-1]["title"] == "Flash 2"
