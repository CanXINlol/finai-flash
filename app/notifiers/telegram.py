from __future__ import annotations
import httpx
from app.config import get_settings
from app.notifiers.base import BaseNotifier

settings = get_settings()

SENTIMENT_EMOJI = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}


class TelegramNotifier(BaseNotifier):
    name = "telegram"

    def __init__(self):
        self.token = settings.tg_bot_token
        self.chat_id = settings.tg_chat_id
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    async def send(self, title: str, body: str, score: int, sentiment: str) -> bool:
        emoji = SENTIMENT_EMOJI.get(sentiment, "⚪")
        stars = "⭐" * min(score, 10)
        text = (
            f"{emoji} *{title}*\n\n"
            f"{body}\n\n"
            f"影响评分: {stars} ({score}/10)"
        )
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self.api_url, json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                })
                return resp.status_code == 200
        except Exception as e:
            print(f"[Telegram] send error: {e}")
            return False
