from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.alert import AlertLog


class AlertService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(self, news_id: int, analysis_id: int, channel: str,
                  status: str, error: str = None) -> AlertLog:
        log = AlertLog(
            news_id=news_id, analysis_id=analysis_id,
            channel=channel, status=status, error=error,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def recent_logs(self, limit: int = 50) -> list[AlertLog]:
        q = select(AlertLog).order_by(AlertLog.sent_at.desc()).limit(limit)
        result = await self.session.execute(q)
        return result.scalars().all()
