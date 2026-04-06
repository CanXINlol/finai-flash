"""
app/models/__init__.py
──────────────────────
Re-export all SQLModel table classes so Alembic's env.py can find them
with a single import:  from app.models import *
"""

from app.models.analysis import AnalysisResult, AnalysisResultRead, AnalysisResultSummary, Sentiment
from app.models.news import NewsItem, NewsItemCreate, NewsItemList, NewsItemRead, compute_fingerprint
from app.models.portfolio import AlertRule, AlertRuleCreate, AlertRuleRead, Position, PositionCreate, PositionRead, PositionUpdate

__all__ = [
    # News
    "NewsItem",
    "NewsItemCreate",
    "NewsItemRead",
    "NewsItemList",
    "compute_fingerprint",
    # Analysis
    "AnalysisResult",
    "AnalysisResultRead",
    "AnalysisResultSummary",
    "Sentiment",
    # Portfolio
    "Position",
    "PositionCreate",
    "PositionRead",
    "PositionUpdate",
    "AlertRule",
    "AlertRuleCreate",
    "AlertRuleRead",
]
