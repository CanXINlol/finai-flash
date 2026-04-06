from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest


def build_analyzer_mock(models: list[str] | None = None) -> Mock:
    analyzer = Mock()
    analyzer.switch_model = Mock()
    analyzer.health_check = AsyncMock(
        return_value={
            "ok": True,
            "available_models": models or ["qwen2.5:7b", "qwen2.5:14b"],
        }
    )
    return analyzer


@pytest.mark.asyncio
async def test_settings_api_returns_defaults(client):
    with patch(
        "app.services.settings_service.get_flash_analyzer",
        return_value=build_analyzer_mock(),
    ):
        response = await client.get("/api/v1/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "qwen2.5:7b"
    assert data["auto_analyze_flash"] is True
    assert data["live_market_quotes"] is True
    assert data["collect_interval_seconds"] == 300
    assert data["available_models"] == ["qwen2.5:7b", "qwen2.5:14b"]


@pytest.mark.asyncio
async def test_settings_api_persists_updates(client):
    with patch(
        "app.services.settings_service.get_flash_analyzer",
        return_value=build_analyzer_mock(["qwen2.5:7b", "deepseek-r1:14b"]),
    ):
        update_response = await client.patch(
            "/api/v1/settings",
            json={
                "model": "deepseek-r1:14b",
                "auto_analyze_flash": False,
                "live_market_quotes": False,
                "collect_interval_seconds": 15,
            },
        )
        read_response = await client.get("/api/v1/settings")

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["model"] == "deepseek-r1:14b"
    assert updated["auto_analyze_flash"] is False
    assert updated["live_market_quotes"] is False
    assert updated["collect_interval_seconds"] == 15

    reread = read_response.json()
    assert reread["model"] == "deepseek-r1:14b"
    assert reread["auto_analyze_flash"] is False
    assert reread["live_market_quotes"] is False
    assert reread["collect_interval_seconds"] == 15
