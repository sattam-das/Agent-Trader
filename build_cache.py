from __future__ import annotations

import os
from typing import Iterable

from dotenv import load_dotenv

from backend.utils.data_fetcher import DataFetcher


DEMO_TICKERS = [
    "AAPL",
    "TSLA",
    "NVDA",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "NFLX",
    "AMD",
    "INTC",
]


def build_cache(tickers: Iterable[str], ttl_hours: int | None = None) -> tuple[int, int]:
    load_dotenv()
    fetcher = DataFetcher(os.getenv("NEWS_API_KEY"), cache_dir="data/cache")

    success_count = 0
    failure_count = 0

    for ticker in tickers:
        symbol = ticker.strip().upper()
        if not symbol:
            continue

        print(f"Fetching data for {symbol}...")
        try:
            fetcher.get_stock_data(
                symbol,
                use_cache=False,
                max_cache_age_hours=ttl_hours,
            )
            success_count += 1
            print(f"OK Cached {symbol}")
        except Exception as exc:
            failure_count += 1
            print(f"FAIL {symbol}: {exc}")

    return success_count, failure_count


if __name__ == "__main__":
    ttl_env = os.getenv("CACHE_TTL_HOURS")
    ttl_hours: int | None = int(ttl_env) if ttl_env else None

    success, failure = build_cache(DEMO_TICKERS, ttl_hours=ttl_hours)
    total = success + failure
    print("\nCache build complete")
    print(f"Total: {total}")
    print(f"Success: {success}")
    print(f"Failed: {failure}")
