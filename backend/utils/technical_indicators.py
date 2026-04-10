"""Pure-math technical indicator calculations using pandas/numpy.

No external API or paid library needed. All computations run on OHLCV
price history fetched by yfinance.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class TechnicalIndicators:
    """Compute common technical indicators from OHLCV DataFrame."""

    @staticmethod
    def compute_all(df: pd.DataFrame) -> dict[str, Any]:
        """Compute every indicator and return a single dict for serialisation."""
        if df is None or df.empty or "Close" not in df.columns:
            return {"error": "Insufficient price data for indicator computation."}

        close = df["Close"].astype(float)
        high = df["High"].astype(float) if "High" in df.columns else close
        low = df["Low"].astype(float) if "Low" in df.columns else close
        volume = df["Volume"].astype(float) if "Volume" in df.columns else pd.Series(dtype=float)

        result: dict[str, Any] = {}

        # --- Trend Indicators ---
        result["sma_20"] = TechnicalIndicators._sma(close, 20)
        result["sma_50"] = TechnicalIndicators._sma(close, 50)
        result["sma_200"] = TechnicalIndicators._sma(close, 200)
        result["ema_20"] = TechnicalIndicators._ema(close, 20)
        result["ema_50"] = TechnicalIndicators._ema(close, 50)
        result["ema_200"] = TechnicalIndicators._ema(close, 200)

        # --- Momentum Indicators ---
        result["rsi_14"] = TechnicalIndicators._rsi(close, 14)
        macd_line, signal_line, histogram = TechnicalIndicators._macd(close)
        result["macd_line"] = macd_line
        result["macd_signal"] = signal_line
        result["macd_histogram"] = histogram

        # --- Volatility Indicators ---
        bb_upper, bb_middle, bb_lower = TechnicalIndicators._bollinger_bands(close, 20, 2.0)
        result["bb_upper"] = bb_upper
        result["bb_middle"] = bb_middle
        result["bb_lower"] = bb_lower
        result["atr_14"] = TechnicalIndicators._atr(high, low, close, 14)

        # --- Support / Resistance ---
        result["support_resistance"] = TechnicalIndicators._support_resistance(high, low, close)

        # --- Signal Summary ---
        result["signals"] = TechnicalIndicators._generate_signals(result, close)

        # --- Current Snapshot (latest values) ---
        result["snapshot"] = TechnicalIndicators._snapshot(result, close)

        return result

    # ------------------------------------------------------------------
    # Moving Averages
    # ------------------------------------------------------------------
    @staticmethod
    def _sma(series: pd.Series, period: int) -> list[float | None]:
        sma = series.rolling(window=period, min_periods=period).mean()
        return [round(v, 4) if pd.notna(v) else None for v in sma]

    @staticmethod
    def _ema(series: pd.Series, period: int) -> list[float | None]:
        ema = series.ewm(span=period, adjust=False, min_periods=period).mean()
        return [round(v, 4) if pd.notna(v) else None for v in ema]

    # ------------------------------------------------------------------
    # RSI (Wilder's smoothing)
    # ------------------------------------------------------------------
    @staticmethod
    def _rsi(series: pd.Series, period: int = 14) -> list[float | None]:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return [round(v, 2) if pd.notna(v) else None for v in rsi]

    # ------------------------------------------------------------------
    # MACD (12, 26, 9)
    # ------------------------------------------------------------------
    @staticmethod
    def _macd(
        series: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal_period: int = 9,
    ) -> tuple[list[float | None], list[float | None], list[float | None]]:
        ema_fast = series.ewm(span=fast, adjust=False, min_periods=fast).mean()
        ema_slow = series.ewm(span=slow, adjust=False, min_periods=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False, min_periods=signal_period).mean()
        histogram = macd_line - signal_line

        def _to_list(s: pd.Series) -> list[float | None]:
            return [round(v, 4) if pd.notna(v) else None for v in s]

        return _to_list(macd_line), _to_list(signal_line), _to_list(histogram)

    # ------------------------------------------------------------------
    # Bollinger Bands
    # ------------------------------------------------------------------
    @staticmethod
    def _bollinger_bands(
        series: pd.Series,
        period: int = 20,
        num_std: float = 2.0,
    ) -> tuple[list[float | None], list[float | None], list[float | None]]:
        middle = series.rolling(window=period, min_periods=period).mean()
        std = series.rolling(window=period, min_periods=period).std()
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)

        def _to_list(s: pd.Series) -> list[float | None]:
            return [round(v, 4) if pd.notna(v) else None for v in s]

        return _to_list(upper), _to_list(middle), _to_list(lower)

    # ------------------------------------------------------------------
    # ATR (Average True Range)
    # ------------------------------------------------------------------
    @staticmethod
    def _atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> list[float | None]:
        prev_close = close.shift(1)
        tr = pd.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
            axis=1,
        ).max(axis=1)
        atr = tr.rolling(window=period, min_periods=period).mean()
        return [round(v, 4) if pd.notna(v) else None for v in atr]

    # ------------------------------------------------------------------
    # Support & Resistance (Pivot Points method)
    # ------------------------------------------------------------------
    @staticmethod
    def _support_resistance(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
    ) -> dict[str, float | None]:
        if len(close) < 5:
            return {"pivot": None, "r1": None, "r2": None, "s1": None, "s2": None}

        recent_high = float(high.iloc[-20:].max()) if len(high) >= 20 else float(high.max())
        recent_low = float(low.iloc[-20:].min()) if len(low) >= 20 else float(low.min())
        recent_close = float(close.iloc[-1])

        pivot = (recent_high + recent_low + recent_close) / 3.0
        r1 = (2.0 * pivot) - recent_low
        s1 = (2.0 * pivot) - recent_high
        r2 = pivot + (recent_high - recent_low)
        s2 = pivot - (recent_high - recent_low)

        return {
            "pivot": round(pivot, 2),
            "r1": round(r1, 2),
            "r2": round(r2, 2),
            "s1": round(s1, 2),
            "s2": round(s2, 2),
        }

    # ------------------------------------------------------------------
    # Signal Generation
    # ------------------------------------------------------------------
    @staticmethod
    def _generate_signals(indicators: dict[str, Any], close: pd.Series) -> list[dict[str, str]]:
        signals: list[dict[str, str]] = []
        current_price = float(close.iloc[-1])

        # RSI signal
        rsi_values = indicators.get("rsi_14", [])
        latest_rsi = next((v for v in reversed(rsi_values) if v is not None), None)
        if latest_rsi is not None:
            if latest_rsi < 30:
                signals.append({"indicator": "RSI", "signal": "OVERSOLD", "direction": "bullish", "value": str(latest_rsi)})
            elif latest_rsi > 70:
                signals.append({"indicator": "RSI", "signal": "OVERBOUGHT", "direction": "bearish", "value": str(latest_rsi)})
            else:
                signals.append({"indicator": "RSI", "signal": "NEUTRAL", "direction": "neutral", "value": str(latest_rsi)})

        # MACD signal
        macd_hist = indicators.get("macd_histogram", [])
        if len(macd_hist) >= 2:
            curr_h = macd_hist[-1]
            prev_h = macd_hist[-2]
            if curr_h is not None and prev_h is not None:
                if prev_h <= 0 < curr_h:
                    signals.append({"indicator": "MACD", "signal": "BULLISH CROSS", "direction": "bullish", "value": str(round(curr_h, 4))})
                elif prev_h >= 0 > curr_h:
                    signals.append({"indicator": "MACD", "signal": "BEARISH CROSS", "direction": "bearish", "value": str(round(curr_h, 4))})
                elif curr_h > 0:
                    signals.append({"indicator": "MACD", "signal": "BULLISH", "direction": "bullish", "value": str(round(curr_h, 4))})
                else:
                    signals.append({"indicator": "MACD", "signal": "BEARISH", "direction": "bearish", "value": str(round(curr_h, 4))})

        # Bollinger Band signal
        bb_upper = indicators.get("bb_upper", [])
        bb_lower = indicators.get("bb_lower", [])
        if bb_upper and bb_lower:
            latest_upper = next((v for v in reversed(bb_upper) if v is not None), None)
            latest_lower = next((v for v in reversed(bb_lower) if v is not None), None)
            if latest_upper is not None and latest_lower is not None:
                if current_price >= latest_upper:
                    signals.append({"indicator": "Bollinger", "signal": "ABOVE UPPER BAND", "direction": "bearish", "value": f"{current_price:.2f} >= {latest_upper:.2f}"})
                elif current_price <= latest_lower:
                    signals.append({"indicator": "Bollinger", "signal": "BELOW LOWER BAND", "direction": "bullish", "value": f"{current_price:.2f} <= {latest_lower:.2f}"})
                else:
                    signals.append({"indicator": "Bollinger", "signal": "WITHIN BANDS", "direction": "neutral", "value": f"{latest_lower:.2f} < {current_price:.2f} < {latest_upper:.2f}"})

        # SMA Cross signals (Golden/Death Cross)
        sma_50 = indicators.get("sma_50", [])
        sma_200 = indicators.get("sma_200", [])
        if sma_50 and sma_200:
            latest_50 = next((v for v in reversed(sma_50) if v is not None), None)
            latest_200 = next((v for v in reversed(sma_200) if v is not None), None)
            if latest_50 is not None and latest_200 is not None:
                if latest_50 > latest_200:
                    signals.append({"indicator": "SMA Cross", "signal": "GOLDEN CROSS (50>200)", "direction": "bullish", "value": f"50SMA={latest_50:.2f}, 200SMA={latest_200:.2f}"})
                else:
                    signals.append({"indicator": "SMA Cross", "signal": "DEATH CROSS (50<200)", "direction": "bearish", "value": f"50SMA={latest_50:.2f}, 200SMA={latest_200:.2f}"})

        # Price vs SMA 200 (trend)
        if sma_200:
            latest_200 = next((v for v in reversed(sma_200) if v is not None), None)
            if latest_200 is not None:
                if current_price > latest_200:
                    signals.append({"indicator": "Trend", "signal": "ABOVE 200 SMA (UPTREND)", "direction": "bullish", "value": f"{current_price:.2f} > {latest_200:.2f}"})
                else:
                    signals.append({"indicator": "Trend", "signal": "BELOW 200 SMA (DOWNTREND)", "direction": "bearish", "value": f"{current_price:.2f} < {latest_200:.2f}"})

        return signals

    # ------------------------------------------------------------------
    # Current Snapshot (latest indicator values)
    # ------------------------------------------------------------------
    @staticmethod
    def _snapshot(indicators: dict[str, Any], close: pd.Series) -> dict[str, Any]:
        def _latest(values: list[float | None]) -> float | None:
            return next((v for v in reversed(values) if v is not None), None)

        current_price = float(close.iloc[-1])

        return {
            "current_price": round(current_price, 2),
            "rsi_14": _latest(indicators.get("rsi_14", [])),
            "macd_line": _latest(indicators.get("macd_line", [])),
            "macd_signal": _latest(indicators.get("macd_signal", [])),
            "macd_histogram": _latest(indicators.get("macd_histogram", [])),
            "sma_20": _latest(indicators.get("sma_20", [])),
            "sma_50": _latest(indicators.get("sma_50", [])),
            "sma_200": _latest(indicators.get("sma_200", [])),
            "ema_20": _latest(indicators.get("ema_20", [])),
            "bb_upper": _latest(indicators.get("bb_upper", [])),
            "bb_middle": _latest(indicators.get("bb_middle", [])),
            "bb_lower": _latest(indicators.get("bb_lower", [])),
            "atr_14": _latest(indicators.get("atr_14", [])),
            "support_resistance": indicators.get("support_resistance", {}),
            "bullish_signals": sum(1 for s in indicators.get("signals", []) if s.get("direction") == "bullish"),
            "bearish_signals": sum(1 for s in indicators.get("signals", []) if s.get("direction") == "bearish"),
            "neutral_signals": sum(1 for s in indicators.get("signals", []) if s.get("direction") == "neutral"),
        }
