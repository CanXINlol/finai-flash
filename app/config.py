from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8888
    debug: bool = False

    database_url: str = "sqlite+aiosqlite:///./data/finai.db"

    ollama_host: str = "http://localhost:11434"
    model: str = "qwen2.5:7b"
    ollama_timeout: int = 180
    ollama_num_ctx: int = 2048
    ollama_num_predict: int = 768
    ollama_temperature: float = 0.05
    rsshub_base_url: str = "http://localhost:1200"

    collect_interval_seconds: int = 300
    max_news_age_hours: int = 24
    auto_analyze_flash: bool = True
    auto_analysis_max_pending: int = 3
    live_market_quotes: bool = True
    market_quote_timeout_seconds: int = 4

    alert_score_threshold: int = 7
    analysis_language: str = "zh"

    my_positions: str = ""

    tg_bot_token: str = ""
    tg_chat_id: str = ""

    discord_webhook_url: str = ""

    @field_validator("alert_score_threshold")
    @classmethod
    def clamp_threshold(cls, value: int) -> int:
        return max(1, min(10, value))

    def parsed_positions(self) -> list[dict]:
        if not self.my_positions.strip():
            return []

        result = []
        for item in self.my_positions.split(","):
            parts = [part.strip() for part in item.split(":")]
            if len(parts) >= 2:
                result.append(
                    {
                        "ticker": parts[0],
                        "name": parts[1] if len(parts) > 1 else parts[0],
                        "quantity": float(parts[2]) if len(parts) > 2 else 0,
                    }
                )
        return result

    def telegram_enabled(self) -> bool:
        return bool(self.tg_bot_token and self.tg_chat_id)

    def discord_enabled(self) -> bool:
        return bool(self.discord_webhook_url)

    def normalized_rsshub_base_url(self) -> str:
        return self.rsshub_base_url.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
