from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.news import NewsItem
from app.models.analysis import AnalysisResult
from app.db.crud import news as news_crud
from app.db.crud import analysis as analysis_crud
from app.ai.analyzer import get_analyzer
from app.config import get_settings
from app.websocket.manager import manager
from app.websocket.events import analysis_event
import app.notifiers.dispatcher as dispatcher

settings = get_settings()


class AnalysisService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.analyzer = get_analyzer()

    async def analyze_news(self, item: NewsItem) -> AnalysisResult | None:
        existing = await analysis_crud.get_by_news_id(self.session, item.id)
        if existing:
            return existing

        positions = settings.parsed_positions() or None
        try:
            parsed, latency_ms = await self.analyzer.analyze(
                title=item.title,
                content=item.content or "",
                pub_time=str(item.pub_time),
                source=str(item.source),
                positions=positions,
            )
        except Exception as e:
            print(f"[Analysis] LLM error for news {item.id}: {e}")
            return None

        result = AnalysisResult(
            news_id=item.id,
            score=parsed.score,
            sentiment=parsed.sentiment,
            summary=parsed.summary,
            reasoning=parsed.reasoning,
            suggestion=parsed.suggestion,
            portfolio_note=parsed.portfolio_note,
            model_used=settings.model,
            latency_ms=latency_ms,
        )
        result = await analysis_crud.create(self.session, result)
        await news_crud.mark_analyzed(self.session, item.id)
        await manager.broadcast(analysis_event(item.id, result))

        if result.score >= settings.alert_score_threshold:
            body = f"{result.reasoning}\n\n{result.suggestion}"
            await dispatcher.dispatch(
                title=item.title, body=body,
                score=result.score, sentiment=result.sentiment,
            )

        return result
