from __future__ import annotations

from app.ai.flash_analyzer import FlashAnalyzer
from app.models.flash_analysis import FlashAnalysis, FlashAnalyzeRequest


def test_flash_analysis_normalizes_sentiment_and_assets():
    result = FlashAnalysis.model_validate(
        {
            "summary": "油价短线受提振。",
            "impact_score": 120,
            "bullish_bearish": "bullish",
            "affected_assets": "原油, 黄金",
            "trading_suggestion": "关注原油回踩做多机会。",
            "historical_reference": "类似2023年OPEC减产预期升温时的表现。",
        }
    )
    assert result.impact_score == 100
    assert result.bullish_bearish == "利多"
    assert result.affected_assets == ["原油", "黄金"]


def test_flash_analyze_request_normalizes_positions():
    request = FlashAnalyzeRequest.model_validate(
        {
            "text": "美联储讲话偏鸽。",
            "positions": [" 黄金 ", "", "纳指多单"],
        }
    )
    assert request.positions == ["黄金", "纳指多单"]


def test_flash_analyzer_extracts_json_from_fenced_output():
    raw = """```json
    {
      "summary": "美元走强压制黄金。",
      "impact_score": 72,
      "bullish_bearish": "利空",
      "affected_assets": ["黄金", "美元指数"],
      "trading_suggestion": "短线回避黄金追多，观察1-3个交易日并设置止损。",
      "historical_reference": "类似2022年美联储鹰派表态后的黄金承压行情。"
    }
    ```"""
    result = FlashAnalyzer._parse_output(raw)
    assert result.bullish_bearish == "利空"
    assert result.impact_score == 72
