from __future__ import annotations

from app.models.news import Sentiment
from app.services.analysis_service import AnalysisService


def test_analysis_service_maps_sentiment_and_score():
    assert AnalysisService._map_sentiment("利多") == Sentiment.BULLISH
    assert AnalysisService._map_sentiment("bearish") == Sentiment.BEARISH
    assert AnalysisService._map_sentiment("unknown") == Sentiment.NEUTRAL

    assert AnalysisService._map_impact_score(0) == 1
    assert AnalysisService._map_impact_score(1) == 1
    assert AnalysisService._map_impact_score(85) == 9
    assert AnalysisService._map_impact_score(100) == 10


def test_analysis_service_formats_positions():
    positions = [
        {"ticker": "CL", "name": "原油多单", "quantity": 2},
        {"ticker": "XAUUSD", "name": "黄金", "quantity": 0},
        {"ticker": "GC", "name": "", "quantity": 1.5},
    ]

    labels = AnalysisService._position_labels(positions)

    assert labels == [
        "原油多单 (CL) x2",
        "黄金 (XAUUSD)",
        "GC x1.5",
    ]
