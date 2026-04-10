"""Dynamic Strategy — executes strategies defined by a JSON specification.

This is the core of the Natural Language Backtesting feature. It takes
a structured spec (produced by NLParser) and generates trading signals
using a safe, predefined set of indicator functions. No eval() or exec().
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from .base_strategy import BaseStrategy


class DynamicStrategy(BaseStrategy):
    """Execute a strategy defined by a JSON specification.

    The spec format:
    {
        "strategy_name": "RSI Reversal",
        "buy_conditions": [{"left": "RSI(14)", "operator": "<", "right": "30"}],
        "buy_logic": "AND",
        "sell_conditions": [{"left": "RSI(14)", "operator": ">", "right": "70"}],
        "sell_logic": "AND",
    }
    """

    def __init__(self, spec: dict[str, Any]) -> None:
        self.spec = spec
        self.name = spec.get("strategy_name", "Custom NL Strategy")
        self.description = spec.get("description", "")
        self._buy_conditions = spec.get("buy_conditions", [])
        self._sell_conditions = spec.get("sell_conditions", [])
        self._buy_logic = spec.get("buy_logic", "AND").upper()
        self._sell_logic = spec.get("sell_logic", "AND").upper()

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate +1 (buy), -1 (sell), 0 (hold) signals from the spec."""
        signals = pd.Series(0, index=df.index)

        if not self._buy_conditions or not self._sell_conditions:
            return signals

        # Evaluate buy conditions
        buy_mask = self._evaluate_conditions(df, self._buy_conditions, self._buy_logic)

        # Evaluate sell conditions
        sell_mask = self._evaluate_conditions(df, self._sell_conditions, self._sell_logic)

        signals[buy_mask] = 1
        signals[sell_mask] = -1

        # Prevent simultaneous buy+sell — sell takes priority
        conflict = buy_mask & sell_mask
        signals[conflict] = 0

        return signals

    def get_params(self) -> dict[str, Any]:
        return self.spec.get("parameters_used", {})

    # ------------------------------------------------------------------
    # Condition Evaluation
    # ------------------------------------------------------------------
    def _evaluate_conditions(
        self, df: pd.DataFrame, conditions: list[dict], logic: str
    ) -> pd.Series:
        """Evaluate a list of conditions and combine with AND/OR logic."""
        if not conditions:
            return pd.Series(False, index=df.index)

        masks = []
        for cond in conditions:
            try:
                mask = self._evaluate_single(df, cond)
                masks.append(mask)
            except Exception:
                # If one condition fails, skip it (graceful degradation)
                continue

        if not masks:
            return pd.Series(False, index=df.index)

        if logic == "OR":
            result = masks[0]
            for m in masks[1:]:
                result = result | m
        else:  # AND
            result = masks[0]
            for m in masks[1:]:
                result = result & m

        return result.fillna(False)

    def _evaluate_single(self, df: pd.DataFrame, condition: dict) -> pd.Series:
        """Evaluate a single condition like {"left": "RSI(14)", "operator": "<", "right": "30"}."""
        left_str = str(condition.get("left", ""))
        operator = str(condition.get("operator", ">"))
        # LLM may return right as int/float (e.g. 30) instead of string "30"
        right_raw = condition.get("right", "0")
        right_str = str(right_raw)

        left = self._resolve_value(df, left_str)
        right = self._resolve_value(df, right_str)

        return self._apply_operator(left, right, operator, df.index)

    # ------------------------------------------------------------------
    # Indicator Resolution (safe — no eval/exec)
    # ------------------------------------------------------------------
    def _resolve_value(self, df: pd.DataFrame, token: str) -> pd.Series | float:
        """Resolve a token like 'RSI(14)' or '30' into a Series or scalar."""
        token = token.strip()

        # Try numeric constant first
        try:
            return float(token)
        except ValueError:
            pass

        # Price columns
        upper_token = token.upper()
        if upper_token == "PRICE" or upper_token == "CLOSE":
            return df["Close"]
        if upper_token == "VOLUME":
            return df["Volume"]
        if upper_token == "HIGH":
            return df["High"]
        if upper_token == "LOW":
            return df["Low"]
        if upper_token == "OPEN":
            return df["Open"]

        # Parse function-style tokens: INDICATOR(param1, param2, ...)
        match = re.match(r"^([A-Z_]+)\(([^)]+)\)$", upper_token)
        if not match:
            # Try without parentheses for simple names
            return self._resolve_simple(df, upper_token)

        func_name = match.group(1)
        params = [p.strip() for p in match.group(2).split(",")]

        return self._compute_indicator(df, func_name, params)

    def _resolve_simple(self, df: pd.DataFrame, name: str) -> pd.Series | float:
        """Handle simple names without parameters."""
        close = df["Close"]
        if name == "RSI":
            return self._rsi(close, 14)
        if name == "SMA":
            return self._sma(close, 20)
        if name == "EMA":
            return self._ema(close, 12)
        if name in ("MACD", "MACD_LINE"):
            line, _, _ = self._macd(close)
            return line
        if name == "MACD_SIGNAL":
            _, sig, _ = self._macd(close)
            return sig
        if name in ("MACD_HISTOGRAM", "MACD_HIST"):
            _, _, hist = self._macd(close)
            return hist
        if name in ("BB_UPPER", "BOLLINGER_UPPER"):
            upper, _, _ = self._bollinger(close)
            return upper
        if name in ("BB_LOWER", "BOLLINGER_LOWER"):
            _, _, lower = self._bollinger(close)
            return lower
        if name in ("BB_MIDDLE", "BOLLINGER_MIDDLE"):
            _, middle, _ = self._bollinger(close)
            return middle
        if name == "ATR":
            return self._compute_atr(df, 14)

        # Fallback: treat as unknown, return close price
        return close

    def _compute_indicator(
        self, df: pd.DataFrame, func: str, params: list[str]
    ) -> pd.Series:
        """Compute a specific indicator with given parameters."""
        close = df["Close"]

        # Parse numeric params safely
        def _int(idx: int, default: int) -> int:
            try:
                return int(float(params[idx])) if idx < len(params) else default
            except (ValueError, IndexError):
                return default

        def _float(idx: int, default: float) -> float:
            try:
                return float(params[idx]) if idx < len(params) else default
            except (ValueError, IndexError):
                return default

        # RSI
        if func == "RSI":
            return self._rsi(close, _int(0, 14))

        # SMA
        if func == "SMA":
            return self._sma(close, _int(0, 20))

        # EMA
        if func == "EMA":
            return self._ema(close, _int(0, 12))

        # MACD variants
        if func in ("MACD_LINE", "MACD"):
            line, _, _ = self._macd(close, _int(0, 12), _int(1, 26), _int(2, 9))
            return line
        if func == "MACD_SIGNAL":
            _, sig, _ = self._macd(close, _int(0, 12), _int(1, 26), _int(2, 9))
            return sig
        if func in ("MACD_HISTOGRAM", "MACD_HIST"):
            _, _, hist = self._macd(close, _int(0, 12), _int(1, 26), _int(2, 9))
            return hist

        # Bollinger Bands
        if func in ("BB_UPPER", "BOLLINGER_UPPER"):
            upper, _, _ = self._bollinger(close, _int(0, 20), _float(1, 2.0))
            return upper
        if func in ("BB_LOWER", "BOLLINGER_LOWER"):
            _, _, lower = self._bollinger(close, _int(0, 20), _float(1, 2.0))
            return lower
        if func in ("BB_MIDDLE", "BOLLINGER_MIDDLE"):
            _, middle, _ = self._bollinger(close, _int(0, 20), _float(1, 2.0))
            return middle

        # ATR
        if func == "ATR":
            return self._compute_atr(df, _int(0, 14))

        # VOLUME
        if func == "VOLUME":
            return df["Volume"]

        # SMA of volume
        if func == "VOLUME_SMA":
            return self._sma(df["Volume"], _int(0, 20))

        # Fallback
        return close

    # ------------------------------------------------------------------
    # ATR (not in base class, so we add it here)
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Compute Average True Range."""
        high = df["High"]
        low = df["Low"]
        close = df["Close"]

        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period, min_periods=period).mean()

    # ------------------------------------------------------------------
    # Operator Application
    # ------------------------------------------------------------------
    @staticmethod
    def _apply_operator(
        left: pd.Series | float,
        right: pd.Series | float,
        operator: str,
        index: pd.Index | None = None,
    ) -> pd.Series:
        """Apply a comparison operator between two values."""
        op = operator.strip().lower()

        if op == ">":
            return left > right
        elif op == "<":
            return left < right
        elif op == ">=":
            return left >= right
        elif op == "<=":
            return left <= right
        elif op in ("crosses_above", "crossover", "cross_above"):
            # Was below or equal, now above
            if isinstance(left, (int, float)):
                return pd.Series(False, index=index)
            prev_left = left.shift(1) if isinstance(left, pd.Series) else left
            prev_right = right.shift(1) if isinstance(right, pd.Series) else right
            result = (left > right) & (prev_left <= prev_right)
            return result.fillna(False)
        elif op in ("crosses_below", "crossunder", "cross_below"):
            # Was above or equal, now below
            if isinstance(left, (int, float)):
                return pd.Series(False, index=index)
            prev_left = left.shift(1) if isinstance(left, pd.Series) else left
            prev_right = right.shift(1) if isinstance(right, pd.Series) else right
            result = (left < right) & (prev_left >= prev_right)
            return result.fillna(False)
        else:
            # Default to >
            return left > right
