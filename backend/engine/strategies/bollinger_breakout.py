"""Bollinger Band Breakout Strategy.

Buys when price closes below the lower band (mean-reversion entry).
Sells when price closes above the upper band (mean-reversion exit).
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .base_strategy import BaseStrategy


class BollingerBreakout(BaseStrategy):
    name = "Bollinger Breakout"
    description = "Buy at lower band touch, sell at upper band touch (mean reversion)."

    def __init__(self, period: int = 20, std_dev: float = 2.0) -> None:
        self.period = period
        self.std_dev = std_dev

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["Close"]
        upper, middle, lower = self._bollinger(close, self.period, self.std_dev)

        signals = pd.Series(0, index=df.index)
        prev_close = close.shift(1)

        # Buy: price crosses below lower band then reverts above
        buy = (close > lower) & (prev_close <= lower)
        # Sell: price crosses above upper band then reverts below
        sell = (close < upper) & (prev_close >= upper)

        signals[buy] = 1
        signals[sell] = -1

        return signals

    def get_params(self) -> dict[str, Any]:
        return {"period": self.period, "std_dev": self.std_dev}
