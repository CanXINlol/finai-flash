from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.base import RawNewsItem
from app.db.crud import news as news_crud
from app.models.news import NewsItem
from app.websocket.events import flash_event, news_event
from app.websocket.manager import flash_manager, manager


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
        return item

    async def get_recent(self, limit=50, offset=0, source=None, since_hours=24):
        return await news_crud.get_recent(
            self.session,
            limit=limit,
            offset=offset,
            source=source,
            since_hours=since_hours,
        )

    async def get_latest_flash(self, limit: int = 10) -> list[NewsItem]:
        return await news_crud.get_latest_flash(self.session, limit=limit)
