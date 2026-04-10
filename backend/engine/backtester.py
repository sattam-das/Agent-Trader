"""Vectorised Backtesting Engine.

Takes a strategy + OHLCV DataFrame, simulates trades with realistic
slippage and commissions, and returns comprehensive performance metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd

from backend.engine.strategies.base_strategy import BaseStrategy


@dataclass
class Trade:
    """A single completed trade."""

    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    shares: int
    pnl: float
    return_pct: float
    holding_days: int


@dataclass
class BacktestResult:
    """All outputs of a backtest run."""

    strategy_name: str
    strategy_params: dict[str, Any]
    ticker: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float

    # Performance metrics
    total_return: float
    cagr: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_return: float
    avg_holding_days: float
    best_trade: float
    worst_trade: float

    # Benchmark comparison
    buy_hold_return: float
    excess_return: float

    # Time-series data (for charting)
    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    drawdown_series: list[dict[str, Any]] = field(default_factory=list)
    trades: list[dict[str, Any]] = field(default_factory=list)
    monthly_returns: list[dict[str, Any]] = field(default_factory=list)
    signals: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialise for JSON API responses."""
        return {
            "strategy_name": self.strategy_name,
            "strategy_params": self.strategy_params,
            "ticker": self.ticker,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_capital": self.initial_capital,
            "final_capital": round(self.final_capital, 2),
            "total_return": round(self.total_return, 4),
            "cagr": round(self.cagr, 4),
            "sharpe_ratio": round(self.sharpe_ratio, 4),
            "sortino_ratio": round(self.sortino_ratio, 4),
            "max_drawdown": round(self.max_drawdown, 4),
            "calmar_ratio": round(self.calmar_ratio, 4),
            "win_rate": round(self.win_rate, 4),
            "profit_factor": round(self.profit_factor, 4),
            "total_trades": self.total_trades,
            "avg_trade_return": round(self.avg_trade_return, 4),
            "avg_holding_days": round(self.avg_holding_days, 1),
            "best_trade": round(self.best_trade, 4),
            "worst_trade": round(self.worst_trade, 4),
            "buy_hold_return": round(self.buy_hold_return, 4),
            "excess_return": round(self.excess_return, 4),
            "equity_curve": self.equity_curve,
            "drawdown_series": self.drawdown_series,
            "trades": self.trades,
            "monthly_returns": self.monthly_returns,
            "signals": self.signals,
        }


