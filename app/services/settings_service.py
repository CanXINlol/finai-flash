from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.ai.flash_analyzer import get_flash_analyzer
from app.config import get_settings
from app.models.settings import (
    AppSettings,
    AppSettingsRead,
    AppSettingsUpdate,
    RuntimeSettingsSnapshot,
)

DEFAULT_ID = 1


class SettingsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.base_settings = get_settings()

    async def get_snapshot(self) -> RuntimeSettingsSnapshot:
        row = await self._get_or_create()
        return RuntimeSettingsSnapshot(
            model=row.model or self.base_settings.model,
            auto_analyze_flash=(
                row.auto_analyze_flash
                if row.auto_analyze_flash is not None
                else self.base_settings.auto_analyze_flash
            ),
            collect_interval_seconds=(
                row.collect_interval_seconds or self.base_settings.collect_interval_seconds
            ),
        )

    async def get_public_settings(self) -> AppSettingsRead:
        snapshot = await self.get_snapshot()
        analyzer = get_flash_analyzer()
        analyzer.switch_model(snapshot.model)
        health = await analyzer.health_check()
        return AppSettingsRead(
            model=snapshot.model,
            auto_analyze_flash=snapshot.auto_analyze_flash,
            collect_interval_seconds=snapshot.collect_interval_seconds,
            available_models=health.get("available_models", []),
            ollama_connected=bool(health.get("ok")),
            updated_at=(await self._get_or_create()).updated_at,
        )

    async def update_settings(self, data: AppSettingsUpdate) -> AppSettingsRead:
        row = await self._get_or_create()
        payload = data.model_dump(exclude_unset=True)
        for field, value in payload.items():
            setattr(row, field, value)
        row.updated_at = datetime.utcnow()
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)

        if row.model:
            get_flash_analyzer().switch_model(row.model)

        return await self.get_public_settings()

    async def _get_or_create(self) -> AppSettings:
        result = await self.session.execute(
            select(AppSettings).where(AppSettings.id == DEFAULT_ID)
        )
        row = result.scalar_one_or_none()
        if row is not None:
            return row

        row = AppSettings(id=DEFAULT_ID)
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row
