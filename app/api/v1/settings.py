from __future__ import annotations

from fastapi import APIRouter, Depends

from app.collectors.scheduler import reschedule_collection
from app.dependencies import get_settings_service
from app.models.settings import AppSettingsRead, AppSettingsUpdate
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=AppSettingsRead)
async def get_settings_view(
    svc: SettingsService = Depends(get_settings_service),
):
    return await svc.get_public_settings()


@router.patch("", response_model=AppSettingsRead)
async def update_settings_view(
    data: AppSettingsUpdate,
    svc: SettingsService = Depends(get_settings_service),
):
    updated = await svc.update_settings(data)
    reschedule_collection(updated.collect_interval_seconds)
    return updated
