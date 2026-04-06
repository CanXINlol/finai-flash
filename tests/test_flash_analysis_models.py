from __future__ import annotations

from app.ai.flash_analyzer import FlashAnalyzer
from app.ai.flash_prompts import build_retry_feedback, default_quality_feedback
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


def test_flash_analyzer_flags_generic_output():
    result = FlashAnalysis.model_validate(
        {
            "summary": "这条新闻可能影响市场情绪。",
            "impact_score": 70,
            "bullish_bearish": "利多",
            "affected_assets": ["原油"],
            "trading_suggestion": "建议关注原油表现，谨慎操作。",
            "historical_reference": "类似之前的事件。",
        }
    )

    issues = FlashAnalyzer._quality_issues(result)

    assert any("summary" in issue for issue in issues)
    assert any("affected_assets" in issue for issue in issues)
    assert any("时间窗口" in issue for issue in issues)
    assert any("年份" in issue for issue in issues)


def test_flash_analyzer_accepts_specific_output():
    result = FlashAnalysis.model_validate(
        {
            "summary": "OPEC+延长减产预期先抬升原油风险溢价，并对通胀交易形成边际支撑。",
            "impact_score": 82,
            "bullish_bearish": "利多",
            "affected_assets": ["原油", "能源股", "黄金"],
            "trading_suggestion": "短线偏多原油，若日内回踩前高不破可分批跟进，观察1-3日；若OPEC+最终否认延长减产或油价跌破消息前低点则止损离场。",
            "historical_reference": "类似2023年4月OPEC+意外减产后，布油在随后数日快速上冲，能源板块同步走强。",
        }
    )

    assert FlashAnalyzer._quality_issues(result) == []


def test_quality_feedback_helpers():
    assert "高质量" in default_quality_feedback()
    retry_feedback = build_retry_feedback(["summary 太空泛", "缺少时间窗口"])
    assert "summary 太空泛" in retry_feedback
    assert "缺少时间窗口" in retry_feedback
