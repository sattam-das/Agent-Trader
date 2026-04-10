"""SQLite database layer for persistent storage.

Stores watchlists, trade journal entries, portfolio holdings, and app settings.
Uses synchronous sqlite3 (called via asyncio.to_thread from FastAPI endpoints).
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Optional


DB_PATH = os.path.join("data", "agenttrader.db")


def _ensure_db() -> None:
    """Create tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL UNIQUE,
            added_at TEXT NOT NULL DEFAULT (datetime('now')),
            notes TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            side TEXT NOT NULL CHECK(side IN ('LONG', 'SHORT')),
            entry_price REAL NOT NULL,
            exit_price REAL,
            shares INTEGER NOT NULL DEFAULT 1,
            entry_date TEXT NOT NULL,
            exit_date TEXT,
            pnl REAL,
            return_pct REAL,
            notes TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN', 'CLOSED')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            shares REAL NOT NULL,
            avg_price REAL NOT NULL,
            added_at TEXT NOT NULL DEFAULT (datetime('now')),
            notes TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# Ensure tables exist on module import
_ensure_db()


# ------------------------------------------------------------------
# Watchlist
# ------------------------------------------------------------------
def watchlist_add(ticker: str, notes: str = "") -> dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (ticker, notes) VALUES (?, ?)",
            (ticker.upper(), notes),
        )
        conn.commit()
        return {"status": "ok", "ticker": ticker.upper()}
    finally:
        conn.close()


def watchlist_remove(ticker: str) -> dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker.upper(),))
        conn.commit()
        return {"status": "ok", "ticker": ticker.upper()}
    finally:
        conn.close()


def watchlist_list() -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM watchlist ORDER BY added_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ------------------------------------------------------------------
# Trade Journal
# ------------------------------------------------------------------
def journal_add(
    ticker: str,
    side: str,
    entry_price: float,
    shares: int,
    entry_date: str,
    notes: str = "",
) -> dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.execute(
            """INSERT INTO journal (ticker, side, entry_price, shares, entry_date, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ticker.upper(), side.upper(), entry_price, shares, entry_date, notes),
        )
        conn.commit()
        return {"status": "ok", "id": c.lastrowid}
    finally:
        conn.close()


def journal_close(
    trade_id: int,
    exit_price: float,
    exit_date: str,
) -> dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM journal WHERE id = ?", (trade_id,)).fetchone()
        if not row:
            return {"error": "Trade not found"}

        entry_price = row["entry_price"]
        shares = row["shares"]
        side = row["side"]

        if side == "LONG":
            pnl = (exit_price - entry_price) * shares
        else:
            pnl = (entry_price - exit_price) * shares

        return_pct = pnl / (entry_price * shares)

        conn.execute(
            """UPDATE journal SET exit_price = ?, exit_date = ?, pnl = ?,
               return_pct = ?, status = 'CLOSED' WHERE id = ?""",
            (exit_price, exit_date, round(pnl, 2), round(return_pct, 4), trade_id),
        )
        conn.commit()
        return {"status": "ok", "pnl": round(pnl, 2), "return_pct": round(return_pct, 4)}
    finally:
        conn.close()


def journal_list(status: Optional[str] = None) -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM journal WHERE status = ? ORDER BY created_at DESC",
                (status.upper(),),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM journal ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def journal_stats() -> dict[str, Any]:
    """Compute journal performance statistics."""
    trades = journal_list(status="CLOSED")
    if not trades:
        return {"total_trades": 0}

    returns = [t["return_pct"] or 0.0 for t in trades]
    pnls = [t["pnl"] or 0.0 for t in trades]
    winners = [r for r in returns if r > 0]
    losers = [r for r in returns if r <= 0]

    return {
        "total_trades": len(trades),
        "win_rate": round(len(winners) / len(trades), 4) if trades else 0,
        "total_pnl": round(sum(pnls), 2),
        "avg_return": round(sum(returns) / len(returns), 4) if returns else 0,
        "best_trade": round(max(returns), 4) if returns else 0,
        "worst_trade": round(min(returns), 4) if returns else 0,
        "avg_winner": round(sum(winners) / len(winners), 4) if winners else 0,
        "avg_loser": round(sum(losers) / len(losers), 4) if losers else 0,
        "consecutive_wins": _max_streak(returns, positive=True),
        "consecutive_losses": _max_streak(returns, positive=False),
    }


def journal_delete(trade_id: int) -> dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM journal WHERE id = ?", (trade_id,))
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()


# ------------------------------------------------------------------
# Portfolio
# ------------------------------------------------------------------
def portfolio_add(ticker: str, shares: float, avg_price: float, notes: str = "") -> dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.execute(
            "INSERT INTO portfolio (ticker, shares, avg_price, notes) VALUES (?, ?, ?, ?)",
            (ticker.upper(), shares, avg_price, notes),
        )
        conn.commit()
        return {"status": "ok", "id": c.lastrowid}
    finally:
        conn.close()


def portfolio_remove(holding_id: int) -> dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM portfolio WHERE id = ?", (holding_id,))
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()


def portfolio_list() -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM portfolio ORDER BY added_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _max_streak(returns: list[float], positive: bool = True) -> int:
    """Count the longest consecutive win/loss streak."""
    max_s = current = 0
    for r in returns:
        if (positive and r > 0) or (not positive and r <= 0):
            current += 1
            max_s = max(max_s, current)
        else:
            current = 0
    return max_s
