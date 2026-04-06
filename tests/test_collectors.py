from __future__ import annotations
import pytest
import respx
import httpx
from app.collectors.jin10 import Jin10Collector
from app.collectors.cls import CLSCollector

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Fed keeps rates unchanged</title>
      <link>https://example.com/1</link>
      <description>The Federal Reserve held its benchmark rate steady.</description>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""


@pytest.mark.asyncio
async def test_jin10_fetch_parses_rss():
    collector = Jin10Collector()
    with respx.mock:
        for url in collector.feed_urls:
            respx.get(url).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))
        items = await collector.fetch()
    assert len(items) > 0
    assert items[0].title == "Fed keeps rates unchanged"
    assert items[0].guid != ""


@pytest.mark.asyncio
async def test_collector_handles_network_error():
    collector = CLSCollector()
    with respx.mock:
        for url in collector.feed_urls:
            respx.get(url).mock(side_effect=httpx.ConnectError("timeout"))
        items = await collector.fetch()
    assert items == []
