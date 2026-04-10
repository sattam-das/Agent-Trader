"""Market Pulse — categorized, broad-market news aggregator.

Fetches news from multiple Google News RSS categories and organizes
them into breaking, India market, global market, earnings, and crypto feeds.
Estimates market mood from aggregate sentiment.
"""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree

import httpx


_FEEDS = {
    "india_market": {
        "label": "🇮🇳 India Market",
        "url": "https://news.google.com/rss/search?q=sensex+nifty+indian+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
        "limit": 8,
    },
    "global_market": {
        "label": "🌐 Global Markets",
        "url": "https://news.google.com/rss/search?q=S%26P+500+global+stock+market+wall+street&hl=en-US&gl=US&ceid=US:en",
        "limit": 6,
    },
    "breaking": {
        "label": "⚡ Breaking",
        "url": "https://news.google.com/rss/search?q=breaking+stock+market+crash+surge+emergency&hl=en-IN&gl=IN&ceid=IN:en",
        "limit": 5,
    },
    "earnings": {
        "label": "💰 Earnings",
        "url": "https://news.google.com/rss/search?q=quarterly+results+earnings+Q4+profit&hl=en-IN&gl=IN&ceid=IN:en",
        "limit": 6,
    },
    "crypto": {
        "label": "₿ Crypto",
        "url": "https://news.google.com/rss/search?q=bitcoin+ethereum+crypto+market&hl=en-US&gl=US&ceid=US:en",
        "limit": 5,
    },
    "rbi_fed": {
        "label": "🏦 Central Banks",
        "url": "https://news.google.com/rss/search?q=RBI+Federal+Reserve+interest+rate+monetary+policy&hl=en-IN&gl=IN&ceid=IN:en",
        "limit": 5,
    },
    "ipos": {
        "label": "🔔 IPOs & Listings",
        "url": "https://news.google.com/rss/search?q=IPO+listing+stock+exchange+NSE+BSE&hl=en-IN&gl=IN&ceid=IN:en",
        "limit": 5,
    },
}

_POS_WORDS = frozenset([
    "surge", "jump", "rise", "gain", "bull", "high", "up", "rally",
    "profit", "growth", "buy", "positive", "record", "boost", "soar",
    "beat", "strong", "upgrade", "outperform",
])

_NEG_WORDS = frozenset([
    "fall", "drop", "crash", "bear", "low", "down", "loss", "sell",
    "negative", "decline", "cut", "slump", "plunge", "tank", "miss",
    "weak", "downgrade", "underperform", "warning", "crisis",
])


class MarketPulse:
    """Fetch categorized market news from multiple sources."""

    @staticmethod
    async def fetch(categories: list[str] | None = None) -> dict[str, Any]:
        """Fetch market pulse across all or selected categories.

        Parameters
        ----------
        categories : list[str], optional
            Filter to specific categories. If None, fetch all.
        """
        feeds = _FEEDS
        if categories:
            feeds = {k: v for k, v in _FEEDS.items() if k in categories}

        results = {}
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        total_articles = 0

        async with httpx.AsyncClient(timeout=10) as client:
            for key, config in feeds.items():
                try:
                    articles = await _fetch_feed(client, config)
                    results[key] = {
                        "label": config["label"],
                        "articles": articles,
                        "count": len(articles),
                    }
                    for a in articles:
                        sentiment_counts[a["sentiment"]] += 1
                        total_articles += 1
                except Exception:
                    results[key] = {
                        "label": config["label"],
                        "articles": [],
                        "count": 0,
                    }

        # Calculate market mood
        pos = sentiment_counts["positive"]
        neg = sentiment_counts["negative"]
        if total_articles > 0:
            score = (pos - neg + total_articles) / (2 * total_articles)
        else:
            score = 0.5

        if score >= 0.65:
            mood = "bullish"
        elif score >= 0.55:
            mood = "cautiously_bullish"
        elif score >= 0.45:
            mood = "neutral"
        elif score >= 0.35:
            mood = "cautiously_bearish"
        else:
            mood = "bearish"

        # Estimate fear/greed (0 = extreme fear, 100 = extreme greed)
        fear_greed = int(score * 100)

        return {
            "categories": results,
            "total_articles": total_articles,
            "sentiment_breakdown": sentiment_counts,
            "market_mood": mood,
            "fear_greed_estimate": fear_greed,
        }


async def _fetch_feed(
    client: httpx.AsyncClient,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Fetch and parse a single RSS feed."""
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = await client.get(config["url"], headers=headers)

    if resp.status_code != 200:
        return []

    root = ElementTree.fromstring(resp.text)
    articles = []
    limit = config.get("limit", 8)

    for item in root.findall(".//item")[:limit]:
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        pub_date = item.findtext("pubDate", "")
        source = item.findtext("source", "News")

        # Sentiment
        t_lower = title.lower()
        pos_hits = sum(1 for w in _POS_WORDS if w in t_lower)
        neg_hits = sum(1 for w in _NEG_WORDS if w in t_lower)

        if pos_hits > neg_hits:
            sentiment = "positive"
        elif neg_hits > pos_hits:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Time formatting
        time_display = pub_date[:22] if pub_date else ""

        articles.append({
            "title": title,
            "url": link,
            "source": source,
            "time": time_display,
            "sentiment": sentiment,
        })

    return articles
