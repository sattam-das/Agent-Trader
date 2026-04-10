# 🧠 AgentTrader — Project Blueprint

## One-Liner
**An all-in-one AI-powered trading environment for Indian & US retail traders** — combining multi-agent AI research, backtesting, live charts, news, screener, and trade journaling in a single professional platform.

---

## 🎯 Problem Statement

Retail traders currently jump between 5-10 different apps/websites:
- **TradingView** for charts
- **Moneycontrol / Economic Times** for news
- **Screener.in / Tickertape** for stock screening
- **Random Excel sheets** for trade journaling
- **No access** to backtesting engines (institutional-grade tools cost ₹50K+/year)

**AgentTrader solves this by putting everything in one place** — and adds AI-powered analysis on top that institutional traders pay lakhs for.

---

## 🧩 What We're Building

### A Professional Trading Terminal with 7 Core Modules

| # | Module | What It Does | Status |
|---|--------|-------------|--------|
| 1 | 📊 **Charts** | Professional candlestick charts with SMA, EMA, RSI, MACD, Bollinger Bands, volume | ✅ Working |
| 2 | 🧠 **AI Analysis** | 5 parallel AI agents (News, Financial, Risk, Technical, Macro) analyze any stock | ✅ Working |
| 3 | 🔬 **Backtest Lab** | Test 5 trading strategies on historical data, see equity curves + Sharpe/drawdown | ✅ Working |
| 4 | 📰 **Live News** | Real-time scrolling news with AI sentiment badges (positive/negative/neutral) | ✅ Working |
| 5 | 📈 **Screener** | Scan Nifty 50 / US Tech stocks by RSI, Golden Cross, Volume Spike, BB Squeeze | ✅ Working |
| 6 | 📋 **Trade Journal** | Log trades, auto-calculate P&L, win rate, streaks, performance analytics | ✅ Working |
| 7 | 💼 **Portfolio** | Track holdings, see allocation, unrealized P&L | ✅ Working |

---

## 🏗️ Architecture & Tech Stack

### Backend (Rajesh — Python)
| Component | Technology | Why |
|-----------|-----------|-----|
| API Framework | **FastAPI** | Async, fast, auto-docs via Swagger |
| AI Engine | **Groq Cloud** (Llama 3.3 70B) | Free, ultra-fast LLM inference |
| Data Source | **yfinance** | Free stock data (NSE + US) |
| Indicators | **NumPy + Pandas** | Pure-math RSI, MACD, Bollinger, SMA, VWAP |
| Simulation | **Monte Carlo (GBM)** | 10,000 path probability engine |
| Backtesting | **Custom vectorized engine** | Sharpe, Sortino, Max Drawdown, Win Rate |
| Database | **SQLite** | Persistent watchlist, journal, portfolio |
| News | **Google News RSS** | Free, no API key needed |

### Frontend (Sattam — to rebuild in React/Next.js)
| Component | Current State | Target |
|-----------|--------------|--------|
| Framework | Vanilla HTML/JS/CSS (working prototype) | **React (Next.js or Vite)** |
| Charts | TradingView Lightweight Charts (working) | Keep or upgrade to TradingView Advanced |
| Styling | Custom dark CSS theme (working) | **Tailwind CSS** or styled-components |
| State | Vanilla JS | **Zustand / Redux** |
| Real-time | Fetch polling | **WebSocket** for live prices |
| Routing | Tab-based SPA | **React Router** |

---

## 📡 API Reference (Backend → Frontend Contract)

All endpoints are live and documented at **http://localhost:8000/docs**

### Existing v2 Endpoints (AI Analysis)
| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `POST` | `/analyze` | Full 5-agent AI analysis | `{ ticker, result: { recommendation, confidence, rationale, ... }, technical_indicators, monte_carlo }` |
| `GET` | `/indicators/{ticker}` | Technical indicators + price history | `{ indicators: { rsi_14, sma_20, macd_line, ... }, price_history: [...] }` |
| `GET` | `/simulate/{ticker}` | Monte Carlo simulation | `{ simulation: { horizons, var_95, paths, ... } }` |
| `POST` | `/compare` | Multi-stock comparison (up to 5) | `{ items: [{ ticker, recommendation, scores, ... }] }` |
| `GET` | `/health` | Health check | `{ status: "ok", version: "3.0.0" }` |

