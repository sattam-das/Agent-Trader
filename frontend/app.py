"""AgentTrader v2 — Professional Trading Analysis Dashboard.

Features:
- TradingView live widget (free, no API key)
- Interactive Plotly candlestick charts with indicator overlays
- Monte Carlo probability distribution visualization
- 5-factor radar chart
- Multi-stock comparison
- Dark professional theme
"""

from __future__ import annotations

from html import escape
import os
from typing import Any

import httpx
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

DEFAULT_API_URL = os.getenv("AGENT_TRADER_API_URL", "http://127.0.0.1:8000")

# ------------------------------------------------------------------
# Theme & Config
# ------------------------------------------------------------------
COLORS = {
    "bg": "#0e1117",
    "card": "#1a1d23",
    "card_border": "#2d3139",
    "text": "#e6edf3",
    "text_muted": "#8b949e",
    "accent_green": "#3fb950",
    "accent_red": "#f85149",
    "accent_blue": "#58a6ff",
    "accent_yellow": "#d29922",
    "accent_purple": "#bc8cff",
    "accent_orange": "#f0883e",
    "gradient_start": "#0b3a6e",
    "gradient_end": "#1f8cc3",
}

REC_STYLES = {
    "STRONG BUY":  {"color": "#3fb950", "bg": "rgba(63,185,80,0.15)", "icon": "🚀"},
    "BUY":         {"color": "#3fb950", "bg": "rgba(63,185,80,0.10)", "icon": "📈"},
    "HOLD":        {"color": "#d29922", "bg": "rgba(210,153,34,0.10)", "icon": "⏸️"},
    "SELL":        {"color": "#f85149", "bg": "rgba(248,81,73,0.10)", "icon": "📉"},
    "STRONG SELL": {"color": "#f85149", "bg": "rgba(248,81,73,0.15)", "icon": "🔻"},
}


# ------------------------------------------------------------------
# API Helpers
# ------------------------------------------------------------------
def _request_analysis(api_url: str, ticker: str, use_cache: bool, max_age: int | None) -> dict[str, Any]:
    payload: dict[str, Any] = {"ticker": ticker, "use_cache": use_cache}
    if max_age is not None:
        payload["max_cache_age_hours"] = max_age

    with httpx.Client(timeout=60.0) as client:
        response = client.post(f"{api_url.rstrip('/')}/analyze", json=payload)
    response.raise_for_status()
    return response.json()


def _request_compare(api_url: str, tickers: list[str], use_cache: bool) -> dict[str, Any]:
    payload = {"tickers": tickers, "use_cache": use_cache}
    with httpx.Client(timeout=120.0) as client:
        response = client.post(f"{api_url.rstrip('/')}/compare", json=payload)
    response.raise_for_status()
    return response.json()


def _request_discovery(
    api_url: str,
    max_age: int | None,
    exclude_tickers: list[str],
) -> dict[str, Any]:
    params: list[tuple[str, str | int]] = [("use_cache", "false")]
    if max_age is not None:
        params.append(("max_cache_age_hours", max_age))
    for ticker in exclude_tickers:
        params.append(("exclude_tickers", ticker))

    with httpx.Client(timeout=60.0) as client:
        response = client.get(f"{api_url.rstrip('/')}/discover", params=params)
    response.raise_for_status()
    return response.json()


# ------------------------------------------------------------------
# Chart Builders
# ------------------------------------------------------------------
def _build_radar_chart(breakdown: dict[str, Any]) -> go.Figure:
    categories = ["News", "Financial", "Risk (inv)", "Technical", "Macro"]
    values = [
        breakdown.get("news_component", 0),
        breakdown.get("financial_component", 0),
        breakdown.get("risk_component", 0),
        breakdown.get("technical_component", 0),
        breakdown.get("macro_component", 0),
    ]
    values.append(values[0])  # close the polygon
    categories.append(categories[0])

    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill="toself",
        fillcolor="rgba(88,166,255,0.2)",
        line=dict(color=COLORS["accent_blue"], width=2),
        marker=dict(size=8, color=COLORS["accent_blue"]),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=COLORS["card"],
            radialaxis=dict(visible=True, range=[0, 1], gridcolor=COLORS["card_border"], tickfont=dict(color=COLORS["text_muted"])),
            angularaxis=dict(gridcolor=COLORS["card_border"], tickfont=dict(color=COLORS["text"], size=12)),
        ),
        paper_bgcolor=COLORS["card"],
        margin=dict(l=60, r=60, t=30, b=30),
        height=350,
        showlegend=False,
    )
    return fig


