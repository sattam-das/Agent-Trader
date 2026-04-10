from __future__ import annotations

import json
from typing import Any

from .base_agent import BaseGroqAgent, DiscoveryAnalysis, DiscoverySuggestion


class DiscoveryAgent(BaseGroqAgent):
    DEFAULT_FALLBACK_TICKERS = [
        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "AMD", "NFLX",
        "INTC", "QCOM", "ADBE", "CRM", "ORCL", "IBM", "UBER", "SHOP", "PLTR", "SNOW",
        "JPM", "BAC", "GS", "MS", "V", "MA", "PYPL", "BRK-B", "WMT", "COST",
        "PG", "KO", "PEP", "XOM", "CVX", "CAT", "GE", "BA", "UNH", "PFE",
    ]

    async def analyze(self, market_context: dict[str, Any], exclude_tickers: list[str] | None = None) -> DiscoveryAnalysis:
        market_news = market_context.get("market_news") or []
        candidate_tickers = market_context.get("candidate_tickers") or []
        excluded = {
            self._normalize_ticker(str(t).strip().upper())
            for t in (exclude_tickers or [])
            if str(t).strip()
        }

        compact_news: list[dict[str, Any]] = []
        for item in market_news[:25]:
            compact_news.append(
                {
                    "title": str(item.get("title") or "").strip(),
                    "description": str(item.get("description") or "").strip(),
                    "source": str(item.get("source") or "").strip(),
                    "published_at": str(item.get("published_at") or "").strip(),
                }
            )

        prompt = (
            "You are a stock discovery analyst. Based on market-wide news context and candidate tickers, "
            "suggest 3 to 5 promising stocks to analyze next. "
            "Return JSON with keys: suggestions, summary. "
            "Each item in suggestions must have: ticker, company_name, reason, confidence. "
            "ticker should be uppercase symbol, confidence must be 0 to 1, reason should be concise and specific. "
            "Prefer diversity in sectors when possible and avoid excluded tickers completely. "
            "If context is weak, still provide best-effort ideas with moderate confidence.\n\n"
            f"market_news:\n{json.dumps(compact_news, ensure_ascii=True)}\n\n"
            f"candidate_tickers:\n{json.dumps(candidate_tickers, ensure_ascii=True)}\n\n"
            f"exclude_tickers:\n{json.dumps(sorted(excluded), ensure_ascii=True)}"
        )

        raw = await self._complete_json(prompt)

        raw_suggestions = raw.get("suggestions")
        if not isinstance(raw_suggestions, list):
            raw_suggestions = []

        normalized_suggestions: list[dict[str, Any]] = []
        for suggestion in raw_suggestions:
            if not isinstance(suggestion, dict):
                continue

            ticker = self._normalize_ticker(str(suggestion.get("ticker") or "").strip().upper())
            company_name = str(suggestion.get("company_name") or ticker).strip()
            reason = str(suggestion.get("reason") or "").strip()

            try:
                confidence = float(suggestion.get("confidence"))
            except (TypeError, ValueError):
                confidence = 0.5

            if not ticker or not reason or ticker in excluded:
                continue

            normalized_suggestions.append(
                {
                    "ticker": ticker,
                    "company_name": company_name or ticker,
                    "reason": reason,
                    "confidence": max(0.0, min(1.0, confidence)),
                }
            )

        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in normalized_suggestions:
            ticker = item["ticker"]
            if ticker in seen:
                continue
            seen.add(ticker)
            deduped.append(item)
            if len(deduped) >= 5:
                break

        if len(deduped) < 3:
            for ticker in [self._normalize_ticker(str(t).strip().upper()) for t in candidate_tickers if str(t).strip()]:
                if not ticker or ticker in seen or ticker in excluded:
                    continue
                seen.add(ticker)
                deduped.append(
                    DiscoverySuggestion(
                        ticker=ticker,
                        company_name=ticker,
                        reason="Included as a fallback candidate due to limited market context.",
                        confidence=0.45,
                    ).model_dump()
                )
                if len(deduped) >= 5:
                    break

        if len(deduped) < 3:
            for ticker in self.DEFAULT_FALLBACK_TICKERS:
                if ticker in seen or ticker in excluded:
                    continue
                seen.add(ticker)
                deduped.append(
                    DiscoverySuggestion(
                        ticker=ticker,
                        company_name=ticker,
                        reason="Default fallback candidate for discovery continuity.",
                        confidence=0.4,
                    ).model_dump()
                )
                if len(deduped) >= 3:
                    break

        raw["suggestions"] = deduped
        if not str(raw.get("summary") or "").strip():
            raw["summary"] = "Suggested tickers are based on current market context and available candidates."

        return self._validate(raw, DiscoveryAnalysis)

    @staticmethod
    def _normalize_ticker(ticker: str) -> str:
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-")
        cleaned = "".join(ch for ch in ticker if ch in allowed)
        return cleaned[:12]
