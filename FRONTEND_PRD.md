# AgentTrader — Frontend PRD (Product Requirements Document)

> **Purpose:** This document describes the complete frontend for AgentTrader — a professional trading environment for retail traders. Use this as the single source of truth to vibe-code the React frontend. The backend is already built and live.

---

## 1. Product Overview

### What is AgentTrader?
AgentTrader is an **all-in-one AI-powered trading workstation** for Indian and US retail traders. Instead of switching between TradingView (charts), Moneycontrol (news), Screener.in (fundamentals), and Excel (trade tracking), traders get everything in one professional dark-themed terminal.

### Who is it for?
- Indian retail stock traders (NSE/BSE)
- US stock enthusiasts
- Finance/CS students doing hackathon demos
- Anyone who wants to learn trading with backtesting

### Core Value Proposition
1. **Charts** — TradingView-grade candlestick charts with indicators
2. **AI Analysis** — 5 parallel LLM agents (News, Financial, Risk, Technical, Macro) analyze any stock
3. **Backtesting** — Test strategies on historical data before risking real money
4. **Live News** — Scrolling news feed with AI sentiment analysis
5. **Screener** — Find stocks matching technical patterns (RSI oversold, Golden Cross, etc.)
6. **Trade Journal** — Log and analyze your trading performance
7. **Portfolio** — Track your holdings and P&L

---

## 2. Tech Stack (Frontend)

| Layer | Technology | Notes |
|-------|-----------|-------|
| Framework | **React 18** (via Vite) | SPA, no SSR needed |
| Routing | **React Router v6** | Client-side routing |
| State | **Zustand** | Lightweight, minimal boilerplate |
| Charts | **lightweight-charts** v4 (npm package) | TradingView's open-source charting lib |
| HTTP | **fetch** or **axios** | All API calls to same-origin backend |
| Styling | **CSS Modules** or **Tailwind CSS** | Dark theme mandatory |
| Fonts | **Inter** (UI) + **JetBrains Mono** (prices/data) | Google Fonts |
| Icons | **Lucide React** or emoji | Minimal icon set |

### Install Commands
```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install lightweight-charts react-router-dom zustand axios lucide-react
```

---

## 3. Backend API Reference

The backend is live at `http://localhost:8000`. Full Swagger docs at `http://localhost:8000/docs`.

### 3.1 Stock Data APIs

#### `GET /api/quote/{ticker}`
Quick price quote for any stock.
```
Request:  GET /api/quote/RELIANCE.NS
Response: {
  "ticker": "RELIANCE.NS",
  "price": 1350.20,
  "previous_close": 1328.85,
  "change_pct": 1.59
}
```

#### `GET /api/indicators/{ticker}`
Full OHLCV price history + computed technical indicators.
```
Request:  GET /api/indicators/RELIANCE.NS
Response: {
  "ticker": "RELIANCE.NS",
  "price_history": [
    { "date": "2025-04-01", "open": 1305.0, "high": 1312.0, "low": 1298.0, "close": 1310.5, "volume": 12500000 },
    ...
  ],
  "indicators": {
    "rsi_14": [null, null, ..., 42.5, 38.2, 55.1],
    "sma_20": [null, ..., 1320.5, 1318.2],
    "sma_50": [null, ..., 1345.0],
    "ema_12": [...],
    "ema_26": [...],
    "macd_line": [...],
    "macd_signal": [...],
    "macd_histogram": [...],
    "bb_upper": [...],
    "bb_middle": [...],
    "bb_lower": [...],
    "atr_14": [...],
    "obv": [...]
  }
}
```
> **Note:** Indicator arrays are same length as `price_history`. Leading `null` values = insufficient data for calculation. Chart rendering must skip nulls.

#### `GET /api/news/{ticker}`
Live news for a ticker via Google News RSS.
```
Request:  GET /api/news/RELIANCE.NS
Response: {
  "ticker": "RELIANCE.NS",
  "count": 20,
  "articles": [
    {
      "title": "Reliance shares surge 3% on refinery expansion plans",
      "url": "https://economictimes.com/...",
      "source": "Economic Times",
      "time": "Thu, 10 Apr 2026 10:",
      "sentiment": "positive"    // "positive" | "negative" | "neutral"
    },
    ...
  ]
}
```

