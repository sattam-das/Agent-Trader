from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
TModel = TypeVar("TModel", bound=BaseModel)

# Module-level client singleton
_client: genai.Client | None = None


def _get_client(api_key: str) -> genai.Client:
    """Return a shared Gemini client (created once per process)."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=api_key)
    return _client


# ------------------------------------------------------------------
# Pydantic Schemas
# ------------------------------------------------------------------
class NewsAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sentiment: str = Field(min_length=1)
    sentiment_score: float = Field(ge=0.0, le=1.0)
    key_events: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1)


class FinancialAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    health_score: float = Field(ge=0.0, le=1.0)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1)


class RiskAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_level: float = Field(ge=0.0, le=1.0)
    risk_factors: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1)


class TechnicalAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_score: float = Field(ge=0.0, le=1.0)
    trend: str = Field(min_length=1)
    signals: list[str] = Field(default_factory=list)
    key_levels: list[str] = Field(default_factory=list)
    pattern_description: str = Field(min_length=1)
    summary: str = Field(min_length=1)


class MacroAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    macro_score: float = Field(ge=0.0, le=1.0)
    institutional_sentiment: str = Field(min_length=1)
    insider_signal: str = Field(min_length=1)
    sector_outlook: str = Field(min_length=1)
    key_observations: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1)


class DiscoverySuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(min_length=1, max_length=12)
    company_name: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class DiscoveryAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggestions: list[DiscoverySuggestion] = Field(default_factory=list)
    summary: str = Field(min_length=1)


# ------------------------------------------------------------------
# Base Agent (Google Gemini — google.genai SDK)
# ------------------------------------------------------------------
class BaseGeminiAgent(ABC):
    """Base agent using Google Gemini API (google.genai SDK)."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        resolved_api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not resolved_api_key:
            raise ValueError("GEMINI_API_KEY is required. Set GEMINI_API_KEY env var or pass api_key.")

        self.client = _get_client(resolved_api_key)
        self.model_name = model or os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL

    @abstractmethod
    async def analyze(self, payload: Any) -> BaseModel:
        raise NotImplementedError

    async def _complete_json(self, prompt: str) -> dict[str, Any]:
        full_prompt = (
            "You are a senior financial analyst. Return only valid JSON. "
            "Do not include markdown code fences or any text outside the JSON.\n\n"
            f"{prompt}"
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_mime_type="application/json",
                ),
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini API call failed: {exc}") from exc

        # Handle safety-blocked or empty responses
        try:
            message = response.text
        except (ValueError, AttributeError):
            raise RuntimeError(
                "Gemini response was blocked or empty. "
                "This may be a safety filter issue with the prompt content."
            )

        if not message:
            raise RuntimeError("Gemini returned an empty response.")

        # Strip markdown fences if present (defensive)
        text = message.strip()
        if text.startswith("```"):
            lines = text.split("\n", 1)
            text = lines[1] if len(lines) > 1 else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Gemini returned invalid JSON: {text[:200]}") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError("Gemini JSON response must be an object.")

        return parsed

    def _validate(self, data: dict[str, Any], schema: type[TModel]) -> TModel:
        try:
            return schema.model_validate(data)
        except Exception as exc:
            raise RuntimeError(f"Invalid {schema.__name__} payload from model: {exc}") from exc
