from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from groq import AsyncGroq
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
TModel = TypeVar("TModel", bound=BaseModel)


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


class BaseGroqAgent(ABC):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        resolved_api_key = api_key or os.getenv("GROQ_API_KEY")
        if not resolved_api_key:
            raise ValueError("GROQ API key is required. Set GROQ_API_KEY or pass api_key.")

        self.client = AsyncGroq(api_key=resolved_api_key)
        self.model = model or os.getenv("GROQ_MODEL") or DEFAULT_GROQ_MODEL

    @abstractmethod
    async def analyze(self, payload: Any) -> BaseModel:
        raise NotImplementedError

    async def _complete_json(self, prompt: str) -> dict[str, Any]:
        completion = await self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Return only valid JSON. Do not include markdown.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        message = completion.choices[0].message.content if completion.choices else None
        if not message:
            raise RuntimeError("Groq returned an empty response.")

        try:
            parsed = json.loads(message)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Groq returned invalid JSON.") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError("Groq JSON response must be an object.")

        return parsed

    def _validate(self, data: dict[str, Any], schema: type[TModel]) -> TModel:
        try:
            return schema.model_validate(data)
        except Exception as exc:
            raise RuntimeError(f"Invalid {schema.__name__} payload from model: {exc}") from exc
