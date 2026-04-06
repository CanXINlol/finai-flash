#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.flash_analyzer import get_flash_analyzer


async def main():
    analyzer = get_flash_analyzer()

    status = await analyzer.health_check()
    print("Health:")
    print(json.dumps(status, ensure_ascii=False, indent=2))

    text = "OPEC+ reportedly discussed extending voluntary supply cuts, sending oil prices higher intraday."
    positions = ["Crude oil long", "Gold"]

    result = await analyzer.analyze(text=text, positions=positions)
    print("\nNon-stream result:")
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))

    print("\nStreaming JSON:")
    async for chunk in analyzer.stream_json(text=text, positions=positions):
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
