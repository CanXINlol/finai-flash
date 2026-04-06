from __future__ import annotations
import httpx
from app.config import get_settings
from app.notifiers.base import BaseNotifier

settings = get_settings()

COLOUR_MAP = {"bullish": 0x22C55E, "bearish": 0xEF4444, "neutral": 0x94A3B8}


class DiscordNotifier(BaseNotifier):
    name = "discord"

    def __init__(self):
        self.webhook_url = settings.discord_webhook_url

    async def send(self, title: str, body: str, score: int, sentiment: str) -> bool:
        colour = COLOUR_MAP.get(sentiment, 0x94A3B8)
        payload = {
            "embeds": [{
                "title": title,
                "description": body,
                "color": colour,
                "footer": {"text": f"Impact score: {score}/10"},
            }]
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self.webhook_url, json=payload)
                return resp.status_code in (200, 204)
        except Exception as e:
            print(f"[Discord] send error: {e}")
            return False
