from __future__ import annotations
from fastapi import APIRouter, Depends
from app.dependencies import get_alert_service
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/logs")
async def get_alert_logs(
    limit: int = 50,
    svc: AlertService = Depends(get_alert_service),
):
    return await svc.recent_logs(limit=limit)
