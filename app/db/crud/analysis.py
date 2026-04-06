from __future__ import annotations
from typing import Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.analysis import AnalysisResult


async def create(session: AsyncSession, result: AnalysisResult) -> AnalysisResult:
    session.add(result)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing = await get_by_news_id(session, result.news_id)
        if existing:
            return existing
        raise
    await session.refresh(result)
    return result


async def get_by_news_id(session: AsyncSession, news_id: int) -> Optional[AnalysisResult]:
    q = select(AnalysisResult).where(AnalysisResult.news_id == news_id)
    result = await session.execute(q)
    return result.scalar_one_or_none()


async def get_by_news_ids(session: AsyncSession, news_ids: list[int]) -> dict[int, AnalysisResult]:
    if not news_ids:
        return {}
    q = select(AnalysisResult).where(AnalysisResult.news_id.in_(news_ids))
    result = await session.execute(q)
    items = result.scalars().all()
    return {item.news_id: item for item in items}


async def get_recent(session: AsyncSession, limit: int = 20) -> list[AnalysisResult]:
    q = select(AnalysisResult).order_by(AnalysisResult.created_at.desc()).limit(limit)
    result = await session.execute(q)
    return result.scalars().all()
