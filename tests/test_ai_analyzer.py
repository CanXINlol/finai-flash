from __future__ import annotations
import pytest
import json
from unittest.mock import AsyncMock, patch
from app.ai.analyzer import NewsAnalyzer
from app.ai.parser import parse_llm_output
from app.models.news import Sentiment

MOCK_RESPONSE = json.dumps({
    "score": 8,
    "sentiment": "bullish",
    "summary": "Fed pauses rate hikes, markets rally",
    "reasoning": "Rate pause signals easing monetary policy, positive for equities and growth stocks.",
    "suggestion": "Consider adding equity exposure. Confidence: High.",
    "portfolio_note": None,
})


def test_parse_llm_output_valid():
    parsed = parse_llm_output(MOCK_RESPONSE)
    assert parsed.score == 8
    assert parsed.sentiment == Sentiment.BULLISH
    assert "Fed" in parsed.summary


def test_parse_llm_output_with_markdown_fence():
    fenced = f"```json\n{MOCK_RESPONSE}\n```"
    parsed = parse_llm_output(fenced)
    assert parsed.score == 8


def test_parse_llm_output_clamps_score():
    bad = json.dumps({"score": 99, "sentiment": "bullish",
                      "summary": "x", "reasoning": "x", "suggestion": "x"})
    parsed = parse_llm_output(bad)
    assert parsed.score == 10


@pytest.mark.asyncio
async def test_analyzer_calls_ollama():
    analyzer = NewsAnalyzer()
    with patch.object(analyzer.client, "generate", new=AsyncMock(return_value=MOCK_RESPONSE)):
        parsed, latency = await analyzer.analyze(
            title="Fed pauses",
            content="The Fed held rates.",
            pub_time="2024-01-01",
            source="reuters",
        )
    assert parsed.score == 8
    assert latency >= 0
