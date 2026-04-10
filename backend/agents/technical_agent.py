"""Technical Analysis Agent — interprets computed indicator values
using LLM reasoning to assess signal confluence and overall technical setup.
"""

from __future__ import annotations

import json
from typing import Any

from .base_agent import BaseGroqAgent, TechnicalAnalysis


class TechnicalAgent(BaseGroqAgent):
    async def analyze(self, technical_data: dict[str, Any]) -> TechnicalAnalysis:
        snapshot = technical_data.get("snapshot", {})
        signals = technical_data.get("signals", [])
        support_resistance = snapshot.get("support_resistance", {})

        if not snapshot and not signals:
            return TechnicalAnalysis(
                signal_score=0.5,
                trend="neutral",
                signals=["No technical data available."],
                key_levels=[],
                pattern_description="Insufficient data for technical analysis.",
                summary="Technical data was unavailable, so the assessment is neutral.",
            )

        prompt = (
            "You are a technical analysis expert. Analyze the following computed indicators "
            "and signals for a stock. Assess signal confluence — when multiple indicators "
            "agree, conviction is higher.\n\n"
            "Return JSON with keys:\n"
            '- signal_score: 0 to 1 (0 = strong sell signal, 0.5 = neutral, 1 = strong buy)\n'
            '- trend: one of "strong_bullish", "bullish", "neutral", "bearish", "strong_bearish"\n'
            '- signals: list of concise signal descriptions (e.g., "RSI oversold at 28 — bullish")\n'
            '- key_levels: list of important price levels (e.g., "Support at $150.20")\n'
            '- pattern_description: 1-2 sentence description of the overall technical pattern\n'
            '- summary: 1-2 sentence actionable summary\n\n'
            f"Indicator Snapshot:\n{json.dumps(snapshot, ensure_ascii=True)}\n\n"
            f"Active Signals:\n{json.dumps(signals, ensure_ascii=True)}\n\n"
            f"Support/Resistance:\n{json.dumps(support_resistance, ensure_ascii=True)}"
        )

        raw = await self._complete_json(prompt)

        # Normalise trend
        trend = str(raw.get("trend") or "neutral").lower().strip().replace(" ", "_")
        valid_trends = {"strong_bullish", "bullish", "neutral", "bearish", "strong_bearish"}
        if trend not in valid_trends:
            trend = "neutral"
        raw["trend"] = trend

        # Normalise lists
        raw["signals"] = self._normalise_list(raw.get("signals"))
        raw["key_levels"] = self._normalise_list(raw.get("key_levels"))

        return self._validate(raw, TechnicalAnalysis)

    @staticmethod
    def _normalise_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        return []
