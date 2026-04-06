from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class FlashAnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, description="Flash news text to analyze")
    positions: list[str] = Field(default_factory=list, description="Optional user positions")
    model: str | None = Field(default=None, description="Optional Ollama model override")

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("text cannot be empty")
        return normalized

    @field_validator("positions", mode="before")
    @classmethod
    def normalize_positions(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        raise ValueError("positions must be a list of strings")


class FlashAnalysis(BaseModel):
    summary: str = Field(min_length=1)
    impact_score: int = Field(ge=0, le=100)
    bullish_bearish: Literal["利多", "利空", "中性"]
    affected_assets: list[str] = Field(default_factory=list)
    trading_suggestion: str = Field(min_length=1)
    historical_reference: str = Field(min_length=1)

    @field_validator("impact_score", mode="before")
    @classmethod
    def clamp_score(cls, value: Any) -> int:
        try:
            score = int(value)
        except (TypeError, ValueError):
            score = 50
        return max(0, min(100, score))

    @field_validator("bullish_bearish", mode="before")
    @classmethod
    def normalize_sentiment(cls, value: Any) -> str:
        text = str(value or "").strip()
        if "利多" in text:
            return "利多"
        if "利空" in text:
            return "利空"
        if "中性" in text:
            return "中性"
        mapping = {
            "bullish": "利多",
            "bearish": "利空",
            "neutral": "中性",
        }
        return mapping.get(text.lower(), "中性")

    @field_validator("affected_assets", mode="before")
    @classmethod
    def normalize_assets(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            if text.startswith("["):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass
            normalized = text.replace("，", ",").replace("、", ",")
            return [item.strip() for item in normalized.split(",") if item.strip()]
        raise ValueError("affected_assets must be a list or string")

    @field_validator("summary", "trading_suggestion", "historical_reference", mode="before")
    @classmethod
    def normalize_text_fields(cls, value: Any) -> str:
        return str(value or "").strip()