### 3.2 AI Analysis API

#### `POST /analyze`
Run full 5-agent AI analysis on a stock. **This is a slow endpoint (5-15 seconds)** — show a loading state.
```
Request:  POST /analyze
Body:     { "ticker": "RELIANCE.NS" }
Response: {
  "ticker": "RELIANCE.NS",
  "company_name": "Reliance Industries Limited",
  "sector": "Energy",
  "industry": "Oil & Gas Refining & Marketing",
  "current_price": 1350.20,
  "model": "llama-3.3-70b-versatile",
  "latency_ms": 8500,
  "result": {
    "recommendation": "BUY",           // "STRONG BUY" | "BUY" | "HOLD" | "SELL" | "STRONG SELL"
    "conviction": "MEDIUM",            // "HIGH" | "MEDIUM" | "LOW"
    "confidence": 0.72,                // 0.0 to 1.0
    "weighted_score": 0.65,
    "score_breakdown": {
      "news_component": 0.8,           // Each is 0.0 to 1.0
      "financial_component": 0.6,
      "risk_component": 0.55,
      "technical_component": 0.7,
      "macro_component": 0.5,
      "confluence_bonus": 0.05
    },
    "rationale": [
      "Strong institutional buying detected in recent quarters",
      "RSI at 42 indicates neutral momentum with slight oversold bias",
      "Positive news sentiment driven by refinery expansion plans"
    ],
    "risk_factors": [
      "High debt-to-equity ratio of 0.45",
      "Global crude oil price volatility"
    ],
    "news_analysis": {
      "sentiment": "positive",
      "summary": "Recent news is bullish, driven by..."
    },
    "financial_analysis": {
      "summary": "Revenue growth of 12% YoY..."
    }
  },
  "technical_indicators": { ... },     // Same format as /api/indicators
  "monte_carlo": {
    "horizons": {
      "30_day": {
        "median_price": 1402.0,
        "bull_case": 1510.0,
        "bear_case": 1280.0,
        "probability_above_current": 0.62
      },
      "90_day": { ... }
    }
  }
}
```

### 3.3 Backtesting API

#### `GET /api/strategies`
List all available strategies and their configurable parameters.
```
Response: [
  {
    "id": "sma_crossover",
    "name": "SMA Crossover",
    "description": "Buy on Golden Cross (fast SMA > slow SMA), sell on Death Cross.",
    "default_params": { "fast_period": 50, "slow_period": 200 }
  },
  {
    "id": "rsi_reversal",
    "name": "RSI Reversal",
    "description": "Buy at RSI oversold reversal, sell at RSI overbought reversal.",
    "default_params": { "rsi_period": 14, "oversold": 30.0, "overbought": 70.0 }
  },
  {
    "id": "macd_momentum",
    "name": "MACD Momentum",
    "description": "Buy on bullish MACD crossover, sell on bearish crossover.",
    "default_params": { "fast": 12, "slow": 26, "signal": 9, "histogram_threshold": 0.0 }
  },
  {
    "id": "bollinger_breakout",
    "name": "Bollinger Breakout",
    "description": "Buy at lower band touch, sell at upper band touch (mean reversion).",
    "default_params": { "period": 20, "std_dev": 2.0 }
  },
  {
    "id": "multi_indicator",
    "name": "Multi-Indicator",
    "description": "Buys when multiple indicators (RSI, MACD, SMA, BB) agree.",
    "default_params": { "min_confluence": 3 }
  }
]
```

