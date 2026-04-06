from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.base import RawNewsItem
from app.config import get_settings
from app.db.crud import analysis as analysis_crud
from app.db.crud import news as news_crud
from app.models.news import FlashAnalysisSummaryRead, FlashItemRead, NewsItem
from app.services.auto_analysis import schedule_auto_analysis
from app.services.settings_service import SettingsService
from app.websocket.events import flash_event, news_event
from app.websocket.manager import flash_manager, manager

settings = get_settings()


class NewsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ingest(self, raw: RawNewsItem) -> NewsItem | None:
        existing = await news_crud.get_by_title_and_pub_time(
            self.session,
            raw.title,
            raw.pub_time,
        )
        if not existing:
            existing = await news_crud.get_by_guid(self.session, raw.guid)
        if existing:
            return None

        item = NewsItem(
            guid=raw.guid,
            title=raw.title,
            content=raw.content,
            source=raw.source,
            source_url=raw.url,
            pub_time=raw.pub_time,
        )
        item = await news_crud.create(self.session, item)
        await manager.broadcast(news_event(item))
        await flash_manager.broadcast(flash_event(item))
        runtime = await SettingsService(self.session).get_snapshot()
        if runtime.auto_analyze_flash:
            schedule_auto_analysis(item.id)
        return item

    async def get_recent(self, limit=50, offset=0, source=None, since_hours=24):
        return await news_crud.get_recent(
            self.session,
            limit=limit,
            offset=offset,
            source=source,
            since_hours=since_hours,
        )

    async def get_latest_flash(self, limit: int = 10) -> list[FlashItemRead]:
        items = await news_crud.get_latest_flash(self.session, limit=limit)
        analyses = await analysis_crud.get_by_news_ids(self.session, [item.id for item in items if item.id is not None])

        result: list[FlashItemRead] = []
        for item in items:
            analysis = analyses.get(item.id)
            summary = None
            if analysis:
                summary = FlashAnalysisSummaryRead(
                    score=analysis.score,
                    sentiment=analysis.sentiment,
                    summary=analysis.summary,
                    suggestion=analysis.suggestion,
                    portfolio_note=analysis.portfolio_note,
                )

            result.append(
                FlashItemRead(
                    id=item.id,
                    title=item.title,
                    content=item.content,
                    source=item.source,
                    source_url=item.source_url,
                    pub_time=item.pub_time,
                    fetched_at=item.fetched_at,
                    is_analyzed=item.is_analyzed,
                    analysis=summary,
                )
            )

        return result
