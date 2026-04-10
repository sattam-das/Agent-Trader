"""5-Factor Orchestrator with signal confluence detection and conviction levels.

Deterministic weighted math — not another LLM call. Every decision is
auditable and debuggable.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.agents import (
    FinancialAnalysis,
    MacroAnalysis,
    NewsAnalysis,
    RiskAnalysis,
    TechnicalAnalysis,
)


class Recommendation(str, Enum):
    STRONG_BUY = "STRONG BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG SELL"


class Conviction(str, Enum):
    VERY_HIGH = "VERY HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ScoreBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    news_component: float = Field(ge=0.0, le=1.0)
    financial_component: float = Field(ge=0.0, le=1.0)
    risk_component: float = Field(ge=0.0, le=1.0)
    technical_component: float = Field(ge=0.0, le=1.0)
    macro_component: float = Field(ge=0.0, le=1.0)
    weighted_score: float = Field(ge=0.0, le=1.0)
    confluence_bonus: float = Field(ge=-0.1, le=0.1)
    final_score: float = Field(ge=0.0, le=1.0)


class OrchestrationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation: Recommendation
    conviction: Conviction
    confidence: float = Field(ge=0.0, le=1.0)
    score_breakdown: ScoreBreakdown
    rationale: list[str] = Field(default_factory=list)
    news_analysis: NewsAnalysis
    financial_analysis: FinancialAnalysis
    risk_analysis: RiskAnalysis
    technical_analysis: TechnicalAnalysis
    macro_analysis: MacroAnalysis


class Orchestrator:
    # Weights sum to 1.0
    NEWS_WEIGHT = 0.15
    FINANCIAL_WEIGHT = 0.25
    RISK_WEIGHT = 0.20
    TECHNICAL_WEIGHT = 0.25
    MACRO_WEIGHT = 0.15

    # Recommendation thresholds
    STRONG_BUY_THRESHOLD = 0.82
    BUY_THRESHOLD = 0.65
    HOLD_UPPER = 0.45
    SELL_THRESHOLD = 0.25

    def decide(
        self,
        news_result: NewsAnalysis,
        financial_result: FinancialAnalysis,
        risk_result: RiskAnalysis,
        technical_result: TechnicalAnalysis,
        macro_result: MacroAnalysis,
    ) -> OrchestrationResult:
        # Extract and normalise scores
        news_score = self._clamp(news_result.sentiment_score)
        financial_score = self._clamp(financial_result.health_score)
        risk_score = 1.0 - self._clamp(risk_result.risk_level)  # invert: low risk = good
        technical_score = self._clamp(technical_result.signal_score)
        macro_score = self._clamp(macro_result.macro_score)

        # Weighted sum
        weighted = self._clamp(
            (news_score * self.NEWS_WEIGHT)
            + (financial_score * self.FINANCIAL_WEIGHT)
            + (risk_score * self.RISK_WEIGHT)
            + (technical_score * self.TECHNICAL_WEIGHT)
            + (macro_score * self.MACRO_WEIGHT)
        )

        # Confluence bonus: when agents agree, boost conviction
        scores = [news_score, financial_score, risk_score, technical_score, macro_score]
        confluence_bonus = self._confluence_bonus(scores)
        final_score = self._clamp(weighted + confluence_bonus)

        # Determine recommendation and conviction
        recommendation = self._recommend(final_score)
        conviction = self._conviction(scores, final_score)

        score_breakdown = ScoreBreakdown(
            news_component=round(news_score, 4),
            financial_component=round(financial_score, 4),
            risk_component=round(risk_score, 4),
            technical_component=round(technical_score, 4),
            macro_component=round(macro_score, 4),
            weighted_score=round(weighted, 4),
            confluence_bonus=round(confluence_bonus, 4),
            final_score=round(final_score, 4),
        )

        rationale = self._build_rationale(
            news_result, financial_result, risk_result,
            technical_result, macro_result,
            recommendation, conviction, scores,
        )

        return OrchestrationResult(
            recommendation=recommendation,
            conviction=conviction,
            confidence=round(final_score, 4),
            score_breakdown=score_breakdown,
            rationale=rationale,
            news_analysis=news_result,
            financial_analysis=financial_result,
            risk_analysis=risk_result,
            technical_analysis=technical_result,
            macro_analysis=macro_result,
        )

    def _recommend(self, score: float) -> Recommendation:
        if score >= self.STRONG_BUY_THRESHOLD:
            return Recommendation.STRONG_BUY
        if score >= self.BUY_THRESHOLD:
            return Recommendation.BUY
        if score >= self.HOLD_UPPER:
            return Recommendation.HOLD
        if score >= self.SELL_THRESHOLD:
            return Recommendation.SELL
        return Recommendation.STRONG_SELL

    def _conviction(self, scores: list[float], final_score: float) -> Conviction:
        """Conviction based on how much agents agree with each other."""
        import statistics

        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0.5

        # Low spread = high agreement = high conviction
        if std_dev < 0.08:
            return Conviction.VERY_HIGH
        if std_dev < 0.15:
            return Conviction.HIGH
        if std_dev < 0.25:
            return Conviction.MEDIUM
        return Conviction.LOW

    def _confluence_bonus(self, scores: list[float]) -> float:
        """Bonus when 4+ agents agree on direction."""
        bullish_count = sum(1 for s in scores if s > 0.6)
        bearish_count = sum(1 for s in scores if s < 0.4)

        if bullish_count >= 4:
            return 0.05  # strong bullish confluence
        if bearish_count >= 4:
            return -0.05  # strong bearish confluence
        if bullish_count >= 3:
            return 0.02
        if bearish_count >= 3:
            return -0.02

        return 0.0

    @staticmethod
    def _clamp(value: float | int | None) -> float:
        if value is None:
            return 0.5
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.5
        return max(0.0, min(1.0, numeric))

    def _build_rationale(
        self,
        news: NewsAnalysis,
        financial: FinancialAnalysis,
        risk: RiskAnalysis,
        technical: TechnicalAnalysis,
        macro: MacroAnalysis,
        recommendation: Recommendation,
        conviction: Conviction,
        scores: list[float],
    ) -> list[str]:
        rationale: list[str] = []

        # Headline
        bullish = sum(1 for s in scores if s > 0.6)
        bearish = sum(1 for s in scores if s < 0.4)
        rationale.append(
            f"Overall: {recommendation.value} with {conviction.value} conviction "
            f"({bullish}/5 agents bullish, {bearish}/5 bearish)."
        )

        # Per-agent insights
        rationale.append(
            f"📰 News: {news.sentiment} sentiment ({self._clamp(news.sentiment_score):.0%}) — {news.summary}"
        )
        rationale.append(
            f"💰 Financial: Health {self._clamp(financial.health_score):.0%} — {financial.summary}"
        )
        rationale.append(
            f"⚠️ Risk: Level {self._clamp(risk.risk_level):.0%} — {risk.summary}"
        )
        rationale.append(
            f"📊 Technical: {technical.trend} ({self._clamp(technical.signal_score):.0%}) — {technical.summary}"
        )
        rationale.append(
            f"🏦 Macro: {macro.institutional_sentiment} ({self._clamp(macro.macro_score):.0%}) — {macro.summary}"
        )

        # Key signals
        if technical.signals:
            top_signals = technical.signals[:3]
            rationale.append(f"Key technical signals: {', '.join(top_signals)}")

        if financial.strengths:
            rationale.append(f"Top strength: {financial.strengths[0]}")
        if financial.weaknesses:
            rationale.append(f"Top weakness: {financial.weaknesses[0]}")

        if news.key_events:
            rationale.append(f"Key event: {news.key_events[0]}")

        if risk.risk_factors:
            rationale.append(f"Primary risk: {risk.risk_factors[0]}")

        if macro.key_observations:
            rationale.append(f"Smart money: {macro.key_observations[0]}")

        return rationale
