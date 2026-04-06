from __future__ import annotations

from enum import Enum


class EventType(str, Enum):
    NEWS_ITEM = "news_item"
    ANALYSIS_DONE = "analysis_done"
    ALERT_SENT = "alert_sent"
    SYSTEM = "system"


def news_event(item) -> dict:
    return {
        "type": EventType.NEWS_ITEM,
        "data": {
            "id": item.id,
            "title": item.title,
            "source": item.source,
            "pub_time": str(item.pub_time),
        },
    }


def flash_event(item) -> dict:
    return {
        "type": "flash",
        "data": {
            "id": item.id,
            "title": item.title,
            "content": item.content,
            "source": item.source,
            "source_url": item.source_url,
            "pub_time": item.pub_time.isoformat(),
            "fetched_at": item.fetched_at.isoformat(),
            "is_analyzed": getattr(item, "is_analyzed", False),
            "analysis": None,
        },
    }


def analysis_event(news_id: int, analysis) -> dict:
    return {
        "type": EventType.ANALYSIS_DONE,
        "data": {
            "news_id": news_id,
            "score": analysis.score,
            "sentiment": analysis.sentiment,
            "summary": analysis.summary,
            "suggestion": analysis.suggestion,
            "portfolio_note": analysis.portfolio_note,
        },
    }
