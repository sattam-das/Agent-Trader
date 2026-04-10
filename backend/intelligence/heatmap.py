"""Sector Heatmap — live sector performance for India & US markets.

Groups representative stocks by sector, fetches latest prices via yfinance,
and computes weighted sector-level change percentages.
"""

from __future__ import annotations

from typing import Any, Optional

import yfinance as yf
import pandas as pd


# ------------------------------------------------------------------
# Sector definitions with representative stocks
# ------------------------------------------------------------------
_SECTORS = {
    "india": {
        "IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS"],
        "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
        "Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"],
        "Auto": ["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS"],
        "Energy": ["RELIANCE.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "ADANIGREEN.NS"],
        "FMCG": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS"],
        "Metals": ["TATASTEEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "COALINDIA.NS", "VEDL.NS"],
        "Realty": ["DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PRESTIGE.NS", "BRIGADE.NS"],
        "Infra": ["LT.NS", "ADANIPORTS.NS", "ULTRACEMCO.NS", "GRASIM.NS", "SHREECEM.NS"],
        "Finance": ["BAJFINANCE.NS", "BAJAJFINSV.NS", "SBILIFE.NS", "HDFCLIFE.NS", "ICICIPRULI.NS"],
    },
    "us": {
        "Tech": ["AAPL", "MSFT", "GOOGL", "NVDA", "META"],
        "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "MRK"],
        "Finance": ["JPM", "BAC", "GS", "MS", "WFC"],
        "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
        "Consumer": ["AMZN", "TSLA", "HD", "NKE", "SBUX"],
        "Industrial": ["CAT", "BA", "GE", "UPS", "HON"],
    },
}


class SectorHeatmap:
    """Fetch live sector performance data."""

    @staticmethod
    def get_heatmap(market: str = "india") -> dict[str, Any]:
        """Get sector-level performance with stock-level detail.

        Parameters
        ----------
        market : str
            "india" or "us" (default "india").
        """
        sectors_config = _SECTORS.get(market.lower(), _SECTORS["india"])
        sectors = []

        for sector_name, tickers in sectors_config.items():
            try:
                sector_data = _fetch_sector(sector_name, tickers)
                sectors.append(sector_data)
            except Exception:
                sectors.append({
                    "name": sector_name,
                    "change_pct": 0.0,
                    "leaders": [],
                    "status": "error",
                })

        # Sort by change_pct (best performing first)
        sectors.sort(key=lambda s: s.get("change_pct", 0), reverse=True)

        # Market-wide mood
        avg_change = sum(s.get("change_pct", 0) for s in sectors) / max(len(sectors), 1)
        if avg_change > 1.0:
            mood = "strong_bullish"
        elif avg_change > 0.2:
            mood = "bullish"
        elif avg_change > -0.2:
            mood = "neutral"
        elif avg_change > -1.0:
            mood = "bearish"
        else:
            mood = "strong_bearish"

        return {
            "market": market,
            "sector_count": len(sectors),
            "market_mood": mood,
            "avg_change_pct": round(avg_change, 2),
            "sectors": sectors,
        }


def _fetch_sector(name: str, tickers: list[str]) -> dict[str, Any]:
    """Fetch price data for a sector's stocks."""
    leaders = []
    changes = []

    # Download all tickers at once for performance
    data = yf.download(tickers, period="2d", progress=False, auto_adjust=True, group_by="ticker")

    for ticker in tickers:
        try:
            if len(tickers) == 1:
                ticker_data = data
            else:
                ticker_data = data[ticker] if ticker in data.columns.get_level_values(0) else None

            if ticker_data is None or ticker_data.empty:
                continue

            # Flatten MultiIndex if needed
            if isinstance(ticker_data.columns, pd.MultiIndex):
                ticker_data.columns = [col[0] if isinstance(col, tuple) else col for col in ticker_data.columns]

            closes = ticker_data["Close"].dropna()
            if len(closes) < 2:
                continue

            current = float(closes.iloc[-1])
            prev = float(closes.iloc[-2])
            change = ((current - prev) / prev) * 100

            short_name = ticker.replace(".NS", "").replace(".BO", "")

            leaders.append({
                "ticker": ticker,
                "name": short_name,
                "price": round(current, 2),
                "change_pct": round(change, 2),
            })
            changes.append(change)
        except Exception:
            continue

    # Sort leaders by absolute change (most active first)
    leaders.sort(key=lambda x: abs(x["change_pct"]), reverse=True)

    sector_change = sum(changes) / max(len(changes), 1) if changes else 0.0

    return {
        "name": name,
        "change_pct": round(sector_change, 2),
        "stock_count": len(leaders),
        "leaders": leaders,
    }
