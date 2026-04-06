from __future__ import annotations
import httpx
from app.config import get_settings

settings = get_settings()


class OllamaClient:
    def __init__(self):
        self.base_url = settings.ollama_host.rstrip("/")
        self.model = settings.model
        self.timeout = settings.ollama_timeout

    async def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 1024},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "")

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                names = [t.get("name", "") for t in resp.json().get("models", [])]
                return any(self.model.split(":")[0] in n for n in names)
        except Exception:
            return False


_client: OllamaClient | None = None

def get_ollama_client() -> OllamaClient:
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client
