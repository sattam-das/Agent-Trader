# AgentTrader Task Tracker

## Phase 6: Proactive Stock Discovery
- [x] **Step 16:** Extend data layer in `backend/utils/data_fetcher.py` with market-wide news fetch method for discovery input.
- [x] **Step 17:** Create `backend/agents/discovery_agent.py` to suggest 3-5 new tickers from current market/news context.
- [x] **Step 18:** Update `backend/agents/base_agent.py` with discovery response schema validation models.
- [x] **Step 19:** Register discovery agent in `backend/agents/__init__.py`.
- [x] **Step 20:** Add `GET /discover` endpoint in `backend/main.py` to return AI-generated stock suggestions.
- [x] **Step 21:** Update frontend `frontend/app.py` with a "Discover New Stocks" section and suggestion cards.
- [x] **Step 22:** Add one-click "Analyze" action from discovered stock into existing analysis flow.
- [x] **Step 23:** Add API and UI error handling states for discovery failures and empty suggestions.
- [x] **Step 24:** Run end-to-end verification for `/discover` and existing `/analyze` behavior.

### Phase 6 Review (To Be Filled After Implementation)
- Discovery data path now supports market-wide context with NewsAPI-first retrieval and Google News RSS fallback, plus cache-backed continuity via `MARKET_DISCOVERY.json`.
- Discovery agent implemented with strict schema validation, output normalization, deduplication, and deterministic fallback candidates to always return 3-5 suggestions when possible.
- Frontend now includes discovery cards and one-click analyze handoff into the primary analysis flow, with API/connection/unexpected error handling and empty-state feedback.
- Verification complete: compile check passed (`python -m compileall backend frontend`), `/discover` handler smoke test returned 3 suggestions, and existing `/analyze` flow remained functional (`AAPL -> HOLD`).

## Phase 6.1: Fresh Discovery Per Click
- [x] Update `GET /discover` to accept `exclude_tickers` and filter repeated suggestions.
- [x] Update discovery agent to enforce exclusion list while preserving 3-5 suggestion continuity.
- [x] Update frontend discover action to always request fresh data (`use_cache=false`) and pass session `exclude_tickers`.
- [x] Persist session seen tickers and append newly discovered symbols after each discover click.
- [x] Verify consecutive discovery calls return non-overlapping suggestion sets when alternatives are available.

### Phase 6.1 Review
- Added query-level `exclude_tickers` support in `backend/main.py` and wired through to discovery agent analysis.
- Discovery agent now excludes prior symbols at model-output and fallback stages, preventing repeats in normal flows.
- Frontend discover button now bypasses discovery cache and sends accumulated session exclusions so each click surfaces fresh candidates.
- Verified with back-to-back discovery calls (`use_cache=False`) that first and second suggestion sets had zero overlap.
