from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from backend.agents import FinancialAnalysis, NewsAnalysis, RiskAnalysis


class Recommendation(str, Enum):
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"


class ScoreBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    news_component: float = Field(ge=0.0, le=1.0)
    financial_component: float = Field(ge=0.0, le=1.0)
    risk_component: float = Field(ge=0.0, le=1.0)
    weighted_score: float = Field(ge=0.0, le=1.0)


class OrchestrationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation: Recommendation
    confidence: float = Field(ge=0.0, le=1.0)
    score_breakdown: ScoreBreakdown
    rationale: list[str] = Field(default_factory=list)
    news_analysis: NewsAnalysis
    financial_analysis: FinancialAnalysis
    risk_analysis: RiskAnalysis


class Orchestrator:
    NEWS_WEIGHT = 0.30
    FINANCIAL_WEIGHT = 0.40
    RISK_WEIGHT = 0.30

    BUY_THRESHOLD = 0.70
    HOLD_THRESHOLD = 0.40

    def decide(
        self,
        news_result: NewsAnalysis,
        financial_result: FinancialAnalysis,
        risk_result: RiskAnalysis,
    ) -> OrchestrationResult:
        news_score = self._clamp(news_result.sentiment_score)
        financial_score = self._clamp(financial_result.health_score)
        risk_score = 1.0 - self._clamp(risk_result.risk_level)

        weighted_score = self._clamp(
            (news_score * self.NEWS_WEIGHT)
            + (financial_score * self.FINANCIAL_WEIGHT)
            + (risk_score * self.RISK_WEIGHT)
        )

        recommendation = self._recommend(weighted_score)
        score_breakdown = ScoreBreakdown(
            news_component=round(news_score, 4),
            financial_component=round(financial_score, 4),
            risk_component=round(risk_score, 4),
            weighted_score=round(weighted_score, 4),
        )

        rationale = self._build_rationale(news_result, financial_result, risk_result, recommendation)

        return OrchestrationResult(
            recommendation=recommendation,
            confidence=round(weighted_score, 4),
            score_breakdown=score_breakdown,
            rationale=rationale,
            news_analysis=news_result,
            financial_analysis=financial_result,
            risk_analysis=risk_result,
        )

    def _recommend(self, score: float) -> Recommendation:
        if score > self.BUY_THRESHOLD:
            return Recommendation.BUY
        if score > self.HOLD_THRESHOLD:
            return Recommendation.HOLD
        return Recommendation.SELL

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
        news_result: NewsAnalysis,
        financial_result: FinancialAnalysis,
        risk_result: RiskAnalysis,
        recommendation: Recommendation,
    ) -> list[str]:
        rationale = [
            (
                f"News sentiment is {news_result.sentiment} "
                f"({self._clamp(news_result.sentiment_score):.2f}), affecting short-term outlook."
            ),
            (
                f"Financial health scores {self._clamp(financial_result.health_score):.2f}, "
                "representing fundamental strength."
            ),
            (
                f"Risk level is {self._clamp(risk_result.risk_level):.2f}, "
                "which inversely impacts confidence."
            ),
            f"Final recommendation is {recommendation.value} based on weighted deterministic scoring.",
        ]

        if financial_result.strengths:
            rationale.append(f"Top strength: {financial_result.strengths[0]}")
        if financial_result.weaknesses:
            rationale.append(f"Top weakness: {financial_result.weaknesses[0]}")
        if news_result.key_events:
            rationale.append(f"Key event: {news_result.key_events[0]}")
        if risk_result.risk_factors:
            rationale.append(f"Primary risk factor: {risk_result.risk_factors[0]}")

        return rationale
