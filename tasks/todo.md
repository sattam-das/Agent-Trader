- [x] Add discovery market-context fetch in `backend/utils/data_fetcher.py` with cache + fallback.
- [x] Add discovery schemas and new `backend/agents/discovery_agent.py`.
- [x] Register discovery agent in `backend/agents/__init__.py`.
- [x] Add `GET /discover` endpoint in `backend/main.py`.
- [x] Integrate discovery UI and one-click analyze handoff in `frontend/app.py`.
- [x] Verify `/discover` and `/analyze` behavior and update `tasks/task.md` checkboxes + review notes.

## Review

- Implemented market-wide discovery context in `DataFetcher` with cache support (`MARKET_DISCOVERY.json`) and dual-source news fallback (NewsAPI -> Google News RSS).
- Added discovery domain models (`DiscoverySuggestion`, `DiscoveryAnalysis`) and new `DiscoveryAgent` with normalization, dedupe, and fallback ticker continuity.
- Registered discovery types/agent in `backend/agents/__init__.py` and exposed `GET /discover` in `backend/main.py` with clear error mapping.
- Integrated discovery UX in Streamlit (`frontend/app.py`) with discover action, suggestion cards, safe text escaping, and one-click auto-analyze handoff.
- Validation:
  - `python -m compileall backend frontend` passed.
  - Discovery smoke: `discover_stocks(use_cache=True, max_cache_age_hours=6)` returned 3 suggestions.
  - Backward compatibility smoke: `analyze_stock(AnalyzeRequest(ticker='AAPL'))` returned `HOLD`.

## Incremental Update

- Implemented fresh-on-click discovery behavior:
  - Frontend now calls `/discover` with `use_cache=false` on every Discover click.
  - Frontend persists `discovered_seen_tickers` in session state and passes them as `exclude_tickers` query params.
  - Backend `/discover` now accepts `exclude_tickers` and forwards exclusions to `DiscoveryAgent`.
  - `DiscoveryAgent` now enforces exclusions across model outputs and fallback ticker sources.
- Validation:
  - Consecutive `/discover` handler calls produced non-overlapping suggestions (`overlap []`).
  - `/analyze` behavior remains backward compatible (`AAPL -> HOLD`).
