from __future__ import annotations

import json
from typing import Any

from .base_agent import BaseGroqAgent, FinancialAnalysis


class FinancialAgent(BaseGroqAgent):
    async def analyze(self, financials: dict[str, Any]) -> FinancialAnalysis:
        normalized = {
            "pe_ratio": financials.get("pe_ratio"),
            "revenue_growth": financials.get("revenue_growth"),
            "profit_margin": financials.get("profit_margin"),
            "market_cap": financials.get("market_cap"),
        }

        has_any_data = any(value is not None for value in normalized.values())
        if not has_any_data:
            return FinancialAnalysis(
                health_score=0.5,
                strengths=[],
                weaknesses=["Insufficient financial data available."],
                summary="Financial metrics were unavailable, so this analysis is neutral.",
            )

        prompt = (
            "Perform a fundamentals-based financial health analysis for this company. "
            "Use common interpretation of P/E ratio, revenue growth, profit margin, and market cap. "
            "Return JSON with keys: health_score, strengths, weaknesses, summary. "
            "health_score must be 0 to 1, where 1 is strongest. strengths and weaknesses are short strings. "
            "summary should be 1-2 sentences.\n\n"
            f"financials:\n{json.dumps(normalized, ensure_ascii=True)}"
        )

        raw = await self._complete_json(prompt)

        strengths = raw.get("strengths")
        weaknesses = raw.get("weaknesses")

        raw["strengths"] = self._normalize_list(strengths)
        raw["weaknesses"] = self._normalize_list(weaknesses)

        return self._validate(raw, FinancialAnalysis)

    @staticmethod
    def _normalize_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            parts = [part.strip(" -") for part in text.replace(";", ",").split(",")]
            return [part for part in parts if part]

        return []
