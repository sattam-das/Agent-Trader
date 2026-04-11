from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from google import genai
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
TModel = TypeVar("TModel", bound=BaseModel)


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
# Base Agent
# ------------------------------------------------------------------
class BaseGeminiAgent(ABC):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        resolved_api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not resolved_api_key:
            raise ValueError("GEMINI API key is required. Set GEMINI_API_KEY or pass api_key.")

        self.client = genai.Client(api_key=resolved_api_key)
        self.model = model or os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL

    @abstractmethod
    async def analyze(self, payload: Any) -> BaseModel:
        raise NotImplementedError

    async def _complete_json(self, prompt: str) -> dict[str, Any]:
        system_instruction = "You are a senior financial analyst. Return only valid JSON. Do not include markdown."
        config = genai.types.GenerateContentConfig(
            temperature=0,
            system_instruction=system_instruction,
            response_mime_type="application/json"
        )
        
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )

        message = response.text
        if not message:
            raise RuntimeError("Gemini returned an empty response.")

        try:
            parsed = json.loads(message)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Gemini returned invalid JSON.") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError("Gemini JSON response must be an object.")

        return parsed

    def _validate(self, data: dict[str, Any], schema: type[TModel]) -> TModel:
        try:
            return schema.model_validate(data)
        except Exception as exc:
            raise RuntimeError(f"Invalid {schema.__name__} payload from model: {exc}") from exc
