from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator

import httpx

from app.ai.flash_prompts import FLASH_HUMAN_TEMPLATE, FLASH_SYSTEM_PROMPT, build_positions_text
from app.config import get_settings
from app.models.flash_analysis import FlashAnalysis

settings = get_settings()


class FlashAnalyzer:
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.1,
        timeout: int | None = None,
        num_predict: int = 1024,
    ):
        self.base_url = (base_url or settings.ollama_host).rstrip("/")
        self.default_model = model or settings.model
        self.temperature = temperature
        self.timeout = timeout or settings.ollama_timeout
        self.num_predict = num_predict

    def ensure_ready(self) -> None:
        self._get_langchain_types()

    async def analyze(
        self,
        text: str,
        positions: list[str] | None = None,
        model: str | None = None,
    ) -> FlashAnalysis:
        selected_model = model or self.default_model
        chain = self._build_chain(selected_model)
        try:
            response = await chain.ainvoke(self._build_payload(text, positions))
        except Exception as exc:
            raise RuntimeError(self._format_model_error(exc, selected_model)) from exc
        try:
            return self._parse_output(self._content_to_text(response))
        except Exception as exc:
            raise RuntimeError(
                f"Model `{selected_model}` returned invalid JSON. "
                f"Original error: {exc}"
            ) from exc

    async def stream_json(
        self,
        text: str,
        positions: list[str] | None = None,
        model: str | None = None,
    ) -> AsyncIterator[str]:
        selected_model = model or self.default_model
        chain = self._build_chain(selected_model)
        try:
            async for chunk in chain.astream(self._build_payload(text, positions)):
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
    ) -> tuple[FlashAnalysis, int, str]:
        selected_model = model or self.default_model
        chain = self._build_chain(selected_model)
        started_at = time.monotonic()
        response = await chain.ainvoke(self._build_payload(text, positions))
        latency_ms = int((time.monotonic() - started_at) * 1000)
        result = self._parse_output(self._content_to_text(response))
        return result, latency_ms, selected_model

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
    def _build_payload(text: str, positions: list[str] | None) -> dict[str, str]:
        return {
            "text": text.strip(),
            "positions_text": build_positions_text(positions),
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


_flash_analyzer: FlashAnalyzer | None = None


def get_flash_analyzer() -> FlashAnalyzer:
    global _flash_analyzer
    if _flash_analyzer is None:
        _flash_analyzer = FlashAnalyzer()
    return _flash_analyzer