#### `POST /api/backtest`
Run a backtest. **Takes 5-20 seconds** (downloads historical data + runs simulation). Show loading state.
```
Request:
{
  "ticker": "RELIANCE.NS",
  "strategy": "sma_crossover",
  "period": "2y",                        // "1y" | "2y" | "5y" | "max"
  "initial_capital": 100000,
  "params": { "fast_period": 50, "slow_period": 200 }  // optional, uses defaults if omitted
}

Response:
{
  "strategy_name": "SMA Crossover",
  "ticker": "RELIANCE.NS",
  "start_date": "2024-04-09",
  "end_date": "2026-04-09",
  "initial_capital": 100000,
  "final_capital": 100510.43,

  // Key metrics
  "total_return": 0.0051,      // 0.51%
  "cagr": 0.0025,              // 0.25%
  "sharpe_ratio": 0.08,
  "sortino_ratio": 0.07,
  "max_drawdown": -0.148,      // -14.8%
  "calmar_ratio": 0.017,
  "win_rate": 1.0,             // 100%
  "profit_factor": 7.40,
  "total_trades": 1,
  "avg_trade_return": 0.0074,
  "avg_holding_days": 45.0,
  "best_trade": 0.0074,
  "worst_trade": 0.0074,
  "buy_hold_return": -0.0807,  // -8.07% (benchmark)
  "excess_return": 0.0858,     // 8.58% (strategy beat benchmark)

  // Chart data
  "equity_curve": [
    { "date": "2024-04-09", "equity": 100000.0 },
    { "date": "2024-04-10", "equity": 99950.2 },
    ...
  ],
  "drawdown_series": [
    { "date": "2024-04-09", "drawdown": 0.0 },
    { "date": "2024-06-15", "drawdown": -0.082 },
    ...
  ],
  "monthly_returns": [
    { "year": 2024, "month": 4, "return": -0.012 },
    { "year": 2024, "month": 5, "return": 0.035 },
    ...
  ],
  "trades": [
    {
      "entry_date": "2025-01-15",
      "exit_date": "2025-03-02",
      "entry_price": 1285.50,
      "exit_price": 1295.00,
      "shares": 73,
      "pnl": 694.50,
      "return_pct": 0.0074,
      "holding_days": 46
    }
  ],
  "signals": [
    { "date": "2025-01-15", "type": "BUY", "price": 1285.50, "shares": 73 },
    { "date": "2025-03-02", "type": "SELL", "price": 1295.00, "shares": 73 }
  ]
}
```

### 3.4 Screener API

#### `GET /api/screener?preset={preset}&filter={filter}`
Scan a group of stocks against a technical filter. **Takes 15-60 seconds** (fetches data for each ticker sequentially). Show loading state with progress if possible.
```
Request:  GET /api/screener?preset=nifty50&filter=rsi_oversold
Response: {
  "preset": "nifty50",
  "filter": "rsi_oversold",
  "count": 3,
  "results": [
    { "ticker": "SBIN.NS", "signal": "RSI Oversold", "value": 28.5, "price": 780.40, "change_pct": -1.2 },
    { "ticker": "ITC.NS", "signal": "RSI Oversold", "value": 25.1, "price": 425.10, "change_pct": -0.8 },
    { "ticker": "MARUTI.NS", "signal": "RSI Oversold", "value": 29.8, "price": 11250.0, "change_pct": -2.1 }
  ]
}
```

**Presets:** `nifty50` (20 stocks), `nse_banking` (8), `nse_it` (8), `us_tech` (15), `us_popular` (15)

**Filters:** `rsi_oversold`, `rsi_overbought`, `golden_cross`, `death_cross`, `bb_squeeze`, `volume_spike`

#### `GET /api/screener/presets`
```
Response: { "nifty50": 20, "nse_banking": 8, "nse_it": 8, "us_tech": 15, "us_popular": 15 }
```

### 3.5 Watchlist API (CRUD)

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| `GET` | `/api/watchlist` | — | `[{ "id": 1, "ticker": "RELIANCE.NS", "added_at": "2026-04-10 10:30:00", "notes": "" }]` |
| `POST` | `/api/watchlist` | `{ "ticker": "RELIANCE.NS" }` | `{ "status": "ok", "ticker": "RELIANCE.NS" }` |
| `DELETE` | `/api/watchlist/{ticker}` | — | `{ "status": "ok" }` |

### 3.6 Trade Journal API (CRUD)

#### Create trade:
```
POST /api/journal
{ "ticker": "INFY.NS", "side": "LONG", "entry_price": 1500.0, "shares": 10, "entry_date": "2026-04-01" }
→ { "status": "ok", "id": 1 }
```

