from __future__ import annotations

import asyncio
import os
from time import perf_counter

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from backend.agents import FinancialAgent, NewsAgent, RiskAgent
from backend.orchestrator import OrchestrationResult, Orchestrator
from backend.utils.data_fetcher import DataFetcher

load_dotenv()

app = FastAPI(title="AgentTrader API", version="0.1.0")


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(min_length=1, max_length=12)
    use_cache: bool = True
    max_cache_age_hours: int | None = Field(default=None, ge=1)


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str
    company_name: str
    fetched_at: str
    model: str
    latency_ms: int
    result: OrchestrationResult


class HealthResponse(BaseModel):
    status: str


def _build_agents() -> tuple[NewsAgent, FinancialAgent, RiskAgent]:
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise HTTPException(status_code=500, detail="Missing GROQ_API_KEY")

    return (
        NewsAgent(api_key=groq_key),
        FinancialAgent(api_key=groq_key),
        RiskAgent(api_key=groq_key),
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_stock(request: AnalyzeRequest) -> AnalyzeResponse:
    ticker = request.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker cannot be empty")

    fetcher = DataFetcher(os.getenv("NEWS_API_KEY"), cache_dir="data/cache")
    orchestrator = Orchestrator()

    start = perf_counter()

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

    news_agent, financial_agent, risk_agent = _build_agents()

    try:
        news_result, financial_result, risk_result = await asyncio.gather(
            news_agent.analyze(stock_payload.get("news", [])),
            financial_agent.analyze(stock_payload.get("financials", {})),
            risk_agent.analyze(stock_payload.get("risk_data", {})),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent analysis failed: {exc}") from exc

    orchestration = orchestrator.decide(news_result, financial_result, risk_result)
    latency_ms = int((perf_counter() - start) * 1000)

    return AnalyzeResponse(
        ticker=stock_payload.get("ticker", ticker),
        company_name=str(stock_payload.get("company_name") or ticker),
        fetched_at=str(stock_payload.get("fetched_at") or ""),
        model=news_agent.model,
        latency_ms=latency_ms,
        result=orchestration,
    )
