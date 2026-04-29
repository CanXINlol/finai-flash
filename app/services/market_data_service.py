from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from app.config import get_settings

settings = get_settings()

ASSET_ALIASES: dict[str, tuple[str, str]] = {
    "原油": ("CL=F", "WTI原油"),
    "原油多单": ("CL=F", "WTI原油"),
    "wti": ("CL=F", "WTI原油"),
    "cl": ("CL=F", "WTI原油"),
    "cl=f": ("CL=F", "WTI原油"),
    "布油": ("BZ=F", "布伦特原油"),
    "brent": ("BZ=F", "布伦特原油"),
    "bz": ("BZ=F", "布伦特原油"),
    "bz=f": ("BZ=F", "布伦特原油"),
    "黄金": ("GC=F", "COMEX黄金"),
    "黄金多单": ("GC=F", "COMEX黄金"),
    "xau": ("GC=F", "COMEX黄金"),
    "xauusd": ("GC=F", "COMEX黄金"),
    "gc": ("GC=F", "COMEX黄金"),
    "gc=f": ("GC=F", "COMEX黄金"),
    "白银": ("SI=F", "COMEX白银"),
    "白银多单": ("SI=F", "COMEX白银"),
    "xag": ("SI=F", "COMEX白银"),
    "xagusd": ("SI=F", "COMEX白银"),
    "si": ("SI=F", "COMEX白银"),
    "si=f": ("SI=F", "COMEX白银"),
    "美元指数": ("DX-Y.NYB", "美元指数"),
    "美指": ("DX-Y.NYB", "美元指数"),
    "dxy": ("DX-Y.NYB", "美元指数"),
    "比特币": ("BTC-USD", "比特币"),
    "btc": ("BTC-USD", "比特币"),
    "btc-usd": ("BTC-USD", "比特币"),
    "以太坊": ("ETH-USD", "以太坊"),
    "eth": ("ETH-USD", "以太坊"),
    "eth-usd": ("ETH-USD", "以太坊"),
    "标普500": ("^GSPC", "标普500"),
    "标普": ("^GSPC", "标普500"),
    "spx": ("^GSPC", "标普500"),
    "纳指": ("^IXIC", "纳斯达克综合"),
    "纳斯达克": ("^IXIC", "纳斯达克综合"),
    "nasdaq": ("^IXIC", "纳斯达克综合"),
    "道指": ("^DJI", "道琼斯工业平均"),
    "dow": ("^DJI", "道琼斯工业平均"),
    "eurusd": ("EURUSD=X", "欧元兑美元"),
    "欧元兑美元": ("EURUSD=X", "欧元兑美元"),
    "usdjpy": ("JPY=X", "美元兑日元"),
    "美元兑日元": ("JPY=X", "美元兑日元"),
}

DIRECT_TICKER_PATTERN = re.compile(r"^[A-Za-z^][A-Za-z0-9.^=\-]{0,14}$")
PAREN_TICKER_PATTERN = re.compile(r"\(([^)]+)\)")


@dataclass(frozen=True)
class QuoteSnapshot:
    symbol: str
    label: str
    price: float
    change_pct: float | None
    currency: str
    as_of: str
    is_stale: bool