#### Close trade:
```
POST /api/journal/1/close
{ "exit_price": 1600.0, "exit_date": "2026-04-10" }
→ { "status": "ok", "pnl": 1000.0, "return_pct": 0.0667 }
```

#### List trades:
```
GET /api/journal
→ [{ "id": 1, "ticker": "INFY.NS", "side": "LONG", "entry_price": 1500.0, "exit_price": 1600.0,
     "shares": 10, "pnl": 1000.0, "return_pct": 0.0667, "status": "CLOSED", "entry_date": "...", "exit_date": "..." }]
```

#### Stats:
```
GET /api/journal/stats
→ { "total_trades": 5, "win_rate": 0.6, "total_pnl": 2500.0, "avg_return": 0.045,
   "best_trade": 0.12, "worst_trade": -0.05, "avg_winner": 0.08, "avg_loser": -0.03,
   "consecutive_wins": 3, "consecutive_losses": 1 }
```

#### Delete trade:
```
DELETE /api/journal/{id} → { "status": "ok" }
```

### 3.7 Portfolio API (CRUD)

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| `GET` | `/api/portfolio` | — | `[{ "id": 1, "ticker": "INFY.NS", "shares": 50, "avg_price": 1500.0 }]` |
| `POST` | `/api/portfolio` | `{ "ticker": "INFY.NS", "shares": 50, "avg_price": 1500.0 }` | `{ "status": "ok", "id": 1 }` |
| `DELETE` | `/api/portfolio/{id}` | — | `{ "status": "ok" }` |

> **Note:** For current prices of portfolio holdings, call `/api/quote/{ticker}` for each holding.

---

## 4. Page & Component Specifications

### 4.1 Layout (Shell)

The app has a **fixed 3-section layout** that never changes:

```
┌──────────────────────────────────────────────────────────┐
│  NAVBAR (52px height, full width)                        │
│  [🧠 AgentTrader] [🔍 Search...] [TICKER ₹PRICE ▲%]    │
├──────────┬───────────────────────────────────────────────┤
│ SIDEBAR  │  TAB BAR (42px)                               │
│ (280px)  │  [Charts] [AI] [Backtest] [News] [Screener]  │
│          ├───────────────────────────────────────────────┤
│ Watchlist│                                               │
│ ────────│              CONTENT AREA                      │
│ AAPL ▲  │         (scrollable, full height)              │
│ TCS  ▼  │                                                │
│ NVDA ▲  │     Content changes based on active tab        │
│          │                                               │
│ ────────│                                               │
│ Quick Add│                                               │
│ [RELIANCE]│                                              │
│ [TCS]    │                                               │
│ [INFY]   │                                               │
└──────────┴───────────────────────────────────────────────┘
```

- Sidebar is always visible (collapsible on mobile)
- Active ticker persists across all tabs
- Selecting a ticker in screener/watchlist/search updates the global ticker

### 4.2 Global State (Zustand Store)

```js
const useStore = create((set) => ({
  activeTicker: '',
  setTicker: (ticker) => set({ activeTicker: ticker }),

  watchlist: [],
  setWatchlist: (items) => set({ watchlist: items }),

  activeTab: 'charts',
  setTab: (tab) => set({ activeTab: tab }),
}))
```

### 4.3 Component Tree

```
App
├── Navbar
│   ├── Logo
│   ├── SearchInput (ticker search, Enter → setTicker)
│   ├── ActiveTickerDisplay (ticker name + price + change badge)
│   └── Clock
├── Sidebar
│   ├── WatchlistSection
│   │   └── WatchlistItem[] (ticker + price + change, click → setTicker)
│   ├── AddTickerInput
│   └── QuickAddButtons (preset buttons: RELIANCE, TCS, INFY, etc.)
├── TabBar
│   └── TabButton[] (one per module, click → setTab)
└── ContentArea
    ├── ChartView (active when tab === 'charts')
    ├── AIAnalysis (active when tab === 'analysis')
    ├── BacktestLab (active when tab === 'backtest')
    ├── NewsFeed (active when tab === 'news')
    ├── Screener (active when tab === 'screener')
    ├── Journal (active when tab === 'journal')
    └── Portfolio (active when tab === 'portfolio')
```

---

## 5. Module Specifications

### 5.1 📊 ChartView

