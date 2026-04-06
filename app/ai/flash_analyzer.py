from __future__ import annotations

import json
import re
import time
from typing import Any, AsyncIterator

import httpx

from app.ai.flash_prompts import (
    FLASH_HUMAN_TEMPLATE,
    FLASH_SYSTEM_PROMPT,
    build_price_guardrails,
    build_positions_text,
    build_retry_feedback,
    default_quality_feedback,
)
from app.config import get_settings
from app.models.flash_analysis import FlashAnalysis

settings = get_settings()

GENERIC_PHRASES = (
    "可能影响市场",
    "建议关注",
    "谨慎操作",
    "市场情绪",
    "市场波动",
    "产生重大影响",
    "值得关注",
)

HORIZON_PATTERN = re.compile(r"(分钟|小时|日内|短线|本周|未来\d+[天日周]|\d+-\d+日|\d+-\d+周|数日|数周|中线)")
RISK_PATTERN = re.compile(r"(止损|失效|若|如果|风险|跌破|站稳|确认|除非)")
YEAR_PATTERN = re.compile(r"(19|20)\d{2}")
MARKET_METRIC_PATTERN = re.compile(
    r"(?:USD|US\$|\$|¥|￥|人民币)?\s*\d+(?:\.\d+)?\s*(?:万亿美元|亿美元|万亿|美元|美金|元|点|bp|bps|%|％)"
)


