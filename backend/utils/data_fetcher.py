"""Enhanced data fetcher with full financials, insider trades,
institutional holdings, analyst targets, and Google News RSS fallback.

All data sourced from yfinance (free, no key) and NewsAPI / Google News RSS.
"""

from __future__ import annotations

import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
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

    # ------------------------------------------------------------------
    # Core live data fetching
    # ------------------------------------------------------------------
    def _fetch_live_data(self, ticker: str) -> dict[str, Any]:
        stock = yf.Ticker(ticker)
        info = stock.info or {}

        # 1-year daily history for technical analysis
        history_1y = stock.history(period="1y")
        # 3-month for backward compat
        history_3mo = stock.history(period="3mo")

        company_name = (
            info.get("longName")
            or info.get("shortName")
            or info.get("displayName")
            or ticker
        )

        # Fetch news (NewsAPI with Google News RSS fallback)
        news_articles = self._fetch_news(company_name)

        # Fetch insider transactions
        insider_trades = self._fetch_insider_trades(stock)

        # Fetch institutional holders
        institutional_holders = self._fetch_institutional_holders(stock)

        # Fetch analyst price targets
        analyst_targets = self._fetch_analyst_targets(stock)

        # Fetch full financial statements
        full_financials = self._fetch_full_financials(stock)

        payload = {
            "ticker": ticker,
            "company_name": str(company_name),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "sector": str(info.get("sector") or "Unknown"),
            "industry": str(info.get("industry") or "Unknown"),
            "current_price": self._to_primitive(info.get("currentPrice") or info.get("regularMarketPrice")),
            "market_state": str(info.get("marketState") or "UNKNOWN"),
            "financials": {
                "pe_ratio": self._to_primitive(info.get("trailingPE")),
                "forward_pe": self._to_primitive(info.get("forwardPE")),
                "peg_ratio": self._to_primitive(info.get("pegRatio")),
                "revenue_growth": self._to_primitive(info.get("revenueGrowth")),
                "earnings_growth": self._to_primitive(info.get("earningsGrowth")),
                "profit_margin": self._to_primitive(info.get("profitMargins")),
                "operating_margin": self._to_primitive(info.get("operatingMargins")),
                "market_cap": self._to_primitive(info.get("marketCap")),
                "enterprise_value": self._to_primitive(info.get("enterpriseValue")),
                "dividend_yield": self._to_primitive(info.get("dividendYield")),
                "return_on_equity": self._to_primitive(info.get("returnOnEquity")),
                "debt_to_equity": self._to_primitive(info.get("debtToEquity")),
                "current_ratio": self._to_primitive(info.get("currentRatio")),
                "free_cash_flow": self._to_primitive(info.get("freeCashflow")),
                "revenue": self._to_primitive(info.get("totalRevenue")),
                "book_value": self._to_primitive(info.get("bookValue")),
                "price_to_book": self._to_primitive(info.get("priceToBook")),
            },
            "risk_data": {
                "beta": self._to_primitive(info.get("beta")),
                "volatility": self._calculate_volatility(history_3mo),
                "fifty_two_week_high": self._to_primitive(info.get("fiftyTwoWeekHigh")),
                "fifty_two_week_low": self._to_primitive(info.get("fiftyTwoWeekLow")),
                "avg_volume": self._to_primitive(info.get("averageVolume")),
                "short_ratio": self._to_primitive(info.get("shortRatio")),
            },
            "news": news_articles,
            "price_history": self._dataframe_to_ohlcv(history_1y),
            "insider_trades": insider_trades,
            "institutional_holders": institutional_holders,
            "analyst_targets": analyst_targets,
            "full_financials": full_financials,
        }

        return payload

    # ------------------------------------------------------------------
    # News fetching (NewsAPI + Google News RSS fallback)
    # ------------------------------------------------------------------
    def _fetch_news(self, company_name: str) -> list[dict[str, Any]]:
        # Try NewsAPI first
        if self.newsapi is not None:
            try:
                return self._fetch_news_api(company_name)
            except Exception:
                pass

        # Fallback to free Google News RSS (no API key needed)
        return self._fetch_google_news_rss(company_name)

    def _fetch_news_api(self, company_name: str) -> list[dict[str, Any]]:
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        response = self.newsapi.get_everything(
            q=company_name,
            from_param=seven_days_ago.strftime("%Y-%m-%d"),
            language="en",
            sort_by="relevancy",
            page_size=10,
        )
        articles = response.get("articles", [])

        normalized: list[dict[str, Any]] = []
        for article in articles:
            normalized.append({
                "source": (article.get("source") or {}).get("name"),
                "author": article.get("author"),
                "title": article.get("title"),
                "description": article.get("description"),
                "url": article.get("url"),
                "published_at": article.get("publishedAt"),
            })
        return normalized

    def _fetch_google_news_rss(self, query: str) -> list[dict[str, Any]]:
        """Free Google News RSS — no API key, no rate limit."""
        try:
            encoded_query = urllib.request.quote(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                xml_data = resp.read()

            root = ET.fromstring(xml_data)
            articles: list[dict[str, Any]] = []

            for item in root.findall(".//item")[:10]:
                title = item.findtext("title", "")
                description = item.findtext("description", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                source = item.findtext("source", "")

                articles.append({
                    "source": source or None,
                    "author": None,
                    "title": title or None,
                    "description": description or None,
                    "url": link or None,
                    "published_at": pub_date or None,
                })

            return articles
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Insider trades
    # ------------------------------------------------------------------
    def _fetch_insider_trades(self, stock: yf.Ticker) -> list[dict[str, Any]]:
        try:
            insider_df = stock.insider_transactions
            if insider_df is None or insider_df.empty:
                return []

            trades: list[dict[str, Any]] = []
            for _, row in insider_df.head(20).iterrows():
                trades.append({
                    "insider": str(row.get("Insider Trading", row.get("insider", ""))),
                    "relation": str(row.get("Relationship", row.get("relationship", ""))),
                    "date": str(row.get("Start Date", row.get("date", ""))),
                    "transaction": str(row.get("Transaction", row.get("transaction", ""))),
                    "shares": self._to_primitive(row.get("Shares", row.get("shares"))),
                    "value": self._to_primitive(row.get("Value", row.get("value"))),
                })
            return trades
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Institutional holders
    # ------------------------------------------------------------------
    def _fetch_institutional_holders(self, stock: yf.Ticker) -> list[dict[str, Any]]:
        try:
            holders_df = stock.institutional_holders
            if holders_df is None or holders_df.empty:
                return []

            holders: list[dict[str, Any]] = []
            for _, row in holders_df.head(15).iterrows():
                holders.append({
                    "holder": str(row.get("Holder", "")),
                    "shares": self._to_primitive(row.get("Shares", row.get("shares"))),
                    "date_reported": str(row.get("Date Reported", "")),
                    "pct_held": self._to_primitive(row.get("% Out", row.get("pctHeld"))),
                    "value": self._to_primitive(row.get("Value", row.get("value"))),
                })
            return holders
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Analyst targets
    # ------------------------------------------------------------------
    def _fetch_analyst_targets(self, stock: yf.Ticker) -> dict[str, Any]:
        try:
            info = stock.info or {}
            return {
                "target_low": self._to_primitive(info.get("targetLowPrice")),
                "target_mean": self._to_primitive(info.get("targetMeanPrice")),
                "target_median": self._to_primitive(info.get("targetMedianPrice")),
                "target_high": self._to_primitive(info.get("targetHighPrice")),
                "recommendation": str(info.get("recommendationKey") or "none"),
                "num_analysts": self._to_primitive(info.get("numberOfAnalystOpinions")),
            }
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Full financial statements
    # ------------------------------------------------------------------
    def _fetch_full_financials(self, stock: yf.Ticker) -> dict[str, Any]:
        result: dict[str, Any] = {}

        try:
            income = stock.income_stmt
            if income is not None and not income.empty:
                result["income_statement"] = self._financial_df_to_dict(income)
        except Exception:
            pass

        try:
            balance = stock.balance_sheet
            if balance is not None and not balance.empty:
                result["balance_sheet"] = self._financial_df_to_dict(balance)
        except Exception:
            pass

        try:
            cashflow = stock.cashflow
            if cashflow is not None and not cashflow.empty:
                result["cash_flow"] = self._financial_df_to_dict(cashflow)
        except Exception:
            pass

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _dataframe_to_ohlcv(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """Convert a yfinance history DataFrame to a list of OHLCV dicts."""
        if df is None or df.empty:
            return []

        records: list[dict[str, Any]] = []
        for date, row in df.iterrows():
            records.append({
                "date": str(date.date()) if hasattr(date, "date") else str(date),
                "open": round(float(row.get("Open", 0)), 2),
                "high": round(float(row.get("High", 0)), 2),
                "low": round(float(row.get("Low", 0)), 2),
                "close": round(float(row.get("Close", 0)), 2),
                "volume": int(row.get("Volume", 0)),
            })
        return records

    def _financial_df_to_dict(self, df: pd.DataFrame) -> dict[str, dict[str, Any]]:
        """Convert a financial statement DataFrame to a serialisable dict."""
        result: dict[str, dict[str, Any]] = {}
        for col in df.columns:
            col_key = str(col.date()) if hasattr(col, "date") else str(col)
            result[col_key] = {}
            for idx, val in df[col].items():
                result[col_key][str(idx)] = self._to_primitive(val)
        return result

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
        if isinstance(value, (str, bool)):
            return value
        if isinstance(value, (int, float)):
            if pd.isna(value):
                return None
            return value

        try:
            f = float(value)
            if pd.isna(f):
                return None
            return f
        except (TypeError, ValueError):
            return str(value)
