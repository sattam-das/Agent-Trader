"""Stock Screener — scan multiple tickers against indicator-based filters.

Supports common retail trader screens:
  - RSI oversold / overbought
  - Golden Cross / Death Cross
  - Bollinger squeeze
  - Volume spike
  - Custom price range
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd
import yfinance as yf

from backend.engine.strategies.base_strategy import BaseStrategy


# Pre-built Indian + US watchlists for quick scanning
PRESET_TICKERS = {
    "nifty50": [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "BAJFINANCE.NS", "ITC.NS",
        "KOTAKBANK.NS", "LT.NS", "HCLTECH.NS", "AXISBANK.NS", "ASIANPAINT.NS",
        "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "WIPRO.NS", "ULTRACEMCO.NS",
    ],
    "us_tech": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "META", "TSLA", "AMD", "NFLX", "INTC",
        "CRM", "ORCL", "ADBE", "PYPL", "UBER",
    ],
    "us_popular": [
        "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL",
        "AMZN", "META", "NFLX", "AMD", "INTC",
        "BAC", "JPM", "DIS", "NKE", "SBUX",
    ],
    "nse_banking": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS",
        "AXISBANK.NS", "INDUSINDBK.NS", "BANDHANBNK.NS", "PNB.NS",
    ],
    "nse_it": [
        "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS",
        "TECHM.NS", "LTIM.NS", "MPHASIS.NS", "COFORGE.NS",
    ],
}


class Screener:
    """Scan a set of tickers and return those matching the specified filter."""

    @staticmethod
    def scan(
        tickers: list[str],
        filter_type: str,
        period: str = "6mo",
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Run a screen and return matching tickers with their data.

        Parameters
        ----------
        tickers : list[str]
            Tickers to scan (e.g. ["AAPL", "RELIANCE.NS"]).
        filter_type : str
            One of: "rsi_oversold", "rsi_overbought", "golden_cross",
            "death_cross", "bb_squeeze", "volume_spike".
        period : str
            yfinance period for data download (default "6mo").
        """

        _FILTERS = {
            "rsi_oversold": Screener._rsi_oversold,
            "rsi_overbought": Screener._rsi_overbought,
            "golden_cross": Screener._golden_cross,
            "death_cross": Screener._death_cross,
            "bb_squeeze": Screener._bb_squeeze,
            "volume_spike": Screener._volume_spike,
        }

        filter_fn = _FILTERS.get(filter_type)
        if filter_fn is None:
            return [{"error": f"Unknown filter: {filter_type}. Available: {list(_FILTERS.keys())}"}]

        results: list[dict[str, Any]] = []

        for ticker in tickers:
            try:
                hist = yf.download(ticker, period=period, progress=False, auto_adjust=True)
                if hist.empty or len(hist) < 30:
                    continue

                # Flatten MultiIndex columns if present
                if isinstance(hist.columns, pd.MultiIndex):
                    hist.columns = [col[0] if isinstance(col, tuple) else col for col in hist.columns]

                match = filter_fn(ticker, hist, **kwargs)
                if match is not None:
                    results.append(match)
            except Exception:
                continue

        return results

    @staticmethod
    def get_presets() -> dict[str, list[str]]:
        """Return available preset ticker lists."""
        return PRESET_TICKERS

    # ------------------------------------------------------------------
    # Filter implementations
    # ------------------------------------------------------------------
    @staticmethod
    def _rsi_oversold(
        ticker: str, df: pd.DataFrame, rsi_threshold: float = 30.0, **_: Any
    ) -> Optional[dict[str, Any]]:
        rsi = BaseStrategy._rsi(df["Close"], 14)
        current_rsi = float(rsi.iloc[-1])
        if current_rsi < rsi_threshold:
            return {
                "ticker": ticker,
                "signal": "RSI Oversold",
                "value": round(current_rsi, 2),
                "price": round(float(df["Close"].iloc[-1]), 2),
                "change_pct": round(float(df["Close"].pct_change().iloc[-1] * 100), 2),
            }
        return None

    @staticmethod
    def _rsi_overbought(
        ticker: str, df: pd.DataFrame, rsi_threshold: float = 70.0, **_: Any
    ) -> Optional[dict[str, Any]]:
        rsi = BaseStrategy._rsi(df["Close"], 14)
        current_rsi = float(rsi.iloc[-1])
        if current_rsi > rsi_threshold:
            return {
                "ticker": ticker,
                "signal": "RSI Overbought",
                "value": round(current_rsi, 2),
                "price": round(float(df["Close"].iloc[-1]), 2),
                "change_pct": round(float(df["Close"].pct_change().iloc[-1] * 100), 2),
            }
        return None

    @staticmethod
    def _golden_cross(ticker: str, df: pd.DataFrame, **_: Any) -> Optional[dict[str, Any]]:
        sma50 = BaseStrategy._sma(df["Close"], 50)
        sma200 = BaseStrategy._sma(df["Close"], 200)
        if pd.isna(sma50.iloc[-1]) or pd.isna(sma200.iloc[-1]):
            return None
        # Current: SMA50 > SMA200, Previous: SMA50 <= SMA200
        if (sma50.iloc[-1] > sma200.iloc[-1]) and (sma50.iloc[-2] <= sma200.iloc[-2]):
            return {
                "ticker": ticker,
                "signal": "Golden Cross",
                "value": round(float(sma50.iloc[-1] - sma200.iloc[-1]), 2),
                "price": round(float(df["Close"].iloc[-1]), 2),
                "change_pct": round(float(df["Close"].pct_change().iloc[-1] * 100), 2),
            }
        return None

    @staticmethod
    def _death_cross(ticker: str, df: pd.DataFrame, **_: Any) -> Optional[dict[str, Any]]:
        sma50 = BaseStrategy._sma(df["Close"], 50)
        sma200 = BaseStrategy._sma(df["Close"], 200)
        if pd.isna(sma50.iloc[-1]) or pd.isna(sma200.iloc[-1]):
            return None
        if (sma50.iloc[-1] < sma200.iloc[-1]) and (sma50.iloc[-2] >= sma200.iloc[-2]):
            return {
                "ticker": ticker,
                "signal": "Death Cross",
                "value": round(float(sma50.iloc[-1] - sma200.iloc[-1]), 2),
                "price": round(float(df["Close"].iloc[-1]), 2),
                "change_pct": round(float(df["Close"].pct_change().iloc[-1] * 100), 2),
            }
        return None

    @staticmethod
    def _bb_squeeze(
        ticker: str, df: pd.DataFrame, squeeze_threshold: float = 0.04, **_: Any
    ) -> Optional[dict[str, Any]]:
        upper, middle, lower = BaseStrategy._bollinger(df["Close"], 20, 2.0)
        if pd.isna(upper.iloc[-1]) or pd.isna(lower.iloc[-1]) or pd.isna(middle.iloc[-1]):
            return None
        bandwidth = (float(upper.iloc[-1]) - float(lower.iloc[-1])) / float(middle.iloc[-1])
        if bandwidth < squeeze_threshold:
            return {
                "ticker": ticker,
                "signal": "BB Squeeze",
                "value": round(bandwidth, 4),
                "price": round(float(df["Close"].iloc[-1]), 2),
                "change_pct": round(float(df["Close"].pct_change().iloc[-1] * 100), 2),
            }
        return None

    @staticmethod
    def _volume_spike(
        ticker: str, df: pd.DataFrame, spike_multiplier: float = 2.0, **_: Any
    ) -> Optional[dict[str, Any]]:
        if "Volume" not in df.columns:
            return None
        avg_vol = df["Volume"].rolling(20).mean()
        if pd.isna(avg_vol.iloc[-1]) or avg_vol.iloc[-1] == 0:
            return None
        ratio = float(df["Volume"].iloc[-1]) / float(avg_vol.iloc[-1])
        if ratio >= spike_multiplier:
            return {
                "ticker": ticker,
                "signal": "Volume Spike",
                "value": round(ratio, 2),
                "price": round(float(df["Close"].iloc[-1]), 2),
                "change_pct": round(float(df["Close"].pct_change().iloc[-1] * 100), 2),
            }
        return None
