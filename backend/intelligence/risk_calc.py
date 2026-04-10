"""Position Size Calculator — risk-based position sizing for traders.

Implements fixed-fractional position sizing: given account size, risk %,
entry price, and stop-loss, calculates exact shares to buy plus
reward-to-risk ratio and commission-adjusted breakeven.
"""

from __future__ import annotations

from typing import Any, Optional
from dataclasses import dataclass
import math


@dataclass
class PositionResult:
    """Result of a position size calculation."""

    # Core sizing
    shares: int
    risk_amount: float
    position_value: float
    position_pct_of_account: float

    # Stop/target
    stop_distance: float
    stop_distance_pct: float
    max_loss: float

    # Target (optional)
    target_profit: Optional[float]
    reward_risk_ratio: Optional[float]

    # Commission
    commission_per_side: float
    total_commission: float
    breakeven_price: float

    # Summary
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "shares": self.shares,
            "risk_amount": round(self.risk_amount, 2),
            "position_value": round(self.position_value, 2),
            "position_pct_of_account": round(self.position_pct_of_account, 2),
            "stop_distance": round(self.stop_distance, 2),
            "stop_distance_pct": round(self.stop_distance_pct, 2),
            "max_loss": round(self.max_loss, 2),
            "target_profit": round(self.target_profit, 2) if self.target_profit else None,
            "reward_risk_ratio": round(self.reward_risk_ratio, 2) if self.reward_risk_ratio else None,
            "commission_per_side": round(self.commission_per_side, 2),
            "total_commission": round(self.total_commission, 2),
            "breakeven_price": round(self.breakeven_price, 2),
            "summary": self.summary,
        }


class PositionSizer:
    """Calculate position sizes based on risk parameters."""

    # Default commission rates
    COMMISSION_RATE = 0.0003  # 0.03% — typical Indian broker (Zerodha-like)
    MIN_COMMISSION = 20.0    # ₹20 minimum

    @staticmethod
    def calculate(
        account_size: float,
        risk_pct: float,
        entry_price: float,
        stop_loss: float,
        target_price: Optional[float] = None,
        commission_rate: Optional[float] = None,
    ) -> PositionResult:
        """Calculate optimal position size.

        Parameters
        ----------
        account_size : float
            Total account value (₹ or $).
        risk_pct : float
            Risk per trade as percentage (e.g., 1.0 = 1%).
        entry_price : float
            Planned entry price.
        stop_loss : float
            Stop-loss price.
        target_price : float, optional
            Take-profit target price.
        commission_rate : float, optional
            Commission as decimal (default 0.03%).
        """
        if account_size <= 0:
            raise ValueError("Account size must be positive")
        if entry_price <= 0:
            raise ValueError("Entry price must be positive")
        if risk_pct <= 0 or risk_pct > 100:
            raise ValueError("Risk % must be between 0 and 100")

        comm_rate = commission_rate if commission_rate is not None else PositionSizer.COMMISSION_RATE

        # Risk amount
        risk_amount = account_size * (risk_pct / 100)

        # Stop distance
        stop_distance = abs(entry_price - stop_loss)
        if stop_distance == 0:
            raise ValueError("Stop-loss cannot equal entry price")

        stop_distance_pct = (stop_distance / entry_price) * 100

        # Position sizing: shares = risk_amount / stop_distance
        raw_shares = risk_amount / stop_distance
        shares = max(1, math.floor(raw_shares))

        # Position value
        position_value = shares * entry_price
        position_pct = (position_value / account_size) * 100

        # Actual max loss with this number of shares
        max_loss = shares * stop_distance

        # Commission
        commission_per_side = max(position_value * comm_rate, PositionSizer.MIN_COMMISSION)
        total_commission = commission_per_side * 2  # Entry + exit

        # Breakeven after commission
        breakeven_price = entry_price + (total_commission / shares) if stop_loss < entry_price else entry_price - (total_commission / shares)

        # Target / reward-risk
        target_profit = None
        reward_risk_ratio = None
        if target_price is not None:
            target_distance = abs(target_price - entry_price)
            target_profit = (shares * target_distance) - total_commission
            if stop_distance > 0:
                reward_risk_ratio = target_distance / stop_distance

        # Direction
        direction = "LONG" if stop_loss < entry_price else "SHORT"

        summary = (
            f"{direction} {shares} shares at {entry_price:.2f}. "
            f"Risking {risk_pct:.1f}% (${risk_amount:.0f}) with stop at {stop_loss:.2f} "
            f"({stop_distance_pct:.1f}% away). "
            f"Position is {position_pct:.1f}% of account."
        )
        if reward_risk_ratio:
            summary += f" R:R = {reward_risk_ratio:.1f}:1."

        return PositionResult(
            shares=shares,
            risk_amount=risk_amount,
            position_value=position_value,
            position_pct_of_account=position_pct,
            stop_distance=stop_distance,
            stop_distance_pct=stop_distance_pct,
            max_loss=max_loss,
            target_profit=target_profit,
            reward_risk_ratio=reward_risk_ratio,
            commission_per_side=commission_per_side,
            total_commission=total_commission,
            breakeven_price=breakeven_price,
            summary=summary,
        )


    @staticmethod
    def multi_risk(
        account_size: float,
        entry_price: float,
        stop_loss: float,
        target_price: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Calculate position sizes for multiple risk levels (0.5%, 1%, 2%, 3%, 5%).

        Useful for showing a comparison table in the UI.
        """
        levels = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
        results = []
        for pct in levels:
            try:
                r = PositionSizer.calculate(account_size, pct, entry_price, stop_loss, target_price)
                d = r.to_dict()
                d["risk_pct"] = pct
                results.append(d)
            except Exception:
                continue
        return results
