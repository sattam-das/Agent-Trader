"""AgentTrader v3 FastAPI Backend — Full trading environment with
5-agent AI analysis, backtesting, screener, trade journal, portfolio,
live news, and WebSocket price streaming.
"""

from __future__ import annotations

import asyncio
import os
from time import perf_counter
from typing import Any, Optional

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from backend.agents import (
    DiscoveryAgent,
    DiscoverySuggestion,
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

app = FastAPI(title="AgentTrader API", version="3.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173", 
        "http://localhost:5174", 
        "http://127.0.0.1:5174", 
        "http://localhost:3000"
    ],
    allow_credentials=True,
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
    historical_prices: dict[str, float] = Field(default_factory=dict)
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


class DiscoverResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fetched_at: str
    model: str
    latency_ms: int
    summary: str
    suggestions: list[DiscoverySuggestion]


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _build_agents() -> tuple[NewsAgent, FinancialAgent, RiskAgent, TechnicalAgent, MacroAgent]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing GEMINI_API_KEY")

    return (
        NewsAgent(api_key=api_key),
        FinancialAgent(api_key=api_key),
        RiskAgent(api_key=api_key),
        TechnicalAgent(api_key=api_key),
        MacroAgent(api_key=api_key),
    )


def _build_discovery_agent() -> DiscoveryAgent:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing GEMINI_API_KEY")

    return DiscoveryAgent(api_key=api_key)


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
    return HealthResponse(status="ok", version="3.0.0")


@app.get("/discover", response_model=DiscoverResponse)
async def discover_stocks(
    use_cache: bool = True,
    max_cache_age_hours: int | None = Query(default=6, ge=1),
    exclude_tickers: list[str] | None = Query(default=None),
) -> DiscoverResponse:
    fetcher = _get_fetcher()
    discovery_agent = _build_discovery_agent()
    start = perf_counter()

    try:
        market_context = await asyncio.to_thread(
            fetcher.get_market_news_context,
            use_cache,
            max_cache_age_hours,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Failed to fetch market discovery context: {exc}") from exc

    try:
        discovery_result = await discovery_agent.analyze(
            market_context,
            exclude_tickers=exclude_tickers or [],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Discovery agent failed: {exc}") from exc

    if not discovery_result.suggestions:
        raise HTTPException(status_code=404, detail="No discovery suggestions available right now.")

    latency_ms = int((perf_counter() - start) * 1000)

    return DiscoverResponse(
        fetched_at=str(market_context.get("fetched_at") or ""),
        model=discovery_agent.model_name,
        latency_ms=latency_ms,
        summary=discovery_result.summary,
        suggestions=discovery_result.suggestions,
    )


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
        model=news_agent.model_name,
        latency_ms=latency_ms,
        result=orchestration,
        historical_prices=stock_payload.get("historical_prices", {}),
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


# ==================================================================
# NEW v3 ENDPOINTS — Backtest, Screener, Watchlist, Journal, etc.
# ==================================================================

from backend.engine.backtester import Backtester
from backend.engine.strategies import (
    SMACrossover,
    RSIReversal,
    MACDMomentum,
    BollingerBreakout,
    MultiIndicator,
)
from backend.engine.screener import Screener, PRESET_TICKERS
from backend import db

_STRATEGY_MAP = {
    "sma_crossover": SMACrossover,
    "rsi_reversal": RSIReversal,
    "macd_momentum": MACDMomentum,
    "bollinger_breakout": BollingerBreakout,
    "multi_indicator": MultiIndicator,
}


# --- Backtest ---
class BacktestRequest(BaseModel):
    ticker: str
    strategy: str = "sma_crossover"
    period: str = "2y"
    initial_capital: float = 100000
    params: Optional[dict[str, Any]] = None


@app.post("/api/backtest")
async def run_backtest(req: BacktestRequest):
    strategy_cls = _STRATEGY_MAP.get(req.strategy)
    if not strategy_cls:
        raise HTTPException(400, f"Unknown strategy: {req.strategy}. Available: {list(_STRATEGY_MAP.keys())}")

    ticker = req.ticker.strip().upper()

    # Download data
    try:
        hist = await asyncio.to_thread(
            yf.download, ticker, period=req.period, progress=False, auto_adjust=True
        )
    except Exception as exc:
        raise HTTPException(503, f"Failed to fetch data: {exc}") from exc

    if hist.empty:
        raise HTTPException(400, f"No data found for {ticker}")

    # Flatten MultiIndex columns if present
    if isinstance(hist.columns, pd.MultiIndex):
        hist.columns = [col[0] if isinstance(col, tuple) else col for col in hist.columns]

    strategy = strategy_cls(**(req.params or {}))
    bt = Backtester(initial_capital=req.initial_capital)
    result = await asyncio.to_thread(bt.run, strategy, hist, ticker)
    return result.to_dict()


@app.get("/api/strategies")
async def list_strategies():
    return [
        {
            "id": k,
            "name": cls().name,
            "description": cls().description,
            "default_params": cls().get_params(),
        }
        for k, cls in _STRATEGY_MAP.items()
    ]


# --- Screener ---
@app.get("/api/screener")
async def run_screener(
    preset: str = "nifty50",
    filter: str = "rsi_oversold",
):
    tickers = PRESET_TICKERS.get(preset)
    if not tickers:
        raise HTTPException(400, f"Unknown preset: {preset}. Available: {list(PRESET_TICKERS.keys())}")

    results = await asyncio.to_thread(Screener.scan, tickers, filter)
    return {"preset": preset, "filter": filter, "count": len(results), "results": results}


@app.get("/api/screener/presets")
async def screener_presets():
    return {k: len(v) for k, v in PRESET_TICKERS.items()}



# --- Ticker Search / Autocomplete ---
@app.get("/api/search")
async def search_tickers(q: str = ""):
    """Search for tickers by name or symbol.

    Uses Yahoo Finance search API to return suggestions with
    company name, exchange, and instrument type so users can
    pick the correct ticker (e.g. TCS.NS vs TCS on other exchanges).
    """
    query = q.strip()
    if len(query) < 1:
        return {"query": query, "results": []}

    import httpx

    try:
        url = "https://query1.finance.yahoo.com/v1/finance/search"
        params = {
            "q": query,
            "lang": "en-US",
            "region": "IN",
            "quotesCount": 10,
            "newsCount": 0,
            "listsCount": 0,
            "enableFuzzyQuery": True,
            "quotesQueryId": "tss_match_phrase_query",
        }
        headers = {"User-Agent": "Mozilla/5.0"}

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, headers=headers, timeout=5)
            data = resp.json()

        quotes = data.get("quotes", [])
        results = []
        for q_item in quotes:
            symbol = q_item.get("symbol", "")
            name = q_item.get("shortname") or q_item.get("longname") or ""
            exchange = q_item.get("exchDisp") or q_item.get("exchange") or ""
            q_type = q_item.get("quoteType", "")

            # Only include equities and ETFs
            if q_type not in ("EQUITY", "ETF", "MUTUALFUND", "INDEX"):
                continue

            # Determine market flag
            is_indian = symbol.endswith(".NS") or symbol.endswith(".BO")
            flag = "🇮🇳" if is_indian else "🇺🇸" if exchange in ("NMS", "NYQ", "NGM", "PCX") else "🌐"

            results.append({
                "symbol": symbol,
                "name": name,
                "exchange": exchange,
                "type": q_type,
                "flag": flag,
                "display": f"{symbol} — {name}" if name else symbol,
            })

        return {"query": q.strip(), "count": len(results), "results": results}

    except Exception as exc:
        # Fallback: return the raw query as a suggestion
        return {
            "query": q.strip(),
            "count": 1,
            "results": [{"symbol": q.strip().upper(), "name": "", "exchange": "", "type": "EQUITY", "flag": "🌐", "display": q.strip().upper()}],
        }


# --- Quote ---
@app.get("/api/quote/{ticker}")
async def get_quote(ticker: str):
    symbol = ticker.strip().upper()
    try:
        stock = yf.Ticker(symbol)
        info = await asyncio.to_thread(lambda: stock.fast_info)
        price = getattr(info, 'last_price', None)
        prev = getattr(info, 'previous_close', None)
        change_pct = ((price - prev) / prev * 100) if price and prev else 0.0
        return {
            "ticker": symbol,
            "price": round(float(price), 2) if price else None,
            "previous_close": round(float(prev), 2) if prev else None,
            "change_pct": round(change_pct, 2),
        }
    except Exception as exc:
        return {"ticker": symbol, "price": None, "error": str(exc)}


# --- Indicators (new path for frontend) ---
@app.get("/api/indicators/{ticker}")
async def get_indicators_v3(ticker: str):
    symbol = ticker.strip().upper()
    fetcher = _get_fetcher()

    try:
        stock_payload = await asyncio.to_thread(fetcher.get_stock_data, symbol, True, None)
    except Exception as exc:
        raise HTTPException(503, str(exc)) from exc

    price_history = stock_payload.get("price_history", [])
    indicators = _compute_indicators(price_history)

    return {
        "ticker": symbol,
        "indicators": indicators,
        "price_history": price_history,
    }


# --- News ---
@app.get("/api/news/{ticker}")
async def get_news(ticker: str):
    """Get live news for a ticker via Google News RSS."""
    import httpx
    from xml.etree import ElementTree

    symbol = ticker.strip().upper()
    search = symbol.replace('.NS', '').replace('.BO', '')

    articles = []
    try:
        url = f"https://news.google.com/rss/search?q={search}+stock&hl=en-IN&gl=IN&ceid=IN:en"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            root = ElementTree.fromstring(resp.text)

            for item in root.findall(".//item")[:20]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                source = item.findtext("source", "News")

                # Simple keyword sentiment
                t_lower = title.lower()
                sentiment = "neutral"
                pos_words = ["surge", "jump", "rise", "gain", "bull", "high", "up", "rally", "profit", "growth", "buy", "positive"]
                neg_words = ["fall", "drop", "crash", "bear", "low", "down", "loss", "sell", "negative", "decline", "cut"]
                if any(w in t_lower for w in pos_words):
                    sentiment = "positive"
                elif any(w in t_lower for w in neg_words):
                    sentiment = "negative"

                articles.append({
                    "title": title,
                    "url": link,
                    "source": source,
                    "time": pub_date[:22] if pub_date else "",
                    "sentiment": sentiment,
                })
    except Exception:
        pass

    return {"ticker": symbol, "count": len(articles), "articles": articles}


# --- Watchlist ---
@app.get("/api/watchlist")
async def get_watchlist():
    return db.watchlist_list()


@app.post("/api/watchlist")
async def add_watchlist(data: dict):
    ticker = data.get("ticker", "").strip().upper()
    if not ticker:
        raise HTTPException(400, "ticker required")
    return db.watchlist_add(ticker, data.get("notes", ""))


@app.delete("/api/watchlist/{ticker}")
async def remove_watchlist(ticker: str):
    return db.watchlist_remove(ticker.upper())


# --- Journal ---
@app.get("/api/journal")
async def get_journal(status: Optional[str] = None):
    return db.journal_list(status)


@app.post("/api/journal")
async def add_journal(data: dict):
    return db.journal_add(
        ticker=data["ticker"],
        side=data["side"],
        entry_price=data["entry_price"],
        shares=data["shares"],
        entry_date=data["entry_date"],
        notes=data.get("notes", ""),
    )


@app.post("/api/journal/{trade_id}/close")
async def close_journal(trade_id: int, data: dict):
    return db.journal_close(trade_id, data["exit_price"], data["exit_date"])


@app.delete("/api/journal/{trade_id}")
async def delete_journal(trade_id: int):
    return db.journal_delete(trade_id)


@app.get("/api/journal/stats")
async def journal_stats():
    return db.journal_stats()


# --- Portfolio ---
@app.get("/api/portfolio")
async def get_portfolio():
    return db.portfolio_list()


@app.post("/api/portfolio")
async def add_portfolio(data: dict):
    return db.portfolio_add(
        ticker=data["ticker"],
        shares=data["shares"],
        avg_price=data["avg_price"],
        notes=data.get("notes", ""),
    )


@app.delete("/api/portfolio/{holding_id}")
async def remove_portfolio(holding_id: int):
    return db.portfolio_remove(holding_id)


# ==================================================================
# INTELLIGENCE HUB — Calendar, Heatmap, Sentiment, Risk, Market Pulse
# ==================================================================

from backend.intelligence.calendar import EconomicCalendar
from backend.intelligence.heatmap import SectorHeatmap
from backend.intelligence.sentiment import SentimentScanner
from backend.intelligence.risk_calc import PositionSizer
from backend.intelligence.market_pulse import MarketPulse


# --- Economic Calendar ---
@app.get("/api/calendar")
async def get_calendar(
    days: int = 30,
    country: Optional[str] = None,
    impact: Optional[str] = None,
):
    """Get upcoming economic events."""
    events = EconomicCalendar.get_events(days=days, country=country, impact=impact)
    return {
        "days": days,
        "country": country,
        "impact": impact,
        "count": len(events),
        "events": events,
    }


# --- Sector Heatmap ---
@app.get("/api/heatmap")
async def get_heatmap(market: str = "india"):
    """Get sector performance heatmap."""
    result = await asyncio.to_thread(SectorHeatmap.get_heatmap, market)
    return result


# --- Sentiment Scanner ---
@app.get("/api/sentiment/{ticker}")
async def get_sentiment(ticker: str):
    """Get Reddit + news sentiment for a ticker."""
    result = await SentimentScanner.scan(ticker.strip().upper())
    return result


# --- Position Size Calculator ---
class PositionSizeRequest(BaseModel):
    account_size: float
    risk_pct: float = 1.0
    entry_price: float
    stop_loss: float
    target_price: Optional[float] = None
    commission_rate: Optional[float] = None


@app.post("/api/position-size")
async def calc_position_size(req: PositionSizeRequest):
    """Calculate optimal position size based on risk."""
    try:
        result = PositionSizer.calculate(
            account_size=req.account_size,
            risk_pct=req.risk_pct,
            entry_price=req.entry_price,
            stop_loss=req.stop_loss,
            target_price=req.target_price,
            commission_rate=req.commission_rate,
        )
        return result.to_dict()
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/position-size/compare")
async def compare_position_sizes(req: PositionSizeRequest):
    """Compare position sizes at multiple risk levels (0.5% to 5%)."""
    results = PositionSizer.multi_risk(
        account_size=req.account_size,
        entry_price=req.entry_price,
        stop_loss=req.stop_loss,
        target_price=req.target_price,
    )
    return {"levels": results}


# --- Market Pulse ---
@app.get("/api/market-pulse")
async def get_market_pulse(categories: Optional[str] = None):
    """Get categorized market news feed.

    categories: comma-separated list (e.g. "india_market,breaking,earnings")
    """
    cat_list = categories.split(",") if categories else None
    result = await MarketPulse.fetch(cat_list)
    return result


# ==================================================================
# NATURAL LANGUAGE BACKTESTING — The Innovation
# ==================================================================

from backend.engine.nl_parser import NLParser
from backend.engine.strategies.dynamic_strategy import DynamicStrategy


class NLBacktestRequest(BaseModel):
    prompt: str
    ticker: str = "RELIANCE.NS"
    period: str = "2y"
    initial_capital: float = 100000


@app.post("/api/nl-backtest")
async def nl_backtest(req: NLBacktestRequest):
    """Natural Language Backtesting — describe a strategy in English, get backtest results.

    Example prompts:
    - "Buy when RSI drops below 30, sell when it goes above 70"
    - "Golden cross strategy with 50 and 200 day SMA"
    - "Buy the dip using Bollinger Bands"
    - "MACD crossover with RSI confirmation below 50"
    """
    from time import perf_counter

    t0 = perf_counter()

    # Step 1: Parse English → structured strategy spec
    try:
        parser = NLParser()
    except ValueError as exc:
        raise HTTPException(500, f"LLM configuration error: {exc}") from exc

    spec = await parser.parse(req.prompt)

    if "error" in spec:
        raise HTTPException(
            400,
            {
                "error": spec["error"],
                "hint": "Try being more specific. Example: 'Buy when RSI goes below 30 and MACD crosses up. Sell when RSI goes above 70.'",
            },
        )

    parse_time = perf_counter() - t0

    # Step 2: Create DynamicStrategy from parsed spec
    strategy = DynamicStrategy(spec)

    # Step 3: Download historical data
    period_map = {"1y": "1y", "2y": "2y", "5y": "5y", "max": "max"}
    yf_period = period_map.get(req.period, "2y")

    df = await asyncio.to_thread(
        lambda: yf.download(req.ticker, period=yf_period, progress=False, auto_adjust=True)
    )

    if df.empty:
        raise HTTPException(404, f"No data found for {req.ticker}")

    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    # Step 4: Run through existing backtester (unchanged)
    from backend.engine.backtester import Backtester

    backtester = Backtester(initial_capital=req.initial_capital)
    result = backtester.run(strategy, df, ticker=req.ticker)

    total_time = perf_counter() - t0

    # Step 5: Return results + parsed spec (transparency)
    response = result.to_dict()
    response["parsed_strategy"] = {
        "strategy_name": spec.get("strategy_name"),
        "description": spec.get("description"),
        "buy_conditions": spec.get("buy_conditions"),
        "buy_logic": spec.get("buy_logic"),
        "sell_conditions": spec.get("sell_conditions"),
        "sell_logic": spec.get("sell_logic"),
        "parameters_used": spec.get("parameters_used"),
        "original_prompt": req.prompt,
    }
    response["timing"] = {
        "llm_parse_seconds": round(parse_time, 2),
        "total_seconds": round(total_time, 2),
    }
    response["innovation"] = "natural_language_backtesting"

    return response

if __name__ == "__main__":
    import uvicorn
    import sys
    from pathlib import Path
    
    # Add the project root to sys.path to resolve 'backend' module imports
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    
    # Run the server
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