class Backtester:
    """Run a strategy backtest on historical OHLCV data.

    Parameters
    ----------
    initial_capital : float
        Starting portfolio value (default $100,000).
    commission_pct : float
        Commission per trade as a fraction (default 0.001 = 0.1%).
    slippage_pct : float
        Simulated slippage per trade as a fraction (default 0.0005 = 0.05%).
    position_size_pct : float
        Fraction of available capital to allocate per trade (default 0.95 = 95%).
    """

    def __init__(
        self,
        initial_capital: float = 100_000.0,
        commission_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        position_size_pct: float = 0.95,
    ) -> None:
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        self.position_size_pct = position_size_pct

    # ------------------------------------------------------------------
    def run(
        self,
        strategy: BaseStrategy,
        df: pd.DataFrame,
        ticker: str = "UNKNOWN",
    ) -> BacktestResult:
        """Execute backtest and return a ``BacktestResult``."""

        if df.empty or len(df) < 30:
            return self._empty_result(strategy, ticker)

        # Ensure a clean copy with proper column names
        df = df.copy()
        if "Close" not in df.columns:
            for col in ["close", "Adj Close"]:
                if col in df.columns:
                    df.rename(columns={col: "Close"}, inplace=True)
                    break

        required = {"Close"}
        if not required.issubset(df.columns):
            return self._empty_result(strategy, ticker)

        # Generate signals
        raw_signals = strategy.generate_signals(df)

        # Simulate trades
        trades, equity, signals_log = self._simulate(df, raw_signals)

        # Compute metrics
        return self._build_result(strategy, df, ticker, trades, equity, signals_log)

    # ------------------------------------------------------------------
    def _simulate(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
    ) -> tuple[list[Trade], pd.Series, list[dict[str, Any]]]:
        """Walk-forward trade simulation."""

        cash = self.initial_capital
        shares = 0
        entry_price = 0.0
        entry_idx = 0

        trades: list[Trade] = []
        equity_values: list[float] = []
        signals_log: list[dict[str, Any]] = []

        closes = df["Close"].values
        dates = df.index if isinstance(df.index, pd.DatetimeIndex) else range(len(df))

        for i in range(len(df)):
            price = float(closes[i])
            sig = int(signals.iloc[i]) if i < len(signals) else 0
            date_str = str(dates[i])[:10] if hasattr(dates[i], "strftime") else str(i)

            if sig == 1 and shares == 0:
                # BUY
                buy_price = price * (1 + self.slippage_pct)
                affordable = int((cash * self.position_size_pct) / buy_price)
                if affordable > 0:
                    cost = affordable * buy_price
                    commission = cost * self.commission_pct
                    cash -= cost + commission
                    shares = affordable
                    entry_price = buy_price
                    entry_idx = i
                    signals_log.append(
                        {"date": date_str, "type": "BUY", "price": round(buy_price, 2), "shares": shares}
                    )

            elif sig == -1 and shares > 0:
                # SELL
                sell_price = price * (1 - self.slippage_pct)
                revenue = shares * sell_price
                commission = revenue * self.commission_pct
                cash += revenue - commission
                pnl = (sell_price - entry_price) * shares - commission
                ret = (sell_price - entry_price) / entry_price

                holding = i - entry_idx
                trade_date = str(dates[entry_idx])[:10] if hasattr(dates[entry_idx], "strftime") else str(entry_idx)

                trades.append(
                    Trade(
                        entry_date=trade_date,
                        exit_date=date_str,
                        entry_price=round(entry_price, 2),
                        exit_price=round(sell_price, 2),
                        shares=shares,
                        pnl=round(pnl, 2),
                        return_pct=round(ret, 4),
                        holding_days=holding,
                    )
                )
                signals_log.append(
                    {"date": date_str, "type": "SELL", "price": round(sell_price, 2), "shares": shares}
                )
                shares = 0

            # Track equity
            portfolio_value = cash + shares * price
            equity_values.append(portfolio_value)

        equity = pd.Series(equity_values, index=df.index)
        return trades, equity, signals_log

    # ------------------------------------------------------------------
    def _build_result(
        self,
        strategy: BaseStrategy,
        df: pd.DataFrame,
        ticker: str,
        trades: list[Trade],
        equity: pd.Series,
        signals_log: list[dict[str, Any]],
    ) -> BacktestResult:
        """Compute all metrics from trade list and equity curve."""

        dates = df.index
        start_date = str(dates[0])[:10]
        end_date = str(dates[-1])[:10]
        final_capital = float(equity.iloc[-1])

        # Total return
        total_return = (final_capital - self.initial_capital) / self.initial_capital

        # Buy & hold benchmark
        buy_hold_return = (float(df["Close"].iloc[-1]) / float(df["Close"].iloc[0])) - 1.0

        # CAGR
        n_days = max((dates[-1] - dates[0]).days, 1) if isinstance(dates, pd.DatetimeIndex) else len(df)
        years = max(n_days / 365.25, 0.01)
        cagr = (final_capital / self.initial_capital) ** (1.0 / years) - 1.0

        # Daily returns for Sharpe/Sortino
        daily_returns = equity.pct_change().dropna()
        trading_days = 252

        # Sharpe Ratio (annualised, risk-free = 0)
        if len(daily_returns) > 1 and daily_returns.std() > 0:
            sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(trading_days)
        else:
            sharpe = 0.0

        # Sortino Ratio (only downside deviation)
        downside = daily_returns[daily_returns < 0]
        if len(downside) > 1 and downside.std() > 0:
            sortino = (daily_returns.mean() / downside.std()) * np.sqrt(trading_days)
        else:
            sortino = 0.0

        # Max Drawdown
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        max_drawdown = float(drawdown.min()) if len(drawdown) > 0 else 0.0

        # Calmar Ratio
        calmar = abs(cagr / max_drawdown) if max_drawdown != 0 else 0.0

        # Trade statistics
        total_trades = len(trades)
        if total_trades > 0:
            returns = [t.return_pct for t in trades]
            winners = [r for r in returns if r > 0]
            losers = [r for r in returns if r <= 0]
            win_rate = len(winners) / total_trades
            gross_profit = sum(r for r in returns if r > 0) if winners else 0.0
            gross_loss = abs(sum(r for r in returns if r < 0)) if losers else 0.001
            profit_factor = gross_profit / gross_loss
            avg_trade_return = sum(returns) / total_trades
            avg_holding = sum(t.holding_days for t in trades) / total_trades
            best_trade = max(returns)
            worst_trade = min(returns)
        else:
            win_rate = profit_factor = avg_trade_return = avg_holding = 0.0
            best_trade = worst_trade = 0.0

        # Equity curve for charting
        equity_curve = []
        for i, (idx, val) in enumerate(equity.items()):
            date_str = str(idx)[:10] if hasattr(idx, "strftime") else str(i)
            equity_curve.append({"date": date_str, "equity": round(float(val), 2)})

        # Drawdown series
        drawdown_series = []
        for i, (idx, val) in enumerate(drawdown.items()):
            date_str = str(idx)[:10] if hasattr(idx, "strftime") else str(i)
            drawdown_series.append({"date": date_str, "drawdown": round(float(val), 4)})

        # Monthly returns
        monthly_returns = self._compute_monthly_returns(equity)

        # Trade list for display
        trade_dicts = [
            {
                "entry_date": t.entry_date,
                "exit_date": t.exit_date,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "shares": t.shares,
                "pnl": t.pnl,
                "return_pct": t.return_pct,
                "holding_days": t.holding_days,
            }
            for t in trades
        ]

        return BacktestResult(
            strategy_name=strategy.name,
            strategy_params=strategy.get_params(),
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            cagr=cagr,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            avg_trade_return=avg_trade_return,
            avg_holding_days=avg_holding,
            best_trade=best_trade,
            worst_trade=worst_trade,
            buy_hold_return=buy_hold_return,
            excess_return=total_return - buy_hold_return,
            equity_curve=equity_curve,
            drawdown_series=drawdown_series,
            trades=trade_dicts,
            monthly_returns=monthly_returns,
            signals=signals_log,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _compute_monthly_returns(equity: pd.Series) -> list[dict[str, Any]]:
        """Aggregate equity into monthly return percentages."""
        if not isinstance(equity.index, pd.DatetimeIndex) or len(equity) < 2:
            return []

        monthly = equity.resample("ME").last().dropna()
        monthly_ret = monthly.pct_change().dropna()

        results = []
        for idx, ret in monthly_ret.items():
            results.append({
                "year": int(idx.year),
                "month": int(idx.month),
                "return": round(float(ret), 4),
            })
        return results

    # ------------------------------------------------------------------
    def _empty_result(self, strategy: BaseStrategy, ticker: str) -> BacktestResult:
        """Return a zero-valued result when data is insufficient."""
        return BacktestResult(
            strategy_name=strategy.name,
            strategy_params=strategy.get_params(),
            ticker=ticker,
            start_date="",
            end_date="",
            initial_capital=self.initial_capital,
            final_capital=self.initial_capital,
            total_return=0.0,
            cagr=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown=0.0,
            calmar_ratio=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            total_trades=0,
            avg_trade_return=0.0,
            avg_holding_days=0.0,
            best_trade=0.0,
            worst_trade=0.0,
            buy_hold_return=0.0,
            excess_return=0.0,
        )
