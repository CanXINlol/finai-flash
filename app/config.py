from __future__ import annotations

from functools import lru_cache
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8888
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/finai.db"

    # Ollama / LLM
    ollama_host: str = "http://localhost:11434"
    model: str = "qwen2.5:7b"
    ollama_timeout: int = 120

    # Collection
    collect_interval_seconds: int = 10
    max_news_age_hours: int = 24

    # AI Analysis
    alert_score_threshold: int = 7  # 1-10; push notification if score >= this
    analysis_language: str = "zh"   # "zh" | "en"

    # Portfolio  (raw string: "TICKER:NAME:QTY,...")
    my_positions: str = ""

    # Telegram
    tg_bot_token: str = ""
    tg_chat_id: str = ""

    # Discord
    discord_webhook_url: str = ""

    # ── Derived helpers ────────────────────────────────────────
    @field_validator("alert_score_threshold")
    @classmethod
    def clamp_threshold(cls, v: int) -> int:
        return max(1, min(10, v))

    def parsed_positions(self) -> list[dict]:
        """Parse MY_POSITIONS env string into list of dicts."""
        if not self.my_positions.strip():
            return []
        result = []
        for item in self.my_positions.split(","):
            parts = [p.strip() for p in item.split(":")]
            if len(parts) >= 2:
                result.append({
                    "ticker": parts[0],
                    "name": parts[1] if len(parts) > 1 else parts[0],
                    "quantity": float(parts[2]) if len(parts) > 2 else 0,
                })
        return result

    def telegram_enabled(self) -> bool:
        return bool(self.tg_bot_token and self.tg_chat_id)

    def discord_enabled(self) -> bool:
        return bool(self.discord_webhook_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