### New v3 Endpoints (Trading Environment)
| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `POST` | `/api/backtest` | Run strategy backtest | `{ total_return, sharpe_ratio, equity_curve: [...], trades: [...] }` |
| `GET` | `/api/strategies` | List available strategies | `[{ id, name, description, default_params }]` |
| `GET` | `/api/screener?preset=nifty50&filter=rsi_oversold` | Stock screener | `{ results: [{ ticker, signal, value, price }] }` |
| `GET` | `/api/screener/presets` | Available screener presets | `{ nifty50: 20, us_tech: 15, nse_banking: 8, ... }` |
| `GET` | `/api/quote/{ticker}` | Quick price quote | `{ ticker, price, change_pct }` |
| `GET` | `/api/news/{ticker}` | Live news with sentiment | `{ articles: [{ title, source, sentiment, url }] }` |
| `GET` | `/api/indicators/{ticker}` | Same as /indicators but under /api path | Same as v2 |
| **Watchlist** |
| `GET` | `/api/watchlist` | List watched tickers | `[{ id, ticker, added_at }]` |
| `POST` | `/api/watchlist` | Add ticker | `{ ticker: "RELIANCE.NS" }` |
| `DELETE` | `/api/watchlist/{ticker}` | Remove ticker | — |
| **Trade Journal** |
| `GET` | `/api/journal` | List all trades | `[{ id, ticker, side, entry_price, exit_price, pnl, ... }]` |
| `POST` | `/api/journal` | Log new trade | `{ ticker, side, entry_price, shares, entry_date }` |
| `POST` | `/api/journal/{id}/close` | Close a trade | `{ exit_price, exit_date }` |
| `DELETE` | `/api/journal/{id}` | Delete trade | — |
| `GET` | `/api/journal/stats` | Performance stats | `{ win_rate, total_pnl, best_trade, worst_trade, ... }` |
| **Portfolio** |
| `GET` | `/api/portfolio` | List holdings | `[{ id, ticker, shares, avg_price }]` |
| `POST` | `/api/portfolio` | Add holding | `{ ticker, shares, avg_price }` |
| `DELETE` | `/api/portfolio/{id}` | Remove holding | — |

### Backtest Request Body Example
```json
{
  "ticker": "RELIANCE.NS",
  "strategy": "sma_crossover",
  "period": "2y",
  "initial_capital": 100000,
  "params": { "fast_period": 50, "slow_period": 200 }
}
```

### Available Strategies
| ID | Name | Description |
|----|------|-------------|
| `sma_crossover` | SMA Crossover | Golden Cross / Death Cross (SMA 50/200) |
| `rsi_reversal` | RSI Reversal | Buy oversold, sell overbought |
| `macd_momentum` | MACD Momentum | MACD signal line crossover |
| `bollinger_breakout` | Bollinger Breakout | Mean reversion on band touches |
| `multi_indicator` | Multi-Indicator | Buy only when 3+ indicators agree |

### Screener Presets
| ID | Market | Tickers |
|----|--------|---------|
| `nifty50` | 🇮🇳 Nifty 50 | RELIANCE, TCS, HDFC, INFY, ICICI... (20) |
| `nse_banking` | 🇮🇳 NSE Banking | HDFCBANK, SBIN, ICICI, KOTAK... (8) |
| `nse_it` | 🇮🇳 NSE IT | TCS, INFY, HCL, WIPRO... (8) |
| `us_tech` | 🇺🇸 US Tech | AAPL, MSFT, GOOGL, NVDA... (15) |
| `us_popular` | 🇺🇸 US Popular | AAPL, TSLA, NVDA, META... (15) |