**Purpose:** Professional candlestick chart with technical indicator overlays.

**Triggers:** Renders whenever `activeTicker` changes. Calls `GET /api/indicators/{ticker}`.

**Components:**
| Component | Description |
|-----------|-------------|
| CandlestickChart | Main chart (height: 480px). Uses `lightweight-charts` `createChart()` + `addCandlestickSeries()`. |
| VolumeOverlay | Volume histogram below candles (same chart, separate price scale at bottom 15%). |
| SMAOverlay | Two line series: SMA 20 (amber) and SMA 50 (blue). |
| BollingerOverlay | Upper and lower BB as dashed purple lines. |
| RSIChart | Separate chart below (height: 180px). Purple line + dashed red line at 70 + dashed green line at 30. |
| MACDChart | Separate chart below (height: 180px). Blue MACD line + amber signal line + green/red histogram bars. |
| TimeframeSelector | Buttons: 1M, 3M, 6M, 1Y, 2Y, 5Y (calls `/api/indicators/{ticker}?period=X`). Not yet in backend — for now show buttons but keep data at default. |

**Chart Config (dark theme):**
```js
{
  layout: { background: { color: '#1a1f2e' }, textColor: '#94a3b8' },
  grid: { vertLines: { color: 'rgba(42,51,69,0.5)' }, horzLines: { color: 'rgba(42,51,69,0.5)' } },
  crosshair: { mode: CrosshairMode.Normal },
  rightPriceScale: { borderColor: '#2a3345' },
  timeScale: { borderColor: '#2a3345' },
}
```

**Candle colors:** Up: `#22c55e`, Down: `#ef4444`

---

### 5.2 🧠 AIAnalysis

**Purpose:** Run 5-agent AI analysis and display recommendation with score breakdown.

**Flow:** User clicks "Run AI Analysis" → `POST /analyze { ticker }` → display results.

**Components:**
| Component | Description |
|-----------|-------------|
| AnalyzeButton | Big blue button. Shows spinner while loading. Disabled without activeTicker. |
| RecommendationBadge | Large pill: "🚀 STRONG BUY · HIGH · 85%" in green. Color-coded by recommendation. |
| ScoreBreakdown | 6 metric cards in a grid: News, Financial, Risk, Technical, Macro, Confluence. Each shows 0-100% with color (green >60%, red <40%, amber between). |
| RationaleList | Bulleted list of rationale strings. |
| RiskFactorsList | Red-tinted bulleted list of risk factors. |
| AnalysisSummaries | Two cards side-by-side: News Summary + Financial Summary. |
| MonteCarlo | If `monte_carlo` data exists: show 30-day and 90-day price projections (bull/bear/median). |

**Recommendation color mapping:**
| Recommendation | Background | Text Color |
|---------------|-----------|------------|
| STRONG BUY | `rgba(34,197,94,0.15)` | `#22c55e` |
| BUY | `rgba(34,197,94,0.15)` | `#22c55e` |
| HOLD | `rgba(245,158,11,0.15)` | `#f59e0b` |
| SELL | `rgba(239,68,68,0.15)` | `#ef4444` |
| STRONG SELL | `rgba(239,68,68,0.15)` | `#ef4444` |

---

### 5.3 🔬 BacktestLab

**Purpose:** Configure and run strategy backtests, visualize results.

**Components:**
| Component | Description |
|-----------|-------------|
| ConfigPanel | Card with 4 inputs in a grid row: Strategy (dropdown), Ticker (text, auto-filled from activeTicker), Period (dropdown: 1Y/2Y/5Y/Max), Initial Capital (number, default 100000). + "Run Backtest" button. |
| MetricsGrid | 12 metric cards in auto-fill grid: Total Return, CAGR, Sharpe, Sortino, Max Drawdown, Win Rate, Trades, Profit Factor, Buy & Hold, Excess Return, Best Trade, Worst Trade. Color-coded green/red. |
| EquityCurveChart | Area chart (blue fill, 350px height) showing equity over time. Uses `lightweight-charts` `addAreaSeries()`. |
| DrawdownChart | Area chart (red fill, 200px height) showing drawdown percentage over time. |
| TradeLogTable | Sortable table: Entry Date, Exit Date, Entry Price, Exit Price, Shares, P&L (green/red), Return %, Days Held. |
| MonthlyReturnsHeatmap | (Optional stretch goal) Calendar-style grid showing monthly returns color-coded. |

