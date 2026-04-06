#!/usr/bin/env python3
"""Quick smoke test: verify Ollama is reachable and model is loaded."""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.ollama_client import OllamaClient
from app.config import get_settings

settings = get_settings()

async def main():
    print(f"Testing Ollama at {settings.ollama_host} with model {settings.model}")
    client = OllamaClient()
    ok = await client.health_check()
    if not ok:
        print("ERROR: Ollama unreachable or model not loaded.")
        print(f"  Run: ollama pull {settings.model}")
        sys.exit(1)
    print("Ollama reachable. Sending test prompt...")
    resp = await client.generate(
        'Return ONLY this JSON: {"score":7,"sentiment":"bullish","summary":"test","reasoning":"test","suggestion":"test","portfolio_note":null}'
    )
    print(f"Response: {resp[:200]}")
    print("OK - Ollama is working correctly.")

asyncio.run(main())
