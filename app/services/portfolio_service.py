from __future__ import annotations
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.portfolio import Position, PositionCreate, PositionUpdate


class PortfolioService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_positions(self) -> list[Position]:
        result = await self.session.execute(select(Position))
        return result.scalars().all()

    async def create_position(self, data: PositionCreate) -> Position:
        pos = Position(**data.model_dump())
        self.session.add(pos)
        await self.session.commit()
        await self.session.refresh(pos)
        return pos

    async def update_position(self, position_id: int, data: PositionUpdate) -> Position | None:
        result = await self.session.execute(select(Position).where(Position.id == position_id))
        pos = result.scalar_one_or_none()
        if not pos:
            return None
        for field, val in data.model_dump(exclude_none=True).items():
            setattr(pos, field, val)
        pos.updated_at = datetime.utcnow()
        self.session.add(pos)
        await self.session.commit()
        await self.session.refresh(pos)
        return pos

    async def delete_position(self, position_id: int) -> bool:
        result = await self.session.execute(select(Position).where(Position.id == position_id))
        pos = result.scalar_one_or_none()
        if not pos:
            return False
        await self.session.delete(pos)
        await self.session.commit()
        return True