class MarketDataService:
    def __init__(self, enabled: bool | None = None):
        self.enabled = settings.live_market_quotes if enabled is None else enabled
        self.exact_prices_enabled = settings.market_quote_exact_prices

    async def build_market_context(
        self,
        text: str,
        positions: list[str] | None = None,
        limit: int = 4,
    ) -> str:
        if not self.enabled:
            return "实时行情查询已关闭。"

        tracked = self._infer_symbols(text, positions, limit=limit)
        if not tracked:
            return "本次未匹配到明确的可查询资产。不要自行补充实时价格、点位或涨跌幅。"

        if not self.exact_prices_enabled:
            assets = "、".join(f"{label} ({symbol})" for symbol, label in tracked)
            return (
                f"已识别相关资产：{assets}。\n"
                "当前免费行情源可能延迟，且可能与用户实际交易终端报价不一致；"
                "本次不要向模型提供或生成任何具体实时价格、目标价、止损价、支撑位、阻力位或涨跌幅。"
                "只能基于快讯内容、用户持仓和事件条件判断方向、影响路径与风险。"
            )

        quotes = await asyncio.to_thread(self._fetch_quotes_sync, tracked)
        if not quotes:
            return "本次未能拿到外部行情快照。不要自行编造现价、涨跌幅、目标位或止损位。"

        lines = [
            "以下是外部行情快照，可能存在交易所或数据源延迟。"
            "它只用于校准方向和相关资产；不要把这些数字改写成目标价、止损价、支撑位或阻力位。"
        ]
        for quote in quotes:
            change_text = f"，近一段变化 {quote.change_pct:+.2f}%" if quote.change_pct is not None else ""
            stale_text = "，可能延迟" if quote.is_stale else ""
            lines.append(
                f"- {quote.label} ({quote.symbol}): 快照价 {quote.price:.4f} {quote.currency}"
                f"{change_text}，时间 {quote.as_of}{stale_text}"
            )
        return "\n".join(lines)

    def _infer_symbols(
        self,
        text: str,
        positions: list[str] | None,
        limit: int,
    ) -> list[tuple[str, str]]:
        seen: set[str] = set()
        tracked: list[tuple[str, str]] = []

        def add(symbol: str, label: str) -> None:
            if symbol in seen or len(tracked) >= limit:
                return
            seen.add(symbol)
            tracked.append((symbol, label))

        for candidate in self._position_candidates(positions or []):
            resolved = self._resolve_symbol(candidate)
            if resolved:
                add(*resolved)

        lowered_text = (text or "").lower()
        for alias, resolved in ASSET_ALIASES.items():
            if alias in lowered_text and len(tracked) < limit:
                add(*resolved)

        return tracked

    def _position_candidates(self, positions: Iterable[str]) -> list[str]:
        candidates: list[str] = []
        for position in positions:
            text = str(position or "").strip()
            if not text:
                continue
            candidates.append(text)
            for match in PAREN_TICKER_PATTERN.findall(text):
                candidates.append(match.strip())
            for token in re.split(r"[\s,/，、]+", text):
                token = token.strip("()[]（）")
                if token:
                    candidates.append(token)
        return candidates

    def _resolve_symbol(self, candidate: str) -> tuple[str, str] | None:
        normalized = candidate.strip()
        lowered = normalized.lower()
        if lowered in ASSET_ALIASES:
            return ASSET_ALIASES[lowered]
        if DIRECT_TICKER_PATTERN.fullmatch(normalized):
            return normalized.upper(), normalized.upper()
        return None

    def _fetch_quotes_sync(self, tracked: list[tuple[str, str]]) -> list[QuoteSnapshot]:
        try:
            import yfinance as yf
        except ImportError:
            return []

        results: list[QuoteSnapshot] = []
        for symbol, label in tracked:
            try:
                ticker = yf.Ticker(symbol)
                intraday = ticker.history(period="1d", interval="1m", prepost=True, auto_adjust=False)
                frame = intraday if not intraday.empty else ticker.history(period="5d", interval="1d", auto_adjust=False)
                if frame.empty:
                    continue

                closes = frame["Close"].dropna()
                if closes.empty:
                    continue

                price = float(closes.iloc[-1])
                prev_price = float(closes.iloc[-2]) if len(closes) > 1 else None
                change_pct = None
                if prev_price not in (None, 0):
                    change_pct = ((price - prev_price) / prev_price) * 100

                currency = self._guess_currency(symbol)
                try:
                    fast_info = getattr(ticker, "fast_info", None) or {}
                    currency = fast_info.get("currency") or currency
                except Exception:
                    pass

                timestamp = closes.index[-1]
                as_of = timestamp.strftime("%Y-%m-%d %H:%M:%S %Z").strip()
                results.append(
                    QuoteSnapshot(
                        symbol=symbol,
                        label=label,
                        price=price,
                        change_pct=change_pct,
                        currency=str(currency or ""),
                        as_of=as_of or "最新可得数据",
                        is_stale=self._is_stale_timestamp(timestamp),
                    )
                )
            except Exception:
                continue
        return results

    @staticmethod
    def _is_stale_timestamp(timestamp) -> bool:
        try:
            value = timestamp.to_pydatetime() if hasattr(timestamp, "to_pydatetime") else timestamp
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            age_seconds = (datetime.now(timezone.utc) - value.astimezone(timezone.utc)).total_seconds()
            return age_seconds > 20 * 60
        except Exception:
            return True

    @staticmethod
    def _guess_currency(symbol: str) -> str:
        if symbol.endswith("-USD") or symbol.endswith("=F"):
            return "USD"
        if symbol.endswith("=X"):
            return "FX"
        return ""
