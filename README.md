# 🤖 AgentTrader

**Multi-Agent AI Stock Research & Trading Analysis Platform**

A professional-grade, 5-agent algorithmic trading analysis system that combines AI-powered research agents with quantitative technical analysis and Monte Carlo probability simulations — all powered by **free APIs**.

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-2.0-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

### 🧠 5 Parallel AI Agents
All agents run simultaneously via `asyncio.gather()` for maximum speed:

| Agent | Role | Data Source |
|-------|------|-------------|
| 📰 **News** | Sentiment analysis from headlines | Google News RSS / NewsAPI |
| 💰 **Financial** | Fundamental health assessment | yfinance |
| ⚠️ **Risk** | Volatility and beta risk scoring | yfinance |
| 📊 **Technical** | Signal confluence interpretation | Computed indicators |
| 🏦 **Macro** | Institutional & insider sentiment | yfinance |

### 📈 Technical Analysis Engine
Pure-math indicator calculations (no paid libraries):
- **RSI** (14-period) — Overbought/Oversold detection
- **MACD** (12, 26, 9) — Trend & momentum signals
- **Bollinger Bands** (20, 2σ) — Volatility & mean reversion
- **SMA/EMA** (20, 50, 200) — Trend direction & Golden/Death Cross
- **ATR** (14) — Average True Range for position sizing
- **Support/Resistance** — Pivot point detection

### 🎯 Monte Carlo Probability Engine
- 10,000 Geometric Brownian Motion simulation paths
- 30/60/90 day price projections with percentile bands
- Probability of hitting analyst price targets
- Value at Risk (VaR) at 95% and 99% confidence

### 🏗️ 5-Factor Orchestrator
Deterministic weighted scoring — fully auditable:
```
News:      15%  |  Financial: 25%  |  Risk: 20%
Technical: 25%  |  Macro:     15%
```
- Signal confluence bonus when 3+ agents agree
- Conviction levels: LOW → MEDIUM → HIGH → VERY HIGH
- Recommendations: STRONG SELL → SELL → HOLD → BUY → STRONG BUY

### 🎨 Professional Dashboard
React + Vite frontend with dark theme:
1. **Discover** — AI-powered stock discovery
2. **Analysis** — 5-agent AI analysis with recommendation
3. **Charts** — Professional candlestick charts (TradingView Lightweight Charts)
4. **Backtest** — Classic + Natural Language backtesting
5. **Screener** — AI-powered stock screener
6. **News / Journal / Portfolio** — Full trading workspace

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Free [Google Gemini API Key](https://aistudio.google.com/apikey) (no credit card needed)

### Setup

```bash
# Clone the repo
git clone https://github.com/sattam-das/Agent-Trader.git
cd Agent-Trader

# Set up environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run (creates venv, installs deps, starts both servers)
./run_app.sh
```

### Manual Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &

# Start frontend
cd next-frontend && npm install && npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze` | Full 5-agent analysis with indicators + Monte Carlo |
| `GET` | `/indicators/{ticker}` | Raw technical indicator data for charting |
| `GET` | `/simulate/{ticker}` | Monte Carlo simulation results |
| `POST` | `/compare` | Multi-stock comparison (up to 5 tickers) |
| `GET` | `/health` | Health check |

**API Docs:** http://localhost:8000/docs (interactive Swagger UI)

### Example

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

---

## 🏗️ Architecture

```
AgentTrader/
├── backend/
│   ├── main.py                    # FastAPI app & endpoints
│   ├── orchestrator.py            # 5-factor weighted scoring engine
│   ├── agents/
│   │   ├── base_agent.py          # Base agent + Pydantic schemas
│   │   ├── news_agent.py          # News sentiment analysis
│   │   ├── financial_agent.py     # Fundamental health scoring
│   │   ├── risk_agent.py          # Volatility & beta risk
│   │   ├── technical_agent.py     # Signal confluence interpreter
│   │   └── macro_agent.py         # Institutional & insider analysis
│   └── utils/
│       ├── data_fetcher.py        # yfinance + News data pipeline
│       ├── technical_indicators.py # RSI, MACD, BB, SMA, ATR
│       └── monte_carlo.py         # GBM simulation engine
├── next-frontend/                   # React + Vite dashboard
│   └── src/components/            # Charts, Analysis, Backtest, etc.
├── requirements.txt
├── run_app.sh                     # Mac/Linux run script
├── .env                           # Environment variables
└── .gitignore
```

---

## 🔧 Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ | Free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `NEWS_API_KEY` | ❌ | Optional — falls back to free Google News RSS |
| `GEMINI_MODEL` | ❌ | Default: `gemini-2.0-flash` |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Google Gemini 2.5 Flash |
| **Backend** | FastAPI, asyncio, Pydantic v2 |
| **Frontend** | React, Vite, TradingView Lightweight Charts |
| **Data** | yfinance, Google News RSS, NewsAPI |
| **Analysis** | NumPy, Pandas (pure math — no paid libraries) |

---

## 👥 Team

- **Sattam Das** — [sattam-das](https://github.com/sattam-das)
- **Rajesh Sardar** — [CpLevi](https://github.com/CpLevi)
- **Saptarshi Mukhopadhyay** — [saptarshi-2006](https://github.com/saptarshi-2006)
- **Swarnavo Bagchi** — [bagchiswarna7-ux](https://github.com/bagchiswarna7-ux)

---