class FlashAnalyzer:
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.1,
        timeout: int | None = None,
        num_predict: int = 1024,
        quality_retries: int = 1,
    ):
        self.base_url = (base_url or settings.ollama_host).rstrip("/")
        self.default_model = model or settings.model
        self.temperature = temperature
        self.timeout = timeout or settings.ollama_timeout
        self.num_predict = num_predict
        self.quality_retries = quality_retries

    def ensure_ready(self) -> None:
        self._get_langchain_types()

    async def analyze(
        self,
        text: str,
        positions: list[str] | None = None,
        model: str | None = None,
        market_context: str | None = None,
    ) -> FlashAnalysis:
        selected_model = model or self.default_model
        return await self._analyze_with_quality_retry(
            text=text,
            positions=positions,
            selected_model=selected_model,
            market_context=market_context,
        )

    async def stream_json(
        self,
        text: str,
        positions: list[str] | None = None,
        model: str | None = None,
        market_context: str | None = None,
    ) -> AsyncIterator[str]:
        selected_model = model or self.default_model
        chain = self._build_chain(selected_model)
        try:
            async for chunk in chain.astream(
                self._build_payload(text, positions, default_quality_feedback(), market_context)
            ):
                chunk_text = self._content_to_text(chunk)
                if chunk_text:
                    yield chunk_text
        except Exception as exc:
            raise RuntimeError(self._format_model_error(exc, selected_model)) from exc

    async def analyze_with_metadata(
        self,
        text: str,
        positions: list[str] | None = None,
        model: str | None = None,
        market_context: str | None = None,
    ) -> tuple[FlashAnalysis, int, str]:
        selected_model = model or self.default_model
        started_at = time.monotonic()
        result = await self._analyze_with_quality_retry(
            text=text,
            positions=positions,
            selected_model=selected_model,
            market_context=market_context,
        )
        latency_ms = int((time.monotonic() - started_at) * 1000)
        return result, latency_ms, selected_model

    async def _analyze_with_quality_retry(
        self,
        text: str,
        positions: list[str] | None,
        selected_model: str,
        market_context: str | None,
    ) -> FlashAnalysis:
        quality_feedback = default_quality_feedback()
        last_exception: Exception | None = None

        for attempt in range(self.quality_retries + 1):
            chain = self._build_chain(selected_model)
            try:
                response = await chain.ainvoke(
                    self._build_payload(text, positions, quality_feedback, market_context)
                )
            except Exception as exc:
                if attempt < self.quality_retries:
                    quality_feedback = build_retry_feedback(
                        [f"上次生成阶段失败：{self._short_error_message(exc)}"]
                    )
                    last_exception = exc
                    continue
                raise RuntimeError(self._format_model_error(exc, selected_model)) from exc

            raw = self._content_to_text(response)
            try:
                parsed = self._parse_output(raw)
            except Exception as exc:
                if attempt < self.quality_retries:
                    quality_feedback = build_retry_feedback(
                        [f"上次输出不是合法 JSON 或字段格式不对：{self._short_error_message(exc)}"]
                    )
                    last_exception = exc
                    continue
                raise RuntimeError(
                    f"Model `{selected_model}` returned invalid JSON. Original error: {exc}"
                ) from exc

            issues = self._quality_issues(parsed, text)
            if not issues:
                return parsed

            last_exception = RuntimeError("; ".join(issues))
            if attempt < self.quality_retries:
                quality_feedback = build_retry_feedback(issues)
                continue

            raise RuntimeError(
                f"Model `{selected_model}` returned an analysis that was too generic: "
                + "; ".join(issues)
            )

        raise RuntimeError(
            f"Flash analysis failed with model `{selected_model}`: "
            f"{self._short_error_message(last_exception) if last_exception else 'unknown error'}"
        )

    async def health_check(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                models = [item.get("name", "") for item in response.json().get("models", [])]
        except Exception as exc:
            return {
                "ok": False,
                "model": self.default_model,
                "ollama_url": self.base_url,
                "error": str(exc),
                "available_models": [],
            }

        selected_model = self.default_model.strip()
        model_base = selected_model.split(":")[0]
        model_available = selected_model in models or (
            ":" not in selected_model and any(name.split(":")[0] == model_base for name in models)
        )
        return {
            "ok": model_available,
            "model": selected_model,
            "ollama_url": self.base_url,
            "model_available": model_available,
            "available_models": models,
        }

    def switch_model(self, model: str) -> None:
        self.default_model = model

    @staticmethod
    def _format_model_error(exc: Exception, model: str) -> str:
        message = str(exc).strip()
        lowered = message.lower()
        if "requires more system memory" in lowered:
            return (
                f"Model `{model}` exceeds available memory on this machine. "
                "Try a lighter model such as `qwen2.5:7b` or `qwen2.5:14b`, "
                "or start the server with a smaller `MODEL` env var."
            )
        if "connection refused" in lowered or "failed to connect" in lowered:
            return (
                f"Cannot reach Ollama at `{settings.ollama_host}`. "
                "Make sure the Ollama service is running."
            )
        return f"Flash analysis failed with model `{model}`: {message}"

    def _build_chain(self, model: str | None):
        ChatPromptTemplate, ChatOllama = self._get_langchain_types()
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", FLASH_SYSTEM_PROMPT),
                ("human", FLASH_HUMAN_TEMPLATE),
            ]
        )
        llm = ChatOllama(
            base_url=self.base_url,
            model=model or self.default_model,
            temperature=self.temperature,
            format="json",
            num_predict=self.num_predict,
            timeout=self.timeout,
        )
        return prompt | llm

    @staticmethod
    def _build_payload(
        text: str,
        positions: list[str] | None,
        quality_feedback: str,
        market_context: str | None,
    ) -> dict[str, str]:
        return {
            "text": text.strip(),
            "positions_text": build_positions_text(positions),
            "pricing_guardrails": build_price_guardrails(text),
            "market_context": (market_context or "本次没有拿到额外实时行情，请不要自行补充现价。").strip(),
            "quality_feedback": quality_feedback.strip(),
        }

    @staticmethod
    def _content_to_text(message: Any) -> str:
        content = getattr(message, "content", message)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append(str(item.get("text", "")))
                else:
                    parts.append(str(item))
            return "".join(parts)
        return str(content)

    @classmethod
    def _parse_output(cls, raw: str) -> FlashAnalysis:
        data = cls._extract_json(raw)
        return FlashAnalysis.model_validate(data)

    @staticmethod
    def _extract_json(raw: str) -> dict[str, Any]:
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        brace_start = cleaned.find("{")
        if brace_start == -1:
            raise ValueError(f"No JSON object found in model output: {cleaned[:200]}")

        depth = 0
        end = -1
        in_string = False
        escape_next = False

        for index, char in enumerate(cleaned[brace_start:], start=brace_start):
            if escape_next:
                escape_next = False
                continue
            if char == "\\" and in_string:
                escape_next = True
                continue
            if char == '"':
                in_string = not in_string
            if not in_string:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        end = index + 1
                        break

        if end == -1:
            raise ValueError(f"Unmatched braces in model output: {cleaned[:200]}")

        return json.loads(cleaned[brace_start:end])

    @staticmethod
    def _get_langchain_types():
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_ollama import ChatOllama
        except ImportError as exc:
            raise RuntimeError(
                "Missing LangChain/Ollama dependencies. Install `langchain` and `langchain-ollama` first."
            ) from exc
        return ChatPromptTemplate, ChatOllama

    @staticmethod
    def _short_error_message(exc: Exception | None) -> str:
        if exc is None:
            return "unknown error"
        message = str(exc).strip()
        return message[:240]

    @staticmethod
    def _quality_issues(result: FlashAnalysis, source_text: str = "") -> list[str]:
        issues: list[str] = []
        summary = result.summary.strip()
        suggestion = result.trading_suggestion.strip()
        historical = result.historical_reference.strip()

        if len(summary) < 12:
            issues.append("summary 过短，没有清楚说明事件、逻辑和主导资产。")
        if any(phrase in summary for phrase in GENERIC_PHRASES):
            issues.append("summary 仍然使用了空泛表述，缺少明确传导逻辑。")
        if len(result.affected_assets) < 2:
            issues.append("affected_assets 太少，至少应给出两个相关资产或板块。")
        if not HORIZON_PATTERN.search(suggestion):
            issues.append("trading_suggestion 缺少明确时间窗口。")
        if not RISK_PATTERN.search(suggestion):
            issues.append("trading_suggestion 缺少风险提示或失效条件。")
        if "建议关注" in suggestion and "若" not in suggestion and "如果" not in suggestion:
            issues.append("trading_suggestion 过于泛泛，没有给出执行条件。")
        if FlashAnalyzer._has_unsupported_price_claim(summary, suggestion, source_text):
            issues.append("summary 或 trading_suggestion 引用了原文未提供的实时价格、点位或涨跌幅。")
        if not YEAR_PATTERN.search(historical):
            issues.append("historical_reference 缺少具体年份。")
        if len(historical) < 12:
            issues.append("historical_reference 过短，没有说明历史事件和市场反应。")
        return issues

    @staticmethod
    def _has_unsupported_price_claim(summary: str, suggestion: str, source_text: str) -> bool:
        output_metrics = FlashAnalyzer._extract_market_metrics(f"{summary}\n{suggestion}")
        if not output_metrics:
            return False
        source_metrics = set(FlashAnalyzer._extract_market_metrics(source_text))
        return any(metric not in source_metrics for metric in output_metrics)

    @staticmethod
    def _extract_market_metrics(text: str) -> list[str]:
        normalized = str(text or "").replace(",", "").replace("，", "").replace("％", "%")
        return [" ".join(match.split()) for match in MARKET_METRIC_PATTERN.findall(normalized)]


_flash_analyzer: FlashAnalyzer | None = None


def get_flash_analyzer() -> FlashAnalyzer:
    global _flash_analyzer
    if _flash_analyzer is None:
        _flash_analyzer = FlashAnalyzer()
    return _flash_analyzer
