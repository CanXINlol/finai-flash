from __future__ import annotations

from typing import AsyncIterator

from app.ai.flash_analyzer import get_flash_analyzer
from app.models.flash_analysis import FlashAnalysis, FlashAnalyzeRequest


class FlashAnalysisService:
    def __init__(self):
        self.analyzer = get_flash_analyzer()

    def ensure_ready(self) -> None:
        self.analyzer.ensure_ready()

    async def analyze(self, data: FlashAnalyzeRequest) -> FlashAnalysis:
        return await self.analyzer.analyze(
            text=data.text,
            positions=data.positions,
            model=data.model,
        )

    async def stream_json(self, data: FlashAnalyzeRequest) -> AsyncIterator[str]:
        async for chunk in self.analyzer.stream_json(
            text=data.text,
            positions=data.positions,
            model=data.model,
        ):
            yield chunk
