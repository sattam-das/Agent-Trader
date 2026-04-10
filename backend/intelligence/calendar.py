"""Economic Calendar — curated high-impact events for India & US markets.

Uses a pre-built schedule of recurring events (RBI, Fed, CPI, GDP, etc.)
and auto-generates upcoming dates. No external API needed.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Optional


# ------------------------------------------------------------------
# Curated recurring events (month, approximate_day, event, country, impact, category)
# These are well-known, fixed-schedule economic events.
# ------------------------------------------------------------------
_RECURRING_EVENTS = [
    # India — RBI
    {"event": "RBI Monetary Policy Decision", "country": "IN", "impact": "HIGH", "category": "interest_rate",
     "schedule": "bimonthly", "months": [2, 4, 6, 8, 10, 12], "day": 6},
    {"event": "India CPI Inflation Data", "country": "IN", "impact": "HIGH", "category": "inflation",
     "schedule": "monthly", "day": 12},
    {"event": "India WPI Inflation Data", "country": "IN", "impact": "MEDIUM", "category": "inflation",
     "schedule": "monthly", "day": 14},
    {"event": "India GDP Growth Rate (Quarterly)", "country": "IN", "impact": "HIGH", "category": "gdp",
     "schedule": "quarterly", "months": [2, 5, 8, 11], "day": 28},
    {"event": "India Trade Balance", "country": "IN", "impact": "MEDIUM", "category": "trade",
     "schedule": "monthly", "day": 15},
    {"event": "India Manufacturing PMI", "country": "IN", "impact": "MEDIUM", "category": "manufacturing",
     "schedule": "monthly", "day": 1},
    {"event": "India Services PMI", "country": "IN", "impact": "MEDIUM", "category": "services",
     "schedule": "monthly", "day": 3},
    {"event": "India Industrial Production (IIP)", "country": "IN", "impact": "MEDIUM", "category": "manufacturing",
     "schedule": "monthly", "day": 12},

    # US — Federal Reserve
    {"event": "US Fed Interest Rate Decision (FOMC)", "country": "US", "impact": "HIGH", "category": "interest_rate",
     "schedule": "bimonthly_irregular", "months": [1, 3, 5, 6, 7, 9, 11, 12], "day": 15},
    {"event": "US CPI Inflation Data", "country": "US", "impact": "HIGH", "category": "inflation",
     "schedule": "monthly", "day": 10},
    {"event": "US Non-Farm Payrolls (NFP)", "country": "US", "impact": "HIGH", "category": "employment",
     "schedule": "monthly", "day": 5},  # First Friday
    {"event": "US GDP Growth Rate (Quarterly)", "country": "US", "impact": "HIGH", "category": "gdp",
     "schedule": "quarterly", "months": [1, 4, 7, 10], "day": 25},
    {"event": "US Core PCE Price Index", "country": "US", "impact": "HIGH", "category": "inflation",
     "schedule": "monthly", "day": 28},
    {"event": "US Retail Sales", "country": "US", "impact": "MEDIUM", "category": "consumer",
     "schedule": "monthly", "day": 16},
    {"event": "US ISM Manufacturing PMI", "country": "US", "impact": "MEDIUM", "category": "manufacturing",
     "schedule": "monthly", "day": 1},
    {"event": "US ISM Services PMI", "country": "US", "impact": "MEDIUM", "category": "services",
     "schedule": "monthly", "day": 3},
    {"event": "US Unemployment Claims (Weekly)", "country": "US", "impact": "LOW", "category": "employment",
     "schedule": "weekly", "weekday": 3},  # Thursday
    {"event": "US Consumer Confidence", "country": "US", "impact": "MEDIUM", "category": "consumer",
     "schedule": "monthly", "day": 25},
    {"event": "US PPI (Producer Price Index)", "country": "US", "impact": "MEDIUM", "category": "inflation",
     "schedule": "monthly", "day": 11},

    # Earnings seasons (approximate)
    {"event": "India Q4 Earnings Season Begins", "country": "IN", "impact": "HIGH", "category": "earnings",
     "schedule": "quarterly", "months": [4, 7, 10, 1], "day": 10},
    {"event": "US Earnings Season Begins", "country": "US", "impact": "HIGH", "category": "earnings",
     "schedule": "quarterly", "months": [1, 4, 7, 10], "day": 12},

    # Global
    {"event": "ECB Interest Rate Decision", "country": "EU", "impact": "HIGH", "category": "interest_rate",
     "schedule": "bimonthly", "months": [1, 3, 4, 6, 7, 9, 10, 12], "day": 10},
    {"event": "Bank of Japan Rate Decision", "country": "JP", "impact": "MEDIUM", "category": "interest_rate",
     "schedule": "bimonthly", "months": [1, 3, 4, 6, 7, 9, 10, 12], "day": 18},
    {"event": "China GDP (Quarterly)", "country": "CN", "impact": "MEDIUM", "category": "gdp",
     "schedule": "quarterly", "months": [1, 4, 7, 10], "day": 15},
]


class EconomicCalendar:
    """Generate upcoming economic events from curated schedules."""

    @staticmethod
    def get_events(
        days: int = 30,
        country: Optional[str] = None,
        impact: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get upcoming events within the specified number of days.

        Parameters
        ----------
        days : int
            Look-ahead window (default 30 days).
        country : str, optional
            Filter by country code ("IN", "US", "EU", "JP", "CN").
        impact : str, optional
            Filter by impact ("HIGH", "MEDIUM", "LOW").
        """
        today = date.today()
        end_date = today + timedelta(days=days)
        events: list[dict[str, Any]] = []

        for template in _RECURRING_EVENTS:
            if country and template["country"] != country.upper():
                continue
            if impact and template["impact"] != impact.upper():
                continue

            upcoming = _generate_occurrences(template, today, end_date)
            events.extend(upcoming)

        # Sort by date
        events.sort(key=lambda e: e["date"])
        return events


