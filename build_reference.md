# AgentTrader Implementation Blueprint

## Core Architecture
- **AI Provider**: Groq (LLaMA 3 models) for ultra-low latency inference.
- **Framework**: Lightweight custom Python classes with `asyncio` for parallel execution.
- **Structured Output**: Pydantic models enforcing strict JSON responses from agents.
- **Backend**: FastAPI for async endpoint handling.
- **Frontend**: Streamlit for the user interface.
- **Orchestration**: Deterministic weighted scoring (No LLM for final decision).

## Directory Structure
```
agenttrader/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py      # Pydantic Schemas
│   │   ├── news_agent.py      # Groq LLM Agent
│   │   ├── financial_agent.py # Groq LLM Agent
│   │   └── risk_agent.py      # Groq LLM Agent
│   ├── utils/
│   │   ├── __init__.py
│   │   └── data_fetcher.py    # yfinance & NewsAPI + Caching
│   ├── main.py                # FastAPI App
│   └── orchestrator.py        # Scoring Logic
├── frontend/
│   └── app.py                 # Streamlit UI
├── data/
│   └── cache/                 # Pre-fetched JSON demo data
├── build_cache.py             # Script to pre-fetch demo data
├── requirements.txt
└── .env
```

## Environment Variables (.env)
- `GROQ_API_KEY`: For LLaMA model inference.
- `NEWS_API_KEY`: For fetching news via NewsAPI.

## Pydantic Schemas (base_agent.py)
1. **NewsAnalysis**: `sentiment`, `sentiment_score`, `key_events`, `summary`
2. **FinancialAnalysis**: `health_score`, `strengths`, `weaknesses`, `summary`
3. **RiskAnalysis**: `risk_level`, `risk_factors`, `summary`

## Orchestrator Logic
- News Score: 30% (`sentiment_score`)
- Finance Score: 40% (`health_score`)
- Risk Score: 30% (`1 - risk_level`)
- **Decision Matrix**:
  - Score > 0.7: BUY
  - Score > 0.4: HOLD
  - Score <= 0.4: SELL

## Key Technical Decisions
1. **No heavy Agent Frameworks**: Avoided LangChain/CrewAI in favor of native Python `asyncio` to maximize speed and reduce overhead.
2. **Groq LPU**: Swapped Anthropic for Groq to reduce agent inference time, aiming for sub-3 second total execution.
3. **Demo Cache**: Implemented a local JSON cache (`build_cache.py`) to prevent live API rate limits/failures during presentations.
4. **Parallel Execution**: Used `asyncio.gather()` in FastAPI to run News, Finance, and Risk agents concurrently rather than sequentially.
