from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yfinance as yf
from newsapi import NewsApiClient


class DataFetcher:
    def __init__(self, news_api_key: str | None, cache_dir: str | Path = "data/cache") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.newsapi = NewsApiClient(api_key=news_api_key) if news_api_key else None

    def get_stock_data(
        self,
        ticker: str,
        use_cache: bool = True,
        max_cache_age_hours: int | None = None,
    ) -> dict[str, Any]:
        symbol = ticker.strip().upper()
        if not symbol:
            raise ValueError("Ticker cannot be empty")

        cached_payload = self._read_cache(symbol)
        if use_cache and cached_payload and self._is_cache_fresh(cached_payload, max_cache_age_hours):
            return cached_payload

        try:
            payload = self._fetch_live_data(symbol)
            self._write_cache(symbol, payload)
            return payload
        except Exception:
            if use_cache and cached_payload:
                return cached_payload
            raise

    def _fetch_live_data(self, ticker: str) -> dict[str, Any]:
        stock = yf.Ticker(ticker)
        info = stock.info or {}
        history = stock.history(period="3mo")

        company_name = (
            info.get("longName")
            or info.get("shortName")
            or info.get("displayName")
            or ticker
        )

        news_articles = self._fetch_news(company_name)

        payload = {
            "ticker": ticker,
            "company_name": str(company_name),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "financials": {
                "pe_ratio": self._to_primitive(info.get("trailingPE")),
                "revenue_growth": self._to_primitive(info.get("revenueGrowth")),
                "profit_margin": self._to_primitive(info.get("profitMargins")),
                "market_cap": self._to_primitive(info.get("marketCap")),
            },
            "risk_data": {
                "beta": self._to_primitive(info.get("beta")),
                "volatility": self._calculate_volatility(history),
            },
            "news": news_articles,
        }

        return payload

    def _fetch_news(self, company_name: str) -> list[dict[str, Any]]:
        if self.newsapi is None:
            return []

        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        response = self.newsapi.get_everything(
            q=company_name,
            from_param=seven_days_ago.strftime("%Y-%m-%d"),
            language="en",
            sort_by="relevancy",
            page_size=10,
        )
        articles = response.get("articles", [])

        normalized_articles: list[dict[str, Any]] = []
        for article in articles:
            normalized_articles.append(
                {
                    "source": (article.get("source") or {}).get("name"),
                    "author": article.get("author"),
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "url": article.get("url"),
                    "published_at": article.get("publishedAt"),
                }
            )
        return normalized_articles

    def _calculate_volatility(self, history: Any) -> float | None:
        if history is None or history.empty or "Close" not in history:
            return None

        pct_changes = history["Close"].pct_change().dropna()
        if pct_changes.empty:
            return None

        try:
            return float(pct_changes.std())
        except Exception:
            return None

    def _cache_file(self, ticker: str) -> Path:
        return self.cache_dir / f"{ticker}.json"

    def _read_cache(self, ticker: str) -> dict[str, Any] | None:
        cache_file = self._cache_file(ticker)
        if not cache_file.exists():
            return None

        try:
            with cache_file.open("r", encoding="utf-8") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

        if not self._is_valid_payload(payload):
            return None

        return payload

    def _write_cache(self, ticker: str, payload: dict[str, Any]) -> None:
        cache_file = self._cache_file(ticker)
        temp_file = cache_file.with_suffix(".tmp")

        with temp_file.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=True)

        temp_file.replace(cache_file)

    def _is_cache_fresh(self, payload: dict[str, Any], max_cache_age_hours: int | None) -> bool:
        if max_cache_age_hours is None:
            return True

        fetched_at_raw = payload.get("fetched_at")
        if not isinstance(fetched_at_raw, str):
            return False

        try:
            fetched_at = datetime.fromisoformat(fetched_at_raw)
        except ValueError:
            return False

        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)

        age = datetime.now(timezone.utc) - fetched_at
        return age <= timedelta(hours=max_cache_age_hours)

    def _is_valid_payload(self, payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False

        required_keys = {
            "ticker",
            "company_name",
            "fetched_at",
            "financials",
            "risk_data",
            "news",
        }
        if not required_keys.issubset(payload.keys()):
            return False

        if not isinstance(payload.get("financials"), dict):
            return False
        if not isinstance(payload.get("risk_data"), dict):
            return False
        if not isinstance(payload.get("news"), list):
            return False

        return True

    def _to_primitive(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (str, bool, int, float)):
            return value

        try:
            return float(value)
        except (TypeError, ValueError):
            return str(value)
