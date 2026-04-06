from __future__ import annotations
import json, re
from dataclasses import dataclass
from app.models.news import Sentiment


@dataclass
class ParsedAnalysis:
    score: int
    sentiment: Sentiment
    summary: str
    reasoning: str
    suggestion: str
    portfolio_note: str | None = None


def parse_llm_output(raw: str) -> ParsedAnalysis:
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    match = re.search(r"\{[\s\S]+\}", cleaned)
    if not match:
        raise ValueError(f"No JSON found in LLM output: {cleaned[:200]}")
    data = json.loads(match.group())
    score = max(1, min(10, int(data.get("score", 5))))
    sent = str(data.get("sentiment", "neutral")).lower()
    if sent not in ("bullish", "bearish", "neutral"):
        sent = "neutral"
    return ParsedAnalysis(
        score=score,
        sentiment=Sentiment(sent),
        summary=str(data.get("summary", ""))[:256],
        reasoning=str(data.get("reasoning", ""))[:1024],
        suggestion=str(data.get("suggestion", ""))[:512],
        portfolio_note=data.get("portfolio_note") or None,
    )
