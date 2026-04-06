from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class AppSettings(SQLModel, table=True):
    __tablename__ = "app_settings"

    id: Optional[int] = Field(default=1, primary_key=True)
    model: Optional[str] = Field(default=None, max_length=128)
    auto_analyze_flash: Optional[bool] = Field(default=None)
    collect_interval_seconds: Optional[int] = Field(default=None, ge=5, le=3600)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AppSettingsRead(SQLModel):
    model: str
    auto_analyze_flash: bool
    collect_interval_seconds: int
    available_models: list[str] = Field(default_factory=list)
    ollama_connected: bool = False
    updated_at: Optional[datetime] = None


class AppSettingsUpdate(SQLModel):
    model: Optional[str] = None
    auto_analyze_flash: Optional[bool] = None
    collect_interval_seconds: Optional[int] = Field(default=None, ge=5, le=3600)

    @field_validator("model")
    @classmethod
    def normalize_model(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("model cannot be empty")
        return normalized


class RuntimeSettingsSnapshot(SQLModel):
    model: str
    auto_analyze_flash: bool
    collect_interval_seconds: int
