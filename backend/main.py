"""AgentTrader FastAPI Backend — 5-agent parallel analysis with
technical indicators, Monte Carlo simulation, and multi-stock comparison.
"""

from __future__ import annotations

import asyncio
import os
from time import perf_counter
from typing import Any, Optional

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from backend.agents import (
    FinancialAgent,
    MacroAgent,
    NewsAgent,
    RiskAgent,
    TechnicalAgent,
)
from backend.orchestrator import OrchestrationResult, Orchestrator
from backend.utils.data_fetcher import DataFetcher
from backend.utils.monte_carlo import MonteCarloSimulator
from backend.utils.technical_indicators import TechnicalIndicators

load_dotenv()

app = FastAPI(title="AgentTrader API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Request / Response Models
# ------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(min_length=1, max_length=12)
    use_cache: bool = True
    max_cache_age_hours: Optional[int] = Field(default=None, ge=1)


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str
    company_name: str
    sector: str
    industry: str
    current_price: Optional[float]
    fetched_at: str
    model: str
    latency_ms: int
    result: OrchestrationResult
    technical_indicators: dict[str, Any] = Field(default_factory=dict)
    monte_carlo: dict[str, Any] = Field(default_factory=dict)
    analyst_targets: dict[str, Any] = Field(default_factory=dict)
    price_history: list[dict[str, Any]] = Field(default_factory=list)


class IndicatorsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str
    indicators: dict[str, Any]
    price_history: list[dict[str, Any]]


class SimulationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str
    simulation: dict[str, Any]


class CompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tickers: list[str] = Field(min_length=1, max_length=5)
    use_cache: bool = True


class CompareItem(BaseModel):
    ticker: str
    company_name: str
    recommendation: str
    conviction: str
    confidence: float
    news_score: float
    financial_score: float
    risk_score: float
    technical_score: float
    macro_score: float
    current_price: Optional[float]
    sector: str


class CompareResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[CompareItem]
    latency_ms: int


class HealthResponse(BaseModel):
    status: str
    version: str


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _build_agents() -> tuple[NewsAgent, FinancialAgent, RiskAgent, TechnicalAgent, MacroAgent]:
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise HTTPException(status_code=500, detail="Missing GROQ_API_KEY")

    return (
        NewsAgent(api_key=groq_key),
        FinancialAgent(api_key=groq_key),
        RiskAgent(api_key=groq_key),
        TechnicalAgent(api_key=groq_key),
        MacroAgent(api_key=groq_key),
    )


def _get_fetcher() -> DataFetcher:
    return DataFetcher(os.getenv("NEWS_API_KEY"), cache_dir="data/cache")


def _compute_indicators(price_history: list[dict[str, Any]]) -> dict[str, Any]:
    """Build pandas DF from price_history list and compute indicators."""
    if not price_history:
        return {"error": "No price history available."}

    df = pd.DataFrame(price_history)
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df.rename(columns={col: col.capitalize()}, inplace=True)

    if "Close" not in df.columns:
        return {"error": "No close price data."}

    return TechnicalIndicators.compute_all(df)


def _run_simulation(
    price_history: list[dict[str, Any]],
    analyst_targets: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run Monte Carlo from price_history list."""
    if not price_history:
        return {"error": "No price history for simulation."}

    closes = [p["close"] for p in price_history if "close" in p]
    if len(closes) < 30:
        return {"error": "Need at least 30 price points."}

    targets = None
    if analyst_targets:
        targets = {
            "low": analyst_targets.get("target_low"),
            "mean": analyst_targets.get("target_mean"),
            "high": analyst_targets.get("target_high"),
        }

    return MonteCarloSimulator.simulate(closes, analyst_targets=targets)


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version="2.0.0")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_stock(request: AnalyzeRequest) -> AnalyzeResponse:
    ticker = request.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker cannot be empty")

    fetcher = _get_fetcher()
    orchestrator = Orchestrator()
    start = perf_counter()

    # 1. Fetch stock data
    try:
        stock_payload = await asyncio.to_thread(
            fetcher.get_stock_data,
            ticker,
            request.use_cache,
            request.max_cache_age_hours,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Failed to fetch stock data: {exc}") from exc

    # 2. Compute technical indicators (pure math, fast)
    price_history = stock_payload.get("price_history", [])
    indicators = _compute_indicators(price_history)

    # 3. Run Monte Carlo simulation (pure math, fast)
    analyst_targets = stock_payload.get("analyst_targets", {})
    simulation = _run_simulation(price_history, analyst_targets)

    # 4. Prepare macro data bundle for the Macro agent
    macro_data = {
        "insider_trades": stock_payload.get("insider_trades", []),
        "institutional_holders": stock_payload.get("institutional_holders", []),
        "analyst_targets": analyst_targets,
        "sector": stock_payload.get("sector", "Unknown"),
        "industry": stock_payload.get("industry", "Unknown"),
    }

    # 5. Run all 5 agents in parallel
    news_agent, financial_agent, risk_agent, technical_agent, macro_agent = _build_agents()

    try:
        news_result, financial_result, risk_result, technical_result, macro_result = (
            await asyncio.gather(
                news_agent.analyze(stock_payload.get("news", [])),
                financial_agent.analyze(stock_payload.get("financials", {})),
                risk_agent.analyze(stock_payload.get("risk_data", {})),
                technical_agent.analyze(indicators),
                macro_agent.analyze(macro_data),
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent analysis failed: {exc}") from exc

    # 6. Orchestrate
    orchestration = orchestrator.decide(
        news_result, financial_result, risk_result, technical_result, macro_result
    )
    latency_ms = int((perf_counter() - start) * 1000)

    return AnalyzeResponse(
        ticker=stock_payload.get("ticker", ticker),
        company_name=str(stock_payload.get("company_name") or ticker),
        sector=str(stock_payload.get("sector") or "Unknown"),
        industry=str(stock_payload.get("industry") or "Unknown"),
        current_price=stock_payload.get("current_price"),
        fetched_at=str(stock_payload.get("fetched_at") or ""),
        model=news_agent.model,
        latency_ms=latency_ms,
        result=orchestration,
        technical_indicators=indicators,
        monte_carlo=simulation,
        analyst_targets=analyst_targets,
        price_history=price_history,
    )


@app.get("/indicators/{ticker}", response_model=IndicatorsResponse)
async def get_indicators(ticker: str) -> IndicatorsResponse:
    symbol = ticker.strip().upper()
    fetcher = _get_fetcher()

    try:
        stock_payload = await asyncio.to_thread(fetcher.get_stock_data, symbol, True, None)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    price_history = stock_payload.get("price_history", [])
    indicators = _compute_indicators(price_history)

    return IndicatorsResponse(
        ticker=symbol,
        indicators=indicators,
        price_history=price_history,
    )


@app.get("/simulate/{ticker}", response_model=SimulationResponse)
async def simulate_stock(ticker: str) -> SimulationResponse:
    symbol = ticker.strip().upper()
    fetcher = _get_fetcher()

    try:
        stock_payload = await asyncio.to_thread(fetcher.get_stock_data, symbol, True, None)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    price_history = stock_payload.get("price_history", [])
    analyst_targets = stock_payload.get("analyst_targets", {})
    simulation = _run_simulation(price_history, analyst_targets)

    return SimulationResponse(ticker=symbol, simulation=simulation)


@app.post("/compare", response_model=CompareResponse)
async def compare_stocks(request: CompareRequest) -> CompareResponse:
    start = perf_counter()
    fetcher = _get_fetcher()
    orchestrator = Orchestrator()

    async def _analyze_one(sym: str) -> CompareItem:
        symbol = sym.strip().upper()
        stock_payload = await asyncio.to_thread(fetcher.get_stock_data, symbol, request.use_cache, None)

        price_history = stock_payload.get("price_history", [])
        indicators = _compute_indicators(price_history)
        macro_data = {
            "insider_trades": stock_payload.get("insider_trades", []),
            "institutional_holders": stock_payload.get("institutional_holders", []),
            "analyst_targets": stock_payload.get("analyst_targets", {}),
            "sector": stock_payload.get("sector", "Unknown"),
            "industry": stock_payload.get("industry", "Unknown"),
        }

        news_agent, financial_agent, risk_agent, technical_agent, macro_agent = _build_agents()

        news_r, fin_r, risk_r, tech_r, macro_r = await asyncio.gather(
            news_agent.analyze(stock_payload.get("news", [])),
            financial_agent.analyze(stock_payload.get("financials", {})),
            risk_agent.analyze(stock_payload.get("risk_data", {})),
            technical_agent.analyze(indicators),
            macro_agent.analyze(macro_data),
        )

        orch = orchestrator.decide(news_r, fin_r, risk_r, tech_r, macro_r)

        return CompareItem(
            ticker=symbol,
            company_name=str(stock_payload.get("company_name") or symbol),
            recommendation=orch.recommendation.value,
            conviction=orch.conviction.value,
            confidence=orch.confidence,
            news_score=orch.score_breakdown.news_component,
            financial_score=orch.score_breakdown.financial_component,
            risk_score=orch.score_breakdown.risk_component,
            technical_score=orch.score_breakdown.technical_component,
            macro_score=orch.score_breakdown.macro_component,
            current_price=stock_payload.get("current_price"),
            sector=str(stock_payload.get("sector") or "Unknown"),
        )

    try:
        items = await asyncio.gather(*[_analyze_one(t) for t in request.tickers])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Comparison failed: {exc}") from exc

    latency_ms = int((perf_counter() - start) * 1000)
    return CompareResponse(items=list(items), latency_ms=latency_ms)