def _build_candlestick_chart(
    price_history: list[dict[str, Any]],
    indicators: dict[str, Any],
    ticker: str,
) -> go.Figure:
    if not price_history:
        return go.Figure()

    dates = [p["date"] for p in price_history]
    opens = [p["open"] for p in price_history]
    highs = [p["high"] for p in price_history]
    lows = [p["low"] for p in price_history]
    closes = [p["close"] for p in price_history]

    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=dates, open=opens, high=highs, low=lows, close=closes,
        name="Price",
        increasing_line_color=COLORS["accent_green"],
        decreasing_line_color=COLORS["accent_red"],
    ))

    # Bollinger Bands
    bb_upper = indicators.get("bb_upper", [])
    bb_lower = indicators.get("bb_lower", [])
    bb_middle = indicators.get("bb_middle", [])
    if bb_upper and len(bb_upper) == len(dates):
        valid_dates = [d for d, v in zip(dates, bb_upper) if v is not None]
        valid_upper = [v for v in bb_upper if v is not None]
        valid_lower = [v for d, v in zip(dates, bb_lower) if v is not None]
        valid_middle = [v for d, v in zip(dates, bb_middle) if v is not None]

        fig.add_trace(go.Scatter(x=valid_dates, y=valid_upper, mode="lines", name="BB Upper",
                                  line=dict(color="rgba(188,140,255,0.4)", width=1, dash="dot")))
        fig.add_trace(go.Scatter(x=valid_dates, y=valid_lower, mode="lines", name="BB Lower",
                                  line=dict(color="rgba(188,140,255,0.4)", width=1, dash="dot"),
                                  fill="tonexty", fillcolor="rgba(188,140,255,0.05)"))
        if valid_middle:
            fig.add_trace(go.Scatter(x=valid_dates, y=valid_middle, mode="lines", name="BB Mid",
                                      line=dict(color="rgba(188,140,255,0.3)", width=1)))

    # SMA 50 & 200
    sma_50 = indicators.get("sma_50", [])
    sma_200 = indicators.get("sma_200", [])
    if sma_50 and len(sma_50) == len(dates):
        valid = [(d, v) for d, v in zip(dates, sma_50) if v is not None]
        if valid:
            fig.add_trace(go.Scatter(x=[v[0] for v in valid], y=[v[1] for v in valid],
                                      mode="lines", name="SMA 50", line=dict(color=COLORS["accent_yellow"], width=1.5)))
    if sma_200 and len(sma_200) == len(dates):
        valid = [(d, v) for d, v in zip(dates, sma_200) if v is not None]
        if valid:
            fig.add_trace(go.Scatter(x=[v[0] for v in valid], y=[v[1] for v in valid],
                                      mode="lines", name="SMA 200", line=dict(color=COLORS["accent_orange"], width=1.5)))

    fig.update_layout(
        title=f"{ticker} — Price & Indicators",
        xaxis_rangeslider_visible=False,
        plot_bgcolor=COLORS["card"],
        paper_bgcolor=COLORS["card"],
        font=dict(color=COLORS["text"]),
        xaxis=dict(gridcolor=COLORS["card_border"]),
        yaxis=dict(gridcolor=COLORS["card_border"], title="Price ($)"),
        height=500,
        margin=dict(l=50, r=20, t=50, b=30),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
    )
    return fig


def _build_rsi_chart(indicators: dict[str, Any], dates: list[str]) -> go.Figure:
    rsi = indicators.get("rsi_14", [])
    if not rsi or len(rsi) != len(dates):
        return go.Figure()

    valid = [(d, v) for d, v in zip(dates, rsi) if v is not None]
    if not valid:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[v[0] for v in valid], y=[v[1] for v in valid],
        mode="lines", name="RSI 14",
        line=dict(color=COLORS["accent_purple"], width=2),
    ))
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS["accent_red"], annotation_text="Overbought (70)")
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS["accent_green"], annotation_text="Oversold (30)")
    fig.add_hrect(y0=30, y1=70, fillcolor="rgba(88,166,255,0.05)", line_width=0)
    fig.update_layout(
        title="RSI (14)",
        plot_bgcolor=COLORS["card"], paper_bgcolor=COLORS["card"],
        font=dict(color=COLORS["text"]),
        xaxis=dict(gridcolor=COLORS["card_border"]),
        yaxis=dict(gridcolor=COLORS["card_border"], range=[0, 100], title="RSI"),
        height=250, margin=dict(l=50, r=20, t=40, b=20),
    )
    return fig


