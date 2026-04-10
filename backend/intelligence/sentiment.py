"""Sentiment Scanner — aggregates sentiment from Reddit RSS and news.

Scrapes Reddit (r/IndianStreetBets, r/wallstreetbets, r/stocks) RSS feeds
for ticker mentions and estimates sentiment using keyword analysis.
No API key required — uses public RSS endpoints.
"""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree

import httpx


# ------------------------------------------------------------------
# Subreddit configurations
# ------------------------------------------------------------------
_SUBREDDITS = {
    "india": [
        {"name": "IndianStreetBets", "url": "https://www.reddit.com/r/IndianStreetBets/hot.rss?limit=50"},
        {"name": "IndiaInvestments", "url": "https://www.reddit.com/r/IndiaInvestments/hot.rss?limit=30"},
        {"name": "DalalStreetTalks", "url": "https://www.reddit.com/r/DalalStreetTalks/hot.rss?limit=30"},
    ],
    "us": [
        {"name": "wallstreetbets", "url": "https://www.reddit.com/r/wallstreetbets/hot.rss?limit=50"},
        {"name": "stocks", "url": "https://www.reddit.com/r/stocks/hot.rss?limit=30"},
        {"name": "investing", "url": "https://www.reddit.com/r/investing/hot.rss?limit=30"},
    ],
}

_POSITIVE_WORDS = frozenset([
    "bull", "bullish", "buy", "long", "moon", "rocket", "surge", "rally",
    "breakout", "green", "profit", "gain", "up", "growth", "beat", "strong",
    "undervalued", "calls", "accumulate", "hold", "🚀", "📈", "🟢",
])

_NEGATIVE_WORDS = frozenset([
    "bear", "bearish", "sell", "short", "crash", "dump", "red", "loss",
    "decline", "drop", "fall", "overvalued", "puts", "warning", "risk",
    "down", "weak", "bubble", "scam", "avoid", "📉", "🔴", "💀",
])


class SentimentScanner:
    """Scan Reddit and news for ticker sentiment."""

    @staticmethod
    async def scan(ticker: str) -> dict[str, Any]:
        """Scan Reddit for mentions and sentiment of a ticker.

        Parameters
        ----------
        ticker : str
            Stock ticker (e.g., "RELIANCE.NS" or "AAPL").
        """
        # Determine market
        is_indian = ticker.endswith(".NS") or ticker.endswith(".BO")
        market = "india" if is_indian else "us"

        # Clean ticker for text search
        search_terms = _get_search_terms(ticker)

        # Fetch Reddit posts
        subreddits = _SUBREDDITS.get(market, _SUBREDDITS["us"])
        all_posts = []

        async with httpx.AsyncClient(timeout=10) as client:
            for sub in subreddits:
                try:
                    posts = await _fetch_subreddit(client, sub, search_terms)
                    all_posts.extend(posts)
                except Exception:
                    continue

        # Calculate sentiment
        total_mentions = len(all_posts)
        if total_mentions == 0:
            return {
                "ticker": ticker,
                "market": market,
                "reddit": {
                    "mentions": 0,
                    "sentiment_score": 0.5,
                    "sentiment": "no_data",
                    "top_posts": [],
                    "subreddits_scanned": len(subreddits),
                },
                "summary": f"No recent Reddit mentions found for {ticker}",
            }

        positive = sum(1 for p in all_posts if p["sentiment"] == "positive")
        negative = sum(1 for p in all_posts if p["sentiment"] == "negative")
        neutral = total_mentions - positive - negative

        # Score: 0.0 (fully bearish) to 1.0 (fully bullish)
        if total_mentions > 0:
            score = (positive - negative + total_mentions) / (2 * total_mentions)
            score = max(0.0, min(1.0, score))
        else:
            score = 0.5

        if score >= 0.65:
            sentiment = "bullish"
        elif score >= 0.55:
            sentiment = "slightly_bullish"
        elif score >= 0.45:
            sentiment = "neutral"
        elif score >= 0.35:
            sentiment = "slightly_bearish"
        else:
            sentiment = "bearish"

        # Sort by engagement score
        all_posts.sort(key=lambda p: p.get("score", 0), reverse=True)

        return {
            "ticker": ticker,
            "market": market,
            "reddit": {
                "mentions": total_mentions,
                "sentiment_score": round(score, 3),
                "sentiment": sentiment,
                "positive_count": positive,
                "negative_count": negative,
                "neutral_count": neutral,
                "top_posts": all_posts[:10],
                "subreddits_scanned": len(subreddits),
            },
            "summary": (
                f"{ticker}: {total_mentions} Reddit mentions. "
                f"Sentiment is {sentiment} ({score:.0%}). "
                f"{positive} positive, {negative} negative, {neutral} neutral."
            ),
        }


def _get_search_terms(ticker: str) -> list[str]:
    """Generate search terms from a ticker symbol."""
    clean = ticker.replace(".NS", "").replace(".BO", "").upper()
    terms = [clean]

    # Add common name mappings for popular Indian stocks
    name_map = {
        "RELIANCE": ["reliance", "ril", "jio"],
        "TCS": ["tcs", "tata consultancy"],
        "INFY": ["infy", "infosys"],
        "HDFCBANK": ["hdfc bank", "hdfc"],
        "ICICIBANK": ["icici bank", "icici"],
        "SBIN": ["sbi", "state bank"],
        "BAJFINANCE": ["bajaj finance", "bajfinance"],
        "ITC": ["itc"],
        "WIPRO": ["wipro"],
        "TATAMOTORS": ["tata motors", "tatamotors"],
        "AAPL": ["apple", "aapl"],
        "TSLA": ["tesla", "tsla"],
        "NVDA": ["nvidia", "nvda"],
        "MSFT": ["microsoft", "msft"],
        "GOOGL": ["google", "googl", "alphabet"],
        "AMZN": ["amazon", "amzn"],
        "META": ["meta", "facebook"],
    }

    extras = name_map.get(clean, [])
    terms.extend(extras)
    return terms


async def _fetch_subreddit(
    client: httpx.AsyncClient,
    sub_config: dict[str, str],
    search_terms: list[str],
) -> list[dict[str, Any]]:
    """Fetch and filter posts from a subreddit RSS feed."""
    headers = {"User-Agent": "AgentTrader/3.0 (Stock Sentiment Scanner)"}
    resp = await client.get(sub_config["url"], headers=headers)

    if resp.status_code != 200:
        return []

    root = ElementTree.fromstring(resp.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    posts = []

    for entry in root.findall(".//atom:entry", ns):
        title = entry.findtext("atom:title", "", ns).strip()
        content = entry.findtext("atom:content", "", ns).strip()
        link = ""
        for link_el in entry.findall("atom:link", ns):
            href = link_el.get("href", "")
            if "/comments/" in href:
                link = href
                break

        full_text = (title + " " + content).lower()

        # Check if any search term matches
        matched = any(term.lower() in full_text for term in search_terms)
        if not matched:
            continue

        # Determine sentiment
        pos_count = sum(1 for w in _POSITIVE_WORDS if w in full_text)
        neg_count = sum(1 for w in _NEGATIVE_WORDS if w in full_text)

        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        updated = entry.findtext("atom:updated", "", ns)

        posts.append({
            "title": title[:200],
            "url": link,
            "subreddit": sub_config["name"],
            "sentiment": sentiment,
            "positive_signals": pos_count,
            "negative_signals": neg_count,
            "updated": updated[:19] if updated else "",
            "score": pos_count + neg_count,  # Engagement proxy
        })

    return posts