def _generate_occurrences(
    template: dict[str, Any], start: date, end: date
) -> list[dict[str, Any]]:
    """Generate event occurrences between start and end dates."""
    results = []
    schedule = template.get("schedule", "monthly")

    if schedule == "weekly":
        weekday = template.get("weekday", 3)
        d = start
        while d <= end:
            if d.weekday() == weekday:
                results.append(_make_event(template, d))
            d += timedelta(days=1)

    elif schedule == "monthly":
        day = template.get("day", 1)
        for m_offset in range(0, ((end.year - start.year) * 12 + end.month - start.month) + 1):
            y = start.year + (start.month + m_offset - 1) // 12
            m = (start.month + m_offset - 1) % 12 + 1
            try:
                d = date(y, m, min(day, _days_in_month(y, m)))
            except ValueError:
                continue
            if start <= d <= end:
                results.append(_make_event(template, d))

    elif schedule in ("bimonthly", "bimonthly_irregular", "quarterly"):
        months = template.get("months", [])
        day = template.get("day", 1)
        for year in range(start.year, end.year + 1):
            for m in months:
                try:
                    d = date(year, m, min(day, _days_in_month(year, m)))
                except ValueError:
                    continue
                if start <= d <= end:
                    results.append(_make_event(template, d))

    return results


def _make_event(template: dict[str, Any], d: date) -> dict[str, Any]:
    """Create an event dict from a template and date."""
    days_away = (d - date.today()).days
    if days_away == 0:
        time_label = "Today"
    elif days_away == 1:
        time_label = "Tomorrow"
    elif days_away < 0:
        time_label = f"{abs(days_away)} days ago"
    else:
        time_label = f"In {days_away} days"

    return {
        "date": d.isoformat(),
        "day_of_week": d.strftime("%A"),
        "event": template["event"],
        "country": template["country"],
        "impact": template["impact"],
        "category": template["category"],
        "time_label": time_label,
        "days_away": days_away,
    }


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - timedelta(days=1)).day