def _build_macd_chart(indicators: dict[str, Any], dates: list[str]) -> go.Figure:
    macd_line = indicators.get("macd_line", [])
    macd_signal = indicators.get("macd_signal", [])
    macd_hist = indicators.get("macd_histogram", [])

    if not macd_line or len(macd_line) != len(dates):
        return go.Figure()

    fig = go.Figure()

    # Histogram
    valid_hist = [(d, v) for d, v in zip(dates, macd_hist) if v is not None]
    if valid_hist:
        hist_colors = [COLORS["accent_green"] if v >= 0 else COLORS["accent_red"] for _, v in valid_hist]
        fig.add_trace(go.Bar(
            x=[v[0] for v in valid_hist], y=[v[1] for v in valid_hist],
            name="Histogram", marker_color=hist_colors, opacity=0.6,
        ))

    # MACD & Signal lines
    valid_macd = [(d, v) for d, v in zip(dates, macd_line) if v is not None]
    valid_signal = [(d, v) for d, v in zip(dates, macd_signal) if v is not None]

    if valid_macd:
        fig.add_trace(go.Scatter(x=[v[0] for v in valid_macd], y=[v[1] for v in valid_macd],
                                  mode="lines", name="MACD", line=dict(color=COLORS["accent_blue"], width=2)))
    if valid_signal:
        fig.add_trace(go.Scatter(x=[v[0] for v in valid_signal], y=[v[1] for v in valid_signal],
                                  mode="lines", name="Signal", line=dict(color=COLORS["accent_orange"], width=1.5)))

    fig.update_layout(
        title="MACD (12, 26, 9)",
        plot_bgcolor=COLORS["card"], paper_bgcolor=COLORS["card"],
        font=dict(color=COLORS["text"]),
        xaxis=dict(gridcolor=COLORS["card_border"]),
        yaxis=dict(gridcolor=COLORS["card_border"], title="MACD"),
        height=250, margin=dict(l=50, r=20, t=40, b=20),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
    )
    return fig


def _build_monte_carlo_chart(simulation: dict[str, Any], ticker: str) -> go.Figure:
    sample_paths = simulation.get("sample_paths", [])
    current_price = simulation.get("current_price", 0)
    horizons = simulation.get("horizons", {})

    if not sample_paths:
        return go.Figure()

    fig = go.Figure()

    # Plot sample paths
    max_days = simulation.get("max_horizon_days", 90)
    days = list(range(1, max_days + 1))

    for i, path in enumerate(sample_paths[:30]):
        fig.add_trace(go.Scatter(
            x=days[:len(path)], y=path[:len(days)],
            mode="lines", name=f"Path {i+1}",
            line=dict(width=0.5, color="rgba(88,166,255,0.15)"),
            showlegend=False,
        ))

    # Percentile bands
    for key, data in horizons.items():
        percentiles = data.get("percentiles", {})
        day_num = data.get("days", 0)
        if percentiles:
            p5 = percentiles.get("p5", current_price)
            p50 = percentiles.get("p50", current_price)
            p95 = percentiles.get("p95", current_price)
            fig.add_trace(go.Scatter(
                x=[day_num], y=[p50], mode="markers+text",
                marker=dict(size=10, color=COLORS["accent_blue"]),
                text=[f"{key}: ${p50}"], textposition="top center",
                textfont=dict(size=10, color=COLORS["text"]),
                showlegend=False,
            ))

    # Starting price line
    fig.add_hline(y=current_price, line_dash="dash", line_color=COLORS["accent_yellow"],
                  annotation_text=f"Current: ${current_price}")

    fig.update_layout(
        title=f"{ticker} — Monte Carlo Simulation (10,000 paths)",
        plot_bgcolor=COLORS["card"], paper_bgcolor=COLORS["card"],
        font=dict(color=COLORS["text"]),
        xaxis=dict(gridcolor=COLORS["card_border"], title="Days Forward"),
        yaxis=dict(gridcolor=COLORS["card_border"], title="Price ($)"),
        height=450, margin=dict(l=50, r=20, t=50, b=40),
    )
    return fig


