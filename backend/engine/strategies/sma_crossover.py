"""SMA Crossover Strategy — Golden Cross / Death Cross.

Generates a BUY signal when the fast SMA crosses above the slow SMA,
and a SELL signal when it crosses below.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .base_strategy import BaseStrategy


class SMACrossover(BaseStrategy):
    name = "SMA Crossover"
    description = "Buy on Golden Cross (fast SMA > slow SMA), sell on Death Cross."

    def __init__(self, fast_period: int = 50, slow_period: int = 200) -> None:
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["Close"]
        fast = self._sma(close, self.fast_period)
        slow = self._sma(close, self.slow_period)

        signals = pd.Series(0, index=df.index)

        # Cross detection: fast crosses above slow → +1, below → -1
        prev_fast = fast.shift(1)
        prev_slow = slow.shift(1)

        golden_cross = (fast > slow) & (prev_fast <= prev_slow)
        death_cross = (fast < slow) & (prev_fast >= prev_slow)

        signals[golden_cross] = 1
        signals[death_cross] = -1

        return signals

    def get_params(self) -> dict[str, Any]:
        return {"fast_period": self.fast_period, "slow_period": self.slow_period}
