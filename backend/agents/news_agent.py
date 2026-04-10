from __future__ import annotations

import json
from typing import Any

from .base_agent import BaseGroqAgent, NewsAnalysis


class NewsAgent(BaseGroqAgent):
    async def analyze(self, news_data: list[dict[str, Any]]) -> NewsAnalysis:
        headlines: list[str] = []
        for article in news_data[:10]:
            title = str(article.get("title") or "").strip()
            description = str(article.get("description") or "").strip()
            if not title and not description:
                continue
            combined = f"{title} -- {description}" if description else title
            headlines.append(combined)

        if not headlines:
            return NewsAnalysis(
                sentiment="neutral",
                sentiment_score=0.5,
                key_events=[],
                summary="No recent news was available for analysis.",
            )

        prompt = (
            "Analyze the sentiment and key events from the provided stock news items. "
            "Return JSON with keys: sentiment, sentiment_score, key_events, summary. "
            "sentiment must be one of: positive, neutral, negative. sentiment_score must be 0 to 1. "
            "key_events should be concise bullet-like strings. summary should be 1-2 sentences.\n\n"
            f"news_items:\n{json.dumps(headlines, ensure_ascii=True)}"
        )

        raw = await self._complete_json(prompt)

        sentiment = str(raw.get("sentiment") or "neutral").lower().strip()
        if sentiment not in {"positive", "neutral", "negative"}:
            sentiment = "neutral"
        raw["sentiment"] = sentiment

        return self._validate(raw, NewsAnalysis)