---

### 5.4 📰 NewsFeed

**Purpose:** Scrollable live news with sentiment analysis.

**Triggers:** Loads when tab opened. Calls `GET /api/news/{activeTicker}`.

**Components:**
| Component | Description |
|-----------|-------------|
| NewsHeader | "Live News" title + Refresh button (re-fetches). |
| NewsCard | For each article: source tag (gray), sentiment badge (green/red/amber), time, headline. Entire card is clickable → opens article URL in new tab. |
| EmptyState | "📰 No news found" with dimmed icon. |

**Sentiment badge colors:**
| Sentiment | Color |
|-----------|-------|
| positive | Green badge |
| negative | Red badge |
| neutral | Amber badge |

---

### 5.5 📈 Screener

**Purpose:** Scan groups of stocks by technical filters.

**Components:**
| Component | Description |
|-----------|-------------|
| FilterRow | Horizontal row: Market dropdown (Nifty 50 / NSE Banking / NSE IT / US Tech / US Popular) + Filter dropdown (RSI Oversold / RSI Overbought / Golden Cross / Death Cross / BB Squeeze / Volume Spike) + "Scan" button. |
| ResultsTable | Table: Ticker (clickable → setTicker + switch to Charts), Signal (blue badge), Value, Price, Change % (green/red). + Chart icon button → go to charts. |
| EmptyState | "No stocks match this filter. Try a different market or filter." |

> **UX Note:** Screener is slow (15-60s). Show a spinner with "Scanning 20 stocks..." messaging.

---

### 5.6 📋 Journal

**Purpose:** Manual trade logging with performance analytics.

**Components:**
| Component | Description |
|-----------|-------------|
| AddTradeForm | Card with 5 inputs: Ticker, Side (LONG/SHORT dropdown), Entry Price, Shares, Date. + "Log Trade" button. |
| StatsGrid | 6 metric cards: Total Trades, Win Rate, Total P&L, Avg Return, Best Trade, Worst Trade. Only shows when there are closed trades. |
| TradeTable | Table: Ticker, Side (green LONG / red SHORT badge), Entry Price, Exit Price, Shares, P&L (green/red), Return % (green/red), Status (amber OPEN / blue CLOSED badge), Actions (Close button + Delete button). |
| CloseTradeModal | When clicking "Close" on an open trade: prompt for exit price. Auto-fills today's date. Calls `POST /api/journal/{id}/close`. |

---

### 5.7 💼 Portfolio

**Purpose:** Track stock holdings and see allocation.

**Components:**
| Component | Description |
|-----------|-------------|
| AddHoldingForm | Card with 3 inputs: Ticker, Shares, Avg Price. + "Add" button. |
| SummaryMetrics | Total value, total invested, unrealized P&L. For each holding, call `/api/quote/{ticker}` to get current price. |
| HoldingsTable | Table: Ticker (clickable → setTicker), Shares, Avg Price, Current Price (from quote API), Value, P&L, Return %, Delete button. |

---

## 6. Design Specifications

### 6.1 Color Palette

```css
--bg-primary: #0a0e17;          /* Body background */
--bg-secondary: #111827;        /* Sidebar, navbar */
--bg-card: #1a1f2e;             /* Cards, chart backgrounds */
--bg-card-hover: #222940;       /* Card hover state */
--bg-input: #151b2b;            /* Input fields */
--border: #2a3345;              /* Borders, dividers */
--border-hover: #3d4f6f;        /* Hover borders */

--text-primary: #e2e8f0;        /* Main text */
--text-secondary: #94a3b8;      /* Secondary text */
--text-muted: #64748b;          /* Labels, section titles */
--text-dim: #475569;            /* Placeholder text */

--green: #22c55e;               /* Positive / buy / profit */
--red: #ef4444;                 /* Negative / sell / loss */
--blue: #3b82f6;                /* Primary actions, active tabs */
--amber: #f59e0b;               /* Warnings, neutral, HOLD */
--purple: #a855f7;              /* RSI, Bollinger indicators */
--cyan: #06b6d4;                /* Active ticker display */
```

