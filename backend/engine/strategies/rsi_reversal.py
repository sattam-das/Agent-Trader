"""RSI Reversal Strategy — Mean-reversion using RSI.

Buys when RSI drops below the oversold level and then crosses back above.
Sells when RSI rises above the overbought level and then crosses back below.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .base_strategy import BaseStrategy


class RSIReversal(BaseStrategy):
    name = "RSI Reversal"
    description = "Buy at RSI oversold reversal, sell at RSI overbought reversal."

    def __init__(
        self,
        rsi_period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
    ) -> None:
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["Close"]
        rsi = self._rsi(close, self.rsi_period)

        signals = pd.Series(0, index=df.index)
        prev_rsi = rsi.shift(1)

        # Buy: RSI crosses above oversold from below
        buy = (rsi > self.oversold) & (prev_rsi <= self.oversold)
        # Sell: RSI crosses below overbought from above
        sell = (rsi < self.overbought) & (prev_rsi >= self.overbought)

        signals[buy] = 1
        signals[sell] = -1

        return signals

    def get_params(self) -> dict[str, Any]:
        return {
            "rsi_period": self.rsi_period,
            "oversold": self.oversold,
            "overbought": self.overbought,
        }
