from __future__ import annotations

import json
from typing import Any

from .base_agent import BaseGroqAgent, RiskAnalysis


class RiskAgent(BaseGroqAgent):
    async def analyze(self, risk_data: dict[str, Any]) -> RiskAnalysis:
        normalized = {
            "beta": risk_data.get("beta"),
            "volatility": risk_data.get("volatility"),
        }

        has_any_data = any(value is not None for value in normalized.values())
        if not has_any_data:
            return RiskAnalysis(
                risk_level=0.5,
                risk_factors=["Risk metrics unavailable."],
                summary="Risk metrics were unavailable, so the risk assessment is neutral.",
            )

        prompt = (
            "Assess market risk for the stock using beta and historical volatility values. "
            "Higher beta and higher volatility should generally increase risk_level. "
            "Return JSON with keys: risk_level, risk_factors, summary. "
            "risk_level must be 0 to 1, where 1 means highest risk. "
            "risk_factors should be concise strings. summary should be 1-2 sentences.\n\n"
            f"risk_data:\n{json.dumps(normalized, ensure_ascii=True)}"
        )

        raw = await self._complete_json(prompt)

        risk_level = raw.get("risk_level")
        try:
            risk_level = float(risk_level)
        except (TypeError, ValueError):
            risk_level = 0.5
        raw["risk_level"] = max(0.0, min(1.0, risk_level))

        return self._validate(raw, RiskAnalysis)