### 6.2 Typography

```css
/* UI text */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

/* Prices, data, indicators, code */
font-family: 'JetBrains Mono', monospace;
```

### 6.3 Component Styles

**Cards:**
- Background: `--bg-card`
- Border: `1px solid --border`
- Border radius: `12px`
- Padding: `20px`
- Hover: border becomes `--border-hover`

**Metric Cards:**
- Same as card but text-centered
- Label: 0.7rem, uppercase, letter-spacing 0.8px, `--text-muted`
- Value: 1.3rem, JetBrains Mono, font-weight 700
- Value color: green if positive, red if negative, white if neutral

**Buttons:**
- Primary: `--blue` background, white text, 8px 16px padding
- Success: `--green` background
- Danger: `--red` background
- Outline: transparent bg, `--border` border, `--text-secondary` text
- All: 6px border-radius, 0.82rem, font-weight 600

**Badges:**
- Pill shape: 20px border-radius, 3px 10px padding
- Green: `rgba(34,197,94,0.15)` bg, `#22c55e` text
- Red: `rgba(239,68,68,0.15)` bg, `#ef4444` text
- Blue: `rgba(59,130,246,0.15)` bg, `#3b82f6` text
- Amber: `rgba(245,158,11,0.15)` bg, `#f59e0b` text

**Tables:**
- Header: sticky, 0.7rem, uppercase, `--text-muted`, border-bottom
- Cells: JetBrains Mono, 0.8rem
- Row hover: `--bg-card-hover`

---

## 7. Indian Stock Tickers

The app must support NSE and BSE stocks. Ticker format:

```
NSE: RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS
BSE: RELIANCE.BO, TCS.BO
US:  AAPL, TSLA, NVDA, MSFT
```

**Currency display rule:**
- If ticker ends with `.NS` or `.BO` → show `₹` symbol
- Otherwise → show `$` symbol

**Quick-add preset tickers for sidebar:**
```
🇮🇳 RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS
🇺🇸 AAPL, TSLA, NVDA
```

---

## 8. Loading & Error States

| Scenario | UI Behavior |
|----------|-------------|
| API call in progress | Replace button text with spinner + "Loading..." / "Analyzing..." / "Running..." |
| Quote fetch fails | Show "—" for price |
| Empty screener results | Show "No stocks match this filter" empty state |
| No trades in journal | Show "No trades logged yet" in table |
| AI analysis fails | Show red card with error message |
| News fetch empty | Show "📰 No news found" empty state |
| Backtest error | Show red error card |

---

## 9. File Structure

```
frontend/
├── index.html
├── package.json
├── vite.config.js
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── App.css (or Tailwind)
│   ├── store.js                    # Zustand store
│   ├── api.js                      # API client (all fetch calls)
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Navbar.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── TabBar.jsx
│   │   ├── Charts/
│   │   │   ├── CandlestickChart.jsx
│   │   │   ├── RSIChart.jsx
│   │   │   └── MACDChart.jsx
│   │   ├── Common/
│   │   │   ├── MetricCard.jsx
│   │   │   ├── Badge.jsx
│   │   │   ├── DataTable.jsx
│   │   │   ├── Spinner.jsx
│   │   │   └── EmptyState.jsx
│   │   ├── News/
│   │   │   └── NewsCard.jsx
│   │   └── Screener/
│   │       └── ScreenerRow.jsx
│   └── pages/
│       ├── ChartView.jsx
│       ├── AIAnalysis.jsx
│       ├── BacktestLab.jsx
│       ├── NewsFeed.jsx
│       ├── Screener.jsx
│       ├── Journal.jsx
│       └── Portfolio.jsx
```

---

## 10. Non-Functional Requirements

- **No authentication** — single-user local app
- **No SSR** — pure client-side SPA
- **Responsive** — works on 1280px+ screens. Sidebar collapses on <900px
- **Performance** — charts must render <500ms after data arrives
- **Accessibility** — all interactive elements need unique IDs
- **SEO** — not needed (local app), but proper `<title>` tag
