from __future__ import annotations
import time
from app.ai.ollama_client import get_ollama_client
from app.ai.prompts import build_prompt
from app.ai.parser import parse_llm_output, ParsedAnalysis
from app.config import get_settings

settings = get_settings()


class NewsAnalyzer:
    def __init__(self):
        self.client = get_ollama_client()

    async def analyze(
        self,
        title: str,
        content: str,
        pub_time: str,
        source: str,
        positions: list[dict] | None = None,
    ) -> tuple[ParsedAnalysis, int]:
        prompt = build_prompt(
            title=title, content=content, pub_time=pub_time,
            source=source, positions=positions,
            language=settings.analysis_language,
        )
        t0 = time.monotonic()
        raw = await self.client.generate(prompt)
        latency_ms = int((time.monotonic() - t0) * 1000)
        parsed = parse_llm_output(raw)
        return parsed, latency_ms


_analyzer: NewsAnalyzer | None = None

def get_analyzer() -> NewsAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = NewsAnalyzer()
    return _analyzer
