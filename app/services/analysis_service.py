from __future__ import annotations

import math

from sqlalchemy.ext.asyncio import AsyncSession

import app.notifiers.dispatcher as dispatcher
from app.ai.flash_analyzer import get_flash_analyzer
from app.db.crud import analysis as analysis_crud
from app.db.crud import news as news_crud
from app.models.analysis import AnalysisResult
from app.models.flash_analysis import FlashAnalysis
from app.models.news import NewsItem, Sentiment
from app.config import get_settings
from app.websocket.events import analysis_event
from app.websocket.manager import manager

settings = get_settings()


class AnalysisService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.analyzer = get_flash_analyzer()

    async def analyze_news(self, item: NewsItem) -> AnalysisResult | None:
        existing = await analysis_crud.get_by_news_id(self.session, item.id)
        if existing:
            return existing

        position_labels = self._position_labels(settings.parsed_positions())
        selected_model = settings.model

        try:
            parsed, latency_ms, selected_model = await self.analyzer.analyze_with_metadata(
                text=self._build_news_text(item),
                positions=position_labels or None,
                model=selected_model,
            )
        except Exception as exc:
            print(f"[Analysis] flash analyzer error for news {item.id}: {exc}")
            return None

        result = AnalysisResult(
            news_id=item.id,
            score=self._map_impact_score(parsed.impact_score),
            sentiment=self._map_sentiment(parsed.bullish_bearish),
            summary=parsed.summary,
            reasoning=self._build_reasoning(parsed),
            suggestion=parsed.trading_suggestion,
            portfolio_note=self._build_portfolio_note(parsed, position_labels),
            model_used=selected_model,
            latency_ms=latency_ms,
        )
        result = await analysis_crud.create(self.session, result)
        await news_crud.mark_analyzed(self.session, item.id)
        await manager.broadcast(analysis_event(item.id, result))

        if result.score >= settings.alert_score_threshold:
            body = f"{result.reasoning}\n\n{result.suggestion}"
            await dispatcher.dispatch(
                title=item.title,
                body=body,
                score=result.score,
                sentiment=result.sentiment,
            )

        return result

    @staticmethod
    def _build_news_text(item: NewsItem) -> str:
        parts = [item.title.strip()]
        if item.content:
            content = item.content.strip()
            if content and content != item.title.strip():
                parts.append(content)
        return "\n".join(parts)

    @staticmethod
    def _position_labels(positions: list[dict] | None) -> list[str]:
        labels: list[str] = []
        for position in positions or []:
            ticker = str(position.get("ticker") or "").strip()
            name = str(position.get("name") or ticker).strip()
            quantity = position.get("quantity", 0)

            base = name
            if ticker and ticker != name:
                base = f"{name} ({ticker})"

            if quantity not in (None, "", 0, 0.0):
                try:
                    quantity_value = float(quantity)
                    if quantity_value.is_integer():
                        base = f"{base} x{int(quantity_value)}"
                    else:
                        base = f"{base} x{quantity_value:g}"
                except (TypeError, ValueError):
                    base = f"{base} x{quantity}"

            labels.append(base)

        return labels

    @staticmethod
    def _map_sentiment(value: str) -> Sentiment:
        text = str(value or "").strip().lower()
        if "bull" in text or "利多" in text:
            return Sentiment.BULLISH
        if "bear" in text or "利空" in text:
            return Sentiment.BEARISH
        return Sentiment.NEUTRAL

    @staticmethod
    def _map_impact_score(value: int) -> int:
        try:
            impact_score = int(value)
        except (TypeError, ValueError):
            impact_score = 50
        impact_score = max(0, min(100, impact_score))
        if impact_score == 0:
            return 1
        return max(1, min(10, math.ceil(impact_score / 10)))

    @staticmethod
    def _build_reasoning(parsed: FlashAnalysis) -> str:
        assets = "、".join(parsed.affected_assets) if parsed.affected_assets else "暂未明确"
        return f"受影响资产：{assets}。历史参照：{parsed.historical_reference}"

    @classmethod
    def _build_portfolio_note(cls, parsed: FlashAnalysis, positions: list[str]) -> str | None:
        if not positions:
            return None
        joined_positions = "、".join(positions)
        return f"持仓关注：{joined_positions}。{parsed.trading_suggestion}"
