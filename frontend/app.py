from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st


DEFAULT_API_URL = os.getenv("AGENT_TRADER_API_URL", "http://127.0.0.1:8000")


def _render_metric(label: str, value: float) -> None:
    st.metric(label, f"{value:.2f}")


def _render_analysis_section(title: str, payload: dict[str, Any]) -> None:
    with st.expander(title, expanded=False):
        st.json(payload)


def _request_analysis(api_url: str, ticker: str, use_cache: bool, max_age: int | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ticker": ticker,
        "use_cache": use_cache,
    }
    if max_age is not None:
        payload["max_cache_age_hours"] = max_age

    with httpx.Client(timeout=30.0) as client:
        response = client.post(f"{api_url.rstrip('/')}/analyze", json=payload)

    response.raise_for_status()
    return response.json()


def main() -> None:
    st.set_page_config(page_title="AgentTrader", page_icon="📈", layout="wide")

    st.markdown(
        """
        <style>
            .stApp {
                background: radial-gradient(circle at top left, #f9fbff 0%, #eef4ff 45%, #e8f0fd 100%);
            }
            .hero {
                padding: 1rem 1.25rem;
                border-radius: 14px;
                background: linear-gradient(115deg, #0b3a6e 0%, #145da0 45%, #1f8cc3 100%);
                color: #ffffff;
                margin-bottom: 1rem;
                box-shadow: 0 8px 24px rgba(8, 42, 79, 0.22);
            }
            .hero h1 {
                margin: 0;
                font-size: 2rem;
                letter-spacing: 0.2px;
            }
            .hero p {
                margin: 0.3rem 0 0;
                opacity: 0.92;
            }
        </style>
        <div class="hero">
            <h1>AgentTrader</h1>
            <p>AI-assisted stock sentiment, financial health, and risk scoring in one view.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.subheader("Connection")
        api_url = st.text_input("Backend URL", value=DEFAULT_API_URL)

        st.subheader("Analysis Settings")
        use_cache = st.checkbox("Use cache", value=True)
        set_max_age = st.checkbox("Set max cache age", value=False)
        max_age: int | None = None
        if set_max_age:
            max_age = st.number_input("Max cache age (hours)", min_value=1, value=24, step=1)

    left, right = st.columns([2, 1], vertical_alignment="bottom")
    with left:
        ticker = st.text_input("Ticker", value="AAPL", max_chars=12).strip().upper()
    with right:
        run = st.button("Run analysis", use_container_width=True, type="primary")

    if not run:
        st.info("Enter a ticker and click Run analysis.")
        return

    if not ticker:
        st.error("Ticker cannot be empty.")
        return

    with st.spinner(f"Analyzing {ticker}..."):
        try:
            data = _request_analysis(api_url, ticker, use_cache, max_age)
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text
            st.error(f"API error ({exc.response.status_code}): {detail}")
            return
        except httpx.HTTPError as exc:
            st.error(f"Connection error: {exc}")
            return
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")
            return

    result = data.get("result", {})
    breakdown = result.get("score_breakdown", {})

    recommendation = str(result.get("recommendation") or "N/A")
    confidence = float(result.get("confidence") or 0.0)
    latency_ms = int(data.get("latency_ms") or 0)

    rec_color = {
        "BUY": "#0f7a4f",
        "HOLD": "#8a6d00",
        "SELL": "#9c1f1f",
    }.get(recommendation, "#334155")

    st.markdown(
        f"""
        <div style="padding: 0.9rem 1rem; border-radius: 12px; border: 1px solid #d6e4ff; background: #ffffff; margin-bottom: 0.75rem;">
            <div style="font-size: 0.9rem; color: #475569;">Recommendation</div>
            <div style="font-size: 1.7rem; font-weight: 700; color: {rec_color};">{recommendation}</div>
            <div style="font-size: 0.9rem; color: #334155;">{data.get('company_name', ticker)} · {data.get('ticker', ticker)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_cols = st.columns(4)
    with metric_cols[0]:
        _render_metric("Confidence", confidence)
    with metric_cols[1]:
        _render_metric("News", float(breakdown.get("news_component") or 0.0))
    with metric_cols[2]:
        _render_metric("Financial", float(breakdown.get("financial_component") or 0.0))
    with metric_cols[3]:
        _render_metric("Risk (inverted)", float(breakdown.get("risk_component") or 0.0))

    st.caption(f"Model: {data.get('model', 'N/A')} · Latency: {latency_ms} ms · Fetched at: {data.get('fetched_at', 'N/A')}")

    rationale = result.get("rationale") or []
    if rationale:
        st.subheader("Rationale")
        for item in rationale:
            st.write(f"- {item}")

    st.subheader("Agent Output Details")
    _render_analysis_section("News Analysis", result.get("news_analysis") or {})
    _render_analysis_section("Financial Analysis", result.get("financial_analysis") or {})
    _render_analysis_section("Risk Analysis", result.get("risk_analysis") or {})


if __name__ == "__main__":
    main()
