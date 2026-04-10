"""Monte Carlo price simulation engine.

Uses Geometric Brownian Motion (GBM) to simulate future price paths
from historical returns. No external API needed — pure numpy math.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class MonteCarloSimulator:
    """Run Monte Carlo simulations on stock price paths."""

    DEFAULT_NUM_SIMULATIONS = 10_000
    HORIZONS_DAYS = [30, 60, 90]
    TRADING_DAYS_PER_YEAR = 252

    @staticmethod
    def simulate(
        price_history: pd.Series | list[float],
        num_simulations: int = DEFAULT_NUM_SIMULATIONS,
        horizons: list[int] | None = None,
        analyst_targets: dict[str, float | None] | None = None,
    ) -> dict[str, Any]:
        """Run full simulation and return structured results.

        Args:
            price_history: Historical closing prices (at least 30 data points).
            num_simulations: Number of random paths to generate.
            horizons: List of day-counts to project (default [30, 60, 90]).
            analyst_targets: Dict with 'low', 'mean', 'high' analyst targets.

        Returns:
            Dict with simulation results, percentiles, VaR, and target probabilities.
        """
        if horizons is None:
            horizons = list(MonteCarloSimulator.HORIZONS_DAYS)

        if isinstance(price_history, list):
            price_history = pd.Series(price_history, dtype=float)

        price_history = price_history.dropna()
        if len(price_history) < 30:
            return {"error": "Need at least 30 data points for simulation."}

        current_price = float(price_history.iloc[-1])
        log_returns = np.log(price_history / price_history.shift(1)).dropna().values

        mu = float(np.mean(log_returns))
        sigma = float(np.std(log_returns))

        if sigma == 0:
            return {"error": "Zero volatility — cannot simulate."}

        max_horizon = max(horizons)
        rng = np.random.default_rng(seed=42)

        # Generate random walks: (num_simulations, max_horizon) matrix
        random_walks = rng.normal(
            loc=mu - 0.5 * sigma**2,
            scale=sigma,
            size=(num_simulations, max_horizon),
        )

        # Cumulative sum to get log-price paths, then exponentiate
        cumulative = np.cumsum(random_walks, axis=1)
        price_paths = current_price * np.exp(cumulative)

        # Build results for each horizon
        horizon_results: dict[str, Any] = {}
        for days in sorted(horizons):
            if days > max_horizon:
                continue
            final_prices = price_paths[:, days - 1]
            horizon_results[f"{days}d"] = MonteCarloSimulator._horizon_stats(
                final_prices, current_price, days
            )

        # Target probability analysis
        target_probs: dict[str, Any] = {}
        if analyst_targets:
            final_90d = price_paths[:, min(89, max_horizon - 1)]
            for label, target in analyst_targets.items():
                if target is not None and target > 0:
                    prob = float(np.mean(final_90d >= target))
                    target_probs[label] = {
                        "target_price": round(target, 2),
                        "probability": round(prob, 4),
                        "probability_pct": f"{prob * 100:.1f}%",
                    }

        # Sample paths for visualization (50 paths to avoid huge payloads)
        sample_indices = rng.choice(num_simulations, size=min(50, num_simulations), replace=False)
        sample_paths = price_paths[sample_indices, :].tolist()
        sample_paths = [
            [round(p, 2) for p in path[:max_horizon]] for path in sample_paths
        ]

        # Value at Risk (VaR) — 95% confidence
        var_results: dict[str, Any] = {}
        for days in sorted(horizons):
            if days > max_horizon:
                continue
            final_prices = price_paths[:, days - 1]
            returns = (final_prices - current_price) / current_price
            var_95 = float(np.percentile(returns, 5))
            var_99 = float(np.percentile(returns, 1))
            var_results[f"{days}d"] = {
                "var_95": round(var_95 * 100, 2),
                "var_99": round(var_99 * 100, 2),
                "var_95_dollar": round(var_95 * current_price, 2),
                "var_99_dollar": round(var_99 * current_price, 2),
            }

        return {
            "current_price": round(current_price, 2),
            "num_simulations": num_simulations,
            "historical_mu": round(mu, 6),
            "historical_sigma": round(sigma, 6),
            "annualised_volatility": round(
                sigma * np.sqrt(MonteCarloSimulator.TRADING_DAYS_PER_YEAR) * 100, 2
            ),
            "horizons": horizon_results,
            "target_probabilities": target_probs,
            "value_at_risk": var_results,
            "sample_paths": sample_paths,
            "max_horizon_days": max_horizon,
        }

    @staticmethod
    def _horizon_stats(
        final_prices: np.ndarray,
        current_price: float,
        days: int,
    ) -> dict[str, Any]:
        """Compute statistics for a single horizon."""
        returns_pct = ((final_prices - current_price) / current_price) * 100

        percentiles = [5, 10, 25, 50, 75, 90, 95]
        price_percentiles = {
            f"p{p}": round(float(np.percentile(final_prices, p)), 2)
            for p in percentiles
        }

        return {
            "days": days,
            "mean_price": round(float(np.mean(final_prices)), 2),
            "median_price": round(float(np.median(final_prices)), 2),
            "std_price": round(float(np.std(final_prices)), 2),
            "min_price": round(float(np.min(final_prices)), 2),
            "max_price": round(float(np.max(final_prices)), 2),
            "mean_return_pct": round(float(np.mean(returns_pct)), 2),
            "prob_positive": round(float(np.mean(final_prices > current_price)), 4),
            "prob_up_5pct": round(float(np.mean(final_prices > current_price * 1.05)), 4),
            "prob_up_10pct": round(float(np.mean(final_prices > current_price * 1.10)), 4),
            "prob_down_5pct": round(float(np.mean(final_prices < current_price * 0.95)), 4),
            "prob_down_10pct": round(float(np.mean(final_prices < current_price * 0.90)), 4),
            "percentiles": price_percentiles,
        }