def _build_probability_chart(simulation: dict[str, Any]) -> go.Figure:
    horizons = simulation.get("horizons", {})
    if not horizons:
        return go.Figure()

    fig = go.Figure()
    colors = [COLORS["accent_blue"], COLORS["accent_purple"], COLORS["accent_green"]]

    for i, (key, data) in enumerate(sorted(horizons.items())):
        percentiles = data.get("percentiles", {})
        labels = list(percentiles.keys())
        values = list(percentiles.values())
        color = colors[i % len(colors)]

        fig.add_trace(go.Bar(
            x=labels, y=values, name=key,
            marker_color=color, opacity=0.8,
        ))

    fig.update_layout(
        title="Price Distribution by Horizon (Percentiles)",
        barmode="group",
        plot_bgcolor=COLORS["card"], paper_bgcolor=COLORS["card"],
        font=dict(color=COLORS["text"]),
        xaxis=dict(gridcolor=COLORS["card_border"], title="Percentile"),
        yaxis=dict(gridcolor=COLORS["card_border"], title="Price ($)"),
        height=350, margin=dict(l=50, r=20, t=50, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


# ------------------------------------------------------------------
# TradingView Widget
# ------------------------------------------------------------------
def _tradingview_widget(ticker: str, height: int = 500) -> None:
    """Embed free TradingView advanced chart widget."""
    widget_html = f"""
    <div class="tradingview-widget-container" style="height:{height}px;width:100%">
      <div id="tradingview_chart" style="height:100%;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
        new TradingView.widget({{
          "autosize": true,
          "symbol": "{ticker}",
          "interval": "D",
          "timezone": "Etc/UTC",
          "theme": "dark",
          "style": "1",
          "locale": "en",
          "toolbar_bg": "#1a1d23",
          "enable_publishing": false,
          "allow_symbol_change": true,
          "studies": ["RSI@tv-basicstudies", "MACD@tv-basicstudies", "BB@tv-basicstudies"],
          "container_id": "tradingview_chart",
          "hide_side_toolbar": false,
          "details": true,
          "calendar": false
        }});
      </script>
    </div>
    """
    components.html(widget_html, height=height + 10)


# ------------------------------------------------------------------
# Main App
# ------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="AgentTrader — AI Stock Analysis",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if "analysis_ticker" not in st.session_state:
        st.session_state["analysis_ticker"] = "AAPL"
    if "auto_run_analysis" not in st.session_state:
        st.session_state["auto_run_analysis"] = False
    if "discovered_seen_tickers" not in st.session_state:
        st.session_state["discovered_seen_tickers"] = []

    # Custom CSS
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        .stApp {{
            background-color: {COLORS["bg"]};
            font-family: 'Inter', sans-serif;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 4px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: {COLORS["card"]};
            border-radius: 8px 8px 0 0;
            padding: 8px 16px;
            color: {COLORS["text_muted"]};
        }}
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background-color: {COLORS["card"]};
            color: {COLORS["accent_blue"]};
            border-bottom: 2px solid {COLORS["accent_blue"]};
        }}
        .stMetric > div {{
            background-color: {COLORS["card"]};
            border: 1px solid {COLORS["card_border"]};
            border-radius: 10px;
            padding: 12px;
        }}
        div[data-testid="stExpander"] {{
            background-color: {COLORS["card"]};
            border: 1px solid {COLORS["card_border"]};
            border-radius: 10px;
        }}
        .hero-card {{
            padding: 1.2rem 1.5rem;
            border-radius: 14px;
            background: linear-gradient(125deg, {COLORS["gradient_start"]} 0%, {COLORS["gradient_end"]} 100%);
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 8px 32px rgba(8, 42, 79, 0.35);
        }}
        .hero-card h1 {{
            margin: 0; font-size: 2rem; letter-spacing: 0.3px; font-weight: 800;
        }}
        .hero-card p {{
            margin: 0.3rem 0 0; opacity: 0.92; font-size: 0.95rem;
        }}
        .rec-badge {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 16px 24px;
            border-radius: 14px;
            font-size: 1.8rem;
            font-weight: 800;
            letter-spacing: 1px;
        }}
        .conviction-tag {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-left: 12px;
        }}
        .signal-card {{
            padding: 10px 16px;
            border-radius: 10px;
            border-left: 4px solid;
            margin-bottom: 8px;
            font-size: 0.9rem;
        }}
        .signal-bullish {{ border-color: {COLORS["accent_green"]}; background: rgba(63,185,80,0.08); color: {COLORS["accent_green"]}; }}
        .signal-bearish {{ border-color: {COLORS["accent_red"]}; background: rgba(248,81,73,0.08); color: {COLORS["accent_red"]}; }}
        .signal-neutral {{ border-color: {COLORS["accent_yellow"]}; background: rgba(210,153,34,0.08); color: {COLORS["accent_yellow"]}; }}
    </style>
    """, unsafe_allow_html=True)

    # Hero
    st.markdown("""
    <div class="hero-card">
        <h1>🤖 AgentTrader</h1>
        <p>Multi-Agent AI Stock Research · Technical Analysis · Monte Carlo Probability · Institutional Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        api_url = st.text_input("Backend URL", value=DEFAULT_API_URL)
        use_cache = st.checkbox("Use cache", value=True)
        set_max_age = st.checkbox("Set max cache age", value=False)
        max_age: int | None = None
        if set_max_age:
            max_age = st.number_input("Max cache age (hours)", min_value=1, value=24, step=1)

        st.divider()
        st.markdown("### 📋 Quick Watchlist")
        watchlist = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD"]
        selected_watchlist = st.selectbox("Quick pick:", [""] + watchlist)

        st.divider()
        st.markdown("### 📊 Compare Stocks")
        compare_input = st.text_input("Tickers (comma-separated):", placeholder="AAPL, TSLA, NVDA")
        compare_btn = st.button("Compare", use_container_width=True)

    # Main input
    st.markdown("### 🔎 Discover New Stocks")
    discover_col1, discover_col2 = st.columns([1, 3], vertical_alignment="center")
    with discover_col1:
        discover_now = st.button("Discover", use_container_width=True)
    with discover_col2:
        st.caption("Generate 3-5 fresh ticker ideas from market-wide context and jump directly into analysis.")

    if discover_now:
        with st.spinner("Discovering stock ideas..."):
            try:
                seen_tickers = [
                    str(t).strip().upper()
                    for t in st.session_state.get("discovered_seen_tickers", [])
                    if str(t).strip()
                ]
                st.session_state["discover_data"] = _request_discovery(api_url, max_age, seen_tickers)
                st.session_state["discover_error"] = ""

                new_suggestions = st.session_state["discover_data"].get("suggestions") or []
                for suggestion in new_suggestions:
                    ticker_symbol = str(suggestion.get("ticker") or "").strip().upper()
                    if ticker_symbol and ticker_symbol not in st.session_state["discovered_seen_tickers"]:
                        st.session_state["discovered_seen_tickers"].append(ticker_symbol)
            except httpx.HTTPStatusError as exc:
                st.session_state["discover_data"] = None
                st.session_state["discover_error"] = f"API error ({exc.response.status_code}): {exc.response.text}"
            except httpx.HTTPError as exc:
                st.session_state["discover_data"] = None
                st.session_state["discover_error"] = f"Connection error: {exc}"
            except Exception as exc:
                st.session_state["discover_data"] = None
                st.session_state["discover_error"] = f"Unexpected error: {exc}"

    discover_error = st.session_state.get("discover_error")
    discover_data = st.session_state.get("discover_data")

    if discover_error:
        st.error(discover_error)
    elif discover_data:
        st.caption(
            f"Discover model: `{discover_data.get('model', 'N/A')}` · "
            f"Latency: `{discover_data.get('latency_ms', 0)}ms` · "
            f"Fetched: `{str(discover_data.get('fetched_at', 'N/A'))[:19]}`"
        )
        summary = str(discover_data.get("summary") or "").strip()
        if summary:
            st.write(summary)

        suggestions = discover_data.get("suggestions") or []
        if not suggestions:
            st.warning("No discovery suggestions available right now.")
        else:
            cards = st.columns(min(3, len(suggestions)))
            for idx, item in enumerate(suggestions):
                with cards[idx % len(cards)]:
                    ticker_symbol = str(item.get("ticker") or "").strip().upper()
                    company_name = str(item.get("company_name") or ticker_symbol)
                    reason = str(item.get("reason") or "")
                    try:
                        confidence = float(item.get("confidence") or 0.0)
                    except (TypeError, ValueError):
                        confidence = 0.0

                    st.markdown(
                        f"""
                        <div style="padding: 0.8rem; border-radius: 10px; border: 1px solid {COLORS['card_border']}; background: {COLORS['card']}; min-height: 170px; margin-bottom: 0.5rem;">
                            <div style="font-size: 1rem; font-weight: 700; color: {COLORS['accent_blue']};">{escape(ticker_symbol)}</div>
                            <div style="font-size: 0.85rem; color: {COLORS['text_muted']}; margin-bottom: 0.4rem;">{escape(company_name)}</div>
                            <div style="font-size: 0.85rem; color: {COLORS['text']};">{escape(reason)}</div>
                            <div style="margin-top: 0.5rem; font-size: 0.8rem; color: {COLORS['text_muted']};">Confidence: {confidence:.0%}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if ticker_symbol and st.button(
                        f"Analyze {ticker_symbol}",
                        key=f"discover-analyze-{ticker_symbol}-{idx}",
                        use_container_width=True,
                    ):
                        st.session_state["analysis_ticker"] = ticker_symbol
                        st.session_state["auto_run_analysis"] = True
                        st.rerun()

    col_input, col_btn = st.columns([3, 1], vertical_alignment="bottom")
    with col_input:
        if selected_watchlist:
            st.session_state["analysis_ticker"] = selected_watchlist
        ticker = st.text_input("Enter Stock Ticker:", key="analysis_ticker", max_chars=12).strip().upper()
    with col_btn:
        run = st.button("🔍 Analyze", use_container_width=True, type="primary")

    auto_run = bool(st.session_state.get("auto_run_analysis"))
    if auto_run:
        st.session_state["auto_run_analysis"] = False

    # --- Compare Mode ---
    if compare_btn and compare_input:
        tickers = [t.strip().upper() for t in compare_input.split(",") if t.strip()]
        if tickers:
            with st.spinner(f"Comparing {', '.join(tickers)}..."):
                try:
                    compare_data = _request_compare(api_url, tickers, use_cache)
                    _render_comparison(compare_data)
                except Exception as exc:
                    st.error(f"Comparison failed: {exc}")
            return

    # --- Analysis Mode ---
    if not (run or auto_run):
        st.info("Enter a ticker and click **Analyze** to begin, or use the Quick Watchlist in the sidebar.")
        return

    if not ticker:
        st.error("Ticker cannot be empty.")
        return

    with st.spinner(f"Running 5-agent analysis on {ticker}..."):
        try:
            data = _request_analysis(api_url, ticker, use_cache, max_age)
        except httpx.HTTPStatusError as exc:
            st.error(f"API error ({exc.response.status_code}): {exc.response.text}")
            return
        except httpx.HTTPError as exc:
            st.error(f"Connection error: {exc}")
            return
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")
            return

    _render_analysis(data, ticker, api_url)


# ------------------------------------------------------------------
# Render: Full Analysis
# ------------------------------------------------------------------
def _render_analysis(data: dict[str, Any], ticker: str, api_url: str) -> None:
    result = data.get("result", {})
    breakdown = result.get("score_breakdown", {})
    indicators = data.get("technical_indicators", {})
    simulation = data.get("monte_carlo", {})
    analyst_targets = data.get("analyst_targets", {})

    recommendation = str(result.get("recommendation") or "N/A")
    conviction = str(result.get("conviction") or "N/A")
    confidence = float(result.get("confidence") or 0.0)
    latency_ms = int(data.get("latency_ms") or 0)

    rec_style = REC_STYLES.get(recommendation, {"color": "#8b949e", "bg": "rgba(139,148,158,0.1)", "icon": "❓"})

    # Recommendation Badge
    st.markdown(f"""
    <div style="text-align: center; margin: 0.5rem 0 1rem;">
        <span class="rec-badge" style="color: {rec_style['color']}; background: {rec_style['bg']};">
            {rec_style['icon']} {recommendation}
        </span>
        <span class="conviction-tag" style="color: {rec_style['color']}; background: {rec_style['bg']};">
            {conviction} CONVICTION
        </span>
    </div>
    <div style="text-align: center; color: {COLORS['text_muted']}; font-size: 0.9rem; margin-bottom: 1rem;">
        {data.get('company_name', ticker)} · {data.get('sector', '')} · {data.get('industry', '')}
    </div>
    """, unsafe_allow_html=True)

    # Score metrics row
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Confidence", f"{confidence:.0%}")
    m2.metric("📰 News", f"{breakdown.get('news_component', 0):.0%}")
    m3.metric("💰 Financial", f"{breakdown.get('financial_component', 0):.0%}")
    m4.metric("⚠️ Risk (inv)", f"{breakdown.get('risk_component', 0):.0%}")
    m5.metric("📊 Technical", f"{breakdown.get('technical_component', 0):.0%}")
    m6.metric("🏦 Macro", f"{breakdown.get('macro_component', 0):.0%}")

    st.caption(
        f"Model: `{data.get('model', 'N/A')}` · Latency: `{latency_ms}ms` · "
        f"Price: `${data.get('current_price', 'N/A')}` · Fetched: `{data.get('fetched_at', 'N/A')[:19]}`"
    )

    # Tabs
    tab_overview, tab_tv, tab_tech, tab_prob, tab_fundamentals, tab_risk = st.tabs([
        "📋 Overview", "📺 TradingView", "📊 Technical", "🎯 Probability", "💰 Fundamentals", "⚠️ Risk & Macro"
    ])

    # ------ Tab: Overview ------
    with tab_overview:
        col_radar, col_rationale = st.columns([1, 2])

        with col_radar:
            st.plotly_chart(_build_radar_chart(breakdown), use_container_width=True)

        with col_rationale:
            st.markdown("#### 📝 Rationale")
            rationale = result.get("rationale", [])
            for item in rationale:
                st.write(f"• {item}")

        # Agent summaries in expanders
        st.markdown("#### 🤖 Agent Reports")
        col_a, col_b = st.columns(2)
        with col_a:
            with st.expander("📰 News Analysis", expanded=False):
                news = result.get("news_analysis", {})
                st.write(f"**Sentiment:** {news.get('sentiment', 'N/A')} ({news.get('sentiment_score', 0):.0%})")
                st.write(f"**Summary:** {news.get('summary', '')}")
                if news.get("key_events"):
                    st.write("**Key Events:**")
                    for ev in news["key_events"]:
                        st.write(f"  - {ev}")

            with st.expander("📊 Technical Analysis", expanded=False):
                tech = result.get("technical_analysis", {})
                st.write(f"**Trend:** {tech.get('trend', 'N/A')} ({tech.get('signal_score', 0):.0%})")
                st.write(f"**Pattern:** {tech.get('pattern_description', '')}")
                st.write(f"**Summary:** {tech.get('summary', '')}")

        with col_b:
            with st.expander("💰 Financial Analysis", expanded=False):
                fin = result.get("financial_analysis", {})
                st.write(f"**Health Score:** {fin.get('health_score', 0):.0%}")
                st.write(f"**Summary:** {fin.get('summary', '')}")
                if fin.get("strengths"):
                    st.write("**Strengths:** " + ", ".join(fin["strengths"]))
                if fin.get("weaknesses"):
                    st.write("**Weaknesses:** " + ", ".join(fin["weaknesses"]))

            with st.expander("🏦 Macro / Institutional", expanded=False):
                macro = result.get("macro_analysis", {})
                st.write(f"**Score:** {macro.get('macro_score', 0):.0%}")
                st.write(f"**Institutional:** {macro.get('institutional_sentiment', 'N/A')}")
                st.write(f"**Insider Signal:** {macro.get('insider_signal', 'N/A')}")
                st.write(f"**Summary:** {macro.get('summary', '')}")

    # ------ Tab: TradingView ------
    with tab_tv:
        st.markdown("#### 📺 TradingView Live Chart")
        st.caption("Interactive chart powered by TradingView (free widget). Includes RSI, MACD, and Bollinger Bands.")
        _tradingview_widget(ticker, height=550)

    # ------ Tab: Technical ------
    with tab_tech:
        # price_history is now included directly in the /analyze response
        raw_history = data.get("price_history", [])

        if raw_history:
            dates = [p["date"] for p in raw_history]
            st.plotly_chart(_build_candlestick_chart(raw_history, indicators, ticker), use_container_width=True)

            col_rsi, col_macd = st.columns(2)
            with col_rsi:
                st.plotly_chart(_build_rsi_chart(indicators, dates), use_container_width=True)
            with col_macd:
                st.plotly_chart(_build_macd_chart(indicators, dates), use_container_width=True)
        else:
            st.info("Price history not available for chart rendering.")

        # Signal Cards
        signals = indicators.get("signals", [])
        if signals:
            st.markdown("#### 🔔 Active Signals")
            sig_cols = st.columns(min(len(signals), 3))
            for i, sig in enumerate(signals):
                direction = sig.get("direction", "neutral")
                css_class = f"signal-{direction}"
                with sig_cols[i % len(sig_cols)]:
                    st.markdown(f"""
                    <div class="signal-card {css_class}">
                        <strong>{sig.get('indicator', '')}</strong><br/>
                        {sig.get('signal', '')}<br/>
                        <small>{sig.get('value', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)

        # Snapshot table
        snapshot = indicators.get("snapshot", {})
        if snapshot:
            st.markdown("#### 📐 Indicator Snapshot")
            snap_cols = st.columns(4)
            snap_items = [
                ("Current Price", snapshot.get("current_price")),
                ("RSI (14)", snapshot.get("rsi_14")),
                ("SMA 20", snapshot.get("sma_20")),
                ("SMA 50", snapshot.get("sma_50")),
                ("SMA 200", snapshot.get("sma_200")),
                ("EMA 20", snapshot.get("ema_20")),
                ("ATR (14)", snapshot.get("atr_14")),
                ("MACD", snapshot.get("macd_line")),
            ]
            for i, (label, val) in enumerate(snap_items):
                with snap_cols[i % 4]:
                    display = f"${val:.2f}" if val is not None and label in ("Current Price", "SMA 20", "SMA 50", "SMA 200", "EMA 20", "ATR (14)") else (f"{val:.2f}" if val is not None else "N/A")
                    st.metric(label, display)

    # ------ Tab: Probability ------
    with tab_prob:
        if simulation and "error" not in simulation:
            st.plotly_chart(_build_monte_carlo_chart(simulation, ticker), use_container_width=True)
            st.plotly_chart(_build_probability_chart(simulation), use_container_width=True)

            # Probability table
            st.markdown("#### 📊 Probability Table")
            horizons = simulation.get("horizons", {})
            for key, hdata in sorted(horizons.items()):
                with st.expander(f"📅 {key} Horizon", expanded=(key == "30d")):
                    p_cols = st.columns(5)
                    p_cols[0].metric("Mean Price", f"${hdata.get('mean_price', 0):.2f}")
                    p_cols[1].metric("P(Up)", f"{hdata.get('prob_positive', 0):.0%}")
                    p_cols[2].metric("P(Up >5%)", f"{hdata.get('prob_up_5pct', 0):.0%}")
                    p_cols[3].metric("P(Up >10%)", f"{hdata.get('prob_up_10pct', 0):.0%}")
                    p_cols[4].metric("P(Down >10%)", f"{hdata.get('prob_down_10pct', 0):.0%}")

            # VaR
            var_data = simulation.get("value_at_risk", {})
            if var_data:
                st.markdown("#### 🛡️ Value at Risk (VaR)")
                var_cols = st.columns(len(var_data))
                for i, (key, vdata) in enumerate(sorted(var_data.items())):
                    with var_cols[i]:
                        st.metric(f"{key} VaR (95%)", f"{vdata.get('var_95', 0):.1f}%")
                        st.caption(f"99%: {vdata.get('var_99', 0):.1f}% (${vdata.get('var_99_dollar', 0):.2f})")

            # Target probabilities
            target_probs = simulation.get("target_probabilities", {})
            if target_probs:
                st.markdown("#### 🎯 Analyst Target Probabilities (90d)")
                tp_cols = st.columns(len(target_probs))
                for i, (label, tdata) in enumerate(target_probs.items()):
                    with tp_cols[i]:
                        st.metric(
                            f"{label.title()} Target",
                            f"${tdata.get('target_price', 0):.2f}",
                        )
                        st.caption(f"Probability: {tdata.get('probability_pct', 'N/A')}")

            st.caption(f"Annualised Volatility: {simulation.get('annualised_volatility', 0):.1f}% · Simulations: {simulation.get('num_simulations', 0):,}")
        else:
            st.info("Monte Carlo simulation data not available.")

    # ------ Tab: Fundamentals ------
    with tab_fundamentals:
        if analyst_targets:
            st.markdown("#### 🎯 Analyst Consensus")
            at_cols = st.columns(4)
            at_cols[0].metric("Target Low", f"${analyst_targets.get('target_low') or 'N/A'}")
            at_cols[1].metric("Target Mean", f"${analyst_targets.get('target_mean') or 'N/A'}")
            at_cols[2].metric("Target High", f"${analyst_targets.get('target_high') or 'N/A'}")
            at_cols[3].metric("Analysts", str(analyst_targets.get("num_analysts", "N/A")))

        st.markdown("#### 💰 Financial Metrics")
        fin_analysis = result.get("financial_analysis", {})
        risk_analysis = result.get("risk_analysis", {})

        with st.expander("Full Financial Data", expanded=True):
            st.json(data.get("result", {}).get("financial_analysis", {}))

        with st.expander("Risk Data"):
            st.json(data.get("result", {}).get("risk_analysis", {}))

    # ------ Tab: Risk & Macro ------
    with tab_risk:
        macro_analysis = result.get("macro_analysis", {})

        st.markdown("#### 🏦 Institutional & Insider Intelligence")

        col_inst, col_ins = st.columns(2)
        with col_inst:
            st.write(f"**Institutional Sentiment:** {macro_analysis.get('institutional_sentiment', 'N/A')}")
            st.write(f"**Sector Outlook:** {macro_analysis.get('sector_outlook', 'N/A')}")

        with col_ins:
            st.write(f"**Insider Signal:** {macro_analysis.get('insider_signal', 'N/A')}")
            st.write(f"**Macro Score:** {macro_analysis.get('macro_score', 0):.0%}")

        if macro_analysis.get("key_observations"):
            st.markdown("**Key Observations:**")
            for obs in macro_analysis["key_observations"]:
                st.write(f"  • {obs}")

        st.write(f"**Summary:** {macro_analysis.get('summary', 'N/A')}")

        # Risk factors
        risk_data = result.get("risk_analysis", {})
        if risk_data.get("risk_factors"):
            st.markdown("#### ⚠️ Risk Factors")
            for rf in risk_data["risk_factors"]:
                st.write(f"  ⚡ {rf}")


# ------------------------------------------------------------------
# Render: Comparison
# ------------------------------------------------------------------
def _render_comparison(data: dict[str, Any]) -> None:
    items = data.get("items", [])
    latency = data.get("latency_ms", 0)

    if not items:
        st.warning("No comparison data returned.")
        return

    st.markdown("### 📊 Stock Comparison")
    st.caption(f"Analysis completed in {latency}ms")

    # Comparison table
    for item in items:
        rec = item.get("recommendation", "N/A")
        rec_style = REC_STYLES.get(rec, {"color": "#8b949e", "bg": "rgba(139,148,158,0.1)", "icon": "❓"})

        st.markdown(f"""
        <div style="padding: 12px 16px; border-radius: 10px; border: 1px solid {COLORS['card_border']};
                    background: {COLORS['card']}; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
            <div>
                <span style="font-size: 1.1rem; font-weight: 700; color: {COLORS['text']};">{item['ticker']}</span>
                <span style="color: {COLORS['text_muted']}; margin-left: 8px;">{item.get('company_name', '')}</span>
                <span style="color: {COLORS['text_muted']}; margin-left: 8px;">· {item.get('sector', '')}</span>
            </div>
            <div>
                <span style="font-size: 0.85rem; color: {COLORS['text_muted']};">
                    ${item.get('current_price', 'N/A')} ·
                    N:{item.get('news_score', 0):.0%}
                    F:{item.get('financial_score', 0):.0%}
                    R:{item.get('risk_score', 0):.0%}
                    T:{item.get('technical_score', 0):.0%}
                    M:{item.get('macro_score', 0):.0%}
                </span>
                <span class="rec-badge" style="color: {rec_style['color']}; background: {rec_style['bg']};
                       font-size: 0.9rem; padding: 6px 14px; margin-left: 12px;">
                    {rec_style['icon']} {rec} · {item.get('conviction', '')}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
