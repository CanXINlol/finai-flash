from __future__ import annotations
import pytest
from datetime import datetime
from app.models.news import NewsItem, NewsSource


@pytest.mark.asyncio
async def test_health_endpoint(client):
    from unittest.mock import patch, AsyncMock
    with patch("app.main.get_ollama_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.health_check = AsyncMock(return_value=True)
        mock_get.return_value = mock_client
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_list_news_empty(client):
    resp = await client.get("/api/v1/news")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_list_news_returns_items(client, session):
    item = NewsItem(
        guid="test-guid-001",
        title="Test news headline",
        source=NewsSource.REUTERS,
        pub_time=datetime.utcnow(),
    )
    session.add(item)
    await session.commit()

    resp = await client.get("/api/v1/news")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Test news headline"
