"""Multi-Indicator Confluence Strategy.

Combines RSI, MACD, SMA trend, and Bollinger Bands. Generates a BUY
signal only when a configurable *min_confluence* number of sub-signals
agree.  This mirrors the existing 5-agent orchestrator concept but
as a purely quantitative, indicator-based strategy.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .base_strategy import BaseStrategy


class MultiIndicator(BaseStrategy):
    name = "Multi-Indicator"
    description = "Buys when multiple indicators (RSI, MACD, SMA, BB) agree."

    def __init__(
        self,
        rsi_period: int = 14,
        rsi_oversold: float = 35.0,
        rsi_overbought: float = 65.0,
        sma_fast: int = 20,
        sma_slow: int = 50,
        bb_period: int = 20,
        bb_std: float = 2.0,
        min_confluence: int = 3,
    ) -> None:
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.sma_fast = sma_fast
        self.sma_slow = sma_slow
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.min_confluence = min_confluence

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["Close"]

        # Sub-indicators
        rsi = self._rsi(close, self.rsi_period)
        macd_line, signal_line, _ = self._macd(close)
        sma_fast = self._sma(close, self.sma_fast)
        sma_slow = self._sma(close, self.sma_slow)
        upper, middle, lower = self._bollinger(close, self.bb_period, self.bb_std)

        # Build sub-signal scores: +1 bullish, -1 bearish, 0 neutral
        rsi_sig = pd.Series(0, index=df.index)
        rsi_sig[rsi < self.rsi_oversold] = 1   # oversold → bullish
        rsi_sig[rsi > self.rsi_overbought] = -1  # overbought → bearish

        macd_sig = pd.Series(0, index=df.index)
        macd_sig[macd_line > signal_line] = 1
        macd_sig[macd_line < signal_line] = -1

        sma_sig = pd.Series(0, index=df.index)
        sma_sig[sma_fast > sma_slow] = 1
        sma_sig[sma_fast < sma_slow] = -1

        bb_sig = pd.Series(0, index=df.index)
        bb_sig[close < lower] = 1   # below lower band → bullish
        bb_sig[close > upper] = -1  # above upper band → bearish

        # Confluence score
        bull_count = (
            (rsi_sig == 1).astype(int)
            + (macd_sig == 1).astype(int)
            + (sma_sig == 1).astype(int)
            + (bb_sig == 1).astype(int)
        )
        bear_count = (
            (rsi_sig == -1).astype(int)
            + (macd_sig == -1).astype(int)
            + (sma_sig == -1).astype(int)
            + (bb_sig == -1).astype(int)
        )

        signals = pd.Series(0, index=df.index)
        signals[bull_count >= self.min_confluence] = 1
        signals[bear_count >= self.min_confluence] = -1

        # Only emit on transitions (avoid repeated signals)
        signals = signals.diff().fillna(0)
        signals[signals > 0] = 1
        signals[signals < 0] = -1

        return signals.astype(int)

    def get_params(self) -> dict[str, Any]:
        return {
            "rsi_period": self.rsi_period,
            "rsi_oversold": self.rsi_oversold,
            "rsi_overbought": self.rsi_overbought,
            "sma_fast": self.sma_fast,
            "sma_slow": self.sma_slow,
            "bb_period": self.bb_period,
            "bb_std": self.bb_std,
            "min_confluence": self.min_confluence,
        }
