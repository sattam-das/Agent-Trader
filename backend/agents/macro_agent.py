"""Macro / Institutional Agent — analyzes insider trades, institutional
holdings, sector positioning, and analyst consensus to gauge smart-money
sentiment.
"""

from __future__ import annotations

import json
from typing import Any

from .base_agent import BaseGroqAgent, MacroAnalysis


class MacroAgent(BaseGroqAgent):
    async def analyze(self, macro_data: dict[str, Any]) -> MacroAnalysis:
        insider_trades = macro_data.get("insider_trades", [])
        institutional_holders = macro_data.get("institutional_holders", [])
        analyst_targets = macro_data.get("analyst_targets", {})
        sector = macro_data.get("sector", "Unknown")
        industry = macro_data.get("industry", "Unknown")

        has_data = insider_trades or institutional_holders or analyst_targets
        if not has_data:
            return MacroAnalysis(
                macro_score=0.5,
                institutional_sentiment="neutral",
                insider_signal="no data",
                sector_outlook="neutral",
                key_observations=["Insufficient macro data available."],
                summary="Macro data was unavailable, so the assessment is neutral.",
            )

        # Summarise insider activity
        insider_summary = self._summarise_insider_trades(insider_trades)

        # Summarise institutional holdings
        holder_summary = self._summarise_holders(institutional_holders)

        prompt = (
            "You are a macro/institutional analyst. Analyze the following smart-money data "
            "for a stock and assess overall institutional sentiment.\n\n"
            "Return JSON with keys:\n"
            '- macro_score: 0 to 1 (0 = very bearish institutional outlook, 1 = very bullish)\n'
            '- institutional_sentiment: one of "very_bullish", "bullish", "neutral", "bearish", "very_bearish"\n'
            '- insider_signal: one of "heavy_buying", "buying", "neutral", "selling", "heavy_selling", "no data"\n'
            '- sector_outlook: one of "positive", "neutral", "negative"\n'
            '- key_observations: list of concise observations about smart-money activity\n'
            '- summary: 1-2 sentence overall assessment\n\n'
            f"Sector: {sector}\n"
            f"Industry: {industry}\n\n"
            f"Analyst Consensus:\n{json.dumps(analyst_targets, ensure_ascii=True)}\n\n"
            f"Recent Insider Activity:\n{insider_summary}\n\n"
            f"Top Institutional Holders:\n{holder_summary}"
        )

        raw = await self._complete_json(prompt)

        # Normalise fields
        inst_sent = str(raw.get("institutional_sentiment") or "neutral").lower().strip().replace(" ", "_")
        valid_sentiments = {"very_bullish", "bullish", "neutral", "bearish", "very_bearish"}
        raw["institutional_sentiment"] = inst_sent if inst_sent in valid_sentiments else "neutral"

        insider_sig = str(raw.get("insider_signal") or "no data").lower().strip().replace(" ", "_")
        valid_signals = {"heavy_buying", "buying", "neutral", "selling", "heavy_selling", "no data"}
        raw["insider_signal"] = insider_sig if insider_sig in valid_signals else "neutral"

        sector_out = str(raw.get("sector_outlook") or "neutral").lower().strip()
        valid_outlooks = {"positive", "neutral", "negative"}
        raw["sector_outlook"] = sector_out if sector_out in valid_outlooks else "neutral"

        raw["key_observations"] = self._normalise_list(raw.get("key_observations"))

        return self._validate(raw, MacroAnalysis)

    @staticmethod
    def _summarise_insider_trades(trades: list[dict[str, Any]]) -> str:
        if not trades:
            return "No recent insider trades available."

        lines: list[str] = []
        for t in trades[:10]:
            insider = t.get("insider", "Unknown")
            txn = t.get("transaction", "Unknown")
            shares = t.get("shares", "?")
            value = t.get("value", "?")
            date = t.get("date", "?")
            lines.append(f"- {insider}: {txn} {shares} shares (${value}) on {date}")

        return "\n".join(lines)

    @staticmethod
    def _summarise_holders(holders: list[dict[str, Any]]) -> str:
        if not holders:
            return "No institutional holder data available."

        lines: list[str] = []
        for h in holders[:10]:
            name = h.get("holder", "Unknown")
            shares = h.get("shares", "?")
            pct = h.get("pct_held", "?")
            lines.append(f"- {name}: {shares} shares ({pct}% held)")

        return "\n".join(lines)

    @staticmethod
    def _normalise_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        return []
