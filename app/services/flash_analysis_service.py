from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.ai.flash_analyzer import get_flash_analyzer
from app.models.flash_analysis import FlashAnalysis, FlashAnalyzeRequest
from app.models.portfolio import Position
from app.services.market_data_service import MarketDataService
from app.services.settings_service import SettingsService


class FlashAnalysisService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.analyzer = get_flash_analyzer()

    def ensure_ready(self) -> None:
        self.analyzer.ensure_ready()

    async def analyze(self, data: FlashAnalyzeRequest) -> FlashAnalysis:
        runtime = await SettingsService(self.session).get_snapshot()
        positions = data.positions or await self._default_positions()
        market_context = await MarketDataService(
            enabled=runtime.live_market_quotes
        ).build_market_context(data.text, positions)
        return await self.analyzer.analyze(
            text=data.text,
            positions=positions,
            model=data.model or runtime.model,
            market_context=market_context,
        )

    async def stream_json(self, data: FlashAnalyzeRequest) -> AsyncIterator[str]:
        runtime = await SettingsService(self.session).get_snapshot()
        positions = data.positions or await self._default_positions()
        market_context = await MarketDataService(
            enabled=runtime.live_market_quotes
        ).build_market_context(data.text, positions)
        async for chunk in self.analyzer.stream_json(
            text=data.text,
            positions=positions,
            model=data.model or runtime.model,
            market_context=market_context,
        ):
            yield chunk

    async def _default_positions(self) -> list[str]:
        result = await self.session.execute(select(Position).order_by(Position.id.asc()))
        positions = result.scalars().all()
        labels: list[str] = []
        for position in positions:
            base = position.name.strip() or position.ticker.strip()
            ticker = position.ticker.strip()
            if ticker and ticker != base:
                base = f"{base} ({ticker})"
            if position.quantity:
                qty = int(position.quantity) if float(position.quantity).is_integer() else position.quantity
                base = f"{base} x{qty}"
            labels.append(base)
        return labels
