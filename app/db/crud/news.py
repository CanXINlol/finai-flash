from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from app.models.news import NewsItem, NewsSource


async def get_by_guid(session: AsyncSession, guid: str) -> Optional[NewsItem]:
    result = await session.execute(select(NewsItem).where(NewsItem.guid == guid))
    return result.scalar_one_or_none()


async def create(session: AsyncSession, item: NewsItem) -> NewsItem:
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def get_recent(
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    source: Optional[NewsSource] = None,
    since_hours: int = 24,
) -> tuple[list[NewsItem], int]:
    cutoff = datetime.utcnow() - timedelta(hours=since_hours)
    q = select(NewsItem).where(NewsItem.pub_time >= cutoff)
    if source:
        q = q.where(NewsItem.source == source)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await session.execute(count_q)).scalar_one()
    q = q.order_by(NewsItem.pub_time.desc()).offset(offset).limit(limit)
    result = await session.execute(q)
    return result.scalars().all(), total


async def mark_analyzed(session: AsyncSession, news_id: int) -> None:
    result = await session.execute(select(NewsItem).where(NewsItem.id == news_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_analyzed = True
        session.add(item)
        await session.commit()


async def get_unanalyzed(session: AsyncSession, limit: int = 10) -> list[NewsItem]:
    q = (
        select(NewsItem)
        .where(NewsItem.is_analyzed == False)
        .order_by(NewsItem.pub_time.desc())
        .limit(limit)
    )
    result = await session.execute(q)
    return result.scalars().all()
