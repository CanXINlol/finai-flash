from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_portfolio_service
from app.services.portfolio_service import PortfolioService
from app.models.portfolio import PositionCreate, PositionRead, PositionUpdate

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=list[PositionRead])
async def list_positions(svc: PortfolioService = Depends(get_portfolio_service)):
    return await svc.list_positions()


@router.post("", response_model=PositionRead, status_code=201)
async def create_position(
    data: PositionCreate,
    svc: PortfolioService = Depends(get_portfolio_service),
):
    return await svc.create_position(data)


@router.patch("/{position_id}", response_model=PositionRead)
async def update_position(
    position_id: int,
    data: PositionUpdate,
    svc: PortfolioService = Depends(get_portfolio_service),
):
    updated = await svc.update_position(position_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Position not found")
    return updated


@router.delete("/{position_id}", status_code=204)
async def delete_position(
    position_id: int,
    svc: PortfolioService = Depends(get_portfolio_service),
):
    deleted = await svc.delete_position(position_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Position not found")
