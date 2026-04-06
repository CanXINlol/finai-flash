from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Position(SQLModel, table=True):
    __tablename__ = "positions"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, max_length=32)
    name: str = Field(max_length=128)
    quantity: float = Field(default=0.0)
    cost_basis: Optional[float] = Field(default=None)   # average cost per unit
    market: Optional[str] = Field(default=None, max_length=16)  # "A股" "港股" "US" "Crypto"
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PositionCreate(SQLModel):
    ticker: str
    name: str
    quantity: float = 0.0
    cost_basis: Optional[float] = None
    market: Optional[str] = None
    notes: Optional[str] = None


class PositionRead(SQLModel):
    id: int
    ticker: str
    name: str
    quantity: float
    cost_basis: Optional[float]
    market: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class PositionUpdate(SQLModel):
    quantity: Optional[float] = None
    cost_basis: Optional[float] = None
    market: Optional[str] = None
    notes: Optional[str] = None
