"""MACD Momentum Strategy.

Buys when MACD line crosses above the signal line (bullish momentum).
Sells when MACD line crosses below the signal line (bearish momentum).
Optional histogram filter: only trade when histogram magnitude exceeds a threshold.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .base_strategy import BaseStrategy


class MACDMomentum(BaseStrategy):
    name = "MACD Momentum"
    description = "Buy on bullish MACD crossover, sell on bearish crossover."

    def __init__(
        self,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        histogram_threshold: float = 0.0,
    ) -> None:
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.histogram_threshold = histogram_threshold

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["Close"]
        macd_line, signal_line, histogram = self._macd(
            close, self.fast, self.slow, self.signal
        )

        signals = pd.Series(0, index=df.index)
        prev_macd = macd_line.shift(1)
        prev_signal = signal_line.shift(1)

        bullish = (macd_line > signal_line) & (prev_macd <= prev_signal)
        bearish = (macd_line < signal_line) & (prev_macd >= prev_signal)

        # Apply histogram threshold filter
        if self.histogram_threshold > 0:
            bullish = bullish & (histogram.abs() >= self.histogram_threshold)
            bearish = bearish & (histogram.abs() >= self.histogram_threshold)

        signals[bullish] = 1
        signals[bearish] = -1

        return signals

    def get_params(self) -> dict[str, Any]:
        return {
            "fast": self.fast,
            "slow": self.slow,
            "signal": self.signal,
            "histogram_threshold": self.histogram_threshold,
        }