### Screener Filters
| ID | What It Detects |
|----|----------------|
| `rsi_oversold` | RSI below 30 (buy opportunity) |
| `rsi_overbought` | RSI above 70 (sell signal) |
| `golden_cross` | SMA 50 just crossed above SMA 200 |
| `death_cross` | SMA 50 just crossed below SMA 200 |
| `bb_squeeze` | Bollinger bandwidth < 4% (breakout imminent) |
| `volume_spike` | Volume 2x above 20-day average |

---

## 👥 Team Roles

### Rajesh (Backend)
- ✅ FastAPI backend — all endpoints LIVE
- ✅ 5-agent AI orchestration system
- ✅ Backtesting engine (5 strategies)
- ✅ Stock screener (6 filters × 5 presets)
- ✅ SQLite DB (watchlist, journal, portfolio)
- ✅ Monte Carlo simulation
- ✅ Technical indicators engine
- 🔄 Future: WebSocket price streaming, more strategies

### Sattam (Frontend)
- 🎯 Rebuild the UI in **React** (the current vanilla JS prototype works — use it as reference)
- 🎯 Professional dark trading terminal design
- 🎯 TradingView Lightweight Charts integration
- 🎯 Responsive layout (sidebar + navbar + content area)
- 🎯 All 7 modules as React components
- 🎯 WebSocket integration for live price updates
- 🎯 State management (Zustand recommended)

---

## 🚀 How to Run

```bash
# Clone
git clone https://github.com/sattam-das/Agent-Trader.git
cd Agent-Trader

# Setup
cp .env.example .env
# Edit .env → add GROQ_API_KEY (free at https://console.groq.com)

# Create virtual env & install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run backend (serves frontend too)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Open: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## 🔑 API Keys Needed

| Key | Required? | Where to Get | Cost |
|-----|-----------|-------------|------|
| `GROQ_API_KEY` | ✅ Required | https://console.groq.com | **Free** |
| `NEWS_API_KEY` | ❌ Optional | https://newsapi.org | Free tier (falls back to RSS) |

---

## 📊 Indian Stock Tickers

Use `.NS` suffix for NSE stocks:
```
RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, ICICIBANK.NS,
SBIN.NS, BAJFINANCE.NS, ITC.NS, BHARTIARTL.NS, KOTAKBANK.NS,
HINDUNILVR.NS, LT.NS, WIPRO.NS, TITAN.NS, SUNPHARMA.NS
```

Use `.BO` suffix for BSE stocks:
```
RELIANCE.BO, TCS.BO, INFY.BO
```

US stocks use plain symbols: `AAPL, TSLA, NVDA, MSFT, GOOGL, AMZN`

---

## 🎯 What Makes This Project Stand Out

1. **Not just a dashboard — it's a trading environment.** Users don't just get one recommendation, they get charts, news, backtesting, screening, and journaling.
2. **Multi-agent AI.** 5 specialized LLM agents analyze stocks in parallel — like having a team of analysts.
3. **Free everything.** Zero cost APIs (Groq, yfinance, Google News). No paid dependencies.
4. **Indian stock support.** Built for Indian retail traders first — Nifty 50, NSE Banking, NSE IT presets.
5. **Real backtesting.** Not toy backtesting — actual Sharpe ratio, max drawdown, slippage modeling, commission costs.
6. **Monte Carlo probability.** 10,000 simulation paths for probabilistic price forecasting.

---

## 📝 Future Enhancements (v4 Ideas)

- [ ] Real-time WebSocket price streaming
- [ ] Alpaca paper trading integration
- [ ] More strategies (VWAP, Ichimoku, Fibonacci)
- [ ] Chart drawing tools (trendlines, fibonacci retracement)
- [ ] Push notifications (Telegram/Discord alerts)
- [ ] AI-generated trade ideas
- [ ] Options chain analysis
- [ ] Sector heatmap
- [ ] Multi-timeframe analysis
- [ ] User authentication & cloud sync
